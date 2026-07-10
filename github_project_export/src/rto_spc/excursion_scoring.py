from __future__ import annotations

import pandas as pd

EVENT_COLUMNS = [
    "event_id",
    "timestamp",
    "phase",
    "tool_id",
    "chamber_id",
    "recipe_group",
    "monitor_type",
    "metric_name",
    "value",
    "measurement_id",
    "ucl",
    "cl",
    "lcl",
    "rule_triggered",
    "severity",
    "suggested_review_area",
    "status",
    "comment",
    "event_source",
    "method_type",
]

SUGGESTED_REVIEW_AREA = {
    "thickness_rtr_mean": "Review run-to-run mean drift, RTO recipe centering, chamber thermal stability, and metrology trend.",
    "thickness_xbar": "Review average thickness behavior, chamber matching, recipe stability, and monitor wafer measurement consistency.",
    "thickness_wiw_stdev": "Review within-wafer uniformity, wafer placement, thermal uniformity, and chamber condition.",
    "thickness_sigma": "Review process variation, metrology repeatability, chamber stability, and monitor data consistency.",
    "particle_total_adder": "Review general contamination sources, chamber clean history, and wafer transfer path.",
    "particle_cluster_adder": "Review localized particle source, wafer handling, chamber condition, and repeated cluster behavior.",
    "particle_large_adder": "Review high-risk particle source, recent chamber recovery, transfer path condition, and PM effectiveness.",
}


def _review_area(metric_name: str, rule_triggered: object) -> str:
    _ = rule_triggered
    return SUGGESTED_REVIEW_AREA.get(metric_name, "Review synthetic monitor stream and recent process context.")


def _phase1_source_and_method(row: pd.Series) -> tuple[str, str]:
    rule = str(row.get("rule_triggered") or "")
    if row.get("monitor_type") == "Thickness":
        return "phase1_thickness_monitor", "baseline_3sigma"
    if "PARTICLE_REPEATED_EVENT_ESCALATION" in rule:
        return "phase1_particle_threshold", "repeated_event"
    return "phase1_particle_threshold", "threshold"


def _append_event(
    rows: list[dict[str, object]],
    *,
    timestamp: object,
    phase: object,
    tool_id: object,
    chamber_id: object,
    recipe_group: object,
    monitor_type: object,
    metric_name: str,
    value: object,
    ucl: object,
    cl: object,
    lcl: object,
    rule_triggered: object,
    severity: object,
    event_source: str,
    method_type: str,
    measurement_id: object = None,
) -> None:
    rows.append(
        {
            "timestamp": timestamp,
            "phase": phase,
            "tool_id": tool_id,
            "chamber_id": chamber_id,
            "recipe_group": recipe_group,
            "monitor_type": monitor_type,
            "metric_name": metric_name,
            "value": value,
            "measurement_id": measurement_id,
            "ucl": ucl,
            "cl": cl,
            "lcl": lcl,
            "rule_triggered": rule_triggered,
            "severity": severity,
            "suggested_review_area": _review_area(metric_name, rule_triggered),
            "status": "Open",
            "comment": "synthetic event generated for demo",
            "event_source": event_source,
            "method_type": method_type,
        }
    )


def build_excursion_events(spc_results_df: pd.DataFrame) -> pd.DataFrame:
    """Create one excursion event row for every Phase 1 warning/OOC row."""
    rows: list[dict[str, object]] = []

    if spc_results_df is not None and not spc_results_df.empty:
        warning = spc_results_df.get("warning_flag", False)
        ooc = spc_results_df.get("ooc_flag", False)
        flagged = spc_results_df[warning.fillna(False).astype(bool) | ooc.fillna(False).astype(bool)].copy()
        if not flagged.empty:
            flagged = flagged.sort_values(["timestamp", "tool_id", "chamber_id", "recipe_group", "metric_name", "sequence_id"])
            for _, row in flagged.iterrows():
                event_source, method_type = _phase1_source_and_method(row)
                metric_name = row["metric_name"]
                _append_event(
                    rows,
                    timestamp=row["timestamp"],
                    phase=row.get("phase"),
                    tool_id=row["tool_id"],
                    chamber_id=row["chamber_id"],
                    recipe_group=row["recipe_group"],
                    monitor_type=row["monitor_type"],
                    metric_name=metric_name,
                    value=row["value"],
                    measurement_id=row.get("measurement_id"),
                    ucl=row.get("ucl"),
                    cl=row.get("cl"),
                    lcl=row.get("lcl"),
                    rule_triggered=row.get("rule_triggered"),
                    severity=row.get("severity"),
                    event_source=event_source,
                    method_type=method_type,
                )

    if not rows:
        return pd.DataFrame(columns=EVENT_COLUMNS)

    events = pd.DataFrame(rows)
    events = events.sort_values(["timestamp", "tool_id", "chamber_id", "recipe_group", "metric_name", "rule_triggered"]).reset_index(drop=True)
    events.insert(0, "event_id", [f"EVT-{event_number:06d}" for event_number in range(1, len(events) + 1)])
    return events[EVENT_COLUMNS]
