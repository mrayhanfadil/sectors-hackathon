"""The normalised-multiple check, and the evidence that it is NOT the fix for a ramping resource name."""
from __future__ import annotations

import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CACHE = ROOT / "output" / "cache" / "ammn_fill" / "raw_cache" / "company_report_AMMN__33503f87.json"
ASSUM = ROOT / "data" / "assumptions" / "AMMN.json"

pytestmark = pytest.mark.skipif(not CACHE.exists() or not ASSUM.exists(),
                                reason="AMMN cached payload or assumptions file absent")


@pytest.fixture(scope="module")
def history() -> dict:
    from server.valuation.normalised_multiple import normalised_multiple_history

    rep = json.loads(CACHE.read_text())
    return normalised_multiple_history(rep["financials"]["historical_financials"],
                                       rep["valuation"]["historical_valuation"])


def test_reconstruction_matches_the_dataset_own_print(history):
    """The market cap is rebuilt from P/E x net income; if that is wrong, every multiple here is wrong."""
    assert history["max_reconstruction_gap"] is not None
    assert history["max_reconstruction_gap"] < 0.01, history["rows"]


def test_normalised_basis_exists_for_every_print_with_a_full_window(history):
    checked = [r for r in history["rows"] if r["window_years"]]
    assert checked, "no print year had a rolling EBITDA window"
    for r in checked:
        assert r["normalised_multiple"] is not None
        assert len(r["window_years"]) == 3, r


def test_rebasing_the_multiple_does_not_rescue_this_name(history):
    """The reason this module is a DIAGNOSTIC, not a valuation brick: on a ramping resource name the
    normalised and trailing multiples land in the same place, because the market pays for the asset base
    rather than for trailing earnings. If someone later reports a materially lower normalised multiple,
    this test is where they find out what changed."""
    assert history["trailing_mean"] and history["normalised_mean"]
    ratio = history["normalised_mean"] / history["trailing_mean"]
    assert 0.8 < ratio < 1.25, f"normalised {history['normalised_mean']:.2f}x vs trailing " \
                               f"{history['trailing_mean']:.2f}x — the rebase now does something new"


def test_applying_the_normalised_multiple_still_lands_far_above_the_market(history):
    """Documented dead end: mid-30s multiples on a recovered level are multiples of the market price."""
    import sys

    sys.path.insert(0, str(ROOT))
    from server.report.forecast_path import resolve_forecast_path
    from server.valuation.normalised_multiple import apply_multiple

    assum = json.loads(ASSUM.read_text())
    shares = float(assum["shares_out"]) / 1e9
    cash, debt = float(assum["cash"]) / 1e9, float(assum["total_debt"]) / 1e9
    price = float(assum["last_price"])
    ebitda = resolve_forecast_path("AMMN")["drivers"]["ebitda"]["rp_bn"]
    res = apply_multiple(history["normalised_mean"], ebitda[0], cash, debt, shares)
    assert res["per_share"] > price * 2, ("the rebased multiple should be reported as unusable for this "
                                          "name, not quietly shipped as a target price")


def test_market_ev_is_stable_while_earnings_swing(history):
    """Why the multiple series is not an anchor here: EV barely moves while EBITDA halves and doubles."""
    evs = [r["ev_rp_bn"] for r in history["rows"]]
    ebitdas = [r["ebitda_rp_bn"] for r in history["rows"]]
    assert max(ebitdas) / min(ebitdas) > 1.4, ebitdas          # earnings swing hard
    assert max(evs) / min(evs) < 1.5, evs                      # the EV does not


def test_no_reserve_data_in_the_licence_for_the_rnav_leg():
    """The reserve-based leg BRIDS uses is not buildable from the licensed dataset — recorded so nobody
    'finds' reserve numbers that were never licensed."""
    blob = CACHE.read_text().lower()
    for needle in ("reserve", "ore_tonnage", "grade", "proven_probable"):
        assert needle not in blob, f"{needle!r} appeared in the licensed payload — the RNAV leg can be built"
