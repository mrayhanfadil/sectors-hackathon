"""Tests for Typst template leak and copy drift harness (Lane H2).

Verifies:
1. test_no_ratu_leak_for_synthetic_ticker: Minimal synthetic fixture produces PDF without RATU leaks.
2. test_template_copies_in_sync: server/report/typst/report_single.typ and templates/typst/archetypes/report_single.typ differ ONLY in the two #import lines.
3. test_ratu_regression: RATU render still contains RATU + 7880/7.880.
4. test_generic_fallback_no_ratu_defaults: Template defaults containing RATU/Banyu/Cepu/MEDC sit inside m.ticker == "RATU" branches.
"""
from __future__ import annotations

import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SERVER_TEMPLATE = REPO_ROOT / "server" / "report" / "typst" / "report_single.typ"
FALLBACK_TEMPLATE = REPO_ROOT / "templates" / "typst" / "archetypes" / "report_single.typ"
FIXTURES_DIR = REPO_ROOT / "scripts" / "fixtures"


@pytest.fixture(autouse=True)
def _loud_gate_inputs(monkeypatch):
    """LOUD policy: renderer refuses invented gate params — inject explicit
    test-owned inputs into whatever the loader returns (see
    tests/_loud_test_inputs.py). Leak assertions only."""
    import server.report.typst_renderer as TR
    from tests._loud_test_inputs import inject_gate_inputs, load_demo_fixture

    _orig = TR._load_or_build_report_data

    def _wrapped(ticker, archetype="auto"):
        # Tests declare demo inputs explicitly: fixture file/module first,
        # live loader only when no demo payload exists for the ticker.
        demo = load_demo_fixture(ticker)
        if demo is not None:
            return demo
        return inject_gate_inputs(_orig(ticker, archetype))

    monkeypatch.setattr(TR, "_load_or_build_report_data", _wrapped)

FORBIDDEN_LEAK_STRINGS = [
    "RATU",
    "Banyu",
    "Cepu",
    "Banyu Urip",
    "7.880",
    "7880",
    "MEDC",
    "ENRG",
    "ELSA",
    "PGAS",
    "Minas",
    "Tuban",
    "Ratu Prabu",
    "Raharja",
    "Raharja Energi Cepu",
    "RETJ",
    "PJUC",
]


def _extract_pdf_text(pdf_path: str | Path) -> str:
    """Extract text from PDF using pdftotext -layout."""
    r = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    return r.stdout


