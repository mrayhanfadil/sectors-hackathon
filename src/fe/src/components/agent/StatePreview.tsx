import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Database, ChevronDown, ChevronRight } from "lucide-react"
import { useStatePreview, type TraceEvent } from "./useStatePreview"

export interface StatePreviewProps {
  events: TraceEvent[]
  className?: string
}

export function StatePreview({ events, className = "" }: StatePreviewProps) {
  const { items, summaryText } = useStatePreview(events)
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set())

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

  return (
    <Card className={`rounded-lg border border-neutral-200 bg-white shadow-none overflow-hidden flex flex-col dark:border-neutral-800 dark:bg-[#111111] ${className}`}>
      <CardHeader className="py-3 px-3.5 flex flex-row items-center justify-between space-y-0 border-b border-neutral-100 bg-white dark:border-neutral-800 dark:bg-[#111111]">
        <div className="flex items-center gap-2 min-w-0">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-neutral-100 text-neutral-800 border border-neutral-200 shadow-2xs shrink-0 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-200">
            <Database className="h-3.5 w-3.5 text-neutral-700 dark:text-neutral-300" />
          </div>
          <CardTitle className="text-xs font-bold tracking-tight text-neutral-900 font-sans dark:text-neutral-100">
            State Preview
          </CardTitle>
        </div>
        <Badge
          variant="secondary"
          className="text-[10px] font-mono text-neutral-600 bg-neutral-100 border border-neutral-200/60 px-1.5 py-0 shrink-0 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300"
        >
          {items.length} keys
        </Badge>
      </CardHeader>
      <CardContent className="p-0 flex-1 flex flex-col justify-between">
        <div className="max-h-[calc(100vh-240px)] overflow-y-auto divide-y divide-neutral-100 dark:divide-neutral-800">
          {items.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 px-4 text-center">
              <div className="flex h-9 w-9 items-center justify-center rounded-md bg-neutral-100 text-neutral-400 mb-2 border border-neutral-200 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-500">
                <Database className="h-4 w-4" />
              </div>
              <p className="text-xs font-semibold text-neutral-800 dark:text-neutral-100">
                Belum ada run
              </p>
              <p className="text-[11px] text-neutral-500 mt-0.5 dark:text-neutral-400">
                State keys akan muncul saat analisis berjalan atau run dipilih.
              </p>
            </div>
          ) : (
            items.map((item) => {
              const isExpanded = expandedKeys.has(item.key)
              return (
                <div
                  key={item.key}
                  className="px-3 py-2.5 hover:bg-neutral-50/80 transition-colors dark:hover:bg-neutral-900/80"
                >
                  <button
                    type="button"
                    onClick={() => toggleKey(item.key)}
                    className="w-full text-left focus:outline-none"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-1.5 min-w-0">
                        {isExpanded ? (
                          <ChevronDown className="h-3.5 w-3.5 text-neutral-400 shrink-0" />
                        ) : (
                          <ChevronRight className="h-3.5 w-3.5 text-neutral-400 shrink-0" />
                        )}
                        <span className="font-mono text-[11px] font-semibold text-neutral-800 break-all dark:text-neutral-100">
                          {item.key}
                        </span>
                      </div>
                      <div className="shrink-0 font-mono text-[10px] text-neutral-400 dark:text-neutral-500">
                        {item.hasValue ? (
                          <span>{item.typeTag}</span>
                        ) : (
                          <span className="italic text-neutral-400 dark:text-neutral-500">not in event</span>
                        )}
                      </div>
                    </div>

                    {!isExpanded && (
                      <div className="mt-1 pl-5">
                        {!item.hasValue ? (
                          <div className="font-mono text-[11px] text-neutral-400 flex items-center gap-1.5 dark:text-neutral-500">
                            <span>-</span>
                            <span className="text-[10px] text-neutral-400/80 italic dark:text-neutral-500/80">(not in event)</span>
                          </div>
                        ) : (
                          <div className="font-mono text-[11px] text-neutral-600 line-clamp-2 break-words leading-relaxed dark:text-neutral-400">
                            {item.previewSnippet}
                          </div>
                        )}
                      </div>
                    )}
                  </button>

                  {isExpanded && (
                    <div className="mt-2 pl-5">
                      {!item.hasValue ? (
                        <div className="rounded border border-neutral-200 bg-neutral-50 px-2.5 py-2 font-mono text-[11px] text-neutral-500 italic dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-400">
                          - Nilai state belum disertakan dalam event delta ini.
                        </div>
                      ) : (
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-[10px] text-neutral-400 font-mono dark:text-neutral-500">
                            <span>
                              Updated by <strong className="text-neutral-600 font-semibold dark:text-neutral-300">{item.author || "agent"}</strong> (#{item.lastUpdatedSeq})
                            </span>
                            <span>
                              {item.byteSize} bytes{item.isTruncated ? " · truncated at 4000 chars" : ""}
                            </span>
                          </div>
                          <pre className="max-h-60 overflow-auto whitespace-pre-wrap break-words rounded bg-neutral-900 p-2.5 font-mono text-[11px] leading-relaxed text-neutral-100 border border-neutral-800 dark:bg-black">
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
        <div className="border-t border-neutral-100 bg-neutral-50/80 px-3 py-2 text-xs font-medium text-neutral-600 flex items-center justify-between shrink-0 dark:border-neutral-800 dark:bg-neutral-900/80 dark:text-neutral-400">
          <span>{summaryText}</span>
          <span className="text-[11px] text-neutral-400 font-mono dark:text-neutral-500">state footprint</span>
        </div>
      </CardContent>
    </Card>
  )
}
