from __future__ import annotations

import numpy as np
import pandas as pd

from rto_spc.config import (
    IMR_MOVING_RANGE_SIGMA_FACTOR,
    MIN_BASELINE_INDIVIDUAL_POINTS,
    MR_UCL_FACTOR,
    NONNEGATIVE_THICKNESS_METRICS,
    SPC_OOC_SIGMA_K,
)

GROUP_COLUMNS = ["tool_id", "chamber_id", "recipe_group", "metric_name"]
GOLDEN_REFERENCE_COLUMNS = ["chamber_id", "recipe_group", "metric_name"]
IMR_COLUMNS = [
    "baseline_mean",
    "baseline_sigma",
    "ucl",
    "cl",
    "lcl",
    "mr_value",
    "mr_ucl",
    "mr_cl",
    "mr_lcl",
]
THICKNESS_LIMIT_COLUMNS = [
    "baseline_mean",
    "baseline_sigma",
    "ucl",
    "cl",
    "lcl",
]


def calculate_baseline_limits_for_group(df_group: pd.DataFrame) -> dict[str, float]:
    """Calculate corrected Phase 1 baseline-only 3-sigma limits for one stream."""
    baseline = df_group[df_group["phase"] == "baseline"].sort_values(["timestamp", "sequence_id"])
    values = pd.to_numeric(baseline["value"], errors="coerce").dropna()
    baseline_mean = float(values.mean()) if not values.empty else np.nan
    baseline_sigma = float(values.std(ddof=1)) if len(values) >= 2 else np.nan
    if not np.isfinite(baseline_sigma) or baseline_sigma <= 0:
        return {
            "baseline_mean": baseline_mean,
            "baseline_sigma": baseline_sigma,
            "ucl": np.nan,
            "cl": baseline_mean,
            "lcl": np.nan,
        }

    metric_name = str(df_group["metric_name"].iloc[0]) if "metric_name" in df_group and not df_group.empty else ""
    lcl = baseline_mean - SPC_OOC_SIGMA_K * baseline_sigma
    if metric_name in NONNEGATIVE_THICKNESS_METRICS:
        lcl = max(0.0, lcl)
    return {
        "baseline_mean": baseline_mean,
        "baseline_sigma": baseline_sigma,
        "ucl": baseline_mean + SPC_OOC_SIGMA_K * baseline_sigma,
        "cl": baseline_mean,
        "lcl": lcl,
    }


def apply_baseline_thickness_limits(df: pd.DataFrame) -> pd.DataFrame:
    """Apply corrected Phase 1 baseline-only limits per tool/chamber/recipe/metric stream."""
    result = df.copy()
    for column in THICKNESS_LIMIT_COLUMNS:
        if column not in result.columns:
            result[column] = np.nan
    for column in ["mr_value", "mr_ucl", "mr_cl", "mr_lcl"]:
        if column not in result.columns:
            result[column] = np.nan

    thickness = result["monitor_type"] == "Thickness"
    for _, group in result[thickness].groupby(GROUP_COLUMNS, sort=False, dropna=False):
        ordered_index = group.sort_values(["timestamp", "sequence_id"]).index
        ordered_group = result.loc[ordered_index]
        limits = calculate_baseline_limits_for_group(ordered_group)
        for column, value in limits.items():
            result.loc[ordered_index, column] = value

    sort_columns = ["timestamp", "tool_id", "chamber_id", "recipe_group", "monitor_type", "metric_name", "sequence_id"]
    return result.sort_values(sort_columns).reset_index(drop=True)


def _unavailable_limits(values: pd.Series) -> dict[str, float]:
    baseline_mean = float(values.mean()) if not values.empty else np.nan
    baseline_sigma = float(values.std(ddof=1)) if len(values) >= 2 else np.nan
    return {
        "baseline_mean": baseline_mean,
        "baseline_sigma": baseline_sigma,
        "ucl": np.nan,
        "cl": baseline_mean,
        "lcl": np.nan,
        "mr_ucl": np.nan,
        "mr_cl": np.nan,
        "mr_lcl": np.nan,
    }


def calculate_imr_limits_for_group(df_group: pd.DataFrame) -> dict[str, float]:
    """Calculate baseline-only I-MR limits for one Thickness stream."""
    baseline = df_group[df_group["phase"] == "baseline"].sort_values(["timestamp", "sequence_id"])
    values = pd.to_numeric(baseline["value"], errors="coerce").dropna()

    if len(values) < MIN_BASELINE_INDIVIDUAL_POINTS:
        return _unavailable_limits(values)

    moving_ranges = values.diff().abs().dropna()
    mr_bar = float(moving_ranges.mean()) if not moving_ranges.empty else np.nan
    baseline_mean = float(values.mean())
    baseline_sigma = float(values.std(ddof=1))

    if not np.isfinite(mr_bar) or mr_bar <= 0:
        return _unavailable_limits(values)

    metric_name = str(df_group["metric_name"].iloc[0]) if "metric_name" in df_group and not df_group.empty else ""
    lcl = baseline_mean - IMR_MOVING_RANGE_SIGMA_FACTOR * mr_bar
    if metric_name in NONNEGATIVE_THICKNESS_METRICS:
        lcl = max(0.0, lcl)

    return {
        "baseline_mean": baseline_mean,
        "baseline_sigma": baseline_sigma,
        "ucl": baseline_mean + IMR_MOVING_RANGE_SIGMA_FACTOR * mr_bar,
        "cl": baseline_mean,
        "lcl": lcl,
        "mr_ucl": MR_UCL_FACTOR * mr_bar,
        "mr_cl": mr_bar,
        "mr_lcl": 0.0,
    }


def _reference_group_for_limits(result: pd.DataFrame, group: pd.DataFrame, golden_tool_id: str | None) -> pd.DataFrame:
    if golden_tool_id is None or group.empty:
        return group

    first = group.iloc[0]
    reference_mask = (result["monitor_type"] == "Thickness") & (result["tool_id"] == golden_tool_id)
    for column in GOLDEN_REFERENCE_COLUMNS:
        reference_mask &= result[column] == first[column]
    reference = result[reference_mask]
    return reference if not reference.empty else group


def apply_baseline_imr_limits(df: pd.DataFrame, *, golden_tool_id: str | None = None) -> pd.DataFrame:
    """Apply frozen baseline-only I-MR limits to Thickness rows."""
    result = df.copy()
    for column in IMR_COLUMNS:
        if column not in result.columns:
            result[column] = np.nan

    thickness = result["monitor_type"] == "Thickness"
    for _, group in result[thickness].groupby(GROUP_COLUMNS, sort=False, dropna=False):
        ordered_index = group.sort_values(["timestamp", "sequence_id"]).index
        ordered_group = result.loc[ordered_index]
        reference_group = _reference_group_for_limits(result, ordered_group, golden_tool_id)
        limits = calculate_imr_limits_for_group(reference_group)
        for column, value in limits.items():
            result.loc[ordered_index, column] = value

        values = pd.to_numeric(ordered_group["value"], errors="coerce")
        result.loc[ordered_index, "mr_value"] = values.diff().abs().to_numpy()

    sort_columns = ["timestamp", "tool_id", "chamber_id", "recipe_group", "monitor_type", "metric_name", "sequence_id"]
    return result.sort_values(sort_columns).reset_index(drop=True)
