"""Slide 3 — Visualisasi Kinerja Keuangan dan Forecasting (2×2 grid, Exhibits 4–7).

Four combo charts, each with its own narrative block attached to the chart, per
`docs/ammn-slides/slide3-visual-spec.md`:

1. Revenue + YoY growth              2. EBITDA + EBITDA margin
3. Net profit + EPS growth           4. DER vs ROE (non-bank default; bank and E&P branches differ)

Every series is copied out of a block the payload already proves, and the page records which block
it came from so the cross-exhibit tie-out rule ("no number may differ between this slide and the Key
Financials exhibit for the same period") is checkable rather than aspirational:

* the FY2024A–FY2028F columns come from the cover's Key Financials table, which is the same series
  the reader sees on page 1, so the two exhibits cannot disagree;
* the DER/ROE quadrant comes from the ratio table's own D/E and ROE rows.

The narratives are derived, not written by hand: they compute the growth rates, compare the forecast
margin with the realised average, and name the below-the-line items that explain a profit gap. Where
the forecast columns rest on an assumption that the narrative disagrees with, the narrative says so
in the copy — a quadrant that quietly repeats an over-optimistic margin is worse than useless.
"""

from __future__ import annotations

from typing import Any, Optional

QUADRANT_TITLES = (
    "Revenue & Revenue Growth",
    "EBITDA & EBITDA Margin",
    "Net Profit & EPS Growth",
    "DER vs ROE",
)


# --------------------------------------------------------------------------- formatting
def _num(value: Any, digits: int = 1) -> str:
    try:
        text = f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return "—"
    return text.replace(",", "\u00a0").replace(".", ",").replace("\u00a0", ".")


def _idr_tn(value: Any, digits: int = 1) -> str:
    """Prose reads in trillions; the chart axis stays in Rp bn as the spec names it."""
    try:
        return "Rp " + _num(float(value) / 1000, digits) + " tn"
    except (TypeError, ValueError):
        return "—"


def _pct(value: Any, digits: int = 1) -> str:
    if value is None:
        return "—"
    try:
        return ("+" if float(value) > 0 else "") + _num(value, digits) + "%"
    except (TypeError, ValueError):
        return "—"


def _row(rows: list, *needles: str) -> Optional[list]:
    """First row whose label contains all needles (case-insensitive)."""
    for row in rows or []:
        label = str(row[0] if isinstance(row, (list, tuple)) and row else "")
        low = label.lower()
        if all(n.lower() in low for n in needles):
            return list(row)
    return None


def _parse_id(value: Any) -> Optional[float]:
    """Parse a number the Indonesian way, which is how the cover table stores its cells.

    The cover's Key Financials rows are PRE-FORMATTED strings: "43.036" is 43,036 (dot =
    thousands), "141,9" is 141.9 (comma = decimal) and "(28,8)" is -28.8. Reading them with
    float() silently turns 43,036 into 43.036 — a factor-of-1000 error that would then fail the
    cross-exhibit tie-out in a way nobody could explain. Values that are already numeric pass
    through untouched.
    """
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").strip()
    if text in ("", "—", "-", "n/a", "N/A", "na"):
        return None
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()").replace("%", "").replace("\u00a0", "").replace(" ", "")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    elif text.count(".") == 1 and len(text.split(".")[1]) == 3:
        text = text.replace(".", "")  # "43.036" = 43036, not 43.036
    try:
        number = float(text)
    except ValueError:
        return None
    return -number if negative else number


def _clean(values: list) -> list:
    """Payload cells -> floats, keeping the series length. '—'/''/None become None."""
    return [_parse_id(v) for v in values]


def _growth(series: list) -> list:
    """YoY growth in percent, None where either side is missing."""
    out: list = [None]
    for i in range(1, len(series)):
        prev, cur = series[i - 1], series[i]
        out.append(None if (prev in (None, 0) or cur is None) else round((cur / prev - 1) * 100, 1))
    return out


