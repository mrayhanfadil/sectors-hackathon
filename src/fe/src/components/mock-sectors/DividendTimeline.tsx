import { useState, useMemo } from "react"
import {
  Calendar,
  DollarSign,
  AlertCircle,
  TrendingUp,
  Layers,
  Info,
  CircleDot,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { CorporateActionsResponse, DividendItem } from "@/lib/api"

interface DividendTimelineProps {
  ticker: string
  data?: CorporateActionsResponse | null
  isLoading?: boolean
}

function formatIDR(val: number | null | undefined): string {
  if (val == null || Number.isNaN(Number(val))) return "N/A"
  return `Rp ${Number(val).toLocaleString("id-ID", { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`
}

export function DividendTimeline({ ticker, data, isLoading }: DividendTimelineProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)
  const [activeTab, setActiveTab] = useState<"chart" | "table">("chart")

  const dividends = useMemo(() => {
    if (!data?.dividend || !Array.isArray(data.dividend)) return []
    // Sort chronologically (oldest -> newest) for left-to-right timeline
    return [...data.dividend].sort((a, b) => {
      const da = new Date(a.ex_date).getTime()
      const db = new Date(b.ex_date).getTime()
      return da - db
    })
  }, [data])

  const splits = data?.stock_split ?? []
  const agms = data?.agm ?? []

  // Stats calculation
  const stats = useMemo(() => {
    if (dividends.length === 0) return null
    const amounts = dividends.map((d) => d.amount_per_share).filter((v) => typeof v === "number" && !Number.isNaN(v))
    if (amounts.length === 0) return null
    const max = Math.max(...amounts)
    const min = Math.min(...amounts)
    const sum = amounts.reduce((acc, v) => acc + v, 0)
    const avg = sum / amounts.length
    const latest = dividends[dividends.length - 1]
    return { count: dividends.length, max, min, avg, latest }
  }, [dividends])

  // SVG Chart Geometry
  const chartWidth = 720
  const chartHeight = 220
  const padLeft = 70
  const padRight = 40
  const padTop = 30
  const padBottom = 45

  const chartPoints = useMemo(() => {
    if (dividends.length === 0) return []
    const amounts = dividends.map((d) => d.amount_per_share || 0)
    const maxAmount = Math.max(...amounts, 1) * 1.15
    const minAmount = 0

    const timestamps = dividends.map((d) => new Date(d.ex_date).getTime())
    const minTime = Math.min(...timestamps)
    const maxTime = Math.max(...timestamps)
    const timeSpan = maxTime - minTime || 1

    const innerW = chartWidth - padLeft - padRight
    const innerH = chartHeight - padTop - padBottom

    return dividends.map((d, i) => {
      const t = new Date(d.ex_date).getTime()
      const x =
        dividends.length === 1
          ? padLeft + innerW / 2
          : padLeft + ((t - minTime) / timeSpan) * innerW
      const y = padTop + innerH - ((d.amount_per_share - minAmount) / (maxAmount - minAmount)) * innerH
      return { ...d, x, y, index: i }
    })
  }, [dividends])

  const maxPayout = stats?.max ?? 100
  const yTicks = [
    { label: formatIDR(maxPayout * 1.0), y: padTop },
    { label: formatIDR(maxPayout * 0.5), y: padTop + (chartHeight - padTop - padBottom) * 0.5 },
    { label: "Rp 0", y: chartHeight - padBottom },
  ]

  const activeDividend: DividendItem | null =
    hoveredIndex !== null && chartPoints[hoveredIndex]
      ? chartPoints[hoveredIndex]
      : stats?.latest ?? null

  return (
    <Card className="overflow-hidden border-slate-200 shadow-sm dark:border-slate-800">
      <CardHeader className="border-b border-slate-100 bg-slate-50/50 pb-4 dark:border-slate-800 dark:bg-slate-900/50">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-base font-semibold text-slate-900 dark:text-slate-100">
                Dividend Timeline & Corporate Actions
              </CardTitle>
              <Badge variant="outline" className="font-mono text-[11px] text-slate-700 dark:text-slate-300">
                {ticker}
              </Badge>
            </div>
            <CardDescription className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Historical cash dividend distributions from Sectors corporate-actions data
            </CardDescription>
          </div>

          <div className="flex items-center gap-1.5 self-start sm:self-auto">
            <button
              type="button"
              onClick={() => setActiveTab("chart")}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                activeTab === "chart"
                  ? "bg-slate-900 text-white dark:bg-slate-800"
                  : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50 dark:bg-[#111111] dark:text-slate-400 dark:border-slate-800 dark:hover:bg-slate-900"
              }`}
            >
              Visual Chart
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("table")}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                activeTab === "table"
                  ? "bg-slate-900 text-white dark:bg-slate-800"
                  : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50 dark:bg-[#111111] dark:text-slate-400 dark:border-slate-800 dark:hover:bg-slate-900"
              }`}
            >
              Payout Table ({dividends.length})
            </button>
          </div>
        </div>

        {/* Quick Stats Banner */}
        {stats && (
          <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
            <div className="rounded-lg border border-slate-200/80 bg-white p-2.5 dark:border-slate-800/80 dark:bg-[#111111]">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Total Dividends</span>
              <div className="mt-0.5 text-sm font-semibold text-slate-900 dark:text-slate-100">
                {stats.count} distributions
              </div>
            </div>
            <div className="rounded-lg border border-slate-200/80 bg-white p-2.5 dark:border-slate-800/80 dark:bg-[#111111]">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Latest Payout</span>
              <div className="mt-0.5 text-sm font-semibold text-emerald-700 dark:text-emerald-200">
                {formatIDR(stats.latest.amount_per_share)}
              </div>
            </div>
            <div className="rounded-lg border border-slate-200/80 bg-white p-2.5 dark:border-slate-800/80 dark:bg-[#111111]">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Historical Peak</span>
              <div className="mt-0.5 text-sm font-semibold text-slate-900 dark:text-slate-100">
                {formatIDR(stats.max)}
              </div>
            </div>
            <div className="rounded-lg border border-slate-200/80 bg-white p-2.5 dark:border-slate-800/80 dark:bg-[#111111]">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Avg Distribution</span>
              <div className="mt-0.5 text-sm font-semibold text-slate-900 dark:text-slate-100">
                {formatIDR(stats.avg)}
              </div>
            </div>
          </div>
        )}
      </CardHeader>

      <CardContent className="p-4 sm:p-6">
        {isLoading ? (
          <div className="flex h-56 items-center justify-center space-x-2 text-slate-400">
            <CircleDot className="h-5 w-5 animate-pulse text-slate-400" />
            <span className="text-sm font-medium">Loading corporate actions for {ticker}...</span>
          </div>
        ) : dividends.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50/50 p-8 text-center dark:border-slate-800 dark:bg-slate-900/50">
            <AlertCircle className="mx-auto h-8 w-8 text-slate-400" />
            <p className="mt-2 text-sm font-medium text-slate-800 dark:text-slate-200">
              No dividends found for {ticker}
            </p>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {data?.note || `No historical cash dividend payouts recorded for ${ticker} via free public sources.`}
            </p>
          </div>
        ) : activeTab === "chart" ? (
          <div className="space-y-4">
            {/* SVG Timeline */}
            <div className="w-full overflow-x-auto rounded-xl border border-slate-100 bg-white p-3 shadow-inner dark:border-slate-800 dark:bg-[#111111]">
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
                      strokeWidth={1}
                      strokeDasharray={idx === yTicks.length - 1 ? "none" : "3,3"}
                      className="stroke-[#e2e8f0] dark:stroke-[#262626]"
                    />
                    <text
                      x={padLeft - 10}
                      y={t.y + 4}
                      textAnchor="end"
                      fill="#64748b"
                      className="text-[10px] font-mono dark:fill-[#a1a1a1]"
                    >
                      {t.label}
                    </text>
                  </g>
                ))}

                {/* X Axis baseline */}
                <line
                  x1={padLeft}
                  y1={chartHeight - padBottom}
                  x2={chartWidth - padRight}
                  y2={chartHeight - padBottom}
                  strokeWidth={1.5}
                  className="stroke-[#94a3b8] dark:stroke-neutral-600"
                />

                {/* Connecting Trend Line */}
                {chartPoints.length > 1 && (
                  <polyline
                    points={chartPoints.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ")}
                    fill="none"
                    stroke="#cbd5e1"
                    strokeWidth={1.5}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                )}

                {/* Data Points */}
                {chartPoints.map((p, i) => {
                  const isHovered = hoveredIndex === i
                  return (
                    <g
                      key={i}
                      className="cursor-pointer transition-transform"
                      onMouseEnter={() => setHoveredIndex(i)}
                      onMouseLeave={() => setHoveredIndex(null)}
                      onClick={() => setHoveredIndex(i)}
                    >
                      {/* Vertical drop line to x-axis */}
                      <line
                        x1={p.x}
                        y1={p.y}
                        x2={p.x}
                        y2={chartHeight - padBottom}
                        strokeWidth={isHovered ? 1.5 : 1}
                        strokeDasharray="2,2"
                        className={isHovered ? "stroke-emerald-600" : "stroke-slate-200 dark:stroke-neutral-800"}
                      />

                      {/* Outer pulse when hovered */}
                      {isHovered && (
                        <circle
                          cx={p.x}
                          cy={p.y}
                          r={9}
                          fill="#d1fae5"
                          opacity={0.8}
                        />
                      )}

                      {/* Main Point Circle */}
                      <circle
                        cx={p.x}
                        cy={p.y}
                        r={isHovered ? 5.5 : 4}
                        fill={isHovered ? "#059669" : "#0f172a"}
                        strokeWidth={1.5}
                        className={`stroke-white dark:stroke-black ${isHovered ? "" : "dark:fill-white"}`}
                      />

                      {/* Date label along X axis */}
                      <text
                        x={p.x}
                        y={chartHeight - padBottom + 16}
                        textAnchor="middle"
                        fill={isHovered ? "#0f172a" : "#64748b"}
                        className={`text-[9px] font-mono ${isHovered ? "font-semibold fill-emerald-800 dark:fill-emerald-300" : "dark:fill-[#a1a1a1]"}`}
                        transform={`rotate(-25, ${p.x}, ${chartHeight - padBottom + 16})`}
                      >
                        {p.ex_date}
                      </text>
                    </g>
                  )
                })}
              </svg>
            </div>

            {/* Selected / Hovered Detail Card */}
            {activeDividend && (
              <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-slate-50/70 p-3.5 sm:flex-row sm:items-center sm:justify-between dark:border-slate-800 dark:bg-slate-900/70">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200">
                    <DollarSign className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                        {formatIDR(activeDividend.amount_per_share)} / share
                      </span>
                      <Badge variant="outline" className="text-[10px] uppercase">
                        {activeDividend.type || "cash"}
                      </Badge>
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400">
                      Currency: {activeDividend.currency || "IDR"} · Source: Sectors corporate actions
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4 text-xs">
                  <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-400">
                    <Calendar className="h-3.5 w-3.5 text-slate-400" />
                    <span className="text-[11px] text-slate-500 dark:text-slate-400">Ex-Date:</span>
                    <span className="font-mono font-medium text-slate-800 dark:text-slate-200">{activeDividend.ex_date}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-400">
                    <Calendar className="h-3.5 w-3.5 text-slate-400" />
                    <span className="text-[11px] text-slate-500 dark:text-slate-400">Payment:</span>
                    <span className="font-mono font-medium text-slate-800 dark:text-slate-200">
                      {activeDividend.payment_date || activeDividend.ex_date}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Table View */
          <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 border-b border-slate-200 dark:bg-slate-900 dark:text-slate-400 dark:border-slate-800">
                <tr>
                  <th className="px-4 py-2.5 font-medium">Ex-Date</th>
                  <th className="px-4 py-2.5 font-medium">Payment Date</th>
                  <th className="px-4 py-2.5 font-medium text-right">Amount / Share</th>
                  <th className="px-4 py-2.5 font-medium">Currency</th>
                  <th className="px-4 py-2.5 font-medium">Type</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {dividends.map((d, i) => (
                  <tr key={i} className="hover:bg-slate-50/75 transition-colors dark:hover:bg-slate-900/75">
                    <td className="px-4 py-2 font-mono text-slate-900 dark:text-slate-100">{d.ex_date}</td>
                    <td className="px-4 py-2 font-mono text-slate-600 dark:text-slate-400">{d.payment_date || "-"}</td>
                    <td className="px-4 py-2 font-mono font-semibold text-emerald-700 text-right dark:text-emerald-200">
                      {formatIDR(d.amount_per_share)}
                    </td>
                    <td className="px-4 py-2 text-slate-600 uppercase dark:text-slate-400">{d.currency || "IDR"}</td>
                    <td className="px-4 py-2 text-slate-600 capitalize dark:text-slate-400">{d.type || "cash"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Additional Corporate Actions Section: Splits & AGMs */}
        {(splits.length > 0 || agms.length > 0) && (
          <div className="mt-5 pt-4 border-t border-slate-200 space-y-3 dark:border-slate-800">
            <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
              Other Corporate Actions Recorded
            </span>

            <div className="grid gap-2 sm:grid-cols-2">
              {splits.map((s, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-2.5 rounded-lg border border-slate-200 bg-slate-50 p-2.5 text-xs dark:border-slate-800 dark:bg-slate-900"
                >
                  <Layers className="h-4 w-4 text-slate-600 shrink-0 mt-0.5 dark:text-slate-400" />
                  <div>
                    <div className="font-semibold text-slate-900 dark:text-slate-100">
                      Stock Split Ratio 1:{s.ratio}
                    </div>
                    <div className="text-[11px] text-slate-500 dark:text-slate-400">
                      Effective Date: <span className="font-mono text-slate-700 dark:text-slate-300">{s.date}</span>
                    </div>
                  </div>
                </div>
              ))}

              {agms.map((a, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-2.5 rounded-lg border border-slate-200 bg-slate-50 p-2.5 text-xs dark:border-slate-800 dark:bg-slate-900"
                >
                  <Info className="h-4 w-4 text-slate-600 shrink-0 mt-0.5 dark:text-slate-400" />
                  <div>
                    <div className="flex items-center gap-1.5">
                      <Badge variant="secondary" className="text-[10px]">
                        {a.type || "AGM"}
                      </Badge>
                      <span className="font-mono text-[11px] text-slate-500 dark:text-slate-400">{a.date}</span>
                    </div>
                    <p className="mt-1 text-[11px] text-slate-700 line-clamp-2 dark:text-slate-300">{a.agenda}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
