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
  Terminal,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { fetchPdf } from "@/lib/api"
import { RecommendationBadge } from "./RecommendationBadge"
import { ENGINE_TICKERS } from "@/components/agent/tickers"

export type ReportHeaderProps = {
  ticker: string
  activeTab?: "overview" | "valuation" | "sentiment" | "challenge"
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
  const isSentimentActive = activeTab === "sentiment"
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
    "inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-sans font-medium border-b-2 transition-colors whitespace-nowrap cursor-pointer"
  const tabActive =
    "border-[#0B1F3A] text-[#0B1F3A] bg-[#E4EEF7] font-bold dark:border-[#A9C9E8] dark:text-[#A9C9E8] dark:bg-[#0B1F3A]/40"
  const tabIdle =
    "border-transparent text-neutral-500 hover:text-neutral-900 hover:border-neutral-300 dark:text-neutral-400 dark:hover:text-neutral-200 dark:hover:border-neutral-700"

  // Target subroute for ticker switcher
  const getTickerRoute = (targetTk: string) => {
    if (isSentimentActive) return `/report/${targetTk}/sentiment`
    if (isChallengeActive) return `/report/${targetTk}/challenge`
    return `/report/${targetTk}`
  }

  return (
    <div className="sticky top-12 z-20 -mx-4 -mt-6 mb-6 border-b border-[#D6E2EE] bg-white/95 backdrop-blur shadow-xs dark:border-[#262930] dark:bg-[#0c0d0e]/95">
      {/* 1. Terminal Command Line & Ticker Switcher Strip */}
      <div className="border-b border-[#D6E2EE] bg-[#F4F8FC] px-4 py-1.5 text-[11px] font-mono text-neutral-600 dark:border-[#1f2228] dark:bg-[#121316] dark:text-neutral-400">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1 font-bold text-[#0B1F3A] dark:text-[#A9C9E8]">
              <Terminal className="h-3.5 w-3.5 text-[#0B1F3A] dark:text-[#A9C9E8]" />
              <span>TERMINAL</span>
            </span>
            <span className="text-[#63748A]">::</span>
            <span className="text-[#0B1F3A] font-semibold dark:text-neutral-300">
              {tk} SAHAM ID · INSTITUTIONAL REPORT
            </span>
          </div>

          {/* Ticker Quick Switcher */}
          <div className="flex items-center gap-1">
            <span className="mr-1 hidden text-[10px] text-[#63748A] sm:inline uppercase">Universe:</span>
            {ENGINE_TICKERS.map((symbol) => {
              const isActive = symbol === tk
              return (
                <Link
                  key={symbol}
                  to={getTickerRoute(symbol)}
                  className={`rounded px-1.5 py-0.5 text-[10px] font-bold font-mono transition-all ${
                    isActive
                      ? "bg-[#0B1F3A] text-white shadow-xs dark:bg-[#A9C9E8] dark:text-[#0B1F3A] font-bold"
                      : "bg-[#E4EEF7] text-[#0B1F3A] hover:bg-[#D6E2EE] dark:bg-[#1c1f26] dark:text-neutral-400 dark:hover:bg-[#282c37] dark:hover:text-neutral-200"
                  }`}
                >
                  {symbol}
                </Link>
              )
            })}
          </div>
        </div>
      </div>

      {/* 2. Main Terminal Key-Stats Strip */}
      <div className="mx-auto max-w-6xl px-4 pt-3 pb-2">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          {/* Identity & Metadata */}
          <div className="flex min-w-0 items-start gap-3">
            <Link
              to="/"
              className="mt-1 inline-flex items-center justify-center rounded-md border border-[#D6E2EE] bg-[#F4F8FC] p-1.5 text-neutral-600 hover:bg-[#E4EEF7] transition-colors dark:border-[#262930] dark:bg-[#181a1f] dark:text-neutral-400 dark:hover:bg-[#22252c] dark:hover:text-neutral-200"
              title="Kembali ke Beranda"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
            </Link>

            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                <span className="rounded bg-[#0B1F3A] px-1.5 py-0.5 font-mono text-xs font-bold text-[#E4EEF7] dark:bg-[#0B1F3A] dark:border dark:border-[#A9C9E8]/30 dark:text-[#A9C9E8]">
                  {tk}
                </span>
                <h1 className="truncate text-base font-bold tracking-tight text-[#0B1F3A] dark:text-neutral-100 font-sans">
                  {finalName || `${tk} Tbk`}
                </h1>
                <RecommendationBadge rating={rating} size="sm" />
              </div>

              <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-mono">
                {template && (
                  <span className="rounded border border-[#D6E2EE] bg-[#E4EEF7] px-1.5 py-px text-[10px] font-semibold uppercase text-[#0B1F3A] dark:border-[#262930] dark:bg-[#181a1f] dark:text-[#A9C9E8]">
                    ARKETIPE: {template}
                  </span>
                )}
                {updatedAt && (
                  <span className="text-[11px] text-[#63748A]">
                    DIAUDIT: {updatedAt} {source ? `(${source})` : ""}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Key Numerals Strip & Actions */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-baseline gap-3 rounded-lg border border-[#D6E2EE] bg-[#F4F8FC] px-3 py-1.5 font-mono dark:border-[#262930] dark:bg-[#121316]">
              {/* Last Price */}
              <div>
                <div className="text-[10px] uppercase text-[#63748A] font-sans font-medium">HARGA PASAR</div>
                <div className="text-sm font-bold text-[#0B1F3A] tabular-nums dark:text-neutral-100">
                  {price != null ? `Rp ${fmtIDR(price)}` : "-"}
                </div>
              </div>

              <div className="h-6 w-px bg-[#D6E2EE] dark:bg-[#262930]" />

              {/* Target Price */}
              <div>
                <div className="text-[10px] uppercase text-[#63748A] font-sans font-medium">NILAI WAJAR (TP)</div>
                <div className="text-sm font-bold text-[#0B1F3A] tabular-nums dark:text-neutral-100">
                  {finalTarget != null ? `Rp ${fmtIDR(finalTarget)}` : "-"}
                </div>
              </div>

              <div className="h-6 w-px bg-[#D6E2EE] dark:bg-[#262930]" />

              {/* Upside / Downside */}
              <div>
                <div className="text-[10px] uppercase text-[#63748A] font-sans font-medium">POTENSI RETURN</div>
                <div
                  className={`text-sm font-bold tabular-nums ${
                    upsidePositive
                      ? "text-[#1E8F5F]"
                      : upsideNegative
                      ? "text-[#C0392B]"
                      : "text-[#63748A]"
                  }`}
                >
                  {upsidePositive ? "▲ " : upsideNegative ? "▼ " : ""}
                  {upsideDisplay}
                </div>
              </div>
            </div>

            {/* Quick Action Buttons */}
            <div className="flex items-center gap-1.5">
              <Button
                variant="outline"
                size="sm"
                onClick={handlePdfDownload}
                disabled={isPdfBusy}
                className="h-8 gap-1.5 rounded-md border-[#D6E2EE] bg-white font-sans text-xs font-semibold text-[#0B1F3A] hover:bg-[#E4EEF7] dark:border-[#262930] dark:bg-[#181a1f] dark:text-neutral-200 dark:hover:bg-[#22252c]"
              >
                {isPdfBusy ? (
                  <Loader2 className="h-3 w-3 animate-spin text-[#0B1F3A] dark:text-[#A9C9E8]" />
                ) : (
                  <Download className="h-3 w-3 text-[#0B1F3A] dark:text-[#A9C9E8]" />
                )}
                <span>[F12] Unduh PDF</span>
              </Button>

              <Link
                to="/agent"
                search={{ ticker: tk } as any}
                className="inline-flex h-8 items-center gap-1.5 rounded-md border border-[#D6E2EE] bg-[#F4F8FC] px-2.5 font-sans text-xs font-semibold text-[#0B1F3A] hover:bg-[#E4EEF7] transition-colors dark:border-[#262930] dark:bg-[#181a1f] dark:text-[#A9C9E8] dark:hover:bg-[#22252c]"
              >
                <Bot className="h-3 w-3" />
                <span>Proses analisis</span>
              </Link>
            </div>
          </div>
        </div>

        {errorMsg && (
          <div className="mt-2 rounded-md border border-[#C0392B]/40 bg-[#C0392B]/10 px-3 py-1 font-mono text-xs text-[#C0392B] dark:border-[#C0392B]/60 dark:bg-[#C0392B]/20">
            [PERINGATAN] {errorMsg}
          </div>
        )}

        {/* 3. Dense Tab Navigation */}
        <div className="mt-3 flex items-center gap-1 overflow-x-auto border-t border-[#D6E2EE] pt-1 dark:border-[#1f2228]">
          <Link
            to="/report/$ticker"
            params={{ ticker: tk }}
            className={`${tabBase} ${isValuationActive ? tabActive : tabIdle}`}
          >
            <FileText className="h-3.5 w-3.5" />
            <span>[1] Laporan Institusional Lengkap</span>
          </Link>

          <Link
            to="/report/$ticker/sentiment"
            params={{ ticker: tk }}
            className={`${tabBase} ${isSentimentActive ? tabActive : tabIdle}`}
          >
            <MessageSquare className="h-3.5 w-3.5" />
            <span>[2] Sentimen Pasar &amp; Berita</span>
          </Link>

          <Link
            to="/report/$ticker/challenge"
            params={{ ticker: tk }}
            className={`${tabBase} ${isChallengeActive ? tabActive : tabIdle}`}
          >
            <Swords className="h-3.5 w-3.5" />
            <span>[3] Uji Tesis (Red Team)</span>
          </Link>

          <div className="ml-auto hidden pr-1 font-mono text-[10px] text-[#63748A] sm:block">
            TERMINAL INSTITUSIONAL // 10 BAB STANDAR PDF
          </div>
        </div>
      </div>
    </div>
  )
}
