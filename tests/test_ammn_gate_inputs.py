"""AMMN-R2D regression guard: Gate-0..5 inputs are read from the assumptions file.

This file pins the wiring: gate inputs are READ from ``data/assumptions/{T}.json``
(nested ``gate_inputs`` block, the same key at top level, or a restatement of a
quantity the file already declares) and passed through to the payload that
``agents/valuation/gates.py::evaluate`` consumes. Keys the file does not support stay
ABSENT — nothing may be handed an invented filing history / equity base / coverage
ratio (LOUD policy).
"""
from __future__ import annotations

import json
import pathlib
from typing import Any

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
AMMN = REPO_ROOT / "data" / "assumptions" / "AMMN.json"

# agents/valuation/gates.py:evaluate — the keyword arguments the gate stage needs.
GATE_KEYS = (
    "filing_history_years",
    "ebit_positive_count",
    "d_de_ratio",
    "net_debt_to_ebitda",
    "interest_coverage",
    "shareholders_equity",
    "nci_pct",
    "revenue_drivers",
    "has_steady_state_3y",
    "life_cycle_stage",
)

# The two keys the loader may RESTATE from a quantity the file already declares.
_RESTATED = ("d_de_ratio", "net_debt_to_ebitda")

# Minimal 15-key valuation input set so _build_live_payload() clears its own 422 gate.
_VALUATION_INPUTS: dict[str, Any] = {
    "rf": 0.071, "beta": 1.4071, "erp": 0.0669, "cod": 0.0649, "g": 0.025,
    "payout": 0.0, "fcf": [13088.9] * 5, "shares_out": 72518217656.0,
    "net_debt": 110786062912260.0, "cash": 13846126732260.0,
    # forward EBITDA FY26F from the cited path x the target forward multiple (see assumptions file)
    "ebitda": 33861520000000.0, "ev_multiple": 15.0, "last_price": 4860.0,
    "we": 0.7608, "wd": 0.2392,
}

# A file-declared gate block for tests: every key the renderer requires, sourced
# from the file itself (mining domain mirrors agents/valuation/gates.py paths).
_DECLARED_GATE_INPUTS: dict[str, Any] = {
    "domain": "mining",
    "filing_history_years": 8,
    "ebit_positive_count": 3,
    "d_de_ratio": 0.24,
    "net_debt_to_ebitda": 5.27,
    "interest_coverage": 3.48,
    "shareholders_equity": 40_000_000_000_000.0,
    "nci_pct": 5.0,
    "revenue_drivers": ["commodity_coal"],
    "has_steady_state_3y": True,
    "life_cycle_stage": "mature",
}


def _assumptions(**overrides: Any) -> dict[str, Any]:
    data = dict(_VALUATION_INPUTS)
    data.update(overrides)
    return data


# ------------------------------------------------------------------ loader unit tests

def test_gate_inputs_read_from_nested_block_and_top_level():
    from server.routers.pdf import _gate_inputs_from_assumptions

    nested = _gate_inputs_from_assumptions({"gate_inputs": dict(_DECLARED_GATE_INPUTS)})
    assert nested == _DECLARED_GATE_INPUTS

    top_level = _gate_inputs_from_assumptions(dict(_DECLARED_GATE_INPUTS))
    assert top_level == _DECLARED_GATE_INPUTS


def test_gate_inputs_restate_file_declared_gearing_and_leverage():
    """wd is documented spot gearing D/(D+E); net_debt_after_cash is the net leg."""
    from server.routers.pdf import _gate_inputs_from_assumptions

    gi = _gate_inputs_from_assumptions({
        "wd": 0.2392, "net_debt_after_cash": 96_939_936_180_000.0,
        "ebitda": 18_396_257_972_040.0,
    })
    assert gi["d_de_ratio"] == pytest.approx(0.2392)
    assert gi["net_debt_to_ebitda"] == pytest.approx(
        96_939_936_180_000.0 / 18_396_257_972_040.0, rel=1e-4)


def test_gross_debt_leg_is_not_used_for_leverage():
    """The file labels `net_debt` the GROSS bridge leg (cash is added back separately);
    without `net_debt_after_cash` the leverage input must stay absent, not be guessed."""
    from server.routers.pdf import _gate_inputs_from_assumptions

    gi = _gate_inputs_from_assumptions({
        "net_debt": 110_786_062_912_260.0, "ebitda": 18_396_257_972_040.0,
    })
    assert "net_debt_to_ebitda" not in gi


def test_file_declared_values_win_over_restatements():
    from server.routers.pdf import _gate_inputs_from_assumptions

    gi = _gate_inputs_from_assumptions({
        "wd": 0.2392, "net_debt_after_cash": 96_939_936_180_000.0,
        "ebitda": 18_396_257_972_040.0,
        "gate_inputs": {"d_de_ratio": 0.77, "net_debt_to_ebitda": 9.99},
    })
    assert gi["d_de_ratio"] == 0.77 and gi["net_debt_to_ebitda"] == 9.99


