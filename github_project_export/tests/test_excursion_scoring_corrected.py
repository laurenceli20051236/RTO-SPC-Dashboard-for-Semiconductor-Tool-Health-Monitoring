from __future__ import annotations

import pandas as pd

from rto_spc.excursion_scoring import build_excursion_events


def test_every_warning_and_ooc_row_becomes_excursion_event() -> None:
    spc = pd.DataFrame(
        [
            {
                "timestamp": "2026-01-01",
                "tool_id": "RTO_A01",
                "chamber_id": "CH1",
                "recipe_group": "RTO_BASELINE",
                "monitor_type": "Thickness",
                "metric_name": "thickness_rtr_mean",
                "value": 101.0,
                "measurement_id": "MEA-1",
                "ucl": 102.0,
                "cl": 100.0,
                "lcl": 98.0,
                "warning_flag": True,
                "ooc_flag": False,
                "rule_triggered": "THICKNESS_WARNING_ZONE",
                "severity": "Medium",
                "sequence_id": 1,
            },
            {
                "timestamp": "2026-01-02",
                "tool_id": "RTO_A01",
                "chamber_id": "CH1",
                "recipe_group": "RTO_BASELINE",
                "monitor_type": "Particle",
                "metric_name": "particle_total_adder",
                "value": 22.0,
                "measurement_id": "MEA-2",
                "ucl": 20.0,
                "cl": 10.0,
                "lcl": 0.0,
                "warning_flag": False,
                "ooc_flag": True,
                "rule_triggered": "PARTICLE_THRESHOLD_HIGH",
                "severity": "High",
                "sequence_id": 2,
            },
        ]
    )

    events = build_excursion_events(spc)
    assert len(events) == 2
    assert events["event_id"].tolist() == ["EVT-000001", "EVT-000002"]
    assert set(events["status"]) == {"Open"}
    assert events["suggested_review_area"].notna().all()
