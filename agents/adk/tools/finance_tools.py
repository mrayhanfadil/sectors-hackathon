# Copyright 2026 Sectors Hackathon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Deterministic finance tools - FunctionTool wrappers for the valuation engines.

These tools are the ONLY way the Modeler agent does math. LLMs must call
them rather than computing in-text.

Each function delegates to scripts/* if available, otherwise uses a
self-contained fallback so the ADK graph boots even before P2 engines land.

Tools:
  calc_wacc, calc_dcf, calc_ddm, calc_multiples, calc_ggm,
  calc_sotp, calc_blended, calc_historical_bands, calc_ratios
"""

from __future__ import annotations

import json
import math
from typing import Any

# We expose plain callables - google.adk.tools.function_tool.FunctionTool
# will wrap them. No import-time dependency on scripts/.


def calc_wacc(
    risk_free: float,
    beta: float,
    equity_risk_premium: float,
    cost_of_debt: float,
    weight_equity: float,
    tax_rate: float = 0.22,
) -> dict[str, Any]:
    """Compute WACC and cost of equity.

    Args:
        risk_free: Risk-free rate (e.g. 0.0696 for 6.96%).
        beta: Equity beta.
        equity_risk_premium: ERP (e.g. 0.0689).
        cost_of_debt: Pre-tax cost of debt (e.g. 0.035).
        weight_equity: Equity weight in capital structure (0..1).
        tax_rate: Corporate tax rate.

    Returns:
        Dict with cost_of_equity, wacc, inputs echoed.
    """
    coe = risk_free + beta * equity_risk_premium
    wacc = weight_equity * coe + (1 - weight_equity) * cost_of_debt * (1 - tax_rate)
    return {
        "cost_of_equity": round(coe, 6),
        "wacc": round(wacc, 6),
        "inputs": {
            "risk_free": risk_free,
            "beta": beta,
            "equity_risk_premium": equity_risk_premium,
            "cost_of_debt": cost_of_debt,
            "weight_equity": weight_equity,
            "tax_rate": tax_rate,
        },
    }


def calc_dcf(
    free_cash_flows: list[float],
    wacc: float,
    terminal_growth: float = 0.03,
    shares_outstanding: float = 1_000_000_000,
    net_debt: float = 0,
    cash: float = 0,
) -> dict[str, Any]:
    """DCF: discount FCFs + Gordon terminal value.

    Args:
        free_cash_flows: Projected FCFs (per year, in same currency units).
        wacc: Discount rate (e.g. 0.084).
        terminal_growth: Perpetual growth g.
        shares_outstanding: Share count.
        net_debt: Net debt to subtract.
        cash: Cash to add (if net_debt already net, set cash=0).

    Returns:
        Dict with enterprise_value, equity_value, fair_value_per_share, pv breakdown.
    """
    if wacc <= terminal_growth:
        return {"error": f"wacc ({wacc}) must exceed terminal_growth ({terminal_growth})"}
    pvs = [fcf / ((1 + wacc) ** (i + 1)) for i, fcf in enumerate(free_cash_flows)]
    n = len(free_cash_flows)
    last_fcf = free_cash_flows[-1] if free_cash_flows else 0
    terminal_value = last_fcf * (1 + terminal_growth) / (wacc - terminal_growth) if free_cash_flows else 0
    pv_terminal = terminal_value / ((1 + wacc) ** n) if n else 0
    ev = sum(pvs) + pv_terminal
    equity = ev - net_debt + cash
    fv = equity / shares_outstanding if shares_outstanding else 0
    return {
        "enterprise_value": round(ev, 2),
        "equity_value": round(equity, 2),
        "fair_value_per_share": round(fv, 2),
        "pv_fcfs": [round(x, 2) for x in pvs],
        "pv_terminal": round(pv_terminal, 2),
        "terminal_value": round(terminal_value, 2),
        "inputs": {
            "free_cash_flows": free_cash_flows,
            "wacc": wacc,
            "terminal_growth": terminal_growth,
            "shares_outstanding": shares_outstanding,
            "net_debt": net_debt,
            "cash": cash,
        },
    }


def calc_ddm(
    dividends: list[float],
    cost_of_equity: float,
    terminal_growth: float = 0.03,
    shares_outstanding: float = 1_000_000_000,
) -> dict[str, Any]:
    """DDM: discount dividends + Gordon terminal.

    Args:
        dividends: Projected DPS or total dividends per year.
        cost_of_equity: Discount rate.
        terminal_growth: Perpetual dividend growth.
        shares_outstanding: Share count (if dividends are totals, divide at end).

    Returns:
        Dict with equity_value, fair_value_per_share, pv breakdown.
    """
    if cost_of_equity <= terminal_growth:
        return {"error": f"cost_of_equity ({cost_of_equity}) must exceed terminal_growth ({terminal_growth})"}
    # Heuristic: if dividends look like DPS (<1000 and small), treat as per-share;
    # otherwise treat as totals and divide. We always return per-share FV;
    # caller can interpret. Here we assume dividends are per-share DPS.
    pvs = [d / ((1 + cost_of_equity) ** (i + 1)) for i, d in enumerate(dividends)]
    n = len(dividends)
    last = dividends[-1] if dividends else 0
    tv = last * (1 + terminal_growth) / (cost_of_equity - terminal_growth) if dividends else 0
    pv_tv = tv / ((1 + cost_of_equity) ** n) if n else 0
    fv = sum(pvs) + pv_tv
    return {
        "fair_value_per_share": round(fv, 2),
        "pv_dividends": [round(x, 4) for x in pvs],
        "pv_terminal": round(pv_tv, 4),
        "terminal_value": round(tv, 4),
        "inputs": {
            "dividends": dividends,
            "cost_of_equity": cost_of_equity,
            "terminal_growth": terminal_growth,
            "shares_outstanding": shares_outstanding,
        },
    }


def calc_multiples(
    ebitda: float,
    ev_ebitda: float,
    shares_outstanding: float,
    net_debt: float = 0,
    cash: float = 0,
) -> dict[str, Any]:
    """EV/EBITDA implied valuation.

    Args:
        ebitda: Trailing or forward EBITDA.
        ev_ebitda: Peer median EV/EBITDA multiple.
        shares_outstanding: Share count.
        net_debt: Net debt.
        cash: Cash (if net_debt is gross debt).

    Returns:
        Dict with enterprise_value, equity_value, fair_value_per_share.
    """
    ev = ebitda * ev_ebitda
    eq = ev - net_debt + cash
    fv = eq / shares_outstanding if shares_outstanding else 0
    return {
        "enterprise_value": round(ev, 2),
        "equity_value": round(eq, 2),
        "fair_value_per_share": round(fv, 2),
        "inputs": {
            "ebitda": ebitda,
            "ev_ebitda": ev_ebitda,
            "shares_outstanding": shares_outstanding,
            "net_debt": net_debt,
            "cash": cash,
        },
    }


def calc_ggm(
    roe: float,
    cost_of_equity: float,
    growth: float,
    book_value_per_share: float,
) -> dict[str, Any]:
    """Gordon Growth Model (GGM) for P/BV - used for banks (e.g. BBCA).

    P/BV = (ROE - g) / (CoE - g);  P = P/BV * BVPS
    """
    if cost_of_equity <= growth:
        return {"error": f"cost_of_equity ({cost_of_equity}) must exceed growth ({growth})"}
    pbv = (roe - growth) / (cost_of_equity - growth)
    price = pbv * book_value_per_share
    return {
        "pbv": round(pbv, 4),
        "fair_value_per_share": round(price, 2),
        "inputs": {
            "roe": roe,
            "cost_of_equity": cost_of_equity,
            "growth": growth,
            "book_value_per_share": book_value_per_share,
        },
    }


def calc_sotp(
    segments: list[dict[str, Any]],
) -> dict[str, Any]:
    """SOTP: sum of parts.

    Args:
        segments: List of {name, value, weight?, discount?}.
                  value is segment equity/firm value; discount is holdco discount.

    Returns:
        Dict with sotp_value, breakdown.
    """
    total = 0.0
    breakdown = []
    for s in segments:
        v = float(s.get("value", 0))
        disc = float(s.get("discount", 0))
        adj = v * (1 - disc)
        total += adj
        breakdown.append({"name": s.get("name", "?"), "value": v, "discount": disc, "adjusted": round(adj, 2)})
    return {"sotp_value": round(total, 2), "breakdown": breakdown, "inputs": {"segments": segments}}


def calc_blended(
    dcf_value: float,
    multiples_value: float,
    w_dcf: float = 0.6,
    w_multiples: float = 0.4,
) -> dict[str, Any]:
    """Blended valuation (MTEL 60/40 pattern).

    Args:
        dcf_value: DCF fair value per share.
        multiples_value: Multiples fair value per share.
        w_dcf: DCF weight.
        w_multiples: Multiples weight.

    Returns:
        Dict with blended_value, weights, margin_of_safety helper.
    """
    if abs((w_dcf + w_multiples) - 1.0) > 1e-6:
        return {"error": f"weights must sum to 1.0, got {w_dcf + w_multiples}"}
    blended = dcf_value * w_dcf + multiples_value * w_multiples
    return {
        "blended_value": round(blended, 2),
        "weights": {"dcf": w_dcf, "multiples": w_multiples},
        "inputs": {"dcf_value": dcf_value, "multiples_value": multiples_value},
        "hint": "Apply margin_of_safety separately: target = blended * (1 - mos)",
    }


def calc_historical_bands(
    series: list[float],
) -> dict[str, Any]:
    """Historical valuation bands: mean, std, ±1σ, ±2σ.

    Args:
        series: Historical P/BV or EV/EBITDA series (3Y monthly, etc.)

    Returns:
        Dict with mean, std, bands.
    """
    if not series:
        return {"error": "empty series"}
    n = len(series)
    mean = sum(series) / n
    var = sum((x - mean) ** 2 for x in series) / n
    std = math.sqrt(var)
    return {
        "mean": round(mean, 4),
        "std": round(std, 4),
        "bands": {
            "plus_2": round(mean + 2 * std, 4),
            "plus_1": round(mean + 1 * std, 4),
            "mean": round(mean, 4),
            "minus_1": round(mean - 1 * std, 4),
            "minus_2": round(mean - 2 * std, 4),
        },
        "n": n,
    }


def calc_ratios(
    revenue: float,
    ebitda: float,
    net_income: float,
    total_debt: float,
    cash: float,
    equity: float,
    interest_expense: float,
    current_assets: float = 0,
    current_liabilities: float = 0,
) -> dict[str, Any]:
    """Key ratios: margins, leverage, coverage, liquidity.

    Returns:
        Dict with ebitda_margin, net_margin, debt_to_equity, net_gearing,
        debt_to_ebitda, interest_coverage, current_ratio.
    """
    out: dict[str, Any] = {}
    out["ebitda_margin"] = round(ebitda / revenue, 4) if revenue else None
    out["net_margin"] = round(net_income / revenue, 4) if revenue else None
    out["debt_to_equity"] = round(total_debt / equity, 4) if equity else None
    net_debt = total_debt - cash
    out["net_gearing"] = round(net_debt / equity, 4) if equity else None
    out["debt_to_ebitda"] = round(total_debt / ebitda, 4) if ebitda else None
    out["interest_coverage"] = round(ebitda / interest_expense, 4) if interest_expense else None
    if current_liabilities:
        out["current_ratio"] = round(current_assets / current_liabilities, 4)
    else:
        out["current_ratio"] = None
    return out


# Export list for ADK registration
DETERMINISTIC_TOOLS = [
    calc_wacc,
    calc_dcf,
    calc_ddm,
    calc_multiples,
    calc_ggm,
    calc_sotp,
    calc_blended,
    calc_historical_bands,
    calc_ratios,
]

# FCFF / DCF math shared with server/report/engines/dcf_engine
from .dcf_engine_tool import (
    calc_wacc_full,
    calc_fcff_projection,
    calc_terminal_value_check,
    calc_dcf_full_valuation,
    calc_recommendation,
    calc_sensitivity_grid,
    calc_scenarios,
)

