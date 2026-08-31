import * as React from "react"
import { createFileRoute } from "@tanstack/react-router"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { fetchUniverse, fetchDebates, submitChallenge } from "@/lib/api"
import { DebateTranscript } from "@/components/challenge/DebateTranscript"
import { ChallengeInputForm } from "@/components/challenge/ChallengeInputForm"
import { DebateScorecard } from "@/components/challenge/DebateScorecard"
import { Badge } from "@/components/ui/badge"
import { ShieldAlert } from "lucide-react"

export const Route = (createFileRoute as any)("/challenge")({
  component: ChallengeHubPage,
})

const DEFAULT_TICKERS = ["MTEL", "RATU", "CDIA", "BBCA", "ADRO"]

function ChallengeHubPage() {
  const [selectedTicker, setSelectedTicker] = React.useState("MTEL")
  const queryClient = useQueryClient()

  const { data: universe } = useQuery({
    queryKey: ["universe"],
    queryFn: fetchUniverse,
  })

  const { data: debates, isLoading } = useQuery({
    queryKey: ["debates", selectedTicker],
    queryFn: () => fetchDebates(selectedTicker),
  })

  const challengeMutation = useMutation({
    mutationFn: (claim: string) => submitChallenge(selectedTicker, claim),
    onSuccess: (newDebate) => {
      queryClient.setQueryData(["debates", selectedTicker], (old: any) => [newDebate, ...(old || [])])
    },
  })

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-xl border border-[#262c38] bg-[#111317] p-6 shadow-lg space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Badge variant="destructive">RED TEAM ADVERSARIAL HUB</Badge>
            <Badge variant="outline">Anti-Sycophancy Critic Protocol</Badge>
          </div>
          <div className="text-xs font-mono text-slate-400">
            Rules: Must defend with audited evidence or concede
          </div>
        </div>

        <h1 className="font-serif text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Adversarial Red Team Audit & Challenge Interface
        </h1>

        <p className="text-xs sm:text-sm text-slate-300 font-sans leading-relaxed max-w-3xl">
          Stress-test equity research recommendations. The Red Team Challenger raises skeptical audits on WACC assumptions, growth targets, and operational metrics. The Lead Analyst Defender must cite verified calculations, filings, and news sources—or concede.
        </p>

        {/* Ticker Selector Buttons */}
        <div className="pt-2">
          <div className="text-[11px] font-mono text-slate-400 mb-1.5 uppercase font-medium">
            Select Ticker to Audit:
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

      {/* Scorecard */}
      {debates && debates.length > 0 && (
        <DebateScorecard scorecard={debates[0].scorecard} ticker={selectedTicker} />
      )}

      {/* Challenge Form */}
      <ChallengeInputForm
        ticker={selectedTicker}
        onSubmitChallenge={(claim) => challengeMutation.mutate(claim)}
        isSubmitting={challengeMutation.isPending}
      />

      {/* Debate Log */}
      <div className="space-y-4">
        <h2 className="font-mono text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 text-amber-400" />
          <span>Active Audit Transcripts for {selectedTicker} ({debates?.length || 0})</span>
        </h2>

        {isLoading ? (
          <div className="p-8 text-center text-sm font-mono text-slate-400">
            Loading debate logs...
          </div>
        ) : (
          debates?.map((debate) => (
            <DebateTranscript key={debate.debateId} debate={debate} />
          ))
        )}
      </div>
    </div>
  )
}
