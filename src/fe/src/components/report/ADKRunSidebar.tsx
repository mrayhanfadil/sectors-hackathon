import { Link } from "@tanstack/react-router"
import { Loader2, ChevronRight, Info, Compass } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AdkRunCard, type Log, type HistoryItem } from "./AdkRunCard"
import { RecommendationBadge } from "./RecommendationBadge"

export interface ADKRunSidebarProps {
  ticker: string
  name?: string
  price?: number | null
  target?: number | null
  upside?: string | null
  rating?: string | null
  template?: string
  shares?: {
    outstanding: number
    unit: string
    free_float_pct?: number
  }
  provenance?: string
  logLoading?: boolean
  logData?: {
    has_run: boolean
    log: Log
    history: HistoryItem[]
  } | null
}

function fmtIDR(n: number | null | undefined): string {
  if (n == null || Number.isNaN(Number(n))) return "—"
  return Number(n).toLocaleString("id-ID")
}

export function ADKRunSidebar({
  ticker,
  name: _name,
  price,
  target,
  upside,
  rating,
  template = "single",
  shares,
  provenance,
  logLoading = false,
  logData,
}: ADKRunSidebarProps) {
  const tk = ticker.toUpperCase()

  return (
    <aside className="w-full shrink-0 space-y-3.5 font-mono lg:w-[320px]">
      {/* 1. ADK Run Card */}
      {logLoading ? (
        <Card className="rounded-lg border border-neutral-200 bg-white p-4 shadow-xs dark:border-[#262930] dark:bg-[#121418]">
          <div className="flex items-center gap-2 text-xs text-neutral-500 dark:text-neutral-400 font-sans">
            <Loader2 className="h-3.5 w-3.5 animate-spin text-amber-500" />
            <span>Menghubungkan ke stream eksekusi mesin ADK...</span>
          </div>
        </Card>
      ) : logData ? (
        <AdkRunCard
          ticker={tk}
          log={logData.log}
          history={logData.history ?? []}
          hasRun={logData.has_run}
        />
      ) : (
        <AdkRunCard
          ticker={tk}
          log={null}
          history={[]}
          hasRun={false}
        />
      )}

      {/* 2. Compact Valuation & Target Summary Card */}
      <Card className="rounded-lg border border-neutral-200 bg-white shadow-xs dark:border-[#262930] dark:bg-[#121418]">
        <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3.5 pb-2.5 dark:border-[#1f2228] dark:bg-[#181a1f]/70">
          <div className="flex items-center justify-between">
            <CardTitle className="text-[11px] font-sans font-bold uppercase tracking-wider text-neutral-600 dark:text-neutral-400">
              Ringkasan Valuasi
            </CardTitle>
            <Badge variant="outline" className="border-neutral-300 text-[9px] uppercase dark:border-[#262930]">
              {template}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3 p-3.5 pt-3">
          {/* Main Price & Target Box */}
          <div className="space-y-2 rounded-md border border-neutral-200 bg-neutral-50 p-3 dark:border-[#262930] dark:bg-[#181a1f]">
            <div className="flex items-center justify-between text-xs">
              <span className="text-neutral-500 dark:text-neutral-400 font-sans">Harga Pasar</span>
              <span className="font-bold text-neutral-900 tabular-nums dark:text-neutral-100 font-mono">
                {price != null ? `Rp ${fmtIDR(price)}` : "—"}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-neutral-500 dark:text-neutral-400 font-sans">Nilai Wajar (TP)</span>
              <span className="font-bold text-neutral-900 tabular-nums dark:text-neutral-100 font-mono">
                {target != null ? `Rp ${fmtIDR(target)}` : "—"}
              </span>
            </div>
            <div className="flex items-center justify-between border-t border-neutral-200 pt-2 text-xs dark:border-[#262930]">
              <span className="text-neutral-500 dark:text-neutral-400 font-sans">Rekomendasi</span>
              <RecommendationBadge rating={rating} upside={upside} size="sm" />
            </div>
          </div>

          {/* Shares Information */}
          {shares && (
            <div className="space-y-1.5 border-t border-neutral-200 pt-2.5 text-xs text-neutral-600 dark:border-[#1f2228] dark:text-neutral-400">
              <div className="flex justify-between">
                <span className="font-sans">Saham Beredar</span>
                <span className="font-bold text-neutral-900 tabular-nums dark:text-neutral-100 font-mono">
                  {shares.outstanding} {shares.unit}
                </span>
              </div>
              {shares.free_float_pct != null && (
                <div className="flex justify-between">
                  <span className="font-sans">Porsi Publik</span>
                  <span className="font-bold text-neutral-900 tabular-nums dark:text-neutral-100 font-mono">
                    {shares.free_float_pct}%
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Sub-route Quick Action Shortcuts */}
          <div className="grid grid-cols-2 gap-2 border-t border-neutral-200 pt-2.5 dark:border-[#1f2228]">
            <Link
              to="/report/$ticker/sentiment"
              params={{ ticker: tk }}
              className="inline-flex items-center justify-center gap-1 rounded-md border border-neutral-200 bg-white py-1.5 text-center font-sans text-xs font-semibold text-neutral-700 hover:bg-neutral-50 hover:text-neutral-900 transition-colors dark:border-[#262930] dark:bg-[#181a1f] dark:text-neutral-300 dark:hover:bg-[#22252c] dark:hover:text-neutral-100"
            >
              <span>[F2] Sentimen Pasar</span>
            </Link>
            <Link
              to="/report/$ticker/challenge"
              params={{ ticker: tk }}
              className="inline-flex items-center justify-center gap-1 rounded-md border border-neutral-200 bg-white py-1.5 text-center font-sans text-xs font-semibold text-neutral-700 hover:bg-neutral-50 hover:text-neutral-900 transition-colors dark:border-[#262930] dark:bg-[#181a1f] dark:text-neutral-300 dark:hover:bg-[#22252c] dark:hover:text-neutral-100"
            >
              <span>[F3] Uji Tesis</span>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* 3. Fast Section Jump Navigation */}
      <Card className="rounded-lg border border-neutral-200 bg-white shadow-xs dark:border-[#262930] dark:bg-[#121418]">
        <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3.5 pb-2.5 dark:border-[#1f2228] dark:bg-[#181a1f]/70">
          <div className="flex items-center gap-2">
            <Compass className="h-3.5 w-3.5 text-amber-500" />
            <CardTitle className="text-[11px] font-sans font-bold uppercase tracking-wider text-neutral-600 dark:text-neutral-400">
              Navigasi Cepat Bab
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent className="p-3.5 pt-2.5">
          <nav className="space-y-1 text-xs font-sans">
            <a
              href="#executive-summary"
              className="flex items-center justify-between rounded-md px-2.5 py-1.5 text-neutral-700 hover:bg-neutral-100 hover:text-neutral-900 transition-colors dark:text-neutral-300 dark:hover:bg-[#181a1f] dark:hover:text-neutral-100"
            >
              <span>01. Ringkasan Eksekutif</span>
              <ChevronRight className="h-3 w-3 text-neutral-400" />
            </a>
            <a
              href="#valuation-methodology"
              className="flex items-center justify-between rounded-md px-2.5 py-1.5 text-neutral-700 hover:bg-neutral-100 hover:text-neutral-900 transition-colors dark:text-neutral-300 dark:hover:bg-[#181a1f] dark:hover:text-neutral-100"
            >
              <span>02. Metodologi Valuasi &amp; KPI</span>
              <ChevronRight className="h-3 w-3 text-neutral-400" />
            </a>
            <a
              href="#sensitivity-analysis"
              className="flex items-center justify-between rounded-md px-2.5 py-1.5 text-neutral-700 hover:bg-neutral-100 hover:text-neutral-900 transition-colors dark:text-neutral-300 dark:hover:bg-[#181a1f] dark:hover:text-neutral-100"
            >
              <span>03. Sensitivitas DCF</span>
              <ChevronRight className="h-3 w-3 text-neutral-400" />
            </a>
            <a
              href="#risk-factors"
              className="flex items-center justify-between rounded-md px-2.5 py-1.5 text-neutral-700 hover:bg-neutral-100 hover:text-neutral-900 transition-colors dark:text-neutral-300 dark:hover:bg-[#181a1f] dark:hover:text-neutral-100"
            >
              <span>04. Risiko &amp; Solvabilitas</span>
              <ChevronRight className="h-3 w-3 text-neutral-400" />
            </a>
            <a
              href="#sources-disclaimer"
              className="flex items-center justify-between rounded-md px-2.5 py-1.5 text-neutral-700 hover:bg-neutral-100 hover:text-neutral-900 transition-colors dark:text-neutral-300 dark:hover:bg-[#181a1f] dark:hover:text-neutral-100"
            >
              <span>05. Kepatuhan &amp; Sumber Data</span>
              <ChevronRight className="h-3 w-3 text-neutral-400" />
            </a>
          </nav>

          {provenance && (
            <div className="mt-3 flex items-center gap-1.5 border-t border-neutral-200 pt-2 text-[10px] text-neutral-400 dark:border-[#1f2228]">
              <Info className="h-3 w-3 shrink-0 text-amber-500" />
              <span className="truncate">{provenance}</span>
            </div>
          )}
        </CardContent>
      </Card>
    </aside>
  )
}

