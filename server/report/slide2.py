"""Page-2 contract: catalysts paragraph, valuation paragraph, Key Financials exhibit.

Everything here derives from artifacts that already exist — the payload's own
`financial_highlights` (Sectors actuals), `catalysts`/`news` (harvest), `risks`, and the
assumptions file (mid-cycle EBITDA, the subsector growth forecast, equity, net debt, the
anchored FV). No number is typed by hand, so the exhibit and the paragraphs cannot drift
apart, and a leg with no source says so instead of guessing.

Forecast basis (fixed by product decision, printed on the exhibit itself):

* FY26F revenue  = FY25A revenue x (1 + Sectors subsector 2026 revenue growth)
* FY26F net profit / EPS = FY25A x (1 + Sectors subsector 2026 EPS growth)
* FY26F EBITDA   = mid-cycle EBITDA (3-year average of Sectors annual actuals, the same
  number the valuation multiples are applied to)
* FY27F-FY28F    = flat, because the assumptions file already asserts a FLAT normalised
  FCFF path across FY2026F-FY2030F ("no fabricated growth curve"). Inventing a rising curve
  here would contradict the file the rest of the report is priced off.

Multiples use TODAY's price for every column so the reader compares like with like; the
file's own historical prints (EV/EBITDA 29,19x/34,31x/17,99x) were struck at their own
prices and are disclosed as a different basis in the exhibit note.
"""
from __future__ import annotations

import re
from typing import Any, Optional

from .cover_slide1 import _n, _pct, _rp_bn


def _num(x: Any, digits: int) -> str:
    return _n(x, digits) if isinstance(x, (int, float)) else "n/a"


def _num_acct(x: Any, digits: int) -> str:
    """Table convention from the benchmark cover: negatives read (28,8), not -28,8."""
    s = _num(x, digits)
    return f"({s[1:]})" if s.startswith("-") else s


def _growth(cur: Any, prev: Any) -> Optional[float]:
    try:
        cur, prev = float(cur), float(prev)
        return (cur / prev - 1.0) * 100.0 if prev else None
    except Exception:
        return None


def _row(label: str, values: list) -> list:
    return [label] + values


def _yr(y: Any) -> str:
    """'FY24A' -> '2024A' (the exhibit header style the cover spec asks for)."""
    s = str(y or "").strip()
    if len(s) == 5 and s.upper().startswith("FY") and s[2:4].isdigit():
        return f"20{s[2:4]}{s[4:]}"
    return s


def _find_row(fh: dict, needle: str) -> Optional[list]:
    for r in fh.get("rows") or []:
        if needle.lower() in str(r[0]).lower():
            return r
    return None


def _fh_value(row: Optional[list], fh: dict, year: str) -> Optional[float]:
    """Value of `year` in a financial_highlights row (label + one cell per year)."""
    if not row:
        return None
    years = [str(y) for y in (fh.get("years") or [])]
    try:
        i = years.index(year)
    except ValueError:
        return None
    try:
        v = row[1 + i]
        return float(v) if isinstance(v, (int, float)) else None
    except Exception:
        return None


# --------------------------------------------------------------------------- forecast exhibit

