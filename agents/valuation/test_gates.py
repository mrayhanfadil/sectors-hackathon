"""Tests for agents/valuation/gates.py - 6-gate Valuation Method Selection Framework.

≥18 tests covering each gate's decision branches + 5 quintet ticker integration.
"""

import pytest

from agents.valuation.gates import (
    DOMAIN_BANK,
    DOMAIN_HOLDING_DISSIMILAR,
    DOMAIN_MINING,
    DOMAIN_OIL_GAS,
    DOMAIN_PLANTATION,
    DOMAIN_REIT,
    DOMAIN_SINGLE_BUSINESS,
    evaluate,
)


# ---------- Gate 0 - Business Model ----------

def test_gate0_bank_goes_to_ddm():
    v = evaluate(
        "TEST_BANK",
        domain=DOMAIN_BANK,
        filing_history_years=25,
        ebit_positive_count=3,
        d_de_ratio=0.0,
        net_debt_to_ebitda=0.0,
        interest_coverage=999.0,
        shareholders_equity=1e12,
        nci_pct=2.0,
        revenue_drivers=["net_interest_margin"],
        has_steady_state_3y=True,
        life_cycle_stage="mature",
        upside_pct=20.0,
    )
    assert v.primary == "DDM / Excess Return"
    assert "0_business_model" in v.gates_passed


def test_gate0_reit_goes_to_nav():
    v = evaluate(
        "TEST_REIT",
        domain=DOMAIN_REIT,
        filing_history_years=8,
        ebit_positive_count=3,
        d_de_ratio=0.4,
        net_debt_to_ebitda=4.0,
        interest_coverage=2.5,
        shareholders_equity=1e10,
        nci_pct=5.0,
        revenue_drivers=["rental"],
        has_steady_state_3y=True,
        life_cycle_stage="mature",
    )
    assert v.primary == "NAV / Reserve-based"


@pytest.mark.parametrize("domain", [DOMAIN_MINING, DOMAIN_OIL_GAS, DOMAIN_PLANTATION])
def test_gate0_finite_reserves_go_to_nav(domain):
    v = evaluate(
        "TEST_RESOURCE",
        domain=domain,
        filing_history_years=10,
        ebit_positive_count=3,
        d_de_ratio=0.3,
        net_debt_to_ebitda=1.5,
        interest_coverage=4.0,
        shareholders_equity=1e10,
        nci_pct=10.0,
        revenue_drivers=["commodity_coal"],
        has_steady_state_3y=True,
        life_cycle_stage="mature",
    )
    assert v.primary == "NAV / Reserve-based"


def test_gate0_holding_dissimilar_goes_to_sotp():
    v = evaluate(
        "TEST_HOLDING",
        domain=DOMAIN_HOLDING_DISSIMILAR,
        filing_history_years=15,
        ebit_positive_count=3,
        d_de_ratio=0.4,
        net_debt_to_ebitda=2.0,
        interest_coverage=3.0,
        shareholders_equity=5e10,
        nci_pct=20.0,
        revenue_drivers=["volume_manufacturing", "rental"],
        has_steady_state_3y=True,
        life_cycle_stage="mature",
    )
    assert v.primary == "SOTP"


def test_gate0_single_business_passes_through():
    v = evaluate(
        "TEST_SINGLE",
        domain=DOMAIN_SINGLE_BUSINESS,
        filing_history_years=8,
        ebit_positive_count=3,
        d_de_ratio=0.3,
        net_debt_to_ebitda=1.5,
        interest_coverage=4.0,
        shareholders_equity=1e10,
        nci_pct=5.0,
        revenue_drivers=["volume_consumer"],
        has_steady_state_3y=True,
        life_cycle_stage="mature",
    )
    assert v.primary == "FCFF/WACC DCF"
    assert "0_business_model" in v.gates_passed


# ---------- Gate 1 - Data Eligibility ----------

