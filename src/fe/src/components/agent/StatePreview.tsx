import { useState, useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Database, ChevronDown, ChevronRight, Search, Copy, Check } from "lucide-react"
import { useStatePreview, type TraceEvent } from "./useStatePreview"

export interface StatePreviewProps {
  events: TraceEvent[]
  className?: string
}

export function StatePreview({ events, className = "" }: StatePreviewProps) {
  const { items, summaryText } = useStatePreview(events)
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set())
  const [searchKey, setSearchKey] = useState("")
  const [copiedKey, setCopiedKey] = useState<string | null>(null)

  const toggleKey = (key: string) => {
    setExpandedKeys((prev) => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }

  const handleCopy = (key: string, text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedKey(key)
    setTimeout(() => setCopiedKey(null), 1500)
  }

  const filteredItems = useMemo(() => {
    if (!searchKey.trim()) return items
    const q = searchKey.toLowerCase().trim()
    return items.filter(
      (it) =>
        it.key.toLowerCase().includes(q) ||
        it.author.toLowerCase().includes(q) ||
        it.typeTag.toLowerCase().includes(q)
    )
  }, [items, searchKey])

  return (
    <Card
      className={`rounded-lg border border-neutral-800 bg-neutral-950 text-neutral-100 shadow-md overflow-hidden flex flex-col font-mono ${className}`}
    >
      <CardHeader className="py-2.5 px-3.5 flex flex-row items-center justify-between space-y-0 border-b border-neutral-800 bg-neutral-900/90">
        <div className="flex items-center gap-2 min-w-0">
          <div className="flex h-6 w-6 items-center justify-center rounded bg-neutral-800 text-cyan-400 border border-neutral-700 shrink-0">
            <Database className="h-3.5 w-3.5" />
          </div>
          <CardTitle className="text-xs font-bold uppercase tracking-wider text-neutral-100 font-mono">
            ISI MEMORI MESIN
          </CardTitle>
        </div>
        <Badge
          variant="secondary"
          className="text-[9px] font-mono text-cyan-300 bg-cyan-950/80 border-cyan-800 px-1.5 py-0 shrink-0"
        >
          {items.length} KUNCI
        </Badge>
      </CardHeader>

      {/* Filter / Search Bar */}
      {items.length > 0 && (
        <div className="p-2 border-b border-neutral-800 bg-neutral-950/90">
          <div className="relative flex items-center">
            <Search className="absolute left-2 h-3 w-3 text-neutral-500" />
            <input
              type="text"
              value={searchKey}
              onChange={(e) => setSearchKey(e.target.value)}
              placeholder="Cari kunci data (mis. dcf, valuasi)..."
              className="w-full rounded bg-neutral-900 border border-neutral-800 pl-7 pr-2 py-1 text-[11px] font-mono text-neutral-200 placeholder:text-neutral-600 focus:outline-none focus:border-neutral-700"
            />
          </div>
        </div>
      )}

      <CardContent className="p-0 flex-1 flex flex-col justify-between">
        <div className="max-h-[380px] overflow-y-auto divide-y divide-neutral-900 scrollbar-thin">
          {items.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 px-4 text-center font-mono text-xs">
              <Database className="h-6 w-6 text-neutral-600 mb-2" />
              <p className="font-semibold text-neutral-400">BELUM ADA MEMORI AKTIF</p>
              <p className="text-[11px] text-neutral-600 mt-1">
                Kunci data akan muncul saat mesin berjalan atau saat proses dimuat.
              </p>
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="py-8 text-center text-xs text-neutral-500 font-mono">
              Tidak ada kunci yang cocok dengan &quot;{searchKey}&quot;
            </div>
          ) : (
            filteredItems.map((item) => {
              const isExpanded = expandedKeys.has(item.key)
              return (
                <div
                  key={item.key}
                  className="px-3 py-2 hover:bg-neutral-900/60 transition-colors text-xs"
                >
                  <button
                    type="button"
                    onClick={() => toggleKey(item.key)}
                    className="w-full text-left focus:outline-none cursor-pointer"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-1.5 min-w-0">
                        {isExpanded ? (
                          <ChevronDown className="h-3.5 w-3.5 text-neutral-500 shrink-0" />
                        ) : (
                          <ChevronRight className="h-3.5 w-3.5 text-neutral-500 shrink-0" />
                        )}
                        <span className="font-mono text-[11px] font-bold text-cyan-300 break-all">
                          {item.key}
                        </span>
                      </div>
                      <div className="shrink-0 font-mono text-[10px]">
                        {item.hasValue ? (
                          <span className="text-neutral-400 bg-neutral-900 border border-neutral-800 px-1 py-0.2 rounded">
                            {item.typeTag}
                          </span>
                        ) : (
                          <span className="text-neutral-600 italic">not in event</span>
                        )}
                      </div>
                    </div>

                    {!isExpanded && (
                      <div className="mt-1 pl-5">
                        {!item.hasValue ? (
                          <div className="font-mono text-[10px] text-neutral-600 flex items-center gap-1.5">
                            <span>-</span>
                            <span className="italic">(kunci dirujuk di daftar perubahan)</span>
                          </div>
                        ) : (
                          <div className="font-mono text-[10px] text-neutral-400 line-clamp-1 break-words">
                            {item.previewSnippet}
                          </div>
                        )}
                      </div>
                    )}
                  </button>

                  {isExpanded && (
                    <div className="mt-2 pl-5 space-y-1.5">
                      {!item.hasValue ? (
                        <div className="rounded border border-neutral-800 bg-neutral-900/80 px-2.5 py-1.5 font-mono text-[10px] text-neutral-500 italic">
                          Kunci dirujuk di daftar perubahan tanpa nilai langsung.
                        </div>
                      ) : (
                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between text-[10px] text-neutral-500 font-mono">
                            <span>
                              Updated by <strong className="text-emerald-400">{item.author || "agent"}</strong> (#{item.lastUpdatedSeq})
                            </span>
                            <div className="flex items-center gap-2">
                              <span>
                                {item.byteSize} bytes{item.isTruncated ? " · truncated" : ""}
                              </span>
                              <button
                                type="button"
                                onClick={() => handleCopy(item.key, item.fullFormatted)}
                                className="flex items-center gap-1 rounded bg-neutral-800 hover:bg-neutral-700 px-1.5 py-0.5 text-neutral-300 transition-colors"
                                title="Copy state value"
                              >
                                {copiedKey === item.key ? (
                                  <>
                                    <Check className="h-2.5 w-2.5 text-emerald-400" />
                                    <span>TERSALIN</span>
                                  </>
                                ) : (
                                  <>
                                    <Copy className="h-2.5 w-2.5" />
                                    <span>SALIN</span>
                                  </>
                                )}
                              </button>
                            </div>
                          </div>
                          <pre className="max-h-64 overflow-auto whitespace-pre-wrap break-words rounded bg-black p-2 font-mono text-[10px] leading-relaxed text-neutral-200 border border-neutral-800">
                            {item.fullFormatted}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })
          )}
        </div>

        <div className="border-t border-neutral-800 bg-neutral-900/60 px-3 py-1.5 text-[10px] font-mono text-neutral-400 flex items-center justify-between shrink-0">
          <span>{summaryText}</span>
          <span className="text-neutral-500">arsip data mesin</span>
        </div>
      </CardContent>
    </Card>
  )
}
