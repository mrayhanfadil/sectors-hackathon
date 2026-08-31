import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Gauge } from "lucide-react"

interface SentimentGaugeProps {
  score: number // 0-100
  label: string
  velocity: string
  mentionsCount: number
  ticker: string
}

export function SentimentGauge({ score, label, velocity, mentionsCount, ticker }: SentimentGaugeProps) {
  // Angle calculation for 180-degree semi-circle (-90 to +90)
  const angle = -90 + (score / 100) * 180

  const badgeVariant =
    score >= 70 ? "buy" : score >= 55 ? "success" : score <= 35 ? "destructive" : "hold"

  return (
    <Card className="border-[#262d3a] bg-[#111317]">
      <CardHeader className="pb-1 border-b border-[#1d222c]">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xs font-semibold flex items-center gap-2 text-slate-200">
            <Gauge className="h-3.5 w-3.5 text-amber-400" />
            <span>Retail Social Sentiment Gauge ({ticker})</span>
          </CardTitle>
          <Badge variant={badgeVariant} className="text-[10px]">
            {label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-3 text-center space-y-3">
        {/* SVG Semi-Circle Dial */}
        <div className="relative flex justify-center py-2">
          <svg viewBox="0 0 200 115" className="w-52 select-none overflow-visible font-mono text-[9px]">
            <defs>
              <linearGradient id="gaugeGradient" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#ef4444" />
                <stop offset="35%" stopColor="#f97316" />
                <stop offset="50%" stopColor="#f59e0b" />
                <stop offset="70%" stopColor="#10b981" />
                <stop offset="100%" stopColor="#059669" />
              </linearGradient>
            </defs>

            {/* Background Arc */}
            <path
              d="M 20 100 A 80 80 0 0 1 180 100"
              fill="none"
              stroke="#1e2430"
              strokeWidth="14"
              strokeLinecap="round"
            />

            {/* Gradient Value Arc */}
            <path
              d="M 20 100 A 80 80 0 0 1 180 100"
              fill="none"
              stroke="url(#gaugeGradient)"
              strokeWidth="14"
              strokeLinecap="round"
              opacity="0.85"
            />

            {/* Center Pivot Point */}
            <circle cx="100" cy="100" r="7" fill="#f59e0b" stroke="#111317" strokeWidth="2" />

            {/* Needle Pointer */}
            <g transform={`rotate(${angle}, 100, 100)`}>
              <line
                x1="100"
                y1="100"
                x2="100"
                y2="28"
                stroke="#ffffff"
                strokeWidth="3"
                strokeLinecap="round"
              />
              <circle cx="100" cy="28" r="3" fill="#f59e0b" />
            </g>

            {/* Scale Markers */}
            <text x="15" y="112" fill="#64748b" textAnchor="middle">0</text>
            <text x="100" y="20" fill="#64748b" textAnchor="middle">50</text>
            <text x="185" y="112" fill="#64748b" textAnchor="middle">100</text>
          </svg>
        </div>

        {/* Score Readout */}
        <div className="space-y-1">
          <div className="font-mono text-3xl font-bold text-white">
            {score}
            <span className="text-sm font-normal text-slate-400 font-sans"> / 100</span>
          </div>
          <div className="text-xs font-mono text-slate-300">
            Velocity: <span className="text-emerald-400 font-bold">{velocity}</span>
          </div>
        </div>

        <div className="p-2.5 rounded bg-[#161a22] border border-[#212734] text-[11px] font-mono flex justify-between text-slate-400">
          <span>30D Mentions: <strong className="text-slate-200">{mentionsCount.toLocaleString("id-ID")}</strong></span>
          <span>Coverage: <strong className="text-amber-400">X + Reddit + Stockbit</strong></span>
        </div>
      </CardContent>
    </Card>
  )
}