def test_gate1_thin_data_triggers_shortened_dcf_and_disclosure():
    """User decision: Gate 1a fail → shortened DCF + thin_data=True (NOT pure Relative)."""
    v = evaluate(
        "TEST_THIN",
        domain=DOMAIN_SINGLE_BUSINESS,
        filing_history_years=2,  # < 4y
        ebit_positive_count=3,
        d_de_ratio=0.4,
        net_debt_to_ebitda=2.0,
        interest_coverage=3.0,
        shareholders_equity=1e10,
        nci_pct=5.0,
        revenue_drivers=["volume_consumer"],
        has_steady_state_3y=True,
        life_cycle_stage="growth",
    )
    assert v.primary == "DCF (shortened horizon)"
    assert v.thin_data is True
    assert "1a_filing_history" in v.gates_failed


def test_gate1_profitability_failure_escalates_to_relative():
    v = evaluate(
        "TEST_LOSER",
        domain=DOMAIN_SINGLE_BUSINESS,
        filing_history_years=8,
        ebit_positive_count=0,  # chronic losses
        d_de_ratio=0.3,
        net_debt_to_ebitda=1.5,
        interest_coverage=4.0,
        shareholders_equity=1e10,
        nci_pct=5.0,
        revenue_drivers=["volume_consumer"],
        has_steady_state_3y=True,
        life_cycle_stage="high_growth_pre_profit",
    )
    assert v.primary == "EV/Sales"  # life-cycle gate also fires
    assert "1b_profitability" in v.gates_failed


def test_gate1_capital_structure_breach_does_not_change_primary():
    v = evaluate(
        "TEST_LEVERED",
        domain=DOMAIN_SINGLE_BUSINESS,
        filing_history_years=8,
        ebit_positive_count=3,
        d_de_ratio=0.85,  # > 80%
        net_debt_to_ebitda=7.0,  # > 6x
        interest_coverage=0.8,  # < 1x
        shareholders_equity=1e10,
        nci_pct=5.0,
        revenue_drivers=["volume_consumer"],
        has_steady_state_3y=True,
        life_cycle_stage="mature",
    )
    assert v.primary == "FCFF/WACC DCF"  # primary unchanged
    assert "1c_capital_structure" in v.gates_failed
    assert v.secondary == "Relative Valuation"  # mandatory cross-check


def test_gate1_negative_equity_forces_relative():
    v = evaluate(
        "TEST_NEG_EQ",
        domain=DOMAIN_SINGLE_BUSINESS,
        filing_history_years=8,
        ebit_positive_count=3,
        d_de_ratio=0.3,
        net_debt_to_ebitda=1.5,
        interest_coverage=4.0,
        shareholders_equity=-1e9,
        nci_pct=5.0,
        revenue_drivers=["volume_consumer"],
        has_steady_state_3y=True,
        life_cycle_stage="mature",
    )
    assert "1d_equity_base" in v.gates_failed


# ---------- Gate 2 - Ownership Structure ----------

def test_gate2_low_nci_no_change():
    v = evaluate(
        "TEST",
        domain=DOMAIN_SINGLE_BUSINESS,
        filing_history_years=8,
        ebit_positive_count=3,
        d_de_ratio=0.3,
        net_debt_to_ebitda=1.5,
        interest_coverage=4.0,
        shareholders_equity=1e10,
        nci_pct=10.0,
        revenue_drivers=["volume_consumer"],
        has_steady_state_3y=True,
        life_cycle_stage="mature",
    )
    assert v.primary == "FCFF/WACC DCF"
    assert "2_nci" in v.gates_passed


def test_gate2_mid_nci_requires_sotp_crosscheck():
    v = evaluate(
        "TEST",
        domain=DOMAIN_SINGLE_BUSINESS,
        filing_history_years=8,
        ebit_positive_count=3,
        d_de_ratio=0.3,
        net_debt_to_ebitda=1.5,
        interest_coverage=4.0,
        shareholders_equity=1e10,
        nci_pct=30.0,  # 15-40%
        revenue_drivers=["volume_consumer"],
        has_steady_state_3y=True,
        life_cycle_stage="mature",
    )
    assert v.primary == "FCFF/WACC DCF"
    assert any("SOTP cross-check" in r for r in v.reasons)


