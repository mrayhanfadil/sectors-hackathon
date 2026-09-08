"""End-to-end behavioral smoke tests for institutional Typst PDF reports.

Renders benchmark archetypes from live Sectors-backed payloads (fixtures
purged Sep 2026) to assert rendered PDFs comply with the Valuation Method
Selection Framework contract, page baselines, font embeddings, FY
standardization, and corporate section conventions. Skips honestly keyless
without data/assumptions files.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
FIXTURES_DIR = SCRIPTS_DIR / "fixtures"
TEMPLATES_DIR = PROJECT_ROOT / "templates" / "typst" / "archetypes"
FONTS_DIR = PROJECT_ROOT / "assets" / "fonts"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from agents.valuation.gates import evaluate
from scripts.render_typst import compile_typst, generate_charts
from server.report.typst_renderer import (
    _build_gate_verdict_dict,
    _get_ticker_gate_params,
    _load_or_build_report_data,
)

pytestmark = pytest.mark.slow

ARCHETYPE_TEMPLATES = {
    "single": TEMPLATES_DIR / "report_single.typ",
    "sotp": TEMPLATES_DIR / "report_sotp.typ",
    "infra": TEMPLATES_DIR / "report_infra.typ",
    "strategy": TEMPLATES_DIR / "report_strategy.typ",
}

TICKER_ARCHETYPES = {
    "RATU": "single",
    "CDIA": "sotp",
    "MTEL": "infra",
    "JCI": "strategy",
    "BBCA": "single",
    "ADRO": "single",
}


def _extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from PDF using pdftotext -layout."""
    r = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    return r.stdout


