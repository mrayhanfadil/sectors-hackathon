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
    np_cells = (_row(cover, "Net Profit") or [])[1:]
    forecast_pairs = [(y, _num(c)) for y, c in zip(cover_years, np_cells) if _num(c) is not None and "f" in y.lower()]
    net_profit_bn: list[float] = []
    for index in range(len(PERIODS)):
        net_profit_bn.append(forecast_pairs[index][1] if index < len(forecast_pairs) else net_profit_bn[-1]) if (forecast_pairs or net_profit_bn) else None

    reasons: list[str] = []
    if not payout:
        reasons.append("payout ratio 0 / kosong di assumptions: tidak ada dividen untuk didiskon")
    if not ke:
        reasons.append("cost of equity belum ada di assumptions")
    if not net_profit_bn or any(v is None for v in net_profit_bn):
        reasons.append("proyeksi Net Profit per tahun tidak tersedia di payload")
    if reasons:
        return {
            "available": False,
            "method": "ddm",
            "title": "Valuasi Intrinsik - DDM",
            "missing": reasons,
            "subtitle": "Opsi B dipilih tetapi datanya tidak cukup; halaman sengaja tidak diisi angka pengganti.",
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
        "title": "Valuasi Intrinsik - DDM",
        "subtitle": (
            "Opsi B (DDM) aktif: emiten membagi dividen, jadi ekuitas dinilai langsung dari arus dividen "
            "dengan Cost of Equity - bukan WACC (DDM menilai ekuitas, bukan enterprise)."
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
            "revenue_basis": f"proyeksi Net Profit dari kolom {forecast_pairs[0][0]}-{forecast_pairs[-1][0]} tabel Key Financials, tahun setelahnya di-hold flat",
            "payout": payout, "forward_roe": forward_roe, "bvps": bvps,
        },
        "notes": _ddm_notes(val, tv, assum, pbv_rows),
        "block2_headers": None,
        "block3_headers": None,
        "sources": [
            "Sectors API: company_report, financials, ownership",
            f"data/assumptions/{(payload.get('meta') or {}).get('ticker') or payload.get('ticker', '?')}.json (payout, cost of equity, g, shares)",
            "Engine valuasi internal: server/report/engines/ddm_engine",
        ],
    }
    return _view_ddm(page)


def _coe_rows(assum: dict, ke: float) -> list[tuple[str, str, str]]:
    """Exhibit 9 for the bank path: the CAPM build, or the five-year band when the assumptions carry it."""
    band = assum.get("coe_band") or {}
    if band:
        return [
            ("Cost of Equity rata-rata 5 tahun", f"{_nf.dec(band.get('mean', 0) * 100, digits=2)}%", "band method: rata-rata historis"),
            ("Standar deviasi 5 tahun", f"{_nf.dec(band.get('sd', 0) * 100, digits=2)}%", "band method: volatilitas CoE"),
            ("Jumlah SD yang dipakai dari mean", str(band.get("sd_used", "mean")), "pilihan analis atas risiko"),
            ("Cost of Equity yang dipakai", f"{_nf.dec(ke * 100, digits=2)}%", "band method (lihat baris di atas)"),
        ]
    return [
        ("Risk-free rate (Rf)", f"{_nf.dec(assum.get('rf', 0) * 100, digits=2)}%", "INDOGB 10Y (assumptions.rf)"),
        ("Beta", f"{_nf.dec(assum.get('beta', 0), digits=4)}", "Regresi harian vs IHSG, disesuaikan sektor"),
        ("Equity Risk Premium (ERP)", f"{_nf.dec(assum.get('erp', 0) * 100, digits=2)}%", "Damodaran (country risk adj.)"),
        ("Cost of Equity (CAPM) = Rf + beta x ERP", f"{_nf.dec(ke * 100, digits=2)}%", "Hitung: rf + beta x erp"),
        ("Cost of Equity yang dipakai", f"{_nf.dec(ke * 100, digits=2)}%", "Dipakai untuk mendiskon DPS (bukan WACC)"),
    ]


