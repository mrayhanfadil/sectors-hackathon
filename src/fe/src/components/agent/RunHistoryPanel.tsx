import { memo, useCallback, useEffect, useState } from "react"
import {
  History,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Database,
  Check,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

export interface AgentRunItem {
  run_id: string
  ticker: string
  status: "running" | "completed" | "interrupted" | "failed" | string
  n_events: number
  started_at: number
  finished_at?: number | null
  error?: string | null
  reason?: string | null
  provider?: string | null
  model?: string | null
  prompt?: string | null
  is_active?: boolean
}

export interface RunHistoryPanelProps {
  currentTicker: string
  selectedRunId?: string | null
  onSelectRun: (runId: string) => void
  apiBase?: string
  className?: string
}

function formatRelativeTime(ts: number | undefined | null): string {
  if (!ts) return "-"
  const now = Date.now() / 1000
  const diff = Math.max(0, Math.floor(now - ts))
  if (diff < 10) return "baru saja"
  if (diff < 60) return `${diff} dtk lalu`
  if (diff < 3600) return `${Math.floor(diff / 60)} mnt lalu`
  if (diff < 86400) return `${Math.floor(diff / 3600)} jam lalu`
  return `${Math.floor(diff / 86400)} hari lalu`
}

function formatRunDuration(
  startedAt: number,
  finishedAt?: number | null,
  status?: string,
  isActive?: boolean
): string {
  if ((status === "running" || isActive) && !finishedAt) {
    const elapsed = Math.max(0, Math.floor(Date.now() / 1000 - startedAt))
    return `${elapsed}s (aktif)`
  }
  if (!finishedAt || !startedAt) return "-"
  const diff = Math.max(0, finishedAt - startedAt)
  if (diff < 1) return `${Math.round(diff * 1000)}ms`
  if (diff < 60) return `${diff.toFixed(1)}s`
  const mins = Math.floor(diff / 60)
  const secs = Math.floor(diff % 60)
  return `${mins}m ${secs}s`
}

function truncateRunId(runId: string): string {
  if (!runId) return "-"
  if (runId.length <= 14) return runId
  return `${runId.slice(0, 12)}...`
}

function renderStatusBadge(status: string, isActive?: boolean) {
  if (isActive || status === "running") {
    return (
      <span className="inline-flex items-center gap-1 rounded-md border border-amber-300 bg-amber-50 px-1.5 py-0.5 text-[10px] font-semibold text-amber-800">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-500" />
        </span>
        <span>Live</span>
      </span>
    )
  }

  switch (status) {
    case "completed":
      return (
        <span className="inline-flex items-center gap-1 rounded-md border border-emerald-200 bg-emerald-50 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-800">
          <CheckCircle2 className="h-3 w-3 text-emerald-600 shrink-0" />
          <span>Selesai</span>
        </span>
      )
    case "interrupted":
      return (
        <span className="inline-flex items-center gap-1 rounded-md border border-amber-200 bg-amber-50 px-1.5 py-0.5 text-[10px] font-medium text-amber-800">
          <AlertCircle className="h-3 w-3 text-amber-600 shrink-0" />
          <span>Terhenti</span>
        </span>
      )
    case "failed":
      return (
        <span className="inline-flex items-center gap-1 rounded-md border border-rose-200 bg-rose-50 px-1.5 py-0.5 text-[10px] font-medium text-rose-800">
          <AlertCircle className="h-3 w-3 text-rose-600 shrink-0" />
          <span>Gagal</span>
        </span>
      )
    default:
      return (
        <span className="inline-flex items-center gap-1 rounded-md border border-slate-200 bg-slate-50 px-1.5 py-0.5 text-[10px] font-medium text-slate-700">
          <span className="h-1.5 w-1.5 rounded-full bg-slate-400" />
          <span>{status}</span>
        </span>
      )
  }
}

export const RunHistoryPanel = memo(function RunHistoryPanel({
  currentTicker,
  selectedRunId,
  onSelectRun,
  apiBase = "",
  className = "",
}: RunHistoryPanelProps) {
  const [runs, setRuns] = useState<AgentRunItem[]>([])
  const [loading, setLoading] = useState(true)
  const [isFetching, setIsFetching] = useState(false)
  const [isCollapsedMobile, setIsCollapsedMobile] = useState(false)

  const fetchRuns = useCallback(
    async (isInitial = false) => {
      if (isInitial) {
        setLoading(true)
      } else {
        setIsFetching(true)
      }

      try {
        const res = await fetch(`${apiBase}/api/agent/runs`)
        if (res.ok) {
          const data = await res.json()
          const fetchedRuns: AgentRunItem[] = Array.isArray(data?.runs) ? data.runs : []
          setRuns(fetchedRuns)
        }
      } catch {
        // Silently handle polling failure
      } finally {
        if (isInitial) {
          setLoading(false)
        }
        setIsFetching(false)
      }
    },
    [apiBase]
  )

  useEffect(() => {
    fetchRuns(true)
    const intervalId = setInterval(() => {
      fetchRuns(false)
    }, 5000)

    return () => clearInterval(intervalId)
  }, [fetchRuns])

  const runningRuns = runs.filter((r) => r.status === "running" || r.is_active)
  const hasRunning = runningRuns.length > 0

  return (
    <div
      className={`rounded-2xl border border-slate-200 bg-white shadow-xs overflow-hidden flex flex-col ${className}`}
    >
      {/* Header Bar */}
      <div className="flex items-center justify-between gap-2 p-3.5 border-b border-slate-100 bg-white">
        <div className="flex items-center gap-2 min-w-0">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-slate-100 text-slate-800 border border-slate-200 shadow-2xs shrink-0">
            <History className="h-3.5 w-3.5 text-slate-700" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <h2 className="text-xs font-bold tracking-tight text-slate-900 font-sans truncate">
                Riwayat Run
              </h2>
              <Badge
                variant="secondary"
                className="font-mono text-[10px] text-slate-600 bg-slate-100 border border-slate-200/60 px-1.5 py-0 shrink-0"
              >
                {runs.length}
              </Badge>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1">
          {hasRunning && (
            <span
              className="relative flex h-2.5 w-2.5 mr-1"
              title={`${runningRuns.length} run sedang berjalan`}
            >
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-amber-500" />
            </span>
          )}

          <Button
            variant="ghost"
            size="sm"
            onClick={() => fetchRuns(false)}
            disabled={isFetching}
            className="h-7 w-7 p-0 text-slate-500 hover:text-slate-900 hover:bg-slate-100 shrink-0"
            title="Perbarui riwayat run"
          >
            <RefreshCw
              className={`h-3 w-3 ${isFetching ? "animate-spin text-slate-800" : ""}`}
            />
          </Button>

          {/* Toggle for mobile screens only */}
          <button
            type="button"
            onClick={() => setIsCollapsedMobile((prev) => !prev)}
            className="sm:hidden p-1 text-slate-500 hover:text-slate-900"
            title="Toggle riwayat run"
          >
            {isCollapsedMobile ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronUp className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>

      {/* Sub-header text */}
      <div className="bg-slate-50/80 px-3.5 py-1.5 text-[11px] text-slate-500 border-b border-slate-100 flex items-center justify-between">
        <span>Klik baris untuk memuat jejak</span>
        {currentTicker && (
          <span className="font-mono font-bold text-slate-700">{currentTicker}</span>
        )}
      </div>

      {/* Body List */}
      <div className={`${isCollapsedMobile ? "hidden sm:block" : "block"}`}>
        {loading ? (
          <div className="flex items-center justify-center py-8 text-xs text-slate-500">
            <RefreshCw className="mr-2 h-3.5 w-3.5 animate-spin text-slate-400" />
            <span>Memuat riwayat...</span>
          </div>
        ) : runs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 px-4 text-center">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-100 text-slate-400 mb-2 border border-slate-200">
              <Database className="h-4 w-4" />
            </div>
            <p className="text-xs font-semibold text-slate-800">
              Belum ada riwayat run
            </p>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Klik "Jalankan Analisis" untuk memulai.
            </p>
          </div>
        ) : (
          <div className="max-h-[calc(100vh-240px)] overflow-y-auto divide-y divide-slate-100">
            {runs.map((run) => {
              const isSelected = selectedRunId === run.run_id
              const isCurrentTicker =
                run.ticker.toUpperCase() === (currentTicker || "").toUpperCase()

              return (
                <button
                  type="button"
                  key={run.run_id}
                  onClick={() => onSelectRun(run.run_id)}
                  className={`w-full text-left p-3 transition-colors cursor-pointer block focus:outline-none ${
                    isSelected
                      ? "bg-slate-100/90 font-medium text-slate-900 border-l-2 border-slate-900"
                      : "hover:bg-slate-50/80 text-slate-700"
                  }`}
                >
                  {/* Line 1: Ticker & Status */}
                  <div className="flex items-center justify-between gap-1.5">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <span className="font-mono font-bold text-slate-900 text-xs">
                        {run.ticker}
                      </span>
                      {isCurrentTicker && (
                        <span
                          className="h-1.5 w-1.5 rounded-full bg-slate-900 shrink-0"
                          title="Saham saat ini dipilih di input"
                        />
                      )}
                      {isSelected && (
                        <Check className="h-3 w-3 text-slate-900 shrink-0 ml-0.5" />
                      )}
                    </div>
                    <div className="shrink-0">
                      {renderStatusBadge(run.status, run.is_active)}
                    </div>
                  </div>

                  {/* Line 2: Events & Started time */}
                  <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono mt-1.5">
                    <span>{run.n_events} aktivitas</span>
                    <span
                      title={
                        run.started_at
                          ? new Date(run.started_at * 1000).toLocaleString("id-ID")
                          : undefined
                      }
                    >
                      {formatRelativeTime(run.started_at)}
                    </span>
                  </div>

                  {/* Line 3: Truncated ID & Duration */}
                  <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono mt-1">
                    <span title={run.run_id}>{truncateRunId(run.run_id)}</span>
                    <span>
                      {formatRunDuration(
                        run.started_at,
                        run.finished_at,
                        run.status,
                        run.is_active
                      )}
                    </span>
                  </div>
                </button>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
})
