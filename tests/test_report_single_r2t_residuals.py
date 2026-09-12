"""AMMN-R2T residual fixes R1-R5 pins (Spark 1.3, 12 Sep 2026).

Guards the five template fixes against regression in BOTH report_single.typ
mirrors (templates/typst/archetypes <-> server/report/typst, modulo the two
import rewrites):
  R1: one-time exhibit-counter offset so Ex 1 is skipped (first header = Ex 2).
  R2: Financial-Highlights defaults are honest dashes (tie-out with Slide-1).
  R3: Slide-3 combo + Slide-5 band headers fire unconditionally with a
      chart-placeholder fallback (no numbering shift keyless vs keyed).
  R4: relval_bars + peer_evebitda demoted to un-numbered plain titles.
  R5: Mid-Cycle EV/EBITDA table lives on the Slide-4 DCF deep-dive page
      (before Cost of Capital Build), not on Page 4.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
COPIES = [
    REPO_ROOT / "templates" / "typst" / "archetypes" / "report_single.typ",
    REPO_ROOT / "server" / "report" / "typst" / "report_single.typ",
]

COUNTER_OFFSET = '#counter(figure.where(kind: "exhibit")).update(1)'

COMBO_TITLES = {
    "rc_title": "revenue_combo",
    "ec_title": "ebitda_combo",
    "nc_title": "netprofit_combo",
    "pcc_title": "production_cost",
}
BAND_TITLES = {
    "peb_title": "pe_hist_band",
    "pbb_title": "pbv_hist_band",
}

HARDCODED_FH_NUMBERS = ("1.290", "1.122", '"610"', '"540"', '"402"', '"355"', "55,2x")


def _src(path: Path) -> str:
    assert path.exists(), f"missing template copy: {path}"
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("path", COPIES, ids=lambda p: p.parent.parent.name)
def test_r1_counter_offset_once_before_first_header(path: Path) -> None:
    txt = _src(path)
    assert txt.count(COUNTER_OFFSET) == 1, "R1 offset must appear exactly once"
    assert txt.index(COUNTER_OFFSET) < txt.index("#exhibit-header("), (
        "R1 offset must precede the first exhibit header"
    )


@pytest.mark.parametrize("path", COPIES, ids=lambda p: p.parent.parent.name)
def test_r2_fh_defaults_are_dashes(path: Path) -> None:
    txt = _src(path)
    block = txt[txt.index("#let default_fh_rows") : txt.index("#let fh_rows")]
    for num in HARDCODED_FH_NUMBERS:
        assert num not in block, f"R2: hardcoded FH number {num} still in defaults"
    assert block.count('"—"') >= 7, "R2: FH default rows must be honest dashes"


@pytest.mark.parametrize("path", COPIES, ids=lambda p: p.parent.parent.name)
def test_r3_combo_headers_fire_with_placeholder_fallback(path: Path) -> None:
    txt = _src(path)
    for var, flag in COMBO_TITLES.items():
        assert f"chart-placeholder({var}," in txt, f"R3: no placeholder for {flag}"
        header_at = txt.index(f"#exhibit-header({var},")
        guard_at = txt.index(f'.at("{flag}", default: false)')
        assert header_at < guard_at, f"R3: {flag} header must sit OUTSIDE its chart guard"


@pytest.mark.parametrize("path", COPIES, ids=lambda p: p.parent.parent.name)
def test_r3_band_headers_fire_with_placeholder_fallback(path: Path) -> None:
    txt = _src(path)
    for var, flag in BAND_TITLES.items():
        assert f"chart-placeholder({var}," in txt, f"R3: no placeholder for {flag}"
        header_at = txt.index(f"#exhibit-header({var},")
        guard_at = txt.index(f'.at("{flag}", default: false)')
        assert header_at < guard_at, f"R3: {flag} header must sit OUTSIDE its chart guard"


@pytest.mark.parametrize("path", COPIES, ids=lambda p: p.parent.parent.name)
def test_r4_extras_demoted_to_plain_titles(path: Path) -> None:
    txt = _src(path)
    assert "exhibit-header(relval_title" not in txt, "R4: relval_bars still numbered"
    assert 'exhibit-header("EV/EBITDA Peers vs Subjek"' not in txt, (
        "R4: peer_evebitda still numbered"
    )
    assert "[#relval_title]" in txt, "R4: relval plain title missing"
    assert "[EV/EBITDA Peers vs Subjek]" in txt, "R4: evebitda plain title missing"


@pytest.mark.parametrize("path", COPIES, ids=lambda p: p.parent.parent.name)
def test_r5_midcycle_on_dcf_page_before_coc(path: Path) -> None:
    txt = _src(path)
    page4 = txt.index("// PAGE 4 — VALUATION")
    page5 = txt.index("// PAGE 5 — COMPREHENSIVE DCF")
    page6 = txt.index("// PAGE 6 — PEERS")
    mid = txt.index("EV/EBITDA Mid-Cycle Cross-Check (3Y Average)")
    coc = txt.index('#exhibit-header("Cost of Capital Build"')
    assert page5 < mid < coc < page6, (
        "R5: mid-cycle table must live on the DCF deep-dive page before CoC"
    )
    assert not (page4 < mid < page5), "R5: mid-cycle table still on Page 4"
