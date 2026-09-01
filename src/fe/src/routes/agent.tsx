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
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useAgentProgress } from "@/components/agent/useAgentProgress"
import { PhaseTimeline } from "@/components/agent/PhaseTimeline"
import { PlainEnglishPanel } from "@/components/agent/PlainEnglishPanel"
import { SummaryCard } from "@/components/agent/SummaryCard"
import {
  getFriendlyAgent,
  type TraceEvent,
} from "@/components/agent/AGENT_FRIENDLY_META"

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
  const search = (Route.useSearch ? Route.useSearch() : {}) as AgentSearchParams
  const initialTicker = (search?.ticker || "BBCA").toUpperCase().trim()
  const [ticker, setTicker] = useState(initialTicker)
  const [events, setEvents] = useState<TraceEvent[]>([])
  const [running, setRunning] = useState(false)
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
  } | null>(null)
  const startRef = useRef<number>(0)

  const apiBase = (import.meta as any).env?.VITE_API_URL || ""

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
      const t = search.ticker.toUpperCase().trim()
      setTicker((prev) => (prev !== t ? t : prev))
    }
  }, [search?.ticker])

  // Auto-load latest persisted run from SQLite on mount / ticker change
  useEffect(() => {
    let active = true
    const t = ticker.trim().toUpperCase() || "BBCA"

    if (running) return

    async function loadLatestRun() {
      try {
        const r = await fetch(`${apiBase}/api/agent/runs/latest?ticker=${encodeURIComponent(t)}`)
        if (!active) return
        if (r.status === 200) {
          const j = await r.json()
          if (!active) return
          if (j && Array.isArray(j.events) && j.events.length > 0) {
            const normalizedEvents: TraceEvent[] = j.events.map((ev: any) => ({
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
  }, [ticker, apiBase, running])

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
    async (mode: "stream" | "blocking") => {
      setLoadedFromDb(null)
      setError(null)
      setDone(null)
      setEvents([])
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
          setEvents((j.trace || []) as TraceEvent[])
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

      // SSE stream mode (live step-by-step trace)
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

            if (frame.event_type === "start") {
              return
            }

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

            // Normal event frame
            setEvents((prev) => [...prev, frame as TraceEvent])
          } catch {
            // Ignore parse errors on individual frames
          }
        }

        let reconnectAttempted = false
        let reconnectTimer: ReturnType<typeof setTimeout> | null = null

        es.onerror = () => {
          // Distinguish transient network blip (readyState CONNECTING) from hard close (CLOSED).
          // EventSource auto-reconnects on transient blips. Only mark interrupted when CLOSED
          // (server actively disconnected) — and offer a SQLite fallback so the user can
          // resume the partial trace instead of losing it.
          setTimeout(() => {
            if (es.readyState === EventSource.CLOSED) {
              // Stream died. Don't auto-retry the same SSE (server already marked interrupted
              // in SQLite). Instead, fetch the partial trace from persistence so the user
              // sees what we captured and can choose to re-run a fresh SSE.
              setRunning(false)
              setError(
                "Stream terputus (mungkin tab di-background, navigasi, atau koneksi idle). " +
                  "Memuat jejak terakhir dari SQLite…"
              )
              // Pull latest persisted events for this ticker so the UI keeps showing what
              // we captured before the disconnect.
              fetch(`${apiBase}/api/agent/runs/latest?ticker=${encodeURIComponent(t)}`)
                .then((r) => (r.status === 200 ? r.json() : null))
                .then((j) => {
                  if (!j || !Array.isArray(j.events)) return
                  const normalized: TraceEvent[] = j.events.map((ev: any) => ({
                    seq: ev.seq ?? 0,
                    ts: ev.ts ?? (ev.payload?.ts || Date.now() / 1000),
                    author: ev.author || ev.payload?.author || "",
                    node: ev.node || ev.payload?.node || "",
                    branch: ev.branch || ev.payload?.branch || null,
                    event_type: ev.event_type || ev.payload?.event_type || "message",
                    text: ev.text ?? ev.payload?.text ?? "",
                    function_calls: ev.function_calls || ev.payload?.function_calls || [],
                    function_responses:
                      ev.function_responses || ev.payload?.function_responses || [],
                    state_delta_keys:
                      ev.state_delta_keys ||
                      (ev.payload?.state_delta && typeof ev.payload.state_delta === "object"
                        ? Object.keys(ev.payload.state_delta)
                        : []),
                    state_delta: ev.state_delta || ev.payload?.state_delta || null,
                    transfer_to: ev.transfer_to || ev.payload?.transfer_to || null,
                  }))
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
                    })
                    setError(
                      `Stream terputus setelah ${normalized.length} events. ` +
                        `Memuat dari SQLite — klik "Jalankan Analisis" untuk retry.`
                    )
                  }
                })
                .catch(() => {
                  /* SQLite fallback also failed — keep the original error. */
                })
            }
            // readyState === CONNECTING (1) means EventSource is auto-retrying the
            // network — keep `running` true so the UI doesn't flash.
          }, 1200)
        }

        // Safety timeout 15 min
        setTimeout(() => {
          try {
            es.close()
          } catch {}
          setRunning(false)
          setError("Batas waktu 15 menit tercapai. Coba lagi atau gunakan Mode Cepat.")
        }, 15 * 60 * 1000)
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e)
        setError(msg.slice(0, 1000))
        setRunning(false)
      }
    },
    [ticker, apiBase]
  )

  const handleClear = useCallback(() => {
    setLoadedFromDb(null)
    setEvents([])
    setDone(null)
    setError(null)
    setFilterAuthor("all")
  }, [])

  const stateKeys = useMemo(() => {
    const set = new Set<string>()
    for (const ev of events) {
      if (ev.state_delta_keys) {
        for (const k of ev.state_delta_keys) set.add(k)
      }
    }
    return Array.from(set)
  }, [events])

  return (
    <div className="space-y-6">
      {/* 1. Hero & Run Controls */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs sm:p-6 space-y-4">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-slate-900 text-white shadow-xs">
                <Bot className="h-5 w-5" />
              </div>
              <h1 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl font-sans">
                Pusat Analisis Saham Multi-Agen AI
              </h1>
            </div>
            <p className="text-sm text-slate-600 max-w-2xl leading-relaxed">
              Pantau 11 agen AI independen yang bekerja sama mencari data IDX, menghitung valuasi finansial, menguji risiko, dan menyusun riset institusional.
            </p>
          </div>

          {/* Status badge pill */}
          <div className="flex flex-wrap items-center gap-2">
            {running ? (
              <div className="flex items-center gap-2 rounded-xl border border-amber-300 bg-amber-50/80 px-3.5 py-2 text-xs text-amber-900 shadow-2xs">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
                  <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-amber-500" />
                </span>
                <span className="font-semibold">{activeCount} dari {totalCount} agen aktif</span>
                <span className="text-slate-300">·</span>
                <span className="flex items-center gap-1 font-mono text-slate-700">
                  <Activity className="h-3 w-3 text-slate-500" />
                  {events.length} aktivitas
                </span>
                <span className="text-slate-300">·</span>
                <span className="flex items-center gap-1 font-mono font-semibold text-amber-800">
                  <Clock className="h-3 w-3 text-amber-600" />
                  ETA {etaText}
                </span>
              </div>
            ) : done ? (
              <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-3.5 py-2 text-xs font-semibold text-emerald-900 shadow-2xs">
                <Sparkles className="h-4 w-4 text-emerald-600" />
                <span>Analisis Selesai</span>
                <span className="text-slate-300">·</span>
                <span className="font-mono text-slate-700">{done.n_events} aktivitas</span>
                <span className="text-slate-300">·</span>
                <span className="font-mono text-slate-600">{(done.ms / 1000).toFixed(1)}s</span>
              </div>
            ) : isInterrupted ? (
              <div className="flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-3.5 py-2 text-xs font-medium text-amber-900">
                <AlertCircle className="h-4 w-4 text-amber-600" />
                <span>Stream terhenti sementara</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs font-medium text-slate-600">
                <span className="h-2 w-2 rounded-full bg-slate-400" />
                <span>Sistem Siap Dijalankan</span>
              </div>
            )}
          </div>
        </div>

        {/* Input form & buttons */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-100">
          <div className="flex flex-wrap items-center gap-2.5">
            <div className="flex items-center gap-2">
              <label htmlFor="ticker-input" className="text-xs font-medium text-slate-700">
                Kode Saham:
              </label>
              <input
                id="ticker-input"
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                placeholder="BBCA"
                className="h-9 w-24 rounded-lg border border-slate-300 bg-white px-2.5 text-sm font-mono font-bold uppercase text-slate-900 shadow-2xs focus:border-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900"
                maxLength={10}
              />
            </div>

            <Button
              onClick={() => run("stream")}
              disabled={running}
              className="h-9 gap-1.5 bg-slate-900 px-4 text-xs font-medium text-white hover:bg-slate-800 shadow-xs"
            >
              {running ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-white" />
                  <span>Memproses Analisis...</span>
                </>
              ) : (
                <>
                  <Play className="h-3.5 w-3.5 fill-current" />
                  <span>Jalankan Analisis</span>
                </>
              )}
            </Button>

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
                className="flex items-center gap-1 font-mono text-[11px] text-slate-600 bg-slate-50"
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

        {/* Loaded from SQLite Header Line */}
        {loadedFromDb && (
          <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-slate-200 bg-slate-50/90 px-3.5 py-2 text-xs text-slate-700">
            <div className="flex flex-wrap items-center gap-2">
              <Database className="h-3.5 w-3.5 text-slate-500 shrink-0" />
              <span className="font-medium text-slate-800">
                Loaded from SQLite · {loadedFromDb.n_events} events · {formatRelativeTime(loadedFromDb.finished_at || loadedFromDb.started_at)}
              </span>
              {loadedFromDb.status !== "completed" && (
                <Badge
                  variant="outline"
                  className={`text-[11px] font-medium ${
                    loadedFromDb.status === "failed"
                      ? "border-rose-300 bg-rose-50 text-rose-700"
                      : "border-amber-300 bg-amber-50 text-amber-700"
                  }`}
                >
                  {loadedFromDb.status === "failed" ? "Gagal (failed)" : "Terhenti (interrupted)"}
                </Badge>
              )}
            </div>
            {loadedFromDb.status !== "completed" && (
              <Button
                onClick={() => run("stream")}
                disabled={running}
                size="sm"
                variant="outline"
                className="h-7 gap-1 text-xs font-medium text-slate-800 border-slate-300 bg-white hover:bg-slate-100"
              >
                <Play className="h-3 w-3 fill-current" />
                <span>Resume from latest?</span>
              </Button>
            )}
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="flex items-start gap-2.5 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-600 mt-0.5" />
            <div className="space-y-1">
              <span className="font-semibold">Terjadi kendala saat menjalankan pipeline:</span>
              <p className="font-mono text-[11px] break-all">{error}</p>
            </div>
          </div>
        )}
      </div>

      {/* 2. "Cara Kerja Sistem" Expandable */}
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

      {/* 3. SummaryCard (Shows when finished or done) */}
      {done && (
        <SummaryCard ticker={ticker} events={events} done={done} />
      )}

      {/* 4. PhaseTimeline (replaces AgentRail) */}
      <PhaseTimeline
        agentStatuses={agentStatuses}
        selectedAuthor={filterAuthor}
        onFilterAuthor={setFilterAuthor}
        running={running}
        done={done}
      />

      {/* 5. PlainEnglishPanel (replaces raw traces for orang awam) */}
      <PlainEnglishPanel
        events={events}
        running={running}
        ticker={ticker}
        selectedAuthor={filterAuthor}
        onFilterAuthor={setFilterAuthor}
      />

      {/* 6. Raw Debug Toggle (Collapsible for developers/engineers) */}
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
            <div className="font-semibold text-slate-800">Log Frame Event SSE Mentah:</div>
            <div className="max-h-80 overflow-y-auto rounded-lg border border-slate-200 bg-slate-900 p-3 font-mono text-[11px] text-slate-300">
              {events.length === 0 ? (
                <div className="text-slate-500 italic">Belum ada frame event yang diterima.</div>
              ) : (
                events.map((ev) => (
                  <div key={ev.seq} className="border-b border-slate-800 py-1.5">
                    <div className="flex items-center gap-2 text-slate-400">
                      <span className="text-sky-400">#{ev.seq}</span>
                      <span className="font-bold text-amber-300">{ev.author}</span>
                      <span className="text-emerald-400">[{ev.event_type}]</span>
                      <span>node: {ev.node}</span>
                    </div>
                    {ev.text && (
                      <div className="mt-0.5 text-slate-300 whitespace-pre-wrap">{ev.text}</div>
                    )}
                    {ev.function_calls?.length > 0 && (
                      <pre className="mt-0.5 text-xs text-amber-200 overflow-x-auto">
                        {JSON.stringify(ev.function_calls, null, 2)}
                      </pre>
                    )}
                    {ev.function_responses?.length > 0 && (
                      <pre className="mt-0.5 text-xs text-emerald-200 overflow-x-auto">
                        {JSON.stringify(ev.function_responses, null, 2)}
                      </pre>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </details>

      {/* 7. Disclaimer Footer */}
      <p className="text-center text-xs text-slate-500">
        Disclaimer: Produk ini adalah informasi dan sarana edukasi, bukan saran investasi. Keputusan investasi sepenuhnya menjadi tanggung jawab pengguna.
      </p>
    </div>
  )
}