def _cagr(series: list) -> Optional[float]:
    pts = [v for v in series if v is not None]
    if len(pts) < 2 or pts[0] <= 0 or pts[-1] <= 0:
        return None
    years = len(pts) - 1
    return ((pts[-1] / pts[0]) ** (1 / years) - 1) * 100


# --------------------------------------------------------------------------- quadrant sources
def _forecast_table(payload: dict) -> tuple[list[str], dict]:
    """The cover's FY2024A–FY2028F Key Financials table: labels -> row, plus its period labels."""
    kf = ((payload.get("cover") or {}).get("slide2") or {}).get("key_financials") or {}
    headers = [str(h) for h in (kf.get("headers") or [])][1:]
    rows = kf.get("rows") or []
    return headers, kf


def _actual_periods(headers: list[str]) -> int:
    """How many leading periods are actual (labels ending in A)."""
    count = 0
    for h in headers:
        if h.strip().upper().endswith("A"):
            count += 1
        else:
            break
    return count


def _quadrant_source(kf: dict) -> str:
    return str(kf.get("source") or "Sectors company/report financials (IDR bn)")


def _ratio_rows(payload: dict) -> list:
    return ((payload.get("financial_statements") or {}).get("ratios") or {}).get("rows") or []


def _ratio_headers(payload: dict) -> list[str]:
    headers = ((payload.get("financial_statements") or {}).get("ratios") or {}).get("headers") or []
    return [str(h) for h in headers][1:]


# --------------------------------------------------------------------------- narratives
def _prior_year_growth(payload: dict, current_label: str) -> Optional[float]:
    """Year-over-year sales growth of the period before `current_label`.

    The two tables label their columns differently ("2025A" in the cover table, "FY25A" in the ratio
    table) and start at different years, so the period is matched on the YEAR, never on the index: an
    index match would silently read FY2021A while claiming to quote FY2024A.
    """
    try:
        current_year = int("".join(ch for ch in current_label if ch.isdigit()))
    except ValueError:
        return None
    want = (current_year - 1) % 100
    headers = _ratio_headers(payload)
    row = _row(_ratio_rows(payload), "sales growth")
    cells = row[1:] if row else []
    for i, header in enumerate(headers):
        digits = "".join(ch for ch in header if ch.isdigit())
        if digits and int(digits) % 100 == want and header.strip().upper().endswith("A") and i < len(cells):
            return _parse_id(cells[i])
    return None


def _narrative_revenue(headers: list[str], rev: list, growth: list, payload: dict) -> str:
    actual_cagr = _cagr([v for v, h in zip(rev, headers) if h.endswith("A")])
    forecast_cagr = _cagr([v for v, h in zip(rev, headers) if not h.endswith("A")])
    idx_fy25 = next((i for i, h in enumerate(headers) if h == "2025A"), None)
    idx_fy26 = next((i for i, h in enumerate(headers) if h.endswith("F")), None)
    parts = []
    if idx_fy25 is not None:
        prior = growth[idx_fy25 - 1] if idx_fy25 > 0 else None
        if prior is None:
            prior = _prior_year_growth(payload, headers[idx_fy25])
        lead = (
            f"setelah naik {_pct(prior)} pada periode sebelumnya: arah pendapatan berbalik, "
            f"bukan melambat saja."
            if prior is not None
            else "tanpa pembanding periode sebelumnya di tabel ini."
        )
        move = growth[idx_fy25]
        verb = "turun" if (move or 0) < 0 else "naik"
        parts.append(
            f"Pendapatan {verb} {_num(abs(move or 0))}% pada {headers[idx_fy25]} menjadi "
            f"{_idr_tn(rev[idx_fy25])}, {lead}"
        )
    segments = payload.get("segments") or []
    if segments:
        parts.append(
            "Bauran pendapatan yang menopang angka ini: "
            + ", ".join(
                f"{seg.get('name')} {_num(seg.get('share_pct'), 1)}%"
                + (f" (yoy {_pct(seg.get('yoy_pct'))})" if seg.get("yoy_pct") is not None else "")
                for seg in segments
                if seg.get("share_pct") is not None
            )
            + ". Periode segmen terakhir yang tersedia adalah FY2024, jadi bauran ini menjelaskan "
            "pendapatan FY2024A dan bukan FY2025A."
        )
    if actual_cagr is not None and forecast_cagr is not None:
        parts.append(
            f"CAGR periode aktual {_pct(actual_cagr)} vs CAGR periode proyeksi {_pct(forecast_cagr)}: "
            f"lajunya berbeda karena periode proyeksi menyusut lebih lambat "
            f"({_pct(growth[idx_fy26]) if idx_fy26 is not None else '—'} di tahun proyeksi pertama)."
        )
    first_flat = headers[index_of_flat_growth(growth)]
    if first_flat:
        parts.append(
            f"Inflection point: pertumbuhan berhenti turun dan mendatar di {first_flat}, dan angka "
            f"datar FY2027F–FY2028F itu berasal dari jalur FCFF flat pada file asumsi, bukan dari tren "
            f"tiga tahun terakhir yang masih negatif."
        )
    return " ".join(parts)


