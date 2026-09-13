// HistoryCharts component.
// Displays the 6-year performance history combo charts (Revenue & YoY growth, EBITDA & EBITDA margin,
// Net Profit & Net margin) over FY20A–FY25A.
//
// Primary data sources (in frozen priority order):
// 1. payload.revenue_combo / payload.ebitda_combo / payload.netprofit_combo (pre-computed combo charts)
// 2. payload.financial_highlights (authoritative 6-year summary table)
// 3. payload.financials (statement table shape)
// 4. payload.financial_statements.income.rows
//
// Disagreement policy (house rule):
// When payload.financial_highlights and payload.financial_statements.income disagree, we bind directly
// to the payload's primary 6-year history source (payload.revenue_combo / payload.financial_highlights)
// as populated by the backend without averaging or interpolating.

import React from "react"
import type { ReportPayload } from "@/lib/reportPayload"
import { TOKENS, PendingBlock, formatIdn, formatPct, parseIdnNumber } from "./tokens"

export interface HistoryPanelData {
  title: string
  window?: string
  labels: string[]
  bars: (number | null)[]
  line: (number | null)[]
  barUnit: string
  lineUnit: string
  barFmt?: string[]
  lineFmt?: string[]
  source?: string
  sourceOrigin: "revenue_combo" | "ebitda_combo" | "netprofit_combo" | "financial_highlights" | "financials" | "financial_statements.income"
}

/**
 * Inline SVG combo chart for 6-year history panels.
 * Renders bars in solid navy (#0B1F3A) and secondary line in buy green (#1E8F5F)
 * with independent scaling, zero baseline, and Indonesian number formatting (e.g. 14.093,6).
 */
