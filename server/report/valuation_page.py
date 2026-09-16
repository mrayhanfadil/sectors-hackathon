"""Deck slide 4 - intrinsic valuation (docs/ammn-slides/slide4-valuation-spec.md).

The arithmetic is the internal FCFF engine (server/report/engines/dcf_engine). This module
only decides WHICH numbers go in, reads them from the Sectors payload + data/assumptions/<ticker>.json,
and assembles the three exhibits the owner's rules define:

    Exhibit 8  FCFF forecast and terminal value - one table, three blocks
    Exhibit 9  WACC components, two columns plus the source of every parameter
    Exhibit 10 Sensitivity grid, base case highlighted

Method selection is manual by rule, so this page prints what was chosen and what was excluded: for
AMMN the dividend model has nothing to discount (the issuer pays none) and the RNAV model has no
asset-level reserve or NAV data anywhere in Sectors. Both are stated on the page rather than being
silently skipped.
"""

from __future__ import annotations

import json
import math
import pathlib
from types import SimpleNamespace

import pandas as pd

from server.report.engines import dcf_engine as engine
from server.report import numfmt as _nf

REPO = pathlib.Path(__file__).resolve().parents[2]
PERIODS = ("FY2026F", "FY2027F", "FY2028F", "FY2029F", "FY2030F")


