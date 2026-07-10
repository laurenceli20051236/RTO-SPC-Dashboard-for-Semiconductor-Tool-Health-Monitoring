"""
Hierarchical synthetic data generator for RTO process monitoring.
Simulates the three real-fab variation levels: lot-to-lot, wafer-to-wafer,
and within-wafer (site-to-site).
"""
import numpy as np
from .wafer_map import generate_49site_pattern


def simulate_lot_history(
    n_lots=60,
    wafers_per_lot=5,
    sites_per_wafer=49,
    target=30.0,
    drift_per_lot=0.006,
    lot_to_lot_sigma=0.15,
    wafer_to_wafer_sigma=0.10,
    within_wafer_sigma=0.18,
    base_signature_strength=0.05,
    signature_growth=0.6,
    inject_excursion_at=None,
    excursion_magnitude=1.2,
    seed=None,
):
    """Returns (thickness_3d, sites_xy)."""
    if seed is not None:
        np.random.seed(seed)

    sites_xy = generate_49site_pattern()
    r = np.sqrt((sites_xy ** 2).sum(axis=1))
    r_norm = r / r.max()
    sig_template = 0.5 - r_norm ** 2

    lot_drift = np.arange(n_lots) * drift_per_lot
    lot_noise = np.random.randn(n_lots) * lot_to_lot_sigma
    lot_means = target + lot_drift + lot_noise

    if inject_excursion_at is not None:
        lot_means[inject_excursion_at] += excursion_magnitude

    wafer_noise = np.random.randn(n_lots, wafers_per_lot) * wafer_to_wafer_sigma

    thickness = np.zeros((n_lots, wafers_per_lot, sites_per_wafer))
    for lot in range(n_lots):
        sig_amp = base_signature_strength * (1 + signature_growth * lot / n_lots)
        signature = sig_amp * sig_template
        for w in range(wafers_per_lot):
            wafer_mean = lot_means[lot] + wafer_noise[lot, w]
            site_noise = np.random.randn(sites_per_wafer) * within_wafer_sigma
            thickness[lot, w] = wafer_mean + signature + site_noise

    return thickness, sites_xy


def aggregate_to_lot_subgroups(thickness_3d):
    """(n_lots, n_wafers, n_sites) -> (n_lots, n_wafers) of wafer means."""
    return thickness_3d.mean(axis=2)


def compute_wiw_trend(thickness_3d):
    """Per-lot WIW non-uniformity trend."""
    wafer_sigma = thickness_3d.std(axis=2, ddof=1)
    wafer_mean = thickness_3d.mean(axis=2)
    nu_per_wafer = wafer_sigma / wafer_mean * 100
    return {
        'NU_pct': nu_per_wafer.mean(axis=1),
        'sigma_A': wafer_sigma.mean(axis=1),
        'lot_mean': wafer_mean.mean(axis=1),
    }
