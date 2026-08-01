"""
Oxide thickness SPC module: X-bar and S charts with Western Electric rules,
plus full monitoring dashboard.
"""
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass

SHEWHART = {
    2:  {'A3': 2.659, 'B3': 0,     'B4': 3.267, 'c4': 0.7979},
    3:  {'A3': 1.954, 'B3': 0,     'B4': 2.568, 'c4': 0.8862},
    4:  {'A3': 1.628, 'B3': 0,     'B4': 2.266, 'c4': 0.9213},
    5:  {'A3': 1.427, 'B3': 0,     'B4': 2.089, 'c4': 0.9400},
    6:  {'A3': 1.287, 'B3': 0.030, 'B4': 1.970, 'c4': 0.9515},
    7:  {'A3': 1.182, 'B3': 0.118, 'B4': 1.882, 'c4': 0.9594},
    8:  {'A3': 1.099, 'B3': 0.185, 'B4': 1.815, 'c4': 0.9650},
    9:  {'A3': 1.032, 'B3': 0.239, 'B4': 1.761, 'c4': 0.9693},
    10: {'A3': 0.975, 'B3': 0.284, 'B4': 1.716, 'c4': 0.9727},
}


@dataclass
class SPCResult:
    xbar: np.ndarray
    s: np.ndarray
    X_bar_bar: float
    S_bar: float
    UCL_X: float
    LCL_X: float
    UCL_S: float
    LCL_S: float
    sigma_hat: float
    quality_margin_index: float
    violations: list


def compute_xbar_s(subgroups, USL=None, LSL=None):
    n = subgroups.shape[1]
    c = SHEWHART[n]
    xbar = subgroups.mean(axis=1)
    s = subgroups.std(axis=1, ddof=1)
    X_bar_bar, S_bar = xbar.mean(), s.mean()
    sigma_hat = S_bar / c['c4']
    UCL_X = X_bar_bar + c['A3'] * S_bar
    LCL_X = X_bar_bar - c['A3'] * S_bar
    UCL_S = c['B4'] * S_bar
    LCL_S = c['B3'] * S_bar
    quality_margin_index = None
    if USL is not None and LSL is not None:
        quality_margin_index = min(USL - X_bar_bar, X_bar_bar - LSL) / (3 * sigma_hat)
    return SPCResult(
        xbar=xbar, s=s, X_bar_bar=X_bar_bar, S_bar=S_bar,
        UCL_X=UCL_X, LCL_X=LCL_X, UCL_S=UCL_S, LCL_S=LCL_S,
        sigma_hat=sigma_hat, quality_margin_index=quality_margin_index,
        violations=western_electric(xbar, X_bar_bar, UCL_X, LCL_X),
    )


def western_electric(data, center, ucl, lcl):
    """Rules 1-4 violations: (index, rule_id, description)."""
    sigma = (ucl - center) / 3
    v = []
    for i, x in enumerate(data):
        if x > ucl or x < lcl:
            v.append((i, 1, 'Beyond 3 sigma'))
    for i in range(2, len(data)):
        w = data[i - 2:i + 1]
        if sum(1 for x in w if x > center + 2 * sigma) >= 2:
            v.append((i, 2, '2 of 3 beyond 2 sigma (high)'))
        if sum(1 for x in w if x < center - 2 * sigma) >= 2:
            v.append((i, 2, '2 of 3 beyond 2 sigma (low)'))
    for i in range(4, len(data)):
        w = data[i - 4:i + 1]
        if sum(1 for x in w if x > center + sigma) >= 4:
            v.append((i, 3, '4 of 5 beyond 1 sigma (high)'))
        if sum(1 for x in w if x < center - sigma) >= 4:
            v.append((i, 3, '4 of 5 beyond 1 sigma (low)'))
    for i in range(7, len(data)):
        seg = data[i - 7:i + 1]
        if all(x > center for x in seg) or all(x < center for x in seg):
            v.append((i, 4, '8 consecutive same side'))
    return v


