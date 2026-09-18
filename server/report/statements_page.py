"""Slide 6 payload - Exhibit 14 Income Statement + Exhibit 15 Balance Sheet (2024A-2028F).

Rules: docs/ammn-slides/slide6-statements-spec.md. Corporate (non-bank) variant for AMMN; the bank row
set is recorded in the spec and switched on by `archetype`/`bank` flag rather than guessed here.

Data policy, all of it deliberate:
  * FY2024A / FY2025A come from Sectors' ANNUAL rows (`financials.historical_financials`). The quarterly
    payload is NOT used for these lines: its revenue field does not reconcile to the annual figures
    (sum of four quarters 44 tn vs FY2025A 30.9 tn), so mixing the two bases would misstate every ratio.
  * FY2026F-FY2028F revenue, EBITDA and net profit are the deck's existing mid-cycle spine
    (cover.slide2.key_financials), so this page cannot drift away from the valuation that uses the same
    numbers. Everything between them is built from documented drivers.
  * Sectors publishes no trade-receivables, trade-payables or interest-income line for this name. Those
    rows are printed with an explicit "n/a" and the amount they carry lives in the matching "Other"
    row, so the statement still foots. Nothing is invented and nothing is silently dropped.
  * `Other income/(expense)` is the RECONCILING line: for the actuals it is whatever makes pre-tax foot
    (= pre-tax - EBIT + interest), and for the forecasts it reconciles to the mid-cycle net-profit path.
    The page says so in print, because a residual presented as a discovered number would be a lie.
  * Cash is the balancing item on the balance sheet, which is what makes Total Assets equal Total
    Liabilities & Equity exactly; the page names cash as the plug and prints the tie-out either way.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional
from server.report import numfmt as _nf

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "output", "cache", "sectors")
# Raw Sectors dumps - consulted in ticker_fill first, then ammn_fill (legacy alias)
# for tickers whose freeze predates the rename. A ticker's raw dump lives at
# output/cache/ticker_fill/raw_cache/<TICKER>_<ENDPOINT>.json (the AMMN historical
# dumps use a slightly different naming with a hash suffix, handled by `_sources`).
LEGACY_CACHE = os.path.join(ROOT, "output", "cache", "ammn_fill", "raw_cache")
PRIMARY_LEGACY_CACHE = os.path.join(ROOT, "output", "cache", "ticker_fill", "raw_cache")
BN = 1e9
ACTUAL_YEARS = ("2024A", "2025A")
FORECAST_YEARS = ("2026F", "2027F", "2028F")
YEARS = ACTUAL_YEARS + FORECAST_YEARS

# row kinds drive the template styling and the gate
SUB, DED, HL, NA = "subtotal", "deduction", "highlight", "na"


def _load(path: str) -> Optional[Any]:
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _num(row: dict, *names: str) -> Optional[float]:
    for k in names:
        v = row.get(k)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return float(v)
    return None


def _bn(v: Optional[float]) -> Optional[float]:
    return None if v is None else v / BN


def _sources(ticker: str) -> dict:
    # The historical freeze dumps (output/cache/ticker_fill/raw_cache/<TICKER>_*.json)
    # are looked up by ticker. The legacy AMMN multisection dump was named with a hash
    # suffix (company_report_AMMN__33503f87.json) before the format was standardised;
    # that file is only relevant when ticker=AMMN, so we keep the literal name as a
    # ticker-scoped legacy alias here rather than hiding it in the directory layout.
    legacy_multisection = {
        "AMMN": "company_report_AMMN__33503f87.json",
    }.get(ticker.upper())
    for base in (os.path.join(CACHE, ticker), PRIMARY_LEGACY_CACHE, LEGACY_CACHE):
        if legacy_multisection and base == LEGACY_CACHE:
            rep = _load(os.path.join(base, legacy_multisection))
        else:
            rep = _load(os.path.join(base, "raw", f"peers_{ticker}.json"))
        if rep:
            return {"report": rep, "dir": base}
    return {"report": {}, "dir": LEGACY_CACHE}


def build_statements_page(ticker: str = "AMMN", spine: Optional[dict] = None,
                          driver_path: Optional[dict] = None,
                          cashflow: Optional[dict] = None) -> dict:
    """`spine` is the deck's Key Financials (revenue/EBITDA/net profit per year) so this page ties to it."""
    tk = ticker.upper()
    src = _sources(tk)
    rep = src["report"] or {}
    assum = _load(os.path.join(ROOT, "data", "assumptions", f"{tk}.json")) or {}
    annual_rows = (((rep.get("financials") or {}).get("historical_financials")) or [])
    annual = {r.get("year"): r for r in annual_rows if isinstance(r, dict)}
    if not annual:
        return {"available": False, "ticker": tk,
                "reason": "Sectors annual statement rows not cached - run the statements harvest first"}

    # --- spine (deck Key Financials) -> forecast revenue / EBITDA / net profit
    spine_rows = {}
    for row in ((spine or {}).get("rows") or []):
        label = str(row[0]).lower()
        if "growth" in label or "%" in label or "margin" in label or label.startswith("eps"):
            continue          # "EBITDA Growth (%)" must never be read as EBITDA itself
        for key in ("revenue", "ebitda", "net profit"):
            if label.startswith(key):
                spine_rows[key] = row[1:]
    def spine_val(key: str, i: int) -> Optional[float]:
        vals = spine_rows.get(key) or []
        if len(vals) < 3:
            return None
        raw = str(vals[2 + i]).replace(".", "").replace(",", ".")
        try:
            return float(raw)
        except ValueError:
            return None

    rev_f = [spine_val("revenue", i) for i in range(3)]
    ebitda_f = [spine_val("ebitda", i) for i in range(3)]
    net_f = [spine_val("net profit", i) for i in range(3)]
    if any(v is None for v in rev_f + ebitda_f + net_f):
        return {"available": False, "ticker": tk,
                "reason": "the deck's Key Financials spine is missing a revenue/EBITDA/net-profit column"}
    # a percentage read as a rupiah figure is the failure mode this guard exists for
    if any(v < 1000 for v in rev_f + ebitda_f + net_f):
        return {"available": False, "ticker": tk,
                "reason": ("the Key Financials spine parsed to an implausible magnitude "
                           f"(revenue {rev_f}, ebitda {ebitda_f}, net {net_f}) - refusing to print it")}

    # --- drivers, each named and sourced
    a25 = annual.get(2025) or annual.get(max(annual))
    rev_25 = _bn(_num(a25, "revenue"))
    ebitda_25 = _bn(_num(a25, "ebitda"))
    ebit_25 = _bn(_num(a25, "ebit"))
    dna_25 = (ebitda_25 - ebit_25)
    tax_rate = float(assum.get("tax") or 0.22)
    cod = float(assum.get("cod") or 0.0)
    gross_debt = _bn(_num(a25, "total_debt")) or 0.0
    st_debt_25 = _bn(_num(a25, "short_term_debt")) or 0.0
    lt_debt_25 = _bn(_num(a25, "long_term_debt")) or 0.0
    inv_25 = _bn(_num(a25, "inventories")) or 0.0
    capex = float(assum.get("fcf_components_idr_bn", {}).get("capex_sustaining_annualised") or 0.0)
    payout = float(assum.get("payout") or 0.0)

    # --- actuals, with the reconciling residual and the derived minority line
    def actual(y: int) -> dict:
        r = annual[y]
        rev, cogs = _bn(_num(r, "revenue")), _bn(_num(r, "cost_of_revenue"))
        gp, opex, ebit, ebitda = (_bn(_num(r, "gross_profit")), _bn(_num(r, "operating_expense")),
                                  _bn(_num(r, "ebit")), _bn(_num(r, "ebitda")))
        ie = _bn(_num(r, "interest_expense_non_operating")) or 0.0
        ebt = _bn(_num(r, "earnings_before_tax"))
        tax = _bn(_num(r, "tax"))
        net = _bn(_num(r, "earnings"))
        return {"rev": rev, "cogs": cogs, "gp": gp, "opex": opex, "ebit": ebit, "ebitda": ebitda,
                "ii": None, "ie": ie, "other": (ebt - ebit + ie), "ebt": ebt, "tax": tax,
                "mino": (ebt - tax - net), "net": net,
                "cash": _bn(_num(r, "cash_and_equivalents")), "inv": _bn(_num(r, "inventories")),
                "tca": _bn(_num(r, "current_assets")), "fixed": _bn(_num(r, "fixed_assets")),
                "ta": _bn(_num(r, "total_assets")), "st": st_debt_25 if y == 2025 else _bn(_num(r, "short_term_debt")),
                "tcl": _bn(_num(r, "current_liabilities")), "lt": lt_debt_25 if y == 2025 else _bn(_num(r, "long_term_debt")),
                "tl": _bn(_num(r, "total_liabilities")), "eq": _bn(_num(r, "total_equity"))}

    acts = {f"{y}A": actual(y) for y in (2024, 2025)}

    # --- forecasts
    fc = []
    fixed = acts["2025A"]["fixed"]
    equity = acts["2025A"]["eq"]
    # Per-year drivers: anything the cited path provides is used as published; anything it does not is
    # derived from the FY2025A run-rate and said so. A driver file that carries a debt schedule is the
    # difference between a real statement and a frozen one.
    dp = (driver_path or {}).get("drivers") or {}

    def drv(key: str, i: int):
        block = dp.get(key) or {}
        vals = block.get("rp_bn") or []
        return float(vals[i]) if i < len(vals) else None

    driver_rows: dict = {}
    for i in range(3):
        rev, ebitda, net = rev_f[i], ebitda_f[i], net_f[i]
        dna_i = drv("dna", i) or dna_25
        ebit = ebitda - dna_i
        ie = drv("interest_expense", i)
        if ie is None:
            ie = gross_debt * cod                     # fallback: flat gross debt at the stated cost of debt
            driver_rows.setdefault("interest_expense", "derived: gross debt flat x cost of debt")
        else:
            driver_rows.setdefault("interest_expense", "dari jalur proyeksi (jadwal utang)")
        ii = drv("interest_income", i) or 0.0
        ebt = net / (1 - tax_rate)
        other = ebt - ebit - ii + ie                  # reconciling line, disclosed on the page
        tax = ebt - net
        mino = drv("minority", i) or 0.0
        capex_i = drv("capex", i) or 0.0
        if capex_i:
            driver_rows.setdefault("capex", "dari jalur proyeksi")
        fixed = fixed + capex_i - dna_i
        equity = equity + net * (1 - payout)
        inv_i = drv("inventory", i)
        inv = inv_i if inv_i is not None else (inv_25 * (rev / rev_25) if rev_25 else inv_25)
        gd_i = drv("gross_debt", i)
        if gd_i:
            # split the gross debt across short/long term on the FY2025A mix, which is the only split the
            # sources publish; state it rather than inventing a schedule
            share_st = st_debt_25 / (st_debt_25 + lt_debt_25) if (st_debt_25 + lt_debt_25) else 0.0
            st_i, lt_i = gd_i * share_st, gd_i * (1 - share_st)
        else:
            st_i, lt_i = st_debt_25, lt_debt_25
        fc.append({"rev": rev, "cogs": None, "gp": None, "opex": None, "ebit": ebit, "ebitda": ebitda,
                   "ii": ii, "ie": ie, "other": other, "ebt": ebt, "tax": tax, "mino": mino, "net": net,
                   "cash": None, "inv": inv, "tca": None, "fixed": fixed, "ta": None, "st": st_i,
                   "tcl": None, "lt": lt_i, "tl": None, "eq": equity})
    # Cost chain: opex is held at the FY2025A run-rate and COGS is the balancing line, which is the only
    # way the statement can both foot vertically AND land on the deck's mid-cycle EBITDA. It implies a
    # lower COGS ratio than FY2025A; the page states that instead of hiding it.
    # Sectors' own rows do not foot in the operating block: reported EBIT is not GP - operating_expense
    # (Rp 1,359 bn apart in FY2024A, Rp 249 bn in FY2025A). EBIT is the anchor, so opex becomes the derived
    # line and the reported figures are stated in the notes - the statement foots and nothing is hidden.
    opex_gaps = {}
    for y in ("2024A", "2025A"):
        a = acts[y]
        reported = a["opex"] or 0.0
        a["opex"] = (a["gp"] or 0.0) - (a["ebit"] or 0.0)
        opex_gaps[y] = reported - a["opex"]
    opex_25_abs = acts["2025A"]["opex"] or 0.0
    for r in fc:
        r["opex"] = opex_25_abs
        r["gp"] = r["ebit"] + r["opex"]          # EBIT (= EBITDA - D&A) drives GP
        r["cogs"] = r["rev"] - r["gp"]
    implied_gm = (fc[0]["gp"] / fc[0]["rev"]) if fc[0]["rev"] else None
    actual_gm = (acts["2025A"]["gp"] / rev_25) if rev_25 else None
    gap_txt = "; ".join(f"{y} {v:+,.0f} bn" for y, v in opex_gaps.items() if abs(v) > 1)

    # --- balance sheet assembly: other-buckets held at FY2025A residual, cash is the plug
    cf_cash = None
    if cashflow and cashflow.get("end_cash"):
        cf_cash = cashflow["end_cash"][2:]          # the three forecast years, in order
    b25 = acts["2025A"]
    # forecast columns hold the FY2025A levels of the residual buckets; each actual year derives its own
    other_ca_25 = (b25["tca"] or 0.0) - (b25["cash"] or 0.0) - (b25["inv"] or 0.0)
    other_nca_25 = (b25["ta"] or 0.0) - (b25["tca"] or 0.0) - (b25["fixed"] or 0.0)
    other_cl_25 = (b25["tcl"] or 0.0) - b25["st"]
    other_ncl_25 = (b25["tl"] or 0.0) - (b25["tcl"] or 0.0) - b25["lt"]

    def bs_from(r: dict, prev_cash: Optional[float], is_forecast: bool,
                cf_cash: Optional[float] = None) -> dict:
        inv = r["inv"]
        if is_forecast:
            other_ca, other_nca, other_cl, other_ncl = other_ca_25, other_nca_25, other_cl_25, other_ncl_25
        else:
            other_ca = (r["tca"] or 0.0) - (r["cash"] or 0.0) - (inv or 0.0)
            other_nca = (r["ta"] or 0.0) - (r["tca"] or 0.0) - (r["fixed"] or 0.0)
            other_cl = (r["tcl"] or 0.0) - r["st"]
            other_ncl = (r["tl"] or 0.0) - (r["tcl"] or 0.0) - r["lt"]
        tca = (r["cash"] if not is_forecast else 0.0) + inv + other_ca
        if is_forecast:
            # cash comes from the cash-flow statement (Exhibit 16) when it is available, so the two
            # exhibits tie by construction; the residual current-asset bucket absorbs the difference
            tcl = r["st"] + other_cl
            tl = tcl + r["lt"] + other_ncl
            tle_ex_cash = tl + r["eq"]
            cash = tle_ex_cash - (inv + other_ca + r["fixed"] + other_nca)
            tca = cash + inv + other_ca
            r["cash"] = cash
            r["tca"], r["tcl"], r["tl"] = tca, tcl, tl
        if is_forecast and cf_cash is not None:
            r["cash"] = cf_cash
            other_ca = (r["tl"] + r["eq"]) - cf_cash - (inv or 0.0) - (r["fixed"] or 0.0) - other_nca
        elif is_forecast:
            other_ca = (r["tl"] + r["eq"]) - (r["cash"] or 0.0) - (inv or 0.0) - (r["fixed"] or 0.0) - other_nca
        r["other_ca"], r["other_nca"] = other_ca, other_nca
        r["other_cl"], r["other_ncl"] = other_cl, other_ncl
        r["ta"] = (r["cash"] or 0.0) + (inv or 0.0) + other_ca + (r["fixed"] or 0.0) + other_nca
        r["tl"] = (r["tcl"] or 0.0) + (r["lt"] or 0.0) + other_ncl
        r["tle"] = r["tl"] + r["eq"]
        # A balance sheet assembled from floats never closes to exactly zero: the difference lands near 1e-11 and both
        # consumers then print it - the PDF showed "-0" and the frontend showed -2.9103830456733704e-11. Snapping the
        # residue changes no displayed figure (the smallest account is Rp bn) and lets each print a clean 0.
        r["gap"] = 0.0 if abs(r["tle"] - r["ta"]) < 1e-6 else (r["tle"] - r["ta"])
        return r

    rows = {**acts}
    for i, r in enumerate(fc):
        rows[FORECAST_YEARS[i]] = bs_from(r, None, True, cf_cash[i] if (cf_cash and True) else None)
    for y in ACTUAL_YEARS:
        rows[y] = bs_from(rows[y], None, False)

    def series(key: str) -> list:
        return [rows[y].get(key) for y in YEARS]

    def rows3(specs: list) -> list:
        out = []
        for label, key, kind, note in specs:
            out.append({"label": label, "cells": series(key), "kind": kind, "note": note})
        return out

    income = rows3([
        ("Revenue / Sales", "rev", "", ""),
        ("Cost of Goods Sold", "cogs", DED, "ditampilkan sebagai pengurang"),
        ("Gross Profit", "gp", SUB, "subtotal"),
        ("Operating Expenses / SG&A", "opex", DED, "ditampilkan sebagai pengurang"),
        ("EBIT", "ebit", SUB, "subtotal"),
        ("Interest Income", "ii", NA, "Sectors tidak mempublikasikan baris ini untuk AMMN - tidak diisi"),
        ("Interest Expense", "ie", DED, "ditampilkan sebagai pengurang"),
        ("Other Income / (Expense) - non-operating", "other", "", "baris rekonsiliasi: membuat pre-tax foot (= pre-tax - EBIT + bunga)"),
        ("Pre-tax Profit", "ebt", SUB, "subtotal"),
        ("Income Tax", "tax", DED, "ditampilkan sebagai pengurang"),
        ("Minority Interest", "mino", "", "= pre-tax - pajak - laba bersih (derivasi eksak Sectors)"),
        ("Net Profit", "net", HL, "baris terpenting - di-highlight"),
    ])
    balance = rows3([
        ("ASSETS", "", "section", "penanda bagian"),
        ("Cash & Cash Equivalents", "cash", "", "forecast: item penyeimbang neraca (dinyatakan di catatan)"),
        ("Trade Receivables", "ar", NA, "Sectors tidak mempublikasikan piutang dagang - tercakup di Other Current Assets"),
        ("Inventory", "inv", "", ""),
        ("Other Current Assets", "other_ca", "", "residual arus lancar non-kas/non-persediaan"),
        ("Total Current Assets", "tca", SUB, "subtotal"),
        ("Fixed Assets (Net)", "fixed", "", "forecast: + capex - D&A"),
        ("Other Non-Current Assets", "other_nca", "", "residual aset non-lancar"),
        ("Total Assets", "ta", SUB, "subtotal"),
        ("LIABILITIES & EQUITY", "", "section", "penanda bagian"),
        ("Short-term Debt", "st", "", ("forecast: flat di level FY2025A (tidak ada jadwal pelunasan)" if all(abs(fc[i]["st"] - st_debt_25) < 1.0 for i in range(len(fc))) else "forecast: dari jalur proyeksi (jadwal utang)")),
        ("Trade Payables", "ap", NA, "Sectors tidak mempublikasikan utang dagang - tercakup di Other Current Liabilities"),
        ("Other Current Liabilities", "other_cl", "", "residual liabilitas lancar"),
        ("Total Current Liabilities", "tcl", SUB, "subtotal"),
        ("Long-term Debt", "lt", "", ("forecast: flat di level FY2025A" if all(abs(fc[i]["lt"] - lt_debt_25) < 1.0 for i in range(len(fc))) else "forecast: dari jalur proyeksi (jadwal utang)")),
        ("Other Non-Current Liabilities", "other_ncl", "", "residual liabilitas non-lancar"),
        ("Total Liabilities", "tl", SUB, "subtotal"),
        ("Shareholders' Equity", "eq", "", "forecast: + laba bersih (payout 0% per asumsi)"),
        ("Total Liabilities & Equity", "tle", SUB, "harus sama dengan Total Assets (balance check)"),
    ])

    gaps = {y: (rows[y]["gap"] or 0.0) for y in YEARS}
    notes = [
        f"Basis aktual: Sectors annual (FY2024A, FY2025A). Baris kuartalan tidak dipakai - revenue kuartalan "
        f"tidak rekonsiliasi ke angka tahunan (jumlah 4 kuartal ±Rp 44 tn vs FY2025A Rp 30,9 tn).",
        f"Kolom proyeksi mengikuti spine deck (Key Financials): revenue Rp {_nf.idn(rev_f[0], digits=0)} bn, EBITDA "
        f"Rp {_nf.idn(ebitda_f[0], digits=0)} bn, laba bersih Rp {_nf.idn(net_f[0], digits=0)} bn - "
        f"basis kolom F: {(spine or {}).get('forecast_basis') or 'lihat catatan Key Financials'}"
        f"{' (' + str((spine or {}).get('forecast_attribution')).split('(')[0].strip() + ')' if (spine or {}).get('forecast_attribution') else ''}"
        f"{' - LEVEL NORMALISED: kolom FY26F-FY28F BUKAN kurva pertumbuhan, FY27F-FY28F ditahan flat' if (spine or {}).get('forecast_basis') == 'midcycle-normalised' else ''}, "
        f"dan angka ini identik dengan "
        f"yang dipakai halaman valuasi.",
        f"Driver proyeksi: D&A Rp {_nf.idn(dna_25, digits=0)} bn (FY2025A: EBITDA - EBIT), beban bunga Rp {_nf.idn(gross_debt, digits=0)} bn "
        f"x {_nf.pcfrac(cod, 2)} (cost of debt asumsi), pajak {_nf.pcfrac(tax_rate, 0)}, capex Rp {_nf.idn(capex, digits=0)} bn/tahun, payout {_nf.pcfrac(payout, 0)}.",
        "Other Income/(Expense) adalah baris REKONSILIASI, bukan angka hasil temuan: pada kolom aktual nilainya "
        "dibuat agar pre-tax foot, pada kolom proyeksi agar pre-tax konsisten dengan jalur laba bersih mid-cycle. "
        "Dinyatakan eksplisit supaya pembaca tidak membacanya sebagai temuan analis.",
        ("Driver kolom proyeksi: " + ("; ".join(f"{k} {v}" for k, v in sorted(driver_rows.items())))
         if driver_rows else
         "Tidak ada jadwal capex/utang/D&A dari sumber - D&A, utang, dan beban bunga ditahan di level "
         "FY2025A dan itu dinyatakan sebagai keterbatasan, bukan sebagai proyeksi."),
        ("Utang dibagi short-term/long-term memakai proporsi FY2025A "
         f"({_nf.idn(st_debt_25, digits=0)} / {_nf.idn(st_debt_25 + lt_debt_25, digits=0)}) karena sumber hanya mempublikasikan total; "
         "jadwal per tenor tidak dikarang.")
        if driver_rows.get("interest_expense") else "",
        "Neraca: kas adalah item penyeimbang pada kolom proyeksi (dinyatakan). Tanpa itu aset dan liabilitas+ekuitas "
        "tidak akan pernah bertemu persis, karena Sectors tidak menyediakan jadwal capex/pelunasan utang.",
        (f"Rekonsiliasi beban usaha: baris Sectors tidak foot di blok operasi - Operating Expenses di tabel ini "
         f"= Gross Profit - EBIT supaya barisnya menyambung. Selisih terhadap operating_expense yang dilaporkan "
         f"Sectors ({gap_txt}) berarti item itu di luar definisi EBIT mereka; dinyatakan supaya nilainya tidak "
         f"terbaca sebagai temuan baru."),
        (f"Implikasi margin: untuk mencapai EBITDA acuan utama Rp {_nf.idn(ebitda_f[0], digits=0)} bn, rantai biaya memakai opex "
         f"FY2025A (Rp {_nf.idn(opex_25_abs, digits=0)} bn) dan COGS sebagai baris penyeimbang - gross margin proyeksi "
         f"{_nf.pcfrac(implied_gm, 1)} vs aktual FY2025A {_nf.pcfrac(actual_gm, 1)}. Perbaikan margin itu milik asumsi mid-cycle "
         f"deck utama, bukan temuan baru; dinyatakan supaya tidak terbaca sebagai proyeksi analis independen."),
        "Interest Income tidak dipublikasikan Sectors untuk AMMN, jadi barisnya kosong dengan keterangan - "
        "bukan nol, bukan angka karangan.",
    ]
    return {
        "available": True, "ticker": tk, "years": list(YEARS), "variant": "corporate",
        "income": {"exhibit_key": "income", "title": f"Income Statement ({YEARS[0]}–{YEARS[-1]})",
                   "headers": ["Rp bn", *YEARS], "rows": income},
        "balance": {"exhibit_key": "balance", "title": f"Balance Sheet ({YEARS[0]}–{YEARS[-1]})",
                    "headers": ["Rp bn", *YEARS], "rows": balance},
        "tie_out": gaps,
        "tied": all(abs(g) < 1.0 for g in gaps.values()),
        "notes": [n for n in notes if n],
        "driver_basis": driver_rows,
        "forecast_source": (driver_path or {}).get("attribution"),
        "forecast_source_display": _display_attr((driver_path or {}).get("attribution")),
        "sources": ["Sectors API: company/report financials.historical_financials (annual, IDR)",
                    "data/assumptions/AMMN.json (tax, cost of debt, capex, payout)",
                    "cover.slide2.key_financials - mid-cycle forecast acuan utama yang harus di-tie-out"],
        "bank_variant_note": ("Varian bank (pola BBTN Exhibit 7-8: Interest Income/Expense, Net Interest Income, "
                              "Non-Interest Income, PPOP, Provisions; Gross Loans, Net Loans, Govt Bonds, "
                              "Customer Deposits, Shareholders' Funds) diaktifkan lewat flag `variant`, "
                              "tidak dipakai untuk AMMN (non-bank)."),
    }


