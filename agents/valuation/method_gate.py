"""Upfront valuation-method pre-filter gate (N-GATE) - single entry path.

Runs BEFORE the full pipeline: intake/modeler calls run_method_gate() first,
emits an ordered method list with skip reasons, and every downstream consumer
(writer/blended, critic) honors ONLY the gated list. Loud-fail throughout:
non-gated fair values raise instead of being silently averaged in.

Source: house valuation method-selection framework (docs/valuation-framework.md)
(references/framework-valuation.pdf, 81.7K; decision flow pp.337-401,
relative-multiple applicability table pp.407-428). The deterministic 6-gate
verdict underneath lives in agents/valuation/gates.py; this module maps that
verdict + dividend/earnings eligibility onto executable engine keys.

METHOD-ORDER TABLE (PDF decision flow, top to bottom):
  1. Financial institution?            -> DDM / Excess Return (anchor DDM; NO DCF - EV undefined, Gate 0)
  2. REIT / property vehicle?          -> NAV (anchor NAV; DCF only as comparison if FCF exists)
  3. Holding company with NCI > 40%?   -> SOTP (anchor SOTP; DCF rough reference only)
  4. Mining/commodity price-driven?    -> NAV/reserve-based primary, DCF as comparison
  5. History < 4y / commissioning?     -> Forward Relative Valuation (user delta: shortened-horizon DCF + Thin Data)
  6. Chronic operating losses?         -> EV/Sales or Price/Sales
  7. Negative equity?                  -> EV-based multiples only (not P/E, not P/BV)
  8. Extreme leverage?                 -> DCF + mandatory Relative cross-check
  9. Passes all checks                 -> FCFF/WACC DCF primary (anchor DCF, always runs)
  10. Post-computation (Gate 5)        -> upside>100% or downside>50%: Review Required;
                                         TV>80% EV: flagged; exit multiple out of range: flagged.
Relative Valuation is never fully optional: a valid DCF is still paired with
a Relative second check (PDF step 10 + p.403).

Engine keys emitted here: DCF, DDM, NAV, SOTP, REL_PE, REL_PBV, REL_EBITDA, REL_SALES.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .gates import (
    DOMAIN_BANK,
    DOMAIN_HOLDING_DISSIMILAR,
    DOMAIN_INSURANCE,
    DOMAIN_MINING,
    DOMAIN_MULTIFINANCE,
    DOMAIN_OIL_GAS,
    DOMAIN_PLANTATION,
    DOMAIN_REIT,
    DOMAIN_SECURITIES,
    GateVerdict,
    evaluate,
)
from server.report import numfmt as _nf

# Engine method keys (map 1:1 onto calc_* tools).
DCF = "DCF"
DDM = "DDM"
NAV = "NAV"
SOTP = "SOTP"
REL_PE = "REL_PE"
REL_PBV = "REL_PBV"
REL_EBITDA = "REL_EBITDA"
REL_SALES = "REL_SALES"

ALL_METHODS = (DCF, DDM, NAV, SOTP, REL_PE, REL_PBV, REL_EBITDA, REL_SALES)

_FINANCIAL_DOMAINS = {DOMAIN_BANK, DOMAIN_INSURANCE, DOMAIN_MULTIFINANCE, DOMAIN_SECURITIES}
_FINITE_RESERVE_DOMAINS = {DOMAIN_MINING, DOMAIN_OIL_GAS, DOMAIN_PLANTATION}

# Verdict-label -> engine-key mapping (gates.evaluate() speaks PDF labels).
_VERDICT_TO_ENGINE = {
    "FCFF/WACC DCF": DCF,
    "DCF (shortened horizon)": DCF,
    "DDM / Excess Return": DDM,
    "NAV / Reserve-based": NAV,
    "SOTP": SOTP,
    "EV/Sales": REL_SALES,
    "Relative Valuation": None,  # resolved via applicability table, not 1:1
    "P/BV": REL_PBV,
}

# Relative-multiple applicability table (PDF pp.407-428).
# Each entry: (USE WHEN, AVOID WHEN) - enforced by relative_extra().
RELATIVE_APPLICABILITY: dict[str, dict[str, str]] = {
    REL_PE: {
        "use_when": "earnings are stable and there is a clear peer group",
        "avoid_when": "earnings are negative or highly volatile",
    },
    REL_PBV: {
        "use_when": "financials / asset-heavy businesses, or distressed/turnaround "
        "where earnings are unreliable but the asset base still holds value",
        "avoid_when": "shareholders' equity is negative (P/BV undefined)",
    },
    REL_EBITDA: {
        "use_when": "comparing companies with different capital structures; "
        "standard cross-check for a DCF's implied exit multiple",
        "avoid_when": "EBITDA is zero or negative",
    },
    REL_SALES: {
        "use_when": "pre-earnings / early-stage, margins vary too widely for EBITDA "
        "multiples, or earnings are distorted by one-offs",
        "avoid_when": "no revenue base to scale from",
    },
}


@dataclass
class MethodGate:
    """Ordered, gated method list - the single contract downstream honors."""

    ticker: str
    ordered: list[str]  # engine keys, anchor first
    skipped: dict[str, str]  # engine key -> skip reason
    primary: str
    secondary: Optional[str]
    anchor: str
    thin_data: bool = False
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "ordered": list(self.ordered),
            "skipped": dict(self.skipped),
            "primary": self.primary,
            "secondary": self.secondary,
            "anchor": self.anchor,
            "thin_data": self.thin_data,
            "reasons": list(self.reasons),
        }


def _num(name: str, v: Any) -> float:
    """Loud numeric coercion - None/NaN/non-numeric fundamentals raise."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"method-gate input '{name}' must be numeric, got {v!r}")
    f = float(v)
    if f != f:  # NaN
        raise ValueError(f"method-gate input '{name}' must not be NaN")
    return f


