import { Users, Leaf, LineChart, Target, Hash } from "lucide-react"
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

function Sparkline({ values, width = 160, height = 32 }: { values: number[]; width?: number; height?: number }) {
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
    <svg width={width} height={height} className="text-emerald-600 dark:text-emerald-400">
      <polyline
        points={points}
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function ShareholderBar({ holders, source }: { holders?: { name: string; pct: number }[]; source?: string }) {
  if (!holders || holders.length === 0) return null
  const colors = [
    "bg-amber-500",
    "bg-sky-500",
    "bg-emerald-500",
    "bg-purple-500",
    "bg-neutral-400",
  ]
  return (
    <div className="space-y-3">
      <div className="flex h-2 overflow-hidden rounded-xs border border-neutral-300 dark:border-[#262930]">
        {holders.map((h, i) => (
          <div
            key={h.name}
            className={colors[i % colors.length]}
            style={{ width: `${h.pct}%` }}
            title={`${h.name}: ${h.pct}%`}
          />
        ))}
      </div>
      <div className="grid gap-1.5 sm:grid-cols-2">
        {holders.map((h, i) => (
          <div
            key={h.name}
            className="flex items-center justify-between rounded border border-neutral-200 bg-neutral-50 px-2.5 py-1 text-xs font-mono dark:border-[#262930] dark:bg-[#121316]"
          >
            <span className="flex items-center gap-1.5 truncate text-neutral-800 dark:text-neutral-200">
              <span className={`h-2 w-2 shrink-0 rounded-xs ${colors[i % colors.length]}`} />
              <span className="truncate">{h.name}</span>
            </span>
            <span className="ml-2 font-bold text-neutral-900 tabular-nums dark:text-neutral-100">
              {h.pct}%
            </span>
          </div>
        ))}
      </div>
      {source && <p className="font-mono text-[10px] text-neutral-400">SRC: {source}</p>}
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
    <section id="executive-summary" className="space-y-3 scroll-mt-28">
      {/* Terminal Section Header */}
      <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-neutral-200 pb-1.5 dark:border-[#262930]">
        <div className="flex items-center gap-2">
          <span className="rounded bg-neutral-900 px-1.5 py-0.5 font-mono text-[10px] font-bold text-amber-400 dark:bg-amber-400/10 dark:text-amber-400">
            01
          </span>
          <h2 className="font-mono text-xs font-bold uppercase tracking-wider text-neutral-900 dark:text-neutral-100">
            {tk} IJ &lt;EQUITY&gt; // EXECUTIVE SUMMARY &amp; INVESTMENT THESIS
          </h2>
        </div>
        <span className="font-mono text-[10px] text-neutral-400">
          BENCHMARK: JCI (IHSG) · DETERMINISTIC AUDIT
        </span>
      </div>

      {/* Main Narrative Card */}
      <Card className="rounded-md border border-neutral-300 bg-white shadow-none dark:border-[#262930] dark:bg-[#121316]">
        <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3 pb-2.5 dark:border-[#1f2228] dark:bg-[#181a1f]/70">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-amber-500" />
              <CardTitle className="font-mono text-xs font-bold uppercase tracking-wide text-neutral-900 dark:text-neutral-100">
                CORE THESIS &amp; RATIONALE
              </CardTitle>
            </div>
            <RecommendationBadge rating={rating} targetPrice={target} upside={upside} showTarget size="sm" />
          </div>
        </CardHeader>
        <CardContent className="space-y-3 p-3 pt-3">
          <p className="text-xs leading-relaxed text-neutral-800 dark:text-neutral-200">
            {summary}
          </p>

          {/* Key Takeaways */}
          {hasTakeaways && (
            <div className="space-y-2 border-t border-neutral-200 pt-2.5 dark:border-[#1f2228]">
              <div className="flex items-center gap-1.5 font-mono text-[11px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                <Hash className="h-3 w-3" />
                <span>KEY VALUE DRIVERS &amp; TAKEAWAYS</span>
              </div>
              <div className="grid gap-1.5">
                {takeaways.map((item, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-2.5 rounded border border-neutral-200 bg-neutral-50/80 p-2 text-xs leading-relaxed text-neutral-800 dark:border-[#262930] dark:bg-[#181a1f]/60 dark:text-neutral-200"
                  >
                    <span className="flex h-4 w-5 shrink-0 items-center justify-center rounded-xs bg-neutral-900 font-mono text-[10px] font-bold text-amber-400 dark:bg-[#262930] dark:text-amber-400">
                      [{String(idx + 1).padStart(2, "0")}]
                    </span>
                    <span className="pt-0.5">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Grid: vs JCI + Shareholder + ESG */}
      <div className="grid gap-3 md:grid-cols-2">
        {/* Kinerja vs IHSG */}
        {vsJci && (
          <Card className="rounded-md border border-neutral-300 bg-white shadow-none dark:border-[#262930] dark:bg-[#121316]">
            <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3 pb-2 dark:border-[#1f2228] dark:bg-[#181a1f]/70">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <LineChart className="h-4 w-4 text-neutral-600 dark:text-neutral-400" />
                  <CardTitle className="font-mono text-xs font-bold uppercase tracking-wide text-neutral-900 dark:text-neutral-100">
                    PERFORMANCE VS JCI (YTD)
                  </CardTitle>
                </div>
                <div className="flex items-center gap-1 font-mono text-xs">
                  <Badge variant="outline" className="border-neutral-300 px-1.5 py-px text-[10px] tabular-nums dark:border-[#262930]">
                    ABS {vsJci.ytd_abs != null ? `${vsJci.ytd_abs > 0 ? "+" : ""}${vsJci.ytd_abs}%` : "—"}
                  </Badge>
                  <Badge variant="outline" className="border-neutral-300 px-1.5 py-px text-[10px] tabular-nums dark:border-[#262930]">
                    REL {vsJci.ytd_rel != null ? `${vsJci.ytd_rel > 0 ? "+" : ""}${vsJci.ytd_rel}%` : "—"}
                  </Badge>
                </div>
              </div>
              <CardDescription className="font-mono text-[10px] text-neutral-400">
                BENCHMARK: {vsJci.source ?? "SECTORS HISTORICAL TICK"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2.5 p-3 pt-2.5">
              {/* Monthly label list */}
              {vsJci.chart?.labels && vsJci.chart.series && (
                <div className="overflow-x-auto rounded border border-neutral-200 bg-neutral-50/60 p-2 font-mono text-[11px] dark:border-[#262930] dark:bg-[#181a1f]/50">
                  <div className="flex gap-1 border-b border-neutral-200 pb-1 text-[10px] text-neutral-400 dark:border-[#262930]">
                    <span className="w-12 font-bold uppercase">PERIOD</span>
                    {vsJci.chart.labels.map((l) => (
                      <span key={l} className="w-8 text-center">{l.slice(0, 3)}</span>
                    ))}
                  </div>
                  <div className="flex gap-1 py-1 font-bold text-neutral-900 dark:text-neutral-100">
                    <span className="w-12 text-amber-500">{tk}</span>
                    {vsJci.chart.series[0]?.map((v, i) => (
                      <span key={i} className="w-8 text-center tabular-nums">{v}</span>
                    ))}
                  </div>
                  <div className="flex gap-1 text-neutral-500 dark:text-neutral-400">
                    <span className="w-12 font-semibold">IHSG</span>
                    {vsJci.chart.series[1]?.map((v, i) => (
                      <span key={i} className="w-8 text-center tabular-nums">{v}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Sparklines */}
              {rawChart && rawChart.length > 1 ? (
                <div className="pt-1">
                  <Sparkline values={rawChart} width={280} height={32} />
                </div>
              ) : vsJci.chart?.series?.[0] && vsJci.chart.series[0].length > 1 ? (
                <div className="flex flex-wrap items-center gap-4 pt-1 font-mono text-xs">
                  <div className="flex items-center gap-1.5 text-neutral-700 dark:text-neutral-300">
                    <span className="font-bold text-amber-500">{tk}:</span>
                    <Sparkline values={vsJci.chart.series[0]} width={110} height={24} />
                  </div>
                  {vsJci.chart.series[1] && (
                    <div className="flex items-center gap-1.5 text-neutral-500 dark:text-neutral-400">
                      <span className="font-semibold">IHSG:</span>
                      <Sparkline values={vsJci.chart.series[1]} width={110} height={24} />
                    </div>
                  )}
                </div>
              ) : null}
            </CardContent>
          </Card>
        )}

        {/* Struktur Pemegang Saham */}
        {hasShareholders && (
          <Card className="rounded-md border border-neutral-300 bg-white shadow-none dark:border-[#262930] dark:bg-[#121316]">
            <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3 pb-2 dark:border-[#1f2228] dark:bg-[#181a1f]/70">
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-neutral-600 dark:text-neutral-400" />
                <CardTitle className="font-mono text-xs font-bold uppercase tracking-wide text-neutral-900 dark:text-neutral-100">
                  MAJOR SHAREHOLDERS &amp; FREE FLOAT
                </CardTitle>
              </div>
              <CardDescription className="font-mono text-[10px] text-neutral-400">
                {shareholdersSrc ?? "IDX DISCLOSURE / ANNUAL AUDIT"}
              </CardDescription>
            </CardHeader>
            <CardContent className="p-3 pt-2.5">
              <ShareholderBar holders={shareholders} source={shareholdersSrc ?? undefined} />
            </CardContent>
          </Card>
        )}

        {/* ESG Box (if found) */}
        {esg?.found && esg.scores && (
          <Card className="rounded-md border border-neutral-300 bg-white shadow-none md:col-span-2 dark:border-[#262930] dark:bg-[#121316]">
            <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3 pb-2 dark:border-[#1f2228] dark:bg-[#181a1f]/70">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Leaf className="h-4 w-4 text-emerald-500" />
                  <CardTitle className="font-mono text-xs font-bold uppercase tracking-wide text-neutral-900 dark:text-neutral-100">
                    SUSTAINABILITY &amp; ESG SCORECARD
                  </CardTitle>
                </div>
                <span className="font-mono text-[10px] text-neutral-400">
                  {esg.source} · {esg.date}
                </span>
              </div>
            </CardHeader>
            <CardContent className="space-y-2 p-3 pt-2.5">
              <div className="grid grid-cols-3 gap-2 text-center font-mono">
                <div className="rounded border border-neutral-200 bg-neutral-50 p-2 dark:border-[#262930] dark:bg-[#181a1f]">
                  <div className="text-[10px] uppercase text-neutral-500 dark:text-neutral-400">ENVIRONMENT (E)</div>
                  <div className="mt-0.5 text-sm font-bold text-neutral-900 tabular-nums dark:text-neutral-100">{esg.scores.e}</div>
                </div>
                <div className="rounded border border-neutral-200 bg-neutral-50 p-2 dark:border-[#262930] dark:bg-[#181a1f]">
                  <div className="text-[10px] uppercase text-neutral-500 dark:text-neutral-400">SOCIAL (S)</div>
                  <div className="mt-0.5 text-sm font-bold text-neutral-900 tabular-nums dark:text-neutral-100">{esg.scores.s}</div>
                </div>
                <div className="rounded border border-neutral-200 bg-neutral-50 p-2 dark:border-[#262930] dark:bg-[#181a1f]">
                  <div className="text-[10px] uppercase text-neutral-500 dark:text-neutral-400">GOVERNANCE (G)</div>
                  <div className="mt-0.5 text-sm font-bold text-neutral-900 tabular-nums dark:text-neutral-100">{esg.scores.g}</div>
                </div>
              </div>
              <p className="font-mono text-[10px] text-neutral-400">
                Verified ESG data from primary issuer disclosure. Rendered strictly when verified score is available.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </section>
  )
}

