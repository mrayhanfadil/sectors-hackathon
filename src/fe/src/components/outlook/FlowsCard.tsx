import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { DollarSign, ShieldAlert, Users, Landmark } from "lucide-react"

interface FlowsCardProps {
  flows: {
    foreignOwnershipPct: number
    foreignYtdNetFlowUsdBn: number
    retailAdtvSharePct: number
    danantaraDryPowderUsdBn: number
    msciFreeFloatRiskNotice: string
  }
}

export function FlowsCard({ flows }: FlowsCardProps) {
  return (
    <Card className="border-[#262d3a] bg-[#111317]">
      <CardHeader className="pb-2 border-b border-[#1d222c]">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold flex items-center gap-2 text-slate-100">
            <DollarSign className="h-4 w-4 text-amber-400" />
            <span>Market Flows, Sovereign Bid & Foreign Ownership Dynamics</span>
          </CardTitle>
          <Badge variant="outline" className="font-mono text-[10px]">
            FLOW INTELLIGENCE
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-3 space-y-4">
        {/* Flow Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
          <div className="p-3 rounded-lg bg-[#161a22] border border-[#212734] space-y-1">
            <div className="flex items-center gap-1 text-slate-400 text-[10px]">
              <Users className="h-3 w-3 text-amber-400" />
              <span>FOREIGN OWNERSHIP</span>
            </div>
            <div className="text-xl font-bold text-white">{flows.foreignOwnershipPct}%</div>
            <div className="text-[10px] text-amber-400 font-sans">Multi-decade underweight</div>
          </div>

          <div className="p-3 rounded-lg bg-[#161a22] border border-[#212734] space-y-1">
            <div className="flex items-center gap-1 text-slate-400 text-[10px]">
              <DollarSign className="h-3 w-3 text-red-400" />
              <span>FOREIGN YTD NET FLOW</span>
            </div>
            <div className="text-xl font-bold text-red-400">US$ {flows.foreignYtdNetFlowUsdBn} Bn</div>
            <div className="text-[10px] text-slate-400 font-sans">Outflow exhaustion near</div>
          </div>

          <div className="p-3 rounded-lg bg-[#161a22] border border-[#212734] space-y-1">
            <div className="flex items-center gap-1 text-slate-400 text-[10px]">
              <Users className="h-3 w-3 text-emerald-400" />
              <span>RETAIL ADTV SHARE</span>
            </div>
            <div className="text-xl font-bold text-emerald-400">{flows.retailAdtvSharePct}%</div>
            <div className="text-[10px] text-slate-400 font-sans">Domestic anchor liquidity</div>
          </div>

          <div className="p-3 rounded-lg bg-[#161a22] border border-[#212734] space-y-1">
            <div className="flex items-center gap-1 text-slate-400 text-[10px]">
              <Landmark className="h-3 w-3 text-purple-400" />
              <span>DANANTARA DRY POWDER</span>
            </div>
            <div className="text-xl font-bold text-purple-300">US$ {flows.danantaraDryPowderUsdBn} Bn</div>
            <div className="text-[10px] text-purple-400 font-sans">0.8% GDP Sovereign Bid</div>
          </div>
        </div>

        {/* MSCI Notice Callout */}
        <div className="p-3 rounded-lg bg-[#181a22] border border-amber-500/30 flex items-start gap-3">
          <ShieldAlert className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-xs font-sans text-slate-300 leading-relaxed">
            <span className="font-semibold text-amber-300 font-mono">MSCI Adjusted Free Float Risk:</span>{" "}
            {flows.msciFreeFloatRiskNotice}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