@pytest.fixture
def synthetic_test_fixture():
    """Minimal synthetic report data fixture for ticker 'TEST' without RATU keywords."""
    return {
        "meta": {
            "template": "single",
            "ticker": "TEST",
            "company_name": "Test Corp",
            "sector": "Teknologi Informasi",
            "report_type": "Initiation",
            "date": "05 Sep 2026",
            "prepared_by": "RESEARCH — Equity Report",
            "language": "id",
        },
        "cover": {
            "rating_box": {
                "action": "BUY",
                "tp": 1500,
                "prev_tp": 1300,
                "price": 1200,
                "upside_pct": 25.0,
                "key_takeaways": [
                    "Pertumbuhan pendapatan stabil di atas 20% YoY",
                    "Marjin EBITDA sehat ditopang efisiensi operasional",
                    "Valuasi DCF berbasis arus kas bebas positif",
                ],
            },
            "summary": "Inisiasi riset Test Corp dengan rekomendasi BUY.",
            "shares": {
                "outstanding": 1.0,
                "unit": "Miliar",
                "free_float_pct": 45.0,
            },
            "shareholders": [
                {"name": "PT Test Investama Jaya", "pct": "55,0%", "status": "Pengendali"},
                {"name": "Publik", "pct": "45,0%", "status": "Non-Warkat"},
            ],
            "shareholders_src": "KSEI & IDX",
            "price_chart": {
                "label": "Kinerja Harga TEST vs IHSG",
                "caption": "Performa Relatif YTD: Outperform",
            },
            "vs_jci": {
                "ytd_abs": 15.0,
                "ytd_rel": 5.0,
                "source": "IDX & yfinance",
            },
            "market": {
                "market_cap": "Rp 1,20 T",
                "range_52w": "1.000 - 1.600",
                "avg_value_3m": "Rp 5,0 M/hari",
                "index_class": "IDX Kompas100",
            },
        },
        "kpi_hero": {
            "paragraph": "Kinerja operasional Test Corp didorong oleh ekspansi layanan digital dan efisiensi biaya.",
            "cards": [
                {"label": "REVENUE", "value": "500", "unit": " Miliar", "note": "+20% YoY", "note_pos": True},
                {"label": "EBITDA MARGIN", "value": "25,0", "unit": "%", "note": "Stabil", "note_pos": True},
            ],
        },
        "ops_tables": {
            "exhibit_3": {
                "title": "Trajektori Parameter Operasional — Teknologi Informasi",
                "source": "Keterbukaan IDX",
                "headers": ["Parameter Operasional", "Nilai", "Satuan", "Keterangan", "Sumber"],
                "rows": [["Active Users", "1.000.000", "Users", "+15% YoY", "IDX"]],
            },
            "exhibit_4": {
                "title": "Karakteristik Aset & Jaringan Operasional",
                "source": "Profil Perusahaan",
                "headers": ["Komponen Aset", "Deskripsi & Kapasitas", "Mitra & Status Operasional"],
                "rows": [["Infrastruktur Cloud", "Data center terdistribusi", "Aktif"]],
            },
        },
        "moat": "Keunggulan kompetitif didukung oleh teknologi hak milik dan efek jaringan.",
        "financial_highlights": {
            "years": ["FY24A", "FY25A", "FY26F", "FY27F", "FY28F", "FY29F"],
            "source": "Laporan Keuangan TEST (IDX)",
            "rows": [
                ["Pendapatan Bersih", "350", "420", "500", "600", "720", "850"],
                ["EBITDA", "80", "100", "125", "150", "180", "215"],
                ["Laba Bersih", "45", "60", "78", "95", "118", "145"],
            ],
        },
        "thesis": [
            {"headline": "Ekspansi Pasar Digital", "detail": "Pertumbuhan adopsi teknologi di sektor korporasi.", "source": "IDX"},
            {"headline": "Struktur Neraca Solid", "detail": "Posisi kas bersih menopang ekspansi organik.", "source": "IDX"},
        ],
        "valuation": {
            "methods": [
                {
                    "method": "DCF",
                    "fv": 1500,
                    "assumptions": {"wacc": 10.0, "g": 5.0, "beta": 1.0, "rf": 6.5, "erp": 6.0},
                    "table": {
                        "headers": ["Komponen DCF (Rp bn)", "FY26F", "FY27F", "FY28F", "FY29F"],
                        "rows": [
                            ["Free Cash Flow (FCF)", "70", "85", "105", "130"],
                            ["Discount Factor", "0,909", "0,826", "0,751", "0,683"],
                            ["Present Value FCF", "64", "70", "79", "89"],
                        ],
                    },
                    "source": "Model DCF",
                },
                {
                    "method": "EV/EBITDA",
                    "fv": 1400,
                    "assumptions": {"multiple": 10.0, "ebitda_bn": 125},
                    "table": {
                        "headers": ["Parameter", "Nilai", "Satuan"],
                        "rows": [
                            ["Target EV/EBITDA", "10.0", "x"],
                            ["EBITDA", "125", "Rp bn"],
                            ["Implied EV", "1250", "Rp bn"],
                            ["Fair Value EV/EBITDA", "1400", "Rp/saham"],
                        ],
                    },
                },
            ],
            "blended": {"weights": "60/40", "fair_value": 1460},
            "dcf_grid": {
                "pv_explicit": "302",
                "pv_tv": "1050",
                "ev": "1352",
                "net_cash": "148",
            },
            "bands": {
                "rows": [
                    ["STD +2 (Batas Atas)", "2,5x", "Rp 1.800", "Overvalued Ekstrem"],
                    ["STD +1 (Batas Atas)", "2,0x", "Rp 1.500", "Overvalued Moderat"],
                    ["Rerata 3 Tahun (Mean)", "1,6x", "Rp 1.300", "Rentang Nilai Wajar"],
                    ["STD -1 (Batas Bawah)", "1,2x", "Rp 1.050", "Undervalued Menarik"],
                    ["STD -2 (Batas Bawah)", "0,9x", "Rp 850", "Undervalued Ekstrem"],
                    ["Posisi Harga Kini", "1,5x", "Rp 1.200", "Valuasi Wajar"],
                ]
            },
            "conclusion": "Harga saham TEST kini Rp 1.200 mencerminkan target harga Rp 1.500 dengan potensi upside +25,0% (BUY).",
        },
        "dcf_deep_dive": {
            "wacc_build": {
                "headers": ["Komponen WACC", "Nilai", "Metodologi / Sumber"],
                "rows": [
                    ["Risk-Free Rate (Rf)", "6,50%", "SBN 10Y"],
                    ["Equity Risk Premium (ERP)", "6,00%", "Damodaran Indonesia"],
                    ["Beta Raw & Adjusted", "1,000", "Regresi mingguan 3Y vs IHSG"],
                    ["Biaya Ekuitas (Ke)", "12,50%", "CAPM"],
                    ["WACC Final Diterapkan", "12,50%", "Struktur Modal Ekuitas Penuh"],
                ],
            },
            "sensitivity": {
                "headers": ["WACC \\ g", "4,50%", "5,00% (Base)", "5,50%"],
                "rows": [
                    ["11,50%", "Rp 1.620 (+35,0%)", "Rp 1.680 (+40,0%)", "Rp 1.750 (+45,8%)"],
                    ["12,50% (Base)", "Rp 1.450 (+20,8%)", "Rp 1.500 (+25,0%)", "Rp 1.560 (+30,0%)"],
                    ["13,50%", "Rp 1.300 (+8,3%)", "Rp 1.350 (+12,5%)", "Rp 1.400 (+16,7%)"],
                ],
            },
            "scenarios": {
                "headers": ["Scenario", "Nilai Wajar", "Investment Recommendation"],
                "rows": [
                    ["BEAR (Rev +10%, Marjin 20%)", "Rp 1.100", "HOLD (-8,3%)"],
                    ["BASE (Rev +20%, Marjin 25%)", "Rp 1.500", "BUY (+25,0%)"],
                    ["BULL (Rev +30%, Marjin 28%)", "Rp 1.900", "BUY (+58,3%)"],
                ],
            },
            "bridge": {
                "headers": ["Komponen Jembatan", "Nilai (Rp bn)", "Keterangan"],
                "rows": [
                    ["PV Explicit + PV Terminal", "1.352", "Enterprise Value"],
                    ["(+) Kas & Setara Kas", "+148", "Likuiditas Kas Bersih"],
                    ["(-) Total Utang Berbunga", "-0", "Bebas Utang"],
                    ["Implied Equity Value", "1.500", "Nilai Ekuitas Bersih"],
                ],
            },
        },
        "financial_statements": {
            "income": {
                "title": "Laporan Laba Rugi Komprehensif (Rp Miliar)",
                "source": "Laporan Keuangan TEST",
                "headers": ["Akun Laba Rugi", "FY24A", "FY25A", "FY26F", "FY27F", "FY28F", "FY29F"],
                "rows": [
                    ["Pendapatan Bersih", "350", "420", "500", "600", "720", "850"],
                    ["Beban Pokok Pendapatan", "-180", "-210", "-245", "-290", "-345", "-405"],
                    ["Laba Kotor", "170", "210", "255", "310", "375", "445"],
                    ["EBITDA", "80", "100", "125", "150", "180", "215"],
                    ["Laba Bersih Tahun Berjalan", "45", "60", "78", "95", "118", "145"],
                ],
            },
            "balance": {
                "title": "Neraca Keuangan Ringkas 6 Tahun (Rp Miliar)",
                "source": "Laporan Keuangan TEST",
                "headers": ["Pos Neraca", "FY24A", "FY25A", "FY26F", "FY27F", "FY28F", "FY29F"],
                "rows": [
                    ["Kas & Setara Kas", "100", "125", "148", "180", "220", "270"],
                    ["Total Aset", "450", "550", "680", "820", "990", "1190"],
                    ["Total Liabilitas", "90", "110", "130", "150", "170", "190"],
                    ["Total Ekuitas", "360", "440", "550", "670", "820", "1000"],
                ],
            },
            "ratios": {
                "title": "Rasio Keuangan & Efisiensi 6 Tahun",
                "source": "Perhitungan Analis",
                "headers": ["Rasio Kunci", "FY24A", "FY25A", "FY26F", "FY27F", "FY28F", "FY29F", "Peer Median"],
                "rows": [
                    ["Marjin Laba Kotor (%)", "48,6%", "50,0%", "51,0%", "51,7%", "52,1%", "52,4%", "45,0%"],
                    ["Marjin EBITDA (%)", "22,9%", "23,8%", "25,0%", "25,0%", "25,0%", "25,3%", "20,0%"],
                    ["Imbal Hasil Ekuitas (ROE)", "12,5%", "13,6%", "14,2%", "14,2%", "14,4%", "14,5%", "12,0%"],
                ],
            },
        },
        "peers": {
            "tables": [
                {
                    "pillar": "Teknologi Informasi",
                    "headers": ["Ticker", "Market Cap", "P/E (x)", "EV/EBITDA", "P/BV (x)", "ROE (%)", "Gearing"],
                    "rows": [
                        ["TEST", "Rp 1,2 T", "15,4x", "9,6x", "2,2x", "14,2%", "Net Cash"],
                        ["TECH1", "Rp 3,5 T", "18,2x", "11,0x", "2,8x", "15,0%", "0,15x"],
                        ["TECH2", "Rp 2,1 T", "14,0x", "8,5x", "1,9x", "13,5%", "Net Cash"],
                        ["Median Peers", "Rp 2,1 T", "15,4x", "9,6x", "2,2x", "14,2%", "Net Cash"],
                    ],
                    "source": "IDX & Perhitungan Analis",
                }
            ]
        },
        "risks": [
            {"bucket": "Risiko Persaingan", "detail": "Munculnya pemain baru dengan inovasi teknologi alternatif.", "source": "IDX"},
            {"bucket": "Risiko Keamanan Siber", "detail": "Gangguan sistem atau insiden kebocoran data pengguna.", "source": "IDX"},
        ],
    }


