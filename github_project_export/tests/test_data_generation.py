from __future__ import annotations

import pandas as pd

from rto_spc.data_pipeline import generate_all_sample_data


def test_sample_data_script_outputs_corrected_phase1_csvs(tmp_path) -> None:
    outputs = generate_all_sample_data(output_dir=tmp_path, seed=42)
    assert outputs["monitor_measurements"].exists()
    assert outputs["spc_results"].exists()
    assert outputs["excursion_events"].exists()


def test_sample_data_contains_required_corrected_phase1_metrics(tmp_path) -> None:
    outputs = generate_all_sample_data(output_dir=tmp_path, seed=42)
    measurements = pd.read_csv(outputs["monitor_measurements"])

    assert {"baseline", "monitoring"}.issubset(set(measurements["phase"]))
    assert {
        "thickness_rtr_mean",
        "thickness_xbar",
        "thickness_wiw_stdev",
        "thickness_sigma",
        "particle_total_adder",
        "particle_cluster_adder",
        "particle_large_adder",
    }.issubset(set(measurements["metric_name"]))
