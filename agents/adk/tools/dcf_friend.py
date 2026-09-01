# Copyright 2026 Sectors Hackathon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""ADK FunctionTool wrappers for friend's deterministic DCF valuation math.

Ported from friend's abidamassi/dcf-valuation-tool (s05-s12).
Exposes typed, deterministic financial calculation tools for the ADK Modeler agent.
All formulas are pure Python with zero LLM math hallucinations.

Tools:
  - calc_wacc_full: Full WACC breakdown + CAPM + debt floor checks + component table
  - calc_fcff_projection: Linear fade revenue growth and EBIT margin FCFF forecast
  - calc_terminal_value_check: Gordon Growth TV + implied EV/EBITDA + TV dependency check
  - calc_dcf_full_valuation: End-to-end full DCF pipeline for an equity ticker
  - calc_recommendation: Upside-to-rating classifier with Review Required guardrails
  - calc_sensitivity_grid: 2D WACC x Terminal Growth matrix with summary stats
  - calc_scenarios: Bull, Base, and Bear operational scenarios using historical volatility
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from server.engines import (
        compute_wacc_full,
        wacc_table_dict,
        project_fcff_simple,
        terminal_value_gordon,
        tv_dependency_check,
        discount_and_bridge,
        make_recommendation,
        sensitivity_grid,
        scenarios_bull_bear,
        dcf_full,
    )
except ImportError:
    from scripts.dcf_engine import (
        compute_wacc_full,
        wacc_table_dict,
        project_fcff_simple,
        terminal_value_gordon,
        tv_dependency_check,
        discount_and_bridge,
        make_recommendation,
        sensitivity_grid,
        scenarios_bull_bear,
        dcf_full,
    )


def calc_wacc_full(
    rf: float,
    beta: float,
    erp: float,
    cod: float,
    market_cap: float,
    total_debt: float,
    tax: float = 0.22,
    size_premium: float = 0.0,
) -> dict[str, Any]:
    """Compute full WACC breakdown with CAPM Cost of Equity, Cost of Debt floors,

    and capital structure weighting. Ported from friend's s05 math.

    Args:
        rf: Risk-free rate (e.g. 0.065 for 6.5%).
        beta: Equity beta (raw or Blume adjusted).
        erp: Equity Risk Premium (e.g. 0.07 for 7.0%).
        cod: Cost of debt pre-tax (e.g. 0.085 for 8.5%).
        market_cap: Market capitalization in IDR.
        total_debt: Total book debt in IDR.
        tax: Corporate tax rate (default 0.22 for 22%).
        size_premium: Small-cap / size premium (default 0.0).

    Returns:
        Dict containing full WACC calculation breakdown, components table, and warnings.
    """
    res = compute_wacc_full(
        rf=rf,
        beta=beta,
        erp=erp,
        cod=cod,
        market_cap=market_cap,
        total_debt=total_debt,
        tax=tax,
        size_premium=size_premium,
    )
    res["components"] = wacc_table_dict(res)
    return res


def calc_fcff_projection(
    revenue_t0: float,
    g1: float,
    g_terminal: float,
    years: int = 5,
    ebit_margin: float = 0.15,
    tax: float = 0.22,
    capex_pct: float = 0.06,
    nwc_pct: float = 0.10,
    da_pct: float | None = None,
) -> dict[str, Any]:
    """Project Free Cash Flows to Firm (FCFF) over forecast horizon with linear growth and margin fade.

    Args:
        revenue_t0: Base year revenue in IDR.
        g1: Year 1 revenue growth rate (e.g. 0.08 for 8%).
        g_terminal: Perpetual terminal growth rate (e.g. 0.025 for 2.5%).
        years: Forecast horizon in years (default 5).
        ebit_margin: Operating EBIT margin (e.g. 0.15 for 15%).
        tax: Corporate tax rate (default 0.22).
        capex_pct: Capital expenditure as % of revenue (default 0.06).
        nwc_pct: Net working capital as % of revenue (default 0.10).
        da_pct: Depreciation & Amortization as % of revenue (optional).

    Returns:
        Dict containing list of projection rows per year and forecast summary.
    """
    proj = project_fcff_simple(
        revenue_t0=revenue_t0,
        g1=g1,
        g_terminal=g_terminal,
        years=years,
        ebit_margin=ebit_margin,
        tax=tax,
        capex_pct=capex_pct,
        nwc_pct=nwc_pct,
        da_pct=da_pct,
    )
    return {
        "projection": proj,
        "years": years,
        "final_fcff": proj[-1]["fcff"] if proj else 0.0,
        "final_revenue": proj[-1]["revenue"] if proj else 0.0,
        "final_ebit": proj[-1]["ebit"] if proj else 0.0,
    }


