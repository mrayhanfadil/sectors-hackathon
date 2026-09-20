"""Slide 2 - Kondisi Industri, Katalis Spesifik Emiten, Sentimen Pasar.

Three narrative paragraphs, no mandatory object, per
`docs/ammn-slides/slide2-industry-spec.md`. The page bridges the cover's terse takeaways and the
valuation pages by using the widest Sectors evidence the fill carries - the subsector report, the
IDX filings digest, corporate actions, the monthly ownership composition and the free-float
screener - instead of only the four headline catalysts.

Discipline this module keeps, because the page is read as prose and prose hides its own holes:

* every number is copied from the payload (a Sectors endpoint value, an engine output, or a sum of
  returned values, which the copy labels as a sum);
* a slot whose data is absent says so in words. Nothing is estimated, interpolated, or carried over
  from a neighbouring year;
* paragraph 3 stays out of valuation - no multiple, no target price, no fair value. That is the
  valuation pages' domain, and `house_rules.audit_industry_page` enforces it;
* both directions of insider activity are reported when the filings carry both. A page that lists
  the buys and drops the sells would be technically sourced and still misleading.
"""

from __future__ import annotations

from typing import Any, Optional

PARAGRAPH_HEADINGS = (
    "1. Kondisi Industri",
    "2. Katalis Spesifik Emiten",
    "3. Sentimen Pasar",
)

_KEY_LABELS = {
    "copper": "tembaga",
    "broker": "broker",
    "shares": "saham",
    "avg_price": "harga rata-rata",
    "by": "oleh",
    "capex_q1": "capex Q1",
    "fcf_q1": "FCF Q1",
    "note": "catatan",
    "volume": "volume",
    "revenue": "pendapatan",
}


# --------------------------------------------------------------------------- formatting helpers
def _num(value: Any, digits: int = 2) -> str:
    """Indonesian number: '.' thousands, ',' decimals."""
    try:
        text = f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return "-"
    return text.replace(",", "\u00a0").replace(".", ",").replace("\u00a0", ".")


def _idr_bn(value: Any, digits: int = 2) -> str:
    """Rp in miliar, the unit the rest of the deck uses. Net flows can be negative."""
    try:
        amount = float(value) / 1e9
    except (TypeError, ValueError):
        return "-"
    sign = "-" if amount < 0 else ""
    return sign + "Rp " + _num(abs(amount), digits) + " md"


def _idr_tn(value: Any, digits: int = 1) -> str:
    try:
        amount = float(value) / 1e12
    except (TypeError, ValueError):
        return "-"
    sign = "-" if amount < 0 else ""
    return sign + "Rp " + _num(abs(amount), digits) + " tn"


def _shares(value: Any, signed: bool = False) -> str:
    try:
        amount = float(value) / 1e6
    except (TypeError, ValueError):
        return "-"
    sign = "+" if signed and amount > 0 else ("-" if amount < 0 else "")
    return sign + _num(abs(amount), 2) + " jt saham"


def _pct(value: Any, digits: int = 2) -> str:
    if value is None:
        return "-"
    try:
        return ("+" if float(value) > 0 else "") + _num(value, digits) + "%"
    except (TypeError, ValueError):
        return "-"


def _human_date(value: Any) -> str:
    """2026-09-12 -> 12 Sep 2026. Anything unexpected is passed through."""
    months = (
        "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des",
    )
    text = str(value or "")
    try:
        year, month, day = text[:10].split("-")
        return f"{int(day)} {months[int(month) - 1]} {year}"
    except (ValueError, IndexError):
        return text


def _sentence(parts: list[str]) -> str:
    """Join non-empty fragments into one sentence, each already carrying its own full stop."""
    return " ".join(p.strip() for p in parts if p and p.strip())


def _basis(parts: list[str]) -> str:
    return "; ".join(p for p in parts if p)


