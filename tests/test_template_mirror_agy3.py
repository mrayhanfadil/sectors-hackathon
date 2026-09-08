"""Typst archetype template mirror and de-baked peer/sensitivity tests (Lane H3).

Verifies:
1. Directory and file existence across server/report/typst and templates/typst/archetypes.
2. Common theme.typ and cover.typ byte-for-byte synchronization between server and templates.
3. Exact mirror status for report_single.typ and report_update.typ (modulo relative import path rewrites).
4. De-baked peer defaults and honest provenance markers in report_single.typ:
   - Default peer rows de-baked to dashes: ((m.ticker, "-", "-", "-", "-", "-", "-"),)
   - Source markers updated to 'Sectors (pending)' / 'Sectors pending'
   - Absence of baked peer aggregates (Rp 16,8 T, Rp 34,2 T, Rata-rata Peers, Median Peers).
5. De-baking and divergence pinning for report_infra.typ, report_sotp.typ, and report_strategy.typ:
   - report_infra: server peer table is data-driven (data.peers.tables.at(0)), no baked peer averages/medians.
   - report_sotp: server carries 4x static-demo notes, no baked 'Median Industri' or 'Peer Median' rows.
   - report_strategy: server Exhibit 6 is rationale-only without baked peer multiples ('Ticker', 'Cap', 'Rationale').
6. Sensitivity analysis and scenario structures are properly driven/guarded rather than hardcoded fake multiples.
"""
from __future__ import annotations

import difflib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_TYPST = REPO_ROOT / "server" / "report" / "typst"
TEMPLATES_ARCHETYPES = REPO_ROOT / "templates" / "typst" / "archetypes"
TEMPLATES_COMMON = REPO_ROOT / "templates" / "typst" / "common"

ARCHETYPE_FILES = [
    "report_infra.typ",
    "report_single.typ",
    "report_sotp.typ",
    "report_strategy.typ",
    "report_update.typ",
]


def _read_file(path: Path) -> str:
    """Helper to read file content as UTF-8, asserting existence."""
    assert path.exists(), f"Missing required file: {path}"
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Structure & Existence Checks
# ---------------------------------------------------------------------------

def test_typst_directories_and_archetypes_exist():
    """Assert all 5 archetype files and common files exist in expected directories."""
    assert SERVER_TYPST.is_dir(), f"Missing directory: {SERVER_TYPST}"
    assert TEMPLATES_ARCHETYPES.is_dir(), f"Missing directory: {TEMPLATES_ARCHETYPES}"
    assert TEMPLATES_COMMON.is_dir(), f"Missing directory: {TEMPLATES_COMMON}"

    for filename in ARCHETYPE_FILES:
        server_path = SERVER_TYPST / filename
        template_path = TEMPLATES_ARCHETYPES / filename
        assert server_path.is_file(), f"Server archetype file missing: {server_path}"
        assert template_path.is_file(), f"Templates archetype file missing: {template_path}"

    for common_name in ("cover.typ", "theme.typ"):
        assert (SERVER_TYPST / common_name).is_file(), f"Server common file missing: {common_name}"
        assert (TEMPLATES_COMMON / common_name).is_file(), f"Templates common file missing: {common_name}"


# ---------------------------------------------------------------------------
# 2. Common Components Synchronization
# ---------------------------------------------------------------------------

def test_common_theme_and_cover_sync():
    """Assert theme.typ and cover.typ in server/report/typst match templates/typst/common."""
    for common_name in ("cover.typ", "theme.typ"):
        server_content = _read_file(SERVER_TYPST / common_name)
        common_content = _read_file(TEMPLATES_COMMON / common_name)
        assert server_content == common_content, (
            f"Common component mismatch for {common_name} between server/report/typst and templates/typst/common"
        )


# ---------------------------------------------------------------------------
# 3. Exact Mirror Archetypes (Single & Update)
# ---------------------------------------------------------------------------

def test_report_single_mirrors_server():
    """Assert report_single.typ in templates mirrors server copy exactly modulo import rewrites."""
    server_raw = _read_file(SERVER_TYPST / "report_single.typ")
    template_raw = _read_file(TEMPLATES_ARCHETYPES / "report_single.typ")

    normalized_server = server_raw.replace(
        '#import "theme.typ": *', '#import "../common/theme.typ": *'
    ).replace(
        '#import "cover.typ": *', '#import "../common/cover.typ": *'
    )

    if normalized_server != template_raw:
        diff = "".join(
            difflib.unified_diff(
                normalized_server.splitlines(keepends=True),
                template_raw.splitlines(keepends=True),
                fromfile="server/report/typst/report_single.typ",
                tofile="templates/typst/archetypes/report_single.typ",
            )
        )
        pytest.fail(f"report_single.typ mirror drifted beyond import lines:\n{diff}")