function SvgHistoryComboChart({
  labels,
  bars,
  line,
  barUnit,
  lineUnit,
}: {
  labels: string[]
  bars: (number | null)[]
  line: (number | null)[]
  barUnit: string
  lineUnit: string
}) {
  const W = 360
  const H = 200
  const padL = 44
  const padR = 42
  const padT = 28
  const padB = 32
  const chartW = W - padL - padR
  const chartH = H - padT - padB

  const n = labels.length
  if (n === 0) return null

  // Bars scale (with 28% headroom to comfortably accommodate bar-top labels)
  const validBars = bars.filter((v): v is number => v !== null && Number.isFinite(v))
  const maxBarRaw = validBars.length > 0 ? Math.max(...validBars) : 1
  const bmax = maxBarRaw > 0 ? maxBarRaw * 1.28 : 1

  // Line scale (anchored to 0 or negative minimum)
  const validLine = line.filter((v): v is number => v !== null && Number.isFinite(v))
  const lminRaw = validLine.length > 0 ? Math.min(...validLine) : 0
  const lmaxRaw = validLine.length > 0 ? Math.max(...validLine) : 1

  const lLo = lminRaw < 0 ? lminRaw * 1.25 : 0
  const lHi = Math.max(lmaxRaw * 1.25, 10)
  const lSpan = lHi - lLo > 0 ? lHi - lLo : 1

  const step = chartW / n
  const bw = Math.min(step * 0.54, 28)

  // Calculate line points
  const linePoints: { x: number; y: number; val: number; text: string; barTop: number }[] = []
  labels.forEach((_, i) => {
    const lv = line[i]
    const bv = bars[i]
    const bh = bv !== null && bv !== undefined && bv > 0 ? (bv / bmax) * chartH : 0
    const barTop = padT + chartH - bh

    if (lv !== null && lv !== undefined && Number.isFinite(lv)) {
      const lx = padL + i * step + step / 2
      const ly = padT + chartH - ((lv - lLo) / lSpan) * chartH

      // Determine label text: growth uses signed %, margin uses unsigned %
      let text = ""
      const isGrowth = lineUnit.toLowerCase().includes("yoy") || lineUnit.toLowerCase().includes("growth")
      if (isGrowth) {
        if (i === 0 && lv === 0) {
          text = "" // Base period has no prior comparison
        } else {
          text = formatPct(lv, 1)
        }
      } else {
        text = `${formatIdn(lv, 1)}%`
      }

      linePoints.push({ x: lx, y: ly, val: lv, text, barTop })
    }
  })

  // Zero line for secondary axis
  const zeroY = lLo < 0 ? padT + chartH - ((0 - lLo) / lSpan) * chartH : null

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="w-full h-auto block select-none text-xs"
      role="img"
      aria-label={`Grafik historis ${labels.join(", ")}`}
    >
      <rect x="0" y="0" width={W} height={H} rx="4" fill="#ffffff" stroke={TOKENS.rule} strokeWidth="0.75" />

      {/* Gridlines & Left axis (Bars: Rp bn) */}
      {[0, 0.5, 1].map((frac, idx) => {
        const gy = padT + chartH - frac * chartH
        const val = bmax * frac
        return (
          <g key={`grid-${idx}`}>
            <line x1={padL} y1={gy} x2={W - padR} y2={gy} stroke={TOKENS.rule} strokeWidth="0.6" strokeDasharray="3 3" />
            <text
              x={padL - 4}
              y={gy + 3}
              fontSize="7"
              fill={TOKENS.muted}
              textAnchor="end"
              fontFamily="monospace"
              className="tabular-nums"
            >
              {formatIdn(val, val >= 100 ? 0 : 1)}
            </text>
          </g>
        )
      })}

      {/* Zero line for negative values */}
      {zeroY !== null && zeroY >= padT && zeroY <= padT + chartH && (
        <line
          x1={padL}
          y1={zeroY}
          x2={W - padR}
          y2={zeroY}
          stroke={TOKENS.muted}
          strokeWidth="0.8"
          strokeDasharray="2 2"
        />
      )}

      {/* Right axis ticks (Line %) */}
      {[0, 0.5, 1].map((frac, idx) => {
        const ly = padT + chartH - frac * chartH
        const val = lLo + frac * lSpan
        return (
          <text
            key={`rtick-${idx}`}
            x={W - padR + 4}
            y={ly + 3}
            fontSize="7"
            fill={TOKENS.muted}
            textAnchor="start"
            fontFamily="monospace"
            className="tabular-nums"
          >
            {formatIdn(val, 0)}%
          </text>
        )
      })}

      {/* Axis Unit Headers */}
      <text x={padL} y={padT - 10} fontSize="7" fontWeight="bold" fill={TOKENS.muted} textAnchor="start">
        {barUnit}
      </text>
      <text x={W - padR} y={padT - 10} fontSize="7" fontWeight="bold" fill={TOKENS.muted} textAnchor="end">
        {lineUnit}
      </text>

      {/* Bars (Histori Aktual) */}
      {labels.map((_, i) => {
        const v = bars[i]
        if (v === null || v === undefined) return null
        const isNeg = v < 0
        const bh = (Math.abs(v) / bmax) * chartH
        const bx = padL + i * step + (step - bw) / 2
        const by = isNeg ? padT + chartH : padT + chartH - bh

        return (
          <g key={`bar-${i}`}>
            <rect
              x={bx}
              y={by}
              width={bw}
              height={Math.max(bh, 0.5)}
              rx="1.5"
              fill={isNeg ? TOKENS.sell : TOKENS.navy}
            />
            {/* Bar top label with exact house format: 14.093,6 */}
            <text
              x={bx + bw / 2}
              y={isNeg ? by + bh + 8 : by - 4}
              fontSize="7"
              fontWeight="bold"
              fill={isNeg ? TOKENS.sell : TOKENS.navy}
              textAnchor="middle"
              fontFamily="monospace"
              className="tabular-nums"
            >
              {formatIdn(v, 1)}
            </text>
          </g>
        )
      })}

      {/* Secondary Line */}
      {linePoints.length > 1 && (
        <polyline
          fill="none"
          stroke={TOKENS.buy}
          strokeWidth="1.8"
          strokeLinejoin="round"
          strokeLinecap="round"
          points={linePoints.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ")}
        />
      )}

      {/* Line Points & Pill Labels */}
      {linePoints.map((p, idx) => {
        if (!p.text) return null
        const isAboveBar = p.y < p.barTop - 10
        const lblY = isAboveBar ? p.y - 5 : Math.min(p.y + 11, padT + chartH - 2)

        return (
          <g key={`pt-${idx}`}>
            <circle cx={p.x} cy={p.y} r="2.8" fill={TOKENS.buy} stroke="#ffffff" strokeWidth="1" />
            <g>
              <rect
                x={p.x - p.text.length * 2.3 - 2}
                y={lblY - 6.5}
                width={p.text.length * 4.6 + 4}
                height="8.5"
                rx="1.5"
                fill="#ffffff"
                fillOpacity="0.92"
                stroke={TOKENS.rule}
                strokeWidth="0.5"
              />
              <text
                x={p.x}
                y={lblY}
                fontSize="6.5"
                fontWeight="bold"
                fill={TOKENS.buy}
                textAnchor="middle"
                fontFamily="monospace"
                className="tabular-nums"
              >
                {p.text}
              </text>
            </g>
          </g>
        )
      })}

      {/* X Axis Period Labels */}
      {labels.map((lab, i) => {
        const lx = padL + i * step + step / 2
        return (
          <text
            key={`xlab-${i}`}
            x={lx}
            y={H - 12}
            fontSize="7.5"
            fill={TOKENS.navy}
            textAnchor="middle"
            fontFamily="monospace"
            fontWeight="bold"
          >
            {lab}
          </text>
        )
      })}

      {/* Footnote / Legend */}
      <text x={padL} y={H - 3} fontSize="6.5" fill={TOKENS.muted} fontFamily="monospace">
        Bar: Realisasi Historis · Garis: {lineUnit}
      </text>
    </svg>
  )
}