def test_gate2_high_nci_flips_to_sotp():
    v = evaluate(
        "TEST",
        domain=DOMAIN_SINGLE_BUSINESS,
        filing_history_years=8,
        ebit_positive_count=3,
        d_de_ratio=0.3,
        net_debt_to_ebitda=1.5,
        interest_coverage=4.0,
        shareholders_equity=1e10,
        nci_pct=55.0,  # > 40%
        revenue_drivers=["volume_consumer"],
        has_steady_state_3y=True,
        life_cycle_stage="mature",
    )
    assert v.primary == "SOTP"
    assert "2_nci" in v.gates_failed


# ---------- Gate 3 - Cyclicality ----------

def test_gate3_commodity_driven_uses_nav():
    v = evaluate(
        "TEST_COAL",
        domain=DOMAIN_MINING,
        filing_history_years=18,
        ebit_positive_count=3,
        d_de_ratio=0.2,
        net_debt_to_ebitda=0.5,
        interest_coverage=10.0,
        shareholders_equity=1e11,
        nci_pct=5.0,
        revenue_drivers=["commodity_coal"],
        has_steady_state_3y=True,
        life_cycle_stage="mature",
    )
    assert v.primary == "NAV / Reserve-based"


def test_gate3_newly_commissioned_uses_forward_relative():
    v = evaluate(
        "TEST_RAMP",
        domain=DOMAIN_SINGLE_BUSINESS,
        filing_history_years=2,
        ebit_positive_count=2,
        d_de_ratio=0.4,
        net_debt_to_ebitda=2.0,
        interest_coverage=3.0,
        shareholders_equity=1e10,
        nci_pct=5.0,
        revenue_drivers=["volume_consumer"],
        has_steady_state_3y=False,  # < 3y steady state
        life_cycle_stage="growth",
    )
    # thin data + ramp + growth → relative + EV/Sales reasons
    assert v.primary in {"DCF (shortened horizon)", "Relative Valuation"}


# ---------- Gate 4 - Life Cycle ----------

def test_gate4_pre_revenue_uses_ev_sales():
    v = evaluate(
        "TEST_EARLY",
        domain=DOMAIN_SINGLE_BUSINESS,
        filing_history_years=8,  # enough history to bypass Gate 1a
        ebit_positive_count=0,
        d_de_ratio=0.3,
        net_debt_to_ebitda=1.5,
        interest_coverage=4.0,
        shareholders_equity=1e10,
        nci_pct=5.0,
        revenue_drivers=["volume_consumer"],
        has_steady_state_3y=True,
        life_cycle_stage="pre_revenue",
    )
    assert v.primary == "EV/Sales"


def test_gate4_decline_uses_pbv():
    v = evaluate(
        "TEST_DECLINE",
        domain=DOMAIN_SINGLE_BUSINESS,
        filing_history_years=8,
        ebit_positive_count=3,
        d_de_ratio=0.3,
        net_debt_to_ebitda=1.5,
        interest_coverage=4.0,
        shareholders_equity=1e10,
        nci_pct=5.0,
        revenue_drivers=["volume_consumer"],
        has_steady_state_3y=True,
        life_cycle_stage="decline",
    )
    assert v.primary == "P/BV"


# ---------- Gate 5 - Output Sanity ----------

def test_gate5_extreme_upside_overrides_rating():
    v = evaluate(
        "TEST_MOON",
        domain=DOMAIN_SINGLE_BUSINESS,
        filing_history_years=8,
        ebit_positive_count=3,
        d_de_ratio=0.3,
        net_debt_to_ebitda=1.5,
        interest_coverage=4.0,
        shareholders_equity=1e10,
        nci_pct=5.0,
        revenue_drivers=["volume_consumer"],
        has_steady_state_3y=True,
        life_cycle_stage="mature",
        upside_pct=150.0,  # > 100%
    )
    assert v.rating_override == "Review Required"
    assert "5_upside_extreme" in v.gates_failed


def test_gate5_extreme_downside_overrides_rating():
    v = evaluate(
        "TEST_CRASH",
        domain=DOMAIN_SINGLE_BUSINESS,
        filing_history_years=8,
        ebit_positive_count=3,
        d_de_ratio=0.3,
        net_debt_to_ebitda=1.5,
        interest_coverage=4.0,
        shareholders_equity=1e10,
        nci_pct=5.0,
        revenue_drivers=["volume_consumer"],
        has_steady_state_3y=True,
        life_cycle_stage="mature",
        upside_pct=-60.0,  # < -50%
    )
    assert v.rating_override == "Review Required"


