"""Production purity tests (AGY-2): verify complete removal of fabricated fallbacks.

Context (purge, Sep 2026):
- data/sectors.db git-removed (seed=42 database removed)
- yfinance dependency removed from server/requirements.txt and zero imports under server/
- scripts/report_fixtures.py + scripts/fixtures/*.json DELETED; zero references under server/ and src/fe/
- pdf._load_fixture helper REMOVED (was dead canary, now gone)
- agents/collector.py synthetic path neutered to raise RuntimeError(sectors_missing_key)
- pdf-route + typst-renderer prod loaders 422 keyless without data/assumptions files
- no 'Sectors (' provenance strings on honest prod skeletons
"""

from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path
import re
import sys
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.collector import _synthetic, _peers_for, collect, QUINTET
from server.main import app
from server.report.typst_renderer import _load_or_build_report_data
from server.routers.pdf import render_html_for_ticker
from tests._loud_test_inputs import load_demo_fixture


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. data/sectors.db does not exist
# ---------------------------------------------------------------------------

def test_sectors_db_does_not_exist():
    """Assert data/sectors.db was git-removed and does not exist on disk."""
    db_file = REPO_ROOT / "data" / "sectors.db"
    assert not db_file.exists(), f"data/sectors.db must not exist on disk: {db_file}"

    # Also verify no sectors.db exists anywhere under data/
    data_dir = REPO_ROOT / "data"
    if data_dir.exists():
        found = list(data_dir.rglob("sectors.db"))
        assert not found, f"Found lingering sectors.db under data/: {found}"


# ---------------------------------------------------------------------------
# 2. zero `import yfinance` under server/ (walk the tree)
# ---------------------------------------------------------------------------

