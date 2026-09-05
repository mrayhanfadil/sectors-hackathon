"""Structured debate validation (ACES 2026-09-05).

`debate_output` MUST be a JSON array of rounds — plain strings and
placeholders ("in progress", "review complete") are invalid. Each round's
defense must cite calc recomputation AND url+date sources, otherwise the
Critic must REJECT.

Schema per round:
  {round: int, challenger: str, claim: str,
   defense: {mode: defend|concede, calc_refs: [str...], sources: [{url, date}...]},
   verdict: str}

Stdlib only. Run: .venv/bin/python -m pytest agents/adk/tests/test_debate.py -v
"""

from __future__ import annotations

import json
from typing import Any

REQUIRED_ROUND_KEYS = ("round", "challenger", "claim", "defense", "verdict")
REQUIRED_DEFENSE_KEYS = ("mode", "calc_refs", "sources")
DEFENSE_MODES = ("defend", "concede")


def _strip_fence(s: str) -> str:
    t = s.strip()
    if t.startswith("```"):
        lines = t.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        t = "\n".join(lines).strip()
    return t


def _coerce(output: Any) -> tuple[Any, str | None]:
    """Return (parsed, error). parsed may be list/dict/str-passthrough."""
    if isinstance(output, list):
        return output, None
    if isinstance(output, dict):
        for key in ("debate", "rounds", "debate_output"):
            if isinstance(output.get(key), list):
                return output[key], None
        return None, "dict without a rounds list (keys: %s)" % sorted(output.keys())
    if isinstance(output, str):
        t = _strip_fence(output)
        if not t:
            return None, "empty debate"
        try:
            parsed = json.loads(t)
        except Exception:
            return None, "not JSON (plain string/placeholder)"
        if isinstance(parsed, dict):
            return _coerce(parsed)
        if isinstance(parsed, list):
            return parsed, None
        return None, "JSON is not an array"
    return None, f"unsupported type {type(output).__name__}"


def validate_debate(output: Any) -> tuple[bool, list[str]]:
    """Validate structured debate. Returns (ok, errors)."""
    errors: list[str] = []
    rounds, err = _coerce(output)
    if err:
        return False, [err]
    if not rounds:
        return False, ["no rounds"]
    for i, r in enumerate(rounds):
        tag = f"round[{i}]"
        if not isinstance(r, dict):
            errors.append(f"{tag}: not an object")
            continue
        for k in REQUIRED_ROUND_KEYS:
            if k not in r:
                errors.append(f"{tag}: missing key '{k}'")
        d = r.get("defense")
        if isinstance(d, dict):
            for k in REQUIRED_DEFENSE_KEYS:
                if k not in d:
                    errors.append(f"{tag}.defense: missing key '{k}'")
            if d.get("mode") not in DEFENSE_MODES:
                errors.append(f"{tag}.defense: mode must be defend|concede")
            if not isinstance(d.get("calc_refs"), list) or not d["calc_refs"]:
                errors.append(f"{tag}.defense: calc_refs must be a non-empty list")
            srcs = d.get("sources")
            if not isinstance(srcs, list) or not srcs:
                errors.append(f"{tag}.defense: sources must be a non-empty list")
            elif not all(
                isinstance(s, dict) and s.get("url") and s.get("date") for s in srcs
            ):
                errors.append(f"{tag}.defense: every source needs url+date")
        elif "defense" in r:
            errors.append(f"{tag}.defense: must be an object")
    return (len(errors) == 0), errors
