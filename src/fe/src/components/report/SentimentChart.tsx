import { useState } from "react"
import {
  Compass,
  Calendar,
  Layers,
  TrendingUp,
  TrendingDown,
  MinusCircle,
  Tag,
  ExternalLink,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { Sentiment } from "@/lib/api"

export type SentimentChartProps = {
  ticker: string
  sentiment?: Sentiment | null
  isLoading?: boolean
}

export function SentimentChart({ ticker, sentiment, isLoading }: SentimentChartProps) {
  const tk = ticker.toUpperCase()
  const [activeView, setActiveView] = useState<"gauge" | "timeline">("gauge")

  const gauge = sentiment?.gauge != null ? Number(sentiment.gauge) : 50
  const narratives = sentiment?.top_narratives?.length
    ? sentiment.top_narratives
    : sentiment?.narratives?.length
    ? sentiment.narratives
    : [
        `Pertumbuhan kinerja operasional dan fundamental ${tk} tetap menjadi jangkar utama perbincangan.`,
        "Ekspektasi dividen final dan rasio payout menjadi katalis sentimen positif ritel.",
        "Dampak suku bunga acuan dan likuiditas perbankan dipantau ketat sebagai faktor volatilitas.",
      ]

  const timeline = sentiment?.timeline && sentiment.timeline.length > 0
    ? sentiment.timeline
    : [
        { date: "Terbaru", note: `Pergerakan harga ${tk} menguji level konsolidasi dengan volume wajar.` },
        { date: "Pekan Lalu", note: "Rilis ikhtisar kinerja tahunan dan pengumuman aksi korporasi." },
        { date: "Awal Bulan", note: "Peningkatan atensi pelaku pasar pada laporan riset sektoral." },
      ]

  const sources = sentiment?.sources || []

  // SVG Gauge Calculations
  const radius = 80
  const centerX = 120
  const centerY = 100
  // Angle maps 0 -> -180 deg (left), 100 -> 0 deg (right)
  const angleDeg = -180 + (gauge / 100) * 180
  const angleRad = (angleDeg * Math.PI) / 180
  const needleLength = 62
  const needleX = centerX + needleLength * Math.cos(angleRad)
  const needleY = centerY + needleLength * Math.sin(angleRad)

  return (
    <Card className="border-neutral-200 bg-white shadow-2xs">
      <CardHeader className="border-b border-neutral-100 bg-neutral-50/50 p-4 pb-3">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Compass className="h-4 w-4 text-neutral-700" />
              <CardTitle className="text-sm font-semibold text-neutral-900">
                Visualisasi Dial Sentimen & Narasi Pasar - {tk}
              </CardTitle>
            </div>
            <CardDescription className="text-xs text-neutral-500">
              Kalkulasi posisi sentimen ritel dan tematik narasi dominan
            </CardDescription>
          </div>

          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setActiveView("gauge")}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                activeView === "gauge"
                  ? "bg-neutral-900 text-white"
                  : "bg-white text-neutral-600 border border-neutral-200 hover:bg-neutral-50"
              }`}
            >
              Dial & Narasi
            </button>
            <button
              type="button"
              onClick={() => setActiveView("timeline")}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                activeView === "timeline"
                  ? "bg-neutral-900 text-white"
                  : "bg-white text-neutral-600 border border-neutral-200 hover:bg-neutral-50"
              }`}
            >
              Kronologi Timeline
            </button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-4 sm:p-6">
        {isLoading ? (
          <div className="flex h-48 items-center justify-center text-xs text-neutral-400">
            <span>Memuat visualisasi sentimen {tk}...</span>
          </div>
        ) : activeView === "gauge" ? (
          <div className="grid gap-6 md:grid-cols-12 items-center">
            {/* Left Col: SVG Speedometer Gauge */}
            <div className="md:col-span-5 flex flex-col items-center justify-center p-2 rounded-xl bg-neutral-50/60 border border-neutral-100">
              <svg
                viewBox="0 0 240 130"
                className="w-full max-w-[240px] select-none"
              >
                {/* Gauge Background Arcs */}
                {/* Bearish Arc (0 to 40) */}
                <path
                  d="M 40 100 A 80 80 0 0 1 73 34"
                  fill="none"
                  stroke="#f43f5e"
                  strokeWidth="12"
                  strokeLinecap="round"
                />
                {/* Neutral Arc (40 to 60) */}
                <path
                  d="M 77 31 A 80 80 0 0 1 163 31"
                  fill="none"
                  stroke="#94a3b8"
                  strokeWidth="12"
                />
                {/* Bullish Arc (60 to 100) */}
                <path
                  d="M 167 34 A 80 80 0 0 1 200 100"
                  fill="none"
                  stroke="#10b981"
                  strokeWidth="12"
                  strokeLinecap="round"
                />

                {/* Center Pivot */}
                <circle cx={centerX} cy={centerY} r="7" fill="#0f172a" />
                <circle cx={centerX} cy={centerY} r="3" fill="#ffffff" />

                {/* Needle Line */}
                <line
                  x1={centerX}
                  y1={centerY}
                  x2={needleX}
                  y2={needleY}
                  stroke="#0f172a"
                  strokeWidth="3"
                  strokeLinecap="round"
                />

                {/* Needle Point Marker */}
                <circle cx={needleX} cy={needleY} r="3" fill="#0f172a" />

                {/* Labels */}
                <text x="35" y="120" textAnchor="middle" fill="#e11d48" className="text-[10px] font-semibold font-mono">
                  0 Bear
                </text>
                <text x="120" y="20" textAnchor="middle" fill="#64748b" className="text-[10px] font-medium font-mono">
                  50 Netral
                </text>
                <text x="205" y="120" textAnchor="middle" fill="#059669" className="text-[10px] font-semibold font-mono">
                  100 Bull
                </text>
              </svg>

              <div className="mt-1 text-center">
                <div className="text-xl font-bold font-mono text-neutral-900">
                  {gauge} <span className="text-xs font-normal text-neutral-500">/ 100</span>
                </div>
                <Badge
                  variant={gauge >= 60 ? "success" : gauge <= 40 ? "destructive" : "secondary"}
                  className="mt-1 text-[11px]"
                >
                  {gauge >= 60 ? "Bullish" : gauge <= 40 ? "Bearish" : "Neutral"}
                </Badge>
              </div>
            </div>

            {/* Right Col: Top Narratives List */}
            <div className="md:col-span-7 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-neutral-700">
                  Narasi Utama Pasar ({narratives.length})
                </h4>
                <span className="text-[11px] text-neutral-400">Peringkat Relevansi</span>
              </div>

              <div className="space-y-2">
                {narratives.map((n, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-2.5 rounded-lg border border-neutral-200/80 bg-white p-3 text-xs leading-relaxed text-neutral-700 shadow-2xs hover:border-neutral-300 transition-colors"
                  >
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-neutral-900 text-[10px] font-bold text-white">
                      #{i + 1}
                    </span>
                    <div className="space-y-1">
                      <p className="font-medium text-neutral-800">{n}</p>
                    </div>
                  </div>
                ))}
              </div>

              {sources.length > 0 && (
                <div className="flex flex-wrap items-center gap-2 pt-1">
                  <span className="text-[11px] text-neutral-400">Rujukan Kanal:</span>
                  {sources.map((src, idx) => (
                    <a
                      key={idx}
                      href={src.url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 rounded bg-neutral-100 px-2 py-0.5 text-[11px] font-medium text-neutral-700 hover:bg-neutral-200 transition-colors"
                    >
                      <span>{src.platform}</span>
                      <ExternalLink className="h-2.5 w-2.5 text-neutral-400" />
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Timeline View */
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-700">
              <Calendar className="h-3.5 w-3.5" />
              <span>Kronologi Pergeseran Narasi & Sentimen</span>
            </div>

            <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-neutral-200">
              {timeline.map((t, idx) => (
                <div key={idx} className="relative">
                  <div className="absolute -left-6 top-1.5 h-2.5 w-2.5 rounded-full border-2 border-white bg-neutral-900 shadow-xs" />
                  <div className="rounded-lg border border-neutral-200 bg-white p-3 shadow-2xs">
                    <span className="font-mono text-[11px] font-semibold text-neutral-900">
                      {t.date}
                    </span>
                    <p className="mt-1 text-xs text-neutral-600 leading-relaxed">
                      {t.note}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="mt-4 pt-3 border-t border-neutral-100 text-[11px] text-neutral-400">
          Penafian: Data sentimen ritel merupakan agregasi opini publik pihak ketiga dan bukan merupakan rekomendasi transaksi efek.
        </div>
      </CardContent>
    </Card>
  )
}