/**
 * Extracts 6-year history rows from financial_highlights.
 */
function extractHighlightsRows(fh: any) {
  if (!fh || !Array.isArray(fh.rows)) return null
  const rawYears = Array.isArray(fh.years) ? fh.years : (Array.isArray(fh.headers) ? fh.headers.slice(1) : [])
  const years = rawYears.map(String)
  if (years.length === 0) return null

  const rows: (string | number)[][] = fh.rows
  const findRow = (...needles: string[]) => {
    return rows.find((r) => {
      const label = String(r[0] ?? "").toLowerCase()
      return needles.every((n) => label.includes(n.toLowerCase()))
    })
  }

  const cleanRow = (row?: (string | number)[]) => {
    if (!row) return []
    return row.slice(1).map(parseIdnNumber)
  }

  return { years, rows, findRow, cleanRow, source: fh.source || "Sectors — laporan keuangan tahunan (IDR bn)" }
}

/**
 * Extracts Revenue & Revenue Growth history panel.
 */
function getRevenuePanel(payload: Record<string, any>): HistoryPanelData | null {
  // 1. Primary: payload.revenue_combo
  const rc = payload.revenue_combo
  if (rc && Array.isArray(rc.bars) && rc.bars.length > 0) {
    const rawLabels = rc.years ?? []
    const labels = Array.isArray(rawLabels) ? rawLabels.map(String) : []
    const bars = rc.bars.map(parseIdnNumber)
    const line = Array.isArray(rc.line) ? rc.line.map(parseIdnNumber) : []
    const title = rc.title || "Revenue & Revenue Growth"
    const window = labels.length > 0 ? `${labels[0]}–${labels[labels.length - 1]}` : undefined
    return {
      title,
      window,
      labels,
      bars,
      line,
      barUnit: "Rp bn",
      lineUnit: "% yoy",
      source: rc.source || "Sectors — laporan keuangan tahunan (IDR bn)",
      sourceOrigin: "revenue_combo",
    }
  }

  // 2. Fallback: payload.financial_highlights
  const fhData = extractHighlightsRows(payload.financial_highlights)
  if (fhData) {
    const revRow = fhData.findRow("pendapatan") || fhData.findRow("revenue")
    if (revRow) {
      const bars = fhData.cleanRow(revRow)
      const line = bars.map((cur, i) => {
        if (i === 0 || cur === null) return null
        const prev = bars[i - 1]
        if (prev === null || prev === 0) return null
        return (cur / prev - 1) * 100
      })
      const labels = fhData.years
      const window = labels.length > 0 ? `${labels[0]}–${labels[labels.length - 1]}` : undefined
      return {
        title: "Revenue & Revenue Growth",
        window,
        labels,
        bars,
        line,
        barUnit: "Rp bn",
        lineUnit: "% yoy",
        source: fhData.source,
        sourceOrigin: "financial_highlights",
      }
    }
  }

  // 3. Fallback: payload.financial_statements.income or payload.financials
  const incomeRows = payload.financial_statements?.income?.rows || payload.financials?.[0]?.rows
  const incomeHeaders = payload.financial_statements?.income?.headers || payload.financials?.[0]?.headers
  if (Array.isArray(incomeRows) && Array.isArray(incomeHeaders)) {
    const labels = incomeHeaders.slice(1).map(String)
    const revRow = incomeRows.find((r: any) => {
      const label = String(r[0] ?? "").toLowerCase()
      return label.includes("revenue") || label.includes("pendapatan")
    })
    if (revRow) {
      const bars = revRow.slice(1).map(parseIdnNumber)
      const line = bars.map((cur: number | null, i: number) => {
        if (i === 0 || cur === null) return null
        const prev = bars[i - 1]
        if (prev === null || prev === 0) return null
        return (cur / prev - 1) * 100
      })
      return {
        title: "Revenue & Revenue Growth",
        window: labels.length > 0 ? `${labels[0]}–${labels[labels.length - 1]}` : undefined,
        labels,
        bars,
        line,
        barUnit: "Rp bn",
        lineUnit: "% yoy",
        source: payload.financial_statements?.income?.source || "Sectors financial_statements.income",
        sourceOrigin: "financial_statements.income",
      }
    }
  }

  return null
}

