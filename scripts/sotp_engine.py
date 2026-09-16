"""Deterministic SOTP (Sum-Of-The-Parts) engine - CDIA 4-pillar + ADRO holdco discount.

Part of T02 - Deterministic Engines. Formulas explicit, no LLM math.
Mirrors server/engines/__init__.py sotp() + finance_tools.calc_sotp().

Benchmarks:
  * CDIA (BCA Sekuritas 23 Jun 2026, plan §2.2): 4 pillars
    Energy / Water / Port / Logistics with peer-avg EV/EBITDA & P/E multiples.
  * ADRO (holdco-discount benchmark, see references/local-global-like/):
    AADI equity US$6.1bn + ADRO post-spin US$5.3-7.0bn (holdco discount range).

Per-pillar value methods supported:
  - "ev_ebitda": value = ebitda * multiple - net_debt_alloc + cash_alloc
  - "pe":        value = net_income * multiple
  - "equity":    direct equity value (e.g. ADRO AADI US$6.1bn)
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List


def _pillar_value(p: Dict[str, Any]) -> float:
    method = p.get("method", "equity")
    if method == "ev_ebitda":
        return (
            float(p["ebitda"]) * float(p["multiple"])
            - float(p.get("net_debt", 0.0))
            + float(p.get("cash", 0.0))
        )
    if method == "pe":
        return float(p["net_income"]) * float(p["multiple"])
    return float(p.get("value", 0.0))


def sotp(
    segments: List[Dict[str, Any]],
    holdco_discount: float = 0.0,
    currency: str = "IDR",
    shares_out: float | None = None,
    fx_to_idr: float | None = None,
) -> Dict[str, Any]:
    """SOTP: sum of parts, optional holdco discount, optional per-share bridge.

    Args:
        segments: [{name, value?, ebitda?, multiple?, net_debt?, cash?, method?}].
        holdco_discount: discount on the TOTAL (decimal, e.g. 0.15).
        currency: reporting currency label (IDR/USD/IDR-equivalent).
        shares_out: when given, compute FV per share (equity_after_discount / shares).
        fx_to_idr: when currency is USD and shares_out given, convert to IDR first.
    """
    if not segments:
        raise ValueError("segments must be non-empty")

    breakdown = []
    subtotal = 0.0
    for s in segments:
        v = _pillar_value(s)
        subtotal += v
        breakdown.append(
            {
                "name": s.get("name", "?"),
                "method": s.get("method", "equity"),
                "value": round(v, 2),
                "multiple": s.get("multiple"),
                "ebitda": s.get("ebitda"),
                "net_debt": s.get("net_debt"),
                "cash": s.get("cash"),
                "pct": 0.0,  # filled after total known
            }
        )
    for b in breakdown:
        b["pct"] = round((b["value"] / subtotal * 100) if subtotal else 0.0, 1)

    discount_abs = subtotal * holdco_discount
    after_discount = subtotal - discount_abs

    out: Dict[str, Any] = {
        "segments": breakdown,
        "subtotal": round(subtotal, 2),
        "holdco_discount_pct": round(holdco_discount * 100, 2),
        "holdco_discount_abs": round(discount_abs, 2),
        "total_after_discount": round(after_discount, 2),
        "currency": currency,
    }

    if shares_out is not None:
        equity_for_fv = after_discount
        if fx_to_idr and currency.upper() == "USD":
            equity_for_fv = after_discount * fx_to_idr
        out["equity_value"] = round(equity_for_fv, 2)
        out["fv_per_share"] = round(equity_for_fv / shares_out, 2) if shares_out else 0.0
        out["shares_out"] = shares_out
        out["fx_to_idr"] = fx_to_idr
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="SOTP engine")
    ap.add_argument("--segments", type=str, required=True,
                    help="JSON list: [{\"name\":..., \"value\":...}, ...]")
    ap.add_argument("--holdco-discount", type=float, default=0.0)
    ap.add_argument("--currency", default="IDR")
    ap.add_argument("--shares", type=float, default=None)
    ap.add_argument("--fx", type=float, default=None)
    args = ap.parse_args()
    segs = json.loads(args.segments)
    out = sotp(segs, args.holdco_discount, args.currency, args.shares, args.fx)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
