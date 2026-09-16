import { createFileRoute, useNavigate, Link } from "@tanstack/react-router"
import { useEffect, useRef, useState, useCallback, useMemo } from "react"
import { AlertCircle } from "lucide-react"
import { useAgentProgress } from "@/components/agent/useAgentProgress"
import { PhaseTimeline } from "@/components/agent/PhaseTimeline"
import { PlainEnglishPanel } from "@/components/agent/PlainEnglishPanel"
import { SummaryCard } from "@/components/agent/SummaryCard"
import { RunHistoryPanel, type AgentRunItem } from "@/components/agent/RunHistoryPanel"
import { StatePreview } from "@/components/agent/StatePreview"
import { TickerPicker } from "@/components/agent/TickerPicker"
import { PipelineHeader } from "@/components/agent/PipelineHeader"
import { type TraceEvent } from "@/components/agent/AGENT_FRIENDLY_META"
import {
  SUPPORTED_TICKERS,
  normalizeTicker,
  fetchUniverse,
  type UniverseTicker,
} from "@/components/agent/tickers"

interface AgentSearchParams {
  ticker?: string
}

export const Route = (createFileRoute as any)("/agent")({
  validateSearch: (search: Record<string, unknown>): AgentSearchParams => {
    return {
      ticker: typeof search.ticker === "string" && search.ticker.trim().length > 0 ? search.ticker.trim().toUpperCase() : undefined,
    }
  },
  component: AgentPage,
})

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