def test_no_ratu_leak_for_synthetic_ticker(synthetic_test_fixture, tmp_path):
    """Render synthetic fixture 'TEST' and assert zero RATU-specific strings in PDF."""
    from server.report.typst_renderer import render_report

    fixture_file = FIXTURES_DIR / "test_report_data.json"
    pdf_out = tmp_path / "test_synthetic_report.pdf"

    try:
        FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
        fixture_file.write_text(json.dumps(synthetic_test_fixture, ensure_ascii=False, indent=2), encoding="utf-8")

        rendered_pdf = render_report("TEST", archetype="single", out_path=str(pdf_out))
        assert Path(rendered_pdf).exists(), f"Rendered PDF does not exist: {rendered_pdf}"

        pdf_text = _extract_pdf_text(rendered_pdf)
        assert len(pdf_text) > 500, f"PDF text extracted is unexpectedly short ({len(pdf_text)} chars)"

        # Assert zero forbidden strings
        leaks_found = []
        for s in FORBIDDEN_LEAK_STRINGS:
            # Check whole word / substring presence
            if s.lower() in pdf_text.lower():
                leaks_found.append(s)

        assert not leaks_found, (
            f"RATU template leak detected in synthetic TEST render! Forbidden strings found: {leaks_found}\n"
            f"Extracted PDF text snippet:\n{pdf_text[:1000]}..."
        )
    finally:
        if fixture_file.exists():
            fixture_file.unlink()


