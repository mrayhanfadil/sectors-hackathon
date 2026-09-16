"""End-to-end audit: run the gate runner against the 5 quintet tickers + render PDFs.

Usage:
    .venv/bin/python scripts/audit_quintet_gates.py

Asserts:
- RATU: primary == "FCFF/WACC DCF", rating_override is None
- CDIA: primary == "DCF (shortened horizon)", thin_data == True,
        "1a_filing_history" in gates_failed
- MTEL: primary == "FCFF/WACC DCF", at least one reason contains "SOTP cross-check"
- BBCA: primary == "DDM / Excess Return"
- ADRO: primary == "NAV / Reserve-based"

Also prints a verdict table for human review.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as a script from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.valuation.gates import (  # noqa: E402
    DOMAIN_BANK,
    DOMAIN_MINING,
    DOMAIN_SINGLE_BUSINESS,
    evaluate,
)

QUINTET = {
    "RATU": dict(
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
        upside_pct=25.87,
    ),
    "CDIA": dict(
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
        upside_pct=22.61,
    ),
    "MTEL": dict(
        domain=DOMAIN_SINGLE_BUSINESS,
        filing_history_years=6,
        ebit_positive_count=3,
        d_de_ratio=0.6,
        net_debt_to_ebitda=3.5,
        interest_coverage=2.5,
        shareholders_equity=2e10,
        nci_pct=25.0,
        revenue_drivers=["volume_consumer", "rental"],
        has_steady_state_3y=True,
        life_cycle_stage="mature",
        upside_pct=33.4,
    ),
    "BBCA": dict(
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
        upside_pct=22.25,
    ),
    "ADRO": dict(
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
        upside_pct=86.32,
    ),
}

EXPECTATIONS = {
    "RATU": lambda v: v.primary == "FCFF/WACC DCF" and v.rating_override is None,
    "CDIA": lambda v: (
        v.primary == "DCF (shortened horizon)"
        and v.thin_data is True
        and "1a_filing_history" in v.gates_failed
    ),
    "MTEL": lambda v: v.primary == "FCFF/WACC DCF"
    and any("SOTP cross-check" in r for r in v.reasons),
    "BBCA": lambda v: v.primary == "DDM / Excess Return",
    "ADRO": lambda v: v.primary == "NAV / Reserve-based",
}


def main() -> int:
    print("=" * 80)
    print("VALUATION GATE AUDIT - Quintet (RATU / CDIA / MTEL / BBCA / ADRO)")
    print("=" * 80)
    print(
        f"{'Ticker':<6} {'Primary':<28} {'Secondary':<24} "
        f"{'Thin':<5} {'Override':<16} {'Pass/Fail':<10}"
    )
    print("-" * 80)

    all_passed = True
    for ticker, params in QUINTET.items():
        verdict = evaluate(ticker, **params)
        passed = EXPECTATIONS[ticker](verdict)
        all_passed = all_passed and passed
        marker = "✓ PASS" if passed else "✗ FAIL"
        print(
            f"{ticker:<6} {verdict.primary:<28} {(verdict.secondary or '-'):<24} "
            f"{str(verdict.thin_data):<5} "
            f"{(verdict.rating_override or '-'):<16} {marker:<10}"
        )

    print("-" * 80)
    if all_passed:
        print("ALL QUINTET TICKERS MATCH EXPECTED METHOD VERDICTS ✓")
        return 0
    else:
        print("ONE OR MORE TICKERS FAILED - review the table above")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