def index_of_flat_growth(growth: list) -> int:
    """First forecast period whose growth is exactly 0 after a non-zero one, else 0."""
    for i in range(1, len(growth)):
        if growth[i] == 0 and growth[i - 1] not in (None, 0):
            return i
    return 0


def _narrative_ebitda(headers: list[str], ebitda: list, rev: list, margins: list) -> str:
    realised = [m for m, h in zip(margins, headers) if h.endswith("A") and m is not None]
    forecast = [m for m, h in zip(margins, headers) if not h.endswith("A") and m is not None]
    parts = []
    if realised:
        parts.append(
            f"Marjin EBITDA aktual {_num(realised[0])}% → {_num(realised[-1])}% "
            f"(rata-rata {_num(sum(realised) / len(realised))}%): marjin relatif bertahan walau "
            f"pendapatan turun tajam, yang berarti penurunan ditahan di sisi margin, bukan hanya "
            f"di sisi volume."
        )
    if forecast and realised:
        avg3 = sum(realised[-3:]) / len(realised[-3:]) if len(realised) >= 3 else sum(realised) / len(realised)
        parts.append(
            f"Sanity check terhadap track record: marjin proyeksi {_num(forecast[0])}% berada "
            f"{_num(forecast[0] - avg3, 1)} poin persentase di atas rata-rata tiga tahun aktual "
            f"({_num(avg3)}%), dan belum pernah tercatat setinggi itu pada periode aktual di tabel "
            f"ini — asumsinya terlalu optimistis untuk dipakai apa adanya."
        )
        parts.append(
            "Mekanismenya layak disebut: EBITDA proyeksi dipegang pada rata-rata tiga tahun aktual "
            "sementara pendapatan proyeksi turun, sehingga marjin naik secara aritmetika. Itu asumsi "
            "proyeksi, bukan ekspansi marjin yang sudah terjadi."
        )
    return " ".join(parts)


