from __future__ import annotations

import pandas as pd

from rto_spc.excursion_scoring import build_excursion_events


def _spc_row(sequence_id: int, warning: bool, ooc: bool, metric_name: str = "total_adder") -> dict:
    return {
        "timestamp": pd.Timestamp("2026-01-01") + pd.Timedelta(days=sequence_id),
        "phase": "monitoring",
        "tool_id": "RTO_A01",
        "chamber_id": "CH1",
        "recipe_group": "RTO_BASELINE",
        "monitor_type": "Particle",
        "metric_name": metric_name,
        "value": 12,
        "unit": "count",
        "lot_id_hash": f"LOT_{sequence_id}",
        "monitor_wafer_id_hash": f"WFR_{sequence_id}",
        "sequence_id": sequence_id,
        "ucl": None,
        "cl": None,
        "lcl": None,
        "warning_flag": warning,
        "ooc_flag": ooc,
        "rule_triggered": "PARTICLE_THRESHOLD_WARNING" if warning else "PARTICLE_THRESHOLD_HIGH",
        "severity": "Medium" if warning else "High",
    }


def test_every_warning_row_becomes_excursion_event() -> None:
    events = build_excursion_events(pd.DataFrame([_spc_row(1, True, False), _spc_row(2, False, False)]))
    assert len(events) == 1
    assert events["event_id"].iloc[0] == "EVT-000001"


def test_every_ooc_row_becomes_excursion_event() -> None:
    events = build_excursion_events(pd.DataFrame([_spc_row(1, False, True), _spc_row(2, False, False)]))
    assert len(events) == 1
    assert events["severity"].iloc[0] == "High"


def test_event_ids_are_sequential() -> None:
    events = build_excursion_events(pd.DataFrame([_spc_row(1, True, False), _spc_row(2, False, True)]))
    assert events["event_id"].tolist() == ["EVT-000001", "EVT-000002"]


def test_suggested_review_area_is_populated() -> None:
    events = build_excursion_events(pd.DataFrame([_spc_row(1, True, False, "cluster_adder")]))
    assert events["suggested_review_area"].iloc[0]


def test_event_status_defaults_to_open() -> None:
    events = build_excursion_events(pd.DataFrame([_spc_row(1, True, False)]))
    assert events["status"].iloc[0] == "Open"
