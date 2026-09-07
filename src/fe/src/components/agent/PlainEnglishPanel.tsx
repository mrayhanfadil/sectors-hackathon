import { memo, useState, useRef, useEffect, useMemo } from "react"
import {
  Activity,
  ChevronDown,
  ChevronUp,
  Clock,
  Code2,
  Filter,
  Layers,
  Sparkles,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import {
  getFriendlyAgent,
  getEventActionDescription,
  formatDurationMs,
  formatTimestamp,
  type TraceEvent,
} from "./AGENT_FRIENDLY_META"

export interface PlainEnglishPanelProps {
  events: TraceEvent[]
  running: boolean
  ticker: string
  selectedAuthor?: string
  onFilterAuthor?: (author: string) => void
  className?: string
}

/** Static dark-mode companions for dynamic agent badge colors (kept literal for Tailwind). */
function darkBadgeClasses(badgeBg: string): string {
  if (badgeBg.includes("neutral-900")) return "dark:border-neutral-300 dark:bg-neutral-100 dark:text-neutral-900"
  if (badgeBg.includes("neutral-")) return "dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300"
  if (badgeBg.includes("sky-")) return "dark:border-sky-800 dark:bg-sky-950 dark:text-sky-200"
  if (badgeBg.includes("amber-")) return "dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200"
  if (badgeBg.includes("violet-")) return "dark:border-violet-800 dark:bg-violet-950 dark:text-violet-200"
  if (badgeBg.includes("emerald-")) return "dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-200"
  if (badgeBg.includes("teal-")) return "dark:border-teal-800 dark:bg-teal-950 dark:text-teal-200"
  if (badgeBg.includes("rose-")) return "dark:border-rose-800 dark:bg-rose-950 dark:text-rose-200"
  if (badgeBg.includes("cyan-")) return "dark:border-cyan-800 dark:bg-cyan-950 dark:text-cyan-200"
  if (badgeBg.includes("indigo-")) return "dark:border-indigo-800 dark:bg-indigo-950 dark:text-indigo-200"
  if (badgeBg.includes("pink-")) return "dark:border-pink-800 dark:bg-pink-950 dark:text-pink-200"
  if (badgeBg.includes("orange-")) return "dark:border-orange-800 dark:bg-orange-950 dark:text-orange-200"
  if (badgeBg.includes("red-")) return "dark:border-red-800 dark:bg-red-950 dark:text-red-200"
  return "dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300"
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
  const AgentIcon = agent.icon

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
    event.function_calls?.length > 0 ||
    event.function_responses?.length > 0 ||
    event.state_delta_keys?.length > 0 ||
    Boolean(event.branch) ||
    Boolean(event.transfer_to)

  return (
    <div className="group border-b border-neutral-100 p-3.5 transition-colors hover:bg-neutral-50/80 dark:border-neutral-800 dark:hover:bg-neutral-900/80">
      <div className="flex items-start justify-between gap-3">
        {/* Agent badge + sequence */}
        <div className="flex flex-wrap items-center gap-2">
          <div
            className={cn(
              "inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-medium",
              agent.badgeBg,
              agent.badgeText,
              agent.badgeBorder,
              darkBadgeClasses(agent.badgeBg)
            )}
          >
            <AgentIcon className="h-3.5 w-3.5 shrink-0" />
            <span>{agent.shortLabel}</span>
          </div>

          <span className="font-mono text-[11px] text-neutral-400 dark:text-neutral-500">
            #{event.seq}
          </span>

          {event.event_type && event.event_type !== "text" && (
            <span className="rounded bg-neutral-100 px-1.5 py-0.2 font-mono text-[10px] text-neutral-500 dark:bg-neutral-800 dark:text-neutral-400">
              {event.event_type}
            </span>
          )}
        </div>

        {/* Timestamp + latency */}
        <div className="flex shrink-0 items-center gap-2 text-right">
          {latencyMs !== null && latencyMs > 0 && (
            <span className="flex items-center gap-1 text-[11px] font-medium text-neutral-500 dark:text-neutral-400">
              <Clock className="h-3 w-3 text-neutral-400" />
              {formatDurationMs(latencyMs)}
            </span>
          )}
          <span className="font-mono text-[11px] text-neutral-400 dark:text-neutral-500">
            {formatTimestamp(event.ts)}
          </span>
        </div>
      </div>

      {/* Main plain Indonesian 1-line action description */}
      <div className="mt-2">
        <p className="text-sm font-medium leading-normal text-neutral-900 dark:text-neutral-100">
          {actionText}
        </p>

        {/* Narrative text snippet if available */}
        {event.text && event.text.trim().length > 0 && (
          <div className="mt-2 rounded-lg border border-neutral-200 bg-white p-2.5 text-xs leading-relaxed text-neutral-700 shadow-2xs dark:border-neutral-800 dark:bg-[#111111] dark:text-neutral-300">
            <div className="font-sans whitespace-pre-wrap break-words">
              {event.text.length > 350
                ? `${event.text.slice(0, 350)}...`
                : event.text}
            </div>
          </div>
        )}
      </div>

      {/* Technical details toggle */}
      {hasTechDetails && (
        <div className="mt-2.5">
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-[11px] font-medium text-neutral-500 transition-colors hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100"
          >
            <Code2 className="h-3 w-3 text-neutral-400" />
            <span>{expanded ? "Tutup detail teknis" : "Lihat detail teknis"}</span>
            {expanded ? (
              <ChevronUp className="h-3 w-3" />
            ) : (
              <ChevronDown className="h-3 w-3" />
            )}
          </button>

          {expanded && (
            <div className="mt-2 space-y-2 rounded-lg border border-neutral-200 bg-neutral-900 p-3 text-white shadow-none dark:border-neutral-700 dark:bg-black">
              {/* Function Calls */}
              {event.function_calls && event.function_calls.length > 0 && (
                <div className="space-y-1.5">
                  <div className="text-[11px] font-mono font-medium text-amber-300">
                    Panggilan Fungsi (Function Calls):
                  </div>
                  {event.function_calls.map((fc, i) => (
                    <div
                      key={fc.id || `${fc.name}-${i}`}
                      className="rounded bg-neutral-800 p-2 font-mono text-[11px]"
                    >
                      <div className="font-semibold text-emerald-400">
                        {fc.name}()
                      </div>
                      <pre className="mt-1 overflow-x-auto text-[10px] text-neutral-300">
                        {JSON.stringify(fc.args, null, 2)}
                      </pre>
                    </div>
                  ))}
                </div>
              )}

              {/* Function Responses */}
              {event.function_responses && event.function_responses.length > 0 && (
                <div className="space-y-1.5">
                  <div className="text-[11px] font-mono font-medium text-emerald-300">
                    Respon Fungsi (Function Responses):
                  </div>
                  {event.function_responses.map((fr, i) => (
                    <div
                      key={fr.id || `${fr.name}-${i}`}
                      className="rounded bg-neutral-800 p-2 font-mono text-[11px]"
                    >
                      <div className="font-semibold text-sky-400">
                        {fr.name} - hasil:
                      </div>
                      <pre className="mt-1 max-h-40 overflow-auto text-[10px] text-neutral-300">
                        {typeof fr.response === "object"
                          ? JSON.stringify(fr.response, null, 2)
                          : String(fr.response)}
                      </pre>
                    </div>
                  ))}
                </div>
              )}

              {/* State Delta Keys */}
              {event.state_delta_keys && event.state_delta_keys.length > 0 && (
                <div>
                  <div className="text-[11px] font-mono font-medium text-sky-300">
                    Kunci Memori Tersimpan (State Keys):
                  </div>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {event.state_delta_keys.map((k) => (
                      <span
                        key={k}
                        className="rounded bg-neutral-800 px-1.5 py-0.5 font-mono text-[10px] text-neutral-300 border border-neutral-700"
                      >
                        {k}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Node / Branch Info */}
              <div className="flex flex-wrap gap-3 pt-1 border-t border-neutral-800 text-[10px] font-mono text-neutral-400">
                {event.node && <span>node: {event.node}</span>}
                {event.branch && <span>branch: {event.branch}</span>}
                {event.transfer_to && <span>transfer_to: {event.transfer_to}</span>}
              </div>
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
  const [filterType, setFilterType] = useState<"all" | "calculations" | "data">("all")

  // Auto-scroll to bottom when streaming events arrive
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight
    }
  }, [events.length])

  const filteredEvents = useMemo(() => {
    return events.filter((ev) => {
      // Author filter
      if (selectedAuthor !== "all" && ev.author !== selectedAuthor) {
        return false
      }
      // Type filter
      if (filterType === "calculations") {
        return (
          ev.function_calls?.some((fc) => fc.name.startsWith("calc_")) ||
          ev.author === "modeler" ||
          ev.author === "sotp"
        )
      }
      if (filterType === "data") {
        return (
          ev.author === "collector" ||
          ev.author === "news_harvester" ||
          ev.author === "social_sentiment"
        )
      }
      return true
    })
  }, [events, selectedAuthor, filterType])

  const authorsInTrace = useMemo(() => {
    const set = new Set<string>()
    for (const e of events) {
      if (e.author) set.add(e.author)
    }
    return Array.from(set)
  }, [events])

  return (
    <Card className={cn("overflow-hidden border-neutral-200 shadow-none dark:border-neutral-800", className)}>
      <CardHeader className="border-b border-neutral-100 bg-neutral-50/50 py-3.5 dark:border-neutral-800 dark:bg-neutral-900/50">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-neutral-900 text-white shadow-2xs dark:bg-neutral-100 dark:text-neutral-900">
              <Activity className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
                Aktivitas Langsung Tim AI
              </CardTitle>
              <p className="text-[11px] text-neutral-500 dark:text-neutral-400">
                Transkrip langkah demi langkah dalam bahasa yang mudah dipahami
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {running && (
              <span className="flex items-center gap-1.5 rounded-full border border-amber-300 bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-900 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200">
                <span className="h-2 w-2 animate-pulse rounded-full bg-amber-500" />
                <span>Sedang Memproses...</span>
              </span>
            )}
            <Badge variant="outline" className="font-mono text-xs text-neutral-600 dark:border-neutral-700 dark:text-neutral-300">
              {filteredEvents.length} aktivitas
            </Badge>
          </div>
        </div>

        {/* Quick Filter Bar */}
        {events.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 pt-2.5 border-t border-neutral-100 dark:border-neutral-800">
            <div className="flex items-center gap-1 text-[11px] font-medium text-neutral-500 mr-1 dark:text-neutral-400">
              <Filter className="h-3 w-3" />
              <span>Filter:</span>
            </div>

            <Button
              size="sm"
              variant={filterType === "all" && selectedAuthor === "all" ? "default" : "outline"}
              className="h-6 px-2 text-[11px]"
              onClick={() => {
                setFilterType("all")
                onFilterAuthor?.("all")
              }}
            >
              Semua ({events.length})
            </Button>

            <Button
              size="sm"
              variant={filterType === "data" ? "default" : "outline"}
              className="h-6 px-2 text-[11px]"
              onClick={() => setFilterType("data")}
            >
              Data & Berita
            </Button>

            <Button
              size="sm"
              variant={filterType === "calculations" ? "default" : "outline"}
              className="h-6 px-2 text-[11px]"
              onClick={() => setFilterType("calculations")}
            >
              Perhitungan Valuasi
            </Button>

            {authorsInTrace.map((aKey) => {
              const aMeta = getFriendlyAgent(aKey)
              const isSelected = selectedAuthor === aKey
              return (
                <Button
                  key={aKey}
                  size="sm"
                  variant={isSelected ? "default" : "outline"}
                  className="h-6 px-2 text-[11px]"
                  onClick={() => {
                    setFilterType("all")
                    onFilterAuthor?.(isSelected ? "all" : aKey)
                  }}
                >
                  {aMeta.shortLabel}
                </Button>
              )
            })}
          </div>
        )}
      </CardHeader>

      <CardContent className="p-0">
        <div
          ref={listRef}
          className="max-h-[64vh] min-h-[320px] overflow-y-auto divide-y divide-neutral-100 dark:divide-neutral-800"
        >
          {filteredEvents.length === 0 ? (
            <div className="flex flex-col items-center justify-center px-4 py-16 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-neutral-100 text-neutral-400 dark:bg-neutral-800 dark:text-neutral-500">
                <Sparkles className="h-6 w-6" />
              </div>
              <h3 className="mt-3 text-sm font-semibold text-neutral-900 dark:text-neutral-100">
                Belum ada aktivitas
              </h3>
              <p className="mt-1 max-w-sm text-xs leading-relaxed text-neutral-500 dark:text-neutral-400">
                Klik <span className="font-semibold text-neutral-800 dark:text-neutral-200">Jalankan Analisis</span> di atas untuk memulai penyelidikan saham {ticker} secara otomatis.
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
      </CardContent>
    </Card>
  )
})
