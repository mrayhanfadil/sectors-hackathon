import { useState } from "react"
import { Link } from "@tanstack/react-router"
import {
  Bot,
  Inbox,
  ChevronDown,
  ChevronUp,
  History,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

export type Log = {
  run_id: string
  status: "completed" | "interrupted" | "failed" | "running"
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
  if (s == null || Number.isNaN(s)) return "-"
  const totalSeconds = Math.round(s)
  const m = Math.floor(totalSeconds / 60)
  const d = totalSeconds % 60
  if (m > 0) {
    return `${m}m ${d}d`
  }
  return `${d}d`
}

export function formatRelativeTime(ts: number | null | undefined): string {
  if (!ts) return "-"
  const now = Date.now() / 1000
  const diff = Math.max(0, now - ts)
  if (diff < 60) return "baru saja"
  if (diff < 3600) return `${Math.floor(diff / 60)} menit lalu`
  if (diff < 86400) return `${Math.floor(diff / 3600)} jam lalu`
  if (diff < 604800) return `${Math.floor(diff / 86400)} hari lalu`
  const date = new Date(ts * 1000)
  return date.toLocaleDateString("id-ID", { day: "numeric", month: "short" })
}

function renderStatusBadge(status: string) {
  switch (status) {
    case "completed":
      return <Badge variant="success">Selesai</Badge>
    case "interrupted":
      return (
        <Badge variant="outline" className="border-amber-300 bg-amber-50 text-amber-800">
          Terinterupsi
        </Badge>
      )
    case "failed":
      return <Badge variant="destructive">Gagal</Badge>
    case "running":
      return (
        <Badge variant="outline" className="border-sky-300 bg-sky-50 text-sky-800 animate-pulse flex items-center gap-1">
          <span className="h-1.5 w-1.5 rounded-full bg-sky-500" />
          Sedang Berjalan
        </Badge>
      )
    default:
      return <Badge variant="secondary">{status}</Badge>
  }
}

export function AdkRunCard({ ticker, log, history, hasRun }: Props) {
  const t = ticker.toUpperCase()
  const [historyOpen, setHistoryOpen] = useState(false)

  if (!hasRun || !log) {
    return (
      <Card className="border-neutral-200 bg-white shadow-2xs">
        <CardHeader className="p-4 pb-2">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-neutral-900 text-white shadow-2xs">
              <Bot className="h-4 w-4" />
            </div>
            <CardTitle className="text-sm font-semibold text-neutral-900">
              Log ADK untuk {t}
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent className="p-4 pt-2 space-y-3">
          <div className="flex items-center gap-2 text-xs text-neutral-500">
            <Inbox className="h-4 w-4 text-neutral-400" />
            <span>Belum ada log ADK untuk {t}</span>
          </div>
          <div>
            <Link to="/agent" search={{ ticker: t } as any}>
              <Button size="sm" variant="outline" className="h-8 gap-1.5 text-xs text-neutral-700">
                <span>Mulai Run →</span>
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    )
  }

  const rawPreview = log.last_text_preview || log.error || null
  const lastTextPreview = rawPreview
    ? rawPreview.length > 80
      ? `${rawPreview.slice(0, 80)}...`
      : rawPreview
    : "-"

  return (
    <Card className="border-neutral-200 bg-white shadow-2xs">
      <CardHeader className="p-4 pb-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-neutral-900 text-white shadow-2xs">
              <Bot className="h-4 w-4" />
            </div>
            <CardTitle className="text-sm font-semibold text-neutral-900">
              Log ADK untuk {t}
            </CardTitle>
          </div>
          <Link to="/agent" search={{ ticker: t } as any}>
            <Button size="sm" variant="default" className="h-8 gap-1.5 text-xs bg-neutral-900 text-white hover:bg-neutral-800">
              <span>Lihat Trace Lengkap →</span>
            </Button>
          </Link>
        </div>
      </CardHeader>

      <CardContent className="p-4 pt-2 space-y-3">
        {/* Row 1: Status Badge + relative time + n_events */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {renderStatusBadge(log.status)}
          <span className="text-neutral-500">{formatRelativeTime(log.started_at)}</span>
          <span className="text-neutral-300">·</span>
          <span className="font-mono text-neutral-600">{log.n_events} aktivitas</span>
        </div>

        {/* Row 2: small caption "{provider}/{model} · {duration_s ? formatDuration(duration_s) : '-'}" */}
        <div className="text-xs text-neutral-500 font-mono">
          <span>{log.provider}/{log.model}</span>
          <span className="mx-1.5 text-neutral-300">·</span>
          <span>{log.duration_s != null ? formatDuration(log.duration_s) : "-"}</span>
        </div>

        {/* Row 3: "Last activity: {last_text_preview}" truncated to 80 chars with ellipsis */}
        <div className="text-xs text-neutral-600 leading-relaxed">
          <span className="font-medium text-neutral-700">Last activity: </span>
          <span className="font-mono text-[11px] text-neutral-600">{lastTextPreview}</span>
        </div>

        {/* Collapsible history: "Riwayat run sebelumnya" (max 5 rows) */}
        {history && history.length > 0 && (
          <div className="border-t border-neutral-100 pt-2 text-xs">
            <button
              type="button"
              onClick={() => setHistoryOpen((prev) => !prev)}
              className="flex w-full items-center justify-between text-left text-neutral-600 hover:text-neutral-900 py-1 select-none"
            >
              <div className="flex items-center gap-1.5 font-medium">
                <History className="h-3.5 w-3.5 text-neutral-400" />
                <span>Riwayat run sebelumnya ({Math.min(history.length, 5)})</span>
              </div>
              {historyOpen ? (
                <ChevronUp className="h-3.5 w-3.5 text-neutral-400" />
              ) : (
                <ChevronDown className="h-3.5 w-3.5 text-neutral-400" />
              )}
            </button>

            {historyOpen && (
              <div className="mt-2 space-y-1.5 rounded-lg bg-neutral-50 p-2.5">
                {history.slice(0, 5).map((h) => (
                  <div
                    key={h.run_id}
                    className="flex flex-wrap items-center justify-between gap-1 py-1 text-[11px] border-b border-neutral-200/50 last:border-0"
                  >
                    <div className="flex items-center gap-2">
                      {renderStatusBadge(h.status)}
                      <span className="text-neutral-500">{formatRelativeTime(h.started_at)}</span>
                    </div>
                    <div className="flex items-center gap-2 font-mono text-neutral-500">
                      <span>{h.n_events} aktivitas</span>
                      <span className="text-neutral-300">·</span>
                      <span>{h.duration_s != null ? formatDuration(h.duration_s) : "-"}</span>
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
