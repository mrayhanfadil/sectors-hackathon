import { useState } from "react"
import { Link } from "@tanstack/react-router"
import {
  ArrowLeft,
  FileText,
  MessageSquare,
  Swords,
  Download,
  Bot,
  Loader2,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { fetchPdf } from "@/lib/api"
import { RecommendationBadge } from "./RecommendationBadge"

export type ReportHeaderProps = {
  ticker: string
  activeTab?: "overview" | "valuation" | "sentiment" | "challenge"
  name?: string | null
  companyName?: string | null
  rating?: string | null
  price?: number | null
  target?: number | null
  targetPrice?: number | null
  upside?: string | null
  updatedAt?: string | null
  template?: string | null
  source?: string | null
  onDownloadPdf?: () => void
  pdfLoading?: boolean
  pdfState?: "idle" | "loading" | "error"
  pdfMsg?: string | null
}

function fmtIDR(n: number | null | undefined): string {
  if (n == null || Number.isNaN(Number(n))) return "-"
  return Number(n).toLocaleString("id-ID")
}

function parseUpside(upside?: string | null): number | null {
  if (upside == null) return null
  const m = String(upside).replace(",", ".").match(/-?\d+(\.\d+)?/)
  return m ? Number(m[0]) : null
}

export function ReportHeader({
  ticker,
  activeTab = "valuation",
  name,
  companyName,
  rating,
  price,
  target,
  targetPrice,
  upside,
  updatedAt,
  template = "single",
  source,
  onDownloadPdf,
  pdfLoading: externalPdfLoading,
  pdfState: externalPdfState,
  pdfMsg,
}: ReportHeaderProps) {
  const tk = ticker.toUpperCase()
  const [internalPdfLoading, setInternalPdfLoading] = useState(false)
  const [internalPdfError, setInternalPdfError] = useState<string | null>(null)

  const finalName = name || companyName || ""
  const finalTarget = targetPrice != null ? targetPrice : target
  const isPdfBusy = externalPdfLoading ?? (externalPdfState === "loading" || internalPdfLoading)
  const errorMsg = pdfMsg || internalPdfError

  const isValuationActive = activeTab === "valuation" || activeTab === "overview"
  const isSentimentActive = activeTab === "sentiment"
  const isChallengeActive = activeTab === "challenge"

  const upsideNum = parseUpside(upside)
  const upsidePositive = upsideNum != null && upsideNum > 0
  const upsideNegative = upsideNum != null && upsideNum < 0
  const logoInitial = (tk.replace(/[^A-Z]/gi, "").slice(0, 1) || tk.slice(0, 1)).toUpperCase()

  async function handlePdfDownload() {
    if (onDownloadPdf) {
      onDownloadPdf()
      return
    }
    setInternalPdfLoading(true)
    setInternalPdfError(null)
    try {
      await fetchPdf(tk)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      if (msg.includes("404") || msg.includes("not available") || msg.includes("soon")) {
        setInternalPdfError("Dokumen PDF belum tersedia di sistem")
      } else {
        setInternalPdfError(msg)
      }
      setTimeout(() => setInternalPdfError(null), 4000)
    } finally {
      setInternalPdfLoading(false)
    }
  }

  const tabBase =
    "inline-flex items-center gap-1.5 whitespace-nowrap border-b-2 px-0.5 pb-2 pt-1 text-[13px] font-medium transition-colors"
  const tabActive = "border-[#0a0a0a] text-[#0a0a0a] dark:border-white dark:text-white"
  const tabIdle = "border-transparent text-neutral-500 hover:text-[#0a0a0a] dark:text-neutral-400 dark:hover:text-white"

  return (
    <div className="sticky top-[57px] z-20 -mx-4 -mt-6 mb-6 border-b border-neutral-200 bg-white/95 backdrop-blur dark:border-neutral-800 dark:bg-[#0a0a0a]/95">
      <div className="mx-auto max-w-6xl px-4 pt-3">
        {/* Breadcrumb */}
        <Link
          to="/"
          className="inline-flex items-center gap-1 text-xs font-medium text-[#0070f3] hover:underline dark:text-[#3291ff]"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Daftar Saham</span>
        </Link>

        {/* Company identity row: logo chip + price/change + actions */}
        <div className="mt-1.5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex min-w-0 items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-neutral-200 bg-neutral-50 text-sm font-bold tracking-tight text-[#0a0a0a] dark:border-neutral-800 dark:bg-neutral-900 dark:text-white">
              {logoInitial}
            </div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                <h1 className="text-lg font-semibold tracking-tight text-[#0a0a0a] dark:text-white">
                  {finalName ? `${finalName} ` : ""}
                  <span className="font-medium text-neutral-400">({tk})</span>
                </h1>
                <RecommendationBadge rating={rating} size="sm" />
              </div>
              <div className="mt-0.5 flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
                {price != null && (
                  <span className="font-mono text-xl font-semibold tabular-nums tracking-tight text-[#0a0a0a] dark:text-white">
                    Rp {fmtIDR(price)}
                  </span>
                )}
                {upside && (
                  <span
                    className={`font-mono text-xs font-semibold tabular-nums ${
                      upsidePositive
                        ? "text-emerald-600 dark:text-emerald-400"
                        : upsideNegative
                        ? "text-red-600 dark:text-red-400"
                        : "text-neutral-500 dark:text-neutral-400"
                    }`}
                  >
                    {upsidePositive ? "▲ " : upsideNegative ? "▼ " : ""}
                    {upside}
                  </span>
                )}
                {finalTarget != null && (
                  <span className="font-mono text-xs tabular-nums text-neutral-500 dark:text-neutral-400">
                    TP Rp {fmtIDR(finalTarget)}
                  </span>
                )}
                {template && (
                  <span className="rounded border border-neutral-200 bg-white px-1.5 py-px font-mono text-[10px] uppercase tracking-wider text-neutral-500 dark:border-neutral-800 dark:bg-[#111111] dark:text-neutral-400">
                    {template}
                  </span>
                )}
              </div>
              {updatedAt && (
                <p className="mt-0.5 font-mono text-[11px] text-neutral-400">
                  Diperbarui: {updatedAt} {source ? `(${source})` : ""}
                </p>
              )}
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex shrink-0 flex-wrap items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePdfDownload}
              disabled={isPdfBusy}
              className="h-8 gap-1.5 border-neutral-200 text-xs text-neutral-700 hover:text-[#0a0a0a] cursor-pointer dark:border-neutral-800 dark:text-neutral-300 dark:hover:text-white"
            >
              {isPdfBusy ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Download className="h-3.5 w-3.5 text-neutral-500 dark:text-neutral-400" />
              )}
              <span>{isPdfBusy ? "Mengunduh..." : "Unduh PDF"}</span>
            </Button>

            <Link
              to="/agent"
              search={{ ticker: tk } as any}
              className="inline-flex h-8 items-center gap-1.5 rounded-md border border-neutral-200 bg-white px-3 text-xs font-medium text-[#0070f3] hover:bg-neutral-50 transition-colors dark:border-neutral-800 dark:bg-[#111111] dark:text-[#3291ff] dark:hover:bg-neutral-900"
            >
              <Bot className="h-3.5 w-3.5" />
              <span>Trace ADK</span>
            </Link>
          </div>
        </div>

        {errorMsg && (
          <div className="mt-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs text-amber-800 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200">
            {errorMsg}
          </div>
        )}

        {/* Dense underline tab navigation */}
        <div className="mt-3 flex items-center gap-5 overflow-x-auto">
          <Link
            to="/report/$ticker"
            params={{ ticker: tk }}
            className={`${tabBase} ${isValuationActive ? tabActive : tabIdle}`}
          >
            <FileText className="h-3.5 w-3.5" />
            <span>Valuasi</span>
          </Link>

          <Link
            to="/report/$ticker/sentiment"
            params={{ ticker: tk }}
            className={`${tabBase} ${isSentimentActive ? tabActive : tabIdle}`}
          >
            <MessageSquare className="h-3.5 w-3.5" />
            <span>Sentimen</span>
          </Link>

          <Link
            to="/report/$ticker/challenge"
            params={{ ticker: tk }}
            className={`${tabBase} ${isChallengeActive ? tabActive : tabIdle}`}
          >
            <Swords className="h-3.5 w-3.5" />
            <span>Challenge</span>
          </Link>

          <div className="ml-auto hidden pb-2 sm:block text-xs text-neutral-400">
            <span>Riset Institusional Sectors 2026</span>
          </div>
        </div>
      </div>
    </div>
  )
}
