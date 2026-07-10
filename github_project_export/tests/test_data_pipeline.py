from __future__ import annotations

import pandas as pd

from rto_spc.data_pipeline import generate_all_sample_data


def test_generate_all_sample_data_returns_all_outputs(tmp_path) -> None:
    outputs = generate_all_sample_data(output_dir=tmp_path, seed=42)
    assert set(outputs) == {
        "monitor_measurements",
        "spc_results",
        "excursion_events",
    }
    assert all(path.exists() for path in outputs.values())


def test_generated_data_contains_primary_thickness_metrics(tmp_path) -> None:
    outputs = generate_all_sample_data(output_dir=tmp_path, seed=42)

    measurements = pd.read_csv(outputs["monitor_measurements"])
    thickness_metrics = set(measurements[measurements["monitor_type"] == "Thickness"]["metric_name"])
    assert {"thickness_rtr_mean", "thickness_xbar", "thickness_wiw_stdev", "thickness_sigma"}.issubset(thickness_metrics)

    events = pd.read_csv(outputs["excursion_events"])
    event_metrics = set(events[events["monitor_type"] == "Thickness"]["metric_name"])
    assert {"thickness_rtr_mean", "thickness_xbar", "thickness_wiw_stdev", "thickness_sigma"}.issubset(event_metrics)


def test_generated_thickness_limits_are_per_stream(tmp_path) -> None:
    outputs = generate_all_sample_data(output_dir=tmp_path, seed=42)

    spc = pd.read_csv(outputs["spc_results"])
    thickness = spc[spc["monitor_type"] == "Thickness"]
    limit_counts = thickness.groupby(["tool_id", "chamber_id", "recipe_group", "metric_name"])[["cl", "ucl", "lcl"]].nunique(dropna=True)
    assert int(limit_counts.max().max()) == 1
    stream_limits = thickness.drop_duplicates(["tool_id", "chamber_id", "recipe_group", "metric_name"])[
        ["tool_id", "chamber_id", "recipe_group", "metric_name", "cl"]
    ]
    xbar_limits = stream_limits[stream_limits["metric_name"] == "thickness_xbar"]
    assert xbar_limits["cl"].nunique() > 1


def test_generated_data_has_measurement_traceability(tmp_path) -> None:
    outputs = generate_all_sample_data(output_dir=tmp_path, seed=42)

    measurements = pd.read_csv(outputs["monitor_measurements"])
    spc = pd.read_csv(outputs["spc_results"])
    events = pd.read_csv(outputs["excursion_events"])

    assert measurements["measurement_id"].notna().all()
    assert spc["measurement_id"].notna().all()
    traced_events = events[events["measurement_id"].notna()]
    assert not traced_events.empty
    source_ids = set(spc["measurement_id"])
    assert set(traced_events["measurement_id"]).issubset(source_ids)
