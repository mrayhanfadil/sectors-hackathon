import { useState, useMemo } from "react"
import {
  TrendingUp,
  TrendingDown,
  MinusCircle,
  AlertCircle,
  BarChart3,
  Layers,
  CircleDot,
  Check,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { QuarterlyFinancialsResponse, QuarterlyFinancialItem } from "@/lib/api"

interface QuarterlyTrendChartProps {
  ticker: string
  data?: QuarterlyFinancialsResponse | null
  isLoading?: boolean
}

type MetricKey = "revenue" | "earnings" | "operating_cash_flow"

interface MetricDef {
  key: MetricKey
  label: string
  shortLabel: string
  color: string
  strokeColor: string
  fillColor: string
  badgeVariant: "default" | "secondary" | "outline" | "success"
}

const METRIC_DEFS: MetricDef[] = [
  {
    key: "revenue",
    label: "Total Revenue",
    shortLabel: "Revenue",
    color: "#059669", // emerald-600
    strokeColor: "#059669",
    fillColor: "#d1fae5",
    badgeVariant: "success",
  },
  {
    key: "earnings",
    label: "Net Earnings",
    shortLabel: "Earnings",
    color: "#2563eb", // blue-600
    strokeColor: "#2563eb",
    fillColor: "#dbeafe",
    badgeVariant: "default",
  },
  {
    key: "operating_cash_flow",
    label: "Operating Cash Flow",
    shortLabel: "Op. Cash Flow",
    color: "#d97706", // amber-600
    strokeColor: "#d97706",
    fillColor: "#fef3c7",
    badgeVariant: "secondary",
  },
]

function formatCompactIDR(val: number | null | undefined): string {
  if (val == null || Number.isNaN(Number(val))) return "N/A"
  const abs = Math.abs(val)
  const sign = val < 0 ? "-" : ""
  if (abs >= 1e12) {
    return `${sign}Rp ${(abs / 1e12).toFixed(2)} T`
  }
  if (abs >= 1e9) {
    return `${sign}Rp ${(abs / 1e9).toFixed(2)} B`
  }
  if (abs >= 1e6) {
    return `${sign}Rp ${(abs / 1e6).toFixed(1)} M`
  }
  return `${sign}Rp ${val.toLocaleString("id-ID")}`
}

function formatQuarterLabel(dateStr: string): string {
  if (!dateStr) return "-"
  const d = new Date(dateStr)
  if (Number.isNaN(d.getTime())) return dateStr
  const month = d.getMonth() + 1
  const q = Math.ceil(month / 3)
  const y = String(d.getFullYear()).slice(-2)
  return `Q${q}'${y}`
}

export function QuarterlyTrendChart({ ticker, data, isLoading }: QuarterlyTrendChartProps) {
  const [visibleMetrics, setVisibleMetrics] = useState<Record<MetricKey, boolean>>({
    revenue: true,
    earnings: true,
    operating_cash_flow: true,
  })
  const [hoveredQuarterIndex, setHoveredQuarterIndex] = useState<number | null>(null)
  const [viewMode, setViewMode] = useState<"chart" | "table">("chart")

  const quarters = useMemo(() => {
    if (!data?.data || !Array.isArray(data.data)) return []
    // Reverse or sort chronologically (oldest -> newest) for left-to-right timeline
    return [...data.data].sort((a, b) => {
      const da = new Date(a.date).getTime()
      const db = new Date(b.date).getTime()
      return da - db
    })
  }, [data])

  const toggleMetric = (key: MetricKey) => {
    setVisibleMetrics((prev) => {
      const activeCount = Object.values(prev).filter(Boolean).length
      if (activeCount === 1 && prev[key]) {
        // Prevent disabling all metrics
        return prev
      }
      return { ...prev, [key]: !prev[key] }
    })
  }

  // SVG Chart Geometry
  const chartWidth = 740
  const chartHeight = 250
  const padLeft = 85
  const padRight = 35
  const padTop = 30
  const padBottom = 50

  const { chartData, yTicks, minVal, maxVal } = useMemo(() => {
    if (quarters.length === 0) {
      return { chartData: [], yTicks: [], minVal: 0, maxVal: 1 }
    }

    const allValues: number[] = []
    quarters.forEach((q) => {
      if (visibleMetrics.revenue && typeof q.revenue === "number") allValues.push(q.revenue)
      if (visibleMetrics.earnings && typeof q.earnings === "number") allValues.push(q.earnings)
      if (visibleMetrics.operating_cash_flow && typeof q.operating_cash_flow === "number") {
        allValues.push(q.operating_cash_flow)
      }
    })

    const rawMax = allValues.length > 0 ? Math.max(...allValues) : 100
    const rawMin = allValues.length > 0 ? Math.min(...allValues) : 0

    // Ensure 0 is represented and add head-room
    const max = Math.max(rawMax * 1.15, 100)
    const min = rawMin < 0 ? rawMin * 1.15 : 0
    const range = max - min || 1

    const innerW = chartWidth - padLeft - padRight
    const innerH = chartHeight - padTop - padBottom

    const points = quarters.map((q, idx) => {
      const x =
        quarters.length === 1
          ? padLeft + innerW / 2
          : padLeft + (idx / (quarters.length - 1)) * innerW

      const getPointsForVal = (val: number | null | undefined) => {
        if (typeof val !== "number" || Number.isNaN(val)) return null
        return padTop + innerH - ((val - min) / range) * innerH
      }

      return {
        quarter: q,
        date: q.date,
        label: formatQuarterLabel(q.date),
        x,
        yRevenue: getPointsForVal(q.revenue),
        yEarnings: getPointsForVal(q.earnings),
        yOcf: getPointsForVal(q.operating_cash_flow),
      }
    })

    const ticks = [
      { val: max, y: padTop },
      { val: min + range * 0.66, y: padTop + innerH * 0.33 },
      { val: min + range * 0.33, y: padTop + innerH * 0.66 },
      { val: min, y: padTop + innerH },
    ]

    return { chartData: points, yTicks: ticks, minVal: min, maxVal: max }
  }, [quarters, visibleMetrics])

  const activeQuarter: QuarterlyFinancialItem | null =
    hoveredQuarterIndex !== null && quarters[hoveredQuarterIndex]
      ? quarters[hoveredQuarterIndex]
      : quarters.length > 0
      ? quarters[quarters.length - 1]
      : null

  // Latest QoQ / YoY growth calculations
  const summaryGrowth = useMemo(() => {
    if (quarters.length < 2) return null
    const latest = quarters[quarters.length - 1]
    const prev = quarters[quarters.length - 2]

    const getGrowth = (cur: number | null | undefined, p: number | null | undefined) => {
      if (typeof cur !== "number" || typeof p !== "number" || p === 0) return null
      const pct = ((cur - p) / Math.abs(p)) * 100
      return pct
    }

    return {
      revenueQoQ: getGrowth(latest.revenue, prev.revenue),
      earningsQoQ: getGrowth(latest.earnings, prev.earnings),
      latestDate: latest.date,
      prevDate: prev.date,
    }
  }, [quarters])

  return (
    <Card className="overflow-hidden border-slate-200 shadow-sm">
      <CardHeader className="border-b border-slate-100 bg-slate-50/50 pb-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-base font-semibold text-slate-900">
                Quarterly Financial Trend
              </CardTitle>
              <Badge variant="outline" className="font-mono text-[11px] text-slate-700">
                {ticker}
              </Badge>
            </div>
            <CardDescription className="mt-1 text-xs text-slate-500">
              Multi-quarter income statement & cash flow trend lines from Sectors quarterly financials
            </CardDescription>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Metric Toggles */}
            <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white p-1">
              {METRIC_DEFS.map((m) => {
                const active = visibleMetrics[m.key]
                return (
                  <button
                    key={m.key}
                    type="button"
                    onClick={() => toggleMetric(m.key)}
                    className={`inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-[11px] font-medium transition-all ${
                      active
                        ? "bg-slate-900 text-white shadow-xs"
                        : "bg-transparent text-slate-500 hover:bg-slate-100 hover:text-slate-800"
                    }`}
                  >
                    <span
                      className="h-2 w-2 rounded-full"
                      style={{ backgroundColor: active ? "#ffffff" : m.color }}
                    />
                    {m.shortLabel}
                  </button>
                )
              })}
            </div>

            {/* View Mode Toggle */}
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => setViewMode("chart")}
                className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                  viewMode === "chart"
                    ? "bg-slate-900 text-white"
                    : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
                }`}
              >
                Chart
              </button>
              <button
                type="button"
                onClick={() => setViewMode("table")}
                className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                  viewMode === "table"
                    ? "bg-slate-900 text-white"
                    : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
                }`}
              >
                Table
              </button>
            </div>
          </div>
        </div>

        {/* Quick Highlights Strip */}
        {quarters.length > 0 && (
          <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
            <div className="rounded-lg border border-slate-200/80 bg-white p-2.5">
              <span className="text-[11px] font-medium text-slate-500">Coverage Span</span>
              <div className="mt-0.5 text-sm font-semibold text-slate-900">
                {quarters.length} Quarters ({formatQuarterLabel(quarters[0]?.date)} : {formatQuarterLabel(quarters[quarters.length - 1]?.date)})
              </div>
            </div>

            <div className="rounded-lg border border-slate-200/80 bg-white p-2.5">
              <span className="text-[11px] font-medium text-slate-500">Latest Revenue</span>
              <div className="mt-0.5 text-sm font-semibold text-emerald-700">
                {formatCompactIDR(quarters[quarters.length - 1]?.revenue)}
              </div>
            </div>

            <div className="rounded-lg border border-slate-200/80 bg-white p-2.5">
              <span className="text-[11px] font-medium text-slate-500">Latest Earnings</span>
              <div className="mt-0.5 text-sm font-semibold text-blue-700">
                {formatCompactIDR(quarters[quarters.length - 1]?.earnings)}
              </div>
            </div>

            <div className="rounded-lg border border-slate-200/80 bg-white p-2.5">
              <span className="text-[11px] font-medium text-slate-500">Revenue QoQ</span>
              <div className="mt-0.5 flex items-center gap-1 text-sm font-semibold">
                {summaryGrowth?.revenueQoQ != null ? (
                  <>
                    {summaryGrowth.revenueQoQ >= 0 ? (
                      <span className="text-emerald-700 inline-flex items-center gap-0.5">
                        <TrendingUp className="h-3.5 w-3.5" />
                        +{summaryGrowth.revenueQoQ.toFixed(1)}%
                      </span>
                    ) : (
                      <span className="text-rose-700 inline-flex items-center gap-0.5">
                        <TrendingDown className="h-3.5 w-3.5" />
                        {summaryGrowth.revenueQoQ.toFixed(1)}%
                      </span>
                    )}
                  </>
                ) : (
                  <span className="text-slate-500">N/A</span>
                )}
              </div>
            </div>
          </div>
        )}
      </CardHeader>

      <CardContent className="p-4 sm:p-6">
        {isLoading ? (
          <div className="flex h-64 items-center justify-center space-x-2 text-slate-400">
            <CircleDot className="h-5 w-5 animate-pulse text-slate-400" />
            <span className="text-sm font-medium">Loading quarterly statements for {ticker}...</span>
          </div>
        ) : quarters.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50/50 p-8 text-center">
            <AlertCircle className="mx-auto h-8 w-8 text-slate-400" />
            <p className="mt-2 text-sm font-medium text-slate-800">
              No quarterly financials available for {ticker}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              {data?.note || `No quarterly statements extracted for ${ticker} from free public sources.`}
            </p>
          </div>
        ) : viewMode === "chart" ? (
          <div className="space-y-4">
            {/* SVG Trend Chart */}
            <div className="w-full overflow-x-auto rounded-xl border border-slate-100 bg-white p-3 shadow-inner">
              <svg
                viewBox={`0 0 ${chartWidth} ${chartHeight}`}
                className="w-full min-w-[620px] select-none text-xs"
              >
                {/* Horizontal reference grid lines */}
                {yTicks.map((t, idx) => (
                  <g key={idx}>
                    <line
                      x1={padLeft}
                      y1={t.y}
                      x2={chartWidth - padRight}
                      y2={t.y}
                      stroke="#f1f5f9"
                      strokeWidth={1}
                      strokeDasharray={idx === yTicks.length - 1 ? "none" : "3,3"}
                    />
                    <text
                      x={padLeft - 10}
                      y={t.y + 4}
                      textAnchor="end"
                      fill="#64748b"
                      className="text-[10px] font-mono"
                    >
                      {formatCompactIDR(t.val)}
                    </text>
                  </g>
                ))}

                {/* X Axis baseline */}
                <line
                  x1={padLeft}
                  y1={chartHeight - padBottom}
                  x2={chartWidth - padRight}
                  y2={chartHeight - padBottom}
                  stroke="#cbd5e1"
                  strokeWidth={1.5}
                />

                {/* Vertical column highlight when hovering */}
                {hoveredQuarterIndex !== null && chartData[hoveredQuarterIndex] && (
                  <g>
                    <line
                      x1={chartData[hoveredQuarterIndex].x}
                      y1={padTop}
                      x2={chartData[hoveredQuarterIndex].x}
                      y2={chartHeight - padBottom}
                      stroke="#0f172a"
                      strokeWidth={1.5}
                      strokeDasharray="3,3"
                      opacity={0.4}
                    />
                    <circle
                      cx={chartData[hoveredQuarterIndex].x}
                      cy={chartHeight - padBottom}
                      r={3}
                      fill="#0f172a"
                    />
                  </g>
                )}

                {/* Revenue Polyline */}
                {visibleMetrics.revenue && (
                  <g>
                    <polyline
                      points={chartData
                        .filter((p) => p.yRevenue !== null)
                        .map((p) => `${p.x.toFixed(1)},${(p.yRevenue as number).toFixed(1)}`)
                        .join(" ")}
                      fill="none"
                      stroke="#059669"
                      strokeWidth={2.5}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </g>
                )}

                {/* Operating Cash Flow Polyline */}
                {visibleMetrics.operating_cash_flow && (
                  <g>
                    <polyline
                      points={chartData
                        .filter((p) => p.yOcf !== null)
                        .map((p) => `${p.x.toFixed(1)},${(p.yOcf as number).toFixed(1)}`)
                        .join(" ")}
                      fill="none"
                      stroke="#d97706"
                      strokeWidth={2}
                      strokeDasharray="4,3"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </g>
                )}

                {/* Earnings Polyline */}
                {visibleMetrics.earnings && (
                  <g>
                    <polyline
                      points={chartData
                        .filter((p) => p.yEarnings !== null)
                        .map((p) => `${p.x.toFixed(1)},${(p.yEarnings as number).toFixed(1)}`)
                        .join(" ")}
                      fill="none"
                      stroke="#2563eb"
                      strokeWidth={2.5}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </g>
                )}

                {/* Hover Interaction Areas & Circles */}
                {chartData.map((p, idx) => {
                  const isHovered = hoveredQuarterIndex === idx
                  return (
                    <g
                      key={idx}
                      className="cursor-pointer"
                      onMouseEnter={() => setHoveredQuarterIndex(idx)}
                      onMouseLeave={() => setHoveredQuarterIndex(null)}
                      onClick={() => setHoveredQuarterIndex(idx)}
                    >
                      {/* Invisible wide vertical hit target */}
                      <rect
                        x={p.x - 25}
                        y={padTop}
                        width={50}
                        height={chartHeight - padTop - padBottom + 30}
                        fill="transparent"
                      />

                      {/* Revenue Dot */}
                      {visibleMetrics.revenue && p.yRevenue !== null && (
                        <circle
                          cx={p.x}
                          cy={p.yRevenue}
                          r={isHovered ? 5.5 : 3.5}
                          fill="#059669"
                          stroke="#ffffff"
                          strokeWidth={1.5}
                        />
                      )}

                      {/* Earnings Dot */}
                      {visibleMetrics.earnings && p.yEarnings !== null && (
                        <circle
                          cx={p.x}
                          cy={p.yEarnings}
                          r={isHovered ? 5.5 : 3.5}
                          fill="#2563eb"
                          stroke="#ffffff"
                          strokeWidth={1.5}
                        />
                      )}

                      {/* OCF Dot */}
                      {visibleMetrics.operating_cash_flow && p.yOcf !== null && (
                        <circle
                          cx={p.x}
                          cy={p.yOcf}
                          r={isHovered ? 5 : 3}
                          fill="#d97706"
                          stroke="#ffffff"
                          strokeWidth={1.5}
                        />
                      )}

                      {/* X-axis Quarter Label */}
                      <text
                        x={p.x}
                        y={chartHeight - padBottom + 16}
                        textAnchor="middle"
                        fill={isHovered ? "#0f172a" : "#64748b"}
                        className={`text-[10px] font-mono ${isHovered ? "font-bold fill-slate-900" : ""}`}
                      >
                        {p.label}
                      </text>

                      {/* Exact Date */}
                      <text
                        x={p.x}
                        y={chartHeight - padBottom + 28}
                        textAnchor="middle"
                        fill="#94a3b8"
                        className="text-[9px] font-mono"
                      >
                        {p.date.slice(5)}
                      </text>
                    </g>
                  )
                })}
              </svg>
            </div>

            {/* Selected Quarter Inspection Strip */}
            {activeQuarter && (
              <div className="rounded-lg border border-slate-200 bg-slate-50/70 p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-semibold text-slate-900">
                      {formatQuarterLabel(activeQuarter.date)} ({activeQuarter.date})
                    </span>
                    <Badge variant="outline" className="text-[10px]">
                      Quarterly Statement
                    </Badge>
                  </div>

                  <div className="flex flex-wrap items-center gap-4 text-xs">
                    {visibleMetrics.revenue && (
                      <div className="flex items-center gap-1.5">
                        <span className="h-2.5 w-2.5 rounded-full bg-emerald-600" />
                        <span className="text-[11px] text-slate-500">Revenue:</span>
                        <span className="font-mono font-semibold text-slate-900">
                          {formatCompactIDR(activeQuarter.revenue)}
                        </span>
                      </div>
                    )}

                    {visibleMetrics.earnings && (
                      <div className="flex items-center gap-1.5">
                        <span className="h-2.5 w-2.5 rounded-full bg-blue-600" />
                        <span className="text-[11px] text-slate-500">Net Earnings:</span>
                        <span className="font-mono font-semibold text-slate-900">
                          {formatCompactIDR(activeQuarter.earnings)}
                        </span>
                      </div>
                    )}

                    {visibleMetrics.operating_cash_flow && (
                      <div className="flex items-center gap-1.5">
                        <span className="h-2.5 w-2.5 rounded-full bg-amber-600" />
                        <span className="text-[11px] text-slate-500">Op. Cash Flow:</span>
                        <span className="font-mono font-semibold text-slate-900">
                          {formatCompactIDR(activeQuarter.operating_cash_flow)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Additional Financial Metrics Row */}
                <div className="mt-3 pt-3 border-t border-slate-200/70 grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
                  <div>
                    <span className="text-[11px] text-slate-500">Total Assets:</span>
                    <div className="font-mono font-medium text-slate-800">
                      {formatCompactIDR(activeQuarter.total_assets)}
                    </div>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-500">Total Equity:</span>
                    <div className="font-mono font-medium text-slate-800">
                      {formatCompactIDR(activeQuarter.total_equity)}
                    </div>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-500">EBITDA:</span>
                    <div className="font-mono font-medium text-slate-800">
                      {formatCompactIDR(activeQuarter.ebitda)}
                    </div>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-500">Operating Margin:</span>
                    <div className="font-mono font-medium text-slate-800">
                      {typeof activeQuarter.operating_pnl === "number" &&
                      typeof activeQuarter.revenue === "number" &&
                      activeQuarter.revenue > 0
                        ? `${((activeQuarter.operating_pnl / activeQuarter.revenue) * 100).toFixed(1)}%`
                        : "N/A"}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Table View */
          <div className="overflow-x-auto rounded-lg border border-slate-200">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
                <tr>
                  <th className="px-3.5 py-2.5 font-medium">Quarter</th>
                  <th className="px-3.5 py-2.5 font-medium">Date</th>
                  <th className="px-3.5 py-2.5 font-medium text-right text-emerald-700">Revenue</th>
                  <th className="px-3.5 py-2.5 font-medium text-right text-blue-700">Net Earnings</th>
                  <th className="px-3.5 py-2.5 font-medium text-right text-amber-700">Op. Cash Flow</th>
                  <th className="px-3.5 py-2.5 font-medium text-right">Total Assets</th>
                  <th className="px-3.5 py-2.5 font-medium text-right">Total Equity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {quarters.map((q, i) => (
                  <tr key={i} className="hover:bg-slate-50/75 transition-colors">
                    <td className="px-3.5 py-2 font-mono font-semibold text-slate-900">
                      {formatQuarterLabel(q.date)}
                    </td>
                    <td className="px-3.5 py-2 font-mono text-slate-600">{q.date}</td>
                    <td className="px-3.5 py-2 font-mono text-right font-medium text-emerald-700">
                      {formatCompactIDR(q.revenue)}
                    </td>
                    <td className="px-3.5 py-2 font-mono text-right font-medium text-blue-700">
                      {formatCompactIDR(q.earnings)}
                    </td>
                    <td className="px-3.5 py-2 font-mono text-right font-medium text-amber-700">
                      {formatCompactIDR(q.operating_cash_flow)}
                    </td>
                    <td className="px-3.5 py-2 font-mono text-right text-slate-600">
                      {formatCompactIDR(q.total_assets)}
                    </td>
                    <td className="px-3.5 py-2 font-mono text-right text-slate-600">
                      {formatCompactIDR(q.total_equity)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
