import { useState, useMemo } from "react"
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
    <div
      className={`rounded-xl border border-[#D9D9D9] dark:border-[#262930] bg-white dark:bg-[#090a0c] p-5 font-sans space-y-3.5 shadow-none ${className}`}
    >
      <div className="flex items-center justify-between pb-3 border-b border-[#D9D9D9]/60 dark:border-[#262930]/60">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#B4C7FF] dark:bg-[#1e2229] text-[#0928B1] dark:text-[#7596FF] border border-[#D9D9D9] dark:border-[#262930] shrink-0">
            <Database className="h-4 w-4" />
          </div>
          <div>
            <h3 className="font-serif text-base font-medium text-[#333333] dark:text-[#f1f5f9] truncate">
              Isi memori alur kerja
            </h3>
            <p className="text-[11px] text-[#666666] dark:text-[#666666]">
              {items.length} kunci data tersimpan
            </p>
          </div>
        </div>
      </div>

      {/* Filter / Search Bar */}
      {items.length > 0 && (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#666666] dark:text-[#666666]" />
          <input
            type="text"
            value={searchKey}
            onChange={(e) => setSearchKey(e.target.value)}
            placeholder="Cari kunci data (mis. valuation, dcf)..."
            className="w-full rounded-lg border border-[#D9D9D9] dark:border-[#262930] bg-white dark:bg-[#090a0c] pl-9 pr-3 py-1.5 text-xs text-[#333333] dark:text-[#f1f5f9] placeholder:text-[#666666]/70 dark:placeholder:text-[#666666]/70 focus:outline-none focus:border-[#0928B1] dark:focus:border-[#7596FF]"
          />
        </div>
      )}

      <div>
        <div className="max-h-[360px] overflow-y-auto divide-y divide-[#D9D9D9]/60 dark:divide-[#262930]/60">
          {items.length === 0 ? (
            <div className="py-8 px-4 text-center space-y-1">
              <p className="text-xs font-medium text-[#333333] dark:text-[#f1f5f9]">Belum ada memori aktif</p>
              <p className="text-[11px] text-[#666666] dark:text-[#666666]">
                Kunci data akan tersimpan saat tahapan analisis berjalan.
              </p>
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="py-8 text-center text-xs text-[#666666] dark:text-[#666666]">
              Tidak ada kunci yang cocok dengan &quot;{searchKey}&quot;
            </div>
          ) : (
            filteredItems.map((item) => {
              const isExpanded = expandedKeys.has(item.key)
              return (
                <div
                  key={item.key}
                  className="py-2.5 hover:bg-[#f1f5f9] dark:hover:bg-[#333333] transition-colors text-xs rounded-lg px-2"
                >
                  <button
                    type="button"
                    onClick={() => toggleKey(item.key)}
                    className="w-full text-left focus:outline-none cursor-pointer"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-1.5 min-w-0">
                        {isExpanded ? (
                          <ChevronDown className="h-3.5 w-3.5 text-[#666666] dark:text-[#666666] shrink-0" />
                        ) : (
                          <ChevronRight className="h-3.5 w-3.5 text-[#666666] dark:text-[#666666] shrink-0" />
                        )}
                        <span className="text-xs font-medium text-[#0928B1] dark:text-[#7596FF] break-all">
                          {item.key}
                        </span>
                      </div>
                      <div className="shrink-0 text-[10px]">
                        {item.hasValue ? (
                          <span className="text-[#666666] dark:text-[#666666] bg-[#B4C7FF] dark:bg-[#1e2229] border border-[#D9D9D9] dark:border-[#262930] px-1.5 py-0.5 rounded">
                            {item.typeTag}
                          </span>
                        ) : (
                          <span className="text-[#666666] dark:text-[#666666] italic">dirujuk</span>
                        )}
                      </div>
                    </div>

                    {!isExpanded && item.hasValue && (
                      <div className="mt-1 pl-5">
                        <div className="text-[11px] text-[#666666] dark:text-[#666666] line-clamp-1 break-words">
                          {item.previewSnippet}
                        </div>
                      </div>
                    )}
                  </button>

                  {isExpanded && (
                    <div className="mt-2 pl-5 space-y-1.5">
                      {!item.hasValue ? (
                        <div className="rounded-lg border border-[#D9D9D9] dark:border-[#262930] bg-[#f1f5f9] dark:bg-[#1e2229] px-2.5 py-1.5 text-[11px] text-[#666666] dark:text-[#666666] italic">
                          Kunci dirujuk di daftar perubahan tanpa nilai langsung.
                        </div>
                      ) : (
                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between text-[11px] text-[#666666] dark:text-[#666666]">
                            <span>
                              Diperbarui oleh: <strong className="text-[#333333] dark:text-[#f1f5f9]">{item.author || "agen"}</strong> (Langkah {item.lastUpdatedSeq})
                            </span>
                            <div className="flex items-center gap-2">
                              <span>
                                {item.byteSize} B{item.isTruncated ? " · dipotong" : ""}
                              </span>
                              <button
                                type="button"
                                onClick={() => handleCopy(item.key, item.fullFormatted)}
                                className="flex items-center gap-1 rounded border border-[#D9D9D9] dark:border-[#262930] bg-white dark:bg-[#090a0c] hover:bg-[#B4C7FF] dark:hover:bg-[#1e2229] px-2 py-0.5 text-[#333333] dark:text-[#f1f5f9] text-[10px] transition-colors"
                              >
                                {copiedKey === item.key ? (
                                  <>
                                    <Check className="h-3 w-3 text-emerald-600 dark:text-emerald-400" />
                                    <span>Tersalin</span>
                                  </>
                                ) : (
                                  <>
                                    <Copy className="h-3 w-3" />
                                    <span>Salin</span>
                                  </>
                                )}
                              </button>
                            </div>
                          </div>
                          <pre className="max-h-60 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-[#f1f5f9] dark:bg-[#1e2229] p-2.5 font-mono text-[11px] leading-relaxed text-[#333333] dark:text-[#f1f5f9] border border-[#D9D9D9] dark:border-[#262930]">
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

        <div className="pt-3 mt-2 border-t border-[#D9D9D9]/60 dark:border-[#262930]/60 text-[11px] text-[#666666] dark:text-[#666666] flex items-center justify-between">
          <span>{summaryText}</span>
          <span>Penyimpanan data analisis</span>
        </div>
      </div>
    </div>
  )
}
