"""Deck page 3 — the investment-thesis rail: layout, the declared anchors, and the extraction rule."""
from __future__ import annotations

import pathlib

import pytest

from server.report.text_figures import hero_stat
from server.routers.pdf import render_html_for_ticker

ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def payload():
    return render_html_for_ticker("AMMN", None)[2]


def test_every_declared_anchor_is_a_figure_the_line_already_prints(payload):
    """The anchor column must never introduce a number: it highlights one that is already in the sentence."""
    items = payload["thesis"]
    assert items, "the deck has no investment thesis"
    for t in items:
        stat = str(t.get("stat") or "")
        assert stat, f"{t['headline']!r} has no anchor"
        assert stat in f"{t['headline']} {t['detail']}", \
            f"anchor {stat!r} does not appear in its own line — that would be a fabricated figure"
        assert t.get("stat_label"), f"{t['headline']!r} has an unlabelled anchor"


def test_the_rail_renders_one_numbered_row_per_pillar_without_boxes(payload):
    html = render_html_for_ticker("AMMN", None)[1]
    start = html.index('class="thesis-rail"')
    block = html[start : html.index("</ol>", start)]
    assert block.count("<li>") == len(payload["thesis"])
    for i, t in enumerate(payload["thesis"], 1):
        assert f"{i:02d}" in block
        assert t["headline"] in block and str(t["stat"]) in block
    assert "card-tint" not in block, "the rail replaces the tinted cards; a card here undoes the redesign"


def test_the_layout_separates_rows_with_hairlines_including_the_last():
    css = (ROOT / "templates" / "macros.html").read_text()
    assert "ol.thesis-rail > li" in css and "border-top" in css
    assert "ol.thesis-rail > li:last-child { border-bottom" in css, \
        "the rail must close with a hairline, otherwise the last row floats"


def test_hero_stat_keeps_the_sign_and_stays_inside_its_own_sentence():
    out, label = hero_stat("De-rating multiple 2026 + arus asing membaik",
                           "EV/EBITDA 2026 17,99× vs 34,31× (2025). Asing 90d −Rp 0,37 tn tapi +Rp 0,24 tn.",
                           True)
    assert out == "17,99×"
    got, lab = hero_stat("Arus asing 90 hari", "Asing 90d −Rp 0,37 tn tapi +Rp 0,24 tn dalam 30d; sisanya.", True)
    assert got.startswith(("−", "-", "–")) and "Rp 0,37 tn" in got, "an outflow must not read as an inflow"
    assert "10,07" not in lab and "PE" not in lab.upper(), f"label crossed a sentence boundary: {lab!r}"
    assert lab.upper().startswith("ASING")


def test_hero_stat_is_generic():
    """Any issuer: a line with a ratio takes the ratio, a line with no figure takes no anchor, and the
    headline wins over the detail."""
    assert hero_stat("Margin naik", "EBITDA margin 23,4% vs 19,1%.") == "23,4%"
    assert hero_stat("Belanja modal turun", "capex turun setengahnya tanpa angka.") == ""
    assert hero_stat("Utang Rp 110.79 tn", "utang bruto Rp 110.79 tn vs kas Rp 13.85 tn") == "Rp 110.79 tn"
    assert hero_stat("") == ""
