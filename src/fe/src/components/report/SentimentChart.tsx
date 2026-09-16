import { useState } from "react"
import {
  Compass,
  Calendar,
  ExternalLink,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { Sentiment } from "@/lib/api"

export type SentimentChartProps = {
  ticker: string
  sentiment?: Sentiment | null
  isLoading?: boolean
}

export function SentimentChart({ ticker, sentiment, isLoading }: SentimentChartProps) {
  const tk = ticker.toUpperCase()
  const [activeView, setActiveView] = useState<"gauge" | "timeline">("gauge")

  // LOUD policy: no invented gauge/narratives/timeline. Missing BE data
  // renders the honest-empty state below (gauge -, no rows).
  const gauge: number | null = sentiment?.gauge != null ? Number(sentiment.gauge) : null
  const narratives: string[] = sentiment?.top_narratives?.length
    ? sentiment.top_narratives
    : sentiment?.narratives?.length
    ? sentiment.narratives
    : []

  const timeline: Array<{ date: string; note: string }> = sentiment?.timeline && sentiment.timeline.length > 0
    ? sentiment.timeline
    : []

  const sources = sentiment?.sources || []

  // SVG Gauge Calculations
  const radius = 80
  const centerX = 120
  const centerY = 100
  // Angle maps 0 -> -180 deg (left), 100 -> 0 deg (right)
  const angleDeg = -180 + ((gauge ?? 50) / 100) * 180
  const angleRad = (angleDeg * Math.PI) / 180
  const needleLength = 64
  const needleX = centerX + needleLength * Math.cos(angleRad)
  const needleY = centerY + needleLength * Math.sin(angleRad)

  return (
    <Card className="rounded-none border border-neutral-300 bg-white shadow-none dark:border-[#262930] dark:bg-[#121316]">
      <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3 pb-2.5 dark:border-[#262930] dark:bg-[#181a1f]/70">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <Compass className="h-4 w-4 text-amber-600 dark:text-amber-400" />
            <CardTitle className="text-xs font-mono font-semibold uppercase tracking-wider text-neutral-900 dark:text-neutral-100">
              TERMINAL :: SENTIMENT & NARRATIVE MATRIX // {tk} &lt;EQUITY&gt; DIAL
            </CardTitle>
          </div>

          <div className="flex items-center gap-1 font-mono text-[11px]">
            <button
              type="button"
              onClick={() => setActiveView("gauge")}
              className={`rounded-none px-2.5 py-1 font-semibold transition-colors cursor-pointer ${
                activeView === "gauge"
                  ? "bg-neutral-900 text-white dark:bg-amber-400 dark:text-black"
                  : "border border-neutral-300 bg-white text-neutral-600 hover:bg-neutral-100 dark:border-[#262930] dark:bg-[#121316] dark:text-neutral-400 dark:hover:bg-[#181a1f]"
              }`}
            >
              [F1] DIAL & NARRATIVE
            </button>
            <button
              type="button"
              onClick={() => setActiveView("timeline")}
              className={`rounded-none px-2.5 py-1 font-semibold transition-colors cursor-pointer ${
                activeView === "timeline"
                  ? "bg-neutral-900 text-white dark:bg-amber-400 dark:text-black"
                  : "border border-neutral-300 bg-white text-neutral-600 hover:bg-neutral-100 dark:border-[#262930] dark:bg-[#121316] dark:text-neutral-400 dark:hover:bg-[#181a1f]"
              }`}
            >
              [F2] TIMELINE CHRONOLOGY
            </button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-3 sm:p-4">
        {isLoading ? (
          <div className="flex h-48 items-center justify-center font-mono text-xs text-neutral-400">
            <span>MEMUAT MATRIKS SENTIMEN {tk}...</span>
          </div>
        ) : gauge == null && narratives.length === 0 && timeline.length === 0 ? (
          <div className="flex h-48 flex-col items-center justify-center gap-1.5 border border-dashed border-neutral-300 bg-neutral-50/50 p-6 font-mono text-xs dark:border-[#262930] dark:bg-[#15171c]">
            <span className="font-semibold text-neutral-700 dark:text-neutral-300">[NO SENTIMENT DATA DETECTED]</span>
            <span className="text-neutral-500 dark:text-neutral-400">Menunggu Ingesti Sinyal Sectors - Menampilkan State Kosong Sesuai Data Nyata.</span>
          </div>
        ) : activeView === "gauge" ? (
          <div className="grid gap-4 md:grid-cols-12 items-center">
            {/* Left Col: SVG Speedometer Gauge */}
            <div className="md:col-span-5 flex flex-col items-center justify-center p-4 border border-neutral-300 bg-neutral-50/50 dark:border-[#262930] dark:bg-[#15171c]">
              <svg
                viewBox="0 0 240 130"
                className="w-full max-w-[240px] select-none"
              >
                {/* Bearish Arc (0 to 40) */}
                <path
                  d="M 40 100 A 80 80 0 0 1 73 34"
                  fill="none"
                  stroke="#f43f5e"
                  strokeWidth="10"
                  strokeLinecap="butt"
                />
                {/* Neutral Arc (40 to 60) */}
                <path
                  d="M 77 31 A 80 80 0 0 1 163 31"
                  fill="none"
                  stroke="#94a3b8"
                  strokeWidth="10"
                />
                {/* Bullish Arc (60 to 100) */}
                <path
                  d="M 167 34 A 80 80 0 0 1 200 100"
                  fill="none"
                  stroke="#10b981"
                  strokeWidth="10"
                  strokeLinecap="butt"
                />

                {/* Center Pivot */}
                <circle cx={centerX} cy={centerY} r="6" className="fill-neutral-900 dark:fill-amber-400" />
                <circle cx={centerX} cy={centerY} r="2.5" className="fill-white dark:fill-black" />

                {/* Needle Line */}
                {gauge != null && (
                  <>
                    <line
                      x1={centerX}
                      y1={centerY}
                      x2={needleX}
                      y2={needleY}
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      className="stroke-neutral-900 dark:stroke-amber-400"
                    />
                    <circle cx={needleX} cy={needleY} r="2.5" className="fill-neutral-900 dark:fill-amber-400" />
                  </>
                )}

                {/* Labels */}
                <text x="35" y="118" textAnchor="middle" fill="#f43f5e" className="text-[9px] font-mono font-bold">
                  0 BEAR
                </text>
                <text x="120" y="20" textAnchor="middle" fill="#64748b" className="text-[9px] font-mono font-medium">
                  50 NET
                </text>
                <text x="205" y="118" textAnchor="middle" fill="#10b981" className="text-[9px] font-mono font-bold">
                  100 BULL
                </text>
              </svg>

              <div className="mt-2 text-center font-mono">
                <div className="text-2xl font-bold tabular-nums text-neutral-900 dark:text-neutral-100">
                  {gauge == null ? "-" : gauge} <span className="text-xs font-normal text-neutral-400">/ 100</span>
                </div>
                <div className="mt-1">
                  <span className={`inline-block border px-2 py-0.5 text-[10px] font-semibold tracking-wider ${
                    gauge == null
                      ? "border-neutral-300 bg-neutral-100 text-neutral-600 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-400"
                      : gauge >= 60
                      ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400"
                      : gauge <= 40
                      ? "border-rose-500/40 bg-rose-500/10 text-rose-700 dark:text-rose-400"
                      : "border-neutral-300 bg-neutral-100 text-neutral-700 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300"
                  }`}>
                    {gauge == null ? "[MENUNGGU DATA]" : gauge >= 60 ? "[BULLISH // POSITIF]" : gauge <= 40 ? "[BEARISH // NEGATIF]" : "[NETRAL // KONSOLIDASI]"}
                  </span>
                </div>
              </div>
            </div>

            {/* Right Col: Top Narratives List */}
            <div className="md:col-span-7 space-y-2.5">
              <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                <span>PRIMARY MARKET NARRATIVES ({narratives.length})</span>
                <span>RANKED BY NLP RELEVANCE</span>
              </div>

              {narratives.length === 0 ? (
                <div className="border border-dashed border-neutral-300 p-4 text-center font-mono text-xs text-neutral-500 dark:border-[#262930] dark:text-neutral-400">
                  Belum ada narasi tematik yang terdeteksi untuk {tk}.
                </div>
              ) : (
                <div className="space-y-1.5">
                  {narratives.map((n, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-2.5 border border-neutral-300 bg-neutral-50/50 p-2.5 text-xs text-neutral-800 transition-colors hover:border-neutral-400 dark:border-[#262930] dark:bg-[#15171c] dark:text-neutral-200 dark:hover:border-neutral-600"
                    >
                      <span className="flex h-5 w-5 shrink-0 items-center justify-center font-mono text-[10px] font-bold bg-neutral-900 text-white dark:bg-[#262930] dark:text-amber-400">
                        [{String(i + 1).padStart(2, "0")}]
                      </span>
                      <p className="font-sans text-xs leading-relaxed text-neutral-800 dark:text-neutral-200">
                        {n}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              {sources.length > 0 && (
                <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-neutral-200 font-mono text-[10px] dark:border-[#262930]">
                  <span className="text-neutral-500 dark:text-neutral-400">RUJUKAN KANAL:</span>
                  {sources.map((src, idx) => (
                    <a
                      key={idx}
                      href={src.url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 border border-neutral-300 bg-white px-1.5 py-0.5 font-mono text-neutral-700 hover:border-neutral-400 hover:bg-neutral-50 transition-colors dark:border-[#262930] dark:bg-[#181a1f] dark:text-neutral-300 dark:hover:border-neutral-600"
                    >
                      <span>[{src.platform.toUpperCase()}]</span>
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
            <div className="flex items-center gap-2 font-mono text-[10px] font-semibold uppercase tracking-wider text-neutral-600 dark:text-neutral-400">
              <Calendar className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
              <span>KRONOLOGI PERGESERAN NARASI & SENTIMEN // TRACE LOG</span>
            </div>

            {timeline.length === 0 ? (
              <div className="border border-dashed border-neutral-300 p-6 text-center font-mono text-xs text-neutral-500 dark:border-[#262930] dark:text-neutral-400">
                Belum ada rekam jejak timeline historis untuk {tk}.
              </div>
            ) : (
              <div className="space-y-2 font-mono">
                {timeline.map((t, idx) => (
                  <div
                    key={idx}
                    className="border border-neutral-300 bg-neutral-50/50 p-2.5 text-xs dark:border-[#262930] dark:bg-[#15171c]"
                  >
                    <div className="flex items-center justify-between border-b border-neutral-200 pb-1 text-[10px] text-neutral-500 dark:border-[#262930] dark:text-neutral-400">
                      <span className="font-semibold text-neutral-900 dark:text-amber-400">TIMESTAMP :: {t.date}</span>
                      <span>LOG #{idx + 1}</span>
                    </div>
                    <p className="mt-1.5 font-sans text-xs text-neutral-700 leading-relaxed dark:text-neutral-300">
                      {t.note}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="mt-3 pt-2 border-t border-neutral-200 font-mono text-[10px] text-neutral-500 dark:border-[#262930] dark:text-neutral-400">
          TERMINAL NOTICE :: Data sentimen ritel diagregasikan secara otomatis dari kanal publik dan bukan merupakan rekomendasi transaksi efek.
        </div>
      </CardContent>
    </Card>
  )
}