function AgentPage() {
  const search = Route.useSearch() as AgentSearchParams
  const navigate = useNavigate()
  const rawTicker = search?.ticker || ""

  const [universe, setUniverse] = useState<UniverseTicker[]>([])
  const knownTickers = useMemo(
    () => (universe.length > 0 ? universe.map((u) => u.kode) : [...SUPPORTED_TICKERS]),
    [universe]
  )

  const selectedTicker = normalizeTicker(rawTicker, knownTickers)

  const [events, setEvents] = useState<TraceEvent[]>([])
  const [running, setRunning] = useState(false)
  const [done, setDone] = useState<{ n_events: number; state_keys: string[]; ms: number } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [filterAuthor, setFilterAuthor] = useState<string>("all")
  const [allRuns, setAllRuns] = useState<AgentRunItem[]>([])
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

  // Load IDX ticker list once for company names and validation
  useEffect(() => {
    let active = true
    fetchUniverse(apiBase).then((u) => {
      if (active) setUniverse(u)
    })
    return () => {
      active = false
    }
  }, [apiBase])

  const companyName = useMemo(() => {
    if (!selectedTicker) return null
    const found = universe.find((u) => u.kode.toUpperCase() === selectedTicker)
    return found?.nama || null
  }, [selectedTicker, universe])

  // Auto-load latest persisted run from server on ticker change
  useEffect(() => {
    let active = true
    if (!selectedTicker) {
      setEvents([])
      setDone(null)
      setError(null)
      setLoadedFromDb(null)
      setSelectedRunId(null)
      return
    }

    if (running) return

    // If already loaded for this ticker and matches selected run, avoid redundant reload
    if (
      selectedRunIdRef.current &&
      loadedFromDb?.run_id === selectedRunIdRef.current &&
      loadedFromDb?.ticker === selectedTicker
    ) {
      return
    }

    async function loadLatestRun() {
      try {
        const r = await fetch(`${apiBase}/api/agent/runs/latest?ticker=${encodeURIComponent(selectedTicker)}`)
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
              ticker: j.ticker || selectedTicker,
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
          setEvents([])
          setDone(null)
        }
      } catch {
        if (active) {
          setLoadedFromDb(null)
          setEvents([])
          setDone(null)
        }
      }
    }

    loadLatestRun()
    return () => {
      active = false
    }
  }, [selectedTicker, apiBase, running, loadedFromDb?.run_id, loadedFromDb?.ticker])

  const startPolling = useCallback(
    (runId: string, runTicker: string) => {
      stopPolling()
      let cancelled = false
      let consecutive404s = 0

      const pollStep = async () => {
        if (cancelled) return

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
              setError(`Proses ${runId} tidak ditemukan di server.`)
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
                    `Analisis terhenti (${fullData.reason || "interrupted"}). Klik "Jalankan analisis" untuk mengulang.`
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

          // Incremental updates while running
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
              // Incremental fetch blip
            }
          }
        } catch {
          // Network blip
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
      try {
        const r = await fetch(`${apiBase}/api/agent/runs/${encodeURIComponent(runId)}`)
        if (r.status === 200) {
          const j = await r.json()
          if (j) {
            const normalizedEvents = normalizeEvents(j.events || [])
            setEvents(normalizedEvents)
            const runTicker = normalizeTicker(j.ticker || selectedTicker, knownTickers)
            if (runTicker && runTicker !== selectedTicker) {
              navigate({ to: "/agent", search: { ticker: runTicker } })
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

            if (j.status === "running") {
              setRunning(true)
              startPolling(j.run_id, runTicker)
            }
          }
        } else {
          setError(`Gagal memuat proses ${runId} (status ${r.status})`)
        }
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e)
        setError(`Gagal memuat jejak proses: ${msg}`)
      }
    },
    [apiBase, selectedTicker, stopPolling, startPolling, knownTickers, navigate]
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

  const handleRun = useCallback(async () => {
    if (!selectedTicker) return
    stopPolling()
    setSelectedRunId(null)
    selectedRunIdRef.current = null
    setLoadedFromDb(null)
    setError(null)
    setDone(null)
    setEvents([])
    setRunning(true)
    startRef.current = Date.now()

    try {
      const res = await fetch(`${apiBase}/api/agent/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker: selectedTicker }),
      })

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}))
        throw new Error(errJson.error || `HTTP ${res.status}: Gagal memulai proses latar belakang.`)
      }

      const data = await res.json()
      if (!data.ok || !data.run_id) {
        throw new Error(data.error || "Server tidak mengembalikan ID proses yang valid.")
      }

      const runId = data.run_id
      const runTicker = (data.ticker || selectedTicker).toUpperCase().trim()

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

      startPolling(runId, runTicker)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e)
      setError(msg)
      setRunning(false)
    }
  }, [selectedTicker, apiBase, stopPolling, startPolling])

  const handleStop = useCallback(() => {
    stopPolling()
    setRunning(false)
  }, [stopPolling])

  // Step 1: When no ticker is selected in search params
  if (!selectedTicker) {
    return (
      <div className="min-h-screen bg-[#FBFAF7] dark:bg-[#14130F]">
        <TickerPicker
          onSelectTicker={(t) => {
            navigate({ to: "/agent", search: { ticker: t } })
          }}
        />
      </div>
    )
  }

  // Step 2: Pipeline view for the chosen ticker
  return (
    <div className="min-h-screen bg-[#FBFAF7] dark:bg-[#14130F] font-sans text-[#1C1B17] dark:text-[#EDEAE3]">
      <div className="max-w-[1100px] mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-8">
        {/* Step 2 Header & Status Control */}
        <PipelineHeader
          ticker={selectedTicker}
          companyName={companyName}
          running={running}
          done={done}
          error={error}
          activeCount={activeCount}
          totalCount={totalCount}
          etaText={etaText}
          isInterrupted={isInterrupted}
          onRun={handleRun}
          onStop={handleStop}
        />

        {/* Error Notification */}
        {error && (
          <div className="flex items-start gap-3 rounded-xl border border-rose-200 dark:border-rose-900/60 bg-rose-50 dark:bg-rose-950/40 p-4 text-xs text-[#B4232A] dark:text-rose-300">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            <div className="space-y-0.5">
              <span className="font-semibold">Kendala proses analisis:</span>
              <p className="break-all">{error}</p>
            </div>
          </div>
        )}

        {/* Synthesis Summary Result (when done) */}
        {done && (
          <SummaryCard ticker={selectedTicker} events={events} done={done} />
        )}

        {/* Pipeline Stages Stepper */}
        <PhaseTimeline
          agentStatuses={agentStatuses}
          selectedAuthor={filterAuthor}
          onFilterAuthor={setFilterAuthor}
          running={running}
          done={done}
        />

        {/* 2-Column Section: Timeline Log & Memory/History */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Main Log / Timeline Stream (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            <PlainEnglishPanel
              events={events}
              running={running}
              ticker={selectedTicker}
              selectedAuthor={filterAuthor}
              onFilterAuthor={setFilterAuthor}
            />
          </div>

          {/* Sidebar: Memory & Run History (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            <RunHistoryPanel
              currentTicker={selectedTicker}
              selectedRunId={selectedRunId || loadedFromDb?.run_id}
              onSelectRun={handleSelectRun}
              apiBase={apiBase}
              runsList={allRuns}
              onRunsFetched={setAllRuns}
            />

            <StatePreview events={events} />
          </div>
        </div>
      </div>
    </div>
  )
}
