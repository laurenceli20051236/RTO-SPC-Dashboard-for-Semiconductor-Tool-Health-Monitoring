from __future__ import annotations

from rto_spc.config import CHAMBERS, PARTICLE_METRICS, RECIPE_GROUPS, THICKNESS_METRICS, TOOLS

MONITOR_MEASUREMENT_REQUIRED_COLUMNS = [
    "timestamp",
    "phase",
    "tool_id",
    "chamber_id",
    "recipe_group",
    "monitor_type",
    "metric_name",
    "value",
    "unit",
    "lot_id_hash",
    "monitor_wafer_id_hash",
    "sequence_id",
]

ALLOWED_PHASES = {"baseline", "monitoring"}
ALLOWED_MONITOR_TYPES = {"Thickness", "Particle"}
ALLOWED_METRIC_NAMES = set(THICKNESS_METRICS + PARTICLE_METRICS)
ALLOWED_TOOLS = set(TOOLS)
ALLOWED_CHAMBERS = set(CHAMBERS)
ALLOWED_RECIPE_GROUPS = set(RECIPE_GROUPS)

EXCURSION_EVENT_REQUIRED_COLUMNS = [
    "event_id",
    "timestamp",
    "tool_id",
    "chamber_id",
    "recipe_group",
    "monitor_type",
    "metric_name",
    "value",
    "ucl",
    "cl",
    "lcl",
    "rule_triggered",
    "severity",
    "suggested_review_area",
    "status",
    "comment",
]