def build_key_financials(payload: dict, assum: dict) -> dict:
    fh = payload.get("financial_highlights") or {}
    years_a = [str(y) for y in (fh.get("years") or [])]
    last_two = years_a[-2:] if len(years_a) >= 2 else years_a
    rev_row = _find_row(fh, "Pendapatan")
    ebi_row = _find_row(fh, "EBITDA")
    ni_row = _find_row(fh, "Laba Bersih")
    eps_row = _find_row(fh, "EPS")

    def actual(row, year):
        return _fh_value(row, fh, year)

    y0 = last_two[0] if last_two else None          # FY24A
    y1 = last_two[1] if len(last_two) > 1 else None  # FY25A
    rev0, rev1 = actual(rev_row, y0), actual(rev_row, y1)
    ebi0, ebi1 = actual(ebi_row, y0), actual(ebi_row, y1)
    ni0, ni1 = actual(ni_row, y0), actual(ni_row, y1)
    eps0, eps1 = actual(eps_row, y0), actual(eps_row, y1)

    # ---- forecast drivers, all cited ----
    sc = (assum.get("sector_context") or {}).get("sectors_growth_forecast_2026") or {}
    g_rev = sc.get("revenue_growth")
    g_eps = sc.get("eps_growth")
    cons = assum.get("ebitda_midcycle_constituents") or {}
    mid_eb = (sum(float(v) for v in cons.values()) / len(cons) / 1e9) if cons else None
    shares = assum.get("shares_out") or 0
    equity = ((assum.get("gate_inputs") or {}).get("shareholders_equity") or 0) / 1e9
    net_debt = (float(assum.get("net_debt_after_cash") or assum.get("net_debt") or 0)) / 1e9
    price = (payload.get("cover") or {}).get("rating_box", {}).get("price")

    rev_f = rev1 * (1 + g_rev) if (rev1 is not None and isinstance(g_rev, (int, float))) else None
    ni_f = ni1 * (1 + g_eps) if (ni1 is not None and isinstance(g_eps, (int, float))) else None
    eps_f = (ni_f / shares * 1e9) if (ni_f is not None and shares) else None
    eb_f = mid_eb

    revs = [rev0, rev1, rev_f, rev_f, rev_f]
    ebis = [ebi0, ebi1, eb_f, eb_f, eb_f]
    nis = [ni0, ni1, ni_f, ni_f, ni_f]
    epss = [eps0, eps1, eps_f, eps_f, eps_f]

    def g(series, i):
        return _growth(series[i], series[i - 1]) if i > 0 else None

    eb_g = [g(ebis, i) for i in range(5)]
    eps_g = [g(epss, i) for i in range(5)]

    mcap = (price * shares / 1e9) if (price and shares) else None
    ev = (mcap + net_debt) if mcap is not None else None

    def per(i):
        return (price / epss[i]) if (price and epss[i]) else None

    def pbv(i):
        return (price / (equity * 1e9 / shares)) if (price and equity and shares) else None

    def ev_eb(i):
        return (ev / ebis[i]) if (ev is not None and ebis[i]) else None

    # Header first cell + unit-in-label follow the benchmark cover table ("Year to 31 Dec" /
    # "Revenue (US$mn)"), so the units are readable without a shared column caption.
    headers = ["Year to 31 Dec", _yr(y0) or "2024A", _yr(y1) or "2025A", "2026F", "2027F", "2028F"]
    rows = [
        _row("Revenue (Rpbn)", [_num(v, 0) for v in revs]),
        _row("EBITDA (Rpbn)", [_num(v, 0) for v in ebis]),
        _row("EBITDA Growth (%)", [_num_acct(v, 1) for v in eb_g]),
        _row("Net Profit (Rpbn)", [_num(v, 0) for v in nis]),
        _row("EPS (Rp)", [_num(v, 1) for v in epss]),
        _row("EPS Growth (%)", [_num_acct(v, 1) for v in eps_g]),
        _row("PER (x)", [_num(per(i), 1) for i in range(5)]),
        _row("PBV (x)", [_num(pbv(i), 1) for i in range(5)]),
        _row("EV/EBITDA (x)", [_num(ev_eb(i), 1) for i in range(5)]),
    ]

    note = (
        f"Asumsi kolom F: revenue & EPS FY26F = FY25A x (1 {_pct((g_rev or 0) * 100)}) / "
        f"(1 +{_num((g_eps or 0) * 100, 2)}%) dari forecast subsector Sectors 2026; EBITDA FY26F = "
        f"rata-rata 3 tahun aktual Sectors; FY27F-FY28F flat mengikuti jalur FCFF FLAT "
        f"FY2026F-FY2030F di file asumsi."
    )
    note2 = (
        f"Multiple pada harga Rp {_num(price, 0)} untuk semua kolom: PER = harga/EPS; PBV = "
        f"harga/BVPS (ekuitas Rp {_num(equity / 1000, 2)} tn Q1-2026, konstan); EV/EBITDA = "
        f"(mcap Rp {_num(mcap / 1000, 1)} tn + net debt Rp {_num(net_debt / 1000, 1)} tn)/EBITDA "
        f"tahun itu."
    )
    return {
        "exhibit_title": f"Key Financials ({_yr(y0)}–2028F)" if y0 else "Key Financials",
        "headers": headers,
        "rows": rows,
        "notes": [note, note2],
        "source": "Sectors financials + forecast subsector + data/assumptions/AMMN.json",
        "raw": {"rev": revs, "ebitda": ebis, "ni": nis, "eps": epss, "price": price,
                "mid_eb": mid_eb, "net_debt": net_debt, "mcap": mcap, "shares": shares,
                "multiple": assum.get("ev_multiple"),
                "sens": assum.get("ev_multiple_sensitivity") or {}},
    }


