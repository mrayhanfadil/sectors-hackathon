"""Tests for institutional typst PDF pipeline.

Covers:
- scripts/report_charts.py: 9 matplotlib chart functions import + render
- templates/typst/archetypes/*.typ: 4 templates compile standalone
- scripts/render_typst.py: end-to-end --all render produces 4 PDFs with
  embedded chart images for MTEL
"""
from __future__ import annotations
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
SCRIPTS = PROJECT / "scripts"
TEMPLATES = PROJECT / "templates" / "typst"
FONTS = PROJECT / "assets" / "fonts"
sys.path.insert(0, str(SCRIPTS))


# ---- Lane 1: report_charts.py ----

def test_report_charts_imports():
    """All 9 chart functions importable."""
    import report_charts
    expected = [
        "chart_vs_jci", "chart_segment_donut", "chart_kpi_bars",
        "chart_pbv_bands", "chart_wacc_breakdown", "chart_sensitivity_heatmap",
        "chart_scenario_bars", "chart_ev_equity_waterfall", "chart_index_trend",
    ]
    for name in expected:
        assert hasattr(report_charts, name), f"missing {name}"


def test_report_charts_render(tmp_path):
    """All 9 chart functions render non-empty PNGs to disk."""
    import matplotlib
    matplotlib.use("Agg")
    from report_charts import (chart_vs_jci, chart_segment_donut, chart_kpi_bars,
                               chart_pbv_bands, chart_wacc_breakdown,
                               chart_sensitivity_heatmap, chart_scenario_bars,
                               chart_ev_equity_waterfall, chart_index_trend)

    palette = {"brand": "#067647", "brand_dark": "#054f31", "accent": "#ecfdf3",
               "ink": "#101828", "muted": "#475467", "line": "#e4e7ec",
               "band": "#f9fafb", "paper": "#ffffff", "pos": "#067647", "neg": "#b42318"}

    calls = [
        (chart_vs_jci, (palette, "TEST", ["Jan", "Feb", "Mar"], [0, 3, 6], [0, 2, 5],
                       "IDX, yfinance", tmp_path / "vs_jci.png")),
        (chart_segment_donut, (palette, [{"name": "A", "share_pct": 60}, {"name": "B", "share_pct": 40}],
                                "IDX", tmp_path / "seg.png")),
        (chart_kpi_bars, (palette, [10, 20, 30], [8, 18, 28], ["KPI1", "KPI2", "KPI3"],
                         "Co", tmp_path / "kpi.png")),
        (chart_pbv_bands, (palette, 1.0, 1.5, 2.0, 2.5, 3.0, 2.2, "ABOVE AVG",
                          tmp_path / "pbv.png")),
        (chart_wacc_breakdown, (palette, [{"label": "WACC", "value": "10.1%"}],
                                tmp_path / "wacc.png")),
        (chart_sensitivity_heatmap, (palette, [0.09, 0.10, 0.11], [0.01, 0.015, 0.02],
                                     [[100, 110, 120], [95, 100, 105], [90, 95, 100]],
                                     100, "Rp", tmp_path / "sens.png")),
        (chart_scenario_bars, (palette, 300, 387, 490, 460, "SELL", "SELL", "HOLD",
                              tmp_path / "scen.png")),
        (chart_ev_equity_waterfall, (palette, 20000, 30000, 1500, -21000, 0, 30500,
                                     tmp_path / "wf.png")),
        (chart_index_trend, (palette, ["T1", "T2", "T3"], [100, 110, 120],
                             "IDX", tmp_path / "idx.png")),
    ]
    for fn, args in calls:
        out = fn(*args)
        assert out.exists(), f"{fn.__name__} did not write to {out}"
        assert out.stat().st_size > 5000, f"{fn.__name__} PNG too small"


# ---- Lane 2-5: archetype templates compile ----

ARCHETYPE_PAGES = {"single": (5, 9), "sotp": (5, 10), "infra": (8, 14), "strategy": (3, 7)}


@pytest.mark.parametrize("archetype,expected_pages", list(ARCHETYPE_PAGES.items()))
def test_archetype_compiles(archetype, expected_pages):
    """Each archetype compiles standalone with --root / and produces expected page range."""
    if not FONTS.exists():
        pytest.skip(f"fonts not installed: {FONTS}")
    template = TEMPLATES / "archetypes" / f"report_{archetype}.typ"
    if not template.exists():
        pytest.skip(f"template not built: {template}")
    out = HERE / f"_test_{archetype}.pdf"
    result = subprocess.run(
        ["typst", "compile", "--font-path", str(FONTS), "--root", "/",
         str(template), str(out)],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        pytest.fail(f"typst compile failed for {archetype}:\n{result.stderr}")
    assert out.exists()
    # Read page count via pypdf
    from pypdf import PdfReader
    n = len(PdfReader(str(out)).pages)
    lo, hi = expected_pages
    assert lo <= n <= hi, f"{archetype} has {n} pages, expected {lo}-{hi}"
    out.unlink()


# ---- Lane 6: orchestrator end-to-end ----

def test_render_typst_all(tmp_path, monkeypatch):
    """render_typst.py --all renders 4 fixtures with charts embedded for MTEL."""
    from render_typst import main as render_main

    # Override cache root to temp dir so we don't pollute the project
    monkeypatch.setenv("TYPST_CACHE_DIR", str(tmp_path / "cache"))

    # Invoke --all programmatically (use subprocess for clean state)
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "render_typst.py"), "--all"],
        capture_output=True, text=True, timeout=180,
        cwd=str(PROJECT),
    )
    # All 4 should succeed
    assert "[OK] RATU" in result.stdout, f"RATU render failed:\n{result.stdout}\n{result.stderr}"
    assert "[OK] CDIA" in result.stdout, f"CDIA render failed:\n{result.stdout}\n{result.stderr}"
    assert "[OK] MTEL" in result.stdout, f"MTEL render failed:\n{result.stdout}\n{result.stderr}"
    assert "[OK] JCI" in result.stdout, f"JCI render failed:\n{result.stdout}\n{result.stderr}"

    # Verify MTEL has embedded charts on page 6
    mtel_pdf = PROJECT / "output" / "mtel_report_typst.pdf"
    assert mtel_pdf.exists()
    from pypdf import PdfReader
    r = PdfReader(str(mtel_pdf))
    assert len(r.pages) >= 10
    p6 = r.pages[5]  # 0-indexed
    xo = p6["/Resources"].get("/XObject", {})
    img_count = sum(1 for v in xo.values() if v.get_object().get("/Subtype") == "/Image")
    assert img_count >= 4, f"MTEL page 6 should have 4+ chart images, got {img_count}"


# ---- Backward compat ----

def test_render_pdf_wrapper_imports():
    """scripts/render_pdf.py is a thin wrapper that delegates to render_typst."""
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location("render_pdf", SCRIPTS / "render_pdf.py")
    assert spec is not None and spec.loader is not None
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    # Wrapper exposes main()
    assert hasattr(mod, "main")