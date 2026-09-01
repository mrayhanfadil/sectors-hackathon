import { useState } from "react"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import {
  Search,
  RefreshCw,
  TrendingUp,
  Database,
  Building2,
  Calendar,
  Newspaper,
  CheckCircle2,
  AlertCircle,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  DividendTimeline,
  QuarterlyTrendChart,
  NewsFeedCard,
} from "@/components/mock-sectors"
import {
  fetchDividends,
  fetchQuarterly,
  fetchNews,
} from "@/lib/api"

export const Route = (createFileRoute as any)("/mock-sectors/$ticker")({
  component: MockSectorsPage,
})

const PRESET_TICKERS = ["BBCA", "MTEL", "RATU", "CDIA", "ADRO"]

function MockSectorsPage() {
  const { ticker } = Route.useParams()
  const navigate = useNavigate()
  const currentTicker = (ticker ? String(ticker) : "BBCA").toUpperCase().trim()
  const [inputTicker, setInputTicker] = useState(currentTicker)

  // Fetch all 3 mock-sectors datasets
  const dividendsQuery = useQuery({
    queryKey: ["mock-dividends", currentTicker],
    queryFn: () => fetchDividends(currentTicker),
    staleTime: 60_000,
  })

  const quarterlyQuery = useQuery({
    queryKey: ["mock-quarterly", currentTicker],
    queryFn: () => fetchQuarterly(currentTicker, 8),
    staleTime: 60_000,
  })

  const newsQuery = useQuery({
    queryKey: ["mock-news", currentTicker],
    queryFn: () => fetchNews(currentTicker, 30),
    staleTime: 60_000,
  })

  const handleSearch = (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    const clean = inputTicker.toUpperCase().trim()
    if (clean && clean !== currentTicker) {
      navigate({ to: `/mock-sectors/${clean}` as any })
    }
  }

  const handlePresetClick = (tk: string) => {
    setInputTicker(tk)
    if (tk !== currentTicker) {
      navigate({ to: `/mock-sectors/${tk}` as any })
    }
  }

  const handleRefreshAll = () => {
    dividendsQuery.refetch()
    quarterlyQuery.refetch()
    newsQuery.refetch()
  }

  const isAnyLoading =
    dividendsQuery.isLoading || quarterlyQuery.isLoading || newsQuery.isLoading

  return (
    <div className="space-y-6">
      {/* Top Header & Ticker Control */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
                Sectors v2 Mock Intelligence Hub
              </h1>
              <Badge variant="outline" className="text-[11px] text-emerald-700 border-emerald-200 bg-emerald-50">
                0 Credits
              </Badge>
            </div>
            <p className="mt-1 max-w-2xl text-xs leading-relaxed text-slate-600 sm:text-sm">
              Visual exploration of institutional datasets mirroring Sectors v2 API schemas: corporate actions timeline, quarterly financial trajectory, and sentiment-classified news feeds. Strictly sourced from free public upstream data.
            </p>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={handleRefreshAll}
            disabled={isAnyLoading}
            className="self-start md:self-auto text-xs"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isAnyLoading ? "animate-spin" : ""}`} />
            Refresh Data
          </Button>
        </div>

        {/* Ticker Search Bar & Quick Ticker Pills */}
        <div className="mt-5 flex flex-col gap-3 pt-4 border-t border-slate-100 sm:flex-row sm:items-center sm:justify-between">
          <form onSubmit={handleSearch} className="flex items-center gap-2">
            <div className="relative">
              <Building2 className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={inputTicker}
                onChange={(e) => setInputTicker(e.target.value.toUpperCase())}
                placeholder="Ticker (e.g. BBCA)"
                maxLength={8}
                className="h-9 w-44 rounded-md border border-slate-300 bg-white pl-9 pr-3 text-xs font-mono font-semibold uppercase tracking-wider text-slate-900 placeholder:text-slate-400 focus:border-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900"
              />
            </div>
            <Button type="submit" size="sm" className="h-9 text-xs">
              <Search className="h-3.5 w-3.5" />
              Run Query
            </Button>
          </form>

          {/* Quick Presets */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs text-slate-600">
            <span className="text-[11px] font-medium text-slate-500">Presets:</span>
            {PRESET_TICKERS.map((tk) => {
              const isSelected = tk === currentTicker
              return (
                <button
                  key={tk}
                  type="button"
                  onClick={() => handlePresetClick(tk)}
                  className={`rounded-md px-2.5 py-1 text-xs font-mono font-medium transition-colors ${
                    isSelected
                      ? "bg-slate-900 text-white"
                      : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                  }`}
                >
                  {tk}
                </button>
              )
            })}
          </div>
        </div>

        {/* Upstream Data Provenance Tags */}
        <div className="mt-4 flex flex-wrap items-center gap-2 pt-3 border-t border-slate-100 text-[11px] text-slate-500">
          <span className="font-medium text-slate-700">Upstream Provenance:</span>
          <span className="inline-flex items-center gap-1 rounded bg-slate-50 border border-slate-200 px-2 py-0.5 font-mono">
            <CheckCircle2 className="h-3 w-3 text-emerald-600" />
            GET /api/mock/corporate-actions (yfinance + IDX)
          </span>
          <span className="inline-flex items-center gap-1 rounded bg-slate-50 border border-slate-200 px-2 py-0.5 font-mono">
            <CheckCircle2 className="h-3 w-3 text-emerald-600" />
            GET /api/mock/quarterly-financials (yfinance statements)
          </span>
          <span className="inline-flex items-center gap-1 rounded bg-slate-50 border border-slate-200 px-2 py-0.5 font-mono">
            <CheckCircle2 className="h-3 w-3 text-emerald-600" />
            GET /api/mock/news (Curated + Tavily)
          </span>
        </div>
      </div>

      {/* Panel 1: Dividend Timeline & Corporate Actions */}
      <section className="space-y-2">
        <div className="flex items-center gap-2 px-1">
          <Calendar className="h-4 w-4 text-slate-600" />
          <h2 className="text-sm font-semibold tracking-tight text-slate-800">
            Panel 1: Corporate Actions & Dividend History
          </h2>
        </div>
        <DividendTimeline
          ticker={currentTicker}
          data={dividendsQuery.data}
          isLoading={dividendsQuery.isLoading}
        />
      </section>

      {/* Section Separator */}
      <div className="border-t border-slate-200" />

      {/* Panel 2: Quarterly Trend Chart */}
      <section className="space-y-2">
        <div className="flex items-center gap-2 px-1">
          <TrendingUp className="h-4 w-4 text-slate-600" />
          <h2 className="text-sm font-semibold tracking-tight text-slate-800">
            Panel 2: Multi-Quarter Financial Trajectory
          </h2>
        </div>
        <QuarterlyTrendChart
          ticker={currentTicker}
          data={quarterlyQuery.data}
          isLoading={quarterlyQuery.isLoading}
        />
      </section>

      {/* Section Separator */}
      <div className="border-t border-slate-200" />

      {/* Panel 3: News Feed Card */}
      <section className="space-y-2">
        <div className="flex items-center gap-2 px-1">
          <Newspaper className="h-4 w-4 text-slate-600" />
          <h2 className="text-sm font-semibold tracking-tight text-slate-800">
            Panel 3: Sentiment-Tagged Public News Feed
          </h2>
        </div>
        <NewsFeedCard
          ticker={currentTicker}
          data={newsQuery.data}
          isLoading={newsQuery.isLoading}
        />
      </section>

      {/* Disclaimer Footer */}
      <p className="mt-8 text-center text-xs text-slate-500">
        Disclaimer: Produk ini adalah informasi, bukan saran investasi. Keputusan investasi sepenuhnya menjadi tanggung jawab pengguna.
      </p>
    </div>
  )
}
