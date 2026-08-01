from __future__ import annotations

import pandas as pd

from rto_spc.control_limits import apply_baseline_thickness_limits
from rto_spc.thickness_monitor_rules import (
    THICKNESS_BEYOND_CONTROL_LIMIT,
    THICKNESS_VARIATION_HIGH,
    THICKNESS_WARNING_ZONE,
    apply_thickness_monitor_rules,
)


def _rows(metric_name: str, *, tool_id: str = "RTO_A01", chamber_id: str = "CH1", recipe_group: str = "RTO_BASELINE", monitoring_value: float = 10.0) -> pd.DataFrame:
    rows = []
    for sequence_id, value in enumerate([9.0, 10.0, 11.0, 10.0, 9.0, 10.0], start=1):
        rows.append(
            {
                "timestamp": f"2026-01-{sequence_id:02d}",
                "phase": "baseline",
                "tool_id": tool_id,
                "chamber_id": chamber_id,
                "recipe_group": recipe_group,
                "monitor_type": "Thickness",
                "metric_name": metric_name,
                "value": value,
                "unit": "synthetic",
                "lot_id_hash": f"LOT-{sequence_id}",
                "monitor_wafer_id_hash": f"WFR-{sequence_id}",
                "measurement_id": f"MEA-{sequence_id}",
                "sequence_id": sequence_id,
            }
        )
    rows.append(
        {
            "timestamp": "2026-01-20",
            "phase": "monitoring",
            "tool_id": tool_id,
            "chamber_id": chamber_id,
            "recipe_group": recipe_group,
            "monitor_type": "Thickness",
            "metric_name": metric_name,
            "value": monitoring_value,
            "unit": "synthetic",
            "lot_id_hash": "LOT-MON",
            "monitor_wafer_id_hash": "WFR-MON",
            "measurement_id": "MEA-MON",
            "sequence_id": 20,
        }
    )
    return pd.DataFrame(rows)


def _ruled(metric_name: str, value: float) -> pd.Series:
    limited = apply_baseline_thickness_limits(_rows(metric_name, monitoring_value=value))
    ruled = apply_thickness_monitor_rules(limited)
    return ruled[ruled["phase"] == "monitoring"].iloc[0]


def test_thickness_rtr_mean_beyond_ucl_triggers_control_limit() -> None:
    row = _ruled("thickness_rtr_mean", 13.5)
    assert row["rule_triggered"] == THICKNESS_BEYOND_CONTROL_LIMIT
    assert row["severity"] == "High"


def test_thickness_xbar_beyond_ucl_triggers_control_limit() -> None:
    row = _ruled("thickness_xbar", 13.5)
    assert row["rule_triggered"] == THICKNESS_BEYOND_CONTROL_LIMIT


def test_thickness_wiw_stdev_beyond_ucl_triggers_variation_high() -> None:
    row = _ruled("thickness_wiw_stdev", 13.5)
    assert row["rule_triggered"] == THICKNESS_VARIATION_HIGH


def test_thickness_sigma_beyond_ucl_triggers_variation_high() -> None:
    row = _ruled("thickness_sigma", 13.5)
    assert row["rule_triggered"] == THICKNESS_VARIATION_HIGH


def test_variation_metric_below_lcl_does_not_trigger_event() -> None:
    row = _ruled("thickness_sigma", 5.0)
    assert pd.isna(row["rule_triggered"])
    assert not row["warning_flag"]
    assert not row["ooc_flag"]


def test_warning_zone_triggers_medium_warning() -> None:
    row = _ruled("thickness_xbar", 11.6)
    assert row["rule_triggered"] == THICKNESS_WARNING_ZONE
    assert row["warning_flag"]
    assert not row["ooc_flag"]
    assert row["severity"] == "Medium"


def test_stable_thickness_data_does_not_trigger_event() -> None:
    row = _ruled("thickness_xbar", 10.0)
    assert pd.isna(row["rule_triggered"])
    assert not row["warning_flag"]
    assert not row["ooc_flag"]


def test_monitoring_excursion_does_not_change_limits() -> None:
    stable = apply_baseline_thickness_limits(_rows("thickness_xbar", monitoring_value=10.0))
    shifted = apply_baseline_thickness_limits(_rows("thickness_xbar", monitoring_value=30.0))
    assert stable["ucl"].iloc[0] == shifted["ucl"].iloc[0]


def test_rules_do_not_cross_stream_boundaries() -> None:
    first = _rows("thickness_xbar", tool_id="RTO_A01", monitoring_value=13.5)
    second = _rows("thickness_xbar", tool_id="RTO_A02", monitoring_value=10.0)
    limited = apply_baseline_thickness_limits(pd.concat([first, second], ignore_index=True))
    ruled = apply_thickness_monitor_rules(limited)
    monitoring = ruled[ruled["phase"] == "monitoring"].sort_values("tool_id")
    assert monitoring.iloc[0]["rule_triggered"] == THICKNESS_BEYOND_CONTROL_LIMIT
    assert pd.isna(monitoring.iloc[1]["rule_triggered"])
