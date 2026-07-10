from __future__ import annotations

import pandas as pd

from rto_spc.chart_helpers import plot_fleet_tool_health_bar
from rto_spc.data_pipeline import generate_all_sample_data
from rto_spc.particle_rules import PARTICLE_REPEATED_EVENT_ESCALATION
from rto_spc.tool_health import calculate_tool_health


def _event(sequence_id: int, monitor_type: str = "Particle", severity: str = "High", rule: str = "PARTICLE_THRESHOLD_HIGH") -> dict:
    return {
        "event_id": f"EVT-{sequence_id:06d}",
        "timestamp": pd.Timestamp("2026-01-01") + pd.Timedelta(days=sequence_id),
        "tool_id": "RTO_A01",
        "chamber_id": "CH1",
        "recipe_group": "RTO_BASELINE",
        "monitor_type": monitor_type,
        "metric_name": "total_adder" if monitor_type == "Particle" else "thickness_mean",
        "value": 20,
        "ucl": None,
        "cl": None,
        "lcl": None,
        "rule_triggered": rule,
        "severity": severity,
        "suggested_review_area": "review",
        "status": "Open",
        "comment": "synthetic event generated for demo",
    }


def test_healthy_score_is_high() -> None:
    health = calculate_tool_health(pd.DataFrame())
    assert health["health_score"].min() >= 90
    assert set(health["status"]) == {"Healthy"}


def test_repeated_events_reduce_score() -> None:
    health = calculate_tool_health(pd.DataFrame([_event(1, "Particle", "High", f"PARTICLE_THRESHOLD_HIGH; {PARTICLE_REPEATED_EVENT_ESCALATION}")]))
    score = health[health["tool_id"] == "RTO_A01"]["health_score"].iloc[0]
    penalty = health[health["tool_id"] == "RTO_A01"]["penalty_points"].iloc[0]
    assert score == 95.0
    assert penalty == 5.0


def test_high_particle_events_reduce_score() -> None:
    health = calculate_tool_health(pd.DataFrame([_event(1, "Particle", "High", "PARTICLE_THRESHOLD_HIGH")]))
    score = health[health["tool_id"] == "RTO_A01"]["health_score"].iloc[0]
    assert score == 97.0


def test_score_is_clamped_between_0_and_100() -> None:
    events = pd.DataFrame([_event(i) | {"timestamp": pd.Timestamp("2026-01-01")} for i in range(1, 2000)])
    health = calculate_tool_health(events)
    score = health[health["tool_id"] == "RTO_A01"]["health_score"].iloc[0]
    assert 0 <= score <= 100
    assert score == 0


def test_status_mapping_works() -> None:
    watch = calculate_tool_health(pd.DataFrame([_event(i) | {"timestamp": pd.Timestamp("2026-01-01")} for i in range(1, 9)]))
    warning = calculate_tool_health(pd.DataFrame([_event(i) | {"timestamp": pd.Timestamp("2026-01-01")} for i in range(1, 14)]))
    critical = calculate_tool_health(pd.DataFrame([_event(i) | {"timestamp": pd.Timestamp("2026-01-01")} for i in range(1, 15)]))
    assert watch[watch["tool_id"] == "RTO_A01"]["status"].iloc[0] == "Watch"
    assert warning[warning["tool_id"] == "RTO_A01"]["status"].iloc[0] == "Warning"
    assert critical[critical["tool_id"] == "RTO_A01"]["status"].iloc[0] == "Critical"


def test_zero_score_tool_health_bar_remains_visible() -> None:
    health = pd.DataFrame(
        [
            {
                "tool_id": "RTO_A01",
                "health_score": 0,
                "status": "Critical",
                "event_count": 10,
                "high_events": 10,
                "medium_events": 0,
            }
        ]
    )
    fig = plot_fleet_tool_health_bar(health)
    assert fig.data[0].orientation == "h"
    assert fig.data[0].x[0] > 0
    assert fig.data[0].customdata[0][0] == 0


def test_health_score_starts_at_100_then_decreases() -> None:
    health = calculate_tool_health(pd.DataFrame([_event(i) | {"timestamp": pd.Timestamp("2026-01-01")} for i in range(1, 6)]))
    row = health[health["tool_id"] == "RTO_A01"].iloc[0]
    assert row["starting_score"] == 100
    assert row["penalty_points"] > 0
    assert row["health_score"] == row["starting_score"] - row["penalty_points"]


def test_generated_demo_health_has_three_healthy_tools_and_one_degraded_tool(tmp_path) -> None:
    outputs = generate_all_sample_data(output_dir=tmp_path, seed=42)
    events = pd.read_csv(outputs["excursion_events"])
    health = calculate_tool_health(events)

    healthy = health[health["health_score"] > 90]
    degraded = health[health["tool_id"] == "RTO_A04"].iloc[0]

    assert set(healthy["tool_id"]) == {"RTO_A01", "RTO_A02", "RTO_A03"}
    assert degraded["health_score"] == 25.0
    assert degraded["status"] == "Critical"
