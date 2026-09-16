"""Normalised own-history multiple - the multiple and the level it multiplies must share a basis.

The deck used to apply a trailing EV/EBITDA mean (28.42x, measured in years when EBITDA was depressed by
the smelter build) to a recovered mid-cycle level. That double-counts the recovery: the multiple was high
BECAUSE earnings were low. This module measures each print year's multiple against the NORMALISED earnings
power of that year (rolling 3-year average EBITDA), so the multiple means "what the market paid for a
normalised earnings stream" and can be applied to a normalised forward stream without double counting.

Reconstruction, all from the licensed dataset:
  market cap_t = P/E_t x net income_t            (P/E and net income both published per year)
  EV_t         = market cap_t + total debt_t - cash_t
  level_t      = rolling 3-year average EBITDA ending at t
  multiple_t   = EV_t / level_t

The module also re-derives the trailing multiple each year and checks it against the dataset's own
`enterprise_to_ebitda` print, so a silent reconstruction error cannot pass.
"""
from __future__ import annotations

from typing import Any, Optional


def _num(v: Any) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f == f else None


def _bn(v: Any) -> Optional[float]:
    n = _num(v)
    return n / 1e9 if n is not None else None


def normalised_multiple_history(
    annual_rows: list[dict],
    prints: list[dict],
    *,
    rolling: int = 3,
) -> dict:
    """Per-print-year EV / rolling-normalised EBITDA, plus the trailing series for comparison."""
    by_year = {int(r["year"]): r for r in annual_rows if _num(r.get("year")) is not None}
    years = sorted(by_year)
    out: list[dict] = []
    trailing_elements: list[float] = []
    normalised_elements: list[float] = []
    check_gaps: list[float] = []

    for p in sorted(prints, key=lambda x: int(x.get("year", 0))):
        y = int(_num(p.get("year")) or 0)
        row = by_year.get(y)
        if row is None:
            continue
        net = _bn(row.get("earnings"))
        pe = _num(p.get("pe"))
        ebitda = _bn(row.get("ebitda"))
        cash = _bn(row.get("cash_and_equivalents")) if _bn(row.get("cash_and_equivalents")) is not None \
            else _bn(row.get("cash_only"))
        debt = sum(v for v in (_bn(row.get("long_term_debt")), _bn(row.get("short_term_debt"))) if v)
        if not all(x is not None for x in (net, pe, ebitda)) or not debt:
            continue
        mcap = pe * net
        ev = mcap + debt - (cash or 0.0)
        n = len(out) + 1  # calendar-progressive only; the rolling window is by year, not by row order
        window = [y - k for k in range(rolling)]
        vals = [_bn(by_year[w].get("ebitda")) for w in window if w in by_year]
        vals = [v for v in vals if v is not None]
        norm = sum(vals) / len(vals) if len(vals) == rolling else None
        rec = {
            "year": y, "mcap_rp_bn": mcap, "debt_rp_bn": debt, "cash_rp_bn": cash or 0.0,
            "ev_rp_bn": ev, "ebitda_rp_bn": ebitda,
            "trailing_multiple": ev / ebitda if ebitda else None,
            "dataset_print": _num(p.get("enterprise_to_ebitda")),
            "normalised_ebitda_rp_bn": norm,
            "normalised_multiple": ev / norm if norm else None,
            "window_years": [w for w in window if w in by_year],
            "n": n,
        }
        out.append(rec)
        if rec["trailing_multiple"]:
            trailing_elements.append(rec["trailing_multiple"])
        if rec["normalised_multiple"]:
            normalised_elements.append(rec["normalised_multiple"])
        if rec["trailing_multiple"] and rec["dataset_print"]:
            check_gaps.append(abs(rec["trailing_multiple"] - rec["dataset_print"]))

    def med(xs: list[float]) -> Optional[float]:
        if not xs:
            return None
        s = sorted(xs)
        m = len(s) // 2
        return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2

    return {
        "rows": out,
        "normalised_mean": (sum(normalised_elements) / len(normalised_elements)) if normalised_elements else None,
        "normalised_median": med(normalised_elements),
        "trailing_mean": (sum(trailing_elements) / len(trailing_elements)) if trailing_elements else None,
        "trailing_median": med(trailing_elements),
        "max_reconstruction_gap": max(check_gaps) if check_gaps else None,
        "rolling": rolling,
    }


def apply_multiple(multiple: float, level_rp_bn: float, cash_rp_bn: float, gross_debt_rp_bn: float,
                   shares_bn: float) -> dict:
    """Equity value and per-share value from a multiple applied to a normalised level."""
    ev = multiple * level_rp_bn
    equity = ev + cash_rp_bn - gross_debt_rp_bn
    return {"ev_rp_bn": ev, "equity_rp_bn": equity,
            "per_share": (equity / shares_bn) if shares_bn else None}
