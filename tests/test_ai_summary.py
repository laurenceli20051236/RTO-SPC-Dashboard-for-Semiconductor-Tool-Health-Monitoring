from __future__ import annotations

from rto_spc.ai_summary import SUMMARY_DISCLAIMER, generate_local_excursion_summary


def _event() -> dict:
    return {
        "event_id": "EVT-000001",
        "timestamp": "2026-01-01 08:00:00",
        "tool_id": "RTO_A01",
        "chamber_id": "CH1",
        "monitor_type": "Particle",
        "metric_name": "total_adder",
        "value": 24,
        "ucl": None,
        "cl": None,
        "lcl": None,
        "rule_triggered": "PARTICLE_THRESHOLD_HIGH",
        "severity": "High",
        "suggested_review_area": "Review general contamination sources.",
    }


def test_summary_includes_event_id() -> None:
    assert "EVT-000001" in generate_local_excursion_summary(_event())


def test_summary_includes_tool_id() -> None:
    assert "RTO_A01" in generate_local_excursion_summary(_event())


def test_summary_includes_metric_name() -> None:
    assert "total_adder" in generate_local_excursion_summary(_event())


def test_summary_includes_severity() -> None:
    assert "High" in generate_local_excursion_summary(_event())


def test_summary_includes_disclaimer() -> None:
    assert SUMMARY_DISCLAIMER in generate_local_excursion_summary(_event())


def test_summary_does_not_require_external_api() -> None:
    summary = generate_local_excursion_summary(_event())
    assert isinstance(summary, str)
    assert summary