def calc_terminal_value_check(
    fcff_last: float,
    ebitda_last: float,
    wacc: float,
    g: float,
    years: int = 5,
    enterprise_value: float | None = None,
) -> dict[str, Any]:
    """Calculate Gordon Growth terminal value, implied exit multiple, and dependency check.

    Args:
        fcff_last: Free cash flow in the final explicit forecast year.
        ebitda_last: EBITDA in the final explicit forecast year.
        wacc: Weighted average cost of capital discount rate (e.g. 0.084).
        g: Perpetual terminal growth rate (e.g. 0.025).
        years: Forecast duration for discounting TV back to present (default 5).
        enterprise_value: Total enterprise value for dependency check (optional).

    Returns:
        Dict with Gordon TV, PV of TV, implied EV/EBITDA multiple, and dependency metrics.
    """
    tv_res = terminal_value_gordon(
        fcff_last=fcff_last,
        wacc=wacc,
        g=g,
        ebitda_last=ebitda_last,
    )
    tv_val = tv_res.get("tv_nominal") or tv_res.get("value")
    pv_tv = None
    if tv_val is not None and tv_res.get("valid", True):
        df_tv = 1.0 / ((1.0 + wacc) ** years)
        pv_tv = round(tv_val * df_tv, 2)

    dep = None
    if pv_tv is not None and enterprise_value is not None and enterprise_value > 0:
        dep = tv_dependency_check(pv_tv, enterprise_value)
    elif pv_tv is not None and tv_val is not None:
        dep = tv_dependency_check(pv_tv, pv_tv * 1.25)

    return {
        "terminal_value": tv_val,
        "tv_nominal": tv_val,
        "pv_terminal": pv_tv,
        "implied_exit_multiple": tv_res.get("implied_exit_multiple"),
        "implied_ev_ebitda": tv_res.get("implied_exit_multiple"),
        "dependency_pct": dep.get("dependency_pct") if dep else None,
        "dependency_flag": dep.get("dependency_flag") if dep else False,
        "valid": tv_res.get("valid", True),
        "reason": tv_res.get("reason", ""),
        "inputs": {
            "fcff_last": fcff_last,
            "ebitda_last": ebitda_last,
            "wacc": wacc,
            "g": g,
        },
    }