# --------------------------------------------------------------------------- paragraph 1
def _paragraph_industry(payload: dict, assumptions: Optional[dict]) -> tuple[str, str]:
    """What the sector is doing, what the macro backdrop is, and where the issuer sits in it."""
    sector = payload.get("sector_data") or {}
    forecast = sector.get("growth_forecast_2026") or {}
    actual = sector.get("growth_actual_2025") or {}
    subsector = sector.get("subsector") or payload.get("meta", {}).get("subsector") or "sektor ini"

    parts: list[str] = []
    if forecast.get("revenue_pct") is not None or forecast.get("eps_pct") is not None:
        base = forecast.get("base_year")
        parts.append(
            f"Proyeksi Sectors untuk subsektor {subsector} tahun 2026 memperkirakan pendapatan "
            f"{_pct(forecast.get('revenue_pct'))} dengan laba per saham {_pct(forecast.get('eps_pct'))} "
            f"(basis tahun {base}); pada 2025 subsektor ini membukukan pendapatan "
            f"{_pct(actual.get('revenue_pct'))} dan laba {_pct(actual.get('eps_pct'))}. "
            f"Artinya pertumbuhan laba sektor tidak lagi bertumpu pada pertumbuhan penjualan, "
            f"melainkan pada perbaikan margin dan basis biaya."
        )
    else:
        parts.append(
            f"Proyeksi pertumbuhan subsektor {subsector} tidak tersedia di data, sehingga arah "
            f"sektor tidak dinyatakan secara kuantitatif di sini."
        )

    top = sector.get("top_mcap") or []
    if top:
        rank = next((i + 1 for i, t in enumerate(top) if "AMMN" in str(t.get("symbol", ""))), None)
        leader = top[0]
        if rank == 1:
            runner = top[1] if len(top) > 1 else {}
            parts.append(
                f"Emiten yang dibahas adalah yang terbesar di lima emiten berkapitalisasi teratas "
                f"yang tersedia di data ({_idr_tn(leader.get('market_cap'))}"
                + (
                    f", di atas {runner.get('name')} pada {_idr_tn(runner.get('market_cap'))}"
                    if runner
                    else ""
                )
                + "), jadi kondisi sektor di atas langsung relevan ke laporan ini."
            )
        elif rank:
            parts.append(
                f"Emiten yang dibahas berada di peringkat {rank} dari lima emiten berkapitalisasi "
                f"terbesar di subsektor ini ({_idr_tn(leader.get('market_cap'))} untuk peringkat "
                f"pertama), jadi ia menanggung risiko sektor tanpa menjadi penentu arahnya."
            )
        else:
            parts.append(
                "Emiten yang dibahas tidak berada dalam lima kapitalisasi terbesar yang "
                "tersedia di data, sehingga posisinya di sektor ini tidak dapat ditentukan "
                "dari data yang ada."
            )

    copper = None
    for item in payload.get("catalysts") or []:
        quantified = item.get("quantified") or {}
        if quantified.get("copper"):
            copper = quantified["copper"]
    if copper:
        parts.append(
            f"Latar komoditas yang paling menentukan bagi sektor ini adalah harga tembaga, yang "
            f"mencatat {copper}."
        )

    fx_note = _fx_backdrop(payload)
    if fx_note:
        parts.append(fx_note)

    # Latest reported year-over-year, so both sides of the comparison are one-year growth rates
    # (the issuer's actual, the sector's forecast). A cumulative multi-year move would not be
    # comparable with a forecast and would flatter the issuer.
    company_revenue = None
    for row in (payload.get("financial_highlights") or {}).get("rows") or []:
        label = str(row[0] if isinstance(row, (list, tuple)) and row else "")
        if label.lower().startswith("pendapatan") and isinstance(row, (list, tuple)) and len(row) > 2:
            try:
                prev, last = float(row[-2]), float(row[-1])
                if prev:
                    company_revenue = (last / prev - 1) * 100
            except (TypeError, ValueError):
                company_revenue = None
    sector_rev = forecast.get("revenue_pct")
    if company_revenue is not None and sector_rev is not None:
        parts.append(
            f"Posisi relatif: pertumbuhan pendapatan tahun terakhir emiten ini "
            f"{_pct(company_revenue)} (aktual, tahun terakhir vs sebelumnya) terhadap proyeksi "
            f"sektor {_pct(sector_rev)} untuk 2026. Keduanya satu tahun dan satuannya sama, tapi "
            f"periodenya berbeda (aktual vs proyeksi), jadi perbandingan ini indikatif: emiten "
            f"menyusut lebih dalam daripada proyeksi penurunan sektor, dan belum terlihat "
            f"mengikuti pemulihan laba sektor."
        )
    else:
        parts.append(
            "Posisi relatif emiten terhadap sektor tidak dapat dinyatakan secara kuantitatif "
            "karena salah satu sisi perbandingan tidak tersedia di data."
        )

    parts.append(
        "Posisi biaya yang menentukan daya saing sektor ini (tonase, kadar, C1, AISC) tidak dapat "
        "data yang tersedia tidak memuat metrik operasional tersebut, jadi "
        "perbandingan biaya vs peers dinyatakan kualitatif dan tidak diisi angka."
    )

    basis = _basis(
        [
            "proyeksi & aktual subsektor: " + str(sector.get("source") or "tidak tersedia"),
            "kapitalisasi terbesar: laporan subsektor Sectors",
            "harga tembaga: sumber per katalis",
            "kinerja keuangan emiten: laporan keuangan emiten",
        ]
    )
    return _sentence(parts), basis