def _get_page_count(pdf_path: Path) -> int:
    """Extract page count from PDF using pdfinfo."""
    r = subprocess.run(
        ["pdfinfo", str(pdf_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    for line in r.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":")[1].strip())
    raise ValueError(f"Page count not found in pdfinfo for {pdf_path}")


def _get_embedded_font_names(pdf_path: Path) -> list[str]:
    """Extract embedded font names using pdffonts."""
    r = subprocess.run(
        ["pdffonts", str(pdf_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = r.stdout.splitlines()
    fonts = []
    if len(lines) > 2:
        for line in lines[2:]:
            parts = line.split()
            if len(parts) >= 4:
                fonts.append(parts[0])
    return fonts


@pytest.fixture(scope="module")
def rendered_reports(tmp_path_factory) -> dict[str, dict[str, Any]]:
    """Render all archetypes (+ quintet tickers) once and cache outputs.

    Live Sectors-backed payloads only (fixtures purged Sep 2026). Skips the
    whole module honestly when Sectors data is absent.
    """
    from fastapi import HTTPException

    cache_base = tmp_path_factory.mktemp("pdf_smoke")
    palette = {
        "brand": "#067647",
        "brand_dark": "#054f31",
        "accent": "#ecfdf3",
        "ink": "#101828",
        "muted": "#475467",
        "line": "#e4e7ec",
        "band": "#f9fafb",
        "paper": "#ffffff",
        "pos": "#067647",
        "neg": "#b42318",
    }

    reports: dict[str, dict[str, Any]] = {}

    for ticker, archetype in TICKER_ARCHETYPES.items():
        tpl_path = ARCHETYPE_TEMPLATES[archetype]
        assert tpl_path.exists(), f"Typst template missing: {tpl_path}"

        try:
            data = _load_or_build_report_data(ticker, archetype="auto")
        except HTTPException as exc:
            if exc.status_code == 422:
                pytest.skip(f"needs Sectors data for {ticker} (keyless, no data/assumptions file)")
            raise

        # LOUD policy: renderer refuses invented gate params — tests supply
        # explicit test-owned inputs (see tests/_loud_test_inputs.py).
        from tests._loud_test_inputs import inject_gate_inputs

        inject_gate_inputs(data)

        # Inject gate verdict for tickers with method selection framework
        if ticker != "JCI":
            params = _get_ticker_gate_params(ticker, data)
            rating = data.get("cover", {}).get("rating_box", {}).get("action", "BUY")
            verdict = evaluate(ticker, **params)
            gate_dict = _build_gate_verdict_dict(ticker, verdict, params, rating)
            data["gate-verdict"] = gate_dict
            data["gate_verdict"] = gate_dict

        t_dir = cache_base / f"render_{ticker.lower()}"
        t_dir.mkdir(parents=True, exist_ok=True)
        data_path = t_dir / "report_data.json"
        data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        # Generate charts locally without network
        generate_charts(ticker, data, palette)

        out_pdf = cache_base / f"{ticker.lower()}_smoke.pdf"
        ok = compile_typst(tpl_path, out_pdf, ticker=ticker, data_path=data_path)
        assert ok, f"Typst compilation failed for {ticker} ({archetype}) at {out_pdf}"
        assert out_pdf.exists(), f"Output PDF does not exist: {out_pdf}"

        text = _extract_pdf_text(out_pdf)
        pages = _get_page_count(out_pdf)
        fonts = _get_embedded_font_names(out_pdf)

        reports[ticker] = {
            "ticker": ticker,
            "archetype": archetype,
            "pdf_path": out_pdf,
            "page_count": pages,
            "text": text,
            "fonts": fonts,
            "data": data,
        }

    return reports


def test_page_count_baseline(rendered_reports):
    """Page count baseline preserved across archetypes: single=7, sotp=7, infra=11, strategy=5."""
    assert rendered_reports["RATU"]["page_count"] == 7, "RATU (single) expected 7 pages"
    # SOTP baseline is 7 pages; accommodates 8 pages when 4-pillar peer tables include median rows
    assert rendered_reports["CDIA"]["page_count"] in (7, 8), "CDIA (sotp) expected 7 or 8 pages"
    assert rendered_reports["MTEL"]["page_count"] == 11, "MTEL (infra) expected 11 pages"
    assert rendered_reports["JCI"]["page_count"] == 5, "JCI (strategy) expected 5 pages"


def test_fy_columns_income_statement(rendered_reports):
    """6 FY columns in income statement: FY24A FY25A FY26F FY27F FY28F FY29F."""
    expected_fys = ["FY24A", "FY25A", "FY26F", "FY27F", "FY28F", "FY29F"]
    for ticker in ["RATU", "CDIA", "MTEL"]:
        text = rendered_reports[ticker]["text"]
        missing = [fy for fy in expected_fys if fy not in text]
        assert not missing, f"{ticker} income statement missing FY columns: {missing}"


def test_embedded_fonts(rendered_reports):
    """Embedded SourceSerif4 + Inter fonts via pdffonts across all 4 archetypes."""
    for ticker in ["RATU", "CDIA", "MTEL", "JCI"]:
        pdf_path = rendered_reports[ticker]["pdf_path"]
        r = subprocess.run(["pdffonts", str(pdf_path)], capture_output=True, text=True, check=True)
        fonts_output = r.stdout
        has_serif = ("SourceSerif4" in fonts_output) or ("Source Serif 4" in fonts_output)
        has_inter = "Inter" in fonts_output
        assert has_serif, f"{ticker} missing embedded Source Serif 4 font in:\n{fonts_output}"
        assert has_inter, f"{ticker} missing embedded Inter font in:\n{fonts_output}"


def test_peer_comparison_median_row(rendered_reports):
    """All 4 archetypes must contain 'Median' in peer comparison tables (Issue 8)."""
    for ticker in ["RATU", "CDIA", "MTEL", "JCI"]:
        text = rendered_reports[ticker]["text"]
        assert "median" in text.lower(), f"{ticker} missing 'Median' row in peer comparison tables"


def test_framework_section_names(rendered_reports):
    """All standard corporate section names are present across the 4 archetypes."""
    expected_sections = [
        "Investment Recommendation",
        "Valuation Methodology",
        "Executive Summary",
        "Sensitivity Analysis",
        "Peer Comparison",
        "Investment Risks",
        "Cost of Capital Build",
    ]
    # Check comprehensive coverage across the full 4-archetype suite
    all_text = " ".join([rendered_reports[t]["text"] for t in ["RATU", "CDIA", "MTEL", "JCI"]])
    for sec in expected_sections:
        assert sec.lower() in all_text.lower(), f"Section '{sec}' missing from rendered report suite"

    # Per-archetype section presence
    for t in ["RATU", "MTEL"]:
        for sec in expected_sections:
            assert sec.lower() in rendered_reports[t]["text"].lower(), f"{t} missing section '{sec}'"


def test_method_selection_panel_heading(rendered_reports):
    """Method Selection Framework / Valuation Methodology panel heading present on cover."""
    for ticker in ["RATU", "CDIA", "MTEL", "BBCA", "ADRO"]:
        text = rendered_reports[ticker]["text"]
        has_heading = ("valuation methodology" in text.lower()) or ("method selection" in text.lower())
        assert has_heading, f"{ticker} missing Method Selection / Valuation Methodology panel heading"
        assert "gate" in text.lower(), f"{ticker} missing Gate Verdict table in panel"

    # JCI has no panel since it's a strategy benchmark
    assert "gate verdict" not in rendered_reports["JCI"]["text"].lower()


def test_ticker_ratu_contract(rendered_reports):
    """RATU: primary=FCFF/WACC DCF in panel, no thin_data banner."""
    params = _get_ticker_gate_params("RATU", rendered_reports["RATU"]["data"])
    verdict = evaluate("RATU", **params)
    assert verdict.primary == "FCFF/WACC DCF"

    text = rendered_reports["RATU"]["text"]
    assert "DCF" in text
    assert "Thin Data" not in text
    assert "⚠" not in text


def test_ticker_cdia_contract(rendered_reports):
    """CDIA: primary=Relative Valuation (ramping fleet), thin-data banner present."""
    params = _get_ticker_gate_params("CDIA", rendered_reports["CDIA"]["data"])
    verdict = evaluate("CDIA", **params)
    assert verdict.primary == "Relative Valuation"
    assert verdict.thin_data is True

    text = rendered_reports["CDIA"]["text"]
    assert "Thin Data" in text
    assert "⚠ Thin Data" in text


def test_ticker_mtel_contract(rendered_reports):
    """MTEL: primary=FCFF/WACC DCF, 'SOTP cross-check' reason in panel."""
    params = _get_ticker_gate_params("MTEL", rendered_reports["MTEL"]["data"])
    verdict = evaluate("MTEL", **params)
    assert verdict.primary == "FCFF/WACC DCF"

    text = rendered_reports["MTEL"]["text"]
    assert re.search(r"SOTP\s*cross[-\s]*check", text, re.IGNORECASE), (
        "MTEL missing 'SOTP cross-check' reason in Method Selection Panel"
    )


def test_ticker_bbca_contract(rendered_reports):
    """BBCA: primary=DDM / Excess Return in panel."""
    params = _get_ticker_gate_params("BBCA", rendered_reports["BBCA"]["data"])
    verdict = evaluate("BBCA", **params)
    assert verdict.primary == "DDM / Excess Return"

    text = rendered_reports["BBCA"]["text"]
    assert "DDM" in text
    assert "Excess Return" in text


def test_ticker_adro_contract(rendered_reports):
    """ADRO: primary=NAV / Reserve-based in panel."""
    params = _get_ticker_gate_params("ADRO", rendered_reports["ADRO"]["data"])
    verdict = evaluate("ADRO", **params)
    assert verdict.primary == "NAV / Reserve-based"

    text = rendered_reports["ADRO"]["text"]
    assert "NAV" in text
