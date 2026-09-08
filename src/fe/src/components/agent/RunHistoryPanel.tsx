import { memo, useCallback, useEffect, useState, useMemo } from "react"
import {
  History,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Search,
  Check,
  Command,
  Filter,
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
  onOpenCommandPalette?: () => void
  runsList?: AgentRunItem[]
  onRunsFetched?: (runs: AgentRunItem[]) => void
}

function formatRelativeTime(ts: number | undefined | null): string {
  if (!ts) return "-"
  const now = Date.now() / 1000
  const diff = Math.max(0, Math.floor(now - ts))
  if (diff < 10) return "just now"
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

function formatRunDuration(
  startedAt: number,
  finishedAt?: number | null,
  status?: string,
  isActive?: boolean
): string {
  if ((status === "running" || isActive) && !finishedAt) {
    const elapsed = Math.max(0, Math.floor(Date.now() / 1000 - startedAt))
    return `${elapsed}s (live)`
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
  return `${runId.slice(0, 10)}…`
}

function renderStatusBadge(status: string, isActive?: boolean) {
  if (isActive || status === "running") {
    return (
      <span className="inline-flex items-center gap-1 rounded bg-amber-950/80 border border-amber-800 px-1.5 py-0.5 text-[10px] font-mono font-bold text-amber-300">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-500" />
        </span>
        <span>JALAN</span>
      </span>
    )
  }

  switch (status) {
    case "completed":
      return (
        <span className="inline-flex items-center gap-1 rounded bg-emerald-950/80 border border-emerald-800 px-1.5 py-0.5 text-[10px] font-mono font-semibold text-emerald-300">
          <CheckCircle2 className="h-2.5 w-2.5 text-emerald-400 shrink-0" />
          <span>SELESAI</span>
        </span>
      )
    case "interrupted":
      return (
        <span className="inline-flex items-center gap-1 rounded bg-amber-950/60 border border-amber-800/80 px-1.5 py-0.5 text-[10px] font-mono font-medium text-amber-300">
          <AlertCircle className="h-2.5 w-2.5 text-amber-400 shrink-0" />
          <span>TERHENTI</span>
        </span>
      )
    case "failed":
      return (
        <span className="inline-flex items-center gap-1 rounded bg-rose-950/80 border border-rose-800 px-1.5 py-0.5 text-[10px] font-mono font-semibold text-rose-300">
          <AlertCircle className="h-2.5 w-2.5 text-rose-400 shrink-0" />
          <span>GAGAL</span>
        </span>
      )
    default:
      return (
        <span className="inline-flex items-center gap-1 rounded bg-neutral-900 border border-neutral-700 px-1.5 py-0.5 text-[10px] font-mono text-neutral-400">
          <span className="h-1.5 w-1.5 rounded-full bg-neutral-500" />
          <span>{status.toUpperCase()}</span>
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
  onOpenCommandPalette,
  runsList,
  onRunsFetched,
}: RunHistoryPanelProps) {
  const [localRuns, setLocalRuns] = useState<AgentRunItem[]>([])
  const runs = runsList ?? localRuns
  const [loading, setLoading] = useState(true)
  const [isFetching, setIsFetching] = useState(false)
  const [filterText, setFilterText] = useState("")
  const [statusFilter, setStatusFilter] = useState<"ALL" | "LIVE" | "DONE" | "FAIL">("ALL")

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
          setLocalRuns(fetchedRuns)
          onRunsFetched?.(fetchedRuns)
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
    [apiBase, onRunsFetched]
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

  const filteredRuns = useMemo(() => {
    return runs.filter((r) => {
      if (statusFilter === "LIVE" && !(r.status === "running" || r.is_active)) return false
      if (statusFilter === "DONE" && r.status !== "completed") return false
      if (statusFilter === "FAIL" && r.status !== "failed" && r.status !== "interrupted") return false

      if (filterText) {
        const q = filterText.toLowerCase().trim()
        const tMatch = r.ticker.toLowerCase().includes(q)
        const idMatch = r.run_id.toLowerCase().includes(q)
        const statusMatch = r.status.toLowerCase().includes(q)
        return tMatch || idMatch || statusMatch
      }
      return true
    })
  }, [runs, statusFilter, filterText])

  return (
    <div
      className={`rounded-lg border border-neutral-800 bg-neutral-950 text-neutral-100 shadow-md overflow-hidden flex flex-col font-sans ${className}`}
    >
      {/* Header Bar */}
      <div className="flex items-center justify-between gap-2 p-3 border-b border-neutral-800 bg-neutral-900/90">
        <div className="flex items-center gap-2 min-w-0">
          <div className="flex h-6 w-6 items-center justify-center rounded bg-neutral-800 text-neutral-300 border border-neutral-700 shrink-0">
            <History className="h-3.5 w-3.5 text-emerald-400" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <h2 className="text-xs font-mono font-bold uppercase tracking-wide text-neutral-100 truncate">
                RIWAYAT PROSES
              </h2>
              <Badge
                variant="secondary"
                className="font-mono text-[9px] text-neutral-300 bg-neutral-800 border-neutral-700 px-1 py-0 shrink-0"
              >
                {runs.length}
              </Badge>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1">
          {hasRunning && (
            <span
              className="relative flex h-2 w-2 mr-1"
              title={`${runningRuns.length} active runs`}
            >
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-500" />
            </span>
          )}

          {onOpenCommandPalette && (
            <button
              type="button"
              onClick={onOpenCommandPalette}
              className="flex items-center gap-1 rounded bg-neutral-800 hover:bg-neutral-700 border border-neutral-700 px-1.5 py-1 text-[10px] font-mono text-neutral-300 transition-colors"
              title="Open Command Palette (⌘K)"
            >
              <Command className="h-2.5 w-2.5" />
              <span className="hidden sm:inline">K</span>
            </button>
          )}

          <Button
            variant="ghost"
            size="sm"
            onClick={() => fetchRuns(false)}
            disabled={isFetching}
            className="h-6 w-6 p-0 text-neutral-400 hover:text-white hover:bg-neutral-800 shrink-0"
            title="Refresh run history"
          >
            <RefreshCw
              className={`h-3 w-3 ${isFetching ? "animate-spin text-emerald-400" : ""}`}
            />
          </Button>
        </div>
      </div>

      {/* Quick Search & Status Filter */}
      <div className="p-2 border-b border-neutral-800 bg-neutral-950/90 space-y-1.5">
        <div className="relative flex items-center">
          <Search className="absolute left-2 h-3 w-3 text-neutral-500" />
          <input
            type="text"
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            placeholder="Filter runs (e.g. BBCA, failed)..."
            className="w-full rounded bg-neutral-900 border border-neutral-800 pl-7 pr-2 py-1 text-[11px] font-mono text-neutral-200 placeholder:text-neutral-600 focus:outline-none focus:border-neutral-700"
          />
        </div>

        <div className="flex items-center justify-between text-[10px] font-mono">
          <div className="flex items-center gap-1 text-neutral-500">
            <Filter className="h-2.5 w-2.5" />
            <span>STATUS:</span>
          </div>
          <div className="flex items-center gap-1">
            {(["ALL", "LIVE", "DONE", "FAIL"] as const).map((st) => (
              <button
                key={st}
                type="button"
                onClick={() => setStatusFilter(st)}
                className={`px-1.5 py-0.5 rounded text-[9px] font-mono transition-colors ${
                  statusFilter === st
                    ? "bg-neutral-800 text-white font-bold border border-neutral-600"
                    : "text-neutral-400 hover:text-neutral-200"
                }`}
              >
                {st === "ALL" ? "SEMUA" : st === "LIVE" ? "JALAN" : st === "DONE" ? "SELESAI" : "GAGAL"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Body List */}
      <div className="flex-1">
        {loading ? (
          <div className="flex items-center justify-center py-10 text-xs font-mono text-neutral-500">
            <RefreshCw className="mr-2 h-3.5 w-3.5 animate-spin text-emerald-500" />
            <span>FETCHING RUNS...</span>
          </div>
        ) : filteredRuns.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 px-4 text-center font-mono text-xs">
            <p className="text-neutral-400 font-semibold">BELUM ADA PROSES</p>
            <p className="text-[11px] text-neutral-600 mt-1">
              {filterText ? "No runs matching query." : "Execute a run to populate history."}
            </p>
          </div>
        ) : (
          <div className="max-h-[calc(100vh-280px)] overflow-y-auto divide-y divide-neutral-900 scrollbar-thin">
            {filteredRuns.map((run) => {
              const isSelected = selectedRunId === run.run_id
              const isCurrentTicker =
                run.ticker.toUpperCase() === (currentTicker || "").toUpperCase()

              return (
                <button
                  type="button"
                  key={run.run_id}
                  onClick={() => onSelectRun(run.run_id)}
                  className={`w-full text-left p-2.5 transition-colors cursor-pointer block focus:outline-none ${
                    isSelected
                      ? "bg-neutral-900/90 border-l-2 border-emerald-400 text-white"
                      : "hover:bg-neutral-900/50 text-neutral-300"
                  }`}
                >
                  {/* Line 1: Ticker & Status */}
                  <div className="flex items-center justify-between gap-1.5">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <span className="font-mono font-bold text-neutral-100 text-xs">
                        {run.ticker}
                      </span>
                      {isCurrentTicker && (
                        <span
                          className="h-1.5 w-1.5 rounded-full bg-emerald-400 shrink-0"
                          title="Current active target ticker"
                        />
                      )}
                      {isSelected && (
                        <Check className="h-3 w-3 text-emerald-400 shrink-0 ml-0.5" />
                      )}
                    </div>
                    <div className="shrink-0">
                      {renderStatusBadge(run.status, run.is_active)}
                    </div>
                  </div>

                  {/* Line 2: Events & Started time */}
                  <div className="flex items-center justify-between text-[10px] text-neutral-500 font-mono mt-1">
                    <span>{run.n_events} EVTS</span>
                    <span
                      title={
                        run.started_at
                          ? new Date(run.started_at * 1000).toLocaleString()
                          : undefined
                      }
                    >
                      {formatRelativeTime(run.started_at)}
                    </span>
                  </div>

                  {/* Line 3: Truncated ID & Duration */}
                  <div className="flex items-center justify-between text-[9px] text-neutral-600 font-mono mt-0.5">
                    <span title={run.run_id}>{truncateRunId(run.run_id)}</span>
                    <span className="text-neutral-400">
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

      {/* Footer Info */}
      <div className="p-2 border-t border-neutral-800 bg-neutral-900/60 text-[10px] font-mono text-neutral-500 flex items-center justify-between">
        <span>ARSIP TERSIMPAN</span>
        <span>5s auto-poll</span>
      </div>
    </div>
  )
})
