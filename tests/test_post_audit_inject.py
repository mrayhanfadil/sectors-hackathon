"""Tests for the post-audit injection.

The injector is the deterministic bridge between the dissent-audit and the
PDF gate. It runs AFTER the ADK graph finishes, reads the same rounds the
audit reads, and surfaces:

  * `gate_flags`               - required_flags appended (union, dedup, declared-first)
  * `non_anchored_fvs_disclosed` - bear/mid/bull ladder, only when the anchor
                                    itself was conceded
  * `anchor_justification`     - audit's own disclosure text

The fixtures (agents/valuation/fixtures/ammn_conceded_run.json) are the real
states of runs the team ran. We use them unchanged so the injector is
tested against the same shape it will see in production.

Two cases worth spelling out:

  * When the writer_output fence is malformed, the injector MUST be a no-op
    (never raise). Real runs are noisy and a hard fail here blocks the gate.

  * Re-running the injector on an already-injected state MUST be idempotent
    - required_flags already present in gate_flags are not duplicated, so the
    PDF gate sees a stable flag set across re-runs.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from agents.adk.post_audit_inject import (
    _parse_writer_output,
    _normalize_flags,
    _compute_non_anchored_fvs,
    apply_audit_to_state,
)


FIXTURE_PATH = Path("agents/valuation/fixtures/ammn_conceded_run.json")
AMMN_PRICE = 4860.0  # the spot printed on the 15 Sep 2026 deck


@pytest.fixture()
def conceded_state() -> dict:
    """Fresh copy every test - earlier tests mutate the writer_output, which is
    a string field on the same dict object. Module scope would leak mutations."""
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


# --- parsing the writer_output fence -----------------------------------------


def test_parse_real_conceded_writer_output(conceded_state):
    inner = _parse_writer_output(conceded_state["writer_output"])
    assert isinstance(inner, dict)
    assert "target_price" in inner
    assert "gate_flags" in inner
    # Real shipped gate_flags was empty on this run - that's the regression
    assert inner.get("gate_flags") in ([], None)


def test_parse_raw_json_blob():
    blob = '\n```json\n{"target_price": 100, "rating": "BUY"}\n```\n'
    inner = _parse_writer_output(blob)
    assert inner == {"target_price": 100, "rating": "BUY"}


def test_parse_unwrapped_json():
    inner = _parse_writer_output('{"target_price": 100, "rating": "SELL"}')
    assert inner == {"target_price": 100, "rating": "SELL"}


def test_parse_wrapped_writer_output():
    inner = _parse_writer_output('\n```json\n{"writer_output": {"target_price": 99}}\n```\n')
    assert inner == {"target_price": 99}


@pytest.mark.parametrize("blob", ["", "   ", "not json at all", "{ malformed"])
def test_parse_returns_none_on_garbage(blob):
    assert _parse_writer_output(blob) is None


# --- flag normalization ------------------------------------------------------


def test_normalize_flags_handles_list():
    assert _normalize_flags(["a", "b"]) == ["a", "b"]


def test_normalize_flags_handles_json_string_list():
    assert _normalize_flags('["a", "b"]') == ["a", "b"]


def test_normalize_flags_handles_bare_string():
    assert _normalize_flags("single") == ["single"]


def test_normalize_flags_handles_none_and_dicts():
    assert _normalize_flags(None) == []
    assert _normalize_flags([{"k": "v"}, "x"]) == ['{"k": "v"}', "x"]


# --- the core behavior: dissent flags reach the deck -------------------------


def test_conceded_run_gets_required_flags_injected(conceded_state):
    """The headline regression: gate_flags was [] on the real run, must now carry DISSENT flags."""
    new_state = apply_audit_to_state(conceded_state, price=AMMN_PRICE)
    inner = _parse_writer_output(new_state["writer_output"])
    assert inner is not None
    flags = inner["gate_flags"]
    assert flags, "gate_flags must be non-empty on a conceded anchor"
    assert any(f.startswith("DISSENT") for f in flags), flags
    # Audit found 2 conceded rounds in the 15 Sep fixture
    dissent_flags = [f for f in flags if f.startswith("DISSENT")]
    assert len(dissent_flags) >= 2, dissent_flags


def test_anchor_contested_run_publishes_non_anchored_fvs(conceded_state):
    """Fix #2: the deck must surface bear/mid/bull instead of a single point."""
    new_state = apply_audit_to_state(conceded_state, price=AMMN_PRICE)
    inner = _parse_writer_output(new_state["writer_output"])
    assert inner is not None
    assert "non_anchored_fvs_disclosed" in inner
    disclosed = inner["non_anchored_fvs_disclosed"]
    assert isinstance(disclosed, list)
    # The 15 Sep fixture ladder had 4277.12 and 5872.75 as non-anchor rungs
    values = {round(d["fair_value"], 2) for d in disclosed}
    assert {4277.12, 5872.75}.issubset(values), values
    # Sorted ascending (bear -> bull)
    fvs = [d["fair_value"] for d in disclosed]
    assert fvs == sorted(fvs), fvs


