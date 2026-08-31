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
from typing import Any, Dict, List, Optional


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


def _parse_list(s: str) -> List[float]:
    return [float(x) for x in s.replace("[", "").replace("]", "").split(",") if x.strip()]


def main() -> None:
    ap = argparse.ArgumentParser(description="DCF / WACC / EV/EBITDA / Index Target engine")
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
    p.add_argument("--ebitda", type=float, required=True, help="EBITDA value")
    p.add_argument("--multiple", type=float, required=True, help="EV/EBITDA multiple (e.g. 22.6)")
    p.add_argument("--shares", type=float, default=1.0, help="Shares outstanding")
    p.add_argument("--net-debt", "--net_debt", dest="net_debt", type=float, default=0.0, help="Net debt (or negative for net cash)")
    p.add_argument("--cash", type=float, default=0.0, help="Cash (if gross debt passed as net_debt)")

    p = sub.add_parser("index_target")
    p.add_argument("--current", type=float, required=True, help="Current index level (e.g. 8425.93)")
    p.add_argument("--eps-growth", type=float, required=True, help="Forward EPS growth decimal (e.g. 0.08)")
    p.add_argument("--multiple", type=float, default=1.0, help="Multiple re-rating factor (default 1.0 for flat multiple)")

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

    elif args.cmd == "index_target":
        out = index_target(args.current, args.eps_growth, args.multiple)
    else:
        ap.print_help()
        return
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