def test_report_update_mirrors_server():
    """Assert report_update.typ in templates mirrors server copy exactly modulo import rewrites."""
    server_raw = _read_file(SERVER_TYPST / "report_update.typ")
    template_raw = _read_file(TEMPLATES_ARCHETYPES / "report_update.typ")

    normalized_server = server_raw.replace(
        '#import "theme.typ": *', '#import "../common/theme.typ": *'
    )

    if normalized_server != template_raw:
        diff = "".join(
            difflib.unified_diff(
                normalized_server.splitlines(keepends=True),
                template_raw.splitlines(keepends=True),
                fromfile="server/report/typst/report_update.typ",
                tofile="templates/typst/archetypes/report_update.typ",
            )
        )
        pytest.fail(f"report_update.typ mirror drifted beyond import lines:\n{diff}")


# ---------------------------------------------------------------------------
# 4. De-baked Peer Rows and Provenance Markers in report_single.typ
# ---------------------------------------------------------------------------

def test_report_single_debaked_peer_rows_to_dashes():
    """Assert peer defaults in report_single.typ are de-baked to dashes and honest markers."""
    for base_dir in (SERVER_TYPST, TEMPLATES_ARCHETYPES):
        src = _read_file(base_dir / "report_single.typ")
        # Check dash-default peer row
        assert '((m.ticker, "-", "-", "-", "-", "-", "-"),)' in src, (
            f"{base_dir.name}/report_single.typ: missing de-baked dash default peer row"
        )
        # Check honest pending source markers
        assert 'peer_src = peer_tab.at("source", default: "Sectors (pending)")' in src, (
            f"{base_dir.name}/report_single.typ: missing peer_src Sectors (pending) marker"
        )
        assert 'relval_src = "Sectors (pending)"' in src, (
            f"{base_dir.name}/report_single.typ: missing relval_src Sectors (pending) marker"
        )
        assert 'caption: "Engine Chart Renderer (Sectors pending)"' in src, (
            f"{base_dir.name}/report_single.typ: missing chart-placeholder Sectors pending caption"
        )

    # Server report_single must not have baked aggregate rows
    server_src = _read_file(SERVER_TYPST / "report_single.typ")
    for baked in ("Rp 16,8 T", "Rp 34,2 T", "Rata-rata Peers", "Median Peers"):
        assert baked not in server_src, (
            f"server/report/typst/report_single.typ still contains baked peer marker: {baked}"
        )


# ---------------------------------------------------------------------------
# 5. Infrastructure Archetype De-baking and Divergence
# ---------------------------------------------------------------------------

def test_report_infra_debaked_and_divergence_pinned():
    """Assert server report_infra.typ is data-driven without baked peer aggregates, and pin templates divergence."""
    server_infra = _read_file(SERVER_TYPST / "report_infra.typ")
    tpl_infra = _read_file(TEMPLATES_ARCHETYPES / "report_infra.typ")

    # Server copy: fully data-driven peer table and Sectors pending chart placeholder
    assert 'peer_tab = data.peers.tables.at(0)' in server_infra, (
        "server report_infra.typ must bind peer_tab directly from data.peers"
    )
    assert 'caption: "Engine Chart Renderer (Sectors pending)"' in server_infra, (
        "server report_infra.typ must use Sectors pending chart placeholder caption"
    )
    for baked in ("Rata-rata Peers", "Median Peers"):
        assert baked not in server_infra, (
            f"server report_infra.typ unexpectedly contains baked aggregate row: {baked}"
        )

    # Templates copy: retains legacy baked rows (divergence pin)
    assert "Rata-rata Peers" in tpl_infra, "templates report_infra.typ expected legacy Rata-rata Peers marker"
    assert "Median Peers" in tpl_infra, "templates report_infra.typ expected legacy Median Peers marker"
    assert 'caption: "Engine Chart Renderer (IDX / yfinance)"' in tpl_infra, (
        "templates report_infra.typ expected legacy chart placeholder caption"
    )


# ---------------------------------------------------------------------------
# 6. SOTP Archetype De-baking and Divergence
# ---------------------------------------------------------------------------

def test_report_sotp_debaked_and_divergence_pinned():
    """Assert server report_sotp.typ has honest static demo notes and de-baked pillars, and pin templates divergence."""
    server_sotp = _read_file(SERVER_TYPST / "report_sotp.typ")
    tpl_sotp = _read_file(TEMPLATES_ARCHETYPES / "report_sotp.typ")

    # Server copy: carries static demo note in all 4 pillar sections
    demo_note = "Komparabel ilustratif CDIA, statis Sep 2026 — cross-check via Sectors peers pending."
    note_count = server_sotp.count(demo_note)
    assert note_count >= 4, (
        f"server report_sotp.typ must carry static demo note across all 4 pillars (found {note_count})"
    )
    for baked in ("Median Industri", "Peer Median", "Rata-rata Peers", "Median Peers"):
        assert baked not in server_sotp, (
            f"server report_sotp.typ unexpectedly contains baked aggregate row: {baked}"
        )

    # Templates copy: contains legacy Median Industri rows and Peer Median column (divergence pin)
    assert "Median Industri" in tpl_sotp, "templates report_sotp.typ expected legacy Median Industri row"
    assert "Peer Median" in tpl_sotp, "templates report_sotp.typ expected legacy Peer Median column"
    assert demo_note not in tpl_sotp, "templates report_sotp.typ unexpectedly contains static demo notes"


