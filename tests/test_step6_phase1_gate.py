from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from rto_spc.config import CHAMBERS, PARTICLE_METRICS, RECIPE_GROUPS, THICKNESS_METRICS, TOOLS
from rto_spc.control_limits import apply_baseline_thickness_limits
from rto_spc.data_pipeline import generate_all_sample_data


ROOT_DIR = Path(__file__).resolve().parents[1]

REQUIRED_MEASUREMENT_COLUMNS = {
    "timestamp",
    "phase",
    "tool_id",
    "chamber_id",
    "recipe_group",
    "monitor_type",
    "metric_name",
    "value",
    "unit",
    "lot_id_hash",
    "monitor_wafer_id_hash",
    "sequence_id",
}
REQUIRED_SPC_COLUMNS = REQUIRED_MEASUREMENT_COLUMNS | {
    "baseline_mean",
    "baseline_sigma",
    "ucl",
    "cl",
    "lcl",
    "warning_flag",
    "ooc_flag",
    "rule_triggered",
    "severity",
}
REQUIRED_EVENT_COLUMNS = {
    "event_id",
    "timestamp",
    "tool_id",
    "chamber_id",
    "recipe_group",
    "monitor_type",
    "metric_name",
    "value",
    "ucl",
    "cl",
    "lcl",
    "rule_triggered",
    "severity",
    "suggested_review_area",
    "status",
    "comment",
}


def test_step6_generates_only_required_phase1_outputs(tmp_path: Path) -> None:
    outputs = generate_all_sample_data(output_dir=tmp_path, seed=42)
    assert set(outputs) == {"monitor_measurements", "spc_results", "excursion_events"}
    for path in outputs.values():
        assert path.exists()
        assert not pd.read_csv(path).empty


def test_step6_monitor_measurements_contract(tmp_path: Path) -> None:
    outputs = generate_all_sample_data(output_dir=tmp_path, seed=42)
    measurements = pd.read_csv(outputs["monitor_measurements"])

    assert REQUIRED_MEASUREMENT_COLUMNS.issubset(measurements.columns)
    assert {"baseline", "monitoring"}.issubset(set(measurements["phase"]))
    assert set(TOOLS).issubset(set(measurements["tool_id"]))
    assert set(CHAMBERS).issubset(set(measurements["chamber_id"]))
    assert set(THICKNESS_METRICS + PARTICLE_METRICS).issubset(set(measurements["metric_name"]))


def test_step6_spc_results_contract_and_event_persistence(tmp_path: Path) -> None:
    outputs = generate_all_sample_data(output_dir=tmp_path, seed=42)
    spc = pd.read_csv(outputs["spc_results"])
    events = pd.read_csv(outputs["excursion_events"])

    assert REQUIRED_SPC_COLUMNS.issubset(spc.columns)
    assert REQUIRED_EVENT_COLUMNS.issubset(events.columns)

    thickness = spc[spc["monitor_type"] == "Thickness"]
    assert thickness[["baseline_mean", "baseline_sigma", "ucl", "cl", "lcl"]].notna().all().all()
    assert spc[["warning_flag", "ooc_flag"]].notna().all().all()

    flagged = spc[spc["warning_flag"].astype(bool) | spc["ooc_flag"].astype(bool)]
    assert not flagged.empty
    assert flagged["rule_triggered"].notna().all()
    assert flagged["severity"].notna().all()
    assert len(events) == len(flagged)
    assert events["suggested_review_area"].notna().all()
    assert set(events["status"]) == {"Open"}
    assert events["comment"].notna().all()
    assert events["event_id"].tolist() == [f"EVT-{i:06d}" for i in range(1, len(events) + 1)]


