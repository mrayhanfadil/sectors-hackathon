import { useState } from "react"
import { Link } from "@tanstack/react-router"
import {
  Bot,
  Inbox,
  ChevronDown,
  ChevronUp,
  History,
  Activity,
  Terminal,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

export type Log = {
  run_id: string
  status: "completed" | "interrupted" | "failed" | "running" | string
  started_at: number
  finished_at: number | null
  duration_s: number | null
  provider: string
  model: string
  n_events: number
  last_text_preview: string | null
  error: string | null
} | null

export type HistoryItem = {
  run_id: string
  status: string
  started_at: number
  n_events: number
  duration_s: number | null
}

export type Props = {
  ticker: string
  log: Log
  history: HistoryItem[]
  hasRun: boolean
}

export function formatDuration(s: number | null | undefined): string {
  if (s == null || Number.isNaN(s)) return "—"
  const totalSeconds = Math.round(s)
  const m = Math.floor(totalSeconds / 60)
  const d = totalSeconds % 60
  if (m > 0) {
    return `${m}m ${d}s`
  }
  return `${d}s`
}

export function formatRelativeTime(ts: number | null | undefined): string {
  if (!ts) return "—"
  const now = Date.now() / 1000
  const diff = Math.max(0, now - ts)
  if (diff < 60) return "just now"
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`
  const date = new Date(ts * 1000)
  return date.toLocaleDateString("id-ID", { day: "numeric", month: "short" })
}

function renderStatusBadge(status: string) {
  const norm = (status || "").toLowerCase()
  switch (norm) {
    case "completed":
      return (
        <span className="inline-flex items-center gap-1 rounded border border-emerald-500/40 bg-emerald-500/10 px-1.5 py-0.5 font-mono text-[10px] font-bold uppercase text-emerald-600 dark:border-emerald-500/50 dark:text-emerald-300">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          COMPLETED
        </span>
      )
    case "interrupted":
      return (
        <span className="inline-flex items-center gap-1 rounded border border-amber-500/40 bg-amber-500/10 px-1.5 py-0.5 font-mono text-[10px] font-bold uppercase text-amber-600 dark:border-amber-500/50 dark:text-amber-300">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
          INTERRUPTED
        </span>
      )
    case "failed":
      return (
        <span className="inline-flex items-center gap-1 rounded border border-rose-500/40 bg-rose-500/10 px-1.5 py-0.5 font-mono text-[10px] font-bold uppercase text-rose-600 dark:border-rose-500/50 dark:text-rose-300">
          <span className="h-1.5 w-1.5 rounded-full bg-rose-500" />
          GAGAL
        </span>
      )
    case "running":
      return (
        <span className="inline-flex items-center gap-1 rounded border border-sky-500/40 bg-sky-500/10 px-1.5 py-0.5 font-mono text-[10px] font-bold uppercase text-sky-600 animate-pulse dark:border-sky-500/50 dark:text-sky-300">
          <span className="h-1.5 w-1.5 rounded-full bg-sky-500" />
          JALAN
        </span>
      )
    default:
      return (
        <span className="inline-flex items-center rounded border border-neutral-300 bg-neutral-100 px-1.5 py-0.5 font-mono text-[10px] font-bold uppercase text-neutral-700 dark:border-[#262930] dark:bg-[#181a1f] dark:text-neutral-300">
          {status.toUpperCase()}
        </span>
      )
  }
}

export function AdkRunCard({ ticker, log, history, hasRun }: Props) {
  const tk = ticker.toUpperCase()
  const [historyOpen, setHistoryOpen] = useState(false)

  if (!hasRun || !log) {
    return (
      <Card className="rounded-md border border-neutral-300 bg-white shadow-none dark:border-[#262930] dark:bg-[#121316]">
        <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3 pb-2 dark:border-[#1f2228] dark:bg-[#181a1f]/70">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot className="h-4 w-4 text-neutral-500 dark:text-neutral-400" />
              <CardTitle className="font-mono text-xs font-bold uppercase tracking-wide text-neutral-900 dark:text-neutral-100">
                ADK AGENT AUDIT // {tk}
              </CardTitle>
            </div>
            <span className="font-mono text-[10px] text-neutral-400">STATUS: IDLE</span>
          </div>
        </CardHeader>
        <CardContent className="space-y-3 p-3 pt-2.5 font-mono">
          <div className="flex items-center gap-2 text-xs text-neutral-500 dark:text-neutral-400">
            <Inbox className="h-4 w-4 text-neutral-400" />
            <span>Belum ada log eksekusi ADK untuk {tk}.</span>
          </div>
          <div>
            <Link to="/agent" search={{ ticker: tk } as any}>
              <Button
                size="sm"
                variant="outline"
                className="h-7 border-neutral-300 font-mono text-xs font-semibold text-neutral-800 hover:bg-neutral-100 dark:border-[#262930] dark:bg-[#181a1f] dark:text-neutral-200 dark:hover:bg-[#22252c]"
              >
                <span>&gt; LAUNCH AGENT RUN</span>
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    )
  }

  const rawPreview = log.last_text_preview || log.error || null
  const lastTextPreview = rawPreview
    ? rawPreview.length > 90
      ? `${rawPreview.slice(0, 90)}...`
      : rawPreview
    : "—"

  return (
    <Card className="rounded-md border border-neutral-300 bg-white shadow-none dark:border-[#262930] dark:bg-[#121316]">
      <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3 pb-2 dark:border-[#1f2228] dark:bg-[#181a1f]/70">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-amber-500" />
            <CardTitle className="font-mono text-xs font-bold uppercase tracking-wide text-neutral-900 dark:text-neutral-100">
              ADK AGENT AUDIT // {tk}
            </CardTitle>
          </div>
          <Link to="/agent" search={{ ticker: tk } as any}>
            <span className="font-mono text-[11px] font-bold text-[#0070f3] hover:underline dark:text-[#3291ff]">
              [VIEW TRACE &gt;]
            </span>
          </Link>
        </div>
      </CardHeader>

      <CardContent className="space-y-2.5 p-3 pt-2.5 font-mono text-xs">
        {/* Row 1: Status & Metadata */}
        <div className="flex flex-wrap items-center justify-between gap-1.5">
          <div>{renderStatusBadge(log.status)}</div>
          <div className="text-[11px] text-neutral-500 tabular-nums dark:text-neutral-400">
            {formatRelativeTime(log.started_at)}
          </div>
        </div>

        {/* Row 2: Metrics grid */}
        <div className="grid grid-cols-2 gap-1.5 text-[11px]">
          <div className="rounded border border-neutral-200 bg-neutral-50 p-1.5 dark:border-[#262930] dark:bg-[#181a1f]">
            <div className="text-[9px] uppercase text-neutral-400">MODEL</div>
            <div className="truncate font-bold text-neutral-800 dark:text-neutral-200">
              {log.provider}/{log.model}
            </div>
          </div>
          <div className="rounded border border-neutral-200 bg-neutral-50 p-1.5 dark:border-[#262930] dark:bg-[#181a1f]">
            <div className="text-[9px] uppercase text-neutral-400">EXEC TIME / EVENTS</div>
            <div className="font-bold text-neutral-800 tabular-nums dark:text-neutral-200">
              {formatDuration(log.duration_s)} · {log.n_events} ev
            </div>
          </div>
        </div>

        {/* Row 3: Last activity stream */}
        <div className="rounded border border-neutral-200 bg-neutral-50/80 p-2 text-[11px] leading-relaxed dark:border-[#262930] dark:bg-[#181a1f]/60">
          <div className="flex items-center gap-1 font-bold uppercase text-neutral-500 dark:text-neutral-400">
            <Terminal className="h-3 w-3 text-amber-500" />
            <span>LAST ACTIVITY STREAM:</span>
          </div>
          <p className="mt-1 text-neutral-700 dark:text-neutral-300">
            &gt; {lastTextPreview}
          </p>
        </div>

        {/* Collapsible history: Riwayat run sebelumnya */}
        {history && history.length > 0 && (
          <div className="border-t border-neutral-200 pt-2 dark:border-[#1f2228]">
            <button
              type="button"
              onClick={() => setHistoryOpen((prev) => !prev)}
              className="flex w-full items-center justify-between py-0.5 text-left text-[11px] font-bold text-neutral-600 hover:text-neutral-900 select-none cursor-pointer dark:text-neutral-400 dark:hover:text-neutral-200"
            >
              <div className="flex items-center gap-1.5">
                <History className="h-3 w-3 text-neutral-400" />
                <span>PREVIOUS RUNS ({Math.min(history.length, 5)})</span>
              </div>
              {historyOpen ? (
                <ChevronUp className="h-3.5 w-3.5 text-neutral-400" />
              ) : (
                <ChevronDown className="h-3.5 w-3.5 text-neutral-400" />
              )}
            </button>

            {historyOpen && (
              <div className="mt-1.5 space-y-1 rounded border border-neutral-200 bg-neutral-50 p-2 dark:border-[#262930] dark:bg-[#181a1f]">
                {history.slice(0, 5).map((h) => (
                  <div
                    key={h.run_id}
                    className="flex flex-wrap items-center justify-between gap-1 border-b border-neutral-200/50 py-1 text-[10px] last:border-0 dark:border-[#262930]/50"
                  >
                    <div className="flex items-center gap-1.5">
                      {renderStatusBadge(h.status)}
                      <span className="text-neutral-500 tabular-nums dark:text-neutral-400">
                        {formatRelativeTime(h.started_at)}
                      </span>
                    </div>
                    <div className="text-neutral-500 tabular-nums dark:text-neutral-400">
                      {h.n_events} ev · {formatDuration(h.duration_s)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

