import { useMemo } from "react"
import {
  Activity,
  BarChart2,
  ShieldCheck,
  Globe2,
  TrendingUp,
  TrendingDown,
  MinusCircle,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { Sentiment } from "@/lib/api"

export type SentimentStatCardsProps = {
  ticker: string
  sentiment?: Sentiment | null
  newsCount?: number
  socialCount?: number
}

export function SentimentStatCards({
  sentiment,
  newsCount = 0,
}: SentimentStatCardsProps) {
  // LOUD policy: no invented gauge 50. Null means missing BE data.
  const gaugeVal: number | null = sentiment?.gauge != null ? Number(sentiment.gauge) : null

  const { statusLabel, badgeColor, barColor } = useMemo(() => {
    if (gaugeVal == null) {
      return {
        statusLabel: "NO DATA",
        badgeColor: "border-neutral-300 bg-neutral-100 text-neutral-600 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-400",
        barColor: "bg-neutral-400 dark:bg-neutral-600",
      }
    }
    if (gaugeVal >= 60) {
      return {
        statusLabel: sentiment?.label ? `BULLISH // ${sentiment.label.toUpperCase()}` : "BULLISH / ACCUMULATION",
        badgeColor: "border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
        barColor: "bg-emerald-600 dark:bg-emerald-500",
      }
    }
    if (gaugeVal <= 40) {
      return {
        statusLabel: sentiment?.label ? `BEARISH // ${sentiment.label.toUpperCase()}` : "BEARISH / CAUTION",
        badgeColor: "border-rose-500/40 bg-rose-500/10 text-rose-700 dark:text-rose-400",
        barColor: "bg-rose-600 dark:bg-rose-500",
      }
    }
    return {
      statusLabel: sentiment?.label ? `NEUTRAL // ${sentiment.label.toUpperCase()}` : "NEUTRAL / CONSOLIDATION",
      badgeColor: "border-neutral-300 bg-neutral-100 text-neutral-700 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300",
      barColor: "bg-amber-600 dark:bg-amber-500",
    }
  }, [gaugeVal, sentiment?.label])

  // Distribution estimation from items if available
  const distribution = useMemo(() => {
    const items = sentiment?.items || []
    if (items.length > 0) {
      let bull = 0
      let bear = 0
      let neut = 0
      items.forEach((it) => {
        const score = it.score ?? 50
        if (score >= 60) bull++
        else if (score <= 40) bear++
        else neut++
      })
      const total = items.length
      return {
        bullishPct: Math.round((bull / total) * 100),
        bearishPct: Math.round((bear / total) * 100),
        neutralPct: Math.round((neut / total) * 100),
        totalItems: total,
      }
    }
    return {
      bullishPct: null as number | null,
      bearishPct: null as number | null,
      neutralPct: null as number | null,
      totalItems: items.length,
    }
  }, [sentiment?.items])

  const confidencePct: number | null = sentiment?.confidence != null
    ? Math.round(sentiment.confidence * 100)
    : null

  const totalSources = (sentiment?.sources?.length || 0) + (sentiment?.items?.length || 0) + newsCount

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {/* Card 1: Gauge Index */}
      <Card className="rounded-none border border-neutral-300 bg-white shadow-none dark:border-[#262930] dark:bg-[#121316]">
        <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3 pb-2 dark:border-[#262930] dark:bg-[#181a1f]/70">
          <div className="flex items-center justify-between">
            <CardTitle className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-700 dark:text-neutral-300">
              SENTIMENT INDEX [0-100]
            </CardTitle>
            <Activity className="h-3.5 w-3.5 text-neutral-400" />
          </div>
        </CardHeader>
        <CardContent className="p-3 space-y-2.5">
          <div className="flex items-baseline justify-between">
            <div className="flex items-baseline gap-1.5">
              <span className={`font-mono text-2xl font-bold tabular-nums ${
                gaugeVal == null
                  ? "text-neutral-400"
                  : gaugeVal >= 60
                  ? "text-emerald-600 dark:text-emerald-400"
                  : gaugeVal <= 40
                  ? "text-rose-600 dark:text-rose-400"
                  : "text-amber-600 dark:text-amber-400"
              }`}>
                {gaugeVal != null ? gaugeVal : "—"}
              </span>
              <span className="font-mono text-[11px] text-neutral-400">/ 100</span>
            </div>
            <span className={`rounded-none border px-1.5 py-0.5 font-mono text-[10px] font-semibold tracking-wider ${badgeColor}`}>
              [{statusLabel}]
            </span>
          </div>

          {/* Visual Gauge Bar with 40 / 60 thresholds */}
          <div className="space-y-1">
            <div className="relative h-2 w-full overflow-hidden rounded-none border border-neutral-300 bg-neutral-100 dark:border-[#262930] dark:bg-[#181a1f]">
              {gaugeVal != null && (
                <div
                  className={`h-full transition-all duration-300 ${barColor}`}
                  style={{ width: `${Math.max(3, Math.min(100, gaugeVal))}%` }}
                />
              )}
              {/* Threshold tick indicators */}
              <div className="absolute top-0 bottom-0 left-[40%] w-px bg-neutral-400/50 dark:bg-neutral-500/50" title="Bearish threshold 40" />
              <div className="absolute top-0 bottom-0 left-[60%] w-px bg-neutral-400/50 dark:bg-neutral-500/50" title="Bullish threshold 60" />
            </div>
            <div className="flex justify-between font-mono text-[9px] text-neutral-400">
              <span>0 BEAR</span>
              <span className="text-neutral-500 dark:text-neutral-400">50 NET</span>
              <span>100 BULL</span>
            </div>
          </div>

          <p className="font-mono text-[10px] leading-relaxed text-neutral-500 dark:text-neutral-400">
            {gaugeVal == null
              ? "MENUNGGU INGESTI DATA SENTIMEN SECTORS."
              : gaugeVal >= 60
              ? "Dominan akumulasi positif di kanal diskusi publik."
              : gaugeVal <= 40
              ? "Sentimen hati-hati / tekanan jual terpantau."
              : "Pergerakan narasi berimbang tanpa polarisasi ekstrem."}
          </p>
        </CardContent>
      </Card>

      {/* Card 2: Ratio Distribution */}
      <Card className="rounded-none border border-neutral-300 bg-white shadow-none dark:border-[#262930] dark:bg-[#121316]">
        <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3 pb-2 dark:border-[#262930] dark:bg-[#181a1f]/70">
          <div className="flex items-center justify-between">
            <CardTitle className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-700 dark:text-neutral-300">
              POLARIZATION RATIO
            </CardTitle>
            <BarChart2 className="h-3.5 w-3.5 text-neutral-400" />
          </div>
        </CardHeader>
        <CardContent className="p-3 space-y-2.5">
          <div className="grid grid-cols-3 gap-1 text-center font-mono">
            <div className="border border-emerald-300 bg-emerald-500/10 p-1 dark:border-emerald-800 dark:bg-emerald-950/40">
              <div className="flex items-center justify-center gap-0.5 text-[9px] font-semibold text-emerald-700 dark:text-emerald-400">
                <TrendingUp className="h-2.5 w-2.5" /> POS
              </div>
              <div className="text-xs font-bold tabular-nums text-emerald-800 dark:text-emerald-300">
                {distribution.bullishPct == null ? "—" : `${distribution.bullishPct}%`}
              </div>
            </div>
            <div className="border border-neutral-300 bg-neutral-100/70 p-1 dark:border-[#262930] dark:bg-[#181a1f]">
              <div className="flex items-center justify-center gap-0.5 text-[9px] font-semibold text-neutral-600 dark:text-neutral-400">
                <MinusCircle className="h-2.5 w-2.5" /> NET
              </div>
              <div className="text-xs font-bold tabular-nums text-neutral-800 dark:text-neutral-200">
                {distribution.neutralPct == null ? "—" : `${distribution.neutralPct}%`}
              </div>
            </div>
            <div className="border border-rose-300 bg-rose-500/10 p-1 dark:border-rose-800 dark:bg-rose-950/40">
              <div className="flex items-center justify-center gap-0.5 text-[9px] font-semibold text-rose-700 dark:text-rose-400">
                <TrendingDown className="h-2.5 w-2.5" /> NEG
              </div>
              <div className="text-xs font-bold tabular-nums text-rose-800 dark:text-rose-300">
                {distribution.bearishPct == null ? "—" : `${distribution.bearishPct}%`}
              </div>
            </div>
          </div>

          <div className="flex h-2 overflow-hidden rounded-none border border-neutral-300 bg-neutral-100 dark:border-[#262930] dark:bg-[#181a1f]">
            <div
              className="bg-emerald-600 transition-all dark:bg-emerald-500"
              style={{ width: `${distribution.bullishPct ?? 0}%` }}
              title={`Positif: ${distribution.bullishPct ?? "—"}%`}
            />
            <div
              className="bg-neutral-400 transition-all dark:bg-neutral-600"
              style={{ width: `${distribution.neutralPct ?? 0}%` }}
              title={`Netral: ${distribution.neutralPct ?? "—"}%`}
            />
            <div
              className="bg-rose-600 transition-all dark:bg-rose-500"
              style={{ width: `${distribution.bearishPct ?? 0}%` }}
              title={`Negatif: ${distribution.bearishPct ?? "—"}%`}
            />
          </div>

          <div className="flex justify-between font-mono text-[10px] text-neutral-500 dark:text-neutral-400">
            <span>SAMPEL: {distribution.totalItems > 0 ? `${distribution.totalItems} POST` : "—"}</span>
            <span>BE RAW DATA</span>
          </div>
        </CardContent>
      </Card>

      {/* Card 3: Confidence Score */}
      <Card className="rounded-none border border-neutral-300 bg-white shadow-none dark:border-[#262930] dark:bg-[#121316]">
        <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3 pb-2 dark:border-[#262930] dark:bg-[#181a1f]/70">
          <div className="flex items-center justify-between">
            <CardTitle className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-700 dark:text-neutral-300">
              SAMPLE CONFIDENCE
            </CardTitle>
            <ShieldCheck className="h-3.5 w-3.5 text-neutral-400" />
          </div>
        </CardHeader>
        <CardContent className="p-3 space-y-2.5">
          <div className="flex items-baseline justify-between">
            <span className="font-mono text-2xl font-bold tabular-nums text-neutral-900 dark:text-neutral-100">
              {confidencePct == null ? "—" : `${confidencePct}%`}
            </span>
            <span className="rounded-none border border-neutral-300 bg-neutral-100 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-neutral-700 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">
              {confidencePct == null ? "[MENUNGGU]" : confidencePct >= 70 ? "[HIGH DENSITY]" : confidencePct >= 50 ? "[SUFFICIENT]" : "[PRELIMINARY]"}
            </span>
          </div>

          <div className="h-2 w-full overflow-hidden rounded-none border border-neutral-300 bg-neutral-100 dark:border-[#262930] dark:bg-[#181a1f]">
            <div
              className="h-full bg-cyan-600 transition-all dark:bg-cyan-500"
              style={{ width: `${confidencePct ?? 0}%` }}
            />
          </div>

          <p className="font-mono text-[10px] leading-relaxed text-neutral-500 dark:text-neutral-400">
            Pelacakan algoritma NLP berbasis kata kunci kontekstual IDX.
          </p>
        </CardContent>
      </Card>

      {/* Card 4: Indexed Sources & Channels */}
      <Card className="rounded-none border border-neutral-300 bg-white shadow-none dark:border-[#262930] dark:bg-[#121316]">
        <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3 pb-2 dark:border-[#262930] dark:bg-[#181a1f]/70">
          <div className="flex items-center justify-between">
            <CardTitle className="text-[11px] font-mono font-semibold uppercase tracking-wider text-neutral-700 dark:text-neutral-300">
              INDEXED CHANNELS
            </CardTitle>
            <Globe2 className="h-3.5 w-3.5 text-neutral-400" />
          </div>
        </CardHeader>
        <CardContent className="p-3 space-y-2.5">
          <div className="flex items-baseline justify-between font-mono">
            <span className="text-2xl font-bold tabular-nums text-neutral-900 dark:text-neutral-100">
              {totalSources > 0 ? totalSources : "—"}
            </span>
            <span className="text-[10px] text-neutral-500 dark:text-neutral-400">ENTRIES DETECTED</span>
          </div>

          <div className="flex flex-wrap gap-1 font-mono text-[10px]">
            <span className="border border-neutral-300 bg-neutral-100 px-1.5 py-0.5 text-neutral-700 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">
              [STOCKBIT]
            </span>
            <span className="border border-neutral-300 bg-neutral-100 px-1.5 py-0.5 text-neutral-700 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">
              [X / TWITTER]
            </span>
            <span className="border border-neutral-300 bg-neutral-100 px-1.5 py-0.5 text-neutral-700 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">
              [IDX PRESS]
            </span>
          </div>

          <p className="font-mono text-[10px] leading-relaxed text-neutral-500 dark:text-neutral-400">
            Diperbarui berkala via News & Social Harvester.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