def _resolve_relative(ebitda: float, net_income: float, earnings_stable: bool,
                      has_peers: bool, revenue: float) -> str:
    """Pick the applicable relative leg per the PDF applicability table."""
    if ebitda > 0:
        return REL_EBITDA
    if net_income > 0 and earnings_stable and has_peers:
        return REL_PE
    return REL_SALES  # loss-makers / no EBITDA base -> sales multiples


def run_method_gate(
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
    revenue_drivers: list,
    has_steady_state_3y: bool,
    life_cycle_stage: str,
    # Dividend / earnings eligibility (task-mandated pre-filter inputs):
    payout_ratio: float = 0.0,
    dps_history_years: int = 0,
    ebitda: float = 0.0,
    revenue: float = 0.0,
    net_income: float = 0.0,
    earnings_stable: bool = False,
    has_peers: bool = False,
    roe: Optional[float] = None,
    bvps: Optional[float] = None,
    segments_count: int = 1,
    fcf_available: bool = True,
) -> MethodGate:
    """Single entry path: 6-gate verdict -> ordered engine-key list + skip reasons.

    Must be called BEFORE any valuation math (intake/modeler pre-filter).
    DCF runs as anchor on every path where firm FCF is defined; the sole
    exception is financials (bank/insurance/multifinance/securities) where EV
    is undefined per PDF Gate 0 - there DDM is the anchor and DCF is skipped
    with an explicit reason (never silently dropped).
    """
    # Loud-fail on garbage fundamentals first (no silent defaults).
    payout_ratio = _num("payout_ratio", payout_ratio)
    ebitda = _num("ebitda", ebitda)
    revenue = _num("revenue", revenue)
    net_income = _num("net_income", net_income)
    shareholders_equity = _num("shareholders_equity", shareholders_equity)
    nci_pct = _num("nci_pct", nci_pct)
    if not isinstance(dps_history_years, int) or dps_history_years < 0:
        raise ValueError(f"dps_history_years must be a non-negative int, got {dps_history_years!r}")
    if not isinstance(segments_count, int) or segments_count < 1:
        raise ValueError(f"segments_count must be a positive int, got {segments_count!r}")

    verdict: GateVerdict = evaluate(
        ticker,
        domain=domain,
        filing_history_years=filing_history_years,
        ebit_positive_count=ebit_positive_count,
        d_de_ratio=d_de_ratio,
        net_debt_to_ebitda=net_debt_to_ebitda,
        interest_coverage=interest_coverage,
        shareholders_equity=shareholders_equity,
        nci_pct=nci_pct,
        revenue_drivers=list(revenue_drivers),
        has_steady_state_3y=has_steady_state_3y,
        life_cycle_stage=life_cycle_stage,
    )

    ordered: list[str] = []
    skipped: dict[str, str] = {}
    reasons: list[str] = list(verdict.reasons)

    def _add(key: str, why: str) -> None:
        if key not in ordered:
            ordered.append(key)
            reasons.append(f"method-gate: {key} gated - {why}")

    def _skip(key: str, why: str) -> None:
        if key not in ordered and key not in skipped:
            skipped[key] = why

    is_financial = domain in _FINANCIAL_DOMAINS

    # --- Anchor (decision-flow steps 1-9): DCF always runs unless EV undefined.
    if is_financial:
        anchor = DDM
        _add(DDM, "anchor for financials - debt is raw material, EV undefined (PDF Gate 0)")
        _skip(DCF, "FCFF/WACC DCF undefined for financials - EV not well defined (PDF Gate 0)")
    else:
        anchor = DCF
        if fcf_available:
            note = "shortened horizon + Thin Data" if verdict.thin_data else "anchor - always runs"
            _add(DCF, note)
        else:
            _skip(DCF, "no FCF history - anchor waived, relative methods carry the valuation")

    # --- Verdict primary / secondary (authoritative for WHICH method).
    prim_key = _VERDICT_TO_ENGINE.get(verdict.primary)
    if prim_key is None:  # "Relative Valuation" -> applicability table
        prim_key = _resolve_relative(ebitda, net_income, earnings_stable, has_peers, revenue)
    _add(prim_key, f"gate-verdict primary ({verdict.primary})")
    if verdict.secondary is not None:
        sec_key = _VERDICT_TO_ENGINE.get(verdict.secondary)
        if sec_key is None:
            sec_key = _resolve_relative(ebitda, net_income, earnings_stable, has_peers, revenue)
        _add(sec_key, f"gate-verdict secondary ({verdict.secondary})")

    # --- Mandatory cross-checks from failed gates (PDF: "sometimes a second
    # --- method is required alongside the first").
    failed = set(verdict.gates_failed)
    if "1c_capital_structure" in failed and not is_financial:
        _add(_resolve_relative(ebitda, net_income, earnings_stable, has_peers, revenue),
             "mandatory Relative cross-check - Gate 1c leverage breach")
    if 15.0 < nci_pct <= 40.0 and SOTP not in ordered:
        _add(SOTP, "mandatory SOTP cross-check - NCI in 15-40% band (PDF Gate 2)")
    if DCF in ordered and not any(k.startswith("REL_") for k in ordered) and not is_financial:
        # PDF step 10: a valid DCF is still paired with a Relative second check.
        _add(_resolve_relative(ebitda, net_income, earnings_stable, has_peers, revenue),
             "Relative second check - Relative Valuation is never fully optional (PDF step 10)")

    # --- Eligibility extras with skip reasons (task-mandated pre-filter rules).
    if DDM not in ordered:
        if payout_ratio > 0 and dps_history_years >= 1:
            _add(DDM, "eligible dividend payer - tertiary cross-check")
        elif payout_ratio <= 0:
            _skip(DDM, f"requires payout>0 and DPS history - payout_ratio={payout_ratio:g}")
        else:
            _skip(DDM, f"requires payout>0 and DPS history - dps_history_years={dps_history_years}")
    if REL_EBITDA not in ordered:
        if ebitda > 0:
            pass  # applicable but not required on this path - leave ungated, no skip claim
        else:
            _skip(REL_EBITDA, f"requires positive EBITDA - ebitda={ebitda:g} "
                              f"({RELATIVE_APPLICABILITY[REL_EBITDA]['avoid_when']})")
    if REL_PE not in ordered:
        if net_income <= 0:
            _skip(REL_PE, "requires positive stable earnings - net_income<=0 "
                           f"({RELATIVE_APPLICABILITY[REL_PE]['avoid_when']})")
        elif not (earnings_stable and has_peers):
            _skip(REL_PE, "requires stable earnings + clear peer group")
    if REL_PBV not in ordered and shareholders_equity <= 0:
        _skip(REL_PBV, "requires positive equity - P/BV undefined on negative equity (PDF Gate 1d)")
    if REL_SALES not in ordered and revenue <= 0:
        _skip(REL_SALES, "requires a revenue base to scale from")
    if SOTP not in ordered and segments_count <= 1:
        _skip(SOTP, "requires multiple dissimilar segments - single-pillar company")
    if NAV not in ordered and domain not in _FINITE_RESERVE_DOMAINS \
            and domain != DOMAIN_REIT and domain != DOMAIN_HOLDING_DISSIMILAR:
        _skip(NAV, "no reserve/asset base routing - NAV is for REIT/finite-reserve/Holding paths")

    return MethodGate(
        ticker=ticker,
        ordered=ordered,
        skipped=skipped,
        primary=ordered[0] if ordered else prim_key,
        secondary=ordered[1] if len(ordered) > 1 else None,
        anchor=anchor,
        thin_data=verdict.thin_data,
        reasons=reasons,
    )


