import { useState } from "react"
import { Link } from "@tanstack/react-router"
import {
  Bot,
  Inbox,
  ChevronDown,
  ChevronUp,
  History,
  Activity,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
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
  if (s == null || Number.isNaN(s)) return "-"
  const totalSeconds = Math.round(s)
  const m = Math.floor(totalSeconds / 60)
  const d = totalSeconds % 60
  if (m > 0) {
    return `${m}m ${d}s`
  }
  return `${d}s`
}

export function formatRelativeTime(ts: number | null | undefined): string {
  if (!ts) return "-"
  const now = Date.now() / 1000
  const diff = Math.max(0, now - ts)
  if (diff < 60) return "baru saja"
  if (diff < 3600) return `${Math.floor(diff / 60)}m lalu`
  if (diff < 86400) return `${Math.floor(diff / 3600)}j lalu`
  if (diff < 604800) return `${Math.floor(diff / 86400)}h lalu`
  const date = new Date(ts * 1000)
  return date.toLocaleDateString("id-ID", { day: "numeric", month: "short" })
}

function renderStatusBadge(status: string) {
  const norm = (status || "").toLowerCase()
  switch (norm) {
    case "completed":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-md border border-[#BCE2C9] bg-[#EBF6EE] px-2 py-0.5 text-xs font-medium text-[#157F3D] dark:border-[#157F3D]/40 dark:bg-[#157F3D]/20 dark:text-[#34D399]">
          <span className="h-1.5 w-1.5 rounded-full bg-[#157F3D]" />
          Selesai
        </span>
      )
    case "interrupted":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-md border border-[#F6E3B8] bg-[#FEF9EE] px-2 py-0.5 text-xs font-medium text-[#A16207] dark:border-[#A16207]/40 dark:bg-[#A16207]/20 dark:text-[#FBBF24]">
          <span className="h-1.5 w-1.5 rounded-full bg-[#A16207]" />
          Terinterupsi
        </span>
      )
    case "failed":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-md border border-[#F8C8CB] bg-[#FDF2F2] px-2 py-0.5 text-xs font-medium text-[#B4232A] dark:border-[#B4232A]/40 dark:bg-[#B4232A]/20 dark:text-[#F87171]">
          <span className="h-1.5 w-1.5 rounded-full bg-[#B4232A]" />
          Gagal
        </span>
      )
    case "running":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-md border border-[#0E6E63]/30 bg-[#0E6E63]/10 px-2 py-0.5 text-xs font-medium text-[#0E6E63] animate-pulse dark:border-[#4FD1B5]/30 dark:bg-[#4FD1B5]/20 dark:text-[#4FD1B5]">
          <span className="h-1.5 w-1.5 rounded-full bg-[#0E6E63]" />
          Sedang diproses
        </span>
      )
    default:
      return (
        <span className="inline-flex items-center rounded-md border border-[#E7E3DA] bg-[#FBFAF7] px-2 py-0.5 text-xs font-medium text-[#6B6659] dark:border-[#2A2822] dark:bg-[#1B1A16] dark:text-[#A8A296]">
          {status}
        </span>
      )
  }
}