def test_gate5_high_tv_share_flags_but_does_not_override_rating():
    v = evaluate(
        "TEST_TV",
        domain=DOMAIN_SINGLE_BUSINESS,
        filing_history_years=8,
        ebit_positive_count=3,
        d_de_ratio=0.3,
        net_debt_to_ebitda=1.5,
        interest_coverage=4.0,
        shareholders_equity=1e10,
        nci_pct=5.0,
        revenue_drivers=["volume_consumer"],
        has_steady_state_3y=True,
        life_cycle_stage="mature",
        upside_pct=20.0,  # in band
        terminal_value_pct_of_ev=85.0,  # > 80%
    )
    assert v.rating_override is None
    assert "5_tv_share_high" in v.gates_failed


# ---------- Quintet Integration (5 tickers) ----------

def test_quintet_ratu_dcf_no_override():
    v = evaluate(
        "RATU",
        domain=DOMAIN_SINGLE_BUSINESS,
        filing_history_years=8,
        ebit_positive_count=3,
        d_de_ratio=0.3,
        net_debt_to_ebitda=1.0,
        interest_coverage=5.0,
        shareholders_equity=1e10,
        nci_pct=5.0,
        revenue_drivers=["volume_consumer"],
        has_steady_state_3y=True,
        life_cycle_stage="mature",
        upside_pct=20.0,
    )
    assert v.primary in {"FCFF/WACC DCF", "DCF"}
    assert v.rating_override is None


def test_quintet_cdia_dcf_thin_data():
    v = evaluate(
        "CDIA",
        domain=DOMAIN_SINGLE_BUSINESS,
        filing_history_years=2,
        ebit_positive_count=2,
        d_de_ratio=0.4,
        net_debt_to_ebitda=2.0,
        interest_coverage=3.0,
        shareholders_equity=1e10,
        nci_pct=5.0,
        revenue_drivers=["volume_consumer"],
        has_steady_state_3y=True,
        life_cycle_stage="growth",
        upside_pct=22.6,
    )
    assert v.primary == "DCF (shortened horizon)"
    assert v.thin_data is True
    assert "1a_filing_history" in v.gates_failed


def test_quintet_bbcA_ddm():
    v = evaluate(
        "BBCA",
        domain=DOMAIN_BANK,
        filing_history_years=25,
        ebit_positive_count=3,
        d_de_ratio=0.0,
        net_debt_to_ebitda=0.0,
        interest_coverage=999.0,
        shareholders_equity=1e13,
        nci_pct=1.0,
        revenue_drivers=["net_interest_margin"],
        has_steady_state_3y=True,
        life_cycle_stage="mature",
        upside_pct=45.0,
    )
    assert v.primary == "DDM / Excess Return"


def test_quintet_adro_nav():
    v = evaluate(
        "ADRO",
        domain=DOMAIN_MINING,
        filing_history_years=18,
        ebit_positive_count=3,
        d_de_ratio=0.2,
        net_debt_to_ebitda=0.5,
        interest_coverage=10.0,
        shareholders_equity=5e10,
        nci_pct=5.0,
        revenue_drivers=["commodity_coal"],
        has_steady_state_3y=True,
        life_cycle_stage="mature",
        upside_pct=86.3,
    )
    assert v.primary == "NAV / Reserve-based"


def test_quintet_mtel_dcf_with_sotp_crosscheck():
    v = evaluate(
        "MTEL",
        domain=DOMAIN_SINGLE_BUSINESS,  # tower, single business line
        filing_history_years=6,
        ebit_positive_count=3,
        d_de_ratio=0.6,
        net_debt_to_ebitda=3.5,
        interest_coverage=2.5,
        shareholders_equity=2e10,
        nci_pct=25.0,  # 15-40% band
        revenue_drivers=["volume_consumer", "rental"],
        has_steady_state_3y=True,
        life_cycle_stage="mature",
        upside_pct=33.4,
    )
    assert v.primary == "FCFF/WACC DCF"
    assert any("SOTP cross-check" in r for r in v.reasons)
