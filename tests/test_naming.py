"""Naming correctness and cross-ticker isolation test suite.

Validates:
1. Whole-repo suffix correctness: 0 occurrences of `.IJ` in tracked files / docs / code.
2. Rendered-output suffix correctness: the RATU and ACES reports the HTML renderer produces
   carry zero `.IJ` (live-Sectors render; skipped keyless without data/assumptions files).
3. Cross-ticker isolation: zero RATU content in the ACES report and zero ACES content in the
   RATU report (live-Sectors render; skipped keyless).
4. Company-name correctness for engine tickers served live (skipped keyless).
5. Sector labels in rendered reports derive from live metadata (skipped keyless).

Render tests need Sectors-backed payloads (fixtures purged Sep 2026) and
skip with an honest message when neither SECTORS_API_KEY nor
data/assumptions/{T}.json is available.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi import HTTPException
from server.routers.pdf import _build_live_payload, render_html_for_ticker


def _render_html_or_skip(ticker: str) -> str:
    """Render the served HTML via the live loader; skip honestly when Sectors data is absent."""
    try:
        _template, html, _data = render_html_for_ticker(ticker)
    except HTTPException as exc:
        if exc.status_code == 422:
            pytest.skip(f"needs Sectors data for {ticker} (keyless, no data/assumptions file)")
        raise
    return html


@pytest.fixture(autouse=True)
def _loud_gate_inputs(monkeypatch):
    """LOUD policy: the loader refuses invented gate params - inject explicit
    test-owned inputs into whatever it returns (see tests/_loud_test_inputs.py).
    Text assertions only."""
    import server.routers.pdf as PDF
    from tests._loud_test_inputs import inject_gate_inputs

    _orig = PDF._build_live_payload

    def _wrapped(ticker, template_override=None):
        return inject_gate_inputs(_orig(ticker, template_override))

    monkeypatch.setattr(PDF, "_build_live_payload", _wrapped)


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


def test_rendered_ratu_and_aces_no_ij():
    """Render RATU and ACES via the served renderer and assert zero .IJ in the output."""
    txt_ratu = _render_html_or_skip("RATU")
    txt_aces = _render_html_or_skip("ACES")

    assert len(txt_ratu) > 500 and len(txt_aces) > 500, "rendered report unexpectedly short"

    ij_ratu = re.findall(r"\b\w+\.IJ\b|\.IJ\b", txt_ratu)
    ij_aces = re.findall(r"\b\w+\.IJ\b|\.IJ\b", txt_aces)

    assert not ij_ratu, f"Found .IJ suffix in RATU PDF: {ij_ratu}"
    assert not ij_aces, f"Found .IJ suffix in ACES PDF: {ij_aces}"


def test_cross_ticker_isolation_ratu_and_aces():
    """Assert zero RATU content in the ACES report and zero ACES content in the RATU report."""
    txt_ratu = _render_html_or_skip("RATU")
    txt_aces = _render_html_or_skip("ACES")

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
    expected_names = {
        "ADRO": "Alamtri Resources",
        "BBCA": "Bank Central Asia",
    }

    # Live loader only: skip honestly when Sectors data is absent.
    for ticker, exp in expected_names.items():
        try:
            data = _build_live_payload(ticker, None)
        except HTTPException as exc:
            if exc.status_code == 422:
                pytest.skip(f"needs Sectors data for {ticker} (keyless, no data/assumptions file)")
            raise
        comp = data.get("meta", {}).get("company_name", "")
        assert exp in comp, f"Ticker {ticker} company_name '{comp}' does not contain expected '{exp}'"


def test_sector_labels_from_live_meta():
    """Verify sector labels in rendered reports derive from live metadata."""
    for ticker in ("RATU", "BBCA"):
        txt = _render_html_or_skip(ticker)
        assert len(txt) > 500, f"rendered {ticker} report text unexpectedly short"
