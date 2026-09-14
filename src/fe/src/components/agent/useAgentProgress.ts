import { useState, useEffect, useMemo } from "react"
import { AGENT_FRIENDLY_MAP, type TraceEvent } from "./AGENT_FRIENDLY_META"
export type { TraceEvent }

export type AgentStatus = "idle" | "running" | "finished" | "error"

export interface AgentMeta {
  key: string
  label: string
  phase: string
  color: string
}

export const AGENT_META_MAP: Record<string, { label: string; phase: string; color: string }> = {
  collector: { label: "Pencari data", phase: "Ambil data", color: "bg-sky-50 text-sky-800 border-sky-200" },
  news_harvester: { label: "Pencari berita", phase: "Ambil data", color: "bg-amber-50 text-amber-800 border-amber-200" },
  news_search_sub: { label: "Pencari berita (sub)", phase: "Cari data", color: "bg-amber-50 text-amber-700 border-amber-200" },
  modeler: { label: "Ahli valuasi", phase: "Hitung nilai", color: "bg-emerald-50 text-emerald-800 border-emerald-300 font-medium" },
  analyst: { label: "Analis fundamental", phase: "Riset", color: "bg-[#F5F2EB] text-[#1C1B17] border-[#E7E3DA]" },
  industry: { label: "Analis industri", phase: "Riset", color: "bg-teal-50 text-teal-800 border-teal-200" },
  industry_search_sub: { label: "Riset industri (sub)", phase: "Cari riset", color: "bg-teal-50 text-teal-700 border-teal-200" },
  risk: { label: "Analis risiko", phase: "Riset", color: "bg-rose-50 text-rose-800 border-rose-200" },
  kpi: { label: "Analis KPI", phase: "Riset", color: "bg-cyan-50 text-cyan-800 border-cyan-200" },
  writer: { label: "Penulis laporan", phase: "Tulis laporan", color: "bg-indigo-50 text-indigo-800 border-indigo-200" },
  visualizer: { label: "Visualisasi data", phase: "Grafik", color: "bg-pink-50 text-pink-800 border-pink-200" },
  sotp: { label: "Valuasi SOTP", phase: "Gabung nilai", color: "bg-orange-50 text-orange-800 border-orange-200" },
  adversarial: { label: "Penguji kritis", phase: "Uji silang", color: "bg-red-50 text-red-800 border-red-200" },
  critic: { label: "Peninjau mutu", phase: "Periksa akhir", color: "bg-[#0E6E63]/10 text-[#0E6E63] border-[#0E6E63]/25" },
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

  // Interval 1s saat proses berjalan agar kalkulasi dinamis
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

    // Kelompokkan event berdasarkan author
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

      // Periksa apakah ada event error
      const hasError = agentEvents.some((e) => e.event_type === "error")
      if (hasError) {
        statuses[key] = "error"
        continue
      }

      // Jika alur kerja sudah selesai
      if (done !== null) {
        statuses[key] = "finished"
        continue
      }

      // Jika alur kerja sedang berjalan
      if (running) {
        const lastEv = agentEvents[agentEvents.length - 1]
        const lastTs = lastEv.ts || nowSec
        const ageSec = Math.max(0, nowSec - lastTs)

        // Deteksi serah terima tugas
        const hasTransferredAway = Boolean(lastEv.transfer_to && lastEv.transfer_to !== key)

        if (hasTransferredAway) {
          statuses[key] = "finished"
        } else if (ageSec <= 8) {
          statuses[key] = "running"
        } else {
          statuses[key] = "finished"
        }
      } else {
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

  // Estimasi sisa waktu
  const { etaText, throughputRate } = useMemo(() => {
    if (events.length < 5) {
      return { etaText: "-", throughputRate: 0 }
    }

    if (done !== null) {
      return { etaText: "0 detik", throughputRate: 0 }
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

    const uncompletedAgents = KNOWN_AGENTS.filter(
      (a) => agentStatuses[a.key] !== "finished" && agentStatuses[a.key] !== "error"
    ).length

    const estRemainingEvents = Math.max(
      1,
      Math.max(35 - events.length, uncompletedAgents * 2.2)
    )

    const estSec = Math.max(1, Math.round(estRemainingEvents / currentRate))

    if (estSec < 60) {
      return { etaText: `${estSec} detik`, throughputRate: currentRate }
    }

    const mins = Math.floor(estSec / 60)
    const secs = estSec % 60
    return { etaText: `${mins} menit ${secs} detik`, throughputRate: currentRate }
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