def plot_xbar_s(result, target=None, USL=None, LSL=None, save_path=None):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    idx = np.arange(len(result.xbar))

    ax1.plot(idx, result.xbar, 'bo-', ms=4, lw=1)
    ax1.axhline(result.X_bar_bar, c='g', lw=1.5, label=f'X-barbar={result.X_bar_bar:.2f}A')
    ax1.axhline(result.UCL_X, c='r', ls='--', label=f'UCL={result.UCL_X:.2f}A')
    ax1.axhline(result.LCL_X, c='r', ls='--', label=f'LCL={result.LCL_X:.2f}A')
    if target:
        ax1.axhline(target, c='k', ls=':', label=f'Target={target}A')
    if USL:
        ax1.axhline(USL, c='orange', ls='-.', alpha=0.6, label=f'USL={USL}A')
    if LSL:
        ax1.axhline(LSL, c='orange', ls='-.', alpha=0.6, label=f'LSL={LSL}A')

    for i, rule, _ in result.violations:
        ax1.plot(i, result.xbar[i], 'rs', ms=12, mfc='none', mew=2)

    title = 'X-bar Chart: Gate Oxide Thickness (RTO)'
    if result.quality_margin_index:
        title += f'  |  Margin index = {result.quality_margin_index:.2f}'
    ax1.set_title(title)
    ax1.set_ylabel('Mean Tox (A)')
    ax1.legend(loc='best', fontsize=9)
    ax1.grid(alpha=0.3)

    ax2.plot(idx, result.s, 'mo-', ms=4, lw=1)
    ax2.axhline(result.S_bar, c='g', lw=1.5, label=f'S-bar={result.S_bar:.3f}A')
    ax2.axhline(result.UCL_S, c='r', ls='--', label=f'UCL={result.UCL_S:.3f}A')
    ax2.axhline(result.LCL_S, c='r', ls='--')
    ax2.set_title('S Chart: Wafer-to-Wafer Variability')
    ax2.set_xlabel('Lot Index')
    ax2.set_ylabel('Within-lot sigma (A)')
    ax2.legend(loc='best', fontsize=9)
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=140, bbox_inches='tight')
    return fig


def plot_full_monitoring_dashboard(thickness_3d, USL=31.5, LSL=28.5,
                                    target=30.0, save_path=None):
    """4-panel dashboard: X-bar, S, WIW NU% trend, rolling quality margin."""
    from .data_generator import aggregate_to_lot_subgroups, compute_wiw_trend

    subgroups = aggregate_to_lot_subgroups(thickness_3d)
    result = compute_xbar_s(subgroups, USL=USL, LSL=LSL)
    wiw = compute_wiw_trend(thickness_3d)

    rolling_quality_margin = []
    for i in range(10, len(subgroups) + 1):
        r = compute_xbar_s(subgroups[i - 10:i], USL=USL, LSL=LSL)
        rolling_quality_margin.append(r.quality_margin_index)

    fig, axes = plt.subplots(2, 2, figsize=(15, 9))

    ax = axes[0, 0]
    ax.plot(result.xbar, 'bo-', ms=4)
    ax.axhline(result.X_bar_bar, c='g', label='X-barbar')
    ax.axhline(result.UCL_X, c='r', ls='--', label='UCL/LCL')
    ax.axhline(result.LCL_X, c='r', ls='--')
    ax.axhline(USL, c='orange', ls='-.', alpha=0.6, label='Spec')
    ax.axhline(LSL, c='orange', ls='-.', alpha=0.6)
    for i, _, _ in result.violations:
        ax.plot(i, result.xbar[i], 'rs', ms=12, mfc='none', mew=2)
    ax.set_title(f'X-bar Chart  (margin index={result.quality_margin_index:.2f}, '
                 f'WE violations={len(set(v[0] for v in result.violations))})')
    ax.set_ylabel('Mean Tox (A)')
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    ax = axes[0, 1]
    ax.plot(result.s, 'mo-', ms=4)
    ax.axhline(result.S_bar, c='g', label='S-bar')
    ax.axhline(result.UCL_S, c='r', ls='--', label='UCL/LCL')
    ax.axhline(result.LCL_S, c='r', ls='--')
    ax.set_title('S Chart (wafer-to-wafer)')
    ax.set_ylabel('Sigma_w2w (A)')
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    ax = axes[1, 0]
    ax.plot(wiw['NU_pct'], 'co-', ms=4)
    ax.axhline(1.0, c='r', ls='--', label='NU% control limit')
    ax.set_title('WIW NU% Trend (lamp degradation indicator)')
    ax.set_xlabel('Lot Index')
    ax.set_ylabel('NU 1-sigma %')
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    ax = axes[1, 1]
    ax.plot(range(10, len(subgroups) + 1), rolling_quality_margin, 'go-', ms=4)
    ax.axhline(1.33, c='r', ls='--', label='Guardband minimum')
    ax.axhline(1.67, c='orange', ls=':', label='Guardband target')
    ax.set_title('Rolling Quality Margin (window=10 lots)')
    ax.set_xlabel('Lot Index')
    ax.set_ylabel('Margin index')
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    plt.suptitle('RTO Process Monitoring Dashboard',
                 fontsize=14, weight='bold')
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=140, bbox_inches='tight')
    return fig, result
