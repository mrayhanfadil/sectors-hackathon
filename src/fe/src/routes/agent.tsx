import { createFileRoute } from "@tanstack/react-router"
import { useEffect, useRef, useState, useCallback, useMemo } from "react"
import {
  Bot,
  Play,
  RotateCcw,
  AlertCircle,
  Cpu,
  RefreshCw,
  Clock,
  Activity,
  Code2,
  Zap,
  Database,
  Square,
  Terminal,
  Command,
  Layers,
  Sparkles,
  ChevronDown,
  ChevronUp,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useAgentProgress, KNOWN_AGENTS } from "@/components/agent/useAgentProgress"
import { PhaseTimeline } from "@/components/agent/PhaseTimeline"
import { PlainEnglishPanel } from "@/components/agent/PlainEnglishPanel"
import { SummaryCard } from "@/components/agent/SummaryCard"
import { RunHistoryPanel, type AgentRunItem } from "@/components/agent/RunHistoryPanel"
import { StatePreview } from "@/components/agent/StatePreview"
import { AgentRail } from "@/components/agent/AgentRail"
import { RunCommandPalette } from "@/components/agent/RunCommandPalette"
import { FunctionCallCard } from "@/components/agent/FunctionCallCard"
import { FunctionResponseCard } from "@/components/agent/FunctionResponseCard"
import { type TraceEvent } from "@/components/agent/AGENT_FRIENDLY_META"
import {
  SUPPORTED_TICKERS,
  normalizeTicker,
  fetchUniverse,
  optionLabel,
  type UniverseTicker,
} from "@/components/agent/tickers"

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

