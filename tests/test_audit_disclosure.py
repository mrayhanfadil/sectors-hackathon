"""Tests for server/report/audit_disclosure.py.

The disclosure block stamps the post-audit injector's output onto
payload["cover"]["audit_disclosure"] so the deck can render it without
re-walking the agent run DB. These tests pin the helper shape so a
schema drift surfaces as a clear failure instead of a silent empty
block in production.

Two test buckets:
  * Pure parsing: writer_output as dict vs fenced-JSON string vs bare
    string, malformed input -> honest-empty defaults.
  * End-to-end: the helper writes to AgentRunStore and stamps a real
    payload; we read the payload back and check the shape.
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure repo root on path so `server.*` imports resolve in CI.
sys.path.insert(0, "/home/fadil/projects/sectors-hackathon")

from server.report.audit_disclosure import (  # noqa: E402
    _parse_writer_output,
    apply_audit_disclosure,
    extract_audit_disclosure,
)


# === _parse_writer_output ============================================
# All four shapes the live agent emits must parse to the same inner dict.


def test_parse_writer_output_dict():
    wo = {"gate_flags": ["DISSENT"], "non_anchored_fvs_disclosed": []}
    out = _parse_writer_output(wo)
    assert out == wo


def test_parse_writer_output_fenced_json():
    wo = {"gate_flags": ["DISSENT"]}
    raw = "```json\n" + json.dumps(wo) + "\n```"
    out = _parse_writer_output(raw)
    assert out == wo


def test_parse_writer_output_fenced_json_with_writer_output_wrapper():
    # The producer wraps the inner dict under its own key when fencing.
    inner = {"gate_flags": ["X"]}
    raw = "```json\n" + json.dumps({"writer_output": inner}) + "\n```"
    out = _parse_writer_output(raw)
    assert out == inner


def test_parse_writer_output_picks_last_fence_when_multiple():
    # Multiple fences can appear in raw text (the agent narrates
    # before the JSON). We want the LAST one (canonical output).
    early = {"gate_flags": ["STALE"]}
    late = {"gate_flags": ["CANONICAL"]}
    raw = (
        "narrative prefix\n```json\n" + json.dumps(early) + "\n```\n"
        "more text\n```json\n" + json.dumps(late) + "\n```\n"
    )
    out = _parse_writer_output(raw)
    assert out == late


def test_parse_writer_output_bare_json_no_fence():
    wo = {"gate_flags": ["PLAIN"]}
    raw = json.dumps(wo)
    out = _parse_writer_output(raw)
    assert out == wo


def test_parse_writer_output_garbage_returns_none():
    assert _parse_writer_output(None) is None
    assert _parse_writer_output("") is None
    assert _parse_writer_output("plain prose, no JSON at all") is None
    assert _parse_writer_output("```json\n{broken\n```") is None


def test_parse_writer_output_non_string_non_dict_returns_none():
    assert _parse_writer_output(42) is None
    assert _parse_writer_output(["list", "not", "dict"]) is None


# === extract_audit_disclosure / apply_audit_disclosure ================
# End-to-end via the real AgentRunStore with a temporary DB file.


@pytest.fixture
def tmp_agent_db_factory(monkeypatch):
    """Point AgentRunStore at a temp DB and return the db_path. Tests
    using this fixture are responsible for seeding their own data.
    """
    from server import storage as storage_mod

    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_path = str(Path(tmp.name))
    original_cls = storage_mod.AgentRunStore
    monkeypatch.setattr(
        storage_mod,
        "AgentRunStore",
        lambda *a, **kw: original_cls(db_path=db_path),
    )
    yield db_path
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def tmp_agent_db(monkeypatch):
    """Point AgentRunStore at a temp DB and seed one completed run."""
    from server import storage as storage_mod

    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_path = str(Path(tmp.name))
    # Schema bootstrap mirrors storage._init_db.
    store = storage_mod.AgentRunStore(db_path=db_path)
    state = {
        "writer_output": "```json\n" + json.dumps({
            "writer_output": {
                "title": "AMMN - test",
                "target_price": 5667.31,
                "rating": "BUY",
                "gate_flags": [
                    "DISSENT (Round 1): red team concede on FY26F EBITDA",
                    "RANGE_DISCLOSURE: anchor TP Rp 5,667 sits on conceded projection",
                ],
                "non_anchored_fvs_disclosed": [
                    {"label": "low_13x", "basis": "TTM EBITDA x 13x",
                     "fair_value": 4733, "contested": False,
                     "delta_from_tp_pct": -16.5},
                    {"label": "headline_15x", "basis": "FY26F EBITDA x 15x",
                     "fair_value": 5667, "contested": True,
                     "delta_from_tp_pct": 0.0},
                ],
                "anchor_justification": (
                    "anchor TP Rp 5,667 sits on conceded FY26F EBITDA projection"
                ),
            },
        }) + "\n```",
        "__audit__": {
            "verdict": "REJECT",
            "anchor_contested": True,
            "required_flags": ["DISSENT (Round 1): ..."],
            "injected_flags": 2,
            "missing_before": 0,
        },
    }
    store.start_run(
        run_id="run-test-disclosure",
        ticker="AMMN",
        prompt="",
        provider="test",
        model="test",
    )
    store.finish_run(
        run_id="run-test-disclosure",
        status="completed",
        last_text="ok",
        state=state,
        error=None,
        reason=None,
    )
    # Capture the ORIGINAL class before monkeypatch, otherwise the
    # lambda's `storage_mod.AgentRunStore(db_path=...)` call resolves
    # to the lambda itself (because monkeypatch already swapped the
    # attribute) and infinite-recurses.
    original_cls = storage_mod.AgentRunStore
    monkeypatch.setattr(
        storage_mod,
        "AgentRunStore",
        lambda *a, **kw: original_cls(db_path=db_path),
    )
    yield db_path
    Path(db_path).unlink(missing_ok=True)


def test_extract_returns_full_block(tmp_agent_db):
    block = extract_audit_disclosure("AMMN")
    assert block["present"] is True
    assert block["run_id"] == "run-test-disclosure"
    assert block["verdict"] == "REJECT"
    assert block["anchor_contested"] is True
    assert len(block["gate_flags"]) == 2
    assert "DISSENT (Round 1)" in block["gate_flags"][0]
    assert len(block["ladder"]) == 2
    assert block["ladder"][0]["label"] == "Kasus Bear (13x)"
    assert block["ladder"][0]["fair_value"] == 4733
    assert block["ladder"][1]["contested"] is True
    assert "conceded FY26F EBITDA" in (block["disclosure"] or "")


def test_extract_computes_delta_from_tp_pct_when_missing(
    tmp_agent_db_factory,
):
    """Sep 17 2026: when a manual mutation (or a producer that bypassed the
    post_audit_inject.py) puts rows in non_anchored_fvs_disclosed without
    a `delta_from_tp_pct` field, extract_audit_disclosure computes it from
    the writer_output.target_price so the Tangga Valuasi table still
    renders the vs TP column. This keeps the deck defensive against
    out-of-band verification states.
    """
    from server import storage as storage_mod

    db_path = tmp_agent_db_factory
    state = {
        "writer_output": "```json\n" + json.dumps({
            "writer_output": {
                "title": "AMMN - manual verify",
                "target_price": 5667.31,
                "rating": "BUY",
                "gate_flags": ["DISSENT (Round 1): ..."],
                "non_anchored_fvs_disclosed": [
                    {
                        "label": "low_13x",
                        "basis": "TTM EBITDA x 13x",
                        "fair_value": 4733.43,
                    },
                    {
                        "label": "high_17x",
                        "basis": "FY26F EBITDA x 17x",
                        "fair_value": 6601.18,
                    },
                ],
                "anchor_justification": "manual verify",
            },
        }) + "\n```",
        "__audit__": {
            "verdict": "REJECT",
            "anchor_contested": True,
            "required_flags": ["DISSENT (Round 1): ..."],
            "injected_flags": 1,
            "missing_before": 0,
        },
    }
    store = storage_mod.AgentRunStore(db_path=db_path)
    store.start_run(
        run_id="run-test-verify",
        ticker="AMMN",
        prompt="",
        provider="test",
        model="test",
    )
    store.finish_run(
        run_id="run-test-verify",
        status="completed",
        last_text="ok",
        state=state,
        error=None,
        reason=None,
    )
    block = extract_audit_disclosure("AMMN")
    assert len(block["ladder"]) == 2
    rows_by_label = {r["label"]: r for r in block["ladder"]}
    # delta_from_tp_pct was missing; computed from target_price (5667.31):
    # 4733.43 -> -16.48%, 6601.18 -> +16.48%
    assert rows_by_label["Kasus Bear (13x)"]["delta_from_tp_pct"] == -16.48
    assert rows_by_label["Kasus Bull (17x)"]["delta_from_tp_pct"] == 16.48
    # contested defaulted from anchor_contested
    assert rows_by_label["Kasus Bear (13x)"]["contested"] is True


def test_extract_returns_honest_empty_for_unknown_ticker(tmp_agent_db):
    block = extract_audit_disclosure("ZZZZ")
    assert block == {
        "present": False,
        "run_id": None,
        "gate_flags": [],
        "ladder": [],
        "disclosure": None,
        "verdict": None,
        "anchor_contested": False,
    }


def test_apply_stamps_onto_cover(tmp_agent_db):
    payload = {"cover": {}}
    out = apply_audit_disclosure(payload, "AMMN")
    assert out is payload  # in-place mutation, returns same obj
    block = payload["cover"]["audit_disclosure"]
    assert block["present"] is True
    assert block["verdict"] == "REJECT"
    assert len(block["gate_flags"]) == 2
    assert len(block["ladder"]) == 2


def test_apply_creates_cover_key_when_missing(tmp_agent_db):
    payload = {}
    apply_audit_disclosure(payload, "AMMN")
    assert "cover" in payload
    assert "audit_disclosure" in payload["cover"]


def test_apply_is_idempotent(tmp_agent_db):
    payload = {"cover": {}}
    apply_audit_disclosure(payload, "AMMN")
    first = dict(payload["cover"]["audit_disclosure"])
    apply_audit_disclosure(payload, "AMMN")
    second = dict(payload["cover"]["audit_disclosure"])
    assert first == second


def test_apply_handles_db_failure_without_raising(monkeypatch):
    """Even when the DB is down, apply_audit_disclosure must stamp
    honest-empty defaults rather than raise - the deck must render."""
    from server.report import audit_disclosure as mod

    def _boom(ticker):
        raise RuntimeError("db down")
    monkeypatch.setattr(mod, "extract_audit_disclosure", _boom)
    payload = {"cover": {}}
    # Must not raise:
    mod.apply_audit_disclosure(payload, "AMMN")
    block = payload["cover"]["audit_disclosure"]
    assert block["present"] is False
    assert block["gate_flags"] == []
    assert block["ladder"] == []


def test_clean_ladder_label_sensitivity_band():
    """Verify that sensitivity_X_band.{low,base,high} patterns are replaced with Indonesian case labels."""
    from server.report.audit_disclosure import _clean_ladder_label

    assert _clean_ladder_label({"label": "sensitivity_13x_to_17x_band.low"}) == "Kasus Bear (13x_to_17x)"
    assert _clean_ladder_label({"label": "sensitivity_13x_to_17x_band.base"}) == "Kasus Dasar (13x_to_17x)"
    assert _clean_ladder_label({"label": "sensitivity_13x_to_17x_band.high"}) == "Kasus Bull (13x_to_17x)"
    assert _clean_ladder_label({"label": "sensitivity_pe_band.low"}) == "Kasus Bear (pe)"
    assert _clean_ladder_label({"label": "sensitivity_pe_band.base"}) == "Kasus Dasar (pe)"
    assert _clean_ladder_label({"label": "sensitivity_pe_band.high"}) == "Kasus Bull (pe)"
    assert _clean_ladder_label({"label": "sensitivity_ev_ebitda_band.low"}) == "Kasus Bear (ev_ebitda)"
    assert _clean_ladder_label({"label": "sensitivity_ev_ebitda_band.high"}) == "Kasus Bull (ev_ebitda)"


def test_extract_handles_sensitivity_band_labels(tmp_agent_db_factory):
    """End-to-end test verifying extract_audit_disclosure converts sensitivity_X_band labels in DB."""
    from server import storage as storage_mod

    db_path = tmp_agent_db_factory
    state = {
        "writer_output": "```json\n" + json.dumps({
            "writer_output": {
                "title": "AMMN - sensitivity band test",
                "target_price": 5667.31,
                "rating": "BUY",
                "gate_flags": ["DISSENT (Round 1): ..."],
                "non_anchored_fvs_disclosed": [
                    {
                        "label": "sensitivity_13x_to_17x_band.low",
                        "basis": "EV/EBITDA 13x",
                        "fair_value": 4733.43,
                    },
                    {
                        "label": "sensitivity_13x_to_17x_band.base",
                        "basis": "EV/EBITDA 15x",
                        "fair_value": 5667.31,
                    },
                    {
                        "label": "sensitivity_13x_to_17x_band.high",
                        "basis": "EV/EBITDA 17x",
                        "fair_value": 6601.18,
                    },
                ],
                "anchor_justification": "sensitivity band test",
            },
        }) + "\n```",
        "__audit__": {
            "verdict": "REJECT",
            "anchor_contested": True,
            "required_flags": ["DISSENT (Round 1): ..."],
            "injected_flags": 1,
            "missing_before": 0,
        },
    }
    store = storage_mod.AgentRunStore(db_path=db_path)
    store.start_run(
        run_id="run-test-sens-band",
        ticker="AMMN",
        prompt="",
        provider="test",
        model="test",
    )
    store.finish_run(
        run_id="run-test-sens-band",
        status="completed",
        last_text="ok",
        state=state,
        error=None,
        reason=None,
    )
    block = extract_audit_disclosure("AMMN")
    assert len(block["ladder"]) == 3
    labels = [r["label"] for r in block["ladder"]]
    assert labels == [
        "Kasus Bear (13x_to_17x)",
        "Kasus Dasar (13x_to_17x)",
        "Kasus Bull (13x_to_17x)",
    ]