export function AdkRunCard({ ticker, log, history, hasRun }: Props) {
  const tk = ticker.toUpperCase()
  const [historyOpen, setHistoryOpen] = useState(false)

  if (!hasRun || !log) {
    return (
      <Card className="rounded-xl border border-[#E7E3DA] bg-white shadow-none dark:border-[#2A2822] dark:bg-[#1B1A16]">
        <CardHeader className="border-b border-[#E7E3DA] p-4 pb-3 dark:border-[#2A2822]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot className="h-4 w-4 text-[#0E6E63] dark:text-[#4FD1B5]" />
              <CardTitle className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                Proses analisis {tk}
              </CardTitle>
            </div>
            <span className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">Siaga</span>
          </div>
        </CardHeader>
        <CardContent className="space-y-3 p-4">
          <div className="flex items-center gap-2 text-xs text-[#6B6659] dark:text-[#A8A296]">
            <Inbox className="h-4 w-4 text-[#A8A296]" />
            <span>Belum ada rekam jejak eksekusi untuk {tk}.</span>
          </div>
          <div>
            <Link to="/agent" search={{ ticker: tk } as any}>
              <Button
                size="sm"
                variant="outline"
                className="h-8 rounded-lg border-[#E7E3DA] bg-white text-xs font-medium text-[#1C1B17] hover:bg-[#F4F1EA] dark:border-[#2A2822] dark:bg-[#1B1A16] dark:text-[#EDEAE3] dark:hover:bg-[#25231E] cursor-pointer"
              >
                <span>Jalankan analisis</span>
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
    : "-"

  return (
    <Card className="rounded-xl border border-[#E7E3DA] bg-white shadow-none dark:border-[#2A2822] dark:bg-[#1B1A16]">
      <CardHeader className="border-b border-[#E7E3DA] p-4 pb-3 dark:border-[#2A2822]">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-[#0E6E63] dark:text-[#4FD1B5]" />
            <CardTitle className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
              Proses analisis {tk}
            </CardTitle>
          </div>
          <Link to="/agent" search={{ ticker: tk } as any}>
            <span className="text-xs font-medium text-[#0E6E63] hover:underline dark:text-[#4FD1B5]">
              Lihat rincian
            </span>
          </Link>
        </div>
      </CardHeader>

      <CardContent className="space-y-3 p-4 text-xs">
        {/* Row 1: Status & Metadata */}
        <div className="flex flex-wrap items-center justify-between gap-1.5">
          <div>{renderStatusBadge(log.status)}</div>
          <div className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">
            {formatRelativeTime(log.started_at)}
          </div>
        </div>

        {/* Row 2: Metrics */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="rounded-lg border border-[#E7E3DA] bg-[#FBFAF7] p-2.5 dark:border-[#2A2822] dark:bg-[#14130F]">
            <div className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">Model</div>
            <div className="truncate font-medium text-[#1C1B17] mt-0.5 dark:text-[#EDEAE3]">
              {log.provider}/{log.model}
            </div>
          </div>
          <div className="rounded-lg border border-[#E7E3DA] bg-[#FBFAF7] p-2.5 dark:border-[#2A2822] dark:bg-[#14130F]">
            <div className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">Durasi / Kejadian</div>
            <div className="font-medium text-[#1C1B17] mt-0.5 dark:text-[#EDEAE3]">
              <span className="font-mono tabular-nums">{formatDuration(log.duration_s)}</span> · <span className="font-mono tabular-nums">{log.n_events}</span> ev
            </div>
          </div>
        </div>

        {/* Row 3: Last activity */}
        <div className="rounded-lg border border-[#E7E3DA] bg-[#FBFAF7] p-3 text-xs leading-relaxed dark:border-[#2A2822] dark:bg-[#14130F]">
          <div className="font-semibold text-[#1C1B17] text-[11px] dark:text-[#EDEAE3]">
            Aktivitas mesin terakhir:
          </div>
          <p className="mt-1 text-[#6B6659] dark:text-[#A8A296]">
            {lastTextPreview}
          </p>
        </div>

        {/* Expandable Riwayat Eksekusi */}
        {history && history.length > 0 && (
          <div className="border-t border-[#E7E3DA] pt-3 dark:border-[#2A2822]">
            <button
              type="button"
              onClick={() => setHistoryOpen((prev) => !prev)}
              className="flex w-full items-center justify-between py-1 text-left text-xs font-semibold text-[#1C1B17] hover:text-[#0E6E63] cursor-pointer dark:text-[#EDEAE3] dark:hover:text-[#4FD1B5]"
            >
              <div className="flex items-center gap-1.5">
                <History className="h-3.5 w-3.5 text-[#6B6659] dark:text-[#A8A296]" />
                <span>Riwayat eksekusi ({Math.min(history.length, 5)})</span>
              </div>
              {historyOpen ? (
                <ChevronUp className="h-3.5 w-3.5 text-[#6B6659] dark:text-[#A8A296]" />
              ) : (
                <ChevronDown className="h-3.5 w-3.5 text-[#6B6659] dark:text-[#A8A296]" />
              )}
            </button>

            {historyOpen && (
              <div className="mt-2 space-y-1.5 rounded-lg border border-[#E7E3DA] bg-[#FBFAF7] p-3 dark:border-[#2A2822] dark:bg-[#14130F]">
                {history.slice(0, 5).map((h) => (
                  <div
                    key={h.run_id}
                    className="flex flex-wrap items-center justify-between gap-1 border-b border-[#E7E3DA]/60 py-1.5 text-xs last:border-0 dark:border-[#2A2822]/60"
                  >
                    <div className="flex items-center gap-1.5">
                      {renderStatusBadge(h.status)}
                      <span className="text-[#6B6659] dark:text-[#A8A296]">
                        {formatRelativeTime(h.started_at)}
                      </span>
                    </div>
                    <div className="text-[#6B6659] dark:text-[#A8A296]">
                      <span className="font-mono tabular-nums">{h.n_events}</span> ev · <span className="font-mono tabular-nums">{formatDuration(h.duration_s)}</span>
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