function AgentTrace() {
  const search = Route.useSearch() as AgentSearchParams
  const initialTicker = normalizeTicker(search?.ticker)
  const [ticker, setTicker] = useState<string>(initialTicker)
  const [universe, setUniverse] = useState<UniverseTicker[]>([])
  const knownTickers = useMemo(
    () => (universe.length > 0 ? universe.map((u) => u.kode) : [...SUPPORTED_TICKERS]),
    [universe],
  )
  const [events, setEvents] = useState<TraceEvent[]>([])
  const [running, setRunning] = useState(false)
  const [pollCount, setPollCount] = useState(0)
  const [done, setDone] = useState<{ n_events: number; state_keys: string[]; ms: number } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [health, setHealth] = useState<HealthInfo | null>(null)
  const [filterAuthor, setFilterAuthor] = useState<string>("all")
  const [rawDebugOpen, setRawDebugOpen] = useState(false)
  const [isPaletteOpen, setIsPaletteOpen] = useState(false)
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
      const t = normalizeTicker(search.ticker, knownTickers)
      setTicker((prev) => (prev !== t ? t : prev))
    }
  }, [search?.ticker, knownTickers])

  // Load IDX universe once (datalist suggestions + run validation)
  useEffect(() => {
    let active = true
    fetchUniverse(apiBase).then((u) => {
      if (active) setUniverse(u)
    })
    return () => {
      active = false
    }
  }, [apiBase])

  // Re-validate current ticker once universe arrives (?ticker= asing -> kosong)
  useEffect(() => {
    if (universe.length > 0) {
      const known = universe.map((u) => u.kode)
      setTicker((prev) => normalizeTicker(prev, known))
    }
  }, [universe])

  // Keyboard shortcut listener for Command Palette (⌘K, Ctrl+K, or /)
  useEffect(() => {
    const handleGlobalKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault()
        setIsPaletteOpen((prev) => !prev)
      } else if (e.key === "/" && !(e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement)) {
        e.preventDefault()
        setIsPaletteOpen(true)
      }
    }
    window.addEventListener("keydown", handleGlobalKey)
    return () => window.removeEventListener("keydown", handleGlobalKey)
  }, [])

  // Auto-load latest persisted run from SQLite on mount / ticker change
  useEffect(() => {
    let active = true
    const t = ticker.trim().toUpperCase()

    if (!t) return // belum ada pilihan
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
              // Incremental fetch blip
            }
          }
        } catch {
          // Network blip, continue polling
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
            const runTicker = normalizeTicker(j.ticker || ticker, knownTickers)
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
    [apiBase, ticker, stopPolling, startPolling, knownTickers]
  )

  const {
    activeCount,
    totalCount,
    agentStatuses,
    etaText,
    isInterrupted,
    knownAgents,
  } = useAgentProgress({
    events,
    running,
    done,
    error,
  })

  const run = useCallback(
    async (mode: "detached" | "blocking" | "sse" = "detached", overrideTicker?: string) => {
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

      const targetT = (overrideTicker || ticker).trim().toUpperCase()
      if (overrideTicker && overrideTicker !== ticker) {
        setTicker(targetT)
      }

      if (!targetT) {
        setError("Pilih emiten dulu dari daftar saran universe IDX.")
        setRunning(false)
        return
      }
      if (!knownTickers.includes(targetT)) {
        setError(`Kode ${targetT} tidak ada di universe IDX (${knownTickers.length} emiten) — pilih dari daftar saran.`)
        setRunning(false)
        return
      }

      if (mode === "blocking") {
        try {
          const r = await fetch(`${apiBase}/api/agent/run`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ticker: targetT }),
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

      // Default: Detached fire-and-forget background task + 2s polling
      try {
        const res = await fetch(`${apiBase}/api/agent/start`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ticker: targetT }),
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
        const runTicker = (data.ticker || targetT).toUpperCase().trim()
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

        // Start 2s polling loop
        startPolling(runId, runTicker)
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e)
        setError(msg.slice(0, 1000))
        setRunning(false)
      }
    },
    [ticker, apiBase, stopPolling, startPolling, knownTickers]
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
    <div className="space-y-4 font-sans text-neutral-100">
      {/* Top Telemetry Header Bar */}
      <header className="rounded-lg border border-neutral-800 bg-neutral-950 p-4 shadow-md space-y-3 font-mono">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2.5">
              <div className="flex h-7 w-7 items-center justify-center rounded bg-neutral-900 border border-neutral-700 text-emerald-400 shrink-0">
                <Terminal className="h-4 w-4" />
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-sm sm:text-base font-bold uppercase tracking-wider text-neutral-100">
                  RUANG PANTAU MESIN // ORKESTRATOR
                </h1>
                <span className="rounded bg-neutral-900 border border-neutral-800 px-1.5 py-0.2 text-[10px] text-neutral-400">
                  {KNOWN_AGENTS.length} AGENTS
                </span>
              </div>
            </div>
            <p className="text-xs text-neutral-400 max-w-3xl leading-relaxed">
              Layar pantau mesin analis: hitung nilai wajar (DCF/DDM/PE), baca laporan keuangan IDX, dan uji silang antar-mesin.
            </p>
          </div>

          {/* Status Pills with Terminal Colors */}
          <div className="flex flex-wrap items-center gap-2">
            {running ? (
              <div className="flex items-center gap-2 rounded border border-amber-800 bg-amber-950/80 px-3 py-1.5 text-xs text-amber-200">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-500" />
                </span>
                <span className="font-bold font-mono">JALAN</span>
                <span className="text-neutral-600">·</span>
                <span className="font-mono">{activeCount}/{totalCount} AKTIF</span>
                <span className="text-neutral-600">·</span>
                <span className="font-mono text-amber-300 flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  SISA {etaText}
                </span>
              </div>
            ) : done ? (
              <div className="flex items-center gap-2 rounded border border-emerald-800 bg-emerald-950/80 px-3 py-1.5 text-xs font-mono text-emerald-300">
                <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
                <span className="font-bold">SELESAI</span>
                <span className="text-neutral-600">·</span>
                <span>{done.n_events} LANGKAH</span>
                <span className="text-neutral-600">·</span>
                <span>{(done.ms / 1000).toFixed(1)}s</span>
              </div>
            ) : isInterrupted ? (
              <div className="flex items-center gap-2 rounded border border-amber-800 bg-amber-950/60 px-3 py-1.5 text-xs font-mono text-amber-300">
                <AlertCircle className="h-3.5 w-3.5 text-amber-400" />
                <span className="font-bold">TERHENTI</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 rounded border border-neutral-800 bg-neutral-900 px-3 py-1.5 text-xs font-mono text-neutral-400">
                <span className="h-1.5 w-1.5 rounded-full bg-neutral-500" />
                <span>MESIN SIAGA</span>
              </div>
            )}
          </div>
        </div>

        {/* Input Form, Command Palette Trigger, & Action Controls */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2.5 border-t border-neutral-800/80">
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Ticker Input */}
            <div className="flex items-center gap-2">
              <label htmlFor="ticker-input" className="text-xs font-mono text-neutral-400 uppercase">
                SAHAM:
              </label>
              <input
                id="ticker-input"
                value={ticker}
                onChange={(e) => {
                  stopPolling()
                  setRunning(false)
                  setSelectedRunId(null)
                  selectedRunIdRef.current = null
                  setTicker(e.target.value.toUpperCase().trim())
                }}
                placeholder="KODE SAHAM…"
                list="ticker-universe"
                autoComplete="off"
                spellCheck={false}
                className="h-8 w-40 rounded bg-neutral-900 border border-neutral-700 px-2.5 text-xs font-mono font-bold uppercase text-emerald-400 placeholder:text-neutral-600 focus:border-emerald-500 focus:outline-none"
                maxLength={10}
              />
              <datalist id="ticker-universe">
                {universe.map((u) => (
                  <option key={u.kode} value={u.kode}>
                    {optionLabel(u)}
                  </option>
                ))}
              </datalist>
            </div>

            {/* Command Palette Button */}
            <Button
              type="button"
              onClick={() => setIsPaletteOpen(true)}
              variant="outline"
              className="h-8 gap-1.5 border-neutral-700 bg-neutral-900 text-xs font-mono text-neutral-300 hover:bg-neutral-800 hover:text-white"
              title="Buka cari cepat (⌘K)"
            >
              <Command className="h-3.5 w-3.5 text-emerald-400" />
              <span>CARI CEPAT</span>
              <kbd className="hidden sm:inline rounded bg-neutral-800 px-1 py-0.5 text-[9px] border border-neutral-700">⌘K</kbd>
            </Button>

            {/* Run Actions */}
            {running ? (
              <Button
                onClick={handleStop}
                variant="outline"
                className="h-8 gap-1.5 text-xs font-mono font-bold border-rose-800 bg-rose-950 text-rose-200 hover:bg-rose-900"
              >
                <Square className="h-3 w-3 fill-current" />
                <span>BERHENTI</span>
              </Button>
            ) : (
              <Button
                onClick={() => run("detached")}
                className="h-8 gap-1.5 bg-emerald-600 text-xs font-mono font-bold text-black hover:bg-emerald-500"
              >
                <Play className="h-3 w-3 fill-current" />
                <span>JALANKAN</span>
              </Button>
            )}

            <Button
              onClick={() => run("blocking")}
              disabled={running}
              variant="outline"
              className="h-8 gap-1 text-xs font-mono text-neutral-400 border-neutral-800 bg-neutral-900 hover:bg-neutral-800 hover:text-neutral-200"
              title="Jalankan dan tunggu sampai selesai"
            >
              <Zap className="h-3 w-3 text-amber-400" />
              <span>KILAT</span>
            </Button>

            <Button
              onClick={handleClear}
              variant="ghost"
              className="h-8 gap-1 text-xs font-mono text-neutral-400 hover:bg-neutral-800 hover:text-white"
              disabled={running}
            >
              <RotateCcw className="h-3 w-3" />
              <span>BERSIHKAN</span>
            </Button>
          </div>

          {/* Model Health / Telemetry */}
          {health && (
            <div className="flex items-center gap-2 text-xs font-mono">
              <Badge
                variant="outline"
                className="flex items-center gap-1.5 border-neutral-800 bg-neutral-900 text-neutral-300 text-[11px]"
              >
                <span
                  className={`h-1.5 w-1.5 rounded-full ${
                    health.ok ? "bg-emerald-400" : "bg-amber-400"
                  }`}
                />
                <Cpu className="h-3 w-3 text-neutral-500" />
                <span>{health.model || "muse-spark-1.2"}</span>
              </Badge>

              <button
                type="button"
                onClick={fetchHealth}
                className="text-neutral-500 hover:text-neutral-200 p-1"
                title="Muat ulang status mesin"
              >
                <RefreshCw className="h-3 w-3" />
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Global Agent Mesh Rail */}
      <AgentRail
        agentStatuses={agentStatuses}
        selectedAuthor={filterAuthor}
        onFilterAuthor={setFilterAuthor}
        knownAgents={knownAgents}
      />

      {/* Main 3-Column Ops Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        {/* Left Column (3 cols): Sticky Run Blotter & Launcher */}
        <aside className="lg:col-span-3 w-full lg:sticky lg:top-16 space-y-3 z-10">
          <RunHistoryPanel
            currentTicker={ticker}
            selectedRunId={selectedRunId || loadedFromDb?.run_id}
            onSelectRun={handleSelectRun}
            apiBase={apiBase}
            onOpenCommandPalette={() => setIsPaletteOpen(true)}
            runsList={allRuns}
            onRunsFetched={setAllRuns}
          />
        </aside>

        {/* Center Column (5 cols): Execution Blotter & Live State Inspector */}
        <div className="lg:col-span-5 w-full space-y-4">
          {/* Phase Execution Blotter */}
          <PhaseTimeline
            agentStatuses={agentStatuses}
            selectedAuthor={filterAuthor}
            onFilterAuthor={setFilterAuthor}
            running={running}
            done={done}
          />

          {/* SQLite Run Banner */}
          {loadedFromDb && (
            <div className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-neutral-800 bg-neutral-900/90 px-3 py-2 text-xs font-mono text-neutral-300">
              <div className="flex items-center gap-2 min-w-0">
                <Database className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
                <span className="truncate">
                  SQLite Run <strong className="text-white">{loadedFromDb.run_id.slice(0, 10)}…</strong> ({loadedFromDb.n_events} evts)
                </span>
              </div>
              {loadedFromDb.status !== "completed" && (
                <Badge
                  variant="outline"
                  className="font-mono text-[10px] border-amber-800 bg-amber-950 text-amber-300"
                >
                  {loadedFromDb.status.toUpperCase()}
                </Badge>
              )}
            </div>
          )}

          {/* Error Alert */}
          {error && (
            <div className="flex items-start gap-2.5 rounded-md border border-rose-800 bg-rose-950/80 p-3 text-xs text-rose-200 font-mono">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-400 mt-0.5" />
              <div className="space-y-1">
                <span className="font-bold">EXECUTION ERROR / PIPELINE BLIP:</span>
                <p className="text-[11px] break-all text-rose-300">{error}</p>
              </div>
            </div>
          )}

          {/* Synthesis / Summary Target Card */}
          {done && <SummaryCard ticker={ticker} events={events} done={done} />}

          {/* Live State Memory Blotter */}
          <StatePreview events={events} />

          {/* Collapsible Raw Frame Debug */}
          <details
            open={rawDebugOpen}
            onToggle={(e) => setRawDebugOpen((e.currentTarget as HTMLDetailsElement).open)}
            className="rounded-lg border border-neutral-800 bg-neutral-950 p-3 text-xs font-mono text-neutral-300"
          >
            <summary className="flex cursor-pointer items-center justify-between select-none hover:text-white">
              <div className="flex items-center gap-2">
                <Code2 className="h-3.5 w-3.5 text-neutral-400" />
                <span className="font-bold uppercase tracking-wider">RAW FRAME DEBUGGER</span>
                <Badge variant="outline" className="font-mono text-[9px] border-neutral-700 text-neutral-400">
                  {events.length} FRAMES
                </Badge>
              </div>
              {rawDebugOpen ? (
                <ChevronUp className="h-3.5 w-3.5 text-neutral-500" />
              ) : (
                <ChevronDown className="h-3.5 w-3.5 text-neutral-500" />
              )}
            </summary>

            <div className="mt-3 pt-3 border-t border-neutral-900 space-y-3">
              <div>
                <div className="text-[10px] text-neutral-500 uppercase font-semibold">Active State Keys:</div>
                <div className="mt-1 flex flex-wrap gap-1">
                  {stateKeys.length === 0 ? (
                    <span className="text-neutral-600 italic">No state keys generated yet</span>
                  ) : (
                    stateKeys.map((k) => (
                      <span key={k} className="rounded bg-neutral-900 border border-neutral-800 px-1.5 py-0.2 text-[9px] text-cyan-300 font-mono">
                        {k}
                      </span>
                    ))
                  )}
                </div>
              </div>

              <div>
                <div className="text-[10px] text-neutral-500 uppercase font-semibold">Raw JSON Event Frames:</div>
                <div className="mt-1 max-h-60 overflow-y-auto rounded bg-black p-2 font-mono text-[10px] text-neutral-300 border border-neutral-900 scrollbar-thin">
                  {events.length === 0 ? (
                    <div className="text-neutral-600 italic">No raw frames in buffer</div>
                  ) : (
                    events.map((ev) => (
                      <div key={ev.seq} className="border-b border-neutral-900 py-1.5">
                        <div className="flex items-center gap-2 text-neutral-400 text-[9px]">
                          <span className="text-cyan-400 font-bold">#{ev.seq}</span>
                          <span className="text-amber-300 font-semibold">{ev.author}</span>
                          <span className="text-emerald-400">[{ev.event_type}]</span>
                          <span>node:{ev.node}</span>
                        </div>
                        {ev.text && (
                          <div className="mt-0.5 text-neutral-300 whitespace-pre-wrap">{ev.text}</div>
                        )}
                        {ev.function_calls?.length > 0 && (
                          <div className="mt-1 space-y-1">
                            {ev.function_calls.map((fc, i) => (
                              <FunctionCallCard key={fc.id || `${fc.name}-${i}`} fc={fc} />
                            ))}
                          </div>
                        )}
                        {ev.function_responses?.length > 0 && (
                          <div className="mt-1 space-y-1">
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
        </div>

        {/* Right Column (4 cols): Monospace Quant Event Stream & Live Transcript */}
        <div className="lg:col-span-4 w-full space-y-4">
          <PlainEnglishPanel
            events={events}
            running={running}
            ticker={ticker}
            selectedAuthor={filterAuthor}
            onFilterAuthor={setFilterAuthor}
          />
        </div>
      </div>

      {/* Command Palette Modal */}
      <RunCommandPalette
        isOpen={isPaletteOpen}
        onClose={() => setIsPaletteOpen(false)}
        currentTicker={ticker}
        onSelectTicker={(t) => setTicker(t)}
        onRunTicker={(t) => run("detached", t)}
        runs={allRuns}
        selectedRunId={selectedRunId || loadedFromDb?.run_id}
        onSelectRun={handleSelectRun}
        universe={universe}
        knownTickers={knownTickers}
        running={running}
      />
    </div>
  )
}
