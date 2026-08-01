from __future__ import annotations

import pandas as pd

from rto_spc.particle_rules import (
    PARTICLE_REPEATED_EVENT_ESCALATION,
    PARTICLE_THRESHOLD_HIGH,
    PARTICLE_THRESHOLD_WARNING,
    apply_particle_threshold_rules,
)


def _row(metric_name: str, value: float, sequence_id: int = 1, tool_id: str = "RTO_A01") -> dict[str, object]:
    return {
        "timestamp": f"2026-01-{sequence_id:02d}",
        "phase": "monitoring",
        "tool_id": tool_id,
        "chamber_id": "CH1",
        "recipe_group": "RTO_BASELINE",
        "monitor_type": "Particle",
        "metric_name": metric_name,
        "value": value,
        "sequence_id": sequence_id,
    }


def test_corrected_particle_metric_thresholds() -> None:
    cases = [
        ("particle_total_adder", 10, PARTICLE_THRESHOLD_WARNING, "Medium"),
        ("particle_total_adder", 20, PARTICLE_THRESHOLD_HIGH, "High"),
        ("particle_cluster_adder", 3, PARTICLE_THRESHOLD_WARNING, "Medium"),
        ("particle_cluster_adder", 6, PARTICLE_THRESHOLD_HIGH, "High"),
        ("particle_large_adder", 1, PARTICLE_THRESHOLD_WARNING, "Medium"),
        ("particle_large_adder", 3, PARTICLE_THRESHOLD_HIGH, "High"),
    ]
    for metric_name, value, expected_rule, expected_severity in cases:
        result = apply_particle_threshold_rules(pd.DataFrame([_row(metric_name, value)]))
        assert result["rule_triggered"].iloc[0] == expected_rule
        assert result["severity"].iloc[0] == expected_severity


def test_repeated_event_escalation_uses_last_10_points_within_group() -> None:
    rows = [_row("particle_total_adder", value, sequence_id=i + 1) for i, value in enumerate([0, 10, 0, 11, 0, 12])]
    result = apply_particle_threshold_rules(pd.DataFrame(rows))
    assert PARTICLE_REPEATED_EVENT_ESCALATION in result["rule_triggered"].iloc[-1]
    assert result["severity"].iloc[-1] == "High"


def test_repeated_event_escalation_does_not_cross_group_boundaries() -> None:
    rows = [
        _row("particle_total_adder", 10, sequence_id=1, tool_id="RTO_A01"),
        _row("particle_total_adder", 10, sequence_id=2, tool_id="RTO_A01"),
        _row("particle_total_adder", 10, sequence_id=3, tool_id="RTO_A02"),
    ]
    result = apply_particle_threshold_rules(pd.DataFrame(rows))
    assert PARTICLE_REPEATED_EVENT_ESCALATION not in str(result[result["tool_id"] == "RTO_A02"]["rule_triggered"].iloc[0])
