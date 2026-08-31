import * as React from "react"
import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { fetchUniverse, fetchSentiment } from "@/lib/api"
import { SentimentGauge } from "@/components/sentiment/SentimentGauge"
import { NarrativesList } from "@/components/sentiment/NarrativesList"
import { PlatformBreakdown } from "@/components/sentiment/PlatformBreakdown"
import { SentimentTimeline } from "@/components/sentiment/SentimentTimeline"
import { DivergenceAlertCard } from "@/components/sentiment/DivergenceAlertCard"
import { Badge } from "@/components/ui/badge"

export const Route = (createFileRoute as any)("/sentiment")({
  component: SentimentHubPage,
})

const DEFAULT_TICKERS = ["MTEL", "RATU", "CDIA", "BBCA", "ADRO"]

function SentimentHubPage() {
  const [selectedTicker, setSelectedTicker] = React.useState("MTEL")

  const { data: universe } = useQuery({
    queryKey: ["universe"],
    queryFn: fetchUniverse,
  })

  const { data: sentiment, isLoading } = useQuery({
    queryKey: ["sentiment", selectedTicker],
    queryFn: () => fetchSentiment(selectedTicker),
  })

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-xl border border-[#262c38] bg-[#111317] p-6 shadow-lg space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Badge variant="amber">RETAIL SOCIAL SENTIMENT HUB</Badge>
            <Badge variant="outline">0-100 Fear & Greed / Velocity Engine</Badge>
          </div>
          <div className="text-xs font-mono text-slate-400">
            Real-time crawling across X, Reddit, and Stockbit
          </div>
        </div>

        <h1 className="font-serif text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Retail Social Sentiment & Narrative Evolution
        </h1>

        <p className="text-xs sm:text-sm text-slate-300 font-sans leading-relaxed max-w-3xl">
          Track Indonesian retail investor sentiment polarity, trending thesis narratives, and identify contrarian divergence setups where institutional accumulation precedes retail hype.
        </p>

        {/* Ticker Selector Buttons */}
        <div className="pt-2">
          <div className="text-[11px] font-mono text-slate-400 mb-1.5 uppercase font-medium">
            Select Ticker for Sentiment Analysis:
          </div>
          <div className="flex flex-wrap gap-1.5 font-mono text-xs">
            {DEFAULT_TICKERS.map((t) => (
              <button
                key={t}
                onClick={() => setSelectedTicker(t)}
                className={`px-3 py-1.5 rounded transition-colors cursor-pointer ${
                  selectedTicker === t
                    ? "bg-amber-500 text-black font-bold"
                    : "bg-[#161a22] text-slate-300 hover:text-white border border-[#232936]"
                }`}
              >
                {t}
              </button>
            ))}

            <select
              value={selectedTicker}
              onChange={(e) => setSelectedTicker(e.target.value)}
              className="bg-[#161a22] text-slate-300 border border-[#232936] rounded px-2.5 py-1 text-xs font-mono outline-none"
            >
              <option value="" disabled>Other IDX Tickers...</option>
              {universe?.map((u) => (
                <option key={u.ticker} value={u.ticker}>
                  {u.ticker} — {u.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex flex-col items-center justify-center min-h-[40vh] space-y-3 font-mono">
          <div className="h-8 w-8 rounded-full border-2 border-amber-400 border-t-transparent animate-spin" />
          <div className="text-sm text-slate-400">
            Harvesting sentiment for {selectedTicker}...
          </div>
        </div>
      ) : sentiment ? (
        <div className="space-y-6">
          {/* Divergence Alert */}
          <DivergenceAlertCard alert={sentiment.divergenceAlert} ticker={selectedTicker} />

          {/* Main Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <SentimentGauge
              score={sentiment.compositeScore}
              label={sentiment.sentimentLabel}
              velocity={sentiment.sentimentVelocity}
              mentionsCount={sentiment.mentionsCount30d}
              ticker={selectedTicker}
            />

            <div className="lg:col-span-2">
              <NarrativesList
                narratives={sentiment.topNarratives}
                ticker={selectedTicker}
              />
            </div>
          </div>

          {/* Platform Breakdown */}
          <PlatformBreakdown platforms={sentiment.platformBreakdown} />

          {/* Timeline */}
          <SentimentTimeline
            timeline={sentiment.timelineEvolution}
            ticker={selectedTicker}
          />
        </div>
      ) : null}
    </div>
  )
}
