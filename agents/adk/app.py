# Copyright 2026 Sectors Hackathon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Main ADK Python graph — 11 agents → Sequential/Parallel/LoopAgent(max=4).

Orchestrator wiring per plan.md §3 + task T05:

  Collector + News + Social  (Parallel, 3-way)
          ↓ blocking
      Modeler (THE BRAIN, deterministic FunctionTools)
          ↓
  Analyst + Industry + Risk + KPI  (Parallel, 4-way)
          ↓
      Writer → Visualizer → SOTP → Adversarial (LoopAgent max=4) → Critic

GoogleSearch isolation: search-bearing sub-agents are Sectors-only (Google was
removed Sep 2026 as an external source). Search sub-agents carry no tools
and emit honest sectors_missing_key empties keyless (genai limit:
GoogleSearch cannot coexist with FunctionTool in the same LlmAgent).

Provider: DeepSeek deepseek-chat via LiteLlm (OpenAI-compat) for main agents;
Gemini gemini-2.0-flash for search-grounded sub-agents. Falls back to LiteLlm
if Gemini key missing.

MCP: Sectors MCP streamable HTTP via McpToolset(StreamableHTTPConnectionParams)
with Authorization: Bearer <SECTORS_API_KEY> — lazy-connect (best-effort).
"""

from __future__ import annotations

# Prevent litellm auto-loading ~/.env with stale GOOGLE_API_KEY; also scrub it if already loaded
import os as _os

_os.environ.setdefault("LITELLM_MODE", "PRODUCTION")
# The key in /home/fadil/.env (AIzaSyAbbT2rqy...) is a placeholder that returns 400 INVALID_ARGUMENT.
# Scrub it so ADK search sub-agents gracefully degrade instead of crashing the Parallel group.
if _os.getenv("GOOGLE_API_KEY", "").startswith("AIzaSyAbbT2"):
    _os.environ.pop("GOOGLE_API_KEY", None)
if _os.getenv("GEMINI_API_KEY", "").startswith("AIzaSyAbbT2"):
    _os.environ.pop("GEMINI_API_KEY", None)

import logging
import os
from typing import Any

from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.loop_agent import LoopAgent
from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.tools.exit_loop_tool import exit_loop
from google.adk.tools.function_tool import FunctionTool
from .tools.peer_tools import request_peer_data

# Bounded peer comms (plan Task 4): research agents may pull missing fields
# from a peer's output_key, max 3 requests/run enforced inside the tool.
PEER_PROTOCOL = (
    "\n\nPEER REQUEST PROTOCOL:\n"
    "Kalau field dari agent lain kosong: (1) cek state dulu, (2) panggil "
    "request_peer_data SEKALI per field-set dengan alasan + from_agent=<namamu>, "
    "(3) kalau peer_requests sudah 3 → lanjut dengan data seadanya + tulis "
    "provenance gap. DILARANG request tanpa needed_fields."
)
# (Sep 2026, Sectors-only rule): GoogleSearchTool import removed (external source).

from .agents.instructions import (
    adversarial_instruction,
    analyst_instruction,
    collector_instruction,
    critic_instruction,
    industry_instruction,
    kpi_instruction,
    modeler_instruction,
    news_harvester_instruction,
    risk_instruction,
    social_sentiment_instruction,
    sotp_instruction,
    visualizer_instruction,
    writer_instruction,
)
from .providers import deepseek_model, gemini_model, spark_model
from .tools.finance_tools import DETERMINISTIC_TOOLS
from .tools.sectors_financial_tools import SECTORS_FINANCIAL_TOOLS
from .debate import submit_debate
from .tools.mcp_sectors import maybe_sectors_mcp_toolset
from .tools.web_tools import web_search

logger = logging.getLogger(__name__)

MAX_ADVERSARIAL_ITERATIONS = 4


def _deepseek_or_gemini(api_key: str | None = None, gemini_api_key: str | None = None):
    """Main LLM: minimax-m3-free preferred, then Spark, then DeepSeek, then Gemini."""
    # 0a. Explicit opencode-go (Muse Spark 1.3 via Responses API, Hermes-style)
    if os.getenv("ADK_PROVIDER", "").lower() in ("opencode-go", "opencode", "opengo", "spark-1.3", "spark13"):
        from .providers import spark13_model

        return spark13_model()
    # 0. Prefer minimax/minimax-m3-free via CommandCode (free tier, requested)
    if os.getenv("ADK_PROVIDER", "").lower() in ("minimax", "minimax-m3-free", "minimax/minimax-m3-free"):
        try:
            from .providers import minimax_model

            return minimax_model()
        except Exception as e:
            logger.info("minimax-m3-free not available (%s), trying Spark", e)
    # Also try minimax first if COMMANDCODE_API_KEY exists (free, no bridge needed)
    _has_cc_key = bool(os.getenv("COMMANDCODE_API_KEY") or _has_commandcode_key_on_disk())
    if _has_cc_key:
        try:
            from .providers import minimax_model

            return minimax_model()
        except Exception as e:
            logger.info("minimax auto-prefer failed (%s), trying Spark", e)
    # 1. Prefer Muse Spark via CommandCode bridge
    try:
        return spark_model()
    except Exception as e:
        logger.info("Spark bridge not available (%s), trying DeepSeek/Gemini", e)
    deepseek_key = api_key or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    if deepseek_key:
        try:
            return deepseek_model(api_key=deepseek_key)
        except Exception as e:
            logger.warning("DeepSeek model init failed (%s), falling back to Gemini", e)
    # fallback
    gkey = gemini_api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
    if gkey:
        try:
            return gemini_model(api_key=gkey)
        except Exception as e:
            logger.warning("Gemini fallback also failed: %s", e)
            raise
    raise ValueError("No LLM key set — need ADK_PROVIDER=minimax or CommandCode bridge (BRIDGE_API_KEY), DEEPSEEK_API_KEY or GOOGLE_API_KEY")


def _has_commandcode_key_on_disk() -> bool:
    import pathlib, re as _re2

    p = pathlib.Path.home() / ".config" / "commandcode-bridge" / "env"
    if p.exists():
        try:
            return bool(_re2.search(r'COMMANDCODE_API_KEY="[^"]+"', p.read_text()))
        except Exception:
            pass
    return False


def _function_tools() -> list[Any]:
    return [FunctionTool(func) for func in DETERMINISTIC_TOOLS] + [FunctionTool(exit_loop)]


def _assumptions_block(ticker: str) -> str:
    """Server-side assumptions injection (AGY audit 2026-09-05, F4).

    Agents have no file-read tool, so the old "read data/assumptions/{T}.json"
    instruction was aspirational and the modeler silently invented beta/rf/erp.
    This loads the file HERE and pastes binding constraints into the prompt.
    Missing file → explicit loud banner, never silent defaults.
    """
    import json as _json
    from pathlib import Path as _Path

    t = (ticker or "").upper().strip()
    p = _Path(__file__).resolve().parents[2] / "data" / "assumptions" / f"{t}.json"
    if not p.exists():
        return (
            f"\n\nBINDING ASSUMPTIONS FOR {t}: NO data/assumptions/{t}.json EXISTS. "
            "You MUST derive beta/rf/erp/g from live collector data and disclose "
            "every parameter as estimated with its source — never present invented "
            "parameters as file-loaded.\n"
        )
    try:
        a = _json.loads(p.read_text())
    except Exception as e:
        return (
            f"\n\nBINDING ASSUMPTIONS FOR {t}: file exists but UNPARSEABLE ({e}). "
            "Treat as missing: derive + disclose per above.\n"
        )
    lines = [f"\n\nBINDING ASSUMPTIONS FOR {t} (from data/assumptions/{t}.json — these OVERRIDE your priors):"]
    for k in sorted(a.keys()):
        if k in ("source",):
            continue
        lines.append(f"- {k} = {a[k]}")
    if "beta_note" in a:
        lines.append(f"- beta_note: {a['beta_note']}")
    lines.append(
        "If live market data contradicts any value above (e.g. price moved), use the LIVE "
        "value for market figures but keep the STRUCTURAL parameters (beta/rf/erp/gate_primary) "
        "and disclose the deviation. Never silently substitute your own beta."
    )
    return "\n".join(lines) + "\n"


def _web_composite_tools() -> list[Any]:
    """Sectors search toolset — web_search only (Sectors-only rule, Sep 2026).

    web_extract + web_search_and_extract killed (arbitrary-URL fetching =
    external source). Agents cite Sectors urls; keyless runs get honest
    sectors_missing_key empties so the Critic rejects uncited claims.
    """
    return [FunctionTool(web_search)]


def build_graph(
    ticker: str = "BBCA",
    *,
    deepseek_api_key: str | None = None,
    gemini_api_key: str | None = None,
    sectors_api_key: str | None = None,
) -> SequentialAgent:
    """Build the full 11-agent Sequential graph. Returns the root SequentialAgent.

    Args:
        ticker: IDX ticker (bare, e.g. BBCA).
        deepseek_api_key: DeepSeek key override (else env).
        gemini_api_key: Gemini key override (else env, for search sub-agents).
        sectors_api_key: Sectors API key override (else SECTORS_API_KEY env).

    The root is a SequentialAgent so callers can run it via Runner/InMemorySession.
    """
    def _fmt(tmpl: str) -> str:
        # Safe ticker substitution — do NOT use str.format() because instruction
        # templates contain JSON examples with braces like {url, title, ...}
        return tmpl.replace("{ticker}", ticker)

    main_model = _deepseek_or_gemini(api_key=deepseek_api_key, gemini_api_key=gemini_api_key)
    ft = _function_tools()
    peer_tool = FunctionTool(request_peer_data)

    # Free-tier throttling: minimax-m3-free 503s on concurrency. When
    # ADK_PROVIDER indicates minimax and ADK_PARALLEL is unset/"0", run intake
    # + research sequentially so only 1 minimax call runs at a time
    # (minimax-m3-free 503s on concurrency).
    is_minimax = os.getenv("ADK_PROVIDER", "").lower() in ("minimax", "minimax-m3-free", "minimax/minimax-m3-free")
    _adk_parallel_val = os.getenv("ADK_PARALLEL", "")
    free_tier = bool(is_minimax and (_adk_parallel_val == "" or _adk_parallel_val == "0"))

    # -- Search sub-agents REMOVED (Sectors-only cleanup, 13 Sep 2026) --------
    # _build_search_subagent + news/social/industry_search_sub were orphans:
    # constructed but never attached to any agent (no AgentTool wiring) and
    # never in the graph dump. Parents (news_harvester, social_sentiment,
    # industry) call Sectors web_search directly. Instructions kept in
    # instructions.py as prompt reference.

    # -- MCP toolset (best-effort) -------------------------------------------
    sectors_toolset = maybe_sectors_mcp_toolset(api_key=sectors_api_key)
    if sectors_toolset is not None:
        logger.info("Sectors MCP toolset attached")
    else:
        logger.info("Sectors MCP skipped (no SECTORS_API_KEY)")

    # -- Leaf LlmAgents -------------------------------------------------------
    # Composite web tools (Sectors search + readability extract) attached to any
    # agent that needs fresh IDX data without Sectors MCP. Generated once and reused.
    composite_web_tools = _web_composite_tools()

    # Collector: Sectors financial FunctionTools always (keyless-honest),
    # plus Sectors MCP if present, else Sectors web_search backup.
    # (Previously empty tools caused LLM hallucination of tool names.)
    collector_tools: list[Any] = [FunctionTool(fn) for fn in SECTORS_FINANCIAL_TOOLS]
    if sectors_toolset is not None:
        collector_tools.append(sectors_toolset)
    else:
        collector_tools.extend(composite_web_tools)

    collector = LlmAgent(
        name="collector",
        model=main_model,
        description="Gathers IDX financials/segments/peers/filings via Sectors financial tools (+ MCP if keyed), else Sectors search.",
        instruction=_fmt(collector_instruction),
        tools=collector_tools,
        output_key="collector_output",
    )

    news_harvester = LlmAgent(
        name="news_harvester",
        model=main_model,
        description="Harvests last 30d IDX news (max 8, tier-filtered) via Sectors search.",
        instruction=_fmt(news_harvester_instruction),
        tools=composite_web_tools,
        output_key="news_output",
    )
    social_sentiment = LlmAgent(
        name="social_sentiment",
        model=main_model,
        description="Gauges retail crowd sentiment 0-100 from Sectors news + filings proxies.",
        instruction=_fmt(social_sentiment_instruction),
        tools=composite_web_tools,
        output_key="social_output",
    )

    modeler = LlmAgent(
        name="modeler",
        model=main_model,
        description="THE BRAIN — deterministic valuation via calc_* tools only.",
        instruction=_fmt(modeler_instruction) + _assumptions_block(ticker),
        tools=ft,
        output_key="valuation_output",
    )

    industry = LlmAgent(
        name="industry",
        model=main_model,
        description="Macro/industry thematics with url+date citations via Sectors.",
        instruction=_fmt(industry_instruction) + PEER_PROTOCOL,
        tools=[*composite_web_tools, peer_tool],
        output_key="industry_output",
    )

    analyst = LlmAgent(
        name="analyst",
        model=main_model,
        description="Company business + ops specs with source per exhibit.",
        instruction=_fmt(analyst_instruction) + PEER_PROTOCOL,
        tools=[peer_tool],
        output_key="analyst_output",
    )

    risk = LlmAgent(
        name="risk",
        model=main_model,
        description="4-7 pillar-specific risk buckets with impact/mitigant.",
        instruction=_fmt(risk_instruction) + PEER_PROTOCOL,
        tools=[peer_tool],
        output_key="risk_output",
    )

    kpi = LlmAgent(
        name="kpi",
        model=main_model,
        description="Operational KPIs per subsector (tenancy, fiber km, BOPD, MW, etc.).",
        instruction=_fmt(kpi_instruction) + PEER_PROTOCOL,
        tools=[peer_tool],
        output_key="kpi_output",
    )

    writer = LlmAgent(
        name="writer",
        model=main_model,
        description="Investment thesis — 4 bullets, every number cited from valuation/kpi.",
        instruction=_fmt(writer_instruction) + _assumptions_block(ticker),
        output_key="writer_output",
    )

    visualizer = LlmAgent(
        name="visualizer",
        model=main_model,
        description="7 mandatory charts with Source per exhibit.",
        instruction=_fmt(visualizer_instruction),
        output_key="visuals_output",
    )

    sotp_agent = LlmAgent(
        name="sotp",
        model=main_model,
        description="SOTP aggregator — 4 pillars, peer multiples, holdco discount (skip if single).",
        instruction=_fmt(sotp_instruction),
        tools=[FunctionTool(calc) for calc in DETERMINISTIC_TOOLS if calc.__name__ in ("calc_sotp", "calc_multiples")],
        output_key="sotp_output",
    )

    adversarial = LlmAgent(
        name="adversarial",
        model=main_model,
        description="Red Team — challenges one claim per iteration, defender must evidence or concede.",
        instruction=_fmt(adversarial_instruction),
        tools=[FunctionTool(exit_loop), FunctionTool(submit_debate)]
        + [
            FunctionTool(calc)
            for calc in DETERMINISTIC_TOOLS
            if calc.__name__
            in (
                "calc_wacc",
                "calc_dcf",
                "calc_ddm",
                "calc_multiples",
                "calc_blended",
                "calc_historical_bands",
            )
        ],
        output_key="debate_output",
    )

    critic = LlmAgent(
        name="critic",
        model=main_model,
        description="QA arbiter — REJECT on any mismatch, PASS when institutional-grade.",
        instruction=_fmt(critic_instruction),
        output_key="critic_output",
    )

    # -- Workflow composition -------------------------------------------------
    # Parallel 1: Collector + News + Social (all blocking inputs to Modeler)
    if free_tier:
        # Sequential for free tier: avoids 3 concurrent minimax calls that 503.
        # Keep name 'intake_parallel' so state/output_keys unchanged.
        intake_parallel = SequentialAgent(
            name="intake_parallel",
            sub_agents=[collector, news_harvester, social_sentiment],
            description="Sequential intake (free-tier throttling): collector → news → social.",
        )
        research_parallel = SequentialAgent(
            name="research_parallel",
            sub_agents=[analyst, industry, risk, kpi],
            description="Sequential research (free-tier throttling): analyst → industry → risk → kpi.",
        )
    else:
        intake_parallel = ParallelAgent(
            name="intake_parallel",
            sub_agents=[collector, news_harvester, social_sentiment],
            description="Parallel intake: collector + news + social.",
        )
        # Parallel 2: Analyst + Industry + Risk + KPI (all after Modeler)
        research_parallel = ParallelAgent(
            name="research_parallel",
            sub_agents=[analyst, industry, risk, kpi],
            description="Parallel research: analyst + industry + risk + KPI.",
        )

    # Adversarial loop — hard cap 4 iterations, exits via exit_loop tool
    adversarial_loop = LoopAgent(
        name="adversarial_loop",
        sub_agents=[adversarial],
        max_iterations=MAX_ADVERSARIAL_ITERATIONS,
        description="Red Team loop — max 4 iterations, exit_loop to stop early.",
    )

    # Root Sequential graph
    root = SequentialAgent(
        name="equity_report_orchestrator",
        sub_agents=[
            intake_parallel,
            modeler,
            research_parallel,
            writer,
            visualizer,
            sotp_agent,
            adversarial_loop,
            critic,
        ],
        description="Institutional equity report — 11 agents, Sequential + Parallel + Loop(max=4), ADK Python + MCP.",
    )

    return root


# Convenience: export root for adk CLI discovery (adk run / adk web expects `root_agent`)
def get_root_agent(ticker: str = "BBCA") -> SequentialAgent:
    return build_graph(ticker=ticker)


# Default root for `adk run` / `adk web` when ADK scans the module for `root_agent`
try:
    root_agent = build_graph()
except Exception as _e:
    # Allow import without keys (e.g. in CI/tests) — tests construct with explicit keys
    logger.warning("root_agent not built at import (missing keys?): %s", _e)
    root_agent = None  # type: ignore[assignment]

__all__ = [
    "MAX_ADVERSARIAL_ITERATIONS",
    "build_graph",
    "get_root_agent",
    "root_agent",
]
