"""Prod-vs-fixture isolation guards (H2, LOUD policy Sep 2026).

Pins that prod loaders never serve static demo fixtures implicitly —
fixtures are reachable in tests ONLY via tests/_loud_test_inputs.py::
load_demo_fixture(). Covers:

- data/sectors.db absent (legacy sqlite removed via git-rm).
- zero `import yfinance` under server/ (Sectors v2 is the single gateway).
- zero LIVE prod importers of scripts/report_fixtures.py (server/ + src/fe
  scan). NOTE: server/routers/pdf.py still contains a dead `_load_fixture`
  helper with function-local report_fixtures imports — this file pins it as
  unreachable (no callers) instead of pretending it is gone. Deleting it is
  owned by another lane; any NEW importer or caller fails these tests.
- collector synthetic path neutered: agents/collector.py::_synthetic raises.
- pdf-route (render_html_for_ticker) + typst-renderer
  (_load_or_build_report_data) return no fixture payload without explicit
  load_demo_fixture().
- no 'Sectors (' provenance strings on fixture-shaped payloads.

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
        "data/sectors.db resurrected — legacy sqlite was git-rm'd, "
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


# ---------------------------------------------------------------- 3. report_fixtures importers

def test_no_live_prod_importers_of_report_fixtures():
    """Zero live prod importers of scripts/report_fixtures.py.

    server/ + src/fe are scanned for report_fixtures imports. The single
    exception is the KNOWN-DEAD server/routers/pdf.py::_load_fixture helper
    (function-local imports, zero callers — pinned dead below). Anything
    else fails.
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
            # Allow ONLY imports nested inside the dead _load_fixture def.
            if p.name == "pdf.py":
                parent = next(
                    (
                        n
                        for n in ast.walk(tree)
                        if isinstance(n, ast.FunctionDef)
                        and n.name == "_load_fixture"
                        and node.lineno >= n.lineno
                        and node.lineno <= (n.end_lineno or node.lineno)
                    ),
                    None,
                )
                if parent is not None:
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


def test_dead_fixture_helper_has_no_callers():
    """pdf._load_fixture is dead code: defined once, called nowhere.

    If anyone re-wires it into render_html_for_ticker/routes, this fails.
    """
    hits = []
    for p in _iter_py(REPO_ROOT / "server"):
        for i, raw in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if "_load_fixture" in raw:
                hits.append((p, i, raw.strip()))
    defs = [h for h in hits if h[2].startswith("def _load_fixture(")]
    calls = [h for h in hits if h not in defs]
    assert len(defs) == 1, f"expected exactly one _load_fixture def, got: {hits}"
    assert not calls, f"_load_fixture re-wired into prod path: {calls}"


def test_prod_loader_sources_import_no_fixtures():
    """render_html_for_ticker / _load_or_build_report_data import no fixtures."""
    from server.routers.pdf import render_html_for_ticker
    from server.report.typst_renderer import _load_or_build_report_data

    pat = re.compile(r"^\s*(import|from)\s+\S*report_fixtures", re.M)
    for fn in (render_html_for_ticker, _load_or_build_report_data):
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
    assert "sectors_missing_key" in str(ei.value)
    assert "RATU" in str(ei.value)


# ---------------------------------------------------------------- 5. pdf route

@pytest.mark.parametrize("ticker", ["RATU", "CDIA", "MTEL"])
def test_pdf_route_serves_no_fixture_implicitly(ticker):
    """Prod pdf loader 422s on demo tickers; only explicit load_demo_fixture() serves them."""
    from server.routers.pdf import render_html_for_ticker

    assert load_demo_fixture(ticker) is not None, f"no declared demo for {ticker}"
    with pytest.raises(HTTPException) as ei:
        render_html_for_ticker(ticker)
    assert ei.value.status_code == 422, f"expected 422, got {ei.value.status_code}"
    assert ticker in str(ei.value.detail)


# ---------------------------------------------------------------- 6. typst renderer

def test_typst_renderer_honest_empty_for_bbca_adro():
    prod = __import__(
        "server.report.typst_renderer", fromlist=["_load_or_build_report_data"]
    )
    for ticker in ("BBCA", "ADRO"):
        data = prod._load_or_build_report_data(ticker, "auto")
        rb = (data.get("cover") or {}).get("rating_box") or {}
        assert rb.get("action") is None and rb.get("tp") is None, (
            f"{ticker} prod payload carries invented rating/tp"
        )
        assert not is_fixture_shaped(data), f"{ticker} prod payload is fixture-shaped"
        assert_no_fixture_provenance(data, f"typst {ticker}")


@pytest.mark.parametrize("ticker", ["RATU", "MTEL", "ZZZQ"])
def test_typst_renderer_no_implicit_fixture(ticker):
    prod = __import__(
        "server.report.typst_renderer", fromlist=["_load_or_build_report_data"]
    )
    with pytest.raises(HTTPException) as ei:
        prod._load_or_build_report_data(ticker, "auto")
    assert ei.value.status_code == 422


# ---------------------------------------------------------------- 7. provenance

def test_no_sectors_paren_provenance_on_fixture_shaped_payloads():
    # Negative control: the static builder module DOES carry the marker,
    # proving the detector below is not vacuous.
    builders = (REPO_ROOT / "scripts" / "report_fixtures.py").read_text(encoding="utf-8")
    assert "Sectors (" in builders

    # Declared demos must never claim live Sectors sourcing...
    for ticker in KNOWN_DEMO_TICKERS:
        demo = load_demo_fixture(ticker)
        if demo is None:
            continue
        assert_no_fixture_provenance(demo, f"demo {ticker}")

    # ...and neither may prod loader outputs for fixture-shaped tickers.
    prod = __import__(
        "server.report.typst_renderer", fromlist=["_load_or_build_report_data"]
    )
    for ticker in ("BBCA", "ADRO"):
        assert_no_fixture_provenance(
            prod._load_or_build_report_data(ticker, "auto"), f"prod {ticker}"
        )


def test_fixture_shape_detector_calibrated():
    """is_fixture_shaped() separates explicit demos from honest-empty prod output."""
    prod = __import__(
        "server.report.typst_renderer", fromlist=["_load_or_build_report_data"]
    )
    demo = load_demo_fixture("RATU")
    assert demo is not None and is_fixture_shaped(demo)
    assert not is_fixture_shaped(prod._load_or_build_report_data("BBCA", "auto"))
