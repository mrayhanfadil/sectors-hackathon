import type { OperationalKpiItem, SegmentMixItem } from "@/lib/types"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Activity, PieChart } from "lucide-react"

interface OperationalKpisCardProps {
  kpis: OperationalKpiItem[]
  segmentMix?: SegmentMixItem[]
  ticker: string
}

export function OperationalKpisCard({ kpis, segmentMix, ticker }: OperationalKpisCardProps) {
  return (
    <div className="space-y-4">
      {/* Operational KPIs Grid */}
      <Card className="border-[#262d3a] bg-[#111317]">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-semibold flex items-center gap-2 text-amber-300">
              <Activity className="h-4 w-4 text-amber-400" />
              <span>Operational KPIs & Asset Metrics (Hero Module for {ticker})</span>
            </CardTitle>
            <Badge variant="amber" className="font-mono text-[10px]">
              AUDITED SUBSECTOR KPIS
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {kpis.map((kpi, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-lg bg-[#161a22] border border-[#212734] space-y-1.5 hover:border-amber-500/30 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-medium text-slate-400 font-sans">
                    {kpi.label}
                  </span>
                  <span className="font-mono text-[10px] text-slate-500">{kpi.period}</span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="font-mono text-2xl font-bold text-white">
                    {kpi.currentValue}
                  </span>
                  <span className="font-mono text-xs text-amber-400 font-medium">
                    {kpi.unit}
                  </span>
                  {kpi.yoyDelta && (
                    <span className="ml-auto font-mono text-xs font-semibold text-emerald-400">
                      {kpi.yoyDelta}
                    </span>
                  )}
                </div>
                {kpi.industryContext && (
                  <p className="text-[11px] text-slate-400 leading-snug font-sans pt-0.5 border-t border-[#1d222c]">
                    {kpi.industryContext}
                  </p>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Segment Mix & Revenue Contribution (if available) */}
      {segmentMix && segmentMix.length > 0 && (
        <Card className="border-[#262d3a] bg-[#111317]">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold flex items-center gap-2 text-slate-200">
              <PieChart className="h-3.5 w-3.5 text-amber-400" />
              <span>Revenue Mix by Segment & Operational Margin</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-1">
            <div className="overflow-x-auto">
              <table className="w-full text-xs font-sans">
                <thead>
                  <tr className="border-b border-[#212631] text-slate-400 font-mono text-[11px] text-left">
                    <th className="pb-2 font-medium">Segment</th>
                    <th className="pb-2 font-medium text-right">Revenue (IDR Bn)</th>
                    <th className="pb-2 font-medium text-right">Revenue Share (%)</th>
                    <th className="pb-2 font-medium text-right">YoY Growth</th>
                    <th className="pb-2 font-medium text-right">EBITDA Margin (%)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1b2029]">
                  {segmentMix.map((seg, i) => (
                    <tr key={i} className="hover:bg-[#161a22]">
                      <td className="py-2.5 font-medium text-slate-100">{seg.segment}</td>
                      <td className="py-2.5 text-right font-mono text-slate-200">
                        {seg.revenueIdrBn.toLocaleString("id-ID")}
                      </td>
                      <td className="py-2.5 text-right font-mono text-amber-300 font-bold">
                        {seg.revenueSharePct}%
                      </td>
                      <td className="py-2.5 text-right font-mono text-emerald-400 font-medium">
                        {seg.growthYoY}
                      </td>
                      <td className="py-2.5 text-right font-mono text-slate-300">
                        {seg.marginEbitdaPct}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
