from __future__ import annotations

import pandas as pd

from rto_spc.chart_helpers import (
    plot_fleet_event_count_bar,
    plot_fleet_excursion_timeline,
    plot_fleet_particle_trend,
    plot_fleet_thickness_trend,
)


def _spc_rows() -> pd.DataFrame:
    rows = []
    for tool_id in ["RTO_A01", "RTO_A02"]:
        for chamber_id in ["CH1", "CH2"]:
            rows.append(
                {
                    "timestamp": "2026-01-01",
                    "phase": "monitoring",
                    "tool_id": tool_id,
                    "chamber_id": chamber_id,
                    "recipe_group": "RTO_BASELINE",
                    "monitor_type": "Thickness",
                    "metric_name": "thickness_xbar",
                    "value": 100.0,
                    "ucl": 101.0 if tool_id == "RTO_A01" else 102.0,
                    "cl": 100.0 if tool_id == "RTO_A01" else 101.0,
                    "lcl": 99.0 if tool_id == "RTO_A01" else 100.0,
                    "warning_flag": False,
                    "ooc_flag": tool_id == "RTO_A02",
                    "rule_triggered": "THICKNESS_BEYOND_CONTROL_LIMIT" if tool_id == "RTO_A02" else None,
                    "severity": "High" if tool_id == "RTO_A02" else None,
                    "sequence_id": 1,
                }
            )
            rows.append(
                {
                    "timestamp": "2026-01-01",
                    "phase": "monitoring",
                    "tool_id": tool_id,
                    "chamber_id": chamber_id,
                    "recipe_group": "RTO_BASELINE",
                    "monitor_type": "Particle",
                    "metric_name": "particle_total_adder",
                    "value": 12.0,
                    "warning_flag": True,
                    "ooc_flag": False,
                    "rule_triggered": "PARTICLE_THRESHOLD_WARNING",
                    "severity": "Medium",
                    "sequence_id": 1,
                }
            )
    return pd.DataFrame(rows)


def _events() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "event_id": "EVT-000001",
                "timestamp": "2026-01-01",
                "tool_id": "RTO_A02",
                "chamber_id": "CH2",
                "recipe_group": "RTO_BASELINE",
                "monitor_type": "Thickness",
                "metric_name": "thickness_xbar",
                "value": 103.0,
                "ucl": 102.0,
                "cl": 101.0,
                "lcl": 100.0,
                "rule_triggered": "THICKNESS_BEYOND_CONTROL_LIMIT",
                "severity": "High",
            }
        ]
    )


def test_fleet_thickness_chart_includes_multiple_tools_and_chambers_without_shared_limits() -> None:
    fig = plot_fleet_thickness_trend(_spc_rows(), "thickness_xbar")
    legend_names = {trace.name for trace in fig.data if trace.name}
    assert any("RTO_01_Ch_A" in name for name in legend_names)
    assert any("RTO_02_Ch_B" in name for name in legend_names)
    assert len({tuple(trace.y) for trace in fig.data if "UCL" in str(trace.name)}) >= 2


def test_fleet_particle_chart_uses_threshold_logic_only() -> None:
    fig = plot_fleet_particle_trend(_spc_rows(), "particle_total_adder")
    annotation_text = " ".join(str(annotation.text) for annotation in fig.layout.annotations)
    assert "Warning" in annotation_text
    assert "High" in annotation_text


def test_fleet_excursion_charts_use_excursion_events() -> None:
    events = _events()
    count_fig = plot_fleet_event_count_bar(events, group_by="metric_name")
    timeline_fig = plot_fleet_excursion_timeline(events)
    assert len(count_fig.data) >= 1
    assert len(timeline_fig.data) >= 1
