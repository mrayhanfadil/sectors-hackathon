import { Link } from "@tanstack/react-router"
import { Loader2, ChevronRight, Info } from "lucide-react"
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
  if (n == null || Number.isNaN(Number(n))) return "-"
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
    <aside className="space-y-4 w-full lg:w-[320px] shrink-0">
      {/* 1. ADK Run Card */}
      {logLoading ? (
        <Card className="border-neutral-200 bg-white p-4 shadow-2xs dark:border-neutral-800 dark:bg-[#111111]">
          <div className="flex items-center gap-2 text-xs text-neutral-500 dark:text-neutral-400">
            <Loader2 className="h-4 w-4 animate-spin text-neutral-400" />
            <span>Memuat status trace ADK {tk}...</span>
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
      <Card className="border-neutral-200 bg-white shadow-2xs dark:border-neutral-800 dark:bg-[#111111]">
        <CardHeader className="p-4 pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
              Ringkasan Valuasi
            </CardTitle>
            <Badge variant="outline" className="text-[10px] font-mono uppercase bg-neutral-50 dark:bg-neutral-900">
              {template}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="p-4 pt-2 space-y-3">
          {/* Main Price & Target Box */}
          <div className="rounded-lg border border-neutral-100 bg-neutral-50/80 p-3 space-y-2 dark:border-neutral-800 dark:bg-neutral-900/80">
            <div className="flex items-center justify-between text-xs">
              <span className="text-neutral-500 dark:text-neutral-400">Harga Terkini</span>
              <span className="font-mono font-semibold text-neutral-900 dark:text-neutral-100">
                {price != null ? `Rp ${fmtIDR(price)}` : "-"}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-neutral-500 dark:text-neutral-400">Nilai Wajar (TP)</span>
              <span className="font-mono font-bold text-neutral-900 dark:text-neutral-100">
                {target != null ? `Rp ${fmtIDR(target)}` : "-"}
              </span>
            </div>
            <div className="flex items-center justify-between border-t border-neutral-200/60 pt-2 text-xs dark:border-neutral-800/60">
              <span className="font-medium text-neutral-700 dark:text-neutral-300">Rekomendasi</span>
              <RecommendationBadge rating={rating} upside={upside} size="sm" />
            </div>
          </div>

          {/* Shares Information */}
          {shares && (
            <div className="space-y-1.5 border-t border-neutral-100 pt-2.5 text-xs dark:border-neutral-800">
              <div className="flex justify-between text-neutral-600 dark:text-neutral-400">
                <span>Saham Beredar</span>
                <span className="font-mono font-medium text-neutral-900 dark:text-neutral-100">
                  {shares.outstanding} {shares.unit}
                </span>
              </div>
              {shares.free_float_pct != null && (
                <div className="flex justify-between text-neutral-600 dark:text-neutral-400">
                  <span>Free Float</span>
                  <span className="font-mono font-medium text-neutral-900 dark:text-neutral-100">
                    {shares.free_float_pct}%
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Sub-route Quick Action Shortcuts */}
          <div className="grid grid-cols-2 gap-2 border-t border-neutral-100 pt-3 dark:border-neutral-800">
            <Link
              to="/report/$ticker/sentiment"
              params={{ ticker: tk }}
              className="inline-flex items-center justify-center gap-1 rounded-md border border-neutral-200 bg-white px-2.5 py-1.5 text-xs font-medium text-neutral-700 hover:bg-neutral-50 hover:text-neutral-900 transition-colors dark:border-neutral-800 dark:bg-[#111111] dark:text-neutral-300 dark:hover:bg-neutral-900 dark:hover:text-neutral-100"
            >
              <span>Sentimen Ritel</span>
            </Link>
            <Link
              to="/report/$ticker/challenge"
              params={{ ticker: tk }}
              className="inline-flex items-center justify-center gap-1 rounded-md border border-neutral-200 bg-white px-2.5 py-1.5 text-xs font-medium text-neutral-700 hover:bg-neutral-50 hover:text-neutral-900 transition-colors dark:border-neutral-800 dark:bg-[#111111] dark:text-neutral-300 dark:hover:bg-neutral-900 dark:hover:text-neutral-100"
            >
              <span>Uji Tesis</span>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* 3. Fast Section Jump Navigation */}
      <Card className="border-neutral-200 bg-white shadow-2xs dark:border-neutral-800 dark:bg-[#111111]">
        <CardHeader className="p-4 pb-2">
          <CardTitle className="text-xs font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
            Navigasi Halaman
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 pt-1">
          <nav className="space-y-1 text-xs">
            <a
              href="#executive-summary"
              className="flex items-center justify-between rounded px-2 py-1.5 text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900 transition-colors dark:text-neutral-400 dark:hover:bg-neutral-900 dark:hover:text-neutral-100"
            >
              <span>1. Ringkasan Eksekutif</span>
              <ChevronRight className="h-3 w-3 text-neutral-400" />
            </a>
            <a
              href="#valuation-methodology"
              className="flex items-center justify-between rounded px-2 py-1.5 text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900 transition-colors dark:text-neutral-400 dark:hover:bg-neutral-900 dark:hover:text-neutral-100"
            >
              <span>2. Metodologi Valuasi</span>
              <ChevronRight className="h-3 w-3 text-neutral-400" />
            </a>
            <a
              href="#sensitivity-analysis"
              className="flex items-center justify-between rounded px-2 py-1.5 text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900 transition-colors dark:text-neutral-400 dark:hover:bg-neutral-900 dark:hover:text-neutral-100"
            >
              <span>3. Analisis Sensitivitas</span>
              <ChevronRight className="h-3 w-3 text-neutral-400" />
            </a>
            <a
              href="#risk-factors"
              className="flex items-center justify-between rounded px-2 py-1.5 text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900 transition-colors dark:text-neutral-400 dark:hover:bg-neutral-900 dark:hover:text-neutral-100"
            >
              <span>4. Faktor Risiko & Solvabilitas</span>
              <ChevronRight className="h-3 w-3 text-neutral-400" />
            </a>
            <a
              href="#sources-disclaimer"
              className="flex items-center justify-between rounded px-2 py-1.5 text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900 transition-colors dark:text-neutral-400 dark:hover:bg-neutral-900 dark:hover:text-neutral-100"
            >
              <span>5. Sumber & Kepatuhan</span>
              <ChevronRight className="h-3 w-3 text-neutral-400" />
            </a>
          </nav>

          {provenance && (
            <div className="mt-3 border-t border-neutral-100 pt-2.5 text-[11px] text-neutral-400 font-mono flex items-center gap-1 dark:border-neutral-800">
              <Info className="h-3 w-3 shrink-0" />
              <span className="truncate">{provenance}</span>
            </div>
          )}
        </CardContent>
      </Card>
    </aside>
  )
}
