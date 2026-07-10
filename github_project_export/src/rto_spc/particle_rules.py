from __future__ import annotations

import pandas as pd

from rto_spc.config import LEGACY_METRIC_ALIASES, PARTICLE_THRESHOLDS

PARTICLE_THRESHOLD_WARNING = "PARTICLE_THRESHOLD_WARNING"
PARTICLE_THRESHOLD_HIGH = "PARTICLE_THRESHOLD_HIGH"
PARTICLE_REPEATED_EVENT_ESCALATION = "PARTICLE_REPEATED_EVENT_ESCALATION"
GROUP_COLUMNS = ["tool_id", "chamber_id", "recipe_group", "metric_name"]


def _ensure_rule_columns(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    for column in ["ucl", "cl", "lcl"]:
        if column not in result.columns:
            result[column] = pd.NA
    if "warning_flag" not in result.columns:
        result["warning_flag"] = False
    if "ooc_flag" not in result.columns:
        result["ooc_flag"] = False
    if "rule_triggered" not in result.columns:
        result["rule_triggered"] = None
    if "severity" not in result.columns:
        result["severity"] = None
    return result


def apply_particle_threshold_rules(df: pd.DataFrame) -> pd.DataFrame:
    """Apply fixed Particle thresholds and repeated-event escalation."""
    result = _ensure_rule_columns(df)
    particle = result["monitor_type"] == "Particle"

    for _, group in result[particle].groupby(GROUP_COLUMNS, sort=False, dropna=False):
        ordered_index = group.sort_values(["timestamp", "sequence_id"]).index
        ordered = result.loc[ordered_index]
        metric_name = LEGACY_METRIC_ALIASES.get(str(ordered["metric_name"].iloc[0]), str(ordered["metric_name"].iloc[0]))
        thresholds = PARTICLE_THRESHOLDS[metric_name]
        result.loc[ordered_index, "ucl"] = thresholds["high"]
        result.loc[ordered_index, "cl"] = thresholds["warning"]
        result.loc[ordered_index, "lcl"] = 0.0
        values = pd.to_numeric(ordered["value"], errors="coerce")
        warning_hits = values >= thresholds["warning"]
        repeated_counts = warning_hits.rolling(window=10, min_periods=1).sum()

        for position, idx in enumerate(ordered_index):
            value = values.iloc[position]
            if pd.isna(value):
                result.at[idx, "warning_flag"] = False
                result.at[idx, "ooc_flag"] = False
                result.at[idx, "rule_triggered"] = None
                result.at[idx, "severity"] = None
                continue

            base_rule = None
            warning_flag = False
            ooc_flag = False
            severity = None

            if value >= thresholds["high"]:
                base_rule = PARTICLE_THRESHOLD_HIGH
                ooc_flag = True
                severity = "High"
            elif value >= thresholds["warning"]:
                base_rule = PARTICLE_THRESHOLD_WARNING
                warning_flag = True
                severity = "Medium"

            repeated = repeated_counts.iloc[position] >= 3
            if repeated:
                base_rule = f"{base_rule}; {PARTICLE_REPEATED_EVENT_ESCALATION}" if base_rule else PARTICLE_REPEATED_EVENT_ESCALATION
                warning_flag = False
                ooc_flag = True
                severity = "High"

            result.at[idx, "warning_flag"] = warning_flag
            result.at[idx, "ooc_flag"] = ooc_flag
            result.at[idx, "rule_triggered"] = base_rule
            result.at[idx, "severity"] = severity

    return result
