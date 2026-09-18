import React from "react"
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  LabelList,
} from "recharts"
import type { ReportPayload } from "@/lib/reportPayload"
import { PendingBlock, formatIdn, formatPct, parseIdnNumber } from "./tokens"
import {
  seriesColor,
  SECTORAL_GRID,
  SECTORAL_ZERO_BASELINE,
  SECTORAL_TICK,
  SECTORAL_TOOLTIP_STYLE,
  SECTORAL_LEGEND_STYLE,
} from "./sectoralSeries"

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
 * Sectoral recharts combo chart for 6-year history panels.
 * Bar series uses SECTORAL_SERIES[0]; line series uses SECTORAL_SERIES[1].
 * Data/logic unchanged from the previous SVG implementation.
 */
function HistoryComboChart({
  labels,
  bars,
  line,
  barUnit,
  lineUnit,
  title,
}: {
  labels: string[]
  bars: (number | null)[]
  line: (number | null)[]
  barUnit: string
  lineUnit: string
  title: string
}) {
  const n = labels.length
  if (n === 0) return null

  const isGrowth = lineUnit.toLowerCase().includes("yoy") || lineUnit.toLowerCase().includes("growth")

  const lineLabel = (lv: number | null, i: number): string => {
    if (lv === null || lv === undefined || !Number.isFinite(lv)) return ""
    if (isGrowth) {
      if (i === 0 && lv === 0) return ""
      return formatPct(lv, 1)
    }
    return `${formatIdn(lv, 1)}%`
  }

  const data = labels.map((label, i) => ({
    name: label,
    bar: bars[i] ?? null,
    barLabel: bars[i] !== null && bars[i] !== undefined ? formatIdn(bars[i], 1) : "",
    line: line[i] ?? null,
    lineLabel: lineLabel(line[i] ?? null, i),
  }))

  const hasNegativeLine = line.some((v) => v !== null && v !== undefined && v < 0)

  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-[11px] text-[#6B6659] dark:text-[#A8A296]">
        <span className="font-semibold">{barUnit}</span>
        <span className="font-semibold">{lineUnit}</span>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <ComposedChart data={data} margin={{ top: 20, right: 8, left: 0, bottom: 0 }} aria-label={`Grafik historis ${labels.join(", ")}`}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={SECTORAL_GRID} />
          <XAxis dataKey="name" tick={SECTORAL_TICK} axisLine={false} tickLine={false} />
          <YAxis yAxisId="bar" tick={SECTORAL_TICK} axisLine={false} tickLine={false} tickFormatter={(v: number) => formatIdn(v, Math.abs(v) >= 100 ? 0 : 1)} width={44} />
          <YAxis yAxisId="line" orientation="right" tick={SECTORAL_TICK} axisLine={false} tickLine={false} tickFormatter={(v: number) => formatIdn(v, 0)} width={40} />
          <Tooltip
            contentStyle={SECTORAL_TOOLTIP_STYLE}
            formatter={(value: unknown, name: unknown) => {
              const label = String(name)
              if (label === "line") {
                return [typeof value === "number" ? formatPct(value, 1) : "-", lineUnit]
              }
              return [typeof value === "number" ? formatIdn(value, 1) : "-", barUnit]
            }}
            labelFormatter={(label: unknown) => String(label)}
          />
          <Legend iconType="square" wrapperStyle={SECTORAL_LEGEND_STYLE} />
          <ReferenceLine yAxisId="bar" y={0} stroke={SECTORAL_ZERO_BASELINE} />
          {hasNegativeLine && <ReferenceLine yAxisId="line" y={0} stroke={SECTORAL_ZERO_BASELINE} />}
          <Bar yAxisId="bar" dataKey="bar" name={`${title} (${barUnit})`} fill={seriesColor(0)} maxBarSize={28} radius={[2, 2, 0, 0]}>
            {data.map((entry, i) => (
              <Cell key={`cell-${i}`} fill={entry.bar !== null && entry.bar < 0 ? seriesColor(4) : seriesColor(0)} />
            ))}
            <LabelList dataKey="barLabel" position="top" fill={seriesColor(0)} fontSize={11} />
          </Bar>
          <Line yAxisId="line" type="monotone" dataKey="line" name={lineUnit} stroke={seriesColor(1)} strokeWidth={2} dot={{ r: 4, fill: seriesColor(1) }} activeDot={{ r: 6 }} connectNulls>
            <LabelList dataKey="lineLabel" position="top" fill={seriesColor(1)} fontSize={11} />
          </Line>
        </ComposedChart>
      </ResponsiveContainer>
      <p className="mt-1 text-[11px] text-[#6B6659] dark:text-[#A8A296]">
        Batang: Realisasi historis · Garis: {lineUnit}
      </p>
    </div>
  )
}

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

  return { years, rows, findRow, cleanRow, source: fh.source || "Sectors - laporan keuangan tahunan (IDR bn)" }
}

