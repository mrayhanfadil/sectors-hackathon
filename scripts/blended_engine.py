"""Deterministic Blended Valuation engine — MTEL 60/40 DCF + EV/EBITDA.

Part of T02 — Deterministic Engines. Formulas explicit, no LLM math.
Mirrors server/engines/__init__.py blended() + finance_tools.calc_blended().

MTEL benchmark (KSI 27 Aug 2026, plan §2.3 / §58):
  DCF 60% (51,556 bn equity -> 630/sh) + EV/EBITDA 40% (7,451 x 10x = 74,513 bn -> 745/sh)
  Blended Equity = 0.60 * 51,556 + 0.40 * 74,513 = 60,739 bn
  Per share at 81.5 bn shares = 745.26 Rp/sh
  Target Price with 15% Margin of Safety:
    TP = 745.26 * (1 - 0.15) = 633.47 ≈ 635 Rp/sh.

Formulas:
  1. Per-Share Blending:
       Blended_FV = sum(FV_i * Weight_i)
       Target_Price = Blended_FV * (1 - MoS)

  2. Aggregate Equity Blending (when valuations are total equity):
       Blended_Equity = sum(Equity_i * Weight_i)
       Raw_FV_per_share = Blended_Equity / Shares_Outstanding
       Target_Price = Raw_FV_per_share * (1 - MoS)
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, Optional


def blended(
    valuations: Dict[str, float],
    weights: Dict[str, float],
    margin_of_safety: float = 0.0,
    shares_out: Optional[float] = None,
) -> Dict[str, Any]:
    """Blended weighted fair value with optional margin of safety.

    Args:
        valuations: {component_name: fair value per share OR total equity}
                    e.g. {"DCF": 630, "EV/EBITDA": 745} or {"DCF": 51556, "EV/EBITDA": 74513}.
        weights: {component_name: weight} e.g. {"DCF": 0.6, "EV/EBITDA": 0.4}. Must sum to 1.0.
        margin_of_safety: decimal MoS to subtract (target = blended * (1 - mos)).
        shares_out: optional share count if valuations are total equity values.
    """
    s = sum(weights.values())
    if abs(s - 1.0) > 1e-6:
        raise ValueError(f"weights must sum to 1.0, got {s:.6f}")
    missing = set(valuations) - set(weights)
    if missing:
        raise ValueError(f"weights missing for components: {sorted(missing)}")

    raw = sum(float(valuations[k]) * float(weights[k]) for k in weights)

    if shares_out is not None and shares_out > 0:
        equity_total = raw
        fv_per_share = equity_total / shares_out
        target = fv_per_share * (1.0 - margin_of_safety)
        out: Dict[str, Any] = {
            "blended_equity": round(equity_total, 2),
            "raw_fv_per_share": round(fv_per_share, 2),
            "target_price": round(target, 2),
            "margin_of_safety_pct": round(margin_of_safety * 100, 2),
            "shares_out": shares_out,
            "components": valuations,
            "weights": weights,
            "weights_sum": round(s, 6),
            "provenance": "TP = (sum(Equity_i * W_i) / Shares) x (1 - MoS)",
        }
    else:
        target = raw * (1.0 - margin_of_safety)
        out = {
            "blended_value": round(raw, 2),
            "target_price": round(target, 2),
            "margin_of_safety_pct": round(margin_of_safety * 100, 2),
            "components": valuations,
            "weights": weights,
            "weights_sum": round(s, 6),
            "provenance": "TP = sum(fv_i * w_i) x (1 - MoS)",
        }

    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Deterministic Blended Valuation Engine")
    ap.add_argument(
        "--components",
        type=str,
        required=True,
        help='JSON dict of component FV/Equity, e.g. \'{"DCF": 630, "EV/EBITDA": 745}\'',
    )
    ap.add_argument(
        "--weights",
        type=str,
        required=True,
        help='JSON dict of weights summing to 1.0, e.g. \'{"DCF": 0.6, "EV/EBITDA": 0.4}\'',
    )
    ap.add_argument("--mos", type=float, default=0.0, help="Margin of safety decimal (e.g. 0.15 for 15%)")
    ap.add_argument("--shares", type=float, default=None, help="Optional shares count if components are equity totals")
    args = ap.parse_args()

    out = blended(json.loads(args.components), json.loads(args.weights), args.mos, args.shares)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
