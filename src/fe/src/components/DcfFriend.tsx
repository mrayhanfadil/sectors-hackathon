import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { fetchDcfFull, type DcfFriendPayload } from "@/lib/api"

interface DcfFriendProps {
  ticker: string
}

function fmtIDR(n: number | null | undefined): string {
  if (n == null || Number.isNaN(Number(n))) return "-"
  return Math.round(Number(n)).toLocaleString("id-ID")
}

function fmtPct(n: number | null | undefined, digits = 1): string {
  if (n == null || Number.isNaN(Number(n))) return "-"
  const v = Number(n)
  return `${v > 0 ? "+" : ""}${v.toFixed(digits)}%`
}

function getHeatmapColor(upsidePct: number | null | undefined, val: number | null | undefined): { bg: string; fg: string } {
  if (val == null) return { bg: "#F4F8FC", fg: "#64748B" }
  if (upsidePct == null) return { bg: "#E1ECF6", fg: "#0B1F3A" }
  if (upsidePct < -10) return { bg: "#FADBD8", fg: "#78281F" }
  if (upsidePct < 0) return { bg: "#FCEAE8", fg: "#C0392B" }
  if (upsidePct <= 10) return { bg: "#E1ECF6", fg: "#0B1F3A" }
  if (upsidePct <= 25) return { bg: "#A9C9E8", fg: "#0B1F3A" }
  return { bg: "#0B1F3A", fg: "#FFFFFF" }
}

