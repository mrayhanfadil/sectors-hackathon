import type { FinancialRatiosGroup } from "@/lib/types"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { BarChart3 } from "lucide-react"

interface FinancialRatiosGridProps {
  ratios: FinancialRatiosGroup[]
}

export function FinancialRatiosGrid({ ratios }: FinancialRatiosGridProps) {
  if (!ratios || ratios.length === 0) return null

  // Extract all periods from the first ratio of the first group
  const periods = Object.keys(ratios[0].ratios[0].values)

  return (
    <Card className="border-[#262d3a] bg-[#111317]">
      <CardHeader className="pb-2 border-b border-[#1d222c]">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold flex items-center gap-2 text-slate-100">
            <BarChart3 className="h-4 w-4 text-amber-400" />
            <span>Key Financial & Operating Ratios (5-6 Year Trajectory)</span>
          </CardTitle>
          <Badge variant="outline" className="font-mono text-[10px]">
            PROFITABILITY • LEVERAGE • LIQUIDITY
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="pt-2 divide-y divide-[#1e2430]">
        {ratios.map((group, gIdx) => (
          <div key={gIdx} className="py-3 first:pt-1 last:pb-1">
            <div className="text-xs font-mono font-bold text-amber-300 mb-2 uppercase tracking-wide">
              {group.groupName}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs font-sans">
                <thead>
                  <tr className="border-b border-[#212631] text-slate-400 font-mono text-[11px] text-right">
                    <th className="pb-1.5 text-left font-medium">Metric</th>
                    <th className="pb-1.5 font-medium text-center">Unit</th>
                    {periods.map((p) => (
                      <th key={p} className="pb-1.5 font-medium">
                        {p}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#181c24] font-mono text-[11px]">
                  {group.ratios.map((r, rIdx) => (
                    <tr key={rIdx} className="hover:bg-[#161a22]">
                      <td className="py-2 text-left font-medium text-slate-200">{r.label}</td>
                      <td className="py-2 text-center text-slate-500 text-[10px]">{r.unit}</td>
                      {periods.map((p) => {
                        const val = r.values[p]
                        return (
                          <td key={p} className="py-2 text-right text-slate-300">
                            {val}
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
