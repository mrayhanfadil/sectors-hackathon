# Copyright 2026 Sectors Hackathon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Tests for peer tools — bounded inter-agent communication (max 3x)."""

import pytest
from agents.adk.tools.peer_tools import (
    PEER_REQUEST_LIMIT,
    peer_request_allowed,
    record_peer_request,
)


def test_peer_request_limit_constant():
    assert PEER_REQUEST_LIMIT == 3


def test_peer_request_allowed_and_recorded():
    state = {}
    assert peer_request_allowed(state) is True
    for _ in range(3):
        state = record_peer_request(state, frm="analyst", to="collector", fields=["segments"])
    assert peer_request_allowed(state) is False  # 4th request blocked
    assert len(state["peer_requests"]) == 3
    assert state["peer_requests"][0]["fields"] == ["segments"]
    assert state["peer_requests"][0]["from"] == "analyst"
    assert state["peer_requests"][0]["to"] == "collector"


def test_record_peer_request_with_reason():
    state = {}
    state = record_peer_request(
        state,
        frm="risk",
        to="collector",
        fields=["debt_breakdown"],
        reason="Need loan structure to assess refinancing risk",
    )
    assert len(state["peer_requests"]) == 1
    req = state["peer_requests"][0]
    assert req["from"] == "risk"
    assert req["to"] == "collector"
    assert req["fields"] == ["debt_breakdown"]
    assert req["reason"] == "Need loan structure to assess refinancing risk"


def test_record_peer_request_empty_fields_raises_value_error():
    state = {}
    with pytest.raises(ValueError, match="needed_fields"):
        record_peer_request(state, frm="analyst", to="collector", fields=[])

    with pytest.raises(ValueError, match="needed_fields"):
        record_peer_request(state, frm="analyst", to="collector", fields="")

    with pytest.raises(ValueError, match="needed_fields"):
        record_peer_request(state, frm="analyst", to="collector", fields=["   "])


def test_record_peer_request_immutability():
    state = {"peer_requests": [{"from": "kpi", "to": "collector", "fields": ["towers"], "reason": "tower count"}]}
    new_state = record_peer_request(state, frm="industry", to="news", fields=["regulations"], reason="policy update")
    assert len(state["peer_requests"]) == 1
    assert len(new_state["peer_requests"]) == 2