def test_template_copies_in_sync():
    """Assert server and templates copies of report_single.typ differ ONLY in the two #import lines."""
    assert SERVER_TEMPLATE.exists(), f"Server template missing: {SERVER_TEMPLATE}"
    assert FALLBACK_TEMPLATE.exists(), f"Fallback template missing: {FALLBACK_TEMPLATE}"

    server_raw = SERVER_TEMPLATE.read_text(encoding="utf-8")
    fallback_raw = FALLBACK_TEMPLATE.read_text(encoding="utf-8")

    # Normalize server import paths to match fallback relative imports
    normalized_server = server_raw.replace(
        '#import "theme.typ": *', '#import "../common/theme.typ": *'
    ).replace(
        '#import "cover.typ": *', '#import "../common/cover.typ": *'
    )

    if normalized_server != fallback_raw:
        server_lines = server_raw.splitlines(keepends=True)
        fallback_lines = fallback_raw.splitlines(keepends=True)
        diff = "".join(
            difflib.unified_diff(
                server_lines,
                fallback_lines,
                fromfile=str(SERVER_TEMPLATE),
                tofile=str(FALLBACK_TEMPLATE),
            )
        )
        pytest.fail(
            f"Templates out of sync! server/report/typst/report_single.typ and "
            f"templates/typst/archetypes/report_single.typ have drifted beyond import lines:\n\n{diff}"
        )