/**
 * Extracts EBITDA & EBITDA Margin history panel.
 */
function getEbitdaPanel(payload: Record<string, any>): HistoryPanelData | null {
  // 1. Primary: payload.ebitda_combo
  const ec = payload.ebitda_combo
  if (ec && Array.isArray(ec.bars) && ec.bars.length > 0) {
    const rawLabels = ec.years ?? []
    const labels = Array.isArray(rawLabels) ? rawLabels.map(String) : []
    const bars = ec.bars.map(parseIdnNumber)
    const line = Array.isArray(ec.line) ? ec.line.map(parseIdnNumber) : []
    const title = ec.title || "EBITDA & EBITDA Margin"
    const window = labels.length > 0 ? `${labels[0]}–${labels[labels.length - 1]}` : undefined
    return {
      title,
      window,
      labels,
      bars,
      line,
      barUnit: "Rp bn",
      lineUnit: "% margin",
      source: ec.source || "Sectors — laporan keuangan tahunan (IDR bn)",
      sourceOrigin: "ebitda_combo",
    }
  }

  // 2. Fallback: payload.financial_highlights
  const fhData = extractHighlightsRows(payload.financial_highlights)
  if (fhData) {
    const ebitdaRow = fhData.rows.find((r) => {
      const l = String(r[0] ?? "").toLowerCase()
      return l.includes("ebitda") && !l.includes("marjin") && !l.includes("margin")
    })
    const marginRow = fhData.findRow("marjin ebitda") || fhData.findRow("ebitda margin")
    const revRow = fhData.findRow("pendapatan") || fhData.findRow("revenue")

    if (ebitdaRow) {
      const bars = fhData.cleanRow(ebitdaRow)
      let line: (number | null)[] = []
      if (marginRow) {
        line = fhData.cleanRow(marginRow)
      } else if (revRow) {
        const rev = fhData.cleanRow(revRow)
        line = bars.map((eb, i) => {
          const r = rev[i]
          if (eb === null || r === null || r === 0) return null
          return (eb / r) * 100
        })
      }
      const labels = fhData.years
      const window = labels.length > 0 ? `${labels[0]}–${labels[labels.length - 1]}` : undefined
      return {
        title: "EBITDA & EBITDA Margin",
        window,
        labels,
        bars,
        line,
        barUnit: "Rp bn",
        lineUnit: "% margin",
        source: fhData.source,
        sourceOrigin: "financial_highlights",
      }
    }
  }

  return null
}

/**
 * Extracts Net Profit & Net Margin history panel.
 */