def _ddm_notes(val: dict, tv: dict, assum: dict, pbv_rows: dict | None) -> list[str]:
    notes = []
    gap = tv.get("payout_gap")
    if gap is not None and abs(gap) > 0.05:
        notes.append(
            f"Uji konsistensi payout fase stabil: payout proyeksi {_nf.dec(tv.get('payout_projected', 0)*100, digits=1)}% "
            f"vs payout yang konsisten dengan g/ROE ({_nf.dec(tv.get('payout_consistent', 0)*100, digits=1)}%), selisih "
            f"{_nf.dec(abs(gap)*100, digits=1)}pp - kalau payout lebih tinggi, nilai cenderung overstated."
        )
    notes.append(
        "DDM menilai ekuitas langsung, jadi discount factor memakai Cost of Equity dan tidak ada bridge "
        "net debt: dividen sudah milik pemegang saham."
    )
    if pbv_rows:
        notes.append(
            f"Jalur alternatif Inverse Cost of Equity dipakai sebagai kolom kedua: forward ROE "
            f"{_nf.dec(pbv_rows['forward_roe']*100, digits=1)}%, fair P/BV {_nf.dec(pbv_rows['fair_pbv'], digits=2)}×, BVPS "
            f"Rp {_nf.idn(pbv_rows['bvps'], digits=0)} -> nilai wajar Rp {_nf.idn(pbv_rows['fair'], digits=0)}."
        )
    notes.append(
        "Basis payout diambil dari assumptions (kebijakan dividen yang diumumkan / payout historis), bukan "
        "diasumsikan ulang di halaman ini."
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
    page["block2_headers"] = ["Blok 2 - Terminal value", "Gordon DDM", "Inverse CoE (fair P/BV x BVPS)"]
    page["block2_rows"] = [
        ("Terminal DPS (DPS terakhir x (1+g))", _fmt(b["fcff"][-1] * 1.0), "-"),
        ("Terminal growth (g) - asumsi eksplisit", _fmt(av["g"] * 100, 2) + "%", _fmt(av["g"] * 100, 2) + "%"),
        ("Terminal Value (undiscounted)",
         _fmt(tv) + " / saham" if tv else "-",
         _fmt(pbv.get("fair")) + " / saham" if pbv else "-"),
        ("Discount factor terminal", _fmt(b["tv_gordon_df"], 3), "-"),
        ("PV of Terminal Value", _fmt(b["pv_tv_gordon"]) if b["pv_tv_gordon"] else "-", "-"),
        ("Forward ROE (basis Inverse CoE)", _fmt(av.get("forward_roe") and av["forward_roe"] * 100, 2) + "%" if av.get("forward_roe") else "-",
         _fmt(pbv.get("forward_roe") and pbv["forward_roe"] * 100, 2) + "%" if pbv else "-"),
    ]
    page["block3_headers"] = ["Blok 3 - Nilai ekuitas per saham", "Rp per saham", "Pembanding"]
    page["block3_rows"] = [
        ("Sum PV of DPS (periode eksplisit)", _fmt0(b["pv_explicit"]), "-"),
        ("(+) PV of Terminal Value", _fmt0(b["pv_tv_gordon"]), "-"),
        ("Fair Value per Share - Gordon DDM", _fmt0(b["fv_gordon"]), "-"),
        ("Fair Value per Share - Inverse CoE (fair P/BV x BVPS)", _fmt0(b["fv_exit"]),
         (_fmt(pbv.get("fair_pbv"), 2) + "x x BVPS " + _fmt0(pbv.get("bvps"))) if pbv else "tidak tersedia"),
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
        ("DDM Gordon (halaman ini)", _fmt0(b["fv_gordon"]), "Nilai intrinsik ekuitas"),
        ("Inverse CoE (fair P/BV x BVPS)", _fmt0(b["fv_exit"]), "Cross-check metode kedua"),
        ("EV/EBITDA mid-cycle", _fmt0(legs.get("ev_ebitda")), "ANCHOR target price bila leg relative dipakai"),
        ("Harga pasar", _fmt0(page["drivers"]["price"]), "Sectors, penutupan terakhir"),
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
            f"Parameter paling sensitif: {dominant}. Menggeser Cost of Equity dari {str(grid.index[0])} ke "
            f"{str(grid.index[-1])} mengubah nilai wajar {_fmt0(ke_span)} per saham; menggeser long-term growth "
            f"dari {cols[0]} ke {cols[-1]} mengubah {_fmt0(g_span)}."
        ),
        (
            f"Driver utama halaman ini adalah trajektori ROE dan kemampuan membayar dividen, bukan arus kas "
            f"bebas seperti DCF. Payout yang dipakai {_fmt((d.get('payout') or 0) * 100, 1)}% diambil dari "
            f"assumptions (kebijakan dividen/payout historis), dan proyeksi laba mengikuti "
            f"{d['revenue_basis']}. Forward ROE "
            + (f"{_fmt(pbv.get('forward_roe') * 100, 2)}% dipakai untuk menguji apakah payout itu konsisten "
               "dengan pertumbuhan yang diasumsikan (payout* = 1 - g/ROE)."
               if pbv.get("forward_roe") else
               "belum tersedia di payload, jadi jalur Inverse CoE tidak dapat dihitung dan itu dinyatakan.")
        ),
        (
            "Dua metode di halaman ini "
            + (f"berbeda {_nf.dec(max(b['fv_gordon'], b['fv_exit']) / min(b['fv_gordon'], b['fv_exit']), digits=2)}× "
               f"(Rp {_fmt0(b['fv_gordon'])} vs Rp {_fmt0(b['fv_exit'])}) dan selisih itu dibiarkan terbuka "
               "sebagai unresolved assumption, bukan dirata-rata."
               if b.get("fv_exit") else
               "hanya satu yang dapat dihitung; kekosongan jalur kedua dinyatakan di catatan, bukan diisi angka.")
        ),
    ]
    return out
