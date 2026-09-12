"""Deterministic valuation engines — Server owns the math.
Mirrors scripts/{dcf,ddm,sotp,blended,bands,ggm}.py from plan section 6.
All formulas explicit, auditable, no LLM math.
Units: all currency in IDR (full rupiah, not billions) unless noted. Keep consistent!
"""
from typing import List, Dict, Any


def pick_fv_anchor(assum: Dict[str, Any], dcf_fv: Any, ev_fv: Any) -> dict:
    """Which valuation leg anchors the headline fair value.

    The assumptions file carries the report's OWN gate decision (`gate_primary`, `dcf_role`),
    and the anchor must be that leg — not DCF-by-default. AMMN is the case that exposed it:
    the file says `gate_primary = "EV/EBITDA mid-cycle (REL)"` and `dcf_role = "Comparison-only,
    NOT the anchor ... punitive by construction"` (that DCF subtracts Rp 110.8 tn gross debt),
    while the headline FV came from the DCF leg — the cover read SELL at −96.97% when the
    file's own anchor implied +20.8%. Rating, TP and every valuation table follow this number,
    so anchoring on the wrong leg is a wrong report.

    A primary the engines do not implement (NAV/SOTP/DDM) raises instead of quietly falling
    back to DCF, so the caller can 422 by name (LOUD policy).
    """
    gp = str((assum or {}).get("gate_primary") or "").strip()
    low = gp.lower()
    if "ev/ebitda" in low or "rel" in low:
        return {"leg": "ev_ebitda", "fv": ev_fv, "basis": f"gate_primary: {gp}"}
    if "dcf" in low:
        return {"leg": "dcf", "fv": dcf_fv, "basis": f"gate_primary: {gp}"}
    if not low:
        return {"leg": "dcf", "fv": dcf_fv,
                "basis": "DCF (no gate_primary in the assumptions file)"}
    raise ValueError(
        f"gate_primary '{gp}' names a method no engine implements yet (NAV/SOTP/DDM): "
        f"refusing to anchor the fair value on the DCF leg instead. Wire the engine or "
        f"change gate_primary in data/assumptions/<TICKER>.json."
    )


def wacc(rf: float, beta: float, erp: float, cod: float, we: float = 0.608, wd: float = 0.392, tax: float = 0.22) -> dict:
    """WACC = We*CoE + Wd*CoD*(1-tax), CoE = Rf + beta*ERP"""
    coe = rf + beta * erp
    cod_after_tax = cod * (1 - tax)
    w = we * coe + wd * cod_after_tax
    return {"wacc": round(w, 5), "coe": round(coe, 5), "cod_after_tax": round(cod_after_tax, 5)}


def dcf(fcf: List[float], wacc_val: float, g_terminal: float, shares_out: float, net_debt: float = 0, cash: float = 0) -> dict:
    """Classic DCF: discount FCFs + Gordon terminal. fcf = annual FCFs in IDR (same unit as cash/net_debt)."""
    if wacc_val <= g_terminal:
        raise ValueError("WACC must exceed g")
    disc: List[dict] = []
    pv_sum = 0.0
    for i, cf in enumerate(fcf, 1):
        cf_f = float(cf)
        df = (1 + wacc_val) ** i
        pv = cf_f / df
        disc.append({"year": i, "fcf": cf_f, "df": round(df, 4), "pv": round(pv, 2)})
        pv_sum += pv
    terminal_fcf = float(fcf[-1]) * (1 + g_terminal)
    terminal_value = terminal_fcf / (wacc_val - g_terminal)
    terminal_pv = terminal_value / ((1 + wacc_val) ** len(fcf))
    firm_value = pv_sum + terminal_pv
    equity_value = firm_value + cash - net_debt
    fv_per_share = equity_value / shares_out if shares_out else 0
    return {
        "firm_value": round(firm_value, 2),
        "equity_value": round(equity_value, 2),
        "fv_per_share": round(fv_per_share, 2),
        "terminal_value": round(terminal_value, 2),
        "terminal_pv": round(terminal_pv, 2),
        "discounted": disc,
        "provenance": "dcf: Gordon g terminal",
    }


def ddm(dividends: List[float], coe: float, g_terminal: float, shares_out: float = 1) -> dict:
    """Dividend Discount Model — for banks/dividend payers (CDIA pilar)."""
    if coe <= g_terminal:
        raise ValueError("CoE must exceed g")
    pv_sum = 0.0
    disc: List[dict] = []
    for i, d in enumerate(dividends, 1):
        pv = float(d) / ((1 + coe) ** i)
        disc.append({"year": i, "div": float(d), "pv": round(pv, 2)})
        pv_sum += pv
    term_div = float(dividends[-1]) * (1 + g_terminal)
    tv = term_div / (coe - g_terminal)
    tv_pv = tv / ((1 + coe) ** len(dividends))
    equity = pv_sum + tv_pv
    fv = equity / shares_out if shares_out else equity
    return {"equity_value": round(equity, 2), "fv_per_share": round(fv, 2), "terminal_value": round(tv, 2), "discounted": disc}