def _normalize(method: str) -> str:
    """Accept engine keys and PDF verdict labels; loud-fail on unknown."""
    m = str(method).strip()
    if m in ALL_METHODS:
        return m
    mapped = _VERDICT_TO_ENGINE.get(m)
    if mapped is not None:
        return mapped
    if m == "Relative Valuation":
        raise ValueError(
            "ambiguous method 'Relative Valuation' - resolve to REL_PE/REL_PBV/REL_EBITDA/REL_SALES "
            "via the applicability table before gating"
        )
    raise ValueError(f"unknown valuation method {method!r} - known: {list(ALL_METHODS)}")


def check_fv_gated(method: str, gate: MethodGate) -> str:
    """Critic enforcement: FV from a non-gated method is REJECTED (loud).

    Returns the normalized engine key when gated; raises ValueError otherwise.
    """
    key = _normalize(method)
    if key not in gate.ordered:
        why = gate.skipped.get(key, "not selected by the method gate")
        raise ValueError(
            f"critic REJECT: FV from non-gated method {key} for {gate.ticker} - {why}. "
            f"Gated list: {gate.ordered}"
        )
    return key


def audit_valuation_fvs(fvs: dict[str, float], gate: MethodGate) -> list[str]:
    """Return one violation string per non-gated FV (empty = critic PASS)."""
    violations = []
    for method in fvs:
        try:
            check_fv_gated(method, gate)
        except ValueError as e:
            violations.append(str(e))
    return violations


