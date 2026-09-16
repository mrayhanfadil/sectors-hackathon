import React from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { RecommendationBadge } from "./RecommendationBadge"
import { HistoryCharts } from "./charts/HistoryCharts"
import { formatIdn } from "./charts/tokens"
import type {
  FullReportPayload,
  CoverSection,
  CoverSlide1,
  CoverSlide2,
  FinancialHighlights,
  IndustryPage,
  ThesisItem,
} from "@/lib/reportTypes"

export interface ExecutiveSummaryProps {
  ticker: string
  payload?: FullReportPayload | null
}

function fmtIDR(n: number | null | undefined): string {
  if (n == null || Number.isNaN(Number(n))) return "-"
  return Number(n).toLocaleString("id-ID")
}

function formatHighlightCell(c: unknown): string {
  if (c == null) return "-"
  if (typeof c === "number") {
    if (!Number.isFinite(c)) return "-"
    const hasDecimals = !Number.isInteger(c)
    const decStr = String(c).split(".")[1] || ""
    const digits = Math.min(Math.max(decStr.length, hasDecimals ? 1 : 0), 2)
    return formatIdn(c, digits)
  }
  return String(c)
}

function PendingCard({ label }: { label: string }) {
  return (
    <div className="rounded-xl border border-[#E7E3DA] bg-white p-6 text-center text-xs text-[#6B6659] dark:border-[#2A2822] dark:bg-[#1B1A16] dark:text-[#A8A296]">
      {label} belum tersedia di payload.
    </div>
  )
}