def test_anchor_justification_is_set_on_conceded(conceded_state):
    new_state = apply_audit_to_state(conceded_state, price=AMMN_PRICE)
    inner = _parse_writer_output(new_state["writer_output"])
    assert inner is not None
    assert inner.get("anchor_justification")
    # Must reference the overridden slot
    assert "Review Required" in inner["anchor_justification"]


def test_range_disclosure_stamped_into_cover_paragraphs(conceded_state):
    """Fix #2: when the anchor is contested, append a range disclosure to the
    cover paragraphs and stamp a RANGE_DISCLOSURE flag for downstream surfaces."""
    fresh = json.loads(json.dumps(conceded_state))
    new_state = apply_audit_to_state(fresh, price=AMMN_PRICE)
    inner = _parse_writer_output(new_state["writer_output"])
    assert inner is not None
    cps = inner.get("cover_paragraphs") or []
    assert isinstance(cps, list)
    # The disclosure is the LAST paragraph
    assert any("Range surfaced from the computed ladder:" in (p or "") for p in cps), cps
    # The helper sources low_fv / high_fv from the actual ladder - so the
    # appended text must carry at least two distinct "Rp X,XXX" tokens. We
    # do NOT hardcode any ticker-specific number into the test.
    last = cps[-1] or ""
    import re
    fv_tokens = re.findall(r"Rp [\d,]+", last)
    distinct_fvs = set(fv_tokens)
    # The anchor TP itself is also present ("The published target (Rp 5,667)")
    # so we expect at least 3 distinct Rp-number tokens: anchor + low + high.
    assert len(distinct_fvs) >= 3, (last, distinct_fvs)
    # RANGE_DISCLOSURE flag also added
    flags = inner["gate_flags"]
    assert any(f.startswith("RANGE_DISCLOSURE:") for f in flags), flags


def test_synthetic_audit_record_attached(conceded_state):
    # Use a fresh copy so other tests' mutations don't poison this assertion
    fresh = json.loads(json.dumps(conceded_state))
    new_state = apply_audit_to_state(fresh, price=AMMN_PRICE)
    a = new_state["__audit__"]
    assert a["verdict"] == "REJECT"
    assert a["anchor_contested"] is True
    assert a["injected_flags"] >= 2
    assert a["reasons_count"] >= 1


# --- idempotency + safety ----------------------------------------------------


def test_injector_is_idempotent(conceded_state):
    fresh = json.loads(json.dumps(conceded_state))
    once = apply_audit_to_state(fresh, price=AMMN_PRICE)
    twice = apply_audit_to_state(once, price=AMMN_PRICE)
    once_inner = _parse_writer_output(once["writer_output"])
    twice_inner = _parse_writer_output(twice["writer_output"])
    assert once_inner is not None and twice_inner is not None
    assert once_inner["gate_flags"] == twice_inner["gate_flags"]


def test_injector_is_noop_when_writer_output_missing():
    state = {"debate_output": "{}", "valuation_output": ""}
    new = apply_audit_to_state(state, price=AMMN_PRICE)
    # No writer_output -> state unchanged
    assert new is state
    # When writer_output is present but malformed -> also unchanged
    state2 = {"writer_output": "{ malformed"}
    new2 = apply_audit_to_state(state2, price=AMMN_PRICE)
    assert new2 is state2