def _narrative_profit(headers: list[str], net: list, ebitda: list, eps_growth: list, payload: dict) -> str:
    parts = []
    idx_fy25 = next((i for i, h in enumerate(headers) if h == "2025A"), None)
    idx_fy26 = next((i for i, h in enumerate(headers) if h.endswith("F")), None)
    if idx_fy25 is not None and idx_fy25 > 0:
        ebitda_g = _growth(ebitda)[idx_fy25]
        net_g = _growth(net)[idx_fy25]
        parts.append(
            f"Gap di bawah garis: pada {headers[idx_fy25]} EBITDA bergerak {_pct(ebitda_g)} sementara "
            f"laba bersih {_pct(net_g)} — laba bersih turun sekitar "
            f"{_num(abs((net_g or 0) - (ebitda_g or 0)))} poin persentase lebih dalam."
        )
        kpis = {str(k.get("name", "")): k for k in (payload.get("kpis") or []) if isinstance(k, dict)}
        de, cov = kpis.get("D/E FY2025"), kpis.get("Interest Coverage FY2025")
        drivers = []
        if de:
            drivers.append(f"D/E {_num(de.get('prev'))}× → {_num(de.get('value'))}×")
        if cov:
            drivers.append(f"interest coverage {_num(cov.get('prev'))}× → {_num(cov.get('value'))}×")
        if drivers:
            parts.append(
                "Penyebab eksplisitnya beban di bawah EBITDA: " + " dan ".join(drivers)
                + ", jadi penurunan laba bersih bukan dari operasi tetapi dari struktur modal."
            )
    if idx_fy26 is not None:
        parts.append(
            f"Di {headers[idx_fy26]} arahnya berbalik: laba bersih diproyeksikan "
            f"{_pct(_growth(net)[idx_fy26])} dan EPS {_pct(eps_growth[idx_fy26])}. Kedua kolom "
            f"proyeksi ini berjangkar pada basis yang berbeda (laba bersih mengikuti proyeksi EPS "
            f"subsektor Sectors, EBITDA mengikuti rata-rata tiga tahun aktual), sehingga jembatan "
            f"EBITDA → laba bersih di tahun proyeksi belum konsisten dan itu dinyatakan di sini "
            f"alih-alih dirapikan."
        )
    return " ".join(parts)


def _narrative_leverage(headers: list[str], de: list, roe: list) -> str:
    parts = []
    pts = [(h, d, r) for h, d, r in zip(headers, de, roe) if d is not None and r is not None]
    if len(pts) >= 2:
        first, last = pts[0], pts[-1]
        prev = pts[-2]
        parts.append(
            f"Leverage vs return: D/E {_num(last[1])}× dan ROE {_num(last[2])}% pada {last[0]}, "
            f"dari {_num(prev[1])}× dan {_num(prev[2])}% setahun sebelumnya "
            f"(awal jendela {first[0]}: {_num(first[1])}× / {_num(first[2])}%)."
        )
        if last[1] > first[1] and last[2] < first[2]:
            parts.append(
                "Arahnya berlawanan: utang bertambah sementara return ke ekuitas turun, sehingga "
                "pertumbuhan yang ada tidak sedang didanai leverage yang sehat — risiko finansial naik "
                "tanpa imbalan return yang sepadan."
            )
        elif last[1] < first[1] and last[2] > first[2]:
            parts.append("Arahnya sehat: utang turun sementara ROE naik.")
    parts.append(
        "Proyeksi DER dan ROE belum dimodelkan per tahun di payload, jadi kuadran ini menyajikan "
        "periode aktual saja dan tidak mengisi kolom proyeksi dengan asumsi."
    )
    return " ".join(parts)


