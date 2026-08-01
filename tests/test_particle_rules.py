from __future__ import annotations

import pandas as pd

from rto_spc.particle_rules import (
    PARTICLE_REPEATED_EVENT_ESCALATION,
    PARTICLE_THRESHOLD_HIGH,
    PARTICLE_THRESHOLD_WARNING,
    apply_particle_threshold_rules,
)


def _particle_row(metric_name: str, value: float, sequence_id: int = 1, tool_id: str = "RTO_A01") -> dict:
    return {
        "timestamp": pd.Timestamp("2026-01-01") + pd.Timedelta(days=sequence_id),
        "phase": "monitoring",
        "tool_id": tool_id,
        "chamber_id": "CH1",
        "recipe_group": "RTO_BASELINE",
        "monitor_type": "Particle",
        "metric_name": metric_name,
        "value": value,
        "unit": "count",
        "lot_id_hash": f"LOT_{tool_id}_{sequence_id}",
        "monitor_wafer_id_hash": f"WFR_{tool_id}_{sequence_id}",
        "sequence_id": sequence_id,
    }


def test_total_adder_warning() -> None:
    result = apply_particle_threshold_rules(pd.DataFrame([_particle_row("total_adder", 10)]))
    assert bool(result["warning_flag"].iloc[0]) is True
    assert result["rule_triggered"].iloc[0] == PARTICLE_THRESHOLD_WARNING


def test_total_adder_high() -> None:
    result = apply_particle_threshold_rules(pd.DataFrame([_particle_row("total_adder", 20)]))
    assert bool(result["ooc_flag"].iloc[0]) is True
    assert result["rule_triggered"].iloc[0] == PARTICLE_THRESHOLD_HIGH


def test_cluster_adder_warning() -> None:
    result = apply_particle_threshold_rules(pd.DataFrame([_particle_row("cluster_adder", 3)]))
    assert bool(result["warning_flag"].iloc[0]) is True


def test_cluster_adder_high() -> None:
    result = apply_particle_threshold_rules(pd.DataFrame([_particle_row("cluster_adder", 6)]))
    assert bool(result["ooc_flag"].iloc[0]) is True


def test_large_particle_adder_warning() -> None:
    result = apply_particle_threshold_rules(pd.DataFrame([_particle_row("large_particle_adder", 1)]))
    assert bool(result["warning_flag"].iloc[0]) is True


def test_large_particle_adder_high() -> None:
    result = apply_particle_threshold_rules(pd.DataFrame([_particle_row("large_particle_adder", 3)]))
    assert bool(result["ooc_flag"].iloc[0]) is True


def test_repeated_event_escalation_in_last_10_points() -> None:
    rows = [_particle_row("total_adder", value, i) for i, value in enumerate([0, 10, 0, 11, 0, 12], start=1)]
    result = apply_particle_threshold_rules(pd.DataFrame(rows))
    last = result.iloc[-1]
    assert bool(last["ooc_flag"]) is True
    assert last["severity"] == "High"
    assert PARTICLE_REPEATED_EVENT_ESCALATION in last["rule_triggered"]


def test_repeated_event_logic_does_not_cross_group_boundaries() -> None:
    rows = [
        _particle_row("total_adder", 10, 1, "RTO_A01"),
        _particle_row("total_adder", 11, 2, "RTO_A01"),
        _particle_row("total_adder", 12, 3, "RTO_A02"),
    ]
    result = apply_particle_threshold_rules(pd.DataFrame(rows))
    assert not result["rule_triggered"].fillna("").str.contains(PARTICLE_REPEATED_EVENT_ESCALATION, regex=False).any()
