import { useState } from "react"
import { Link } from "@tanstack/react-router"
import {
  ArrowLeft,
  FileText,
  Swords,
  Download,
  Bot,
  Loader2,
  ChevronRight,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { fetchPdf } from "@/lib/api"
import { RecommendationBadge } from "./RecommendationBadge"
import { ENGINE_TICKERS } from "@/components/agent/tickers"

export type ReportHeaderProps = {
  ticker: string
  activeTab?: "overview" | "valuation" | "challenge"
  name?: string | null
  companyName?: string | null
  rating?: string | null
  price?: number | null
  target?: number | null
  targetPrice?: number | null
  upside?: string | number | null
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

function parseUpside(upside?: string | number | null): number | null {
  if (upside == null) return null
  if (typeof upside === "number") return upside
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
  const isChallengeActive = activeTab === "challenge"

  const upsideNum = parseUpside(upside)
  const upsidePositive = upsideNum != null && upsideNum > 0
  const upsideNegative = upsideNum != null && upsideNum < 0

  const upsideDisplay = (() => {
    if (upside == null) return "-"
    if (typeof upside === "number") {
      return `${upside > 0 ? "+" : ""}${upside.toFixed(1)}%`
    }
    return String(upside)
  })()

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
    "inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer"
  const tabActive =
    "border-[#0E6E63] text-[#0E6E63] font-semibold bg-[#0E6E63]/5 dark:border-[#4FD1B5] dark:text-[#4FD1B5] dark:bg-[#4FD1B5]/10"
  const tabIdle =
    "border-transparent text-[#6B6659] hover:text-[#1C1B17] hover:border-[#E7E3DA] dark:text-[#A8A296] dark:hover:text-[#EDEAE3] dark:hover:border-[#2A2822]"

  const getTickerRoute = (targetTk: string) => {
    if (isChallengeActive) return `/report/${targetTk}/challenge`
    return `/report/${targetTk}`
  }

  return (
    <div className="sticky top-0 z-20 -mx-4 -mt-6 mb-8 border-b border-[#E7E3DA] bg-[#FBFAF7]/95 backdrop-blur-sm dark:border-[#2A2822] dark:bg-[#14130F]/95">
      {/* 1. Sub-nav strip & Ticker Switcher */}
      <div className="border-b border-[#E7E3DA] bg-white/60 px-4 py-2 text-xs text-[#6B6659] dark:border-[#2A2822] dark:bg-[#1B1A16]/60 dark:text-[#A8A296]">
        <div className="mx-auto flex max-w-[1100px] flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Link to="/" className="inline-flex items-center mr-1 hover:opacity-85 transition-opacity" title="Sectoral">
              <img src="/sectoral-logo.svg" alt="Sectoral" className="h-4 w-auto" />
            </Link>
            <Link
              to="/"
              className="inline-flex items-center gap-1 font-medium text-[#0928B1] hover:underline dark:text-[#7596FF]"
            >
              Beranda
            </Link>
            <ChevronRight className="h-3 w-3 text-[#6B6659] dark:text-[#A8A296]" />
            <span className="font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
              Laporan {tk}
            </span>
          </div>

          {/* Emiten Switcher */}
          <div className="flex items-center gap-1.5">
            <span className="mr-1 hidden text-xs text-[#6B6659] sm:inline dark:text-[#A8A296]">
              Pilih emiten:
            </span>
            {ENGINE_TICKERS.map((symbol) => {
              const isActive = symbol === tk
              return (
                <Link
                  key={symbol}
                  to={getTickerRoute(symbol)}
                  className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                    isActive
                      ? "bg-[#0E6E63] text-white dark:bg-[#4FD1B5] dark:text-[#14130F] font-semibold"
                      : "bg-[#F4F1EA] text-[#1C1B17] hover:bg-[#E7E3DA] dark:bg-[#2A2822] dark:text-[#EDEAE3] dark:hover:bg-[#38352E]"
                  }`}
                >
                  {symbol}
                </Link>
              )
            })}
          </div>
        </div>
      </div>

      {/* 2. Main Header Key-Stats Strip */}
      <div className="mx-auto max-w-[1100px] px-4 pt-4 pb-3">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          {/* Company Identity */}
          <div className="flex min-w-0 items-start gap-3.5">
            <Link
              to="/"
              className="mt-1 inline-flex items-center justify-center rounded-lg border border-[#E7E3DA] bg-white p-2 text-[#6B6659] hover:bg-[#F4F1EA] hover:text-[#1C1B17] transition-colors dark:border-[#2A2822] dark:bg-[#1B1A16] dark:text-[#A8A296] dark:hover:bg-[#25231E] dark:hover:text-[#EDEAE3]"
              title="Kembali ke beranda"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>

            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2.5">
                <span className="rounded-md bg-[#0E6E63]/10 px-2 py-0.5 text-xs font-bold text-[#0E6E63] dark:bg-[#4FD1B5]/20 dark:text-[#4FD1B5]">
                  {tk}
                </span>
                <h1 className="truncate font-serif text-xl sm:text-2xl font-normal tracking-tight text-[#1C1B17] dark:text-[#EDEAE3]">
                  {finalName || `${tk} Tbk.`}
                </h1>
                <RecommendationBadge rating={rating} size="md" />
              </div>

              <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[#6B6659] dark:text-[#A8A296]">
                {template && (
                  <span className="rounded bg-[#F4F1EA] px-2 py-0.5 text-[11px] font-medium text-[#1C1B17] dark:bg-[#2A2822] dark:text-[#EDEAE3]">
                    Arketipe: {template}
                  </span>
                )}
                {updatedAt && (
                  <span>
                    Diperbarui {updatedAt} {source ? `(${source})` : ""}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Key Numbers & Actions */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-4 rounded-xl border border-[#E7E3DA] bg-white px-4 py-2.5 dark:border-[#2A2822] dark:bg-[#1B1A16]">
              <div>
                <div className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">Harga pasar</div>
                <div className="text-sm font-semibold text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
                  {price != null ? `Rp ${fmtIDR(price)}` : "-"}
                </div>
              </div>

              <div className="h-7 w-px bg-[#E7E3DA] dark:bg-[#2A2822]" />

              <div>
                <div className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">Nilai wajar</div>
                <div className="text-sm font-semibold text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
                  {finalTarget != null ? `Rp ${fmtIDR(finalTarget)}` : "-"}
                </div>
              </div>

              <div className="h-7 w-px bg-[#E7E3DA] dark:bg-[#2A2822]" />

              <div>
                <div className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">Potensi return</div>
                <div
                  className={`text-sm font-semibold font-mono tabular-nums ${
                    upsidePositive
                      ? "text-[#157F3D] dark:text-[#34D399]"
                      : upsideNegative
                      ? "text-[#B4232A] dark:text-[#F87171]"
                      : "text-[#6B6659] dark:text-[#A8A296]"
                  }`}
                >
                  {upsidePositive ? "▲ " : upsideNegative ? "▼ " : ""}
                  {upsideDisplay}
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handlePdfDownload}
                disabled={isPdfBusy}
                className="h-9 gap-1.5 rounded-lg border-[#E7E3DA] bg-white px-3.5 text-xs font-medium text-[#1C1B17] hover:bg-[#F4F1EA] dark:border-[#2A2822] dark:bg-[#1B1A16] dark:text-[#EDEAE3] dark:hover:bg-[#25231E] cursor-pointer"
              >
                {isPdfBusy ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-[#0E6E63] dark:text-[#4FD1B5]" />
                ) : (
                  <Download className="h-3.5 w-3.5 text-[#0E6E63] dark:text-[#4FD1B5]" />
                )}
                <span>Unduh PDF</span>
              </Button>

              <Link
                to="/agent"
                search={{ ticker: tk } as any}
                className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-[#0E6E63] px-3.5 text-xs font-medium text-white hover:bg-[#0B5B52] transition-colors dark:bg-[#4FD1B5] dark:text-[#14130F] dark:hover:bg-[#3EBAA0]"
              >
                <Bot className="h-3.5 w-3.5" />
                <span>Proses analisis</span>
              </Link>
            </div>
          </div>
        </div>

        {errorMsg && (
          <div className="mt-3 rounded-lg border border-[#F8C8CB] bg-[#FDF2F2] px-3.5 py-2 text-xs text-[#B4232A] dark:border-[#B4232A]/40 dark:bg-[#B4232A]/20 dark:text-[#F87171]">
            {errorMsg}
          </div>
        )}

        {/* 3. Editorial Tabs (Laporan & Uji silang) */}
        <div className="mt-4 flex items-center gap-1 overflow-x-auto border-t border-[#E7E3DA] pt-1 dark:border-[#2A2822]">
          <Link
            to="/report/$ticker"
            params={{ ticker: tk }}
            className={`${tabBase} ${isValuationActive ? tabActive : tabIdle}`}
          >
            <FileText className="h-4 w-4" />
            <span>Laporan lengkap</span>
          </Link>

          <Link
            to="/report/$ticker/challenge"
            params={{ ticker: tk }}
            className={`${tabBase} ${isChallengeActive ? tabActive : tabIdle}`}
          >
            <Swords className="h-4 w-4" />
            <span>Uji silang tesis</span>
          </Link>
        </div>
      </div>
    </div>
  )
}