function getNetProfitPanel(payload: Record<string, any>): HistoryPanelData | null {
  // 1. Primary: payload.netprofit_combo
  const npc = payload.netprofit_combo
  if (npc && Array.isArray(npc.bars) && npc.bars.length > 0) {
    const rawLabels = npc.years ?? []
    const labels = Array.isArray(rawLabels) ? rawLabels.map(String) : []
    const bars = npc.bars.map(parseIdnNumber)
    const line = Array.isArray(npc.line) ? npc.line.map(parseIdnNumber) : []
    const title = npc.title || "Net Profit & Net Margin"
    const window = labels.length > 0 ? `${labels[0]}–${labels[labels.length - 1]}` : undefined
    return {
      title,
      window,
      labels,
      bars,
      line,
      barUnit: "Rp bn",
      lineUnit: "% margin",
      source: npc.source || "Sectors — laporan keuangan tahunan (IDR bn)",
      sourceOrigin: "netprofit_combo",
    }
  }

  // 2. Fallback: payload.financial_highlights
  const fhData = extractHighlightsRows(payload.financial_highlights)
  if (fhData) {
    const netRow = fhData.findRow("laba bersih") || fhData.findRow("net profit") || fhData.findRow("net income")
    const marginRow = fhData.findRow("marjin bersih") || fhData.findRow("npm") || fhData.findRow("net margin")
    const revRow = fhData.findRow("pendapatan") || fhData.findRow("revenue")

    if (netRow) {
      const bars = fhData.cleanRow(netRow)
      let line: (number | null)[] = []
      if (marginRow) {
        line = fhData.cleanRow(marginRow)
      } else if (revRow) {
        const rev = fhData.cleanRow(revRow)
        line = bars.map((n, i) => {
          const r = rev[i]
          if (n === null || r === null || r === 0) return null
          return (n / r) * 100
        })
      }
      const labels = fhData.years
      const window = labels.length > 0 ? `${labels[0]}–${labels[labels.length - 1]}` : undefined
      return {
        title: "Net Profit & Net Margin",
        window,
        labels,
        bars,
        line,
        barUnit: "Rp bn",
        lineUnit: "% margin",
        source: fhData.source,
        sourceOrigin: "financial_highlights",
      }
    }
  }

  return null
}

export function HistoryCharts({ payload }: { payload?: ReportPayload | null }) {
  if (!payload) {
    return <PendingBlock label="Historis Kinerja Keuangan" message="data historis keuangan belum tersedia di payload." />
  }

  const p = payload as Record<string, any>
  const revPanel = getRevenuePanel(p)
  const ebitdaPanel = getEbitdaPanel(p)
  const netProfitPanel = getNetProfitPanel(p)

  const panels = [revPanel, ebitdaPanel, netProfitPanel].filter((p): p is HistoryPanelData => p !== null)

  if (panels.length === 0) {
    return <PendingBlock label="Historis Kinerja Keuangan" message="data historis keuangan belum tersedia di payload." />
  }

  const sourceFootnote = panels[0]?.source || "Sectors — laporan keuangan tahunan (IDR bn)"

  return (
    <div className="space-y-3 font-sans">
      <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#D6E2EE] pb-2 dark:border-[#262930]">
        <div>
          <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-neutral-100">
            Historis Kinerja Keuangan (6 Tahun Aktual)
          </h3>
          <p className="text-[11px] text-[#63748A]">
            Tren realisasi pendapatan, EBITDA, dan laba bersih per tahun (FY20A–FY25A)
          </p>
        </div>
        <span className="font-mono text-[10px] text-[#63748A]">
          Source: {sourceFootnote}
        </span>
      </div>

      <div className={`grid grid-cols-1 gap-4 ${panels.length === 3 ? "lg:grid-cols-3" : "lg:grid-cols-2"}`}>
        {panels.map((panel, idx) => (
          <div
            key={idx}
            className="flex flex-col rounded-lg border border-[#D6E2EE] bg-white p-3.5 shadow-xs dark:border-[#262930] dark:bg-[#121418]"
          >
            <div className="mb-2 flex items-center justify-between border-b border-[#D6E2EE]/60 pb-2 dark:border-[#1f2228]">
              <span className="text-xs font-bold text-[#0B1F3A] dark:text-neutral-100">{panel.title}</span>
              {panel.window && <span className="font-mono text-[10px] text-[#63748A]">{panel.window}</span>}
            </div>

            <div className="my-auto">
              <SvgHistoryComboChart
                labels={panel.labels}
                bars={panel.bars}
                line={panel.line}
                barUnit={panel.barUnit}
                lineUnit={panel.lineUnit}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