export function DcfFriend({ ticker }: DcfFriendProps) {
  const [data, setData] = useState<DcfFriendPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetchDcfFull(ticker)
      if ("error" in res && res.error) {
        setError(res.error)
        setData(null)
      } else {
        setData(res as DcfFriendPayload)
        setError(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [ticker])

  useEffect(() => {
    loadData()
  }, [loadData])

  const rec = data?.recommendation
  const marketPrice = data?.valuation?.market_price

  const ratingColorClass = (() => {
    const r = rec?.rating?.toUpperCase() || ""
    if (r === "BUY") return "bg-emerald-50 border-emerald-300 text-emerald-950 dark:bg-emerald-950 dark:border-emerald-800 dark:text-emerald-100"
    if (r === "HOLD") return "bg-amber-50 border-amber-300 text-amber-950 dark:bg-amber-950 dark:border-amber-800 dark:text-amber-100"
    if (r === "SELL") return "bg-red-50 border-red-300 text-red-950 dark:bg-red-950 dark:border-red-800 dark:text-red-100"
    return "bg-slate-100 border-slate-300 text-slate-900 dark:bg-slate-800 dark:border-slate-800 dark:text-slate-100"
  })()

  const ratingBadgeClass = (() => {
    const r = rec?.rating?.toUpperCase() || ""
    if (r === "BUY") return "bg-emerald-600 text-white"
    if (r === "HOLD") return "bg-amber-600 text-white"
    if (r === "SELL") return "bg-red-600 text-white"
    return "bg-slate-700 text-white"
  })()

  return (
    <details className="group rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-[#111111]">
      <summary className="flex cursor-pointer items-center justify-between p-4 font-semibold text-slate-800 hover:bg-slate-50 select-none dark:text-slate-200 dark:hover:bg-slate-900">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-bold">Analisa DCF (Friend-style)</span>
          <span className="text-xs font-normal text-slate-500 dark:text-slate-400">
            Port dari abidamassi/dcf-valuation-tool : math deterministic, audit-friendly
          </span>
        </div>
        <svg className="h-4 w-4 text-slate-400 group-open:rotate-180 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </summary>

      <div className="border-t border-slate-100 p-4 space-y-6 dark:border-slate-800">
        {loading && (
          <div className="space-y-4 py-4">
            <div className="h-16 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800" />
            <div className="grid gap-4 md:grid-cols-2">
              <div className="h-64 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800" />
              <div className="h-64 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800" />
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 space-y-3 dark:border-red-800 dark:bg-red-950 dark:text-red-200">
            <div>
              <div className="font-semibold">Gagal Memuat Analisa DCF Friend-style</div>
              <p className="text-xs text-red-600 mt-1 dark:text-red-400">{error}</p>
            </div>
            <Button size="sm" variant="outline" onClick={loadData} className="bg-white hover:bg-red-50 dark:bg-[#111111] dark:hover:bg-red-950">
              Coba Lagi
            </Button>
          </div>
        )}

        {!loading && !error && data && (
          <>
            {/* 1. Recommendation Banner */}
            {rec && (
              <div className={`rounded-xl border p-4 ${ratingColorClass}`}>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className={`rounded px-3 py-1 text-sm font-bold ${ratingBadgeClass}`}>
                      {rec.rating}
                    </span>
                    <div>
                      <div className="text-sm font-bold">
                        {rec.label || "Rekomendasi Valuasi DCF"}
                        {rec.upside != null && (
                          <span className="ml-2 font-mono text-xs font-semibold">
                            ({fmtPct(rec.upside * 100)})
                          </span>
                        )}
                      </div>
                      {rec.note && <div className="text-xs opacity-90 mt-0.5">{rec.note}</div>}
                    </div>
                  </div>
                  {data.valuation?.fair_value_per_share != null && (
                    <div className="text-right">
                      <div className="text-xs opacity-75">Nilai Wajar DCF</div>
                      <div className="text-base font-bold font-mono">
                        Rp {fmtIDR(data.valuation.fair_value_per_share)}
                      </div>
                    </div>
                  )}
                </div>

                {rec.reason_override && (
                  <div className="mt-3 rounded-lg border-l-4 border-slate-700 bg-white/70 p-3 text-xs text-slate-800 dark:bg-[#111111]/70 dark:text-slate-200">
                    <div className="font-semibold text-slate-900 mb-1 dark:text-slate-100">Catatan Gate Review Required:</div>
                    <p className="leading-relaxed">{rec.reason_override}</p>
                  </div>
                )}
              </div>
            )}

            {/* 2. WACC Breakdown + Scenarios Grid */}
            <div className="grid gap-6 lg:grid-cols-2">
              {/* Section: WACC Breakdown */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-bold">WACC Breakdown</CardTitle>
                  <CardDescription className="text-xs">
                    Komponen pembentuk biaya modal (CAPM + after-tax debt)
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b bg-slate-900 text-white dark:bg-slate-800">
                          <th className="py-2 px-3 text-left font-semibold">Komponen</th>
                          <th className="py-2 px-3 text-right font-semibold">Nilai</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.wacc_table.map((row, idx) => {
                          const isLast = idx === data.wacc_table.length - 1
                          return (
                            <tr
                              key={row.label}
                              className={`border-b ${
                                isLast
                                  ? "bg-sky-100 font-bold text-slate-900 dark:bg-sky-900 dark:text-slate-100"
                                  : idx % 2 === 1
                                  ? "bg-slate-50 dark:bg-slate-900"
                                  : "bg-white dark:bg-[#111111]"
                              }`}
                            >
                              <td className="py-1.5 px-3">{row.label}</td>
                              <td className="py-1.5 px-3 text-right font-mono font-medium">
                                {row.value}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>

              {/* Section: Scenarios */}
              <div className="space-y-3">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">Skenario Bear / Base / Bull</h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Sensitivitas operasional terhadap pertumbuhan dan margin
                    {marketPrice ? ` (Harga Pasar: Rp ${fmtIDR(marketPrice)})` : ""}
                  </p>
                </div>

                <div className="grid gap-3">
                  {(["BEAR", "BASE", "BULL"] as const).map((scName) => {
                    const sc = data.scenarios?.[scName]
                    if (!sc) return null

                    const isBase = scName === "BASE"
                    const isBull = scName === "BULL"

                    const cardBg = isBase
                      ? "border-2 border-slate-900 bg-slate-900 text-white dark:border-slate-700 dark:bg-slate-800"
                      : isBull
                      ? "border border-sky-300 bg-sky-50 text-slate-900 dark:border-sky-800 dark:bg-sky-950 dark:text-slate-100"
                      : "border border-slate-200 bg-slate-50 text-slate-900 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100"

                    const badgeClass = isBase
                      ? "bg-white text-slate-900 font-bold dark:bg-[#111111] dark:text-slate-100"
                      : isBull
                      ? "bg-emerald-600 text-white"
                      : "bg-amber-600 text-white"

                    return (
                      <div key={scName} className={`rounded-xl p-3.5 ${cardBg}`}>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold tracking-wider">{sc.scenario}</span>
                            <span className={`rounded px-2 py-0.5 text-[10px] font-semibold ${badgeClass}`}>
                              {sc.rating}
                            </span>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-bold font-mono">
                              Rp {fmtIDR(sc.fair_value_per_share)}
                            </div>
                            {sc.upside != null && (
                              <div
                                className={`text-[10px] font-mono font-semibold ${
                                  isBase
                                    ? "text-sky-300"
                                    : sc.upside >= 0
                                    ? "text-emerald-700 dark:text-emerald-200"
                                    : "text-red-700 dark:text-red-200"
                                }`}
                              >
                                {fmtPct(sc.upside * 100)}
                              </div>
                            )}
                          </div>
                        </div>

                        <div
                          className={`mt-2 grid grid-cols-3 gap-2 border-t pt-2 text-[11px] ${
                            isBase ? "border-slate-700 text-slate-300" : "border-slate-200 text-slate-600 dark:border-slate-800 dark:text-slate-400"
                          }`}
                        >
                          <div>
                            <span className="opacity-75">Growth Y1: </span>
                            <span className="font-mono font-medium">
                              {(sc.revenue_growth_y1 * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div>
                            <span className="opacity-75">EBIT Margin: </span>
                            <span className="font-mono font-medium">
                              {(sc.ebit_margin * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div>
                            <span className="opacity-75">Terminal g: </span>
                            <span className="font-mono font-medium">
                              {(sc.terminal_growth * 100).toFixed(2)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>

            {/* 3. Sensitivity Heatmap */}
            {data.sensitivity && data.sensitivity.fair_value && (
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <CardTitle className="text-sm font-bold">
                        Sensitivitas: WACC x Terminal Growth
                      </CardTitle>
                      <CardDescription className="text-xs">
                        Nilai wajar saham (Rp) pada berbagai kombinasi WACC (baris) dan Terminal Growth (kolom)
                      </CardDescription>
                    </div>
                    {marketPrice ? (
                      <Badge variant="outline" className="text-xs">
                        Acuan Harga: Rp {fmtIDR(marketPrice)}
                      </Badge>
                    ) : null}
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="overflow-x-auto">
                    <table className="w-full text-center text-xs border-collapse">
                      <thead>
                        <tr className="bg-slate-900 text-white dark:bg-slate-800">
                          <th className="py-2 px-3 text-left font-semibold">WACC \ g</th>
                          {data.sensitivity.g_axis.map((g) => (
                            <th key={g} className="py-2 px-3 font-semibold font-mono">
                              g = {(g * 100).toFixed(2)}%
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {data.sensitivity.wacc_axis.map((w, rowIdx) => {
                          const rowVals = data.sensitivity.fair_value[rowIdx] || []
                          const rowUps = data.sensitivity.upside?.[rowIdx] || []
                          return (
                            <tr key={w} className="border-b">
                              <td className="py-2 px-3 text-left font-bold font-mono bg-slate-50 text-slate-900 dark:bg-slate-900 dark:text-slate-100">
                                {(w * 100).toFixed(2)}%
                              </td>
                              {rowVals.map((val, colIdx) => {
                                const up = rowUps[colIdx] != null ? rowUps[colIdx] : (val != null && marketPrice ? ((val - marketPrice) / marketPrice) * 100 : null)
                                const color = getHeatmapColor(up, val)
                                return (
                                  <td
                                    key={colIdx}
                                    className="py-2 px-3 font-mono border-r border-slate-100 last:border-r-0 dark:border-slate-800"
                                    style={{ backgroundColor: color.bg, color: color.fg }}
                                  >
                                    <div className="font-bold">Rp {fmtIDR(val)}</div>
                                    {up != null && (
                                      <div className="text-[10px] opacity-90">{fmtPct(up)}</div>
                                    )}
                                  </td>
                                )
                              })}
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>

                  <div className="flex flex-wrap items-center justify-between p-3 text-[11px] text-slate-500 border-t bg-slate-50 dark:text-slate-400 dark:bg-slate-900">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">Legenda Upside:</span>
                      <span className="inline-block px-1.5 py-0.5 rounded text-[10px]" style={{ backgroundColor: "#FADBD8", color: "#78281F" }}>&lt; -10%</span>
                      <span className="inline-block px-1.5 py-0.5 rounded text-[10px]" style={{ backgroundColor: "#FCEAE8", color: "#C0392B" }}>-10% s.d. 0%</span>
                      <span className="inline-block px-1.5 py-0.5 rounded text-[10px]" style={{ backgroundColor: "#E1ECF6", color: "#0B1F3A" }}>0% s.d. 10%</span>
                      <span className="inline-block px-1.5 py-0.5 rounded text-[10px]" style={{ backgroundColor: "#A9C9E8", color: "#0B1F3A" }}>10% s.d. 25%</span>
                      <span className="inline-block px-1.5 py-0.5 rounded text-[10px]" style={{ backgroundColor: "#0B1F3A", color: "#FFFFFF" }}>&gt; 25%</span>
                    </div>
                    {data.sensitivity.stats && (
                      <div>
                        Rentang FV: Rp {fmtIDR(data.sensitivity.stats.min)} - Rp {fmtIDR(data.sensitivity.stats.max)}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            <div className="text-right text-[11px] text-slate-400">
              {data.provenance || "dcf_full : friend s05-s12 engine"}
            </div>
          </>
        )}
      </div>
    </details>
  )
}
