"""
PM Deferral Decision Engine.
Multi-criteria evaluation of whether scheduled maintenance can be safely deferred.
"""
import numpy as np
from dataclasses import dataclass, field
from enum import Enum


class Decision(Enum):
    DEFER = "DEFER PM"
    PROCEED = "PROCEED with scheduled PM"
    EMERGENCY = "EMERGENCY PM (do not defer)"


@dataclass
class DeferralConfig:
    risk_threshold_defer: float = 0.35
    default_defer_horizon_days: float = 5.0
    quality_index_minimum: float = 1.33
    max_deferral_multiplier: float = 1.5
    spc_violation_lookback_days: int = 7
    weibull_beta: float = 2.3
    weibull_eta: float = 180.0
    cost_pm: float = 8_000.0
    cost_excursion: float = 150_000.0
    w_weibull_hazard: float = 5.0
    w_weibull_cap: float = 0.5
    w_drift_scaling: float = 0.4
    w_drift_cap: float = 0.3
    w_quality_index_penalty: float = 0.4


@dataclass
class ToolState:
    days_since_last_pm: float
    scheduled_pm_interval: float
    recent_quality_index: float
    spc_violations_last_7d: int
    drift_slope_per_day: float
    sigma_margin_to_USL: float
    sigma_margin_to_LSL: float


@dataclass
class DeferralReport:
    decision: Decision
    risk_score: float
    net_benefit_usd: float
    deferred_to_day: float
    rationale: list = field(default_factory=list)

    def __str__(self):
        pct = self.risk_score * 100
        if pct <= 15:
            level = "[LOW]"
        elif pct <= 35:
            level = "[MODERATE]"
        elif pct <= 60:
            level = "[HIGH]"
        else:
            level = "[CRITICAL]"
        s = f"\n{'=' * 62}\n  {self.decision.value}\n{'=' * 62}\n"
        s += f"  Risk score:    {pct:5.1f}%  {level}\n"
        s += f"  Net benefit:   ${self.net_benefit_usd:,.0f}\n"
        s += f"  Defer to day:  {self.deferred_to_day:.1f}\n\n  Rationale:\n"
        for r in self.rationale:
            s += f"   - {r}\n"
        return s


def F_weibull(t, beta, eta):
    return 1 - np.exp(-(t / eta) ** beta)


def evaluate_deferral(state: ToolState, defer_horizon: float = None,
                      config: DeferralConfig = None) -> DeferralReport:
    cfg = config or DeferralConfig()
    horizon = defer_horizon if defer_horizon is not None else cfg.default_defer_horizon_days
    rationale = []
    t_now = state.days_since_last_pm
    t_def = t_now + horizon
    max_def = state.scheduled_pm_interval * cfg.max_deferral_multiplier

    # HARD STOPS
    if state.spc_violations_last_7d > 0:
        return DeferralReport(
            decision=Decision.EMERGENCY, risk_score=1.0, net_benefit_usd=0,
            deferred_to_day=t_now,
            rationale=[f"SPC Western Electric violation in past 7d "
                       f"({state.spc_violations_last_7d} hits) - no deferral allowed"],
        )

    if state.recent_quality_index < cfg.quality_index_minimum:
        return DeferralReport(
            decision=Decision.EMERGENCY, risk_score=1.0, net_benefit_usd=0,
            deferred_to_day=t_now,
            rationale=[f"Quality index={state.recent_quality_index:.2f} below guardband target "
                       f"{cfg.quality_index_minimum}"],
        )

    if t_def > max_def:
        return DeferralReport(
            decision=Decision.PROCEED, risk_score=0.6, net_benefit_usd=0,
            deferred_to_day=state.scheduled_pm_interval,
            rationale=[f"Deferral to day {t_def:.1f} exceeds hard cap "
                       f"({max_def:.0f}d = {cfg.max_deferral_multiplier}x scheduled)"],
        )

    # SOFT RISK SCORE
    risk_score = 0.0
    dF = (F_weibull(t_def, cfg.weibull_beta, cfg.weibull_eta)
          - F_weibull(t_now, cfg.weibull_beta, cfg.weibull_eta))
    risk_score += min(dF * cfg.w_weibull_hazard, cfg.w_weibull_cap)
    rationale.append(
        f"Weibull deltaP(fail) over {horizon:.0f}d = {dF * 100:.2f}%"
    )

    projected_shift = abs(state.drift_slope_per_day * horizon)
    drift_consume = projected_shift / (state.sigma_margin_to_USL * cfg.w_drift_scaling)
    risk_score += min(drift_consume, cfg.w_drift_cap)
    rationale.append(
        f"Projected drift over {horizon:.0f}d = {projected_shift:.3f}A "
        f"(margin {state.sigma_margin_to_USL:.1f} sigma)"
    )

    quality_margin = state.recent_quality_index - cfg.quality_index_minimum
    risk_score += max(0, (0.5 - quality_margin) * cfg.w_quality_index_penalty)
    rationale.append(f"Quality-index margin to guardband target: {quality_margin:.2f}")

    risk_score = min(risk_score, 1.0)

    pm_saved = cfg.cost_pm * (horizon / state.scheduled_pm_interval)
    risk_cost = dF * cfg.cost_excursion
    net_benefit = pm_saved - risk_cost
    rationale.append(
        f"Economics: save ${pm_saved:,.0f} vs risk ${risk_cost:,.0f} "
        f"-> net ${net_benefit:+,.0f}"
    )

    if risk_score < cfg.risk_threshold_defer and net_benefit > 0:
        decision = Decision.DEFER
        defer_to = t_def
    else:
        decision = Decision.PROCEED
        defer_to = state.scheduled_pm_interval
        rationale.append(
            f"-> Risk score {risk_score * 100:.1f}% >= "
            f"{cfg.risk_threshold_defer * 100:.0f}% OR net benefit <= 0"
        )

    return DeferralReport(
        decision=decision, risk_score=risk_score,
        net_benefit_usd=net_benefit, deferred_to_day=defer_to,
        rationale=rationale,
    )
