import * as React from "react"
import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { fetchUniverse, type UniverseTickerItem } from "@/lib/api"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { 
  Sparkles, 
  Search, 
  ArrowUpRight, 
  CheckCircle2,
  Cpu,
  Database
} from "lucide-react"

export const Route = (createFileRoute as any)("/")({ component: HomePage })

const QUINTET_SHOWCASE = [
  {
    ticker: "MTEL",
    name: "Dayamitra Telekomunikasi Tbk.",
    archetype: "Recurring Infra (Tower/Fiber)",
    engine: "Blended 60% DCF + 40% EV/EBITDA",
    rating: "BUY",
    price: 460,
    target: 635,
    upside: "+38.0%",
    highlight: "Tenancy 1.57x, 59k km fiber, Telco merger +IDR 420bn catalyst",
    source: "Kiwoom Sekuritas 27 Aug 2026 (1.05MB)",
  },
  {
    ticker: "RATU",
    name: "Ratu Prabu Energi Tbk.",
    archetype: "Pure-Play Oil Upstream",
    engine: "DCF (WACC 8.4%) + EV/EBITDA 22.6x",
    rating: "BUY",
    price: 7150,
    target: 7880,
    upside: "+10.2%",
    highlight: "Cepu PSC 169k BOPD, bottom-line +28% despite -13% rev",
    source: "HP Sekuritas 7 Jan 2026 (819KB)",
  },
  {
    ticker: "CDIA",
    name: "Chandra Daya Investasi Tbk.",
    archetype: "Conglomerate SOTP (4-Pillar)",
    engine: "SOTP 4-Pillar + DCF 815 + DDM 810",
    rating: "BUY",
    price: 742,
    target: 815,
    upside: "+9.8%",
    highlight: "Energy 55%, Logistics +44.7%, 120MW power, 7 vessels",
    source: "BCA Sekuritas 23 Jun 2026 (1.58MB)",
  },
  {
    ticker: "BBCA",
    name: "Bank Central Asia Tbk.",
    archetype: "Commercial Banking Champion",
    engine: "Gordon Growth Model (GGM) Implied P/BV",
    rating: "BUY",
    price: 7890,
    target: 9600,
    upside: "+21.9%",
    highlight: "CASA 81.2%, NIM 5.8%, GGM P/BV 3.30x fallback",
    source: "Samuel Sekuritas 21 Oct 2025 (598KB)",
  },
  {
    ticker: "ADRO",
    name: "Adaro Energy Indonesia Tbk.",
    archetype: "SOTP Spin-Off Demerger",
    engine: "AADI SOTP US$6.1bn + Dual DCF",
    rating: "BUY",
    price: 2080,
    target: 2450,
    upside: "+17.8%",
    highlight: "Thermal coal spin-off + special dividend capital return",
    source: "BRIDS Research 18 Nov 2024 (1.8MB)",
  },
]

