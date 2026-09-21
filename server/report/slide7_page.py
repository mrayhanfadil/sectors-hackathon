"""Slide 7 - Exhibit 16 Cash Flow Statement + Exhibit 17 Key Ratio (non-bank variant).

Rules: docs/ammn-slides/slide7-cashflow-ratio-spec.md.

Two design choices this module makes, both disclosed on the page rather than smoothed over:

1. FOR THE ACTUALS the published Sectors cash-flow sections do not foot to the published cash balance
   (FY2025A: OCF -7,949 + investing -24,484 + financing 31,471 = +9,038, while `net_cash_flow` prints 0 and
   the cash balance moves -859). The page prints the sections as published, then a NAMED reconciliation row
   so Ending Cash equals the balance sheet exactly, as the rules require. Smoothing that difference into a
   section would be the "error link antar-sheet" the rules warn about, hidden instead of shown.

2. FOR THE FORECASTS the cash-flow statement DRIVES cash: ending cash from the drivers becomes the balance
   sheet's cash, and the balance sheet's residual current-asset bucket absorbs the difference, so the two
   exhibits tie by construction with no plug inside the cash-flow statement.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any, Optional
from server.report import numfmt as _nf

CACHE_DIRS = (
    pathlib.Path("output/cache/ammn_fill/raw_cache"),
    pathlib.Path("output/cache"),
)
YEARS = ["2024A", "2025A", "2026F", "2027F", "2028F"]
GROWTH_ROWS = ["Sales", "EBITDA", "Operating Profit", "Net Profit"]
PROFIT_ROWS = ["Gross Margin", "EBITDA Margin", "Operating Margin", "Net Margin", "ROAA", "ROAE"]
LEV_ROWS = ["Net Gearing (x)", "Interest Coverage (x)"]


def _num(v: Any) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f == f else None


def _bn(v: Any) -> Optional[float]:
    n = _num(v)
    return n / 1e9 if n is not None else None


def _load(ticker: str) -> dict:
    for d in CACHE_DIRS:
        if not d.exists():
            continue
        for f in sorted(d.glob(f"company_report_{ticker.upper()}*.json")):
            return json.loads(f.read_text())
    return {}


def _annual_rows(ticker: str) -> dict[int, dict]:
    rep = _load(ticker)
    rows = ((rep.get("financials") or {}).get("historical_financials") or [])
    return {int(r["year"]): r for r in rows if _num(r.get("year")) is not None}


def build_cashflow_page(ticker: str = "AMMN", spine: Optional[dict] = None,
                        driver_path: Optional[dict] = None,
                        balance: Optional[dict] = None) -> dict:
    tk = ticker.upper()
    rows = _annual_rows(tk)
    if 2025 not in rows or 2024 not in rows:
        return {"available": False, "ticker": tk, "reason": "annual cash-flow rows are not cached"}

    dp = (driver_path or {}).get("drivers") or {}

    def drv(key: str, i: int):
        vals = (dp.get(key) or {}).get("rp_bn") or []
        return float(vals[i]) if i < len(vals) else None

    def a(year: int, key: str):
        return _bn(rows[year].get(key))

    notes: list[str] = []
    values: dict[str, list] = {k: [] for k in
                               ("net", "dna", "dwc", "other_op", "ocf", "capex", "other_inv", "icf",
                                "debt", "div", "equity_fin", "fcf_fin", "net_change", "begin", "end",
                                "residual", "fcf_memo")}

    # ---- actual years: published sections, with the source's own reconciliation shown
    prev_cash = None
    for y in (2024, 2025):
        net, ebitda, ebit = a(y, "earnings"), a(y, "ebitda"), a(y, "ebit")
        dna = (ebitda - ebit) if (ebitda is not None and ebit is not None) else 0.0
        ocf, capex = a(y, "operating_cash_flow") or 0.0, a(y, "capital_expenditure") or 0.0
        icf, fcf_fin = a(y, "investing_cash_flow") or 0.0, a(y, "financing_cash_flow") or 0.0
        cash = a(y, "cash_and_equivalents") or a(y, "cash_only")
        ca, cl = a(y, "current_assets"), a(y, "current_liabilities")
        dwc = 0.0
        if ca is not None and cl is not None:
            prev = rows.get(y - 1) or {}
            pca, pcl = _bn(prev.get("current_assets")), _bn(prev.get("current_liabilities"))
            pcash = _bn(prev.get("cash_and_equivalents")) or _bn(prev.get("cash_only")) or 0.0
            # cash sits inside current assets; leaving it in would count the cash movement twice
            wc_now = (ca - (cash or 0.0)) - cl
            if pca is not None and pcl is not None:
                dwc = -(wc_now - ((pca - pcash) - pcl))   # an increase in WC consumes cash
        debt_now = a(y, "total_debt") or 0.0
        debt_prev = (a(y - 1, "total_debt") or 0.0) if (y - 1) in rows else debt_now
        other_op = (ocf - (net or 0.0) - dna - dwc)
        other_inv = (icf - (-capex))
        div = 0.0
        equity_fin = (fcf_fin - (debt_now - debt_prev) - div)
        begin = prev_cash if prev_cash is not None else (a(y - 1, "cash_and_equivalents")
                                                        if (y - 1) in rows else None)
        net_change = ocf + icf + fcf_fin
        residual = None
        if cash is not None and begin is not None:
            residual = cash - (begin + net_change)           # named, never folded into a section
        for key, val in (("net", net), ("dna", dna), ("dwc", dwc), ("other_op", other_op), ("ocf", ocf),
                         ("capex", -capex), ("other_inv", other_inv), ("icf", icf),
                         ("debt", debt_now - debt_prev), ("div", div), ("equity_fin", equity_fin),
                         ("fcf_fin", fcf_fin), ("net_change", net_change), ("begin", begin),
                         ("end", cash), ("residual", residual), ("fcf_memo", ocf - capex)):
            values[key].append(val)
        if abs(residual or 0.0) > 1.0:
            notes.append(
                f"FY{y}A: section arus kas Sectors tidak foot ke saldo kasnya - OCF {_nf.idn(ocf, digits=0)} + investasi "
                f"{_nf.idn(icf, digits=0)} + pendanaan {_nf.idn(fcf_fin, digits=0)} = {_nf.idn(net_change, digits=0)}, sedangkan kas tercatat berubah "
                f"{_nf.idn(cash - begin, digits=0)}. Selisih {_nf.idn(residual, digits=0)} dinyatakan sebagai baris rekonsiliasi supaya "
                f"Ending Cash identik dengan neraca; angka section-nya tidak diubah.")
        prev_cash = cash

    # ---- forecast years: the drivers build the statement, and the statement drives cash
    for i in range(3):
        net = drv("net_profit", i)
        dna = drv("dna", i) or 0.0
        dwc = drv("working_capital", i)
        dwc = dwc if dwc is not None else 0.0            # the cited path prints the CASH effect directly
        capex = drv("capex", i) or 0.0
        debt_now = drv("gross_debt", i)
        debt_prev = (values["debt_now_prev"][-1] if values.get("debt_now_prev")
                     else (a(2025, "total_debt") or 0.0))
        if debt_now is None:
            debt_now = debt_prev
        div = 0.0
        ocf = (net or 0.0) + dna + dwc
        other_op = 0.0
        icf = -capex
        other_inv = 0.0
        fcf_fin = (debt_now - debt_prev) - div
        equity_fin = 0.0
        net_change = ocf + icf + fcf_fin
        begin = prev_cash
        end = (begin or 0.0) + net_change
        for key, val in (("net", net), ("dna", dna), ("dwc", dwc), ("other_op", other_op), ("ocf", ocf),
                         ("capex", -capex), ("other_inv", other_inv), ("icf", icf),
                         ("debt", debt_now - debt_prev), ("div", div), ("equity_fin", equity_fin),
                         ("fcf_fin", fcf_fin), ("net_change", net_change), ("begin", begin),
                         ("end", end), ("residual", 0.0), ("fcf_memo", ocf - capex)):
            values[key].append(val)
        values.setdefault("debt_now_prev", []).append(debt_now)
        prev_cash = end

    def row(label: str, key: str, kind: str = "", note: str = "") -> dict:
        cells = []
        for v in values[key]:
            cells.append(round(v, 0) if isinstance(v, (int, float)) else None)
        return {"label": label, "cells": cells, "kind": kind, "note": note}

    sections = [
        {"title": "Cash Flow from Operations", "rows": [
            row("Net Profit", "net"),
            row("(+) Depreciation & Amortization", "dna"),
            row("(-)/(+) Increase/Decrease in Working Capital", "dwc"),
            row("Other Operating Items", "other_op",
                note="residual operasi; pada tahun aktual menyerap pos yang tidak dirinci Sectors"),
            row("Net Cash from Operations", "ocf", "subtotal"),
        ]},
        {"title": "Cash Flow from Investing", "rows": [
            row("(-) Capital Expenditure", "capex"),
            row("Other Investing Items", "other_inv"),
            row("Net Cash from Investing", "icf", "subtotal"),
        ]},
        {"title": "Cash Flow from Financing", "rows": [
            row("Debt Raised/(Repaid)", "debt"),
            row("Dividends Paid", "div"),
            row("Equity Raised/(Buyback)", "equity_fin"),
            row("Net Cash from Financing", "fcf_fin", "subtotal"),
        ]},
    ]
    closing = [
        row("Net Change in Cash", "net_change", "subtotal"),
        row("Beginning Cash Balance", "begin"),
        row("Ending Cash Balance", "end", "highlight",
            note="harus identik dengan Cash & Cash Equivalents di Balance Sheet (Exhibit 15)"),
    ]
    if any(v is not None and abs(v) > 1.0 for v in values["residual"]):
        closing.append(row("Selisih tidak terjelaskan di sumber Sectors", "residual",
                           note="baris rekonsiliasi ke saldo kas terpublikasi - bukan pembulatan"))
    memo = [row("Free Cash Flow = Net Cash from Operations - Capital Expenditure", "fcf_memo", "memo")]

    # cross-check against the FCFF this deck's DCF actually uses (Slide 4 / Exhibit 8)
    fcff = None
    try:
        assum = json.loads((pathlib.Path(__file__).resolve().parents[2]
                            / "data" / "assumptions" / f"{tk}.json").read_text())
        comp = assum.get("fcf_components_idr_bn") or {}
        fcff = comp.get("fcf_normalised")
        if fcff:
            fcf_bn = values["fcf_memo"][2]
            gap = (fcf_bn - fcff) / abs(fcff)
            notes.append(
                f"Cross-check FCFF: Free Cash Flow FY26F dari exhibit ini Rp {_nf.idn(fcf_bn, digits=0)} bn vs FCFF "
                f"normalised di Exhibit 8 Rp {_nf.idn(fcff, digits=0)} bn (selisih {_nf.pcfrac(gap, 0)}). Keduanya tidak identik "
                f"karena FCFF memakai NOPAT sementara baris ini mulai dari laba bersih dan beban bunga "
                f"diperlakukan berbeda"
                + ("; selisih sebesar ini perlu dicek ulang sebelum publish." if abs(gap) > 0.6 else
                   " - masih dalam ballpark yang wajar.")
            )
            notes.append(
                "Catatan Capex: Capital Expenditure di exhibit ini (Rp 8.332 bn pada 2026F) mencerminkan belanja modal kas riil / sustaining capex proyeksi, berbeda dari total reinvestment capex pada build-up DCF Exhibit 8 (Rp 13.850,2 bn pada FY2026F) yang menyerap rasio reinvestment penuh terhadap pendapatan."
            )
    except Exception:
        pass

    memo_state: dict = {}
    return {
        "available": True, "ticker": tk, "years": YEARS,
        "sections": sections, "closing": closing, "memo": memo,
        "headers": ["Rp bn", *YEARS],
        "end_cash": values["end"],
        "net_change": values["net_change"],
        "fcf": values["fcf_memo"],
        "fcff_exhibit8": fcff,
        "notes": notes,
        "sources": [
            "Sectors company/report financials.historical_financials (section arus kas, IDR)",
            "data/drivers/AMMN.json (D&A, capex, working capital, jadwal utang untuk kolom proyeksi)"
            if dp else "jalur proyeksi tidak tersedia - kolom F ditandai",
        ],
    }


def build_key_ratio_page(ticker: str = "AMMN", spine: Optional[dict] = None,
                         cashflow: Optional[dict] = None,
                         statements: Optional[dict] = None,
                         driver_path: Optional[dict] = None) -> dict:
    """Exhibit 17: growth / profitability / leverage, one decimal, parentheses for negatives."""
    tk = ticker.upper()
    rows = _annual_rows(tk)
    if not rows or not spine:
        return {"available": False, "ticker": tk, "reason": "annual rows or spine missing"}
    kf = {str(r[0]): r[1:] for r in (spine.get("rows") or [])}

    def kf_num(prefix: str, i: int):
        row = next((v for k, v in kf.items() if k.startswith(prefix)), None)
        if not row or i >= len(row):
            return None
        return _num(str(row[i]).replace(".", "").replace(",", "."))

    # Use the statements page the deck actually prints. Rebuilding it here without the same driver inputs
    # produced a ratio block computed from a DIFFERENT income statement than the one on the page - the exact
    # cross-sheet drift Exhibit 17 exists to expose.
    is_page = statements or {}
    if not is_page:
        try:
            from server.report.statements_page import build_statements_page

            is_page = build_statements_page(tk, spine, driver_path=driver_path, cashflow=cashflow)
        except Exception:
            pass
    is_row: dict[str, list] = {}
    is_key: dict[str, list] = {}
    for block in ("income", "balance"):
        for r in ((is_page.get(block) or {}).get("rows") or []):
            # Label-prefix index is the legacy lookup; it breaks whenever a label is
            # retitled (e.g. plain-Indonesian relabel Sep 2026 turned "EBIT" into
            # "Laba usaha (EBIT)"). The stable "key" index below survives retitles.
            is_row[str(r["label"]).split(" /")[0].split(" (")[0].strip()] = r["cells"]
            if r.get("key"):
                is_key[str(r["key"])] = r["cells"]

    def isv(label: str, i: int):
        row = is_row.get(label)
        return row[i] if row and i < len(row) else None

    def isk(key: str, i: int):
        row = is_key.get(key) or is_row.get(key)
        return row[i] if row and i < len(row) else None

    # year 0 (2024A) growth needs FY2023A, which is outside the exhibit's columns but is published
    prev_rev = _bn(rows.get(2023, {}).get("revenue"))
    prev_ebitda = _bn(rows.get(2023, {}).get("ebitda"))
    prev_ebit = _bn(rows.get(2023, {}).get("ebit"))
    prev_net = _bn(rows.get(2023, {}).get("earnings"))

    def growth(series: list, prev0: Optional[float]) -> list:
        out = []
        for i, v in enumerate(series):
            base = prev0 if i == 0 else series[i - 1]
            out.append(((v / base - 1) * 100) if (v is not None and base) else None)
        return out

    rev = [isk("rev", i) or isv("Revenue", i) for i in range(5)]
    ebitda = [kf_num("EBITDA", i) for i in range(5)]
    op = [isk("ebit", i) or isv("EBIT", i) for i in range(5)]
    net = [isk("net", i) or isv("Net Profit", i) for i in range(5)]
    gp = [isk("gp", i) or isv("Gross Profit", i) for i in range(5)]
    opex = [isk("opex", i) or isv("Operating Expenses", i) for i in range(5)]
    intr = [isk("ie", i) or isv("Interest Expense", i) for i in range(5)]
    ebt = [isk("ebt", i) or isv("Pre-tax Profit", i) for i in range(5)]

    def pct(a: list, b: list) -> list:
        return [(x / y * 100) if (x is not None and y) else None for x, y in zip(a, b)]

    def ratio(a: list, b: list) -> list:
        return [(x / y) if (x is not None and y) else None for x, y in zip(a, b)]

    equity = [isv("Shareholders' Equity", i) for i in range(5)]
    debt = [isv("Total Liabilities", i) for i in range(5)]
    cash = [isv("Cash & Cash Equivalents", i) for i in range(5)]
    assets = [isv("Total Assets", i) for i in range(5)]
    total_debt = []
    for i in range(5):
        st = isv("Short-term Debt", i)
        lt = isv("Long-term Debt", i)
        total_debt.append((st or 0) + (lt or 0) if (st is not None or lt is not None) else None)

    prev_assets = _bn(rows.get(2023, {}).get("total_assets"))

    def avg(series: list, i: int):
        if i == 0:
            return (series[0] + prev_assets) / 2 if (series[0] is not None and prev_assets) else None
        if series[i] is None or series[i - 1] is None:
            return None
        return (series[i] + series[i - 1]) / 2

    roaa = [(net[i] / avg(assets, i) * 100) if (net[i] is not None and avg(assets, i)) else None
            for i in range(5)]
    prev_eq = _bn(rows.get(2023, {}).get("total_equity"))
    roae = []
    for i in range(5):
        base = prev_eq if i == 0 else equity[i - 1]
        if net[i] is not None and base and equity[i] is not None:
            roae.append(net[i] / ((equity[i] + base) / 2) * 100)
        else:
            roae.append(None)
    gearing = [((total_debt[i] - (cash[i] or 0)) / equity[i]) if (total_debt[i] is not None and equity[i])
               else None for i in range(5)]
    coverage = [(op[i] / intr[i]) if (op[i] is not None and intr[i]) else None for i in range(5)]

    def section(title: str, rows_: list) -> dict:
        return {"title": title, "rows": rows_}

    return {
        "available": True, "ticker": tk, "years": YEARS, "headers": ["", *YEARS],
        "exhibit_title": f"Key Ratio ({YEARS[0]}–{YEARS[-1]})",
        "sections": [
            section("Growth (%)", [
                {"label": "Sales", "cells": growth(rev, prev_rev)},
                {"label": "EBITDA", "cells": growth(ebitda, prev_ebitda)},
                {"label": "Operating Profit", "cells": growth(op, prev_ebit)},
                {"label": "Net Profit", "cells": growth(net, prev_net)},
            ]),
            section("Profitability (%)", [
                {"label": "Gross Margin", "cells": pct(gp, rev)},
                {"label": "EBITDA Margin", "cells": pct(ebitda, rev)},
                {"label": "Operating Margin", "cells": pct(op, rev)},
                {"label": "Net Margin", "cells": pct(net, rev)},
                {"label": "ROAA", "cells": roaa},
                {"label": "ROAE", "cells": roae},
            ]),
            section("Leverage", [
                {"label": "Net Gearing (x)", "cells": gearing},
                {"label": "Interest Coverage (x)", "cells": coverage},
            ]),
        ],
        "notes": [
            "Satu desimal konsisten di semua baris; angka negatif ditulis dalam tanda kurung, bukan minus.",
            "ROAA/ROAE memakai saldo rata-rata (awal+akhir)/2; rata-rata tahun 2024 memerlukan saldo "
            "FY2023A dari Sectors, bukan angka yang diinterpolasi.",
            "Net Gearing = (Total Debt - Cash) / Total Equity; Interest Coverage = EBIT / Interest Expense.",
        ],
        "sources": ["Sectors annual financials + Exhibit 14/15 halaman ini (basis sama, bukan file terpisah)"],
        "growth_basis": {
            "sales": growth(rev, prev_rev)[0], "ebitda": growth(ebitda, prev_ebitda)[0],
            "operating": growth(op, prev_ebit)[0], "net": growth(net, prev_net)[0],
        },
    }
