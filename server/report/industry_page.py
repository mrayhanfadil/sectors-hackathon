"""Slide 2 — Kondisi Industri, Katalis Spesifik Emiten, Sentimen Pasar.

Three narrative paragraphs, no mandatory object, per
`docs/ammn-slides/slide2-industry-spec.md`. The page bridges the cover's thesis with the
performance page: paragraph 1 sets the sector and macro backdrop, paragraph 2 lists the
issuer-specific catalysts, paragraph 3 reads market positioning.

Two rules shape the code:

* **Nothing is estimated.** Every number here comes from the render payload (engines + Sectors
  fills) or from the assumptions file, and a datum the payload does not carry is stated as
  unavailable rather than filled with a plausible one — the spec's quantification discipline, and
  the same reason `kpis_note` exists.
* **Paragraph 3 stays out of valuation.** No multiple, no fair value, no target price: the spec
  forbids it there, and those numbers are the valuation page's. This module never reads the
  valuation block, so a later copy edit cannot leak one in.

The builder is deterministic and pure: same payload in, same three paragraphs out.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
FX_CACHE = REPO_ROOT / "output" / "cache" / "fx_usdidr.json"

BASIS_LABELS = {
    "shares": "jumlah saham",
    "avg_price": "harga rata-rata",
    "copper": "tembaga",
    "broker": "broker",
    "capex_q1": "capex Q1",
    "fcf_q1": "FCF Q1",
    "note": "catatan",
    "by": "periode",
    "volume": "volume",
    "price": "harga",
}

PARAGRAPH_HEADINGS = (
    "1. Kondisi Industri",
    "2. Katalis Spesifik Emiten",
    "3. Sentimen Pasar",
)


# --------------------------------------------------------------------- formatting (Indonesian)
def _num(value: Any, decimals: int = 2, signed: bool = False) -> Optional[str]:
    """1234.5 -> '1.234,50' (Indonesian decimal comma)."""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    txt = f"{num:+,.{decimals}f}" if signed else f"{num:,.{decimals}f}"
    return txt.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def _idr_bn(value: Any) -> str:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return "tidak tersedia"
    if abs(num) >= 1000:
        return f"Rp {_num(num / 1000)} tn"
    return f"Rp {_num(num)} md"


def _pct(value: Any, decimals: int = 2, signed: bool = False) -> Optional[str]:
    txt = _num(value, decimals=decimals, signed=signed)
    return None if txt is None else f"{txt}%"


def _as_fraction_pct(value: Any) -> Optional[float]:
    """`sector_context` stores growth as fractions (0.6808 = +68.08%), so scale before formatting."""
    try:
        return float(value) * 100
    except (TypeError, ValueError):
        return None


_MONTHS = ("Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des")


def _human_date(value: Any) -> str:
    """2026-09-12 -> '12 Sep 2026'; anything else passes through untouched."""
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", str(value or ""))
    if not m:
        return str(value or "tanggal terakhir")
    year, month, day = m.groups()
    return f"{int(day)} {_MONTHS[int(month) - 1]} {year}"


# --------------------------------------------------------------------- payload readers
def _series_moves(chart: Any) -> list[Optional[float]]:
    """Rebased % move per series. The cover chart carries unlabelled series, in the order the
    builder writes them: ticker first, index second (verified against the block's own note)."""
    if not isinstance(chart, dict):
        return []
    out: list[Optional[float]] = []
    for series in chart.get("series") or []:
        values = series.get("data") if isinstance(series, dict) else series
        if not isinstance(values, list) or len(values) < 2:
            out.append(None)
            continue
        try:
            first, last = float(values[0]), float(values[-1])
            out.append((last / first - 1) * 100 if first else None)
        except (TypeError, ValueError, ZeroDivisionError):
            out.append(None)
    return out


def _relative_performance(payload: dict) -> dict:
    """Ticker vs index over the window the payload actually carries.

    The Sectors daily feed caps at 90 days, so YTD is not computable and is reported as absent
    rather than extrapolated.
    """
    vs_jci = ((payload.get("cover") or {}).get("vs_jci")) or {}
    moves = _series_moves(vs_jci.get("chart"))
    ticker_move = moves[0] if len(moves) > 0 else None
    index_move = moves[1] if len(moves) > 1 else None
    rel = None if ticker_move is None or index_move is None else ticker_move - index_move
    return {
        "window": "90 hari",
        "ticker_move_pct": ticker_move,
        "index_move_pct": index_move,
        "rel_pp": rel,
        "ytd_available": vs_jci.get("ytd_abs") is not None,
        "source": vs_jci.get("source") or "",
    }


def _revenue_row(highlights: dict) -> tuple[Optional[str], Optional[float], list]:
    """Company revenue path from `financial_highlights`, which stores rows as
    [label, v1, v2, ...] under a parallel `years` list."""
    years = highlights.get("years") or []
    rows = highlights.get("rows") or []
    row = next((r for r in rows if isinstance(r, list) and r and "pendapatan" in str(r[0]).lower()), None)
    if not row or len(row) < 3:
        return None, None, years
    values = [v for v in row[1:] if isinstance(v, (int, float))]
    if len(values) < 2:
        return str(row[0]), None, years
    move = (values[-1] / values[-2] - 1) * 100 if values[-2] else None
    return re.sub(r"\s*\([^)]*\)\s*$", "", str(row[0])), move, years


def _fx_rate(payload: dict) -> Optional[dict]:
    """USD/IDR as the fill wrote it. The payload only carries it inside a prose source string,
    so the cache file the same build wrote is the readable source of truth."""
    try:
        fx = json.loads(FX_CACHE.read_text(encoding="utf-8"))
        if isinstance(fx, dict) and fx.get("rate"):
            return fx
    except (OSError, ValueError):
        pass
    meta = payload.get("meta") or {}
    return meta.get("fx_usdidr") if isinstance(meta.get("fx_usdidr"), dict) else None


# --------------------------------------------------------------------- the three paragraphs
def _paragraph_industry(payload: dict, assumptions: Optional[dict]) -> tuple[str, list[str]]:
    facts: list[str] = []
    sector = (assumptions or {}).get("sector_context") or {}
    forecast = sector.get("sectors_growth_forecast_2026") or {}
    # sector_context stores these as fractions (0.6808), unlike every other ratio in the repo
    rev = _pct(_as_fraction_pct(forecast.get("revenue_growth")), signed=True)
    eps = _pct(_as_fraction_pct(forecast.get("eps_growth")), signed=True)
    if rev and eps:
        facts.append(
            f"Sektor basic materials diperkirakan 2026F dengan pendapatan {rev} tetapi EPS {eps} "
            "(basis 2025; Sectors sector context), sehingga pemulihan laba sektor bertumpu pada "
            "margin, bukan pertumbuhan top-line."
        )
    elif sector:
        facts.append(
            "Proyeksi pertumbuhan sektor basic materials tidak lengkap di payload (Sectors sector "
            "context tanpa pasangan pendapatan/EPS) — dinyatakan kualitatif, bukan diestimasi."
        )

    copper = None
    for cat in payload.get("catalysts") or []:
        q = (cat or {}).get("quantified") or {}
        if isinstance(q, dict) and q.get("copper"):
            copper = (str(cat.get("name") or ""), str(q["copper"]), str(cat.get("source") or ""))
            break
    if copper:
        name, level, src = copper
        facts.append(
            f"Backdrop komoditas yang paling material tercatat pada katalis '{name}' — tembaga "
            f"{level}" + (f" (sumber: {src})" if src else "") + "."
        )
    else:
        facts.append(
            "Backdrop harga komoditas: tidak ada print terverifikasi di payload pada periode ini — "
            "dinyatakan kualitatif, bukan diestimasi."
        )

    fx = _fx_rate(payload)
    if fx:
        facts.append(
            f"Kurs USD/IDR {_num(fx['rate'], decimals=0)} per {_human_date(fx.get('date'))} "
            f"({fx.get('source', 'sumber terverifikasi')}): pendapatan emiten berdenominasi harga "
            "komoditas USD sementara sebagian basis biaya domestik berdenominasi rupiah, sehingga "
            "pergerakan kurs bekerja sebagai bantalan marjin operasional."
        )

    label, company_move, years = _revenue_row(payload.get("financial_highlights") or {})
    if company_move is not None and rev:
        facts.append(
            f"Posisi relatif emiten: {label or 'pendapatan'} pada tahun buku terakhir bergerak "
            f"{_pct(company_move, decimals=1, signed=True)}"
            + (f" (sampai {years[-1]})" if years else "")
            + f" sementara proyeksi sektor 2026F {rev} — basis periode tidak sebanding "
            "(aktual vs forecast), jadi pembacaan ini indikatif, bukan like-for-like."
        )
    elif company_move is not None:
        facts.append(
            f"Posisi relatif emiten belum dapat dibandingkan ke sektor: {label or 'pendapatan'} "
            f"tahun buku terakhir {_pct(company_move, decimals=1, signed=True)}, proyeksi sektor "
            "tidak tersedia di payload."
        )

    gap = payload.get("kpis_note")
    if gap:
        facts.append(
            "Posisi biaya struktural (kuartil biaya tunai/C1, tonase, kadar bijih) tidak dapat "
            f"dihitung dari payload: {gap}"
        )

    body = " ".join(facts) if facts else (
        "Kondisi industri tidak dapat disusun: payload tidak membawa data sektor maupun komoditas "
        "terverifikasi — dinyatakan sebagai tidak tersedia, bukan diisi estimasi."
    )
    return body, facts


def _paragraph_catalysts(payload: dict) -> tuple[str, list[str]]:
    catalysts = [c for c in (payload.get("catalysts") or []) if isinstance(c, dict)]
    if not catalysts:
        return (
            "Belum ada katalis spesifik emiten yang terverifikasi di payload — katalis generik "
            "sektor tidak dipakai sebagai penggantinya.",
            [],
        )
    parts: list[str] = []
    for i, cat in enumerate(catalysts, start=1):
        name = str(cat.get("name") or "katalis tanpa nama").strip()
        effect = str(cat.get("effect") or "").strip()
        quantified_raw = cat.get("quantified")
        src = str(cat.get("source") or "").strip()
        has_number = False
        if isinstance(quantified_raw, dict) and quantified_raw:
            basis = "; ".join(
                f"{BASIS_LABELS.get(str(k), str(k).replace('_', ' '))}: {v}"
                for k, v in quantified_raw.items()
                if v not in (None, "")
            )
            has_number = any(re.search(r"\d", str(v)) for v in quantified_raw.values())
            quantified = f"terkuantifikasi ({basis})" if has_number else f"kualitatif eksplisit ({basis})"
        elif isinstance(quantified_raw, str) and quantified_raw.strip():
            quantified = f"terkuantifikasi ({quantified_raw.strip()})"
        else:
            quantified = "kualitatif eksplisit (tanpa basis angka yang dapat dihitung)"
        line = f"({i}) {name} — {quantified}"
        if effect:
            line += f"; arah dampak: {effect}"
        if src:
            line += f" (sumber: {src})"
        parts.append(line + ".")
    note = str(payload.get("catalysts_note") or "").strip()
    body = "Katalis yang berlaku langsung ke emiten yang dicover: " + " ".join(parts)
    if note:
        body += f" Disiplin kuantifikasi: {note}"
    return body, parts


def _paragraph_sentiment(payload: dict) -> tuple[str, list[str]]:
    s = payload.get("sentiment") or {}
    facts: list[str] = []

    n30, n90 = s.get("net_foreign_30d_bn"), s.get("net_foreign_90d_bn")
    if n30 is not None or n90 is not None:
        bits = []
        if n30 is not None:
            bits.append(
                f"30 hari terakhir {'net beli' if float(n30) >= 0 else 'net jual'} "
                f"{_idr_bn(abs(float(n30)))}"
            )
        if n90 is not None:
            bits.append(
                f"90 hari {'net beli' if float(n90) >= 0 else 'net jual'} "
                f"{_idr_bn(abs(float(n90)))}"
            )
        facts.append("Arus dana asing mencatat " + " dan ".join(bits) + ".")

    buyers = [b for b in (s.get("top_buyers") or []) if isinstance(b, list) and len(b) >= 2]
    sellers = [x for x in (s.get("top_sellers") or []) if isinstance(x, list) and len(x) >= 2]
    if buyers and sellers:
        b_txt = ", ".join(f"{b[0]} {_idr_bn(abs(float(b[1])))}" for b in buyers[:3])
        s_txt = ", ".join(f"{x[0]} {_idr_bn(abs(float(x[1])))}" for x in sellers[:3])
        facts.append(f"Konsentrasi broker: sisi beli {b_txt}; sisi jual {s_txt}.")
    if s.get("pos_days"):
        facts.append(f"Frekuensi hari positif {s['pos_days']} sesi perdagangan.")

    rel = _relative_performance(payload)
    if rel["ticker_move_pct"] is not None and rel["index_move_pct"] is not None:
        facts.append(
            f"Kinerja harga relatif terhadap IHSG pada jendela {rel['window']}: emiten "
            f"{_pct(rel['ticker_move_pct'], signed=True)} vs IHSG {_pct(rel['index_move_pct'], signed=True)} "
            f"(relatif {_num(rel['rel_pp'], signed=True)} poin persentase)"
            + (f", basis {rel['source']}" if rel["source"] else "")
            + "."
        )
        if not rel["ytd_available"]:
            facts.append(
                "Jendela year-to-date tidak tersedia (feed harian Sectors dibatasi 90 hari) dan "
                "tidak diekstrapolasi."
            )

    news = [n for n in (payload.get("news") or []) if isinstance(n, dict)]
    if news:
        themes = "; ".join(
            f"{str(n.get('title') or '')[:70]} ({_human_date(n.get('date'))})" for n in news[:3]
        )
        facts.append(
            "Tone pemberitaan dinyatakan kualitatif: feed berita yang dipakai tidak membawa dimensi "
            f"sentimen, sehingga tidak ada skor yang dilaporkan. Judul terbaru yang membentuk narasi: {themes}."
        )
    else:
        facts.append("Feed berita kosong pada periode ini — tone media tidak dapat dinilai.")

    facts.append(
        "Agregat konsensus rating sektor (jumlah Buy/Hold/Sell) tidak tersedia di payload: tidak "
        "ada endpoint rating di sumber data yang dipakai, dan angkanya tidak diada-adakan."
    )
    return " ".join(facts), facts


def build_industry_page(payload: dict, assumptions: Optional[dict] = None) -> dict:
    """Return the slide-2 page block: three paragraphs, their basis, and the source list."""
    p1, basis1 = _paragraph_industry(payload, assumptions)
    p2, basis2 = _paragraph_catalysts(payload)
    p3, basis3 = _paragraph_sentiment(payload)

    sources: list[str] = []
    for cat in payload.get("catalysts") or []:
        if isinstance(cat, dict) and cat.get("source"):
            sources.append(str(cat["source"]))
    sent = payload.get("sentiment") or {}
    if sent.get("source"):
        sources.append(str(sent["source"]))
    rel = _relative_performance(payload)
    if rel["source"]:
        sources.append(rel["source"])
    for n in (payload.get("news") or [])[:3]:
        if isinstance(n, dict) and n.get("source"):
            sources.append(str(n["source"]))
    sector = (assumptions or {}).get("sector_context") or {}
    if sector.get("subsector_slug"):
        sources.append(f"Sectors sector context ({sector['subsector_slug']})")
    deduped = list(dict.fromkeys(s for s in sources if s))

    return {
        "title": "Kondisi Industri, Katalis & Sentimen",
        "subtitle": (
            "Latar sektor, katalis spesifik emiten, dan posisi pasar pada periode pelaporan. Tanpa "
            "objek wajib: tiga paragraf naratif, setiap angka dapat dilacak ke sumbernya."
        ),
        "paragraphs": [
            {"heading": PARAGRAPH_HEADINGS[0], "body": p1, "basis": basis1},
            {"heading": PARAGRAPH_HEADINGS[1], "body": p2, "basis": basis2},
            {"heading": PARAGRAPH_HEADINGS[2], "body": p3, "basis": basis3},
        ],
        "sources": deduped,
        "notes": [
            "Paragraf 3 tidak memuat multiple valuasi maupun target harga (domain halaman valuasi).",
            "Angka yang tidak tersedia dinyatakan eksplisit, bukan diestimasi.",
        ],
    }
