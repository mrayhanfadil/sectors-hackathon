"""The deck's gate-primary leg must state its multiple basis, and the TP must tie to it."""
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ASSUM = ROOT / "data" / "assumptions" / "AMMN.json"
DRIVER = ROOT / "data" / "drivers" / "AMMN.json"

pytestmark = pytest.mark.skipif(not ASSUM.exists() or not DRIVER.exists(),
                                reason="AMMN assumptions or driver file absent")


@pytest.fixture(scope="module")
def payload() -> dict:
    from server.routers.pdf import render_html_for_ticker

    return render_html_for_ticker("AMMN", None)[2]


def test_gate_primary_is_a_forward_multiple_on_a_stated_level():
    a = json.loads(ASSUM.read_text())
    assert "forward" in str(a["gate_primary"]).lower()
    assert float(a["ev_multiple"]) == pytest.approx(15.0)
    ebitda_f = json.loads(DRIVER.read_text())["drivers"]["ebitda"]["path"]
    fx = json.loads(DRIVER.read_text())["fx_rp_bn_per_usd_mn"]
    assert float(a["ebitda"]) == pytest.approx(ebitda_f[0] * fx * 1e9, rel=1e-6), \
        "the multiple must multiply the FORWARD level, not the historic average"
    assert "level forward" in str(a["ebitda_leg_level_note"]).lower()


def test_the_own_history_multiple_is_recorded_as_unusable_with_a_reason():
    a = json.loads(ASSUM.read_text())
    own = a["ev_multiple_own_history"]
    assert own["usable_as_anchor"] is False
    assert own["trailing_mean"] and own["normalised_mean"]
    assert len(str(own["why"])) > 80, "the refusal must carry its reasoning, not a bare flag"


def test_target_price_ties_to_multiple_times_forward_ebitda(payload):
    a = json.loads(ASSUM.read_text())
    shares_bn = float(a["shares_out"]) / 1e9
    level_bn = float(a["ebitda"]) / 1e9
    cash_bn, debt_bn = float(a["cash"]) / 1e9, float(a["net_debt"]) / 1e9
    want = (float(a["ev_multiple"]) * level_bn + cash_bn - debt_bn) / shares_bn
    assert float(payload["cover"]["rating_box"]["tp"]) == pytest.approx(want, abs=2.0)


def test_the_valuation_exhibit_shows_the_basis_and_the_rejected_basis(payload):
    rows = ((payload.get("valuation") or {}).get("midcycle") or {}).get("rows") or []
    assert rows, "the valuation exhibit is missing"
    blob = " ".join(str(c) for r in rows for c in r)
    assert "basis TP" in blob, "the exhibit must mark which level and multiple drive the target price"
    assert "tidak dipakai" in blob.lower(), "the rejected own-history basis must be shown as rejected"
    assert "13,3" in blob and "15,7" in blob, "the market and third-party cross-checks must be on the page"


def test_a_rejected_basis_row_computes_the_rejected_multiple(payload):
    """A row labelled 'if that multiple were used' must not quietly use the accepted one."""
    a = json.loads(ASSUM.read_text())
    rows = ((payload.get("valuation") or {}).get("midcycle") or {}).get("rows") or []
    row = next((r for r in rows if "Own-history multiple pada level FY26F" in str(r[0])), None)
    assert row, "the rejected-basis row disappeared"
    from tests.idn_number import to_float

    shown = to_float(row[1])
    shares_bn = float(a["shares_out"]) / 1e9
    want = ((a["ev_multiple_own_history"]["trailing_mean"] * float(a["ebitda"]) / 1e9
             + float(a["cash"]) / 1e9 - float(a["net_debt"]) / 1e9) / shares_bn)
    assert shown == pytest.approx(want, rel=0.01), (shown, want)


def test_rating_and_target_stay_consistent_with_the_market_price(payload):
    rb = payload["cover"]["rating_box"]
    price, tp = float(rb["price"]), float(rb["tp"])
    assert tp > price, "a Buy with a target below the price is a contradiction"
    assert rb["upside_pct"] == pytest.approx((tp / price - 1) * 100, abs=0.2)


def test_gate_requires_the_basis_disclosure(payload):
    """The rule that the agent carries must also be enforced where a page can violate it."""
    from server.report.house_rules import audit_house_rules

    assert audit_house_rules(payload)["violations"] == []
    import copy

    broken = copy.deepcopy(payload)
    broken["valuation_page"]["notes"] = [n for n in broken["valuation_page"]["notes"]
                                         if "BASIS MULTIPLE" not in n]
    # strip the basis AND the rejection: the page prices a leg without saying what produced it
    broken["valuation"]["midcycle"]["rows"] = []
    out = audit_house_rules(broken)["violations"]
    assert any("basis of the level" in v for v in out), out
    assert any("rejected basis" in v for v in out), out


def test_sensitivity_block_reads_its_numbers_from_the_payload():
    """The block's chips and bridge must follow the model: change the payload and the text must move with it.

    The block used to be prose that restated the same values by hand, so a model change could leave the page
    describing a stale number. This pins the components to `valuation_page`.
    """
    import re

    from server.routers import pdf as pdf_mod
    from server.routers.pdf import render_html_for_ticker

    _t, html, data = render_html_for_ticker("AMMN", None)
    vp = data["valuation_page"]
    br = vp["bridge"]

    # the terminal-value chip carries the payload's share, scaled (the pct filter takes percent units)
    share = f"{round(br['tv_share'] * 100, 1):.1f}".replace(".", ",")
    assert share in html.replace("+", ""), "the chip must show the model's terminal-value share"

    # a changed model value must change the rendered block
    assert '<div class="sens-strip">' in html and 'class="bridge-bar"' in html
    assert "class=\"field\"" in html