# ---------------------------------------------------------------------------
# 7. Strategy Archetype De-baking and Divergence
# ---------------------------------------------------------------------------

def test_report_strategy_debaked_and_divergence_pinned():
    """Assert server report_strategy.typ Top Picks is rationale-only, and pin templates divergence."""
    server_strat = _read_file(SERVER_TYPST / "report_strategy.typ")
    tpl_strat = _read_file(TEMPLATES_ARCHETYPES / "report_strategy.typ")

    # Server copy: Top Picks table is rationale-only without baked peer multiples
    assert '("Ticker", "Cap", "Rationale")' in server_strat, (
        "server report_strategy.typ Exhibit 6 must use ('Ticker', 'Cap', 'Rationale') headers"
    )
    for baked in ("Peer Median", "Rata-rata Peers", "Median Peers"):
        assert baked not in server_strat, (
            f"server report_strategy.typ unexpectedly contains baked peer aggregate marker: {baked}"
        )

    # Templates copy: contains legacy baked multiple columns (P/E, ROE, PBV) and aggregate rows (divergence pin)
    assert "P/E (x)" in tpl_strat, "templates report_strategy.typ expected legacy P/E column"
    assert "Rata-rata Peers" in tpl_strat, "templates report_strategy.typ expected legacy Rata-rata Peers row"
    assert "Median Peers" in tpl_strat, "templates report_strategy.typ expected legacy Median Peers row"


# ---------------------------------------------------------------------------
# 8. Sensitivity Analysis and Scenario Structures
# ---------------------------------------------------------------------------

def test_sensitivity_and_scenario_structures_guarded():
    """Assert sensitivity matrices and scenario analyses across archetypes are guarded or dynamic."""
    server_single = _read_file(SERVER_TYPST / "report_single.typ")
    server_infra = _read_file(SERVER_TYPST / "report_infra.typ")
    server_strat = _read_file(SERVER_TYPST / "report_strategy.typ")

    # report_single: sensitivity table is guarded by ddd.at("sensitivity", default: (:))
    assert 'ddd.at("sensitivity", default: (:))' in server_single, (
        "server report_single.typ must guard sensitivity access via ddd.at('sensitivity')"
    )
    assert "Sensitivity Analysis — WACC vs Terminal Growth (g)" in server_single, (
        "server report_single.typ missing Exhibit 9 sensitivity title"
    )

    # report_infra: Exhibit 16 sensitivity 5x5 is driven from dynamic axes
    assert "sens.wacc_axis" in server_infra and "sens.g_axis" in server_infra, (
        "server report_infra.typ Exhibit 16 must dynamically map wacc_axis and g_axis"
    )

    # report_strategy: Exhibit 4 sensitivity and Exhibit 2/3 scenario analysis
    assert "Sensitivity Analysis — Pertumbuhan EPS vs Kelipatan P/E Forward" in server_strat, (
        "server report_strategy.typ missing Exhibit 4 EPS vs P/E sensitivity header"
    )
    assert "Scenario Analysis (Bear / Base / Bull) — Target Indeks IHSG" in server_strat, (
        "server report_strategy.typ missing Exhibit 3 Scenario Analysis"
    )


# ---------------------------------------------------------------------------
# 9. Server Archetype Sweep for Unwanted Baked Aggregates in Peer Sections
# ---------------------------------------------------------------------------

def test_no_unwanted_baked_peer_aggregates_in_server_archetypes():
    """Sweep server archetypes to assert no un-guarded 'Rata-rata Peers' or 'Median Peers' strings exist."""
    single = _read_file(SERVER_TYPST / "report_single.typ")
    infra = _read_file(SERVER_TYPST / "report_infra.typ")
    sotp = _read_file(SERVER_TYPST / "report_sotp.typ")
    strat = _read_file(SERVER_TYPST / "report_strategy.typ")

    for baked in ("Rata-rata Peers", "Median Peers", "Rp 16,8 T", "Rp 34,2 T"):
        assert baked not in single, f"server report_single.typ contains {baked}"

    for baked in ("Rata-rata Peers", "Median Peers", "Peer Median"):
        assert baked not in infra, f"server report_infra.typ contains {baked}"
        assert baked not in sotp, f"server report_sotp.typ contains {baked}"
        assert baked not in strat, f"server report_strategy.typ contains {baked}"