def ev_ebitda(ebitda: float, multiple: float, net_debt: float, shares_out: float, cash: float = 0) -> dict:
    ev = float(ebitda) * multiple
    equity = ev - net_debt + cash
    fv = equity / shares_out if shares_out else 0
    return {"ev": round(ev, 2), "equity_value": round(equity, 2), "fv_per_share": round(fv, 2), "multiple": multiple}


def ggm(roe: float, g: float, coe: float, bvps: float) -> dict:
    """Gordon Growth implied P/BV = (ROE - g)/(CoE - g) — Samuel BBCA fallback."""
    if coe <= g:
        raise ValueError("CoE must exceed g")
    pbv = (roe - g) / (coe - g)
    fv = pbv * bvps
    return {"pbv_implied": round(pbv, 3), "fv_per_share": round(fv, 2), "formula": "P/BV=(ROE-g)/(CoE-g)"}


def sotp(segments: List[dict]) -> dict:
    """Sum-of-the-parts: segments = [{name, value, weight?}]"""
    total = sum(float(s.get("value", 0)) for s in segments)
    for s in segments:
        s["pct"] = round((float(s.get("value", 0)) / total * 100) if total else 0, 1)
    return {"segments": segments, "total": round(total, 2), "holdco_discount": 0.15, "total_after_discount": round(total * 0.85, 2)}


def blended(valuations: Dict[str, float], weights: Dict[str, float]) -> dict:
    """Blended weighted TP — MTEL 60/40. weights must sum to 1.0"""
    s = sum(weights.values())
    if abs(s - 1.0) > 1e-6:
        raise ValueError(f"weights sum {s} != 1.0")
    blended_val = sum(float(valuations[k]) * float(weights[k]) for k in valuations if k in weights)
    return {"blended": round(blended_val, 2), "components": valuations, "weights": weights, "check_sum": round(s, 4)}


def historical_bands(prices: List[float]) -> dict:
    """PBV/EV bands: STD+2/+1/AVG/-1/-2 — needs 3Y daily. Fallback if short."""
    import statistics

    if len(prices) < 10:
        return {"error": "insufficient history for bands", "n": len(prices)}
    avg = statistics.mean(prices)
    sd = statistics.pstdev(prices)
    return {
        "avg": round(avg, 3),
        "sd": round(sd, 3),
        "std_plus_2": round(avg + 2 * sd, 3),
        "std_plus_1": round(avg + sd, 3),
        "std_minus_1": round(avg - sd, 3),
        "std_minus_2": round(avg - 2 * sd, 3),
        "n": len(prices),
    }


def ratios(fin: dict) -> dict:
    """Key ratios from a minimal financial snapshot — deterministic."""
    out: dict[str, Any] = {}
    try:
        if fin.get("revenue"):
            out["npm"] = round(fin.get("net_income", 0) / fin["revenue"] * 100, 2)
            out["ebitda_margin"] = round(fin.get("ebitda", 0) / fin["revenue"] * 100, 2)
        if fin.get("equity"):
            out["roe"] = round(fin.get("net_income", 0) / fin["equity"] * 100, 2)
        if fin.get("assets"):
            out["roa"] = round(fin.get("net_income", 0) / fin["assets"] * 100, 2)
            out["dar"] = round(fin.get("debt", 0) / fin["assets"] * 100, 2)
        if fin.get("equity") and fin.get("debt") is not None:
            out["der"] = round(fin["debt"] / fin["equity"] if fin["equity"] else 0, 3)
        if fin.get("ebit") and fin.get("interest") is not None:
            out["icr"] = round(fin["ebit"] / fin["interest"] if fin["interest"] else 0, 2)
    except Exception:
        pass
    return out


# Ported from friend's s05-s12 via scripts.dcf_engine
from scripts.dcf_engine import (
    beta_blume_adj,
    compute_wacc_full,
    wacc_table_dict,
    project_fcff_simple,
    terminal_value_gordon,
    tv_dependency_check,
    discount_and_bridge,
    make_recommendation,
    sensitivity_grid,
    scenarios_bull_bear,
    _NullFlags,
    dcf_full,
)

__all__ = [
    "pick_fv_anchor",
    "wacc",
    "dcf",
    "ddm",
    "ev_ebitda",
    "ggm",
    "sotp",
    "blended",
    "historical_bands",
    "ratios",
    "beta_blume_adj",
    "compute_wacc_full",
    "wacc_table_dict",
    "project_fcff_simple",
    "terminal_value_gordon",
    "tv_dependency_check",
    "discount_and_bridge",
    "make_recommendation",
    "sensitivity_grid",
    "scenarios_bull_bear",
    "_NullFlags",
    "dcf_full",
]