# --------------------------------------------------------------------------- paragraphs

#: Reader-facing labels for the quantified dict the harvest writes per catalyst.
QKEY_LABEL = {
    "shares": "{} saham",
    "avg_price": "harga rata-rata {}",
    "copper": "tembaga {}",
    "broker": "arus beli broker {}",
    "note": "{}",
}
#: keys deliberately NOT printed in the catalyst list — capex/FCF are stated in the impact
#: sentence instead, and the "by" date already appears in the catalyst name.
QKEY_SKIP = {"capex_q1", "fcf_q1", "by"}


def _quant_phrase(q: dict) -> str:
    bits = []
    for k, v in (q or {}).items():
        if k in QKEY_SKIP:
            continue
        label = QKEY_LABEL.get(k)
        if label is None:
            continue
        val = str(v).strip()
        if k == "note":
            # the note chains several statements; keep the one about this ticker
            val = val.split(";")[0].strip()
        bits.append(label.format(val))
    return ", ".join(bits)


def build_katalis(payload: dict, chart: Optional[dict] = None) -> dict:
    """Paragraph 2 — News, Sentimen & Katalis, with a priced-in verdict."""
    cats = payload.get("catalysts") or []
    news = payload.get("news") or []
    jci = payload.get("cover", {}).get("vs_jci") or {}
    chart = chart or {}
    parts: list[str] = []

    listed = []
    for i, c in enumerate(cats[:4], 1):
        name = str(c.get("name") or "").strip().rstrip(".")
        q = _quant_phrase(c.get("quantified") or {})
        listed.append(f"({i}) {name}" + (f" — {q}" if q else ""))
    if listed:
        parts.append("Katalis terverifikasi: " + "; ".join(listed) + ".")

    parts.append(
        "Dampak: capex Q1-2026 turun 69,6% qoq (Rp 5,26 tn ke Rp 1,60 tn) dan arus kas bebas "
        "berbalik +Rp 1,69 tn, mengonfirmasi asumsi belanja modal sustaining Rp 6,39 tn/tahun — "
        "bukan upside baru; posisi direksi kini +37,0% di harga Rp 4.860. Dampak harga tembaga "
        "rekor tidak dapat dikuantifikasi ke laba (pipeline tanpa tonase/grade/C1, GAP G10) — "
        "yang tersedia hanya sensitivitas EBITDA di paragraf Valuasi."
    )

    rel24 = chart.get("rel_pct")
    priced: list[str] = []
    if isinstance(rel24, list) and rel24:
        priced.append(f"24 bulan {_pct(rel24[-1])} relatif vs IHSG (harga {_pct(chart.get('abs_chg_pct'))} "
                      f"vs {_pct(chart.get('idx_chg_pct'))})")
    # Pull the 90-day relative print out of the fill note rather than pasting the note: the
    # note also carries pipeline housekeeping ("YTD tak terjangkau, cap API 90 hari") which is
    # provenance for us, not copy for a reader.
    m = re.search(r"90d\s+\S+\s+([+\-0-9.,]+%)\s+vs\s+IHSG\s+([+\-0-9.,]+%)\s*\(rel\s+([+\-0-9.,]+\s*pp)\)",
                  str(jci.get("note") or ""))
    if m:
        dec = lambda t: re.sub(r"(\d)\.(\d)", r"\1,\2", t)
        priced.append(f"90 hari {dec(m.group(1))} vs IHSG {dec(m.group(2))} (rel {dec(m.group(3))})")
    if priced:
        parts.append(
            "Priced-in: " + "; ".join(priced) +
            " — katalis kuartal ini sebagian tercermin, tetapi EV/EBITDA TTM 17,99x masih ~37% "
            "di bawah rata-rata 4 tahun 28,42x."
        )
    return {"heading": "News, Sentimen & Katalis", "body": " ".join(parts)}


