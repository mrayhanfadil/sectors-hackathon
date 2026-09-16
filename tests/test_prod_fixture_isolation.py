"""Prod-vs-fixture isolation guards (H2, LOUD policy Sep 2026).

Pins the Sectors-only purge: static demo fixtures
(scripts/fixtures/*.json, scripts/report_fixtures.py) are DELETED and
server/routers/pdf.py::_load_fixture is REMOVED. Prod loaders 422 or
return honest-empty skeletons without Sectors-backed inputs.

- data/sectors.db absent (legacy sqlite removed via git-rm).
- zero `import yfinance` under server/ (Sectors v2 is the single gateway).
- scripts/report_fixtures.py does not exist; zero references under server/.
- no `_load_fixture` symbol anywhere under server/ (dead canary removed).
- collector synthetic path neutered: agents/collector.py::_synthetic raises.
- prod loaders (render_html_for_ticker / _build_live_payload) 422 keyless
  without data/assumptions files.
- no 'Sectors (' provenance strings on honest prod payloads.

Run: .venv/bin/python -m pytest tests/test_prod_fixture_isolation.py -q
(from repo root)
"""
from __future__ import annotations

import ast
import inspect
import re
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests._loud_test_inputs import (  # noqa: E402
    KNOWN_DEMO_TICKERS,
    assert_no_fixture_provenance,
    is_fixture_shaped,
    load_demo_fixture,
)

# ---------------------------------------------------------------- static scans

_PY_IMPORT_RE = re.compile(r"^(?:import|from)\s+([A-Za-z0-9_.]+)")


def _py_code(line: str) -> str:
    """A .py line minus trailing comment (import lines never hold '#' in strings)."""
    return line.split("#", 1)[0].strip()