def calc_dcf_full_valuation(
    ticker: str,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Perform complete DCF valuation including WACC breakdown, FCFF forecast,

    Gordon TV, EV/Equity bridge, Recommendation rating with gates, Sensitivity grid,
    and Bull/Base/Bear scenarios.

    Args:
        ticker: Stock ticker symbol (e.g. 'RATU', 'MTEL', 'BBCA').
        overrides: Optional dictionary of assumption overrides (e.g. {'rf': 0.07, 'g': 0.03}).

    Returns:
        Full DCF valuation payload.
    """
    return dcf_full(ticker=ticker.upper().strip(), overrides=overrides)


def calc_recommendation(
    fair_value: float,
    market_price: float,
    upside_thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Translate model fair value and market price into BUY/HOLD/SELL rating with Review Required guardrail.

    Args:
        fair_value: Model fair value per share in IDR.
        market_price: Current market price per share in IDR.
        upside_thresholds: Optional custom threshold dict {'buy': 0.10, 'sell': -0.10, 'review_up': 1.00, 'review_down': -0.50}.

    Returns:
        Dict with rating (BUY/HOLD/SELL/Review Required), upside percentage, label, and explanation note.
    """
    upside = ((float(fair_value) / float(market_price)) - 1.0) if float(market_price) > 0 else None
    val_dict = {
        "fair_value_per_share": float(fair_value),
        "market_price": float(market_price),
        "upside": upside,
    }
    return make_recommendation(val_dict, thresholds=upside_thresholds)


def calc_sensitivity_grid(
    proj: list[dict[str, Any]],
    wacc_base: float,
    g_base: float,
    snapshot: dict[str, Any],
    steps: int = 2,
    wacc_step: float = 0.005,
    g_step: float = 0.0025,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute 2D sensitivity matrix varying WACC and Terminal Growth Rate g.

    Args:
        proj: List of projected FCFF dictionaries per forecast year.
        wacc_base: Base WACC discount rate.
        g_base: Base terminal growth rate.
        snapshot: Balance sheet snapshot with cash, total_debt, minority, shares_outstanding, price.
        steps: Number of grid steps in each direction (default 2 -> (2*steps+1)x(2*steps+1) grid).
        wacc_step: Delta step size for WACC (default 0.005 = 50bps).
        g_step: Delta step size for terminal growth g (default 0.0025 = 25bps).
        data: Optional market data dict overriding snapshot shares / price.

    Returns:
        Dict with fair_value matrix, upside matrix, stats (min/max/median), wacc_axis, g_axis.
    """
    return sensitivity_grid(
        proj=proj,
        wacc_base=wacc_base,
        g_base=g_base,
        snapshot=snapshot,
        data=data,
        steps=steps,
        wacc_step=wacc_step,
        g_step=g_step,
    )


def calc_scenarios(
    proj: list[dict[str, Any]] | dict[str, Any],
    wacc_base: float,
    g_base: float,
    hist_std: dict[str, float],
    snapshot: dict[str, Any],
    data: dict[str, Any] | None = None,
    k: float = 1.0,
    g_shift: float = 0.005,
    years: int = 5,
    tax: float = 0.22,
    capex_pct: float = 0.06,
    nwc_pct: float = 0.10,
) -> dict[str, Any]:
    """Generate Bull, Base, and Bear operational scenarios based on historical std deviations.

    Args:
        proj: List of explicit projection dicts or parameter dict.
        wacc_base: Base WACC discount rate.
        g_base: Base perpetual growth rate.
        hist_std: Historical standard deviations (e.g. {'rev_growth_sd': 0.03, 'ebit_margin_sd': 0.01}).
        snapshot: Balance sheet snapshot with cash, total_debt, minority, shares_outstanding, price.
        data: Optional market data dict.
        k: Number of standard deviations to shift (default 1.0).
        g_shift: Shift in terminal growth rate for Bull/Bear (default 0.005 = 50bps).
        years: Forecast horizon (default 5).
        tax: Corporate tax rate (default 0.22).
        capex_pct: Capex % of revenue.
        nwc_pct: NWC % of revenue.

    Returns:
        Dict containing BEAR, BASE, and BULL valuation scenarios.
    """
    return scenarios_bull_bear(
        proj_or_params=proj,
        wacc_base=wacc_base,
        g_base=g_base,
        hist_std=hist_std,
        snapshot=snapshot,
        data=data,
        k=k,
        g_shift=g_shift,
        years=years,
        tax=tax,
        capex_pct=capex_pct,
        nwc_pct=nwc_pct,
    )


__all__ = [
    "calc_wacc_full",
    "calc_fcff_projection",
    "calc_terminal_value_check",
    "calc_dcf_full_valuation",
    "calc_recommendation",
    "calc_sensitivity_grid",
    "calc_scenarios",
]
