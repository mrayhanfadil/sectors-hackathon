import * as React from "react"
import { useQuery } from "@tanstack/react-query"
import { fetchUniverse, type UniverseTickerItem } from "@/lib/api"
import { Search, Sparkles, X } from "lucide-react"

interface SearchModalProps {
  isOpen: boolean
  onClose: () => void
}

export function SearchModal({ isOpen, onClose }: SearchModalProps) {
  const [query, setQuery] = React.useState("")
  const inputRef = React.useRef<HTMLInputElement>(null)

  const { data: universe } = useQuery({
    queryKey: ["universe"],
    queryFn: fetchUniverse,
  })

  React.useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [isOpen])

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        if (isOpen) onClose()
        else {
          setQuery("")
          // will open via parent state
        }
      }
      if (e.key === "Escape" && isOpen) {
        onClose()
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) return null

  const filtered = (universe || []).filter((item: UniverseTickerItem) => {
    const q = query.toLowerCase().trim()
    if (!q) return true
    return (
      item.ticker.toLowerCase().includes(q) ||
      item.name.toLowerCase().includes(q) ||
      item.sector.toLowerCase().includes(q)
    )
  })

  const benchmarks = (universe || []).filter((u) => u.hasBenchmarkReport)

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="w-full max-w-2xl rounded-xl border border-[#262c38] bg-[#111317] text-slate-100 shadow-2xl overflow-hidden">
        {/* Search Input Bar */}
        <div className="flex items-center gap-3 border-b border-[#212631] px-4 py-3 bg-[#161920]">
          <Search className="h-4 w-4 text-amber-400 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search 49 IDX tickers, companies, or sectors (e.g. MTEL, BBCA, Coal, Oil)..."
            className="flex-1 bg-transparent text-sm text-slate-100 placeholder:text-slate-500 outline-none font-sans"
          />
          {query && (
            <button
              onClick={() => setQuery("")}
              className="text-slate-400 hover:text-slate-200 p-1 text-xs"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
          <kbd className="hidden sm:inline-flex items-center gap-0.5 rounded border border-[#2a303d] bg-[#0c0e12] px-1.5 py-0.5 font-mono text-[10px] text-slate-400">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-96 overflow-y-auto p-2 divide-y divide-[#1b2029]">
          {!query && (
            <div className="p-2">
              <div className="flex items-center gap-1.5 text-[11px] font-mono font-medium text-amber-400 mb-2">
                <Sparkles className="h-3 w-3" />
                <span>BENCHMARK ARCHETYPE EQUITY REPORTS</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                {benchmarks.map((b) => (
                  <a
                    key={b.ticker}
                    href={`/report/${b.ticker}`}
                    onClick={onClose}
                    className="flex items-center justify-between p-2 rounded-md bg-[#161920] hover:bg-[#1f242e] border border-[#212631] transition-colors"
                  >
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono font-bold text-amber-300 text-xs">
                          {b.ticker}
                        </span>
                        <span className="text-[10px] font-mono text-slate-400">
                          {b.archetype}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-300 line-clamp-1">
                        {b.name}
                      </div>
                    </div>
                    <div className="text-right font-mono text-xs">
                      <div className="text-slate-200">
                        {b.lastPrice.toLocaleString("id-ID")}
                      </div>
                      <div
                        className={
                          b.changePct >= 0 ? "text-emerald-400" : "text-red-400"
                        }
                      >
                        {b.changePct >= 0 ? `+${b.changePct}%` : `${b.changePct}%`}
                      </div>
                    </div>
                  </a>
                ))}
              </div>
            </div>
          )}

          <div className="p-2">
            <div className="text-[11px] font-mono text-slate-400 px-2 py-1">
              {query ? `MATCHING TICKERS (${filtered.length})` : "ALL 49 COVERED TICKERS"}
            </div>

            {filtered.length === 0 ? (
              <div className="text-center py-8 text-sm text-slate-500">
                No matching tickers found for &ldquo;{query}&rdquo;
              </div>
            ) : (
              <div className="space-y-1 mt-1">
                {filtered.map((item) => (
                  <a
                    key={item.ticker}
                    href={`/report/${item.ticker}`}
                    onClick={onClose}
                    className="flex items-center justify-between px-3 py-2 rounded-md hover:bg-[#181c24] transition-colors group"
                  >
                    <div className="flex items-center gap-3">
                      <div className="h-7 w-7 rounded bg-[#1f242e] flex items-center justify-center font-mono font-bold text-xs text-amber-400 border border-[#2a313e]">
                        {item.ticker.slice(0, 2)}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-sm text-slate-100 group-hover:text-amber-300 transition-colors">
                            {item.ticker}
                          </span>
                          <span className="text-[11px] text-slate-400">
                            {item.name}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-[10px] text-slate-500">
                          <span>{item.sector}</span>
                          <span>•</span>
                          <span>{item.industry}</span>
                        </div>
                      </div>
                    </div>

                    <div className="text-right font-mono text-xs">
                      <div className="text-slate-200">
                        {item.lastPrice.toLocaleString("id-ID")} IDR
                      </div>
                      <div
                        className={
                          item.changePct >= 0 ? "text-emerald-400" : "text-red-400"
                        }
                      >
                        {item.changePct >= 0
                          ? `+${item.changePct}%`
                          : `${item.changePct}%`}
                      </div>
                    </div>
                  </a>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer info */}
        <div className="flex items-center justify-between border-t border-[#212631] px-4 py-2 bg-[#0d0f13] text-[11px] text-slate-500 font-mono">
          <span>Sektoral.id Deterministic Equity Intelligence</span>
          <span>49 Tickers in data/sectors.db</span>
        </div>
      </div>
    </div>
  )
}