def test_step6_limits_are_baseline_only_and_per_stream(tmp_path: Path) -> None:
    outputs = generate_all_sample_data(output_dir=tmp_path, seed=42)
    spc = pd.read_csv(outputs["spc_results"])
    thickness = spc[spc["monitor_type"] == "Thickness"]

    for key, group in thickness.groupby(["tool_id", "chamber_id", "recipe_group", "metric_name"], dropna=False):
        baseline = group[group["phase"] == "baseline"]["value"]
        expected_mean = baseline.mean()
        expected_sigma = baseline.std(ddof=1)
        expected_ucl = expected_mean + 3 * expected_sigma
        expected_lcl = expected_mean - 3 * expected_sigma
        if key[3] in {"thickness_wiw_stdev", "thickness_sigma"}:
            expected_lcl = max(0.0, expected_lcl)

        for column, expected in {
            "baseline_mean": expected_mean,
            "baseline_sigma": expected_sigma,
            "ucl": expected_ucl,
            "cl": expected_mean,
            "lcl": expected_lcl,
        }.items():
            assert np.allclose(group[column].astype(float), expected, rtol=1e-9, atol=1e-9)

    limits = thickness.drop_duplicates(["tool_id", "chamber_id", "recipe_group", "metric_name"])
    a01 = limits[(limits["tool_id"] == "RTO_A01") & (limits["metric_name"] == "thickness_xbar")]["cl"].iloc[0]
    a02 = limits[(limits["tool_id"] == "RTO_A02") & (limits["metric_name"] == "thickness_xbar")]["cl"].iloc[0]
    ch1 = limits[(limits["chamber_id"] == "CH1") & (limits["metric_name"] == "thickness_xbar")]["cl"].iloc[0]
    ch2 = limits[(limits["chamber_id"] == "CH2") & (limits["metric_name"] == "thickness_xbar")]["cl"].iloc[0]
    base = limits[(limits["recipe_group"] == "RTO_BASELINE") & (limits["metric_name"] == "thickness_xbar")]["cl"].iloc[0]
    oxide = limits[(limits["recipe_group"] == "RTO_OXIDE_A") & (limits["metric_name"] == "thickness_xbar")]["cl"].iloc[0]
    xbar = limits[limits["metric_name"] == "thickness_xbar"]["cl"].iloc[0]
    sigma = limits[limits["metric_name"] == "thickness_sigma"]["cl"].iloc[0]

    assert a01 != a02
    assert ch1 != ch2
    assert base != oxide
    assert xbar != sigma


def test_step6_control_limit_calculation_ignores_monitoring_extremes() -> None:
    rows = []
    for phase, values in [("baseline", [10.0, 11.0, 12.0, 13.0]), ("monitoring", [1000.0, -1000.0])]:
        for sequence_id, value in enumerate(values, start=1 if phase == "baseline" else 5):
            rows.append(
                {
                    "timestamp": pd.Timestamp("2026-01-01") + pd.Timedelta(days=sequence_id),
                    "phase": phase,
                    "tool_id": "RTO_A01",
                    "chamber_id": "CH1",
                    "recipe_group": "RTO_BASELINE",
                    "monitor_type": "Thickness",
                    "metric_name": "thickness_xbar",
                    "value": value,
                    "sequence_id": sequence_id,
                }
            )
    result = apply_baseline_thickness_limits(pd.DataFrame(rows))
    baseline = pd.Series([10.0, 11.0, 12.0, 13.0])
    assert np.allclose(result["baseline_mean"], baseline.mean())
    assert np.allclose(result["baseline_sigma"], baseline.std(ddof=1))


def test_step6_required_pages_exist_and_forbidden_pages_absent() -> None:
    pages = ROOT_DIR / "app" / "pages"
    required = {
        "1_Tool_Health_Summary.py",
        "2_Thickness_Monitor.py",
        "3_Particle_Alerts.py",
        "4_Excursion_Review.py",
        "5_Local_Event_Summary.py",
    }
    assert required.issubset({path.name for path in pages.glob("*.py")})
    assert not (pages / "2_Thickness_IMR.py").exists()
    assert not any(path.name.endswith(("Thickness_Xbar_S.py", "Particle_Count_SPC.py")) for path in pages.glob("*.py"))


def test_step6_readme_disclaimer_and_phase1_claims() -> None:
    text = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
    assert "This is an RTO-only synthetic dashboard." in text
    assert "Thickness Phase 1 uses RTR Mean, X-BAR, WIW Stdev, and SIGMA." in text
    assert "Particle Phase 1 uses Total Adder, Cluster Adder, and Large Adder threshold + repeated-event alerts." in text
    assert "Limits are calculated from baseline data only." in text
    assert "Fleet charts are visualization-only and do not calculate shared SPC limits." in text
    assert "All alerts are persisted to excursion_events.csv." in text
    assert (
        "This project uses fully synthetic and anonymized semiconductor monitor data for public portfolio demonstration only. "
        "It does not contain real tool identifiers, real recipe names, real product information, real wafer records, real lot records, "
        "real process limits, real SPC limits, or any confidential manufacturing information."
    ) in text
