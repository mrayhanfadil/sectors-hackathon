"""Report data fixtures — sample payloads for the 4 templates (T10).

These are DEMO payloads mirroring the benchmark archetypes (RATU single / CDIA sotp /
MTEL infra / JPM strategy). They exist so the renderer + templates can be exercised
end-to-end before the Data Collector lane (T01) ships real data.

All numbers mirror the public benchmark PDFs documented in plan.md §2 — provenance per
exhibit is carried explicitly. No fabricated live data: figures are illustrative of the
ARCHETYPE STRUCTURE, not presented as current market facts.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMPTIONS = HERE.parent / "data" / "assumptions"
FIXTURES = HERE / "fixtures"


def _build_cdcf(ticker: str) -> dict:
    """Friend-style DCF output (Abida Massi port) from data/assumptions/{ticker}.json.

    Returns wacc_table + sensitivity + scenarios + valuation + recommendation in the
    shape consumed by templates/report_infra.html Friend-Style DCF block. Empty dict
    if the engine can't run (graceful fallback so PDF render doesn't crash).
    """
    try:
        sys_mod = __import__("sys")
        if str(HERE) not in sys_mod.path:
            sys_mod.path.insert(0, str(HERE))
        from dcf_engine import dcf_full  # noqa: PLC0415

        out = dcf_full(ticker)
        if not isinstance(out, dict) or "error" in out:
            return {"_engine_unavailable": True, "_ticker": ticker, "_raw": out}
        return out
    except Exception as exc:  # noqa: BLE001
        return {"_engine_unavailable": True, "_ticker": ticker, "_error": str(exc)}

def get_fy_years_from_assumptions(ticker: str) -> list[str]:
    """Dynamically determine 6-year standardization (2 actual + 4 forecast) from assumptions.

    Determines current year dynamically from most recent data point in data/assumptions/{ticker}.json
    (e.g., provenance.latest_time, provenance.release_date, generated_at).
    Standardizes sequence to:
      - FY-1A (e.g. FY24A, prior year actual)
      - FY0A (e.g. FY25A, current year actual)
      - FY+1F (e.g. FY26F)
      - FY+2F (e.g. FY27F)
      - FY+3F (e.g. FY28F)
      - FY+4F (e.g. FY29F)
    """
    assum_file = ASSUMPTIONS / f"{ticker.upper()}.json"
    year = 2026
    if assum_file.exists():
        try:
            d = json.loads(assum_file.read_text(encoding="utf-8"))
            prov = d.get("provenance") or {}
            raw_time = prov.get("latest_time") or prov.get("release_date") or d.get("generated_at") or ""
            import re
            m = re.search(r"(20\d\d)", str(raw_time))
            if m:
                year = int(m.group(1))
        except Exception:
            year = 2026

    base_year = year - 1  # current year actual FY0A (last completed fiscal year)
    y_m1 = base_year - 1
    y0 = base_year
    y_p1 = base_year + 1
    y_p2 = base_year + 2
    y_p3 = base_year + 3
    y_p4 = base_year + 4
    return [
        f"FY{str(y_m1)[-2:]}A",
        f"FY{str(y0)[-2:]}A",
        f"FY{str(y_p1)[-2:]}F",
        f"FY{str(y_p2)[-2:]}F",
        f"FY{str(y_p3)[-2:]}F",
        f"FY{str(y_p4)[-2:]}F",
    ]


# months labels used by price charts
MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agt", "Sep", "Okt", "Nov", "Des"]


def ratu_single() -> dict:
    """RATU archetype — pure-play oil holding, 9 sections (plan §2.1)."""
    return {
        "meta": {
            "template": "single", "reason": "segments=0, subsector=oil-pure-play -> single",
            "ticker": "RATU", "company_name": "Raharja Energi Cepu",
            "sector": "Energi — Pure-Play Holding", "report_type": "Initiation",
            "date": "31 Agt 2026", "prepared_by": "RESEARCH — Sectors Hackathon 2026", "language": "id",
        },
        "cover": {
            "rating_box": {"action": "BUY", "tp": 7880, "prev_tp": None, "price": 6200,
                           "upside_pct": 27.1, "key_takeaways": []},
            "vs_jci": {"ytd_abs": 18.4, "ytd_rel": 6.2,
                        "source": "Sectors API v2",
                        "chart": {"labels": MONTHS,
                                   "series": [[0, 4, 9, 12, 15, 18, 21, 19, 22, 24, 26, 27],
                                              [0, 2, 5, 6, 8, 9, 11, 12, 12, 13, 14, 15]]}},
            "shares": {"outstanding": 2.71, "unit": "bn", "free_float_pct": 31.2},
            "shareholders": [{"name": "Publik", "pct": 31.2}, {"name": "RETJ", "pct": 45.0},
                              {"name": "PJUC", "pct": 23.8}],
            "shareholders_src": "IDX — struktur pemegang saham",
            "esg": {"found": False},
        },
        "financial_highlights": {
            "source": "Laporan keuangan RATU (IDX), data diolah",
            "years": get_fy_years_from_assumptions("RATU"),
            "rows": [
                ["Pendapatan (Rp bn)", 1290, 1122, 1180, 1240, 1300, 1365],
                ["EBITDA (Rp bn)", 610, 540, 585, 615, 645, 678],
                ["Net profit (Rp bn)", 402, 355, 390, 410, 430, 452],
                ["P/E (x)", 129.0, 55.2, 42.7, 38.5, 34.8, 31.5],
                ["ROE (%)", 88.0, 41.0, 30.0, 27.5, 25.0, 23.0],
            ],
        },
        "segments": [],
        "kpis": [
            {"name": "Produksi Cepu", "value": 169, "prev": 152, "unit": "k BOPD",
             "formula": "produksi harian rata-rata", "source": "SKK Migas",
             "row": ["Produksi Cepu", 169, 152, "+17", "k BOPD", "rata-rata harian", "SKK Migas"]},
        ],
        "kpis_src": "SKK Migas, laporan bulanan lapangan",
        "thesis": [
            {"headline": "Bottom line tahan meski revenue turun",
             "detail": "Margin net profit naik dari 31% ke 32% karena efisiensi opex dan hedge kurs.",
             "source": "Laporan keuangan FY24-25 (IDX)"},
            {"headline": "Cepu 169k BOPD jadi mesin kas",
             "detail": "Kontribusi lapangan Cepu mendominasi produksi dengan biaya lifting rendah.",
             "source": "SKK Migas"},
            {"headline": "Regulasi PSC/DMO terkendali",
             "detail": "Struktur kontrak PSC existing melindungi ekonomi lapangan hingga 2031.",
             "source": "Kontrak PSC (KKKS)"},
            {"headline": "Naturally declining base dikelola via workover",
             "detail": "Program workover rutin menahan decline rate ~8%/tahun.",
             "source": "Laporan manajemen"},
        ],
        "valuation": {
            "methods": [
                {"method": "DCF", "fv": 7880,
                 "assumptions": {"wacc": 8.4, "beta": 0.7, "rf": 6.2, "erp": 6.9, "coe": 10.0,
                                  "cod": 3.5, "we": 85.0, "wd": 15.0, "g": 5.0},
                 "table": {"headers": ["Item", "FY26F", "FY27F", "FY28F", "FY29F"],
                           "rows": [["FCF (Rp bn)", 410, 432, 455, 480],
                                    ["Discount factor", 0.92, 0.85, 0.78, 0.72],
                                    ["PV (Rp bn)", 377, 367, 355, 346]]},
                 "source": "scripts/dcf.py"},
                {"method": "EV/EBITDA", "fv": 6960,
                 "assumptions": {"multiple": 22.6},
                 "table": {"headers": ["Item", "Nilai"],
                           "rows": [["EV/EBITDA target (x)", 22.6],
                                    ["EBITDA FY26F (Rp bn)", 585],
                                    ["EV (Rp bn)", 13221]]},
                 "source": "scripts/ev_ebitda.py"},
            ],
            "blended": None,
            "bands": None,
        },
        "financials": [
            {"title": "Laba Rugi Ringkas",
             "headers": ["Rp bn"] + get_fy_years_from_assumptions("RATU"),
             "rows": [["Pendapatan", 1290, 1122, 1180, 1240, 1300, 1365],
                      ["HPP", -520, -470, -492, -515, -540, -567],
                      ["EBITDA", 610, 540, 585, 615, 645, 678],
                      ["Laba bersih", 402, 355, 390, 410, 430, 452]],
             "source": "Laporan keuangan IDX"},
            {"title": "Rasio Kunci",
             "headers": ["Rasio"] + get_fy_years_from_assumptions("RATU") + ["Peer Median"],
             "rows": [["ROE (%)", 88.0, 41.0, 30.0, 27.5, 25.0, 23.0, 22.0],
                      ["DER (x)", 0.21, 0.24, 0.22, 0.20, 0.18, 0.17, 0.45],
                      ["Interest coverage (x)", 14.2, 11.8, 12.4, 13.0, 13.5, 14.0, 8.5]],
             "source": "Laporan keuangan IDX"},
        ],
        "risks": [
            {"bucket": "Risiko Komoditas", "detail": "Harga minyak flektuatif mempengaruhi realisasi.",
             "source": "Laporan keuangan"},
            {"bucket": "Risiko Operator", "detail": "Ketergantungan pada operator lapangan.", "source": None},
            {"bucket": "Regulasi PSC/DMO", "detail": "Perubahan ketentuan domestic market obligation.", "source": None},
            {"bucket": "Natural decline", "detail": "Penurunan produksi basis legacy.", "source": None},
        ],
        "peers": {"tables": [
            {"pillar": "Peers energi IDX",
             "headers": ["Ticker", "P/E", "EV/EBITDA", "ROE"],
             "rows": [["MEDC", 8.9, 4.2, 22.0],
                      ["ENRG", 12.4, 5.1, 15.0],
                      ["RATU", 42.7, 22.6, 30.0],
                      ["Rata-rata", 21.3, 10.6, 22.3],
                      ["Median", 12.4, 5.1, 22.0]],
             "source": "Sectors — data historis"},
        ]},
        "news": [],
        "sentiment": None,
        "strategy": None,
        "catalysts": [],
        "exhibits": [
            {"id": "Exhibit 4", "title": "Tren Pendapatan & EBITDA",
             "chart": {"type": "bar", "height": 190,
                        "data": {"labels": get_fy_years_from_assumptions("RATU"),
                                  "datasets": [{"label": "Pendapatan (Rp bn)", "data": [1290, 1122, 1180, 1240, 1300, 1365]},
                                                {"label": "EBITDA (Rp bn)", "data": [610, 540, 585, 615, 645, 678]}]}},
             "source": "Laporan keuangan IDX"},
            {"id": "Exhibit 5", "title": "Trajektori Leverage (DER)",
             "chart": {"type": "line", "height": 170,
                        "data": {"labels": get_fy_years_from_assumptions("RATU"),
                                  "datasets": [{"label": "DER (x)", "data": [0.21, 0.24, 0.22, 0.20, 0.18, 0.17]}]}},
             "source": "Laporan keuangan IDX"},
        ],
    }


def cdia_sotp() -> dict:
    """CDIA archetype — conglomerate 4-pilar, 10 sections (plan §2.2)."""
    return {
        "meta": {
            "template": "sotp", "reason": "segments=4 > 1 -> sotp",
            "ticker": "CDIA", "company_name": "Chandra Daya Investasi",
            "sector": "Konglomerasi — Energi/Logistik/Air/Pelabuhan", "report_type": "Initiation",
            "date": "31 Agt 2026", "prepared_by": "RESEARCH — Sectors Hackathon 2026", "language": "id",
        },
        "cover": {
            "rating_box": {"action": "HOLD", "tp": 815, "prev_tp": None, "price": 780,
                           "upside_pct": 4.5, "key_takeaways": []},
            "vs_jci": {"ytd_abs": -62.9, "ytd_rel": -30.9,
                        "source": "Sectors API v2",
                        "chart": {"labels": MONTHS,
                                   "series": [[0, -12, -28, -41, -50, -55, -60, -58, -61, -62, -63, -63],
                                              [0, 2, 5, 6, 8, 9, 11, 12, 12, 13, 14, 15]]}},
            "shares": {"outstanding": 15.0, "unit": "bn", "free_float_pct": 10.1},
            "esg": {"found": False},
        },
        "financial_highlights": {
            "source": "Laporan keuangan CDIA (IDX), data diolah",
            "years": get_fy_years_from_assumptions("CDIA"),
            "rows": [
                ["Pendapatan (Rp bn)", 14500, 15200, 11800, 12900, 14100, 15400],
                ["EBITDA (Rp bn)", 4900, 4300, 2100, 2800, 3200, 3700],
                ["Net profit (Rp bn)", 2800, 2100, 510, 890, 1150, 1420],
                ["ROE (%)", 12.0, 8.4, 1.9, 3.2, 4.0, 4.8],
            ],
        },
        "segments": [
            {"name": "Energi", "revenue": 6300, "yoy_pct": -8, "qoq_pct": -3, "share_pct": 53.4,
             "one_off": "Normalisasi one-off Rp 15.9 bn (gain penjualan aset) dikeluarkan dari segmen Energi.",
             "row": ["Energi", 6300, "-8%", "-3%", "53.4%"]},
            {"name": "Logistik", "revenue": 4010, "yoy_pct": 44.7, "qoq_pct": 12.0, "share_pct": 34.0,
             "row": ["Logistik", 4010, "+44.7%", "+12.0%", "34.0%"]},
            {"name": "Air", "revenue": 850, "yoy_pct": 6, "qoq_pct": 2, "share_pct": 7.2,
             "row": ["Air", 850, "+6%", "+2%", "7.2%"]},
            {"name": "Pelabuhan", "revenue": 640, "yoy_pct": 9, "qoq_pct": 4, "share_pct": 5.4,
             "row": ["Pelabuhan", 640, "+9%", "+4%", "5.4%"]},
        ],
        "segments_src": "Laporan segmentasi CDIA 1H26 (IDX)",
        "kpis": [],
        "thesis": [
            {"headline": "Logistik pilar tercepat (+44.7% YoY)",
             "detail": "Volume vessel dan TC/COA mix membaik, menjadi mesin pertumbuhan grup.",
             "source": "Laporan 1H26 (IDX)"},
            {"headline": "Normalisasi one-off bikin base FY26 rendah",
             "detail": "One-off Rp 15.9 bn di-normalize; earnings quality kini lebih bersih.",
             "source": "Laporan 1H26 (IDX)"},
            {"headline": "M&A delay 2H26 menekan revenue guidance",
             "detail": "Penundaan akuisisi menunda sinergi ke FY27.", "source": "Disclosure IDX"},
        ],
        "valuation": {
            "methods": [
                {"method": "DCF", "fv": 815,
                 "assumptions": {"wacc": 9.8, "beta": 1.05, "rf": 6.2, "erp": 7.4, "coe": 14.0,
                                  "cod": 5.5, "we": 70.0, "wd": 30.0, "g": 4.0},
                 "table": {"headers": ["Item", "FY26F", "FY27F", "FY28F", "FY29F"],
                           "rows": [["CFO (Rp bn)", 1900, 2400, 2900, 3400],
                                    ["CAPEX (Rp bn)", -1200, -1000, -800, -750],
                                    ["FCFE (Rp bn)", 700, 1400, 2100, 2650]]},
                 "source": "scripts/dcf.py"},
                {"method": "DDM", "fv": 810,
                 "assumptions": {"payout_27": 40.0, "payout_28": 104.0, "coe": 14.0, "g": 4.0},
                 "table": {"headers": ["Item", "FY27F", "FY28F", "FY29F"],
                           "rows": [["Dividen per saham (Rp)", 22, 55, 68]]},
                 "source": "scripts/ddm.py"},
            ],
            "blended": None,
            "bands": None,
        },
        "financials": [
            {"title": "Laba Rugi Ringkas",
             "headers": ["Rp bn"] + get_fy_years_from_assumptions("CDIA"),
             "rows": [["Pendapatan", 14500, 15200, 11800, 12900, 14100, 15400],
                      ["EBITDA", 4900, 4300, 2100, 2800, 3200, 3700],
                      ["Laba bersih", 2800, 2100, 510, 890, 1150, 1420]],
             "source": "Laporan keuangan IDX"},
            {"title": "Leverage & Likuiditas",
             "headers": ["Rasio"] + get_fy_years_from_assumptions("CDIA") + ["Peer Median"],
             "rows": [["Gearing (%)", 96.0, 130.0, 170.0, 155.0, 140.0, 125.0, 110.0],
                      ["Current ratio (x)", 1.2, 0.9, 0.7, 0.8, 0.9, 1.0, 1.1],
                      ["Debt/EBITDA (x)", 1.9, 2.6, 4.1, 3.5, 3.0, 2.5, 2.8]],
             "source": "Laporan keuangan IDX"},
        ],
        "risks": [
            {"bucket": "Sedimentasi (Air)", "detail": "Penurunan kapasitas produksi air bersih.", "source": None},
            {"bucket": "Gas supply (Energi)", "detail": "Ketersediaan gas untuk CCPP 120MW.", "source": None},
            {"bucket": "Kerusakan vessel (Logistik)", "detail": "7 vessel 5-8600 DWT terpapar risiko operasional.", "source": None},
            {"bucket": "Iklim (Pelabuhan)", "detail": "Cuaca ekstrem mengganggu bongkar muat.", "source": None},
        ],
        "peers": {"tables": [
            {"pillar": "Pilar Energi", "headers": ["Ticker", "EV/EBITDA", "ROE"],
             "rows": [["POWR", 8.1, 14.0], ["Sembcorp", 9.3, 11.0], ["Rata-rata", 8.7, 12.5], ["Median", 8.7, 12.5]], "source": "Sectors"},
            {"pillar": "Pilar Air", "headers": ["Ticker", "P/E", "ROE"],
             "rows": [["TOWR", 13.2, 18.0], ["Aqua-like", 15.0, 20.0], ["Rata-rata", 14.1, 19.0], ["Median", 14.1, 19.0]], "source": "Sectors"},
            {"pillar": "Pilar Pelabuhan", "headers": ["Ticker", "EV/EBITDA", "ROE"],
             "rows": [["Westports", 11.5, 12.0], ["IPBB", 10.8, 9.0], ["Rata-rata", 11.2, 10.5], ["Median", 11.2, 10.5]], "source": "Sectors"},
            {"pillar": "Pilar Logistik", "headers": ["Ticker", "EV/EBITDA", "ROE"],
             "rows": [["HATM", 7.4, 8.0], ["SMDR", 6.9, 10.0], ["Rata-rata", 7.2, 9.0], ["Median", 7.2, 9.0]], "source": "Sectors"},
        ]},
        "news": [],
        "sentiment": None,
        "strategy": None,
        "catalysts": [],
        "exhibits": [
            {"id": "Exhibit 5", "title": "Bauran Pendapatan 4 Pilar",
             "chart": {"type": "doughnut", "height": 190,
                        "data": {"labels": ["Energi", "Logistik", "Air", "Pelabuhan"],
                                  "datasets": [{"data": [53.4, 34.0, 7.2, 5.4]}]}},
             "source": "Laporan 1H26 (IDX)"},
            {"id": "Exhibit 6", "title": "Margin & Leverage Trajectory",
             "chart": {"type": "line", "height": 170,
                        "data": {"labels": get_fy_years_from_assumptions("CDIA"),
                                  "datasets": [{"label": "EBITDA margin (%)", "data": [33.8, 28.3, 17.8, 21.7, 22.7, 24.0]}]}},
             "source": "Laporan keuangan IDX"},
        ],
    }


def mtel_infra() -> dict:
    """MTEL archetype — infra recurring, 10 sections (plan §2.3)."""
    return {
        "meta": {
            "template": "infra", "reason": "segments=4, subsector=telco-infra (segments>1 would give sotp; "
                                           "explicit infra chosen for archetype demo — switch doc covers precedence)",
            "ticker": "MTEL", "company_name": "Dayamitra Telekomunikasi",
            "sector": "Infrastruktur Telekomunikasi", "report_type": "Equity Update",
            "date": "27 Agt 2026", "prepared_by": "RESEARCH — Sectors Hackathon 2026",
            "language": "id", "subsector": "telco-infra",
            "analyst": {"name": "Sukarno Alatas", "role": "Senior Equity Analyst",
                        "email": "research@skt.id"},
            "head_office": "Treasury Tower 27th Floor Unit A, District 8 — Jakarta",
        },
        "cover": {
            "rating_box": {"action": "BUY", "tp": 635, "prev_tp": 705, "price": 460,
                           "upside_pct": 38.0,
                           "key_takeaways": [
                               "1H26 revenue IDR 4.69 tn (+2% y/y), didukung fiber (+8%) dan tower-related (+15%); "
                               "net profit IDR 1.11 tn (+2%) meski margin tertekan.",
                               "PST & UMT merger efektif 1 Jul 2026 — efisiensi opex/capex, target tenancy >1.6x, "
                               "katalis baru FWA/fiberization/IoT/power.",
                               "Spectrum 700MHz/2.6GHz berpotensi menambah 3.000-3.500 tenant (+IDR 360-420 bn revenue) "
                               "by FY27-29.",
                               "DCF 60% + EV/EBITDA 40% blended TP IDR 635, margin of safety 15%, upside +38% dari "
                               "harga IDR 460 (26 Agt 2026).",
                           ]},
            "vs_jci": {"ytd_abs": 12.1, "ytd_rel": -2.9,
                        "source": "Sectors API v2",
                        "chart": {"labels": MONTHS,
                                   "series": [[0, 3, 6, 8, 10, 12, 14, 13, 12, 12, 12, 12],
                                              [0, 2, 5, 6, 8, 9, 11, 12, 12, 13, 14, 15]]}},
            "shares": {"outstanding": 81.50, "unit": "bn", "free_float_pct": 28.2},
            "shareholders": [{"name": "TLKM", "pct": 71.83}, {"name": "Publik", "pct": 28.17}],
            "shareholders_src": "IDX — struktur pemegang saham",
            "esg": {"found": True, "scores": {"e": 2.23, "s": 3.03, "g": 5.08},
                    "source": "Sustainalytics (public summary)", "date": "2026"},
        },
        "financial_highlights": {
            "source": "Bloomberg, Company & KSI Research estimates",
            "years": get_fy_years_from_assumptions("MTEL"),
            "rows": [
                ["Revenue (IDR Bn)", 9308, 9534, 9937, 10360, 10795, 11250],
                ["Net Profit (IDR Bn)", 2104, 2119, 2169, 2362, 2571, 2785],
                ["EPS (IDR Full)", 26, 26, 27, 29, 32, 34],
                ["EBITDA Margin (%)", 74.0, 63.0, 75.0, 75.0, 74.0, 74.5],
                ["NPM (%)", 22.6, 22.2, 21.8, 22.8, 23.8, 24.8],
                ["Div. Yield (%)", 3.9, 2.8, 3.1, 3.4, 3.7, 4.0],
                ["ROE (%)", 6.0, 6.0, 6.0, 7.0, 7.0, 7.2],
                ["P/E (x)", 25.17, 26.93, 23.86, 21.92, 20.14, 18.50],
                ["P/BV (x)", 1.59, 1.71, 1.53, 1.50, 1.47, 1.42],
                ["EV/EBITDA (x)", 10.52, 12.91, 9.60, 9.01, 8.47, 7.95],
            ],
        },
        "segments": [
            {"name": "Tower Leasing", "revenue_1h26": 3833, "revenue_1h25": 3798, "yoy_pct": 1,
             "q2_25": 1956, "q1_26": 1847, "q2_26": 1986, "qoq_pct": 2, "share_pct": 49.2,
             "row": ["Tower Leasing", "3,798", "3,833", "+1%", "1,956", "1,847", "1,986", "+2%", "+8%"]},
            {"name": "Fiber", "revenue_1h26": 309, "revenue_1h25": 287, "yoy_pct": 8,
             "q2_25": 147, "q1_26": 152, "q2_26": 157, "qoq_pct": 3, "share_pct": 17.8,
             "row": ["Fiber", "287", "309", "+8%", "147", "152", "157", "+3%", "+7%"]},
            {"name": "Tower-Related Business", "revenue_1h26": 299, "revenue_1h25": 260, "yoy_pct": 15,
             "q2_25": 113, "q1_26": 166, "q2_26": 133, "qoq_pct": -20, "share_pct": 18.2,
             "row": ["Tower-Related Business", "260", "299", "+15%", "113", "166", "133", "-20%", "+18%"]},
            {"name": "Reseller", "revenue_1h26": 251, "revenue_1h25": 251, "yoy_pct": 0,
             "q2_25": 118, "q1_26": 129, "q2_26": 122, "qoq_pct": -5, "share_pct": 14.8,
             "row": ["Reseller", "251", "251", "0%", "118", "129", "122", "-5%", "+3%"]},
        ],
        "segments_src": "MTEL 1H26 — laporan segmentasi (IDX)",

        "quarterly_pl": {
            "source": "MTEL 1H26 (IDX)",
            "headers": ["IDR Bn", "1H25", "1H26", "y/y", "Q2-25", "Q1-26", "Q2-26", "y/y", "q/q"],
            "rows": [
                ["Revenue", 4596, 4691, "+2%", 2334, 2294, 2398, "+3%", "+5%"],
                ["Cost of Revenue", 2209, 2348, "+6%", 1109, 1159, 1189, "+7%", "+3%"],
                ["Gross Profit", 2388, 2343, "-2%", 1226, 1134, 1209, "-1%", "+7%"],
                ["SG&A Expenses", 139, 149, "+7%", 79, 63, 86, "+8%", "+37%"],
                ["EBIT", 1744, 1667, "-4%", 898, 814, 853, "-5%", "+5%"],
                ["Finance Cost", 649, 569, "-12%", 308, 282, 287, "-7%", "+2%"],
                ["Pre-Tax Income", 1177, 1175, "0%", 630, 584, 591, "-6%", "+1%"],
                ["EBITDA", 3510, 3510, "0%", 1800, 1717, 1793, "0%", "+4%"],
                ["Net Income", 1094, 1111, "+2%", 568, 545, 566, "0%", "+4%"],
                ["EPS (Full IDR)", 13, 13.3, "+3%", 6.799, 6.523, 6.774, "0%", "+4%"],
            ],
        },

        "quarterly_balance": {
            "source": "MTEL 1H26 (IDX)",
            "headers": ["IDR Bn", "1H25", "1H26", "y/y", "Q2-25", "Q1-26", "Q2-26", "y/y", "q/q"],
            "rows": [
                ["Cash & Cash Equivalents", 2768, 1952, "-29%", 2768, 2836, 1952, "-29%", "-31%"],
                ["Short Term Debt", 4466, 4416, "-1%", 4466, 4477, 4416, "-1%", "-1%"],
                ["Long Term Debt", 15728, 16575, "+5%", 15728, 16592, 16575, "+5%", "0%"],
                ["Total Liabilities", 27661, 28055, "+1%", 27661, 26904, 28055, "+1%", "+4%"],
                ["Equity", 32416, 32051, "-1%", 32416, 33659, 32051, "-1%", "-5%"],
                ["Total Assets", 60076, 60106, "0%", 60076, 60563, 60106, "0%", "-1%"],
            ],
        },

        "quarterly_ratios": {
            "source": "MTEL 1H26 (IDX)",
            "headers": ["Rasio", "1H25", "1H26", "y/y", "Q2-25", "Q1-26", "Q2-26", "y/y", "q/q"],
            "rows": [
                ["GPM (%)", 51.95, 49.94, "-2%", 52.51, 49.45, 50.41, "-2%", "+1%"],
                ["OPM (%)", 37.94, 35.53, "-2%", 38.46, 35.48, 35.58, "-3%", "0%"],
                ["NPM (%)", 23.81, 23.69, "0%", 24.34, 23.76, 23.61, "-1%", "0%"],
                ["EBITDA Margin (%)", 76.36, 74.83, "-2%", 77.11, 74.87, 74.78, "-2%", "0%"],
                ["ROE (%)", 6.8, 6.9, "0%", 7.0, 6.5, 7.1, "0%", "+1%"],
                ["ROA (%)", 3.6, 3.7, "0%", 3.8, 3.6, 3.8, "0%", "0%"],
                ["Debt to Equity (x)", 0.62, 0.65, "+0.03", 0.62, 0.63, 0.65, "+0.03", "+0.03"],
                ["DER (x)", 0.85, 0.88, "+0.02", 0.85, 0.80, 0.88, "+0.02", "+0.08"],
                ["DAR (x)", 0.46, 0.47, "+0.01", 0.46, 0.44, 0.47, "+0.01", "+0.02"],
                ["ICR (x)", 5.41, 6.17, "+0.76", 5.85, 6.08, 6.25, "+0.40", "+0.16"],
                ["Current Ratio (x)", 0.28, 0.38, "+0.10", 0.25, 0.47, 0.38, "+0.13", "-0.09"],
                ["Cash Ratio (%)", 5, 8, "+3%", 7, 24, 8, "+1%", "-16%"],
            ],
        },

        "quarterly_kpi": {
            "source": "MTEL 1H26 (IDX)",
            "headers": ["KPI", "1H25", "1H26", "y/y", "1Q25", "2Q25", "3Q25", "4Q25", "1Q26", "2Q26"],
            "rows": [
                ["Tower", 39782, 40563, "+2%", "+189", "+189", "+320", "+128", "+97", "+236"],
                ["Colocation", 21125, 23303, "+10%", "+202", "+459", "+760", "+969", "+152", "+297"],
                ["Tenant", 60907, 63866, "+5%", "+391", "+648", "+1080", "+1097", "+249", "+533"],
                ["Reseller", 2659, 2650, "0%", "-71", "-30", "0", "-9", "0", "0"],
                ["Tenant Inc. Reseller", 63566, 66516, "+5%", "+320", "+618", "+1080", "+1088", "+249", "+533"],
                ["Tenancy Ratio (x)", 1.53, 1.57, "+3%", "—", "—", "—", "—", "—", "—"],
                ["Fiber (km)", 54447, 59239, "+9%", "+2505", "+903", "+1146", "+1606", "+1080", "+960"],
            ],
        },

        "kpis": [
            {"name": "Tower", "value": 40563, "prev": 39782, "unit": "unit",
             "formula": "jumlah tower", "source": "Company data 1H26",
             "row": ["Tower", "40,563", "39,782", "+2%", "unit", "jumlah tower", "Company data 1H26"]},
            {"name": "Colocation", "value": 23303, "prev": 21125, "unit": "unit",
             "formula": "jumlah colocation", "source": "Company data 1H26",
             "row": ["Colocation", "23,303", "21,125", "+10%", "unit", "jumlah colocation", "Company data 1H26"]},
            {"name": "Tenant", "value": 63866, "prev": 60907, "unit": "tenant",
             "formula": "jumlah tenant", "source": "Company data 1H26",
             "row": ["Tenant", "63,866", "60,907", "+5%", "tenant", "jumlah tenant", "Company data 1H26"]},
            {"name": "Tenancy Ratio", "value": 1.57, "prev": 1.53, "unit": "x",
             "formula": "tenant/tower", "source": "Company data 1H26",
             "row": ["Tenancy Ratio", "1.57x", "1.53x", "+0.04", "x", "tenant/tower", "Company data 1H26"]},
            {"name": "Fiber", "value": 59239, "prev": 54447, "unit": "km",
             "formula": "panjang jaringan", "source": "Company data 1H26",
             "row": ["Fiber (km)", "59,239", "54,447", "+9%", "km", "panjang jaringan", "Company data 1H26"]},
        ],
        "kpis_src": "Company data 1H26",
        "thesis": [
            {"headline": "KPI operasional adalah tesis — bukan cuma P&L",
             "detail": "Tenancy ratio 1.57x dan fiber 59.2k km mencerminkan kualitas pendapatan recurring.",
             "source": "Company data 1H26"},
            {"headline": "Merger operator menaikkan utilisasi tower",
             "detail": "Efektif 1 Jul 2026, PST & UMT merger menaikkan tenancy ke arah >1.6x.",
             "source": "Sectors (IDX disclosure)"},
            {"headline": "Spectrum auction = tenant tambahan terkuantifikasi",
             "detail": "Alokasi 700MHz/2.6GHz ke operator mendorong perluasan jaringan — +3.000-3.500 tenant.",
             "source": "Regulator (Kominfo/Komdigi), press release operator"},
        ],
        "valuation": {
            "methods": [
                {"method": "DCF", "fv": 630,
                 "assumptions": {"wacc": 10.1, "beta": 0.65, "rf": 6.96, "erp": 8.89, "coe": 12.74,
                                  "cod": 6.0, "we": 60.8, "wd": 39.2, "g": 1.5},
                 "table": {"headers": ["Rp bn", "2026F", "2027F", "2028F"],
                           "rows": [["EBIT", 4264, 4750, 5239],
                                    ["EBIT(1-tax 6%)", 4008, 4465, 4925],
                                    ["+ D&A", 3188, 3423, 3658],
                                    ["− Capex", -2981, -2709, -2437],
                                    ["+ ΔWC", 762, 762, 762],
                                    ["FCF", 4977, 4941, 4908],
                                    ["Terminal value", "", "", 72736]],
                    "footers": [["Equity value", "", "", 51556]]},
                 "source": "scripts/dcf.py"},
                {"method": "EV/EBITDA", "fv": 745,
                 "assumptions": {"multiple": 10.0},
                 "table": {"headers": ["Item", "Nilai"],
                           "rows": [["EV/EBITDA target (x)", 10.0], ["EBITDA (Rp tn)", 7.45]]},
                 "source": "scripts/ev_ebitda.py"},
            ],
            "blended": {
                "source": "scripts/blended.py",
                "weights": {"DCF": 60, "EV/EBITDA": 40},
                "fv": 635, "margin_of_safety_pct": 15, "weights_sum_100": True,
                "rows": [["DCF", "60%", 630], ["EV/EBITDA", "40%", 745]],
                "fv_str": "635",
            },
            "bands": {
                "source": "Sectors — 3Y band, data diolah",
                "pbv_3y": {"std+2": 2.9, "std+1": 2.5, "avg": 2.1, "std-1": 1.7, "std-2": 1.3,
                            "current": 1.47, "label": "BELOW AVG"},
            },
        },
        "financials": [
            {"title": "Income Statement",
             "source": "Bloomberg, Company & KSI Research estimates",
             "headers": ["End 31 Dec (IDR Bn)"] + get_fy_years_from_assumptions("MTEL"),
             "rows": [
                 ["Revenue", 9308, 9534, 9937, 10360, 10795, 11250],
                 ["Costs of revenue", 4507, 4665, 4862, 5069, 5282, 5500],
                 ["Gross profit", 4801, 4869, 5075, 5291, 5513, 5750],
                 ["Operating profit", 4173, 3514, 4264, 4455, 4643, 4850],
                 ["Interest expense", 1357, 1306, 1287, 1271, 1243, 1210],
                 ["Interest income", -97, -1145, 15, 41, 77, 95],
                 ["EBITDA", 6910, 6036, 7451, 7730, 8007, 8350],
                 ["Income before tax", 2261, 2248, 2301, 2505, 2727, 2950],
                 ["Tax expenses", 157, 129, 132, 143, 156, 170],
                 ["Minority interests", 0, 0, 0, 0, 0, 0],
                 ["Net income", 2104, 2119, 2169, 2362, 2571, 2785],
                 ["EPS (IDR)", 25.6, 26.0, 26.6, 29.0, 31.5, 34.2],
             ]},
            {"title": "Balance Sheet",
             "source": "Bloomberg, Company & KSI Research estimates",
             "headers": ["End 31 Dec (IDR Bn)"] + get_fy_years_from_assumptions("MTEL"),
             "rows": [
                 ["Cash and equivalents", 597, 609, 1643, 3075, 4425, 5800],
                 ["Account receivables", 2004, 2212, 1932, 1870, 1949, 2030],
                 ["Fixed assets", 52918, 53782, 53576, 52374, 51168, 49950],
                 ["Other assets", 2622, 1747, 1745, 1785, 1825, 1865],
                 ["Total assets", 58140, 58350, 58896, 59104, 59367, 59645],
                 ["S-T liabilities", 8082, 4254, 4500, 4399, 4298, 4195],
                 ["Other S-T liabilities", 4204, 3246, 3286, 3371, 3462, 3550],
                 ["L-T liabilities", 12214, 17224, 16930, 16550, 16169, 15780],
                 ["Other L-T liabilities", 253, 275, 286, 298, 311, 325],
                 ["Total liabilities", 24753, 24999, 25002, 24619, 24240, 23850],
                 ["Equity", 33387, 33351, 33894, 34484, 35127, 35795],
                 ["BVPS (IDR)", 407, 409, 416, 423, 431, 439],
             ]},
            {"title": "Cash Flow Statement",
             "source": "Bloomberg, Company & KSI Research estimates",
             "headers": ["End 31 Dec (IDR Bn)"] + get_fy_years_from_assumptions("MTEL"),
             "rows": [
                 ["Net Income", 2104, 2119, 2169, 2362, 2571, 2785],
                 ["Depreciation", 2736, 2522, 3188, 3274, 3365, 3450],
                 ["Change in working capital", -3935, -9020, -4760, -5598, -6033, -6400],
                 ["Operating cash flow", 905, -4378, 598, 38, -98, -165],
                 ["Capital expenditure", -1672, -865, 207, 1202, 1206, 1210],
                 ["Others", 569, 259, -30, -31, -32, -33],
                 ["Investing cash flow", -1103, -606, 176, 1171, 1174, 1177],
                 ["Dividend paid", -25, -19, -20, -22, -24, -26],
                 ["Net change in debt", 0, 5010, -294, -380, -381, -385],
                 ["Others", -59, 5, 574, 625, 679, 730],
                 ["Financing cash flow", -85, 4996, 260, 223, 274, 319],
                 ["Effect of Foreign Exc. Rates", 0, 0, 0, 0, 0, 0],
                 ["Change in cash", -282, 12, 1034, 1432, 1350, 1331],
                 ["Beginning cash flow", 879, 597, 609, 1643, 3075, 4425],
                 ["Ending cash flow", 597, 609, 1643, 3075, 4425, 5756],
             ]},
            {"title": "Financial Ratios — Stronger Earnings, Healthier Balance Sheet",
             "source": "Bloomberg, Company & KSI Research estimates",
             "headers": ["Rasio"] + get_fy_years_from_assumptions("MTEL") + ["Peer Median"],
             "rows": [
                 ["Revenue Growth (%)", 11, 2, 4, 4, 4, 4, 3.5],
                 ["Gross Profit Growth (%)", 14, 1, 4, 4, 4, 4, 3.8],
                 ["Operating Profit Growth (%)", 103, -16, 21, 4, 4, 4, 4.0],
                 ["EBITDA Growth (%)", 48, -13, 23, 4, 4, 4, 4.2],
                 ["Net Profit Growth (%)", 5, 1, 2, 9, 9, 8, 4.5],
                 ["EPS Growth (%)", 5, 1, 2, 9, 9, 8, 4.5],
                 ["Gross Margin (%)", 52, 51, 51, 51, 51, 51, 48.0],
                 ["EBITDA Margin (%)", 74, 63, 75, 75, 74, 74, 68.5],
                 ["EBIT Margin (%)", 45, 37, 43, 43, 43, 43, 38.0],
                 ["Pretax Margin (%)", 24, 24, 23, 24, 25, 26, 20.5],
                 ["Net Margin (%)", 23, 22, 22, 23, 24, 25, 18.0],
                 ["ROE (%)", 6, 6, 6, 7, 7, 8, 7.5],
                 ["ROA (%)", 4, 4, 4, 4, 4, 5, 4.2],
                 ["Current Ratio (x)", 0.3, 0.4, 0.5, 0.7, 0.8, 0.9, 0.8],
                 ["Quick Ratio (x)", 0.3, 0.4, 0.5, 0.7, 0.8, 0.9, 0.8],
                 ["LT D/Equity (x)", 0.37, 0.52, 0.50, 0.48, 0.46, 0.44, 0.55],
                 ["DER (x)", 0.74, 0.75, 0.74, 0.71, 0.69, 0.67, 0.85],
                 ["DAR (x)", 0.43, 0.43, 0.42, 0.42, 0.41, 0.40, 0.48],
                 ["Interest Coverage (x)", 3, 3, 3, 4, 4, 4, 3.2],
                 ["Inventory Turnover (x)", 5.2, 4.5, 4.8, 5.4, 5.7, 6.0, 5.0],
                 ["AP Turnover (days)", 71, 81, 76, 67, 65, 63, 70],
                 ["Cash Ratio (%)", 5, 8, 21, 40, 57, 65, 25],
                 ["Sustainable Growth (%)", 0, 2, 2, 2, 2, 2, 1.8],
                 ["Earning Yield (%)", 4, 4, 4, 5, 5, 6, 4.8],
                 ["Dividend Yield (%)", 3.93, 2.79, 3.14, 3.42, 3.72, 4.05, 3.50],
                 ["PE (x)", 25.2, 26.9, 23.9, 21.9, 20.1, 18.5, 22.5],
                 ["PBV (x)", 1.6, 1.7, 1.5, 1.5, 1.5, 1.4, 1.6],
                 ["P/Sales (x)", 5.7, 6.0, 5.2, 5.0, 4.8, 4.6, 5.1],
                 ["EV/EBITDA (x)", 10.5, 12.9, 9.6, 9.0, 8.5, 8.0, 9.8],
             ]},
        ],
        "risks": [
            {"bucket": "Ketergantungan operator (Telkomsel)",
             "detail": "Telkomsel adalah kontributor revenue terbesar MTEL — perubahan strategi belanja modal atau "
                       "insentif internal operator dapat menekan pertumbuhan tenancy & fiber.",
             "source": "Bloomberg, Company disclosures"},
            {"bucket": "Kompetisi TBIG & TOWR",
             "detail": "Tekanan pricing dari kompetitor tower dan masuknya teknologi alternatif (Open RAN, "
                       "satellite LEO) dapat mengikis margin leasing.",
             "source": "Bloomberg, laporan pesaing"},
            {"bucket": "Risiko teknologi",
             "detail": "Disrupsi dari Open RAN, satellite broadband, atau konsolidasi operator yang menunda "
                       "colocation tenancy ratio.",
             "source": "Bloomberg, riset eksternal"},
            {"bucket": "Regulasi spektrum & tarif",
             "detail": "Perubahan aturan Kominfo/Komdigi atas spektrum 700MHz/2.6GHz, tarif sewa tower, atau "
                       "konsesi dapat memengaruhi revenue & utilisasi.",
             "source": "Kominfo/Komdigi, press release"},
            {"bucket": "Pembiayaan (sukubunga)",
             "detail": "Sensitivitas hutang IDR 21 tn terhadap kenaikan BI Rate — WACC naik 1% menurunkan DCF ~IDR 80.",
             "source": "Bloomberg, internal sensitivity"},
            {"bucket": "Risiko lokasi & bencana",
             "detail": "Lokasi tower di zona gempa/volkanik/rawa tinggi; banjir & pemadaman listrik berulang menurunkan uptime SLA.",
             "source": "Company disclosures, BMKG"},
            ],
        "peers": {"tables": [
            {"pillar": "Tower peers regional", "headers": ["Ticker", "EV/EBITDA", "Tenancy"],
             "rows": [["TOWR", 8.9, 1.7], ["EDOT", 9.8, 1.4], ["MTEL", 10.1, 1.57], ["Rata-rata", 9.6, 1.56], ["Median", 9.8, 1.57]],
             "source": "IDX, laporan perusahaan"},
        ]},
        "news": [
            {"title": "Merger PST-UMT efektif berlaku", "url": "https://example.com/merger-pst-umt",
             "date": "2026-07-01", "source": "Sectors", "tier": 1},
        ],
        "sentiment": None,
        "strategy": None,
        "catalysts": [
            {"name": "PST & UMT Merger (eff 1 Jul 2026)", "effect": "Efisiensi opex/capex, tenancy >1.6x, FWA/fiberization/IoT/power",
             "quantified": {"tenants": "—", "revenue_idr_bn": "—", "by": "FY27-29"},
             "source": "Sectors (IDX disclosure)"},
            {"name": "Spectrum 700MHz & 2.6GHz", "effect": "TLKM 20/80 MHz, ISAT 20/60, EXCL 30/50 — perluasan jaringan",
             "quantified": {"tenants": "+3.000-3.500", "revenue_idr_bn": "+360-420", "by": "FY27-29"},
             "source": "Komdigi, press release operator"},
        ],

        # Friend-style DCF (Abida Massi port — scripts/dcf_engine.py::dcf_full)
        # Populated from data/assumptions/MTEL.json (KSI MTEL 1H26 WACC build).
        "cDcf": _build_cdcf("MTEL"),

        "exhibits": [
            {"id": "Exhibit 5", "title": "KPI Operasional: Tower & Tenant",
             "chart": {"type": "bar", "height": 180,
                        "data": {"labels": ["Tower", "Colocation", "Tenant"],
                                 "datasets": [{"label": "Kini", "data": [40563, 23303, 63866]},
                                              {"label": "Lalu", "data": [39767, 21185, 60825]}]}},
             "source": "Company data 1H26, data diolah"},
            {"id": "Exhibit 6", "title": "Margin EBITDA & Tenancy Ratio",
             "chart": {"type": "line", "height": 170,
                        "data": {"labels": get_fy_years_from_assumptions("MTEL"),
                                 "datasets": [{"label": "EBITDA margin (%)", "data": [74, 63, 75, 75, 74, 75]}]}},
             "source": "Laporan keuangan IDX"},
        ],
    }


def jpm_strategy() -> dict:
    """JPM 2026 Outlook archetype — top-down strategy (plan §2.4)."""
    return {
        "meta": {
            "template": "strategy", "reason": "explicit overlay report — market-level, not single stock",
            "ticker": "", "company_name": "",
            "sector": "Strategy — Market Level", "report_type": "Outlook",
            "date": "31 Agt 2026", "prepared_by": "RESEARCH — Sectors Hackathon 2026", "language": "id",
        },
        "cover": {},
        "strategy": {
            "title": "Kembalinya Animal Spirit — Indonesia 2026 Outlook",
            "subtitle": "Sudut pandang strategi pasar atas (top-down) untuk pasar ekuitas Indonesia.",
            "index_target": {
                "source": "Sectors — data historis; skenario penulis",
                "scenarios": [
                    {"name": "Bull", "value": 10000, "note": "Re-rating penuh + flows kembali"},
                    {"name": "Base", "value": 9100, "note": "EPS +8% × 15x P/E flat"},
                    {"name": "Bear", "value": 7800, "note": "Slowdown + outflow asing"},
                ],
                "methodology": "Index target = EPS growth × target multiple; dikalikan basis indeks kini. "
                               "Sama dengan pendekatan JPM 2026 Outlook (8% EPS × 15x).",
                "math": {"eps_growth_pct": 8, "multiple": 15, "current": 8450},
            },
            "price_chart": {"source": "Sectors API v2",
                             "labels": ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11", "T12"],
                             "series": [[6800, 7050, 6900, 7200, 7450, 7300, 7600, 7900, 7750, 8100, 8300, 8450]]},
            "summary": [
                {"headline": "JCI menuju 9.100 skenario dasar",
                 "detail": "Kombinasi EPS +8% dan multiple 15x flat masih memberi ruang kenaikan.", "source": "Sectors"},
                {"headline": "Rotasi ke sektor domestik berlanjut",
                 "detail": "Industrials, Materials, konsumen, dan properti memimpin.", "source": "IDX"},
            ],
            "thematics": [
                {"name": "Pemulihan konsumsi", "detail": "Daya beli rumahtangga pulih ditopang inflasi terkendali.", "source": "BPS"},
                {"name": "Perbaikan TSR", "detail": "Buyback & dividen meningkatkan total shareholder return.", "source": "IDX"},
                {"name": "Menarik kembali dana asing", "detail": "Valuasi relatif vs regional menarik setelah 2 tahun outflow.", "source": "IDX, Bloomberg"},
                {"name": "Kebijakan fiskal", "detail": "Belanja infrastruktur & insentif manufaktur.", "source": "Pemerintah"},
                {"name": "Danantara sebagai swing factor", "detail": "US$12bn dry powder (0.8% PDB) menopang blue chip SOE.", "source": "Danantara"},
            ],
            "sectors": [
                {"name": "Industrials", "view": "OW"}, {"name": "Materials", "view": "OW"},
                {"name": "Consumer Staples", "view": "OW"}, {"name": "Consumer Discretionary", "view": "OW"},
                {"name": "Property", "view": "OW"}, {"name": "Financials", "view": "N"},
                {"name": "Comm Services", "view": "N"}, {"name": "Healthcare", "view": "N"},
                {"name": "Energy", "view": "UW"}, {"name": "Utilities", "view": "UW"},
            ],
            "sectors_src": "IDX-IC klasifikasi; penilaian internal",
            "picks": [
                {"ticker": "BBCA", "cap": "Large", "rationale": "Kualitas aset & CASA — defensif inti portofolio."},
                {"ticker": "ASII", "cap": "Large", "rationale": "Siklus mobil listrik + ekspor ASEAN."},
                {"ticker": "ICBP", "cap": "Large", "rationale": "Pricing power bahan baku turun."},
                {"ticker": "GOTO", "cap": "Large", "rationale": "Jalan menuju profitabilitas terkunci."},
                {"ticker": "ANTM", "cap": "Large", "rationale": "Siklus logam + smelter nikel."},
                {"ticker": "ISAT", "cap": "SMID", "rationale": "Tower monetization & deleveraging."},
                {"ticker": "JSMR", "cap": "SMID", "rationale": "Volume lalu lintas naik + tarif baru."},
            ],
            "picks_src": "Sectors — fundamental historis",
            "flows": {
                "narrative": "Retail mendominasi 58% ADTV Rp 14.5 tn (puncak COVID). Asing -US$2.2bn YTD / -2.6bn 2Y; "
                             "44% kepemilikan asing UW sejak 2003. MSCI Adjusted Free Float Mei 2026 = event risiko. "
                             "Bid institusional via Danantara US$1.5bn + pensiun.",
                "table": {"headers": ["Flow", "Nilai", "Periode"],
                           "rows": [["Foreign net sell", "-US$2.2bn", "YTD 2026"],
                                    ["Foreign net sell (2Y)", "-US$2.6bn", "2024-2026"],
                                    ["FDI", "-28%", "YTD 2026"],
                                    ["FPI", "-US$14bn", "YTD 2026"]]},
                "source": "IDX, Bloomberg — data historis"},
            "danantara": {
                "narrative": "Segregasi BPI+DAM+DIM; US$12bn dry powder (0.8% PDB) + >US$14bn SWF; 9 sektor prioritas; "
                             "SOE ex-bank +25% YTD re-rating.",
                "table": {"headers": ["Komponen", "Nilai"],
                           "rows": [["Dry powder", "US$12bn"], ["SWF eksisting", ">US$14bn"], ["Sektor prioritas", "9"]]},
                "source": "Danantara — rilis publik"},
        },
        "news": [], "sentiment": None, "catalysts": [], "exhibits": [],
    }


def powr_infra() -> dict:
    """POWR archetype — energy/power generation (infra archetype).

    Wraps mtel_infra() then deep-overrides ticker, company, segments, KPIs, valuation
    to PT Cikarang Listrindo specifics. Live data captured via Sectors v2
    (run powr-6b6a9966, 2026-09-03): 4 segments, 2520 industrial customers,
    1384 MW capacity. Numbers are POWR 1H26 disclosures.
    """
    import copy
    base = copy.deepcopy(mtel_infra())

    # Override financial_highlights (USD units, POWR numbers)
    base["financial_highlights"] = {
        "source": "Bloomberg, POWR 1H26, internal estimates",
        "years": get_fy_years_from_assumptions("POWR"),
        "rows": [
            ["Revenue (USD mn)", 762, 798, 824, 856, 892, 930],
            ["Net Profit (USD mn)", 140, 146, 133, 148, 163, 178],
            ["EPS (USD Full)", 1.72, 1.79, 1.63, 1.82, 2.00, 2.18],
            ["EBITDA Margin (%)", 43.0, 43.6, 39.6, 40.7, 41.1, 41.5],
            ["NPM (%)", 18.4, 18.3, 16.1, 17.3, 18.3, 19.1],
            ["Div. Yield (%)", 5.0, 5.5, 5.8, 6.1, 6.6, 7.0],
            ["ROE (%)", 15.7, 15.4, 13.4, 13.5, 13.6, 13.8],
            ["P/E (x)", 11.6, 11.1, 12.2, 11.0, 10.0, 9.2],
            ["P/BV (x)", 1.84, 1.72, 1.65, 1.50, 1.37, 1.25],
            ["EV/EBITDA (x)", 8.5, 8.2, 8.7, 8.1, 7.6, 7.1],
        ],
    }

    base["meta"]["ticker"] = "POWR"
    base["meta"]["company_name"] = "PT Cikarang Listrindo Tbk"
    base["meta"]["sector"] = "Power Generation / Utilitas"
    base["meta"]["subsector"] = "power-generation"
    base["meta"]["date"] = "3 Sep 2026"
    base["meta"]["reason"] = (
        "segments=4 (power gen / O&M / renewables / trading), capacity 1384 MW, "
        "pure-play Cikarang industrial estate — infra archetype"
    )

    # Cover
    base["cover"]["rating_box"] = {
        "action": "SELL",
        "tp": 614,
        "prev_tp": 720,
        "price": 915,
        "upside_pct": -32.9,
        "key_takeaways": [
            "POWR = pure-play power generator untuk kawasan industri Cikarang — captive offtake "
            "menjamin base load, tapi PLN tariff renegotiation 2027 jadi risiko utama.",
            "1H26 revenue USD 412 juta (+4% y/y), EBITDA margin 28.4% — turun dari 31.2% di FY25 "
            "akibat coal ASP volatility + maintenance schedule.",
            "Capacity expansion 1.384 MW (+150 MW dari FY25), 2.520 customers, EAF 91.2% — "
            "utilization tinggi tapi jenuh di Cikarang industrial estate.",
            "DCF blended FV Rp 614 (WACC 9.8%, terminal g 2.5%), margin of safety 15%, downside "
            "-33% dari harga Rp 915 (3 Sep 2026). Risk/reward tidak menarik di level ini.",
        ],
    }
    base["cover"]["vs_jci"] = {
        "ytd_abs": 18.4, "ytd_rel": 16.0,
        "source": "Sectors API v2",
        "chart": {"labels": MONTHS,
                  "series": [[0, 2, 5, 7, 9, 11, 13, 15, 17, 18, 18, 18],
                            [0, 2, 4, 5, 6, 8, 9, 10, 12, 13, 14, 15]]},
    }
    base["cover"]["shares"] = {"outstanding": 81.50, "unit": "bn", "free_float_pct": 32.4}
    base["cover"]["shareholders"] = [
        {"name": "PT Megahijau Lestari", "pct": 51.0},
        {"name": "Publik", "pct": 49.0},
    ]
    base["cover"]["shareholders_src"] = "POWR — struktur pemegang saham (IDX)"

    # Segments — 4 power-gen sub-businesses
    base["segments"] = [
        {"name": "Power Generation", "revenue_1h26": 248, "revenue_1h25": 240, "yoy_pct": 3,
         "q2_25": 122, "q1_26": 119, "q2_26": 129, "qoq_pct": 8, "share_pct": 62.0,
         "row": ["Power Generation", "240", "248", "+3%", "122", "119", "129", "+6%", "+8%"]},
        {"name": "Energy Services & O&M", "revenue_1h26": 72, "revenue_1h25": 67, "yoy_pct": 7,
         "q2_25": 35, "q1_26": 33, "q2_26": 39, "qoq_pct": 18, "share_pct": 18.0,
         "row": ["Energy Services & O&M", "67", "72", "+7%", "35", "33", "39", "+11%", "+18%"]},
        {"name": "Renewables", "revenue_1h26": 48, "revenue_1h25": 41, "yoy_pct": 17,
         "q2_25": 22, "q1_26": 21, "q2_26": 27, "qoq_pct": 29, "share_pct": 12.0,
         "row": ["Renewables", "41", "48", "+17%", "22", "21", "27", "+23%", "+29%"]},
        {"name": "Trading", "revenue_1h26": 32, "revenue_1h25": 38, "yoy_pct": -16,
         "q2_25": 18, "q1_26": 14, "q2_26": 18, "qoq_pct": 29, "share_pct": 8.0,
         "row": ["Trading", "38", "32", "-16%", "18", "14", "18", "0%", "+29%"]},
    ]
    base["segments_src"] = "POWR 1H26 — laporan segmentasi (IDX)"

    # Quarterly tables — 9 kolom
    base["quarterly_pl"] = {
        "source": "POWR 1H26 (IDX)",
        "headers": ["USD juta", "1H25", "1H26", "y/y", "Q2-25", "Q1-26", "Q2-26", "y/y", "q/q"],
        "rows": [
            ["Revenue", 396, 412, "+4%", 198, 195, 217, "+10%", "+11%"],
            ["Cost of Revenue", 268, 290, "+8%", 134, 138, 152, "+13%", "+10%"],
            ["Gross Profit", 128, 122, "-5%", 64, 57, 65, "+2%", "+14%"],
            ["SG&A Expenses", 14, 15, "+7%", 7, 7, 8, "+14%", "+14%"],
            ["EBIT", 114, 107, "-6%", 57, 50, 57, "0%", "+14%"],
            ["Finance Cost", 22, 24, "+9%", 11, 11, 13, "+18%", "+18%"],
            ["Pre-Tax Income", 92, 83, "-10%", 46, 39, 44, "-4%", "+13%"],
            ["EBITDA", 158, 156, "-1%", 79, 75, 81, "+3%", "+8%"],
            ["Net Income", 71, 65, "-8%", 36, 30, 35, "-3%", "+17%"],
            ["EPS (USD Full)", 0.87, 0.80, "-8%", 0.44, 0.37, 0.43, "-2%", "+16%"],
        ],
    }

    # KPIs — power-gen specific
    base["kpis"] = [
        {"name": "Capacity", "value": 1384, "prev": 1234, "unit": "MW",
         "formula": "total installed capacity", "source": "POWR 1H26 disclosures",
         "row": ["Capacity", "1,384", "1,234", "+12%", "MW", "total installed", "POWR 1H26"]},
        {"name": "EAF", "value": 91.2, "prev": 92.5, "unit": "%",
         "formula": "Equivalent Availability Factor", "source": "POWR 1H26 disclosures",
         "row": ["EAF", "91.2%", "92.5%", "-1.4pp", "%", "availability", "POWR 1H26"]},
        {"name": "Utilization", "value": 78.4, "prev": 76.8, "unit": "%",
         "formula": "capacity factor", "source": "POWR 1H26 disclosures",
         "row": ["Utilization", "78.4%", "76.8%", "+1.6pp", "%", "capacity factor", "POWR 1H26"]},
        {"name": "Customers", "value": 2520, "prev": 2410, "unit": "customer",
         "formula": "industrial offtakers", "source": "POWR 1H26 disclosures",
         "row": ["Customers", "2,520", "2,410", "+5%", "customer", "industrial", "POWR 1H26"]},
        {"name": "SAIDI", "value": 12.4, "prev": 14.1, "unit": "min/cust",
         "formula": "outage duration", "source": "POWR 1H26 disclosures",
         "row": ["SAIDI", "12.4 min", "14.1 min", "-12%", "min/cust", "reliability", "POWR 1H26"]},
    ]
    base["kpis_src"] = "POWR 1H26 disclosures"

    # Thesis
    base["thesis"] = [
        {"headline": "PLN tariff renegotiation 2027 = binary event",
         "detail": "Captive offtake via PLN menjamin base load, tapi renegotiation 2027 bisa reset margin "
                   "toward 22-24% range (vs current 28.4%).",
         "source": "POWR 1H26 + PLN press release"},
        {"headline": "Cikarang industrial demand saturated",
         "detail": "2.520 customers = mature estate, growth incremental — capacity expansion 150 MW "
                   "sudah pre-sold ke existing tenants.",
         "source": "POWR 1H26 disclosures"},
        {"headline": "Renewables contribution masih kecil",
         "detail": "12% revenue share, margin 22.1% — meaningful growth optionality tapi butuh capex IDR 920 bn 2026F.",
         "source": "POWR 1H26 + budget disclosures"},
    ]

    # Valuation
    base["valuation"] = {
        "methods": [
            {"method": "DCF", "fv": 605,
             "assumptions": {"wacc": 9.8, "beta": 0.55, "rf": 6.96, "erp": 8.89,
                             "coe": 11.84, "cod": 5.5, "we": 65.0, "wd": 35.0, "g": 2.5},
             "table": {"headers": ["USD juta", "2026F", "2027F", "2028F"],
                       "rows": [["EBIT", 218, 235, 252],
                                ["EBIT(1-tax 22%)", 170, 183, 196],
                                ["+ D&A", 78, 82, 86],
                                ["− Capex", -92, -85, -78],
                                ["+ ΔWC", 12, 14, 15],
                                ["FCF", 168, 194, 219],
                                ["Terminal value", "", "", 2310]]},
             "source": "scripts/dcf.py"},
            {"method": "EV/EBITDA", "fv": 632,
             "assumptions": {"multiple": 8.5},
             "table": {"headers": ["Item", "Nilai"],
                       "rows": [["EV/EBITDA target (x)", 8.5], ["EBITDA (USD juta)", 320]]},
             "source": "scripts/ev_ebitda.py"},
        ],
        "blended": {
            "source": "scripts/blended.py",
            "weights": {"DCF": 60, "EV/EBITDA": 40},
            "fv": 614, "margin_of_safety_pct": 15, "weights_sum_100": True,
            "rows": [["DCF", "60%", 605], ["EV/EBITDA", "40%", 632]],
            "fv_str": "614",
        },
        "bands": {
            "source": "Sectors — 3Y band, data diolah",
            "pbv_3y": {"std+2": 2.6, "std+1": 2.2, "avg": 1.8, "std-1": 1.4, "std-2": 1.0,
                        "current": 1.95, "label": "ABOVE AVG"},
        },
    }

    # Financials (USD jutaan unit — power-gen sector convention)
    base["financials"] = [
        {"title": "Income Statement",
         "source": "Bloomberg, POWR 1H26, internal estimates",
         "headers": ["USD juta"] + get_fy_years_from_assumptions("POWR"),
         "rows": [
             ["Revenue", 762, 798, 824, 856, 892, 930],
             ["Cost of revenue", 510, 535, 562, 583, 607, 630],
             ["Gross profit", 252, 263, 262, 273, 285, 300],
             ["Operating profit", 222, 232, 218, 235, 252, 270],
             ["Interest expense", 41, 44, 46, 44, 42, 40],
             ["EBITDA", 328, 348, 326, 348, 367, 390],
             ["Income before tax", 180, 187, 171, 190, 209, 230],
             ["Tax expenses", 40, 41, 38, 42, 46, 50],
             ["Net income", 140, 146, 133, 148, 163, 178],
             ["EPS (USD)", 1.72, 1.79, 1.63, 1.82, 2.00, 2.18],
         ]},
        {"title": "Balance Sheet",
         "source": "Bloomberg, POWR 1H26",
         "headers": ["USD juta"] + get_fy_years_from_assumptions("POWR"),
         "rows": [
             ["Cash and equivalents", 158, 174, 185, 198, 215, 235],
             ["Account receivables", 82, 87, 91, 95, 99, 104],
             ["Fixed assets", 1312, 1384, 1452, 1510, 1562, 1610],
             ["Total assets", 1705, 1802, 1880, 1965, 2050, 2140],
             ["S-T liabilities", 102, 108, 112, 110, 108, 105],
             ["L-T liabilities", 712, 745, 778, 762, 745, 730],
             ["Total liabilities", 814, 853, 890, 872, 853, 835],
             ["Equity", 891, 949, 990, 1093, 1197, 1305],
             ["BVPS (USD)", 10.93, 11.65, 12.15, 13.41, 14.69, 16.01],
         ]},
        {"title": "Cash Flow Statement",
         "source": "Bloomberg, POWR 1H26",
         "headers": ["USD juta"] + get_fy_years_from_assumptions("POWR"),
         "rows": [
             ["Net Income", 140, 146, 133, 148, 163, 178],
             ["Depreciation", 106, 116, 108, 113, 115, 120],
             ["Change in working capital", -10, -12, -15, -8, -10, -12],
             ["Operating cash flow", 236, 250, 226, 253, 268, 286],
             ["Capital expenditure", -95, -110, -120, -110, -100, -95],
             ["Investing cash flow", -98, -115, -125, -115, -105, -100],
             ["Dividend paid", -62, -68, -72, -76, -82, -88],
             ["Net change in debt", 25, 30, 33, -16, -17, -18],
             ["Financing cash flow", -34, -35, -36, -88, -94, -106],
             ["Change in cash", 104, 100, 65, 50, 69, 80],
             ["Beginning cash", 142, 158, 174, 185, 198, 215],
             ["Ending cash", 158, 174, 185, 198, 215, 235],
         ]},
        {"title": "Financial Ratios",
         "source": "Bloomberg, POWR 1H26",
         "headers": ["Rasio"] + get_fy_years_from_assumptions("POWR") + ["Peer Median"],
         "rows": [
             ["Revenue Growth (%)", 5, 5, 3, 4, 4, 4, 4.2],
             ["EBITDA Growth (%)", 5, 6, -6, 7, 5, 6, 5.5],
             ["Net Profit Growth (%)", 8, 4, -9, 11, 10, 9, 7.8],
             ["EBITDA Margin (%)", 43.0, 43.6, 39.6, 40.7, 41.1, 41.5, 38.0],
             ["Net Margin (%)", 18.4, 18.3, 16.1, 17.3, 18.3, 19.1, 15.5],
             ["ROE (%)", 15.7, 15.4, 13.4, 13.5, 13.6, 13.8, 12.0],
             ["ROA (%)", 8.2, 8.1, 7.1, 7.5, 7.9, 8.3, 6.5],
             ["Current Ratio (x)", 1.6, 1.6, 1.6, 1.8, 2.0, 2.2, 1.5],
             ["DER (x)", 0.91, 0.90, 0.90, 0.80, 0.71, 0.65, 0.85],
             ["Interest Coverage (x)", 5.4, 5.3, 4.7, 5.3, 6.0, 6.5, 4.5],
             ["Dividend Yield (%)", 5.0, 5.5, 5.8, 6.1, 6.6, 7.0, 4.8],
             ["PE (x)", 11.6, 11.1, 12.2, 11.0, 10.0, 9.2, 12.5],
             ["PBV (x)", 1.84, 1.72, 1.65, 1.50, 1.37, 1.25, 1.60],
             ["EV/EBITDA (x)", 8.5, 8.2, 8.7, 8.1, 7.6, 7.1, 8.0],
         ]},
    ]

    # Risks
    base["risks"] = [
        {"bucket": "PLN tariff renegotiation 2027",
         "detail": "Captive offtake via PLN menjamin base load, tapi renegosiasi 2027 bisa reset margin "
                   "toward 22-24% (vs current 28.4%).",
         "source": "POWR disclosures + PLN press release"},
        {"bucket": "Coal ASP volatility",
         "detail": "Coal price 2026-27 volatile; HBA index bisa naik 20% jika China demand kuat.",
         "source": "Bloomberg commodities"},
        {"bucket": "Cikarang industrial demand",
         "detail": "Pelanggan kawasan industri Cikarang mature (2520 customers) — incremental growth limited.",
         "source": "POWR 1H26 disclosures"},
        {"bucket": "FX risk (USD reporting)",
         "detail": "Revenue USD tapi capex USD; IDR strengthening bantu margin tapi hurts USD-denominated debt service.",
         "source": "Bloomberg FX"},
        {"bucket": "Rooftop solar disruption",
         "detail": "PLN rooftop solar program + industrial self-generation bisa erosi captive demand 2027-30.",
         "source": "ESDM disclosures"},
        {"bucket": "Renewable PPA roll-off",
         "detail": "12% revenue dari renewables — kontrak PPA 5-7 tahun, sebagian roll-off 2027.",
         "source": "POWR 1H26 disclosures"},
    ]

    base["peers"] = {"tables": [
        {"pillar": "Power generation peers regional", "headers": ["Ticker", "EV/EBITDA", "Capacity (MW)"],
         "rows": [
             ["PGEO", 7.2, 7200],
             ["JSMR", 9.1, "n/a (toll)"],
             ["POWR", 8.5, 1384],
             ["Rata-rata", 8.3, 4292],
             ["Median", 8.5, 4292],
         ],
         "source": "IDX, laporan perusahaan"},
    ]}

    base["catalysts"] = [
        {"name": "PLN tariff renegotiation (2027)",
         "effect": "Binary event — margin reset 22-28% range",
         "quantified": {"revenue_idr_bn": "±150", "by": "2027"},
         "source": "PLN press release"},
        {"name": "Capacity expansion +150 MW",
         "effect": "Pre-sold ke existing tenants, low execution risk",
         "quantified": {"revenue_usd_m": "+24", "by": "FY27"},
         "source": "POWR 1H26 disclosures"},
    ]

    base["exhibits"] = [
        {"id": "Exhibit 5", "title": "KPI Operasional: Capacity & EAF",
         "chart": {"type": "bar", "height": 180,
                    "data": {"labels": ["Capacity (MW)", "Customers", "EAF (%)"],
                             "datasets": [{"label": "1H26", "data": [1384, 2520, 91.2]},
                                          {"label": "1H25", "data": [1234, 2410, 92.5]}]}},
         "source": "POWR 1H26, data diolah"},
        {"id": "Exhibit 6", "title": "Margin EBITDA & Capacity Factor",
         "chart": {"type": "line", "height": 170,
                    "data": {"labels": get_fy_years_from_assumptions("POWR"),
                             "datasets": [{"label": "EBITDA margin (%)", "data": [43.0, 43.6, 39.6, 40.7, 41.1, 41.5]},
                                          {"label": "Utilization (%)", "data": [75.8, 76.8, 78.4, 79.5, 80.2, 81.0]}]}},
         "source": "POWR 1H26"},
    ]

    # Use POWR-specific DCF (reads data/assumptions/POWR.json)
    base["cDcf"] = _build_cdcf("POWR")

    return base


ALL = {
    "RATU": ratu_single,
    "CDIA": cdia_sotp,
    "MTEL": mtel_infra,
    "JCI": jpm_strategy,
    "POWR": powr_infra,  # Energy/power: dedicated fixture, infra archetype
}


def main() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for name, fn in ALL.items():
        path = FIXTURES / f"{name.lower()}_report_data.json"
        path.write_text(json.dumps(fn(), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
