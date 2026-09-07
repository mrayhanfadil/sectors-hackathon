import { useState, useEffect, useMemo } from "react"

export type AgentStatus = "idle" | "running" | "finished" | "error"

export interface AgentMeta {
  key: string
  label: string
  phase: string
  color: string
}

export interface TraceEvent {
  seq: number
  ts: number
  author: string
  node: string
  branch?: string | null
  event_type: string
  text: string
  function_calls: { name: string; args: Record<string, unknown>; id: string }[]
  function_responses: { name: string; response: unknown; id: string }[]
  state_delta_keys: string[]
  state_delta?: Record<string, unknown> | null
  transfer_to?: string | null
}

export const AGENT_META_MAP: Record<string, { label: string; phase: string; color: string }> = {
  collector: { label: "Collector", phase: "Intake", color: "bg-sky-100 text-sky-800 border-sky-300" },
  news_harvester: { label: "News Harvester", phase: "Intake", color: "bg-amber-100 text-amber-800 border-amber-300" },
  social_sentiment: { label: "Social Sentiment", phase: "Intake", color: "bg-violet-100 text-violet-800 border-violet-300" },
  news_search_sub: { label: "News Search Sub", phase: "Intake Search", color: "bg-amber-50 text-amber-800 border-amber-200" },
  social_search_sub: { label: "Social Search Sub", phase: "Intake Search", color: "bg-violet-50 text-violet-800 border-violet-200" },
  modeler: { label: "Modeler", phase: "Valuation", color: "bg-emerald-100 text-emerald-800 border-emerald-400 font-semibold" },
  analyst: { label: "Analyst", phase: "Research", color: "bg-neutral-100 text-neutral-800 border-neutral-300" },
  industry: { label: "Industry", phase: "Research", color: "bg-teal-100 text-teal-800 border-teal-300" },
  industry_search_sub: { label: "Industry Search Sub", phase: "Research Search", color: "bg-emerald-50 text-emerald-800 border-emerald-200" },
  risk: { label: "Risk", phase: "Research", color: "bg-red-100 text-red-800 border-red-300" },
  kpi: { label: "KPI", phase: "Research", color: "bg-cyan-100 text-cyan-800 border-cyan-300" },
  writer: { label: "Writer", phase: "Narrative", color: "bg-indigo-100 text-indigo-800 border-indigo-300" },
  visualizer: { label: "Visualizer", phase: "Charts", color: "bg-pink-100 text-pink-800 border-pink-300" },
  sotp: { label: "SOTP", phase: "Aggregation", color: "bg-orange-100 text-orange-800 border-orange-300" },
  adversarial: { label: "Adversarial", phase: "Red Team", color: "bg-rose-100 text-rose-800 border-rose-300" },
  critic: { label: "Critic", phase: "QA", color: "bg-neutral-900 text-white border-neutral-900" },
}

export const KNOWN_AGENTS: AgentMeta[] = Object.entries(AGENT_META_MAP).map(([key, meta]) => ({
  key,
  label: meta.label,
  phase: meta.phase,
  color: meta.color,
}))

export interface UseAgentProgressProps {
  events: TraceEvent[]
  running: boolean
  done: { n_events: number; state_keys: string[]; ms: number } | null
  error?: string | null
}

export interface UseAgentProgressReturn {
  activeCount: number
  totalCount: number
  completedCount: number
  errorCount: number
  agentStatuses: Record<string, AgentStatus>
  agentLastSeen: Record<string, number>
  etaText: string
  eventsCount: number
  throughputRate: number
  isInterrupted: boolean
  knownAgents: AgentMeta[]
}