def blended_from_gated(
    fvs: dict[str, float], weights: dict[str, float], gate: MethodGate
) -> dict[str, Any]:
    """Writer/blended enforcement: blend ONLY gated methods (loud-fail).

    Raises ValueError when any component is non-gated, when weights and FVs
    disagree on components, or when weights do not sum to 1.0.
    """
    if not fvs:
        raise ValueError("blended_from_gated: no FV components supplied")
    if set(weights) != set(fvs):
        raise ValueError(
            f"blended_from_gated: weights keys {sorted(weights)} != FV keys {sorted(fvs)}"
        )
    for method in fvs:
        check_fv_gated(method, gate)  # raises on non-gated
    s = sum(float(weights[k]) for k in weights)
    if abs(s - 1.0) > 1e-6:
        raise ValueError(f"blended_from_gated: weights sum {s} != 1.0")
    val = sum(float(fvs[k]) * float(weights[k]) for k in fvs)
    return {
        "blended_value": round(val, 2),
        "components": {k: float(fvs[k]) for k in fvs},
        "weights": {k: float(weights[k]) for k in weights},
        "gated_list": list(gate.ordered),
    }


def apply_output_sanity(
    gate: MethodGate,
    *,
    upside_pct: Optional[float],
    terminal_value_pct_of_ev: Optional[float] = None,
    implied_exit_ev_ebitda: Optional[float] = None,
    peer_exit_low: Optional[float] = None,
    peer_exit_high: Optional[float] = None,
) -> dict[str, Any]:
    """Gate 5, applied AFTER computation (PDF p.305-335 + user Delta 2).

    upside > 100% or downside < -50% vs market -> rating overridden to
    "Review Required" (never a bare BUY/HOLD/SELL). TV > 80% of EV -> flagged,
    no override. Implied exit EV/EBITDA outside the peer/historical range ->
    flagged for Relative cross-check, no override.
    """
    flags: list[str] = []
    rating_override: Optional[str] = None
    if upside_pct is not None:
        if upside_pct > 100.0:
            rating_override = "Review Required"
            flags.append(f"Gate 5: upside {_nf.dec(upside_pct, digits=1, signed=True)}% > 100% -> Review Required")
        elif upside_pct < -50.0:
            rating_override = "Review Required"
            flags.append(f"Gate 5: downside {_nf.dec(upside_pct, digits=1, signed=True)}% < -50% -> Review Required")
    if terminal_value_pct_of_ev is not None and terminal_value_pct_of_ev > 80.0:
        flags.append(
            f"Gate 5: terminal value {_nf.dec(terminal_value_pct_of_ev, digits=1)}% > 80% of EV -> "
            "flagged, pair with exit-multiple / Relative cross-check"
        )
    if implied_exit_ev_ebitda is not None and peer_exit_low is not None \
            and peer_exit_high is not None:
        if not (peer_exit_low <= implied_exit_ev_ebitda <= peer_exit_high):
            flags.append(
                f"Gate 5: implied exit EV/EBITDA {_nf.dec(implied_exit_ev_ebitda, digits=1)}× outside "
                f"peer range {_nf.dec(peer_exit_low, digits=1)}-{_nf.dec(peer_exit_high, digits=1)}× -> WACC/g out of sync "
                "with market pricing, cross-check vs EV/EBITDA relative valuation"
            )
    return {"rating_override": rating_override, "flags": flags, "ticker": gate.ticker}
