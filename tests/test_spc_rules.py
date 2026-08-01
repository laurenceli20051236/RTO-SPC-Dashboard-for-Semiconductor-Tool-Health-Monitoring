from __future__ import annotations

import pandas as pd

from rto_spc.control_limits import apply_baseline_imr_limits
from rto_spc.spc_rules import THICKNESS_IMR_BEYOND_LIMIT, THICKNESS_IMR_WARNING_LIMIT, THICKNESS_MR_SPIKE, apply_thickness_imr_rules


def _row(value: float, *, ucl: float = 12.0, lcl: float = 8.0, mr_value: float = 0.0, mr_ucl: float = 2.0) -> dict:
    return {
        "timestamp": pd.Timestamp("2026-01-01"),
        "phase": "monitoring",
        "tool_id": "RTO_A01",
        "chamber_id": "CH1",
        "recipe_group": "RTO_BASELINE",
        "monitor_type": "Thickness",
        "metric_name": "thickness_mean",
        "value": value,
        "unit": "nm",
        "lot_id_hash": "LOT",
        "monitor_wafer_id_hash": "WFR",
        "sequence_id": 1,
        "baseline_mean": 10.0,
        "baseline_sigma": 1.0,
        "ucl": ucl,
        "cl": 10.0,
        "lcl": lcl,
        "mr_value": mr_value,
        "mr_ucl": mr_ucl,
        "mr_cl": 1.0,
        "mr_lcl": 0.0,
    }


def test_value_above_ucl_triggers_beyond_limit() -> None:
    result = apply_thickness_imr_rules(pd.DataFrame([_row(13.0)]))
    assert bool(result["ooc_flag"].iloc[0]) is True
    assert result["rule_triggered"].iloc[0] == THICKNESS_IMR_BEYOND_LIMIT
    assert result["severity"].iloc[0] == "High"


def test_value_below_lcl_triggers_beyond_limit() -> None:
    result = apply_thickness_imr_rules(pd.DataFrame([_row(7.0)]))
    assert result["rule_triggered"].iloc[0] == THICKNESS_IMR_BEYOND_LIMIT


def test_mr_above_mr_ucl_triggers_mr_spike() -> None:
    result = apply_thickness_imr_rules(pd.DataFrame([_row(10.0, mr_value=3.0, mr_ucl=2.0)]))
    assert bool(result["ooc_flag"].iloc[0]) is False
    assert bool(result["warning_flag"].iloc[0]) is True
    assert result["rule_triggered"].iloc[0] == THICKNESS_MR_SPIKE
    assert result["severity"].iloc[0] == "Medium"


def test_value_beyond_warning_limit_triggers_medium_warning() -> None:
    result = apply_thickness_imr_rules(pd.DataFrame([_row(12.5, ucl=13.0, lcl=7.0)]))
    assert bool(result["ooc_flag"].iloc[0]) is False
    assert bool(result["warning_flag"].iloc[0]) is True
    assert result["rule_triggered"].iloc[0] == THICKNESS_IMR_WARNING_LIMIT
    assert result["severity"].iloc[0] == "Medium"


def test_stable_thickness_does_not_trigger_event() -> None:
    result = apply_thickness_imr_rules(pd.DataFrame([_row(10.0, mr_value=1.0, mr_ucl=2.0)]))
    assert bool(result["ooc_flag"].iloc[0]) is False
    assert bool(result["warning_flag"].iloc[0]) is False
    assert pd.isna(result["rule_triggered"].iloc[0])


def test_rules_do_not_cross_group_boundaries() -> None:
    rows = []
    for tool_id, base, monitor in [("RTO_A01", 10, 10.5), ("RTO_A02", 50, 50.5)]:
        for i, value in enumerate([base, base + 1] * 10 + [monitor], start=1):
            rows.append(
                {
                    "timestamp": pd.Timestamp("2026-01-01") + pd.Timedelta(days=i),
                    "phase": "baseline" if i <= 20 else "monitoring",
                    "tool_id": tool_id,
                    "chamber_id": "CH1",
                    "recipe_group": "RTO_BASELINE",
                    "monitor_type": "Thickness",
                    "metric_name": "thickness_mean",
                    "value": value,
                    "unit": "nm",
                    "lot_id_hash": f"LOT_{tool_id}_{i}",
                    "monitor_wafer_id_hash": f"WFR_{tool_id}_{i}",
                    "sequence_id": i,
                }
            )
    limited = apply_baseline_imr_limits(pd.DataFrame(rows))
    ruled = apply_thickness_imr_rules(limited)
    monitoring = ruled[ruled["phase"] == "monitoring"]
    assert not monitoring["ooc_flag"].any()
