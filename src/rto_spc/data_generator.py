from __future__ import annotations

import hashlib
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from rto_spc.config import (
    CHAMBERS,
    PARTICLE_CLUSTER_ADDER,
    PARTICLE_LARGE_ADDER,
    PARTICLE_METRICS,
    PARTICLE_TOTAL_ADDER,
    RANDOM_SEED,
    RECIPE_GROUPS,
    THICKNESS_METRICS,
    THICKNESS_RTR_MEAN,
    THICKNESS_SIGMA,
    THICKNESS_WIW_STDEV,
    THICKNESS_XBAR,
    TOOLS,
    TRAILING_RTR_MEAN_WINDOW,
    TRAILING_RUN_SIGMA_WINDOW,
)

PRIMARY_THICKNESS_METRICS = THICKNESS_METRICS
INDIVIDUAL_THICKNESS_METRICS = [THICKNESS_RTR_MEAN, THICKNESS_SIGMA]
LEGACY_THICKNESS_METRICS = ["rtr_mean", "xbar", "wiw_stdev", "sigma", "thickness_mean"]
ALL_METRICS = PRIMARY_THICKNESS_METRICS + PARTICLE_METRICS


def _hash_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def _thickness_center(tool_id: str, chamber_id: str, recipe_group: str, metric_name: str) -> float:
    _ = tool_id
    chamber_offset = CHAMBERS.index(chamber_id) * 0.04
    recipe_offset = RECIPE_GROUPS.index(recipe_group) * 0.18
    if metric_name in {THICKNESS_RTR_MEAN, THICKNESS_XBAR, "rtr_mean", "xbar", "thickness_mean"}:
        return 100.0 + chamber_offset + recipe_offset
    if metric_name in {THICKNESS_WIW_STDEV, THICKNESS_SIGMA, "wiw_stdev", "sigma", "thickness_sigma"}:
        return 1.20 + chamber_offset * 0.05 + recipe_offset * 0.04
    raise ValueError(f"Unsupported thickness metric: {metric_name}")


def _stable_particle_value(rng: np.random.Generator, metric_name: str) -> float:
    if metric_name in {PARTICLE_TOTAL_ADDER, "total_adder"}:
        return float(rng.integers(0, 6))
    if metric_name in {PARTICLE_CLUSTER_ADDER, "cluster_adder"}:
        return float(rng.integers(0, 3))
    if metric_name in {PARTICLE_LARGE_ADDER, "large_particle_adder"}:
        return 0.0
    raise ValueError(f"Unsupported particle metric: {metric_name}")


def _stable_thickness_value(
    rng: np.random.Generator,
    *,
    center: float,
    metric_name: str,
    phase: str,
    sequence_id: int,
) -> float:
    if metric_name in {THICKNESS_RTR_MEAN, THICKNESS_XBAR, "rtr_mean", "xbar", "thickness_mean"}:
        if phase == "baseline":
            pattern = 0.06 if sequence_id % 2 else -0.06
            return float(center + pattern + rng.normal(0.0, 0.002))
        return float(center + 0.015 * np.sin(sequence_id / 4.0) + rng.normal(0.0, 0.001))

    if metric_name in {THICKNESS_WIW_STDEV, THICKNESS_SIGMA, "wiw_stdev", "sigma", "thickness_sigma"}:
        if phase == "baseline":
            pattern = 0.006 if sequence_id % 2 else -0.006
            return float(center + pattern + rng.normal(0.0, 0.0005))
        return float(center + 0.002 * np.sin(sequence_id / 4.0) + rng.normal(0.0, 0.0002))

    raise ValueError(f"Unsupported thickness metric: {metric_name}")


def _set_value(
    df: pd.DataFrame,
    *,
    tool_id: str,
    chamber_id: str,
    recipe_group: str,
    monitor_type: str,
    metric_name: str,
    sequence_id: int,
    value: float,
) -> None:
    mask = (
        (df["tool_id"] == tool_id)
        & (df["chamber_id"] == chamber_id)
        & (df["recipe_group"] == recipe_group)
        & (df["monitor_type"] == monitor_type)
        & (df["metric_name"] == metric_name)
        & (df["sequence_id"] == sequence_id)
    )
    df.loc[mask, "value"] = float(value)


