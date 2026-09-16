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
  return `${(bytes / 1024).toFixed(1)} KB`
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
    <div className="rounded-lg border border-[#E7E3DA] dark:border-[#2A2822] bg-[#FBFAF7] dark:bg-[#14130F] text-xs">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex w-full items-center justify-between px-3 py-1.5 text-left hover:bg-[#F5F2EB] dark:hover:bg-[#1B1A16] rounded-lg focus:outline-none cursor-pointer"
      >
        <div className="flex items-center gap-2 min-w-0">
          {isOpen ? (
            <ChevronDown className="h-3.5 w-3.5 shrink-0 text-[#6B6659] dark:text-[#A8A296]" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5 shrink-0 text-[#6B6659] dark:text-[#A8A296]" />
          )}
          <Wrench className="h-3.5 w-3.5 shrink-0 text-amber-600 dark:text-amber-400" />
          <span className="font-medium text-[#1C1B17] dark:text-[#EDEAE3] truncate">
            {fc.name}()
          </span>
          <span className="text-[#6B6659] dark:text-[#A8A296] text-[11px] shrink-0">
            · {byteText}
          </span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-[10px] text-amber-800 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 px-1.5 py-0.5 rounded">
            Parameter fungsi
          </span>
        </div>
      </button>

      {isOpen && (
        <div className="border-t border-[#E7E3DA] dark:border-[#2A2822] p-3 space-y-1.5 bg-white dark:bg-[#1B1A16]">
          <div className="flex items-center justify-between text-[11px] text-[#6B6659] dark:text-[#A8A296]">
            <span>
              {isTruncated ? `Parameter (dipotong, total ${byteText})` : `Parameter lengkap (${byteText})`}
            </span>
            <button
              type="button"
              onClick={handleCopy}
              className="flex items-center gap-1 rounded border border-[#E7E3DA] dark:border-[#2A2822] bg-[#FBFAF7] dark:bg-[#14130F] hover:bg-[#F5F2EB] dark:hover:bg-[#23211C] px-2 py-0.5 text-[#1C1B17] dark:text-[#EDEAE3] text-[10px] transition-colors"
            >
              {copied ? (
                <>
                  <Check className="h-3 w-3 text-emerald-600 dark:text-emerald-400" />
                  <span>Tersalin</span>
                </>
              ) : (
                <>
                  <Copy className="h-3 w-3" />
                  <span>Salin JSON</span>
                </>
              )}
            </button>
          </div>
          <pre className="max-h-60 overflow-auto whitespace-pre-wrap break-words text-[11px] font-mono leading-relaxed p-2.5 rounded-md bg-[#FBFAF7] dark:bg-[#14130F] border border-[#E7E3DA] dark:border-[#2A2822] text-[#1C1B17] dark:text-[#EDEAE3]">
            {displayedArgs}
          </pre>
        </div>
      )}
    </div>
  )
}
