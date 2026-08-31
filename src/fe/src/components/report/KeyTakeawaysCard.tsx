import type { InstitutionalEquityReport } from "@/lib/types"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Zap, PieChart, ShieldCheck } from "lucide-react"

interface KeyTakeawaysCardProps {
  report: InstitutionalEquityReport
}

export function KeyTakeawaysCard({ report }: KeyTakeawaysCardProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* 3 Key Takeaways Highlights */}
      <Card className="lg:col-span-2 border-[#262d3a] bg-[#111317]">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-semibold flex items-center gap-2 text-amber-300">
              <Zap className="h-4 w-4 text-amber-400" />
              <span>Investment Thesis & Core Takeaways</span>
            </CardTitle>
            <Badge variant="outline" className="font-mono text-[10px]">
              AUDITED TAKEAWAYS
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3 pt-2">
          {report.keyTakeaways.map((item, idx) => (
            <div
              key={idx}
              className="flex items-start gap-3 p-3 rounded-lg bg-[#161a22] border border-[#212734]"
            >
              <div className="h-6 w-6 rounded-full bg-amber-500/10 border border-amber-500/30 flex items-center justify-center font-mono font-bold text-xs text-amber-400 shrink-0 mt-0.5">
                {idx + 1}
              </div>
              <div className="space-y-1">
                <div className="text-xs font-semibold text-slate-100 font-sans">
                  {item.bullet}
                </div>
                <div className="text-[11px] text-slate-400 leading-relaxed font-sans">
                  <span className="text-amber-400/90 font-medium">Strategic Impact:</span> {item.implication}
                </div>
              </div>
            </div>
          ))}

          {/* Quantified Catalyst Box (if available) */}
          {report.executiveThesis.catalystQuantified && (
            <div className="p-3 rounded-lg bg-gradient-to-r from-amber-500/10 via-[#181d26] to-[#161a22] border border-amber-500/30">
              <div className="flex items-center justify-between text-xs font-mono font-bold text-amber-300 mb-1">
                <span className="flex items-center gap-1.5">
                  <Zap className="h-3.5 w-3.5 text-amber-400" />
                  <span>QUANTIFIED CATALYST EVENT: {report.executiveThesis.catalystQuantified.catalystName}</span>
                </span>
                <span className="text-[10px] text-slate-400 font-normal">
                  {report.executiveThesis.catalystQuantified.effectiveDate}
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] mt-2 font-sans">
                <div className="bg-[#12151b] p-2 rounded border border-[#222836]">
                  <span className="text-slate-400 block text-[10px] uppercase font-mono">Operational Driver</span>
                  <span className="text-slate-200">{report.executiveThesis.catalystQuantified.operationalImpact}</span>
                </div>
                <div className="bg-[#12151b] p-2 rounded border border-[#222836]">
                  <span className="text-amber-400 block text-[10px] uppercase font-mono">Financial Run-Rate Impact</span>
                  <span className="text-emerald-300 font-mono font-semibold">{report.executiveThesis.catalystQuantified.annualizedFinancialImpact}</span>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Shareholder Structure & ESG Scorecard */}
      <div className="space-y-4">
        {/* Shareholder Breakdown */}
        <Card className="border-[#262d3a] bg-[#111317]">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold flex items-center gap-2 text-slate-200">
              <PieChart className="h-3.5 w-3.5 text-amber-400" />
              <span>Shareholder Structure</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-2 space-y-2">
            {report.shareholders.map((sh, i) => (
              <div key={i} className="space-y-1">
                <div className="flex justify-between text-xs font-sans">
                  <span className="text-slate-300 text-[11px] line-clamp-1">{sh.name}</span>
                  <span className="font-mono font-bold text-amber-300">{sh.percentage}%</span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-[#1e2430] overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      sh.isControlling ? "bg-amber-400" : "bg-slate-500"
                    }`}
                    style={{ width: `${sh.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* ESG Matrix */}
        <Card className="border-[#262d3a] bg-[#111317]">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-xs font-semibold flex items-center gap-2 text-slate-200">
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
                <span>ESG Disclosure Rating</span>
              </CardTitle>
              <Badge variant="outline" className="font-mono text-[10px] text-emerald-400 border-emerald-500/40">
                GRADE {report.esgScore.rating}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="pt-2">
            <div className="grid grid-cols-3 gap-2 text-center font-mono">
              <div className="p-2 rounded bg-[#161a22] border border-[#212734]">
                <div className="text-[10px] text-slate-400">ENV</div>
                <div className="text-sm font-bold text-emerald-400">{report.esgScore.environmental}</div>
              </div>
              <div className="p-2 rounded bg-[#161a22] border border-[#212734]">
                <div className="text-[10px] text-slate-400">SOC</div>
                <div className="text-sm font-bold text-blue-400">{report.esgScore.social}</div>
              </div>
              <div className="p-2 rounded bg-[#161a22] border border-[#212734]">
                <div className="text-[10px] text-slate-400">GOV</div>
                <div className="text-sm font-bold text-purple-400">{report.esgScore.governance}</div>
              </div>
            </div>
            <div className="mt-2 text-center text-[10px] font-mono text-slate-400">
              Composite Benchmark: <span className="text-slate-200 font-bold">{report.esgScore.composite} / 5.00</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
