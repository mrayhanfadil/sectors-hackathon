"""Tests for friend DCF math functions ported to our deterministic engines.

Covers:
  - Blume beta adjustment
  - Full WACC computation (unlevered, debt floor, capital structure weights)
  - FCFF linear fade projection
  - Gordon Growth terminal value + dependency checks
  - Mid-year discounting and EV-to-equity bridge
  - Recommendation engine + Review Required gate
  - 5x5 WACC x g sensitivity grid
  - Bull/Base/Bear operational scenarios
  - Full DCF smoke tests for RATU and archetype tickers
"""

import pytest
from server.engines import (
    beta_blume_adj,
    compute_wacc_full,
    wacc_table_dict,
    project_fcff_simple,
    terminal_value_gordon,
    tv_dependency_check,
    discount_and_bridge,
    make_recommendation,
    sensitivity_grid,
    scenarios_bull_bear,
    dcf_full,
    _NullFlags,
)


def test_beta_blume_adj():
    # beta_raw=1.2 -> adjusted=1.1 (0.67*1.2 + 0.33*1.0 = 1.134 -> rounds to 1.1)
    beta_raw = 1.2
    adj = beta_blume_adj(beta_raw)
    assert round(adj, 1) == 1.1
    assert abs(adj - (0.67 * 1.2 + 0.33 * 1.0)) < 1e-5


def test_compute_wacc_full_no_debt():
    # rf=0.065, beta=1.0, erp=0.07, cod=0.10, market_cap=1e15, total_debt=0 -> Ke=13.5%, Wd=0%, WACC=13.5%
    res = compute_wacc_full(
        rf=0.065,
        beta=1.0,
        erp=0.07,
        cod=0.10,
        market_cap=1e15,
        total_debt=0.0,
        tax=0.22,
        size_premium=0.0,
    )
    assert res["ke"] == pytest.approx(0.135)
    assert res["weight_debt"] == pytest.approx(0.0)
    assert res["weight_equity"] == pytest.approx(1.0)
    assert res["wacc"] == pytest.approx(0.135)


def test_compute_wacc_full_with_debt_floor():
    # cod=0.04 should be floored to rf+200bps=8.5%, verify warning via flags
    class FlagCollector:
        def __init__(self):
            self.warnings = []
        def warn(self, field, msg):
            self.warnings.append((field, msg))

    flags = FlagCollector()
    res = compute_wacc_full(
        rf=0.065,
        beta=1.0,
        erp=0.07,
        cod=0.04,
        market_cap=1e12,
        total_debt=1e12,
        tax=0.22,
        flags=flags,
    )
    # Floored to 0.065 + 0.02 = 0.085 (8.5%)
    assert res["kd_pretax"] == pytest.approx(0.085)
    assert len(flags.warnings) > 0 or len(res["warnings"]) > 0


def test_project_fcff_fade():
    # verify growth fades linearly g1 -> g_terminal
    proj = project_fcff_simple(
        revenue_t0=10000.0,
        g1=0.10,
        g_terminal=0.02,
        years=5,
        ebit_margin=0.15,
        tax=0.22,
        capex_pct=0.06,
        nwc_pct=0.10,
    )
    assert len(proj) == 5
    assert proj[0]["growth"] == pytest.approx(0.10)
    assert proj[4]["growth"] == pytest.approx(0.02)
    # Linear step: midpoint at year 3 is 0.06
    assert proj[2]["growth"] == pytest.approx(0.06)
    assert all("fcff" in row and "revenue" in row and "nopat" in row for row in proj)
    # Year 1 revenue: 10000 * 1.10 = 11000
    assert proj[0]["revenue"] == pytest.approx(11000.0)


def test_terminal_value_gordon():
    # fcff=100, wacc=0.10, g=0.03 -> TV = 100 * 1.03 / 0.07 = 1471.43
    tv = terminal_value_gordon(fcff_last=100.0, wacc=0.10, g=0.03, ebitda_last=200.0)
    assert tv["valid"] is True
    assert tv["tv_nominal"] == pytest.approx(1471.43, rel=1e-4)
    assert tv["implied_exit_multiple"] == pytest.approx(1471.43 / 200.0, rel=1e-3)


def test_tv_dependency_flag():
    # pv_tv=800, ev=1000 -> 80% triggers flag
    dep = tv_dependency_check(pv_tv=800.0, enterprise_value=1000.0)
    assert dep["dependency_pct"] == pytest.approx(0.80)
    assert dep["dependency_flag"] is True

    dep_low = tv_dependency_check(pv_tv=700.0, enterprise_value=1000.0)
    assert dep_low["dependency_pct"] == pytest.approx(0.70)
    assert dep_low["dependency_flag"] is False


def test_make_recommendation_buy():
    # upside = +0.15 -> BUY
    val = {"upside": 0.15, "fair_value_per_share": 1150.0, "market_price": 1000.0}
    rec = make_recommendation(val)
    assert rec["rating"] == "BUY"
    assert rec["label"] == "Undervalued"
    assert "reason_override" not in rec


def test_make_recommendation_review_required():
    # upside = +1.5 -> "Review Required" + reason
    val = {"upside": 1.50, "fair_value_per_share": 2500.0, "market_price": 1000.0}
    rec = make_recommendation(val)
    assert rec["rating"] == "Review Required"
    assert "reason_override" in rec
    assert "defensible range" in rec["reason_override"]