def test_injector_is_noop_on_clean_run():
    """When the audit says no dissent, gate_flags should not be polluted by FORCE-injected flags."""
    # Build a minimal clean state: 1 round, defense.mode='evidence', target=100, ladder={100: fv=100}
    writer_output = '\n```json\n{\n  "target_price": 100,\n  "rating": "HOLD",\n  "gate_flags": ["ORIGINAL_FLAG"],\n  "non_anchored_fvs_disclosed": null\n}\n```\n'
    valuation_output = json.dumps({
        "headline": {"fair_value_per_share": 100}
    })
    state = {
        "writer_output": writer_output,
        "valuation_output": valuation_output,
        "debate_output": json.dumps({
            "debate": [
                {
                    "round": 1,
                    "defense": {"mode": "evidence"},
                    "verdict": "defended",
                    "claim": "trivially true about volume",
                }
            ]
        }),
    }
    new = apply_audit_to_state(state, price=100.0)
    inner = _parse_writer_output(new["writer_output"])
    assert inner is not None
    # Original flag preserved (declared-first order)
    assert inner["gate_flags"][0] == "ORIGINAL_FLAG"
    # Audit didn't require anything new
    assert len(inner["gate_flags"]) == 1
    # anchor not contested -> no extra disclosure blocks
    assert inner.get("non_anchored_fvs_disclosed") is None
    assert "anchor_justification" not in inner


def test_injector_preserves_existing_flags(conceded_state):
    """If the writer had its OWN flags, they stay as the first entries."""
    state = json.loads(json.dumps(conceded_state))
    inner = _parse_writer_output(state["writer_output"])
    assert inner is not None
    inner["gate_flags"] = ["WRITER_FLAG_1", "WRITER_FLAG_2"]
    state["writer_output"] = "\n```json\n" + json.dumps(inner) + "\n```\n"
    new = apply_audit_to_state(state, price=AMMN_PRICE)
    new_inner = _parse_writer_output(new["writer_output"])
    assert new_inner is not None
    assert new_inner["gate_flags"][:2] == ["WRITER_FLAG_1", "WRITER_FLAG_2"]
    # Audit DISSENT flags come AFTER (declared-first order)
    assert any(f.startswith("DISSENT") for f in new_inner["gate_flags"])


def test_range_disclosure_idempotent_on_rerun(conceded_state):
    """Re-running the injector must not duplicate the range paragraph or flag."""
    fresh = json.loads(json.dumps(conceded_state))
    once = apply_audit_to_state(fresh, price=AMMN_PRICE)
    twice = apply_audit_to_state(once, price=AMMN_PRICE)
    inner_once = _parse_writer_output(once["writer_output"])
    inner_twice = _parse_writer_output(twice["writer_output"])
    assert inner_once is not None and inner_twice is not None
    cps_once = inner_once["cover_paragraphs"]
    cps_twice = inner_twice["cover_paragraphs"]
    # Exactly one range-disclosure paragraph in each
    rng_once = sum(1 for p in cps_once if "Range surfaced from the computed ladder:" in (p or ""))
    rng_twice = sum(1 for p in cps_twice if "Range surfaced from the computed ladder:" in (p or ""))
    assert rng_once == 1 and rng_twice == 1
    # Flag count also stable
    flag_once = sum(1 for f in inner_once["gate_flags"] if f.startswith("RANGE_DISCLOSURE:"))
    flag_twice = sum(1 for f in inner_twice["gate_flags"] if f.startswith("RANGE_DISCLOSURE:"))
    assert flag_once == flag_twice == 1


# --- bear/mid/bull sort + delta math -----------------------------------------


def test_compute_non_anchored_fvs_sorts_ascending():
    ladder = [
        {"label": "head", "basis": "", "fair_value": 5667, "contested": True},
        {"label": "low",  "basis": "", "fair_value": 3830, "contested": False},
        {"label": "mid",  "basis": "", "fair_value": 5176, "contested": False},
        {"label": "high", "basis": "", "fair_value": 5872, "contested": False},
    ]
    out = _compute_non_anchored_fvs(ladder, target_price=5667, anchor_value=5667)
    fvs = [d["fair_value"] for d in out]
    # anchor excluded, rest sorted ascending
    assert fvs == [3830, 5176, 5872]


def test_compute_non_anchored_fvs_delta_pct():
    out = _compute_non_anchored_fvs(
        [{"label": "low", "basis": "TTM EBITDA x 15x", "fair_value": 3830, "contested": False}],
        target_price=5667,
        anchor_value=5667,
    )
    assert out[0]["delta_from_tp_pct"] == pytest.approx(-32.39, abs=0.5)
