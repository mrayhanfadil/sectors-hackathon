import { createFileRoute, Link } from "@tanstack/react-router"
import {
  Database,
  Layers,
  ArrowRight,
  CheckCircle2,
  Calendar,
  TrendingUp,
  Newspaper,
  FileText,
  ShieldCheck,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

export const Route = (createFileRoute as any)("/")({ component: Home })

const DATA_SOURCES = [
  {
    endpoint: "GET /api/mock/corporate-actions",
    title: "Corporate Actions & Dividends",
    source: "Yahoo Finance (.JK) + IDX Keterbukaan Informasi",
    coverage: "Historical cash dividends, stock split ratios, and RUPS / AGM announcements.",
    icon: Calendar,
    color: "text-emerald-700",
    bg: "bg-emerald-50 border-emerald-200",
    snippet: `{\n  "dividend": [\n    {\n      "ex_date": "2024-03-22",\n      "amount_per_share": 270.0,\n      "currency": "IDR",\n      "type": "cash"\n    }\n  ],\n  "stock_split": [],\n  "agm": []\n}`,
  },
  {
    endpoint: "GET /api/mock/quarterly-financials",
    title: "Quarterly Financial Statements",
    source: "Yahoo Finance (.JK) Statement Engine",
    coverage: "Multi-quarter revenue, net income, operating cash flow, balance sheet items, and EBITDA.",
    icon: TrendingUp,
    color: "text-blue-700",
    bg: "bg-blue-50 border-blue-200",
    snippet: `{\n  "pagination": { "limit": 8, "total": 8 },\n  "data": [\n    {\n      "date": "2024-12-31",\n      "revenue": 27800000000000,\n      "earnings": 14200000000000,\n      "operating_cash_flow": 12000000000000\n    }\n  ]\n}`,
  },
  {
    endpoint: "GET /api/mock/news",
    title: "Sentiment-Tagged News Feed",
    source: "Tavily Search API + Curated Media Harvester",
    coverage: "Real-time news articles with automated keyword-based bullish/bearish/neutral sentiment classification.",
    icon: Newspaper,
    color: "text-amber-700",
    bg: "bg-amber-50 border-amber-200",
    snippet: `{\n  "pagination": { "limit": 30, "total": 5 },\n  "data": [\n    {\n      "title": "BBCA Raih Kinerja Positif FY25",\n      "dimension": {\n        "sentiment": "bullish",\n        "relevance": 0.88\n      }\n    }\n  ]\n}`,
  },
  {
    endpoint: "GET /api/mock/filings",
    title: "IDX Insider & Regulatory Filings",
    source: "IDX Keterbukaan Informasi Scraper",
    coverage: "Director and commissioner insider share transactions, institutional filings, and ownership changes.",
    icon: FileText,
    color: "text-slate-700",
    bg: "bg-slate-50 border-slate-200",
    snippet: `{\n  "pagination": { "limit": 30, "total": 12 },\n  "data": [\n    {\n      "title": "Laporan Perubahan Kepemilikan Saham",\n      "transaction_type": "buy",\n      "holder_type": "insider",\n      "symbol": "BBCA"\n    }\n  ]\n}`,
  },
]

function Home() {
  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
              Institutional-Grade Equity Report - untuk Retail
            </h1>
            <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-600">
              Deep 1 product kredibel (bukan 31 demo shallow). Benchmark RATU + CDIA + MTEL + JPM 2026 Outlook + 4 local. Multi-agent + deterministic math (DCF/DDM/SOTP/Blended/Bands/GGM). Frontend CSR Vite -&gt; Pages.dev (bukan Next SSR).
            </p>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <Badge>T03 - Frontend</Badge>
          <Badge variant="outline">React Vite + TS + TanStack Query/Router</Badge>
          <Badge variant="secondary">CSR - vite build -&gt; dist</Badge>
          <Badge variant="outline" className="border-emerald-300 text-emerald-800 bg-emerald-50">
            Sectors v2 Mock Layer Active
          </Badge>
        </div>

        <div className="mt-6 flex flex-wrap items-center gap-3 pt-4 border-t border-slate-100">
          <Link
            to="/mock-sectors/$ticker"
            params={{ ticker: "BBCA" }}
            className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-slate-800"
          >
            <Database className="h-4 w-4" />
            Explore Mock Data Hub
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
          <Link
            to="/agent"
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-50"
          >
            <Layers className="h-4 w-4" />
            ADK Live Stream
          </Link>
        </div>
      </div>

      {/* Locked Tech 6 Card */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold text-slate-900">
            Locked Tech 6
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm leading-relaxed text-slate-600">
          Frontend React+Vite+TS+TanStack Query/Router CSR only (no SSR).{" "}
          <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs text-slate-800">
            vite build -&gt; dist
          </code>{" "}
          static -&gt; Cloudflare Pages{" "}
          <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs text-slate-800">
            *.pages.dev
          </code>
          . Overkill Next.js dihindari: no SSR, bundle kecil, dev cepat.
        </CardContent>
      </Card>

      {/* Data Sources Section */}
      <section className="space-y-4 pt-2">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-slate-700" />
              <h2 className="text-base font-semibold tracking-tight text-slate-900">
                Upstream Data Sources & API Mirrors
              </h2>
            </div>
            <p className="text-xs text-slate-500">
              Mirroring /api/health upstream sources and Sectors v2 endpoints.
            </p>
          </div>

          <div className="flex items-center gap-1.5 self-start sm:self-auto rounded-full bg-emerald-50 border border-emerald-200 px-3 py-1 text-[11px] font-medium text-emerald-800">
            <ShieldCheck className="h-3.5 w-3.5" />
            Free public sources, no Sectors API credits consumed
          </div>
        </div>

        {/* 4 Cards Grid */}
        <div className="grid gap-4 sm:grid-cols-2">
          {DATA_SOURCES.map((ds, idx) => {
            const Icon = ds.icon
            return (
              <Card key={idx} className="overflow-hidden border-slate-200 shadow-xs flex flex-col justify-between">
                <CardHeader className="bg-slate-50/50 pb-3">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] font-semibold text-slate-700">
                      {ds.endpoint}
                    </span>
                    <div className={`p-1.5 rounded-md border ${ds.bg}`}>
                      <Icon className={`h-4 w-4 ${ds.color}`} />
                    </div>
                  </div>
                  <CardTitle className="text-sm font-semibold text-slate-900 mt-1">
                    {ds.title}
                  </CardTitle>
                  <CardDescription className="text-xs text-slate-600 font-medium">
                    Upstream: {ds.source}
                  </CardDescription>
                </CardHeader>

                <CardContent className="p-4 space-y-3 flex-1 flex flex-col justify-between">
                  <p className="text-xs leading-relaxed text-slate-600">
                    {ds.coverage}
                  </p>

                  <div className="space-y-1">
                    <span className="text-[10px] font-mono font-medium uppercase tracking-wider text-slate-400">
                      Response Sample
                    </span>
                    <pre className="overflow-x-auto rounded-md bg-slate-900 p-2.5 font-mono text-[10px] leading-relaxed text-slate-200">
                      <code>{ds.snippet}</code>
                    </pre>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </section>

      {/* Disclaimer Footer */}
      <p className="text-center text-xs text-slate-500 pt-4">
        Disclaimer: Produk ini adalah informasi, bukan saran investasi. Keputusan investasi sepenuhnya menjadi tanggung jawab pengguna.
      </p>
    </div>
  )
}