function SvgPriceVsJci({
  labels = [],
  price = [],
  relPct = [],
  tickerLabel = "",
}: {
  labels?: string[]
  price?: number[]
  relPct?: number[]
  tickerLabel?: string
}) {
  if (!labels.length || (!price.length && !relPct.length)) {
    return (
      <div className="flex h-36 items-center justify-center rounded-lg border border-[#E7E3DA] bg-[#FBFAF7] text-xs text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
        Grafik harga vs IHSG belum tersedia di payload
      </div>
    )
  }

  const W = 340
  const H = 220
  const padL = 40
  const padR = 40
  const padT = 24
  const padB = 26
  const chartW = W - padL - padR
  const chartH = H - padT - padB
  const n = labels.length
  const step = n > 1 ? chartW / (n - 1) : 0

  const pVals = price.filter((v) => typeof v === "number" && !Number.isNaN(v))
  const rVals = relPct.filter((v) => typeof v === "number" && !Number.isNaN(v))

  const pMinRaw = pVals.length ? Math.min(...pVals) : 0
  const pMaxRaw = pVals.length ? Math.max(...pVals) : 1
  const pHead = (pMaxRaw - pMinRaw) * 0.08 || 1
  const pMin = pMinRaw - pHead
  const pMax = pMaxRaw + pHead
  const pRange = pMax - pMin || 1

  const rMinRaw = rVals.length ? Math.min(...rVals) : -10
  const rMaxRaw = rVals.length ? Math.max(...rVals) : 10
  const rHead = (rMaxRaw - rMinRaw) * 0.08 || 1
  const rMin = rMinRaw - rHead
  const rMax = rMaxRaw + rHead
  const rRange = rMax - rMin || 1

  const ptsP = price
    .map((v, i) => {
      const x = padL + i * step
      const y = padT + chartH - ((v - pMin) / pRange) * chartH
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(" ")

  const ptsR = relPct
    .map((v, i) => {
      const x = padL + i * step
      const y = padT + chartH - ((v - rMin) / rRange) * chartH
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(" ")

  const yZero = padT + chartH - ((0 - rMin) / rRange) * chartH
  const lastP = price.length ? price[price.length - 1] : null
  const yLastP = lastP != null ? padT + chartH - ((lastP - pMin) / pRange) * chartH : null

  return (
    <div className="space-y-1">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full h-auto rounded-lg border border-[#E7E3DA] bg-white text-xs dark:border-[#2A2822] dark:bg-[#1B1A16]"
        role="img"
        aria-label={`Harga ${tickerLabel} vs IHSG`}
      >
        {/* Grid lines */}
        {Array.from({ length: 4 }, (_, i) => i).map((i) => {
          const y = padT + (i * chartH) / 3
          const pVal = pMax - (i * (pMax - pMin)) / 3
          const rVal = rMax - (i * (rMax - rMin)) / 3
          return (
            <g key={i}>
              <line
                x1={padL}
                y1={y}
                x2={W - padR}
                y2={y}
                stroke="#E7E3DA"
                strokeWidth={0.7}
                strokeDasharray="3 3"
              />
              <text
                x={padL - 4}
                y={y + 3}
                fontSize={8}
                fontFamily="monospace"
                fill="#6B6659"
                textAnchor="end"
              >
                {Math.round(pVal)}
              </text>
              <text
                x={W - padR + 4}
                y={y + 3}
                fontSize={8}
                fontFamily="monospace"
                fill="#6B6659"
                textAnchor="start"
              >
                {rVal > 0 ? `+${Math.round(rVal)}` : Math.round(rVal)}%
              </text>
            </g>
          )
        })}

        {/* Relative Zero line */}
        {yZero >= padT && yZero <= padT + chartH && (
          <line
            x1={padL}
            y1={yZero}
            x2={W - padR}
            y2={yZero}
            stroke="#A8A296"
            strokeWidth={1}
            strokeDasharray="2 2"
          />
        )}

        {/* Shaded Price Area & Lines */}
        {ptsP && (
          <>
            <polygon
              points={`${padL},${padT + chartH} ${ptsP} ${padL + (n - 1) * step},${padT + chartH}`}
              fill="rgba(14,110,99,0.06)"
            />
            <polyline
              points={ptsP}
              fill="none"
              stroke="#0E6E63"
              strokeWidth={2}
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          </>
        )}

        {ptsR && (
          <polyline
            points={ptsR}
            fill="none"
            stroke="#A8A296"
            strokeWidth={1.5}
            strokeLinejoin="round"
            strokeLinecap="round"
          />
        )}

        {/* Last Price Marker */}
        {lastP != null && yLastP != null && (
          <g>
            <line
              x1={padL}
              y1={yLastP}
              x2={W - padR}
              y2={yLastP}
              stroke="#B4232A"
              strokeWidth={1}
              strokeDasharray="3 2"
            />
            <rect
              x={padL + 2}
              y={yLastP - 10}
              width={76}
              height={10}
              rx={2}
              fill="#FFFFFF"
              opacity={0.92}
            />
            <text
              x={padL + 4}
              y={yLastP - 2}
              fontSize={8}
              fontFamily="monospace"
              fontWeight="bold"
              fill="#B4232A"
            >
              Terakhir {fmtIDR(lastP)}
            </text>
          </g>
        )}

        {/* X-axis Labels */}
        {labels.map((lbl, i) => {
          if (i % 2 === 0 || i === labels.length - 1) {
            const x = padL + i * step
            return (
              <text
                key={i}
                x={x}
                y={H - 6}
                fontSize={8}
                fontFamily="monospace"
                fill="#6B6659"
                textAnchor="middle"
              >
                {lbl}
              </text>
            )
          }
          return null
        })}

        {/* Legend */}
        <g fontSize={8} fontFamily="sans-serif">
          <line x1={padL} y1={padT - 12} x2={padL + 12} y2={padT - 12} stroke="#0E6E63" strokeWidth={2} />
          <text x={padL + 16} y={padT - 9} fill="#1C1B17" fontWeight="bold">
            Harga (Rp, kiri)
          </text>
          <line x1={padL + 110} y1={padT - 12} x2={padL + 122} y2={padT - 12} stroke="#A8A296" strokeWidth={1.5} />
          <text x={padL + 126} y={padT - 9} fill="#6B6659">
            Relatif vs IHSG (%, kanan)
          </text>
        </g>
      </svg>
    </div>
  )
}

export function ExecutiveSummary({ ticker, payload }: ExecutiveSummaryProps) {
  const tk = ticker.toUpperCase()
  const cover: CoverSection | undefined = payload?.cover
  const s1: CoverSlide1 | undefined = cover?.slide1
  const s2: CoverSlide2 | undefined = cover?.slide2
  const meta = payload?.meta
  const industryPage: IndustryPage | undefined = payload?.industry_page
  const thesis: ThesisItem[] = payload?.thesis || []
  const highlights6y: FinancialHighlights | undefined = payload?.financial_highlights

  // Rating and key info
  const action = s1?.rating?.action || cover?.rating_box?.action || "-"
  const actionStatus = s1?.rating?.action_status || "Riset ekuitas institusional"
  const prevAction = s1?.rating?.prev_action
  const prevTp = s1?.rating?.prev_tp ?? cover?.rating_box?.prev_tp
  const price = cover?.rating_box?.price
  const tp = cover?.rating_box?.tp
  const upsidePct = cover?.rating_box?.upside_pct
  const companyName = meta?.company_name || `${tk} Tbk.`

  // Highlights list
  const highlights = s1?.highlights || cover?.rating_box?.key_takeaways || []
  const shareholders = s1?.stats?.major_shareholders || cover?.shareholders || []
  const priceBoxRows = s1?.price_box?.rows || []
  const statsRows = s1?.stats?.rows || []

  // JCI Chart data
  const jciLabels = s1?.jci_chart?.labels || cover?.vs_jci?.chart?.labels || []
  const jciPrice = s1?.jci_chart?.price || cover?.vs_jci?.chart?.series?.[0] || []
  const jciRel = s1?.jci_chart?.rel_pct || cover?.vs_jci?.chart?.series?.[1] || []
  const jciSource = s1?.jci_chart?.source || cover?.vs_jci?.source || "Sectors API / yfinance"

  // Key Financials
  const kf = s2?.key_financials || payload?.key_financials

  return (
    <div className="space-y-8">
      {/* ========================================================================= */}
      {/* SECTION 1: COVER & RATING                                                 */}
      {/* ========================================================================= */}
      <section id="cover-rating" className="scroll-mt-28 space-y-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#E7E3DA] pb-2 dark:border-[#2A2822]">
          <h2 className="font-serif text-xl font-medium tracking-tight text-[#1C1B17] dark:text-[#EDEAE3]">
            Ringkasan dan peringkat {tk}
          </h2>
          <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
            Ikhtisar emiten
          </span>
        </div>

        {cover ? (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-[34%_66%] items-start">
            {/* Left Column */}
            <div className="space-y-4">
              {/* Rating & Stats Card */}
              <div className="rounded-xl border border-[#E7E3DA] bg-white p-5 space-y-4 dark:border-[#2A2822] dark:bg-[#1B1A16]">
                {/* Rating Display */}
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">Rekomendasi</span>
                    <RecommendationBadge rating={action} size="md" />
                  </div>
                  <div className="text-xs text-[#6B6659] mt-1.5 dark:text-[#A8A296]">
                    {actionStatus}
                    {prevAction && <span className="ml-1">(Sebelumnya: {prevAction})</span>}
                  </div>
                </div>

                {/* Price Box Table */}
                <div className="border-t border-[#E7E3DA] pt-3 dark:border-[#2A2822]">
                  <table className="w-full text-xs">
                    <tbody className="divide-y divide-[#E7E3DA]/60 dark:divide-[#2A2822]/60">
                      {priceBoxRows.length > 0 ? (
                        priceBoxRows.map((row, i) => (
                          <tr key={i}>
                            <td className="py-1.5 text-[#6B6659] dark:text-[#A8A296]">{row[0]}</td>
                            <td className="py-1.5 text-right font-medium text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
                              {row[1]}
                            </td>
                          </tr>
                        ))
                      ) : (
                        <>
                          <tr>
                            <td className="py-1.5 text-[#6B6659] dark:text-[#A8A296]">Harga pasar</td>
                            <td className="py-1.5 text-right font-medium text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
                              {price != null ? `Rp ${fmtIDR(price)}` : "-"}
                            </td>
                          </tr>
                          <tr>
                            <td className="py-1.5 text-[#6B6659] dark:text-[#A8A296]">Nilai wajar (TP)</td>
                            <td className="py-1.5 text-right font-medium text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
                              {tp != null ? `Rp ${fmtIDR(tp)}` : "-"}
                            </td>
                          </tr>
                          {prevTp != null && (
                            <tr>
                              <td className="py-1.5 text-[#6B6659] dark:text-[#A8A296]">TP sebelumnya</td>
                              <td className="py-1.5 text-right text-[#6B6659] font-mono tabular-nums dark:text-[#A8A296]">
                                Rp {fmtIDR(prevTp)}
                              </td>
                            </tr>
                          )}
                          <tr>
                            <td className="py-1.5 text-[#6B6659] dark:text-[#A8A296]">Potensi return</td>
                            <td className="py-1.5 text-right font-semibold text-[#157F3D] font-mono tabular-nums dark:text-[#34D399]">
                              {upsidePct != null ? `${upsidePct > 0 ? "+" : ""}${upsidePct.toFixed(1)}%` : "-"}
                            </td>
                          </tr>
                        </>
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Secondary Stats Table */}
                {statsRows.length > 0 && (
                  <div className="border-t border-[#E7E3DA] pt-3 dark:border-[#2A2822]">
                    <table className="w-full text-xs">
                      <tbody className="divide-y divide-[#E7E3DA]/60 dark:divide-[#2A2822]/60">
                        {statsRows.map((row, i) => (
                          <tr key={i}>
                            <td className="py-1.5 text-[#6B6659] dark:text-[#A8A296]">{row[0]}</td>
                            <td className="py-1.5 text-right font-medium text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
                              {row[1]}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Major Shareholders Table */}
                {shareholders.length > 0 && (
                  <div className="border-t border-[#E7E3DA] pt-3 space-y-2 dark:border-[#2A2822]">
                    <div className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                      Pemegang saham utama (%)
                    </div>
                    <table className="w-full text-xs">
                      <tbody className="divide-y divide-[#E7E3DA]/60 dark:divide-[#2A2822]/60">
                        {shareholders.map((h, i) => (
                          <tr key={i}>
                            <td className="py-1.5 text-[#1C1B17] truncate max-w-[140px] dark:text-[#EDEAE3]">
                              {h.name}
                            </td>
                            <td className="py-1.5 text-right font-medium text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
                              {h.pct_str || `${h.pct}%`}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Relative to JCI Chart */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-medium text-[#1C1B17] dark:text-[#EDEAE3]">
                  <span>Harga {tk} relatif terhadap IHSG</span>
                </div>
                <SvgPriceVsJci
                  labels={jciLabels}
                  price={jciPrice}
                  relPct={jciRel}
                  tickerLabel={tk}
                />
                <div className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">
                  Sumber: {jciSource}
                </div>
              </div>

              {/* Analyst Attribution */}
              {s1?.analyst && (
                <div className="rounded-xl border border-[#E7E3DA] bg-white p-3.5 text-xs dark:border-[#2A2822] dark:bg-[#1B1A16]">
                  <div className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">
                    Analis penyusun
                  </div>
                  <div className="font-semibold text-[#1C1B17] mt-0.5 dark:text-[#EDEAE3]">
                    {s1.analyst.name}
                  </div>
                  <div className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">{s1.analyst.title}</div>
                </div>
              )}
            </div>

            {/* Right Column */}
            <div className="space-y-5">
              {/* Title & Theme */}
              <div>
                <h1 className="font-serif text-2xl font-medium tracking-tight text-[#1C1B17] dark:text-[#EDEAE3]">
                  {companyName} <span className="text-[#6B6659] font-normal dark:text-[#A8A296]">({tk})</span>
                </h1>
                {s1?.theme_title && (
                  <p className="text-sm italic text-[#6B6659] mt-1 dark:text-[#A8A296]">
                    {s1.theme_title}
                  </p>
                )}
              </div>

              {/* Highlights Box */}
              {highlights.length > 0 && (
                <div className="rounded-xl border border-[#E7E3DA] bg-[#FBFAF7] p-5 dark:border-[#2A2822] dark:bg-[#1B1A16]/60">
                  <div className="text-xs font-semibold text-[#0E6E63] mb-3 dark:text-[#4FD1B5]">
                    Poin-poin utama:
                  </div>
                  <ul className="space-y-2 pl-4 list-disc text-sm text-[#1C1B17] dark:text-[#EDEAE3] leading-relaxed">
                    {highlights.map((h, i) => (
                      <li key={i}>{h}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Narrative paragraphs */}
              {s1?.financial_para && (
                <div className="space-y-1.5">
                  <h3 className="text-sm font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                    {s1.financial_para.heading}
                  </h3>
                  <p className="text-sm leading-relaxed text-[#1C1B17] text-justify dark:text-[#EDEAE3]/90">
                    {s1.financial_para.body}
                  </p>
                </div>
              )}

              {s2?.katalis && (
                <div className="space-y-1.5">
                  <h3 className="text-sm font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                    {s2.katalis.heading}
                  </h3>
                  <p className="text-sm leading-relaxed text-[#1C1B17] text-justify dark:text-[#EDEAE3]/90">
                    {s2.katalis.body}
                  </p>
                </div>
              )}

              {s2?.valuasi && (
                <div className="space-y-1.5">
                  <h3 className="text-sm font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                    {s2.valuasi.heading}
                  </h3>
                  <p className="text-sm leading-relaxed text-[#1C1B17] text-justify dark:text-[#EDEAE3]/90">
                    {s2.valuasi.body}
                  </p>
                </div>
              )}

              {cover.summary && !s1?.financial_para && (
                <div className="text-sm leading-relaxed text-[#1C1B17] text-justify dark:text-[#EDEAE3]/90">
                  {cover.summary}
                </div>
              )}
            </div>
          </div>
        ) : (
          <PendingCard label="Cover dan peringkat" />
        )}
      </section>

      {/* ========================================================================= */}
      {/* SECTION 2: KEY FINANCIALS & 6-YEAR HIGHLIGHTS                             */}
      {/* ========================================================================= */}
      <section id="key-financials" className="scroll-mt-28 space-y-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#E7E3DA] pb-2 dark:border-[#2A2822]">
          <h2 className="font-serif text-xl font-medium tracking-tight text-[#1C1B17] dark:text-[#EDEAE3]">
            Ringkasan keuangan dan proyeksi
          </h2>
          <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
            Proyeksi 3 tahun
          </span>
        </div>

        {kf && kf.headers && kf.rows ? (
          <Card className="rounded-xl border border-[#E7E3DA] bg-white dark:border-[#2A2822] dark:bg-[#1B1A16]">
            <CardHeader className="border-b border-[#E7E3DA] p-5 pb-3 dark:border-[#2A2822]">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                  {("exhibit_title" in kf ? kf.exhibit_title : "") || ("title" in kf ? kf.title : "") || "Ringkasan metrik keuangan (2024A–2028F)"}
                </CardTitle>
                <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
                  {kf.source || "Sumber: Laporan keuangan emiten"}
                </span>
              </div>
            </CardHeader>
            <CardContent className="p-5 space-y-3">
              <div className="overflow-x-auto rounded-lg border border-[#E7E3DA] dark:border-[#2A2822]">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-[#E7E3DA] bg-[#FBFAF7] text-right text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
                      {kf.headers.map((h, i) => (
                        <th key={i} className={`py-2.5 px-3 font-semibold ${i === 0 ? "text-left text-[#1C1B17] dark:text-[#EDEAE3]" : ""}`}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E7E3DA]/60 dark:divide-[#2A2822]/60">
                    {kf.rows.map((row, rIdx) => {
                      const isBold =
                        String(row[0]).includes("Revenue") ||
                        String(row[0]).includes("EBITDA (Rpbn)") ||
                        String(row[0]).includes("Net Profit");
                      return (
                        <tr
                          key={rIdx}
                          className={`${
                            rIdx % 2 === 1 ? "bg-[#FBFAF7]/50 dark:bg-[#14130F]/30" : "bg-white dark:bg-[#1B1A16]"
                          } ${isBold ? "font-semibold text-[#1C1B17] dark:text-[#EDEAE3]" : "text-[#1C1B17] dark:text-[#EDEAE3]/90"}`}
                        >
                          {row.map((cell, cIdx) => (
                            <td
                              key={cIdx}
                              className={`py-2 px-3 ${cIdx === 0 ? "text-left font-sans" : "text-right font-mono tabular-nums"}`}
                            >
                              {cIdx === 0 ? (cell != null ? String(cell) : "-") : formatHighlightCell(cell)}
                            </td>
                          ))}
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>

              {"notes" in kf && Array.isArray(kf.notes) && kf.notes.length > 0 && (
                <div className="space-y-1 text-xs text-[#6B6659] leading-relaxed dark:text-[#A8A296]">
                  {(kf.notes as string[]).map((nt: string, idx: number) => (
                    <p key={idx}>{nt}</p>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        ) : (
          <PendingCard label="Ringkasan metrik keuangan" />
        )}

        {/* 6-Year Financial Highlights */}
        {highlights6y && highlights6y.years && highlights6y.rows && (
          <Card className="rounded-xl border border-[#E7E3DA] bg-white dark:border-[#2A2822] dark:bg-[#1B1A16]">
            <CardHeader className="border-b border-[#E7E3DA] p-5 pb-3 dark:border-[#2A2822]">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                  Sorotan keuangan ({highlights6y.years.length} tahun)
                </CardTitle>
                <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
                  Sumber: {highlights6y.source || "Laporan keuangan IDX"}
                </span>
              </div>
            </CardHeader>
            <CardContent className="p-5 space-y-2">
              <div className="overflow-x-auto rounded-lg border border-[#E7E3DA] dark:border-[#2A2822]">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-[#E7E3DA] bg-[#FBFAF7] text-right text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
                      <th className="py-2.5 px-3 text-left font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">Pos keuangan</th>
                      {highlights6y.years.map((y, i) => (
                        <th key={i} className="py-2.5 px-3 text-right font-semibold">
                          {y}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E7E3DA]/60 dark:divide-[#2A2822]/60">
                    {highlights6y.rows.map((r, rIdx) => (
                      <tr
                        key={rIdx}
                        className={`${
                          rIdx % 2 === 1 ? "bg-[#FBFAF7]/50 dark:bg-[#14130F]/30" : "bg-white dark:bg-[#1B1A16]"
                        }`}
                      >
                        {r.map((c, cIdx) => (
                          <td
                            key={cIdx}
                            className={`py-2 px-3 ${cIdx === 0 ? "text-left font-medium text-[#1C1B17] dark:text-[#EDEAE3]" : "text-right font-mono tabular-nums text-[#1C1B17] dark:text-[#EDEAE3]/90"}`}
                          >
                            {cIdx === 0 ? (c != null ? String(c) : "-") : formatHighlightCell(c)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Visualisasi Tren Historis */}
        <HistoryCharts payload={payload} />

        {/* Kondisi Industri, Katalis & Sentimen */}
        {industryPage && industryPage.paragraphs && industryPage.paragraphs.length > 0 && (
          <Card className="rounded-xl border border-[#E7E3DA] bg-white dark:border-[#2A2822] dark:bg-[#1B1A16]">
            <CardHeader className="border-b border-[#E7E3DA] p-5 pb-3 dark:border-[#2A2822]">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                  {industryPage.title || "Kondisi industri, katalis dan sentimen"}
                </CardTitle>
                {industryPage.sources && (
                  <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
                    {industryPage.sources.join("; ")}
                  </span>
                )}
              </div>
            </CardHeader>
            <CardContent className="p-5 space-y-4">
              {industryPage.paragraphs.map((p, idx) => (
                <div key={idx} className="space-y-1.5">
                  <h4 className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                    {p.heading}
                  </h4>
                  <p className="text-sm leading-relaxed text-[#1C1B17] text-justify dark:text-[#EDEAE3]/90">
                    {p.body}
                  </p>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Tesis Investasi - 4 Pilar */}
        {thesis.length > 0 && (
          <Card className="rounded-xl border border-[#E7E3DA] bg-white dark:border-[#2A2822] dark:bg-[#1B1A16]">
            <CardHeader className="border-b border-[#E7E3DA] p-5 pb-3 dark:border-[#2A2822]">
              <CardTitle className="text-sm font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                Tesis investasi - 4 pilar utama
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5">
              <div className="space-y-4">
                {thesis.map((t, idx) => (
                  <div
                    key={idx}
                    className="grid grid-cols-[28px_1fr_auto] gap-3 items-start border-t border-[#E7E3DA] pt-3 first:border-0 first:pt-0 dark:border-[#2A2822]"
                  >
                    <span className="font-serif text-base font-semibold text-[#0E6E63] dark:text-[#4FD1B5]">
                      {idx + 1}.
                    </span>
                    <div className="space-y-1">
                      <h4 className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                        {t.headline}
                      </h4>
                      <p className="text-xs text-[#6B6659] leading-relaxed dark:text-[#A8A296]">
                        {t.detail}
                      </p>
                    </div>
                    {t.stat && (
                      <div className="text-right pl-3 shrink-0">
                        <div className="text-xs font-semibold text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
                          {t.stat}
                        </div>
                        {t.stat_label && (
                          <div className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">
                            {t.stat_label}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </section>
    </div>
  )
}
