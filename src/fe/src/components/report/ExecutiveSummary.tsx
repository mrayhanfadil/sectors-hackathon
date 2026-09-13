import React from "react"
import { Users, LineChart, Target, Hash, Building2, UserCheck, TrendingUp, Info } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { RecommendationBadge } from "./RecommendationBadge"
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
  if (n == null || Number.isNaN(Number(n))) return "—"
  return Number(n).toLocaleString("id-ID")
}

function PendingCard({ label }: { label: string }) {
  return (
    <div className="rounded-md border border-[#D6E2EE] bg-[#F4F8FC] p-4 text-center font-mono text-xs text-[#63748A] dark:border-[#262930] dark:bg-[#121316]">
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
      <div className="flex h-36 items-center justify-center rounded border border-[#D6E2EE] bg-white font-mono text-[11px] text-[#63748A]">
        Grafik harga vs IHSG belum tersedia di payload
      </div>
    )
  }

  const W = 340
  const H = 220
  const padL = 36
  const padR = 36
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
        className="w-full h-auto rounded border border-[#D6E2EE] bg-white text-xs"
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
                stroke="#D6E2EE"
                strokeWidth={0.7}
                strokeDasharray="3 3"
              />
              <text
                x={padL - 3}
                y={y + 3}
                fontSize={8.5}
                fontFamily="monospace"
                fill="#0B1F3A"
                textAnchor="end"
              >
                {Math.round(pVal)}
              </text>
              <text
                x={W - padR + 3}
                y={y + 3}
                fontSize={8.5}
                fontFamily="monospace"
                fill="#63748A"
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
            stroke="#63748A"
            strokeWidth={1}
            strokeDasharray="2 2"
          />
        )}

        {/* Shaded Price Area & Lines */}
        {ptsP && (
          <>
            <polygon
              points={`${padL},${padT + chartH} ${ptsP} ${padL + (n - 1) * step},${padT + chartH}`}
              fill="rgba(11,31,58,0.06)"
            />
            <polyline
              points={ptsP}
              fill="none"
              stroke="#0B1F3A"
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
            stroke="#A9C9E8"
            strokeWidth={1.8}
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
              stroke="#C0392B"
              strokeWidth={1}
              strokeDasharray="3 2"
            />
            <rect
              x={padL + 2}
              y={yLastP - 10}
              width={76}
              height={10}
              rx={1.5}
              fill="#ffffff"
              opacity={0.92}
            />
            <text
              x={padL + 4}
              y={yLastP - 2}
              fontSize={8.5}
              fontFamily="monospace"
              fontWeight="bold"
              fill="#C0392B"
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
                fill="#63748A"
                textAnchor="middle"
              >
                {lbl}
              </text>
            )
          }
          return null
        })}

        {/* Legend */}
        <g fontSize={8.5} fontFamily="monospace">
          <line x1={padL} y1={padT - 12} x2={padL + 14} y2={padT - 12} stroke="#0B1F3A" strokeWidth={2} />
          <text x={padL + 18} y={padT - 9} fill="#0B1F3A" fontWeight="bold">
            Harga (Rp, kiri)
          </text>
          <line x1={padL + 115} y1={padT - 12} x2={padL + 129} y2={padT - 12} stroke="#A9C9E8" strokeWidth={2} />
          <text x={padL + 133} y={padT - 9} fill="#63748A">
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
  const action = s1?.rating?.action || cover?.rating_box?.action || "—"
  const actionStatus = s1?.rating?.action_status || "Institutional Research"
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
    <div className="space-y-6">
      {/* ========================================================================= */}
      {/* BAB 1: COVER & RATING (ONE-PAGER INSTITUSIONAL)                           */}
      {/* ========================================================================= */}
      <section id="cover-rating" className="scroll-mt-28 space-y-3">
        {/* Section Header */}
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#D6E2EE] pb-2 dark:border-[#262930]">
          <div className="flex items-center gap-2">
            <span className="rounded bg-[#0B1F3A] px-1.5 py-0.5 font-mono text-[10px] font-bold text-[#E4EEF7] dark:bg-[#0B1F3A] dark:text-[#A9C9E8]">
              01
            </span>
            <h2 className="font-sans text-sm font-bold tracking-tight text-[#0B1F3A] dark:text-neutral-100 uppercase">
              Cover &amp; Rating Box // {tk}
            </h2>
          </div>
          <span className="font-mono text-[11px] text-[#63748A]">
            One-Pager Institusional
          </span>
        </div>

        {cover ? (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-[32%_68%] items-start">
            {/* Left Sidebar (~32%) */}
            <div className="space-y-3 font-mono">
              {/* Tinted Panel: Rating -> Price Box -> Stats -> Shareholders */}
              <div className="rounded-md border border-[#D6E2EE] bg-[#F4F8FC] p-3.5 space-y-3 dark:border-[#262930] dark:bg-[#121316]">
                {/* Big Rating Banner */}
                <div>
                  <div className="text-2xl font-black tracking-tight text-[#0B1F3A] dark:text-[#A9C9E8]">
                    {action}
                  </div>
                  <div className="text-xs italic text-[#63748A] mt-0.5">
                    {actionStatus}
                    {prevAction && <span className="ml-1 text-[10px]">(Sebelumnya: {prevAction})</span>}
                  </div>
                </div>

                {/* Price Box Table */}
                <div className="border-t border-[#D6E2EE] pt-2.5">
                  <table className="w-full text-xs">
                    <tbody>
                      {priceBoxRows.length > 0 ? (
                        priceBoxRows.map((row, i) => (
                          <tr key={i} className="border-b border-[#D6E2EE]/60 last:border-0">
                            <td className="py-1 text-[#63748A]">{row[0]}</td>
                            <td className="py-1 text-right font-bold text-[#0B1F3A] tabular-nums dark:text-neutral-100">
                              {row[1]}
                            </td>
                          </tr>
                        ))
                      ) : (
                        <>
                          <tr className="border-b border-[#D6E2EE]/60">
                            <td className="py-1 text-[#63748A]">Harga Pasar</td>
                            <td className="py-1 text-right font-bold text-[#0B1F3A] tabular-nums dark:text-neutral-100">
                              {price != null ? `Rp ${fmtIDR(price)}` : "—"}
                            </td>
                          </tr>
                          <tr className="border-b border-[#D6E2EE]/60">
                            <td className="py-1 text-[#63748A]">Target Price (TP)</td>
                            <td className="py-1 text-right font-bold text-[#0B1F3A] tabular-nums dark:text-neutral-100">
                              {tp != null ? `Rp ${fmtIDR(tp)}` : "—"}
                            </td>
                          </tr>
                          {prevTp != null && (
                            <tr className="border-b border-[#D6E2EE]/60">
                              <td className="py-1 text-[#63748A]">TP Sebelumnya</td>
                              <td className="py-1 text-right text-[#63748A] tabular-nums">
                                Rp {fmtIDR(prevTp)}
                              </td>
                            </tr>
                          )}
                          <tr>
                            <td className="py-1 text-[#63748A]">Potensi Return</td>
                            <td className="py-1 text-right font-bold text-[#1E8F5F] tabular-nums">
                              {upsidePct != null ? `${upsidePct > 0 ? "+" : ""}${upsidePct.toFixed(1)}%` : "—"}
                            </td>
                          </tr>
                        </>
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Secondary Stats Table */}
                {statsRows.length > 0 && (
                  <div className="border-t border-[#D6E2EE] pt-2.5">
                    <table className="w-full text-xs">
                      <tbody>
                        {statsRows.map((row, i) => (
                          <tr key={i} className="border-b border-[#D6E2EE]/60 last:border-0">
                            <td className="py-1 text-[#63748A]">{row[0]}</td>
                            <td className="py-1 text-right font-bold text-[#0B1F3A] tabular-nums dark:text-neutral-100">
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
                  <div className="border-t border-[#D6E2EE] pt-2.5 space-y-1.5">
                    <div className="text-[10px] font-bold uppercase tracking-wider text-[#63748A]">
                      Major Shareholder (%)
                    </div>
                    <table className="w-full text-xs">
                      <tbody>
                        {shareholders.map((h, i) => (
                          <tr key={i} className="border-b border-[#D6E2EE]/60 last:border-0">
                            <td className="py-1 text-[#0B1F3A] truncate max-w-[140px] dark:text-neutral-300">
                              {h.name}
                            </td>
                            <td className="py-1 text-right font-bold text-[#0B1F3A] tabular-nums dark:text-neutral-100">
                              {h.pct_str || `${h.pct}%`}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Relative to JCI Index Chart */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-[11px] font-bold text-[#0B1F3A] dark:text-neutral-200">
                  <span>{tk} relative to JCI Index</span>
                </div>
                <SvgPriceVsJci
                  labels={jciLabels}
                  price={jciPrice}
                  relPct={jciRel}
                  tickerLabel={tk}
                />
                <div className="text-[10px] text-[#63748A] italic">
                  Source: {jciSource}
                </div>
              </div>

              {/* Analyst Attribution */}
              {s1?.analyst && (
                <div className="rounded-md border border-[#D6E2EE] bg-white p-2.5 text-xs dark:border-[#262930] dark:bg-[#121316]">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-[#63748A]">
                    Sectors.app Analysts
                  </div>
                  <div className="font-bold text-[#0B1F3A] mt-0.5 dark:text-neutral-100">
                    {s1.analyst.name}
                  </div>
                  <div className="text-[11px] text-[#63748A]">{s1.analyst.title}</div>
                </div>
              )}
            </div>

            {/* Right Main Column (~68%) */}
            <div className="space-y-3.5">
              {/* Header Title & Theme */}
              <div>
                <h1 className="text-xl font-extrabold tracking-tight text-[#0B1F3A] dark:text-neutral-100">
                  {companyName} <span className="text-[#63748A] font-normal">({tk} IJ)</span>
                </h1>
                {s1?.theme_title && (
                  <p className="text-sm italic font-medium text-[#63748A] mt-0.5">
                    {s1.theme_title}
                  </p>
                )}
              </div>

              {/* Key Highlights Callout (Tinted box with brand spine) */}
              {highlights.length > 0 && (
                <div className="rounded-r-md border-l-[3px] border-[#0B1F3A] bg-[#F4F8FC] p-3.5 dark:border-[#A9C9E8] dark:bg-[#121316]">
                  <div className="text-xs font-bold uppercase tracking-wider text-[#0B1F3A] mb-2 dark:text-[#A9C9E8]">
                    Key Highlights:
                  </div>
                  <ul className="space-y-1.5 pl-4 list-disc text-xs sm:text-[13px] text-[#0B1F3A] dark:text-neutral-200 leading-relaxed font-medium">
                    {highlights.map((h, i) => (
                      <li key={i}>{h}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Body Paragraphs */}
              {s1?.financial_para && (
                <div className="space-y-1">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-neutral-100">
                    {s1.financial_para.heading}
                  </h3>
                  <p className="text-xs sm:text-[13px] leading-relaxed text-[#0B1F3A] text-justify dark:text-neutral-300">
                    {s1.financial_para.body}
                  </p>
                </div>
              )}

              {s2?.katalis && (
                <div className="space-y-1">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-neutral-100">
                    {s2.katalis.heading}
                  </h3>
                  <p className="text-xs sm:text-[13px] leading-relaxed text-[#0B1F3A] text-justify dark:text-neutral-300">
                    {s2.katalis.body}
                  </p>
                </div>
              )}

              {s2?.valuasi && (
                <div className="space-y-1">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-neutral-100">
                    {s2.valuasi.heading}
                  </h3>
                  <p className="text-xs sm:text-[13px] leading-relaxed text-[#0B1F3A] text-justify dark:text-neutral-300">
                    {s2.valuasi.body}
                  </p>
                </div>
              )}

              {cover.summary && !s1?.financial_para && (
                <div className="text-xs sm:text-[13px] leading-relaxed text-[#0B1F3A] text-justify dark:text-neutral-300">
                  {cover.summary}
                </div>
              )}
            </div>
          </div>
        ) : (
          <PendingCard label="Cover & rating" />
        )}
      </section>

      {/* ========================================================================= */}
      {/* BAB 2: KEY FINANCIALS (2024A-2028F) & RINGKASAN HISTORIS                  */}
      {/* ========================================================================= */}
      <section id="key-financials" className="scroll-mt-28 space-y-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#D6E2EE] pb-2 dark:border-[#262930]">
          <div className="flex items-center gap-2">
            <span className="rounded bg-[#0B1F3A] px-1.5 py-0.5 font-mono text-[10px] font-bold text-[#E4EEF7] dark:bg-[#0B1F3A] dark:text-[#A9C9E8]">
              02
            </span>
            <h2 className="font-sans text-sm font-bold tracking-tight text-[#0B1F3A] dark:text-neutral-100 uppercase">
              Key Financials &amp; Proyeksi Deterministik // {tk}
            </h2>
          </div>
          <span className="font-mono text-[11px] text-[#63748A]">
            Proyeksi 3 Tahun
          </span>
        </div>

        {kf && kf.headers && kf.rows ? (
          <Card className="rounded-lg border border-[#D6E2EE] bg-white shadow-xs dark:border-[#262930] dark:bg-[#121418]">
            <CardHeader className="border-b border-[#D6E2EE] bg-[#F4F8FC] p-4 pb-3 dark:border-[#1f2228] dark:bg-[#181a1f]">
              <div className="flex items-center justify-between">
                <CardTitle className="font-mono text-xs font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-neutral-100">
                  {("exhibit_title" in kf ? kf.exhibit_title : "") || ("title" in kf ? kf.title : "") || "Key Financials (2024A–2028F)"}
                </CardTitle>
                <span className="font-mono text-[10px] text-[#63748A]">
                  {kf.source || "Source: Company, Team Estimates"}
                </span>
              </div>
            </CardHeader>
            <CardContent className="p-4 sm:p-5 space-y-3">
              <div className="overflow-x-auto rounded border border-[#D6E2EE] font-mono text-xs dark:border-[#262930]">
                <table className="w-full">
                  <thead>
                    <tr className="bg-[#0B1F3A] text-white text-right text-[11px]">
                      {kf.headers.map((h, i) => (
                        <th key={i} className={`py-2 px-3 ${i === 0 ? "text-left" : ""}`}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {kf.rows.map((row, rIdx) => {
                      const isBold =
                        String(row[0]).includes("Revenue") ||
                        String(row[0]).includes("EBITDA (Rpbn)") ||
                        String(row[0]).includes("Net Profit");
                      return (
                        <tr
                          key={rIdx}
                          className={`border-b border-[#D6E2EE]/60 last:border-0 ${
                            rIdx % 2 === 1 ? "bg-[#F4F8FC] dark:bg-[#181a1f]" : "bg-white dark:bg-[#121316]"
                          } ${isBold ? "font-bold text-[#0B1F3A] dark:text-neutral-100" : "text-[#0B1F3A] dark:text-neutral-300"}`}
                        >
                          {row.map((cell, cIdx) => (
                            <td
                              key={cIdx}
                              className={`py-1.5 px-3 tabular-nums ${cIdx === 0 ? "text-left font-medium" : "text-right"}`}
                            >
                              {cell != null ? String(cell) : "—"}
                            </td>
                          ))}
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>

              {"notes" in kf && Array.isArray(kf.notes) && kf.notes.length > 0 && (
                <div className="space-y-1 text-[11px] text-[#63748A] leading-relaxed">
                  {(kf.notes as string[]).map((nt: string, idx: number) => (
                    <p key={idx}>{nt}</p>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        ) : (
          <PendingCard label="Key Financials" />
        )}

        {/* 6-Year Financial Highlights Snapshot if present */}
        {highlights6y && highlights6y.years && highlights6y.rows && (
          <Card className="rounded-lg border border-[#D6E2EE] bg-white shadow-xs dark:border-[#262930] dark:bg-[#121418]">
            <CardHeader className="border-b border-[#D6E2EE] bg-[#F4F8FC] p-3.5 pb-2.5 dark:border-[#1f2228] dark:bg-[#181a1f]">
              <div className="flex items-center justify-between">
                <CardTitle className="font-mono text-xs font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-neutral-100">
                  Financial Highlights ({highlights6y.years.length} Tahun)
                </CardTitle>
                <span className="font-mono text-[10px] text-[#63748A]">
                  Source: {highlights6y.source || "Laporan Keuangan IDX"}
                </span>
              </div>
            </CardHeader>
            <CardContent className="p-4 space-y-2">
              <div className="overflow-x-auto rounded border border-[#D6E2EE] font-mono text-xs dark:border-[#262930]">
                <table className="w-full">
                  <thead>
                    <tr className="bg-[#0B1F3A] text-white text-right text-[11px]">
                      <th className="py-2 px-3 text-left">Pos Keuangan</th>
                      {highlights6y.years.map((y, i) => (
                        <th key={i} className="py-2 px-3 text-right">
                          {y}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {highlights6y.rows.map((r, rIdx) => (
                      <tr
                        key={rIdx}
                        className={`border-b border-[#D6E2EE]/60 last:border-0 ${
                          rIdx % 2 === 1 ? "bg-[#F4F8FC] dark:bg-[#181a1f]" : "bg-white dark:bg-[#121316]"
                        }`}
                      >
                        {r.map((c, cIdx) => (
                          <td
                            key={cIdx}
                            className={`py-1.5 px-3 tabular-nums ${cIdx === 0 ? "text-left font-medium text-[#0B1F3A]" : "text-right"}`}
                          >
                            {c != null ? String(c) : "—"}
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

        {/* Kondisi Industri, Katalis & Sentimen (PDF Page 2) */}
        {industryPage && industryPage.paragraphs && industryPage.paragraphs.length > 0 && (
          <Card className="rounded-lg border border-[#D6E2EE] bg-white shadow-xs dark:border-[#262930] dark:bg-[#121418]">
            <CardHeader className="border-b border-[#D6E2EE] bg-[#F4F8FC] p-4 pb-3 dark:border-[#1f2228] dark:bg-[#181a1f]">
              <div className="flex items-center justify-between">
                <CardTitle className="font-mono text-xs font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-neutral-100">
                  {industryPage.title || "Kondisi Industri, Katalis & Sentimen"}
                </CardTitle>
                {industryPage.sources && (
                  <span className="font-mono text-[10px] text-[#63748A]">
                    {industryPage.sources.join("; ")}
                  </span>
                )}
              </div>
            </CardHeader>
            <CardContent className="p-4 sm:p-5 space-y-3.5">
              {industryPage.paragraphs.map((p, idx) => (
                <div key={idx} className="space-y-1">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-neutral-100">
                    {p.heading}
                  </h4>
                  <p className="text-xs sm:text-[13px] leading-relaxed text-[#0B1F3A] text-justify dark:text-neutral-300">
                    {p.body}
                  </p>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Tesis Investasi (PDF Page 2 Rail) */}
        {thesis.length > 0 && (
          <Card className="rounded-lg border border-[#D6E2EE] bg-white shadow-xs dark:border-[#262930] dark:bg-[#121418]">
            <CardHeader className="border-b border-[#D6E2EE] bg-[#F4F8FC] p-4 pb-3 dark:border-[#1f2228] dark:bg-[#181a1f]">
              <CardTitle className="font-mono text-xs font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-neutral-100">
                Tesis Investasi — 4 Pilar Utama
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 sm:p-5">
              <div className="space-y-2.5">
                {thesis.map((t, idx) => (
                  <div
                    key={idx}
                    className="grid grid-cols-[32px_1fr_auto] gap-3 items-start border-t border-[#D6E2EE] pt-2.5 first:border-0 first:pt-0 dark:border-[#262930]"
                  >
                    <span className="font-mono text-sm font-black text-[#0B1F3A] dark:text-[#A9C9E8]">
                      {String(idx + 1).padStart(2, "0")}
                    </span>
                    <div className="space-y-0.5">
                      <h4 className="text-xs font-bold text-[#0B1F3A] dark:text-neutral-100">
                        {t.headline}
                      </h4>
                      <p className="text-xs text-[#63748A] leading-relaxed">
                        {t.detail}
                      </p>
                    </div>
                    {t.stat && (
                      <div className="text-right font-mono pl-3 shrink-0">
                        <div className="text-xs font-bold text-[#0B1F3A] tabular-nums dark:text-[#A9C9E8]">
                          {t.stat}
                        </div>
                        {t.stat_label && (
                          <div className="text-[9px] uppercase text-[#63748A]">
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