export function useAgentProgress({
  events,
  running,
  done,
  error,
}: UseAgentProgressProps): UseAgentProgressReturn {
  const [now, setNow] = useState<number>(() => Date.now())

  // Keep a 1-second interval while running so the 8s sliding window evaluates dynamically
  useEffect(() => {
    if (!running) return
    const interval = setInterval(() => {
      setNow(Date.now())
    }, 1000)
    return () => clearInterval(interval)
  }, [running])

  const { agentStatuses, agentLastSeen, activeCount, completedCount, errorCount } = useMemo(() => {
    const statuses: Record<string, AgentStatus> = {}
    const lastSeen: Record<string, number> = {}

    // Group events by author
    const eventsByAuthor: Record<string, TraceEvent[]> = {}
    for (const ev of events) {
      if (!ev.author) continue
      if (!eventsByAuthor[ev.author]) {
        eventsByAuthor[ev.author] = []
      }
      eventsByAuthor[ev.author].push(ev)
      lastSeen[ev.author] = Math.max(lastSeen[ev.author] || 0, ev.ts)
    }

    const nowSec = now / 1000

    for (const agent of KNOWN_AGENTS) {
      const key = agent.key
      const agentEvents = eventsByAuthor[key]

      if (!agentEvents || agentEvents.length === 0) {
        statuses[key] = "idle"
        continue
      }

      // Check if any error event occurred
      const hasError = agentEvents.some((e) => e.event_type === "error")
      if (hasError) {
        statuses[key] = "error"
        continue
      }

      // If run has finished with done frame
      if (done !== null) {
        statuses[key] = "finished"
        continue
      }

      // If currently running, apply the 8s heuristic and transfer detection
      if (running) {
        const lastEv = agentEvents[agentEvents.length - 1]
        const lastTs = lastEv.ts || nowSec
        const ageSec = Math.max(0, nowSec - lastTs)

        // If explicitly transferred away to another agent
        const hasTransferredAway = Boolean(lastEv.transfer_to && lastEv.transfer_to !== key)

        if (hasTransferredAway) {
          statuses[key] = "finished"
        } else if (ageSec <= 8) {
          statuses[key] = "running"
        } else {
          statuses[key] = "finished"
        }
      } else {
        // Run is not active and not officially done (stopped/idle/interrupted)
        statuses[key] = "finished"
      }
    }

    let active = 0
    let completed = 0
    let errs = 0

    for (const status of Object.values(statuses)) {
      if (status === "running") active += 1
      else if (status === "finished") completed += 1
      else if (status === "error") errs += 1
    }

    return {
      agentStatuses: statuses,
      agentLastSeen: lastSeen,
      activeCount: active,
      completedCount: completed,
      errorCount: errs,
    }
  }, [events, running, done, now])

  // Rolling ETA computation over the last 10 events
  const { etaText, throughputRate } = useMemo(() => {
    if (events.length < 5) {
      return { etaText: "-", throughputRate: 0 }
    }

    if (done !== null) {
      return { etaText: "0s", throughputRate: 0 }
    }

    if (!running) {
      return { etaText: "-", throughputRate: 0 }
    }

    const windowSize = Math.min(10, events.length)
    const windowEvents = events.slice(-windowSize)
    const firstTs = windowEvents[0].ts
    const lastTs = windowEvents[windowEvents.length - 1].ts

    const durationSec = Math.max(1, lastTs - firstTs)
    const currentRate = Math.max(0.1, windowEvents.length / durationSec)

    // Estimate remaining events based on uncompleted agents and typical 35-event pipeline
    const uncompletedAgents = KNOWN_AGENTS.filter(
      (a) => agentStatuses[a.key] !== "finished" && agentStatuses[a.key] !== "error"
    ).length

    const estRemainingEvents = Math.max(
      1,
      Math.max(35 - events.length, uncompletedAgents * 2.2)
    )

    const estSec = Math.max(1, Math.round(estRemainingEvents / currentRate))

    if (estSec < 60) {
      return { etaText: `${estSec}s`, throughputRate: currentRate }
    }

    const mins = Math.floor(estSec / 60)
    const secs = estSec % 60
    return { etaText: `${mins}m ${secs}s`, throughputRate: currentRate }
  }, [events, done, running, agentStatuses])

  const isInterrupted = !running && done === null && events.length > 0 && !error

  return {
    activeCount,
    totalCount: KNOWN_AGENTS.length,
    completedCount,
    errorCount,
    agentStatuses,
    agentLastSeen,
    etaText,
    eventsCount: events.length,
    throughputRate,
    isInterrupted,
    knownAgents: KNOWN_AGENTS,
  }
}
