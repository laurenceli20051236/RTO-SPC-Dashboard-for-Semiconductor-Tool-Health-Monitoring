from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"

MONITOR_MEASUREMENT_COLUMNS = [
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
    "measurement_id",
    "sequence_id",
]

SPC_RESULT_COLUMNS = MONITOR_MEASUREMENT_COLUMNS + [
    "baseline_mean",
    "baseline_sigma",
    "ucl",
    "cl",
    "lcl",
    "mr_value",
    "mr_ucl",
    "mr_cl",
    "mr_lcl",
    "warning_flag",
    "ooc_flag",
    "rule_triggered",
    "severity",
]

EXCURSION_EVENT_COLUMNS = [
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

def _load_csv(filename: str, columns: list[str]) -> pd.DataFrame:
    path = DATA_DIR / filename
    if not path.exists():
        return pd.DataFrame(columns=columns)
    parse_dates = [column for column in ["timestamp", "window_end_timestamp", "event_timestamp", "context_timestamp"] if column in columns]
    return pd.read_csv(path, parse_dates=parse_dates)


def load_monitor_measurements() -> pd.DataFrame:
    return _load_csv("monitor_measurements.csv", MONITOR_MEASUREMENT_COLUMNS)


def load_spc_results() -> pd.DataFrame:
    return _load_csv("spc_results.csv", SPC_RESULT_COLUMNS)


def load_excursion_events() -> pd.DataFrame:
    return _load_csv("excursion_events.csv", EXCURSION_EVENT_COLUMNS)