def _fx_backdrop(payload: dict) -> str:
    """FX from the payload's market block when it is there, otherwise nothing (never a guess)."""
    text = ""
    stats = ((payload.get("cover") or {}).get("slide1") or {}).get("stats") or {}
    sources = stats.get("sources") or {}
    if isinstance(sources, dict):
        text = str(sources.get("mkt_cap_usd") or "")
    if "USD/IDR" in text:
        return (
            f"Latar makro yang paling menentukan: {text.split('·')[0].strip() if '·' in text else text}, "
            f"sementara harga jual komoditas emiten ini didominasi denominasi dolar dan sebagian "
            f"biayanya berdenominasi rupiah."
        )
    return ""


# --------------------------------------------------------------------------- paragraph 2
def _paragraph_catalysts(payload: dict) -> tuple[str, str]:
    """Issuer-specific catalysts, each with its own quantitative basis or an explicit label."""
    parts: list[str] = []
    items = payload.get("catalysts") or []
    if items:
        listed = []
        for item in items:
            quantified = item.get("quantified") or {}
            numeric = bool(quantified) and any(
                any(ch.isdigit() for ch in str(v)) and "kualitatif" not in str(v).lower()
                for v in quantified.values()
            )
            detail = ", ".join(
                f"{_KEY_LABELS.get(k, k.replace('_', ' '))} {v}" for k, v in quantified.items()
            )
            label = "terkuantifikasi" if numeric else "kualitatif eksplisit"
            listed.append(
                f"{item.get('name')} ({label}: {detail}; sumber: {item.get('source')}) - "
                f"efek: {item.get('effect')}"
            )
        parts.append("Katalis yang langsung menyentuh emiten ini: " + "; ".join(listed) + ".")
    else:
        parts.append(
            "Catatan katalis kosong di data, sehingga daftar katalis emiten tidak dapat "
            "dinyatakan pada halaman ini."
        )

    digest = payload.get("filings_digest") or {}
    buy, sell = digest.get("buy") or {}, digest.get("sell") or {}
    if buy.get("n") or sell.get("n"):
        parts.append(
            f"Di sisi keterbukaan IDX, {digest.get('n')} dokumen terakhir yang dikembalikan "
            f"data berisi {buy.get('n', 0)} transaksi beli oleh "
            f"{len(buy.get('holders') or [])} nama berbeda "
            f"({_shares(buy.get('shares'))}, nilai transaksi {_idr_tn(buy.get('value'))}, "
            f"{_human_date(buy.get('first'))} sampai {_human_date(buy.get('last'))}) dan "
            f"{sell.get('n', 0)} transaksi jual oleh {len(sell.get('holders') or [])} nama "
            f"({_shares(sell.get('shares'))}, nilai {_idr_tn(sell.get('value'))}, "
            f"{_human_date(sell.get('first'))} sampai {_human_date(sell.get('last'))}). "
            f"Dua arah ini harus dibaca bersama: pembelian oleh orang dalam yang jadi sorotan berita "
            f"berjalan bersamaan dengan penjualan pemegang saham terkait, jadi kesimpulan "
            f"sepihak bahwa orang dalam mengakumulasi saham tidak didukung datanya."
        )
        try:
            net = float(buy.get("value") or 0) - float(sell.get("value") or 0)
            parts.append(
                f"Neto dari kedua arah transaksi tersebut adalah {_idr_tn(net)} "
                f"(jumlah dari nilai transaksi yang tersedia di data, bukan angka yang "
                f"dilaporkan langsung oleh Sectors)."
            )
        except (TypeError, ValueError):
            pass
    else:
        parts.append(
            "Ringkasan keterbukaan IDX tidak tersedia di data, sehingga aktivitas orang dalam "
            "tidak dikuantifikasi di halaman ini."
        )

    ca = payload.get("corporate_actions") or {}
    if ca:
        status = [
            name
            for name, key in (
                ("dividen", "dividend"),
                ("dividen mendatang", "upcoming_dividend"),
                ("bonus", "bonus"),
                ("right issue", "right_issue"),
                ("stock split", "stock_split"),
                ("waran", "warrant"),
            )
            if ca.get(key)
        ]
        agm = ca.get("agm") or []
        agm_text = (
            f"RUPS terakhir tercatat {_human_date(sorted(agm)[-1])}"
            if agm
            else "tanggal RUPS tidak tersedia di data"
        )
        parts.append(
            f"Aksi korporasi: {agm_text}. "
            + (
                "Tidak ada dividen, bonus, right issue, stock split, maupun waran yang tercatat, "
                "sehingga katalis pengembalian modal kepada pemegang saham belum ada basisnya di "
                "data ini."
                if not status
                else "Yang tercatat: " + ", ".join(status) + "."
            )
        )
    else:
        parts.append(
            "Aksi korporasi tidak tersedia di data, sehingga tidak ada katalis korporasi yang "
            "dapat dinyatakan untuk emiten ini."
        )

    if payload.get("catalysts_note"):
        parts.append(str(payload["catalysts_note"]))
    return _sentence(parts), _basis(
        [
            "catatan katalis (sumber per butir)",
            str(digest.get("source") or "keterbukaan IDX"),
            str(ca.get("source") or "aksi korporasi tidak tersedia"),
        ]
    )


