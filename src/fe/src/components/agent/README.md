# Agent Visualization Components (Lane A)

Components and hooks for visualizing ADK agent execution progress, live agent activity statuses, rolling throughput, and honest ETAs on the `/agent` trace route.

## State Machine

Each agent transitions through the following four lifecycle states:

```
[ idle ] (queued / gray dot)
   │
   ▼ (event authored within last 8s)
[ running ] (amber pulsing dot)
   │
   ├─► [ error ] (event_type === "error" / red dot)
   │
   ▼ (transfer_to away OR age > 8s OR "done" frame received)
[ finished ] (green check dot)
```

- **`idle`**: Agent has not authored any events in the current execution run.
- **`running`**: Agent authored an event within the last 8 seconds while run is active and has not transferred execution away.
- **`finished`**: Agent emitted completion output / transferred to another agent, or pipeline reached the `done` event.
- **`error`**: Agent authored an event frame with `event_type === "error"`.

## Component & Hook Props

### `useAgentProgress(props: UseAgentProgressProps)`
- **Inputs**: `events: TraceEvent[]`, `running: boolean`, `done: DonePayload | null`, `error?: string | null`
- **Outputs**:
  - `activeCount`: number of currently running agents (`X`).
  - `totalCount`: total known agents in `AGENT_META_MAP` (`Y = 16`).
  - `agentStatuses`: `Record<string, "idle" | "running" | "finished" | "error">`.
  - `etaText`: computed from rolling throughput of last 10 events (shows `"—"` until ≥5 events).
  - `isInterrupted`: boolean flag indicating stream closure before `done`.

### `<AgentRail ... />`
- `agentStatuses`: status map from `useAgentProgress`.
- `selectedAuthor?`: active filter author key.
- `onFilterAuthor?`: callback when an agent node is clicked.
- `knownAgents?`: ordered array of agent metadata with phase tags.

### `<ProgressHeader ... />`
- Renders ticker controls, run actions, bridge health badges, live status pill (`X / Y agents active · N events · ETA ...`), and embeds `<AgentRail />`.

## State / Function Components (Lane B)
- **`StatePreview.tsx`**: Real-time state preview card displaying all accumulated state keys across streaming events, sorted by recency. Supports expanding keys to view up to 4000 characters of formatted JSON/string values, detects missing state deltas with subtle hints, and computes total state memory footprint footer.
- **`useStatePreview.ts`**: Custom hook aggregating `state_delta` and `state_delta_keys` across trace events, tracking byte sizes, type tags (`[object:3.2kb]`, `[array:1.5kb]`, etc.), and sorting keys most-recently-written first.
- **`FunctionCallCard.tsx`**: Collapsible card in amber-50/200 styling displaying tool invocations with Wrench icon, payload byte size, and full expandable arguments preview up to 8000 characters.
- **`FunctionResponseCard.tsx`**: Collapsible card in emerald-50/200 styling displaying tool returns with CornerDownLeft icon, response byte size, and full expandable return data preview up to 6000 characters.
