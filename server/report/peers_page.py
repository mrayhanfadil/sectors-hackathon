"""Slide 5 page payload — peer table (Exhibit 11) + own-history bands (12-13) + implied prices.

Reads the cached artifacts only: no network, no Sectors client, so a PDF render is offline and
deterministic. The two halves are kept as separate objects on purpose — the page prints a hard break
between them and the gate forbids merging their conclusions into one story.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

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
    "Implied price di bagian ini adalah cross-check mean-reversion berbasis multiple historis — "
    "bukan Target Price resmi di Slide 4 — dan dihitung dengan asumsi driver fundamental (EPS, BVPS, "
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
    return f"{v:,.{d}f}" if isinstance(v, (int, float)) else "n.m."


def _fmt_rp(v: Optional[float]) -> str:
    return f"Rp {v:,.0f}" if isinstance(v, (int, float)) else "n/a"


def build_peers_page(ticker: str = "AMMN") -> dict:
    tk = ticker.upper()
    peers = _load(os.path.join(CACHE_ROOT, tk, "peer_table.json"))
    bands = _load(os.path.join(CACHE_ROOT, tk, "bands_1y.json"))
    if not peers or not bands or not bands.get("available"):
        return {"available": False, "ticker": tk,
                "reason": ("data peer/historis belum tersedia di cache — jalankan "
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
        f"{tk} diperdagangkan pada P/E {_fmt(covered['pe_ttm'])}x dan P/BV {_fmt(covered['pb_mrq'])}x — "
        f"vs median peer {_fmt(stats['pe_ttm']['median'])}x / {_fmt(stats['pb_mrq']['median'])}x "
        f"({gaps['pe_ttm']:+.0f}% / {gaps['pb_mrq']:+.0f}%) dan average "
        f"{_fmt(stats['pe_ttm']['average'])}x / {_fmt(stats['pb_mrq']['average'])}x."
        if gaps["pe_ttm"] is not None else f"{tk} P/E n.m. — earnings TTM negatif.")
    if covered.get("ev_ebitda_ttm") and stats["ev_ebitda_ttm"]["median"]:
        parts_a_narr.append(
            f"Pada multiple berbasis kas, EV/EBITDA {_fmt(covered['ev_ebitda_ttm'])}x vs median "
            f"{_fmt(stats['ev_ebitda_ttm']['median'])}x ({gaps['ev_ebitda_ttm']:+.0f}%), sementara ROE TTM "
            f"{covered['roe_ttm']*100:.1f}% vs median {stats['roe_ttm']['median']*100:.1f}% "
            f"({gaps['roe_ttm']:+.0f}%) — jadi premium P/E bukan semata efek basis earnings.")
    if peers.get("pe_excluded"):
        parts_a_narr.append(
            f"P/E {', '.join(peers['pe_excluded'])} dinyatakan n.m. (earnings negatif/near-zero) dan "
            f"tidak diikutkan dalam median/average; n pada baris statistik menunjukkan jumlah peer yang valid.")
    part_a = {
        "exhibit": 11,
        "title": f"Peer Valuation Table — {tk} vs comparables ({peers['as_of']})",
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
        "criteria": ("Peer set: emiten Basic Materials — Logam & Mineral dengan rentang market cap "
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
        narr = (f"Sekarang {s['current']:.2f}x — persentil {s['percentile']:.0f} dari {s['n']} sesi "
                f"(mean {s['mean']:.2f}x, median {s['median']:.2f}x).")
        if implied:
            if implied.get("is_range"):
                narr += (f" Implied: mean {_fmt_rp(implied['to_mean'])}, median "
                         f"{_fmt_rp(implied['to_median'])} — selisih material, disajikan sebagai rentang "
                         f"{_fmt_rp(implied['low'])}–{_fmt_rp(implied['high'])}.")
            else:
                narr += (f" Implied: mean {_fmt_rp(implied['to_mean'])}, median "
                         f"{_fmt_rp(implied['to_median'])} — kedua metode konvergen.")
        band_blocks.append({
            "key": key, "label": BAND_LABELS[key], "n": s["n"], "mean": s["mean"], "median": s["median"],
            "current": s["current"], "percentile": s["percentile"], "min": s["min"], "max": s["max"],
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
        "title": f"Relative Valuation — own history, 1-year window ({bands['window']['from']} – "
                 f"{bands['window']['to']})",
        "methodology": METHODOLOGY,
        "bands": band_blocks,
        "implied": implied_rows,
        "driver": bands["driver"],
        "driver_note": (f"Driver fundamental TTM per {bands['driver']['as_of']}; {frozen} dari {total} sesi "
                        f"memakai driver yang sama karena kuartal terbaru Sectors belum melewati tanggal itu — "
                        f"dinyatakan eksplisit, bukan disamarkan sebagai TTM segar."),
        "last_close": bands["last_close"],
        "disclaimer": DISCLAIMER,
        "sources": bands["sources"],
        "credit_log": bands.get("credit_log"),
    }

    return {"available": True, "ticker": tk, "as_of": peers["as_of"], "part_a": part_a, "part_b": part_b,
            "sections": {"a": "Peer Valuation (cross-sectional)",
                         "b": "Relative Valuation — Own History (time-series)"}}


def render_band_svg(block: dict, width: int = 430, height: int = 104) -> str:
    """Inline SVG line for a band block: series + dashed mean + dotted median + current marker."""
    pts = block["series"]
    if len(pts) < 5:
        return ""
    vals = [p["value"] for p in pts]
    lo, hi = min(vals + [block["mean"], block["median"]]), max(vals + [block["mean"], block["median"]])
    pad = (hi - lo) * 0.08 or 1.0
    lo, hi = lo - pad, hi + pad
    n = len(pts)

    def x(i: int) -> float:
        return 4 + (width - 8) * i / max(1, n - 1)

    def y(v: float) -> float:
        return height - 16 - (height - 26) * (v - lo) / (hi - lo)

    line = " ".join(f"{x(i):.1f},{y(p['value']):.1f}" for i, p in enumerate(pts))
    cur = pts[-1]
    out = [f'<svg viewBox="0 0 {width} {height}" class="band-svg" role="img">',
           f'<polyline points="{line}" fill="none" stroke="#12395b" stroke-width="1.6"/>',
           f'<line x1="4" y1="{y(block["mean"]):.1f}" x2="{width-4}" y2="{y(block["mean"]):.1f}" '
           f'stroke="#b45309" stroke-width="1" stroke-dasharray="6,3"/>',
           f'<line x1="4" y1="{y(block["median"]):.1f}" x2="{width-4}" y2="{y(block["median"]):.1f}" '
           f'stroke="#0f766e" stroke-width="1" stroke-dasharray="2,3"/>',
           f'<line x1="4" y1="{y(block["min"]):.1f}" x2="{width-4}" y2="{y(block["min"]):.1f}" '
           f'stroke="#cbd5e1" stroke-width="0.8"/>',
           f'<line x1="4" y1="{y(block["max"]):.1f}" x2="{width-4}" y2="{y(block["max"]):.1f}" '
           f'stroke="#cbd5e1" stroke-width="0.8"/>',
           f'<circle cx="{x(n-1):.1f}" cy="{y(cur["value"]):.1f}" r="3.6" fill="#b91c1c"/>',
           f'<text x="6" y="12" font-size="9" fill="#475569">mean {block["mean"]:.1f}x</text>',
           f'<text x="6" y="{height-3}" font-size="9" fill="#475569">{pts[0]["date"]}</text>',
           f'<text x="{width-70}" y="{height-3}" font-size="9" fill="#475569">{cur["date"]}</text>',
           "</svg>"]
    return "".join(out)


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
        print(f"  {blk['label']:10s} n={blk['n']:>3d} now={blk['current']:>7.2f} pct={blk['percentile']:>3.0f} "
              f"mean={blk['mean']:>7.2f} median={blk['median']:>7.2f}")
    for r in b["implied"]:
        print(f"  implied {r['label']:10s} mean {r['to_mean']:>9,.0f} median {r['to_median']:>9,.0f} "
              f"range={r['is_range']}")
    print(f"  disclaimer: {len(b['disclaimer'])} chars | driver note: {b['driver_note'][:90]}")
