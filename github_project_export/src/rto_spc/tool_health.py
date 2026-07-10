from __future__ import annotations

import pandas as pd

from rto_spc.config import (
    TOOL_HEALTH_HIGH_EVENT_WEIGHT,
    TOOL_HEALTH_LOOKBACK_DAYS,
    TOOL_HEALTH_MEDIUM_EVENT_WEIGHT,
    TOOL_HEALTH_REPEATED_EVENT_WEIGHT,
    TOOL_HEALTH_SCORE_POINTS_PER_WEIGHT,
    TOOL_HEALTH_START_SCORE,
)
from rto_spc.data_generator import TOOLS
from rto_spc.particle_rules import PARTICLE_REPEATED_EVENT_ESCALATION

TOOL_HEALTH_LABEL = (
    "Synthetic deterministic score: trailing 30-day monitoring weighted events "
    "(High x3 + Medium x1 + repeated particle escalation x2) start at 100 and subtract "
    f"{TOOL_HEALTH_SCORE_POINTS_PER_WEIGHT:g} health-score points per weighted event point. "
    "Synthetic demo health score, not a production disposition rule."
)


def _status(score: float) -> str:
    if score >= 90:
        return "Healthy"
    if score >= 75:
        return "Watch"
    if score >= 60:
        return "Warning"
    return "Critical"


def _event_penalty(row: pd.Series) -> int:
    severity = row.get("severity")
    rule = str(row.get("rule_triggered") or "")
    if severity == "High":
        weight = TOOL_HEALTH_HIGH_EVENT_WEIGHT
    elif severity == "Medium":
        weight = TOOL_HEALTH_MEDIUM_EVENT_WEIGHT
    else:
        weight = 0

    if PARTICLE_REPEATED_EVENT_ESCALATION in rule:
        weight += TOOL_HEALTH_REPEATED_EVENT_WEIGHT
    return weight


def calculate_tool_health(excursion_events_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate a simple synthetic tool-level demo health score."""
    if excursion_events_df is None or excursion_events_df.empty:
        tools = TOOLS
    else:
        excursion_events_df = excursion_events_df.copy()
        excursion_events_df["timestamp"] = pd.to_datetime(excursion_events_df["timestamp"])
        if "phase" in excursion_events_df.columns:
            excursion_events_df = excursion_events_df[excursion_events_df["phase"].fillna("monitoring") == "monitoring"]
        latest_timestamp = excursion_events_df["timestamp"].max()
        window_start = latest_timestamp - pd.Timedelta(days=TOOL_HEALTH_LOOKBACK_DAYS)
        excursion_events_df = excursion_events_df[excursion_events_df["timestamp"] >= window_start]
        tools = sorted(set(TOOLS).union(set(excursion_events_df["tool_id"].dropna().astype(str))))

    rows = []
    for tool_id in tools:
        if excursion_events_df is None or excursion_events_df.empty:
            events = pd.DataFrame()
        else:
            events = excursion_events_df[excursion_events_df["tool_id"] == tool_id]

        weighted_events = int(events.apply(_event_penalty, axis=1).sum()) if not events.empty else 0
        penalty = round(weighted_events * TOOL_HEALTH_SCORE_POINTS_PER_WEIGHT, 1)
        score = round(max(0.0, min(TOOL_HEALTH_START_SCORE, TOOL_HEALTH_START_SCORE - penalty)), 1)
        rules = events.get("rule_triggered", pd.Series(dtype=str)).fillna("").astype(str) if not events.empty else pd.Series(dtype=str)
        rows.append(
            {
                "tool_id": tool_id,
                "starting_score": TOOL_HEALTH_START_SCORE,
                "penalty_points": penalty,
                "health_score": score,
                "status": _status(score),
                "event_count": int(len(events)),
                "high_events": int((events.get("severity") == "High").sum()) if not events.empty else 0,
                "medium_events": int((events.get("severity") == "Medium").sum()) if not events.empty else 0,
                "weighted_event_score": weighted_events,
                "repeated_escalations": int(rules.str.contains(PARTICLE_REPEATED_EVENT_ESCALATION, regex=False).sum()),
            }
        )

    return pd.DataFrame(rows).sort_values("tool_id").reset_index(drop=True)