def test_zero_yfinance_imports_under_server():
    """Walk server/ tree and assert zero imports of yfinance across all Python files."""
    server_dir = REPO_ROOT / "server"
    assert server_dir.exists(), "server/ directory must exist"

    py_files = list(server_dir.rglob("*.py"))
    assert len(py_files) > 0, "Expected Python files under server/"

    yf_ast_imports: list[tuple[str, str]] = []
    yf_text_matches: list[tuple[str, int, str]] = []

    for py_path in py_files:
        content = py_path.read_text(encoding="utf-8")
        rel_path = py_path.relative_to(REPO_ROOT).as_posix()

        # 1. AST check for Import and ImportFrom nodes
        try:
            tree = ast.parse(content, filename=str(py_path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "yfinance" or alias.name.startswith("yfinance."):
                            yf_ast_imports.append((rel_path, alias.name))
                elif isinstance(node, ast.ImportFrom):
                    if node.module and (node.module == "yfinance" or node.module.startswith("yfinance.")):
                        yf_ast_imports.append((rel_path, node.module))
        except SyntaxError:
            pytest.fail(f"Syntax error parsing {rel_path}")

        # 2. Line-by-line check for un-commented import statements
        for idx, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "import yfinance" in stripped or "from yfinance" in stripped:
                yf_text_matches.append((rel_path, idx, stripped))

    assert not yf_ast_imports, f"Found yfinance AST imports in server/: {yf_ast_imports}"
    assert not yf_text_matches, f"Found active yfinance import lines in server/: {yf_text_matches}"


def test_yfinance_removed_from_server_requirements():
    """Assert server/requirements.txt does not declare yfinance."""
    req_path = REPO_ROOT / "server" / "requirements.txt"
    if req_path.exists():
        req_text = req_path.read_text(encoding="utf-8")
        lines = [line.strip().lower() for line in req_text.splitlines() if line.strip() and not line.startswith("#")]
        yf_entries = [line for line in lines if line.startswith("yfinance")]
        assert not yf_entries, f"server/requirements.txt must not contain yfinance: {yf_entries}"


# ---------------------------------------------------------------------------
# 3. zero prod importers of scripts/report_fixtures.py under server/ and src/fe/
# ---------------------------------------------------------------------------

def test_zero_prod_importers_of_report_fixtures_under_src_fe():
    """Assert zero references to report_fixtures across frontend files in src/fe/."""
    fe_dir = REPO_ROOT / "src" / "fe"
    if not fe_dir.exists():
        return

    fe_files = [
        p for p in fe_dir.rglob("*")
        if p.is_file() and p.suffix in (".ts", ".tsx", ".js", ".jsx", ".json", ".html", ".css")
        and not any(part in ("node_modules", "dist", "build", ".tanstack", ".wrangler") for part in p.parts)
    ]
    fe_matches: list[str] = []
    for fp in fe_files:
        text = fp.read_text(encoding="utf-8", errors="ignore")
        if "report_fixtures" in text:
            fe_matches.append(fp.relative_to(REPO_ROOT).as_posix())

    assert not fe_matches, f"Found report_fixtures references in src/fe/: {fe_matches}"


def test_zero_prod_importers_of_report_fixtures_in_server():
    """Assert no top-level imports of report_fixtures in any server module."""
    server_dir = REPO_ROOT / "server"
    for py_path in server_dir.rglob("*.py"):
        tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
        for stmt in tree.body:
            rel = py_path.relative_to(REPO_ROOT).as_posix()
            if isinstance(stmt, ast.Import):
                for alias in stmt.names:
                    assert "report_fixtures" not in alias.name, f"Top-level import of report_fixtures in {rel}"
            elif isinstance(stmt, ast.ImportFrom):
                if stmt.module:
                    assert "report_fixtures" not in stmt.module, f"Top-level import from report_fixtures in {rel}"


def test_load_fixture_helper_removed_from_pdf():
    """Assert pdf._load_fixture is fully removed from server/ (purge, Sep 2026)."""
    server_dir = REPO_ROOT / "server"
    hits: list[str] = []
    for py_path in server_dir.rglob("*.py"):
        lines = py_path.read_text(encoding="utf-8").splitlines()
        for i, raw in enumerate(lines, 1):
            if "_load_fixture" in raw:
                hits.append(f"{py_path.relative_to(REPO_ROOT)}:{i}: {raw.strip()}")
    assert not hits, f"_load_fixture resurrected in server/: {hits}"


# ---------------------------------------------------------------------------
# 4. collector neutered synthetic path raises (agents/collector.py)
# ---------------------------------------------------------------------------

def test_collector_synthetic_function_raises():
    """Assert agents/collector.py::_synthetic raises RuntimeError with sectors_missing_key."""
    for ticker in (*QUINTET, "TEST"):
        with pytest.raises(RuntimeError) as exc_info:
            _synthetic(ticker)
        msg = str(exc_info.value)
        assert "sectors_missing_key" in msg, f"_synthetic({ticker}) must mention sectors_missing_key"
        assert "synthetic fallback retired" in msg.lower(), f"_synthetic({ticker}) must mention synthetic fallback retired"


def test_collector_collect_keyless_raises_runtime_error(monkeypatch):
    """Assert collect() without local IDX dump or API key raises RuntimeError (no synthetic fallback)."""
    import agents.collector as C
    monkeypatch.setattr(C, "_try_idx", lambda ticker: None)
    monkeypatch.setattr(C, "_try_sectors", lambda ticker: None)

    with pytest.raises(RuntimeError) as exc_info:
        C.collect("RATU", use_cache=False)
    msg = str(exc_info.value)
    assert "sectors_missing_key" in msg, f"collect() must mention sectors_missing_key, got: {msg}"
    assert "synthetic fallback retired" in msg.lower() or "no idx dump" in msg.lower()


def test_collector_peers_for_returns_honest_missing_key_source():
    """Assert _peers_for returns empty peers with source='sectors_missing_key' when no peers file."""
    res = _peers_for("NONEXISTENT_TICKER_FOR_TEST")
    assert isinstance(res, dict)
    assert res.get("source") == "sectors_missing_key"
    assert res.get("peers") == []


# ---------------------------------------------------------------------------
# 5. pdf-route + typst-renderer prod loaders serve no fixture payload
#    without explicit load_demo_fixture()
# ---------------------------------------------------------------------------

def test_typst_renderer_prod_loader_no_fixture_interception():
    """Assert _load_or_build_report_data does not serve rich demo fixtures automatically."""
    # 1. BBCA & ADRO return honest-empty skeleton (refusing fabricated exhibits)
    for ticker in ("BBCA", "ADRO"):
        data = _load_or_build_report_data(ticker, "auto")
        assert data["financial_highlights"]["rows"] == []
        assert "no fixture/builder" in data["financial_highlights"]["source"]
        assert "refusing fabricated exhibits" in data["financial_highlights"]["source"]

    # 2. RATU / CDIA / MTEL in keyless/unverified environment raise 422 or return live empty highlights, NOT fixture
    for ticker in ("RATU", "CDIA", "MTEL"):
        try:
            prod_data = _load_or_build_report_data(ticker, "auto")
            assert prod_data["financial_highlights"]["rows"] == [], f"Prod loader must not return fixture rows for {ticker}"
            assert prod_data["financial_highlights"]["source"] == "sectors_missing_key"
        except HTTPException as exc:
            assert exc.status_code == 422
            assert "refusing generic fallback" in str(exc.detail)

    # 3. Retired demo stub serves nothing (fixtures purged Sep 2026)
    assert load_demo_fixture("RATU") is None, "demo stub must stay retired"


def test_pdf_route_prod_loader_no_fixture_interception(client):
    """Assert pdf router /api/report/{ticker}/html and /pdf do not serve fixture payloads."""
    # BBCA keyless must 422 (refusing generic fallback)
    res_bbca = client.get("/api/report/BBCA/html")
    assert res_bbca.status_code == 422
    assert "refusing generic fallback" in res_bbca.text or "assumptions" in res_bbca.text

    # Unknown ticker must 422
    res_unknown = client.get("/api/report/NOPEXYZ/html")
    assert res_unknown.status_code == 422

    # Direct render_html_for_ticker for unknown ticker raises HTTPException(422)
    with pytest.raises(HTTPException) as exc_info:
        render_html_for_ticker("NOPEXYZ")
    assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# 6. no 'Sectors (' provenance strings on fixture-shaped payloads
# ---------------------------------------------------------------------------

def _collect_all_strings(obj: Any) -> list[str]:
    """Recursively gather all string values in a nested dict/list/tuple."""
    strings: list[str] = []
    if isinstance(obj, str):
        strings.append(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str):
                strings.append(k)
            strings.extend(_collect_all_strings(v))
    elif isinstance(obj, (list, tuple, set)):
        for item in obj:
            strings.extend(_collect_all_strings(item))
    return strings


def test_negative_control_builder_module_absent():
    """Positive control: scripts/report_fixtures.py is deleted (purge, Sep 2026)."""
    assert not (REPO_ROOT / "scripts" / "report_fixtures.py").exists(), (
        "scripts/report_fixtures.py resurrected — static builders stay purged"
    )


def test_no_fixture_json_files_on_disk():
    """Assert scripts/fixtures/*.json are all deleted (purge, Sep 2026)."""
    fixtures_dir = REPO_ROOT / "scripts" / "fixtures"
    fixture_files = list(fixtures_dir.glob("*.json")) if fixtures_dir.is_dir() else []
    assert not fixture_files, f"fixture JSON resurrected: {[f.name for f in fixture_files]}"


def test_demo_stub_serves_nothing():
    """Assert the retired load_demo_fixture() stub returns None for every ticker."""
    benchmark_tickers = ["RATU", "CDIA", "MTEL", "POWR", "JCI", "ACES", "BBRI", "PGEO", "SSIA", "SSMS", "TPIA"]

    for ticker in benchmark_tickers:
        assert load_demo_fixture(ticker) is None, f"demo stub must stay retired for {ticker}"


def test_no_sectors_open_paren_provenance_in_honest_skeletons():
    """Assert honest skeletons for BBCA and ADRO contain zero 'Sectors (' strings."""
    for ticker in ("BBCA", "ADRO"):
        data = _load_or_build_report_data(ticker, "auto")
        for s in _collect_all_strings(data):
            assert "Sectors (" not in s, f"Found 'Sectors (' in {ticker} honest skeleton: {s}"
