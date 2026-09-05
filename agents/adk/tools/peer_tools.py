# Copyright 2026 Sectors Hackathon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Bounded peer-to-peer communication tools and ledger (max 3x per run).

Implements deterministic inter-agent communication:
- Max 3 peer requests allowed per session run.
- Immutable state ledger tracking: from, to, fields, reason.
- Prevents infinite loops and token burns without vector DB.
- Requesting agent must state explicit needed_fields and justification reason.
- Critic audits requests and flags/rejects requests without justification.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Sequence

logger = logging.getLogger(__name__)

PEER_REQUEST_LIMIT: int = 3


def peer_request_allowed(state: dict[str, Any] | None) -> bool:
    """Check if the session state has remaining peer request quota.

    Args:
        state: Current session state dict or None.

    Returns:
        True if current request count < PEER_REQUEST_LIMIT, False otherwise.
    """
    if not state or not isinstance(state, dict):
        return True
    return len(state.get("peer_requests", [])) < PEER_REQUEST_LIMIT


def record_peer_request(
    state: dict[str, Any] | None,
    frm: str,
    to: str,
    fields: list[str] | Sequence[str] | str,
    reason: str = "",
) -> dict[str, Any]:
    """Record a peer data request in the state ledger.

    Args:
        state: Current session state dict.
        frm: Requesting agent name (e.g. 'analyst').
        to: Target agent name (e.g. 'collector').
        fields: Specific field names needed (cannot be empty).
        reason: Mandatory justification for why these fields are needed.

    Raises:
        ValueError: If fields is empty, whitespace-only, or missing.

    Returns:
        Updated state dictionary with new entry appended to 'peer_requests'.
    """
    if not fields:
        raise ValueError("request wajib sebut needed_fields spesifik")

    if isinstance(fields, str):
        cleaned_fields = [f.strip() for f in fields.split(",") if f.strip()]
        if not cleaned_fields:
            raise ValueError("request wajib sebut needed_fields spesifik")
    elif isinstance(fields, (list, tuple)):
        cleaned_fields = [str(f).strip() for f in fields if str(f).strip()]
        if not cleaned_fields:
            raise ValueError("request wajib sebut needed_fields spesifik")
    else:
        cleaned_fields = [str(fields)]

    current_state = dict(state) if state is not None else {}
    existing_requests = list(current_state.get("peer_requests", []))

    entry = {
        "from": frm,
        "to": to,
        "fields": cleaned_fields,
        "reason": reason.strip() if isinstance(reason, str) else str(reason),
    }

    return {**current_state, "peer_requests": [*existing_requests, entry]}


def request_peer_data(
    target_agent: str,
    needed_fields: list[str] | str,
    reason: str = "",
    from_agent: str = "analyst",
    tool_context: Any = None,
) -> dict[str, Any]:
    """Request specific data fields from a peer agent's output.

    Bounded inter-agent communication:
    - Maximum 3 requests allowed per session run.
    - Every request must specify needed_fields and justification reason.
    - If 3-request limit is reached, returns rejection so agent falls back to
      proceeding with gaps and documenting provenance.

    Args:
        target_agent: Target peer agent (e.g. 'collector', 'valuation').
        needed_fields: List of specific field keys needed (e.g. ['segments']).
        reason: Reason/justification for the request.
        from_agent: Name of the requesting agent.
        tool_context: ADK ToolContext injected automatically at runtime.

    Returns:
        Dict with status ('fulfilled', 'recorded', or 'rejected'), data, and message.
    """
    # Resolve state from tool_context or standalone dict
    session_state: dict[str, Any] | None = None
    if tool_context is not None:
        if isinstance(tool_context, dict):
            session_state = tool_context
        elif hasattr(tool_context, "_invocation_context") and hasattr(tool_context._invocation_context, "session"):
            session_state = tool_context._invocation_context.session.state
        elif hasattr(tool_context, "state"):
            ctx_state = tool_context.state
            if isinstance(ctx_state, dict):
                session_state = ctx_state
            elif hasattr(ctx_state, "_mapping"):
                inv = getattr(tool_context, "_invocation_context", None)
                if inv and hasattr(inv, "session"):
                    session_state = inv.session.state

    state_for_check = session_state if session_state is not None else {}

    # Check quota
    if not peer_request_allowed(state_for_check):
        return {
            "status": "rejected",
            "message": (
                f"Peer request quota reached (max {PEER_REQUEST_LIMIT}). "
                "Proceed with gaps and document data provenance in your report."
            ),
            "quota_limit": PEER_REQUEST_LIMIT,
            "requests_count": len(state_for_check.get("peer_requests", [])),
            "data": {},
        }

    # Record request in ledger
    try:
        updated = record_peer_request(
            state_for_check,
            frm=from_agent,
            to=target_agent,
            fields=needed_fields,
            reason=reason,
        )
    except ValueError as e:
        return {
            "status": "error",
            "message": str(e),
            "data": {},
        }

    # Update mutable session state if available
    if session_state is not None and isinstance(session_state, dict):
        session_state["peer_requests"] = updated["peer_requests"]

    # Attempt to locate requested data from target agent output
    raw_output = (
        state_for_check.get(f"{target_agent}_output")
        or state_for_check.get(target_agent)
        or {}
    )

    data_payload: dict[str, Any] = {}
    if isinstance(raw_output, str):
        try:
            parsed = json.loads(raw_output)
            if isinstance(parsed, dict):
                data_payload = parsed
        except Exception:
            pass
    elif isinstance(raw_output, dict):
        data_payload = raw_output

    norm_fields = [f.strip() for f in (needed_fields if isinstance(needed_fields, list) else [needed_fields])]
    extracted = {k: data_payload[k] for k in norm_fields if k in data_payload}

    requests_count = len(updated["peer_requests"])
    if extracted:
        return {
            "status": "fulfilled",
            "target_agent": target_agent,
            "data": extracted,
            "requests_count": requests_count,
            "remaining_quota": PEER_REQUEST_LIMIT - requests_count,
        }

    return {
        "status": "recorded",
        "target_agent": target_agent,
        "message": f"Request recorded for {target_agent} (field(s) not present yet).",
        "requests_count": requests_count,
        "remaining_quota": PEER_REQUEST_LIMIT - requests_count,
        "data": {},
    }


def audit_peer_requests(state: dict[str, Any] | None) -> tuple[bool, list[str]]:
    """Audit peer_requests entries for compliance and anti-laziness.

    Checks:
    - Every request has a non-empty, meaningful reason.
    - Every request has non-empty fields.
    - Total requests <= PEER_REQUEST_LIMIT.

    Args:
        state: State dictionary containing 'peer_requests'.

    Returns:
        (is_valid, list_of_violations)
    """
    if not state or not isinstance(state, dict):
        return True, []

    requests = state.get("peer_requests", [])
    if not requests:
        return True, []

    violations: list[str] = []
    if len(requests) > PEER_REQUEST_LIMIT:
        violations.append(
            f"Peer requests limit exceeded: {len(requests)} > {PEER_REQUEST_LIMIT}"
        )

    for idx, entry in enumerate(requests):
        reason = entry.get("reason", "")
        if not reason or not str(reason).strip():
            violations.append(
                f"Entry #{idx+1} from '{entry.get('from', '?')}' to '{entry.get('to', '?')}' "
                "missing justification reason (lazy request)"
            )
        fields = entry.get("fields", [])
        if not fields:
            violations.append(
                f"Entry #{idx+1} from '{entry.get('from', '?')}' to '{entry.get('to', '?')}' "
                "has empty needed_fields"
            )

    return len(violations) == 0, violations
