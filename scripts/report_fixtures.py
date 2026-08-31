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
FIXTURES = HERE / "fixtures"

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
             "source": "Laporan keuangan IDX"},
            {"bucket": "Risiko Operator", "detail": "Ketergantungan pada operator lapangan.", "source": "SKK Migas, KKKS Cepu"},
            {"bucket": "Regulasi PSC/DMO", "detail": "Perubahan ketentuan domestic market obligation.", "source": "Kementerian ESDM / SKK Migas"},
            {"bucket": "Natural decline", "detail": "Penurunan produksi basis legacy.", "source": "Laporan Manajemen Lapangan Cepu"},
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
            {"bucket": "Sedimentasi (Air)", "detail": "Penurunan kapasitas produksi air bersih.", "source": "BCA Sekuritas CDIA p.7, Analisis Risiko Pilar Air"},
            {"bucket": "Gas supply (Energi)", "detail": "Ketersediaan gas untuk CCPP 120MW.", "source": "PGAS Contract, Kementerian ESDM"},
            {"bucket": "Kerusakan vessel (Logistik)", "detail": "7 vessel 5-8600 DWT terpapar risiko operasional.", "source": "Laporan Manajemen Armada CDIA"},
            {"bucket": "Iklim (Pelabuhan)", "detail": "Cuaca ekstrem mengganggu bongkar muat.", "source": "BMKG, Pelindo Terminal Data"},
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
            "sector": "Infrastruktur Telekomunikasi", "report_type": "Initiation",
            "date": "31 Agt 2026", "prepared_by": "RESEARCH — Sectors Hackathon 2026",
            "language": "id", "subsector": "telco-infra",
        },
        "cover": {
            "rating_box": {"action": "BUY", "tp": 635, "prev_tp": 705, "price": 460,
                           "upside_pct": 38.0,
                           "key_takeaways": [
                               "PST & UMT merger efektif 1 Jul 2026 membuka efisiensi opex/capex dan tenancy >1.6x.",
                               "Spectrum 700MHz/2.6GHz berpotensi menambah 3.000-3.500 tenant (+Rp 360-420 bn) by FY27-29.",
                               "DCF 60% + EV/EBITDA 40% blended TP Rp 635, margin of safety 15%.",
                           ]},
            "vs_jci": {"ytd_abs": 12.1, "ytd_rel": -2.9,
                        "source": "IDX, yfinance (MTEL.JK vs ^JKSE)",
                        "chart": {"labels": MONTHS,
                                   "series": [[0, 3, 6, 8, 10, 12, 14, 13, 12, 12, 12, 12],
                                              [0, 2, 5, 6, 8, 9, 11, 12, 12, 13, 14, 15]]}},
            "shares": {"outstanding": 81.5, "unit": "bn", "free_float_pct": 28.2},
            "shareholders": [{"name": "TLKM", "pct": 71.83}, {"name": "Publik", "pct": 28.17}],
            "shareholders_src": "IDX — struktur pemegang saham",
            "esg": {"found": True, "scores": {"e": 2.23, "s": 3.03, "g": 5.08},
                    "source": "Sustainalytics (public summary)", "date": "2026"},
        },
        "financial_highlights": {
            "source": "Laporan keuangan MTEL (IDX), data diolah",
            "years": ["2023A", "2024A", "2025A", "2026F", "2027F", "2028F"],
            "rows": [
                ["Pendapatan (Rp tn)", 8.5, 9.1, 9.6, 10.0, 10.4, 10.7],
                ["Laba bersih (Rp tn)", 2.0, 2.2, 2.3, 2.4, 2.5, 2.5],
                ["EPS (Rp)", 24, 27, 29, 30, 31, 32],
                ["EBITDA margin (%)", 54.0, 58.0, 62.0, 66.0, 70.0, 74.0],
                ["Div yield (%)", 2.6, 2.9, 3.2, 3.4, 3.6, 3.7],
                ["ROE (%)", 6.0, 6.4, 6.7, 6.9, 7.0, 7.0],
                ["P/E (x)", 29.0, 25.5, 22.0, 21.0, 20.5, 20.0],
                ["EV/EBITDA (x)", 16.3, 13.9, 11.5, 10.1, 9.2, 8.5],
            ],
        },
        "segments": [
            {"name": "Tower Leasing", "revenue": 3833, "yoy_pct": 1, "qoq_pct": 2, "share_pct": 49.2,
             "row": ["Tower Leasing", 3833, "+1%", "+2%", "49.2%"]},
            {"name": "Fiber", "revenue": 309, "yoy_pct": 8, "qoq_pct": 3, "share_pct": 17.8,
             "row": ["Fiber", 309, "+8%", "+3%", "17.8%"]},
            {"name": "Tower-Related", "revenue": 299, "yoy_pct": 15, "qoq_pct": 5, "share_pct": 18.2,
             "row": ["Tower-Related", 299, "+15%", "+5%", "18.2%"]},
            {"name": "Reseller", "revenue": 251, "yoy_pct": 0, "qoq_pct": 0, "share_pct": 14.8,
             "row": ["Reseller", 251, "0%", "0%", "14.8%"]},
        ],
        "segments_src": "MTEL 1H26 — laporan segmentasi (IDX)",
        "kpis": [
            {"name": "Tower", "value": 40563, "prev": 39767, "unit": "unit",
             "formula": "jumlah tower", "source": "Company data",
             "row": ["Tower", 40563, 39767, "+796", "unit", "jumlah tower", "Company data"]},
            {"name": "Colocation", "value": 23303, "prev": 21185, "unit": "unit",
             "formula": "colocation", "source": "Company data",
             "row": ["Colocation", 23303, 21185, "+2118", "unit", "colocation", "Company data"]},
            {"name": "Tenant", "value": 63866, "prev": 60825, "unit": "tenant",
             "formula": "jumlah tenant", "source": "Company data",
             "row": ["Tenant", 63866, 60825, "+3041", "tenant", "jumlah tenant", "Company data"]},
            {"name": "Tenancy Ratio", "value": 1.57, "prev": 1.53, "unit": "x",
             "formula": "tenant/tower", "source": "Company data, data diolah",
             "row": ["Tenancy Ratio", 1.57, 1.53, "+0.04", "x", "tenant/tower", "Company data"]},
            {"name": "Fiber", "value": 59239, "prev": 54348, "unit": "km",
             "formula": "panjang jaringan", "source": "Company data",
             "row": ["Fiber", 59239, 54348, "+4891", "km", "panjang jaringan", "Company data"]},
        ],
        "kpis_src": "Company data 1H26, data diolah",
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
            {"title": "Laba Rugi Ringkas",
             "headers": ["Rp tn", "2023A", "2024A", "2025A", "2026F"],
             "rows": [["Pendapatan", 8.5, 9.1, 9.6, 10.0], ["EBITDA", 4.6, 5.3, 6.0, 6.6],
                      ["Laba bersih", 2.0, 2.2, 2.3, 2.4]],
             "source": "Laporan keuangan IDX"},
            {"title": "Rasio Lengkap",
             "headers": ["Rasio", "2023A", "2026F"],
             "rows": [["Current ratio (x)", 0.3, 0.8], ["LT D/E (x)", 0.34, 0.46],
                      ["DER (x)", 0.67, 0.69], ["ICR (x)", 2.0, 4.0], ["Cash ratio (%)", 8.0, 57.0]],
             "source": "Laporan keuangan IDX"},
        ],
        "risks": [
            {"bucket": "Ketergantungan operator (Telkomsel)", "detail": "Konsentrasi pendapatan pada operator besar.", "source": "KSI Research MTEL p.6, Laporan Tahunan"},
            {"bucket": "Kompetisi tower/satellite/Open RAN", "detail": "Teknologi alternatif menekan pricing tower.", "source": "Asosiasi Menara Telekomunikasi Indonesia"},
            {"bucket": "Regulasi spektrum & tarif", "detail": "Perubahan aturan memengaruhi ekspansi tenant.", "source": "Kementerian Kominfo, Regulasi Spektrum"},
            {"bucket": "Pembiayaan (suku bunga)", "detail": "Hutang fiber buildout sensitif bunga.", "source": "Bank Indonesia, Laporan Keuangan MTEL"},
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