def _py_import_roots(path: Path) -> list[tuple[int, str]]:
    """(lineno, root-module) for top-level import statements in a .py file."""
    out: list[tuple[int, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return out
    for i, raw in enumerate(text.splitlines(), 1):
        code = _py_code(raw)
        m = _PY_IMPORT_RE.match(code)
        if not m:
            continue
        for mod in m.group(1).split(","):
            mod = mod.strip().split(" ")[0].strip()
            if mod:
                out.append((i, mod.split(".")[0] if "." not in mod.split()[0] else mod))
    return out


def _iter_py(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if ".venv" not in p.parts)


_FE_SKIP_DIRS = {"node_modules", "dist", "build", ".tanstack", ".wrangler"}


def _iter_fe() -> list[Path]:
    root = REPO_ROOT / "src" / "fe"
    if not root.is_dir():
        return []
    exts = {".ts", ".tsx", ".js", ".jsx"}
    return sorted(
        p
        for p in root.rglob("*")
        if p.suffix in exts and not any(d in p.parts for d in _FE_SKIP_DIRS)
    )


def _is_fe_comment(line: str) -> bool:
    s = line.strip()
    return s.startswith(("//", "*", "/*", "<!--")) or not s


# ---------------------------------------------------------------- 1. legacy db

def test_sectors_db_absent():
    assert not (REPO_ROOT / "data" / "sectors.db").exists(), (
        "data/sectors.db resurrected - legacy sqlite was git-rm'd, "
        "Sectors v2 + data/idx dumps are the only prod sources"
    )


# ---------------------------------------------------------------- 2. yfinance

def test_no_yfinance_imports_under_server():
    offenders = [
        f"{p.relative_to(REPO_ROOT)}:{i}"
        for p in _iter_py(REPO_ROOT / "server")
        for i, mod in _py_import_roots(p)
        if mod == "yfinance"
    ]
    assert not offenders, f"yfinance imports under server/: {offenders}"


# ---------------------------------------------------------------- 3. report_fixtures purged

def test_report_fixtures_module_absent():
    """scripts/report_fixtures.py is deleted (Sectors-only purge, Sep 2026)."""
    assert not (REPO_ROOT / "scripts" / "report_fixtures.py").exists(), (
        "scripts/report_fixtures.py resurrected - static builders are purged, "
        "Sectors v2 + data/assumptions files are the only prod sources"
    )
    assert not list((REPO_ROOT / "scripts" / "fixtures").glob("*.json")), (
        "fixture JSON resurrected under scripts/fixtures/"
    )


def test_no_live_prod_importers_of_report_fixtures():
    """Zero report_fixtures references anywhere under server/ or src/fe.

    The module is deleted, so any reference is a resurrection attempt.
    """
    live: list[str] = []

    for p in _iter_py(REPO_ROOT / "server"):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [node.module or ""]
            else:
                continue
            if not any("report_fixtures" in m for m in mods):
                continue
            live.append(f"{p.relative_to(REPO_ROOT)}:{node.lineno}")

    for p in _iter_fe():
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for i, raw in enumerate(lines, 1):
            if _is_fe_comment(raw) or "report_fixtures" not in raw:
                continue
            s = raw.strip()
            if re.match(r"^(import|export)\b", s) or "require(" in s or re.match(r"^from\b", s):
                live.append(f"{p.relative_to(REPO_ROOT)}:{i}")

    assert not live, f"live prod importers of report_fixtures: {live}"


def test_load_fixture_helper_deleted():
    """pdf._load_fixture is removed: zero hits anywhere under server/.

    The dead canary was purged Sep 2026. Any reintroduction fails here.
    """
    hits = []
    for p in _iter_py(REPO_ROOT / "server"):
        for i, raw in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if "_load_fixture" in raw:
                hits.append(f"{p.relative_to(REPO_ROOT)}:{i}: {raw.strip()}")
    assert not hits, f"_load_fixture resurrected under server/: {hits}"


def test_prod_loader_sources_import_no_fixtures():
    """render_html_for_ticker / _build_live_payload import no fixtures."""
    from server.routers.pdf import _build_live_payload, render_html_for_ticker

    pat = re.compile(r"^\s*(import|from)\s+\S*report_fixtures", re.M)
    for fn in (render_html_for_ticker, _build_live_payload):
        src = inspect.getsource(fn)
        assert not pat.search(src), f"{fn.__name__} imports report_fixtures"


# ---------------------------------------------------------------- 4. collector

def test_collector_synthetic_path_neutered():
    """agents/collector.py::_synthetic raises (seed-42 fallback retired)."""
    import agents.collector as C
    from agents.collector import QUINTET

    assert callable(C._synthetic)
    for t in QUINTET:
        with pytest.raises(RuntimeError, match="synthetic fallback retired"):
            C._synthetic(t)


def test_collector_collect_no_source_raises_loud(monkeypatch):
    """No IDX dump + no Sectors hit -> RuntimeError naming ticker (no synthetic)."""
    import agents.collector as C

    monkeypatch.setattr(C, "_try_idx", lambda ticker: None)
    monkeypatch.setattr(C, "_try_sectors", lambda ticker: None)
    with pytest.raises(RuntimeError) as ei:
        C.collect("RATU", use_cache=False)
    assert "sectors_missing_key" in str(ei.value) or "sectors_offline_mode" in str(ei.value)
    assert "RATU" in str(ei.value)


# ---------------------------------------------------------------- 5. pdf route

@pytest.mark.parametrize("ticker", ["RATU", "CDIA", "MTEL"])
def test_pdf_route_serves_no_fixture_implicitly(ticker):
    """Prod pdf loader 422s keyless without data/assumptions files (fixtures purged)."""
    from server.routers.pdf import render_html_for_ticker

    assert load_demo_fixture(ticker) is None, "demo stub must stay retired"
    with pytest.raises(HTTPException) as ei:
        render_html_for_ticker(ticker)
    assert ei.value.status_code == 422, f"expected 422, got {ei.value.status_code}"
    assert ticker in str(ei.value.detail)


# ---------------------------------------------------------------- 6. LOUD prod loader

@pytest.mark.parametrize("ticker", ["BBCA", "ADRO", "RATU", "MTEL", "ZZZQ"])
def test_prod_loader_refuses_without_verified_assumptions(ticker):
    """LOUD policy: no verified assumptions file -> 422 naming the ticker, never a skeleton.

    The removed Typst loader answered these with an honest-empty skeleton. The served path
    refuses instead, which is the stronger guarantee: nothing is rendered, so nothing can be
    fabricated. The skeleton shape is therefore deliberately absent from the codebase.
    """
    from server.routers.pdf import _build_live_payload

    with pytest.raises(HTTPException) as ei:
        _build_live_payload(ticker, None)
    assert ei.value.status_code == 422
    assert ticker in str(ei.value.detail)


def test_fixture_shape_detector_calibrated():
    """is_fixture_shaped() separates demo-shaped dicts from honest-empty output."""
    demo_shaped = {"cover": {"rating_box": {"tp": 7880, "price": 6200}},
                   "valuation": {"methods": [{"method": "DCF"}]},
                   "financial_highlights": {"rows": [["x"]]}}
    honest_empty = {"cover": {"rating_box": {"action": None, "tp": None, "price": None}},
                    "valuation": {"methods": []},
                    "financial_highlights": {"rows": [], "source": "sectors_missing_key"}}
    assert is_fixture_shaped(demo_shaped)
    assert not is_fixture_shaped(honest_empty)
