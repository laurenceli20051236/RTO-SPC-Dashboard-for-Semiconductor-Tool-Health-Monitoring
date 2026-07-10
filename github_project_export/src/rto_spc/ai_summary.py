from __future__ import annotations

import pandas as pd

from rto_spc.particle_rules import PARTICLE_THRESHOLDS

SUMMARY_DISCLAIMER = "This summary is generated from deterministic SPC / threshold results and does not replace engineering review."


def _value_or_blank(event_row: dict, key: str) -> object:
    value = event_row.get(key)
    if pd.isna(value):
        return "not available"
    return value


def _limit_or_threshold_context(event_row: dict) -> str:
    metric_name = event_row.get("metric_name")
    if metric_name in PARTICLE_THRESHOLDS:
        thresholds = PARTICLE_THRESHOLDS[metric_name]
        return f"synthetic warning threshold={thresholds['warning']}, high threshold={thresholds['high']}"

    ucl = event_row.get("ucl")
    cl = event_row.get("cl")
    lcl = event_row.get("lcl")
    if pd.notna(ucl) and pd.notna(cl) and pd.notna(lcl):
        return f"baseline-only limits UCL={ucl}, CL={cl}, LCL={lcl}"
    return "limit context not available"


def generate_local_excursion_summary(event_row: dict) -> str:
    """Generate a deterministic local summary for one excursion event."""
    row = dict(event_row)
    return (
        f"Event {_value_or_blank(row, 'event_id')} occurred at {_value_or_blank(row, 'timestamp')} "
        f"on tool {_value_or_blank(row, 'tool_id')} chamber {_value_or_blank(row, 'chamber_id')}. "
        f"Monitor type: {_value_or_blank(row, 'monitor_type')}. "
        f"Metric: {_value_or_blank(row, 'metric_name')}. "
        f"Value: {_value_or_blank(row, 'value')}. "
        f"Limit or threshold context: {_limit_or_threshold_context(row)}. "
        f"Rule triggered: {_value_or_blank(row, 'rule_triggered')}. "
        f"Severity: {_value_or_blank(row, 'severity')}. "
        f"Suggested review area: {_value_or_blank(row, 'suggested_review_area')}. "
        f"{SUMMARY_DISCLAIMER}"
    )
