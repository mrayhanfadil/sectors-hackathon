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
  TrendingUp,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
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

  return (
    <div className="sticky top-[57px] z-20 -mx-4 -mt-6 mb-6 border-b border-slate-200 bg-white/95 backdrop-blur shadow-2xs">
      <div className="mx-auto max-w-6xl px-4 py-3">
        {/* Top bar: Back link + Company Info + Actions */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <Link
                to="/"
                className="inline-flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-slate-900 transition-colors"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                <span>Daftar Saham</span>
              </Link>
              <span className="text-slate-300">/</span>
              <span className="font-mono text-xs font-bold text-slate-900">{tk}</span>

              <RecommendationBadge
                rating={rating}
                targetPrice={finalTarget}
                upside={upside}
                showTarget
                size="sm"
              />

              {price != null && (
                <span className="font-mono text-xs text-slate-700 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded">
                  Px Rp {fmtIDR(price)}
                </span>
              )}

              {template && (
                <Badge variant="secondary" className="text-[10px] uppercase font-mono tracking-wider">
                  {template}
                </Badge>
              )}
            </div>

            <div className="flex flex-wrap items-baseline gap-2">
              <h1 className="text-lg font-bold tracking-tight text-slate-900 sm:text-xl font-mono">
                {tk} {finalName ? `- ${finalName}` : ""}
              </h1>
              {updatedAt && (
                <span className="text-xs text-slate-400 font-mono">
                  Diperbarui: {updatedAt} {source ? `(${source})` : ""}
                </span>
              )}
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePdfDownload}
              disabled={isPdfBusy}
              className="h-8 gap-1.5 text-xs text-slate-700 hover:text-slate-900 cursor-pointer"
            >
              {isPdfBusy ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Download className="h-3.5 w-3.5 text-slate-500" />
              )}
              <span>{isPdfBusy ? "Mengunduh..." : "Unduh PDF"}</span>
            </Button>

            <Link
              to="/agent"
              search={{ ticker: tk } as any}
              className="inline-flex h-8 items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 text-xs font-medium text-slate-700 hover:bg-slate-50 hover:text-slate-900 transition-colors"
            >
              <Bot className="h-3.5 w-3.5 text-slate-500" />
              <span>Trace ADK</span>
            </Link>

          </div>
        </div>

        {errorMsg && (
          <div className="mt-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs text-amber-800">
            {errorMsg}
          </div>
        )}

        {/* Tab Navigation Row */}
        <div className="mt-3 flex items-center gap-1.5 overflow-x-auto border-t border-slate-100 pt-2.5 scrollbar-none">
          <Link
            to="/report/$ticker"
            params={{ ticker: tk }}
            className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
              isValuationActive
                ? "bg-slate-900 text-white shadow-xs"
                : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            }`}
          >
            <FileText className="h-3.5 w-3.5" />
            <span>Valuasi</span>
          </Link>

          <Link
            to="/report/$ticker/sentiment"
            params={{ ticker: tk }}
            className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
              isSentimentActive
                ? "bg-slate-900 text-white shadow-xs"
                : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            }`}
          >
            <MessageSquare className="h-3.5 w-3.5" />
            <span>Sentimen</span>
          </Link>

          <Link
            to="/report/$ticker/challenge"
            params={{ ticker: tk }}
            className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
              isChallengeActive
                ? "bg-slate-900 text-white shadow-xs"
                : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            }`}
          >
            <Swords className="h-3.5 w-3.5" />
            <span>Challenge</span>
          </Link>

          <div className="ml-auto hidden sm:flex items-center gap-2 text-xs text-slate-400">
            <TrendingUp className="h-3.5 w-3.5" />
            <span>Riset Institusional Sectors 2026</span>
          </div>
        </div>
      </div>
    </div>
  )
}
