import type { RedTeamDebateThread } from "@/lib/types"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ShieldAlert, FileText, CheckCircle2 } from "lucide-react"

interface DebateTranscriptProps {
  debate: RedTeamDebateThread
}

export function DebateTranscript({ debate }: DebateTranscriptProps) {
  return (
    <Card className="border-[#262d3a] bg-[#111317] space-y-3">
      <CardHeader className="pb-2 border-b border-[#1d222c]">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-red-400" />
              <CardTitle className="text-sm font-semibold text-slate-100 font-mono">
                {debate.debateId}: {debate.topic}
              </CardTitle>
            </div>
            <p className="text-xs text-slate-400 font-sans italic">
              Initial Audit Claim: &ldquo;{debate.initialChallengerClaim}&rdquo;
            </p>
          </div>

          <div className="flex items-center gap-2 font-mono text-xs">
            <Badge variant="success" className="text-[10px]">
              {debate.status}
            </Badge>
            <span className="text-slate-400">Grounding: {debate.scorecard.evidenceGroundingScore}%</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-2 space-y-4">
        {debate.turns.map((turn, i) => {
          const isChallenger = turn.role === "challenger"
          const isDefender = turn.role === "defender"
          // isArbiter

          return (
            <div
              key={i}
              className={`p-4 rounded-lg border transition-all ${
                isChallenger
                  ? "bg-[#18151a] border-red-500/30 text-slate-200"
                  : isDefender
                  ? "bg-[#141a18] border-emerald-500/30 text-slate-200"
                  : "bg-[#161a22] border-amber-500/40 text-amber-200"
              }`}
            >
              {/* Turn Header */}
              <div className="flex flex-wrap items-center justify-between gap-2 mb-2 pb-2 border-b border-[#212631]/60">
                <div className="flex items-center gap-2">
                  <Badge
                    variant={isChallenger ? "destructive" : isDefender ? "success" : "amber"}
                    className="text-[10px] font-mono font-bold"
                  >
                    {isChallenger
                      ? "RED TEAM CHALLENGER"
                      : isDefender
                      ? "LEAD DEFENDER (EVIDENCE)"
                      : "CRITIC ARBITER VERDICT"}
                  </Badge>
                  <span className="text-xs font-semibold text-slate-200 font-sans">
                    {turn.speakerName}
                  </span>
                </div>
                <span className="font-mono text-[10px] text-slate-500">{turn.timestamp}</span>
              </div>

              {/* Turn Body Message */}
              <div className="text-xs font-sans leading-relaxed space-y-2">
                <p>{turn.message}</p>
              </div>

              {/* Evidence Citations */}
              {turn.evidenceCitations && turn.evidenceCitations.length > 0 && (
                <div className="mt-3 pt-2 border-t border-[#202734] space-y-1.5 font-mono text-[11px]">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">
                    Cited Evidence & Audit Filings:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {turn.evidenceCitations.map((cit, cIdx) => (
                      <span
                        key={cIdx}
                        className="inline-flex items-center gap-1 rounded bg-[#101318] px-2 py-0.5 text-[10px] text-slate-300 border border-[#232936]"
                      >
                        <FileText className="h-3 w-3 text-amber-400" />
                        <span>{cit.reference}</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Arbiter Stamp */}
              {turn.verdict && (
                <div className="mt-3 pt-2 border-t border-amber-500/20 flex items-center gap-2 font-mono text-xs font-bold text-emerald-400">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  <span>AUDIT STATUS: {turn.verdict.replace(/_/g, " ")}</span>
                </div>
              )}
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