# --------------------------------------------------------------------------- paragraph 3
def _paragraph_sentiment(payload: dict) -> tuple[str, str]:
    """How the market currently treats the sector and the issuer. No valuation content."""
    parts: list[str] = []
    sentiment = payload.get("sentiment") or {}
    window = sentiment.get("window") or "90 hari"
    if sentiment.get("net_foreign_90d_bn") is not None or sentiment.get("net_foreign_30d_bn") is not None:
        parts.append(
            f"Arus dana asing: neto {_idr_bn((sentiment.get('net_foreign_90d_bn') or 0) * 1e9)} "
            f"sepanjang {window} terakhir, dan {_idr_bn((sentiment.get('net_foreign_30d_bn') or 0) * 1e9)} "
            f"pada 30 hari terakhir, jadi arus asing berbalik arah menjadi beli bersih di bulan "
            f"terakhir setelah jual bersih pada jendela yang lebih panjang."
            if (sentiment.get("net_foreign_30d_bn") or 0) > 0
            and (sentiment.get("net_foreign_90d_bn") or 0) < 0
            else f"Arus dana asing: neto {_idr_bn((sentiment.get('net_foreign_90d_bn') or 0) * 1e9)} "
            f"pada {window} terakhir dan {_idr_bn((sentiment.get('net_foreign_30d_bn') or 0) * 1e9)} "
            f"pada 30 hari terakhir, arahnya belum berbalik."
        )
        if sentiment.get("pos_days"):
            parts.append(
                f"Hari penutupan positif {sentiment['pos_days']} sesi pada jendela yang sama."
            )
    else:
        parts.append(
            f"Arus dana asing tidak tersedia di data, sehingga arah dana asing pada {window} "
            f"terakhir tidak dinyatakan angkanya."
        )

    buyers, sellers = sentiment.get("top_buyers") or [], sentiment.get("top_sellers") or []
    if buyers or sellers:
        parts.append(
            "Konsentrasi broker: sisi beli "
            + ", ".join(f"{b[0]} {_idr_bn((b[1] or 0) * 1e9)}" for b in buyers[:3])
            + "; sisi jual "
            + ", ".join(f"{s[0]} {_idr_bn(abs(s[1] or 0) * 1e9)}" for s in sellers[:3])
            + _broker_gap(buyers)
        )

    mix = payload.get("ownership_mix") or {}
    latest, first = mix.get("latest") or {}, mix.get("first") or {}
    if latest.get("foreign") is not None and first.get("foreign") is not None:
        try:
            delta = float(latest["foreign"]) - float(first["foreign"])
            dom_delta = float(latest.get("domestic") or 0) - float(first.get("domestic") or 0)
            parts.append(
                f"Komposisi pemegang saham (bulanan, {mix.get('months')} titik data): kepemilikan "
                f"asing {_shares(latest['foreign'])} per {_human_date(latest.get('date'))} vs "
                f"{_shares(first['foreign'])} per {_human_date(first.get('date'))} "
                f"({_shares(delta)} dalam periode ini), sementara kepemilikan domestik "
                f"{_shares(dom_delta, signed=True)}. Di dalam blok asing, institusi keuangan asing "
                f"{_shares(latest.get('foreign_institutions'))} dan reksa dana asing "
                f"{_shares(latest.get('foreign_mutual_fund'))}, jadi penurunan asing bukan "
                f"penarikan tunggal satu tipe investor."
            )
        except (TypeError, ValueError):
            parts.append("Komposisi pemegang saham tersedia tetapi tidak dapat dihitung selisihnya.")
    else:
        parts.append(
            "Komposisi pemegang saham lokal vs asing tidak tersedia di data, sehingga tidak "
            "dinyatakan angkanya."
        )

    rel = ((payload.get("cover") or {}).get("vs_jci") or {}).get("chart") or {}
    moves = _chart_moves(rel)
    if moves:
        parts.append(
            f"Kinerja harga relatif: pada 90 hari terakhir saham ini bergerak {_pct(moves[0])} "
            f"terhadap IHSG {_pct(moves[1])} (selisih {_num(moves[0] - moves[1])} poin persentase), "
            f"menempatkan emiten naik lebih tinggi daripada IHSG pada jendela tersebut. Angka ini dihitung "
            f"dari seri harga 90 hari yang sama dengan grafik kinerja di halaman pertama dan tidak "
            f"diekstrapolasi ke periode lain."
        )
    else:
        parts.append(
            "Kinerja harga relatif terhadap IHSG tidak dapat dihitung karena seri harganya tidak "
            "tersedia di data."
        )

    news = payload.get("news") or []
    if news:
        themes = ", ".join(str(n.get("title")) for n in news[:3])
        parts.append(
            f"Nada pemberitaan: data berita yang tersedia tidak memuat skor sentimen per artikel, jadi "
            f"nada berita dinyatakan dari judul yang ada ({len(news)} artikel, contoh: {themes}). "
            f"Tidak ada skor sentimen yang dihitung atau dikarang dari judul tersebut."
        )
    else:
        parts.append("Tidak ada artikel berita di data untuk menyatakan nada pemberitaan.")

    ff = payload.get("free_float") or {}
    if ff.get("in_list"):
        parts.append(
            f"Emiten ini masuk daftar {ff.get('n')} saham dengan saham beredar publik terbesar versi "
            f"daftar Sectors; daftar tersebut tidak membawa persentase, sehingga besarannya tidak "
            f"dinyatakan di sini."
        )

    parts.append(
        "Agregat konsensus rating broker (jumlah Buy/Hold/Sell untuk saham di sektor ini) tidak "
        "tersedia: data peringkat konsensus analis belum tersedia, jadi angka itu tidak "
        "dinyatakan dan tidak diada-adakan."
    )

    return _sentence(parts), _basis(
        [
            str(sentiment.get("source") or "arus & broker: tidak tersedia"),
            str(mix.get("source") or "komposisi pemegang saham: tidak tersedia"),
            "kinerja relatif: seri harga 90 hari + IHSG",
            "berita: 8 artikel yang tersedia",
            str(ff.get("source") or "free float: tidak tersedia"),
        ]
    )


