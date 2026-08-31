import type { TopPickStock } from "@/lib/types"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Sparkles, ArrowUpRight } from "lucide-react"

interface TopPicksGridProps {
  picks: TopPickStock[]
}

export function TopPicksGrid({ picks }: TopPicksGridProps) {
  return (
    <Card className="border-[#262d3a] bg-[#111317]">
      <CardHeader className="pb-2 border-b border-[#1d222c]">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold flex items-center gap-2 text-amber-300">
            <Sparkles className="h-4 w-4 text-amber-400" />
            <span>High-Conviction Stock Picks: Large Cap & SMID Ideas</span>
          </CardTitle>
          <Badge variant="amber" className="font-mono text-[10px]">
            CONVICTION PICKS
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-3">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {picks.map((pick) => (
            <a
              key={pick.ticker}
              href={`/report/${pick.ticker}`}
              className="p-3.5 rounded-lg bg-[#161a22] border border-[#212734] space-y-2 hover:border-amber-500/40 hover:bg-[#1a1f29] transition-all group"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-base font-bold text-white group-hover:text-amber-300 transition-colors">
                      {pick.ticker}
                    </span>
                    <Badge variant="outline" className="text-[10px]">
                      {pick.marketCapTier}
                    </Badge>
                  </div>
                  <div className="text-[11px] text-slate-400 line-clamp-1">{pick.name}</div>
                </div>
                <div className="text-right font-mono">
                  <div className="text-xs font-bold text-amber-300">
                    TP {pick.targetPrice.toLocaleString("id-ID")}
                  </div>
                  <div className="flex items-center justify-end text-[11px] font-semibold text-emerald-400">
                    <ArrowUpRight className="h-3 w-3" />
                    <span>+{pick.upsidePct}%</span>
                  </div>
                </div>
              </div>

              <div className="pt-1 text-xs text-slate-300 font-sans line-clamp-2 leading-relaxed">
                {pick.keyInvestmentThesis}
              </div>

              <div className="pt-1.5 border-t border-[#1d222c] flex items-center justify-between text-[10px] font-mono text-slate-400">
                <span>P/E Multiple: {pick.targetPeMultiple}x</span>
                <span className="text-amber-400 group-hover:underline">View Report →</span>
              </div>
            </a>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
