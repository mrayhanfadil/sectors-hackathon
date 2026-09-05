"""Tests for Method Selection Panel on Typst PDF cover.

5/5 PASS — one test per quintet ticker:
- BBCA -> DDM
- ADRO -> NAV
- CDIA -> DCF-thin with "⚠ Thin Data"
- RATU -> DCF
- MTEL -> DCF + SOTP cross-check
"""
from __future__ import annotations

import subprocess
from pathlib import Path
import pytest
from pypdf import PdfReader

from server.report.typst_renderer import render_report


def _extract_pdf_text(pdf_path: str | Path) -> str:
    r = subprocess.run(["pdftotext", "-layout", str(pdf_path), "-"], capture_output=True, text=True, check=True)
    return r.stdout


def _get_page_count(pdf_path: str | Path) -> int:
    reader = PdfReader(str(pdf_path))
    return len(reader.pages)


def test_cover_panel_ratu():
    """RATU -> Single archetype, DCF primary, mature, 7 pages."""
    pdf = render_report("RATU", archetype="auto")
    text = _extract_pdf_text(pdf)
    assert "Method Selection" in text or "METHOD SELECTION" in text
    assert "DCF" in text
    assert "Thin Data" not in text
    pages = _get_page_count(pdf)
    assert pages == 7, f"RATU expected 7 pages, got {pages}"


def test_cover_panel_bbca():
    """BBCA -> Bank, DDM primary."""
    pdf = render_report("BBCA", archetype="auto")
    text = _extract_pdf_text(pdf)
    assert "Method Selection" in text or "METHOD SELECTION" in text
    assert "DDM" in text
    pages = _get_page_count(pdf)
    assert pages == 7, f"BBCA expected 7 pages, got {pages}"


def test_cover_panel_adro():
    """ADRO -> Mining / Coal commodity, NAV primary."""
    pdf = render_report("ADRO", archetype="auto")
    text = _extract_pdf_text(pdf)
    assert "Method Selection" in text or "METHOD SELECTION" in text
    assert "NAV" in text
    pages = _get_page_count(pdf)
    assert pages == 7, f"ADRO expected 7 pages, got {pages}"


def test_cover_panel_cdia():
    """CDIA -> SOTP archetype, DCF (shortened horizon) with '⚠ Thin Data'."""
    pdf = render_report("CDIA", archetype="auto")
    text = _extract_pdf_text(pdf)
    assert "Method Selection" in text or "METHOD SELECTION" in text
    assert "DCF" in text
    assert "Thin Data" in text
    pages = _get_page_count(pdf)
    assert pages == 7, f"CDIA expected 7 pages, got {pages}"


def test_cover_panel_mtel():
    """MTEL -> Infra archetype, DCF primary + SOTP cross-check (NCI in 15-40% band)."""
    pdf = render_report("MTEL", archetype="auto")
    text = _extract_pdf_text(pdf)
    assert "Method Selection" in text or "METHOD SELECTION" in text
    assert "DCF" in text
    assert "SOTP" in text
    pages = _get_page_count(pdf)
    assert pages == 11, f"MTEL expected 11 pages, got {pages}"