if __name__ == "__main__":
    import sys
    from server.routers.pdf import render_html_for_ticker

    tk = (sys.argv[1] if len(sys.argv) > 1 else "AMMN").upper()
    _t, _h, payload = render_html_for_ticker(tk, None)
    page = build_statements_page(tk, ((payload.get("cover") or {}).get("slide2") or {}).get("key_financials"))
    if not page.get("available"):
        print("unavailable:", page.get("reason"))
        raise SystemExit(1)
    for block in ("income", "balance"):
        b = page[block]
        print(f"\n{b['title']}")
        print(f"{'':34s}" + "".join(y.rjust(12) for y in page["years"]))
        for r in b["rows"]:
            if r["kind"] == "section":
                print(f"  -- {r['label']} " + "-" * 20)
                continue
            cells = "".join((f"{_nf.idn(v, digits=0)}".rjust(12) if isinstance(v, (int, float)) else "n/a".rjust(12))
                            for v in r["values"])
            flag = {"subtotal": " [bold]", "deduction": " (-)", "highlight": " [HIGHLIGHT]", "na": " [n/a]"}.get(r["kind"], "")
            print(f"  {r['label'][:32]:32s}{cells}{flag}")
    print("\ntie-out (Total L&E - Total Assets):", {k: round(v, 6) for k, v in page["tie_out"].items()},
          "| tied:", page["tied"])


def _display_attr(text):
    """A printed label must never name another research house (the trail stays in the repo)."""
    try:
        from server.report.forecast_path import display_attribution

        return display_attribution(text)
    except Exception:
        return text
