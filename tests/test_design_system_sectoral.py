"""Sectoral Design System wiring guards (friend-supplied, Sep 2026).

The friend's full text lives in `docs/design-system-friend.md` (base64 image
blobs notwithstanding - the token values below are normative). Four lanes wire
the surfaces concurrently (src/fe, templates/macros.html, server/report pages,
house_format.py); this file is the meeting point: it stays red until every
token below is wired into its surface.

  primary #0928B1 | bg #FFFFFF | text #333333 | grid #D9D9D9 / #E0E0E0
  table header #0928B1 with white text | even row #B4C7FF
  chart series order: #0928B1 #B4C7FF #3ED628 #1DCD9F #0047AB #7596FF
  Roboto only.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FE_INDEX_HTML = REPO_ROOT / "src" / "fe" / "index.html"
FE_INDEX_CSS = REPO_ROOT / "src" / "fe" / "src" / "index.css"
FE_SRC = REPO_ROOT / "src" / "fe" / "src"
MACROS = REPO_ROOT / "templates" / "macros.html"
RULE_DOC = REPO_ROOT / "docs" / "rules" / "house-report-format.md"
FRIEND_DOC = REPO_ROOT / "docs" / "design-system-friend.md"

SECTORAL_SERIES = ["#0928B1", "#B4C7FF", "#3ED628", "#1DCD9F", "#0047AB", "#7596FF"]


# ---------------------------------------------------------------- typography


def test_fe_index_html_loads_roboto() -> None:
    txt = FE_INDEX_HTML.read_text(encoding="utf-8")
    assert "roboto" in txt.lower(), (
        "src/fe/index.html does not load Roboto - the Sectoral system uses Roboto only"
    )


def test_macros_html_uses_roboto() -> None:
    txt = MACROS.read_text(encoding="utf-8")
    assert "roboto" in txt.lower(), (
        "templates/macros.html does not set Roboto - the printed report must use Roboto only"
    )


# ------------------------------------------------------------------- primary


def test_fe_index_css_carries_primary() -> None:
    txt = FE_INDEX_CSS.read_text(encoding="utf-8")
    assert "#0928b1" in txt.lower(), (
        "src/fe/src/index.css does not carry the Sectoral primary #0928B1"
    )


def test_house_divider_is_sectoral_primary() -> None:
    from server.report import house_format

    assert str(house_format.DIVIDER_COLOR).upper() == "#0928B1", (
        f"DIVIDER_COLOR is {house_format.DIVIDER_COLOR!r}, want '#0928B1'"
    )


# -------------------------------------------------------------- chart series


def test_house_chart_palette_order() -> None:
    from server.report import house_format

    assert hasattr(house_format, "SECTORAL_CHART_PALETTE"), (
        "house_format.SECTORAL_CHART_PALETTE is missing - the PDF charts cannot "
        "share the Sectoral series order with the FE"
    )
    got = [str(c).upper() for c in house_format.SECTORAL_CHART_PALETTE]
    assert got == SECTORAL_SERIES, f"SECTORAL_CHART_PALETTE is {got}, want {SECTORAL_SERIES}"


def _ordered_hexes(text: str) -> list[str]:
    return [m.group(0).upper() for m in re.finditer(r"#[0-9A-Fa-f]{6}\b", text)]


def _is_subsequence(hay: list[str], needle: list[str]) -> bool:
    it = iter(hay)
    return all(any(h == n for h in it) for n in needle)


def test_fe_chart_palette_order() -> None:
    """The FE chart surface carries the six Sectoral series colors in order -
    either as chart tokens or as a sectoralSeries export; the order is the contract."""
    hits: list[str] = []
    scanned = 0
    for path in sorted(FE_SRC.rglob("*")):
        if path.suffix not in (".ts", ".tsx", ".css") or not path.is_file():
            continue
        if "node_modules" in path.parts:
            continue
        scanned += 1
        if _is_subsequence(_ordered_hexes(path.read_text(encoding="utf-8")), SECTORAL_SERIES):
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert scanned, f"no FE sources scanned under {FE_SRC}"
    assert hits, (
        "no FE source carries the Sectoral series order "
        f"{' '.join(SECTORAL_SERIES)} (chart tokens or sectoralSeries)"
    )


# -------------------------------------------------------------------- tables


def _css_var_map(txt: str) -> dict[str, str]:
    """`--name: value` definitions in the file, so a token wired through a
    variable still counts (the macros lane owns the spelling)."""
    return {
        name.strip().lower(): val.strip().lower()
        for name, val in re.findall(r"--([\w-]+)\s*:\s*([^;{}]+);", txt)
    }


def _block_texts(txt: str, selector_re: str) -> list[str]:
    return [
        m.group(0).lower()
        for m in re.finditer(selector_re + r"\s*\{[^}]*\}", txt, re.IGNORECASE | re.DOTALL)
    ]


def _mentions(block: str, varmap: dict[str, str], *hexes: str) -> bool:
    if any(h in block for h in hexes):
        return True
    return any(
        varmap.get(v.lower(), "") in hexes
        for v in re.findall(r"var\(\s*--([\w-]+)", block)
    )


def test_macros_table_header_and_zebra() -> None:
    txt = MACROS.read_text(encoding="utf-8")
    low = txt.lower()
    assert "#0928b1" in low, "macros.html does not carry the Sectoral primary"
    assert "#b4c7ff" in low, "macros.html does not carry the Sectoral even-row tint"
    varmap = _css_var_map(txt)
    headers = _block_texts(txt, r"[^{}]*\bth\b[^{}]*")
    assert any(_mentions(b, varmap, "#0928b1") for b in headers), (
        "macros.html table header band is not the Sectoral primary #0928B1 "
        "(literally or via a CSS variable)"
    )
    assert any(_mentions(b, varmap, "#fff", "#ffffff") for b in headers), (
        "macros.html table header text is not white on the Sectoral primary"
    )
    zebras = _block_texts(txt, r"[^{}]*nth-child\(even\)[^{}]*")
    assert any(_mentions(b, varmap, "#b4c7ff") for b in zebras), (
        "macros.html even rows are not the Sectoral tint #B4C7FF "
        "(literally or via a CSS variable)"
    )


# ---------------------------------------------------------------------- logo


def test_sectoral_logo_svgs_exist() -> None:
    brand = sorted((REPO_ROOT / "assets" / "brand").glob("sectoral*.svg"))
    assert brand, "no sectoral*.svg under assets/brand/ (report slides header)"
    fe = sorted((REPO_ROOT / "src" / "fe" / "public").glob("sectoral*.svg"))
    assert fe, "no sectoral*.svg under src/fe/public/ (app header)"


# ----------------------------------------------------------------------- doc


def test_friend_doc_is_present() -> None:
    assert FRIEND_DOC.exists(), "docs/design-system-friend.md is missing"
    txt = FRIEND_DOC.read_text(encoding="utf-8")
    assert "#0928B1" in txt, "friend doc no longer states the Sectoral primary"


def test_rule_doc_has_sectoral_section() -> None:
    txt = RULE_DOC.read_text(encoding="utf-8")
    assert "docs/design-system-friend.md" in txt, (
        "rule doc does not point at the friend-supplied design system"
    )
    for token in ("#0928B1", "#B4C7FF", "#3ED628", "#1DCD9F", "#0047AB", "#7596FF", "Roboto"):
        assert token in txt, f"rule doc Sectoral section is missing {token}"
