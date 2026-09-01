import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Database, ChevronDown, ChevronRight } from "lucide-react"
import { useStatePreview, type TraceEvent } from "./useStatePreview"

export interface StatePreviewProps {
  events: TraceEvent[]
}

export function StatePreview({ events }: StatePreviewProps) {
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
    <Card className="overflow-hidden flex flex-col h-full">
      <CardHeader className="py-3 flex flex-row items-center justify-between space-y-0">
        <div className="flex items-center gap-1.5">
          <Database className="h-4 w-4 text-slate-600 shrink-0" />
          <CardTitle className="text-sm">State Preview</CardTitle>
        </div>
        <Badge variant="secondary" className="text-[11px] font-mono shrink-0">
          {items.length} keys
        </Badge>
      </CardHeader>
      <CardContent className="p-0 flex-1 flex flex-col justify-between">
        <div className="max-h-[68vh] overflow-auto divide-y divide-slate-100">
          {items.length === 0 ? (
            <div className="px-4 py-10 text-center text-xs text-slate-500">
              Belum ada state delta. State keys akan muncul saat agent berjalan.
            </div>
          ) : (
            items.map((item) => {
              const isExpanded = expandedKeys.has(item.key)
              return (
                <div
                  key={item.key}
                  className="px-3 py-2.5 hover:bg-slate-50 transition-colors"
                >
                  <button
                    type="button"
                    onClick={() => toggleKey(item.key)}
                    className="w-full text-left focus:outline-none"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-1.5 min-w-0">
                        {isExpanded ? (
                          <ChevronDown className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                        ) : (
                          <ChevronRight className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                        )}
                        <span className="font-mono text-[11px] font-semibold text-slate-800 break-all">
                          {item.key}
                        </span>
                      </div>
                      <div className="shrink-0 font-mono text-[10px] text-slate-400">
                        {item.hasValue ? (
                          <span>{item.typeTag}</span>
                        ) : (
                          <span className="italic text-slate-400">not in event</span>
                        )}
                      </div>
                    </div>

                    {!isExpanded && (
                      <div className="mt-1 pl-5">
                        {!item.hasValue ? (
                          <div className="font-mono text-[11px] text-slate-400 flex items-center gap-1.5">
                            <span>—</span>
                            <span className="text-[10px] text-slate-400/80 italic">(not in event)</span>
                          </div>
                        ) : (
                          <div className="font-mono text-[11px] text-slate-600 line-clamp-2 break-words leading-relaxed">
                            {item.previewSnippet}
                          </div>
                        )}
                      </div>
                    )}
                  </button>

                  {isExpanded && (
                    <div className="mt-2 pl-5">
                      {!item.hasValue ? (
                        <div className="rounded border border-slate-200 bg-slate-50 px-2.5 py-2 font-mono text-[11px] text-slate-500 italic">
                          — Nilai state belum disertakan dalam event delta ini.
                        </div>
                      ) : (
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
                            <span>
                              Updated by <strong className="text-slate-600 font-semibold">{item.author || "agent"}</strong> (#{item.lastUpdatedSeq})
                            </span>
                            <span>
                              {item.byteSize} bytes{item.isTruncated ? " · truncated at 4000 chars" : ""}
                            </span>
                          </div>
                          <pre className="max-h-60 overflow-auto whitespace-pre-wrap break-words rounded bg-slate-900 p-2.5 font-mono text-[11px] leading-relaxed text-slate-100 border border-slate-800">
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
        <div className="border-t bg-slate-50/80 px-3 py-2 text-xs font-medium text-slate-600 flex items-center justify-between shrink-0">
          <span>{summaryText}</span>
          <span className="text-[11px] text-slate-400 font-mono">state footprint</span>
        </div>
      </CardContent>
    </Card>
  )
}
