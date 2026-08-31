import * as React from "react"
import { createFileRoute } from "@tanstack/react-router"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { fetchDebates, submitChallenge, fetchReport } from "@/lib/api"
import { DebateTranscript } from "@/components/challenge/DebateTranscript"
import { ChallengeInputForm } from "@/components/challenge/ChallengeInputForm"
import { DebateScorecard } from "@/components/challenge/DebateScorecard"
import { Badge } from "@/components/ui/badge"
import { ShieldAlert, ArrowLeft } from "lucide-react"

export const Route = (createFileRoute as any)("/report/$ticker/challenge")({
  component: ReportChallengePage,
})

function ReportChallengePage() {
  const { ticker } = Route.useParams()
  const tk = String(ticker).toUpperCase()
  const queryClient = useQueryClient()

  const { data: report } = useQuery({
    queryKey: ["report", tk],
    queryFn: () => fetchReport(tk),
  })

  const { data: debates, isLoading } = useQuery({
    queryKey: ["debates", tk],
    queryFn: () => fetchDebates(tk),
  })

  const challengeMutation = useMutation({
    mutationFn: (claim: string) => submitChallenge(tk, claim),
    onSuccess: (newDebate) => {
      queryClient.setQueryData(["debates", tk], (old: any) => [newDebate, ...(old || [])])
    },
  })

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
            <Badge variant="destructive" className="text-[10px]">
              ADVERSARIAL RED TEAM AUDIT
            </Badge>
          </div>
          <div className="text-xs font-mono text-slate-400">
            Anti-Sycophancy Multi-Agent Defense Protocol
          </div>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="font-mono text-2xl font-bold text-white">
              {tk} — Adversarial Audit & Evidence Defense
            </h1>
            <p className="text-xs text-slate-300 font-sans mt-0.5">
              Every valuation claim must be defended with empirical calculations, SEC/IDX filings, or conceded.
            </p>
          </div>

          {report && (
            <div className="text-right font-mono text-xs p-2 rounded bg-[#161a22] border border-[#212734]">
              <span className="text-slate-400">Target Price: </span>
              <strong className="text-amber-300">IDR {report.targetPrice.toLocaleString("id-ID")}</strong>
              <span className="text-emerald-400 font-semibold ml-1.5">(+{report.upsidePct}%)</span>
            </div>
          )}
        </div>
      </div>

      {/* Model Integrity Scorecard */}
      {debates && debates.length > 0 && (
        <DebateScorecard scorecard={debates[0].scorecard} ticker={tk} />
      )}

      {/* Interactive Challenge Submitter */}
      <ChallengeInputForm
        ticker={tk}
        onSubmitChallenge={(claim) => challengeMutation.mutate(claim)}
        isSubmitting={challengeMutation.isPending}
      />

      {/* Active Debates List */}
      <div className="space-y-4">
        <h2 className="font-mono text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 text-amber-400" />
          <span>Audit Debate Transcripts ({debates?.length || 0})</span>
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