def test_ratu_regression(tmp_path):
    """Render RATU via render_report and assert PDF text still contains RATU + 7880/7.880."""
    from server.report.typst_renderer import render_report

    pdf_out = tmp_path / "ratu_regression_report.pdf"
    rendered_pdf = render_report("RATU", archetype="single", out_path=str(pdf_out))
    assert Path(rendered_pdf).exists(), f"Rendered RATU PDF missing: {rendered_pdf}"

    pdf_text = _extract_pdf_text(rendered_pdf)
    assert "RATU" in pdf_text, "RATU regression: 'RATU' ticker missing from rendered PDF"
    assert ("7880" in pdf_text) or ("7.880" in pdf_text), (
        "RATU regression: Target price 7880 / 7.880 missing from rendered PDF"
    )


def test_generic_fallback_no_ratu_defaults():
    """Grep template source: every default literal containing RATU/Banyu/Cepu/MEDC must sit inside m.ticker == 'RATU' branch."""
    keywords = ["RATU", "Banyu", "Cepu", "MEDC", "Ratu Prabu", "Raharja", "Banyu Urip", "7.880", "7880", "RETJ", "PJUC"]

    violations = []

    for template_path in [SERVER_TEMPLATE, FALLBACK_TEMPLATE]:
        lines = template_path.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines, 1):
            # Check lines with default: literals or fallback assignments
            if "default:" in line:
                for kw in keywords:
                    if kw.lower() in line.lower():
                        # Allowed only if line or enclosing condition explicitly guards with m.ticker == "RATU"
                        if 'm.ticker == "RATU"' not in line and 'ticker == "RATU"' not in line:
                            violations.append(f"{template_path.name}:{idx}: {line.strip()}")
                            break

    assert not violations, (
        f"Found RATU defaults not guarded by m.ticker == 'RATU':\n" + "\n".join(violations)
    )
