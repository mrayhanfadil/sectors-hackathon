import * as React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { ShieldAlert, Send, Sparkles } from "lucide-react"

interface ChallengeInputFormProps {
  ticker: string
  onSubmitChallenge: (claim: string) => void
  isSubmitting: boolean
}

export function ChallengeInputForm({ ticker, onSubmitChallenge, isSubmitting }: ChallengeInputFormProps) {
  const [claim, setClaim] = React.useState("")

  const suggestions: Record<string, string[]> = {
    MTEL: [
      "Is WACC 10.10% too low given IndoGov yield volatility?",
      "Can tenancy ratio sustain 1.57x after Indosat-Tri merger?",
      "Will fiber capex dilute corporate ROIC below 6%?",
    ],
    RATU: [
      "Why is RATU WACC 8.4% when oil upstream carries commodity risk?",
      "Will lifting cost remain $4.20/bbl if production declines?",
      "How is +28% net profit sustainable with -13% revenue?",
    ],
    CDIA: [
      "Is DDM payout 104% in FY28F realistic with ongoing capex?",
      "Why was FY26F EBITDA revised down -52.1%?",
      "How does Cilegon port sedimentation impact logistics margins?",
    ],
    BBCA: [
      "Will CASA 81.2% compress if Bank Indonesia cuts rates by 75 bps?",
      "Is GGM target 3.30x P/BV overly aggressive vs peer BMRI 1.85x?",
    ],
    ADRO: [
      "Is AADI US$6.1bn coal valuation too rich at $78/t coal ASP?",
      "Will special dividend distribution be delayed by EGMS approval?",
    ],
  }

  const promptChips = suggestions[ticker.toUpperCase()] || [
    `Are the cash flow growth projections for ${ticker} supported by sector historical metrics?`,
    `Is the cost of equity assumption conservative enough for current interest rates?`,
  ]

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!claim.trim() || isSubmitting) return
    onSubmitChallenge(claim.trim())
    setClaim("")
  }

  return (
    <Card className="border-[#262d3a] bg-[#111317]">
      <CardHeader className="pb-2 border-b border-[#1d222c]">
        <CardTitle className="text-sm font-semibold flex items-center gap-2 text-slate-100">
          <ShieldAlert className="h-4 w-4 text-red-400" />
          <span>Submit Adversarial Challenge to Research Lead (Anti-Sycophancy Engine)</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-3 space-y-3">
        {/* Suggestion Chips */}
        <div className="space-y-1.5">
          <div className="text-[11px] font-mono text-slate-400 flex items-center gap-1.5">
            <Sparkles className="h-3 w-3 text-amber-400" />
            <span>QUICK AUDIT CHALLENGES:</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {promptChips.map((chip, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setClaim(chip)}
                className="text-left rounded-md bg-[#161a22] hover:bg-[#1f242e] border border-[#232936] px-2.5 py-1 text-xs text-slate-300 hover:text-amber-300 transition-colors cursor-pointer"
              >
                &ldquo;{chip}&rdquo;
              </button>
            ))}
          </div>
        </div>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="space-y-2">
          <textarea
            value={claim}
            onChange={(e) => setClaim(e.target.value)}
            rows={3}
            placeholder={`Type your skeptical challenge against ${ticker} assumptions (e.g. WACC too low, revenue over-optimistic, peer comps inappropriate)...`}
            className="w-full rounded-md border border-[#282f3d] bg-[#14171f] p-3 text-xs text-slate-100 placeholder:text-slate-500 outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500 font-sans resize-none"
          />

          <div className="flex items-center justify-between">
            <div className="text-[11px] font-mono text-slate-500">
              Protocol: Defender must cite verified calculations or concede. No sycophancy.
            </div>
            <Button
              type="submit"
              disabled={!claim.trim() || isSubmitting}
              className="font-mono text-xs"
            >
              <Send className="h-3.5 w-3.5" />
              <span>{isSubmitting ? "Auditing Claims..." : "Execute Audit Challenge"}</span>
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