def test_sensitivity_grid_shape():
    # steps=2 -> 5x5 matrix, stats.min < stats.max
    proj = project_fcff_simple(
        revenue_t0=10000e9,
        g1=0.08,
        g_terminal=0.025,
        years=5,
        ebit_margin=0.15,
        tax=0.22,
        capex_pct=0.06,
        nwc_pct=0.10,
    )
    snapshot = {
        "cash": 1000e9,
        "total_debt": 2000e9,
        "minority": 0.0,
        "shares_outstanding": 10e9,
        "price": 1000.0,
    }
    sens = sensitivity_grid(
        proj=proj,
        wacc_base=0.10,
        g_base=0.025,
        snapshot=snapshot,
        steps=2,
    )
    assert len(sens["fair_value"]) == 5
    assert all(len(row) == 5 for row in sens["fair_value"])
    assert len(sens["wacc_axis"]) == 5
    assert len(sens["g_axis"]) == 5
    assert sens["stats"]["min"] < sens["stats"]["max"]
    assert sens["stats"]["n_valid"] > 0


def test_scenarios_order():
    # BEAR < BASE < BULL (when feasible)
    proj = project_fcff_simple(
        revenue_t0=10000e9,
        g1=0.10,
        g_terminal=0.025,
        years=5,
        ebit_margin=0.15,
        tax=0.22,
        capex_pct=0.06,
        nwc_pct=0.10,
    )
    snapshot = {
        "revenue": 10000e9,
        "cash": 1000e9,
        "total_debt": 2000e9,
        "minority": 0.0,
        "shares_outstanding": 10e9,
        "price": 1000.0,
    }
    hist_std = {"rev_growth_sd": 0.04, "ebit_margin_sd": 0.02}
    scen = scenarios_bull_bear(
        proj_or_params=proj,
        wacc_base=0.10,
        g_base=0.025,
        hist_std=hist_std,
        snapshot=snapshot,
    )
    assert "BEAR" in scen and "BASE" in scen and "BULL" in scen
    bear_fv = scen["BEAR"]["fair_value_per_share"]
    base_fv = scen["BASE"]["fair_value_per_share"]
    bull_fv = scen["BULL"]["fair_value_per_share"]
    assert bear_fv is not None and base_fv is not None and bull_fv is not None
    assert bear_fv < base_fv < bull_fv


def test_dcf_full_smoke_mtel_overrides_backed():
    # Loud policy Sep 2026: dcf_full requires explicit inputs (file or overrides).
    # No data/assumptions/*.json exist post-purge — all MTEL math flows via overrides.
    res = dcf_full(
        "MTEL",
        overrides={
            "rf": 0.07, "beta": 1.0, "erp": 0.069, "cod": 0.09,
            "revenue": 5000e9, "ebit_margin": 0.20, "g1": 0.08, "g": 0.03,
            "tax": 0.22, "capex_pct": 0.06, "nwc_pct": 0.05,
            "shares_out": 5e9, "last_price": 2000.0, "price": 2000.0,
        },
    )
    required_keys = [
        "wacc",
        "wacc_table",
        "projection",
        "terminal",
        "valuation",
        "recommendation",
        "sensitivity",
        "scenarios",
        "provenance",
    ]
    for k in required_keys:
        assert k in res, f"Missing key {k} in dcf_full result"

    assert res["provenance"] == "dcf_full: wacc+sens+scenarios from friend's s05-s12"
    assert isinstance(res["wacc_table"], list)
    assert isinstance(res["projection"], list)
    assert isinstance(res["sensitivity"]["fair_value"], list)
    assert "BEAR" in res["scenarios"] and "BASE" in res["scenarios"] and "BULL" in res["scenarios"]
    assert res["valuation"]["fair_value_per_share"] > 0


def test_dcf_full_bare_ratu_raises_no_seeds():
    # Seed bases killed Sep 2026: RATU.json is provenance-only (no valuation
    # keys) so bare dcf_full must raise naming the gap, never invent math.
    import pytest as _pytest

    with _pytest.raises(ValueError, match="missing explicit inputs"):
        dcf_full("RATU")


def test_dcf_full_unknown_ticker_raises_no_file():
    # Loud policy: unknown tickers raise naming the explicit inputs the caller
    # must supply (no seed-math, no fabricated fallback).
    import pytest as _pytest

    with _pytest.raises(ValueError, match="missing explicit inputs"):
        dcf_full("ZZZZZZ")


def test_dcf_full_review_required_threshold():
    # extreme assumption -> review_required (overrides-only; no assumption file)
    res = dcf_full(
        "MTEL",
        overrides={
            "rf": 0.07, "beta": 1.0, "erp": 0.069, "cod": 0.09,
            "revenue": 5000e9, "ebit_margin": 0.20, "g1": 0.08, "g": 0.03,
            "tax": 0.22, "capex_pct": 0.06, "nwc_pct": 0.05,
            "shares_out": 5e9, "last_price": 50.0, "price": 50.0,
        },
    )
    assert res["recommendation"]["rating"] == "Review Required"
    assert "reason_override" in res["recommendation"]


def test_wacc_table_dict_rendering():
    wacc_res = compute_wacc_full(
        rf=0.065,
        beta=1.2,
        erp=0.07,
        cod=0.08,
        market_cap=800e9,
        total_debt=200e9,
        tax=0.22,
    )
    table = wacc_table_dict(wacc_res)
    assert isinstance(table, list)
    assert len(table) >= 10
    assert any(row["label"].startswith("Cost of Equity") for row in table)
    assert any(row["label"].startswith("WACC") for row in table)


def test_make_recommendation_sell_and_hold():
    sell_rec = make_recommendation({"upside": -0.25, "fair_value_per_share": 750.0, "market_price": 1000.0})
    assert sell_rec["rating"] == "SELL"
    assert sell_rec["label"] == "Overvalued"

    hold_rec = make_recommendation({"upside": 0.05, "fair_value_per_share": 1050.0, "market_price": 1000.0})
    assert hold_rec["rating"] == "HOLD"
    assert hold_rec["label"] == "Fairly valued"
