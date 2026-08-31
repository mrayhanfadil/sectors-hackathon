import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { fetchSentiment, fetchReport } from "@/lib/api"
import { SentimentGauge } from "@/components/sentiment/SentimentGauge"
import { NarrativesList } from "@/components/sentiment/NarrativesList"
import { PlatformBreakdown } from "@/components/sentiment/PlatformBreakdown"
import { SentimentTimeline } from "@/components/sentiment/SentimentTimeline"
import { DivergenceAlertCard } from "@/components/sentiment/DivergenceAlertCard"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft } from "lucide-react"

export const Route = (createFileRoute as any)("/report/$ticker/sentiment")({
  component: ReportSentimentPage,
})

function ReportSentimentPage() {
  const { ticker } = Route.useParams()
  const tk = String(ticker).toUpperCase()

  const { data: sentiment, isLoading } = useQuery({
    queryKey: ["sentiment", tk],
    queryFn: () => fetchSentiment(tk),
  })

  const { data: report } = useQuery({
    queryKey: ["report", tk],
    queryFn: () => fetchReport(tk),
  })

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-3 font-mono">
        <div className="h-8 w-8 rounded-full border-2 border-amber-400 border-t-transparent animate-spin" />
        <div className="text-sm text-slate-400">
          Harvesting Social Sentiment from X, Reddit & Stockbit for {tk}...
        </div>
      </div>
    )
  }

  if (!sentiment) {
    return (
      <div className="p-8 text-center text-sm font-mono text-red-400">
        Failed to load sentiment for {tk}.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-xl border border-[#262c38] bg-[#111317] p-5 shadow-lg space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <a
              href={`/report/${tk}`}
              className="inline-flex items-center gap-1 text-xs font-mono text-amber-400 hover:underline"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Back to {tk} Report</span>
            </a>
            <span className="text-slate-500">•</span>
            <Badge variant="amber" className="text-[10px]">
              RETAIL SOCIAL SENTIMENT RADAR
            </Badge>
          </div>
          <div className="text-xs font-mono text-slate-400">
            Channels: X / Twitter • Reddit r/finansial • Stockbit Stream
          </div>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="font-mono text-2xl font-bold text-white">
              {tk} — Retail Social Sentiment & Narrative Tracking
            </h1>
            <p className="text-xs text-slate-300 font-sans mt-0.5">
              Real-time public discussion intelligence capturing social momentum and retail-institutional divergence.
            </p>
          </div>

          {report && (
            <div className="text-right font-mono text-xs p-2 rounded bg-[#161a22] border border-[#212734]">
              <span className="text-slate-400">Consensus TP: </span>
              <strong className="text-amber-300">IDR {report.targetPrice.toLocaleString("id-ID")}</strong>
            </div>
          )}
        </div>
      </div>

      {/* Divergence Alert */}
      <DivergenceAlertCard alert={sentiment.divergenceAlert} ticker={tk} />

      {/* Main Sentiment Grid: Gauge + Top Narratives */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <SentimentGauge
          score={sentiment.compositeScore}
          label={sentiment.sentimentLabel}
          velocity={sentiment.sentimentVelocity}
          mentionsCount={sentiment.mentionsCount30d}
          ticker={tk}
        />

        <div className="lg:col-span-2">
          <NarrativesList narratives={sentiment.topNarratives} ticker={tk} />
        </div>
      </div>

      {/* Cross-Platform Verbatim Posts */}
      <PlatformBreakdown platforms={sentiment.platformBreakdown} />

      {/* Historical Narrative Evolution Timeline */}
      <SentimentTimeline timeline={sentiment.timelineEvolution} ticker={tk} />
    </div>
  )
}
