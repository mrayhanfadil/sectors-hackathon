"""Deterministic DDM (Dividend Discount Model) engine - CDIA DDM 810.

Part of T02 - Deterministic Engines. Formulas explicit, no LLM math.
Mirrors server/engines/__init__.py ddm() and finance_tools.calc_ddm().

CDIA benchmark (BCA Sekuritas 23 Jun 2026, plan §2.2):
  DDM 810 with payout 40% (FY27-28F) -> 104% (FY28F). DPS = EPS * payout.
  Dividends discounted at CoE; terminal via Gordon growth.

This engine supports both per-share DPS input and total-dividend input.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List


def ddm(
    dividends: List[float],
    coe: float,
    g_terminal: float,
    shares_out: float = 1.0,
    per_share: bool = True,
) -> Dict[str, Any]:
    """Dividend Discount Model.

    Args:
        dividends: DPS per period (per_share=True) or total dividends (per_share=False).
        coe: cost of equity (decimal).
        g_terminal: perpetual dividend growth (decimal). Must be < coe.
        shares_out: share count (only used when per_share=False).
    """
    if not dividends:
        raise ValueError("dividends must be non-empty")
    if coe <= g_terminal:
        raise ValueError(f"coe ({coe}) must exceed g_terminal ({g_terminal})")

    dps = [float(d) for d in dividends]
    if not per_share:
        if not shares_out:
            raise ValueError("shares_out required when dividends are totals")
        dps = [d / shares_out for d in dps]

    pvs = [d / ((1 + coe) ** (i + 1)) for i, d in enumerate(dps)]
    n = len(dps)
    last = dps[-1]
    tv = last * (1 + g_terminal) / (coe - g_terminal)
    pv_tv = tv / ((1 + coe) ** n)
    equity = sum(pvs) + pv_tv
    fv_per_share = equity if per_share else equity / shares_out

    return {
        "pv_dividends": [round(x, 4) for x in pvs],
        "pv_terminal": round(pv_tv, 4),
        "terminal_value": round(tv, 4),
        "equity_value": round(equity, 4),
        "fv_per_share": round(fv_per_share, 4),
        "inputs": {
            "dividends": dividends,
            "coe": coe,
            "g_terminal": g_terminal,
            "shares_out": shares_out,
            "per_share": per_share,
        },
        "provenance": "DDM: PV(dividends) + Gordon terminal PV",
    }


def dps_from_payout(eps: List[float], payout: List[float]) -> List[float]:
    """DPS = EPS * payout for each year (payout as decimals)."""
    if len(eps) != len(payout):
        raise ValueError("eps and payout must be same length")
    return [e * p for e, p in zip(eps, payout)]


def _parse_list(s: str) -> List[float]:
    return [float(x) for x in s.replace("[", "").replace("]", "").split(",") if x.strip()]


def main() -> None:
    ap = argparse.ArgumentParser(description="DDM engine")
    ap.add_argument("--dividends", type=str, required=True, help="DPS or total divs, comma list")
    ap.add_argument("--coe", type=float, required=True)
    ap.add_argument("--g", type=float, required=True)
    ap.add_argument("--shares", type=float, default=1.0)
    ap.add_argument("--totals", action="store_true", help="dividends are totals (not per-share)")
    args = ap.parse_args()
    out = ddm(_parse_list(args.dividends), args.coe, args.g, args.shares, per_share=not args.totals)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
