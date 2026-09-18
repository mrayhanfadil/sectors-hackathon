import { memo } from "react"
import {
  Play,
  RotateCcw,
  RefreshCw,
  Cpu,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Clock,
  Activity,
} from "lucide-react"
import { AgentRail } from "./AgentRail"
import { SUPPORTED_TICKERS, normalizeTicker } from "./tickers"
import {
  useAgentProgress,
  type TraceEvent,
} from "./useAgentProgress"

export interface ProgressHeaderHealth {
  ok?: boolean
  model?: string
  provider?: string
  elapsed_ms?: number
  bridge_ping?: string
  bridge_error?: string
  graph?: { name: string; n_subagents?: number; subagents?: string[] }
}

export interface ProgressHeaderProps {
  ticker: string
  onTickerChange: (ticker: string) => void
  onRun: (mode: "stream" | "blocking") => void
  onClear: () => void
  running: boolean
  done: { n_events: number; state_keys: string[]; ms: number } | null
  error: string | null
  events: TraceEvent[]
  health: ProgressHeaderHealth | null
  onRefreshHealth: () => void
  selectedFilter: string
  onFilterChange: (filter: string) => void
}

export const ProgressHeader = memo(function ProgressHeader({
  ticker,
  onTickerChange,
  onRun,
  onClear,
  running,
  done,
  error,
  events,
  health,
  onRefreshHealth,
  selectedFilter,
  onFilterChange,
}: ProgressHeaderProps) {
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

  return (
    <div className="rounded-xl border border-[#D9D9D9] dark:border-[#262930] bg-white dark:bg-[#090a0c] p-5 sm:p-6 space-y-4 font-sans shadow-none">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1.5 max-w-3xl">
          <h2 className="font-serif text-xl font-medium tracking-tight text-[#333333] dark:text-[#f1f5f9]">
            Orkestrator alur kerja mesin
          </h2>
          <p className="text-xs leading-relaxed text-[#666666] dark:text-[#666666]">
            Alur kerja multi-agen untuk analisis laporan keuangan emiten IDX.
          </p>

          {health && (
            <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-[#666666] dark:text-[#666666]">
                <span
                  className={`h-1.5 w-1.5 rounded-full ${
                    health.ok ? "bg-emerald-500" : "bg-amber-500"
                  }`}
                />
                <span>{health.model || "muse-spark-1.2"}</span>
              </span>
              <button
                type="button"
                className="text-xs text-[#0928B1] dark:text-[#7596FF] hover:underline"
                onClick={onRefreshHealth}
              >
                Segarkan status
              </button>
            </div>
          )}
        </div>

        <div className="flex flex-col items-end gap-1.5 text-xs">
          {running ? (
            <div className="flex items-center gap-2 text-amber-800 dark:text-amber-300">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              <span>{activeCount} dari {totalCount} agen aktif</span>
              <span>·</span>
              <span>Sisa {etaText}</span>
            </div>
          ) : done ? (
            <div className="flex items-center gap-1.5 text-emerald-800 dark:text-emerald-300">
              <CheckCircle2 className="h-3.5 w-3.5" />
              <span>Selesai ({done.n_events} langkah)</span>
            </div>
          ) : null}
        </div>
      </div>

      <AgentRail
        agentStatuses={agentStatuses}
        selectedAuthor={selectedFilter}
        onFilterAuthor={onFilterChange}
        knownAgents={knownAgents}
      />

      <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-[#D9D9D9]/60 dark:border-[#262930]/60">
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={ticker}
            onChange={(e) => onTickerChange(normalizeTicker(e.target.value))}
            className="h-8 rounded-lg border border-[#D9D9D9] dark:border-[#262930] bg-white dark:bg-[#090a0c] px-2.5 text-xs font-medium text-[#333333] dark:text-[#f1f5f9]"
          >
            {SUPPORTED_TICKERS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>

          <button
            type="button"
            onClick={() => onRun("stream")}
            disabled={running}
            className="h-8 rounded-lg bg-[#0928B1] text-white hover:bg-[#0c5c53] px-3 py-1.5 text-xs font-medium transition-colors"
          >
            {running ? "Sedang berjalan…" : "Jalankan analisis"}
          </button>

          <button
            type="button"
            onClick={onClear}
            disabled={running}
            className="h-8 rounded-lg border border-[#D9D9D9] dark:border-[#262930] bg-white dark:bg-[#090a0c] text-[#666666] dark:text-[#666666] hover:bg-[#B4C7FF] dark:hover:bg-[#1e2229] px-3 py-1.5 text-xs transition-colors"
          >
            Bersihkan
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-start gap-2 rounded-lg border border-rose-200 dark:border-rose-900/60 bg-rose-50 dark:bg-rose-950/40 p-3 text-xs text-[#B4232A] dark:text-rose-300">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <div className="break-all">{error}</div>
        </div>
      )}
    </div>
  )
})
