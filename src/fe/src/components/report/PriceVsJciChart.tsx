import * as React from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { BarChart2 } from "lucide-react"

interface PriceVsJciChartProps {
  history: {
    date: string
    stockNormalized: number
    jciNormalized: number
    stockPrice: number
    jciIndex: number
    volume: number
  }[]
  ticker: string
}

export function PriceVsJciChart({ history, ticker }: PriceVsJciChartProps) {
  const [hoverIndex, setHoverIndex] = React.useState<number | null>(null)

  if (!history || history.length === 0) return null

  // Calculate stats
  const first = history[0]
  const last = history[history.length - 1]
  const stockReturn = (((last.stockNormalized - first.stockNormalized) / first.stockNormalized) * 100).toFixed(1)
  const jciReturn = (((last.jciNormalized - first.jciNormalized) / first.jciNormalized) * 100).toFixed(1)
  const alpha = (Number(stockReturn) - Number(jciReturn)).toFixed(1)

  // Chart dimensions
  const width = 700
  const height = 220
  const padding = { top: 20, right: 30, bottom: 30, left: 45 }

  const minVal = Math.min(...history.map((h) => Math.min(h.stockNormalized, h.jciNormalized))) * 0.98
  const maxVal = Math.max(...history.map((h) => Math.max(h.stockNormalized, h.jciNormalized))) * 1.02
  const maxVol = Math.max(...history.map((h) => h.volume)) || 1

  const getX = (i: number) => padding.left + (i / (history.length - 1)) * (width - padding.left - padding.right)
  const getY = (val: number) => padding.top + (1 - (val - minVal) / (maxVal - minVal)) * (height - padding.top - padding.bottom)

  // Generate Stock Path
  const stockPoints = history.map((h, i) => `${getX(i)},${getY(h.stockNormalized)}`).join(" ")
  const jciPoints = history.map((h, i) => `${getX(i)},${getY(h.jciNormalized)}`).join(" ")

  // Area under stock
  const stockArea = `${getX(0)},${height - padding.bottom} ${stockPoints} ${getX(history.length - 1)},${height - padding.bottom}`

  const activePoint = hoverIndex !== null ? history[hoverIndex] : last

  return (
    <Card className="border-[#262d3a] bg-[#111317]">
      <CardHeader className="pb-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="space-y-0.5">
            <CardTitle className="text-xs font-semibold flex items-center gap-2 text-slate-200">
              <BarChart2 className="h-3.5 w-3.5 text-amber-400" />
              <span>Comparative Performance: {ticker} vs IHSG Benchmark (Normalized = 100)</span>
            </CardTitle>
            <div className="text-[11px] text-slate-400 font-mono">
              Indexed Rebase: 100.0 baseline across historical coverage trajectory
            </div>
          </div>

          <div className="flex items-center gap-3 font-mono text-xs">
            <div className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-amber-400 inline-block"></span>
              <span className="text-slate-300 font-semibold">{ticker}:</span>
              <span className={Number(stockReturn) >= 0 ? "text-emerald-400" : "text-red-400"}>
                {Number(stockReturn) >= 0 ? `+${stockReturn}%` : `${stockReturn}%`}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-blue-400 inline-block"></span>
              <span className="text-slate-400">IHSG:</span>
              <span className={Number(jciReturn) >= 0 ? "text-emerald-400" : "text-red-400"}>
                {Number(jciReturn) >= 0 ? `+${jciReturn}%` : `${jciReturn}%`}
              </span>
            </div>
            <Badge variant="amber" className="text-[10px]">
              Alpha {Number(alpha) >= 0 ? `+${alpha}%` : `${alpha}%`}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-2">
        {/* SVG Interactive Chart */}
        <div className="relative w-full overflow-x-auto">
          <svg
            viewBox={`0 0 ${width} ${height}`}
            className="w-full h-48 sm:h-56 select-none font-mono text-[10px]"
            onMouseLeave={() => setHoverIndex(null)}
          >
            <defs>
              <linearGradient id="stockGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.0" />
              </linearGradient>
            </defs>

            {/* Grid horizontal lines */}
            {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
              const val = minVal + pct * (maxVal - minVal)
              const y = getY(val)
              return (
                <g key={i}>
                  <line
                    x1={padding.left}
                    y1={y}
                    x2={width - padding.right}
                    y2={y}
                    stroke="#1c222d"
                    strokeDasharray="3 3"
                  />
                  <text x={padding.left - 8} y={y + 3} textAnchor="end" fill="#64748b">
                    {val.toFixed(0)}
                  </text>
                </g>
              )
            })}

            {/* Volume bars at bottom */}
            {history.map((h, i) => {
              const barHeight = (h.volume / maxVol) * 28
              const x = getX(i) - 4
              const y = height - padding.bottom - barHeight
              return (
                <rect
                  key={i}
                  x={x}
                  y={y}
                  width="8"
                  height={barHeight}
                  fill="#1e2430"
                  opacity="0.6"
                />
              )
            })}

            {/* Area Fill for Stock */}
            <polygon points={stockArea} fill="url(#stockGradient)" />

            {/* IHSG Line (Blue) */}
            <polyline
              points={jciPoints}
              fill="none"
              stroke="#38bdf8"
              strokeWidth="2"
              strokeDasharray="4 3"
            />

            {/* Stock Line (Amber) */}
            <polyline
              points={stockPoints}
              fill="none"
              stroke="#f59e0b"
              strokeWidth="2.5"
            />

            {/* Hover Points and Cursor */}
            {history.map((h, i) => {
              const x = getX(i)
              const yStock = getY(h.stockNormalized)
              const isHovered = hoverIndex === i
              return (
                <g key={i} className="cursor-pointer" onMouseEnter={() => setHoverIndex(i)}>
                  <circle
                    cx={x}
                    cy={yStock}
                    r={isHovered ? 5 : 3}
                    fill={isHovered ? "#fbbf24" : "#f59e0b"}
                    stroke="#111317"
                    strokeWidth="2"
                  />
                  {/* Invisible hit area */}
                  <rect
                    x={x - 12}
                    y={padding.top}
                    width="24"
                    height={height - padding.top - padding.bottom}
                    fill="transparent"
                  />
                </g>
              )
            })}

            {/* X-axis labels */}
            {history.map((h, i) => {
              if (i === 0 || i === history.length - 1 || i === Math.floor(history.length / 2)) {
                return (
                  <text
                    key={i}
                    x={getX(i)}
                    y={height - 8}
                    textAnchor="middle"
                    fill="#64748b"
                  >
                    {h.date}
                  </text>
                )
              }
              return null
            })}
          </svg>
        </div>

        {/* Dynamic Hover Tooltip Bar */}
        <div className="mt-2 flex flex-wrap items-center justify-between p-2 rounded bg-[#161a22] border border-[#222836] font-mono text-xs text-slate-300">
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Date:</span>
            <span className="font-semibold text-white">{activePoint.date}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-amber-400 font-semibold">{ticker} Price:</span>
            <span className="text-white">IDR {activePoint.stockPrice.toLocaleString("id-ID")}</span>
            <span className="text-slate-400 text-[10px]">({activePoint.stockNormalized})</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-blue-400">IHSG Level:</span>
            <span className="text-white">{activePoint.jciIndex.toLocaleString("id-ID")}</span>
            <span className="text-slate-400 text-[10px]">({activePoint.jciNormalized})</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
