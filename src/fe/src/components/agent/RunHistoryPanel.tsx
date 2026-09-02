import { memo, useCallback, useEffect, useRef, useState } from "react"
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
  if (!ts) return "—"
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
  if (!finishedAt || !startedAt) return "—"
  const diff = Math.max(0, finishedAt - startedAt)
  if (diff < 1) return `${Math.round(diff * 1000)}ms`
  if (diff < 60) return `${diff.toFixed(1)}s`
  const mins = Math.floor(diff / 60)
  const secs = Math.floor(diff % 60)
  return `${mins}m ${secs}s`
}

function truncateRunId(runId: string): string {
  if (!runId) return "—"
  if (runId.length <= 16) return runId
  return `${runId.slice(0, 14)}…`
}

function renderStatusBadge(status: string, isActive?: boolean) {
  if (isActive || status === "running") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-md border border-amber-300 bg-amber-50 px-2 py-0.5 text-[11px] font-semibold text-amber-800">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-500" />
        </span>
        <span>Berjalan</span>
        <span className="inline-flex items-center font-mono text-[10px] text-amber-900 font-bold ml-0.5">
          ● Live
        </span>
      </span>
    )
  }

  switch (status) {
    case "completed":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-md border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-800">
          <CheckCircle2 className="h-3 w-3 text-emerald-600 shrink-0" />
          <span>Selesai</span>
        </span>
      )
    case "interrupted":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-md border border-amber-200 bg-amber-50 px-2 py-0.5 text-[11px] font-medium text-amber-800">
          <AlertCircle className="h-3 w-3 text-amber-600 shrink-0" />
          <span>Terhenti</span>
        </span>
      )
    case "failed":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-md border border-rose-200 bg-rose-50 px-2 py-0.5 text-[11px] font-medium text-rose-800">
          <AlertCircle className="h-3 w-3 text-rose-600 shrink-0" />
          <span>Gagal</span>
        </span>
      )
    default:
      return (
        <span className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-slate-50 px-2 py-0.5 text-[11px] font-medium text-slate-700">
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
  const [isCollapsed, setIsCollapsed] = useState(false)
  const hasInitializedCollapseRef = useRef(false)
  const userToggledRef = useRef(false)

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

          if (!hasInitializedCollapseRef.current && !userToggledRef.current) {
            hasInitializedCollapseRef.current = true
            setIsCollapsed(fetchedRuns.length > 5)
          }
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

  const handleToggleCollapse = useCallback(() => {
    userToggledRef.current = true
    setIsCollapsed((prev) => !prev)
  }, [])

  const handleManualRefresh = useCallback(() => {
    fetchRuns(false)
  }, [fetchRuns])

  const runningRuns = runs.filter((r) => r.status === "running" || r.is_active)
  const hasRunning = runningRuns.length > 0

  return (
    <div
      className={`rounded-2xl border border-slate-200 bg-white shadow-xs overflow-hidden ${className}`}
    >
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 sm:px-5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-slate-100 text-slate-800 border border-slate-200/80 shadow-2xs">
            <History className="h-4 w-4 text-slate-700" />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-sm font-bold tracking-tight text-slate-900 font-sans">
              Riwayat Run Analisis
            </h2>
            <Badge
              variant="secondary"
              className="font-mono text-[11px] text-slate-600 bg-slate-100 border border-slate-200/60 px-2 py-0.5"
            >
              {runs.length} {runs.length === 1 ? "run" : "runs"}
            </Badge>

            {hasRunning && (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-300 bg-amber-50 px-2.5 py-0.5 text-[11px] font-semibold text-amber-900 shadow-2xs">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-500" />
                </span>
                <span>{runningRuns.length} Live Berjalan</span>
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleManualRefresh}
            disabled={isFetching}
            className="h-8 w-8 p-0 text-slate-500 hover:text-slate-900 hover:bg-slate-100"
            title="Perbarui riwayat run"
          >
            <RefreshCw
              className={`h-3.5 w-3.5 ${isFetching ? "animate-spin text-slate-800" : ""}`}
            />
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleToggleCollapse}
            className="h-8 px-2.5 text-xs text-slate-700 hover:text-slate-900 hover:bg-slate-50 flex items-center gap-1.5 border-slate-200 shadow-2xs"
          >
            {isCollapsed ? (
              <>
                <ChevronDown className="h-3.5 w-3.5 text-slate-500" />
                <span>Lihat Riwayat ({runs.length})</span>
              </>
            ) : (
              <>
                <ChevronUp className="h-3.5 w-3.5 text-slate-500" />
                <span>Sembunyikan</span>
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Collapsible Content */}
      {!isCollapsed && (
        <>
          {/* Sub-header Hint */}
          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 bg-slate-50/70 px-4 py-2 text-[11px] text-slate-500 sm:px-5">
            <div className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-slate-400" />
              <span>
                Auto-loading latest for{" "}
                <strong className="font-mono font-semibold text-slate-800">
                  {currentTicker || "BBCA"}
                </strong>
              </span>
            </div>
            <span className="text-slate-400">
              Klik baris untuk memuat jejak analisis &amp; hasil valuasi
            </span>
          </div>

          {/* Body: Table or Empty State */}
          {loading ? (
            <div className="flex items-center justify-center py-8 text-xs text-slate-500">
              <RefreshCw className="mr-2 h-4 w-4 animate-spin text-slate-400" />
              <span>Memuat riwayat run...</span>
            </div>
          ) : runs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 px-4 text-center">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-400 mb-2 border border-slate-200">
                <Database className="h-5 w-5" />
              </div>
              <p className="text-xs font-semibold text-slate-800">
                Belum ada run history.
              </p>
              <p className="text-xs text-slate-500 mt-0.5">
                Klik "Jalankan Analisis" untuk memulai.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-600 border-collapse">
                <thead>
                  <tr className="border-t border-b border-slate-200 bg-slate-50/90 text-[11px] font-semibold text-slate-700 uppercase tracking-wider font-mono">
                    <th className="py-2.5 px-4 sm:px-5">Saham</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Aktivitas</th>
                    <th className="py-2.5 px-3">Waktu Mulai</th>
                    <th className="py-2.5 px-3">Durasi</th>
                    <th className="py-2.5 px-3">ID Run</th>
                    <th className="py-2.5 px-4 text-right">Aksi</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {runs.map((run) => {
                    const isSelected = selectedRunId === run.run_id
                    const isCurrentTicker =
                      run.ticker.toUpperCase() === (currentTicker || "").toUpperCase()

                    return (
                      <tr
                        key={run.run_id}
                        onClick={() => onSelectRun(run.run_id)}
                        className={`group cursor-pointer transition-colors ${
                          isSelected
                            ? "bg-slate-100/90 font-medium text-slate-900"
                            : "hover:bg-slate-50/80 text-slate-700"
                        }`}
                      >
                        {/* Ticker */}
                        <td className="py-2.5 px-4 sm:px-5 whitespace-nowrap">
                          <div className="flex items-center gap-1.5">
                            <span className="font-mono font-bold text-slate-900 text-[13px]">
                              {run.ticker}
                            </span>
                            {isCurrentTicker && (
                              <span
                                className="h-1.5 w-1.5 rounded-full bg-slate-900"
                                title="Saham saat ini dipilih"
                              />
                            )}
                          </div>
                        </td>

                        {/* Status badge */}
                        <td className="py-2.5 px-3 whitespace-nowrap">
                          {renderStatusBadge(run.status, run.is_active)}
                        </td>

                        {/* Events count */}
                        <td className="py-2.5 px-3 whitespace-nowrap font-mono text-[11px] text-slate-700">
                          {run.n_events} aktivitas
                        </td>

                        {/* Started time (relative) */}
                        <td
                          className="py-2.5 px-3 whitespace-nowrap text-slate-600 text-[11px]"
                          title={
                            run.started_at
                              ? new Date(run.started_at * 1000).toLocaleString("id-ID")
                              : undefined
                          }
                        >
                          {formatRelativeTime(run.started_at)}
                        </td>

                        {/* Duration */}
                        <td className="py-2.5 px-3 whitespace-nowrap font-mono text-[11px] text-slate-600">
                          {formatRunDuration(run.started_at, run.finished_at, run.status, run.is_active)}
                        </td>

                        {/* Run ID */}
                        <td className="py-2.5 px-3 whitespace-nowrap font-mono text-[11px] text-slate-500">
                          <span title={run.run_id}>{truncateRunId(run.run_id)}</span>
                        </td>

                        {/* Selection Action */}
                        <td className="py-2.5 px-4 text-right whitespace-nowrap">
                          {isSelected ? (
                            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-900">
                              <Check className="h-3 w-3 text-slate-900" />
                              <span>Dimuat</span>
                            </span>
                          ) : (
                            <span className="text-[11px] text-slate-400 group-hover:text-slate-900 transition-colors">
                              Pilih &rarr;
                            </span>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  )
})