function getRevenuePanel(payload: Record<string, any>): HistoryPanelData | null {
  const rc = payload.revenue_combo
  if (rc && Array.isArray(rc.bars) && rc.bars.length > 0) {
    const rawLabels = rc.years ?? []
    const labels = Array.isArray(rawLabels) ? rawLabels.map(String) : []
    const bars = rc.bars.map(parseIdnNumber)
    const line = Array.isArray(rc.line) ? rc.line.map(parseIdnNumber) : []
    const title = rc.title || "Pendapatan dan pertumbuhan pendapatan"
    const window = labels.length > 0 ? `${labels[0]}–${labels[labels.length - 1]}` : undefined
    return {
      title,
      window,
      labels,
      bars,
      line,
      barUnit: "Rp bn",
      lineUnit: "% yoy",
      source: rc.source || "Sectors - laporan keuangan tahunan (IDR bn)",
      sourceOrigin: "revenue_combo",
    }
  }

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
        title: "Pendapatan dan pertumbuhan pendapatan",
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
        title: "Pendapatan dan pertumbuhan pendapatan",
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

function getEbitdaPanel(payload: Record<string, any>): HistoryPanelData | null {
  const ec = payload.ebitda_combo
  if (ec && Array.isArray(ec.bars) && ec.bars.length > 0) {
    const rawLabels = ec.years ?? []
    const labels = Array.isArray(rawLabels) ? rawLabels.map(String) : []
    const bars = ec.bars.map(parseIdnNumber)
    const line = Array.isArray(ec.line) ? ec.line.map(parseIdnNumber) : []
    const title = ec.title || "EBITDA dan marjin EBITDA"
    const window = labels.length > 0 ? `${labels[0]}–${labels[labels.length - 1]}` : undefined
    return {
      title,
      window,
      labels,
      bars,
      line,
      barUnit: "Rp bn",
      lineUnit: "% marjin",
      source: ec.source || "Sectors - laporan keuangan tahunan (IDR bn)",
      sourceOrigin: "ebitda_combo",
    }
  }

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
        title: "EBITDA dan marjin EBITDA",
        window,
        labels,
        bars,
        line,
        barUnit: "Rp bn",
        lineUnit: "% marjin",
        source: fhData.source,
        sourceOrigin: "financial_highlights",
      }
    }
  }

  return null
}

function getNetProfitPanel(payload: Record<string, any>): HistoryPanelData | null {
  const npc = payload.netprofit_combo
  if (npc && Array.isArray(npc.bars) && npc.bars.length > 0) {
    const rawLabels = npc.years ?? []
    const labels = Array.isArray(rawLabels) ? rawLabels.map(String) : []
    const bars = npc.bars.map(parseIdnNumber)
    const line = Array.isArray(npc.line) ? npc.line.map(parseIdnNumber) : []
    const title = npc.title || "Laba bersih dan marjin bersih"
    const window = labels.length > 0 ? `${labels[0]}–${labels[labels.length - 1]}` : undefined
    return {
      title,
      window,
      labels,
      bars,
      line,
      barUnit: "Rp bn",
      lineUnit: "% marjin",
      source: npc.source || "Sectors - laporan keuangan tahunan (IDR bn)",
      sourceOrigin: "netprofit_combo",
    }
  }

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
        title: "Laba bersih dan marjin bersih",
        window,
        labels,
        bars,
        line,
        barUnit: "Rp bn",
        lineUnit: "% marjin",
        source: fhData.source,
        sourceOrigin: "financial_highlights",
      }
    }
  }

  return null
}

export function HistoryCharts({ payload }: { payload?: ReportPayload | null }) {
  if (!payload) {
    return <PendingBlock label="Historis kinerja keuangan" message="data historis keuangan belum tersedia di payload." />
  }

  const p = payload as Record<string, any>
  const revPanel = getRevenuePanel(p)
  const ebitdaPanel = getEbitdaPanel(p)
  const netProfitPanel = getNetProfitPanel(p)

  const panels = [revPanel, ebitdaPanel, netProfitPanel].filter((p): p is HistoryPanelData => p !== null)

  if (panels.length === 0) {
    return <PendingBlock label="Historis kinerja keuangan" message="data historis keuangan belum tersedia di payload." />
  }

  const sourceFootnote = panels[0]?.source || "Sectors - laporan keuangan tahunan (IDR bn)"

  return (
    <div className="space-y-4 font-sans">
      <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#E7E3DA] pb-2 dark:border-[#2A2822]">
        <div>
          <h3 className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
            Historis kinerja keuangan (6 tahun aktual)
          </h3>
          <p className="text-xs text-[#6B6659] dark:text-[#A8A296]">
            Tren realisasi pendapatan, EBITDA, dan laba bersih per tahun (FY20A–FY25A)
          </p>
        </div>
        <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
          Sumber: {sourceFootnote}
        </span>
      </div>

      <div className={`grid grid-cols-1 gap-4 ${panels.length === 3 ? "lg:grid-cols-3" : "lg:grid-cols-2"}`}>
        {panels.map((panel, idx) => (
          <div
            key={idx}
            className="flex flex-col rounded-xl border border-[#E7E3DA] bg-white p-4 dark:border-[#2A2822] dark:bg-[#1B1A16]"
          >
            <div className="mb-3 flex items-center justify-between border-b border-[#E7E3DA]/60 pb-2 dark:border-[#2A2822]">
              <span className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">{panel.title}</span>
              {panel.window && <span className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">{panel.window}</span>}
            </div>

            <div className="my-auto">
              <HistoryComboChart
                labels={panel.labels}
                bars={panel.bars}
                line={panel.line}
                barUnit={panel.barUnit}
                lineUnit={panel.lineUnit}
                title={panel.title}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
