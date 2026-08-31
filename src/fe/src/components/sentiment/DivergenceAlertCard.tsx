import { Card, CardContent } from "@/components/ui/card"
import { AlertCircle, TrendingUp, ShieldCheck } from "lucide-react"

interface DivergenceAlertProps {
  alert?: {
    isDivergent: boolean
    type: "RETAIL_EUPHORIA_OVERPRICED" | "CONTRARIAN_OPPORTUNITY" | "ALIGNED"
    description: string
  }
  ticker: string
}

export function DivergenceAlertCard({ alert }: DivergenceAlertProps) {
  if (!alert) return null

  const isOpportunity = alert.type === "CONTRARIAN_OPPORTUNITY"
  const isEuphoria = alert.type === "RETAIL_EUPHORIA_OVERPRICED"

  return (
    <Card
      className={`border transition-all ${
        isOpportunity
          ? "border-emerald-500/40 bg-[#121915]"
          : isEuphoria
          ? "border-red-500/40 bg-[#1a1416]"
          : "border-[#262d3a] bg-[#111317]"
      }`}
    >
      <CardContent className="p-4 flex items-start gap-3">
        {isOpportunity ? (
          <TrendingUp className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
        ) : isEuphoria ? (
          <AlertCircle className="h-5 w-5 text-red-400 shrink-0 mt-0.5" />
        ) : (
          <ShieldCheck className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
        )}

        <div className="space-y-1 text-xs">
          <div className="flex items-center gap-2">
            <span
              className={`font-mono font-bold uppercase text-[11px] ${
                isOpportunity
                  ? "text-emerald-300"
                  : isEuphoria
                  ? "text-red-300"
                  : "text-amber-300"
              }`}
            >
              {isOpportunity
                ? "Institutional vs Retail Divergence: Contrarian Value Opportunity"
                : isEuphoria
                ? "Retail Euphoria Warning: Diverging from DCF Fundamentals"
                : "Social Sentiment Aligned with Fundamental Consensus"}
            </span>
          </div>

          <p className="text-slate-300 font-sans leading-relaxed">
            {alert.description}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
