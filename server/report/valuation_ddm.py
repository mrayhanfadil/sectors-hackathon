"""Opsi B - the DDM branch of deck slide 4 (docs/ammn-slides/slide4-valuation-spec.md).

Arithmetic from the internal dividend-discount engine (server/report/engines/ddm_engine). The page
contract is deliberately identical to the DCF branch - same `blocks` / `bridge` / `sensitivity` shapes
and the same `_view()` - so the markup and the gate treat one option at a time without branching on
the markup side. In the two-column terminal block the left column is the Gordon DDM value and the
right column is the owner's alternative path (Inverse Cost of Equity: fair P/BV x BVPS).
"""

from __future__ import annotations

from types import SimpleNamespace

import pandas as pd

from server.report.engines import ddm_engine as engine
from server.report import numfmt as _nf
from server.report.house_format import ERP_SOURCE_NOTE

PERIODS = ("FY2026F", "FY2027F", "FY2028F", "FY2029F", "FY2030F")


class _Flags:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str, str]] = []

    def warn(self, where: str, message: str) -> None:
        self.messages.append(("warn", where, message))

    def missing(self, where: str, message: str) -> None:
        self.messages.append(("missing", where, message))


def build_ddm_page(payload: dict, assumptions: dict, helpers: dict) -> dict:
    """Build the dividend-discount page. `helpers` carries the cover-table readers from valuation_page
    so the two branches parse the deck's own numbers the same way."""
    _row, _num = helpers["row"], helpers["num"]
    assum = assumptions or {}
    cover = ((payload.get("cover") or {}).get("slide2") or {}).get("key_financials") or {}
    statements = payload.get("financial_statements") or {}

    payout = assum.get("payout")
    ke = assum.get("cost_of_equity") or assum.get("coe_used")
    # Terminal growth is a ticker-agnostic team constant (3.5% as of Sep 2026);
    # locked via the helper so the same value reaches valuation_page too.
    from server.report.valuation_constants import lock_g, lock_erp
    g = lock_g(assum)
    lock_erp(assum)
    shares_bn = (assum.get("shares_out") or 0) / 1e9
    price = assum.get("last_price")

    cover_years = [str(h) for h in (cover.get("headers") or [])[1:]]
    np_cells = _row(cover, "Net Profit") or []
    forecast_pairs = [(y, _num(c)) for y, c in zip(cover_years, np_cells) if _num(c) is not None and "f" in y.lower()]
    net_profit_bn: list[float] = []
    for index in range(len(PERIODS)):
        net_profit_bn.append(forecast_pairs[index][1] if index < len(forecast_pairs) else net_profit_bn[-1]) if (forecast_pairs or net_profit_bn) else None

    reasons: list[str] = []
    if not payout:
        reasons.append("payout ratio 0 / empty in assumptions: no dividend to discount")
    if not ke:
        reasons.append("cost of equity not yet in assumptions")
    if not net_profit_bn or any(v is None for v in net_profit_bn):
        reasons.append("per-year Net Profit projection not in the data")
    if reasons:
        return {
            "available": False,
            "method": "ddm",
            "title": "Intrinsic Valuation - DDM",
            "missing": reasons,
            "subtitle": "Option B selected but the data is not enough; the page is deliberately left without substitute figures.",
            "sources": ["Sectors API", f"data/assumptions/{(payload.get('meta') or {}).get('ticker') or payload.get('ticker', '?')}.json"],
        }

    scale = 1e9
    equity_bn = _num((_row(statements.get("balance") or {}, "Shareholders' Equity") or [None])[-1]) or 0.0
    bvps = (equity_bn * scale / (shares_bn * scale)) if shares_bn else None
    roe_row = (_row(statements.get("ratios") or {}, "Return on Equity") or [])
    forward_roe = _num(roe_row[-1]) if roe_row else None
    forward_roe = (forward_roe / 100) if forward_roe and forward_roe > 1 else forward_roe

    dps_bn = [np_ * payout / shares_bn for np_ in net_profit_bn]
    dps_growth = [None] + [
        (dps_bn[i] / dps_bn[i - 1] - 1) * 100 if dps_bn[i - 1] else None for i in range(1, len(PERIODS))
    ]
    discount = [1.0 / ((1 + ke) ** t) for t in range(1, len(PERIODS) + 1)]
    pv_dps = [d * df for d, df in zip(dps_bn, discount)]

    # DDM values equity directly, so the engine consumes DPS in rupiah PER SHARE (no 1e9 scaling)
    proj = pd.DataFrame({"DPS": list(dps_bn)}, index=range(1, len(PERIODS) + 1))
    flags = _Flags()
    tv = engine.terminal_value(dps_bn[-1], ke, terminal_g=g, roe_terminal=forward_roe,
                               payout_final=payout, flags=flags)
    val = engine.discount_dividends(proj, tv, ke, SimpleNamespace(price=price, shares_outstanding=shares_bn * scale),
                                    flags, mid_year=False)

    pbv_fair = None
    pbv_rows = None
    if forward_roe and bvps:
        pbv = engine.fair_pbv(forward_roe, ke, g, bvps, flags=flags)
        if isinstance(pbv, dict) and pbv.get("fair_pbv"):
            pbv_fair = pbv["fair_pbv"] * bvps
            pbv_rows = {
                "forward_roe": forward_roe, "fair_pbv": pbv["fair_pbv"], "bvps": bvps, "fair": pbv_fair,
            }

    # Exhibit 10: cost of equity against long-term growth, engine arithmetic per cell
    steps = engine.ENGINE_ASSUMPTIONS["sens_steps"]
    ke_step = engine.ENGINE_ASSUMPTIONS["sens_ke_step"]
    g_step = engine.ENGINE_ASSUMPTIONS["sens_g_step"]
    ke_axis = [ke + i * ke_step for i in range(-steps, steps + 1)]
    g_axis = [g + j * g_step for j in range(-steps, steps + 1)]
    fv_rows: list[dict] = []
    for ke_value in ke_axis:
        row = {}
        for g_value in g_axis:
            tv_cell = engine.terminal_value(dps_bn[-1], ke_value, terminal_g=g_value,
                                            roe_terminal=forward_roe, payout_final=payout, flags=None)
            cell = engine.discount_dividends(
                proj, tv_cell, ke_value,
                SimpleNamespace(price=price, shares_outstanding=shares_bn * scale), _Flags(), mid_year=False,
            ) if tv_cell.get("valid") else {"valid": False}
            row[g_value] = cell.get("fair_value_per_share") if cell.get("valid") else None
        fv_rows.append(row)
    grid = pd.DataFrame([[r[gv] for gv in g_axis] for r in fv_rows],
                        index=[f"{_nf.dec(k*100, digits=2)}%" for k in ke_axis],
                        columns=[f"{_nf.dec(gv*100, digits=2)}%" for gv in g_axis])
    flat = [v for row in grid.values.tolist() for v in row if v is not None]

    page = {
        "available": True,
        "method": "ddm",
        "title": "Intrinsic Valuation - DDM",
        "subtitle": (
            "Option B (DDM) active: the issuer pays dividends, so equity is valued directly off the dividend stream "
            "with Cost of Equity - not WACC (DDM values equity, not enterprise)."
        ),
        "periods": list(PERIODS),
        "blocks": {"build_up": {
            "Net Profit": [v for v in net_profit_bn],
            "Payout Ratio (%)": [payout * 100 for _ in PERIODS],
            "DPS": dps_bn,
            "DPS growth (%)": dps_growth,
            "Discount factor (Cost of Equity)": discount,
            "PV of DPS": pv_dps,
        }},
        "bridge": {
            "fcff": dps_bn,
            "growth": dps_growth,
            "discount": discount,
            "pv_fcff": pv_dps,
            "pv_explicit": val.get("pv_explicit"),
            "tv_gordon": tv.get("tv_nominal"),
            "tv_gordon_df": val.get("tv_discount_factor"),
            "pv_tv_gordon": val.get("pv_terminal"),
            "tv_exit": pbv_fair,
            "pv_tv_exit": None,
            "ev_gordon": val.get("fair_value_per_share"),
            "ev_exit": pbv_fair,
            "equity_gordon": val.get("fair_value_per_share"),
            "equity_exit": pbv_fair,
            "fv_gordon": val.get("fair_value_per_share"),
            "fv_exit": pbv_fair,
            "tv_share": val.get("tv_share_of_value"),
            "implied_exit_multiple": None,
            "net_debt": 0.0,
            "flags": flags.messages,
        },
        "alternatives": {},
        "wacc_rows": _coe_rows(assum, ke),
        "sensitivity": {
            "fair_value": grid, "wacc_axis": ke_axis, "g_axis": g_axis,
            "base": (len(ke_axis) // 2, len(g_axis) // 2),
            "base_fv": val.get("fair_value_per_share"),
            "swing": ({"min": min(flat), "max": max(flat), "median": sorted(flat)[len(flat) // 2]} if flat else None),
            "stats": ({"min": min(flat), "max": max(flat), "n_valid": len(flat),
                       "n_cells": len(ke_axis) * len(g_axis)} if flat else None),
        },
        "assumptions_view": {"wacc": ke, "g": g, "shares_bn": shares_bn, "rf": assum.get("rf"),
                             "beta": assum.get("beta"), "erp": assum.get("erp")},
        "legs": {"dcf": None, "ev_ebitda": None},
        "pbv": pbv_rows,
        "drivers": {
            "revenue_fy25": None, "ebit_margin_fy25": None, "effective_tax": assum.get("tax", 0) * 100,
            "da_fy25": None, "capex_sustaining": None, "multiple": None, "price": price,
            "revenue_basis": f"Net Profit projection from the {forecast_pairs[0][0]}-{forecast_pairs[-1][0]} Key Financials columns, later years held flat",
            "payout": payout, "forward_roe": forward_roe, "bvps": bvps,
        },
        "notes": _ddm_notes(val, tv, assum, pbv_rows),
        "block2_headers": None,
        "block3_headers": None,
        "sources": [
            "Sectors API: company_report, financials, ownership",
            f"data/assumptions/{(payload.get('meta') or {}).get('ticker') or payload.get('ticker', '?')}.json (payout, cost of equity, g, shares)",
            "Internal valuation engine: ddm_engine (dividend discount)",
        ],
    }
    return _view_ddm(page)


def _coe_rows(assum: dict, ke: float) -> list[tuple[str, str, str]]:
    """Exhibit 9 for the bank path: the CAPM build, or the five-year band when the assumptions carry it."""
    band = assum.get("coe_band") or {}
    if band:
        return [
            ("5-year average Cost of Equity", f"{_nf.dec(band.get('mean', 0) * 100, digits=2)}%", "band method: historic average"),
            ("5-year standard deviation", f"{_nf.dec(band.get('sd', 0) * 100, digits=2)}%", "band method: CoE volatility"),
            ("SDs used from the mean", str(band.get("sd_used", "mean")), "analyst's risk choice"),
            ("Cost of Equity used", f"{_nf.dec(ke * 100, digits=2)}%", "band method (see rows above)"),
        ]
    return [
        ("Risk-free rate (Rf)", f"{_nf.dec(assum.get('rf', 0) * 100, digits=2)}%", "INDOGB 10Y (assumptions.rf)"),
        ("Beta", f"{_nf.dec(assum.get('beta', 0), digits=4)}", "Daily regression vs JCI, sector-adjusted"),
        ("Equity Risk Premium (ERP)", f"{_nf.dec(assum.get('erp', 0) * 100, digits=2)}%", ERP_SOURCE_NOTE),
        ("Cost of Equity (CAPM) = Rf + beta x ERP", f"{_nf.dec(ke * 100, digits=2)}%", "Calc: rf + beta x erp"),
        ("Cost of Equity used", f"{_nf.dec(ke * 100, digits=2)}%", "Used to discount DPS (not WACC)"),
    ]


def _ddm_notes(val: dict, tv: dict, assum: dict, pbv_rows: dict | None) -> list[str]:
    notes = []
    gap = tv.get("payout_gap")
    if gap is not None and abs(gap) > 0.05:
        notes.append(
            f"Steady-phase payout consistency check: projected payout {_nf.dec(tv.get('payout_projected', 0)*100, digits=1)}% "
            f"vs the g/ROE-consistent payout ({_nf.dec(tv.get('payout_consistent', 0)*100, digits=1)}%), a gap of "
            f"{_nf.dec(abs(gap)*100, digits=1)}pp - if payout runs higher, value tends to read overstated."
        )
    notes.append(
        "DDM values equity directly, so the discount factor uses Cost of Equity with no net-debt "
        "bridge: dividends already belong to shareholders."
    )
    if pbv_rows:
        notes.append(
            f"The alternative Inverse Cost of Equity path is used as the second column: forward ROE "
            f"{_nf.dec(pbv_rows['forward_roe']*100, digits=1)}%, fair P/BV {_nf.dec(pbv_rows['fair_pbv'], digits=2)}×, BVPS "
            f"Rp {_nf.idn(pbv_rows['bvps'], digits=0)} -> fair value Rp {_nf.idn(pbv_rows['fair'], digits=0)}."
        )
    notes.append(
        "The payout basis comes from assumptions (announced dividend policy / historic payout), not "
        "re-assumed on this page."
    )
    return notes


def _fmt(value, digits: int = 1) -> str:
    if value is None:
        return "-"
    return f"{value:,.{digits}f}".replace(",", "\u2009").replace(".", ",").replace("\u2009", ".")


def _fmt0(value) -> str:
    return "-" if value is None else f"{_nf.idn(value, digits=0)}".replace(",", ".")


def _view_ddm(page: dict) -> dict:
    """Shape the DDM page for the template. Same keys as the DCF branch so the markup is shared."""
    b = page["bridge"]
    av = page["assumptions_view"]
    rows = page["blocks"]["build_up"]
    page["block1_rows"] = [
        (label, ["-" if v is None else _fmt(v, 3 if "Discount factor" in label else 1) for v in rows[key]])
        for label, key in (
            ("Net Profit (Rp bn)", "Net Profit"),
            ("Payout Ratio (%)", "Payout Ratio (%)"),
            ("DPS (Rp)", "DPS"),
            ("DPS growth (%)", "DPS growth (%)"),
            ("Discount factor (Cost of Equity)", "Discount factor (Cost of Equity)"),
            ("PV of DPS", "PV of DPS"),
        )
    ]
    pbv = page.get("pbv") or {}
    tv = b["tv_gordon"]
    page["block2_headers"] = ["Block 2 - Terminal value", "Gordon DDM", "Inverse CoE (fair P/BV x BVPS)"]
    page["block2_rows"] = [
        ("Terminal DPS (last DPS x (1+g))", _fmt(b["fcff"][-1] * 1.0), "-"),
        ("Terminal growth (g) - explicit assumption", _fmt(av["g"] * 100, 2) + "%", _fmt(av["g"] * 100, 2) + "%"),
        ("Terminal Value (undiscounted)",
         _fmt(tv) + " / share" if tv else "-",
         _fmt(pbv.get("fair")) + " / share" if pbv else "-"),
        ("Terminal discount factor", _fmt(b["tv_gordon_df"], 3), "-"),
        ("PV of Terminal Value", _fmt(b["pv_tv_gordon"]) if b["pv_tv_gordon"] else "-", "-"),
        ("Forward ROE (Inverse CoE basis)", _fmt(av.get("forward_roe") and av["forward_roe"] * 100, 2) + "%" if av.get("forward_roe") else "-",
         _fmt(pbv.get("forward_roe") and pbv["forward_roe"] * 100, 2) + "%" if pbv else "-"),
    ]
    page["block3_headers"] = ["Block 3 - Equity value per share", "Rp per share", "Comparison"]
    page["block3_rows"] = [
        ("Sum PV of DPS (explicit period)", _fmt0(b["pv_explicit"]), "-"),
        ("(+) PV of Terminal Value", _fmt0(b["pv_tv_gordon"]), "-"),
        ("Fair Value per Share - Gordon DDM", _fmt0(b["fv_gordon"]), "-"),
        ("Fair Value per Share - Inverse CoE (fair P/BV x BVPS)", _fmt0(b["fv_exit"]),
         (_fmt(pbv.get("fair_pbv"), 2) + "x x BVPS " + _fmt0(pbv.get("bvps"))) if pbv else "not available"),
    ]
    grid = page["sensitivity"]["fair_value"]
    base = page["sensitivity"]["base"]
    page["sensitivity"]["columns"] = [str(c) for c in grid.columns]
    page["sensitivity"]["rows"] = [
        {
            "label": str(label),
            "cells": [
                {"value": _fmt0(v), "base": bool(base and r == base[0] and c == base[1])}
                for c, v in enumerate(grid.loc[label].tolist())
            ],
        }
        for r, label in enumerate(grid.index)
    ]
    page["sensitivity"]["base_wacc"] = str(grid.index[base[0]]) if base else "-"
    page["sensitivity"]["base_g"] = str(grid.columns[base[1]]) if base else "-"
    legs = page.get("legs") or {}
    page["crosscheck_rows"] = [
        ("DDM Gordon (this page)", _fmt0(b["fv_gordon"]), "Intrinsic equity value"),
        ("Inverse CoE (fair P/BV x BVPS)", _fmt0(b["fv_exit"]), "Second-method cross-check"),
        ("EV/EBITDA mid-cycle", _fmt0(legs.get("ev_ebitda")), "Target-price ANCHOR if the relative leg is used"),
        ("Market price", _fmt0(page["drivers"]["price"]), "Sectors, latest close"),
    ]
    page["narrative"] = _narrative_ddm(page)
    return page


def _narrative_ddm(page: dict) -> list[str]:
    """The DDM narrative the rules ask for: ROE trajectory as the driver, payout sustainability, and the
    gap between the two methods rather than a quiet average."""
    b = page["bridge"]
    grid = page["sensitivity"]["fair_value"]
    rows = [grid.loc[i].tolist() for i in grid.index]
    cols = [str(c) for c in grid.columns]
    ke_span = (max(r[0] for r in rows) - min(r[0] for r in rows)) if rows else 0
    g_span = (max(r[-1] for r in rows) - min(r[-1] for r in rows)) if rows else 0
    dominant = "Cost of Equity" if ke_span >= g_span else "long-term growth"
    d = page["drivers"]
    pbv = page.get("pbv") or {}
    out = [
        (
            f"Most sensitive parameter: {dominant}. Moving Cost of Equity from {str(grid.index[0])} to "
            f"{str(grid.index[-1])} changes fair value by {_fmt0(ke_span)} per share; moving long-term growth "
            f"from {cols[0]} to {cols[-1]} changes {_fmt0(g_span)}."
        ),
        (
            f"This page's main driver is the ROE trajectory and the ability to pay dividends, not free cash "
            f"flow as in DCF. The payout used, {_fmt((d.get('payout') or 0) * 100, 1)}%, comes from "
            f"assumptions (dividend policy/historic payout), and the earnings projection follows "
            f"{d['revenue_basis']}. Forward ROE "
            + (f"{_fmt(pbv.get('forward_roe') * 100, 2)}% is used to test whether that payout is consistent "
               "with the assumed growth (payout* = 1 - g/ROE)."
               if pbv.get("forward_roe") else
               "is not yet in the data, so the Inverse CoE path cannot be computed and that is stated.")
        ),
        (
            "The two methods on this page "
            + (f"differ {_nf.dec(max(b['fv_gordon'], b['fv_exit']) / min(b['fv_gordon'], b['fv_exit']), digits=2)}× "
               f"(Rp {_fmt0(b['fv_gordon'])} vs Rp {_fmt0(b['fv_exit'])}) and that gap is left open "
               "as an unresolved assumption, not averaged."
               if b.get("fv_exit") else
               "have only one computable leg; the second leg's absence is stated in the notes, not filled with a figure.")
        ),
    ]
    return out
