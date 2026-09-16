"""2A+4F financial-exhibit projection math - the SINGLE home for forecast arithmetic.

Scheme (reviewer demand): financial exhibits carry the last 2 actual fiscal years
only (FY-1A, FY0A e.g. FY24A/FY25A) plus a minimum 4 forecast years
(FY+1F..FY+4F e.g. FY26F..FY29F) - 6 columns total with explicit A/F labels.

Formula (every cell traceable):
    forecast_t = last_actual x (1 + g)^t,   t = 1..4
where g comes from the ticker assumptions (revenue_growth et al.) modulated by
the news/sentiment overlay in `.assumptions.adjust_assumptions` when news or
sentiment payloads are present. Each projected cell records its base, g, t,
formula and source string - no silent numbers.

Callers: server/routers/pdf.py (live inline payload), scripts/report_fixtures.py
helpers, and the ACES JSON fixture (pre-computed with this module; growth rates
+ sources embedded in the fixture source strings).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .assumptions import adjust_assumptions
from server.report import numfmt as _nf

N_ACTUAL = 2
N_FORECAST = 4

#: Assumption keys consulted for the revenue-line growth rate, in priority order.
REVENUE_GROWTH_KEYS = ("revenue_growth", "rev_growth", "sales_growth", "revenue_cagr")
#: Assumption keys consulted for the bottom-line growth rate, in priority order.
EARNINGS_GROWTH_KEYS = ("earnings_growth", "ni_growth", "net_income_growth", "profit_growth")


def project_series(base: float, g: float, periods: int = N_FORECAST) -> List[float]:
    """Project `periods` forecast points as base x (1+g)^t for t = 1..periods."""
    return [base * ((1.0 + g) ** t) for t in range(1, periods + 1)]


def _pick_g(base_assumptions: Dict[str, Any], keys: Tuple[str, ...]) -> Tuple[Optional[float], Optional[str]]:
    """Return (g, assumption_key) for the first matching numeric key, else (None, None)."""
    for k in keys:
        v = (base_assumptions or {}).get(k)
        if isinstance(v, (int, float)):
            return float(v), k
    return None, None


def resolve_growth(
    base_assumptions: Optional[Dict[str, Any]] = None,
    keys: Tuple[str, ...] = REVENUE_GROWTH_KEYS,
    fallback_g: float = 0.0,
    news: Any = None,
    sentiment: Any = None,
) -> Dict[str, Any]:
    """Resolve the effective growth rate after the news/sentiment overlay.

    Returns dict with: g (effective), base_g (pre-overlay), g_key (assumption key
    or 'fallback_g'), multiplier provenance (revenue_growth_multiplier,
    sentiment_score, news_count_last_30d, avg_news_sentiment, notes) so every
    downstream cell can cite where g came from.
    """
    base_assumptions = dict(base_assumptions or {})
    base_g, g_key = _pick_g(base_assumptions, keys)
    if base_g is None:
        base_g, g_key = float(fallback_g), "fallback_g"
    adjusted = adjust_assumptions("GEN", base_assumptions, news=news, sentiment=sentiment)
    # Effective g: overlay multiplies the matching revenue-line key when present;
    # otherwise apply the documented revenue multiplier directly to base_g.
    eff_g: Optional[float] = None
    for k in keys:
        if k in adjusted and isinstance(adjusted[k], (int, float)):
            eff_g, g_key = float(adjusted[k]), k
            break
    if eff_g is None:
        eff_g = float(base_g) * float(adjusted.get("revenue_growth_multiplier", 1.0))
    return {
        "g": round(eff_g, 6),
        "base_g": round(float(base_g), 6),
        "g_key": g_key,
        "revenue_growth_multiplier": adjusted.get("revenue_growth_multiplier", 1.0),
        "sentiment_score": adjusted.get("sentiment_score"),
        "news_count_last_30d": adjusted.get("news_count_last_30d", 0),
        "avg_news_sentiment": adjusted.get("avg_news_sentiment", 0.0),
        "notes": adjusted.get("notes", []),
    }


def build_trend_forecast(
    actuals: Dict[str, List[float]],
    growth: Dict[str, float],
    sources: Dict[str, str],
    years: Optional[List[str]] = None,
    base_year: int = 2025,
    ndigits: int = 0,
) -> Dict[str, Any]:
    """Build full 6-column (2A+4F) series with per-cell traceability.

    actuals: metric -> [FY-1A value, FY0A value] (exactly the last 2 actuals).
    growth:  metric -> g (decimal, e.g. 0.022). Use resolve_growth() upstream
             when g must reflect the news/sentiment overlay.
    sources: metric -> source string citing the growth rate provenance
             (e.g. "g=+2,2% SSSG H1-2026 (Kontan 2026-07-21)").
    years:   explicit 6 labels; default FY{base_year-1}A..FY{base_year+4}F.
    Returns {"years", "series": {metric: [6 values]}, "traces": {metric: [6 cells]}},
    where each trace cell is {metric, year, kind: 'A'|'F', value, base, g, t,
    formula, source}.
    """
    if years is None:
        y0 = base_year
        years = [
            f"FY{str(y0 - 1)[-2:]}A",
            f"FY{str(y0)[-2:]}A",
            f"FY{str(y0 + 1)[-2:]}F",
            f"FY{str(y0 + 2)[-2:]}F",
            f"FY{str(y0 + 3)[-2:]}F",
            f"FY{str(y0 + 4)[-2:]}F",
        ]
    assert len(years) == N_ACTUAL + N_FORECAST, f"2A+4F scheme needs 6 year labels, got {len(years)}"
    assert all(y.endswith("A") for y in years[:N_ACTUAL]), f"first 2 labels must end with 'A': {years}"
    assert all(y.endswith("F") for y in years[N_ACTUAL:]), f"last 4 labels must end with 'F': {years}"

    out_series: Dict[str, List[float]] = {}
    out_traces: Dict[str, List[Dict[str, Any]]] = {}
    for metric, vals in actuals.items():
        assert len(vals) == N_ACTUAL, f"{metric}: need exactly 2 actuals [FY-1A, FY0A], got {vals}"
        g = float(growth[metric])
        src = sources.get(metric, "g source undisclosed")
        base = float(vals[-1])
        raw = list(vals) + project_series(base, g, N_FORECAST)
        series = [round(float(v), ndigits) for v in raw]
        cells: List[Dict[str, Any]] = []
        for i, (yr, v) in enumerate(zip(years, series)):
            if i < N_ACTUAL:
                cells.append({"metric": metric, "year": yr, "kind": "A", "value": v,
                              "base": None, "g": None, "t": 0,
                              "formula": "actual (sectors-verified)",
                              "source": "actual"})
            else:
                t = i - N_ACTUAL + 1
                cells.append({"metric": metric, "year": yr, "kind": "F", "value": v,
                              "base": base, "g": round(g, 6), "t": t,
                              "formula": f"{base} x (1+{_nf.dec(g, digits=4)})^{t}",
                              "source": src})
        out_series[metric] = series
        out_traces[metric] = cells
    return {"years": years, "series": out_series, "traces": out_traces}


def describe_g_source(g: float, provenance: str) -> str:
    """One-line source fragment for fixture/template source strings."""
    pct = f"{_nf.dec(g * 100, digits=1, signed=True)}%".replace(".", ",")
    return f"g={pct} ({provenance})"
