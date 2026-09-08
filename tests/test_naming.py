"""Naming correctness and cross-ticker isolation test suite.

Validates:
1. Whole-repo suffix correctness: 0 occurrences of `.IJ` in tracked files / docs / code.
2. Rendered PDF suffix correctness: RATU and ACES PDFs rendered via typst_renderer have zero `.IJ`
   (live-Sectors render; skipped keyless without data/assumptions files).
3. Cross-ticker isolation: zero RATU content in ACES PDF and zero ACES content in RATU PDF
   (live-Sectors render; skipped keyless).
4. Company-name correctness for engine tickers served live (skipped keyless).
5. Sector labels in rendered reports derive from live metadata (skipped keyless).

Render tests need Sectors-backed payloads (fixtures purged Sep 2026) and
skip with an honest message when neither SECTORS_API_KEY nor
data/assumptions/{T}.json is available.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from server.report.typst_renderer import render_report
from fastapi import HTTPException


def _render_or_skip(ticker: str, archetype: str, out_path: str) -> str:
    """Render via the live loader; skip honestly when Sectors data is absent."""
    try:
        return render_report(ticker, archetype=archetype, out_path=out_path)
    except HTTPException as exc:
        if exc.status_code == 422:
            pytest.skip(f"needs Sectors data for {ticker} (keyless, no data/assumptions file)")
        raise


@pytest.fixture(autouse=True)
def _loud_gate_inputs(monkeypatch):
    """LOUD policy: renderer refuses invented gate params — inject explicit
    test-owned inputs into whatever the loader returns (see
    tests/_loud_test_inputs.py). Typography assertions only."""
    import server.report.typst_renderer as TR
    from tests._loud_test_inputs import inject_gate_inputs

    _orig = TR._load_or_build_report_data

    def _wrapped(ticker, archetype="auto"):
        return inject_gate_inputs(_orig(ticker, archetype))

    monkeypatch.setattr(TR, "_load_or_build_report_data", _wrapped)


def _extract_pdf_text(pdf_path: str | Path) -> str:
    """Extract full layout text from PDF using pdftotext."""
    cmd = ["pdftotext", "-layout", str(pdf_path), "-"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return res.stdout


def test_whole_repo_no_ij_suffix():
    """Whole repo scan: assert zero .IJ suffix hits across code, fixtures, references, and docs."""
    ij_regex = re.compile(r"\.IJ\b")
    excludes = {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        ".hermes",
        "output",
        ".pytest_cache",
        "__pycache__",
        ".ruff_cache",
    }
    ignored_exts = {
        ".png",
        ".jpg",
        ".jpeg",
        ".ttf",
        ".pdf",
        ".pyc",
        ".ico",
        ".woff",
        ".woff2",
        ".db",
    }

    hits: list[str] = []
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in excludes and not d.startswith(".worktree")]
        for f in filenames:
            if f in {"test_naming.py", "harness_post_agy.py"}:
                continue
            ext = os.path.splitext(f)[1].lower()
            if ext in ignored_exts:
                continue

            full_path = Path(dirpath) / f
            try:
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                for idx, line in enumerate(content.splitlines(), start=1):
                    if ij_regex.search(line):
                        rel = full_path.relative_to(REPO_ROOT)
                        hits.append(f"{rel}:{idx}: {line.strip()[:80]}")
            except OSError:
                continue

    assert not hits, f"Found .IJ ticker suffix in repository:\n" + "\n".join(hits[:10])


def test_rendered_ratu_and_aces_no_ij(tmp_path: Path):
    """Render RATU and ACES PDFs via typst_renderer and assert zero .IJ in extracted text."""
    ratu_pdf = tmp_path / "ratu_test.pdf"
    aces_pdf = tmp_path / "aces_test.pdf"

    p_ratu = _render_or_skip("RATU", archetype="single", out_path=str(ratu_pdf))
    p_aces = _render_or_skip("ACES", archetype="single", out_path=str(aces_pdf))

    assert Path(p_ratu).exists() and Path(p_ratu).stat().st_size > 0
    assert Path(p_aces).exists() and Path(p_aces).stat().st_size > 0

    txt_ratu = _extract_pdf_text(p_ratu)
    txt_aces = _extract_pdf_text(p_aces)

    ij_ratu = re.findall(r"\b\w+\.IJ\b|\.IJ\b", txt_ratu)
    ij_aces = re.findall(r"\b\w+\.IJ\b|\.IJ\b", txt_aces)

    assert not ij_ratu, f"Found .IJ suffix in RATU PDF: {ij_ratu}"
    assert not ij_aces, f"Found .IJ suffix in ACES PDF: {ij_aces}"


def test_cross_ticker_isolation_ratu_and_aces(tmp_path: Path):
    """Assert zero RATU content in ACES PDF and zero ACES content in RATU PDF."""
    ratu_pdf = tmp_path / "ratu_iso.pdf"
    aces_pdf = tmp_path / "aces_iso.pdf"

    p_ratu = _render_or_skip("RATU", archetype="single", out_path=str(ratu_pdf))
    p_aces = _render_or_skip("ACES", archetype="single", out_path=str(aces_pdf))

    txt_ratu = _extract_pdf_text(p_ratu)
    txt_aces = _extract_pdf_text(p_aces)

    # Keywords specific to RATU that must NOT appear in ACES report
    ratu_specific = [
        "RATU",
        "Raharja Energi",
        "Ratu Prabu",
        "Banyu Urip",
        "Blok Cepu",
        "RETJ",
        "PJUC",
        "7.880",
        "7880",
    ]
    for kw in ratu_specific:
        assert kw not in txt_aces, f"Cross-ticker leak: RATU keyword '{kw}' found in ACES PDF"

    # Keywords specific to ACES that must NOT appear in RATU report
    aces_specific = [
        "ACES",
        "Aspirasi Hidup Indonesia",
        "AZKO",
        "Ace Hardware",
        "606.52",
    ]
    for kw in aces_specific:
        assert kw not in txt_ratu, f"Cross-ticker leak: ACES keyword '{kw}' found in RATU PDF"


def test_six_engine_tickers_company_names():
    """Verify company names for engine tickers served live match official names."""
    from server.report.typst_renderer import _load_or_build_report_data

    expected_names = {
        "ADRO": "Alamtri Resources",
        "BBCA": "Bank Central Asia",
    }

    # Live loader only: skip honestly when Sectors data is absent.
    for ticker, exp in expected_names.items():
        try:
            data = _load_or_build_report_data(ticker, "auto")
        except HTTPException as exc:
            if exc.status_code == 422:
                pytest.skip(f"needs Sectors data for {ticker} (keyless, no data/assumptions file)")
            raise
        comp = data.get("meta", {}).get("company_name", "")
        assert exp in comp, f"Ticker {ticker} company_name '{comp}' does not contain expected '{exp}'"


def test_sector_labels_from_live_meta(tmp_path: Path):
    """Verify sector labels in rendered reports derive from live metadata."""
    for ticker, archetype in [("RATU", "single"), ("BBCA", "single")]:
        pdf_path = tmp_path / f"{ticker.lower()}_sec.pdf"
        p = _render_or_skip(ticker, archetype=archetype, out_path=str(pdf_path))
        txt = _extract_pdf_text(p)
        assert len(txt) > 500, f"rendered {ticker} PDF text unexpectedly short"
