import { useState } from "react"
import { ChevronDown, ChevronRight, CornerDownLeft, Copy, Check } from "lucide-react"

export interface FunctionResponseProps {
  fr: {
    name: string
    response: unknown
    id?: string
  }
}

function formatByteSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`
  }
  return `${(bytes / 1024).toFixed(1)} kb`
}

export function FunctionResponseCard({ fr }: FunctionResponseProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [copied, setCopied] = useState(false)

  const respStr =
    typeof fr.response === "string"
      ? fr.response
      : JSON.stringify(fr.response, null, 2)

  const byteSize = new TextEncoder().encode(respStr).length
  const byteText = formatByteSize(byteSize)
  const isTruncated = respStr.length > 6000
  const displayedResp = isTruncated ? `${respStr.slice(0, 6000)}…` : respStr

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation()
    navigator.clipboard.writeText(respStr)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="rounded border border-emerald-900/60 bg-emerald-950/30 text-emerald-200 transition-colors font-mono text-xs">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex w-full items-center justify-between px-2 py-1 text-left hover:bg-emerald-900/40 rounded focus:outline-none cursor-pointer"
      >
        <div className="flex items-center gap-1.5 min-w-0">
          {isOpen ? (
            <ChevronDown className="h-3 w-3 shrink-0 text-emerald-400" />
          ) : (
            <ChevronRight className="h-3 w-3 shrink-0 text-emerald-400" />
          )}
          <CornerDownLeft className="h-3 w-3 shrink-0 text-emerald-400" />
          <span className="font-bold text-emerald-300 truncate">{fr.name} - result</span>
          <span className="text-emerald-500 text-[10px] shrink-0">· {byteText}</span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {fr.id && (
            <span className="text-[9px] text-emerald-500/80 truncate font-mono">{fr.id}</span>
          )}
          <span className="text-[9px] text-emerald-400/80 bg-emerald-950 border border-emerald-800 px-1 rounded">
            FRESP
          </span>
        </div>
      </button>

      {isOpen && (
        <div className="border-t border-emerald-900/60 p-2 bg-black space-y-1">
          <div className="flex items-center justify-between text-[10px] text-emerald-500">
            <span>
              {isTruncated ? `Response truncated (total ${byteText})` : `Full response (${byteText})`}
            </span>
            <button
              type="button"
              onClick={handleCopy}
              className="flex items-center gap-1 rounded bg-neutral-900 hover:bg-neutral-800 border border-neutral-700 px-1.5 py-0.5 text-neutral-300 text-[9px]"
              title="Copy response JSON"
            >
              {copied ? (
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
          <pre className="max-h-60 overflow-auto whitespace-pre-wrap break-words text-[10px] text-emerald-100 font-mono leading-relaxed p-1.5 rounded bg-neutral-950 border border-neutral-900">
            {displayedResp}
          </pre>
        </div>
      )}
    </div>
  )
}
