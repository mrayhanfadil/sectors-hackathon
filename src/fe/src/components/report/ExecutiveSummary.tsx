import { Users, Leaf, LineChart, Target } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { RecommendationBadge } from "./RecommendationBadge"

export interface ExecutiveSummaryProps {
  ticker: string
  name?: string
  price?: number | null
  target?: number | null
  upside?: string | null
  rating?: string | null
  summary: string
  takeaways?: string[]
  vsJci?: {
    ytd_abs?: number | null
    ytd_rel?: number | null
    source?: string
    chart?: {
      labels: string[]
      series: number[][]
    } | null
  }
  rawChart?: number[]
  shareholders?: { name: string; pct: number }[]
  shareholdersSrc?: string | null
  esg?: {
    found: boolean
    scores?: { e: number; s: number; g: number }
    source?: string
    date?: string
  }
}

function Sparkline({ values, width = 140, height = 32 }: { values: number[]; width?: number; height?: number }) {
  if (!Array.isArray(values) || values.length < 2) return null
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const points = values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * width
      const y = height - ((v - min) / range) * (height - 6) - 3
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(" ")
  return (
    <svg width={width} height={height} className="text-neutral-800 dark:text-neutral-200">
      <polyline points={points} fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function ShareholderBar({ holders, source }: { holders?: { name: string; pct: number }[]; source?: string }) {
  if (!holders || holders.length === 0) return null
  const colors = ["bg-neutral-900 dark:bg-neutral-800", "bg-neutral-600 dark:bg-neutral-500", "bg-neutral-400 dark:bg-neutral-600", "bg-emerald-600", "bg-amber-500"]
  return (
    <div className="space-y-3">
      <div className="flex h-2.5 overflow-hidden rounded-full border border-neutral-200 dark:border-neutral-800">
        {holders.map((h, i) => (
          <div
            key={h.name}
            className={colors[i % colors.length]}
            style={{ width: `${h.pct}%` }}
            title={`${h.name}: ${h.pct}%`}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        {holders.map((h, i) => (
          <span key={h.name} className="inline-flex items-center gap-1.5 rounded-md border border-neutral-200 bg-white px-2.5 py-1 text-xs text-neutral-700 dark:border-neutral-800 dark:bg-[#111111] dark:text-neutral-300">
            <span className={`h-2 w-2 rounded-full ${colors[i % colors.length]}`} />
            <span className="font-medium text-neutral-900 dark:text-neutral-100">{h.name}</span>
            <span className="font-mono text-neutral-500 dark:text-neutral-400">{h.pct}%</span>
          </span>
        ))}
      </div>
      {source && <p className="text-[11px] text-neutral-400">Sumber: {source}</p>}
    </div>
  )
}

export function ExecutiveSummary({
  ticker,
  name: _name,
  price: _price,
  target,
  upside,
  rating,
  summary,
  takeaways = [],
  vsJci,
  rawChart,
  shareholders = [],
  shareholdersSrc,
  esg,
}: ExecutiveSummaryProps) {
  const tk = ticker.toUpperCase()
  const hasShareholders = shareholders.length > 0
  const hasTakeaways = takeaways.length > 0

  return (
    <section id="executive-summary" className="space-y-4 scroll-mt-28">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[15px] font-semibold tracking-tight text-[#0a0a0a] dark:text-white">
            1. Ringkasan Eksekutif
          </h2>
          <p className="text-xs text-neutral-500 dark:text-neutral-400">
            Tesis investasi utama, profil rekomendasi, dan perbandingan kinerja pasar
          </p>
        </div>
      </div>

      {/* Main Narrative Card */}
      <Card className="border-neutral-200 bg-white shadow-2xs dark:border-neutral-800 dark:bg-[#111111]">
        <CardHeader className="p-4 pb-2">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-neutral-700 dark:text-neutral-300" />
              <CardTitle className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
                Tesis Investasi & Pandangan Inti
              </CardTitle>
            </div>
            <RecommendationBadge rating={rating} targetPrice={target} upside={upside} showTarget size="sm" />
          </div>
        </CardHeader>
        <CardContent className="p-4 pt-2 space-y-4">
          <p className="text-sm leading-relaxed text-neutral-700 font-normal dark:text-neutral-300">
            {summary}
          </p>

          {/* Key Takeaways (3-5 Bullet Points) */}
          {hasTakeaways && (
            <div className="space-y-2 border-t border-neutral-100 pt-3 dark:border-neutral-800">
              <div className="text-xs font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                Poin Kunci (Key Takeaways)
              </div>
              <div className="grid gap-2">
                {takeaways.map((item, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-2.5 rounded-lg border border-neutral-100 bg-neutral-50/60 p-2.5 text-xs text-neutral-800 dark:border-neutral-800 dark:bg-neutral-900/60 dark:text-neutral-200"
                  >
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-neutral-900 text-[10px] font-bold text-white dark:bg-neutral-800">
                      {idx + 1}
                    </span>
                    <span className="pt-0.5 leading-relaxed">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Grid: vs JCI + Shareholder + ESG */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Kinerja vs IHSG */}
        {vsJci && (
          <Card className="border-neutral-200 bg-white shadow-2xs dark:border-neutral-800 dark:bg-[#111111]">
            <CardHeader className="p-4 pb-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <LineChart className="h-4 w-4 text-neutral-700 dark:text-neutral-300" />
                  <CardTitle className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
                    Kinerja vs IHSG (YTD)
                  </CardTitle>
                </div>
                <div className="flex items-center gap-1.5">
                  <Badge variant="secondary" className="text-xs font-mono">
                    Abs {vsJci.ytd_abs != null ? `${vsJci.ytd_abs > 0 ? "+" : ""}${vsJci.ytd_abs}%` : "-"}
                  </Badge>
                  <Badge variant="outline" className="text-xs font-mono bg-neutral-50 dark:bg-neutral-900">
                    Rel {vsJci.ytd_rel != null ? `${vsJci.ytd_rel > 0 ? "+" : ""}${vsJci.ytd_rel}%` : "-"}
                  </Badge>
                </div>
              </div>
              <CardDescription className="text-[11px] text-neutral-400">
                {vsJci.source ?? "Sectors API"}
              </CardDescription>
            </CardHeader>
            <CardContent className="p-4 pt-2 space-y-3">
              {/* Monthly label list */}
              {vsJci.chart?.labels && vsJci.chart.series && (
                <div className="overflow-x-auto rounded border border-neutral-100 bg-neutral-50/50 p-2 dark:border-neutral-800 dark:bg-neutral-900/50">
                  <div className="flex gap-1 text-[10px] text-neutral-400 pb-1 border-b border-neutral-200/60 dark:border-neutral-800/60">
                    <span className="w-14 font-medium">Bulan</span>
                    {vsJci.chart.labels.map((l) => (
                      <span key={l} className="w-7 text-center font-mono">{l.slice(0, 3)}</span>
                    ))}
                  </div>
                  <div className="flex gap-1 text-[11px] text-neutral-800 py-1 font-mono dark:text-neutral-200">
                    <span className="w-14 font-semibold text-neutral-900 dark:text-neutral-100">{tk}</span>
                    {vsJci.chart.series[0]?.map((v, i) => (
                      <span key={i} className="w-7 text-center">{v}</span>
                    ))}
                  </div>
                  <div className="flex gap-1 text-[11px] text-neutral-500 font-mono dark:text-neutral-400">
                    <span className="w-14 font-medium">IHSG</span>
                    {vsJci.chart.series[1]?.map((v, i) => (
                      <span key={i} className="w-7 text-center">{v}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Sparklines */}
              {rawChart && rawChart.length > 1 ? (
                <div className="pt-1">
                  <Sparkline values={rawChart} width={260} height={36} />
                </div>
              ) : vsJci.chart?.series?.[0] && vsJci.chart.series[0].length > 1 ? (
                <div className="flex flex-wrap items-center gap-4 pt-1">
                  <div className="flex items-center gap-2 text-xs text-neutral-700 dark:text-neutral-300">
                    <span className="font-semibold font-mono">{tk}:</span>
                    <Sparkline values={vsJci.chart.series[0]} width={120} height={28} />
                  </div>
                  {vsJci.chart.series[1] && (
                    <div className="flex items-center gap-2 text-xs text-neutral-500 dark:text-neutral-400">
                      <span className="font-medium">IHSG:</span>
                      <Sparkline values={vsJci.chart.series[1]} width={120} height={28} />
                    </div>
                  )}
                </div>
              ) : null}
            </CardContent>
          </Card>
        )}

        {/* Struktur Pemegang Saham */}
        {hasShareholders && (
          <Card className="border-neutral-200 bg-white shadow-2xs dark:border-neutral-800 dark:bg-[#111111]">
            <CardHeader className="p-4 pb-2">
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-neutral-700 dark:text-neutral-300" />
                <CardTitle className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
                  Struktur Pemegang Saham
                </CardTitle>
              </div>
              <CardDescription className="text-[11px] text-neutral-400">
                {shareholdersSrc ?? "Keterbukaan Informasi IDX"}
              </CardDescription>
            </CardHeader>
            <CardContent className="p-4 pt-2">
              <ShareholderBar holders={shareholders} source={shareholdersSrc ?? undefined} />
            </CardContent>
          </Card>
        )}

        {/* ESG Box (if found) */}
        {esg?.found && esg.scores && (
          <Card className="border-neutral-200 bg-white shadow-2xs md:col-span-2 dark:border-neutral-800 dark:bg-[#111111]">
            <CardHeader className="p-4 pb-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Leaf className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                  <CardTitle className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
                    Skor Keberlanjutan & ESG
                  </CardTitle>
                </div>
                <span className="text-[11px] text-neutral-400 font-mono">
                  {esg.source} · {esg.date}
                </span>
              </div>
            </CardHeader>
            <CardContent className="p-4 pt-2 space-y-2">
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="rounded-lg border border-neutral-100 bg-neutral-50/80 p-2.5 dark:border-neutral-800 dark:bg-neutral-900/80">
                  <div className="text-[11px] font-medium text-neutral-500 dark:text-neutral-400">Environmental (E)</div>
                  <div className="text-base font-bold font-mono text-neutral-900 dark:text-neutral-100">{esg.scores.e}</div>
                </div>
                <div className="rounded-lg border border-neutral-100 bg-neutral-50/80 p-2.5 dark:border-neutral-800 dark:bg-neutral-900/80">
                  <div className="text-[11px] font-medium text-neutral-500 dark:text-neutral-400">Social (S)</div>
                  <div className="text-base font-bold font-mono text-neutral-900 dark:text-neutral-100">{esg.scores.s}</div>
                </div>
                <div className="rounded-lg border border-neutral-100 bg-neutral-50/80 p-2.5 dark:border-neutral-800 dark:bg-neutral-900/80">
                  <div className="text-[11px] font-medium text-neutral-500 dark:text-neutral-400">Governance (G)</div>
                  <div className="text-base font-bold font-mono text-neutral-900 dark:text-neutral-100">{esg.scores.g}</div>
                </div>
              </div>
              <p className="text-[11px] text-neutral-400">
                Skor ESG dari penyedia data terverifikasi (Sustainalytics/IDX). Hanya ditampilkan jika data resmi tersedia.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </section>
  )
}
