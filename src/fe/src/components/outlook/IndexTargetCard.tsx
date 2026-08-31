import type { JciScenario } from "@/lib/types"
import { Card, CardHeader, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Target } from "lucide-react"

interface IndexTargetCardProps {
  scenarios: JciScenario[]
  methodologyNote: string
}

export function IndexTargetCard({ scenarios, methodologyNote }: IndexTargetCardProps) {
  return (
    <div className="space-y-3">
      {/* 3 Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {scenarios.map((sc) => {
          const isBase = sc.scenario === "Base"
          const isBull = sc.scenario === "Bull"
          // isBear

          return (
            <Card
              key={sc.scenario}
              className={`border transition-all ${
                isBase
                  ? "border-amber-500/50 bg-[#161a22] shadow-[0_0_20px_rgba(245,158,11,0.15)] ring-1 ring-amber-500/30"
                  : isBull
                  ? "border-emerald-500/30 bg-[#111317]"
                  : "border-red-500/30 bg-[#111317]"
              }`}
            >
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 font-mono text-xs font-bold uppercase tracking-wider">
                    <span
                      className={`h-2 w-2 rounded-full ${
                        isBase
                          ? "bg-amber-400"
                          : isBull
                          ? "bg-emerald-400"
                          : "bg-red-400"
                      }`}
                    />
                    <span
                      className={
                        isBase
                          ? "text-amber-300"
                          : isBull
                          ? "text-emerald-300"
                          : "text-red-300"
                      }
                    >
                      {sc.scenario} Case Scenario
                    </span>
                  </div>
                  {isBase && <Badge variant="amber">CONSENSUS</Badge>}
                </div>
                <div className="flex items-baseline gap-2 pt-1 font-mono">
                  <span className="text-3xl font-bold text-white">
                    {sc.targetIndex.toLocaleString("id-ID")}
                  </span>
                  <span
                    className={`text-xs font-semibold ${
                      sc.impliedUpsidePct >= 0
                        ? "text-emerald-400"
                        : "text-red-400"
                    }`}
                  >
                    {sc.impliedUpsidePct >= 0
                      ? `+${sc.impliedUpsidePct}%`
                      : `${sc.impliedUpsidePct}%`}{" "}
                    Upside
                  </span>
                </div>
              </CardHeader>
              <CardContent className="pt-2 space-y-3">
                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="p-2 rounded bg-[#12151b] border border-[#1f242e]">
                    <div className="text-[10px] text-slate-400">TARGET P/E</div>
                    <div className="font-bold text-slate-200 mt-0.5">{sc.peMultiple}x</div>
                  </div>
                  <div className="p-2 rounded bg-[#12151b] border border-[#1f242e]">
                    <div className="text-[10px] text-slate-400">EPS GROWTH</div>
                    <div className="font-bold text-slate-200 mt-0.5">{sc.epsGrowthPct}% YoY</div>
                  </div>
                </div>

                <p className="text-xs text-slate-300 font-sans leading-relaxed">
                  {sc.coreDrivers}
                </p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Methodology Callout */}
      <div className="p-3 rounded-lg bg-[#14171e] border border-[#222833] text-xs font-mono text-slate-400 flex items-center gap-2">
        <Target className="h-4 w-4 text-amber-400 shrink-0" />
        <span>{methodologyNote}</span>
      </div>
    </div>
  )
}
