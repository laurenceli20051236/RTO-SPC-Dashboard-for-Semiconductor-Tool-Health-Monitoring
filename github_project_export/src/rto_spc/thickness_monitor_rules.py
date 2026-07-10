from __future__ import annotations

import pandas as pd

from rto_spc.config import (
    SPC_WARNING_SIGMA_K,
    THICKNESS_VARIATION_METRICS,
)

THICKNESS_BEYOND_CONTROL_LIMIT = "THICKNESS_BEYOND_CONTROL_LIMIT"
THICKNESS_WARNING_ZONE = "THICKNESS_WARNING_ZONE"
THICKNESS_VARIATION_HIGH = "THICKNESS_VARIATION_HIGH"


def _ensure_rule_columns(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    if "warning_flag" not in result.columns:
        result["warning_flag"] = False
    if "ooc_flag" not in result.columns:
        result["ooc_flag"] = False
    if "rule_triggered" not in result.columns:
        result["rule_triggered"] = None
    if "severity" not in result.columns:
        result["severity"] = None
    return result


def apply_thickness_monitor_rules(df: pd.DataFrame) -> pd.DataFrame:
    """Apply corrected Phase 1 RTO thickness monitor rules."""
    result = _ensure_rule_columns(df)
    thickness_index = result.index[result["monitor_type"] == "Thickness"]

    for idx in thickness_index:
        row = result.loc[idx]
        metric_name = str(row.get("metric_name"))
        value = pd.to_numeric(pd.Series([row.get("value")]), errors="coerce").iloc[0]
        ucl = pd.to_numeric(pd.Series([row.get("ucl")]), errors="coerce").iloc[0]
        cl = pd.to_numeric(pd.Series([row.get("cl")]), errors="coerce").iloc[0]
        lcl = pd.to_numeric(pd.Series([row.get("lcl")]), errors="coerce").iloc[0]
        baseline_sigma = pd.to_numeric(pd.Series([row.get("baseline_sigma")]), errors="coerce").iloc[0]

        rule = None
        warning_flag = False
        ooc_flag = False
        severity = None

        if metric_name in THICKNESS_VARIATION_METRICS:
            if pd.notna(value) and pd.notna(ucl) and value > ucl:
                rule = THICKNESS_VARIATION_HIGH
                ooc_flag = True
                severity = "High"
            elif pd.notna(value) and pd.notna(cl) and pd.notna(baseline_sigma) and baseline_sigma > 0:
                warning_ucl = cl + SPC_WARNING_SIGMA_K * baseline_sigma
                if value > warning_ucl:
                    rule = THICKNESS_WARNING_ZONE
                    warning_flag = True
                    severity = "Medium"
        elif pd.notna(value) and pd.notna(ucl) and pd.notna(lcl) and (value > ucl or value < lcl):
            rule = THICKNESS_BEYOND_CONTROL_LIMIT
            ooc_flag = True
            severity = "High"
        elif pd.notna(value) and pd.notna(cl) and pd.notna(baseline_sigma) and baseline_sigma > 0:
            warning_ucl = cl + SPC_WARNING_SIGMA_K * baseline_sigma
            warning_lcl = cl - SPC_WARNING_SIGMA_K * baseline_sigma
            within_limits = (pd.isna(ucl) or value <= ucl) and (pd.isna(lcl) or value >= lcl)
            if within_limits and (value > warning_ucl or value < warning_lcl):
                rule = THICKNESS_WARNING_ZONE
                warning_flag = True
                severity = "Medium"

        result.at[idx, "warning_flag"] = warning_flag
        result.at[idx, "ooc_flag"] = ooc_flag
        result.at[idx, "rule_triggered"] = rule
        result.at[idx, "severity"] = severity

    return result
