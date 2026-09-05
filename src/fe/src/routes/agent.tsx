import { createFileRoute } from "@tanstack/react-router"
import { useEffect, useRef, useState, useCallback, useMemo } from "react"
import {
  Bot,
  Play,
  RotateCcw,
  Loader2,
  AlertCircle,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Cpu,
  RefreshCw,
  Clock,
  Activity,
  Code2,
  HelpCircle,
  Zap,
  Database,
  Square,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useAgentProgress } from "@/components/agent/useAgentProgress"
import { PhaseTimeline } from "@/components/agent/PhaseTimeline"
import { PlainEnglishPanel } from "@/components/agent/PlainEnglishPanel"
import { SummaryCard } from "@/components/agent/SummaryCard"
import { RunHistoryPanel } from "@/components/agent/RunHistoryPanel"
import { StatePreview } from "@/components/agent/StatePreview"
import { FunctionCallCard } from "@/components/agent/FunctionCallCard"
import { FunctionResponseCard } from "@/components/agent/FunctionResponseCard"
import { type TraceEvent } from "@/components/agent/AGENT_FRIENDLY_META"
import { SUPPORTED_TICKERS, normalizeTicker } from "@/components/agent/tickers"

interface AgentSearchParams {
  ticker?: string
}

export const Route = (createFileRoute as any)("/agent")({
  validateSearch: (search: Record<string, unknown>): AgentSearchParams => {
    return {
      ticker: typeof search.ticker === "string" ? search.ticker : undefined,
    }
  },
  component: AgentTrace,
})

interface HealthInfo {
  ok?: boolean
  model?: string
  provider?: string
  elapsed_ms?: number
  bridge_ping?: string
  bridge_error?: string
  graph?: { name: string; n_subagents?: number; subagents?: string[] }
}

function normalizeEvents(rawEvents: any[]): TraceEvent[] {
  if (!Array.isArray(rawEvents)) return []
  return rawEvents.map((ev: any) => ({
    seq: ev.seq ?? 0,
    ts: ev.ts ?? (ev.payload?.ts || Date.now() / 1000),
    author: ev.author || ev.payload?.author || "",
    node: ev.node || ev.payload?.node || "",
    branch: ev.branch || ev.payload?.branch || null,
    event_type: ev.event_type || ev.payload?.event_type || "message",
    text: ev.text ?? ev.payload?.text ?? "",
    function_calls: ev.function_calls || ev.payload?.function_calls || [],
    function_responses: ev.function_responses || ev.payload?.function_responses || [],
    state_delta_keys:
      ev.state_delta_keys ||
      (ev.payload?.state_delta && typeof ev.payload.state_delta === "object"
        ? Object.keys(ev.payload.state_delta)
        : []),
    state_delta: ev.state_delta || ev.payload?.state_delta || null,
    transfer_to: ev.transfer_to || ev.payload?.transfer_to || null,
  }))
}

function formatRelativeTime(ts: number | undefined | null): string {
  if (!ts) return "baru saja"
  const now = Date.now() / 1000
  const diff = Math.max(0, Math.floor(now - ts))
  if (diff < 60) return "baru saja"
  if (diff < 3600) return `${Math.floor(diff / 60)} menit lalu`
  if (diff < 86400) return `${Math.floor(diff / 3600)} jam lalu`
  return `${Math.floor(diff / 86400)} hari lalu`
}

