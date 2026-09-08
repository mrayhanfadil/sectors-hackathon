"""Tests for institutional typst PDF pipeline.

Covers:
- scripts/report_charts.py: 9 matplotlib chart functions import + render
- templates/typst/archetypes/*.typ: 4 templates compile standalone with an
  explicit data_path (no fixture defaults since the Sep 2026 Sectors-only purge)
- scripts/render_typst.py: end-to-end render of an explicit report_data.json
  produces a PDF (rich chart-embed assertions need live Sectors payloads)
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


# ---- Lane 2-5: archetype templates compile (explicit data_path) ----

def _skeleton_data_file(tmp_path, archetype="single") -> Path:
    """Write scaffolding payload for standalone compiles.

    Honest-empty BBCA skeleton plus the minimal extra sections the
    infra template reads unguarded (empty tables, TEST-labeled source).
    """
    from server.report.typst_renderer import _load_or_build_report_data

    data = _load_or_build_report_data("BBCA", "auto")
    if archetype == "infra":
        data["meta"]["analyst"] = {"name": "TEST", "role": "TEST scaffolding", "email": "test@example.invalid"}
        data["meta"]["head_office"] = "TEST"
        _qx = {
            "source": "TEST scaffolding (standalone compile only)",
            "headers": ["Akun", "Nilai"],
            "rows": [],
        }
        data["quarterly_pl"] = dict(_qx)
        data["quarterly_balance"] = dict(_qx)
        data["quarterly_ratios"] = dict(_qx)
        data["quarterly_kpi"] = dict(_qx)
        data["financials"] = [
            {"source": "TEST scaffolding", "title": "TEST",
             "headers": ["Akun", "Nilai"], "rows": []}
            for _ in range(4)
        ]
        data["valuation"] = {"methods": [{
            "method": "DCF", "fv": 1000,
            "source": "TEST scaffolding (standalone compile only)",
            "assumptions": {"wacc": 10.0, "g": 5.0, "beta": 1.0, "rf": 6.5,
                            "erp": 6.0, "coe": 12.5, "cod": 8.0,
                            "we": 60.0, "wd": 40.0},
            "table": {"headers": ["Item", "Nilai"], "rows": []},
        }, {
            "method": "EV/EBITDA", "fv": 900,
            "source": "TEST scaffolding (standalone compile only)",
            "assumptions": {"multiple": 10.0},
            "table": {"headers": ["Item", "Nilai"], "rows": []},
        }], "note": "TEST scaffolding",
            "blended": {"fv": 960, "fv_str": "960",
                        "weights": {"DCF": 60, "EV/EBITDA": 40},
                        "margin_of_safety_pct": 15,
                        "rows": [["DCF", "60%", 1000], ["EV/EBITDA", "40%", 900]]},
            "bands": {"source": "TEST scaffolding",
                       "pbv_3y": {"std+2": 2.5, "std+1": 2.0, "avg": 1.6,
                                 "std-1": 1.2, "std-2": 0.9, "current": 1.5,
                                 "label": "Rentang Nilai Wajar"}}}
        data["cDcf"] = {
            "valuation": {"enterprise_value": 1.0e12, "cash": 1.0e11,
                          "total_debt": 5.0e10, "equity_value": 1.05e12,
                          "fair_value_per_share": 1000, "pv_explicit": 4.0e11,
                          "pv_terminal": 6.0e11, "upside": 0.25},
            "sensitivity": {"wacc_axis": [0.09, 0.10], "g_axis": [0.04, 0.05],
                            "fair_value": [[900, 950], [1000, 1050]],
                            "upside": [[0.10, 0.15], [0.20, 0.25]]},
            "scenarios": {
                "BEAR": {"fair_value_per_share": 800, "upside": -0.10, "rating": "HOLD"},
                "BASE": {"fair_value_per_share": 1000, "upside": 0.25, "rating": "BUY"},
                "BULL": {"fair_value_per_share": 1200, "upside": 0.50, "rating": "BUY"},
            },
            "wacc": {"wacc_raw": 10.0},
        }
        data["financial_highlights"] = {
            "source": "TEST scaffolding (standalone compile only)",
            "years": ["FY24A", "FY25A"],
            "rows": [["Pendapatan Bersih", "350", "420"]],
        }
        data["peers"] = {"tables": [{
            "pillar": "TEST", "headers": ["Ticker", "Nilai"], "rows": [],
            "source": "TEST scaffolding",
        }]}
    p = tmp_path / f"skeleton_{archetype}_report_data.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


@pytest.mark.parametrize("archetype", ["single", "sotp", "infra", "strategy"])
def test_archetype_compiles(archetype, tmp_path):
    """Each archetype compiles standalone with explicit data_path input."""
    if not FONTS.exists():
        pytest.skip(f"fonts not installed: {FONTS}")
    template = TEMPLATES / "archetypes" / f"report_{archetype}.typ"
    if not template.exists():
        pytest.skip(f"template not built: {template}")
    out = tmp_path / f"_test_{archetype}.pdf"
    data_path = _skeleton_data_file(tmp_path, archetype)
    result = subprocess.run(
        ["typst", "compile", "--font-path", str(FONTS), "--root", "/",
         "--input", f"data_path={data_path}",
         str(template), str(out)],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        pytest.fail(f"typst compile failed for {archetype}:\n{result.stderr}")
    assert out.exists()


# ---- Lane 6: orchestrator end-to-end ----

def test_render_typst_explicit_data(tmp_path):
    """render_typst.py renders an explicit report_data.json to PDF."""
    from server.report.typst_renderer import _load_or_build_report_data

    data = _load_or_build_report_data("BBCA", "auto")
    data_path = tmp_path / "report_data.json"
    data_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    out_pdf = tmp_path / "bbca_report_typst.pdf"

    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "render_typst.py"), str(data_path),
         "--out", str(out_pdf)],
        capture_output=True, text=True, timeout=180,
        cwd=str(PROJECT),
    )
    assert out_pdf.exists(), f"render failed:\n{result.stdout}\n{result.stderr}"
    from pypdf import PdfReader
    assert len(PdfReader(str(out_pdf)).pages) >= 1


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