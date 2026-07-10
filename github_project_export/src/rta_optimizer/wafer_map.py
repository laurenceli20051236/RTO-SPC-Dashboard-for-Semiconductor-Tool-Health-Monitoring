"""
Oxide thickness uniformity wafer map module.

Simulates metrology tool output (KLA Aleris / Nanometrics Atlas-class
ellipsometer) using the industry-standard 49-site polar sampling pattern,
computes within-wafer (WIW) uniformity statistics, and generates
publication-quality contour maps.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from scipy.interpolate import griddata


def generate_49site_pattern(diameter_mm=300, edge_exclusion_mm=3):
    """Returns (49, 2) array of (x, y) mm site coordinates."""
    r_max = diameter_mm / 2 - edge_exclusion_mm
    rings = [(0.00, 1), (0.20, 4), (0.40, 8),
             (0.60, 12), (0.80, 16), (0.96, 8)]
    points = []
    for r_frac, n in rings:
        r = r_frac * r_max
        if n == 1:
            points.append((0.0, 0.0))
        else:
            for i in range(n):
                offset = (np.pi / n) if r_frac in [0.4, 0.8] else 0.0
                theta = 2 * np.pi * i / n + offset
                points.append((r * np.cos(theta), r * np.sin(theta)))
    return np.array(points)


def simulate_oxide_thickness(sites_xy, target_thickness=30.0,
                             signature='bullseye', nu_percent=0.6, seed=None):
    """Synthetic thickness with controllable process signature."""
    if seed is not None:
        np.random.seed(seed)
    x, y = sites_xy[:, 0], sites_xy[:, 1]
    r = np.sqrt(x ** 2 + y ** 2)
    r_norm = r / r.max()
    sigma_target = target_thickness * nu_percent / 100

    if signature == 'bullseye':
        pattern = 3.0 * sigma_target * (0.5 - r_norm ** 2)
    elif signature == 'm_shape':
        pattern = 2.5 * sigma_target * np.sin(np.pi * r_norm)
        pattern -= pattern.mean()
    elif signature == 'tilted':
        pattern = 2.0 * sigma_target * (x / r.max())
    elif signature == 'edge_fast':
        pattern = 2.5 * sigma_target * (r_norm ** 2 - 0.5)
    elif signature == 'random':
        pattern = 0.0
    else:
        raise ValueError(f"Unknown signature: {signature}")

    noise = np.random.randn(len(sites_xy)) * sigma_target * 0.4
    return target_thickness + pattern + noise


def compute_uniformity_stats(thickness, USL=None, LSL=None):
    """Within-wafer metrology stats (matches metro tool reports)."""
    mean = thickness.mean()
    sigma = thickness.std(ddof=1)
    rng = thickness.max() - thickness.min()
    stats = {
        'sites': len(thickness),
        'mean': mean,
        'sigma': sigma,
        'min': thickness.min(),
        'max': thickness.max(),
        'range': rng,
        'NU_1sigma_pct': sigma / mean * 100,
        'NU_range_pct': rng / (2 * mean) * 100,
    }
    if USL is not None and LSL is not None:
        stats['quality_margin_index'] = min(USL - mean, mean - LSL) / (3 * sigma)
        stats['oos_sites'] = int(np.sum((thickness > USL) | (thickness < LSL)))
    return stats


def plot_wafer_map(sites_xy, thickness, target=None, USL=None, LSL=None,
                   edge_exclusion_mm=3, title='Oxide Thickness Uniformity Map',
                   save_path=None):
    """Wafer map with contour, sites, stats box, wafer outline, notch."""
    stats = compute_uniformity_stats(thickness, USL, LSL)
    site_r_max = np.sqrt((sites_xy ** 2).sum(axis=1)).max()
    wafer_r = site_r_max + edge_exclusion_mm

    fig, ax = plt.subplots(figsize=(10, 8))
    gx, gy = np.mgrid[-wafer_r:wafer_r:200j, -wafer_r:wafer_r:200j]
    gz = griddata(sites_xy, thickness, (gx, gy), method='cubic')
    mask = (gx ** 2 + gy ** 2) > site_r_max ** 2
    gz = np.ma.array(gz, mask=mask)

    vmin, vmax = thickness.min() - 0.05, thickness.max() + 0.05
    cf = ax.contourf(gx, gy, gz, levels=20, cmap='RdYlBu_r',
                     vmin=vmin, vmax=vmax)
    ax.scatter(sites_xy[:, 0], sites_xy[:, 1], c=thickness,
               cmap='RdYlBu_r', s=70, edgecolors='black', linewidth=0.6,
               vmin=vmin, vmax=vmax, zorder=5)

    ax.add_patch(Circle((0, 0), wafer_r, fill=False, color='black', lw=2))
    ax.add_patch(Circle((0, 0), site_r_max, fill=False, color='gray',
                        lw=1, ls='--', alpha=0.5))
    ax.plot([0, 0], [-wafer_r, -wafer_r - 6], 'k-', lw=2.5)
    ax.text(0, -wafer_r - 12, 'NOTCH', ha='center', fontsize=9, weight='bold')

    lines = [
        f"Sites:        {stats['sites']}",
        f"Mean:         {stats['mean']:.3f} A",
        f"WIW 1sigma:   {stats['sigma']:.3f} A",
        f"Range:        {stats['range']:.3f} A",
        f"Min / Max:    {stats['min']:.2f} / {stats['max']:.2f}",
        f"NU (1sigma%): {stats['NU_1sigma_pct']:.2f} %",
        f"NU (range%):  {stats['NU_range_pct']:.2f} %",
    ]
    if 'quality_margin_index' in stats:
        lines.append(f"Margin idx:   {stats['quality_margin_index']:.2f}")
        if stats['oos_sites'] > 0:
            lines.append(f"OOS sites:    {stats['oos_sites']} !")
    ax.text(1.28, 0.5, '\n'.join(lines), transform=ax.transAxes,
            va='center', fontsize=10, family='monospace',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow',
                      edgecolor='gray', alpha=0.95))

    cbar = plt.colorbar(cf, ax=ax, shrink=0.65, pad=0.02)
    cbar.set_label('Thickness (A)', fontsize=10)

    ax.set_xlim(-wafer_r * 1.15, wafer_r * 1.7)
    ax.set_ylim(-wafer_r * 1.2, wafer_r * 1.2)
    ax.set_aspect('equal')
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_title(title, fontsize=12, weight='bold')
    ax.grid(alpha=0.15)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=140, bbox_inches='tight')
    return fig, stats
