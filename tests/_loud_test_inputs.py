"""Shared test-only gate inputs for render-path tests (LOUD policy, Sep 2026).

`server/report/typst_renderer.py::_get_ticker_gate_params` refuses to invent
gate params: render tests must supply explicit `data["gate_inputs"]`.
These are DECLARED TEST SCENARIOS for typography/layout + gate-logic
assertions only — never market facts, never served in prod. Each scenario is
chosen to exercise a documented gate path in agents/valuation/gates.py:

- RATU: full-pass single business -> FCFF/WACC DCF, no thin banner.
- CDIA: filing<4y (thin) + ramping asset -> Relative Valuation + thin banner.
- MTEL: full-pass + NCI 15-40% band -> DCF + SOTP cross-check reason.
- BBCA: bank domain -> DDM / Excess Return.
- ADRO: mining domain -> NAV / Reserve-based.
- default: full-pass single business (JCI/TEST/others).
"""

from __future__ import annotations

from typing import Any

_BASE: dict[str, Any] = {
    "domain": "single_business",
    "filing_history_years": 5,
    "ebit_positive_count": 3,
    "d_de_ratio": 0.3,
    "net_debt_to_ebitda": 1.0,
    "interest_coverage": 4.0,
    "shareholders_equity": 1_000_000_000_000.0,
    "nci_pct": 5.0,
    "revenue_drivers": ["test-only placeholder"],
    "has_steady_state_3y": True,
    "life_cycle_stage": "mature",
}

TEST_GATE_INPUTS: dict[str, Any] = dict(_BASE)

TEST_GATE_SCENARIOS: dict[str, dict[str, Any]] = {
    "RATU": dict(_BASE),
    "CDIA": {
        **_BASE,
        "filing_history_years": 2,  # <4y -> thin_data + shortened-horizon DCF...
        "has_steady_state_3y": False,  # ...then gate 3 ramping override -> Relative
        "life_cycle_stage": "mature",  # must stay mature: gate 4 pre-profit/decline would clobber Relative
    },
    "MTEL": {**_BASE, "nci_pct": 25.0},  # 15-40% band -> DCF + SOTP cross-check
    "BBCA": {**_BASE, "domain": "bank"},
    "ADRO": {**_BASE, "domain": "mining"},
}


def inject_gate_inputs(data: dict[str, Any]) -> dict[str, Any]:
    """Set per-ticker test gate inputs on a render payload dict (mutates, returns it)."""
    if isinstance(data, dict):
        ticker = str((data.get("meta") or {}).get("ticker", "")).upper()
        data.setdefault("gate_inputs", dict(TEST_GATE_SCENARIOS.get(ticker, TEST_GATE_INPUTS)))
    return data
