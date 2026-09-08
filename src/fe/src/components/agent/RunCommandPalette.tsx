import { useEffect, useState, useMemo, useRef, useCallback } from "react"
import {
  Search,
  Terminal,
  Play,
  History,
  CheckCircle2,
  AlertCircle,
  Check,
  X,
  CornerDownLeft,
  ArrowUpDown,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import type { AgentRunItem } from "./RunHistoryPanel"
import type { UniverseTicker } from "./tickers"

export interface RunCommandPaletteProps {
  isOpen: boolean
  onClose: () => void
  currentTicker: string
  onSelectTicker: (ticker: string) => void
  onRunTicker: (ticker: string) => void
  runs: AgentRunItem[]
  selectedRunId?: string | null
  onSelectRun: (runId: string) => void
  universe: UniverseTicker[]
  knownTickers: string[]
  running: boolean
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

function truncateId(id: string): string {
  if (!id) return "-"
  return id.length > 14 ? `${id.slice(0, 12)}…` : id
}

export function RunCommandPalette({
  isOpen,
  onClose,
  currentTicker,
  onSelectTicker,
  onRunTicker,
  runs,
  selectedRunId,
  onSelectRun,
  universe,
  knownTickers,
  running,
}: RunCommandPaletteProps) {
  const [query, setQuery] = useState("")
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  // Focus input on open
  useEffect(() => {
    if (isOpen) {
      setQuery("")
      setSelectedIndex(0)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [isOpen])

  // Filter tickers
  const filteredTickers = useMemo(() => {
    const q = query.trim().toUpperCase()
    const all = knownTickers.length > 0 ? knownTickers : ["ADRO", "BBCA", "CDIA", "MTEL", "POWR", "RATU"]
    if (!q) return all.slice(0, 8)
    return all.filter((t) => {
      const u = universe.find((item) => item.kode === t)
      const name = (u?.nama || "").toUpperCase()
      return t.includes(q) || name.includes(q)
    }).slice(0, 8)
  }, [query, knownTickers, universe])

  // Filter runs
  const filteredRuns = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return runs.slice(0, 12)
    return runs.filter(
      (r) =>
        r.ticker.toLowerCase().includes(q) ||
        r.run_id.toLowerCase().includes(q) ||
        r.status.toLowerCase().includes(q)
    ).slice(0, 12)
  }, [query, runs])

  // Flattened items for keyboard navigation
  type PaletteItem =
    | { type: "ticker"; ticker: string; meta?: UniverseTicker }
    | { type: "run"; run: AgentRunItem }

  const items: PaletteItem[] = useMemo(() => {
    const res: PaletteItem[] = []
    for (const t of filteredTickers) {
      const meta = universe.find((u) => u.kode === t)
      res.push({ type: "ticker", ticker: t, meta })
    }
    for (const r of filteredRuns) {
      res.push({ type: "run", run: r })
    }
    return res
  }, [filteredTickers, filteredRuns, universe])

  // Reset selected index when items change
  useEffect(() => {
    setSelectedIndex(0)
  }, [items.length])

  // Scroll active item into view
  useEffect(() => {
    if (listRef.current) {
      const activeEl = listRef.current.querySelector(`[data-index="${selectedIndex}"]`)
      if (activeEl) {
        activeEl.scrollIntoView({ block: "nearest" })
      }
    }
  }, [selectedIndex])

  const handleSelect = useCallback(
    (item: PaletteItem, executeRun = false) => {
      if (item.type === "ticker") {
        onSelectTicker(item.ticker)
        if (executeRun && !running) {
          onRunTicker(item.ticker)
        }
        onClose()
      } else if (item.type === "run") {
        onSelectRun(item.run.run_id)
        onClose()
      }
    },
    [onSelectTicker, onRunTicker, onSelectRun, onClose, running]
  )

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault()
        onClose()
      } else if (e.key === "ArrowDown") {
        e.preventDefault()
        setSelectedIndex((prev) => (items.length > 0 ? (prev + 1) % items.length : 0))
      } else if (e.key === "ArrowUp") {
        e.preventDefault()
        setSelectedIndex((prev) => (items.length > 0 ? (prev - 1 + items.length) % items.length : 0))
      } else if (e.key === "Enter") {
        e.preventDefault()
        if (items[selectedIndex]) {
          handleSelect(items[selectedIndex], e.shiftKey || e.ctrlKey || e.metaKey)
        }
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [isOpen, items, selectedIndex, handleSelect, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center p-4 pt-16 sm:pt-24 backdrop-blur-xs bg-black/70 animate-in fade-in duration-150">
      <div
        className="w-full max-w-2xl rounded-lg border border-neutral-700 bg-neutral-950 text-neutral-100 shadow-2xl overflow-hidden flex flex-col font-sans"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Command Palette Header */}
        <div className="flex items-center justify-between px-3.5 py-2.5 bg-neutral-900/90 border-b border-neutral-800 text-xs font-mono">
          <div className="flex items-center gap-2 text-neutral-300">
            <Terminal className="h-4 w-4 text-emerald-400" />
            <span className="font-semibold text-neutral-200">QUANT RUN SELECTOR // COMMAND PALETTE</span>
          </div>
          <div className="flex items-center gap-1 text-[11px] text-neutral-400">
            <span className="rounded bg-neutral-800 px-1.5 py-0.5 border border-neutral-700">ESC</span>
            <span>to close</span>
          </div>
        </div>

        {/* Input Bar */}
        <div className="relative flex items-center px-3.5 py-3 border-b border-neutral-800 bg-neutral-950">
          <Search className="h-4 w-4 text-neutral-400 shrink-0 mr-2.5" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type ticker code (BBCA, CDIA...), run ID, or status..."
            className="w-full bg-transparent text-sm font-mono text-neutral-100 placeholder:text-neutral-500 focus:outline-none"
            spellCheck={false}
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery("")}
              className="text-neutral-500 hover:text-neutral-300 p-1"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* Results List */}
        <div
          ref={listRef}
          className="max-h-[380px] overflow-y-auto divide-y divide-neutral-900 p-2 space-y-2 text-xs"
        >
          {items.length === 0 ? (
            <div className="py-12 text-center text-neutral-500 font-mono text-xs">
              No matching ticker or run found for &quot;{query}&quot;
            </div>
          ) : (
            <>
              {/* Tickers Section */}
              {filteredTickers.length > 0 && (
                <div>
                  <div className="px-2 py-1 text-[10px] font-mono font-semibold uppercase tracking-wider text-neutral-500 flex items-center justify-between">
                    <span>Universe Tickers (Select &amp; Execute)</span>
                    <span>{filteredTickers.length} results</span>
                  </div>
                  <div className="mt-1 space-y-0.5">
                    {filteredTickers.map((t) => {
                      const itemIndex = items.findIndex(
                        (i) => i.type === "ticker" && i.ticker === t
                      )
                      const isSelected = selectedIndex === itemIndex
                      const isCurrent = currentTicker === t
                      const meta = universe.find((u) => u.kode === t)

                      return (
                        <div
                          key={`ticker-${t}`}
                          data-index={itemIndex}
                          onClick={() => handleSelect(items[itemIndex], false)}
                          className={`flex items-center justify-between px-3 py-2 rounded-md cursor-pointer transition-colors ${
                            isSelected
                              ? "bg-neutral-800 text-white ring-1 ring-neutral-600"
                              : "text-neutral-300 hover:bg-neutral-900"
                          }`}
                        >
                          <div className="flex items-center gap-2.5 min-w-0">
                            <span className="font-mono font-bold text-emerald-400 text-sm">
                              {t}
                            </span>
                            {meta?.nama && (
                              <span className="text-neutral-400 text-[11px] truncate">
                                {meta.nama}
                              </span>
                            )}
                            {meta?.sector && (
                              <Badge
                                variant="outline"
                                className="font-mono text-[9px] border-neutral-700 bg-neutral-900 text-neutral-400 py-0"
                              >
                                {meta.sector}
                              </Badge>
                            )}
                            {isCurrent && (
                              <span className="text-[10px] font-mono text-neutral-400 bg-neutral-900 border border-neutral-800 px-1 rounded">
                                SELECTED
                              </span>
                            )}
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleSelect(items[itemIndex], true)
                              }}
                              disabled={running}
                              className="flex items-center gap-1 rounded bg-emerald-950 border border-emerald-800 px-2 py-0.5 text-[10px] font-mono font-medium text-emerald-300 hover:bg-emerald-900 transition-colors"
                              title="Set ticker and run immediately"
                            >
                              <Play className="h-2.5 w-2.5 fill-current" />
                              <span>EXECUTE</span>
                            </button>
                            <span className="text-neutral-600 font-mono text-[10px]">
                              <CornerDownLeft className="h-3 w-3 inline" /> SELECT
                            </span>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Past Runs Section */}
              {filteredRuns.length > 0 && (
                <div className="pt-2">
                  <div className="px-2 py-1 text-[10px] font-mono font-semibold uppercase tracking-wider text-neutral-500 flex items-center justify-between">
                    <span>Persisted Run History (SQLite Blotter)</span>
                    <span>{filteredRuns.length} runs</span>
                  </div>
                  <div className="mt-1 space-y-0.5">
                    {filteredRuns.map((r) => {
                      const itemIndex = items.findIndex(
                        (i) => i.type === "run" && i.run.run_id === r.run_id
                      )
                      const isSelected = selectedIndex === itemIndex
                      const isRunActive = selectedRunId === r.run_id
                      const isLive = r.status === "running" || r.is_active

                      return (
                        <div
                          key={`run-${r.run_id}`}
                          data-index={itemIndex}
                          onClick={() => handleSelect(items[itemIndex], false)}
                          className={`flex items-center justify-between px-3 py-2 rounded-md cursor-pointer transition-colors ${
                            isSelected
                              ? "bg-neutral-800 text-white ring-1 ring-neutral-600"
                              : "text-neutral-300 hover:bg-neutral-900"
                          }`}
                        >
                          <div className="flex items-center gap-2.5 min-w-0">
                            <History className="h-3.5 w-3.5 text-neutral-500 shrink-0" />
                            <span className="font-mono font-bold text-neutral-100">
                              {r.ticker}
                            </span>
                            <span className="font-mono text-[11px] text-neutral-500">
                              {truncateId(r.run_id)}
                            </span>
                            <span className="font-mono text-[11px] text-neutral-400">
                              {r.n_events} evts
                            </span>
                            {isRunActive && (
                              <Check className="h-3 w-3 text-emerald-400 shrink-0" />
                            )}
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            {isLive ? (
                              <span className="inline-flex items-center gap-1 rounded bg-amber-950 border border-amber-800 px-1.5 py-0.5 text-[10px] font-mono font-semibold text-amber-300">
                                <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-ping" />
                                LIVE
                              </span>
                            ) : r.status === "completed" ? (
                              <span className="inline-flex items-center gap-1 rounded bg-emerald-950 border border-emerald-800 px-1.5 py-0.5 text-[10px] font-mono font-medium text-emerald-300">
                                <CheckCircle2 className="h-2.5 w-2.5" />
                                DONE
                              </span>
                            ) : r.status === "failed" ? (
                              <span className="inline-flex items-center gap-1 rounded bg-rose-950 border border-rose-800 px-1.5 py-0.5 text-[10px] font-mono font-medium text-rose-300">
                                <AlertCircle className="h-2.5 w-2.5" />
                                FAIL
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 rounded bg-neutral-900 border border-neutral-700 px-1.5 py-0.5 text-[10px] font-mono font-medium text-neutral-400">
                                {r.status}
                              </span>
                            )}
                            <span className="font-mono text-[10px] text-neutral-500">
                              {formatRelativeTime(r.started_at)}
                            </span>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer Shortcut Guide */}
        <div className="flex items-center justify-between px-3.5 py-2 bg-neutral-900/90 border-t border-neutral-800 text-[11px] font-mono text-neutral-400">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1">
              <ArrowUpDown className="h-3 w-3 text-neutral-500" />
              <span>Navigate</span>
            </span>
            <span className="flex items-center gap-1">
              <CornerDownLeft className="h-3 w-3 text-neutral-500" />
              <span>Select Run/Ticker</span>
            </span>
          </div>
          <div className="text-neutral-500">
            Real runs bound to SQLite database
          </div>
        </div>
      </div>
    </div>
  )
}
