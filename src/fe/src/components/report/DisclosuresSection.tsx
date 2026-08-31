import type { ExhibitProvenanceItem } from "@/lib/types"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { FileCheck } from "lucide-react"

interface DisclosuresSectionProps {
  exhibits: ExhibitProvenanceItem[]
  ticker: string
}

export function DisclosuresSection({ exhibits }: DisclosuresSectionProps) {
  return (
    <Card className="border-[#262d3a] bg-[#111317]">
      <CardHeader className="pb-2 border-b border-[#1d222c]">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xs font-semibold flex items-center gap-2 text-slate-200">
            <FileCheck className="h-3.5 w-3.5 text-amber-400" />
            <span>Exhibit Provenance & Regulatory Disclosures (OJK Standard)</span>
          </CardTitle>
          <Badge variant="outline" className="font-mono text-[10px]">
            PROVENANCE TRACEABILITY
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-3 space-y-4">
        {/* Exhibit Sources Table */}
        <div className="space-y-1.5">
          <div className="text-[11px] font-mono font-medium text-slate-300">
            Exhibit Data Provenance & Verified Sources
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 font-mono text-[11px]">
            {exhibits.map((ex) => (
              <div
                key={ex.exhibitNumber}
                className="p-2.5 rounded bg-[#161a22] border border-[#212734] space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="text-amber-400 font-bold">Exhibit {ex.exhibitNumber}</span>
                  <span className="text-slate-500 text-[10px]">{ex.dataTimestamp}</span>
                </div>
                <div className="text-slate-200 font-sans text-xs">{ex.title}</div>
                <div className="text-slate-400 text-[10px]">Source: {ex.sourceOrganization}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Rating Guide Box */}
        <div className="p-3 rounded-lg bg-[#14171e] border border-[#222733] space-y-2">
          <div className="text-[11px] font-mono font-bold text-slate-300">
            STOCK RATING DEFINITIONS (12-MONTH HORIZON)
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-center font-mono text-[10px]">
            <div className="p-1.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
              <span className="font-bold block">BUY</span>
              <span>&gt; +15% Upside</span>
            </div>
            <div className="p-1.5 rounded bg-emerald-500/5 border border-emerald-500/20 text-emerald-400">
              <span className="font-bold block">TRADING BUY</span>
              <span>+5% to +15%</span>
            </div>
            <div className="p-1.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-300">
              <span className="font-bold block">HOLD</span>
              <span>-10% to +15%</span>
            </div>
            <div className="p-1.5 rounded bg-red-500/5 border border-red-500/20 text-red-400">
              <span className="font-bold block">TRADING SELL</span>
              <span>-5% to -15%</span>
            </div>
            <div className="p-1.5 rounded bg-red-500/10 border border-red-500/30 text-red-300">
              <span className="font-bold block">SELL</span>
              <span>&lt; -15% Downside</span>
            </div>
          </div>
        </div>

        {/* Analyst Certification */}
        <div className="text-[11px] text-slate-400 font-sans leading-relaxed pt-1 border-t border-[#1d222c]">
          <span className="font-semibold text-slate-300">Analyst Certification:</span> The research analyst(s) primarily responsible for the preparation of this research report certify that the views expressed accurately reflect their personal deterministic models regarding the subject securities and issuers. No compensation was or will be directly or indirectly related to specific recommendations.
        </div>
      </CardContent>
    </Card>
  )
}
