import { useState } from "react"
import { ChevronDown, ChevronRight, Wrench, Copy, Check } from "lucide-react"

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
  const [copied, setCopied] = useState(false)

  const argsStr = JSON.stringify(fc.args ?? {}, null, 2)
  const byteSize = new TextEncoder().encode(argsStr).length
  const byteText = formatByteSize(byteSize)
  const isTruncated = argsStr.length > 8000
  const displayedArgs = isTruncated ? `${argsStr.slice(0, 8000)}…` : argsStr

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation()
    navigator.clipboard.writeText(argsStr)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="rounded border border-amber-900/60 bg-amber-950/30 text-amber-200 transition-colors font-mono text-xs">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex w-full items-center justify-between px-2 py-1 text-left hover:bg-amber-900/40 rounded focus:outline-none cursor-pointer"
      >
        <div className="flex items-center gap-1.5 min-w-0">
          {isOpen ? (
            <ChevronDown className="h-3 w-3 shrink-0 text-amber-400" />
          ) : (
            <ChevronRight className="h-3 w-3 shrink-0 text-amber-400" />
          )}
          <Wrench className="h-3 w-3 shrink-0 text-amber-400" />
          <span className="font-bold text-amber-300 truncate">{fc.name}()</span>
          <span className="text-amber-500 text-[10px] shrink-0">· {byteText}</span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {fc.id && (
            <span className="text-[9px] text-amber-500/80 truncate font-mono">{fc.id}</span>
          )}
          <span className="text-[9px] text-amber-400/80 bg-amber-950 border border-amber-800 px-1 rounded">
            FCALL
          </span>
        </div>
      </button>

      {isOpen && (
        <div className="border-t border-amber-900/60 p-2 bg-black space-y-1">
          <div className="flex items-center justify-between text-[10px] text-amber-500">
            <span>
              {isTruncated ? `Args truncated (total ${byteText})` : `Full arguments (${byteText})`}
            </span>
            <button
              type="button"
              onClick={handleCopy}
              className="flex items-center gap-1 rounded bg-neutral-900 hover:bg-neutral-800 border border-neutral-700 px-1.5 py-0.5 text-neutral-300 text-[9px]"
              title="Copy arguments JSON"
            >
              {copied ? (
                <>
                  <Check className="h-2.5 w-2.5 text-emerald-400" />
                  <span>COPIED</span>
                </>
              ) : (
                <>
                  <Copy className="h-2.5 w-2.5" />
                  <span>COPY</span>
                </>
              )}
            </button>
          </div>
          <pre className="max-h-60 overflow-auto whitespace-pre-wrap break-words text-[10px] text-amber-100 font-mono leading-relaxed p-1.5 rounded bg-neutral-950 border border-neutral-900">
            {displayedArgs}
          </pre>
        </div>
      )}
    </div>
  )
}
