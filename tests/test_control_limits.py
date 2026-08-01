from __future__ import annotations

import numpy as np
import pandas as pd

from rto_spc.control_limits import apply_baseline_imr_limits, calculate_imr_limits_for_group


def _thickness_rows(
    *,
    tool_id: str = "RTO_A01",
    chamber_id: str = "CH1",
    recipe_group: str = "RTO_BASELINE",
    metric_name: str = "thickness_mean",
    baseline_values: list[float] | None = None,
    monitoring_values: list[float] | None = None,
) -> pd.DataFrame:
    baseline_values = baseline_values or [10, 11] * 10
    monitoring_values = monitoring_values or [10.5, 10.6]
    rows = []
    for i, value in enumerate(baseline_values + monitoring_values, start=1):
        rows.append(
            {
                "timestamp": pd.Timestamp("2026-01-01") + pd.Timedelta(days=i),
                "phase": "baseline" if i <= len(baseline_values) else "monitoring",
                "tool_id": tool_id,
                "chamber_id": chamber_id,
                "recipe_group": recipe_group,
                "monitor_type": "Thickness",
                "metric_name": metric_name,
                "value": value,
                "unit": "nm",
                "lot_id_hash": f"LOT_{i}",
                "monitor_wafer_id_hash": f"WFR_{i}",
                "sequence_id": i,
            }
        )
    return pd.DataFrame(rows)


def test_imr_limits_use_baseline_only() -> None:
    df = _thickness_rows(monitoring_values=[1000])
    limits = calculate_imr_limits_for_group(df)
    assert np.isclose(limits["baseline_mean"], 10.5)
    assert np.isclose(limits["ucl"], 13.16)
    assert np.isclose(limits["lcl"], 7.84)


def test_monitoring_excursion_does_not_change_baseline_limits() -> None:
    stable = _thickness_rows(monitoring_values=[10.5])
    excursion = _thickness_rows(monitoring_values=[1000])
    assert calculate_imr_limits_for_group(stable)["ucl"] == calculate_imr_limits_for_group(excursion)["ucl"]


def test_grouping_does_not_mix_tools() -> None:
    df = pd.concat(
        [
            _thickness_rows(tool_id="RTO_A01", baseline_values=[10, 11] * 10),
            _thickness_rows(tool_id="RTO_A02", baseline_values=[50, 51] * 10),
        ],
        ignore_index=True,
    )
    result = apply_baseline_imr_limits(df)
    assert result[result["tool_id"] == "RTO_A01"]["cl"].iloc[0] == 10.5
    assert result[result["tool_id"] == "RTO_A02"]["cl"].iloc[0] == 50.5


def test_golden_tool_baseline_can_be_applied_to_matching_tools() -> None:
    df = pd.concat(
        [
            _thickness_rows(tool_id="RTO_A01", baseline_values=[10, 11] * 10),
            _thickness_rows(tool_id="RTO_A02", baseline_values=[50, 51] * 10),
        ],
        ignore_index=True,
    )
    result = apply_baseline_imr_limits(df, golden_tool_id="RTO_A01")
    assert result[result["tool_id"] == "RTO_A01"]["cl"].iloc[0] == 10.5
    assert result[result["tool_id"] == "RTO_A02"]["cl"].iloc[0] == 10.5


def test_grouping_does_not_mix_chambers() -> None:
    df = pd.concat(
        [
            _thickness_rows(chamber_id="CH1", baseline_values=[10, 11] * 10),
            _thickness_rows(chamber_id="CH2", baseline_values=[20, 21] * 10),
        ],
        ignore_index=True,
    )
    result = apply_baseline_imr_limits(df)
    assert result[result["chamber_id"] == "CH1"]["cl"].iloc[0] == 10.5
    assert result[result["chamber_id"] == "CH2"]["cl"].iloc[0] == 20.5


def test_grouping_does_not_mix_recipes() -> None:
    df = pd.concat(
        [
            _thickness_rows(recipe_group="RTO_BASELINE", baseline_values=[10, 11] * 10),
            _thickness_rows(recipe_group="RTO_OXIDE_A", baseline_values=[30, 31] * 10),
        ],
        ignore_index=True,
    )
    result = apply_baseline_imr_limits(df)
    assert result[result["recipe_group"] == "RTO_BASELINE"]["cl"].iloc[0] == 10.5
    assert result[result["recipe_group"] == "RTO_OXIDE_A"]["cl"].iloc[0] == 30.5


def test_grouping_does_not_mix_metrics() -> None:
    df = pd.concat(
        [
            _thickness_rows(metric_name="thickness_mean", baseline_values=[10, 11] * 10),
            _thickness_rows(metric_name="thickness_sigma", baseline_values=[1, 2] * 10),
        ],
        ignore_index=True,
    )
    result = apply_baseline_imr_limits(df)
    assert result[result["metric_name"] == "thickness_mean"]["cl"].iloc[0] == 10.5
    assert result[result["metric_name"] == "thickness_sigma"]["cl"].iloc[0] == 1.5


def test_constant_baseline_does_not_crash() -> None:
    result = apply_baseline_imr_limits(_thickness_rows(baseline_values=[10] * 20))
    assert result["ucl"].isna().all()


def test_insufficient_baseline_does_not_crash() -> None:
    result = apply_baseline_imr_limits(_thickness_rows(baseline_values=[10, 11] * 9 + [10]))
    assert result["ucl"].isna().all()
