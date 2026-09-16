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
        <Card className="rounded-xl border border-[#E7E3DA] bg-white p-5 dark:border-[#2A2822] dark:bg-[#1B1A16]">
          <div className="flex items-center gap-2 text-xs text-[#6B6659] dark:text-[#A8A296]">
            <Loader2 className="h-4 w-4 animate-spin text-[#0E6E63] dark:text-[#4FD1B5]" />
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
      <Card className="rounded-xl border border-[#E7E3DA] bg-white dark:border-[#2A2822] dark:bg-[#1B1A16]">
        <CardHeader className="border-b border-[#E7E3DA] p-4 pb-3 dark:border-[#2A2822]">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
              Ringkasan valuasi
            </CardTitle>
            <span className="rounded bg-[#F4F1EA] px-2 py-0.5 text-[11px] font-medium text-[#1C1B17] dark:bg-[#2A2822] dark:text-[#EDEAE3]">
              {template}
            </span>
          </div>
        </CardHeader>
        <CardContent className="space-y-3 p-4">
          {/* Main Price & Target Box */}
          <div className="space-y-2 rounded-lg border border-[#E7E3DA] bg-[#FBFAF7] p-3.5 dark:border-[#2A2822] dark:bg-[#14130F]">
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#6B6659] dark:text-[#A8A296]">Harga pasar</span>
              <span className="font-semibold text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
                {price != null ? `Rp ${fmtIDR(price)}` : "-"}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#6B6659] dark:text-[#A8A296]">Nilai wajar (TP)</span>
              <span className="font-semibold text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
                {target != null ? `Rp ${fmtIDR(target)}` : "-"}
              </span>
            </div>
            <div className="flex items-center justify-between border-t border-[#E7E3DA] pt-2 text-xs dark:border-[#2A2822]">
              <span className="text-[#6B6659] dark:text-[#A8A296]">Rekomendasi</span>
              <RecommendationBadge rating={rating} upside={upside} size="sm" />
            </div>
          </div>

          {/* Shares Information */}
          {shares && (
            <div className="space-y-1.5 border-t border-[#E7E3DA] pt-3 text-xs text-[#6B6659] dark:border-[#2A2822] dark:text-[#A8A296]">
              <div className="flex justify-between">
                <span>Saham beredar</span>
                <span className="font-medium text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
                  {shares.outstanding} {shares.unit}
                </span>
              </div>
              {shares.free_float_pct != null && (
                <div className="flex justify-between">
                  <span>Porsi publik</span>
                  <span className="font-medium text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
                    {shares.free_float_pct}%
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Challenge Entry Point */}
          <div className="border-t border-[#E7E3DA] pt-3 dark:border-[#2A2822]">
            <Link
              to="/report/$ticker/challenge"
              params={{ ticker: tk }}
              className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-[#0E6E63] py-2 text-center text-xs font-medium text-white hover:bg-[#0B5B52] transition-colors dark:bg-[#4FD1B5] dark:text-[#14130F] dark:hover:bg-[#3EBAA0]"
            >
              <Swords className="h-3.5 w-3.5" />
              <span>Uji silang tesis {tk}</span>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* 3. Fast Section Jump Navigation */}
      <Card className="rounded-xl border border-[#E7E3DA] bg-white dark:border-[#2A2822] dark:bg-[#1B1A16]">
        <CardHeader className="border-b border-[#E7E3DA] p-4 pb-3 dark:border-[#2A2822]">
          <div className="flex items-center gap-2">
            <Compass className="h-4 w-4 text-[#0E6E63] dark:text-[#4FD1B5]" />
            <CardTitle className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
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
                className="flex items-center justify-between rounded-md px-2.5 py-1.5 text-[#1C1B17] hover:bg-[#F4F1EA] transition-colors dark:text-[#EDEAE3] dark:hover:bg-[#25231E]"
              >
                <span className="truncate">
                  <span className="text-[#6B6659] mr-1.5 dark:text-[#A8A296]">{idx + 1}.</span>
                  {item.label}
                </span>
                <ChevronRight className="h-3 w-3 text-[#6B6659] shrink-0 dark:text-[#A8A296]" />
              </a>
            ))}
          </nav>

          {provenance && (
            <div className="mt-3 flex items-center gap-1.5 border-t border-[#E7E3DA] pt-2.5 text-[11px] text-[#6B6659] dark:border-[#2A2822] dark:text-[#A8A296]">
              <Info className="h-3.5 w-3.5 shrink-0 text-[#0E6E63] dark:text-[#4FD1B5]" />
              <span className="truncate">{provenance}</span>
            </div>
          )}
        </CardContent>
      </Card>
    </aside>
  )
}
