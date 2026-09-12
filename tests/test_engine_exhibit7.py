"""Engine guards for the mining/E&P Exhibit-7 chart and the statement exhibits.

`tests/test_exhibit_convention.py` proves the house format is implemented;
`tests/test_house_format_adoption.py` proves it is adopted. This file pins the
three things the mining build added on top:

1. `chart_production_cost` renders a real PNG under BOTH unit parameterizations
   (Cu-eq + C1, concentrate + AISC) and refuses to invent a chart from empty or
   mismatched input instead of raising;
2. that chart is registered in BOTH render paths — the CLI orchestrator
   (`scripts/render_typst.py`) and the API renderer (`server/report/typst_renderer.py`)
   — with matching flag names, so a chart cannot exist in one and be invisible in
   the other;
3. the statement exhibits keep the house row order, and the cash-flow exhibit
   (house Exhibit 16), which was absent from the Typst render path, is present in
   BOTH trees with sub-totals bolded in place (`fin-table(bold-rows:)`).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
TEMPLATES_ARCHETYPES = REPO_ROOT / "templates" / "typst" / "archetypes"
SERVER_TYPST = REPO_ROOT / "server" / "report" / "typst"
THEME_MIRRORS = [
    REPO_ROOT / "templates" / "typst" / "common" / "theme.typ",
    SERVER_TYPST / "theme.typ",
]
SINGLE_MIRRORS = [
    TEMPLATES_ARCHETYPES / "report_single.typ",
    SERVER_TYPST / "report_single.typ",
]

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


# ------------------------------------------------------- render-path wiring


def _flag_names(src: str) -> list[str]:
    """The chart-availability flag names from a `for _name in [...]` list."""
    m = re.search(r"for _name in \[(.*?)\]", src, re.S)
    assert m, "no chart flag list found"
    return sorted(re.findall(r'"([a-z_]+)"', m.group(1)))


def test_both_renderers_register_the_production_cost_chart():
    cli = (SCRIPTS / "render_typst.py").read_text(encoding="utf-8")
    api = (REPO_ROOT / "server" / "report" / "typst_renderer.py").read_text(encoding="utf-8")

    # the CLI must both import and call it (registration, not just a flag)
    assert "chart_production_cost" in cli.split("def generate_charts")[1], (
        "render_typst.generate_charts does not call chart_production_cost"
    )

    cli_flags = _flag_names(cli)
    api_flags = _flag_names(api)
    assert "production_cost" in cli_flags, f"CLI flag list lacks production_cost: {cli_flags}"
    assert cli_flags == api_flags, (
        "the two renderers disagree on which charts exist — one path would silently "
        f"drop a chart the other produces:\nCLI={cli_flags}\nAPI={api_flags}"
    )

    # the placeholder fallback list (used so typst never hits a missing file) must
    # cover every flag, or the flag flips true against a 1.2K placeholder
    m = re.search(r"chart_names = \[(.*?)\]", api, re.S)
    assert m, "no chart_names fallback list in typst_renderer"
    fallback = sorted(n[:-4] for n in re.findall(r'"([a-z_]+\.png)"', m.group(1)))
    assert fallback == api_flags, (
        f"placeholder list and flag list drifted:\nfallback={fallback}\nflags={api_flags}"
    )


# ------------------------------------------------- statements 14-17 in the tree


def _cf_default_rows(src: str) -> list[str]:
    """The honest-empty cash-flow row labels, in rendered order."""
    block = src[src.index("#let cf_rows = if cf_has_data {"):]
    block = block[: block.index("}\n  #let cf_bold")]
    # split on the block's own `} else {` (the data branch contains an inline
    # `if c == none { ... } else { ... }`, so a bare split("else") would cut there)
    return re.findall(r'\("([^"]+)"', block.split("\n  } else {")[1])


def test_cash_flow_exhibit_is_present_in_both_single_archetype_trees():
    """House Exhibit 16 was missing from the Typst render path entirely; both trees
    must carry it, byte-identical modulo the import rewrite."""
    srcs = [p.read_text(encoding="utf-8") for p in SINGLE_MIRRORS]
    for path, src in zip(SINGLE_MIRRORS, srcs):
        assert '#let cf = fs.at("cashflow"' in src, f"{path}: no cash-flow exhibit"
        assert "Laporan Arus Kas" in src, f"{path}: cash-flow exhibit has no house title"

    def norm(s: str) -> str:
        return s.replace('#import "../common/theme.typ"', '#import "theme.typ"').replace(
            '#import "../common/cover.typ"', '#import "cover.typ"')

    assert norm(srcs[0]) == norm(srcs[1]), "the new exhibit landed in only one template tree"


def test_cash_flow_row_order_matches_the_house_template():
    """House Slide-7 order is Operating -> Investing -> Financing -> closing
    balances; a table that renders them out of order breaks the tie-out story."""
    for path in SINGLE_MIRRORS:
        rows = _cf_default_rows(path.read_text(encoding="utf-8"))
        order = [
            "ARUS KAS DARI OPERASI",
            "Laba Bersih Tahun Berjalan",
            "Arus Kas Bersih dari Operasi",
            "ARUS KAS DARI INVESTASI",
            "Arus Kas Bersih dari Investasi",
            "ARUS KAS DARI PENDANAAN",
            "Arus Kas Bersih dari Pendanaan",
        ]
        positions = [rows.index(label) for label in order]
        assert positions == sorted(positions), f"{path}: cash-flow rows out of house order: {rows}"
        footers = path.read_text(encoding="utf-8")
        for closing in ("Perubahan Kas Bersih", "Saldo Kas Awal", "Saldo Kas Akhir"):
            assert closing in footers, f"{path}: closing balance {closing!r} missing"


def test_fin_table_supports_in_place_bold_subtotals():
    """Statement sub-totals are marked by weight, not colour; the macro must expose
    `bold-rows` and the two theme mirrors must stay byte-identical."""
    for path in THEME_MIRRORS:
        txt = path.read_text(encoding="utf-8")
        assert "bold-rows: ()" in txt, f"{path}: fin-table has no bold-rows parameter"
        assert "bold-rows.contains(ri)" in txt, f"{path}: bold-rows is declared but unused"
        assert 'text(weight: "bold")[#c]' in txt, f"{path}: footer rows are not bolded"
    assert THEME_MIRRORS[0].read_bytes() == THEME_MIRRORS[1].read_bytes(), (
        "theme.typ mirrors drifted — the renderer prefers server/report/typst"
    )
