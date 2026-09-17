"""Tests for the tool_call_safety module.

The patch installs at import-time. Tests use the public `install()` and
`_patched_parse_tool_call_arguments` symbols to verify each repair path:
strict JSON, ast.literal_eval, ADK key-quote repair, and the new
salvage-partial path (Sep 17 2026).
"""
from __future__ import annotations

import json

import pytest

from agents.adk import tool_call_safety as tcs


def test_install_is_idempotent():
    """Calling install() twice should not double-install or crash."""
    a = tcs.install()
    b = tcs.install()
    # Either first call returns True and second False, or both False (already
    # installed by another test). Either is fine.
    assert isinstance(a, bool)
    assert isinstance(b, bool)
    assert not (a and b)


def test_strict_json_passes_through():
    assert tcs._patched_parse_tool_call_arguments('{"a": 1}') == {"a": 1}


def test_python_literal_fallback_works():
    """ast.literal_eval should accept single quotes for the salvage path."""
    # Single-quoted dict (Python literal, not strict JSON)
    result = tcs._patched_parse_tool_call_arguments("{'a': 1, 'b': 'two'}")
    assert result == {"a": 1, "b": "two"}


def test_unterminated_string_is_salvaged():
    """The model's actual failure mode: an apostrophe inside a string value
    terminates the JSON parser at column 17. Our salvage should still return
    the prefix dict that was valid."""
    bad = '{"claim": "I'  # unterminated - exactly the failure we saw
    result = tcs._patched_parse_tool_call_arguments(bad)
    # Salvage returns the prefix up to the cut-off point.
    assert isinstance(result, dict)
    # The salvage path strips the broken tail, so claim is either partial or
    # absent - the key thing is that we got a dict back, not a raise.
    assert "claim" in result or result == {}


def test_unterminated_with_full_prefix_dict():
    """A more realistic payload: full valid prefix dict, then unterminated
    tail. We should get the full prefix."""
    bad = (
        '{"round": 1, "claim": "anchor TP vulnerable", '
        '"defense_mode": "defend", "evidence_refs": ["FY26F EBITDA", "15x mult"]'
    )  # missing closing braces + apostrophe in evidence
    result = tcs._patched_parse_tool_call_arguments(bad)
    assert isinstance(result, dict)
    # Salvage should preserve the valid prefix fields.
    assert result.get("round") == 1
    assert result.get("claim") == "anchor TP vulnerable"
    assert result.get("defense_mode") == "defend"


def test_totally_unparseable_returns_empty_dict():
    """When even salvage fails, return {} so the tool call still goes through
    with no args. The next agent iteration will see the empty response and
    retry or skip."""
    result = tcs._patched_parse_tool_call_arguments("this is not json at all")
    assert result == {}


def test_empty_string_returns_empty_dict():
    assert tcs._patched_parse_tool_call_arguments("") == {}


def test_non_string_passes_through():
    """If the upstream provider already returns a dict, do not stringify."""
    obj = {"already": "a dict"}
    assert tcs._patched_parse_tool_call_arguments(obj) is obj


def test_live_adk_lite_llm_is_patched():
    """Verify the patch actually replaced the ADK symbol."""
    from google.adk.models import lite_llm

    assert lite_llm._parse_tool_call_arguments is tcs._patched_parse_tool_call_arguments


def test_real_failure_mode_apostrophe_in_string():
    """Mirror the live Sep 17 2026 failure: the model's tool-call arguments
    were `{"claim": "I'll` (apostrophe at column 17, char 16). The standard
    ADK paths all fail on this and the run dies. Verify our salvage path
    returns a dict instead of raising.
    """
    # Exact shape from the live log:
    bad = '{"claim": "I'
    result = tcs._patched_parse_tool_call_arguments(bad)
    assert isinstance(result, dict)
    # Salvage returns {} when nothing parseable (we'd need at least a complete
    # key/value pair), but the key guarantee is: no exception, returns dict.


def test_real_failure_mode_with_valid_prefix():
    """The live model's actual output before the cut-off had several valid
    prefix fields. Verify we recover those instead of returning empty."""
    bad = (
        '{"round": 1, "claim": "anchor TP vulnerable to single-input forecast", '
        '"defense_mode": "defend", "evidence": ['
    )
    result = tcs._patched_parse_tool_call_arguments(bad)
    assert isinstance(result, dict)
    assert result.get("round") == 1
    assert result.get("claim") == "anchor TP vulnerable to single-input forecast"
    assert result.get("defense_mode") == "defend"
