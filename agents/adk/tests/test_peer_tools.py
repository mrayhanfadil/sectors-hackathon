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


def test_function_tool_wrapper_request_peer_data():
    import json
    from google.adk.tools import FunctionTool
    from agents.adk.tools.peer_tools import request_peer_data

    ft = FunctionTool(request_peer_data)
    assert ft.name == "request_peer_data"
    assert "request_peer_data" in ft.description.lower() or "peer" in ft.description.lower()


def test_request_peer_data_lifecycle_with_state():
    import json
    from agents.adk.tools.peer_tools import request_peer_data

    state = {
        "collector_output": json.dumps({"segments": ["Banking", "Treasury"], "peers": ["BBRI", "BMRI"]}),
        "peer_requests": [],
    }

    # 1st request — should be fulfilled
    res1 = request_peer_data(
        target_agent="collector",
        needed_fields=["segments"],
        reason="Need segments breakdown for operational thesis",
        from_agent="analyst",
        tool_context=state,
    )
    assert res1["status"] == "fulfilled"
    assert res1["data"]["segments"] == ["Banking", "Treasury"]
    assert len(state["peer_requests"]) == 1

    # 2nd request — recorded
    res2 = request_peer_data(
        target_agent="news_harvester",
        needed_fields=["catalysts"],
        reason="Need catalyst headlines for risk analysis",
        from_agent="risk",
        tool_context=state,
    )
    assert res2["status"] in ("fulfilled", "recorded")
    assert len(state["peer_requests"]) == 2

    # 3rd request — recorded
    res3 = request_peer_data(
        target_agent="collector",
        needed_fields=["peers"],
        reason="Need peer comparison for industry outlook",
        from_agent="industry",
        tool_context=state,
    )
    assert res3["status"] == "fulfilled"
    assert res3["data"]["peers"] == ["BBRI", "BMRI"]
    assert len(state["peer_requests"]) == 3

    # 4th request — rejected (quota exceeded)
    res4 = request_peer_data(
        target_agent="collector",
        needed_fields=["financials_5y"],
        reason="Need financials",
        from_agent="kpi",
        tool_context=state,
    )
    assert res4["status"] == "rejected"
    assert "quota reached" in res4["message"].lower() or "limit" in res4["message"].lower()
    assert len(state["peer_requests"]) == 3  # Not added


def test_request_peer_data_validation_error():
    from agents.adk.tools.peer_tools import request_peer_data

    state = {}
    res = request_peer_data(
        target_agent="collector",
        needed_fields=[],
        reason="Need data",
        from_agent="analyst",
        tool_context=state,
    )
    assert res["status"] == "error"
    assert "needed_fields" in res["message"]


def test_peer_wiring_snippet_file_exists_and_valid():
    import pathlib

    snippet_path = pathlib.Path(__file__).parent.parent / "tools" / "PEER_WIRING.snippet.md"
    assert snippet_path.exists(), "PEER_WIRING.snippet.md must exist"

    content = snippet_path.read_text(encoding="utf-8")
    assert "from agents.adk.tools.peer_tools import request_peer_data" in content
    assert "FunctionTool(request_peer_data)" in content
    assert "needed_fields" in content
    assert "proceed-with-gaps" in content or "provenance" in content


def test_research_instructions_have_peer_protocol():
    from agents.adk.agents.instructions import (
        analyst_instruction,
        industry_instruction,
        risk_instruction,
        kpi_instruction,
    )

    for name, instr in [
        ("analyst", analyst_instruction),
        ("industry", industry_instruction),
        ("risk", risk_instruction),
        ("kpi", kpi_instruction),
    ]:
        assert "request_peer_data" in instr, f"{name}_instruction must mention request_peer_data"
        assert "needed_fields" in instr, f"{name}_instruction must mention needed_fields"
        assert "peer_requests sudah 3" in instr or "peer_requests" in instr, f"{name}_instruction must mention 3-strike rule"

