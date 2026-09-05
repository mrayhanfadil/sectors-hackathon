# Copyright 2026 Sectors Hackathon
"""Tests for opencode-go Responses-API adapter (Muse Spark 1.3).

Live test is gated: set OPENCODE_GO_LIVE=1 to hit the real endpoint.
Default suite is fully mocked (no network, no key needed).
"""

from __future__ import annotations

import asyncio
import json
import os

import pytest

from google.adk.models.llm_request import LlmRequest
from google.genai import types

from agents.adk.providers.opencode_responses import (
    OpenGoResponsesLlm,
    _contents_to_input_items,
    _opencode_go_key,
    spark13_model,
)


def _req(contents=None, tools=None) -> LlmRequest:
    req = LlmRequest(contents=contents or [])
    if tools is not None:
        req.config.tools = tools
    return req


def _user_req(text: str = "hi") -> LlmRequest:
    return _req([types.Content(role="user", parts=[types.Part.from_text(text=text)])])


class _FakeResp:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = json.dumps(self._payload)

    def json(self):
        return self._payload


class _FakeClient:
    captured: dict = {}
    reply: _FakeResp = _FakeResp()

    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, headers=None, json=None):
        _FakeClient.captured = {"url": url, "headers": headers or {}, "json": json or {}}
        return _FakeClient.reply


def _run(coro_gen):
    async def collect():
        return [x async for x in coro_gen]

    return asyncio.run(collect())


@pytest.fixture
def mock_client(monkeypatch):
    import httpx

    _FakeClient.captured = {}
    _FakeClient.reply = _FakeResp(200, {"status": "completed", "output": []})
    monkeypatch.setattr(httpx, "AsyncClient", _FakeClient)
    return _FakeClient


def _model() -> OpenGoResponsesLlm:
    return OpenGoResponsesLlm(model="muse-spark-1.3-contributor", api_key="test-key")


def test_text_round_trip(mock_client):
    _FakeClient.reply = _FakeResp(
        200,
        {
            "status": "completed",
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": "PONG"}],
                }
            ],
        },
    )
    out = _run(_model().generate_content_async(_user_req("Reply with PONG")))
    assert len(out) == 1
    assert out[0].content.parts[0].text == "PONG"
    payload = _FakeClient.captured["json"]
    assert payload["model"] == "muse-spark-1.3-contributor"
    assert payload["input"] == [{"role": "user", "content": "Reply with PONG"}]
    assert _FakeClient.captured["url"].endswith("/responses")
    assert _FakeClient.captured["headers"]["Authorization"] == "Bearer test-key"


def test_function_call_parse(mock_client):
    _FakeClient.reply = _FakeResp(
        200,
        {
            "status": "completed",
            "output": [
                {
                    "type": "function_call",
                    "call_id": "call_123",
                    "name": "calc",
                    "arguments": '{"expr": "12*13"}',
                }
            ],
        },
    )
    out = _run(_model().generate_content_async(_user_req("calc")))
    fc = out[0].content.parts[0].function_call
    assert fc.name == "calc"
    assert fc.args == {"expr": "12*13"}
    assert fc.id == "call_123"


def test_history_translation():
    fc_part = types.Part.from_function_call(name="calc", args={"expr": "12*13"})
    assert fc_part.function_call is not None
    fc_part.function_call.id = "call_123"
    fr_part = types.Part.from_function_response(name="calc", response={"result": 156})
    assert fr_part.function_response is not None
    fr_part.function_response.id = "call_123"
    contents = [
        types.Content(role="user", parts=[types.Part.from_text(text="q")]),
        types.Content(role="model", parts=[fc_part]),
        types.Content(role="user", parts=[fr_part]),
    ]
    items = _contents_to_input_items(contents)
    assert items[0] == {"role": "user", "content": "q"}
    assert items[1]["type"] == "function_call"
    assert items[1]["call_id"] == "call_123"
    assert json.loads(items[1]["arguments"]) == {"expr": "12*13"}
    assert items[2]["type"] == "function_call_output"
    assert items[2]["call_id"] == "call_123"
    assert json.loads(items[2]["output"]) == {"result": 156}


def test_tools_translation(mock_client):
    _FakeClient.reply = _FakeResp(
        200,
        {"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": "ok"}]}]},
    )
    fd = types.FunctionDeclaration(
        name="calc",
        description="multiply",
        parameters_json_schema={
            "type": "object",
            "properties": {"expr": {"type": "string"}},
            "required": ["expr"],
        },
    )
    req = _user_req("calc")
    req.config.tools = [types.Tool(function_declarations=[fd])]
    _run(_model().generate_content_async(req))
    tools = _FakeClient.captured["json"]["tools"]
    assert tools[0]["type"] == "function"
    assert tools[0]["name"] == "calc"
    assert tools[0]["parameters"]["properties"]["expr"]["type"] == "string"


def test_empty_output_raises(mock_client):
    _FakeClient.reply = _FakeResp(200, {"status": "incomplete", "output": [], "incomplete_details": {"reason": "max_output_tokens"}})
    with pytest.raises(RuntimeError, match="no usable output"):
        _run(_model().generate_content_async(_user_req("hi")))


def test_http_error_raises_no_key_leak(mock_client):
    _FakeClient.reply = _FakeResp(500, {"type": "error", "error": {"message": "boom"}})
    with pytest.raises(RuntimeError, match="HTTP 500") as ei:
        _run(_model().generate_content_async(_user_req("hi")))
    assert "test-key" not in str(ei.value)


def test_key_explicit_passthrough():
    assert _opencode_go_key("  my-key  ") == "my-key"
    m = spark13_model(api_key="my-key")
    assert isinstance(m, OpenGoResponsesLlm)
    assert m.model == "muse-spark-1.3-contributor"
    assert m.api_base.startswith("https://opencode.ai/zen/go/v1")


def test_provider_aliases():
    from agents.adk.providers import provider_model

    for alias in ("opencode-go", "spark-1.3", "muse-spark-1.3-contributor"):
        m = provider_model(alias, api_key="k")
        assert isinstance(m, OpenGoResponsesLlm), alias


@pytest.mark.skipif(os.getenv("OPENCODE_GO_LIVE") != "1", reason="live probe gated (OPENCODE_GO_LIVE=1)")
def test_live_pong():
    m = spark13_model()
    out = _run(m.generate_content_async(_user_req("Reply with exactly the word PONG and nothing else")))
    texts = [p.text for p in out[0].content.parts if p.text]
    assert any("PONG" in t.upper() for t in texts), texts
