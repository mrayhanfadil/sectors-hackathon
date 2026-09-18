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
  return `${(bytes / 1024).toFixed(1)} KB`
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
    <div className="rounded-lg border border-[#D9D9D9] dark:border-[#262930] bg-[#f1f5f9] dark:bg-[#1e2229] text-xs">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex w-full items-center justify-between px-3 py-1.5 text-left hover:bg-[#B4C7FF] dark:hover:bg-[#090a0c] rounded-lg focus:outline-none cursor-pointer"
      >
        <div className="flex items-center gap-2 min-w-0">
          {isOpen ? (
            <ChevronDown className="h-3.5 w-3.5 shrink-0 text-[#666666] dark:text-[#666666]" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5 shrink-0 text-[#666666] dark:text-[#666666]" />
          )}
          <CornerDownLeft className="h-3.5 w-3.5 shrink-0 text-emerald-600 dark:text-emerald-400" />
          <span className="font-medium text-[#333333] dark:text-[#f1f5f9] truncate">
            {fr.name} - hasil
          </span>
          <span className="text-[#666666] dark:text-[#666666] text-[11px] shrink-0">
            · {byteText}
          </span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-[10px] text-emerald-800 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 px-1.5 py-0.5 rounded">
            Hasil fungsi
          </span>
        </div>
      </button>

      {isOpen && (
        <div className="border-t border-[#D9D9D9] dark:border-[#262930] p-3 space-y-1.5 bg-white dark:bg-[#090a0c]">
          <div className="flex items-center justify-between text-[11px] text-[#666666] dark:text-[#666666]">
            <span>
              {isTruncated ? `Hasil kembalian (dipotong, total ${byteText})` : `Hasil lengkap (${byteText})`}
            </span>
            <button
              type="button"
              onClick={handleCopy}
              className="flex items-center gap-1 rounded border border-[#D9D9D9] dark:border-[#262930] bg-[#f1f5f9] dark:bg-[#1e2229] hover:bg-[#B4C7FF] dark:hover:bg-[#1e2229] px-2 py-0.5 text-[#333333] dark:text-[#f1f5f9] text-[10px] transition-colors"
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
          <pre className="max-h-60 overflow-auto whitespace-pre-wrap break-words text-[11px] font-mono leading-relaxed p-2.5 rounded-md bg-[#f1f5f9] dark:bg-[#1e2229] border border-[#D9D9D9] dark:border-[#262930] text-[#333333] dark:text-[#f1f5f9]">
            {displayedResp}
          </pre>
        </div>
      )}
    </div>
  )
}
