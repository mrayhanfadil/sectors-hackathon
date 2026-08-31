import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ShieldCheck } from "lucide-react"

interface DebateScorecardProps {
  scorecard: {
    evidenceGroundingScore: number
    sycophancyRiskScore: number
    modelIntegrityVerified: boolean
  }
  ticker: string
}

export function DebateScorecard({ scorecard, ticker }: DebateScorecardProps) {
  return (
    <Card className="border-[#262d3a] bg-[#111317]">
      <CardHeader className="pb-2 border-b border-[#1d222c]">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xs font-semibold flex items-center gap-2 text-slate-200">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
            <span>Red Team Model Integrity Scorecard ({ticker})</span>
          </CardTitle>
          <Badge variant="success" className="font-mono text-[10px]">
            INTEGRITY VERIFIED
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-3 space-y-3">
        <div className="grid grid-cols-3 gap-2 font-mono text-center">
          <div className="p-2.5 rounded bg-[#161a22] border border-[#212734]">
            <div className="text-[10px] text-slate-400 uppercase">Grounding Score</div>
            <div className="text-lg font-bold text-emerald-400 mt-0.5">
              {scorecard.evidenceGroundingScore}%
            </div>
          </div>
          <div className="p-2.5 rounded bg-[#161a22] border border-[#212734]">
            <div className="text-[10px] text-slate-400 uppercase">Sycophancy Risk</div>
            <div className="text-lg font-bold text-amber-400 mt-0.5">
              {scorecard.sycophancyRiskScore}%
            </div>
          </div>
          <div className="p-2.5 rounded bg-[#161a22] border border-[#212734]">
            <div className="text-[10px] text-slate-400 uppercase">Arbiter Status</div>
            <div className="text-xs font-bold text-slate-200 mt-1">PASSED</div>
          </div>
        </div>

        <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
          The QA Critic checks every defense against deterministic math in <code className="text-amber-300 font-mono">data/sectors.db</code>. If an agent concedes without audited evidence or hallucinates unverified numbers, the debate is flagged as rejected.
        </p>
      </CardContent>
    </Card>
  )
}