def _rolling_mean(values: list[float], window: int) -> list[float]:
    series = pd.Series(values, dtype=float)
    return series.rolling(window=window, min_periods=1).mean().tolist()


def _rolling_sigma(values: list[float], window: int) -> list[float]:
    series = pd.Series(values, dtype=float)
    sigma = series.rolling(window=window, min_periods=2).std(ddof=1)
    fallback = float(sigma.dropna().median()) if sigma.notna().any() else 0.0
    return sigma.fillna(fallback).clip(lower=0.0).tolist()


def generate_monitor_measurements(seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Generate deterministic synthetic RTO monitor measurements."""
    rng = np.random.default_rng(seed)
    start = datetime(2026, 1, 1, 8, 0, 0)
    rows: list[dict[str, object]] = []

    for tool_id in TOOLS:
        for chamber_id in CHAMBERS:
            for recipe_group in RECIPE_GROUPS:
                mean_center = _thickness_center(tool_id, chamber_id, recipe_group, THICKNESS_XBAR)
                variation_center = _thickness_center(tool_id, chamber_id, recipe_group, THICKNESS_WIW_STDEV)
                run_means = [
                    _stable_thickness_value(
                        rng,
                        center=mean_center,
                        metric_name=THICKNESS_XBAR,
                        phase="baseline" if sequence_id <= 30 else "monitoring",
                        sequence_id=sequence_id,
                    )
                    for sequence_id in range(1, 61)
                ]
                wiw_stdevs = [
                    _stable_thickness_value(
                        rng,
                        center=variation_center,
                        metric_name=THICKNESS_WIW_STDEV,
                        phase="baseline" if sequence_id <= 30 else "monitoring",
                        sequence_id=sequence_id,
                    )
                    for sequence_id in range(1, 61)
                ]
                thickness_series = {
                    THICKNESS_RTR_MEAN: _rolling_mean(run_means, TRAILING_RTR_MEAN_WINDOW),
                    THICKNESS_XBAR: run_means,
                    THICKNESS_WIW_STDEV: wiw_stdevs,
                    THICKNESS_SIGMA: _rolling_sigma(run_means, TRAILING_RUN_SIGMA_WINDOW),
                }
                for metric_name, metric_values in thickness_series.items():
                    for i in range(60):
                        sequence_id = i + 1
                        phase = "baseline" if sequence_id <= 30 else "monitoring"
                        rows.append(
                            {
                                "timestamp": start + timedelta(days=i),
                                "phase": phase,
                                "tool_id": tool_id,
                                "chamber_id": chamber_id,
                                "recipe_group": recipe_group,
                                "monitor_type": "Thickness",
                                "metric_name": metric_name,
                                "value": float(metric_values[i]),
                                "unit": "nm",
                                "lot_id_hash": _hash_id("LOT", tool_id, chamber_id, recipe_group, sequence_id),
                                "monitor_wafer_id_hash": _hash_id("WFR", tool_id, chamber_id, recipe_group, sequence_id, metric_name),
                                "measurement_id": _hash_id("MEA", tool_id, chamber_id, recipe_group, metric_name, sequence_id),
                                "sequence_id": sequence_id,
                            }
                        )

                for metric_name in PARTICLE_METRICS:
                    for i in range(60):
                        sequence_id = i + 1
                        phase = "baseline" if sequence_id <= 30 else "monitoring"
                        rows.append(
                            {
                                "timestamp": start + timedelta(days=i),
                                "phase": phase,
                                "tool_id": tool_id,
                                "chamber_id": chamber_id,
                                "recipe_group": recipe_group,
                                "monitor_type": "Particle",
                                "metric_name": metric_name,
                                "value": _stable_particle_value(rng, metric_name),
                                "unit": "count",
                                "lot_id_hash": _hash_id("LOT", tool_id, chamber_id, recipe_group, sequence_id),
                                "monitor_wafer_id_hash": _hash_id("WFR", tool_id, chamber_id, recipe_group, sequence_id, metric_name),
                                "measurement_id": _hash_id("MEA", tool_id, chamber_id, recipe_group, metric_name, sequence_id),
                                "sequence_id": sequence_id,
                            }
                        )

    df = pd.DataFrame(rows)

    _set_value(
        df,
        tool_id="RTO_A01",
        chamber_id="CH1",
        recipe_group="RTO_OXIDE_A",
        monitor_type="Thickness",
        metric_name=THICKNESS_RTR_MEAN,
        sequence_id=45,
        value=_thickness_center("RTO_A01", "CH1", "RTO_OXIDE_A", THICKNESS_RTR_MEAN) + 0.80,
    )
    _set_value(
        df,
        tool_id="RTO_A03",
        chamber_id="CH1",
        recipe_group="RTO_OXIDE_A",
        monitor_type="Thickness",
        metric_name=THICKNESS_XBAR,
        sequence_id=44,
        value=_thickness_center("RTO_A03", "CH1", "RTO_OXIDE_A", THICKNESS_XBAR) + 0.80,
    )
    _set_value(
        df,
        tool_id="RTO_A04",
        chamber_id="CH2",
        recipe_group="RTO_BASELINE",
        monitor_type="Thickness",
        metric_name=THICKNESS_WIW_STDEV,
        sequence_id=48,
        value=_thickness_center("RTO_A04", "CH2", "RTO_BASELINE", THICKNESS_WIW_STDEV) + 0.050,
    )

    injected_particle_events = [
        ("RTO_A01", "CH1", "RTO_OXIDE_A", PARTICLE_TOTAL_ADDER, 37, 12),
        ("RTO_A01", "CH1", "RTO_OXIDE_A", PARTICLE_TOTAL_ADDER, 52, 24),
        ("RTO_A02", "CH1", "RTO_OXIDE_A", PARTICLE_CLUSTER_ADDER, 38, 4),
        ("RTO_A02", "CH1", "RTO_OXIDE_A", PARTICLE_CLUSTER_ADDER, 53, 7),
        ("RTO_A03", "CH1", "RTO_OXIDE_A", PARTICLE_LARGE_ADDER, 39, 1),
        ("RTO_A03", "CH1", "RTO_OXIDE_A", PARTICLE_LARGE_ADDER, 54, 4),
        ("RTO_A04", "CH2", "RTO_OXIDE_A", PARTICLE_TOTAL_ADDER, 42, 11),
        ("RTO_A04", "CH2", "RTO_OXIDE_A", PARTICLE_TOTAL_ADDER, 46, 12),
        ("RTO_A04", "CH2", "RTO_OXIDE_A", PARTICLE_TOTAL_ADDER, 49, 13),
    ]
    injected_particle_events.extend(
        ("RTO_A04", "CH1", "RTO_BASELINE", PARTICLE_TOTAL_ADDER, sequence_id, 24)
        for sequence_id in range(50, 61)
    )
    injected_particle_events.extend(
        [
            ("RTO_A04", "CH1", "RTO_BASELINE", PARTICLE_CLUSTER_ADDER, 35, 4),
            ("RTO_A04", "CH1", "RTO_OXIDE_A", PARTICLE_CLUSTER_ADDER, 36, 4),
            ("RTO_A04", "CH2", "RTO_BASELINE", PARTICLE_CLUSTER_ADDER, 37, 4),
            ("RTO_A04", "CH2", "RTO_BASELINE", PARTICLE_LARGE_ADDER, 38, 1),
        ]
    )
    for tool_id, chamber_id, recipe_group, metric_name, sequence_id, value in injected_particle_events:
        _set_value(
            df,
            tool_id=tool_id,
            chamber_id=chamber_id,
            recipe_group=recipe_group,
            monitor_type="Particle",
            metric_name=metric_name,
            sequence_id=sequence_id,
            value=float(value),
        )

    sort_columns = ["timestamp", "tool_id", "chamber_id", "recipe_group", "monitor_type", "metric_name", "sequence_id"]
    return df.sort_values(sort_columns).reset_index(drop=True)
