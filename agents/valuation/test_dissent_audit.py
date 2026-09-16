"""Tests for the deterministic dissent audit.

The headline case is not synthetic: `fixtures/ammn_conceded_run.json` is the real
state of run ammn-4edb7301 (15 Sep 2026), in which the red team's Round 2 defense
conceded the 15.0x anchor and the published rating stayed BUY with
`gate_flags = []`. That run shipped a BUY whose own underwriting had been
withdrawn, so it is the regression the audit exists to catch.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.valuation.dissent_audit import (
    BUY_UPSIDE,
    SELL_UPSIDE,
    Rung,
    audit,
    ladder_from_text,
    parse_rounds,
    rating_for,
)

FIXTURE = Path(__file__).parent / "fixtures" / "ammn_conceded_run.json"
PRICE = 4860.0  # AMMN spot printed on the 15 Sep 2026 deck


@pytest.fixture(scope="module")
def conceded_state() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


# --- the real failing run ---------------------------------------------------


def test_real_conceded_run_is_rejected(conceded_state):
    res = audit(conceded_state, price=PRICE)
    assert res.verdict == "REJECT"


def test_real_conceded_run_flags_are_derived_not_written(conceded_state):
    """Both rounds conceded; both must produce a mechanically-derived flag."""
    res = audit(conceded_state, price=PRICE)
    assert len(res.required_flags) == 2, res.required_flags
    assert all(f.startswith("DISSENT (Round") for f in res.required_flags)
    assert res.missing_flags == res.required_flags, "declared gate_flags was empty"


def test_real_conceded_run_demands_the_house_override(conceded_state):
    """The published target sits on the conceded rung -> directional rating is not publishable."""
    res = audit(conceded_state, price=PRICE)
    assert res.anchor_contested is True
    assert res.rating_override_required == "Review Required"
    assert res.rating_actual == "BUY"
    assert any("directional" in r for r in res.reasons)


def test_real_conceded_run_ladder_is_reported(conceded_state):
    """The reader must be able to see every computed rung, not just the headline."""
    res = audit(conceded_state, price=PRICE)
    values = {round(r["fair_value"], 2) for r in res.ladder}
    assert {5667.31, 4277.12, 5872.75}.issubset(values), values
    primary = next(r for r in res.ladder if r["fair_value"] == 5667.31)
    assert primary["contested"] is True


# --- bands ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("upside", "expected"),
    [
        (0.50, "BUY"),
        (BUY_UPSIDE, "BUY"),
        (BUY_UPSIDE - 0.001, "HOLD"),
        (0.0, "HOLD"),
        (SELL_UPSIDE, "SELL"),
        (SELL_UPSIDE - 0.001, "SELL"),
        (-0.21, "SELL"),
    ],
)
def test_declared_bands(upside, expected):
    assert rating_for(upside) == expected


# --- parsing ----------------------------------------------------------------


def test_rounds_are_read_with_their_concession_state():
    state = {
        "debate_output": {
            "debate": [
                {"round": 1, "claim": "the TP anchor is too high", "defense": {"mode": "defend"},
                 "verdict": "CHALLENGE REJECTED"},
                {"round": 2, "claim": "the 15.0x multiple is mislabelled", "defense": {"mode": "concede"},
                 "verdict": "CHALLENGE ACCEPTED"},
            ]
        }
    }
    rounds = parse_rounds(state)
    assert [r.conceded for r in rounds] == [False, True]
    assert all(r.rating_relevant for r in rounds)


def test_ladder_reads_the_modelers_own_json_blocks():
    text = '{"low_13x": {"ev_ebitda": 13.0, "fair_value_per_share": 4733.43}, "primary_fv": {"multiple": 15.0, "fair_value_per_share": 5667.31}}'
    rungs = ladder_from_text(text)
    assert {r.label for r in rungs} == {"low_13x", "primary_fv"}
    assert max(r.fair_value for r in rungs) == 5667.31


def test_ladder_is_empty_when_the_modeler_computed_nothing():
    assert ladder_from_text("no numbers here") == []


# --- states that must NOT be rejected ---------------------------------------


def test_clean_run_without_concede_passes():
    state = {
        "debate_output": {"debate": [{"round": 1, "claim": "the TP anchor is high",
                                      "defense": {"mode": "defend"}, "verdict": "CHALLENGE REJECTED"}]},
        "writer_output": '{"rating": "BUY", "target_price": 5000, "gate_flags": []}',
        "valuation_output": '{"primary_fv": {"fair_value_per_share": 5000}}',
    }
    res = audit(state, price=4000.0)
    assert res.verdict == "PASS"
    assert res.required_flags == []
    assert res.rating_override_required is None


def test_concede_on_an_immaterial_claim_still_requires_disclosure_only():
    """A concede that does not touch the anchor forces the flag, not the override."""
    state = {
        "debate_output": {"debate": [{"round": 1, "claim": "the dividend policy wording is stale",
                                      "defense": {"mode": "concede"}, "verdict": "CHALLENGE ACCEPTED"}]},
        "writer_output": '{"rating": "BUY", "target_price": 5000, "gate_flags": []}',
        "valuation_output": '{"primary_fv": {"fair_value_per_share": 5000}}',
    }
    res = audit(state, price=4000.0)
    assert res.verdict == "PASS", "an immaterial concede is not a rating problem"
    assert res.required_flags == []


def test_published_target_off_ladder_is_flagged():
    state = {
        "debate_output": {"debate": [{"round": 1, "claim": "the 15.0x anchor is unanchored",
                                      "defense": {"mode": "concede"}, "verdict": "CHALLENGE ACCEPTED"}]},
        "writer_output": '{"rating": "BUY", "target_price": 9999, "gate_flags": []}',
        "valuation_output": '{"primary_fv": {"fair_value_per_share": 5667.31}}',
    }
    res = audit(state, price=4000.0)
    assert res.verdict == "REJECT"
    assert any("does not match any rung" in r for r in res.reasons)


def test_rung_and_audit_shapes_are_serialisable():
    res = audit({"debate_output": {}, "writer_output": "{}"}, price=100.0)
    dumped = json.dumps(res.to_dict())
    assert '"verdict"' in dumped


def test_sep16_shape_ladder_parses_with_idr_suffix():
    """The Sep 16 modeler emits the per-share value as `fair_value_per_share_idr`,
    not `fair_value_per_share`. The audit must extract those rungs so a concede's
    audience sees the full ladder instead of 'ladder unavailable'."""
    valuation = json.dumps({
        "primary_fv": {
            "method": "EV/EBITDA FY26F forward",
            "multiple_x": 15.0,
            "fair_value_per_share_idr": 5667.31,
        },
        "mid_cycle_cross_check": {
            "method": "EV/EBITDA on 3Y mean EBITDA",
            "multiple_x": 28.42,
            "fair_value_per_share_idr": 5872.75,
        },
        "sensitivity_primary": {
            "low_13x": {"fair_value_per_share_idr": 4733.43},
            "high_17x": {"fair_value_per_share_idr": 6601.18},
        },
    })
    rungs = ladder_from_text(valuation)
    values = {round(r.fair_value, 2) for r in rungs}
    assert {5667.31, 5872.75, 4733.43, 6601.18}.issubset(values), values
    labels = {r.label for r in rungs}
    # At minimum the named labels come through
    assert "primary_fv" in labels and "mid_cycle_cross_check" in labels


def test_sep16_flat_fv_per_share_keys_parse_as_rungs():
    """The Sep 16 producer emits flat keys at the top of the block:
    ``low_13x_fv_per_share`` / ``headline_15x_fv_per_share`` /
    ``high_17x_fv_per_share``. The audit must extract these so the
    Tangga valuasi row in the deck (server/report/ladder.py) lights up.
    Without Shape E, the deck prints 'Tangga valuasi belum tersedia'
    even though the run has 3 published rungs - which Fadil flagged on
    16 Sep 2026 E2E."""
    valuation = json.dumps({
        "low_13x_fv_per_share": 4733.43,
        "headline_15x_fv_per_share": 5667.31,
        "high_17x_fv_per_share": 6601.18,
        "current_price_idr_per_share": 4860.00,
    })
    rungs = ladder_from_text(valuation)
    values = {round(r.fair_value, 2) for r in rungs}
    assert {4733.43, 5667.31, 6601.18}.issubset(values), values
    labels = {r.label for r in rungs}
    assert {"low_13x_fv_per_share", "headline_15x_fv_per_share",
            "high_17x_fv_per_share"}.issubset(labels), labels


def test_sep16_conceded_run_is_rejected_with_anchor_contested():
    """Full pipeline check using the Sep 16 producer shape - the headline
    regression: a single binding projection that the red team conceded."""
    state = {
        "debate_output": json.dumps({
            "debate": [{
                "round": 1,
                "claim": "the 15.0x EV/EBITDA anchor on FY26F EBITDA is unanchored - it's a forward projection",
                "defense": {"mode": "concede"},
                "verdict": "CHALLENGE ACCEPTED: corrected framing recommended",
            }]
        }),
        "writer_output": json.dumps({
            "rating": "BUY",
            "target_price": 5667.31,
            "gate_flags": [],
        }),
        "valuation_output": json.dumps({
            "primary_fv": {
                "method": "EV/EBITDA FY26F forward",
                "multiple_x": 15.0,
                "fair_value_per_share_idr": 5667.31,
            },
            "mid_cycle_cross_check": {
                "method": "EV/EBITDA on 3Y mean EBITDA",
                "multiple_x": 28.42,
                "fair_value_per_share_idr": 5872.75,
            },
            "sensitivity_primary": {
                "low_13x": {"fair_value_per_share_idr": 4733.43, "multiple_x": 13.0},
                "high_17x": {"fair_value_per_share_idr": 6601.18, "multiple_x": 17.0},
            },
        }),
    }
    res = audit(state, price=4860)
    assert res.verdict == "REJECT"
    assert res.anchor_contested is True
    assert res.rating_override_required == "Review Required"
    assert any("directional" in r for r in res.reasons)
    assert Rung(label="x", basis="y", fair_value=1.0).fair_value == 1.0
