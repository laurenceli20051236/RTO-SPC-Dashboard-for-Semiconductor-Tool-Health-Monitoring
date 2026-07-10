from __future__ import annotations

import pandas as pd

from rto_spc.config import NONNEGATIVE_THICKNESS_METRICS, SPC_OOC_SIGMA_K, SPC_WARNING_SIGMA_K

THICKNESS_IMR_BEYOND_LIMIT = "THICKNESS_IMR_BEYOND_LIMIT"
THICKNESS_IMR_WARNING_LIMIT = "THICKNESS_IMR_WARNING_LIMIT"
THICKNESS_MR_SPIKE = "THICKNESS_MR_SPIKE"


def _ensure_rule_columns(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    if "warning_flag" not in result.columns:
        result["warning_flag"] = False
    if "ooc_flag" not in result.columns:
        result["ooc_flag"] = False
    if "rule_triggered" not in result.columns:
        result["rule_triggered"] = None
    if "severity" not in result.columns:
        result["severity"] = None
    return result


def apply_thickness_imr_rules(df: pd.DataFrame) -> pd.DataFrame:
    """Apply frozen Thickness individual-value fallback rules."""
    result = _ensure_rule_columns(df)
    thickness_index = result.index[result["monitor_type"] == "Thickness"]

    for idx in thickness_index:
        row = result.loc[idx]
        rules: list[str] = []
        value = pd.to_numeric(pd.Series([row.get("value")]), errors="coerce").iloc[0]
        ucl = pd.to_numeric(pd.Series([row.get("ucl")]), errors="coerce").iloc[0]
        cl = pd.to_numeric(pd.Series([row.get("cl")]), errors="coerce").iloc[0]
        lcl = pd.to_numeric(pd.Series([row.get("lcl")]), errors="coerce").iloc[0]
        mr_value = pd.to_numeric(pd.Series([row.get("mr_value")]), errors="coerce").iloc[0]
        mr_ucl = pd.to_numeric(pd.Series([row.get("mr_ucl")]), errors="coerce").iloc[0]

        if pd.notna(value) and pd.notna(ucl) and pd.notna(lcl) and (value > ucl or value < lcl):
            rules.append(THICKNESS_IMR_BEYOND_LIMIT)
        elif pd.notna(value) and pd.notna(ucl) and pd.notna(lcl) and pd.notna(cl):
            sigma_estimate = (ucl - cl) / SPC_OOC_SIGMA_K if ucl > cl else pd.NA
            if pd.notna(sigma_estimate) and sigma_estimate > 0:
                warning_ucl = cl + SPC_WARNING_SIGMA_K * sigma_estimate
                warning_lcl = cl - SPC_WARNING_SIGMA_K * sigma_estimate
                if str(row.get("metric_name")) in NONNEGATIVE_THICKNESS_METRICS:
                    warning_lcl = max(0.0, warning_lcl)
                if value > warning_ucl or value < warning_lcl:
                    rules.append(THICKNESS_IMR_WARNING_LIMIT)
        if pd.notna(mr_value) and pd.notna(mr_ucl) and mr_value > mr_ucl:
            rules.append(THICKNESS_MR_SPIKE)

        if rules:
            is_high = THICKNESS_IMR_BEYOND_LIMIT in rules
            result.at[idx, "warning_flag"] = not is_high
            result.at[idx, "ooc_flag"] = is_high
            result.at[idx, "rule_triggered"] = "; ".join(rules)
            result.at[idx, "severity"] = "High" if is_high else "Medium"
        else:
            result.at[idx, "warning_flag"] = False
            result.at[idx, "ooc_flag"] = False
            result.at[idx, "rule_triggered"] = None
            result.at[idx, "severity"] = None

    return result
