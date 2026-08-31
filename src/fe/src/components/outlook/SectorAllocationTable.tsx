import type { SectorAllocationCall } from "@/lib/types"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Layers } from "lucide-react"

interface SectorAllocationTableProps {
  allocations: SectorAllocationCall[]
}

export function SectorAllocationTable({ allocations }: SectorAllocationTableProps) {
  return (
    <Card className="border-[#262d3a] bg-[#111317]">
      <CardHeader className="pb-2 border-b border-[#1d222c]">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold flex items-center gap-2 text-slate-100">
            <Layers className="h-4 w-4 text-amber-400" />
            <span>2026 Sector Allocation Framework & Strategic Positioning</span>
          </CardTitle>
          <Badge variant="outline" className="font-mono text-[10px]">
            JPM BENCHMARK ALLOCATION
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-2">
        <div className="overflow-x-auto">
          <table className="w-full text-xs font-sans">
            <thead>
              <tr className="border-b border-[#212631] text-slate-400 font-mono text-[11px] text-left">
                <th className="pb-2 font-medium">Sector</th>
                <th className="pb-2 font-medium text-center">Stance</th>
                <th className="pb-2 font-medium text-right">Weight (%)</th>
                <th className="pb-2 font-medium pl-4">High-Conviction Top Picks</th>
                <th className="pb-2 font-medium pl-4">Key Investment Catalysts</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#181c24]">
              {allocations.map((sec) => {
                const isOW = sec.stance === "OVERWEIGHT"
                const isUW = sec.stance === "UNDERWEIGHT"
                return (
                  <tr key={sec.sectorName} className="hover:bg-[#161a22]">
                    <td className="py-3 font-semibold text-slate-100">{sec.sectorName}</td>
                    <td className="py-3 text-center">
                      <Badge
                        variant={isOW ? "buy" : isUW ? "sell" : "hold"}
                        className="text-[10px] px-2 py-0.5"
                      >
                        {sec.stance}
                      </Badge>
                    </td>
                    <td className="py-3 text-right font-mono font-bold text-slate-200">
                      {sec.allocationWeightPct}%
                    </td>
                    <td className="py-3 pl-4">
                      <div className="flex flex-wrap gap-1.5 font-mono text-xs">
                        {sec.topPicks.map((pick) => (
                          <a
                            key={pick}
                            href={`/report/${pick}`}
                            className="rounded bg-[#1a1f29] px-2 py-0.5 text-amber-300 hover:bg-amber-500 hover:text-black transition-colors font-bold border border-[#262f3f]"
                          >
                            {pick}
                          </a>
                        ))}
                      </div>
                    </td>
                    <td className="py-3 pl-4 text-slate-300 text-xs leading-relaxed max-w-xs">
                      {sec.catalysts}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
