# Recipe 03 — Multi-Agent Workflows for Financial Research

> Source: <https://docs.sectors.app/recipes/generative-ai-python/03-multiagent-workflows>
> By: Billy Samuel, Andreas Christianto · March 5, 2026

## What this chapter teaches

Move from a single-agent RAG system to a **multi-agent orchestration** with two key patterns:
1. **Sequential chain** — output of one specialized agent feeds into the next
2. **Judge-critic loop** — third agent evaluates output and demands revisions

Used together: a robust, self-improving financial research pipeline.

## Why this matters

Single-agent systems struggle with reliability as tasks become multi-step. Multi-agent design:
- Decomposes complexity into narrow responsibilities
- Reduces hallucinations (each agent has a tight prompt)
- Enables self-correction (judge-critic loop)

## The 3 agents

```python
from openai_agents import Agent, Runner, function_tool

screener_agent = Agent(
    name="IDX Screener",
    instructions=(
        "Screen IDX companies by calling find_companies_screener. "
        "Return ONLY a Python list of clean ticker symbols without .JK suffix. "
        "Example: ['BBCA', 'BBRI', 'TLKM']"
    ),
    tools=[find_companies_screener],
    model="gpt-4o-mini",
)

researcher_agent = Agent(
    name="IDX Researcher",
    instructions=(
        "For each ticker, call get_company_overview to gather data. "
        "Return ONLY a raw JSON object with 'metric_fields' and 'results' array. "
        "Do not use markdown fences."
    ),
    tools=[get_company_overview],
    model="gpt-4o",
)

evaluator_agent = Agent(
    name="Evaluator",
    instructions=(
        "Grade the JSON. Check: (1) every result has ticker + company_name, "
        "(2) metric fields contain non-null numeric values. "
        "Score 'pass' if all checks pass."
    ),
    model="gpt-4o-mini",
    output_type=EvaluationFeedback,
)
```

## Tools (Sectors wrappers)

```python
@function_tool
def find_companies_screener(order_by: str, limit: int, where: str = "") -> str:
    """Screen IDX companies via Sectors v2 API."""
    params = [f"order_by={requests.utils.quote(order_by)}", f"limit={limit}"]
    if where:
        params.insert(0, f"where={requests.utils.quote(where.strip())}")
    url = f"https://api.sectors.app/v2/projects/?{url}"
    response = requests.get(url, headers={"Authorization": SECTORS_API_KEY})
    return json.dumps(response.json())

@function_tool
def get_company_overview(ticker: str) -> str:
    """Get company overview + financials for IDX ticker."""
    url = f"https://api.sectors.app/v2/company/report/{ticker}/?sections=overview,financials"
    response = requests.get(url, headers=HEADERS)
    return json.dumps(response.json())
```

## Orchestration pattern

```python
async def research_workflow(user_query: str, max_revisions: int = 3):
    # Step 1: screener returns tickers
    ticker_list = await Runner.run(screener_agent, user_query)

    # Step 2: researcher fetches data for each ticker
    research_output = await Runner.run(
        researcher_agent,
        f"Query: {user_query}\nTickers: {ticker_list}"
    )

    # Step 3: judge-critic loop
    for _ in range(max_revisions):
        evaluation = await Runner.run(evaluator_agent, research_output)
        if evaluation.score == "pass":
            break
        research_output = await Runner.run(
            researcher_agent,
            f"{research_output}\n\nFix: {evaluation.feedback}"
        )
    return research_output
```

## Hackathon applicability

- **AI Agents & Assistants track (primary)** — this is the gold standard for production-grade IDX research agents.
- **Market Intelligence** — turn the screener into a daily-ranker agent that emails a ranked list every morning.
- Less applicable for Automation (the multi-step flow is more conversational than scheduled).

## When to use this vs single-agent (recipe 02)

| Use single-agent (recipe 02) | Use multi-agent (recipe 03) |
|---|---|
| Query is simple, 1-2 tool calls | Query needs screener → data → validation |
| Tolerate occasional hallucinations | Need reliable, audit-able outputs |
| Latency matters (10s budget) | Quality > latency (60s budget OK) |
| MVP / prototype | Production / demo |

## Pitfalls

- **Cost** — judge-critic loop can run 3-4 times = 3-4× LLM cost.
- **Latency** — 3+ agents in series = 15-30s typical.
- **JSON parsing brittleness** — researcher_agent must return clean JSON (no markdown fences). Add explicit schema validation.
- **Credit budget** — every get_company_overview call = 1 credit. Cache by ticker for 24h.

## See also

- `references/mcp/setup.md` — multi-agent orchestration is simpler with MCP servers + LangGraph's `MultiServerMCPClient`.
- `references/cookbook/04-structured-output.md` — extract generated for full Pydantic schema pattern.