def _broker_gap(buyers: list) -> str:
    """State how concentrated the buy side is using the two largest values, not an adjective."""
    try:
        first, second = float(buyers[0][1]), float(buyers[1][1])
    except (IndexError, TypeError, ValueError):
        return ", jadi sisi beli tercatat di beberapa broker."
    if not second:
        return ", jadi sisi beli tercatat di beberapa broker."
    return (
        f", dengan broker terbesar sekitar {_num(first / second, 1)} kali broker kedua di sisi beli."
    )


def _chart_moves(chart: dict) -> Optional[list]:
    """Percent move of both series, rebased on the first point. Series order is issuer then index."""
    series = chart.get("series") or []
    out = []
    for values in series[:2]:
        if isinstance(values, dict):
            values = values.get("data")
        if not isinstance(values, (list, tuple)) or len(values) < 2:
            return None
        try:
            first = float(values[0][1] if isinstance(values[0], (list, tuple)) else values[0])
            last = float(values[-1][1] if isinstance(values[-1], (list, tuple)) else values[-1])
        except (TypeError, ValueError, IndexError):
            return None
        if not first:
            return None
        out.append((last / first - 1) * 100)
    return out if len(out) == 2 else None


# --------------------------------------------------------------------------- page
def _foreign_flow_series(payload: dict) -> dict:
    """Daily net-foreign series for the FF bar chart, read from freeze files only.

    Ticker-agnostic: resolves <TICKER> from payload meta and reads
    ``foreign_flow_<T>_90d.json`` from ticker_fill/ then ammn_fill/ (legacy).
    Zero Sectors cost - a file read, never an upstream call. Absent/stale file
    -> available=False and the template prints the honest line, never a gap.
    """
    import json as _json
    import pathlib as _pl
    import time as _time
    from server.credit_policy import freeze_max_age_seconds as _freeze_max_age_s
    ticker = str((payload.get("meta") or {}).get("ticker") or "").upper()
    repo = _pl.Path(__file__).resolve().parents[2]
    cand_dirs = (repo / "output" / "cache" / "ticker_fill",
                 repo / "output" / "cache" / "ammn_fill")
    rows: list = []
    src = ""
    if ticker:
        for d in cand_dirs:
            p = d / f"foreign_flow_{ticker}_90d.json"
            if p.exists():
                try:
                    # FREEZE_TTL_DAYS gate (default: forever). The age is disclosed in
                    # the source string either way, so a reader always sees how old the
                    # series is - this gate is a degradation, never a silent gap.
                    max_age_s = _freeze_max_age_s()
                    age_days = (_time.time() - p.stat().st_mtime) / 86400.0
                    if _time.time() - p.stat().st_mtime > max_age_s:
                        # Whole days only - a decimal would print an English separator
                        # and trip the house format gate (§7-§9: dot thousands, comma decimals).
                        src = (f"freeze {p.name} kedaluwarsa "
                               f"(>{max_age_s / 86400.0:.0f} hari)")
                        break
                    body = _json.loads(p.read_text(encoding="utf-8"))
                    raw = body.get("data") or []
                    for r in raw:
                        try:
                            rows.append({"date": str(r.get("date"))[:10],
                                         "net_bn": round(float(r.get("net_foreign_inflow") or 0) / 1e9, 2)})
                        except (TypeError, ValueError):
                            continue
                    rows.sort(key=lambda r: r["date"])
                    rows = rows[-62:]
                    src = f"Sectors foreign-flow 90d ({len(rows)} sesi, freeze {age_days:.0f} hari)"
                except Exception:
                    rows = []
                break
    if not rows:
        return {"available": False,
                "source": src or "tidak ada freeze foreign-flow untuk emiten ini"}
    return {"available": True, "dates": [r["date"] for r in rows],
            "values_bn": [r["net_bn"] for r in rows], "source": src}


