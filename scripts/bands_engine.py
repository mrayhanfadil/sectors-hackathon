"""Deterministic Historical Valuation Bands engine (PBV, EV/EBITDA, P/E).

Part of T02 — Deterministic Engines (Python, NOT LLM math).
Mirrors server/engines/__init__.py historical_bands() and finance_tools.calc_historical_bands().

Methodology:
  Given a historical time-series of valuation multiples (3Y/5Y daily or monthly):
    Mean (mu) = sum(x_i) / N
    Std Dev (sigma) = sqrt(sum((x_i - mu)^2) / N)
    Bands:
      +2 SD = mu + 2 * sigma
      +1 SD = mu + 1 * sigma
      Mean  = mu
      -1 SD = mu - 1 * sigma
      -2 SD = mu - 2 * sigma

  Positioning Labels:
    x > +2 SD           -> "> +2SD (OVERBOUGHT)"
    +1 SD < x <= +2 SD  -> "+1SD TO +2SD"
    mu < x <= +1 SD     -> "ABOVE AVG"
    -1 SD <= x <= mu    -> "BELOW AVG"
    -2 SD <= x < -1 SD  -> "-1SD TO -2SD"
    x < -2 SD           -> "< -2SD (OVERSOLD)"

  Mean-Reversion Upside:
    Upside to Mean (%) = (mu / current - 1) * 100
    Upside to +1SD (%) = ((mu + sigma) / current - 1) * 100

Benchmarks & Archetypes:
  * MTEL (KSI 27 Aug 2026, plan §2.3 / §59):
    3Y PBV band: STD+2 (2.9x), STD+1 (2.5x), AVG (2.1x), STD-1 (1.7x), STD-2 (1.3x)
    Current PBV = 1.47x -> "BELOW AVG"
  * Maybank Strategy (2 Jan 2025, references/local-global-like/maybank-strategy.md):
    JCI Forward P/E at 11.8x (-2 SD vs 10Y avg 15.2x)
  * Samuel Strategy (Dec 2023, references/local-global-like/samuel-strategy.md):
    JCI 5Y P/E Band (Fig 73: +2/+1/Mean/-1/-2 SD)
  * BRIDS GOTO (18 Nov 2024, references/local-global-like/brids-ADRO-GOTO.md):
    EV/Gross Revenue multiple at -1 SD of 2.5Y mean
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from typing import Any, Dict, List, Optional


def calc_bands(
    series: List[float],
    current: Optional[float] = None,
    fundamental_base: Optional[float] = None,
    metric_name: str = "P/BV",
) -> Dict[str, Any]:
    """Calculate historical mean, standard deviation, and ±1/±2 sigma valuation bands.

    Args:
        series: Historical valuation multiples (e.g. 3Y daily/monthly P/BV or EV/EBITDA).
        current: Current multiple value (e.g. 1.47 for MTEL P/BV).
        fundamental_base: Optional fundamental driver (e.g. BVPS, EPS, or EBITDA per share)
                          to generate implied target price at each band level.
        metric_name: Label for the multiple (e.g. 'P/BV', 'EV/EBITDA', 'P/E').

    Returns:
        Dict with mean, std dev, 5 band levels, percentiles, current positioning,
        z-score, positioning label, mean-reversion upside, and optional price targets.
    """
    if not series:
        raise ValueError("series must be non-empty")
    if len(series) < 2:
        raise ValueError(f"series must have at least 2 points, got {len(series)}")

    n = len(series)
    avg = float(statistics.mean(series))
    # Use population stdev for full census of historical period or sample if requested
    sd = float(statistics.pstdev(series)) if n > 1 else 0.0

    std_plus_2 = avg + 2.0 * sd
    std_plus_1 = avg + 1.0 * sd
    std_minus_1 = avg - 1.0 * sd
    std_minus_2 = avg - 2.0 * sd

    sorted_s = sorted(series)
    percentiles = {
        "p10": round(sorted_s[int(0.10 * (n - 1))], 3),
        "p25": round(sorted_s[int(0.25 * (n - 1))], 3),
        "p50_median": round(sorted_s[int(0.50 * (n - 1))], 3),
        "p75": round(sorted_s[int(0.75 * (n - 1))], 3),
        "p90": round(sorted_s[int(0.90 * (n - 1))], 3),
    }

    bands_dict = {
        "std_plus_2": round(std_plus_2, 3),
        "std_plus_1": round(std_plus_1, 3),
        "avg": round(avg, 3),
        "std_minus_1": round(std_minus_1, 3),
        "std_minus_2": round(std_minus_2, 3),
    }

    out: Dict[str, Any] = {
        "metric": metric_name,
        "n_samples": n,
        "avg": round(avg, 3),
        "sd": round(sd, 3),
        "bands": bands_dict,
        "percentiles": percentiles,
        "min": round(min(series), 3),
        "max": round(max(series), 3),
        "provenance": f"Historical bands over {n} points: mean +/- 1SD, +/- 2SD",
    }

    if current is not None:
        c = float(current)
        z = (c - avg) / sd if sd > 1e-9 else 0.0
        # Determine qualitative position label
        if c > std_plus_2:
            label = "> +2SD (OVERBOUGHT)"
        elif c > std_plus_1:
            label = "+1SD TO +2SD"
        elif c > avg:
            label = "ABOVE AVG"
        elif c >= std_minus_1:
            label = "BELOW AVG"
        elif c >= std_minus_2:
            label = "-1SD TO -2SD"
        else:
            label = "< -2SD (OVERSOLD)"

        rank = sum(1 for x in series if x <= c) / n * 100.0
        upside_to_mean = ((avg / c) - 1.0) * 100.0 if c > 0 else 0.0
        upside_to_plus_1sd = ((std_plus_1 / c) - 1.0) * 100.0 if c > 0 else 0.0

        out["current"] = {
            "value": round(c, 3),
            "z_score": round(z, 2),
            "percentile_rank": round(rank, 1),
            "label": label,
            "upside_to_mean_pct": round(upside_to_mean, 2),
            "upside_to_plus_1sd_pct": round(upside_to_plus_1sd, 2),
        }

    if fundamental_base is not None:
        base = float(fundamental_base)
        out["implied_targets"] = {
            "at_plus_2sd": round(std_plus_2 * base, 2),
            "at_plus_1sd": round(std_plus_1 * base, 2),
            "at_mean": round(avg * base, 2),
            "at_minus_1sd": round(std_minus_1 * base, 2),
            "at_minus_2sd": round(std_minus_2 * base, 2),
            "fundamental_base": base,
        }

    return out


def historical_bands(prices: List[float], current: Optional[float] = None) -> Dict[str, Any]:
    """Compatibility wrapper matching server/engines/__init__.py historical_bands()."""
    if len(prices) < 2:
        return {"error": "insufficient history for bands", "n": len(prices)}
    return calc_bands(prices, current=current)


def _parse_list(s: str) -> List[float]:
    return [float(x) for x in s.replace("[", "").replace("]", "").split(",") if x.strip()]


def main() -> None:
    ap = argparse.ArgumentParser(description="Deterministic Historical Valuation Bands Engine")
    ap.add_argument("--series", type=str, required=True, help="Comma-separated historical multiples/prices")
    ap.add_argument("--current", type=float, default=None, help="Current multiple/price to evaluate position")
    ap.add_argument("--base", type=float, default=None, help="Fundamental base (BVPS/EPS/EBITDA) for price targets")
    ap.add_argument("--metric", type=str, default="Multiple", help="Metric label (e.g. PBV, EV/EBITDA, PER)")
    args = ap.parse_args()

    s = _parse_list(args.series)
    out = calc_bands(s, current=args.current, fundamental_base=args.base, metric_name=args.metric)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
