"""House exhibit / header / footer convention guards (Fadil spec, 11 Sep 2026).

Rules under test:
1. Every visual/tabular object is labelled `Exhibit N. <descriptive name>` above
   the object, with the constant line `Source: Company, Team Estimates` below.
2. Exhibit numbers come from ONE document-global counter — never a literal
   `"Exhibit N"` at a call site — so revising one page re-sequences every later
   exhibit automatically.
3. Page header on EVERY page: `Equity Research – Company Update` + the date
   `Day, DD Month YYYY` at left, Sectors.app logo at right, house divider
   (#067647) below. Drawn natively (page margin), so content overflow cannot
   produce a page without furniture.
4. Page footer on EVERY page: `sectors.app` at left, disclosure pointer + the
   real page number at right.

These tests fail loudly if a future edit re-introduces hardcoded numbering, drops
the native furniture, desynchronises the theme mirrors, loses the logo, or makes
an archetype unreachable from the renderer's template map.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_TYPST = REPO_ROOT / "server" / "report" / "typst"
TEMPLATES_COMMON = REPO_ROOT / "templates" / "typst" / "common"
TEMPLATES_ARCHETYPES = REPO_ROOT / "templates" / "typst" / "archetypes"
SERVER_ARCHETYPES = SERVER_TYPST

BOTH_TREES = [TEMPLATES_ARCHETYPES, SERVER_ARCHETYPES]

# The legacy Indonesian source-line label. Note the colon: bare uses such as a
# "Sumber Data" table column header are legitimate and must not trip this.
BANNED_SOURCE_LABEL = "Sumber:"

# Archetypes that must label their objects. report_update previously had zero
# exhibit labels, so it is guarded explicitly below.
ALL_ARCHETYPES = [
    "report_single", "report_sotp", "report_infra", "report_strategy", "report_update",
]


def _theme() -> str:
    return (TEMPLATES_COMMON / "theme.typ").read_text(encoding="utf-8")


def _typ_files() -> list[Path]:
    return [p for tree in BOTH_TREES for p in sorted(tree.glob("report_*.typ"))]


# ---------------------------------------------------------------- rule 2


@pytest.mark.parametrize("path", _typ_files(), ids=lambda p: f"{p.parent.parent.name}/{p.name}")
def test_no_hardcoded_exhibit_numbers_in_call_sites(path: Path) -> None:
    """A literal 'Exhibit N' argument means numbering went manual again."""
    txt = path.read_text(encoding="utf-8")
    offenders = re.findall(r'exhibit-header\(\s*"Exhibit\s+\d', txt)
    offenders += re.findall(r'h-sec\(\s*"Exhibit\s+\d', txt)
    assert not offenders, (
        f"{path.name}: {len(offenders)} call site(s) hardcode the exhibit number. "
        "exhibit-header/exhibit-figure number themselves via the figure counter."
    )


def test_exhibit_numbering_uses_the_document_figure_counter() -> None:
    txt = _theme()
    assert 'kind: "exhibit"' in txt, "no 'exhibit' figure kind in theme.typ"
    assert "supplement: [Exhibit]" in txt, "figure caption must be supplemented 'Exhibit'"
    assert "numbering: \"1.\"" in txt, "figure numbering not pinned"
    # the previous hand-rolled counter must not come back alongside the figure one
    assert "exhibit-counter.step()" not in txt, "double numbering: hand-rolled counter still steps"


def test_exhibit_figures_are_referenceable_from_prose() -> None:
    """A label must sit on a SINGLE figure element, otherwise `@ref` breaks with
    'cannot reference sequence'."""
    txt = _theme()
    assert "#let exhibit-figure(title)" in txt, "no bare-figure helper for labelled exhibits"
    assert "#let exhibit-mark(source)" in txt, "no source-flush helper"


@pytest.mark.parametrize("path", _typ_files(), ids=lambda p: f"{p.parent.parent.name}/{p.name}")
def test_no_stale_hardcoded_prose_cross_references(path: Path) -> None:
    """Prose that names an exhibit number by hand drifts the moment a page is
    revised; it must be a live `@ref` instead."""
    txt = path.read_text(encoding="utf-8")
    offenders = re.findall(r"(?:pada|lihat|see|Lihat|See)\s+Exhibit\s+\d+", txt)
    assert not offenders, (
        f"{path.name}: hardcoded prose exhibit reference(s) {offenders} — "
        "use #exhibit-mark(...) + #exhibit-figure(...) <label> and cite @label"
    )


# ---------------------------------------------------------------- rule 1


def test_source_line_is_the_constant_house_string() -> None:
    txt = _theme()
    assert 'SOURCE_LINE = "Company, Team Estimates"' in txt
    assert "[Source: #s]" in txt, "source line must render as 'Source: ...'"
    assert BANNED_SOURCE_LABEL not in txt, "legacy Indonesian 'Sumber:' label returned"


@pytest.mark.parametrize("path", _typ_files(), ids=lambda p: f"{p.parent.parent.name}/{p.name}")
def test_legacy_indonesian_source_label_gone_from_archetypes(path: Path) -> None:
    assert BANNED_SOURCE_LABEL not in path.read_text(encoding="utf-8"), (
        f"{path.name} still renders a 'Sumber:' source line"
    )


@pytest.mark.parametrize("archetype", ALL_ARCHETYPES)
def test_every_archetype_labels_its_objects(archetype: str) -> None:
    """report_update shipped with zero exhibit labels; every archetype must
    label at least one object."""
    txt = (TEMPLATES_ARCHETYPES / f"{archetype}.typ").read_text(encoding="utf-8")
    n = len(re.findall(r"exhibit-header\(|exhibit-figure\(", txt))
    assert n >= 1, f"{archetype}.typ has no labelled exhibits"
    if archetype == "report_update":
        assert n >= 8, f"report_update.typ regressed to only {n} labelled exhibits"


def test_source_flushes_at_the_end_of_each_page_wrapper() -> None:
    txt = _theme()
    wrap = txt[txt.index("#let page-wrap("):]
    assert "exhibit-flushed" in wrap, "page-wrap does not flush a pending source line"


# ---------------------------------------------------------------- rule 3/4


def test_header_and_footer_are_drawn_natively_on_every_page() -> None:
    """In-flow furniture cannot cover an overflow page; only the page margin can."""
    txt = _theme()
    assert "header: context running-header(" in txt, "header is not drawn natively"
    assert "footer: context page-footer()" in txt, "footer is not drawn natively"
    assert "counter(page).display()" in txt, "footer page number is not the real page counter"


def test_page_wrapper_no_longer_draws_furniture() -> None:
    txt = _theme()
    start = txt.index("#let page-wrap(")
    rest = txt[start:]
    # body of page-wrap only: up to the next top-level definition
    nxt = re.search(r"\n#let ", rest[1:])
    body = rest[: nxt.start() + 1] if nxt else rest
    assert "running-header(" not in body, "page-wrap still draws the header in flow"
    assert "page-footer(" not in body, "page-wrap still draws the footer in flow"


def test_header_and_footer_house_strings() -> None:
    txt = _theme()
    assert 'HEADER_TITLE = "Equity Research – Company Update"' in txt
    assert 'FOOTER_LEFT = "sectors.app"' in txt
    assert 'FOOTER_RIGHT = "See important disclosure at the back of this report"' in txt
    assert 'HEADER_DIVIDER_COLOR = rgb("#067647")' in txt


def test_page_bands_are_tall_enough_for_the_furniture() -> None:
    txt = _theme()
    top = re.search(r"#let MARGIN_TOP = (\d+)mm", txt)
    bottom = re.search(r"#let MARGIN_BOTTOM = (\d+)mm", txt)
    assert top and bottom, "native header/footer need explicit vertical bands"
    assert int(top.group(1)) >= 17, "top band too short for title + date + logo + divider"
    assert int(bottom.group(1)) >= 13, "bottom band too short for the footer"


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
    "logo_path,where",
    [
        (REPO_ROOT / "assets" / "brand" / "sectors-icon.svg", "repo root"),
        (REPO_ROOT / "templates" / "typst" / "assets" / "brand" / "sectors-icon.svg", "templates tree"),
        (REPO_ROOT / "server" / "report" / "assets" / "brand" / "sectors-icon.svg", "server tree"),
    ],
)
def test_logo_asset_present(logo_path: Path, where: str) -> None:
    assert logo_path.exists(), f"missing Sectors logo in {where}: {logo_path}"
    body = logo_path.read_text(encoding="utf-8")
    assert "<svg" in body, f"{logo_path} is not an SVG"
    assert "#E11D48" in body or "#E0003B" in body, f"{logo_path} is not the Sectors mark"


def test_logo_is_wired_into_the_running_header() -> None:
    txt = _theme()
    assert 'LOGO_PATH = "../assets/brand/sectors-icon.svg"' in txt
    assert "image(LOGO_PATH" in txt, "logo not placed in the running header"


# ---------------------------------------------------------------- mirrors


def test_theme_mirrors_are_byte_identical() -> None:
    """The renderer prefers server/report/typst and falls back to templates/typst;
    a drifting copy means the house convention silently stops applying."""
    assert (TEMPLATES_COMMON / "theme.typ").read_bytes() == (SERVER_TYPST / "theme.typ").read_bytes(), (
        "theme.typ differs between the two template trees"
    )


# Only report_single and report_update are byte-mirrors between the two template
# trees (pinned by tests/test_template_mirror_agy3.py). The other three are
# intentionally divergent, so the convention is guarded structurally instead.
MIRRORED_ARCHETYPES = ["report_single", "report_update"]


@pytest.mark.parametrize("archetype", MIRRORED_ARCHETYPES)
def test_mirrored_archetypes_differ_only_by_import_path(archetype: str) -> None:
    norm = lambda s: re.sub(r'#import "[^"]+": \*', "#IMPORT#", s)
    a = norm((TEMPLATES_ARCHETYPES / f"{archetype}.typ").read_text(encoding="utf-8"))
    b = norm((SERVER_ARCHETYPES / f"{archetype}.typ").read_text(encoding="utf-8"))
    assert a == b, f"{archetype}.typ drifted between templates/typst and server/report/typst"


@pytest.mark.parametrize("archetype", MIRRORED_ARCHETYPES)
def test_both_trees_label_the_same_number_of_objects(archetype: str) -> None:
    """The house convention must hold in whichever tree the renderer picks.
    Restricted to the mirrored archetypes: infra/sotp/strategy carry a
    pre-existing content divergence, so their counts legitimately differ."""
    a = (TEMPLATES_ARCHETYPES / f"{archetype}.typ").read_text(encoding="utf-8")
    b = (SERVER_ARCHETYPES / f"{archetype}.typ").read_text(encoding="utf-8")
    count = lambda s: len(re.findall(r"exhibit-header\(|exhibit-figure\(", s))
    assert count(a) == count(b), (
        f"{archetype}.typ: templates has {count(a)} labelled exhibits, "
        f"server has {count(b)} — the convention drifted between trees"
    )


def test_single_archetype_keeps_disclosure_on_its_own_page() -> None:
    """report_single previously crammed peers + risks + rating guide + disclosure
    onto one logical page, so it always spilled onto an extra paper page. The
    split is what keeps `pages == logical page-wraps` for every single-ticker
    fixture, and it makes the footer's "disclosure at the back" literal."""
    txt = (TEMPLATES_ARCHETYPES / "report_single.typ").read_text(encoding="utf-8")
    assert txt.count("#page-wrap(") == 8, "report_single should have 8 logical pages"
    assert "Investment Risks & Disclosure" in txt, "disclosure page section header missing"
    assert "pagebreak(weak: true)" in txt, "strong pagebreaks can emit blank pages"


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
        assert f'"{name}"' in block, (
            f"CLI TEMPLATE_FILES is missing '{name}' -> renders report_single.typ instead"
        )
        assert (TEMPLATES_ARCHETYPES / fname).exists(), f"{fname} missing from templates"
