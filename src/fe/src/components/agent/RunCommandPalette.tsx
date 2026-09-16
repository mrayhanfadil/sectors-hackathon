import { useEffect, useState, useMemo, useRef, useCallback } from "react"
import {
  Search,
  CheckCircle2,
  AlertCircle,
  Check,
  X,
  CornerDownLeft,
  ArrowUpDown,
  History,
} from "lucide-react"
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
  if (diff < 10) return "baru saja"
  if (diff < 60) return `${diff} detik lalu`
  if (diff < 3600) return `${Math.floor(diff / 60)} menit lalu`
  if (diff < 86400) return `${Math.floor(diff / 3600)} jam lalu`
  return `${Math.floor(diff / 86400)} hari lalu`
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
  runs,
  selectedRunId,
  onSelectRun,
  universe,
  knownTickers,
}: RunCommandPaletteProps) {
  const [query, setQuery] = useState("")
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isOpen) {
      setQuery("")
      setSelectedIndex(0)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [isOpen])

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

  useEffect(() => {
    setSelectedIndex(0)
  }, [items.length])

  useEffect(() => {
    if (listRef.current) {
      const activeEl = listRef.current.querySelector(`[data-index="${selectedIndex}"]`)
      if (activeEl) {
        activeEl.scrollIntoView({ block: "nearest" })
      }
    }
  }, [selectedIndex])

  const handleSelect = useCallback(
    (item: PaletteItem) => {
      if (item.type === "ticker") {
        onSelectTicker(item.ticker)
        onClose()
      } else if (item.type === "run") {
        onSelectRun(item.run.run_id)
        onClose()
      }
    },
    [onSelectTicker, onSelectRun, onClose]
  )

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
          handleSelect(items[selectedIndex])
        }
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [isOpen, items, selectedIndex, handleSelect, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center p-4 pt-16 sm:pt-24 bg-black/50 animate-in fade-in duration-150">
      <div
        className="w-full max-w-2xl rounded-xl border border-[#E7E3DA] dark:border-[#2A2822] bg-white dark:bg-[#1B1A16] text-[#1C1B17] dark:text-[#EDEAE3] shadow-lg overflow-hidden flex flex-col font-sans"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-4 py-3 bg-[#FBFAF7] dark:bg-[#14130F] border-b border-[#E7E3DA] dark:border-[#2A2822] text-xs">
          <span className="font-medium text-[#1C1B17] dark:text-[#EDEAE3]">Cari cepat emiten dan proses</span>
          <button
            type="button"
            onClick={onClose}
            className="text-[#6B6659] dark:text-[#A8A296] hover:text-[#1C1B17] dark:hover:text-[#EDEAE3]"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="relative flex items-center px-4 py-3 border-b border-[#E7E3DA] dark:border-[#2A2822]">
          <Search className="h-4 w-4 text-[#6B6659] dark:text-[#A8A296] shrink-0 mr-2.5" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ketik kode saham atau status..."
            className="w-full bg-transparent text-sm text-[#1C1B17] dark:text-[#EDEAE3] placeholder:text-[#6B6659]/70 dark:placeholder:text-[#A8A296]/70 focus:outline-none"
            spellCheck={false}
          />
        </div>

        <div
          ref={listRef}
          className="max-h-[360px] overflow-y-auto divide-y divide-[#E7E3DA]/60 dark:divide-[#2A2822]/60 p-2 space-y-1 text-xs"
        >
          {items.length === 0 ? (
            <div className="py-10 text-center text-[#6B6659] dark:text-[#A8A296] text-xs">
              Tidak ditemukan hasil untuk &quot;{query}&quot;
            </div>
          ) : (
            <>
              {filteredTickers.length > 0 && (
                <div className="p-1">
                  <div className="px-2 py-1 text-[11px] font-medium text-[#6B6659] dark:text-[#A8A296]">
                    Daftar emiten ({filteredTickers.length})
                  </div>
                  <div className="space-y-0.5">
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
                          onClick={() => handleSelect(items[itemIndex])}
                          className={`flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-colors ${
                            isSelected
                              ? "bg-[#0E6E63]/10 dark:bg-[#4FD1B5]/15 text-[#0E6E63] dark:text-[#4FD1B5]"
                              : "text-[#1C1B17] dark:text-[#EDEAE3] hover:bg-[#FBFAF7] dark:hover:bg-[#14130F]"
                          }`}
                        >
                          <div className="flex items-center gap-2.5 min-w-0">
                            <span className="font-serif font-medium text-sm">
                              {t}
                            </span>
                            {meta?.nama && (
                              <span className="text-[#6B6659] dark:text-[#A8A296] text-xs truncate">
                                {meta.nama}
                              </span>
                            )}
                            {isCurrent && (
                              <span className="text-[10px] text-[#6B6659] dark:text-[#A8A296] bg-[#F5F2EB] dark:bg-[#23211C] border border-[#E7E3DA] dark:border-[#2A2822] px-1.5 py-0.5 rounded">
                                Sedang aktif
                              </span>
                            )}
                          </div>

                          <div className="flex items-center gap-2 shrink-0 text-xs text-[#6B6659] dark:text-[#A8A296]">
                            <CornerDownLeft className="h-3 w-3 inline" />
                            <span>Pilih</span>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {filteredRuns.length > 0 && (
                <div className="p-1">
                  <div className="px-2 py-1 text-[11px] font-medium text-[#6B6659] dark:text-[#A8A296]">
                    Riwayat proses ({filteredRuns.length})
                  </div>
                  <div className="space-y-0.5">
                    {filteredRuns.map((r) => {
                      const itemIndex = items.findIndex(
                        (i) => i.type === "run" && i.run.run_id === r.run_id
                      )
                      const isSelected = selectedIndex === itemIndex
                      const isRunActive = selectedRunId === r.run_id

                      return (
                        <div
                          key={`run-${r.run_id}`}
                          data-index={itemIndex}
                          onClick={() => handleSelect(items[itemIndex])}
                          className={`flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-colors ${
                            isSelected
                              ? "bg-[#0E6E63]/10 dark:bg-[#4FD1B5]/15 text-[#0E6E63] dark:text-[#4FD1B5]"
                              : "text-[#1C1B17] dark:text-[#EDEAE3] hover:bg-[#FBFAF7] dark:hover:bg-[#14130F]"
                          }`}
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <History className="h-3.5 w-3.5 text-[#6B6659] dark:text-[#A8A296] shrink-0" />
                            <span className="font-serif font-medium">
                              {r.ticker}
                            </span>
                            <span className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">
                              {truncateId(r.run_id)}
                            </span>
                            {isRunActive && (
                              <Check className="h-3.5 w-3.5 text-[#0E6E63] dark:text-[#4FD1B5] shrink-0 ml-0.5" />
                            )}
                          </div>

                          <div className="flex items-center gap-2 shrink-0 text-[11px] text-[#6B6659] dark:text-[#A8A296]">
                            <span>{formatRelativeTime(r.started_at)}</span>
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
      </div>
    </div>
  )
}
