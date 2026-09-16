import { memo, useCallback, useEffect, useState, useMemo } from "react"
import {
  History,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Search,
  Check,
} from "lucide-react"

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
  runsList?: AgentRunItem[]
  onRunsFetched?: (runs: AgentRunItem[]) => void
}

function formatRelativeTime(ts: number | undefined | null): string {
  if (!ts) return "-"
  const now = Date.now() / 1000
  const diff = Math.max(0, Math.floor(now - ts))
  if (diff < 10) return "baru saja"
  if (diff < 60) return `${diff} detik lalu`
  if (diff < 3600) return `${Math.floor(diff / 60)} menit lalu`
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
    return `${elapsed} detik (aktif)`
  }
  if (!finishedAt || !startedAt) return "-"
  const diff = Math.max(0, finishedAt - startedAt)
  if (diff < 1) return `${Math.round(diff * 1000)} ms`
  if (diff < 60) return `${diff.toFixed(1)} detik`
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
      <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 px-2 py-0.5 text-[11px] font-medium text-amber-800 dark:text-amber-300">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-500" />
        </span>
        <span>Sedang diproses</span>
      </span>
    )
  }

  switch (status) {
    case "completed":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 px-2 py-0.5 text-[11px] font-medium text-emerald-800 dark:text-emerald-300">
          <CheckCircle2 className="h-3 w-3 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <span>Selesai</span>
        </span>
      )
    case "interrupted":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 px-2 py-0.5 text-[11px] font-medium text-amber-800 dark:text-amber-300">
          <AlertCircle className="h-3 w-3 text-amber-600 dark:text-amber-400 shrink-0" />
          <span>Terhenti</span>
        </span>
      )
    case "failed":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 px-2 py-0.5 text-[11px] font-medium text-[#B4232A] dark:text-rose-300">
          <AlertCircle className="h-3 w-3 text-[#B4232A] shrink-0" />
          <span>Gagal</span>
        </span>
      )
    default:
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-[#F5F2EB] dark:bg-[#23211C] border border-[#E7E3DA] dark:border-[#2A2822] px-2 py-0.5 text-[11px] text-[#6B6659] dark:text-[#A8A296]">
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
  runsList,
  onRunsFetched,
}: RunHistoryPanelProps) {
  const [localRuns, setLocalRuns] = useState<AgentRunItem[]>([])
  const runs = runsList ?? localRuns
  const [loading, setLoading] = useState(true)
  const [isFetching, setIsFetching] = useState(false)
  const [filterText, setFilterText] = useState("")

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

  const filteredRuns = useMemo(() => {
    return runs.filter((r) => {
      if (filterText) {
        const q = filterText.toLowerCase().trim()
        const tMatch = r.ticker.toLowerCase().includes(q)
        const idMatch = r.run_id.toLowerCase().includes(q)
        const statusMatch = r.status.toLowerCase().includes(q)
        return tMatch || idMatch || statusMatch
      }
      return true
    })
  }, [runs, filterText])

  return (
    <div
      className={`rounded-xl border border-[#E7E3DA] dark:border-[#2A2822] bg-white dark:bg-[#1B1A16] p-5 font-sans space-y-3.5 shadow-none ${className}`}
    >
      {/* Header Bar */}
      <div className="flex items-center justify-between gap-2 pb-3 border-b border-[#E7E3DA]/60 dark:border-[#2A2822]/60">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#F5F2EB] dark:bg-[#23211C] text-[#0E6E63] dark:text-[#4FD1B5] border border-[#E7E3DA] dark:border-[#2A2822] shrink-0">
            <History className="h-4 w-4" />
          </div>
          <div>
            <h3 className="font-serif text-base font-medium text-[#1C1B17] dark:text-[#EDEAE3] truncate">
              Riwayat proses
            </h3>
            <p className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">
              {runs.length} catatan tersimpan
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => fetchRuns(false)}
          disabled={isFetching}
          className="h-7 w-7 inline-flex items-center justify-center rounded-lg border border-[#E7E3DA] dark:border-[#2A2822] bg-white dark:bg-[#1B1A16] text-[#6B6659] dark:text-[#A8A296] hover:bg-[#F5F2EB] dark:hover:bg-[#23211C] shrink-0 transition-colors"
          title="Segarkan riwayat proses"
        >
          <RefreshCw
            className={`h-3.5 w-3.5 ${isFetching ? "animate-spin text-[#0E6E63] dark:text-[#4FD1B5]" : ""}`}
          />
        </button>
      </div>

      {/* Quick Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#6B6659] dark:text-[#A8A296]" />
        <input
          type="text"
          value={filterText}
          onChange={(e) => setFilterText(e.target.value)}
          placeholder="Saring riwayat (mis. BBCA)..."
          className="w-full rounded-lg border border-[#E7E3DA] dark:border-[#2A2822] bg-white dark:bg-[#1B1A16] pl-9 pr-3 py-1.5 text-xs text-[#1C1B17] dark:text-[#EDEAE3] placeholder:text-[#6B6659]/70 dark:placeholder:text-[#A8A296]/70 focus:outline-none focus:border-[#0E6E63] dark:focus:border-[#4FD1B5]"
        />
      </div>

      {/* Body List */}
      <div>
        {loading ? (
          <div className="flex items-center justify-center py-8 text-xs text-[#6B6659] dark:text-[#A8A296]">
            <RefreshCw className="mr-2 h-3.5 w-3.5 animate-spin text-[#0E6E63] dark:text-[#4FD1B5]" />
            <span>Memuat riwayat proses…</span>
          </div>
        ) : filteredRuns.length === 0 ? (
          <div className="py-8 px-3 text-center text-xs space-y-1">
            <p className="font-medium text-[#1C1B17] dark:text-[#EDEAE3]">Belum ada riwayat proses</p>
            <p className="text-[#6B6659] dark:text-[#A8A296] text-[11px]">
              {filterText ? "Tidak ada proses yang cocok dengan kata kunci." : "Jalankan analisis untuk menyimpan riwayat."}
            </p>
          </div>
        ) : (
          <div className="max-h-[360px] overflow-y-auto divide-y divide-[#E7E3DA]/60 dark:divide-[#2A2822]/60">
            {filteredRuns.map((run) => {
              const isSelected = selectedRunId === run.run_id
              const isCurrentTicker =
                run.ticker.toUpperCase() === (currentTicker || "").toUpperCase()

              return (
                <button
                  type="button"
                  key={run.run_id}
                  onClick={() => onSelectRun(run.run_id)}
                  className={`w-full text-left p-3 transition-colors cursor-pointer block rounded-lg my-0.5 focus:outline-none ${
                    isSelected
                      ? "bg-[#0E6E63]/10 dark:bg-[#4FD1B5]/15 border border-[#0E6E63]/30 dark:border-[#4FD1B5]/30 text-[#1C1B17] dark:text-[#EDEAE3]"
                      : "hover:bg-[#FBFAF7] dark:hover:bg-[#14130F] text-[#1C1B17] dark:text-[#EDEAE3]"
                  }`}
                >
                  {/* Line 1: Ticker & Status */}
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <span className="font-serif font-medium text-sm text-[#1C1B17] dark:text-[#EDEAE3]">
                        {run.ticker}
                      </span>
                      {isCurrentTicker && (
                        <span
                          className="h-1.5 w-1.5 rounded-full bg-[#0E6E63] dark:bg-[#4FD1B5] shrink-0"
                          title="Emiten yang sedang dibuka"
                        />
                      )}
                      {isSelected && (
                        <Check className="h-3.5 w-3.5 text-[#0E6E63] dark:text-[#4FD1B5] shrink-0 ml-0.5" />
                      )}
                    </div>
                    <div className="shrink-0">
                      {renderStatusBadge(run.status, run.is_active)}
                    </div>
                  </div>

                  {/* Line 2: Events & Started time */}
                  <div className="flex items-center justify-between text-[11px] text-[#6B6659] dark:text-[#A8A296] mt-1">
                    <span>{run.n_events} langkah</span>
                    <span>{formatRelativeTime(run.started_at)}</span>
                  </div>

                  {/* Line 3: ID & Duration */}
                  <div className="flex items-center justify-between text-[11px] text-[#6B6659]/80 dark:text-[#A8A296]/80 mt-0.5">
                    <span>ID: {truncateRunId(run.run_id)}</span>
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
