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

# months labels used by price charts
MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agt", "Sep", "Okt", "Nov", "Des"]


def ratu_single() -> dict:
    """RATU archetype — pure-play oil holding, 9 sections (plan §2.1)."""
    return {
        "meta": {
            "template": "single", "reason": "segments=0, subsector=oil-pure-play -> single",
            "ticker": "RATU", "company_name": "Ratu Prabu Energi",
            "sector": "Energi — Pure-Play Holding", "report_type": "Initiation",
            "date": "31 Agt 2026", "prepared_by": "RESEARCH — Sectors Hackathon 2026", "language": "id",
        },
        "cover": {
            "rating_box": {"action": "BUY", "tp": 7880, "prev_tp": None, "price": 6200,
                           "upside_pct": 27.1, "key_takeaways": []},
            "vs_jci": {"ytd_abs": 18.4, "ytd_rel": 6.2,
                        "source": "IDX, yfinance (RATU.JK vs ^JKSE)",
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
            "years": ["FY24A", "FY25A", "FY26F"],
            "rows": [
                ["Pendapatan (Rp bn)", 1290, 1122, 1180],
                ["EBITDA (Rp bn)", 610, 540, 585],
                ["Net profit (Rp bn)", 402, 355, 390],
                ["P/E (x)", 129.0, 55.2, 42.7],
                ["ROE (%)", 88.0, 41.0, 30.0],
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
                 "table": {"headers": ["Item", "FY26F", "FY27F", "FY28F"],
                           "rows": [["FCF (Rp bn)", 410, 432, 455],
                                    ["Discount factor", 0.92, 0.85, 0.78],
                                    ["PV (Rp bn)", 377, 367, 355]]},
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
             "headers": ["Rp bn", "FY24A", "FY25A", "FY26F"],
             "rows": [["Pendapatan", 1290, 1122, 1180], ["HPP", -520, -470, -492],
                      ["EBITDA", 610, 540, 585], ["Laba bersih", 402, 355, 390]],
             "source": "Laporan keuangan IDX"},
            {"title": "Rasio Kunci",
             "headers": ["Rasio", "FY24A", "FY25A", "FY26F"],
             "rows": [["ROE (%)", 88.0, 41.0, 30.0], ["DER (x)", 0.21, 0.24, 0.22],
                      ["Interest coverage (x)", 14.2, 11.8, 12.4]],
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
             "rows": [["MEDC", 8.9, 4.2, 22.0], ["ENRG", 12.4, 5.1, 15.0], ["RATU", 42.7, 22.6, 30.0]],
             "source": "IDX, yfinance — data historis"},
        ]},
        "news": [],
        "sentiment": None,
        "strategy": None,
        "catalysts": [],
        "exhibits": [
            {"id": "Exhibit 4", "title": "Tren Pendapatan & EBITDA",
             "chart": {"type": "bar", "height": 190,
                        "data": {"labels": ["FY24A", "FY25A", "FY26F"],
                                  "datasets": [{"label": "Pendapatan (Rp bn)", "data": [1290, 1122, 1180]},
                                                {"label": "EBITDA (Rp bn)", "data": [610, 540, 585]}]}},
             "source": "Laporan keuangan IDX"},
            {"id": "Exhibit 5", "title": "Trajektori Leverage (DER)",
             "chart": {"type": "line", "height": 170,
                        "data": {"labels": ["FY24A", "FY25A", "FY26F"],
                                  "datasets": [{"label": "DER (x)", "data": [0.21, 0.24, 0.22]}]}},
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
                        "source": "IDX, yfinance (CDIA.JK vs ^JKSE)",
                        "chart": {"labels": MONTHS,
                                   "series": [[0, -12, -28, -41, -50, -55, -60, -58, -61, -62, -63, -63],
                                              [0, 2, 5, 6, 8, 9, 11, 12, 12, 13, 14, 15]]}},
            "shares": {"outstanding": 15.0, "unit": "bn", "free_float_pct": 10.1},
            "esg": {"found": False},
        },
        "financial_highlights": {
            "source": "Laporan keuangan CDIA (IDX), data diolah",
            "years": ["FY24A", "FY25A", "FY26F", "FY27F"],
            "rows": [
                ["Pendapatan (Rp bn)", 14500, 15200, 11800, 12900],
                ["EBITDA (Rp bn)", 4900, 4300, 2100, 2800],
                ["Net profit (Rp bn)", 2800, 2100, 510, 890],
                ["ROE (%)", 12.0, 8.4, 1.9, 3.2],
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
                 "table": {"headers": ["Item", "FY26F", "FY27F", "FY28F"],
                           "rows": [["CFO (Rp bn)", 1900, 2400, 2900],
                                    ["CAPEX (Rp bn)", -1200, -1000, -800],
                                    ["FCFE (Rp bn)", 700, 1400, 2100]]},
                 "source": "scripts/dcf.py"},
                {"method": "DDM", "fv": 810,
                 "assumptions": {"payout_27": 40.0, "payout_28": 104.0, "coe": 14.0, "g": 4.0},
                 "table": {"headers": ["Item", "FY27F", "FY28F"],
                           "rows": [["Dividen per saham (Rp)", 22, 55]]},
                 "source": "scripts/ddm.py"},
            ],
            "blended": None,
            "bands": None,
        },
        "financials": [
            {"title": "Laba Rugi Ringkas",
             "headers": ["Rp bn", "FY24A", "FY25A", "FY26F"],
             "rows": [["Pendapatan", 14500, 15200, 11800], ["EBITDA", 4900, 4300, 2100],
                      ["Laba bersih", 2800, 2100, 510]],
             "source": "Laporan keuangan IDX"},
            {"title": "Leverage & Likuiditas",
             "headers": ["Rasio", "FY24A", "FY25A", "FY26F"],
             "rows": [["Gearing (%)", 96.0, 130.0, 170.0], ["Current ratio (x)", 1.2, 0.9, 0.7],
                      ["Debt/EBITDA (x)", 1.9, 2.6, 4.1]],
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
             "rows": [["POWR", 8.1, 14.0], ["Sembcorp", 9.3, 11.0]], "source": "IDX, yfinance"},
            {"pillar": "Pilar Air", "headers": ["Ticker", "P/E", "ROE"],
             "rows": [["TOWR", 13.2, 18.0], ["Aqua-like", 15.0, 20.0]], "source": "IDX, yfinance"},
            {"pillar": "Pilar Pelabuhan", "headers": ["Ticker", "EV/EBITDA", "ROE"],
             "rows": [["Westports", 11.5, 12.0], ["IPBB", 10.8, 9.0]], "source": "IDX, yfinance"},
            {"pillar": "Pilar Logistik", "headers": ["Ticker", "EV/EBITDA", "ROE"],
             "rows": [["HATM", 7.4, 8.0], ["SMDR", 6.9, 10.0]], "source": "IDX, yfinance"},
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
                        "data": {"labels": ["FY24A", "FY25A", "FY26F"],
                                  "datasets": [{"label": "EBITDA margin (%)", "data": [33.8, 28.3, 17.8]}]}},
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
                        "source": "IDX, yfinance (MTEL.JK vs ^JKSE)",
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
            "years": ["2023A", "2024A", "2025A", "2026F", "2027F", "2028F"],
            "rows": [
                ["Revenue (IDR Bn)", 8595, 9308, 9534, 9937, 10360, 10795],
                ["Net Profit (IDR Bn)", 2010, 2104, 2119, 2169, 2362, 2571],
                ["EPS (IDR Full)", 24, 26, 26, 27, 29, 32],
                ["EBITDA Margin (%)", 54.0, 74.0, 63.0, 75.0, 75.0, 74.0],
                ["NPM (%)", 23.4, 22.6, 22.2, 21.8, 22.8, 23.8],
                ["Div. Yield (%)", 2.6, 3.9, 2.8, 3.1, 3.4, 3.7],
                ["ROE (%)", 6.0, 6.0, 6.0, 6.0, 7.0, 7.0],
                ["P/E (x)", 29.0, 25.17, 26.93, 23.86, 21.92, 20.14],
                ["P/BV (x)", 1.7, 1.59, 1.71, 1.53, 1.50, 1.47],
                ["EV/EBITDA (x)", 16.3, 10.52, 12.91, 9.60, 9.01, 8.47],
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
             "source": "Disclosure IDX, kontan"},
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
                "source": "IDX, yfinance — 3Y band, data diolah",
                "pbv_3y": {"std+2": 2.9, "std+1": 2.5, "avg": 2.1, "std-1": 1.7, "std-2": 1.3,
                            "current": 1.47, "label": "BELOW AVG"},
            },
        },
        "financials": [
            {"title": "Income Statement",
             "source": "Bloomberg, Company & KSI Research estimates",
             "headers": ["End 31 Dec (IDR Bn)", "2023A", "2024A", "2025A", "2026F", "2027F", "2028F"],
             "rows": [
                 ["Revenue", 8595, 9308, 9534, 9937, 10360, 10795],
                 ["Costs of revenue", 4379, 4507, 4665, 4862, 5069, 5282],
                 ["Gross profit", 4216, 4801, 4869, 5075, 5291, 5513],
                 ["Operating profit", 2057, 4173, 3514, 4264, 4455, 4643],
                 ["Interest expense", 1333, 1357, 1306, 1287, 1271, 1243],
                 ["Interest income", -441, -97, -1145, 15, 41, 77],
                 ["EBITDA", 4658, 6910, 6036, 7451, 7730, 8007],
                 ["Income before tax", 2138, 2261, 2248, 2301, 2505, 2727],
                 ["Tax expenses", 128, 157, 129, 132, 143, 156],
                 ["Minority interests", 0, 0, 0, 0, 0, 0],
                 ["Net income", 2010, 2104, 2119, 2169, 2362, 2571],
                 ["EPS (IDR)", 24.3, 25.6, 26.0, 26.6, 29.0, 31.5],
             ]},
            {"title": "Balance Sheet",
             "source": "Bloomberg, Company & KSI Research estimates",
             "headers": ["End 31 Dec (IDR Bn)", "2023A", "2024A", "2025A", "2026F", "2027F", "2028F"],
             "rows": [
                 ["Cash and equivalents", 879, 597, 609, 1643, 3075, 4425],
                 ["Account receivables", 1607, 2004, 2212, 1932, 1870, 1949],
                 ["Fixed assets", 51246, 52918, 53782, 53576, 52374, 51168],
                 ["Other assets", 3278, 2622, 1747, 1745, 1785, 1825],
                 ["Total assets", 57010, 58140, 58350, 58896, 59104, 59367],
                 ["S-T liabilities", 6732, 8082, 4254, 4500, 4399, 4298],
                 ["Other S-T liabilities", 4339, 4204, 3246, 3286, 3371, 3462],
                 ["L-T liabilities", 11660, 12214, 17224, 16930, 16550, 16169],
                 ["Other L-T liabilities", 241, 253, 275, 286, 298, 311],
                 ["Total liabilities", 22973, 24753, 24999, 25002, 24619, 24240],
                 ["Equity", 34038, 33387, 33351, 33894, 34484, 35127],
                 ["BVPS (IDR)", 412, 407, 409, 416, 423, 431],
             ]},
            {"title": "Cash Flow Statement",
             "source": "Bloomberg, Company & KSI Research estimates",
             "headers": ["End 31 Dec (IDR Bn)", "2023A", "2024A", "2025A", "2026F", "2027F", "2028F"],
             "rows": [
                 ["Net Income", 2010, 2104, 2119, 2169, 2362, 2571],
                 ["Depreciation", 2601, 2736, 2522, 3188, 3274, 3365],
                 ["Change in working capital", -4733, -3935, -9020, -4760, -5598, -6033],
                 ["Operating cash flow", -122, 905, -4378, 598, 38, -98],
                 ["Capital expenditure", -4989, -1672, -865, 207, 1202, 1206],
                 ["Others", -416, 569, 259, -30, -31, -32],
                 ["Investing cash flow", -5405, -1103, -606, 176, 1171, 1174],
                 ["Dividend paid", -18, -25, -19, -20, -22, -24],
                 ["Net change in debt", 68, 0, 5010, -294, -380, -381],
                 ["Others", 17, -59, 5, 574, 625, 679],
                 ["Financing cash flow", 68, -85, 4996, 260, 223, 274],
                 ["Effect of Foreign Exc. Rates", 0, 0, 0, 0, 0, 0],
                 ["Change in cash", -5460, -282, 12, 1034, 1432, 1350],
                 ["Beginning cash flow", 6339, 879, 597, 609, 1643, 3075],
                 ["Ending cash flow", 879, 597, 609, 1643, 3075, 4425],
             ]},
            {"title": "Financial Ratios — Stronger Earnings, Healthier Balance Sheet",
             "source": "Bloomberg, Company & KSI Research estimates",
             "headers": ["Rasio", "2023A", "2024A", "2025A", "2026F", "2027F", "2028F"],
             "rows": [
                 ["Revenue Growth (%)", 11, 11, 2, 4, 4, 4],
                 ["Gross Profit Growth (%)", 15, 14, 1, 4, 4, 4],
                 ["Operating Profit Growth (%)", 119, 103, -16, 21, 4, 4],
                 ["EBITDA Growth (%)", 38, 48, -13, 23, 4, 4],
                 ["Net Profit Growth (%)", 13, 5, 1, 2, 9, 9],
                 ["EPS Growth (%)", 13, 5, 1, 2, 9, 9],
                 ["Gross Margin (%)", 49, 52, 51, 51, 51, 51],
                 ["EBITDA Margin (%)", 54, 74, 63, 75, 75, 74],
                 ["EBIT Margin (%)", 24, 45, 37, 43, 43, 43],
                 ["Pretax Margin (%)", 25, 24, 24, 23, 24, 25],
                 ["Net Margin (%)", 23, 23, 22, 22, 23, 24],
                 ["ROE (%)", 6, 6, 6, 6, 7, 7],
                 ["ROA (%)", 4, 4, 4, 4, 4, 4],
                 ["Current Ratio (x)", 0.3, 0.3, 0.4, 0.5, 0.7, 0.8],
                 ["Quick Ratio (x)", 0.3, 0.3, 0.4, 0.5, 0.7, 0.8],
                 ["LT D/Equity (x)", 0.34, 0.37, 0.52, 0.50, 0.48, 0.46],
                 ["DER (x)", 0.67, 0.74, 0.75, 0.74, 0.71, 0.69],
                 ["DAR (x)", 0.40, 0.43, 0.43, 0.42, 0.42, 0.41],
                 ["Interest Coverage (x)", 2, 3, 3, 3, 4, 4],
                 ["Inventory Turnover (x)", 6.5, 5.2, 4.5, 4.8, 5.4, 5.7],
                 ["AP Turnover (days)", 56, 71, 81, 76, 67, 65],
                 ["Cash Ratio (%)", 8, 5, 8, 21, 40, 57],
                 ["Sustainable Growth (%)", 1, 0, 2, 2, 2, 2],
                 ["Earning Yield (%)", 3, 4, 4, 4, 5, 5],
                 ["Dividend Yield (%)", 2.59, 3.93, 2.79, 3.14, 3.42, 3.72],
                 ["PE (x)", 29.0, 25.2, 26.9, 23.9, 21.9, 20.1],
                 ["PBV (x)", 1.7, 1.6, 1.7, 1.5, 1.5, 1.5],
                 ["P/Sales (x)", 6.8, 5.7, 6.0, 5.2, 5.0, 4.8],
                 ["EV/EBITDA (x)", 16.3, 10.5, 12.9, 9.6, 9.0, 8.5],
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
             "rows": [["TOWR", 8.9, 1.7], ["EDOT", 9.8, 1.4], ["MTEL", 10.1, 1.57]],
             "source": "IDX, laporan perusahaan"},
        ]},
        "news": [
            {"title": "Merger PST-UMT efektif berlaku", "url": "https://example.com/merger-pst-umt",
             "date": "2026-07-01", "source": "Kontan", "tier": 1},
        ],
        "sentiment": None,
        "strategy": None,
        "catalysts": [
            {"name": "PST & UMT Merger (eff 1 Jul 2026)", "effect": "Efisiensi opex/capex, tenancy >1.6x, FWA/fiberization/IoT/power",
             "quantified": {"tenants": "—", "revenue_idr_bn": "—", "by": "FY27-29"},
             "source": "Disclosure IDX, Kontan"},
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
                        "data": {"labels": ["2023A", "2024A", "2025A", "2026F", "2027F", "2028F"],
                                  "datasets": [{"label": "EBITDA margin (%)", "data": [54, 58, 62, 66, 70, 74]}]}},
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
                "source": "IDX, yfinance — data historis; skenario penulis",
                "scenarios": [
                    {"name": "Bull", "value": 10000, "note": "Re-rating penuh + flows kembali"},
                    {"name": "Base", "value": 9100, "note": "EPS +8% × 15x P/E flat"},
                    {"name": "Bear", "value": 7800, "note": "Slowdown + outflow asing"},
                ],
                "methodology": "Index target = EPS growth × target multiple; dikalikan basis indeks kini. "
                               "Sama dengan pendekatan JPM 2026 Outlook (8% EPS × 15x).",
                "math": {"eps_growth_pct": 8, "multiple": 15, "current": 8450},
            },
            "price_chart": {"source": "IDX, yfinance (^JKSE 3Y)",
                             "labels": ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11", "T12"],
                             "series": [[6800, 7050, 6900, 7200, 7450, 7300, 7600, 7900, 7750, 8100, 8300, 8450]]},
            "summary": [
                {"headline": "JCI menuju 9.100 skenario dasar",
                 "detail": "Kombinasi EPS +8% dan multiple 15x flat masih memberi ruang kenaikan.", "source": "IDX, yfinance"},
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
            "picks_src": "IDX, yfinance — fundamental historis",
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


ALL = {
    "RATU": ratu_single,
    "CDIA": cdia_sotp,
    "MTEL": mtel_infra,
    "JCI": jpm_strategy,
}


def main() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for name, fn in ALL.items():
        path = FIXTURES / f"{name.lower()}_report_data.json"
        path.write_text(json.dumps(fn(), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
