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
  if (n == null || Number.isNaN(Number(n))) return "—"
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
    "inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono font-medium border-b-2 transition-colors whitespace-nowrap cursor-pointer"
  const tabActive =
    "border-amber-500 text-amber-500 bg-amber-500/10 font-bold dark:border-amber-400 dark:text-amber-300 dark:bg-amber-950/40"
  const tabIdle =
    "border-transparent text-neutral-500 hover:text-neutral-900 hover:border-neutral-300 dark:text-neutral-400 dark:hover:text-neutral-200 dark:hover:border-neutral-700"

  // Target subroute for ticker switcher
  const getTickerRoute = (targetTk: string) => {
    if (isSentimentActive) return `/report/${targetTk}/sentiment`
    if (isChallengeActive) return `/report/${targetTk}/challenge`
    return `/report/${targetTk}`
  }

  return (
    <div className="sticky top-12 z-20 -mx-4 -mt-6 mb-6 border-b border-neutral-200 bg-white/95 backdrop-blur shadow-xs dark:border-[#262930] dark:bg-[#0c0d0e]/95">
      {/* 1. Terminal Command Line & Ticker Switcher Strip */}
      <div className="border-b border-neutral-200 bg-neutral-100/90 px-4 py-1.5 text-[11px] font-mono text-neutral-600 dark:border-[#1f2228] dark:bg-[#121316] dark:text-neutral-400">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1 font-bold text-neutral-900 dark:text-amber-400">
              <Terminal className="h-3.5 w-3.5 text-amber-500" />
              <span>TERMINAL</span>
            </span>
            <span className="text-neutral-400 dark:text-neutral-600">::</span>
            <span className="text-neutral-700 dark:text-neutral-300">
              {tk} SAHAM ID
            </span>
          </div>

          {/* Ticker Quick Switcher */}
          <div className="flex items-center gap-1">
            <span className="mr-1 hidden text-[10px] text-neutral-400 sm:inline uppercase">Universe:</span>
            {ENGINE_TICKERS.map((symbol) => {
              const isActive = symbol === tk
              return (
                <Link
                  key={symbol}
                  to={getTickerRoute(symbol)}
                  className={`rounded px-1.5 py-0.5 text-[10px] font-bold font-mono transition-all ${
                    isActive
                      ? "bg-neutral-900 text-white shadow-xs dark:bg-amber-400 dark:text-neutral-950 font-bold"
                      : "bg-neutral-200/80 text-neutral-700 hover:bg-neutral-300 dark:bg-[#1c1f26] dark:text-neutral-400 dark:hover:bg-[#282c37] dark:hover:text-neutral-200"
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
              className="mt-1 inline-flex items-center justify-center rounded border border-neutral-300 bg-neutral-100 p-1 text-neutral-600 hover:bg-neutral-200 dark:border-[#262930] dark:bg-[#181a1f] dark:text-neutral-400 dark:hover:bg-[#22252c] dark:hover:text-neutral-200"
              title="Kembali ke Beranda"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
            </Link>

            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                <span className="rounded bg-neutral-900 px-1.5 py-0.5 font-mono text-xs font-bold text-amber-400 dark:bg-amber-400/10 dark:border dark:border-amber-400/30 dark:text-amber-400">
                  {tk} SAHAM ID
                </span>
                <h1 className="truncate text-base font-bold tracking-tight text-neutral-900 dark:text-neutral-100">
                  {finalName || `${tk} Tbk`}
                </h1>
                <RecommendationBadge rating={rating} size="sm" />
              </div>

              <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-mono">
                {template && (
                  <span className="rounded border border-neutral-300 bg-neutral-100 px-1.5 py-px text-[10px] font-semibold uppercase text-neutral-700 dark:border-[#262930] dark:bg-[#181a1f] dark:text-neutral-300">
                    ARCHETYPE: {template}
                  </span>
                )}
                {updatedAt && (
                  <span className="text-[11px] text-neutral-500 dark:text-neutral-400">
                    AUDITED: {updatedAt} {source ? `(${source})` : ""}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Key Numerals Strip & Actions */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-baseline gap-3 rounded-md border border-neutral-200 bg-neutral-50/80 px-3 py-1.5 font-mono dark:border-[#262930] dark:bg-[#121316]">
              {/* Last Price */}
              <div>
                <div className="text-[10px] uppercase text-neutral-500 dark:text-neutral-400">HARGA TERAKHIR</div>
                <div className="text-sm font-bold text-neutral-900 tabular-nums dark:text-neutral-100">
                  {price != null ? `Rp ${fmtIDR(price)}` : "—"}
                </div>
              </div>

              <div className="h-6 w-px bg-neutral-200 dark:bg-[#262930]" />

              {/* Target Price */}
              <div>
                <div className="text-[10px] uppercase text-neutral-500 dark:text-neutral-400">TARGET (NILAI WAJAR)</div>
                <div className="text-sm font-bold text-neutral-900 tabular-nums dark:text-neutral-100">
                  {finalTarget != null ? `Rp ${fmtIDR(finalTarget)}` : "—"}
                </div>
              </div>

              <div className="h-6 w-px bg-neutral-200 dark:bg-[#262930]" />

              {/* Upside / Downside */}
              <div>
                <div className="text-[10px] uppercase text-neutral-500 dark:text-neutral-400">POTENSI NAIK</div>
                <div
                  className={`text-sm font-bold tabular-nums ${
                    upsidePositive
                      ? "text-emerald-600 dark:text-emerald-400"
                      : upsideNegative
                      ? "text-rose-600 dark:text-rose-400"
                      : "text-neutral-500 dark:text-neutral-400"
                  }`}
                >
                  {upsidePositive ? "▲ " : upsideNegative ? "▼ " : ""}
                  {upside || "—"}
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
                className="h-8 gap-1 border-neutral-300 font-mono text-xs font-semibold text-neutral-800 hover:bg-neutral-100 dark:border-[#262930] dark:bg-[#181a1f] dark:text-neutral-200 dark:hover:bg-[#22252c]"
              >
                {isPdfBusy ? (
                  <Loader2 className="h-3 w-3 animate-spin text-amber-500" />
                ) : (
                  <Download className="h-3 w-3 text-neutral-500 dark:text-neutral-400" />
                )}
                <span>[F12] PDF</span>
              </Button>

              <Link
                to="/agent"
                search={{ ticker: tk } as any}
                className="inline-flex h-8 items-center gap-1 rounded border border-neutral-300 bg-neutral-100 px-2.5 font-mono text-xs font-semibold text-[#0070f3] hover:bg-neutral-200 transition-colors dark:border-[#262930] dark:bg-[#181a1f] dark:text-[#3291ff] dark:hover:bg-[#22252c]"
              >
                <Bot className="h-3 w-3" />
                <span>[F5] TRACE</span>
              </Link>
            </div>
          </div>
        </div>

        {errorMsg && (
          <div className="mt-2 rounded border border-amber-300 bg-amber-50 px-3 py-1 font-mono text-xs text-amber-900 dark:border-amber-800/60 dark:bg-amber-950/60 dark:text-amber-200">
            [NOTICE] {errorMsg}
          </div>
        )}

        {/* 3. Terminal Dense Tab Navigation */}
        <div className="mt-3 flex items-center gap-1 overflow-x-auto border-t border-neutral-200 pt-1 dark:border-[#1f2228]">
          <Link
            to="/report/$ticker"
            params={{ ticker: tk }}
            className={`${tabBase} ${isValuationActive ? tabActive : tabIdle}`}
          >
            <FileText className="h-3.5 w-3.5" />
            <span>[1] VALUATION // MODEL</span>
          </Link>

          <Link
            to="/report/$ticker/sentiment"
            params={{ ticker: tk }}
            className={`${tabBase} ${isSentimentActive ? tabActive : tabIdle}`}
          >
            <MessageSquare className="h-3.5 w-3.5" />
            <span>[2] SENTIMENT // SOCIAL & NEWS</span>
          </Link>

          <Link
            to="/report/$ticker/challenge"
            params={{ ticker: tk }}
            className={`${tabBase} ${isChallengeActive ? tabActive : tabIdle}`}
          >
            <Swords className="h-3.5 w-3.5" />
            <span>[3] RED TEAM // THESIS CHALLENGE</span>
          </Link>

          <div className="ml-auto hidden pr-1 font-mono text-[10px] text-neutral-400 sm:block">
            TERMINAL VER 2.6 // DETERMINISTIC EQUITY ENGINE
          </div>
        </div>
      </div>
    </div>
  )
}

