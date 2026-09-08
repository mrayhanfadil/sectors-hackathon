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


def load_demo_fixture(ticker: str) -> dict[str, Any] | None:
    """Retired Sep 2026 (Sectors-only purge): static demo fixtures deleted.

    Always returns None. Kept as a stub so older imports fail soft during
    the migration window — new code must not call this. Render-path tests
    use explicit inline scaffolding; prod loaders 422 without Sectors data.
    """
    return None


# --- H2 prod-vs-fixture isolation helpers (Sep 2026) -----------------------
# LOUD policy: prod loaders must never serve static demo fixtures implicitly.
# Fixtures are reachable in tests ONLY via load_demo_fixture() above. These
# helpers let isolation tests name "fixture-shaped" payloads and their
# provenance markers without re-implementing the checks per test module.

#: Provenance prefix that must never appear on demo-shaped payloads served
#: (or claimed) as live data. Live Sectors sourcing stamps structured
#: `source` fields ("sectors", "sectors_missing_key", "assumptions/..."),
#: never a free-text "Sectors (...)" string. The static builders in
#: scripts/report_fixtures.py historically used "Sectors (IDX disclosure)".
FIXTURE_PROVENANCE_PREFIX = "Sectors ("

#: Tickers that historically had declared demo payloads (purged Sep 2026).
#: Prod loaders must 422 or return honest-empty data for these unless live
#: inputs exist. Kept (empty) so isolation tests iterate a stable symbol.
KNOWN_DEMO_TICKERS: tuple[str, ...] = ()


def payload_text(payload: dict[str, Any]) -> str:
    """Serialize a report payload for provenance/shape assertions."""
    import json as _json

    return _json.dumps(payload, ensure_ascii=False, default=str)


def contains_fixture_provenance(payload: dict[str, Any]) -> bool:
    """True when a payload carries a free-text live-Sectors provenance marker."""
    return FIXTURE_PROVENANCE_PREFIX in payload_text(payload)


def assert_no_fixture_provenance(payload: dict[str, Any], where: str = "") -> None:
    """Fail when a payload masquerades demo data as live Sectors output."""
    if contains_fixture_provenance(payload):
        raise AssertionError(
            f"fixture provenance {FIXTURE_PROVENANCE_PREFIX!r} on payload"
            f"{(' ' + where) if where else ''}"
            " — demo data must never claim live Sectors sourcing"
        )


def is_fixture_shaped(payload: dict[str, Any]) -> bool:
    """True when a payload carries demo numbers (vs honest-empty LOUD output).

    Honest-empty prod payloads (BBCA/ADRO typst skeletons) have
    rating_box.tp/price None, zero valuation methods and zero highlight rows.
    """
    if not isinstance(payload, dict):
        return False
    rb = ((payload.get("cover") or {}).get("rating_box") or {})
    if rb.get("tp") is not None or rb.get("price") is not None:
        return True
    if (payload.get("valuation") or {}).get("methods"):
        return True
    if (payload.get("financial_highlights") or {}).get("rows"):
        return True
    return False
