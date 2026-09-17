"""Slide 5 page payload - peer table (Exhibit 11) + own-history bands (12-13) + implied prices.

Reads the cached artifacts only: no network, no Sectors client, so a PDF render is offline and
deterministic. The two halves are kept as separate objects on purpose - the page prints a hard break
between them and the gate forbids merging their conclusions into one story.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from markupsafe import Markup
from server.report import numfmt as _nf

CACHE_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                          "output", "cache", "sectors")

BAND_LABELS = {"pe": "P/E", "pbv": "P/BV", "ev_ebitda": "EV/EBITDA", "ev_sales": "EV/Sales"}
DEFAULT_BANDS = ("pe", "pbv")

METHODOLOGY = (
    "Own-history relative valuation: empat trailing multiple (P/E, P/BV, EV/EBITDA, EV/Sales) sepanjang "
    "window satu tahun, dibandingkan dengan distribusi historisnya sendiri (average, median, persentil). "
    "Driver fundamental = rolling TTM (empat kuartal terakhir) dengan fallback berlapis; mata uang "
    "laporan dikonversi ke mata uang harga sebelum multiple dihitung."
)

DISCLAIMER = (
    "Implied price di bagian ini adalah cross-check mean-reversion berbasis multiple historis - "
    "bukan Target Price resmi di Halaman 4 - dan dihitung dengan asumsi driver fundamental (EPS, BVPS, "
    "EBITDA, Revenue) tetap konstan di level TTM saat ini, hanya multiple yang direversi ke rata-rata / "
    "median historisnya. Sifatnya snapshot posisi relatif terhadap sejarah harga sendiri, bukan proyeksi "
    "earnings atau target harga."
)


def _load(path: str) -> Optional[dict]:
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _pct(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if not a or not b:
        return None
    return (a / b - 1.0) * 100.0


def _fmt(v: Optional[float], d: int = 2) -> str:
    """Indonesian grouping, so a peer multiple reads 12,51× like the rest of the deck."""
    return _nf.idn(v, d) if isinstance(v, (int, float)) else "n.m."


def _fmt_rp(v: Optional[float]) -> str:
    return f"Rp {_nf.idn(v, digits=0)}" if isinstance(v, (int, float)) else "n/a"


def build_peers_page(ticker: str = "AMMN") -> dict:
    tk = ticker.upper()
    peers = _load(os.path.join(CACHE_ROOT, tk, "peer_table.json"))
    bands = _load(os.path.join(CACHE_ROOT, tk, "bands_1y.json"))
    if not peers or not bands or not bands.get("available"):
        return {"available": False, "ticker": tk,
                "reason": ("data peer/historis belum tersedia di cache - jalankan "
                           "python -m server.report.peers_data " + tk)}

    covered = next((r for r in peers["rows"] if r["is_covered"]), None)
    if covered is None:
        return {"available": False, "ticker": tk,
                "reason": "peer table carries no row for the covered issuer"}
    stats = peers["stats"]

    # ---- Part A: table -----------------------------------------------------
    table_rows = []
    for r in peers["rows"]:
        table_rows.append({
            "symbol": r["symbol"],
            "name": (r.get("company_name") or r["symbol"]).replace("PT ", "").replace(" Tbk.", ""),
            "is_covered": r["is_covered"],
            "pe": r["pe_ttm"] if r.get("pe_meaningful") else None,
            "pe_nm": not r.get("pe_meaningful"),
            "pbv": r.get("pb_mrq"),
            "ev_ebitda": r.get("ev_ebitda_ttm"),
            "ev_ebitda_nm": r.get("ev_ebitda_ttm") is None,
            "roe": r.get("roe_ttm"),
            "market_cap": r.get("market_cap"),
        })
    gaps = {k: _pct(covered.get({k: "pe_ttm", "pb_mrq": "pb_mrq", "ev_ebitda_ttm": "ev_ebitda_ttm",
                                 "roe_ttm": "roe_ttm"}.get(k, k)),
                    stats[k]["median"]) for k in ("pe_ttm", "pb_mrq", "ev_ebitda_ttm", "roe_ttm")}

    parts_a_narr = []
    parts_a_narr.append(
        f"{tk} diperdagangkan pada P/E {_fmt(covered['pe_ttm'])}× dan P/BV {_fmt(covered['pb_mrq'])}× - "
        f"vs median peer {_fmt(stats['pe_ttm']['median'])}× / {_fmt(stats['pb_mrq']['median'])}× "
        f"({_nf.dec(gaps['pe_ttm'], digits=0, signed=True)}% / {_nf.dec(gaps['pb_mrq'], digits=0, signed=True)}%) dan average "
        f"{_fmt(stats['pe_ttm']['average'])}× / {_fmt(stats['pb_mrq']['average'])}×."
        if gaps["pe_ttm"] is not None else f"{tk} P/E n.m. - earnings TTM negatif.")
    if covered.get("ev_ebitda_ttm") and stats["ev_ebitda_ttm"]["median"]:
        parts_a_narr.append(
            f"Pada multiple berbasis kas, EV/EBITDA LTM {_fmt(covered['ev_ebitda_ttm'])}× vs median "
            f"{_fmt(stats['ev_ebitda_ttm']['median'])}× ({_nf.dec(gaps['ev_ebitda_ttm'], digits=0, signed=True)}%), sementara ROE TTM "
            f"{_nf.dec(covered['roe_ttm']*100, digits=1)}% vs median {_nf.dec(stats['roe_ttm']['median']*100, digits=1)}% "
            f"({_nf.dec(gaps['roe_ttm'], digits=0, signed=True)}%) - jadi premium P/E bukan semata efek basis earnings.")
    if peers.get("pe_excluded"):
        parts_a_narr.append(
            f"P/E {', '.join(peers['pe_excluded'])} dinyatakan n.m. (earnings negatif/near-zero) dan "
            f"tidak diikutkan dalam median/average; n pada baris statistik menunjukkan jumlah peer yang valid.")
    part_a = {
        "exhibit": 11,
        "title": f"Peer Valuation Table - {tk} vs comparables ({peers['as_of']})",
        "columns": ["Ticker", "Perusahaan", "P/E (x)", "P/BV (x)", "EV/EBITDA (x)", "ROE (%)", "Market Cap"],
        "rows": table_rows,
        "median": {"symbol": "MEDIAN", "pe": stats["pe_ttm"]["median"], "pbv": stats["pb_mrq"]["median"],
                   "ev_ebitda": stats["ev_ebitda_ttm"]["median"], "roe": stats["roe_ttm"]["median"],
                   "is_stat": True},
        "average": {"symbol": "AVERAGE", "pe": stats["pe_ttm"]["average"], "pbv": stats["pb_mrq"]["average"],
                    "ev_ebitda": stats["ev_ebitda_ttm"]["average"], "roe": stats["roe_ttm"]["average"],
                    "is_stat": True},
        "counts": {k: stats[k]["n"] for k in stats},
        "basis": peers["basis"],
        "as_of": peers["as_of"],
        "criteria": ("Peer set: emiten Basic Materials - Logam & Mineral dengan rentang market cap "
                     "sebanding (Rp 0,9 tn – Rp 127 tn) dan cakupan laporan kuartalan lengkap di Sectors; "
                     "harga as of " + peers["as_of"] + "."),
        "narrative": parts_a_narr,
        "narrative_text": " ".join(parts_a_narr),
        "sources": peers["sources"],
        "credit_log": peers.get("credit_log"),
    }

    # ---- Part B: bands -----------------------------------------------------
    band_blocks = []
    for key in ("pe", "pbv", "ev_ebitda", "ev_sales"):
        s = bands["summary"].get(key)
        if not s:
            continue
        series = [{"date": x["date"], "value": x[key]} for x in bands["sessions"] if x[key] is not None]
        implied = bands["implied_price"].get(key)
        narr = (f"Sekarang {_nf.dec(s['current'], digits=2)}× - persentil {_nf.dec(s['percentile'], digits=0)} dari {s['n']} sesi "
                f"(mean {_nf.dec(s['mean'], digits=2)}×, median {_nf.dec(s['median'], digits=2)}×).")
        if implied:
            if implied.get("is_range"):
                narr += (f" Implied: mean {_fmt_rp(implied['to_mean'])}, median "
                         f"{_fmt_rp(implied['to_median'])} - selisih material, disajikan sebagai rentang "
                         f"{_fmt_rp(implied['low'])}–{_fmt_rp(implied['high'])}.")
            else:
                narr += (f" Implied: mean {_fmt_rp(implied['to_mean'])}, median "
                         f"{_fmt_rp(implied['to_median'])} - kedua metode konvergen.")
        # The distribution band the tool shades (P10-P90) is not in the payload's summary, so it is derived from
        # the same sessions the chart plots - nothing is authored.
        _vals = sorted(x["value"] for x in series if isinstance(x.get("value"), (int, float)))

        def _pctile(pct: float):
            if not _vals:
                return None
            k = (len(_vals) - 1) * pct / 100.0
            lo_i, hi_i = int(k), min(int(k) + 1, len(_vals) - 1)
            return _vals[lo_i] + (_vals[hi_i] - _vals[lo_i]) * (k - lo_i)

        band_blocks.append({
            "key": key, "label": BAND_LABELS[key], "n": s["n"], "mean": s["mean"], "median": s["median"],
            "current": s["current"], "percentile": s["percentile"], "min": s["min"], "max": s["max"],
            "p10": _pctile(10), "p90": _pctile(90),
            "series": series, "implied": implied, "narrative": narr,
        })

    implied_rows = [{"key": k, "label": BAND_LABELS[k], "to_mean": v["to_mean"], "to_median": v["to_median"],
                     "low": v["low"], "high": v["high"], "is_range": v.get("is_range", False),
                     "delta_pct": ((v["high"] - v["low"]) / v["high"] * 100.0) if v["high"] else None}
                    for k, v in bands["implied_price"].items()]

    frozen = bands.get("driver_frozen_sessions", 0)
    total = bands["window"]["sessions"]
    part_b = {
        "exhibits": [12, 13],
        "title": f"Relative Valuation - own history, 1-year window ({bands['window']['from']} – "
                 f"{bands['window']['to']})",
        "methodology": METHODOLOGY,
        "bands": band_blocks,
        "implied": implied_rows,
        "driver": bands["driver"],
        "driver_note": (f"Driver fundamental TTM per {bands['driver']['as_of']}; {frozen} dari {total} sesi "
                        f"memakai driver yang sama karena kuartal terbaru Sectors belum melewati tanggal itu - "
                        f"dinyatakan eksplisit, bukan disamarkan sebagai TTM segar."),
        "last_close": bands["last_close"],
        "disclaimer": DISCLAIMER,
        "sources": bands["sources"],
        "credit_log": bands.get("credit_log"),
    }

    return {"available": True, "ticker": tk, "as_of": peers["as_of"], "part_a": part_a, "part_b": part_b,
            "sections": {"a": "Peer Valuation (cross-sectional)",
                         "b": "Relative Valuation - Own History (time-series)"}}


def render_band_svg(block: dict, width: int = 430, height: int = 170) -> str:
    """One multiple's own history, drawn the way the valuation tool draws its panels.

    Shaded P10-P90 distribution band, the series line over it, the median as a dashed line pinned to the left and
    the average as a dotted line pinned to the right (so two benchmarks that sit close together cannot collide),
    and today's value as a marker with a label. Same colour meanings as the deck's tables and heatmap: navy is the
    subject, ice is its historical distribution, and the reference lines borrow the buy/sell tokens.
    """
    NAVY, ICE, RULE, MUTED, BUY, SELL = "#0B1F3A", "#A9C9E8", "#D6E2EE", "#63748A", "#1E8F5F", "#C0392B"
    pts = block["series"]
    if len(pts) < 5:
        return ""
    vals = [p["value"] for p in pts]
    p10, p90 = block.get("p10"), block.get("p90")
    refs = [v for v in (block["mean"], block["median"], p10, p90) if isinstance(v, (int, float))]
    lo, hi = min(vals + refs), max(vals + refs)
    pad = (hi - lo) * 0.10 or 1.0
    lo, hi = lo - pad, hi + pad
    n = len(pts)

    def x(i: int) -> float:
        return 4 + (width - 14) * i / max(1, n - 1)

    def y(v: float) -> float:
        return height - 22 - (height - 40) * (v - lo) / (hi - lo)

    def d(v: float) -> str:
        # Geometry must be locale-independent: "34,2" is not a number to an SVG renderer, and the whole plot
        # collapsed to a flat strip while the labels looked fine. Text keeps the house convention below.
        return f"{v:.1f}"

    out = [f'<svg viewBox="0 0 {width} {height}" class="band-svg" role="img">']
    # the distribution band, exactly the tool's shading
    if isinstance(p10, (int, float)) and isinstance(p90, (int, float)):
        y10, y90 = y(p10), y(p90)
        out.append(f'<rect x="4" y="{d(y90)}" width="{width - 8}" height="{d(max(y10 - y90, 0.5))}" '
                   f'fill="rgba(169,201,232,0.30)"/>')
        out.append(f'<line x1="4" y1="{d(y90)}" x2="{width - 4}" y2="{d(y90)}" stroke="{ICE}" stroke-width="0.7"/>')
        out.append(f'<line x1="4" y1="{d(y10)}" x2="{width - 4}" y2="{d(y10)}" stroke="{ICE}" stroke-width="0.7"/>')
    # references: average pinned right, median pinned left
    for val, colour, dash, txt, anchor_x, anchor, dy in (
            (block["mean"], SELL, "5 3", f"rata-rata {_nf.dec(block['mean'], digits=1)}×", width - 6, "end", 11),
            (block["median"], BUY, "2 3", f"median {_nf.dec(block['median'], digits=1)}×", 6, "start", -4)):
        if not isinstance(val, (int, float)):
            continue
        yy = d(y(val))
        out.append(f'<line x1="4" y1="{yy}" x2="{width - 4}" y2="{yy}" stroke="{colour}" stroke-width="1" '
                   f'stroke-dasharray="{dash}"/>')
        out.append(f'<text x="{anchor_x}" y="{d(y(val) + dy)}" font-size="8" font-weight="700" fill="{colour}" '
                   f'text-anchor="{anchor}">{txt}</text>')
    line = " ".join(f"{d(x(i))},{d(y(v))}" for i, v in enumerate(vals))
    out.append(f'<polyline points="{line}" fill="none" stroke="{NAVY}" stroke-width="1.8" '
               f'stroke-linejoin="round" stroke-linecap="round"/>')
    cur = pts[-1]
    cx, cy = x(n - 1), y(cur["value"])
    out.append(f'<circle cx="{d(cx)}" cy="{d(cy)}" r="3.4" fill="{NAVY}" stroke="#ffffff" stroke-width="1.2"/>')
    out.append(f'<text x="{width - 6}" y="{d(cy - 6)}" font-size="8.5" font-weight="700" fill="{NAVY}" '
               f'text-anchor="end">{_nf.dec(cur["value"], digits=1)}× · p{_nf.dec(block["percentile"], digits=0)}</text>')
    # Secondary current-value label below the point so it cannot collide with the mean label
    out.append(f'<text x="{width - 6}" y="{d(cy + 12)}" font-size="7.5" fill="{MUTED}" '
               f'text-anchor="end">sekarang</text>')
    out.append(f'<line x1="4" y1="{height - 12}" x2="{width - 4}" y2="{height - 12}" stroke="{RULE}" stroke-width="0.7"/>')
    out.append(f'<text x="6" y="{height - 3}" font-size="8" fill="{MUTED}">{pts[0]["date"]}</text>')
    out.append(f'<text x="{width - 6}" y="{height - 3}" font-size="8" fill="{MUTED}" text-anchor="end">'
               f'{cur["date"]} · P10-P90 {_nf.dec(p10, digits=0)}×-{_nf.dec(p90, digits=0)}×</text>')
    out.append("</svg>")
    # Jinja autoescapes html by default: without Markup the chart reaches the page as escaped text
    return Markup("".join(out))


if __name__ == "__main__":
    import sys
    tk = (sys.argv[1] if len(sys.argv) > 1 else "AMMN").upper()
    page = build_peers_page(tk)
    if not page.get("available"):
        print("unavailable:", page.get("reason"))
        raise SystemExit(1)
    a, b = page["part_a"], page["part_b"]
    print(f"Exhibit {a['exhibit']}: {len(a['rows'])} rows + median/average | narrative {len(a['narrative'])} sentences")
    print("  " + a["narrative_text"][:300])
    for blk in b["bands"]:
        print(f"  {blk['label']:10s} n={blk['n']:>3d} now={_nf.dec(blk['current'], digits=2, width=7)} pct={_nf.dec(blk['percentile'], digits=0, width=3)} "
              f"mean={_nf.dec(blk['mean'], digits=2, width=7)} median={_nf.dec(blk['median'], digits=2, width=7)}")
    for r in b["implied"]:
        print(f"  implied {r['label']:10s} mean {_nf.idn(r['to_mean'], digits=0, width=9)} median {_nf.idn(r['to_median'], digits=0, width=9)} "
              f"range={r['is_range']}")
    print(f"  disclaimer: {len(b['disclaimer'])} chars | driver note: {b['driver_note'][:90]}")