def test_absent_keys_stay_absent_no_invented_defaults():
    """LOUD policy: an assumptions dict without gate facts yields an EMPTY block."""
    from server.routers.pdf import _gate_inputs_from_assumptions

    bare = {k: v for k, v in _assumptions().items() if k not in ("wd", "net_debt_after_cash")}
    assert _gate_inputs_from_assumptions(bare) == {}
    assert _gate_inputs_from_assumptions({}) == {}


# ------------------------------------------------------------------ live AMMN payload

@pytest.fixture(scope="module")
def ammn() -> dict:
    if not AMMN.exists():
        pytest.skip("data/assumptions/AMMN.json not present (AMMN data lane purged)")
    return json.loads(AMMN.read_text(encoding="utf-8"))


def test_ammn_live_payload_gate_inputs_are_file_backed(ammn: dict):
    """No gate input may appear on the payload that the file does not support."""
    from server.routers.pdf import _build_live_payload

    gi = _build_live_payload("AMMN", None)["gate_inputs"]
    nested: dict = dict(ammn.get("gate_inputs") or {})
    supported = set(nested) | {k for k in GATE_KEYS if ammn.get(k) is not None}
    supported |= {"domain"} | set(_RESTATED)
    assert set(gi) <= supported, f"payload invented gate inputs: {sorted(set(gi) - supported)}"

    if gi.get("d_de_ratio") is not None:
        assert gi["d_de_ratio"] == pytest.approx(float(ammn["wd"]))
    if gi.get("net_debt_to_ebitda") is not None:
        declared = (ammn.get("gate_inputs") or {}).get("net_debt_to_ebitda")
        if declared is not None:
            # The leverage gate input is declared, on the historic mid-cycle EBITDA (conservative). The
            # pricing leg runs on the forward level, so the two denominators differ on purpose and the
            # file has to say so — otherwise the next reader "corrects" the gate.
            assert gi["net_debt_to_ebitda"] == pytest.approx(float(declared), rel=1e-4)
            assert str(ammn.get("gate_inputs_basis_note") or "").strip(), \
                "a declared gate input on a different basis than the pricing leg must be annotated"
        else:
            assert gi["net_debt_to_ebitda"] == pytest.approx(
                float(ammn["net_debt_after_cash"]) / float(ammn["ebitda"]), rel=1e-4)


def test_payload_gate_inputs_are_never_invented(ammn: dict):
    """Every gate input on the payload must trace back to the assumptions file.

    Keys the file does not carry stay ABSENT: the gate stage is then handed only what the
    filing supports. A defaulted value here would be an invented filing history / equity base /
    coverage ratio, which is exactly what the LOUD policy forbids.
    """
    from server.routers.pdf import _build_live_payload

    gi = _build_live_payload("AMMN", None)["gate_inputs"]
    nested: dict = dict(ammn.get("gate_inputs") or {})

    # 1. nothing invented: each carried key is declared by the file (or restated from a
    #    quantity the file already declares).
    for key in gi:
        if key in _RESTATED:
            continue
        assert key in nested or ammn.get(key) is not None, f"payload invented gate input {key}"

    # 2. nothing defaulted: a key the file does not support must be absent from the payload,
    #    not filled with a plausible placeholder.
    for key in GATE_KEYS:
        if key in nested or ammn.get(key) is not None or key in _RESTATED:
            continue
        assert key not in gi, f"payload defaulted a gate input the file never declares: {key}"


# ------------------------------------------------- file -> gate passthrough (end-to-end)

def test_unassisted_render_passes_the_files_gate_inputs_through(tmp_path, monkeypatch):
    """The production loader, unassisted — no gate_inputs injected into the payload.

    The assumptions file (a tmp ``data/assumptions/TESTX.json``, the loader's real source)
    carries the ten keys, so the payload must carry them verbatim and the gate engine must
    clear with NAV primary: mining domain (Gate 0), 8y filing history (Gate 1, not thin).
    """
    from agents.valuation import gates as gate_engine
    from server.routers import pdf as pdf_router

    (tmp_path / "TESTX.json").write_text(
        json.dumps(_assumptions(gate_inputs=dict(_DECLARED_GATE_INPUTS))), encoding="utf-8"
    )
    monkeypatch.setattr(pdf_router, "ASSUMPTIONS_DIR", tmp_path)

    _template, _html, data = pdf_router.render_html_for_ticker("TESTX")
    assert data["gate_inputs"] == _DECLARED_GATE_INPUTS

    verdict = gate_engine.evaluate("TESTX", **data["gate_inputs"])
    # Gate 0 mining -> NAV (reserve-based) primary; Gate 1 passes on an 8y filing history so the
    # DCF runs as the cross-check rather than as the thin-data fallback.
    assert verdict.primary.startswith("NAV"), verdict.primary
    assert "DCF" in verdict.secondary, verdict.secondary
    assert verdict.thin_data is False
    assert not verdict.gates_failed
    assert len(verdict.gates_passed) == 9
