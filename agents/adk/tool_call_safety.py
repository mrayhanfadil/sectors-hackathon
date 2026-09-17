"""Defensive patch for ADK LiteLlm tool-call argument parsing.

Background (Sep 17 2026): `MiniMax-M3` (and possibly other free-tier models via
LiteLlm) sometimes emits tool-call argument JSON that has an unterminated string
(e.g. an unescaped apostrophe in a justification value). ADK's
`google.adk.models.lite_llm._parse_tool_call_arguments` tries three paths
(strict JSON, ast.literal_eval, key-quote repair) and if all fail it raises the
JSONDecodeError. The whole run dies at that point - the run is unrecoverable.

This module installs a 4th fallback: when the three ADK paths fail, scan for
the first balanced `{...}` substring that the standard library's
`json.JSONDecoder.raw_decode` can consume, and return whatever it parsed. The
remaining text is dropped, which is acceptable for tool calls (ADK's downstream
tool dispatch only sees the dict, and the agent's next iteration will retry or
skip).

Importing this module installs the patch as a side effect. Import it once at
runner startup; afterwards every LiteLlm call is protected.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_INSTALLED = False


def _repair_unterminated_string(arguments: str) -> dict | None:
    """Last-resort parser: find the longest prefix + synthetic close that
    parses as a JSON object.

    For each truncation stop, try appending one of a small set of synthetic
    closing characters (`, `}`, `" }`, `] }`, `" ] }`) and parse. Return the
    first dict we find, preferring the longest valid prefix.

    The synthetic-close trick handles two failure modes:
      1. The model's JSON is intact but missing the final closing brace(s)
         because the run got cut off mid-stream.
      2. The model emitted an unescaped apostrophe inside a string value,
         which terminates the JSON parser early. Dropping the tail before the
         apostrophe restores the parser's view of a complete object.
    """
    decoder = json.JSONDecoder()
    n = len(arguments)
    # Trim trailing whitespace.
    end = n
    while end > 0 and arguments[end - 1] in " \t\n\r":
        end -= 1
    if end == 0:
        return None
    # Closers to try, in order of likelihood. The list value-with-bool-key
    # pattern needs `\"` for the key close; the dict-with-list-of-strings
    # pattern needs `]}`; the dict-with-list-of-objects needs `}]}`.
    closers = (
        "",
        "}",
        "\"",
        "\"}",
        "\"]",
        "\"]}",
        "]",
        "]}",
        "}]",
        "}]}",
    )
    # Prefer the longest valid prefix.
    for stop in range(end, 1, -1):
        prefix = arguments[:stop]
        for closer in closers:
            try:
                obj, _consumed = decoder.raw_decode(prefix + closer)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                return obj
    return None


def _patched_parse_tool_call_arguments(arguments: Any) -> Any:
    """Drop-in replacement for ``lite_llm._parse_tool_call_arguments``.

    Adds one extra repair step after the three ADK-native fallbacks: try to
    salvage whatever JSON the model emitted before it got cut off. Returns `{}`
    only when salvage fails entirely, so the agent loop never crashes on a
    malformed tool call.
    """
    if not arguments:
        return {}
    if not isinstance(arguments, str):
        return arguments

    # 1. Strict JSON.
    try:
        return json.loads(arguments)
    except json.JSONDecodeError as exc:
        json_error = exc

    # 2. Python literal (handles single quotes + unquoted keys).
    try:
        import ast

        return ast.literal_eval(arguments)
    except (SyntaxError, ValueError):
        pass

    # 3. ADK key-quote repair (quote unquoted object keys).
    try:
        from google.adk.models import lite_llm as _adk_lite_llm

        repaired = _adk_lite_llm._quote_unquoted_json_object_keys(arguments)
    except Exception:
        repaired = arguments
    if repaired != arguments:
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            try:
                import ast

                return ast.literal_eval(repaired)
            except (SyntaxError, ValueError):
                pass

    # 4. NEW (Sep 17 2026): salvaged partial parse. Try every { position.
    salvaged = _repair_unterminated_string(arguments)
    if salvaged is not None:
        logger.warning(
            "tool_call_safety: salvaged partial tool-call JSON "
            "(%d keys, %d dropped chars)",
            len(salvaged),
            max(0, len(arguments) - 200),
        )
        return salvaged

    # All paths failed - return empty dict so the tool call still goes through
    # with no args. The agent's next iteration will see the empty-args response
    # and either retry or skip. This is strictly better than raising.
    logger.warning(
        "tool_call_safety: could not parse tool-call arguments "
        "(first 80 chars: %r); returning empty dict",
        arguments[:80],
    )
    return {}


def install() -> bool:
    """Install the patched parser. Idempotent; safe to call multiple times.

    Returns True if installation happened on this call, False if already
    installed.
    """
    global _INSTALLED
    if _INSTALLED:
        return False
    try:
        from google.adk.models import lite_llm as _adk_lite_llm
    except Exception as exc:  # pragma: no cover
        logger.warning("tool_call_safety: ADK lite_llm unavailable (%s); skipping", exc)
        return False
    _adk_lite_llm._parse_tool_call_arguments = _patched_parse_tool_call_arguments
    _INSTALLED = True
    logger.info("tool_call_safety: installed patched tool-call arg parser")
    return True


# Install on import so any code path that loads this module gets the patch.
install()
