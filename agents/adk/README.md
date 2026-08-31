# T05 — ADK Python+MCP scaffold

## Run

```bash
pip install -r agents/adk/requirements.txt
# requires: google-adk==2.8.0, mcp>=1.24,<2, litellm, google-genai
export DEEPSEEK_API_KEY=sk-...
export GOOGLE_API_KEY=...        # for search-grounded sub-agents (Gemini)
export SECTORS_API_KEY=...       # for Sectors MCP (Bearer, optional — graph runs without it)

# One-shot via Runner (no adk CLI needed, no browser):
PYTHONPATH=. python -c "
import asyncio
from agents.adk.runner import run_report
print(asyncio.run(run_report(ticker='BBCA')))
"

# Or ADK web UI:
adk web agents/adk --port 8080
```

## Layout

```
agents/adk/
  app.py              # build_graph() → Sequential( intake_parallel → modeler → research_parallel → writer → visualizer → sotp → adversarial_loop(max=4) → critic )
  runner.py           # run_report(ticker) via Runner + InMemorySessionService
  requirements.txt    # google-adk==2.8.0 + mcp + litellm
  agents/
    instructions.py   # 11 agent prompts (collector, news, social, modeler, analyst, industry, risk, kpi, writer, visualizer, sotp, adversarial, critic)
  providers/
    __init__.py       # deepseek_model() via LiteLlm(openai/deepseek-chat, api_base=https://api.deepseek.com/v1), gemini_model() via Gemini
  tools/
    finance_tools.py  # DETERMINISTIC_TOOLS: calc_wacc/dcf/ddm/multiples/ggm/sotp/blended/bands/ratios (FunctionTool wrappers)
    mcp_sectors.py    # sectors_mcp_toolset() via McpToolset(StreamableHTTPConnectionParams(url=https://sectors-mcp.supertype.ai/mcp, headers={Authorization: Bearer <key>}))
  tests/
    test_adk_scaffold.py  # 17 tests (finance math + provider + graph structure + MCP wiring) — green

agents/stubs/         # thin re-exports so other lanes can import agents.<name> without ADK
```

## Graph

```
collector ─┐
news ──────┤ Parallel(intake) ─┬─► modeler ─┬─► analyst ─┐
social ────┘                   │  (calc_*)  │   industry ├─ Parallel(research) ─► writer ─► visualizer ─► sotp ─► adversarial_loop(max=4) ─► critic
                                    ▲                   │   risk     │
                                    └───────────────────┘   kpi      ┘
```

* Search isolation: news/social/industry route Google Search via AgentTool(search_subagent with GoogleSearchTool) — genai forbids GoogleSearch + FunctionTool in the same LlmAgent.
* Modeler is the only agent with FunctionTools (calc_wacc, calc_dcf, ... + exit_loop for adversarial).
* Adversarial loop exits via exit_loop tool (sets escalate=true); LoopAgent hard-caps at 4.
* MCP is best-effort: maybe_sectors_mcp_toolset() returns None without SECTORS_API_KEY so tests/CI never need a live key.

## Contracts

* 11 LlmAgents, 2 ParallelAgents, 1 LoopAgent(max=4), 1 SequentialAgent root.
* Provider: DeepSeek deepseek-chat (LiteLlm, api_base https://api.deepseek.com/v1, strip <think> tags) or Gemini for search sub-agents.
* MCP: StreamableClientTransport / StreamableHTTPConnectionParams pattern (not SseClientTransport).
* Task branch: wt/t05-adk off feat/institutional-report
