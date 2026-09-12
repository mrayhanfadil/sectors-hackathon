"""Engine guard for the mining/E&P Exhibit-7 chart.

`tests/test_house_format_adoption.py` proves the house format is implemented and adopted.
This file pins the one thing the
mining build added on top: `chart_production_cost` renders a real PNG under BOTH unit
parameterizations (Cu-eq + C1, concentrate + AISC) and refuses to invent a chart from empty or
mismatched input instead of raising.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))

PALETTE = {
    "brand": "#067647", "brand_dark": "#054f31", "accent": "#ecfdf3",
    "ink": "#101828", "muted": "#475467", "line": "#e4e7ec",
    "band": "#f9fafb", "paper": "#ffffff", "pos": "#067647", "neg": "#b42318",
}


# ------------------------------------------------------- the chart function


def test_chart_production_cost_renders_both_unit_parameterizations(tmp_path):
    """One function, two mining builds: Cu-eq volume + C1 cost, and concentrate
    volume + AISC cost (no cost series at all). Both must produce a real PNG."""
    from report_charts import chart_production_cost

    cu = chart_production_cost(
        PALETTE,
        ["2023A", "2024A", "2025F", "2026F", "2027F"],
        [210.0, 245.5, 268.0, 291.5, 310.0],
        [1.85, 1.72, 1.58, 1.49, 1.44],
        tmp_path / "cu_eq.png",
        volume_unit="kt Cu-eq",
        cost_label="C1 Cash Cost",
        cost_unit="US$/lb Cu-eq",
        actual_periods=2,
        source="Company filings, Team Estimates",
    )
    assert cu is not None and cu.exists(), "Cu-eq/C1 variant produced no PNG"
    assert cu.stat().st_size > 5000, f"Cu-eq chart too small: {cu.stat().st_size} bytes"

    conc = chart_production_cost(
        PALETTE,
        ["2025F", "2026F"],
        [1200.0, 1350.0],
        [],
        tmp_path / "concentrate.png",
        volume_unit="kt concentrate",
        cost_label="AISC",
        cost_unit="US$/t",
        actual_periods=0,
    )
    assert conc is not None and conc.exists(), "concentrate/AISC variant produced no PNG"
    assert conc.stat().st_size > 5000, f"concentrate chart too small: {conc.stat().st_size} bytes"


def test_chart_production_cost_never_fabricates_a_chart():
    """Absent or inconsistent data returns None (the caller skips the exhibit);
    the chart must not render an empty frame that reads as a real exhibit."""
    from report_charts import chart_production_cost

    assert chart_production_cost(PALETTE, [], [], [], "x.png") is None
    assert chart_production_cost(PALETTE, ["A", "B"], [1.0], [], "x.png") is None
