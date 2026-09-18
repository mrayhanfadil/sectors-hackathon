import { memo, useState, useRef, useEffect, useMemo } from "react"
import {
  Activity,
  ChevronDown,
  ChevronUp,
  Code2,
  Search,
  ArrowDownCircle,
  Copy,
  Check,
} from "lucide-react"
import { cn } from "@/lib/utils"
import {
  getFriendlyAgent,
  getEventActionDescription,
  formatTimestamp,
  type TraceEvent,
} from "./AGENT_FRIENDLY_META"
import { FunctionCallCard } from "./FunctionCallCard"
import { FunctionResponseCard } from "./FunctionResponseCard"

export interface PlainEnglishPanelProps {
  events: TraceEvent[]
  running: boolean
  ticker: string
  selectedAuthor?: string
  onFilterAuthor?: (author: string) => void
  className?: string
}

interface EventRowProps {
  event: TraceEvent
  prevEvent?: TraceEvent
  ticker: string
  isLast: boolean
}

function EventRow({ event, prevEvent, ticker }: EventRowProps) {
  const [expanded, setExpanded] = useState(false)
  const agent = getFriendlyAgent(event.author)

  const actionText = useMemo(() => {
    return getEventActionDescription(event, ticker)
  }, [event, ticker])

  const latencyMs = useMemo(() => {
    if (prevEvent && event.ts && prevEvent.ts && event.ts >= prevEvent.ts) {
      return Math.round((event.ts - prevEvent.ts) * 1000)
    }
    return null
  }, [event, prevEvent])

  const hasTechDetails =
    (event.function_calls && event.function_calls.length > 0) ||
    (event.function_responses && event.function_responses.length > 0) ||
    (event.state_delta_keys && event.state_delta_keys.length > 0)

  return (
    <div className="group border-b border-[#D9D9D9]/70 dark:border-[#262930]/70 py-3 transition-colors hover:bg-[#f1f5f9]/60 dark:hover:bg-[#333333]/40 text-xs">
      <div className="flex flex-wrap items-center justify-between gap-2">
        {/* Step sequence & agent tag */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[11px] font-medium text-[#666666] dark:text-[#666666]">
            Langkah {event.seq}
          </span>

          <span
            className={cn(
              "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[11px] font-medium",
              agent.badgeBg,
              agent.badgeText,
              agent.badgeBorder
            )}
          >
            {agent.shortLabel}
          </span>
        </div>

        {/* Timestamp */}
        <div className="flex items-center gap-2 text-right text-[11px] text-[#666666] dark:text-[#666666]">
          {latencyMs !== null && latencyMs > 0 && (
            <span className="text-[#0928B1] dark:text-[#7596FF]">
              +{latencyMs} ms
            </span>
          )}
          <span>{formatTimestamp(event.ts)}</span>
        </div>
      </div>

      {/* Main Action Line */}
      <div className="mt-1.5 space-y-1">
        <p className="text-xs font-medium leading-relaxed text-[#333333] dark:text-[#f1f5f9]">
          {actionText}
        </p>

        {/* Text preview if available */}
        {event.text && event.text.trim().length > 0 && (
          <div className="rounded-lg bg-[#f1f5f9] dark:bg-[#1e2229] border border-[#D9D9D9] dark:border-[#262930] p-2.5 text-xs leading-relaxed text-[#666666] dark:text-[#666666]">
            <div className="whitespace-pre-wrap break-words">
              {event.text.length > 400
                ? `${event.text.slice(0, 400)}…`
                : event.text}
            </div>
          </div>
        )}
      </div>

      {/* Expandable Technical Details */}
      {hasTechDetails && (
        <div className="mt-2">
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="inline-flex items-center gap-1 text-[11px] font-medium text-[#666666] dark:text-[#666666] hover:text-[#0928B1] dark:hover:text-[#7596FF] transition-colors focus:outline-none"
          >
            <Code2 className="h-3 w-3" />
            <span>{expanded ? "Sembunyikan rincian parameter" : "Lihat rincian kalkulasi"}</span>
            {expanded ? (
              <ChevronUp className="h-3 w-3" />
            ) : (
              <ChevronDown className="h-3 w-3" />
            )}
          </button>

          {expanded && (
            <div className="mt-2 space-y-2 rounded-lg border border-[#D9D9D9] dark:border-[#262930] bg-[#f1f5f9]/80 dark:bg-[#1e2229]/80 p-3 text-[#333333] dark:text-[#f1f5f9]">
              {/* Function Calls */}
              {event.function_calls && event.function_calls.length > 0 && (
                <div className="space-y-1">
                  <div className="text-[11px] font-medium text-[#666666] dark:text-[#666666]">
                    Parameter kalkulasi:
                  </div>
                  {event.function_calls.map((fc, i) => (
                    <FunctionCallCard key={fc.id || `${fc.name}-${i}`} fc={fc} />
                  ))}
                </div>
              )}

              {/* Function Responses */}
              {event.function_responses && event.function_responses.length > 0 && (
                <div className="space-y-1">
                  <div className="text-[11px] font-medium text-[#666666] dark:text-[#666666]">
                    Hasil kalkulasi:
                  </div>
                  {event.function_responses.map((fr, i) => (
                    <FunctionResponseCard key={fr.id || `${fr.name}-${i}`} fr={fr} />
                  ))}
                </div>
              )}

              {/* State Delta Keys */}
              {event.state_delta_keys && event.state_delta_keys.length > 0 && (
                <div className="pt-1">
                  <div className="text-[11px] font-medium text-[#666666] dark:text-[#666666]">
                    Kunci memori diperbarui:
                  </div>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {event.state_delta_keys.map((k) => (
                      <span
                        key={k}
                        className="rounded bg-white dark:bg-[#090a0c] px-1.5 py-0.5 text-[10px] text-[#0928B1] dark:text-[#7596FF] border border-[#D9D9D9] dark:border-[#262930]"
                      >
                        {k}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export const PlainEnglishPanel = memo(function PlainEnglishPanel({
  events,
  running,
  ticker,
  selectedAuthor = "all",
  onFilterAuthor,
  className,
}: PlainEnglishPanelProps) {
  const listRef = useRef<HTMLDivElement>(null)
  const [filterType, setFilterType] = useState<"all" | "data" | "valuation" | "research" | "qa">("all")
  const [searchText, setSearchText] = useState("")
  const [autoScroll, setAutoScroll] = useState(true)
  const [copiedTrace, setCopiedTrace] = useState(false)

  useEffect(() => {
    if (autoScroll && listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight
    }
  }, [events.length, autoScroll])

  const filteredEvents = useMemo(() => {
    return events.filter((ev) => {
      // Author filter
      if (selectedAuthor !== "all" && ev.author !== selectedAuthor) {
        return false
      }
      // Stage category filter
      if (filterType === "data") {
        return ["collector", "news_harvester", "news_search_sub"].includes(ev.author)
      }
      if (filterType === "valuation") {
        return ev.author === "modeler" || ev.author === "sotp" || ev.function_calls?.some((fc) => fc.name.startsWith("calc_"))
      }
      if (filterType === "research") {
        return ["analyst", "industry", "risk", "kpi", "industry_search_sub", "writer", "visualizer"].includes(ev.author)
      }
      if (filterType === "qa") {
        return ev.author === "adversarial" || ev.author === "critic"
      }

      // Search text filter
      if (searchText.trim()) {
        const q = searchText.toLowerCase().trim()
        const textMatch = ev.text.toLowerCase().includes(q)
        const authorMatch = ev.author.toLowerCase().includes(q)
        const fcMatch = ev.function_calls?.some((fc) => fc.name.toLowerCase().includes(q))
        return textMatch || authorMatch || fcMatch
      }

      return true
    })
  }, [events, selectedAuthor, filterType, searchText])

  const handleCopyTraceJson = () => {
    const jsonStr = JSON.stringify(events, null, 2)
    navigator.clipboard.writeText(jsonStr)
    setCopiedTrace(true)
    setTimeout(() => setCopiedTrace(false), 2000)
  }

  return (
    <div className={cn("rounded-xl border border-[#D9D9D9] dark:border-[#262930] bg-white dark:bg-[#090a0c] p-5 sm:p-6 font-sans shadow-none space-y-4", className)}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#D9D9D9]/60 dark:border-[#262930]/60">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#B4C7FF] dark:bg-[#1e2229] text-[#0928B1] dark:text-[#7596FF] border border-[#D9D9D9] dark:border-[#262930]">
            <Activity className="h-4 w-4" />
          </div>
          <div>
            <h2 className="font-serif text-lg font-medium text-[#333333] dark:text-[#f1f5f9]">
              Catatan langkah alur kerja
            </h2>
            <p className="text-xs text-[#666666] dark:text-[#666666]">
              Jejak kronologis langkah kerja agen yang mudah dibaca.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs">
          {running && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 px-2.5 py-0.5 text-xs font-medium text-amber-800 dark:text-amber-300">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-ping" />
              <span>Memproses</span>
            </span>
          )}

          <span className="rounded-full bg-[#B4C7FF] dark:bg-[#1e2229] border border-[#D9D9D9] dark:border-[#262930] px-2.5 py-0.5 text-xs font-medium text-[#666666] dark:text-[#666666]">
            {filteredEvents.length} dari {events.length} langkah
          </span>

          <button
            type="button"
            onClick={() => setAutoScroll((prev) => !prev)}
            className={cn(
              "inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs border transition-colors",
              autoScroll
                ? "bg-[#0928B1]/10 dark:bg-[#7596FF]/15 border-[#0928B1]/25 dark:border-[#7596FF]/30 text-[#0928B1] dark:text-[#7596FF]"
                : "bg-white dark:bg-[#090a0c] border-[#D9D9D9] dark:border-[#262930] text-[#666666] dark:text-[#666666]"
            )}
            title="Otomatis gulir ke bawah saat ada langkah baru"
          >
            <ArrowDownCircle className="h-3 w-3" />
            <span>Gulir otomatis: {autoScroll ? "Aktif" : "Mati"}</span>
          </button>

          {events.length > 0 && (
            <button
              type="button"
              onClick={handleCopyTraceJson}
              className="inline-flex items-center gap-1 rounded-md border border-[#D9D9D9] dark:border-[#262930] bg-white dark:bg-[#090a0c] hover:bg-[#B4C7FF] dark:hover:bg-[#1e2229] px-2 py-1 text-xs text-[#666666] dark:text-[#666666] transition-colors"
              title="Salin data jejak analisis lengkap"
            >
              {copiedTrace ? (
                <>
                  <Check className="h-3 w-3 text-emerald-600 dark:text-emerald-400" />
                  <span>Tersalin</span>
                </>
              ) : (
                <>
                  <Copy className="h-3 w-3" />
                  <span>Salin JSON</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="space-y-2">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#666666] dark:text-[#666666]" />
            <input
              type="text"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              placeholder="Cari catatan langkah..."
              className="w-full rounded-lg border border-[#D9D9D9] dark:border-[#262930] bg-white dark:bg-[#090a0c] pl-9 pr-3 py-1.5 text-xs text-[#333333] dark:text-[#f1f5f9] placeholder:text-[#666666]/70 dark:placeholder:text-[#666666]/70 focus:outline-none focus:border-[#0928B1] dark:focus:border-[#7596FF]"
            />
          </div>

          <div className="flex flex-wrap items-center gap-1">
            {(
              [
                { id: "all", label: "Semua" },
                { id: "data", label: "Data" },
                { id: "valuation", label: "Valuasi" },
                { id: "research", label: "Riset" },
                { id: "qa", label: "Uji mutu" },
              ] as const
            ).map((cat) => (
              <button
                key={cat.id}
                type="button"
                onClick={() => setFilterType(cat.id)}
                className={cn(
                  "px-2.5 py-1 rounded-md text-xs transition-colors border",
                  filterType === cat.id
                    ? "bg-[#0928B1] text-white border-[#0928B1] font-medium"
                    : "bg-white dark:bg-[#090a0c] text-[#666666] dark:text-[#666666] border-[#D9D9D9] dark:border-[#262930] hover:text-[#333333] dark:hover:text-[#f1f5f9]"
                )}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {selectedAuthor !== "all" && (
          <div className="flex items-center gap-2 text-xs text-[#666666] dark:text-[#666666]">
            <span>Filter agen: <strong>{getFriendlyAgent(selectedAuthor).title}</strong></span>
            <button
              type="button"
              onClick={() => onFilterAuthor?.("all")}
              className="text-[#0928B1] dark:text-[#7596FF] underline text-xs"
            >
              Tampilkan semua
            </button>
          </div>
        )}
      </div>

      {/* Events List */}
      <div
        ref={listRef}
        className="max-h-[500px] min-h-[240px] overflow-y-auto divide-y divide-[#D9D9D9]/60 dark:divide-[#262930]/60 pr-1"
      >
        {filteredEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center space-y-2">
            <Activity className="h-6 w-6 text-[#666666] dark:text-[#666666]" />
            <h3 className="font-serif text-base font-medium text-[#333333] dark:text-[#f1f5f9]">
              {events.length === 0 ? "Belum ada catatan langkah" : "Tidak ada langkah yang sesuai"}
            </h3>
            <p className="text-xs text-[#666666] dark:text-[#666666] max-w-sm">
              {events.length === 0
                ? `Jalankan analisis untuk ${ticker || "emiten terpilih"} untuk melihat proses alur kerja multi-agen.`
                : "Coba ubah kata kunci pencarian atau hapus filter kategori."}
            </p>
          </div>
        ) : (
          filteredEvents.map((event, idx) => (
            <EventRow
              key={event.seq || idx}
              event={event}
              prevEvent={idx > 0 ? filteredEvents[idx - 1] : undefined}
              ticker={ticker}
              isLast={idx === filteredEvents.length - 1}
            />
          ))
        )}
      </div>
    </div>
  )
})
