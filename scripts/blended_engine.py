"""Deterministic Blended Valuation engine - MTEL 60/40 DCF + EV/EBITDA.

Part of T02 - Deterministic Engines. Formulas explicit, no LLM math.
Mirrors server/engines/__init__.py blended() + finance_tools.calc_blended().

MTEL benchmark (KSI 27 Aug 2026, plan §2.3):
  DCF 60% (51,556 equity -> 630/sh) + EV/EBITDA 40% (7,451 x 10x = 74,513 -> 745/sh)
  = 60,739 -> TP 635. Margin of safety 15%.

TP = sum(component_fv * weight). Optionally apply margin of safety:
  target = blended * (1 - mos). (Report labels TP 635 WITH the 15% MoS already
  reflected in the DCF leg; engine exposes both raw blended and MoS-adjusted.)
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict


def blended(
    valuations: Dict[str, float],
    weights: Dict[str, float],
    margin_of_safety: float = 0.0,
) -> Dict[str, Any]:
    """Blended weighted fair value.

    Args:
        valuations: {component_name: fair value per share} e.g. {"DCF": 630, "EV/EBITDA": 745}.
        weights: {component_name: weight} e.g. {"DCF": 0.6, "EV/EBITDA": 0.4}. Must sum to 1.
        margin_of_safety: decimal MoS to subtract (target = blended * (1 - mos)).
    """
    s = sum(weights.values())
    if abs(s - 1.0) > 1e-6:
        raise ValueError(f"weights must sum to 1.0, got {s:.6f}")
    missing = set(valuations) - set(weights)
    if missing:
        raise ValueError(f"weights missing for components: {sorted(missing)}")

    raw = sum(valuations[k] * weights[k] for k in weights)
    target = raw * (1 - margin_of_safety)

    return {
        "blended_value": round(raw, 2),
        "target_price": round(target, 2),
        "margin_of_safety_pct": round(margin_of_safety * 100, 2),
        "components": valuations,
        "weights": weights,
        "weights_sum": round(s, 6),
        "provenance": "TP = sum(fv_i * w_i) x (1 - MoS)",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Blended valuation engine")
    ap.add_argument("--components", type=str, required=True,
                    help='JSON dict of component FV per share, e.g. {"DCF": 630, "EV/EBITDA": 745}')
    ap.add_argument("--weights", type=str, required=True,
                    help='JSON dict of weights summing to 1.0, e.g. {"DCF": 0.6, "EV/EBITDA": 0.4}')
    ap.add_argument("--mos", type=float, default=0.0, help="margin of safety (decimal)")
    args = ap.parse_args()
    out = blended(json.loads(args.components), json.loads(args.weights), args.mos)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
