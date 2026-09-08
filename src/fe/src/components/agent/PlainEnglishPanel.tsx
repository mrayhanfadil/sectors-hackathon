import { memo, useState, useRef, useEffect, useMemo } from "react"
import {
  Activity,
  ChevronDown,
  ChevronUp,
  Clock,
  Code2,
  Filter,
  Search,
  ArrowDownCircle,
  Copy,
  Check,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
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

function getAgentTerminalColor(author: string): { bg: string; text: string; border: string } {
  switch (author) {
    case "collector":
      return { bg: "bg-sky-950/80", text: "text-sky-300", border: "border-sky-800" }
    case "news_harvester":
    case "news_search_sub":
      return { bg: "bg-amber-950/80", text: "text-amber-300", border: "border-amber-800" }
    case "social_sentiment":
    case "social_search_sub":
      return { bg: "bg-purple-950/80", text: "text-purple-300", border: "border-purple-800" }
    case "modeler":
      return { bg: "bg-emerald-950/80", text: "text-emerald-300", border: "border-emerald-700" }
    case "analyst":
      return { bg: "bg-slate-900", text: "text-slate-200", border: "border-slate-700" }
    case "industry":
    case "industry_search_sub":
      return { bg: "bg-teal-950/80", text: "text-teal-300", border: "border-teal-800" }
    case "risk":
      return { bg: "bg-rose-950/80", text: "text-rose-300", border: "border-rose-800" }
    case "kpi":
      return { bg: "bg-cyan-950/80", text: "text-cyan-300", border: "border-cyan-800" }
    case "writer":
      return { bg: "bg-indigo-950/80", text: "text-indigo-300", border: "border-indigo-800" }
    case "visualizer":
      return { bg: "bg-pink-950/80", text: "text-pink-300", border: "border-pink-800" }
    case "sotp":
      return { bg: "bg-orange-950/80", text: "text-orange-300", border: "border-orange-800" }
    case "adversarial":
      return { bg: "bg-red-950/90", text: "text-red-300", border: "border-red-700" }
    case "critic":
      return { bg: "bg-neutral-800", text: "text-emerald-200", border: "border-emerald-600" }
    default:
      return { bg: "bg-neutral-900", text: "text-neutral-300", border: "border-neutral-700" }
  }
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
  const colors = getAgentTerminalColor(event.author)

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
    (event.state_delta_keys && event.state_delta_keys.length > 0) ||
    Boolean(event.branch) ||
    Boolean(event.transfer_to)

  const formattedSeq = String(event.seq).padStart(4, "0")

  return (
    <div className="group border-b border-neutral-900 p-2.5 transition-colors hover:bg-neutral-900/50 font-mono text-xs">
      <div className="flex flex-wrap items-center justify-between gap-2">
        {/* Sequence + Agent tag + Event type */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[11px] font-mono text-cyan-400 font-bold">
            #{formattedSeq}
          </span>

          <span
            className={cn(
              "inline-flex items-center gap-1 rounded border px-1.5 py-0.2 text-[10px] font-mono font-bold tracking-tight",
              colors.bg,
              colors.text,
              colors.border
            )}
          >
            {agent.shortLabel.toUpperCase()}
          </span>

          {event.event_type && (
            <span className="rounded bg-neutral-900 px-1 py-0.2 font-mono text-[9px] text-neutral-400 border border-neutral-800 uppercase">
              {event.event_type}
            </span>
          )}

          {event.node && (
            <span className="text-[10px] font-mono text-neutral-500">
              node:{event.node}
            </span>
          )}
        </div>

        {/* Timestamp + Real latency diff */}
        <div className="flex items-center gap-2 text-right text-[10px] font-mono text-neutral-500">
          {latencyMs !== null && latencyMs > 0 && (
            <span className="text-emerald-400/90 font-medium">
              +{latencyMs}ms
            </span>
          )}
          <span>{formatTimestamp(event.ts)}</span>
        </div>
      </div>

      {/* Main Action Line */}
      <div className="mt-1.5">
        <p className="text-xs font-mono font-medium leading-normal text-neutral-200">
          {actionText}
        </p>

        {/* Text snippet if available */}
        {event.text && event.text.trim().length > 0 && (
          <div className="mt-1.5 rounded bg-black/80 border border-neutral-800/80 p-2 text-[11px] font-mono leading-relaxed text-neutral-300">
            <div className="whitespace-pre-wrap break-words">
              {event.text.length > 500
                ? `${event.text.slice(0, 500)}…`
                : event.text}
            </div>
          </div>
        )}
      </div>

      {/* Function Calls / Responses / Delta keys preview */}
      {hasTechDetails && (
        <div className="mt-2">
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-[10px] font-mono text-neutral-400 hover:text-neutral-200 transition-colors focus:outline-none"
          >
            <Code2 className="h-3 w-3 text-neutral-500" />
            <span>{expanded ? "HIDE PAYLOAD" : "INSPECT PAYLOAD / PARAMS"}</span>
            {expanded ? (
              <ChevronUp className="h-3 w-3 text-neutral-500" />
            ) : (
              <ChevronDown className="h-3 w-3 text-neutral-500" />
            )}
          </button>

          {expanded && (
            <div className="mt-2 space-y-2 rounded border border-neutral-800 bg-black p-2.5 text-neutral-200">
              {/* Function Calls */}
              {event.function_calls && event.function_calls.length > 0 && (
                <div className="space-y-1">
                  <div className="text-[10px] font-mono font-bold text-amber-400 uppercase">
                    Function Invocations:
                  </div>
                  {event.function_calls.map((fc, i) => (
                    <FunctionCallCard key={fc.id || `${fc.name}-${i}`} fc={fc} />
                  ))}
                </div>
              )}

              {/* Function Responses */}
              {event.function_responses && event.function_responses.length > 0 && (
                <div className="space-y-1">
                  <div className="text-[10px] font-mono font-bold text-emerald-400 uppercase">
                    Function Returns:
                  </div>
                  {event.function_responses.map((fr, i) => (
                    <FunctionResponseCard key={fr.id || `${fr.name}-${i}`} fr={fr} />
                  ))}
                </div>
              )}

              {/* State Delta Keys */}
              {event.state_delta_keys && event.state_delta_keys.length > 0 && (
                <div className="pt-1">
                  <div className="text-[10px] font-mono font-bold text-cyan-400 uppercase">
                    State Keys Delta:
                  </div>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {event.state_delta_keys.map((k) => (
                      <span
                        key={k}
                        className="rounded bg-neutral-900 px-1.5 py-0.2 font-mono text-[9px] text-cyan-300 border border-neutral-800"
                      >
                        {k}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Node / Branch Info */}
              <div className="flex flex-wrap gap-3 pt-1 border-t border-neutral-900 text-[9px] font-mono text-neutral-500">
                {event.node && <span>NODE: {event.node}</span>}
                {event.branch && <span>BRANCH: {event.branch}</span>}
                {event.transfer_to && <span>TRANSFER_TO: {event.transfer_to}</span>}
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
  const [filterType, setFilterType] = useState<"all" | "calculations" | "data" | "qa" | "errors">("all")
  const [searchText, setSearchText] = useState("")
  const [autoScroll, setAutoScroll] = useState(true)
  const [copiedTrace, setCopiedTrace] = useState(false)

  // Auto-scroll to bottom when streaming events arrive
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
      // Category filter
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
          ev.author === "social_sentiment" ||
          ev.author === "news_search_sub" ||
          ev.author === "social_search_sub"
        )
      }
      if (filterType === "qa") {
        return ev.author === "adversarial" || ev.author === "critic"
      }
      if (filterType === "errors") {
        return ev.event_type === "error" || ev.text.toLowerCase().includes("error")
      }

      // Free text search
      if (searchText.trim()) {
        const q = searchText.toLowerCase().trim()
        const textMatch = ev.text.toLowerCase().includes(q)
        const authorMatch = ev.author.toLowerCase().includes(q)
        const nodeMatch = ev.node?.toLowerCase().includes(q)
        const fcMatch = ev.function_calls?.some((fc) => fc.name.toLowerCase().includes(q))
        return textMatch || authorMatch || nodeMatch || fcMatch
      }

      return true
    })
  }, [events, selectedAuthor, filterType, searchText])

  const authorsInTrace = useMemo(() => {
    const set = new Set<string>()
    for (const e of events) {
      if (e.author) set.add(e.author)
    }
    return Array.from(set)
  }, [events])

  const handleCopyTraceJson = () => {
    const jsonStr = JSON.stringify(events, null, 2)
    navigator.clipboard.writeText(jsonStr)
    setCopiedTrace(true)
    setTimeout(() => setCopiedTrace(false), 2000)
  }

  return (
    <Card className={cn("overflow-hidden border-neutral-800 bg-neutral-950 text-neutral-100 shadow-md font-mono", className)}>
      <CardHeader className="border-b border-neutral-800 bg-neutral-900/90 p-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-neutral-800 text-emerald-400 border border-neutral-700">
              <Activity className="h-3.5 w-3.5" />
            </div>
            <div>
              <CardTitle className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-100">
                CATATAN LANGKAH MESIN
              </CardTitle>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {running && (
              <span className="flex items-center gap-1 rounded bg-amber-950 border border-amber-800 px-2 py-0.5 text-[10px] font-mono font-bold text-amber-300">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-ping" />
                <span>STREAMING</span>
              </span>
            )}
            <Badge variant="outline" className="font-mono text-[10px] border-neutral-700 bg-neutral-900 text-neutral-300">
              {filteredEvents.length} / {events.length} EVTS
            </Badge>

            <button
              type="button"
              onClick={() => setAutoScroll((prev) => !prev)}
              className={cn(
                "flex items-center gap-1 rounded px-1.5 py-0.5 text-[9px] font-mono border transition-colors",
                autoScroll
                  ? "bg-emerald-950 border-emerald-800 text-emerald-300"
                  : "bg-neutral-900 border-neutral-800 text-neutral-500"
              )}
              title="Toggle auto-scroll on new events"
            >
              <ArrowDownCircle className="h-2.5 w-2.5" />
              <span>SCROLL: {autoScroll ? "ON" : "OFF"}</span>
            </button>

            {events.length > 0 && (
              <button
                type="button"
                onClick={handleCopyTraceJson}
                className="flex items-center gap-1 rounded bg-neutral-800 hover:bg-neutral-700 border border-neutral-700 px-1.5 py-0.5 text-[9px] font-mono text-neutral-300 transition-colors"
                title="Copy entire trace as JSON"
              >
                {copiedTrace ? (
                  <>
                    <Check className="h-2.5 w-2.5 text-emerald-400" />
                    <span>TERSALIN</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-2.5 w-2.5" />
                    <span>JSON</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {/* Search & Category Filter Toolbar */}
        <div className="mt-2 pt-2 border-t border-neutral-800 space-y-1.5">
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative flex-1 min-w-[140px]">
              <Search className="absolute left-2 top-1.5 h-3 w-3 text-neutral-500" />
              <input
                type="text"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                placeholder="Search event logs (text, function, node)..."
                className="w-full rounded bg-neutral-900 border border-neutral-800 pl-7 pr-2 py-1 text-[11px] font-mono text-neutral-200 placeholder:text-neutral-600 focus:outline-none focus:border-neutral-700"
              />
            </div>

            <div className="flex flex-wrap items-center gap-1">
              {(
                [
                  { id: "all", label: "ALL" },
                  { id: "data", label: "DATA" },
                  { id: "calculations", label: "VALUATION" },
                  { id: "qa", label: "QA/RED TEAM" },
                  { id: "errors", label: "ERRORS" },
                ] as const
              ).map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => setFilterType(cat.id)}
                  className={cn(
                    "px-1.5 py-0.5 rounded text-[9px] font-mono transition-colors border",
                    filterType === cat.id
                      ? "bg-neutral-800 text-white font-bold border-neutral-600"
                      : "bg-neutral-900/60 text-neutral-400 border-neutral-800 hover:text-neutral-200"
                  )}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          {/* Author micro-chips if multiple authors exist */}
          {authorsInTrace.length > 0 && (
            <div className="flex flex-wrap items-center gap-1 pt-1">
              <span className="text-[9px] font-mono text-neutral-500 mr-1">AGENTS:</span>
              <button
                type="button"
                onClick={() => onFilterAuthor?.("all")}
                className={cn(
                  "px-1.5 py-0.2 rounded text-[9px] font-mono transition-colors border",
                  selectedAuthor === "all"
                    ? "bg-emerald-950 border-emerald-800 text-emerald-300 font-bold"
                    : "bg-neutral-900 border-neutral-800 text-neutral-400 hover:text-neutral-200"
                )}
              >
                ALL ({events.length})
              </button>
              {authorsInTrace.map((aKey) => {
                const aMeta = getFriendlyAgent(aKey)
                const isSelected = selectedAuthor === aKey
                const aCount = events.filter((e) => e.author === aKey).length
                return (
                  <button
                    key={aKey}
                    type="button"
                    onClick={() => onFilterAuthor?.(isSelected ? "all" : aKey)}
                    className={cn(
                      "px-1.5 py-0.2 rounded text-[9px] font-mono transition-colors border",
                      isSelected
                        ? "bg-emerald-950 border-emerald-800 text-emerald-300 font-bold"
                        : "bg-neutral-900 border-neutral-800 text-neutral-400 hover:text-neutral-200"
                    )}
                  >
                    {aMeta.shortLabel.toUpperCase()} ({aCount})
                  </button>
                )
              })}
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <div
          ref={listRef}
          className="max-h-[580px] min-h-[360px] overflow-y-auto divide-y divide-neutral-900 scrollbar-thin bg-black"
        >
          {filteredEvents.length === 0 ? (
            <div className="flex flex-col items-center justify-center px-4 py-16 text-center font-mono text-xs">
              <Activity className="h-8 w-8 text-neutral-700 mb-2" />
              <h3 className="font-bold text-neutral-400">
                {events.length === 0 ? "BELUM ADA CATATAN" : "TIDAK ADA YANG COCOK"}
              </h3>
              <p className="mt-1 max-w-sm text-[11px] text-neutral-600">
                {events.length === 0
                  ? `Execute a run for ${ticker || "selected ticker"} to stream live multi-agent execution events.`
                  : "Try clearing filter criteria or searching a different term."}
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
