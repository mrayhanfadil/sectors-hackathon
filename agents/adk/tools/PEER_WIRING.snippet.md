# PEER_WIRING Snippet — Bounded Inter-Agent Comms (max 3)

This snippet provides the exact wiring for bounded peer communications (`request_peer_data`) across the research agents (`analyst`, `industry`, `risk`, `kpi`).

> **Note for Orchestrator / Lane A (`app.py` owner):**
> Follow the two parts below to wire `request_peer_data` into `agents/adk/app.py`.

---

## Part (a): Import + Function-Tool Wrapper

In `agents/adk/app.py`:

### 1. Import `request_peer_data`

Add import from `agents.adk.tools.peer_tools`:

```python
from agents.adk.tools.peer_tools import request_peer_data
```

### 2. Wrap as FunctionTool

In `build_graph()` or toolset definition in `agents/adk/app.py`:

```python
peer_tool = FunctionTool(request_peer_data)
```

### 3. Attach `peer_tool` to Research Agents

Attach `peer_tool` to `analyst`, `industry`, `risk`, and `kpi` agents:

```python
analyst = LlmAgent(
    name="analyst",
    model=main_model,
    description="Company business + ops specs with source per exhibit.",
    instruction=_fmt(analyst_instruction),
    tools=[peer_tool],
    output_key="analyst_output",
)

industry = LlmAgent(
    name="industry",
    model=main_model,
    description="Macro/industry thematics with url+date citations via Tavily + readability.",
    instruction=_fmt(industry_instruction),
    tools=[*composite_web_tools, peer_tool],
    output_key="industry_output",
)

risk = LlmAgent(
    name="risk",
    model=main_model,
    description="4-7 pillar-specific risk buckets with impact/mitigant.",
    instruction=_fmt(risk_instruction),
    tools=[peer_tool],
    output_key="risk_output",
)

kpi = LlmAgent(
    name="kpi",
    model=main_model,
    description="Operational KPIs per subsector (tenancy, fiber km, BOPD, MW, etc.).",
    instruction=_fmt(kpi_instruction),
    tools=[peer_tool],
    output_key="kpi_output",
)
```

---

## Part (b): Instruction Paragraph for Research Prompts

Add this exact instruction paragraph to the prompt instructions of `analyst`, `industry`, `risk`, and `kpi` (in `agents/adk/agents/instructions.py` or wherever prompt strings are loaded):

```
PEER REQUEST PROTOCOL:
Kalau field dari agent lain kosong: (1) cek state dulu, (2) panggil request_peer_data SEKALI per field-set dengan alasan, (3) kalau peer_requests sudah 3 → lanjut dengan data seadanya + tulis provenance gap. DILARANG request tanpa needed_fields.
```

Rules enforced:
1. **Mandatory `needed_fields` + `reason`**: Requests without specific needed fields or justification reasons will fail validation or be rejected by the Critic.
2. **3rd-Strike Fallback (`proceed-with-gaps`)**: Once `peer_requests` hits the limit of 3, further requests are blocked (`status='rejected'`). Agents must proceed with available data and explicitly document the gap and its provenance.

---

## Note on Critic Audit Rule (Task 5)

`critic_instruction` in `agents/adk/agents/instructions.py` has been updated with:
```
- Peer requests justified? (flag/REJECT any peer_requests entry without explicit reason/justification or with empty fields)
```
If your orchestrator overrides `critic_instruction` inside `app.py`, ensure this check is present in the Critic prompt.
