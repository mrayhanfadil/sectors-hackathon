import { useState } from "react"
import { ChevronDown, ChevronRight, CornerDownLeft } from "lucide-react"

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

  const respStr =
    typeof fr.response === "string"
      ? fr.response
      : JSON.stringify(fr.response, null, 2)

  const byteSize = new TextEncoder().encode(respStr).length
  const byteText = formatByteSize(byteSize)
  const isTruncated = respStr.length > 6000
  const displayedResp = isTruncated ? `${respStr.slice(0, 6000)}…` : respStr

  return (
    <div className="rounded border border-emerald-200 bg-emerald-50 text-emerald-900 transition-colors">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex w-full items-center justify-between px-2.5 py-1.5 text-left font-mono text-[11px] hover:bg-emerald-100/60 rounded focus:outline-none"
      >
        <div className="flex items-center gap-1.5 min-w-0">
          {isOpen ? (
            <ChevronDown className="h-3 w-3 shrink-0 text-emerald-700" />
          ) : (
            <ChevronRight className="h-3 w-3 shrink-0 text-emerald-700" />
          )}
          <CornerDownLeft className="h-3 w-3 shrink-0 text-emerald-700" />
          <span className="font-semibold truncate">{fr.name}</span>
          <span className="text-emerald-700/70 font-normal shrink-0">· {byteText}</span>
        </div>
        {fr.id ? (
          <span className="text-[10px] text-emerald-700/60 truncate ml-2 font-mono">{fr.id}</span>
        ) : null}
      </button>
      {isOpen && (
        <div className="border-t border-emerald-200/60 px-2.5 py-2">
          {isTruncated && (
            <div className="mb-1 text-[10px] text-emerald-800/70 font-mono">
              (Response truncated at 6000 chars · total {byteText})
            </div>
          )}
          <pre className="max-h-60 overflow-auto whitespace-pre-wrap break-words text-[11px] text-emerald-950/90 font-mono leading-relaxed">
            {displayedResp}
          </pre>
        </div>
      )}
    </div>
  )
}