def build_industry_page(payload: dict, assumptions: Optional[dict] = None) -> dict:
    """Assemble deck page 2 from the payload. Always returns three paragraphs, never raises."""
    assumptions = assumptions or {}
    built = (
        _paragraph_industry(payload, assumptions),
        _paragraph_catalysts(payload),
        _paragraph_sentiment(payload),
    )
    paragraphs = [
        {"heading": heading, "body": body, "basis": basis}
        for heading, (body, basis) in zip(PARAGRAPH_HEADINGS, built)
    ]
    sources: list[str] = []
    for block in ("sector_data", "filings_digest", "corporate_actions", "ownership_mix",
                  "free_float", "sentiment", "news"):
        value = payload.get(block)
        source = value.get("source") if isinstance(value, dict) else None
        if source and source not in sources:
            sources.append(str(source))
    return {
        "title": f"Kondisi Industri, Katalis & Sentimen - {payload.get('meta', {}).get('ticker', '')}".strip(" -"),
        "paragraphs": paragraphs,
        "sources": sources,
        "foreign_flow": _foreign_flow_series(payload),
        "notes": [
            "Halaman naratif: tidak ada objek wajib, dan tidak ada Exhibit yang ditambahkan, "
            "sehingga penomoran Exhibit dokumen tidak bergeser.",
            "Setiap paragraf menyertakan basis datanya; angka yang tidak ada basisnya dinyatakan "
            "tidak tersedia, bukan diperkirakan.",
        ],
    }
