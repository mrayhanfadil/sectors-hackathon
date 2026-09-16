"""N-GATE tests - upfront method-order pre-filter + Gate 5 ACES regression.

Matrix covers: healthy payer, zero-payout (DDM skipped), negative-EBITDA
(EV/EBITDA skipped, EV/Sales gated), bank (DDM anchor, no DCF), mining
(NAV + DCF comparison), NCI>40% (SOTP), NCI 15-40% (mandatory SOTP
cross-check), thin-data (shortened DCF), critic/writer loud-fail, and the
Gate 5 regression (synthetic 2079%-upside DCF -> Review Required; 69.42%
upside stays BUY-eligible). Pure gate math - no fixture dependency.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.valuation.gates import DOMAIN_BANK, DOMAIN_MINING, DOMAIN_SINGLE_BUSINESS, evaluate  # noqa: E402
from agents.valuation.method_gate import (  # noqa: E402
    DCF,
    DDM,
    NAV,
    REL_EBITDA,
    REL_SALES,
    SOTP,
    MethodGate,
    apply_output_sanity,
    audit_valuation_fvs,
    blended_from_gated,
    check_fv_gated,
    run_method_gate,
)


def _base(**over) -> dict:
    kw = dict(
        domain=DOMAIN_SINGLE_BUSINESS,
        filing_history_years=8,
        ebit_positive_count=3,
        d_de_ratio=0.30,
        net_debt_to_ebitda=1.5,
        interest_coverage=4.0,
        shareholders_equity=1e10,
        nci_pct=5.0,
        revenue_drivers=["volume_consumer"],
        has_steady_state_3y=True,
        life_cycle_stage="mature",
        payout_ratio=0.40,
        dps_history_years=5,
        ebitda=1e9,
        revenue=5e9,
        net_income=1e9,
        earnings_stable=True,
        has_peers=True,
        fcf_available=True,
    )
    kw.update(over)
    return kw


# ---------- Gate matrix ----------

def test_healthy_payer_anchors_dcf_with_ddm_and_relative():
    g = run_method_gate("RATU", **_base())
    assert g.ordered[0] == DCF
    assert DDM in g.ordered
    assert REL_EBITDA in g.ordered
    assert not g.thin_data


def test_zero_payout_skips_ddm_with_reason():
    g = run_method_gate("NOPAY", **_base(payout_ratio=0.0, dps_history_years=0))
    assert DDM not in g.ordered
    assert DDM in g.skipped and "payout" in g.skipped[DDM]
    assert g.ordered[0] == DCF  # anchor unaffected


def test_negative_ebitda_skips_ev_ebitda_gates_ev_sales():
    g = run_method_gate(
        "LOSSMAKER",
        **_base(ebit_positive_count=0, ebitda=-1e9, net_income=-5e8, earnings_stable=False),
    )
    assert REL_EBITDA in g.skipped
    assert REL_SALES in g.ordered  # loss-makers -> sales multiples (PDF Gate 1b)


def test_bank_anchors_ddm_and_excludes_dcf():
    g = run_method_gate(
        "BBCA",
        **_base(domain=DOMAIN_BANK, revenue_drivers=["net_interest_margin"],
                payout_ratio=0.5, dps_history_years=10),
    )
    assert g.anchor == DDM and g.ordered[0] == DDM
    assert DCF in g.skipped and "EV" in g.skipped[DCF]


def test_mining_nav_primary_with_dcf_comparison():
    g = run_method_gate(
        "ADRO",
        **_base(domain=DOMAIN_MINING, revenue_drivers=["commodity_coal"],
                payout_ratio=0.3, dps_history_years=4),
    )
    assert NAV in g.ordered and DCF in g.ordered


def test_nci_over_40_routes_sotp():
    g = run_method_gate("HOLDCO", **_base(nci_pct=55.0))
    assert SOTP in g.ordered


def test_nci_band_attaches_mandatory_sotp_crosscheck():
    g = run_method_gate("MTEL", **_base(nci_pct=25.0))
    assert g.ordered[0] == DCF
    assert SOTP in g.ordered
    assert any("NCI" in r and "SOTP" in r for r in g.reasons)


def test_thin_data_shortened_dcf_flag():
    g = run_method_gate("CDIA", **_base(filing_history_years=2))
    assert g.thin_data is True
    assert DCF in g.ordered


def test_garbage_inputs_raise_loud():
    with pytest.raises(ValueError):
        run_method_gate("X", **_base(payout_ratio=None))
    with pytest.raises(ValueError):
        run_method_gate("X", **_base(ebitda=float("nan")))


# ---------- Critic / writer enforcement (loud-fail) ----------

def test_critic_rejects_fv_from_non_gated_method():
    g = run_method_gate("NOPAY", **_base(payout_ratio=0.0, dps_history_years=0))
    assert check_fv_gated("DCF", g) == DCF
    with pytest.raises(ValueError, match="non-gated method DDM"):
        check_fv_gated("DDM", g)
    with pytest.raises(ValueError, match="non-gated method DDM"):
        check_fv_gated("DDM / Excess Return", g)  # verdict label also rejected
    assert len(audit_valuation_fvs({"DCF": 600.0, DDM: 100.0}, g)) == 1
    assert audit_valuation_fvs({"DCF": 600.0}, g) == []


def test_writer_blend_honors_only_gated_list():
    g = run_method_gate("RATU", **_base())
    out = blended_from_gated({"DCF": 600.0, REL_EBITDA: 700.0},
                             {"DCF": 0.6, REL_EBITDA: 0.4}, g)
    assert out["blended_value"] == pytest.approx(640.0)
    with pytest.raises(ValueError, match="non-gated"):
        blended_from_gated({"DCF": 600.0, NAV: 900.0}, {"DCF": 0.6, NAV: 0.4}, g)
    with pytest.raises(ValueError, match="sum"):
        blended_from_gated({"DCF": 600.0}, {"DCF": 0.5}, g)
    with pytest.raises(ValueError, match="keys"):
        blended_from_gated({"DCF": 600.0}, {"DCF": 0.6, REL_EBITDA: 0.4}, g)


# ---------- Gate 5 ACES regression ----------

def _aces_params(upside: float) -> dict:
    return dict(
        ticker="ACES",
        domain=DOMAIN_SINGLE_BUSINESS,
        filing_history_years=10,
        ebit_positive_count=3,
        d_de_ratio=0.05,
        net_debt_to_ebitda=-0.5,
        interest_coverage=50.0,
        shareholders_equity=5e12,
        nci_pct=0.0,
        revenue_drivers=["volume_retail"],
        has_steady_state_3y=True,
        life_cycle_stage="mature",
        upside_pct=upside,
    )


def test_gate5_fabricated_2079_upside_forces_review_required():
    v = evaluate(**_aces_params(2079.0))
    assert v.rating_override == "Review Required"
    assert "5_upside_extreme" in v.gates_failed


def test_gate5_real_aces_69_upside_stays_buy_eligible():
    # Gate 5 calibration: upside_pct 69.42 stays BUY-eligible (pure gate math,
    # no fixture dependency since the Sep 2026 Sectors-only purge).
    v = evaluate(**_aces_params(69.42))
    assert v.rating_override is None


def test_gate5_tv_and_exit_multiple_flag_without_override():
    v = evaluate(**_aces_params(20.0), terminal_value_pct_of_ev=85.0)
    assert v.rating_override is None
    assert "5_tv_share_high" in v.gates_failed
    v2 = evaluate(**_aces_params(20.0), implied_exit_ev_ebitda=25.0,
                  peer_exit_low=8.0, peer_exit_high=12.0)
    assert v2.rating_override is None
    assert "5_exit_multiple_out_of_range" in v2.gates_failed
    v3 = evaluate(**_aces_params(20.0), implied_exit_ev_ebitda=10.0,
                  peer_exit_low=8.0, peer_exit_high=12.0)
    assert "5_exit_multiple_in_range" in v3.gates_passed


def test_apply_output_sanity_mirrors_gate5():
    g = run_method_gate("RATU", **_base())
    assert apply_output_sanity(g, upside_pct=2079.0)["rating_override"] == "Review Required"
    assert apply_output_sanity(g, upside_pct=69.42)["rating_override"] is None
    flagged = apply_output_sanity(g, upside_pct=20.0, terminal_value_pct_of_ev=85.0,
                                  implied_exit_ev_ebitda=25.0,
                                  peer_exit_low=8.0, peer_exit_high=12.0)
    assert flagged["rating_override"] is None and len(flagged["flags"]) == 2


def test_method_gate_serializes():
    g = run_method_gate("RATU", **_base())
    d = g.to_dict()
    assert isinstance(g, MethodGate)
    assert d["ordered"][0] == DCF and isinstance(d["skipped"], dict)