function AgentTrace() {
  const search = Route.useSearch() as AgentSearchParams
  const initialTicker = normalizeTicker(search?.ticker)
  const [ticker, setTicker] = useState<string>(initialTicker)
  const [events, setEvents] = useState<TraceEvent[]>([])
  const [running, setRunning] = useState(false)
  const [pollCount, setPollCount] = useState(0)
  const [done, setDone] = useState<{ n_events: number; state_keys: string[]; ms: number } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [health, setHealth] = useState<HealthInfo | null>(null)
  const [filterAuthor, setFilterAuthor] = useState<string>("all")
  const [rawDebugOpen, setRawDebugOpen] = useState(false)
  const [loadedFromDb, setLoadedFromDb] = useState<{
    run_id: string
    ticker: string
    status: string
    n_events: number
    started_at: number
    finished_at?: number | null
    error?: string | null
    reason?: string | null
  } | null>(null)
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const selectedRunIdRef = useRef<string | null>(null)
  useEffect(() => {
    selectedRunIdRef.current = selectedRunId
  }, [selectedRunId])
  const startRef = useRef<number>(0)
  const pollCleanupRef = useRef<(() => void) | null>(null)

  const apiBase = (import.meta as any).env?.VITE_API_URL || ""

  const stopPolling = useCallback(() => {
    if (pollCleanupRef.current) {
      pollCleanupRef.current()
      pollCleanupRef.current = null
    }
  }, [])

  useEffect(() => {
    return () => {
      stopPolling()
    }
  }, [stopPolling])

  const fetchHealth = useCallback(async () => {
    try {
      const r = await fetch(`${apiBase}/api/agent/health`)
      const j = await r.json()
      setHealth(j)
    } catch (e: unknown) {
      setHealth({ ok: false, bridge_error: String(e) })
    }
  }, [apiBase])

  useEffect(() => {
    fetchHealth()
  }, [fetchHealth])

  // Sync search param ticker with state if URL changes
  useEffect(() => {
    if (search?.ticker) {
      const t = normalizeTicker(search.ticker)
      setTicker((prev) => (prev !== t ? t : prev))
    }
  }, [search?.ticker])

  // Auto-load latest persisted run from SQLite on mount / ticker change
  useEffect(() => {
    let active = true
    const t = ticker.trim().toUpperCase() || "BBCA"

    if (running) return

    // If user explicitly selected a run and it's already loaded for this ticker, don't overwrite with latest
    if (
      selectedRunIdRef.current &&
      loadedFromDb?.run_id === selectedRunIdRef.current &&
      loadedFromDb?.ticker === t
    ) {
      return
    }

    async function loadLatestRun() {
      try {
        const r = await fetch(`${apiBase}/api/agent/runs/latest?ticker=${encodeURIComponent(t)}`)
        if (!active) return
        if (r.status === 200) {
          const j = await r.json()
          if (!active) return
          if (j && Array.isArray(j.events) && j.events.length > 0) {
            const normalizedEvents = normalizeEvents(j.events)
            setEvents(normalizedEvents)
            const isCompleted = j.status === "completed"
            if (isCompleted) {
              setDone({
                n_events: j.n_events || normalizedEvents.length,
                state_keys: j.state ? Object.keys(j.state) : [],
                ms:
                  j.finished_at && j.started_at
                    ? Math.max(0, Math.round((j.finished_at - j.started_at) * 1000))
                    : 0,
              })
            } else {
              setDone(null)
            }
            if (j.error) {
              setError(j.error)
            } else {
              setError(null)
            }
            setLoadedFromDb({
              run_id: j.run_id,
              ticker: j.ticker || t,
              status: j.status || "completed",
              n_events: j.n_events || normalizedEvents.length,
              started_at: j.started_at,
              finished_at: j.finished_at,
              error: j.error,
              reason: j.reason,
            })
            return
          }
        }
        if (active) {
          setLoadedFromDb(null)
        }
      } catch {
        if (active) {
          setLoadedFromDb(null)
        }
      }
    }

    loadLatestRun()
    return () => {
      active = false
    }
  }, [ticker, apiBase, running, loadedFromDb?.run_id, loadedFromDb?.ticker])

  const startPolling = useCallback(
    (runId: string, runTicker: string) => {
      stopPolling()
      let cancelled = false
      let consecutive404s = 0

      const pollStep = async () => {
        if (cancelled) return
        setPollCount((prev) => prev + 1)

        try {
          const statusRes = await fetch(
            `${apiBase}/api/agent/runs/${encodeURIComponent(runId)}/status`
          )

          if (cancelled) return

          if (statusRes.status === 404) {
            consecutive404s++
            if (consecutive404s > 5) {
              stopPolling()
              setRunning(false)
              setError(`Run ${runId} tidak ditemukan di server.`)
            }
            return
          }

          consecutive404s = 0

          if (!statusRes.ok) return

          const statusData = await statusRes.json()
          if (cancelled) return

          const currentStatus = statusData.status || "running"

          setLoadedFromDb((prev) => ({
            run_id: runId,
            ticker: statusData.ticker || runTicker,
            status: currentStatus,
            n_events: statusData.n_events || 0,
            started_at: statusData.started_at || prev?.started_at || Date.now() / 1000,
            finished_at: statusData.finished_at || null,
            error: statusData.reason || null,
            reason: statusData.reason || null,
          }))

          if (
            currentStatus === "completed" ||
            currentStatus === "failed" ||
            currentStatus === "interrupted"
          ) {
            stopPolling()
            setRunning(false)

            try {
              const fullRes = await fetch(
                `${apiBase}/api/agent/runs/${encodeURIComponent(runId)}`
              )
              if (fullRes.ok && !cancelled) {
                const fullData = await fullRes.json()
                const normalized = normalizeEvents(fullData.events || [])
                setEvents(normalized)

                if (currentStatus === "completed") {
                  setDone({
                    n_events: fullData.n_events || normalized.length,
                    state_keys: fullData.state ? Object.keys(fullData.state) : [],
                    ms:
                      fullData.finished_at && fullData.started_at
                        ? Math.max(
                            0,
                            Math.round((fullData.finished_at - fullData.started_at) * 1000)
                          )
                        : Date.now() - startRef.current,
                  })
                  setError(null)
                } else if (currentStatus === "failed") {
                  setDone(null)
                  setError(fullData.error || fullData.reason || "Analisis gagal diselesaikan.")
                } else {
                  setDone(null)
                  setError(
                    `Analisis terhenti (${fullData.reason || "interrupted"}). Klik "Jalankan Analisis" untuk melanjutkan.`
                  )
                }

                setLoadedFromDb({
                  run_id: fullData.run_id || runId,
                  ticker: fullData.ticker || runTicker,
                  status: currentStatus,
                  n_events: fullData.n_events || normalized.length,
                  started_at: fullData.started_at || statusData.started_at,
                  finished_at: fullData.finished_at || statusData.finished_at,
                  error: fullData.error || fullData.reason,
                  reason: fullData.reason || statusData.reason,
                })
              }
            } catch {
              // Full fetch fallback
            }
            return
          }

          // While running: fetch full events incrementally so the UI updates live
          if (currentStatus === "running") {
            try {
              const fullRes = await fetch(
                `${apiBase}/api/agent/runs/${encodeURIComponent(runId)}`
              )
              if (fullRes.ok && !cancelled) {
                const fullData = await fullRes.json()
                if (Array.isArray(fullData.events) && fullData.events.length > 0) {
                  const normalized = normalizeEvents(fullData.events)
                  setEvents(normalized)
                }
              }
            } catch {
              // Non-fatal incremental fetch blip
            }
          }
        } catch {
          // Network blip, continue next poll interval
        }
      }

      pollStep()
      const intervalId = setInterval(pollStep, 2000)
      pollCleanupRef.current = () => {
        cancelled = true
        clearInterval(intervalId)
      }
    },
    [apiBase, stopPolling]
  )

  const handleSelectRun = useCallback(
    async (runId: string) => {
      stopPolling()
      setSelectedRunId(runId)
      selectedRunIdRef.current = runId
      setError(null)
      setRunning(false)
      setPollCount(0)
      try {
        const r = await fetch(`${apiBase}/api/agent/runs/${encodeURIComponent(runId)}`)
        if (r.status === 200) {
          const j = await r.json()
          if (j) {
            const normalizedEvents = normalizeEvents(j.events || [])
            setEvents(normalizedEvents)
            const runTicker = normalizeTicker(j.ticker || ticker)
            if (runTicker !== ticker) {
              setTicker(runTicker)
            }
            const isCompleted = j.status === "completed"
            if (isCompleted) {
              setDone({
                n_events: j.n_events || normalizedEvents.length,
                state_keys: j.state ? Object.keys(j.state) : [],
                ms:
                  j.finished_at && j.started_at
                    ? Math.max(0, Math.round((j.finished_at - j.started_at) * 1000))
                    : 0,
              })
            } else {
              setDone(null)
            }
            if (j.error) {
              setError(j.error)
            } else {
              setError(null)
            }
            setLoadedFromDb({
              run_id: j.run_id,
              ticker: runTicker,
              status: j.status || "completed",
              n_events: j.n_events || normalizedEvents.length,
              started_at: j.started_at,
              finished_at: j.finished_at,
              error: j.error,
              reason: j.reason,
            })

            // If selected run is still active in BE, resume polling it!
            if (j.status === "running") {
              setRunning(true)
              startPolling(j.run_id, runTicker)
            }
          }
        } else {
          setError(`Gagal memuat run ${runId} (status ${r.status})`)
        }
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e)
        setError(`Gagal memuat jejak run: ${msg}`)
      }
    },
    [apiBase, ticker, stopPolling, startPolling]
  )

  const {
    activeCount,
    totalCount,
    agentStatuses,
    etaText,
    isInterrupted,
  } = useAgentProgress({
    events,
    running,
    done,
    error,
  })

  const run = useCallback(
    async (mode: "detached" | "blocking" | "sse" = "detached") => {
      stopPolling()
      setSelectedRunId(null)
      selectedRunIdRef.current = null
      setLoadedFromDb(null)
      setError(null)
      setDone(null)
      setEvents([])
      setPollCount(0)
      setRunning(true)
      startRef.current = Date.now()
      const t = ticker.trim().toUpperCase() || "BBCA"

      if (mode === "blocking") {
        try {
          const r = await fetch(`${apiBase}/api/agent/run`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ticker: t }),
          })
          const j = await r.json()
          if (!j.ok) throw new Error(j.error || JSON.stringify(j).slice(0, 800))
          setEvents(normalizeEvents(j.trace || []))
          setDone({
            n_events: j.n_events,
            state_keys: j.state_keys || [],
            ms: j.elapsed_ms || Date.now() - startRef.current,
          })
        } catch (e: unknown) {
          const msg = e instanceof Error ? e.message : String(e)
          setError(msg.slice(0, 1000))
        } finally {
          setRunning(false)
        }
        return
      }

      if (mode === "sse") {
        // SSE stream fallback
        try {
          const es = new EventSource(`${apiBase}/api/agent/stream?ticker=${encodeURIComponent(t)}`)
          es.onmessage = (ev) => {
            try {
              const frame = JSON.parse(ev.data) as TraceEvent & {
                done?: boolean
                state_keys?: string[]
                state_preview?: unknown
                ticker?: string
                error?: string
              }

              if (frame.event_type === "start") return

              if (frame.event_type === "error") {
                setError(frame.error || frame.text || "Terjadi kendala pada stream.")
                es.close()
                setRunning(false)
                return
              }

              if (frame.event_type === "done") {
                const d = frame as { n_events?: number; state_keys?: string[] }
                setDone({
                  n_events: d.n_events || 0,
                  state_keys: d.state_keys || [],
                  ms: Date.now() - startRef.current,
                })
                es.close()
                setRunning(false)
                return
              }

              setEvents((prev) => [...prev, frame as TraceEvent])
            } catch {}
          }

          es.onerror = () => {
            setTimeout(() => {
              if (es.readyState === EventSource.CLOSED) {
                setRunning(false)
                setError("Stream terputus. Memuat jejak dari SQLite…")
                fetch(`${apiBase}/api/agent/runs/latest?ticker=${encodeURIComponent(t)}`)
                  .then((r) => (r.status === 200 ? r.json() : null))
                  .then((j) => {
                    if (!j || !Array.isArray(j.events)) return
                    const normalized = normalizeEvents(j.events)
                    if (normalized.length > 0) {
                      setEvents(normalized)
                      setLoadedFromDb({
                        run_id: j.run_id,
                        ticker: j.ticker || t,
                        status: j.status || "interrupted",
                        n_events: j.n_events || normalized.length,
                        started_at: j.started_at,
                        finished_at: j.finished_at,
                        error: j.error,
                        reason: j.reason,
                      })
                    }
                  })
                  .catch(() => {})
              }
            }, 1200)
          }

          setTimeout(() => {
            try {
              es.close()
            } catch {}
            setRunning(false)
          }, 15 * 60 * 1000)
        } catch (e: unknown) {
          const msg = e instanceof Error ? e.message : String(e)
          setError(msg.slice(0, 1000))
          setRunning(false)
        }
        return
      }

      // Default: Detached fire-and-forget background task + polling
      try {
        const res = await fetch(`${apiBase}/api/agent/start`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ticker: t }),
        })

        if (!res.ok) {
          const errJson = await res.json().catch(() => ({}))
          throw new Error(errJson.error || `HTTP ${res.status}: Gagal memulai background run.`)
        }

        const data = await res.json()
        if (!data.ok || !data.run_id) {
          throw new Error(data.error || "Server tidak mengembalikan run_id yang valid.")
        }

        const runId = data.run_id
        const runTicker = (data.ticker || t).toUpperCase().trim()
        if (runTicker !== ticker) {
          setTicker(runTicker)
        }
        setSelectedRunId(runId)
        selectedRunIdRef.current = runId

        setLoadedFromDb({
          run_id: runId,
          ticker: runTicker,
          status: "running",
          n_events: 0,
          started_at: Date.now() / 1000,
          finished_at: null,
          error: null,
          reason: null,
        })

        // Start polling loop every 2s
        startPolling(runId, runTicker)
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e)
        setError(msg.slice(0, 1000))
        setRunning(false)
      }
    },
    [ticker, apiBase, stopPolling, startPolling]
  )

  const handleStop = useCallback(() => {
    stopPolling()
    setRunning(false)
  }, [stopPolling])

  const handleClear = useCallback(() => {
    stopPolling()
    setRunning(false)
    setSelectedRunId(null)
    selectedRunIdRef.current = null
    setLoadedFromDb(null)
    setEvents([])
    setDone(null)
    setError(null)
    setPollCount(0)
    setFilterAuthor("all")
  }, [stopPolling])

  const stateKeys = useMemo(() => {
    const set = new Set<string>()
    for (const ev of events) {
      if (ev.state_delta_keys) {
        for (const k of ev.state_delta_keys) set.add(k)
      }
    }
    return Array.from(set)
  }, [events])

  const isEmptyState = events.length === 0 && !running && !loadedFromDb

  return (
    <div className="space-y-5">
      {/* Row 1: Top Bar (Full Width) */}
      <header className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-5 shadow-xs space-y-3.5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-slate-900 text-white shadow-xs">
                <Bot className="h-5 w-5" />
              </div>
              <h1 className="text-xl font-bold tracking-tight text-slate-900 font-sans">
                Pusat Analisis Saham Multi-Agen AI
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-slate-600 max-w-2xl leading-relaxed">
              Pantau 11 agen AI independen yang bekerja sama mencari data IDX, valuasi finansial, risiko, dan riset institusional.
            </p>
          </div>

          {/* Status badge pill */}
          <div className="flex flex-wrap items-center gap-2">
            {running ? (
              <div className="flex items-center gap-2 rounded-xl border border-amber-300 bg-amber-50/80 px-3.5 py-1.5 text-xs text-amber-900 shadow-2xs">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
                  <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-amber-500" />
                </span>
                <span className="font-semibold">{activeCount} dari {totalCount} agen aktif</span>
                <span className="text-slate-300">·</span>
                <span className="flex items-center gap-1 font-mono text-slate-700">
                  <Activity className="h-3 w-3 text-slate-500" />
                  {events.length > 0 ? events.length : (loadedFromDb?.n_events ?? 0)} aktivitas
                </span>
                <span className="text-slate-300">·</span>
                <span className="flex items-center gap-1 font-mono text-slate-600" title={`Polling aktif (#${pollCount})`}>
                  <RefreshCw className="h-3 w-3 animate-spin text-slate-500" />
                  <span>polling 2 dtk</span>
                </span>
                <span className="text-slate-300">·</span>
                <span className="flex items-center gap-1 font-mono font-semibold text-amber-800">
                  <Clock className="h-3 w-3 text-amber-600" />
                  ETA {etaText}
                </span>
              </div>
            ) : done ? (
              <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-3.5 py-1.5 text-xs font-semibold text-emerald-900 shadow-2xs">
                <Sparkles className="h-4 w-4 text-emerald-600" />
                <span>Analisis Selesai</span>
                <span className="text-slate-300">·</span>
                <span className="font-mono text-slate-700">{done.n_events} aktivitas</span>
                <span className="text-slate-300">·</span>
                <span className="font-mono text-slate-600">{(done.ms / 1000).toFixed(1)}s</span>
              </div>
            ) : isInterrupted ? (
              <div className="flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-3.5 py-1.5 text-xs font-medium text-amber-900">
                <AlertCircle className="h-4 w-4 text-amber-600" />
                <span>Analisis terhenti sementara</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-1.5 text-xs font-medium text-slate-600">
                <span className="h-2 w-2 rounded-full bg-slate-400" />
                <span>Sistem Siap Dijalankan</span>
              </div>
            )}
          </div>
        </div>

        {/* Input form & buttons */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2.5 border-t border-slate-100">
          <div className="flex flex-wrap items-center gap-2.5">
            <div className="flex items-center gap-2">
              <label htmlFor="ticker-input" className="text-xs font-medium text-slate-700">
                Kode Saham:
              </label>
              <select
                id="ticker-input"
                value={ticker}
                onChange={(e) => {
                  stopPolling()
                  setRunning(false)
                  setSelectedRunId(null)
                  selectedRunIdRef.current = null
                  setTicker(normalizeTicker(e.target.value))
                }}
                className="h-9 rounded-lg border border-slate-300 bg-white px-2.5 text-sm font-mono font-bold uppercase text-slate-900 shadow-2xs focus:border-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900"
              >
                {SUPPORTED_TICKERS.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>

            {running ? (
              <Button
                onClick={handleStop}
                variant="outline"
                className="h-9 gap-1.5 text-xs font-medium text-rose-700 border-rose-300 bg-rose-50 hover:bg-rose-100 hover:text-rose-800 shadow-2xs"
              >
                <Square className="h-3.5 w-3.5 fill-current" />
                <span>Hentikan</span>
              </Button>
            ) : (
              <Button
                onClick={() => run("detached")}
                className="h-9 gap-1.5 bg-slate-900 px-4 text-xs font-medium text-white hover:bg-slate-800 shadow-xs"
              >
                <Play className="h-3.5 w-3.5 fill-current" />
                <span>Jalankan Analisis</span>
              </Button>
            )}

            <Button
              onClick={() => run("blocking")}
              disabled={running}
              variant="outline"
              className="h-9 gap-1.5 text-xs font-medium text-slate-700 border-slate-300 hover:bg-slate-50"
            >
              <Zap className="h-3.5 w-3.5 text-slate-500" />
              <span>Mode Cepat</span>
            </Button>

            <Button
              onClick={handleClear}
              variant="ghost"
              className="h-9 gap-1 text-xs text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              disabled={running}
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Bersihkan</span>
            </Button>
          </div>

          {/* Model / Bridge Health Badge */}
          {health && (
            <div className="flex items-center gap-2 text-xs">
              <Badge
                variant="outline"
                className="flex items-center gap-1 font-mono text-[11px] text-slate-600 bg-slate-50 border-slate-200"
              >
                <span
                  className={`h-1.5 w-1.5 rounded-full ${
                    health.ok ? "bg-emerald-500" : "bg-amber-500"
                  }`}
                />
                <Cpu className="h-3 w-3 text-slate-400" />
                <span>{health.model || "muse-spark-1.2"}</span>
              </Badge>

              <button
                type="button"
                onClick={fetchHealth}
                className="text-slate-400 hover:text-slate-700 p-1"
                title="Perbarui status server"
              >
                <RefreshCw className="h-3 w-3" />
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Row 2: 3-Column Layout (lg+), 2-Column (md), 1-Column (sm) */}
      <div className="flex flex-col lg:flex-row items-start gap-5">
        {/* LEFT COLUMN: RunHistoryPanel (280px fixed on lg+, 240px on md, 100% on sm) */}
        <aside className="w-full lg:w-[280px] md:w-[240px] shrink-0 lg:sticky lg:top-20 md:sticky md:top-20 z-10">
          <RunHistoryPanel
            currentTicker={ticker}
            selectedRunId={selectedRunId || loadedFromDb?.run_id}
            onSelectRun={handleSelectRun}
            apiBase={apiBase}
          />
        </aside>

        {/* CENTER COLUMN: Timeline Column (flex-1) */}
        <main className="flex-1 min-w-0 w-full space-y-5">
          {/* On md: Collapsible drawer for State Preview at top of center column */}
          <div className="hidden md:block lg:hidden">
            <details className="group rounded-2xl border border-slate-200 bg-white shadow-xs overflow-hidden">
              <summary className="flex cursor-pointer items-center justify-between p-3.5 text-xs font-semibold text-slate-800 select-none hover:bg-slate-50">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-slate-600" />
                  <span>State Preview ({stateKeys.length} keys)</span>
                </div>
                <ChevronDown className="h-4 w-4 text-slate-400 group-open:rotate-180 transition-transform" />
              </summary>
              <div className="border-t border-slate-100 p-2">
                <StatePreview events={events} />
              </div>
            </details>
          </div>

          {/* If no run selected & no events: Show empty state */}
          {isEmptyState ? (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 sm:p-12 text-center space-y-4 shadow-2xs">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100 text-slate-600 border border-slate-200 shadow-2xs">
                <Bot className="h-6 w-6" />
              </div>
              <div className="space-y-1.5 max-w-md mx-auto">
                <h3 className="text-base font-bold text-slate-900 font-sans">
                  Pilih run di sidebar atau mulai baru
                </h3>
                <p className="text-xs leading-relaxed text-slate-500">
                  Pilih salah satu riwayat analisis saham di sidebar kiri untuk memuat jejak sebelumnya, atau masukkan kode saham di bilah atas lalu klik <strong>Jalankan Analisis</strong>.
                </p>
              </div>
              <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
                <Button
                  onClick={() => run("detached")}
                  disabled={running}
                  size="sm"
                  className="bg-slate-900 text-xs font-medium text-white hover:bg-slate-800 shadow-xs"
                >
                  <Play className="mr-1.5 h-3.5 w-3.5 fill-current" />
                  Mulai Analisis Saham {ticker || "BBCA"}
                </Button>
              </div>
            </div>
          ) : (
            <>
              {/* ProgressHeader / SQLite Status Banner */}
              {loadedFromDb && (
                <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-slate-200 bg-slate-50/90 px-3.5 py-2 text-xs text-slate-700">
                  <div className="flex flex-wrap items-center gap-2">
                    <Database className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                    <span className="font-medium text-slate-800">
                      Loaded from SQLite · {loadedFromDb.n_events} aktivitas · {formatRelativeTime(loadedFromDb.finished_at || loadedFromDb.started_at)}
                    </span>
                    {loadedFromDb.status !== "completed" && (
                      <Badge
                        variant="outline"
                        className={`text-[11px] font-medium ${
                          loadedFromDb.status === "failed"
                            ? "border-rose-300 bg-rose-50 text-rose-700"
                            : loadedFromDb.status === "running"
                            ? "border-amber-300 bg-amber-50 text-amber-700"
                            : "border-amber-300 bg-amber-50 text-amber-700"
                        }`}
                      >
                        {loadedFromDb.status === "failed"
                          ? "Gagal"
                          : loadedFromDb.status === "running"
                          ? "Sedang Berjalan"
                          : "Terhenti"}
                      </Badge>
                    )}
                  </div>
                  {loadedFromDb.status !== "completed" && loadedFromDb.status !== "running" && (
                    <Button
                      onClick={() => run("detached")}
                      disabled={running}
                      size="sm"
                      variant="outline"
                      className="h-7 gap-1 text-xs font-medium text-slate-800 border-slate-300 bg-white hover:bg-slate-100"
                    >
                      <Play className="h-3 w-3 fill-current" />
                      <span>Lanjutkan Analisis?</span>
                    </Button>
                  )}
                </div>
              )}

              {/* Error Alert */}
              {error && (
                <div className="flex items-start gap-2.5 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
                  <AlertCircle className="h-4 w-4 shrink-0 text-rose-600 mt-0.5" />
                  <div className="space-y-1">
                    <span className="font-semibold">Terjadi kendala saat menjalankan pipeline:</span>
                    <p className="font-mono text-[11px] break-all">{error}</p>
                  </div>
                </div>
              )}

              {/* SummaryCard */}
              {done && <SummaryCard ticker={ticker} events={events} done={done} />}

              {/* PhaseTimeline */}
              <PhaseTimeline
                agentStatuses={agentStatuses}
                selectedAuthor={filterAuthor}
                onFilterAuthor={setFilterAuthor}
                running={running}
                done={done}
              />

              {/* PlainEnglishPanel */}
              <PlainEnglishPanel
                events={events}
                running={running}
                ticker={ticker}
                selectedAuthor={filterAuthor}
                onFilterAuthor={setFilterAuthor}
              />

              {/* Collapsible Explainer Guide */}
              <details className="group rounded-xl border border-slate-200 bg-white p-4 text-xs text-slate-600 shadow-2xs">
                <summary className="flex cursor-pointer items-center justify-between font-medium text-slate-800 select-none">
                  <div className="flex items-center gap-2">
                    <HelpCircle className="h-4 w-4 text-slate-500" />
                    <span className="text-sm font-semibold">Bagaimana Tim AI Bekerja?</span>
                  </div>
                  <span className="text-xs text-slate-400 group-open:hidden">Klik untuk melihat penjelasan alur</span>
                </summary>
                <div className="mt-3 space-y-2 border-t border-slate-100 pt-3 text-xs leading-relaxed text-slate-600">
                  <p>
                    Analisis ini dibuat oleh 11 agen AI yang bekerja sama: mereka mencari data dari IDX dan media, menghitung valuasi secara matematis tanpa rekayasa teks, menulis laporan riset terstruktur, dan saling menguji asumsi (Red Team) sebelum disetujui. Hasilnya ditujukan untuk informasi dan bukan saran investasi resmi.
                  </p>
                  <div className="grid gap-2 pt-1 sm:grid-cols-5 text-[11px]">
                    <div className="rounded-lg bg-slate-50 p-2 border border-slate-200/60">
                      <div className="font-semibold text-slate-800">1. Data</div>
                      <div>Koleksi laporan IDX, berita, dan sentimen.</div>
                    </div>
                    <div className="rounded-lg bg-slate-50 p-2 border border-slate-200/60">
                      <div className="font-semibold text-slate-800">2. Valuasi</div>
                      <div>Kalkulasi matematis DCF, DDM, dan PE/PBV.</div>
                    </div>
                    <div className="rounded-lg bg-slate-50 p-2 border border-slate-200/60">
                      <div className="font-semibold text-slate-800">3. Riset</div>
                      <div>Kajian fundamental, risiko, dan KPI industri.</div>
                    </div>
                    <div className="rounded-lg bg-slate-50 p-2 border border-slate-200/60">
                      <div className="font-semibold text-slate-800">4. Penulisan</div>
                      <div>Penyusunan narasi tesis dan grafik visual.</div>
                    </div>
                    <div className="rounded-lg bg-slate-50 p-2 border border-slate-200/60">
                      <div className="font-semibold text-slate-800">5. Uji Kualitas</div>
                      <div>Debat Red Team dan verifikasi QA akhir.</div>
                    </div>
                  </div>
                </div>
              </details>

              {/* Collapsible Raw Technical Debug */}
              <details
                open={rawDebugOpen}
                onToggle={(e) => setRawDebugOpen((e.currentTarget as HTMLDetailsElement).open)}
                className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs"
              >
                <summary className="flex cursor-pointer items-center justify-between text-xs font-medium text-slate-700 select-none">
                  <div className="flex items-center gap-2">
                    <Code2 className="h-4 w-4 text-slate-500" />
                    <span className="font-semibold">Lihat data teknis mentah (untuk developer)</span>
                    <Badge variant="outline" className="font-mono text-[10px] text-slate-500">
                      {events.length} frame JSON
                    </Badge>
                  </div>
                  {rawDebugOpen ? (
                    <ChevronUp className="h-4 w-4 text-slate-400" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-slate-400" />
                  )}
                </summary>

                <div className="mt-4 space-y-4 border-t border-slate-100 pt-4 text-xs">
                  <div className="space-y-2">
                    <div className="font-semibold text-slate-800">Kunci Memori Pipeline (State Keys):</div>
                    <div className="flex flex-wrap gap-1.5">
                      {stateKeys.length === 0 ? (
                        <span className="text-slate-400 italic">Belum ada kunci memori tersimpan</span>
                      ) : (
                        stateKeys.map((k) => (
                          <Badge key={k} variant="secondary" className="font-mono text-[11px]">
                            {k}
                          </Badge>
                        ))
                      )}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="font-semibold text-slate-800">Log Frame Event Aktivitas (JSON):</div>
                    <div className="max-h-80 overflow-y-auto rounded-lg border border-slate-200 bg-slate-900 p-3 font-mono text-[11px] text-slate-300">
                      {events.length === 0 ? (
                        <div className="text-slate-500 italic">Belum ada frame event yang diterima.</div>
                      ) : (
                        events.map((ev) => (
                          <div key={ev.seq} className="border-b border-slate-800 py-2">
                            <div className="flex items-center gap-2 text-slate-400">
                              <span className="text-sky-400">#{ev.seq}</span>
                              <span className="font-bold text-amber-300">{ev.author}</span>
                              <span className="text-emerald-400">[{ev.event_type}]</span>
                              <span>node: {ev.node}</span>
                            </div>
                            {ev.text && (
                              <div className="mt-1 text-slate-300 whitespace-pre-wrap">{ev.text}</div>
                            )}
                            {ev.function_calls?.length > 0 && (
                              <div className="mt-1.5 space-y-1">
                                {ev.function_calls.map((fc, i) => (
                                  <FunctionCallCard key={fc.id || `${fc.name}-${i}`} fc={fc} />
                                ))}
                              </div>
                            )}
                            {ev.function_responses?.length > 0 && (
                              <div className="mt-1.5 space-y-1">
                                {ev.function_responses.map((fr, i) => (
                                  <FunctionResponseCard key={fr.id || `${fr.name}-${i}`} fr={fr} />
                                ))}
                              </div>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              </details>
            </>
          )}

          {/* On sm: Collapsible State Preview at the bottom of center */}
          <div className="block lg:hidden md:hidden">
            <details className="group rounded-2xl border border-slate-200 bg-white shadow-xs overflow-hidden">
              <summary className="flex cursor-pointer items-center justify-between p-3.5 text-xs font-semibold text-slate-800 select-none hover:bg-slate-50">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-slate-600" />
                  <span>State Preview ({stateKeys.length} keys)</span>
                </div>
                <ChevronDown className="h-4 w-4 text-slate-400 group-open:rotate-180 transition-transform" />
              </summary>
              <div className="border-t border-slate-100 p-2">
                <StatePreview events={events} />
              </div>
            </details>
          </div>

          {/* Disclaimer Footer */}
          <p className="text-center text-xs text-slate-500 pt-2">
            Disclaimer: Produk ini adalah informasi dan sarana edukasi, bukan saran investasi. Keputusan investasi sepenuhnya menjadi tanggung jawab pengguna.
          </p>
        </main>

        {/* RIGHT COLUMN: StatePreview (360px fixed on lg+, sticky) */}
        <aside className="hidden lg:block w-[360px] shrink-0 sticky top-20 z-10">
          <StatePreview events={events} />
        </aside>
      </div>
    </div>
  )
}
