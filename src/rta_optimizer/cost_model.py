"""
Cost-risk trade-off model for RTO PM interval optimization.
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize_scalar

BETA = 2.3
ETA = 180.0   # days; characteristic life of lamp module (well-maintained)
C_PM = 8_000
C_MON = 1_200
C_EXC = 150_000
D_OP = 350


def F_weibull(t, beta=BETA, eta=ETA):
    """Cumulative failure probability."""
    return 1 - np.exp(-(t / eta) ** beta)


def annual_cost(T_pm, monitor_freq=0.25, beta=BETA, eta=ETA,
                c_pm=C_PM, c_mon=C_MON, c_exc=C_EXC, d_op=D_OP):
    n_pm = d_op / T_pm
    pm_cost = n_pm * c_pm
    mon_cost = monitor_freq * d_op * c_mon
    exc_cost = n_pm * F_weibull(T_pm, beta, eta) * c_exc
    return pm_cost + mon_cost + exc_cost


def optimize_pm_interval(monitor_freq=0.25, bounds=(15, 90)):
    res = minimize_scalar(lambda T: annual_cost(T, monitor_freq),
                          bounds=bounds, method='bounded')
    return res.x, res.fun


def plot_cost_risk_tradeoff(save_path=None):
    T_range = np.linspace(15, 90, 100)
    costs_opt = [annual_cost(t, 0.25) for t in T_range]
    costs_base = [annual_cost(t, 1.0) for t in T_range]
    risks = [F_weibull(t) * 100 for t in T_range]
    T_star, c_star = optimize_pm_interval(0.25)

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.plot(T_range, np.array(costs_base) / 1000, 'b--', lw=2,
             label='Baseline (daily monitor)', alpha=0.7)
    ax1.plot(T_range, np.array(costs_opt) / 1000, 'b-', lw=2.5,
             label='Optimized (Tier-1 + 0.25x monitor)')
    ax1.axvline(T_star, color='g', ls='--', lw=2,
                label=f'T* = {T_star:.1f} days')
    ax1.set_xlabel('PM Interval (days)', fontsize=11)
    ax1.set_ylabel('Annual Cost (USD, thousands)', color='b', fontsize=11)
    ax1.tick_params(axis='y', labelcolor='b')
    ax1.grid(alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(T_range, risks, 'r-', lw=2, label='Excursion risk %')
    ax2.axhline(5, color='r', ls=':', alpha=0.5, label='5% risk constraint')
    ax2.set_ylabel('Excursion Risk (%)', color='r', fontsize=11)
    ax2.tick_params(axis='y', labelcolor='r')

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2,
               loc='upper center', fontsize=9, ncol=2)

    plt.title('Cost-Risk Trade-off: Optimal PM Interval',
              fontsize=13, weight='bold')
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=140, bbox_inches='tight')
    return fig, T_star
