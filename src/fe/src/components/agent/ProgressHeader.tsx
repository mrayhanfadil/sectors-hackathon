import { memo } from "react"
import {
  Activity,
  Bot,
  CheckCircle2,
  Clock,
  Loader2,
  AlertCircle,
  Play,
  RotateCcw,
  RefreshCw,
  Cpu,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
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
    <div className="rounded-md border border-neutral-200 bg-white p-5 shadow-none space-y-4 dark:border-neutral-800 dark:bg-[#111111]">
      {/* Top Header Row */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1.5 max-w-3xl">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-neutral-900 text-white shadow-none dark:bg-neutral-100 dark:text-neutral-900">
              <Bot className="h-4 w-4" />
            </div>
            <h1 className="text-xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-100">
              ADK Orchestrator - Live Trace
            </h1>
          </div>

          <p className="text-sm leading-relaxed text-neutral-600 dark:text-neutral-400">
            11 agents → <span className="font-medium text-neutral-800 dark:text-neutral-200">Muse Spark 1M</span> via CommandCode bridge{" "}
            <code className="rounded bg-neutral-100 px-1 py-0.5 font-mono text-xs text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">127.0.0.1:9992</code> · intake_parallel → modeler → research_parallel → writer → visualizer → sotp → adversarial×4 → critic. Stream SSE{" "}
            <code className="rounded bg-neutral-100 px-1 py-0.5 font-mono text-xs text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">/api/agent/stream</code> for step-by-step.
          </p>

          {/* Health Details */}
          {health && (
            <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
              <Badge
                variant={health.ok ? "default" : "secondary"}
                className="flex items-center gap-1 font-mono text-[11px]"
              >
                <span
                  className={`h-1.5 w-1.5 rounded-full ${
                    health.ok ? "bg-emerald-400" : "bg-amber-400"
                  }`}
                />
                {health.ok
                  ? "Spark OK"
                  : `Bridge ping: ${(health.bridge_ping || health.bridge_error || "-").slice(0, 30)}`}
              </Badge>
              <Badge variant="outline" className="font-mono text-[11px] text-neutral-600 dark:text-neutral-300">
                <Cpu className="mr-1 h-3 w-3 text-neutral-400" />
                {health.model || "meta/muse-spark-1.2-contributor"}
              </Badge>
              <Badge variant="outline" className="font-mono text-[11px] text-neutral-600 dark:text-neutral-300">
                {health.graph?.name || "equity_report_orchestrator"} · {health.graph?.n_subagents ?? 8} nodes
              </Badge>
              <span className="text-[11px] text-neutral-500 font-mono dark:text-neutral-400">
                provider: {health.provider || "spark (commandcode bridge)"} · {health.elapsed_ms ?? "-"}ms
              </span>
              <Button
                size="sm"
                variant="outline"
                className="h-6 px-2 text-[11px] text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100"
                onClick={onRefreshHealth}
              >
                <RefreshCw className="mr-1 h-3 w-3" />
                Refresh health
              </Button>
            </div>
          )}
        </div>

        {/* Live Status & ETA Pill */}
        <div className="flex flex-col items-end gap-1.5">
          <div className="flex items-center gap-2 rounded-lg border border-neutral-200 bg-neutral-50 px-3 py-1.5 text-xs shadow-2xs dark:border-neutral-800 dark:bg-neutral-900">
            {running ? (
              <div className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-500" />
                </span>
                <span className="font-semibold text-neutral-900 dark:text-neutral-100">
                  {activeCount} / {totalCount} agents active
                </span>
                <span className="text-neutral-400">·</span>
                <span className="flex items-center gap-1 font-mono text-neutral-700 dark:text-neutral-300">
                  <Activity className="h-3 w-3 text-neutral-500 dark:text-neutral-400" />
                  {events.length} events
                </span>
                <span className="text-neutral-400">·</span>
                <span className="flex items-center gap-1 font-mono text-amber-800 font-medium dark:text-amber-200">
                  <Clock className="h-3 w-3 text-amber-600" />
                  ETA {etaText}
                </span>
              </div>
            ) : done ? (
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                <span className="font-semibold text-emerald-900 dark:text-emerald-200">Execution complete</span>
                <span className="text-neutral-400">·</span>
                <span className="font-mono text-neutral-700 dark:text-neutral-300">{done.n_events} events</span>
                <span className="text-neutral-400">·</span>
                <span className="font-mono text-neutral-600 dark:text-neutral-400">{(done.ms / 1000).toFixed(1)}s</span>
              </div>
            ) : isInterrupted ? (
              <div className="flex items-center gap-2">
                <AlertCircle className="h-3.5 w-3.5 text-amber-600" />
                <span className="font-medium text-amber-900 dark:text-amber-200">stream interrupted · partial result</span>
                <span className="text-neutral-400">·</span>
                <span className="font-mono text-neutral-700 dark:text-neutral-300">{events.length} events</span>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-neutral-400" />
                <span className="font-medium text-neutral-700 dark:text-neutral-300">Ready</span>
                <span className="text-neutral-400">·</span>
                <span className="text-neutral-500 dark:text-neutral-400">SSE + blocking</span>
              </div>
            )}
          </div>

          <div className="text-[11px] text-neutral-500 font-mono dark:text-neutral-400">
            {running
              ? "Live execution streaming via EventSource"
              : done
              ? `Keys generated: ${done.state_keys.length} state outputs`
              : "Idle pipeline"}
          </div>
        </div>
      </div>

      {/* Agent Rail */}
      <AgentRail
        agentStatuses={agentStatuses}
        selectedAuthor={selectedFilter}
        onFilterAuthor={onFilterChange}
        knownAgents={knownAgents}
      />

      {/* Controls & Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-neutral-100 dark:border-neutral-800">
        <div className="flex flex-wrap items-center gap-2">
          <label className="flex items-center gap-2 text-xs font-medium text-neutral-700 dark:text-neutral-300">
            <span>Ticker</span>
            <select
              value={ticker}
              onChange={(e) => onTickerChange(normalizeTicker(e.target.value))}
              className="h-8 rounded-md border border-neutral-300 bg-white px-2.5 text-sm font-mono font-semibold uppercase text-neutral-900 shadow-2xs focus:border-neutral-800 focus:outline-none focus:ring-1 focus:ring-neutral-800 dark:border-neutral-700 dark:bg-[#111111] dark:text-white dark:focus:border-neutral-400 dark:focus:ring-neutral-400"
            >
              {SUPPORTED_TICKERS.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>

          <Button
            onClick={() => onRun("stream")}
            disabled={running}
            className="h-8 gap-1.5 bg-neutral-900 text-xs font-medium text-white hover:bg-neutral-800 dark:bg-neutral-100 dark:text-neutral-900 dark:hover:bg-white"
          >
            {running ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin text-white" />
                Running… (SSE live)
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5" />
                ▶ Run ADK (SSE live trace)
              </>
            )}
          </Button>

          <Button
            onClick={() => onRun("blocking")}
            disabled={running}
            variant="outline"
            className="h-8 text-xs font-medium text-neutral-700 border-neutral-300 hover:bg-neutral-50 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
          >
            Run (blocking POST)
          </Button>

          <Button
            onClick={onClear}
            variant="ghost"
            className="h-8 gap-1 text-xs text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-neutral-100"
            disabled={running}
          >
            <RotateCcw className="h-3 w-3" />
            Clear
          </Button>
        </div>

        <div className="text-xs text-neutral-500 font-mono dark:text-neutral-400">
          {events.length} events{" "}
          {done ? (
            `· done ${done.n_events} events · keys: ${done.state_keys.join(", ") || "-"} · ${done.ms}ms`
          ) : running ? (
            `· streaming… (${activeCount} active · ETA ${etaText})`
          ) : isInterrupted ? (
            "· stream interrupted · partial result"
          ) : (
            ""
          )}
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="flex items-start gap-2 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-800 dark:border-rose-800 dark:bg-rose-950 dark:text-rose-200">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-600 mt-0.5" />
          <div className="font-mono break-all">{error}</div>
        </div>
      )}
    </div>
  )
})
