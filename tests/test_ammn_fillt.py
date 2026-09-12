"""AMMN-FILLT pins (Spark 1.3, 12 Sep 2026).

Verifies the Sectors-harvested fill (output/cache/ammn_fill, sibling lane
t_2c5f420e) is wired into _build_live_payload for AMMN and renders on BOTH
paths (server HTML + Typst CLI) with real numbers, honest-empty GAPs and
holding tie-outs. Keyless: needs only the local harvest dir (0 credits);
skips honestly when it is absent.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

FILL_DIR = PROJECT_ROOT / "output" / "cache" / "ammn_fill"
needs_fill = pytest.mark.skipif(
    not (FILL_DIR / "company_report_AMMN_multisection.json").exists(),
    reason="needs sibling harvest output/cache/ammn_fill (t_2c5f420e), 0 credits",
)


def _payload():
    from server.routers.pdf import _build_live_payload

    return _build_live_payload("AMMN", None)


@needs_fill
def test_fill_meta_reports_filled_vs_gaps():
    d = _payload()
    fm = d.get("fill_meta") or {}
    assert len(fm.get("filled", [])) >= 15, fm.get("filled")
    assert len(fm.get("gaps", [])) == 10, fm.get("gaps")


@needs_fill
def test_cover_anchors():
    d = _payload()
    assert d["meta"]["company_name"] == "PT Amman Mineral Internasional Tbk."
    assert d["meta"]["sector"].startswith("Basic Materials")
    rb = d["cover"]["rating_box"]
    assert rb["price"] == 4860.0
    assert rb["upside_pct"] == pytest.approx(round((rb["tp"] - rb["price"]) / rb["price"] * 100, 2), abs=0.02)
    assert rb["action"] in ("BUY", "TRADING BUY", "HOLD", "TRADING SELL", "SELL")
    assert d["cover"]["shares"]["outstanding"] == 72.5
    assert len(d["cover"]["shareholders"]) == 12
    assert d["cover"]["shareholders"][0]["name"] == "PT Sumber Gemilang Persada"
    # GAPs stay honest-empty
    assert d["cover"]["vs_jci"]["ytd_abs"] is None
    assert d["cover"]["vs_jci"]["ytd_rel"] is None
    assert d["cover"]["shares"]["free_float_pct"] is None
    assert d["valuation"]["bands"] is None
    # 90d chart series is real (62 sessions joined)
    ch = d["cover"]["vs_jci"]["chart"]
    assert len(ch["labels"]) == 62
    assert len(ch["series"][0]) == 62 and len(ch["series"][1]) == 62


@needs_fill
def test_thesis_and_summary_populated():
    d = _payload()
    assert len(d["thesis"]) == 4
    for t in d["thesis"]:
        assert t["headline"] and t["detail"] and t["source"]
    blob = " ".join(t["detail"] for t in d["thesis"]) + d["cover"]["summary"]
    assert "lengkapi fixture" not in blob
    assert "Rp" in d["cover"]["summary"]
    assert str(d["cover"]["rating_box"]["tp"]) in d["cover"]["summary"]


@needs_fill
def test_segments_two_pillars_sum_100():
    d = _payload()
    segs = d["segments"]
    assert len(segs) == 2
    assert abs(sum(s["share_pct"] for s in segs) - 100) <= 0.5
    names = {s["name"] for s in segs}
    assert names == {"Tembaga", "Emas"}


@needs_fill
def test_tie_outs_hold_on_real_numbers():
    d = _payload()
    fh = {r[0]: r[1:] for r in d["financial_highlights"]["rows"]}
    stmts = {s["title"]: {r[0]: r[1:] for r in s["rows"]} for s in d["financials"]}
    # NP == Ex3: income Net Profit == FH Laba Bersih == key_financials Net Profit
    assert stmts["Income Statement"]["Net Profit"] == fh["Laba Bersih (Rp bn)"]
    kf = {r[0]: r[1:] for r in d["key_financials"]["rows"]}
    assert kf["Net Profit (Rp bn)"] == fh["Laba Bersih (Rp bn)"][1:]
    # cash == BS: CF footer close == balance cash row
    cf = d["financial_statements"]["cashflow"]
    assert cf["footers"][2][1:] == stmts["Balance Sheet"]["Cash & Equivalents"]
    # spot anchors on real prints
    assert fh["Laba Bersih (Rp bn)"][-1] == 4167.0
    assert fh["Pendapatan Bersih (Rp bn)"][2] == 44127.3


@needs_fill
def test_peers_news_risks_catalysts():
    d = _payload()
    pt = d["peers"]["tables"][0]
    assert len(pt["rows"]) == 9  # subject excluded from median/average (modeler rule)
    assert pt["median"][2] == 12.51
    assert pt["median"][4] == 2.16
    assert pt["average"][2] == 1003.88
    assert all(r[3] == "—" for r in pt["rows"])  # GAP G8: no peer EV/EBITDA
    assert len(d["news"]) == 8
    assert all(n["url"] and n["date"] for n in d["news"])
    assert len(d["risks"]) == 6
    assert all(r["bucket"] and r["detail"] for r in d["risks"])
    assert len(d["catalysts"]) == 4


@needs_fill
def test_single_archetype_both_paths():
    d = _payload()
    from scripts.select_template import select_template

    assert select_template(d)[0] == "single"
    from server.report.typst_renderer import _resolve_archetype

    assert _resolve_archetype("AMMN", d, "auto") == "single"


@needs_fill
def test_server_html_has_no_placeholders():
    from server.routers.pdf import render_html_for_ticker

    tpl, html, data = render_html_for_ticker("AMMN", None)
    assert tpl == "single"
    assert "lengkapi fixture" not in html
    assert "Bauran emas menyalip tembaga" in html
    assert str(data["cover"]["rating_box"]["tp"]) in html


@needs_fill
@pytest.mark.slow
def test_typst_renders_clean_with_contiguous_numbering(tmp_path):
    if not shutil.which("typst") or not shutil.which("pdftotext"):
        pytest.skip("needs typst + pdftotext binaries")
    from server.report.typst_renderer import render_report

    out = tmp_path / "ammn_fillt.pdf"
    pdf = render_report("AMMN", archetype="auto", out_path=out)
    assert Path(pdf).exists()
    assert Path(pdf).stat().st_size > 20_000
    text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                          capture_output=True, text=True, check=True).stdout
    assert "lengkapi fixture" not in text
    assert "4 Pilar Tesis Investasi" in text
    nums = [int(m.group(1)) for m in re.finditer(r"Exhibit\s+(\d+)\.", text)]
    assert nums, "no exhibits found in AMMN pdf"
    assert nums == list(range(2, max(nums) + 1)), nums
    sources = text.count("Source: Company, Team Estimates")
    assert sources == len(nums), (sources, len(nums))
    assert "Equity Research" in text
    assert "sectors.app" in text
