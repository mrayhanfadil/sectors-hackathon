import type { RiskBucketItem } from "@/lib/types"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AlertTriangle, ShieldCheck } from "lucide-react"

interface RiskMatrixCardProps {
  risks: RiskBucketItem[]
  ticker: string
}

export function RiskMatrixCard({ risks }: RiskMatrixCardProps) {
  if (!risks || risks.length === 0) return null

  return (
    <Card className="border-[#262d3a] bg-[#111317]">
      <CardHeader className="pb-2 border-b border-[#1d222c]">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold flex items-center gap-2 text-slate-100">
            <AlertTriangle className="h-4 w-4 text-amber-400" />
            <span>Pillar-Specific Investment Risk Matrix & Mitigants</span>
          </CardTitle>
          <Badge variant="outline" className="font-mono text-[10px]">
            RISK ASSESSMENT
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-3 space-y-3">
        {risks.map((risk, idx) => {
          const isHigh = risk.severity === "HIGH"
          return (
            <div
              key={idx}
              className="p-3.5 rounded-lg bg-[#161a22] border border-[#212734] space-y-2 hover:border-slate-600 transition-colors"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Badge variant={isHigh ? "destructive" : "secondary"} className="text-[10px]">
                    {risk.category}
                  </Badge>
                  <span className="text-xs font-semibold text-slate-100 font-sans">
                    {risk.riskTitle}
                  </span>
                </div>
                <div className="flex items-center gap-2 font-mono text-[10px]">
                  <span className="text-slate-400">
                    Severity:{" "}
                    <span className={isHigh ? "text-red-400 font-bold" : "text-amber-300"}>
                      {risk.severity}
                    </span>
                  </span>
                  <span className="text-slate-500">•</span>
                  <span className="text-slate-400">Likelihood: {risk.likelihood}</span>
                </div>
              </div>

              <p className="text-xs text-slate-300 font-sans leading-relaxed">
                {risk.detail}
              </p>

              <div className="flex items-start gap-2 pt-1.5 border-t border-[#1d222c] text-xs font-sans text-emerald-300">
                <ShieldCheck className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-emerald-400">Mitigant & Cushion:</span>{" "}
                  <span className="text-slate-300">{risk.mitigant}</span>
                </div>
              </div>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