function HomePage() {
  const [search, setSearch] = React.useState("")
  const [selectedSector, setSelectedSector] = React.useState<string>("ALL")

  const { data: universe, isLoading } = useQuery({
    queryKey: ["universe"],
    queryFn: fetchUniverse,
  })

  const sectors = React.useMemo(() => {
    if (!universe) return []
    const set = new Set(universe.map((u) => u.sector))
    return ["ALL", ...Array.from(set)]
  }, [universe])

  const filteredUniverse = (universe || []).filter((item: UniverseTickerItem) => {
    const matchesSearch =
      item.ticker.toLowerCase().includes(search.toLowerCase()) ||
      item.name.toLowerCase().includes(search.toLowerCase()) ||
      item.industry.toLowerCase().includes(search.toLowerCase())
    const matchesSector = selectedSector === "ALL" || item.sector === selectedSector
    return matchesSearch && matchesSector
  })

  return (
    <div className="space-y-8">
      {/* Hero Institutional Header */}
      <div className="rounded-xl border border-[#262c38] bg-gradient-to-br from-[#13161c] via-[#111317] to-[#0c0e12] p-6 sm:p-8 shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-amber-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-4xl space-y-3 relative z-10">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="amber" className="text-xs px-2.5 py-0.5">
              SEKTORAL.ID MULTI-AGENT ENGINE
            </Badge>
            <Badge variant="secondary" className="text-xs">
              49 IDX Equities in data/sectors.db
            </Badge>
            <Badge variant="outline" className="text-xs">
              P0-P1 0 Credit Mode
            </Badge>
          </div>

          <h1 className="font-serif text-3xl sm:text-4xl font-bold tracking-tight text-white leading-tight">
            Institutional-Grade Equity Research for Indonesian Retail Investors
          </h1>

          <p className="text-sm sm:text-base leading-relaxed text-slate-300 font-sans">
            Calibrated against 15 institutional equity reports (J.P. Morgan, Kiwoom MTEL, BCA CDIA, HP RATU, Samuel, BRIDS). Every report features explicit deterministic WACC schedules, blended multi-engine valuations, operational KPIs per subsector, adversarial Red Team audits, and retail social sentiment gauges.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-2 font-mono text-xs text-slate-400">
            <div className="flex items-center gap-1.5 text-slate-200">
              <CheckCircle2 className="h-4 w-4 text-amber-400" />
              <span>Deterministic Math (No Hallucinations)</span>
            </div>
            <div className="flex items-center gap-1.5 text-slate-200">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              <span>Anti-Sycophancy Red Team Defense</span>
            </div>
            <div className="flex items-center gap-1.5 text-slate-200">
              <CheckCircle2 className="h-4 w-4 text-purple-400" />
              <span>X + Reddit + Stockbit Retail Radar</span>
            </div>
          </div>
        </div>
      </div>

      {/* 5 Benchmark Archetype Research Reports */}
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#212631] pb-2">
          <div className="space-y-0.5">
            <h2 className="font-mono text-lg font-bold text-slate-100 flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-amber-400" />
              <span>5 Benchmark Archetype Research Reports</span>
            </h2>
            <p className="text-xs text-slate-400 font-sans">
              Primary anchor templates calibrated to institutional standards
            </p>
          </div>
          <a
            href="/outlook"
            className="text-xs font-mono text-amber-400 hover:underline flex items-center gap-1"
          >
            <span>View 2026 Strategy Outlook (JCI 9,100)</span>
            <ArrowUpRight className="h-3 w-3" />
          </a>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {QUINTET_SHOWCASE.map((q) => (
            <Card
              key={q.ticker}
              className="border-[#262d3a] bg-[#111317] hover:border-amber-500/40 transition-all flex flex-col justify-between"
            >
              <CardHeader className="pb-3 border-b border-[#1b2029]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xl font-bold text-white">
                      {q.ticker}
                    </span>
                    <Badge variant="buy" className="text-[10px]">
                      {q.rating}
                    </Badge>
                  </div>
                  <div className="text-right font-mono">
                    <div className="text-xs font-bold text-amber-300">
                      TP {q.target.toLocaleString("id-ID")}
                    </div>
                    <div className="text-[11px] font-semibold text-emerald-400">
                      {q.upside}
                    </div>
                  </div>
                </div>
                <div className="text-xs font-serif text-slate-300 italic line-clamp-1 mt-1">
                  {q.name}
                </div>
                <div className="flex items-center gap-1.5 text-[11px] font-mono text-slate-400 mt-1">
                  <Badge variant="outline" className="text-[10px]">
                    {q.archetype}
                  </Badge>
                </div>
              </CardHeader>

              <CardContent className="pt-3 space-y-3 flex-1 flex flex-col justify-between">
                <div className="space-y-2 text-xs">
                  <div className="p-2 rounded bg-[#161a22] border border-[#212734] font-mono text-[11px] text-slate-300">
                    <span className="text-amber-400 font-bold">Engine:</span> {q.engine}
                  </div>
                  <p className="text-slate-300 font-sans text-xs leading-relaxed">
                    {q.highlight}
                  </p>
                  <div className="text-[10px] font-mono text-slate-500">
                    Ref: {q.source}
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-[#1b2029]">
                  <a
                    href={`/report/${q.ticker}`}
                    className="flex-1 inline-flex justify-center items-center h-8 rounded bg-amber-500 px-3 text-xs font-bold text-black hover:bg-amber-400 transition-colors"
                  >
                    Full Report
                  </a>
                  <a
                    href={`/report/${q.ticker}/challenge`}
                    className="inline-flex items-center h-8 rounded border border-red-500/40 bg-[#161a22] px-2.5 text-xs text-red-300 hover:bg-red-500/20 transition-colors"
                  >
                    Red Team
                  </a>
                  <a
                    href={`/report/${q.ticker}/sentiment`}
                    className="inline-flex items-center h-8 rounded border border-purple-500/40 bg-[#161a22] px-2.5 text-xs text-purple-300 hover:bg-purple-500/20 transition-colors"
                  >
                    Sentiment
                  </a>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* 49-Ticker Interactive Screener */}
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#212631] pb-2">
          <div className="space-y-0.5">
            <h2 className="font-mono text-lg font-bold text-slate-100 flex items-center gap-2">
              <Database className="h-4 w-4 text-amber-400" />
              <span>49-Ticker Indonesian Equities Screener (data/sectors.db)</span>
            </h2>
            <p className="text-xs text-slate-400 font-sans">
              Search and filter across all audited synthetic equities in the local database
            </p>
          </div>

          {/* Search Box */}
          <div className="relative min-w-[240px]">
            <Search className="h-3.5 w-3.5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search ticker, company, sector..."
              className="w-full rounded-md border border-[#262d3a] bg-[#14171f] pl-8 pr-3 py-1.5 text-xs text-slate-100 placeholder:text-slate-500 outline-none focus:border-amber-500"
            />
          </div>
        </div>

        {/* Sector Tabs */}
        <div className="flex flex-wrap gap-1.5 font-mono text-xs">
          {sectors.map((sec) => (
            <button
              key={sec}
              onClick={() => setSelectedSector(sec)}
              className={`px-3 py-1 rounded text-xs transition-colors cursor-pointer ${
                selectedSector === sec
                  ? "bg-amber-500 text-black font-bold"
                  : "bg-[#161a22] text-slate-400 hover:text-slate-200 border border-[#212734]"
              }`}
            >
              {sec}
            </button>
          ))}
        </div>

        {/* Screener Table */}
        <Card className="border-[#262d3a] bg-[#111317] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs font-sans">
              <thead>
                <tr className="border-b border-[#212631] text-slate-400 font-mono text-[11px] text-right bg-[#14171f]">
                  <th className="py-2.5 px-4 text-left font-medium">Ticker</th>
                  <th className="py-2.5 px-3 text-left font-medium">Company Name</th>
                  <th className="py-2.5 px-3 text-left font-medium">Sector</th>
                  <th className="py-2.5 px-3 font-medium">Last Price (IDR)</th>
                  <th className="py-2.5 px-3 font-medium">Daily Change</th>
                  <th className="py-2.5 px-3 font-medium">52W Range</th>
                  <th className="py-2.5 px-4 text-center font-medium">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#181c24] font-mono text-[11px]">
                {isLoading ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-500 font-sans">
                      Loading universe data from data/sectors.db...
                    </td>
                  </tr>
                ) : filteredUniverse.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-500 font-sans">
                      No tickers found matching filter criteria.
                    </td>
                  </tr>
                ) : (
                  filteredUniverse.map((item) => {
                    const isPos = item.changePct >= 0
                    return (
                      <tr key={item.ticker} className="hover:bg-[#161a22] transition-colors">
                        <td className="py-2.5 px-4 text-left font-bold">
                          <a
                            href={`/report/${item.ticker}`}
                            className="text-amber-300 hover:underline flex items-center gap-1.5"
                          >
                            <span>{item.ticker}</span>
                            {item.hasBenchmarkReport && (
                              <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
                            )}
                          </a>
                        </td>
                        <td className="py-2.5 px-3 text-left font-sans text-slate-200 line-clamp-1">
                          {item.name}
                        </td>
                        <td className="py-2.5 px-3 text-left text-slate-400">
                          <Badge variant="outline" className="text-[10px]">
                            {item.sector}
                          </Badge>
                        </td>
                        <td className="py-2.5 px-3 text-right font-bold text-white">
                          {item.lastPrice.toLocaleString("id-ID")}
                        </td>
                        <td
                          className={`py-2.5 px-3 text-right font-semibold ${
                            isPos ? "text-emerald-400" : "text-red-400"
                          }`}
                        >
                          {isPos ? `+${item.changePct}%` : `${item.changePct}%`}
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-400 text-[10px]">
                          {item.low52w.toLocaleString("id-ID")} – {item.high52w.toLocaleString("id-ID")}
                        </td>
                        <td className="py-2.5 px-4 text-center">
                          <a
                            href={`/report/${item.ticker}`}
                            className="inline-flex items-center gap-1 rounded bg-[#1f242e] hover:bg-amber-500 hover:text-black px-2.5 py-1 text-[10px] font-bold text-amber-300 transition-colors border border-[#2a3242]"
                          >
                            <span>Report</span>
                            <ArrowUpRight className="h-2.5 w-2.5" />
                          </a>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* Locked Tech Stack §6 Card */}
      <Card className="border-[#262d3a] bg-[#111317]">
        <CardHeader className="pb-2 border-b border-[#1d222c]">
          <CardTitle className="text-xs font-semibold flex items-center gap-2 text-slate-200">
            <Cpu className="h-3.5 w-3.5 text-amber-400" />
            <span>Architecture & Locked Tech Stack (§6)</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-3 text-xs text-slate-300 font-sans leading-relaxed space-y-2">
          <p>
            <strong className="text-white">Frontend (§6):</strong> React 19 + Vite 8 + TypeScript + TanStack Query + TanStack Router + Tailwind CSS v4. CSR only (no Next.js SSR overhead). Optimized for rapid static deployment to Cloudflare Pages and automated PDF export via Playwright.
          </p>
          <p>
            <strong className="text-white">Deterministic Data Layer:</strong> 49 IDX equities, 72,000+ daily price points, and operational KPIs seeded directly in <code className="text-amber-300 font-mono">data/sectors.db</code> SQLite. Zero API credit consumption in P0-P1 mode.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
