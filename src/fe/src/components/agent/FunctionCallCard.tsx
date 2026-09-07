import { useState } from "react"
import { ChevronDown, ChevronRight, Wrench } from "lucide-react"

export interface FunctionCallProps {
  fc: {
    name: string
    args: Record<string, unknown>
    id?: string
  }
}

function formatByteSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`
  }
  return `${(bytes / 1024).toFixed(1)} kb`
}

export function FunctionCallCard({ fc }: FunctionCallProps) {
  const [isOpen, setIsOpen] = useState(false)

  const argsStr = JSON.stringify(fc.args ?? {}, null, 2)
  const byteSize = new TextEncoder().encode(argsStr).length
  const byteText = formatByteSize(byteSize)
  const isTruncated = argsStr.length > 8000
  const displayedArgs = isTruncated ? `${argsStr.slice(0, 8000)}…` : argsStr

  return (
    <div className="rounded border border-amber-200 bg-amber-50 text-amber-900 transition-colors dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex w-full items-center justify-between px-2.5 py-1.5 text-left font-mono text-[11px] hover:bg-amber-100/60 rounded focus:outline-none dark:hover:bg-amber-900/40"
      >
        <div className="flex items-center gap-1.5 min-w-0">
          {isOpen ? (
            <ChevronDown className="h-3 w-3 shrink-0 text-amber-700 dark:text-amber-400" />
          ) : (
            <ChevronRight className="h-3 w-3 shrink-0 text-amber-700 dark:text-amber-400" />
          )}
          <Wrench className="h-3 w-3 shrink-0 text-amber-700 dark:text-amber-400" />
          <span className="font-semibold truncate">{fc.name}</span>
          <span className="text-amber-700/70 font-normal shrink-0 dark:text-amber-400/70">· {byteText}</span>
        </div>
        {fc.id ? (
          <span className="text-[10px] text-amber-700/60 truncate ml-2 font-mono dark:text-amber-400/60">{fc.id}</span>
        ) : null}
      </button>
      {isOpen && (
        <div className="border-t border-amber-200/60 px-2.5 py-2 dark:border-amber-800/60">
          {isTruncated && (
            <div className="mb-1 text-[10px] text-amber-800/70 font-mono dark:text-amber-300/70">
              (Args truncated at 8000 chars · total {byteText})
            </div>
          )}
          <pre className="max-h-60 overflow-auto whitespace-pre-wrap break-words text-[11px] text-amber-950/90 font-mono leading-relaxed dark:text-amber-100/90">
            {displayedArgs}
          </pre>
        </div>
      )}
    </div>
  )
}
