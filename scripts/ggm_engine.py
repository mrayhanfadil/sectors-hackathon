"""Deterministic Gordon Growth Model (GGM) Engine — Bank / Financial P/BV & Fair Value.

Part of T02 — Deterministic Engines (Python, NOT LLM math).
Mirrors server/engines/__init__.py ggm() and finance_tools.calc_ggm().

Formulas (all explicit, auditable):
  1. Implied Price-to-Book Ratio:
       P/BV = (ROE - g) / (CoE - g)
     Where:
       ROE = Return on Equity (decimal, e.g. 0.197 for 19.7%)
       CoE = Cost of Equity from CAPM (decimal, e.g. 0.1085 for 10.85%)
       g   = Perpetual sustainable growth rate (decimal, e.g. 0.07 for 7.0%)
     Requirement: CoE > g.

  2. Fair Value Per Share:
       FV_per_share = P/BV * BVPS
     Or:
       FV_per_share = ((ROE - g) / (CoE - g)) * (Total_Equity / Shares_Outstanding)

  3. Gordon Dividend Form (Equivalence):
       P_0 = DPS_1 / (CoE - g) = (EPS * payout * (1 + g)) / (CoE - g)
     When retention rate b = (1 - payout) = g / ROE:
       P_0 / BVPS = (ROE * payout) / (CoE - g) = (ROE - g) / (CoE - g)

  4. Analytical Solvers:
       Implied ROE  = P/BV * (CoE - g) + g
       Implied CoE  = (ROE - g) / (P/BV) + g
       Implied g    = (P/BV * CoE - ROE) / (P/BV - 1)

Benchmark Reproduction:
  * BBCA (Samuel Sekuritas 21 Oct 2025, references/local-global-like/samuel-BBCA.md):
    ROE = 19.7%, CoE = 10.848% (Rf 6.9%, beta 0.8, ERP 5.0%), g = 7.0%
    -> Implied P/BV = (0.197 - 0.07) / (0.10848 - 0.07) = 0.127 / 0.03848 = 3.30x
    -> At BVPS = 2,909.09 Rp -> Target Price = 3.30 * 2,909.09 = 9,600 Rp (+21.9% upside).
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, Optional


def ggm(
    roe: float,
    coe: float,
    g: float,
    bvps: Optional[float] = None,
    shares_out: Optional[float] = None,
    total_equity: Optional[float] = None,
) -> Dict[str, Any]:
    """Gordon Growth Model (GGM) for P/BV and Fair Value.

    Args:
        roe: Return on Equity (decimal, e.g. 0.197 for 19.7%).
        coe: Cost of Equity (decimal, e.g. 0.1085 for 10.85%).
        g: Perpetual growth rate (decimal, e.g. 0.07 for 7.0%). Must be < coe.
        bvps: Book Value Per Share. If None and total_equity/shares_out provided, computed.
        shares_out: Total shares outstanding (e.g. in billions or full count).
        total_equity: Total shareholders' equity (same unit as shares_out).

    Returns:
        Dict with pbv_implied, fv_per_share, inputs, and provenance.
    """
    if coe <= g:
        raise ValueError(f"coe ({coe}) must exceed perpetual growth g ({g})")

    pbv = (roe - g) / (coe - g)

    if bvps is None and total_equity is not None and shares_out is not None and shares_out > 0:
        bvps = total_equity / shares_out

    fv = pbv * bvps if bvps is not None else None
    total_market_eq = fv * shares_out if (fv is not None and shares_out is not None) else None

    out: Dict[str, Any] = {
        "pbv_implied": round(pbv, 4),
        "formula": "P/BV = (ROE - g) / (CoE - g)",
        "inputs": {
            "roe": roe,
            "coe": coe,
            "g": g,
            "bvps": bvps,
            "shares_out": shares_out,
            "total_equity": total_equity,
        },
        "provenance": "GGM: P/BV=(ROE-g)/(CoE-g); Target Price = P/BV * BVPS",
    }

    if fv is not None:
        out["fv_per_share"] = round(fv, 2)
        out["bvps"] = round(bvps, 2)
    if total_market_eq is not None:
        out["implied_equity_value"] = round(total_market_eq, 2)

    return out


def implied_coe(pbv: float, roe: float, g: float) -> Dict[str, Any]:
    """Solve for implied Cost of Equity given market P/BV, ROE, and g."""
    if pbv <= 0:
        raise ValueError("pbv must be positive")
    coe = (roe - g) / pbv + g
    return {
        "implied_coe": round(coe, 6),
        "implied_coe_pct": round(coe * 100, 3),
        "formula": "CoE = (ROE - g) / (P/BV) + g",
        "inputs": {"pbv": pbv, "roe": roe, "g": g},
    }


def implied_roe(pbv: float, coe: float, g: float) -> Dict[str, Any]:
    """Solve for implied ROE given target P/BV, CoE, and g."""
    roe = pbv * (coe - g) + g
    return {
        "implied_roe": round(roe, 6),
        "implied_roe_pct": round(roe * 100, 3),
        "formula": "ROE = P/BV * (CoE - g) + g",
        "inputs": {"pbv": pbv, "coe": coe, "g": g},
    }


def implied_g(pbv: float, roe: float, coe: float) -> Dict[str, Any]:
    """Solve for implied perpetual growth g given P/BV, ROE, and CoE."""
    if abs(pbv - 1.0) < 1e-6:
        raise ValueError("Cannot solve for g when P/BV = 1.0 (ROE must equal CoE)")
    g = (pbv * coe - roe) / (pbv - 1.0)
    return {
        "implied_g": round(g, 6),
        "implied_g_pct": round(g * 100, 3),
        "formula": "g = (P/BV * CoE - ROE) / (P/BV - 1)",
        "inputs": {"pbv": pbv, "roe": roe, "coe": coe},
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Deterministic Gordon Growth Model (GGM) Engine")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_ggm = sub.add_parser("calc", help="Calculate implied P/BV and target price")
    p_ggm.add_argument("--roe", type=float, required=True, help="ROE decimal (e.g. 0.197 for 19.7%)")
    p_ggm.add_argument("--coe", type=float, required=True, help="Cost of Equity decimal (e.g. 0.1085 for 10.85%)")
    p_ggm.add_argument("--g", type=float, required=True, help="Perpetual growth g decimal (e.g. 0.07 for 7%)")
    p_ggm.add_argument("--bvps", type=float, default=None, help="Book Value Per Share (Rp)")
    p_ggm.add_argument("--shares", type=float, default=None, help="Shares outstanding count")
    p_ggm.add_argument("--equity", type=float, default=None, help="Total equity value")

    p_coe = sub.add_parser("implied_coe", help="Solve for implied CoE")
    p_coe.add_argument("--pbv", type=float, required=True, help="Target or market P/BV multiple")
    p_coe.add_argument("--roe", type=float, required=True, help="ROE decimal")
    p_coe.add_argument("--g", type=float, required=True, help="Perpetual growth g decimal")

    p_roe = sub.add_parser("implied_roe", help="Solve for implied ROE")
    p_roe.add_argument("--pbv", type=float, required=True, help="Target or market P/BV multiple")
    p_roe.add_argument("--coe", type=float, required=True, help="Cost of Equity decimal")
    p_roe.add_argument("--g", type=float, required=True, help="Perpetual growth g decimal")

    args = ap.parse_args()
    if args.cmd == "calc":
        out = ggm(args.roe, args.coe, args.g, args.bvps, args.shares, args.equity)
    elif args.cmd == "implied_coe":
        out = implied_coe(args.pbv, args.roe, args.g)
    elif args.cmd == "implied_roe":
        out = implied_roe(args.pbv, args.coe, args.g)
    else:
        ap.print_help()
        return

    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
