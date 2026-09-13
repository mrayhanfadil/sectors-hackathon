"""The deck prints one number format: dot thousands, comma decimals."""
from __future__ import annotations

import re

import pytest

from server.report.house_rules import audit_number_format
from server.routers.pdf import render_html_for_ticker


@pytest.fixture(scope="module")
def payload():
    return render_html_for_ticker("AMMN", None)[2]


def _visible_text(html: str) -> str:
    """Only what a reader sees: no stylesheet, no script, no attributes."""
    stripped = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    return " ".join(re.findall(r">([^<]*)<", stripped))


def test_no_english_decimal_reaches_the_reader(payload):
    """Read the page the way a reader does: rendered visible text, not the markup.

    innerText excludes stylesheets, scripts, and SVG geometry (`stroke-width="2.0"`, `points="30.0,..."`), so
    anything it finds is a figure someone can actually read.
    """
    import pathlib as _p

    from playwright.sync_api import sync_playwright

    html = render_html_for_ticker("AMMN", None)[1]
    tmp = _p.Path("/tmp/_number_format_check.html")
    tmp.write_text(html, encoding="utf-8")
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1240, "height": 1754})
        pg.goto(f"file://{tmp}")
        pg.wait_for_timeout(400)
        text = pg.inner_text("body")
        b.close()
    hits = re.findall(r"(?<![\d.])\d+\.\d{1,2}(?![\d])", text)
    assert not hits, f"English decimals still on the page: {sorted(set(hits))[:12]}"
    signs = re.findall(r"(?<![\w,.])\d+(?:[.,]\d+)?\s?x(?![a-zA-Z0-9(])", text)
    assert not signs, f"ASCII multiplication signs still on the page: {sorted(set(signs))[:12]}"


def test_gate_flags_an_english_decimal_and_allows_a_thousands_group():
    ok = {"sector": {"rows": [["EBITDA", "33.862", "Rp 1,60 tn", "17,99×"]]}}
    assert audit_number_format(ok) == []
    bad = {"sector": {"rows": [["EBITDA", "33.862"], ["margin", "57.3%"]]}}
    out = audit_number_format(bad)
    assert out and "57.3" in out[0]
    # the internal trail is exempt: it is not printed
    assert audit_number_format({"_trail": {"raw": "57.3"}}) == []


def test_the_formatter_swaps_correctly():
    from server.report import numfmt

    assert numfmt.idn(1234.567, 2) == "1.234,57"
    assert numfmt.idn(44616, 0) == "44.616"
    assert numfmt.dec(43.04, 2) == "43,04"
    assert numfmt.pct(20.84, 1) == "+20,8%"
    assert numfmt.pcfrac(0.2084, 1) == "20,8%"
    assert numfmt.idn(None) == "—" and numfmt.dec("x") == "—"
    assert numfmt.idn(-1234.5, 1, signed=True) == "-1.234,5"