class _Flags:
    """The engine's flag sink, collected so the page can disclose what the engine complained about."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, str, str]] = []

    def warn(self, where: str, message: str) -> None:
        self.messages.append(("warn", where, message))

    def missing(self, where: str, message: str) -> None:
        self.messages.append(("missing", where, message))


def _row(block: dict, label: str) -> list:
    """Exact match first, then a contains match: the cover's rows carry units in the label
    ("Revenue (Rpbn)") while the statement rows do not ("Revenue")."""
    rows = block.get("rows") or []
    needle = label.lower()
    for row in rows:
        if str(row[0]).strip().lower() == needle:
            return row[1:]
    for row in rows:
        if needle in str(row[0]).strip().lower():
            return row[1:]
    return []


def _num(value) -> float | None:
    """Parse a cell the way the deck prints it: "43.036" is 43,036, "141,9" is 141.9, "(28,8)" -28.8."""
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").strip()
    if text in ("", "-", "-", "n/a", "N/A"):
        return None
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()").replace("%", "")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    elif text.count(".") == 1 and len(text.split(".")[1]) == 3:
        text = text.replace(".", "")
    try:
        number = float(text)
    except ValueError:
        return None
    return -number if negative else number


def _fy25(statements: dict, block: str, label: str) -> float | None:
    cells = _row(statements.get(block) or {}, label)
    return _num(cells[-1]) if cells else None


def build_valuation_page(payload: dict, assumptions: dict | None = None) -> dict:
    """Assemble deck slide 4 for whichever option the analyst activated.

    The rules make the choice manual: `valuation_method` in data/assumptions/<ticker>.json decides. With
    no explicit choice the page falls back to the DCF and says so, and - when the issuer looks like a
    financial - it says on the page that the DDM would be the expected default for that sector. A cheap
    sector heuristic never silently switches the model.
    """
    assum = assumptions or {}
    method = str(assum.get("valuation_method") or "dcf").lower()
    if method in ("rnav", "nav"):
        from server.report.valuation_rnav import build_rnav_page

        page = build_rnav_page(payload, assum, {"num": _num})
        if page.get("available") and not assum.get("valuation_method"):
            page["notes"] = list(page.get("notes") or []) + [
                "Metode dipilih otomatis ke RNAV karena aset dominan; rules meminta pilihan manual, jadi "
                "tambahkan `valuation_method` di file assumptions untuk mengunci pilihan."
            ]
        return page
    if method in ("ddm", "dividend"):
        from server.report.valuation_ddm import build_ddm_page

        page = build_ddm_page(payload, assum, {"row": _row, "num": _num})
        if page.get("available") and not assum.get("valuation_method"):
            page["notes"] = list(page.get("notes") or []) + [
                "Metode dipilih otomatis ke DDM karena sektor emiten keuangan; rules meminta pilihan "
                "manual, jadi tambahkan `valuation_method` di file assumptions untuk mengunci pilihan."
            ]
        return page
    statements = payload.get("financial_statements") or {}
    cover = ((payload.get("cover") or {}).get("slide2") or {}).get("key_financials") or {}

    revenue_fy25 = _fy25(statements, "income", "Revenue")
    ebit_fy25 = _fy25(statements, "income", "EBIT")
    ebitda_cells = _row(cover, "EBITDA")
    ebitda_fy25 = _num(ebitda_cells[1]) if len(ebitda_cells) > 1 else None
    pretax = _fy25(statements, "income", "Pre-tax Profit")
    tax = _fy25(statements, "income", "Income Tax")
    # Bridge inputs follow the rules' "at the valuation date": the assumptions carry the Sectors figures
    # as of the latest quarter, which is later than the FY25A annual statement. The statement is the
    # fallback and the page says which one it used.
    total_debt = assum.get("total_debt", 0) / 1e9 or _fy25(statements, "balance", "Total Debt")
    cash = assum.get("cash", 0) / 1e9 or _fy25(statements, "balance", "Cash & Equivalents")
    bridge_basis = (
        "neraca Sectors per " + str((assum.get("bridge") or {}).get("as_of") or "tanggal valuasi")
        if assum.get("total_debt") else "neraca FY25A (laporan keuangan tahunan)"
    )

    fcff_doc_bn = ((assum.get("fcf_components_idr_bn") or {}).get("fcf_normalised"))
    sustain_capex_bn = ((assum.get("fcf_components_idr_bn") or {}).get("capex_sustaining_annualised"))
    wacc = assum.get("wacc")
    # Terminal growth is a ticker-agnostic team constant (3.5% as of Sep 2026).
    # Locking here so the same value is reflected in the page header, the gate
    # inputs, and the rendered assumption view (all read assum["g"] downstream).
    from server.report.valuation_constants import lock_g, lock_erp
    g = lock_g(assum)
    lock_erp(assum)
    multiple = assum.get("ev_multiple")
    shares_bn = (assum.get("shares_out") or 0) / 1e9
    price = assum.get("last_price")

    required = {
        "revenue FY25A": revenue_fy25, "EBIT FY25A": ebit_fy25, "EBITDA FY25A": ebitda_fy25,
        "tax FY25A": tax, "pre-tax FY25A": pretax, "total debt": total_debt, "cash": cash,
        "FCFF normalised": fcff_doc_bn, "capex sustaining": sustain_capex_bn,
        "WACC": wacc, "terminal g": g, "shares": shares_bn or None, "price": price,
    }
    missing = [k for k, v in required.items() if v in (None, 0)]
    if missing:
        return {
            "available": False,
            "title": "Valuasi Intrinsik",
            "missing": missing,
            "convention": "year-end (discount factor = 1/(1+WACC)^t); engine default mid-year di-disclose di catatan",
        "sources": [f"data/assumptions/{(payload.get('meta') or {}).get('ticker') or payload.get('ticker', '?')}.json", "payload financial_statements"],
        }

    # ---------- Blok 1: the explicit five-year build-up ----------
    # Linear-fade revenue path with ratio-driven reinvestment (ported 16 Sep 2026 from
    # the friend-tool pattern: g1 -> g_terminal across the N years, D&A/Capex/NWC ratios
    # off revenue so the rows vary end-to-end instead of holding a single FY25A scalar
    # flat for 5 years; the previous deck did the latter and the FCFF row collapsed to
    # identical values from FY27F onwards which read as fabricated data).
    #
    # Two-stage growth path:
    #   Stage 1 (years where the cover publishes a forecast): use the cover's value as-is.
    #     This protects the FY26F-FY28F Phase-8 ramp numbers that the BRIDS driver ships.
    #   Stage 2 (years beyond the cover's forecast horizon): linear fade from the LAST
    #     cover value to g_terminal across the remaining columns. Avoids the
    #     mathematically-pure-but-economically-absurd "132% YoY forever" extrapolation
    #     that an end-to-end fade produces.
    ebit_margin = ebit_fy25 / revenue_fy25
    tax_eff = tax / pretax
    da_bn = ebitda_fy25 - ebit_fy25                      # derived: EBITDA - EBIT

    cover_years = [str(h) for h in (cover.get("headers") or [])[1:]]
    cover_revenue = [_num(c) for c in (_row(cover, "Revenue") or [])[1:]]
    forecast_revenue_pairs = [(y, v) for y, v in zip(cover_years, cover_revenue)
                              if v is not None and "f" in y.lower()]
    g_term = float(g or 0.0)

    revenue_path: list[float] = []
    growth_path: list[float] = []
    cover_used_n = min(len(forecast_revenue_pairs), len(PERIODS))
    for i in range(cover_used_n):
        revenue_path.append(forecast_revenue_pairs[i][1])
        if i == 0 and revenue_fy25:
            growth_path.append(forecast_revenue_pairs[i][1] / revenue_fy25 - 1.0)
        else:
            growth_path.append(revenue_path[i] / revenue_path[i - 1] - 1.0)

    # Fade the last used cover value to g_terminal across remaining columns (linear).
    remaining = len(PERIODS) - cover_used_n
    if remaining > 0 and revenue_path:
        last_rev = revenue_path[-1]
        # Linear interpolation: g_terminal is the END-point rate; build N=remaining steps.
        # Inherited from friend tool: g_t = g_terminal each step keeps the path consistent.
        # To avoid a discontinuity at the join (cover value -> fade start), the first
        # remaining column uses 0 growth (the cover value held flat), then g_terminal onward.
        for j in range(remaining):
            if j == 0:
                growth_path.append(0.0)
                revenue_path.append(last_rev)
            else:
                growth_path.append(g_term)
                last_rev = last_rev * (1.0 + g_term)
                revenue_path.append(last_rev)
    # Pad to exactly len(PERIODS) if cover had no forecast at all (offline path).
    while len(revenue_path) < len(PERIODS):
        growth_path.append(g_term if revenue_path else 0.0)
        last = revenue_path[-1] if revenue_path else revenue_fy25
        revenue_path.append(last * (1.0 + g_term))

    g1 = growth_path[0] if growth_path else 0.0
    if forecast_revenue_pairs:
        g1_basis = (f"{forecast_revenue_pairs[0][0]} dari Key Financials Slide 2 / revenue FY25A "
                    f"({_nf.dec(g1 * 100, digits=1)}% YoY); kolom setelah horizon cover di-fade ke g_terminal "
                    f"{_nf.dec(g_term * 100, digits=2)}%")
    else:
        g1_basis = (f"YoY revenue FY25A/FY24A = {_nf.dec(g1 * 100, digits=1)}%; "
                    f"semua kolom di-fade ke g_terminal {_nf.dec(g_term * 100, digits=2)}%")
    revenue_basis = f"two-stage: {cover_used_n} kolom cover dipakai as-is, sisanya linear-fade ke g_terminal; {g1_basis}"

    # Ratio-driven reinvestment. The historical ratios are taken at FY25A; abidamassi
    # uses a moving average but the deck publishes a single FY25A anchor.
    da_ratio = (da_bn or 0) / revenue_fy25 if revenue_fy25 else 0.0
    capex_ratio = (sustain_capex_bn or 0) / revenue_fy25 if revenue_fy25 else 0.0
    # nwc_ratio: prefer AMMN.json nwc_fy25 (Q4-2025 working capital level / revenue FY25A);
    # fall back to working_capital_fy25 then 0 (modelled as zero, disclosed in narrative).
    nwc_level_fy25 = assum.get("nwc_fy25") or assum.get("working_capital_fy25") or 0.0
    nwc_ratio = (nwc_level_fy25 / revenue_fy25) if (revenue_fy25 and nwc_level_fy25) else 0.0
    # Capex may not fall below D&A while the company is growing (abidamassi s07 line 86):
    # if capex < D&A, the asset base is shrinking, and large D&A add-back + small capex
    # creates a fake FCFF-printing machine. Floor capex_ratio at da_ratio when g1 > 0.
    capex_ratio_applied = max(capex_ratio, da_ratio) if g1 > 0 else capex_ratio

    ebit = [r * ebit_margin for r in revenue_path]
    tax_on_ebit = [e * tax_eff for e in ebit]
    nopat = [e - t for e, t in zip(ebit, tax_on_ebit)]
    da_path = [r * da_ratio for r in revenue_path]
    capex_path = [r * capex_ratio_applied for r in revenue_path]
    # NWC level each year = revenue * nwc_ratio; DnWC = nwc[t] - nwc[t-1] (abidamassi s07 7.4).
    # Year 0 uses the FY25A anchor; the level is held flat from the FY25A point onward when
    # nwc_ratio = 0 (no anchor supplied) so DnWC = 0 in that case - same disclosure as before.
    nwc_levels = [nwc_level_fy25]
    for r in revenue_path:
        nwc_levels.append(r * nwc_ratio)
    nwc_path = [nwc_levels[t + 1] - nwc_levels[t] for t in range(len(PERIODS))]
    build_fcff = [n + d - c - w for n, d, c, w in zip(nopat, da_path, capex_path, nwc_path)]

    # Internal consistency check (abidamassi s07 7.6): Reinvestment Rate x ROIC = implied
    # growth. Gap to assumed revenue growth is reported, not hidden - the deck reader
    # needs to know when the build-up math is internally incoherent.
    roic_path: list[float] = []
    implied_g_path: list[float] = []
    reinvest_path: list[float] = []
    ic_proxy = (revenue_fy25 or 0.0) + ((total_debt or 0) - (cash or 0))   # rough invested-capital proxy
    prev_ic = ic_proxy
    for t in range(len(PERIODS)):
        reinvest = capex_path[t] - da_path[t] + nwc_path[t]
        rr = reinvest / nopat[t] if nopat[t] else None
        roic = nopat[t] / prev_ic if (prev_ic and nopat[t]) else None
        implied_g = (rr * roic) if (rr is not None and roic is not None) else None
        reinvest_path.append(reinvest)
        roic_path.append(roic if roic is not None else 0.0)
        implied_g_path.append((implied_g if implied_g is not None else 0.0) * 100.0)  # in %
        prev_ic = prev_ic + reinvest

    # the deck publishes the year-end convention (that is what the cover's DCF leg prints), so both
    # the displayed row and the engine call use it; the page states the convention it used.
    discount = [1.0 / ((1 + wacc) ** t) for t in range(1, len(PERIODS) + 1)]
    pv_fcff = [f * d for f, d in zip(build_fcff, discount)]
    growth = [None] + [
        (build_fcff[i] / build_fcff[i - 1] - 1) * 100 if build_fcff[i - 1] else None
        for i in range(1, len(PERIODS))
    ]

    # ---------- Blok 2/3: the engine does the terminal value and the bridge ----------
    scale = 1e9

    def run_bridge(fcff_series_bn: list[float], basis_label: str) -> dict:
        flags = _Flags()
        series = pd.DataFrame(
            {"FCFF": [v * scale for v in fcff_series_bn],
             "EBIT": [v * scale for v in ebit],
             "D&A": [v * scale for v in da_path]},
            index=range(1, len(PERIODS) + 1),
        )
        ebitda_abs = ebitda_fy25 * scale
        tv = engine.terminal_value(fcff_series_bn[-1] * scale, ebitda_abs, wacc, terminal_g=g, flags=flags)
        val = engine.discount_and_value(
            series, tv, wacc,
            {"cash": cash * scale, "total_debt": total_debt * scale, "minority": 0.0,
             "ebitda": ebitda_abs},
            SimpleNamespace(shares_outstanding=shares_bn * scale, price=price),
            flags, mid_year=False,   # the deck publishes the year-end convention (the cover's DCF leg)
        )
        net_debt = (total_debt - cash) * scale
        exit_tv = multiple * ebitda_abs if multiple else None
        exit_df = 1.0 / ((1 + wacc) ** len(PERIODS))
        exit_pv = exit_tv * exit_df if exit_tv else None
        exit_ev = (val["pv_explicit"] + exit_pv) if exit_pv else None
        exit_equity = (exit_ev + cash * scale - total_debt * scale - 0.0) if exit_ev else None
        return {
            "basis": basis_label,
            "fcff": fcff_series_bn,
            "growth": growth,
            "discount": discount,
            "pv_fcff": [f * d for f, d in zip(fcff_series_bn, discount)],
            "tv_gordon": tv["tv_nominal"],
            "tv_gordon_df": val["tv_discount_factor"],
            "pv_tv_gordon": val["pv_terminal"],
            "tv_exit": exit_tv,
            "pv_tv_exit": exit_pv,
            "pv_explicit": val["pv_explicit"],
            "ev_gordon": val["enterprise_value"],
            "ev_exit": exit_ev,
            "equity_gordon": val["equity_value"],
            "pv_explicit_abs": val["pv_explicit"],
            "equity_exit": exit_equity,
            "fv_gordon": val["fair_value_per_share"],
            "fv_exit": (exit_equity / (shares_bn * 1e9)) if exit_equity is not None else None,
            "tv_share": val["tv_share_of_ev"],
            "net_debt": net_debt,
            # the ratio is stated as payload data rather than computed in the template, so the PDF and the web page
            # cannot round it differently; None when the enterprise value is missing (never a substituted 0)
            "net_debt_share": (net_debt / val["enterprise_value"]) if val.get("enterprise_value") else None,
            "implied_exit_multiple": val["implied_exit_multiple"],
            "flags": flags.messages,
        }

    primary = run_bridge([fcff_doc_bn for _ in PERIODS], "FCFF normalised (steady-state, dokumentasi asumsi)")
    sensitivity_alts = {
        "build_up": run_bridge(build_fcff, "Build-up EBIT-based (Revenue x margin FY25A)"),
    }

    # ---------- Exhibit 9: WACC components, each with its source ----------
    wacc_rows = [
        ("Risk-free rate (Rf)", f"{_nf.dec(assum.get('rf', 0) * 100, digits=2)}%", "INDOGB 10Y (assumptions.rf)"),
        ("Beta (relevered, sektor)", f"{_nf.dec(assum.get('beta', 0), digits=4)}", "Regresi harian vs IHSG, disesuaikan sektor"),
        ("Equity Risk Premium (ERP)", f"{_nf.dec(assum.get('erp', 0) * 100, digits=2)}%", "Damodaran (country risk adj.)"),
        ("Cost of Equity (CAPM) = Rf + beta x ERP", f"{_nf.dec((assum.get('rf', 0) + assum.get('beta', 0) * assum.get('erp', 0)) * 100, digits=2)}%", "Hitung: rf + beta x erp"),
        ("Cost of Debt pre-tax", f"{_nf.dec(assum.get('cod', 0) * 100, digits=2)}%", "Beban bunga / rata-rata pinjaman (laporan keuangan)"),
        ("Effective tax rate", f"{_nf.dec(assum.get('tax', 0) * 100, digits=2)}%", "Pajak efektif FY25A = beban pajak / laba sebelum pajak"),
        ("Cost of Debt after-tax", f"{_nf.dec(assum.get('cod', 0) * (1 - assum.get('tax', 0)) * 100, digits=2)}%", "Hitung: Kd x (1 - t)"),
        ("Weight of Equity (market value)", f"{_nf.dec(assum.get('we', 0) * 100, digits=2)}%", "Kap. pasar / (kap. pasar + total debt)"),
        ("Weight of Debt (book value of debt)", f"{_nf.dec(assum.get('wd', 0) * 100, digits=2)}%", "Total debt / (kap. pasar + total debt)"),
        ("WACC = We x CoE + Wd x Kd x (1-t)", f"{_nf.dec(wacc * 100, digits=2)}%", "Hitung"),
    ]

    # ---------- Exhibit 10: the sensitivity grid, straight from the engine ----------
    # Exhibit 10 uses the engine's terminal_value + discount_and_value for every cell. The engine's own
    # sensitivity_grid is fixed to its mid-year config default, and this deck publishes the year-end
    # convention (that is what the cover's DCF leg prints), so the loop is written here on purpose: the
    # base cell then has to equal the bridge above, which is a tie-out the gate checks.
    proj = pd.DataFrame(
        {"FCFF": [fcff_doc_bn * scale for _ in PERIODS], "EBIT": [v * scale for v in ebit],
         "D&A": [v * scale for v in da_path]},
        index=range(1, len(PERIODS) + 1),
    )
    steps = engine.ENGINE_ASSUMPTIONS["sens_steps"]
    wacc_step = engine.ENGINE_ASSUMPTIONS["sens_wacc_step"]
    g_step = engine.ENGINE_ASSUMPTIONS["sens_g_step"]
    wacc_axis = [wacc + i * wacc_step for i in range(-steps, steps + 1)]
    g_axis = [g + j * g_step for j in range(-steps, steps + 1)]
    snapshot = {"cash": cash * scale, "total_debt": total_debt * scale, "minority": 0.0,
                "ebitda": ebitda_fy25 * scale}
    data_stub = SimpleNamespace(shares_outstanding=shares_bn * scale, price=price)
    fv_rows: list[dict] = []
    for w in wacc_axis:
        row = {}
        for g_value in g_axis:
            tv_cell = engine.terminal_value(fcff_doc_bn * scale, ebitda_fy25 * scale, w,
                                            terminal_g=g_value, flags=None)
            val_cell = engine.discount_and_value(proj, tv_cell, w, snapshot, data_stub, _Flags(),
                                                 mid_year=False) if tv_cell.get("valid") else {"valid": False}
            row[g_value] = val_cell.get("fair_value_per_share") if val_cell.get("valid") else None
        fv_rows.append(row)
    grid = {
        "fair_value": pd.DataFrame(
            [[row[g_value] for g_value in g_axis] for row in fv_rows],
            index=[f"{_nf.dec(w*100, digits=2)}%" for w in wacc_axis],
            columns=[f"{_nf.dec(g_value*100, digits=2)}%" for g_value in g_axis],
        ),
        "wacc_axis": wacc_axis,
        "g_axis": g_axis,
        "stats": None,
    }
    cells_flat = [v for row in grid["fair_value"].values.tolist() for v in row if v is not None]
    grid["stats"] = {
        "min": min(cells_flat), "max": max(cells_flat),
        "median": sorted(cells_flat)[len(cells_flat) // 2], "n_valid": len(cells_flat),
        "n_cells": len(wacc_axis) * len(g_axis),
    }
    fv_grid = grid.get("fair_value")
    wacc_axis, g_axis = grid.get("wacc_axis") or [], grid.get("g_axis") or []
    base_pick = None
    if fv_grid is not None and len(wacc_axis) and len(g_axis):
        base_pick = (len(wacc_axis) // 2, len(g_axis) // 2)   # the axes centre ON the base case
    swing = None
    if fv_grid is not None:
        flat = [v for row in fv_grid.values.tolist() for v in row if v is not None]
        if flat:
            swing = {"min": min(flat), "max": max(flat), "median": sorted(flat)[len(flat) // 2]}

    page = {
        "available": True,
        "method": "dcf",
        "title": "Valuasi Intrinsik - DCF (FCFF)",
        "subtitle": (
            "Metode dipilih manual: Opsi A - DCF FCFF. DDM tidak berlaku (emiten tidak membagi dividen) dan "
            "RNAV tidak dapat disusun (tidak ada data NAV per aset di Sectors) - lihat catatan metode."
        ),
        "periods": list(PERIODS),
        "blocks": {
            "build_up": {
                "Revenue": revenue_path, "EBIT": ebit, "Tax on EBIT": tax_on_ebit, "NOPAT": nopat,
                "(+) D&A": da_path, "(-) Capex": capex_path, "(-/+) Delta NWC": nwc_path,
                "FCFF (build-up)": build_fcff, "FCFF growth (%)": growth,
                "Discount factor": discount, "PV of FCFF": pv_fcff,
            },
            "documented_fcff": [fcff_doc_bn for _ in PERIODS],
        },
        "bridge": primary,
        "alternatives": sensitivity_alts,
        "wacc_rows": wacc_rows,
        "sensitivity": {
            "fair_value": fv_grid, "wacc_axis": wacc_axis, "g_axis": g_axis,
            "base": base_pick, "base_fv": primary["fv_gordon"], "swing": swing,
            "stats": grid.get("stats"),
        },
        "bridge_basis": bridge_basis,
        "drivers": {
            "revenue_fy25": revenue_fy25, "ebit_margin_fy25": ebit_margin * 100,
            "effective_tax": tax_eff * 100, "da_fy25": da_bn, "capex_sustaining": sustain_capex_bn,
            "multiple": multiple, "price": price, "revenue_basis": revenue_basis,
            "growth_path": growth_path, "g1": g1, "g_terminal": g_term, "g_term_input": g_term,
            "da_ratio": da_ratio, "capex_ratio": capex_ratio, "capex_ratio_applied": capex_ratio_applied,
            "nwc_ratio": nwc_ratio, "nwc_level_fy25": nwc_level_fy25,
            "ic_proxy_fy25": ic_proxy, "reinvest_path": reinvest_path,
            "roic_path": roic_path, "implied_g_path": implied_g_path,
        },
        "notes": _notes(primary, sensitivity_alts["build_up"], multiple, total_debt - cash, g, wacc, assum,
                         anchor_fv=((payload.get("valuation") or {}).get("legs") or {}).get("ev_ebitda")),
        "convention": "year-end (discount factor = 1/(1+WACC)^t); engine default mid-year di-disclose di catatan",
        "block2_headers": None,
        "block3_headers": None,
        "block1_headers": None,
        "assumptions_view": {
            "wacc": wacc, "g": g, "shares_bn": shares_bn, "rf": assum.get("rf"),
            "beta": assum.get("beta"), "erp": assum.get("erp"),
        },
        "legs": {
            "dcf": ((payload.get("valuation") or {}).get("legs") or {}).get("dcf"),
            "ev_ebitda": ((payload.get("valuation") or {}).get("legs") or {}).get("ev_ebitda"),
        },
        "sources": [
            "Sectors API: company_report, financials (income statement, balance sheet, cash flow), valuation",
            f"data/assumptions/{(payload.get('meta') or {}).get('ticker') or payload.get('ticker', '?')}.json (rf, beta, ERP, Kd, WACC, FCFF, net debt, shares)",
            "Engine valuasi internal: server/report/engines/dcf_engine",
        ],
    }
    # Valuation ladder - appended here so BOTH payload paths (PDF render and the
    # /payload endpoint) carry it, and so the frozen top-level key contract stays
    # at its declared count. Failure is non-fatal: a missing ladder must not cost
    # the deck its page.
    try:
        from server.report.ladder import build_ladder

        rating_box = ((payload.get("cover") or {}).get("rating_box") or {})
        page["ladder"] = build_ladder(
            str(payload.get("ticker") or "").upper(),
            price=rating_box.get("price") or assum.get("last_price"),
            target=rating_box.get("tp") or assum.get("target_price"),
        )
    except Exception as exc:  # noqa: BLE001
        import logging as _logging

        _logging.getLogger(__name__).warning("valuation ladder unavailable: %s", exc)
    return _view(page)


def _notes(primary: dict, build_up: dict, multiple, net_debt_bn: float, g: float, wacc: float,
           assum: dict | None = None, anchor_fv: float | None = None) -> list[str]:
    """The disclosures the rules require: finite reserve, the terminal gap, and what was not modelled."""
    notes: list[str] = []
    # The gate-primary leg's multiple and the level it multiplies must be stated here, with the rejected
    # basis named - a target price whose basis is only in the payload is not disclosed to the reader.
    _basis = assum.get("ev_multiple_basis")
    if _basis:
        own = assum.get("ev_multiple_own_history") or {}
        extra = ""
        if own and own.get("usable_as_anchor") is False:
            extra = (f" Own-history multiple ({_nf.dec(own.get('trailing_mean', 0), digits=2)}× trailing / "
                     f"{_nf.dec(own.get('normalised_mean', 0), digits=2)}× normalised) DITOLAK sebagai anchor: EV bertahan "
                     f"Rp 506-672 tn saat EBITDA naik-turun 2×, jadi multiple itu menghukum level yang sudah "
                     f"pulih (memberi Rp 13.559/saham, 2,8× harga).")
        notes.append("BASIS MULTIPLE (leg gate-primary): " + str(_basis) + extra + " " +
                     str(assum.get("ebitda_leg_level_note") or ""))
    # A reader who meets Rp 148 and Rp 5.667 on the same page has to be told why they differ and which one the
    # target price uses. Fires on the gap, not on a ticker: it stays silent when the two bases agree.
    if anchor_fv and primary.get("fv_gordon") and primary["fv_gordon"] > 0 and float(anchor_fv) > 0:
        _gap = max(float(anchor_fv), primary["fv_gordon"]) / min(float(anchor_fv), primary["fv_gordon"])
        if _gap > 1.5:
            notes.append(
                f"BASIS TARGET PRICE - DCF FCFF di halaman ini (terminal Gordon) memberi Rp "
                f"{_rp(primary['fv_gordon'])} sementara anchor EV/EBITDA {_fmt(multiple, 2)}× "
                f"(basis gate-primary) memberi Rp "
                f"{_rp(float(anchor_fv))}: selisih {_nf.dec(_gap, digits=1)}×. Keduanya tidak dirata-rata; "
                "anchor dipakai sebagai target price dan DCF tetap menjadi cross-check intrinsik."
            )
    if primary["fv_gordon"] is not None and primary["fv_exit"] is not None and primary["fv_gordon"] > 0:
        ratio = max(primary["fv_exit"], primary["fv_gordon"]) / min(primary["fv_exit"], primary["fv_gordon"])
        notes.append(
            f"UNRESOLVED ASSUMPTION - terminal Gordon (g {_nf.dec(g*100, digits=1)}%) memberi Rp {_rp(primary['fv_gordon'])} "
            f"sementara terminal exit multiple {_nf.dec(multiple, digits=2)}× memberi Rp {_rp(primary['fv_exit'])}: selisih "
            f"{_nf.dec(ratio, digits=1)}× pada basis FCFF yang sama. Tidak dirata-rata; angka mana yang dipakai harus diputuskan analis."
        )
    if build_up["equity_gordon"] is not None and build_up["equity_gordon"] <= 0:
        notes.append(
            "Basis build-up EBIT-based menghasilkan equity value negatif: net debt (Rp "
            f"{_bn(net_debt_bn)}) melebihi value operasi pada FCFF build-up, jadi lapisan "
            "steady-state asumsi (FCFF normalised) yang menjaga hasil tetap positif - perbedaan basis ini "
            "dinyatakan, bukan disembunyikan."
        )
    notes.append(
        "Reserve finite: DCF perpetual secara teori tidak defensible untuk tambang dengan umur cadangan "
        "terbatas; terminal pertumbuhan di sini dipakai sebagai proxy jangka panjang, bukan klaim cadangan abadi."
    )
    notes.append(
        "Konvensi diskon year-end (DF = 1/(1+WACC)^t). Engine internal default-nya mid-year; selisihnya "
        "±6% ke atas pada nilai wajar, dan konvensi yang dipakai di sini adalah yang sama dengan leg DCF "
        "di halaman 1 supaya kedua halaman tidak berbeda."
    )
    notes.append(
        "Build-up baris memakai pola linear-fade (g1 -> g_terminal) untuk Revenue selama N tahun, "
        "lalu D&A / Capex / Delta NWC diturunkan dari rasio FY25A dikalikan Revenue per tahun (port "
        "16 Sep 2026). Capex di-floor di D&A ratio ketika pertumbuhan positif supaya D&A add-back + "
        "capex kecil tidak menjadi FCFF printer palsu. Konsistensi internal (Reinvestment Rate x ROIC = "
        "implied growth) dilaporkan per tahun; gap ke growth yang diasumsikan tidak disembunyikan."
    )
    return notes


def _fmt(value, digits: int = 1) -> str:
    """Deck number format: Indonesian separators, em dash when absent."""
    if value is None:
        return "-"
    return f"{value:,.{digits}f}".replace(",", "\u2009").replace(".", ",").replace("\u2009", ".")


def _fmt0(value) -> str:
    return "-" if value is None else f"{_nf.idn(value, digits=0)}".replace(",", ".")


def _view(page: dict) -> dict:
    """Shape what the template prints, so the markup carries no arithmetic."""
    if not page.get("available"):
        return page
    periods = page["periods"]
    build = page["blocks"]["build_up"]
    row_order = [
        ("Revenue", "Revenue"),
        ("EBIT", "EBIT"),
        ("Tax on EBIT (tarif efektif)", "Tax on EBIT"),
        ("NOPAT", "NOPAT"),
        ("(+) Depreciation & Amortization", "(+) D&A"),
        ("(-) Capital Expenditure", "(-) Capex"),
        ("(-/+) Increase/Decrease in Net Working Capital", "(-/+) Delta NWC"),
        ("FCFF (build-up)", "FCFF (build-up)"),
        ("FCFF growth (%)", "FCFF growth (%)"),
        ("Discount factor (1/(1+WACC)^n)", "Discount factor"),
        ("PV of FCFF", "PV of FCFF"),
    ]
    page["block1_rows"] = [
        (
            label,
            [
                "-" if val is None else _fmt(val, 3 if key == "Discount factor" else 1)
                for val in build.get(key, [])
            ],
        )
        for label, key in row_order
    ]
    b = page["bridge"]
    av = page["assumptions_view"]
    tv_df_exit = 1.0 / ((1 + av["wacc"]) ** len(periods))
    page["block2_rows"] = [
        ("Terminal FCFF (FCFF terakhir x (1+g))", _fmt(b["fcff"][-1]), _fmt(b["fcff"][-1])),
        ("Terminal growth (g) - asumsi eksplisit", _fmt(av["g"] * 100, 2) + "%", "-"),
        ("Terminal Value (undiscounted)", _fmt(b["tv_gordon"] / 1e9), _fmt((b["tv_exit"] or 0) / 1e9)),
        ("Discount factor terminal", _fmt(b["tv_gordon_df"], 3), _fmt(tv_df_exit, 3)),
        ("PV of Terminal Value", _fmt(b["pv_tv_gordon"] / 1e9), _fmt((b["pv_tv_exit"] or 0) / 1e9)),
        ("Implied exit multiple dari TV Gordon", _fmt(b["implied_exit_multiple"], 2) + "×",
         _fmt(page["drivers"]["multiple"], 2) + "×"),
    ]
    page["block3_rows"] = [
        ("Sum PV of FCFF (periode eksplisit)", _fmt(b["pv_explicit"] / 1e9), "-"),
        ("(+) PV of Terminal Value (Gordon)", _fmt(b["pv_tv_gordon"] / 1e9), "-"),
        ("Enterprise Value", _fmt(b["ev_gordon"] / 1e9), "-"),
        ("(-) Net Debt (Total Debt - Cash)", _fmt(b["net_debt"] / 1e9), "-"),
        ("(+/-) Minority Interest / Non-Operating Assets", _fmt(0.0), "-"),
        ("Equity Value", _fmt(b["equity_gordon"] / 1e9), "-"),
        ("Jumlah saham beredar (bn saham)", _fmt(av["shares_bn"], 2), "-"),
        ("Fair Value per Share - terminal Gordon", _fmt0(b["fv_gordon"]), _fmt0(b["fv_gordon"])),
        ("Fair Value per Share - terminal exit multiple", _fmt0(b["fv_exit"]), _fmt0(b["fv_exit"])),
    ]
    grid = page["sensitivity"]["fair_value"]
    base = page["sensitivity"]["base"]
    page["sensitivity"]["columns"] = [str(c) for c in grid.columns]
    # Colour by upside, the way the tools' sensitivity heatmap does: red where the grid prices below the market,
    # cream at parity, navy where it prices well above. Computed here rather than in the template so nothing has
    # to parse a formatted string back into a number.
    # The reference is the base case, not the market price: this leg's grid sits far below the traded price as a
    # whole (the method bars carry that point), so reading it against the price turns every cell the same colour
    # and says nothing about which WACC/g combination moves the value.
    base_ref = page["sensitivity"].get("base_fv") or 0

    def _band(fv):
        try:
            fv = float(fv)
        except (TypeError, ValueError):
            return ""
        if not (base_ref and math.isfinite(fv)):
            return ""
        rel = (fv / float(base_ref) - 1) * 100
        if rel <= -50:
            return "h-neg2"
        if rel <= -15:
            return "h-neg1"
        if rel < 15:
            return "h-mid"
        if rel < 50:
            return "h-pos1"
        return "h-pos2"

    page["sensitivity"]["rows"] = [
        {
            "label": str(label),
            "cells": [
                {"value": _fmt0(val), "base": bool(base and r == base[0] and c == base[1]), "band": _band(val)}
                for c, val in enumerate(grid.loc[label].tolist())
            ],
        }
        for r, label in enumerate(grid.index)
    ]
    page["sensitivity"]["base_wacc"] = str(grid.index[base[0]]) if base else "-"
    page["sensitivity"]["base_g"] = str(grid.columns[base[1]]) if base else "-"
    legs = page.get("legs") or {}
    page["crosscheck_rows"] = [
        ("DCF (leg kedua, halaman ini)", _fmt0(b["fv_gordon"]), "Cross-check intrinsik"),
        ("DCF + terminal exit multiple", _fmt0(b["fv_exit"]), "Batas atas skenario multiple"),
        ("EV/EBITDA mid-cycle " + _fmt(page["drivers"]["multiple"], 2) + "×",
         _fmt0(legs.get("ev_ebitda")), "ANCHOR target price (halaman 1 & 5)"),
        ("Harga pasar", _fmt0(page["drivers"]["price"]), "Sectors, penutupan terakhir"),
    ]
    page["narrative"] = _narrative(page)
    return page


def _narrative(page: dict) -> list[str]:
    """The integrated narrative the rules ask for: dominant parameter, driver linkage, the gap."""
    b = page["bridge"]
    grid = page["sensitivity"]["fair_value"]
    rows = [grid.loc[i].tolist() for i in grid.index]
    cols = [str(c) for c in grid.columns]
    wacc_span = (max(r[0] for r in rows) - min(r[0] for r in rows)) if rows else 0
    g_span = (max(r[-1] for r in rows) - min(r[-1] for r in rows)) if rows else 0
    dominant = "WACC" if wacc_span >= g_span else "terminal growth"
    d = page["drivers"]
    swing = page["sensitivity"]["swing"] or {"min": 0, "max": 0}
    return [
        (
            f"Parameter paling sensitif: {dominant}. Menggeser WACC dari {str(grid.index[0])} ke "
            f"{str(grid.index[-1])} mengubah nilai wajar {_fmt0(wacc_span)} per saham; menggeser terminal growth "
            f"dari {cols[0]} ke {cols[-1]} mengubah {_fmt0(g_span)}. Dua hal membuat hasil ini rapuh: "
            f"PV of terminal value menyumbang {_fmt(b['tv_share'] * 100, 1)}% dari enterprise value, dan net debt "
            f"Rp {_fmt0(b['net_debt'] / 1e9)} bn memakan hampir seluruh Rp {_fmt0(b['ev_gordon'] / 1e9)} bn "
            "enterprise value (equity tersisa "
            f"Rp {_fmt0(b['equity_gordon'] / 1e9)} bn, {_fmt(b['equity_gordon'] / b['ev_gordon'] * 100, 1)}% dari EV). "
            "Di dalam grid ini saja nilai wajar bergerak dari "
            f"Rp {_fmt0(swing['min'])} sampai Rp {_fmt0(swing['max'])}."
        ),
        (
            "Penghubung ke driver bisnis (Slide 2-3): jalur pendapatan memakai pola linear-fade "
            f"({d['revenue_basis']}) sehingga baris Revenue, EBIT, Tax, NOPAT, D&A, Capex, dan Delta NWC "
            "ikut bervariasi end-to-end (bukan di-hold flat dari kolom ke-3); "
            f"marjin EBIT {_fmt(d['ebit_margin_fy25'], 1)}% (level FY25A); "
            f"pajak tarif efektif {_fmt(d['effective_tax'], 1)}%, bukan statutori; "
            f"D&A ratio {_fmt(d['da_ratio'] * 100, 1)}% revenue, capex ratio {_fmt(d['capex_ratio_applied'] * 100, 1)}% "
            f"revenue (floor di D&A ratio saat pertumbuhan positif), "
            f"Delta NWC dihitung dari perubahan level NWC ratio {_fmt(d['nwc_ratio'] * 100, 1)}% revenue. "
            f"Pemeriksaan konsistensi internal (RR x ROIC = implied growth) per tahun tersedia di catatan metode."
        ),
        (
            "Gap antar metode dibaca sebagai unresolved assumption, bukan dirata-rata: terminal Gordon dan terminal "
            f"exit multiple berbeda {_nf.dec(max(b['fv_gordon'], b['fv_exit']) / min(b['fv_gordon'], b['fv_exit']), digits=1)}× "
            f"(Rp {_fmt0(b['fv_gordon'])} vs Rp {_fmt0(b['fv_exit'])}) di basis FCFF yang sama, dan basis build-up "
            f"EBIT-based menghasilkan equity value negatif (Rp {_fmt0(page['alternatives']['build_up']['equity_gordon'] / 1e9)} bn). "
            "Target price laporan berdiri di leg relative (EV/EBITDA mid-cycle); halaman ini memperlihatkan seberapa "
            "jauh model arus kas melihat ke bawah."
        ),
    ]


def _rp(value: float | None) -> str:
    return "n/a" if value is None else f"{_nf.idn(value, digits=0)}".replace(",", ".")


def _bn(value: float | None) -> str:
    return "n/a" if value is None else f"{_nf.idn(value, digits=0)}".replace(",", ".")


def load_assumptions(ticker: str) -> dict:
    path = REPO / "data" / "assumptions" / f"{ticker}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