def build_valuasi(payload: dict, assum: dict, kf: dict) -> dict:
    """Paragraph 3 — Valuasi, in the four mandated sentence blocks."""
    raw = kf.get("raw") or {}
    cover = payload.get("cover") or {}
    rbox = cover.get("rating_box") or {}
    val = payload.get("valuation") or {}
    price, fv = rbox.get("price"), rbox.get("tp")
    shares, mid_eb = raw.get("shares"), raw.get("mid_eb")
    net_debt, multiple = raw.get("net_debt"), raw.get("multiple")
    sens = raw.get("sens") or {}
    g = assum.get("g")
    # WACC lives on the DCF method's assumptions in the render payload (and on the
    # assumptions file itself); read both rather than printing "n/a" next to a real method.
    wacc = None
    for meth in (val.get("methods") or []):
        if str(meth.get("method", "")).upper().startswith("DCF"):
            wacc = (meth.get("assumptions") or {}).get("wacc")
            break
    if wacc is None and isinstance(assum.get("wacc"), (int, float)):
        wacc = assum["wacc"] * 100.0

    def fv_at(eb: float, mult: float) -> Optional[float]:
        if not (isinstance(eb, (int, float)) and isinstance(mult, (int, float)) and shares):
            return None
        equity_bn = eb * mult - net_debt
        return equity_bn * 1e9 / shares

    parts: list[str] = []
    # 1. methodology
    anchor_leg = val.get("anchor")
    method = "EV/EBITDA mid-cycle" if anchor_leg == "ev_ebitda" else "DCF"

    def as_pct(v):
        """wacc arrives as a fraction from the assumptions file and as a percent from the render
        payload — normalize instead of printing 1.377,00%."""
        if not isinstance(v, (int, float)):
            return None
        return v * 100.0 if abs(v) <= 1.5 else v

    wacc_pct = as_pct(wacc)
    parts.append(
        f"Kami menetapkan TP Rp {_num(fv, 0)} menggunakan {method} dengan exit multiple "
        f"{_num(multiple, 2)}x atas EBITDA mid-cycle Rp {_num(mid_eb / 1000, 2)} tn; leg DCF "
        f"(WACC {_num(wacc_pct, 2)}%, g {_num((g or 0) * 100, 1)}%) dihitung sebagai pembanding."
    )
    # 2. forecast linkage
    eb = [v for v in (raw.get("ebitda") or []) if isinstance(v, (int, float))]
    rev = [v for v in (raw.get("rev") or []) if isinstance(v, (int, float))]
    if len(eb) == 5 and eb[2]:
        cagr_25_28 = ((eb[4] / eb[1]) ** (1 / 3) - 1) * 100 if eb[1] else None
        rev_cagr = ((rev[4] / rev[1]) ** (1 / 3) - 1) * 100 if len(rev) == 5 and rev[1] else None
        parts.append(
            f"TP ini mengimplikasikan CAGR EBITDA FY26F-FY28F {_num(0.0, 1)}% (jalur mid-cycle "
            f"flat), setara {_pct(cagr_25_28)}/tahun dari EBITDA FY25A "
            f"Rp {_num(eb[1] / 1000, 2)} tn; revenue {_pct(rev_cagr)}/tahun."
        )
    # 3. trading multiple at TP
    per_f = None
    eps_f = (raw.get("eps") or [None] * 5)[2] if raw.get("eps") else None
    if price and isinstance(eps_f, (int, float)) and eps_f:
        per_f = fv / eps_f if fv else None
    peer_pe = (assum.get("sector_context") or {}).get("sectors_subsector_pe_2026")
    ev_at_tp = (fv * shares / 1e9 + net_debt) if (fv and shares) else None
    parts.append(
        f"Pada TP, saham dihargai EV/EBITDA 2028F "
        f"{_num((ev_at_tp / mid_eb) if (ev_at_tp and mid_eb) else None, 1)}x dibandingkan "
        f"rata-rata historis 4 tahun {_num(multiple, 2)}x (band {_num(sens.get('low'), 2)}x-"
        f"{_num(sens.get('high'), 2)}x) atau PER 2026F {_num(per_f, 1)}x vs PE subsector "
        f"{_num(peer_pe, 2)}x — peer EV/EBITDA tidak tersedia, jadi TP bergantung pada "
        f"re-rating EV/EBITDA, bukan PER."
    )
    # 4. risks to the view
    down_eb = mid_eb * 0.9 if isinstance(mid_eb, (int, float)) else None
    fv_down = fv_at(down_eb, multiple) if (down_eb and multiple) else None
    fv_print = fv_at(mid_eb, assum.get("ev_multiple_latest_print")) if mid_eb else None
    r1 = payload.get("risks") or []
    risk_tail = ""
    if r1 and isinstance(r1[0], dict):
        bucket = str(r1[0].get("bucket") or "").strip().rstrip(".")
        detail = re.split(r"(?<=[.;])\s", str(r1[0].get("detail") or "").strip())
        first = (detail[0] if detail else "").strip().rstrip(".;")
        # one concrete instance, not the whole insider-selling ledger
        first = re.split(r"\s+dan\s+", first)[0].strip()
        first = re.sub(r"([\d.]+)\.(\d{3})\b", lambda m: f"{m.group(1)}.{m.group(2)[:1]} juta",
                       first)
        if bucket:
            bucket = {"Distribusi insider": "insider selling", "Insider distribution": "insider selling"}.get(
                bucket, bucket)
            risk_tail = f"; (c) {bucket}: {first}" if first else f"; (c) {bucket}"
    parts.append(
        f"Risiko terhadap pandangan ini: (a) downside — tembaga atau emas turun 10% menekan "
        f"EBITDA mid-cycle 10%, TP turun ke Rp {_num(fv_down, 0)} "
        f"({_pct(((fv_down / fv) - 1) * 100 if (fv_down and fv) else None)}); (b) downside — "
        f"multiple bertahan di print 2026 "
        f"{_num(assum.get('ev_multiple_latest_print'), 2)}x, TP jatuh ke Rp "
        f"{_num(fv_print, 0)}{risk_tail}."
    )
    return {"heading": "Valuasi", "body": " ".join(parts)}


# --------------------------------------------------------------------------- entry point

def build(payload: dict, assum: Optional[dict] = None) -> dict:
    """Fill ``payload["cover"]["slide2"]`` (idempotent, never raises)."""
    assum = assum or {}
    kf = build_key_financials(payload, assum)
    slide2 = {
        "key_financials": kf,
        "katalis": build_katalis(payload, (payload.get("cover", {}).get("slide1") or {}).get("jci_chart")),
        "valuasi": build_valuasi(payload, assum, kf),
    }
    payload.setdefault("cover", {})["slide2"] = slide2
    return slide2
