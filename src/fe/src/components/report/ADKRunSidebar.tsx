import { Link } from "@tanstack/react-router"
import { Loader2, ChevronRight, Info, Compass, Swords } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
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
    <aside className="w-full shrink-0 space-y-4 lg:w-[320px]">
      {/* 1. ADK Run Card */}
      {logLoading ? (
        <Card className="rounded-xl border border-[#D9D9D9] bg-white p-5 dark:border-[#262930] dark:bg-[#090a0c]">
          <div className="flex items-center gap-2 text-xs text-[#666666] dark:text-[#666666]">
            <Loader2 className="h-4 w-4 animate-spin text-[#0928B1] dark:text-[#7596FF]" />
            <span>Menghubungkan ke proses analisis...</span>
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
      <Card className="rounded-xl border border-[#D9D9D9] bg-white dark:border-[#262930] dark:bg-[#090a0c]">
        <CardHeader className="border-b border-[#D9D9D9] p-4 pb-3 dark:border-[#262930]">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs font-semibold text-[#333333] dark:text-[#f1f5f9]">
              Ringkasan valuasi
            </CardTitle>
            <span className="rounded bg-[#B4C7FF] px-2 py-0.5 text-[11px] font-medium text-[#333333] dark:bg-[#262930] dark:text-[#f1f5f9]">
              {template}
            </span>
          </div>
        </CardHeader>
        <CardContent className="space-y-3 p-4">
          {/* Main Price & Target Box */}
          <div className="space-y-2 rounded-lg border border-[#D9D9D9] bg-[#f1f5f9] p-3.5 dark:border-[#262930] dark:bg-[#1e2229]">
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#666666] dark:text-[#666666]">Harga pasar</span>
              <span className="font-semibold text-[#333333] font-mono tabular-nums dark:text-[#f1f5f9]">
                {price != null ? `Rp ${fmtIDR(price)}` : "-"}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#666666] dark:text-[#666666]">Nilai wajar (TP)</span>
              <span className="font-semibold text-[#333333] font-mono tabular-nums dark:text-[#f1f5f9]">
                {target != null ? `Rp ${fmtIDR(target)}` : "-"}
              </span>
            </div>
            <div className="flex items-center justify-between border-t border-[#D9D9D9] pt-2 text-xs dark:border-[#262930]">
              <span className="text-[#666666] dark:text-[#666666]">Rekomendasi</span>
              <RecommendationBadge rating={rating} upside={upside} size="sm" />
            </div>
          </div>

          {/* Shares Information */}
          {shares && (
            <div className="space-y-1.5 border-t border-[#D9D9D9] pt-3 text-xs text-[#666666] dark:border-[#262930] dark:text-[#666666]">
              <div className="flex justify-between">
                <span>Saham beredar</span>
                <span className="font-medium text-[#333333] font-mono tabular-nums dark:text-[#f1f5f9]">
                  {shares.outstanding} {shares.unit}
                </span>
              </div>
              {shares.free_float_pct != null && (
                <div className="flex justify-between">
                  <span>Porsi publik</span>
                  <span className="font-medium text-[#333333] font-mono tabular-nums dark:text-[#f1f5f9]">
                    {shares.free_float_pct}%
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Challenge Entry Point */}
          <div className="border-t border-[#D9D9D9] pt-3 dark:border-[#262930]">
            <Link
              to="/report/$ticker/challenge"
              params={{ ticker: tk }}
              className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-[#0928B1] py-2 text-center text-xs font-medium text-white hover:bg-[#0047AB] transition-colors dark:bg-[#7596FF] dark:text-[#333333] dark:hover:bg-[#3EBAA0]"
            >
              <Swords className="h-3.5 w-3.5" />
              <span>Uji silang tesis {tk}</span>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* 3. Fast Section Jump Navigation */}
      <Card className="rounded-xl border border-[#D9D9D9] bg-white dark:border-[#262930] dark:bg-[#090a0c]">
        <CardHeader className="border-b border-[#D9D9D9] p-4 pb-3 dark:border-[#262930]">
          <div className="flex items-center gap-2">
            <Compass className="h-4 w-4 text-[#0928B1] dark:text-[#7596FF]" />
            <CardTitle className="text-xs font-semibold text-[#333333] dark:text-[#f1f5f9]">
              Daftar bab laporan
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent className="p-3">
          <nav className="space-y-0.5 text-xs">
            {[
              { href: "#cover-rating", label: "Ringkasan dan peringkat" },
              { href: "#key-financials", label: "Ringkasan keuangan & proyeksi" },
              { href: "#performance-quadrants", label: "Visualisasi kinerja keuangan" },
              { href: "#valuation-spread", label: "Nilai wajar dan sensitivitas DCF" },
              { href: "#peers-5a", label: "Valuasi komparasi peer" },
              { href: "#peers-5b", label: "Valuasi relatif historis" },
              { href: "#financial-statements", label: "Laporan keuangan (Laba rugi & neraca)" },
              { href: "#cashflow-ratios", label: "Arus kas dan rasio" },
              { href: "#risk-factors", label: "Faktor risiko" },
              { href: "#sources-disclaimer", label: "Cara membaca dan disklaimer" },
            ].map((item, idx) => (
              <a
                key={item.href}
                href={item.href}
                className="flex items-center justify-between rounded-md px-2.5 py-1.5 text-[#333333] hover:bg-[#B4C7FF] transition-colors dark:text-[#f1f5f9] dark:hover:bg-[#1e2229]"
              >
                <span className="truncate">
                  <span className="text-[#666666] mr-1.5 dark:text-[#666666]">{idx + 1}.</span>
                  {item.label}
                </span>
                <ChevronRight className="h-3 w-3 text-[#666666] shrink-0 dark:text-[#666666]" />
              </a>
            ))}
          </nav>

          {provenance && (
            <div className="mt-3 flex flex-wrap items-start gap-1.5 border-t border-[#D9D9D9] pt-2.5 text-[11px] text-[#666666] dark:border-[#262930] dark:text-[#666666]">
              <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#0928B1] dark:text-[#7596FF]" />
              <span className="min-w-0 flex-1 break-words text-ellipsis" title={provenance}>
                {provenance}
              </span>
            </div>
          )}
        </CardContent>
      </Card>
    </aside>
  )
}
