import type { InstitutionalEquityReport } from "@/lib/types"
import { Badge } from "@/components/ui/badge"
import { 
  Calendar, 
  UserCheck, 
  Printer, 
  ShieldAlert, 
  Radio, 
  ArrowUpRight,
  TrendingUp
} from "lucide-react"

interface ReportHeaderProps {
  report: InstitutionalEquityReport
}

export function ReportHeader({ report }: ReportHeaderProps) {
  // isPositive
  const ratingVariant =
    report.recommendation === "BUY" || report.recommendation === "TRADING BUY"
      ? "buy"
      : report.recommendation === "SELL" || report.recommendation === "TRADING SELL"
      ? "sell"
      : "hold"

  return (
    <div className="rounded-xl border border-[#262c38] bg-[#111317] p-5 shadow-lg space-y-4">
      {/* Top Meta Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1f242e] pb-3 text-xs text-slate-400 font-mono">
        <div className="flex items-center gap-2">
          <Badge variant="amber">{report.sector}</Badge>
          <span className="text-slate-500">•</span>
          <span className="text-slate-300">{report.subsector}</span>
          <span className="text-slate-500">•</span>
          <Badge variant="outline" className="capitalize">{report.archetype.replace("-", " ")}</Badge>
        </div>

        <div className="flex items-center gap-4 text-[11px]">
          <span className="flex items-center gap-1">
            <Calendar className="h-3 w-3 text-amber-400" />
            <span>{report.coverageDate}</span>
          </span>
          <span className="flex items-center gap-1">
            <UserCheck className="h-3 w-3 text-amber-400" />
            <span>{report.leadAnalyst.name}</span>
          </span>
        </div>
      </div>

      {/* Main Stock Snapshot Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        {/* Company Title & Ticker */}
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <h1 className="font-mono text-3xl font-bold tracking-tight text-white">
              {report.ticker}
            </h1>
            <Badge variant={ratingVariant} className="text-xs px-3 py-1">
              {report.recommendation}
            </Badge>
            <Badge variant="outline" className="font-mono text-xs">
              ESG {report.esgScore.rating} ({report.esgScore.composite})
            </Badge>
          </div>
          <p className="font-serif text-lg text-slate-300 italic">
            {report.name}
          </p>
          <div className="flex flex-wrap gap-1.5 pt-1">
            {report.indexInclusion.map((idx) => (
              <span
                key={idx}
                className="inline-block rounded bg-[#181b22] px-2 py-0.5 font-mono text-[10px] text-slate-400 border border-[#222733]"
              >
                {idx}
              </span>
            ))}
          </div>
        </div>

        {/* Price & Valuation Snapshot Boxes */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Target Price Box */}
          <div className="rounded-lg bg-[#161a22] border border-amber-500/30 p-3.5 min-w-[150px]">
            <div className="text-[10px] font-mono uppercase tracking-wider text-amber-400/90 font-medium">
              Target Price (12M)
            </div>
            <div className="font-mono text-2xl font-bold text-amber-300">
              IDR {report.targetPrice.toLocaleString("id-ID")}
            </div>
            <div className="flex items-center gap-1 text-xs font-mono font-semibold text-emerald-400 mt-0.5">
              <ArrowUpRight className="h-3.5 w-3.5" />
              <span>+{report.upsidePct}% Upside</span>
              {report.previousTargetPrice && (
                <span className="text-[10px] text-slate-500 font-normal ml-1">
                  (Prev. {report.previousTargetPrice})
                </span>
              )}
            </div>
          </div>

          {/* Current Price Box */}
          <div className="rounded-lg bg-[#161a22] border border-[#232935] p-3.5 min-w-[130px]">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
              Current Price
            </div>
            <div className="font-mono text-xl font-bold text-white">
              IDR {report.currentPrice.toLocaleString("id-ID")}
            </div>
            <div className="text-[10px] font-mono text-slate-400 mt-0.5">
              MoS: {report.valuation.marginOfSafetyPct}%
            </div>
          </div>

          {/* Market Cap & Shares Box */}
          <div className="hidden sm:block rounded-lg bg-[#161a22] border border-[#232935] p-3.5 text-xs font-mono space-y-1">
            <div className="flex justify-between gap-4 text-slate-400">
              <span>Market Cap:</span>
              <span className="font-semibold text-slate-200">
                IDR {report.marketCapIdrTn} Tn
              </span>
            </div>
            <div className="flex justify-between gap-4 text-slate-400">
              <span>Shares Out:</span>
              <span className="font-semibold text-slate-200">
                {report.sharesOutstandingBn} Bn
              </span>
            </div>
            <div className="flex justify-between gap-4 text-slate-400">
              <span>Free Float:</span>
              <span className="font-semibold text-slate-200">
                {report.freeFloatPct}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Action Ribbons */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#1f242e] pt-3">
        <div className="flex flex-wrap items-center gap-2">
          <a
            href={`/report/${report.ticker}/challenge`}
            className="inline-flex items-center gap-1.5 rounded-md bg-[#1c222e] border border-red-500/30 px-3 py-1.5 text-xs font-medium text-red-300 hover:bg-red-500/20 transition-colors"
          >
            <ShieldAlert className="h-3.5 w-3.5 text-red-400" />
            <span>Adversarial Red Team Audit</span>
          </a>

          <a
            href={`/report/${report.ticker}/sentiment`}
            className="inline-flex items-center gap-1.5 rounded-md bg-[#1c222e] border border-purple-500/30 px-3 py-1.5 text-xs font-medium text-purple-300 hover:bg-purple-500/20 transition-colors"
          >
            <Radio className="h-3.5 w-3.5 text-purple-400" />
            <span>Retail Sentiment Radar</span>
          </a>

          <a
            href="/outlook"
            className="inline-flex items-center gap-1.5 rounded-md bg-[#1c222e] border border-[#293140] px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-[#252c3b] transition-colors"
          >
            <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
            <span>JCI 9,100 Strategy Context</span>
          </a>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => window.print()}
            className="inline-flex items-center gap-1.5 rounded-md border border-[#2a3140] bg-[#161a22] px-3 py-1.5 text-xs text-slate-300 hover:text-white hover:bg-[#202633] transition-colors cursor-pointer"
          >
            <Printer className="h-3.5 w-3.5 text-amber-400" />
            <span>Export / Print PDF</span>
          </button>
        </div>
      </div>
    </div>
  )
}
