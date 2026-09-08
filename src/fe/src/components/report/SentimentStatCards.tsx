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
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
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
  socialCount = 0,
}: SentimentStatCardsProps) {
  // LOUD policy: no invented gauge 50. Null means missing BE data.
  const gaugeVal: number | null = sentiment?.gauge != null ? Number(sentiment.gauge) : null

  const { statusLabel, badgeVariant, colorClass } = useMemo(() => {
    if (gaugeVal == null) {
      return {
        statusLabel: "Menunggu data",
        badgeVariant: "secondary" as const,
        colorClass: "text-neutral-500 dark:text-neutral-400",
      }
    }
    if (gaugeVal >= 60) {
      return {
        statusLabel: sentiment?.label || "Bullish / Positif",
        badgeVariant: "success" as const,
        colorClass: "text-emerald-700 dark:text-emerald-200",
      }
    }
    if (gaugeVal <= 40) {
      return {
        statusLabel: sentiment?.label || "Bearish / Negatif",
        badgeVariant: "destructive" as const,
        colorClass: "text-rose-700 dark:text-rose-200",
      }
    }
    return {
      statusLabel: sentiment?.label || "Netral / Terkonsolidasi",
      badgeVariant: "secondary" as const,
      colorClass: "text-neutral-700 dark:text-neutral-300",
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
    // LOUD policy: no gauge-derived invention (0.7 factors, floor 10).
    return {
      bullishPct: null as number | null,
      bearishPct: null as number | null,
      neutralPct: null as number | null,
      totalItems: items.length,
    }
  }, [sentiment?.items, gaugeVal, newsCount, socialCount])

  // LOUD policy: no invented 65/40 confidence scores.
  const confidencePct: number | null = sentiment?.confidence != null
    ? Math.round(sentiment.confidence * 100)
    : null

  const totalSources = (sentiment?.sources?.length || 0) + (sentiment?.items?.length || 0) + newsCount

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {/* Card 1: Gauge Index */}
      <Card className="border-neutral-200 bg-white shadow-2xs dark:border-neutral-800 dark:bg-[#111111]">
        <CardHeader className="p-4 pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs font-semibold text-neutral-700 dark:text-neutral-300">
              Indeks Sentimen Ritel
            </CardTitle>
            <Activity className="h-4 w-4 text-neutral-400" />
          </div>
          <CardDescription className="text-[11px] text-neutral-500 dark:text-neutral-400">
            Skor agregat 0 (Bear) s/d 100 (Bull)
          </CardDescription>
        </CardHeader>
        <CardContent className="p-4 pt-1 space-y-2">
          <div className="flex items-baseline gap-2">
            <span className={`text-3xl font-bold tracking-tight ${colorClass}`}>
              {sentiment?.gauge != null ? sentiment.gauge : "-"}
            </span>
            <span className="text-xs font-normal text-neutral-400">/ 100</span>
            <Badge variant={badgeVariant} className="ml-auto text-[10px]">
              {statusLabel}
            </Badge>
          </div>
          {/* Visual Gauge Bar */}
          <div className="h-2 w-full overflow-hidden rounded-full bg-neutral-100 dark:bg-neutral-800">
            <div
              className={`h-full transition-all duration-500 ${
                gaugeVal >= 60 ? "bg-emerald-600" : gaugeVal <= 40 ? "bg-rose-600" : "bg-neutral-700"
              }`}
              style={{ width: `${Math.max(5, Math.min(100, gaugeVal))}%` }}
            />
          </div>
          <p className="text-[11px] text-neutral-500 dark:text-neutral-400">
            {gaugeVal >= 60
              ? "Dominan akumulasi positif di kanal diskusi publik."
              : gaugeVal <= 40
              ? "Sentimen hati-hati / tekanan jual terpantau."
              : "Pergerakan narasi berimbang tanpa polarisasi ekstrem."}
          </p>
        </CardContent>
      </Card>

      {/* Card 2: Ratio Distribution */}
      <Card className="border-neutral-200 bg-white shadow-2xs dark:border-neutral-800 dark:bg-[#111111]">
        <CardHeader className="p-4 pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs font-semibold text-neutral-700 dark:text-neutral-300">
              Distribusi Polarisasi
            </CardTitle>
            <BarChart2 className="h-4 w-4 text-neutral-400" />
          </div>
          <CardDescription className="text-[11px] text-neutral-500 dark:text-neutral-400">
            Komposisi postingan & berita terkini
          </CardDescription>
        </CardHeader>
        <CardContent className="p-4 pt-1 space-y-2">
          <div className="grid grid-cols-3 gap-1 text-center">
            <div className="rounded border border-emerald-100 bg-emerald-50/50 p-1 dark:border-emerald-800 dark:bg-emerald-950/50">
              <div className="flex items-center justify-center gap-0.5 text-[10px] font-medium text-emerald-700 dark:text-emerald-200">
                <TrendingUp className="h-3 w-3" /> Positif
              </div>
              <div className="font-mono text-xs font-bold text-emerald-800 dark:text-emerald-200">
                {distribution.bullishPct == null ? "—" : `${distribution.bullishPct}%`}
              </div>
            </div>
            <div className="rounded border border-neutral-200 bg-neutral-50 p-1 dark:border-neutral-800 dark:bg-neutral-900">
              <div className="flex items-center justify-center gap-0.5 text-[10px] font-medium text-neutral-600 dark:text-neutral-400">
                <MinusCircle className="h-3 w-3" /> Netral
              </div>
              <div className="font-mono text-xs font-bold text-neutral-800 dark:text-neutral-200">
                {distribution.neutralPct == null ? "—" : `${distribution.neutralPct}%`}
              </div>
            </div>
            <div className="rounded border border-rose-100 bg-rose-50/50 p-1 dark:border-rose-800 dark:bg-rose-950/50">
              <div className="flex items-center justify-center gap-0.5 text-[10px] font-medium text-rose-700 dark:text-rose-200">
                <TrendingDown className="h-3 w-3" /> Negatif
              </div>
              <div className="font-mono text-xs font-bold text-rose-800 dark:text-rose-200">
                {distribution.bearishPct == null ? "—" : `${distribution.bearishPct}%`}
              </div>
            </div>
          </div>

          <div className="flex h-2 overflow-hidden rounded-full border border-neutral-200 dark:border-neutral-800">
            <div
              className="bg-emerald-600 transition-all"
              style={{ width: `${distribution.bullishPct ?? 0}%` }}
              title={`Positif: ${distribution.bullishPct ?? "—"}%`}
            />
            <div
              className="bg-neutral-400 transition-all dark:bg-neutral-600"
              style={{ width: `${distribution.neutralPct ?? 0}%` }}
              title={`Netral: ${distribution.neutralPct ?? "—"}%`}
            />
            <div
              className="bg-rose-500 transition-all"
              style={{ width: `${distribution.bearishPct ?? 0}%` }}
              title={`Negatif: ${distribution.bearishPct ?? "—"}%`}
            />
          </div>
          <p className="text-[11px] text-neutral-500 dark:text-neutral-400">
            Diolah dari data publik tanpa manipulasi bobot.
          </p>
        </CardContent>
      </Card>

      {/* Card 3: Confidence Score */}
      <Card className="border-neutral-200 bg-white shadow-2xs dark:border-neutral-800 dark:bg-[#111111]">
        <CardHeader className="p-4 pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs font-semibold text-neutral-700 dark:text-neutral-300">
              Tingkat Keyakinan
            </CardTitle>
            <ShieldCheck className="h-4 w-4 text-neutral-400" />
          </div>
          <CardDescription className="text-[11px] text-neutral-500 dark:text-neutral-400">
            Validitas sampel & kepadatan bukti
          </CardDescription>
        </CardHeader>
        <CardContent className="p-4 pt-1 space-y-2">
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-bold font-mono tracking-tight text-neutral-900 dark:text-neutral-100">
              {confidencePct == null ? "—" : `${confidencePct}%`}
            </span>
            <Badge variant="outline" className="text-[10px] font-medium text-neutral-700 dark:text-neutral-300">
              {confidencePct == null ? "Menunggu data" : confidencePct >= 70 ? "Kerapatan Tinggi" : confidencePct >= 50 ? "Sampel Cukup" : "Sampel Awal"}
            </Badge>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-neutral-100 dark:bg-neutral-800">
            <div
              className="h-full bg-neutral-800 transition-all"
              style={{ width: `${confidencePct ?? 0}%` }}
            />
          </div>
          <p className="text-[11px] text-neutral-500 dark:text-neutral-400">
            Pelacakan algoritma NLP berbasis kata kunci kontekstual IDX.
          </p>
        </CardContent>
      </Card>

      {/* Card 4: Indexed Sources & Channels */}
      <Card className="border-neutral-200 bg-white shadow-2xs dark:border-neutral-800 dark:bg-[#111111]">
        <CardHeader className="p-4 pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs font-semibold text-neutral-700 dark:text-neutral-300">
              Cakupan Kanal & Sumber
            </CardTitle>
            <Globe2 className="h-4 w-4 text-neutral-400" />
          </div>
          <CardDescription className="text-[11px] text-neutral-500 dark:text-neutral-400">
            Stockbit, X, Reddit, Media Publik
          </CardDescription>
        </CardHeader>
        <CardContent className="p-4 pt-1 space-y-2">
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-bold font-mono tracking-tight text-neutral-900 dark:text-neutral-100">
              {totalSources > 0 ? totalSources : "Siaga"}
            </span>
            <span className="text-xs text-neutral-500 dark:text-neutral-400">entri terdeteksi</span>
          </div>
          <div className="flex flex-wrap gap-1">
            <span className="rounded bg-neutral-100 px-1.5 py-0.5 text-[10px] font-medium text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">
              Stockbit
            </span>
            <span className="rounded bg-neutral-100 px-1.5 py-0.5 text-[10px] font-medium text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">
              X / Twitter
            </span>
            <span className="rounded bg-neutral-100 px-1.5 py-0.5 text-[10px] font-medium text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">
              Media Berita
            </span>
          </div>
          <p className="text-[11px] text-neutral-500 dark:text-neutral-400">
            Data diperbarui berkala via News & Social Harvester.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
