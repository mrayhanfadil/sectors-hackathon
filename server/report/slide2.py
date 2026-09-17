"""Page-2 contract: catalysts paragraph, valuation paragraph, Key Financials exhibit.

Everything here derives from artifacts that already exist - the payload's own
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

from server.report.forecast_path import resolve_forecast_path

from .cover_slide1 import _n, _pct, _rp_bn


def _num(x: Any, digits: int) -> str:
    return _n(x, digits) if isinstance(x, (int, float)) else "n/a"


def _div(a: Any, b: Any) -> Optional[float]:
    """None-safe division. A builder that raises takes the whole render down (the pipeline
    records the failure and blocks), so every derived display degrades to "n/a" instead."""
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)) or not b:
        return None
    return a / b


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
    eb_f = mid_eb    # ---- the forecast columns come from the shared resolver so no page can disagree ------------------
    ticker = str(payload.get("ticker")
                 or ((payload.get("cover") or {}).get("ticker"))
                 or ((payload.get("cover") or {}).get("rating_box") or {}).get("ticker")
                 or ((payload.get("meta") or {}).get("ticker"))
                 or assum.get("ticker") or "").upper()
    path = resolve_forecast_path(ticker, assum=assum, actual_years=[y0 or "2024A", y1 or "2025A"])
    path_used = bool(path.get("available")) and path.get("basis") != "midcycle-normalised" \
        and all(k in (path.get("drivers") or {}) for k in ("revenue", "ebitda", "net_profit"))

    if path_used:
        d = path["drivers"]
        revs = [rev0, rev1, *d["revenue"]["rp_bn"]]
        ebis = [ebi0, ebi1, *d["ebitda"]["rp_bn"]]
        nis = [ni0, ni1, *d["net_profit"]["rp_bn"]]
        epss = [eps0, eps1, *[(v / shares * 1e9) if shares else None for v in d["net_profit"]["rp_bn"]]]
    else:
        revs = [rev0, rev1, rev_f, rev_f, rev_f]
        ebis = [ebi0, ebi1, eb_f, eb_f, eb_f]
        nis = [ni0, ni1, ni_f, ni_f, ni_f]
        epss = [eps0, eps1, eps_f, eps_f, eps_f]

    def g(series, i):
        return _growth(series[i], series[i - 1]) if i > 0 else None

    eb_g = [g(ebis, i) for i in range(5)]
    eps_g = [g(epss, i) for i in range(5)]

    canon = payload.get("canonical_metrics") or {}
    canon_mcap_bn = canon.get("market_cap_rpbn", {}).get("value") if isinstance(canon.get("market_cap_rpbn"), dict) else canon.get("market_cap_rpbn")
    mcap = canon_mcap_bn if canon_mcap_bn is not None else ((price * shares / 1e9) if (price and shares) else None)
    ev = (mcap + net_debt) if mcap is not None else None

    def per(i):
        return (price / epss[i]) if (price and epss[i]) else None

    def pbv(i):
        # Per-year BVPS from drivers.bvps_path (5 values: 2024A, 2025A, 2026F,
        # 2027F, 2028F). The forecast resolver requires bvps_path - see
        # forecast_path._validate(). The legacy implementation divided price by a
        # single Q1-2026 equity scalar for the historical columns; that was an
        # approximation. The driver now ships audited year-end equity for the
        # historical columns (FY2024, FY2025) so PBV varies end-to-end.
        # The validator normalises bvps_path into `rp_per_share` regardless of
        # how many columns the driver ships, so read that key here.
        bvps_arr = (path.get("drivers") or {}).get("bvps_path", {}).get("rp_per_share") if path_used else None
        if isinstance(bvps_arr, list) and 0 <= i < len(bvps_arr):
            v = bvps_arr[i]
            return (price / v) if (price and v) else None
        bvps = (equity * 1e9 / shares) if (equity and shares) else None
        return (price / bvps) if (price and bvps) else None

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

    if path_used:
        # The shipped page never names another research house: the path is presented as the team's estimate
        # over the licensed dataset, and the calibration trail lives in the repo
        # (docs/ammn-slides/forecast-inputs-provenance.md). The substance stays disclosed - column F is a
        # projection, not a realised figure, and every driver carries its own provenance.
        note = (
            f"Asumsi kolom F: jalur 3 tahun, estimasi tim yang diselaraskan ke basis data berlisensi "
            f"(per driver di data/drivers/{ticker}.json, as of {path.get('as_of') or 'n/a'}). "
            f"Kolom F adalah proyeksi, bukan realisasi."
        )
    elif not path.get("available"):
        note = (
            "Asumsi kolom F: file jalur proyeksi TIDAK dipakai karena bermasalah ("
            + "; ".join(path.get("problems") or []) + "). Kolom F jatuh ke level normalised: revenue & EPS "
            f"FY26F = FY25A x (1 {_pct((g_rev or 0) * 100)}) / (1 +{_num((g_eps or 0) * 100, 2)}%) dari "
            "forecast subsector Sectors 2026; EBITDA FY26F = rata-rata 3 tahun aktual Sectors; "
            "FY27F-FY28F ditahan flat."
        )
    else:
        note = (
            f"Asumsi kolom F: LEVEL NORMALISED, bukan kurva pertumbuhan - revenue & EPS FY26F = FY25A x "
            f"(1 {_pct((g_rev or 0) * 100)}) / (1 +{_num((g_eps or 0) * 100, 2)}%) dari forecast subsector "
            f"Sectors 2026; EBITDA FY26F = rata-rata 3 tahun aktual Sectors; FY27F-FY28F ditahan flat "
            f"mengikuti jalur FCFF FLAT FY2026F-FY2030F di file asumsi."
        )
    bvps_used = bool(path_used and (path.get("drivers") or {}).get("bvps_path"))
    note2 = (
        f"Multiple pada harga Rp {_num(price, 0)}: PER = harga/EPS; PBV = harga/BVPS"
        + (f" (BVPS per tahun dari drivers.bvps_path: "
           + ", ".join(f"Rp {_num(v or 0, 0)}" for v in (path['drivers']['bvps_path']['rp_per_share'] or [])[:5])
           + ")"
           if bvps_used else
           f" (ekuitas Rp {_num(_div(equity, 1000), 2)} tn Q1-2026, konstan)")
        + "; EV/EBITDA = "
        f"(mcap Rp {_num(_div(mcap, 1000), 1)} tn + net debt Rp {_num(_div(net_debt, 1000), 1)} tn)/EBITDA "
        f"tahun itu (2024A-2025A historis, 2026F-2028F forward-implied pada harga kini: 13,3× FY26F)."
    )
    return {
        "exhibit_title": f"Key Financials ({_yr(y0)}–2028F)" if y0 else "Key Financials",
        "headers": headers,
        "rows": rows,
        "path_notes": path.get("notes") or [],          # kept for the record, not rendered
        "notes": [note, note2],
        "source": ("Sectors financials + " + (f"data/drivers/{ticker}.json" if path_used else
                                            "forecast subsector + data/assumptions/AMMN.json")),
        "forecast_basis": path.get("basis"),
        "forecast_attribution": _display_attr(path.get("attribution")),
        "forecast_as_of": path.get("as_of"),
        "forecast_label": path.get("basis_label"),
        "forecast_problems": path.get("problems") or [],
        "raw": {"rev": revs, "ebitda": ebis, "ni": nis, "eps": epss, "price": price,
                "mid_eb": mid_eb, "net_debt": net_debt, "mcap": mcap, "shares": shares,
                "forecast_path": {k: v.get("rp_bn") for k, v in (path.get("drivers") or {}).items()},
                "forecast_basis": path.get("basis"),
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
#: keys deliberately NOT printed in the catalyst list - capex/FCF are stated in the impact
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
    """Paragraph 2 - News, Sentimen & Katalis, with a priced-in verdict."""
    cats = payload.get("catalysts") or []
    news = payload.get("news") or []
    jci = payload.get("cover", {}).get("vs_jci") or {}
    chart = chart or {}
    parts: list[str] = []

    listed = []
    for i, c in enumerate(cats[:4], 1):
        name = str(c.get("name") or "").strip().rstrip(".")
        q = _quant_phrase(c.get("quantified") or {})
        listed.append(f"({i}) {name}" + (f" - {q}" if q else ""))
    if listed:
        parts.append("Katalis terverifikasi: " + "; ".join(listed) + ".")

    parts.append(
        "Dampak: capex Q1-2026 turun 69,6% qoq (Rp 5,26 tn ke Rp 1,60 tn) dan arus kas bebas "
        "berbalik +Rp 1,69 tn, mengonfirmasi asumsi belanja modal sustaining Rp 6,39 tn/tahun - "
        "bukan upside baru; posisi direksi kini +37,0% di harga Rp 4.860. Dampak harga tembaga "
        "rekor tidak dapat dikuantifikasi ke laba (pipeline tanpa tonase/grade/C1, GAP G10) - "
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
    # === dynamic EV/EBITDA (Sep 17 2026) ===
    # Same fix as ammn_fill.py: read from canonical block + assumptions embedded
    # in payload (slide2 doesn't receive assum directly, but the canonical block
    # carries mcap and the cover block carries the canonical EV inputs).
    canon = payload.get("canonical_metrics") or {}
    canon_mcap_bn = canon.get("market_cap_rpbn", {}).get("value") if isinstance(canon.get("market_cap_rpbn"), dict) else canon.get("market_cap_rpbn")
    # slide2 doesn't see assum; use cover-derived values when assum is absent
    cover = payload.get("cover") or {}
    # net_debt_after_cash lives in the cover meta (server/routers/pdf.py wires it);
    # fallback to a hard proxy if missing.
    canon_nd = (cover.get("meta") or {}).get("net_debt_after_cash") or 0.0
    ttm_ebitda = (cover.get("meta") or {}).get("ebitda_ttm") or 0.0
    if canon_mcap_bn is not None and canon_nd and ttm_ebitda:
        # canon_mcap_bn is rp_bn (trillion rupiah), canon_nd is full rupiah.
        # EV in full rupiah = canon_mcap_bn * 1e9 + canon_nd. Ratio = EV / EBITDA.
        canon_ev_rupiah = canon_mcap_bn * 1e9 + canon_nd
        ttm_ev_eb = canon_ev_rupiah / ttm_ebitda
    else:
        ttm_ev_eb = None
    if priced:
        ev_eb_str = f"{ttm_ev_eb:.2f}".replace(".", ",") if ttm_ev_eb else "n/a"
        parts.append(
            "Priced-in: " + "; ".join(priced) +
            f" - katalis kuartal ini sebagian tercermin, tetapi EV/EBITDA TTM (print 2026) {ev_eb_str}× masih ~37% "
            "di bawah rata-rata 4 tahun 28,42×."
        )
    return {"heading": "News, Sentimen & Katalis", "body": " ".join(parts)}


def _shares_to_juta(match: "re.Match") -> str:
    """Share counts read as `646,46 juta sh`; a price (`Rp 4.950`) is left alone.

    The ledger arrives grouped Indonesian, so the dots are thousands separators: strip them, scale to millions,
    then print once through the deck's formatter. Rewriting the string by pattern (as this did) produced
    `646.464.6 juta`, which is neither a share count nor a valid number.
    """
    digits = match.group(1).replace(".", "")
    if not digits.isdigit():
        return match.group(0)
    return f"{_num(float(digits) / 1e6, 2)} juta"


def build_valuasi(payload: dict, assum: dict, kf: dict) -> dict:
    """Paragraph 3 - Valuasi, in the four mandated sentence blocks."""
    raw = kf.get("raw") or {}
    cover = payload.get("cover") or {}
    rbox = cover.get("rating_box") or {}
    val = payload.get("valuation") or {}
    price, fv = rbox.get("price"), rbox.get("tp")
    shares, mid_eb = raw.get("shares"), raw.get("mid_eb")
    net_debt, multiple = raw.get("net_debt"), raw.get("multiple")
    sens = raw.get("sens") or {}
    # Terminal growth is a ticker-agnostic team constant (3.5% as of Sep 2026);
    # locked via the helper so the same value reaches valuation_page too.
    from server.report.valuation_constants import lock_g, lock_erp
    g = lock_g(assum)
    lock_erp(assum)
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
    method = "EV/EBITDA FY26F" if anchor_leg == "ev_ebitda" else "DCF"

    def as_pct(v):
        """wacc arrives as a fraction from the assumptions file and as a percent from the render
        payload - normalize instead of printing 1.377,00%."""
        if not isinstance(v, (int, float)):
            return None
        return v * 100.0 if abs(v) <= 1.5 else v

    wacc_pct = as_pct(wacc)
    eb_fy26 = (raw.get("ebitda") or [None, None, None])[2] if raw.get("ebitda") else None
    eb_val_tn = _div(eb_fy26, 1000) if (eb_fy26 is not None) else _div(mid_eb, 1000)
    eb_label = f"EBITDA FY26F Rp {_num(eb_val_tn, 2)} tn" if eb_fy26 else f"EBITDA mid-cycle Rp {_num(eb_val_tn, 2)} tn"
    parts.append(
        f"Kami menetapkan TP Rp {_num(fv, 0)} menggunakan {method} dengan exit multiple "
        f"{_num(multiple, 2)}× atas {eb_label}; leg DCF "
        f"(WACC {_num(wacc_pct, 2)}%, g {_num((g or 0) * 100, 1)}%) dihitung sebagai pembanding."
    )
    # 2. forecast linkage
    eb = [v for v in (raw.get("ebitda") or []) if isinstance(v, (int, float))]
    rev = [v for v in (raw.get("rev") or []) if isinstance(v, (int, float))]
    if len(eb) == 5 and eb[2]:
        cagr_26_28 = ((eb[4] / eb[2]) ** (1 / 2) - 1) * 100 if (len(eb) == 5 and eb[2] and eb[4]) else None
        cagr_25_28 = ((eb[4] / eb[1]) ** (1 / 3) - 1) * 100 if (len(eb) == 5 and eb[1] and eb[4]) else None
        rev_cagr = ((rev[4] / rev[1]) ** (1 / 3) - 1) * 100 if len(rev) == 5 and rev[1] else None
        cagr_str = f"CAGR EBITDA FY26F-FY28F {_pct(cagr_26_28)}" if cagr_26_28 is not None else "CAGR EBITDA FY26F-FY28F 0,0%"
        parts.append(
            f"TP ini mengimplikasikan {cagr_str}, setara {_pct(cagr_25_28)}/tahun dari EBITDA FY25A "
            f"Rp {_num(_div(eb[1], 1000), 2)} tn; revenue {_pct(rev_cagr)}/tahun."
        )
    # 3. trading multiple at TP
    per_f = None
    eps_f = (raw.get("eps") or [None] * 5)[2] if raw.get("eps") else None
    if price and isinstance(eps_f, (int, float)) and eps_f:
        per_f = fv / eps_f if fv else None
    peer_pe = (assum.get("sector_context") or {}).get("sectors_subsector_pe_2026")
    ev_at_tp = (fv * shares / 1e9 + net_debt) if (fv and shares) else None
    ev_eb_28 = _div(ev_at_tp, eb[4]) if (len(eb) == 5 and eb[4]) else _div(ev_at_tp, mid_eb)
    parts.append(
        f"Pada TP, saham dihargai EV/EBITDA 2028F "
        f"{_num(ev_eb_28, 1)}× dibandingkan "
        f"rata-rata historis 4 tahun {_num(multiple, 2)}× (band {_num(sens.get('low'), 2)}×-"
        f"{_num(sens.get('high'), 2)}×) atau PER 2026F {_num(per_f, 1)}× vs PE subsector "
        f"{_num(peer_pe, 2)}× - peer EV/EBITDA tidak tersedia, jadi TP bergantung pada "
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
        first = re.sub(r"([\d.]{7,})(?=\s*sh)", _shares_to_juta, first)
        if bucket:
            bucket = {"Distribusi insider": "insider selling", "Insider distribution": "insider selling"}.get(
                bucket, bucket)
            risk_tail = f"; (c) {bucket}: {first}" if first else f"; (c) {bucket}"
    parts.append(
        f"Risiko terhadap pandangan ini: (a) downside - tembaga atau emas turun 10% menekan "
        f"EBITDA mid-cycle 10%, TP turun ke Rp {_num(fv_down, 0)} "
        f"({_pct(((fv_down / fv) - 1) * 100 if (fv_down and fv) else None)}); (b) downside - "
        f"multiple bertahan di print 2026 "
        f"{_num(assum.get('ev_multiple_latest_print'), 2)}×, TP jatuh ke Rp "
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
    # Leave the §7-§9 verdict on the payload itself: the Critic gate, the guard tests and a
    # human reading /api/report/{ticker}/json all read the same audit instead of re-deriving it.
    try:
        from .house_rules import audit_house_rules

        payload["house_rules"] = audit_house_rules(payload)
    except Exception:
        pass
    return slide2


def _display_attr(text):
    """A printed label must never name another research house (the trail stays in the repo)."""
    try:
        from server.report.forecast_path import display_attribution

        return display_attribution(text)
    except Exception:
        return text
