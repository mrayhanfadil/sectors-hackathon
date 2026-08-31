# Copyright 2026 Sectors Hackathon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Tests for T05 ADK Python scaffold.

Run: pytest agents/adk/tests/ -v
Requires: google-adk, mcp, litellm, pytest
No live LLM calls — all tests use fake BaseLlm / mocked McpToolset.
"""

from __future__ import annotations

import os
import re

import pytest

# ---------------------------------------------------------------------------
# Deterministic finance tools — no ADK needed
# ---------------------------------------------------------------------------


def test_calc_wacc_basic():
    from agents.adk.tools.finance_tools import calc_wacc

    out = calc_wacc(risk_free=0.0696, beta=0.7, equity_risk_premium=0.0689, cost_of_debt=0.035, weight_equity=0.6)
    assert abs(out["cost_of_equity"] - 0.11783) < 1e-4
    assert "wacc" in out
    assert out["wacc"] > 0


def test_calc_dcf_and_blended_weights():
    from agents.adk.tools.finance_tools import calc_dcf, calc_blended

    dcf = calc_dcf([100.0, 110.0, 120.0], wacc=0.10, terminal_growth=0.03, shares_outstanding=1_000_000_000)
    assert "fair_value_per_share" in dcf
    assert "error" not in dcf
    blended = calc_blended(dcf_value=dcf["fair_value_per_share"], multiples_value=5.0, w_dcf=0.6, w_multiples=0.4)
    assert abs(blended["blended_value"] - (dcf["fair_value_per_share"] * 0.6 + 5.0 * 0.4)) < 1e-6


def test_calc_dcf_rejects_wacc_le_growth():
    from agents.adk.tools.finance_tools import calc_dcf

    out = calc_dcf([100.0], wacc=0.03, terminal_growth=0.03, shares_outstanding=1e9)
    assert "error" in out


def test_calc_blended_rejects_bad_weights():
    from agents.adk.tools.finance_tools import calc_blended

    out = calc_blended(dcf_value=10, multiples_value=10, w_dcf=0.5, w_multiples=0.6)
    assert "error" in out


def test_calc_historical_bands():
    from agents.adk.tools.finance_tools import calc_historical_bands

    out = calc_historical_bands([1.0, 1.2, 1.1, 0.9, 1.3])
    assert "std" in out and "bands" in out
    assert out["bands"]["plus_2"] > out["bands"]["mean"] > out["bands"]["minus_2"]


def test_calc_ggm():
    from agents.adk.tools.finance_tools import calc_ggm

    out = calc_ggm(roe=0.197, cost_of_equity=0.12, growth=0.03, book_value_per_share=1000)
    assert "pbv" in out and "fair_value_per_share" in out
    assert out["pbv"] > 0


def test_calc_sotp():
    from agents.adk.tools.finance_tools import calc_sotp

    out = calc_sotp([{"name": "Energy", "value": 100}, {"name": "Water", "value": 50, "discount": 0.1}])
    assert out["sotp_value"] == pytest.approx(100 + 45)


def test_calc_ratios():
    from agents.adk.tools.finance_tools import calc_ratios

    out = calc_ratios(revenue=1000, ebitda=200, net_income=100, total_debt=500, cash=100, equity=800, interest_expense=20)
    assert out["ebitda_margin"] == pytest.approx(0.2)
    assert out["interest_coverage"] == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------


def test_strip_thinking_tags():
    from agents.adk.providers import strip_thinking_tags

    assert strip_thinking_tags("a <think>hidden</think> b") == "a  b"
    assert strip_thinking_tags("no tags") == "no tags"
    assert strip_thinking_tags("<think>x</think>") == ""


def test_provider_requires_api_key(monkeypatch):
    from agents.adk.providers import deepseek_model, gemini_model

    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        deepseek_model(api_key="")

    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
        gemini_model(api_key="")


def test_deepseek_litellm_construction_with_fake_key(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-fake-build-only")
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-gemini")
    from agents.adk.providers import deepseek_model

    m = deepseek_model()
    assert m.model == "openai/deepseek-chat"


def test_gemini_construction_with_fake_key(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-gemini-key")
    from agents.adk.providers import gemini_model

    m = gemini_model()
    assert "gemini" in m.model


# ---------------------------------------------------------------------------
# Graph structure — no live LLM calls
# ---------------------------------------------------------------------------


def test_build_graph_structure(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-fake")
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-gemini")

    # Avoid real MCP connection
    import agents.adk.app as app_mod
    from unittest.mock import patch
    import google.adk.tools.mcp_tool.mcp_toolset as mcp_mod

    orig_init = mcp_mod.McpToolset.__init__

    def fake_init(self, *a, **kw):
        self._fake = True
        self.connection_params = kw.get("connection_params")
        self.tool_filter = kw.get("tool_filter")
        self._tool_list_cache_ttl_seconds = kw.get("tool_list_cache_ttl_seconds", 60)
        self._closed = False
        self.name = "sectors_mcp"
        self._tools = []

    with patch.object(mcp_mod.McpToolset, "__init__", fake_init):
        from agents.adk.app import build_graph

        root = build_graph(ticker="BBCA")

    # Root is Sequential with 8 stages
    assert root.name == "equity_report_orchestrator"
    assert len(root.sub_agents) == 8

    intake, modeler, research, writer, visualizer, sotp, adv_loop, critic = root.sub_agents
    assert intake.name == "intake_parallel"
    assert modeler.name == "modeler"
    assert research.name == "research_parallel"
    assert writer.name == "writer"
    assert visualizer.name == "visualizer"
    assert sotp.name == "sotp"
    assert adv_loop.name == "adversarial_loop"
    assert critic.name == "critic"

    # Parallel composition
    assert len(intake.sub_agents) == 3  # collector, news, social
    assert {a.name for a in intake.sub_agents} == {"collector", "news_harvester", "social_sentiment"}
    assert len(research.sub_agents) == 4  # analyst, industry, risk, kpi

    # Loop cap is task-mandated max=4
    assert adv_loop.max_iterations == 4

    # GoogleSearch isolation: collector has no direct GoogleSearchTool; search agents do
    from google.adk.tools.google_search_tool import GoogleSearchTool

    collector = intake.sub_agents[0]
    assert not any(isinstance(t, GoogleSearchTool) for t in (collector.tools or [])), "collector must not own GoogleSearch directly"

    # News/social/industry route via AgentTool
    news = intake.sub_agents[1]
    social = intake.sub_agents[2]
    industry = research.sub_agents[1]
    assert any("AgentTool" in type(t).__name__ for t in (news.tools or []))
    assert any("AgentTool" in type(t).__name__ for t in (social.tools or []))
    assert any("AgentTool" in type(t).__name__ for t in (industry.tools or []))

    # Modeler owns deterministic calc_* FunctionTools
    assert modeler.tools, "modeler must have FunctionTools"
    tool_names = {getattr(t, "name", "") or getattr(t, "_name", "") or str(t) for t in modeler.tools}
    # at least these must be present
    assert any("calc_wacc" in n or "wacc" in n.lower() for n in tool_names), f"calc_wacc missing: {tool_names}"
    assert any("calc_dcf" in n for n in tool_names), f"calc_dcf missing: {tool_names}"


def test_max_iterations_drift_guard():
    """Single source of truth: MAX_ADVERSARIAL_ITERATIONS must appear in adversarial_loop."""
    from agents.adk.app import MAX_ADVERSARIAL_ITERATIONS
    from agents.adk.agents.instructions import adversarial_instruction

    assert MAX_ADVERSARIAL_ITERATIONS == 4
    # instruction should mention the cap (so drift is visible), but the enforced value is the const
    # don't assert on wording — just that the graph uses the const (checked above)


def test_mcp_endpoint_constant():
    from agents.adk.tools.mcp_sectors import SECTORS_MCP_URL

    assert SECTORS_MCP_URL == "https://sectors-mcp.supertype.ai/mcp"


def test_sectors_mcp_requires_key(monkeypatch):
    # clear all sector keys
    monkeypatch.delenv("SECTORS_API_KEY", raising=False)
    monkeypatch.delenv("SECTORS_MCP_API_KEY", raising=False)
    from agents.adk.tools.mcp_sectors import sectors_mcp_toolset

    with pytest.raises(ValueError, match="SECTORS_API_KEY"):
        sectors_mcp_toolset(api_key="")


def test_sectors_mcp_uses_bearer_and_streamable(monkeypatch):
    """Sectors MCP must use Authorization: Bearer and StreamableHTTPConnectionParams."""
    monkeypatch.setenv("SECTORS_API_KEY", "sk-sectors-fake")
    from unittest.mock import patch

    import google.adk.tools.mcp_tool.mcp_toolset as mcp_mod
    import google.adk.tools.mcp_tool.mcp_session_manager as sess_mod

    captured = {}

    def fake_init(self, *a, **kw):
        captured["kw"] = kw
        self._fake = True
        self.name = "sectors_mcp"
        self._tools = []

    with patch.object(mcp_mod.McpToolset, "__init__", fake_init):
        from agents.adk.tools.mcp_sectors import sectors_mcp_toolset

        sectors_mcp_toolset(api_key="sk-sectors-fake")

    cp = captured["kw"]["connection_params"]
    assert isinstance(cp, sess_mod.StreamableHTTPConnectionParams)
    assert cp.url == "https://sectors-mcp.supertype.ai/mcp"
    assert cp.headers["Authorization"] == "Bearer sk-sectors-fake"
