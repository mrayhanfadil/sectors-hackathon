import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { fetchReport } from "@/lib/api"
import { ReportHeader } from "@/components/report/ReportHeader"
import { KeyTakeawaysCard } from "@/components/report/KeyTakeawaysCard"
import { PriceVsJciChart } from "@/components/report/PriceVsJciChart"
import { ValuationSection } from "@/components/report/ValuationSection"
import { OperationalKpisCard } from "@/components/report/OperationalKpisCard"
import { FinancialStatementsTable } from "@/components/report/FinancialStatementsTable"
import { FinancialRatiosGrid } from "@/components/report/FinancialRatiosGrid"
import { PeerCompsTable } from "@/components/report/PeerCompsTable"
import { RiskMatrixCard } from "@/components/report/RiskMatrixCard"
import { DisclosuresSection } from "@/components/report/DisclosuresSection"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { BookOpen, AlertCircle } from "lucide-react"

export const Route = (createFileRoute as any)("/report/$ticker/")({ component: ReportDetailPage })

function ReportDetailPage() {
  const { ticker } = Route.useParams()
  const tk = String(ticker).toUpperCase()

  const { data: report, isLoading, error } = useQuery({
    queryKey: ["report", tk],
    queryFn: () => fetchReport(tk),
  })

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-3 font-mono">
        <div className="h-8 w-8 rounded-full border-2 border-amber-400 border-t-transparent animate-spin" />
        <div className="text-sm text-slate-400">
          Generating Institutional Research Report for <span className="text-amber-400 font-bold">{tk}</span>...
        </div>
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="p-8 rounded-xl border border-red-500/30 bg-[#161316] text-center space-y-3">
        <AlertCircle className="h-8 w-8 text-red-400 mx-auto" />
        <h2 className="text-lg font-bold text-white font-mono">Failed to load report for {tk}</h2>
        <p className="text-xs text-slate-400 font-sans">
          Could not find ticker in data/sectors.db or institutional library.
        </p>
        <a
          href="/"
          className="inline-flex items-center rounded-md bg-[#222834] px-4 py-2 text-xs font-mono text-slate-200 hover:bg-[#2d3545]"
        >
          ← Return to Terminal Universe
        </a>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 1. Institutional Report Cover & Header */}
      <ReportHeader report={report} />

      {/* 2. Key Takeaways, Catalysts & ESG Matrix */}
      <KeyTakeawaysCard report={report} />

      {/* 3. Executive Thesis Narrative & 4 Investment Pillars */}
      <Card className="border-[#262d3a] bg-[#111317]">
        <CardHeader className="pb-2 border-b border-[#1d222c]">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-semibold flex items-center gap-2 text-amber-300">
              <BookOpen className="h-4 w-4 text-amber-400" />
              <span>Executive Thesis & Strategic Pillars</span>
            </CardTitle>
            <Badge variant="outline" className="font-mono text-[10px]">
              THESIS PILLARS
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-3 space-y-4 font-sans text-xs">
          <p className="text-slate-300 leading-relaxed text-sm font-serif italic bg-[#161a22] p-3.5 rounded-lg border border-[#212734]">
            &ldquo;{report.executiveThesis.narrative}&rdquo;
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {report.executiveThesis.pillars.map((pil, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-[#161a22] border border-[#212734] space-y-2 flex flex-col justify-between"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="h-5 w-5 rounded bg-amber-500/10 border border-amber-500/30 flex items-center justify-center font-mono font-bold text-xs text-amber-400">
                      P{idx + 1}
                    </span>
                    <span className="font-bold text-slate-100 font-sans text-xs line-clamp-1">
                      {pil.title}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-300 leading-relaxed font-sans pt-1">
                    {pil.thesis}
                  </p>
                </div>

                <div className="p-2 rounded bg-[#101318] border border-[#232936] font-mono text-center">
                  <div className="text-[10px] text-slate-400 uppercase">{pil.metricLabel}</div>
                  <div className="text-base font-bold text-amber-300 mt-0.5">{pil.quantitativeMetric}</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 4. Comparative Price Chart vs IHSG */}
      <PriceVsJciChart history={report.priceVsJciHistory} ticker={report.ticker} />

      {/* 5. Adaptive Valuation Deep Dive */}
      <ValuationSection
        valuation={report.valuation}
        archetype={report.archetype}
        ticker={report.ticker}
      />

      {/* 6. Operational KPIs & Segment Mix */}
      <OperationalKpisCard
        kpis={report.operationalKpis}
        segmentMix={report.segmentMix}
        ticker={report.ticker}
      />

      {/* 7. 6-Year Financial Exhibits */}
      <FinancialStatementsTable
        incomeStatement={report.financialStatements.incomeStatement}
        balanceSheet={report.financialStatements.balanceSheet}
        cashFlowStatement={report.financialStatements.cashFlowStatement}
      />

      {/* 8. Financial Ratios Grid */}
      <FinancialRatiosGrid ratios={report.financialRatios} />

      {/* 9. Peer Group Comps Benchmarking */}
      <PeerCompsTable peers={report.peerComps} targetTicker={report.ticker} />

      {/* 10. Pillar-Specific Risk Matrix */}
      <RiskMatrixCard risks={report.risks} ticker={report.ticker} />

      {/* 11. Exhibit Provenance & Regulatory Disclosures */}
      <DisclosuresSection exhibits={report.exhibits} ticker={report.ticker} />
    </div>
  )
}