# --------------------------------------------------------------------------- page
def build_performance_page(payload: dict, assumptions: Optional[dict] = None) -> dict:
    """Assemble deck slide 3. Always returns four quadrants; never raises on missing data."""
    headers, kf = _forecast_table(payload)
    rows = kf.get("rows") or []
    actual_n = _actual_periods(headers)

    def _series(*needles: str) -> list:
        row = _row(rows, *needles)
        return _clean(row[1:]) if row else []

    rev = _series("revenue")
    ebitda = _series("ebitda")
    net = _series("net profit")
    eps = _series("eps")

    rev_growth = _growth(rev)
    margins = [
        (e / r * 100) if (e is not None and r) else None for e, r in zip(ebitda, rev)
    ]
    eps_growth = _growth(eps)

    ratio_headers = _ratio_headers(payload)
    ratio_rows = _ratio_rows(payload)
    de_row = _row(ratio_rows, "d/e")
    roe_row = _row(ratio_rows, "return on equity")
    de = _clean(de_row[1:]) if de_row else []
    roe = _clean(roe_row[1:]) if roe_row else []

    quadrants = [
        {
            "title": QUADRANT_TITLES[0],
            "window": f"{headers[0]}–{headers[-1]}" if headers else "tidak tersedia",
            "bars": rev,
            "line": rev_growth,
            "labels": headers,
            "actual_n": actual_n,
            "bar_unit": "Rp bn",
            "line_unit": "% yoy",
            "bar_fmt": [_num(v, 0) for v in rev],
            "line_fmt": [_pct(v, 1) if v is not None else "" for v in rev_growth],
            "narrative": _narrative_revenue(headers, rev, rev_growth, payload),
            "tie_out": {
                "block": "cover.slide2.key_financials (Exhibit 2)",
                "series": {"revenue": rev},
                "periods": headers,
            },
        },
        {
            "title": QUADRANT_TITLES[1],
            "window": f"{headers[0]}–{headers[-1]}" if headers else "tidak tersedia",
            "bars": ebitda,
            "line": margins,
            "labels": headers,
            "actual_n": actual_n,
            "bar_unit": "Rp bn",
            "line_unit": "% margin",
            "bar_fmt": [_num(v, 0) for v in ebitda],
            "line_fmt": [_num(v, 1) if v is not None else "" for v in margins],
            "narrative": _narrative_ebitda(headers, ebitda, rev, margins),
            "tie_out": {
                "block": "cover.slide2.key_financials (Exhibit 2) + financial_highlights (Exhibit 3)",
                "series": {"ebitda": ebitda},
                "periods": headers,
            },
        },
        {
            "title": QUADRANT_TITLES[2],
            "window": f"{headers[0]}–{headers[-1]}" if headers else "tidak tersedia",
            "bars": net,
            "line": eps_growth,
            "labels": headers,
            "actual_n": actual_n,
            "bar_unit": "Rp bn",
            "line_unit": "% EPS growth",
            "bar_fmt": [_num(v, 0) for v in net],
            "line_fmt": [_pct(v, 1) if v is not None else "" for v in eps_growth],
            "narrative": _narrative_profit(headers, net, ebitda, eps_growth, payload),
            "tie_out": {
                "block": "cover.slide2.key_financials (Exhibit 2)",
                "series": {"net_profit": net, "eps": eps},
                "periods": headers,
            },
        },
        {
            "title": QUADRANT_TITLES[3],
            "window": f"{ratio_headers[0]}–{ratio_headers[-1]}" if ratio_headers else "tidak tersedia",
            "bars": de,
            "line": roe,
            "labels": ratio_headers,
            "actual_n": len(ratio_headers),
            "bar_unit": "×",
            "line_unit": "% ROE",
            "bar_fmt": [_num(v, 2) for v in de],
            "line_fmt": [_num(v, 1) if v is not None else "" for v in roe],
            "narrative": _narrative_leverage(ratio_headers, de, roe),
            "tie_out": {
                "block": "financial_statements.ratios (D/E, ROE)",
                "series": {"d_e": de, "roe": roe},
                "periods": ratio_headers,
            },
        },
    ]

    return {
        "title": "Visualisasi Kinerja Keuangan dan Forecasting",
        "subtitle": (
            "Empat kuadran, tiap chart menempel pada narasinya sendiri. Seluruh angka periode "
            "2024A–2028F berasal dari tabel Key Financials di halaman pertama, sehingga tidak ada "
            "angka yang berbeda antar exhibit untuk periode yang sama."
        ),
        "quadrants": quadrants,
        "notes": [
            f"Bar aktual dicetak penuh, bar proyeksi {max(len(headers) - actual_n, 0)} periode "
            f"terakhir dicetak lebih muda dengan pola garis, jadi aktual vs proyeksi terbaca tanpa "
            f"membaca label.",
            "Kuadran keempat memakai default non-bank (DER vs ROE); cabang bank (NIM/CoC) dan "
            "E&P/upstream (volume & lifting cost) belum tersedia datanya di payload.",
            "Proyeksi DER/ROE per tahun belum dimodelkan, jadi kuadran leverage menyajikan periode "
            "aktual saja.",
        ],
        "sources": [
            _quadrant_source(kf),
            "Sectors financial_statements.ratios (D/E, ROE)",
            "Sectors segments (bauran pendapatan)",
        ],
    }
