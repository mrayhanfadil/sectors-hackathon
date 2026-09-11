"""House exhibit/header/footer convention guards (Fadil spec, 11 Sep 2026).

Rules under test:
1. Every visual/tabular object is labelled `Exhibit N. <descriptive name>` above
   the object, with the constant line `Source: Company, Team Estimates` below.
2. Exhibit numbers are a GLOBAL counter across the document — never a literal
   `"Exhibit N"` string at a call site, so removing/adding an object re-sequences
   every later exhibit automatically.
3. Page header: `Equity Research – Company Update` + date `Day, DD Month YYYY`
   at left, Sectors.app logo at right, house divider (#067647) below.
4. Page footer: `sectors.app` at left, disclosure pointer + page number at right.

These tests fail loudly if a future edit re-introduces hardcoded numbering, drops
the logo, desynchronises the theme mirrors, or loses an archetype's template map.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_TYPST = REPO_ROOT / "server" / "report" / "typst"
TEMPLATES_COMMON = REPO_ROOT / "templates" / "typst" / "common"
TEMPLATES_ARCHETYPES = REPO_ROOT / "templates" / "typst" / "archetypes"
SERVER_REPORT = REPO_ROOT / "server" / "report" / "typst"

ARCHETYPES = ["report_single", "report_sotp", "report_infra", "report_strategy"]

# Legacy Indonesian source-line label. The house line is English and constant.
# Note: this is the source-line pattern ("Sumber:"), not the bare word — table
# column headers such as "Sumber Data" are legitimate and must not trip this.
BANNED_SOURCE_LABEL = "Sumber:"


def _theme() -> str:
    return (TEMPLATES_COMMON / "theme.typ").read_text(encoding="utf-8")


# ---------------------------------------------------------------- rule 2


@pytest.mark.parametrize("path", sorted(TEMPLATES_ARCHETYPES.glob("report_*.typ")))
def test_no_hardcoded_exhibit_numbers_in_call_sites(path: Path) -> None:
    """A literal 'Exhibit N' first argument means numbering is manual again."""
    txt = path.read_text(encoding="utf-8")
    offenders = re.findall(r'exhibit-header\(\s*"Exhibit\s+\d', txt)
    assert not offenders, (
        f"{path.name}: {len(offenders)} call site(s) hardcode the exhibit number. "
        "exhibit-header(title, source) numbers itself via the global counter."
    )


def test_exhibit_counter_is_a_global_document_counter() -> None:
    txt = _theme()
    assert 'counter("exhibit")' in txt, "no global exhibit counter in theme.typ"
    assert "exhibit-counter.step()" in txt, "counter never steps"
    assert "exhibit-counter.display()" in txt, "counter never rendered"


def test_exhibit_label_renders_above_and_source_below() -> None:
    """The label block must precede the stashed source, and the source must be
    flushed by both the next label and the end of a page."""
    txt = _theme()
    assert "exhibit-src-state" in txt, "source not stashed"
    assert "exhibit-source()" in txt, "no source-line renderer"
    # page-wrap must flush so the last object on a page still gets its source
    wrap = txt[txt.index("#let page-wrap("):]
    assert "exhibit-flushed" in wrap, "page-wrap does not flush a pending source"


# ---------------------------------------------------------------- rule 1


def test_source_line_is_the_constant_house_string() -> None:
    txt = _theme()
    assert 'SOURCE_LINE = "Company, Team Estimates"' in txt
    assert "[Source: #s]" in txt, "source line must render as 'Source: ...'"
    assert BANNED_SOURCE_LABEL not in txt, "legacy Indonesian 'Sumber:' label returned"


def test_legacy_indonesian_source_label_gone_from_archetypes() -> None:
    offenders = []
    for p in list(TEMPLATES_ARCHETYPES.glob("*.typ")) + list(SERVER_REPORT.glob("report_*.typ")):
        if BANNED_SOURCE_LABEL in p.read_text(encoding="utf-8"):
            offenders.append(str(p.relative_to(REPO_ROOT)))
    assert not offenders, f"'Sumber:' still present in: {offenders}"


# ---------------------------------------------------------------- rule 3/4


def test_header_and_footer_house_strings() -> None:
    txt = _theme()
    assert 'HEADER_TITLE = "Equity Research – Company Update"' in txt
    assert 'FOOTER_LEFT = "sectors.app"' in txt
    assert 'FOOTER_RIGHT = "See important disclosure at the back of this report"' in txt
    assert 'HEADER_DIVIDER_COLOR = rgb("#067647")' in txt


def test_date_formatter_emits_day_dd_month_yyyy() -> None:
    txt = _theme()
    assert "#let format-date-en(" in txt, "no English date formatter"
    # the return expression must stay on ONE line: a trailing '+' continuation
    # after `return` parses as a separate statement and silently drops the tail.
    assert "return _DAY_NAMES.at(dt.weekday() - 1) + " in txt, (
        "date formatter return was split across lines — Typst will return only "
        "the weekday name"
    )


@pytest.mark.parametrize(
    "tree,logo",
    [
        (REPO_ROOT / "assets" / "brand" / "sectors-icon.svg", "repo root"),
        (REPO_ROOT / "templates" / "typst" / "assets" / "brand" / "sectors-icon.svg", "templates tree"),
        (REPO_ROOT / "server" / "report" / "assets" / "brand" / "sectors-icon.svg", "server tree"),
    ],
)
def test_logo_asset_present(tree: Path, logo: str) -> None:
    assert tree.exists(), f"missing Sectors logo in {logo}: {tree}"
    body = tree.read_text(encoding="utf-8")
    assert "<svg" in body, f"{tree} is not an SVG"
    # the official mark is the rose/orange bar motif
    assert "#E11D48" in body or "#E0003B" in body, f"{tree} does not look like the Sectors mark"


def test_logo_is_wired_into_the_running_header() -> None:
    txt = _theme()
    assert 'LOGO_PATH = "../assets/brand/sectors-icon.svg"' in txt
    assert "image(LOGO_PATH" in txt, "logo not placed in the running header"


# ---------------------------------------------------------------- mirrors


def test_theme_mirrors_are_byte_identical() -> None:
    """The renderer prefers server/report/typst and falls back to templates/typst;
    a drifting copy means the house convention silently stops applying."""
    a = (TEMPLATES_COMMON / "theme.typ").read_bytes()
    b = (SERVER_TYPST / "theme.typ").read_bytes()
    assert a == b, "theme.typ differs between the two template trees"


def test_both_template_trees_share_the_logo_relative_path() -> None:
    """LOGO_PATH is relative to theme.typ, and both copies must resolve it."""
    for theme in (TEMPLATES_COMMON / "theme.typ", SERVER_TYPST / "theme.typ"):
        assert 'LOGO_PATH = "../assets/brand/sectors-icon.svg"' in theme.read_text(encoding="utf-8")


# ---------------------------------------------------------------- template map


def test_cli_template_map_covers_every_archetype() -> None:
    """A missing key silently falls back to report_single.typ."""
    cli = (REPO_ROOT / "scripts" / "render_typst.py").read_text(encoding="utf-8")
    block = cli[cli.index("TEMPLATE_FILES = {"):]
    block = block[: block.index("}")]
    for name, fname in [
        ("single", "report_single.typ"),
        ("sotp", "report_sotp.typ"),
        ("infra", "report_infra.typ"),
        ("strategy", "report_strategy.typ"),
        ("update", "report_update.typ"),
    ]:
        assert f'"{name}"' in block, f"CLI TEMPLATE_FILES is missing '{name}' -> renders single"
        assert (TEMPLATES_ARCHETYPES / fname).exists(), f"{fname} missing from templates"
