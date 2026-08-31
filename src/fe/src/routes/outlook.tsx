import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { fetchOutlook } from "@/lib/api"
import { IndexTargetCard } from "@/components/outlook/IndexTargetCard"
import { SectorAllocationTable } from "@/components/outlook/SectorAllocationTable"
import { TopPicksGrid } from "@/components/outlook/TopPicksGrid"
import { ThematicsAccordion } from "@/components/outlook/ThematicsAccordion"
import { FlowsCard } from "@/components/outlook/FlowsCard"
import { Badge } from "@/components/ui/badge"
// lucide icons

export const Route = (createFileRoute as any)("/outlook")({ component: OutlookPage })

function OutlookPage() {
  const { data: outlook, isLoading, error } = useQuery({
    queryKey: ["outlook"],
    queryFn: fetchOutlook,
  })

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-3 font-mono">
        <div className="h-8 w-8 rounded-full border-2 border-amber-400 border-t-transparent animate-spin" />
        <div className="text-sm text-slate-400">
          Loading 2026 Macro Strategy & Market Outlook...
        </div>
      </div>
    )
  }

  if (error || !outlook) {
    return (
      <div className="p-8 rounded-xl border border-red-500/30 bg-[#161316] text-center space-y-3">
        <h2 className="text-lg font-bold text-white font-mono">Failed to load Market Outlook</h2>
        <a href="/" className="text-xs font-mono text-amber-400 hover:underline">
          Return to Terminal Universe
        </a>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Strategy Header Banner */}
      <div className="rounded-xl border border-[#262c38] bg-gradient-to-r from-[#141820] via-[#111317] to-[#0c0e12] p-6 shadow-xl space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Badge variant="amber">MACRO STRATEGY BENCHMARK</Badge>
            <Badge variant="outline">J.P. Morgan 2026 Strategy Archetype (52p)</Badge>
          </div>
          <div className="text-xs font-mono text-slate-400">
            Dated: {outlook.reportDate} • Lead: Henry Wibowo et al.
          </div>
        </div>

        <h1 className="font-serif text-3xl font-bold text-white tracking-tight">
          {outlook.title}
        </h1>

        <p className="font-sans text-sm text-slate-300 max-w-3xl leading-relaxed">
          {outlook.themeTagline}. Comprehensive top-down strategy framework synthesizing index EPS growth, sovereign capital allocation via Danantara, and thematic sector allocations across Indonesian equities.
        </p>
      </div>

      {/* 1. Index Target Scenarios */}
      <IndexTargetCard
        scenarios={outlook.jciScenarios}
        methodologyNote={outlook.valuationMethodologyNote}
      />

      {/* 2. Sector Allocation Callout Table */}
      <SectorAllocationTable allocations={outlook.sectorAllocations} />

      {/* 3. Top Picks Grid */}
      <TopPicksGrid picks={outlook.topPicks} />

      {/* 4. 5 Structural Macro Thematics */}
      <ThematicsAccordion thematics={outlook.thematics} />

      {/* 5. Flows & Sovereign Bid */}
      <FlowsCard flows={outlook.marketFlows} />
    </div>
  )
}
