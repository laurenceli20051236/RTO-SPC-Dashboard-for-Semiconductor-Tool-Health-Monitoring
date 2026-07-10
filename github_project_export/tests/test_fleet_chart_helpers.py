from __future__ import annotations

import pandas as pd

from rto_spc.chart_helpers import (
    plot_fleet_event_count_bar,
    plot_fleet_excursion_timeline,
    plot_fleet_particle_trend,
    plot_fleet_thickness_trend,
)
from rto_spc.data_pipeline import generate_all_sample_data
from rto_spc.particle_rules import PARTICLE_REPEATED_EVENT_ESCALATION


def _fleet_thickness_rows() -> pd.DataFrame:
    rows = []
    for tool_id, chamber_id, ucl in [("RTO_A01", "CH1", 101.0), ("RTO_A02", "CH2", 202.0)]:
        for sequence_id in [1, 2]:
            rows.append(
                {
                    "timestamp": pd.Timestamp("2026-01-01") + pd.Timedelta(days=(sequence_id - 1) * 7),
                    "phase": "monitoring",
                    "tool_id": tool_id,
                    "chamber_id": chamber_id,
                    "recipe_group": "RTO_BASELINE",
                    "monitor_type": "Thickness",
                    "metric_name": "rtr_mean",
                    "value": ucl - 1.0 + sequence_id * 0.01,
                    "ucl": ucl,
                    "cl": ucl - 1.0,
                    "lcl": ucl - 2.0,
                    "warning_flag": sequence_id == 1 and tool_id == "RTO_A01",
                    "ooc_flag": sequence_id == 2 and tool_id == "RTO_A02",
                    "rule_triggered": "THICKNESS_IMR_BEYOND_LIMIT" if sequence_id == 2 and tool_id == "RTO_A02" else "",
                }
            )
    return pd.DataFrame(rows)


def test_fleet_thickness_chart_includes_multiple_tools_chambers_and_stream_limits() -> None:
    fig = plot_fleet_thickness_trend(_fleet_thickness_rows(), "rtr_mean")

    trace_names = " ".join(str(trace.name) for trace in fig.data)
    assert "RTO_01_Ch_A" in trace_names
    assert "RTO_02_Ch_B" in trace_names

    ucl_traces = [trace for trace in fig.data if str(trace.name).endswith(" UCL")]
    ucl_values = {tuple(float(value) for value in trace.y) for trace in ucl_traces}
    assert (101.0, 101.0) in ucl_values
    assert (202.0, 202.0) in ucl_values

    assert tuple(fig.layout.xaxis.tickvals) == tuple(range(1, 15))
    assert tuple(fig.layout.xaxis.ticktext) == tuple(f"W{week:02d}" for week in range(1, 15))
    assert all("RTO_BASELINE" not in str(trace.name) for trace in fig.data)
    limit_annotations = [
        annotation.text
        for annotation in fig.layout.annotations
        if str(annotation.text).startswith("<b>") and any(label in str(annotation.text) for label in ["UCL", "CL", "LCL"])
    ]
    assert len(limit_annotations) == 6


def test_fleet_thickness_chart_uses_precomputed_event_flags() -> None:
    fig = plot_fleet_thickness_trend(_fleet_thickness_rows(), "rtr_mean")
    event_point_count = sum(len(trace.x) for trace in fig.data if "Events" in str(trace.name))
    assert event_point_count == 2


def test_fleet_thickness_chart_limits_overlay_to_first_14_weekly_pm_points() -> None:
    rows = []
    for week_index in range(1, 19):
        rows.append(
            {
                "timestamp": pd.Timestamp("2026-01-01") + pd.Timedelta(days=(week_index - 1) * 7),
                "phase": "monitoring",
                "tool_id": "RTO_A01",
                "chamber_id": "CH1",
                "recipe_group": "RTO_BASELINE",
                "monitor_type": "Thickness",
                "metric_name": "rtr_mean",
                "value": 100.0 + week_index * 0.01,
                "ucl": 101.0,
                "cl": 100.0,
                "lcl": 99.0,
                "warning_flag": False,
                "ooc_flag": False,
                "rule_triggered": "",
            }
        )

    fig = plot_fleet_thickness_trend(pd.DataFrame(rows), "rtr_mean")
    primary_trace = next(trace for trace in fig.data if str(trace.name) == "A RTO_01_Ch_A")
    assert tuple(primary_trace.x) == tuple(range(1, 15))


def test_fleet_thickness_chart_labels_same_tool_chamber_overlay() -> None:
    rows = []
    for chamber_id, value_offset in [("CH1", 0.0), ("CH2", 0.2)]:
        for week_index in range(1, 3):
            rows.append(
                {
                    "timestamp": pd.Timestamp("2026-01-01") + pd.Timedelta(days=(week_index - 1) * 7),
                    "phase": "monitoring",
                    "tool_id": "RTO_A01",
                    "chamber_id": chamber_id,
                    "recipe_group": "RTO_BASELINE",
                    "monitor_type": "Thickness",
                    "metric_name": "rtr_mean",
                    "value": 100.0 + value_offset + week_index * 0.01,
                    "ucl": 101.0 + value_offset,
                    "cl": 100.0 + value_offset,
                    "lcl": 99.0 + value_offset,
                    "warning_flag": False,
                    "ooc_flag": False,
                    "rule_triggered": "",
                }
            )

    fig = plot_fleet_thickness_trend(pd.DataFrame(rows), "rtr_mean")
    trace_names = " ".join(str(trace.name) for trace in fig.data)

    assert "RTO_01_Ch_A" in trace_names
    assert "RTO_01_Ch_B" in trace_names


def test_fleet_particle_chart_uses_threshold_logic_only() -> None:
    rows = []
    for tool_id, chamber_id, severity, rule, value in [
        ("RTO_A01", "CH1", "Medium", "PARTICLE_THRESHOLD_WARNING", 12),
        ("RTO_A02", "CH2", "High", PARTICLE_REPEATED_EVENT_ESCALATION, 24),
    ]:
        rows.append(
            {
                "timestamp": pd.Timestamp("2026-01-01"),
                "tool_id": tool_id,
                "chamber_id": chamber_id,
                "recipe_group": "RTO_BASELINE",
                "monitor_type": "Particle",
                "metric_name": "total_adder",
                "value": value,
                "severity": severity,
                "rule_triggered": rule,
            }
        )
    fig = plot_fleet_particle_trend(pd.DataFrame(rows), "total_adder")

    names = " ".join(str(trace.name) for trace in fig.data)
    assert "RTO_01_Ch_A" in names
    assert "RTO_02_Ch_B" in names
    assert "Medium" in names
    assert "High" in names
    assert "Repeated escalation" in names
    assert len(fig.layout.shapes) == 2
    assert not any("UCL" in str(trace.name) or "LCL" in str(trace.name) for trace in fig.data)


def test_fleet_event_count_chart_uses_excursion_events_csv(tmp_path) -> None:
    outputs = generate_all_sample_data(output_dir=tmp_path, seed=42)
    events = pd.read_csv(outputs["excursion_events"])

    fig = plot_fleet_event_count_bar(events, group_by="metric_name")
    chart_counts = dict(zip(fig.data[0].x, fig.data[0].y))
    expected_counts = events["metric_name"].value_counts().to_dict()
    assert chart_counts == expected_counts

    timeline = plot_fleet_excursion_timeline(events)
    assert len(timeline.data) > 0
