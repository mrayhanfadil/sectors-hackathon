"""Deterministic DCF + WACC engine (FCFF/FCFE, Gordon terminal).

Part of T02 — Deterministic Engines (Python, NOT LLM math).
Mirrors server/engines/__init__.py and agents/adk/tools/finance_tools.py signatures
so the FastAPI backend and the ADK Modeler agent can import this file directly.

Formulas (all explicit, auditable):
  CoE  = rf + beta * ERP
  WACC = We*CoE + Wd*CoD*(1-tax)          (pass tax=0 for pre-tax convention)
  PV_i = FCF_i / (1+WACC)^t_i
  TV   = FCF_last * (1+g) / (WACC - g)    (Gordon)  -- or pass explicit `tv`
  Firm = sum(PV_i) + TV * DF_terminal
  Eq   = Firm + cash - net_debt           (FCFF) | Firm itself (FCFE)
  FV   = Eq / shares_out

Reproduction notes (see scripts/benchmarks.json + README-engines.md):
  * MTEL DCF: 6 explicit periods, first FCF at t=0 (discount_from_year0=True)
    reproduces the plan's published "Discount 1.00 -> 0.62" schedule at WACC
    10.10%, bridging to documented Terminal 72,736 / Equity 51,556 / FV 630.
  * MTEL WACC 10.10% uses the pre-tax convention (tax=0) at W.E 60.8% / W.D 39.2%.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import pathlib
import statistics
from typing import Any, Dict, List, Optional


# =============================================================================
# ORIGINAL / CLASSIC ENGINE FUNCTIONS
# =============================================================================

def wacc(
    rf: float,
    beta: float,
    erp: float,
    cod: float,
    we: float = 0.608,
    wd: float = 0.392,
    tax: float = 0.22,
) -> Dict[str, Any]:
    """WACC = We*CoE + Wd*CoD*(1-tax); CoE = Rf + beta*ERP.

    Pass tax=0.0 for the pre-tax convention (MTEL 10.10% @ we 60.8/wd 39.2).
    """
    coe = rf + beta * erp
    cod_after_tax = cod * (1 - tax)
    w = we * coe + wd * cod_after_tax
    return {
        "wacc": round(w, 6),
        "coe": round(coe, 6),
        "cod_after_tax": round(cod_after_tax, 6),
        "inputs": {"rf": rf, "beta": beta, "erp": erp, "cod": cod, "we": we, "wd": wd, "tax": tax},
        "provenance": "CoE=Rf+beta*ERP; WACC=We*CoE+Wd*CoD*(1-tax)",
    }


def _discount_factors(wacc: float, n: int, discount_from_year0: bool, mid_year: bool) -> List[float]:
    offset = (0.0 if discount_from_year0 else 1.0) + (0.5 if mid_year else 0.0)
    return [1.0 / ((1.0 + wacc) ** (offset + i)) for i in range(n)]


def dcf(
    fcf: List[float],
    wacc: float,
    g_terminal: float,
    shares_out: float = 1.0,
    cash: float = 0.0,
    net_debt: float = 0.0,
    tv: Optional[float] = None,
    mid_year: bool = False,
    discount_from_year0: bool = False,
    fcfe: bool = False,
) -> Dict[str, Any]:
    """Classic DCF: discount FCFs + Gordon terminal value.

    Args:
        fcf: projected free cash flows (per period, same currency unit as cash/debt).
        wacc: discount rate (decimal). Must exceed g_terminal when tv is computed.
        g_terminal: perpetual growth (decimal).
        shares_out: share count (for FV per share).
        cash / net_debt: FCFF bridge to equity. Ignored when fcfe=True.
        tv: explicit terminal value override (e.g. 72,736 from the MTEL plan table).
        mid_year: mid-year convention (first FCF at t=0.5 / 1.5, ...).
        discount_from_year0: first FCF at t=0 (plan's "Discount 1.00 -> 0.62" = 6 periods).
        fcfe: True -> FCFs are FCFE (equity cash flows), skip cash/debt bridge.
    """
    if not fcf:
        raise ValueError("fcf must be non-empty")
    n = len(fcf)
    if tv is None:
        if wacc <= g_terminal:
            raise ValueError(f"wacc ({wacc}) must exceed g_terminal ({g_terminal})")
        tv = float(fcf[-1]) * (1 + g_terminal) / (wacc - g_terminal)

    dfs = _discount_factors(wacc, n, discount_from_year0, mid_year)
    pv_fcfs = [float(cf) * df for cf, df in zip(fcf, dfs)]
    # Terminal value sits at the end of the last explicit period.
    t_terminal = (n - 1 if discount_from_year0 else n) + (0.5 if mid_year else 0.0)
    df_terminal = 1.0 / ((1.0 + wacc) ** t_terminal)
    terminal_pv = tv * df_terminal

    firm_value = sum(pv_fcfs) + terminal_pv
    equity_value = firm_value if fcfe else firm_value + cash - net_debt
    fv_per_share = equity_value / shares_out if shares_out else 0.0

    return {
        "pv_fcfs": [round(x, 2) for x in pv_fcfs],
        "discount_factors": [round(x, 6) for x in dfs],
        "terminal_value": round(tv, 2),
        "terminal_pv": round(terminal_pv, 2),
        "firm_value": round(firm_value, 2),
        "equity_value": round(equity_value, 2),
        "fv_per_share": round(fv_per_share, 2),
        "method": "fcfe" if fcfe else "fcff",
        "convention": ("mid-year" if mid_year else "year-end")
        + (" + year0-first" if discount_from_year0 else ""),
        "inputs": {
            "fcf": fcf,
            "wacc": wacc,
            "g_terminal": g_terminal,
            "shares_out": shares_out,
            "cash": cash,
            "net_debt": net_debt,
            "tv_explicit": tv,
        },
    }


def ev_ebitda(
    ebitda: float,
    multiple: float,
    shares_out: float = 1.0,
    net_debt: float = 0.0,
    cash: float = 0.0,
) -> Dict[str, Any]:
    """EV/EBITDA multiple valuation: EV = EBITDA * multiple; Eq = EV - net_debt + cash."""
    ev = float(ebitda) * multiple
    equity = ev - net_debt + cash
    fv = equity / shares_out if shares_out else 0.0
    return {
        "ev": round(ev, 2),
        "equity_value": round(equity, 2),
        "fv_per_share": round(fv, 2),
        "multiple": multiple,
        "provenance": "EV=EBITDA*multiple; Eq=EV-net_debt+cash",
    }


def index_target(current: float, eps_growth: float, multiple: float = 1.0) -> Dict[str, Any]:
    """Top-down index target = current * (1 + EPS growth) * (multiple re-rating factor).

    JPM 2026 Outlook (2 Dec 2025): JCI base 9,100 = spot * (1+8%) * 15x/15x (flat 15x).
    """
    target = current * (1 + eps_growth) * multiple
    return {
        "index_target": round(target, 2),
        "inputs": {"current": current, "eps_growth": eps_growth, "multiple": multiple},
        "methodology": "Index target = current x (1+EPS growth) x multiple re-rating",
    }


# =============================================================================
# FRIEND'S PURE-MATH FUNCTIONS (s05 - s12)
# =============================================================================

class _NullFlags:
    """An empty flag sink so sensitivity grids and batch runs don't flood logs."""
    def warn(self, *a, **k): pass
    def missing(self, *a, **k): pass
    def zero(self, *a, **k): pass
    def check_series(self, *a, **k): return True


def beta_blume_adj(beta_raw: float) -> float:
    """Blume adjusted beta = 0.67 * beta_raw + 0.33 * 1.00.

    Pulls beta toward market mean of 1.00. Standard Bloomberg convention.
    """
    return round(0.67 * float(beta_raw) + 0.33 * 1.0, 6)


def compute_wacc_full(
    rf: float,
    beta: float,
    erp: float,
    cod: float,
    market_cap: float,
    total_debt: float,
    tax: float = 0.22,
    size_premium: float = 0.0,
    flags: Optional[Any] = None,
    cod_spread_floor: float = 0.02,
    cod_floor: float = 0.03,
    cod_cap: float = 0.20,
    wacc_floor: float = 0.06,
    wacc_cap: float = 0.25,
) -> Dict[str, Any]:
    """Compute WACC with full breakdown, debt floor checks, and warnings.

    Ke = Rf + beta * ERP + SizePremium
    Kd floored at Rf + 200bps if debt > 0 and cod < Rf + 200bps
    WACC = We * Ke + Wd * Kd * (1 - tax)
    """
    warnings: List[str] = []
    ke = rf + beta * erp + size_premium

    kd_method = "Interest Expense / average Total Debt"
    total_debt = max(float(total_debt), 0.0)
    market_cap = max(float(market_cap), 0.0)

    if total_debt <= 0:
        kd_pretax = rf + cod_spread_floor
        kd_method = "No debt. Kd proxied as Rf + 200bps (zero debt weight)."
        if flags and hasattr(flags, "warn"):
            flags.warn("Cost of Debt", kd_method)
    else:
        floor_rel = rf + cod_spread_floor
        floor_val = max(cod_floor, floor_rel)
        if cod < floor_rel:
            warn_msg = (
                f"Computed Cost of Debt {cod*100:.2f}% is BELOW the risk-free rate + "
                f"{cod_spread_floor*10000:.0f}bps ({floor_rel*100:.2f}%). "
                f"Raised to {floor_rel*100:.2f}%."
            )
            warnings.append(warn_msg)
            if flags and hasattr(flags, "warn"):
                flags.warn("Cost of Debt", warn_msg)
            kd_pretax = floor_rel
            kd_method += " (raised to Rf + spread floor)"
        else:
            kd_pretax = cod

        kd_pretax = max(min(kd_pretax, cod_cap), floor_val)

    kd_aftertax = kd_pretax * (1.0 - tax)

    total_cap = market_cap + total_debt
    if total_cap > 0:
        w_e = market_cap / total_cap
        w_d = total_debt / total_cap
    else:
        w_e = 1.0
        w_d = 0.0

    wacc_raw = w_e * ke + w_d * kd_aftertax
    wacc_val = max(min(wacc_raw, wacc_cap), wacc_floor)
    if wacc_val != wacc_raw:
        warnings.append(f"WACC {wacc_raw*100:.2f}% clipped to bounds [{wacc_floor*100:.2f}%, {wacc_cap*100:.2f}%]")

    return {
        "rf": round(rf, 6),
        "erp": round(erp, 6),
        "beta": round(beta, 6),
        "beta_raw": round(beta, 6),
        "beta_adj": round(beta, 6),
        "beta_r2": None,
        "beta_nobs": None,
        "size_premium": round(size_premium, 6),
        "ke": round(ke, 6),
        "kd_pretax": round(kd_pretax, 6),
        "kd_aftertax": round(kd_aftertax, 6),
        "kd_method": kd_method,
        "tax_rate": round(tax, 6),
        "equity_value_mkt": round(market_cap, 2),
        "debt_book": round(total_debt, 2),
        "weight_equity": round(w_e, 6),
        "weight_debt": round(w_d, 6),
        "wacc_raw": round(wacc_raw, 6),
        "wacc": round(wacc_val, 6),
        "warnings": warnings,
        "provenance": "Ke=Rf+beta*ERP+SizePrem; WACC=We*Ke+Wd*Kd*(1-t)",
    }


def wacc_table_dict(wacc_result: Dict[str, Any]) -> List[Dict[str, str]]:
    """Format WACC breakdown rows for FE rendering."""
    w = wacc_result
    beta_raw_val = w.get("beta_raw", w.get("beta", 1.0))
    beta_adj_val = w.get("beta_adj", w.get("beta", 1.0))
    r2_val = w.get("beta_r2")

    return [
        {"label": "Risk-free rate (manual input)", "value": f"{w['rf']*100:.2f}%"},
        {"label": "Equity Risk Premium (manual input)", "value": f"{w['erp']*100:.2f}%"},
        {"label": "Beta raw (regression vs IHSG)", "value": f"{beta_raw_val:.3f}" if beta_raw_val is not None else "n/a"},
        {"label": "Beta adjusted (Blume)", "value": f"{beta_adj_val:.3f}" if beta_adj_val is not None else "n/a"},
        {"label": "Beta regression R-squared", "value": f"{r2_val:.3f}" if r2_val is not None else "n/a"},
        {"label": "Size premium", "value": f"{w['size_premium']*100:.2f}%"},
        {"label": "Cost of Equity (CAPM)", "value": f"{w['ke']*100:.2f}%"},
        {"label": "Cost of Debt, pre-tax", "value": f"{w['kd_pretax']*100:.2f}%"},
        {"label": "Effective tax rate", "value": f"{w['tax_rate']*100:.2f}%"},
        {"label": "Cost of Debt, after-tax", "value": f"{w['kd_aftertax']*100:.2f}%"},
        {"label": "Equity weight E/(D+E)", "value": f"{w['weight_equity']*100:.1f}%"},
        {"label": "Debt weight D/(D+E)", "value": f"{w['weight_debt']*100:.1f}%"},
        {"label": "WACC", "value": f"{w['wacc']*100:.2f}%"},
    ]


def project_fcff_simple(
    revenue_t0: float,
    g1: float,
    g_terminal: float,
    years: int = 5,
    ebit_margin: float = 0.15,
    tax: float = 0.22,
    capex_pct: float = 0.06,
    nwc_pct: float = 0.10,
    da_pct: Optional[float] = None,
    ebit_margin_target: Optional[float] = None,
    invested_capital_t0: Optional[float] = None,
    cap_terminal_at_g1: bool = True,
) -> List[Dict[str, Any]]:
    """Project FCFF over explicit forecast horizon with linear growth and margin fade.

    Returns DataFrame-like list of dicts (plain Python, JSON-serializable).
    """
    N = int(years)
    g1 = float(g1)
    margin = float(ebit_margin)
    g_term = float(g_terminal)
    tax_rate = float(tax)

    if cap_terminal_at_g1 and g_term > g1:
        g_term = max(g1, 0.0)

    da_r = float(da_pct) if da_pct is not None else 0.04
    cx_r = float(capex_pct)
    nwc_r = float(nwc_pct)

    if g1 > 0 and cx_r < da_r:
        cx_r = da_r

    m_target = float(ebit_margin_target) if ebit_margin_target is not None else margin

    rev0 = float(revenue_t0)
    nwc0 = rev0 * nwc_r
    prev_rev = rev0
    prev_nwc = nwc0
    prev_ic = float(invested_capital_t0) if invested_capital_t0 is not None else (rev0 * 0.5)

    rows: List[Dict[str, Any]] = []
    for t in range(1, N + 1):
        if N > 1:
            g_t = g1 - (g1 - g_term) * (t - 1) / (N - 1)
            m_t = margin + (m_target - margin) * (t - 1) / (N - 1)
        else:
            g_t = g1
            m_t = margin

        rev = prev_rev * (1.0 + g_t)
        ebit = rev * m_t
        nopat = ebit * (1.0 - tax_rate)
        da = rev * da_r
        capex = rev * cx_r
        nwc = rev * nwc_r
        dnwc = nwc - prev_nwc

        fcff = nopat + da - capex - dnwc
        reinvest = capex - da + dnwc
        rr = (reinvest / nopat) if nopat != 0 else None
        roic = (nopat / prev_ic) if (prev_ic and prev_ic != 0) else None
        implied_g = (rr * roic) if (rr is not None and roic is not None) else None

        rows.append({
            "year": t,
            "growth": round(g_t, 6),
            "revenue": round(rev, 2),
            "ebit": round(ebit, 2),
            "ebit_margin": round(m_t, 6),
            "nopat": round(nopat, 2),
            "da": round(da, 2),
            "capex": round(capex, 2),
            "nwc": round(nwc, 2),
            "delta_nwc": round(dnwc, 2),
            "fcff": round(fcff, 2),
            "reinvestment_rate": round(rr, 6) if rr is not None else None,
            "roic": round(roic, 6) if roic is not None else None,
            "implied_growth": round(implied_g, 6) if implied_g is not None else None,
        })

        prev_rev = rev
        prev_nwc = nwc
        if prev_ic is not None:
            prev_ic = prev_ic + reinvest

    return rows


def terminal_value_gordon(
    fcff_last: float,
    wacc: float,
    g: float,
    ebitda_last: Optional[float] = None,
    min_spread: float = 0.04,
    flags: Optional[Any] = None,
) -> Dict[str, Any]:
    """Gordon Growth terminal value: TV = FCFF_N * (1+g) / (WACC - g).

    Cross-checks implied EV/EBITDA multiple.
    """
    g = float(g)
    wacc = float(wacc)
    fcff_last = float(fcff_last)
    spread = wacc - g

    if spread < min_spread:
        reason = (
            f"WACC ({wacc*100:.2f}%) is only {spread*100:.2f}% above terminal growth ({g*100:.2f}%). "
            f"A minimum spread of {min_spread*10000:.0f}bps is required."
        )
        if flags and hasattr(flags, "warn"):
            flags.warn("Terminal Value", reason)
        return {
            "terminal_growth": round(g, 6),
            "wacc": round(wacc, 6),
            "fcff_final": round(fcff_last, 2),
            "fcff_terminal": None,
            "tv_nominal": None,
            "value": None,
            "implied_exit_multiple": None,
            "valid": False,
            "reason": reason,
        }

    if fcff_last <= 0:
        reason = f"Final year FCFF is not positive ({fcff_last:,.1f}). Gordon TV is not meaningful."
        if flags and hasattr(flags, "warn"):
            flags.warn("Terminal Value", reason)
        return {
            "terminal_growth": round(g, 6),
            "wacc": round(wacc, 6),
            "fcff_final": round(fcff_last, 2),
            "fcff_terminal": None,
            "tv_nominal": None,
            "value": None,
            "implied_exit_multiple": None,
            "valid": False,
            "reason": reason,
        }

    fcff_terminal = fcff_last * (1.0 + g)
    tv = fcff_terminal / spread

    implied_multiple = None
    if ebitda_last is not None and ebitda_last > 0:
        implied_multiple = round(tv / float(ebitda_last), 4)

    return {
        "terminal_growth": round(g, 6),
        "wacc": round(wacc, 6),
        "fcff_final": round(fcff_last, 2),
        "fcff_terminal": round(fcff_terminal, 2),
        "tv_nominal": round(tv, 2),
        "value": round(tv, 2),
        "implied_exit_multiple": implied_multiple,
        "valid": True,
        "reason": "",
    }


def tv_dependency_check(
    pv_tv: float,
    enterprise_value: float,
    threshold: float = 0.80,
    flags: Optional[Any] = None,
) -> Dict[str, Any]:
    """Check how much of enterprise value relies on terminal value perpetuity."""
    if not enterprise_value or enterprise_value == 0:
        return {"dependency_pct": 0.0, "dependency_flag": False, "share": 0.0, "flag": False}

    share = float(pv_tv) / float(enterprise_value)
    flag = bool(share >= threshold)
    if flag and flags and hasattr(flags, "warn"):
        flags.warn(
            "Terminal value dependency",
            f"{share*100:.1f}% of EV comes from terminal value (>= {threshold*100:.0f}% threshold)."
        )
    return {
        "dependency_pct": round(share, 4),
        "dependency_flag": flag,
        "share": round(share, 4),
        "flag": flag,
    }


def discount_and_bridge(
    proj: List[Dict[str, Any]],
    wacc: float,
    terminal_value: Any,
    snapshot: Dict[str, Any],
    data: Optional[Dict[str, Any]] = None,
    mid_year: bool = True,
    flags: Optional[Any] = None,
) -> Dict[str, Any]:
    """Discount explicit cash flows and TV to enterprise value and bridge to equity value per share."""
    wacc = float(wacc)
    N = len(proj)

    if isinstance(terminal_value, dict):
        if not terminal_value.get("valid", True):
            return {"valid": False, "reason": terminal_value.get("reason", "Invalid Terminal Value")}
        tv_nominal = float(terminal_value.get("tv_nominal", terminal_value.get("value", 0.0)))
        implied_exit = terminal_value.get("implied_exit_multiple")
    else:
        tv_nominal = float(terminal_value)
        implied_exit = None

    disc_rows: List[Dict[str, Any]] = []
    pv_explicit = 0.0

    for t in range(1, N + 1):
        fcff = float(proj[t - 1]["fcff"])
        exponent = (t - 0.5) if mid_year else float(t)
        df = 1.0 / ((1.0 + wacc) ** exponent)
        pv = fcff * df
        pv_explicit += pv
        disc_rows.append({
            "year": t,
            "fcff": round(fcff, 2),
            "exponent": round(exponent, 2),
            "discount_factor": round(df, 4),
            "pv": round(pv, 2),
        })

    df_tv = 1.0 / ((1.0 + wacc) ** N)
    pv_tv = tv_nominal * df_tv
    enterprise_value = pv_explicit + pv_tv

    dep = tv_dependency_check(pv_tv, enterprise_value, flags=flags)

    cash = float(snapshot.get("cash", 0.0) or 0.0)
    debt = float(snapshot.get("total_debt", snapshot.get("debt", 0.0)) or 0.0)
    minority = float(snapshot.get("minority", 0.0) or 0.0)

    equity_value = enterprise_value + cash - debt - minority

    data_src = data if data is not None else snapshot
    shares = float(data_src.get("shares_outstanding", data_src.get("shares_out", 1.0)) or 1.0)
    price = float(data_src.get("price", data_src.get("last_price", 0.0)) or 0.0)

    fv_per_share = (equity_value / shares) if shares > 0 else 0.0
    upside = ((fv_per_share / price) - 1.0) if price > 0 else None

    return {
        "valid": True,
        "pv_explicit": round(pv_explicit, 2),
        "pv_terminal": round(pv_tv, 2),
        "tv_nominal": round(tv_nominal, 2),
        "tv_discount_factor": round(df_tv, 4),
        "tv_share_of_ev": dep["dependency_pct"],
        "tv_dependency_flag": dep["dependency_flag"],
        "implied_exit_multiple": implied_exit,
        "enterprise_value": round(enterprise_value, 2),
        "cash": round(cash, 2),
        "total_debt": round(debt, 2),
        "minority": round(minority, 2),
        "equity_value": round(equity_value, 2),
        "shares_outstanding": shares,
        "fair_value_per_share": round(fv_per_share, 2),
        "market_price": price,
        "upside": round(upside, 6) if upside is not None else None,
        "wacc": round(wacc, 6),
        "mid_year": mid_year,
        "discount_table": disc_rows,
    }


def make_recommendation(
    valuation: Dict[str, Any],
    thresholds: Optional[Dict[str, float]] = None,
    flags: Optional[Any] = None,
) -> Dict[str, Any]:
    """Translate upside into BUY/HOLD/SELL rating with Review Required gate for extreme values."""
    th = {
        "buy": 0.10,
        "sell": -0.10,
        "review_up": 1.00,
        "review_down": -0.50,
    }
    if thresholds:
        th["buy"] = thresholds.get("buy", thresholds.get("buy_threshold", th["buy"]))
        th["sell"] = thresholds.get("sell", thresholds.get("sell_threshold", th["sell"]))
        th["review_up"] = thresholds.get("review_up", thresholds.get("review_upside_threshold", th["review_up"]))
        th["review_down"] = thresholds.get("review_down", thresholds.get("review_downside_threshold", th["review_down"]))

    upside = valuation.get("upside")
    fv = valuation.get("fair_value_per_share", 0.0)
    px = valuation.get("market_price", 0.0)

    if upside is None or (isinstance(upside, float) and (math.isnan(upside) or math.isinf(upside))):
        return {
            "rating": "N/A",
            "upside": None,
            "label": "Cannot be rated",
            "note": "Fair value or market price is unavailable.",
        }

    upside = float(upside)
    if upside > th["buy"]:
        rating, label = "BUY", "Undervalued"
    elif upside < th["sell"]:
        rating, label = "SELL", "Overvalued"
    else:
        rating, label = "HOLD", "Fairly valued"

    ud_word = "upside" if upside >= 0 else "downside"
    note = f"Model fair value IDR {fv:,.0f} versus market price IDR {px:,.0f}, {ud_word} {upside*100:+.1f}%."

    result: Dict[str, Any] = {
        "rating": rating,
        "upside": round(upside, 6),
        "label": label,
        "note": note,
        "threshold_buy": th["buy"],
        "threshold_sell": th["sell"],
    }

    if upside > th["review_up"] or upside < th["review_down"]:
        result["rating"] = "Review Required"
        result["reason_override"] = (
            "This result falls outside a defensible range for FCFF-based DCF. "
            "The gap between fair value and market price is wide enough that "
            "it more often signals a modelling or data issue than genuine "
            "mispricing. Consider cross-checking with SOTP, Net Asset Value, "
            "or relative valuation (EV/EBITDA, P/E against peers) before "
            "drawing a conclusion."
        )

    return result


def sensitivity_grid(
    proj: List[Dict[str, Any]],
    wacc_base: float,
    g_base: float,
    snapshot: Dict[str, Any],
    data: Optional[Dict[str, Any]] = None,
    steps: int = 2,
    wacc_step: float = 0.005,
    g_step: float = 0.0025,
    flags: Optional[Any] = None,
) -> Dict[str, Any]:
    """WACC x Terminal growth sensitivity grid (2D list of lists)."""
    wacc_axis = [round(wacc_base + i * wacc_step, 6) for i in range(-steps, steps + 1)]
    g_axis = [round(g_base + j * g_step, 6) for j in range(-steps, steps + 1)]

    fcff_final = float(proj[-1]["fcff"])
    ebitda_final = float(proj[-1].get("ebit", 0.0) + proj[-1].get("da", 0.0))

    fv_matrix: List[List[Optional[float]]] = []
    up_matrix: List[List[Optional[float]]] = []

    for w in wacc_axis:
        row_fv: List[Optional[float]] = []
        row_up: List[Optional[float]] = []
        for g in g_axis:
            tv = terminal_value_gordon(fcff_final, w, g, ebitda_final, min_spread=0.04, flags=None)
            if not tv.get("valid"):
                row_fv.append(None)
                row_up.append(None)
                continue
            v = discount_and_bridge(proj, w, tv, snapshot, data, flags=_NullFlags())
            if not v.get("valid"):
                row_fv.append(None)
                row_up.append(None)
                continue
            row_fv.append(round(v["fair_value_per_share"], 2))
            row_up.append(round(v["upside"] * 100, 1) if v.get("upside") is not None else None)
        fv_matrix.append(row_fv)
        up_matrix.append(row_up)

    valid_fvs = [x for row in fv_matrix for x in row if x is not None]
    stats = {
        "min": round(min(valid_fvs), 2) if valid_fvs else None,
        "max": round(max(valid_fvs), 2) if valid_fvs else None,
        "median": round(statistics.median(valid_fvs), 2) if valid_fvs else None,
        "n_valid": len(valid_fvs),
        "n_cells": len(wacc_axis) * len(g_axis),
    }

    return {
        "fair_value": fv_matrix,
        "upside": up_matrix,
        "stats": stats,
        "wacc_axis": wacc_axis,
        "g_axis": g_axis,
    }


def scenarios_bull_bear(
    proj_or_params: Any,
    wacc_base: float,
    g_base: float,
    hist_std: Dict[str, float],
    snapshot: Dict[str, Any],
    data: Optional[Dict[str, Any]] = None,
    k: float = 1.0,
    g_shift: float = 0.005,
    years: int = 5,
    tax: float = 0.22,
    capex_pct: float = 0.06,
    nwc_pct: float = 0.10,
    da_pct: Optional[float] = None,
) -> Dict[str, Any]:
    """Bull, Base, Bear operational scenarios using historical standard deviations."""
    if isinstance(proj_or_params, list) and len(proj_or_params) > 0:
        base_g1 = float(proj_or_params[0]["growth"])
        base_margin = float(proj_or_params[0]["ebit_margin"])
        rev0 = float(snapshot.get("revenue", proj_or_params[0]["revenue"] / (1.0 + base_g1)))
    else:
        base_g1 = float(snapshot.get("g1", 0.08))
        base_margin = float(snapshot.get("ebit_margin", 0.15))
        rev0 = float(snapshot.get("revenue", 10000e9))

    sd_g = float(hist_std.get("rev_growth_sd", hist_std.get("growth_sd", 0.03)))
    sd_m = float(hist_std.get("ebit_margin_sd", hist_std.get("margin_sd", 0.01)))

    specs = {
        "BULL": {
            "g1": base_g1 + k * sd_g,
            "margin": base_margin + k * sd_m,
            "g_term": g_base + g_shift,
        },
        "BASE": {
            "g1": base_g1,
            "margin": base_margin,
            "g_term": g_base,
        },
        "BEAR": {
            "g1": base_g1 - k * sd_g,
            "margin": max(base_margin - k * sd_m, 0.01),
            "g_term": max(g_base - g_shift, 0.0),
        },
    }

    scen_out: Dict[str, Any] = {}
    for name in ("BEAR", "BASE", "BULL"):
        s = specs[name]
        proj_sc = project_fcff_simple(
            revenue_t0=rev0,
            g1=s["g1"],
            g_terminal=s["g_term"],
            years=years,
            ebit_margin=s["margin"],
            tax=tax,
            capex_pct=capex_pct,
            nwc_pct=nwc_pct,
            da_pct=da_pct,
        )
        fcff_last = proj_sc[-1]["fcff"]
        ebitda_last = proj_sc[-1]["ebit"] + proj_sc[-1]["da"]
        tv = terminal_value_gordon(fcff_last, wacc_base, s["g_term"], ebitda_last=ebitda_last, min_spread=0.04, flags=None)
        if tv.get("valid"):
            v = discount_and_bridge(proj_sc, wacc_base, tv, snapshot, data, flags=_NullFlags())
            rec = make_recommendation(v)
            scen_out[name] = {
                "scenario": name,
                "revenue_growth_y1": round(s["g1"], 6),
                "ebit_margin": round(s["margin"], 6),
                "terminal_growth": round(s["g_term"], 6),
                "fair_value_per_share": round(v["fair_value_per_share"], 2),
                "upside": round(v["upside"], 6) if v.get("upside") is not None else None,
                "rating": rec["rating"],
                "note": rec.get("note", ""),
            }
        else:
            scen_out[name] = {
                "scenario": name,
                "revenue_growth_y1": round(s["g1"], 6),
                "ebit_margin": round(s["margin"], 6),
                "terminal_growth": round(s["g_term"], 6),
                "fair_value_per_share": None,
                "upside": None,
                "rating": "N/A",
                "note": tv.get("reason", ""),
            }

    return {
        "BEAR": scen_out["BEAR"],
        "BASE": scen_out["BASE"],
        "BULL": scen_out["BULL"],
    }


def _load_ticker_assumptions(ticker: str) -> Dict[str, Any]:
    """Load valuation assumptions for ticker — FILE ONLY (LOUD, Sep 2026).

    KILLED: the five hardcoded per-ticker seed bases (MTEL/TOWR/TLKM, RATU,
    CDIA, BBCA, ADRO with invented revenue/ebitda/shares/last_price) plus the
    generic dummy base and the README.json/seed_assumptions.json side-paths.
    Only data/assumptions/{T}.json counts; anything else raises ValueError
    naming the missing file. Callers: pass explicit overrides or stop.
    """
    t = ticker.upper().strip()
    fp = pathlib.Path(f"data/assumptions/{t}.json")
    base: Dict[str, Any] = {"ticker": t}
    if fp.exists():
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                if t in data and isinstance(data[t], dict):
                    base.update({k: v for k, v in data[t].items() if v is not None})
                elif data.get("ticker") == t:
                    base.update({k: v for k, v in data.items() if v is not None})
        except Exception:
            pass
    if len(base) <= 1:
        raise ValueError(
            f"no assumptions for {t}: add data/assumptions/{t}.json "
            f"(hardcoded seed bases killed Sep 2026 — refusing invented DCF)")
    return base


def dcf_full(ticker: str, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Complete DCF valuation including WACC breakdown, FCFF projection, Gordon TV,

    EV/Equity bridge, Recommendation rating with gates, WACC x g Sensitivity grid,
    and Bull/Base/Bear scenarios. Ported from friend's s05-s12 math.
    """
    assum = _load_ticker_assumptions(ticker)
    if overrides:
        assum.update(overrides)

    # LOUD gate (Sep 2026, no-fabrication sweep): valuation-driving inputs must
    # be explicit (file or overrides) — no silent .get() invention. Display /
    # scenario knobs (years, sens steps, thresholds, sds) keep safe defaults.
    _need = ["rf", "beta", "erp", "cod", "revenue", "ebit_margin", "g1",
             "tax", "capex_pct", "nwc_pct"]
    _missing = [k for k in _need if assum.get(k) is None]
    if assum.get("g") is None and assum.get("g_terminal") is None:
        _missing.append("g|g_terminal")
    if assum.get("shares_out") is None and assum.get("shares_outstanding") is None:
        _missing.append("shares_out|shares_outstanding")
    if assum.get("last_price") is None and assum.get("price") is None:
        _missing.append("last_price|price")
    if _missing:
        raise ValueError(
            f"dcf_full({ticker.upper().strip()}): missing explicit inputs "
            f"{', '.join(_missing)} (file data/assumptions/*.json or overrides; "
            f"seed defaults killed Sep 2026)")

    rf = float(assum.get("rf", 0.065))
    beta = float(assum.get("beta", 1.0))
    erp = float(assum.get("erp", 0.07))
    cod = float(assum.get("cod", 0.085))
    market_cap = float(assum.get("market_cap", (assum.get("shares_out", 1e9) * assum.get("last_price", 1000))))
    total_debt = float(assum.get("total_debt", 0.0))
    tax = float(assum.get("tax", 0.22))
    size_premium = float(assum.get("size_premium", 0.0))

    # 1. WACC
    wacc_res = compute_wacc_full(
        rf=rf,
        beta=beta,
        erp=erp,
        cod=cod,
        market_cap=market_cap,
        total_debt=total_debt,
        tax=tax,
        size_premium=size_premium,
    )
    wacc_val = float(assum.get("wacc_override", wacc_res["wacc"]))
    if "wacc_override" in assum:
        # Honour the override in the displayed breakdown table + provenance so the
        # FE/PDF WACC matches the analyst's intended rate even if the floor logic
        # pushed the computed value higher.
        wacc_res = {**wacc_res, "wacc": wacc_val, "wacc_raw": wacc_val}
    wacc_table = wacc_table_dict(wacc_res)

    # 2. Forecast
    rev0 = float(assum.get("revenue", 10000e9))
    g1 = float(assum.get("g1", 0.08))
    g_terminal = float(assum.get("g_terminal", assum.get("g", 0.025)))
    years = int(assum.get("years", 5))
    ebit_margin = float(assum.get("ebit_margin", 0.15))
    capex_pct = float(assum.get("capex_pct", 0.06))
    nwc_pct = float(assum.get("nwc_pct", 0.10))
    da_pct = float(assum.get("da_pct", 0.04)) if "da_pct" in assum else None

    proj = project_fcff_simple(
        revenue_t0=rev0,
        g1=g1,
        g_terminal=g_terminal,
        years=years,
        ebit_margin=ebit_margin,
        tax=tax,
        capex_pct=capex_pct,
        nwc_pct=nwc_pct,
        da_pct=da_pct,
    )

    # 3. Terminal value
    fcff_final = float(proj[-1]["fcff"])
    ebitda_final = float(proj[-1]["ebit"] + proj[-1]["da"])
    tv_res = terminal_value_gordon(
        fcff_last=fcff_final,
        wacc=wacc_val,
        g=g_terminal,
        ebitda_last=ebitda_final,
    )

    # 4. Valuation bridge
    snapshot = {
        "cash": float(assum.get("cash", 0.0)),
        "total_debt": total_debt,
        "minority": float(assum.get("minority", 0.0)),
        "ebitda": float(assum.get("ebitda", ebitda_final)),
        "revenue": rev0,
    }
    data_dict = {
        "shares_outstanding": float(assum.get("shares_out", assum.get("shares_outstanding", 1.0))),
        "price": float(assum.get("last_price", assum.get("price", 1000.0))),
    }
    val_res = discount_and_bridge(
        proj=proj,
        wacc=wacc_val,
        terminal_value=tv_res,
        snapshot=snapshot,
        data=data_dict,
        mid_year=bool(assum.get("mid_year", True)),
    )

    # 5. Recommendation
    thresholds = {
        "buy": float(assum.get("buy_threshold", 0.10)),
        "sell": float(assum.get("sell_threshold", -0.10)),
        "review_up": float(assum.get("review_upside_threshold", 1.00)),
        "review_down": float(assum.get("review_downside_threshold", -0.50)),
    }
    rec_res = make_recommendation(val_res, thresholds=thresholds)

    # 6. Sensitivity grid
    sens_res = sensitivity_grid(
        proj=proj,
        wacc_base=wacc_val,
        g_base=g_terminal,
        snapshot=snapshot,
        data=data_dict,
        steps=int(assum.get("sens_steps", 2)),
        wacc_step=float(assum.get("sens_wacc_step", 0.005)),
        g_step=float(assum.get("sens_g_step", 0.0025)),
    )

    # 7. Bull/Base/Bear scenarios
    hist_std = {
        "rev_growth_sd": float(assum.get("growth_sd", 0.03)),
        "ebit_margin_sd": float(assum.get("margin_sd", 0.01)),
    }
    scen_res = scenarios_bull_bear(
        proj_or_params=proj,
        wacc_base=wacc_val,
        g_base=g_terminal,
        hist_std=hist_std,
        snapshot=snapshot,
        data=data_dict,
        years=years,
        tax=tax,
        capex_pct=capex_pct,
        nwc_pct=nwc_pct,
        da_pct=da_pct,
    )

    rec_payload: Dict[str, Any] = {
        "rating": rec_res.get("rating"),
        "upside": rec_res.get("upside"),
        "label": rec_res.get("label"),
        "note": rec_res.get("note"),
    }
    if "reason_override" in rec_res:
        rec_payload["reason_override"] = rec_res["reason_override"]

    return {
        "wacc": wacc_res,
        "wacc_table": wacc_table,
        "projection": proj,
        "terminal": {
            "value": tv_res.get("tv_nominal"),
            "pv": val_res.get("pv_terminal"),
            "implied_ev_ebitda": tv_res.get("implied_exit_multiple"),
            "dependency_pct": val_res.get("tv_share_of_ev"),
            "dependency_flag": val_res.get("tv_dependency_flag"),
        },
        "valuation": {
            "pv_explicit": val_res.get("pv_explicit"),
            "pv_terminal": val_res.get("pv_terminal"),
            "enterprise_value": val_res.get("enterprise_value"),
            "equity_value": val_res.get("equity_value"),
            "fair_value_per_share": val_res.get("fair_value_per_share"),
            "market_price": val_res.get("market_price"),
            "upside": val_res.get("upside"),
            # Bridge inputs (so SVG waterfall + reviewer can see net-debt build):
            "cash": snapshot.get("cash"),
            "total_debt": snapshot.get("total_debt"),
            "minority": snapshot.get("minority"),
            "ebitda": snapshot.get("ebitda"),
            "shares_outstanding": data_dict.get("shares_outstanding"),
            "last_price": data_dict.get("price"),
        },
        "recommendation": rec_payload,
        "sensitivity": sens_res,
        "scenarios": scen_res,
        "provenance": "dcf_full: wacc+sens+scenarios from friend's s05-s12",
    }


def _parse_list(s: str) -> List[float]:
    return [float(x) for x in s.replace("[", "").replace("]", "").split(",") if x.strip()]


def main() -> None:
    ap = argparse.ArgumentParser(description="DCF / WACC / EV/EBITDA engine")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("wacc")
    for a in ("rf", "beta", "erp", "cod", "we", "wd", "tax"):
        p.add_argument(f"--{a}", type=float, required=(a in ("rf", "beta", "erp", "cod")))

    p = sub.add_parser("dcf")
    p.add_argument("--fcf", type=str, required=True)
    p.add_argument("--wacc", type=float, required=True)
    p.add_argument("--g", type=float, required=True)
    p.add_argument("--shares", type=float, default=1.0)
    p.add_argument("--cash", type=float, default=0.0)
    p.add_argument("--net-debt", type=float, default=0.0)
    p.add_argument("--tv", type=float, default=None)
    p.add_argument("--mid-year", action="store_true")
    p.add_argument("--year0", action="store_true")
    p.add_argument("--fcfe", action="store_true")

    p = sub.add_parser("ev_ebitda")
    for a in ("ebitda", "multiple", "shares", "net_debt", "cash"):
        p.add_argument(f"--{a}", type=float, required=(a in ("ebitda", "multiple")))

    p = sub.add_parser("dcf_full")
    p.add_argument("--ticker", type=str, required=True)

    args = ap.parse_args()
    if args.cmd == "wacc":
        out = wacc(args.rf, args.beta, args.erp, args.cod, args.we, args.wd, args.tax)
    elif args.cmd == "dcf":
        out = dcf(
            _parse_list(args.fcf), args.wacc, args.g, args.shares, args.cash,
            args.net_debt, args.tv, args.mid_year, args.year0, args.fcfe,
        )
    elif args.cmd == "ev_ebitda":
        out = ev_ebitda(args.ebitda, args.multiple, args.shares, args.net_debt, args.cash)
    elif args.cmd == "dcf_full":
        out = dcf_full(args.ticker)
    else:
        out = {"error": "unknown command"}
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

