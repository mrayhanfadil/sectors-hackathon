"""Valuation Method Selection Framework — 6 gates (0-5) per PDF.

User decision (2026-09-04): Gate 1 fallback = shortened DCF + thin-data disclosure
(banker doesn't apply for the thin-data case because pure Relative Valuation has no
defensible fair value). Gate 5 auto-overrides rating to "Review Required" when
upside > 100% or downside > 50% vs market price.

Returns GateVerdict(primary, secondary, gates_passed, gates_failed, reasons,
rating_override). Pure stdlib — deterministic, no LLM calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal, Optional
from server.report import numfmt as _nf

Method = Literal[
    "FCFF/WACC DCF",
    "DCF (shortened horizon)",
    "DDM / Excess Return",
    "NAV / Reserve-based",
    "SOTP",
    "EV/Sales",
    "Relative Valuation",
    "P/BV",
]

# Domain categorization (Gate 0 input)
DOMAIN_BANK = "bank"
DOMAIN_INSURANCE = "insurance"
DOMAIN_MULTIFINANCE = "multifinance"
DOMAIN_SECURITIES = "securities"
DOMAIN_REIT = "reit"
DOMAIN_MINING = "mining"
DOMAIN_OIL_GAS = "oil_gas"
DOMAIN_PLANTATION = "plantation"
DOMAIN_HOLDING_DISSIMILAR = "holding_dissimilar"
DOMAIN_SINGLE_BUSINESS = "single_business"


@dataclass
class GateVerdict:
    primary: str
    secondary: Optional[str]
    gates_passed: list[str]
    gates_failed: list[str]
    reasons: list[str]
    rating_override: Optional[str] = None  # None | "Review Required"
    thin_data: bool = False  # Gate 1a failure flag — shows ⚠ banner on cover

    def to_dict(self) -> dict:
        return asdict(self)


def _gate0_business_model(
    domain: str,
) -> tuple[Method | None, str | None]:
    """Returns (primary_method_if_gate0_decides, reason).

    Bank/insurance/multifinance/securities → DDM
    REIT → NAV
    Mining/oil&gas/plantation → NAV reserve-based
    Holding with dissimilar lines → SOTP
    Single business → None (passes to Gate 1)
    """
    financial = {DOMAIN_BANK, DOMAIN_INSURANCE, DOMAIN_MULTIFINANCE, DOMAIN_SECURITIES}
    finite_reserves = {DOMAIN_MINING, DOMAIN_OIL_GAS, DOMAIN_PLANTATION}

    if domain in financial:
        return ("DDM / Excess Return", "Financial institution — debt is raw material, EV undefined, FCF convention inapplicable")
    if domain == DOMAIN_REIT:
        return ("NAV / Reserve-based", "REIT — value is asset-driven, rental income is a derivative of asset value")
    if domain in finite_reserves:
        return ("NAV / Reserve-based", "Finite reserves — perpetual-growth DCF structurally wrong, reserve-based NAV is correct")
    if domain == DOMAIN_HOLDING_DISSIMILAR:
        return ("SOTP", "Holding with dissimilar subsidiaries — one WACC hides value, each line needs its own method")
    # single business → DCF candidate, proceed to Gate 1
    return (None, None)


def _gate1_data_eligibility(
    filing_history_years: int,
    ebit_positive_count: int,
    d_de_ratio: float,
    net_debt_to_ebitda: float,
    interest_coverage: float,
    shareholders_equity: float,
) -> tuple[list[str], list[str], list[str], bool, Method | None]:
    """Returns (passed, failed, reasons, thin_data_flag, primary_override).

    User decision: filing history < 4y → DCF (shortened horizon) + thin_data=True,
    NOT pure Relative Valuation. Other failures: relative valuation / EV multiples.
    """
    passed: list[str] = []
    failed: list[str] = []
    reasons: list[str] = []
    thin_data = False
    primary_override: Method | None = None

    # 1a — filing history
    if filing_history_years >= 4:
        passed.append("1a_filing_history")
    else:
        failed.append("1a_filing_history")
        thin_data = True
        primary_override = "DCF (shortened horizon)"
        reasons.append(
            f"1a filing history {filing_history_years}y < 4y → shortened-horizon DCF + ⚠ Thin Data disclosure"
        )

    # 1b — operating profitability
    if ebit_positive_count >= 2:
        passed.append("1b_profitability")
    else:
        failed.append("1b_profitability")
        reasons.append(
            f"1b EBIT positive in only {ebit_positive_count}/3y → Relative Valuation only (EV/Sales / Price/Sales)"
        )
        # If profitability fails too, escalate fallback
        if primary_override is None:
            primary_override = "Relative Valuation"

    # 1c — capital structure
    if d_de_ratio <= 0.80 and net_debt_to_ebitda <= 6.0 and interest_coverage >= 1.0:
        passed.append("1c_capital_structure")
    else:
        failed.append("1c_capital_structure")
        reasons.append(
            f"1c capital structure breach (D/(D+E)={_nf.dec(d_de_ratio, digits=2)}, ND/EBITDA={_nf.dec(net_debt_to_ebitda, digits=2)}×, IC={_nf.dec(interest_coverage, digits=2)}×) → DCF proceeds with mandatory Relative cross-check"
        )

    # 1d — equity base
    if shareholders_equity > 0:
        passed.append("1d_equity_base")
    else:
        failed.append("1d_equity_base")
        reasons.append("1d negative shareholders' equity → EV-based multiples only (no P/E, no P/BV)")
        if primary_override is None:
            primary_override = "Relative Valuation"

    return passed, failed, reasons, thin_data, primary_override


def _gate2_ownership_structure(nci_pct: float) -> tuple[list[str], list[str], list[str], Method | None]:
    """Returns (passed, failed, reasons, primary_override)."""
    if nci_pct <= 15.0:
        return (
            ["2_nci"],
            [],
            [],
            None,
        )
    if nci_pct <= 40.0:
        return (
            ["2_nci"],
            [],
            [f"2 NCI {_nf.dec(nci_pct, digits=1)}% in 15–40% band → DCF + mandatory SOTP cross-check"],
            None,  # keep DCF as primary, but SOTP cross-check is logged in reasons
        )
    return (
        [],
        ["2_nci"],
        [f"2 NCI {_nf.dec(nci_pct, digits=1)}% > 40% → SOTP becomes primary, consolidated DCF is rough reference only"],
        "SOTP",
    )


def _gate3_cyclicality(
    revenue_drivers: list[str],
    has_steady_state_3y: bool,
) -> tuple[list[str], list[str], list[str], Method | None]:
    """Returns (passed, failed, reasons, primary_override).

    revenue_drivers is a list of tags; recognized tags:
      'commodity_coal', 'commodity_nickel', 'commodity_cpo', 'commodity_oil',
      'volume_consumer', 'volume_manufacturing', 'volume_retail',
      'net_interest_margin', 'premium', 'rental', 'other'.

    newly commissioned = has_steady_state_3y == False.
    """
    passed: list[str] = ["3_cyclicality"]  # always "passes" structurally
    failed: list[str] = []
    reasons: list[str] = []
    primary_override: Method | None = None

    commodity_tags = {
        "commodity_coal",
        "commodity_nickel",
        "commodity_cpo",
        "commodity_oil",
    }
    if any(tag in commodity_tags for tag in revenue_drivers):
        primary_override = "NAV / Reserve-based"
        reasons.append(
            "3 commodity-driven revenue → NAV/reserve-based primary + DCF as long-run price deck comparison"
        )
        return passed, failed, reasons, primary_override

    if not has_steady_state_3y:
        primary_override = "Relative Valuation"
        reasons.append(
            "3 newly commissioned / ramping asset (<3y steady-state) → forward Relative Valuation primary (EV/EBITDA at target capacity against mature peers)"
        )
        return passed, failed, reasons, primary_override

    return passed, failed, reasons, primary_override


def _gate4_life_cycle(stage: str) -> tuple[list[str], list[str], list[str], Method | None]:
    """Returns (passed, failed, reasons, primary_override).

    stage ∈ {'pre_revenue', 'high_growth_pre_profit', 'mature', 'decline'}
    """
    passed: list[str] = ["4_life_cycle"]
    failed: list[str] = []
    reasons: list[str] = []
    primary_override: Method | None = None

    if stage == "pre_revenue":
        primary_override = "EV/Sales"
        reasons.append("4 pre-revenue / early growth → EV/Sales primary, DCF with caution")
    elif stage == "high_growth_pre_profit":
        primary_override = "EV/Sales"
        reasons.append(
            "4 high-growth pre-profit → EV/Sales primary + DCF with explicit margin fade to long-run target"
        )
    elif stage == "decline":
        primary_override = "P/BV"
        reasons.append("4 decline / turnaround → P/BV (or NAV if asset base is substantial), DCF too speculative")
    # 'mature' → no override, keep DCF
    return passed, failed, reasons, primary_override


def _gate5_output_sanity(
    upside_pct: float | None,
    terminal_value_pct_of_ev: float | None,
    implied_exit_ev_ebitda: float | None = None,
    peer_exit_low: float | None = None,
    peer_exit_high: float | None = None,
) -> tuple[list[str], list[str], list[str], Optional[str]]:
    """Returns (passed, failed, reasons, rating_override).

    User decision: upside > 100% or downside < -50% → auto-override rating to "Review Required".
    TV > 80% of EV → flag but do NOT override rating.
    Implied exit EV/EBITDA outside the peer/historical range → flag for EV/EBITDA
    cross-check (PDF Gate 5 row 3: WACC/g out of sync with market pricing), no override.
    """
    passed: list[str] = []
    failed: list[str] = []
    reasons: list[str] = []
    rating_override: Optional[str] = None

    if upside_pct is not None:
        if upside_pct > 100.0:
            failed.append("5_upside_extreme")
            reasons.append(
                f"5 upside {_nf.dec(upside_pct, digits=1, signed=True)}% > 100% → rating auto-override to Review Required"
            )
            rating_override = "Review Required"
        elif upside_pct < -50.0:
            failed.append("5_downside_extreme")
            reasons.append(
                f"5 downside {_nf.dec(upside_pct, digits=1, signed=True)}% < -50% → rating auto-override to Review Required"
            )
            rating_override = "Review Required"
        else:
            passed.append("5_upside_band")

    if terminal_value_pct_of_ev is not None and terminal_value_pct_of_ev > 80.0:
        failed.append("5_tv_share_high")
        reasons.append(
            f"5 terminal value {_nf.dec(terminal_value_pct_of_ev, digits=1)}% > 80% of EV → flagged for cross-check (implied exit-multiple or Relative Valuation)"
        )
        # Note: per user decision, do NOT auto-override rating here, just flag
    else:
        if "5_upside_band" in passed or not failed:
            passed.append("5_tv_share")

    if (
        implied_exit_ev_ebitda is not None
        and peer_exit_low is not None
        and peer_exit_high is not None
    ):
        if not (peer_exit_low <= implied_exit_ev_ebitda <= peer_exit_high):
            failed.append("5_exit_multiple_out_of_range")
            reasons.append(
                f"5 implied exit EV/EBITDA {_nf.dec(implied_exit_ev_ebitda, digits=1)}× outside peer range "
                f"{_nf.dec(peer_exit_low, digits=1)}-{_nf.dec(peer_exit_high, digits=1)}× → WACC/g out of sync with market "
                "pricing, cross-check vs EV/EBITDA relative valuation"
            )
        else:
            passed.append("5_exit_multiple_in_range")

    return passed, failed, reasons, rating_override


def evaluate(
    ticker: str,
    *,
    domain: str,
    filing_history_years: int,
    ebit_positive_count: int,
    d_de_ratio: float,
    net_debt_to_ebitda: float,
    interest_coverage: float,
    shareholders_equity: float,
    nci_pct: float,
    revenue_drivers: list[str],
    has_steady_state_3y: bool,
    life_cycle_stage: str,
    upside_pct: float | None = None,
    terminal_value_pct_of_ev: float | None = None,
    implied_exit_ev_ebitda: float | None = None,
    peer_exit_low: float | None = None,
    peer_exit_high: float | None = None,
) -> GateVerdict:
    """Run gates 0–5 in order and return a single GateVerdict.

    Parameters mirror the PDF's checklist + user-decision deltas:
    - Gate 1 fallback (thin data) = DCF (shortened horizon) + thin_data=True (NOT pure Relative)
    - Gate 5 (extreme upside/downside) auto-overrides rating to "Review Required"
    """
    all_passed: list[str] = []
    all_failed: list[str] = []
    all_reasons: list[str] = []

    primary: Method = "FCFF/WACC DCF"  # default
    secondary: Method | None = None
    thin_data = False
    rating_override: Optional[str] = None

    # Gate 0
    g0_primary, g0_reason = _gate0_business_model(domain)
    if g0_primary is not None:
        all_passed.append("0_business_model")
        primary = g0_primary
        if g0_reason:
            all_reasons.append(g0_reason)
        # Banks skip most downstream gates (financials have no D/E ratio, no FCF)
        if domain in {DOMAIN_BANK, DOMAIN_INSURANCE, DOMAIN_MULTIFINANCE, DOMAIN_SECURITIES}:
            # Apply Gate 5 only — financial valuation doesn't fit Gates 1-4
            g5_passed, g5_failed, g5_reasons, g5_override = _gate5_output_sanity(
                upside_pct, terminal_value_pct_of_ev,
                implied_exit_ev_ebitda, peer_exit_low, peer_exit_high,
            )
            all_passed.extend(g5_passed)
            all_failed.extend(g5_failed)
            all_reasons.extend(g5_reasons)
            if g5_override:
                rating_override = g5_override
            return GateVerdict(
                primary=primary,
                secondary=None,
                gates_passed=all_passed,
                gates_failed=all_failed,
                reasons=all_reasons,
                rating_override=rating_override,
                thin_data=False,
            )
    else:
        all_passed.append("0_business_model")

    # Gate 1
    g1_passed, g1_failed, g1_reasons, g1_thin, g1_override = _gate1_data_eligibility(
        filing_history_years,
        ebit_positive_count,
        d_de_ratio,
        net_debt_to_ebitda,
        interest_coverage,
        shareholders_equity,
    )
    all_passed.extend(g1_passed)
    all_failed.extend(g1_failed)
    all_reasons.extend(g1_reasons)
    thin_data = thin_data or g1_thin
    if g1_override is not None:
        primary = g1_override

    # Gate 2
    g2_passed, g2_failed, g2_reasons, g2_override = _gate2_ownership_structure(nci_pct)
    all_passed.extend(g2_passed)
    all_failed.extend(g2_failed)
    all_reasons.extend(g2_reasons)
    if g2_override is not None:
        primary = g2_override

    # Gate 3
    g3_passed, g3_failed, g3_reasons, g3_override = _gate3_cyclicality(
        revenue_drivers, has_steady_state_3y
    )
    all_passed.extend(g3_passed)
    all_failed.extend(g3_failed)
    all_reasons.extend(g3_reasons)
    if g3_override is not None:
        primary = g3_override

    # Gate 4
    g4_passed, g4_failed, g4_reasons, g4_override = _gate4_life_cycle(life_cycle_stage)
    all_passed.extend(g4_passed)
    all_failed.extend(g4_failed)
    all_reasons.extend(g4_reasons)
    if g4_override is not None:
        primary = g4_override

    # Determine secondary method (cross-check) based on primary
    secondary = _secondary_for(primary, all_failed)

    # Gate 5 — applied after DCF is computed (output sanity)
    # Only apply if DCF is the primary; for NAV/SOTP/DDM it's less meaningful but
    # still applies for the upside band logic.
    g5_passed, g5_failed, g5_reasons, g5_override = _gate5_output_sanity(
        upside_pct, terminal_value_pct_of_ev,
        implied_exit_ev_ebitda, peer_exit_low, peer_exit_high,
    )
    all_passed.extend(g5_passed)
    all_failed.extend(g5_failed)
    all_reasons.extend(g5_reasons)
    if g5_override:
        rating_override = g5_override

    return GateVerdict(
        primary=primary,
        secondary=secondary,
        gates_passed=all_passed,
        gates_failed=all_failed,
        reasons=all_reasons,
        rating_override=rating_override,
        thin_data=thin_data,
    )


def _secondary_for(primary: Method, gates_failed: list[str]) -> Method | None:
    """Pick a sensible secondary / cross-check method based on primary + failed gates.

    Note: the bank/insurance/multifinance/securities branch in evaluate() short-circuits
    after Gate 0 with secondary=None (since downstream gates 1-4 don't apply to financials).
    The "DDM / Excess Return" mapping below is intentionally unreachable from that branch
    but kept for callers that invoke _secondary_for() directly (e.g. external tooling).
    """
    if primary == "FCFF/WACC DCF":
        if "1c_capital_structure" in gates_failed:
            return "Relative Valuation"
        return "Relative Valuation"  # default DCF cross-check
    if primary == "DCF (shortened horizon)":
        return "Relative Valuation"
    if primary == "NAV / Reserve-based":
        return "FCFF/WACC DCF"  # NAV compared to DCF with explicit price deck
    if primary == "SOTP":
        return "FCFF/WACC DCF"
    if primary == "DDM / Excess Return":
        return "Relative Valuation"
    if primary == "EV/Sales":
        return "FCFF/WACC DCF"
    if primary == "Relative Valuation":
        return "FCFF/WACC DCF"
    if primary == "P/BV":
        return "NAV / Reserve-based"
    return None
