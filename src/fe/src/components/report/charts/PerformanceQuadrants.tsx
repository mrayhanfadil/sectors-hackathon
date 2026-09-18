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

interface QuadrantData {
  title: string
  window?: string
  labels: string[]
  bars: (number | null)[]
  line: (number | null)[]
  barUnit: string
  lineUnit: string
  barFmt?: string[]
  lineFmt?: string[]
  actualN: number
  narrative?: string
  tieOut?: string
}

/**
 * Sectoral recharts combo chart rendering bars and a line on a secondary axis.
 * Actual periods render solid series color; projection periods render faded.
 * Data/logic unchanged from the previous SVG implementation.
 */
function QuadrantComboChart({
  labels,
  bars,
  line,
  actualN,
  barFmt,
  lineFmt,
  barUnit,
  lineUnit,
  title,
}: {
  labels: string[]
  bars: (number | null)[]
  line: (number | null)[]
  actualN: number
  barFmt?: string[]
  lineFmt?: string[]
  barUnit: string
  lineUnit: string
  title: string
}) {
  const n = labels.length
  if (n === 0) return null

  const pointLabel = (i: number, lv: number | null): string => {
    const fmt = lineFmt?.[i]
    if (fmt && fmt.trim() !== "" && fmt.trim() !== "-") return fmt
    if (lv === null || lv === undefined || !Number.isFinite(lv)) return ""
    return formatPct(lv, 1)
  }

  const data = labels.map((label, i) => {
    const bv = bars[i] ?? null
    return {
      name: label,
      bar: bv,
      barOpacity: i < actualN ? 1 : 0.4,
      barLabel: bv !== null && bv !== undefined ? (barFmt?.[i] ?? formatIdn(bv, Math.abs(bv) >= 100 ? 0 : 1)) : "",
      line: line[i] ?? null,
      lineLabel: pointLabel(i, line[i] ?? null),
    }
  })

  const hasNegativeLine = line.some((v) => v !== null && v !== undefined && v < 0)

  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-[11px] text-[#6B6659] dark:text-[#A8A296]">
        <span className="font-semibold">{barUnit}</span>
        <span className="font-semibold">{lineUnit}</span>
      </div>
      <ResponsiveContainer width="100%" height={190}>
        <ComposedChart data={data} margin={{ top: 20, right: 8, left: 0, bottom: 0 }} aria-label={`Grafik kinerja ${labels.join(", ")}`}>
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
          <Bar yAxisId="bar" dataKey="bar" name={`${title} (${barUnit})`} fill={seriesColor(0)} maxBarSize={32} radius={[2, 2, 0, 0]}>
            {data.map((entry, i) => (
              <Cell key={`cell-${i}`} fill={seriesColor(0)} fillOpacity={entry.barOpacity} />
            ))}
            <LabelList dataKey="barLabel" position="top" fill={seriesColor(0)} fontSize={11} />
          </Bar>
          <Line yAxisId="line" type="monotone" dataKey="line" name={lineUnit} stroke={seriesColor(1)} strokeWidth={2} dot={{ r: 4, fill: seriesColor(1) }} activeDot={{ r: 6 }} connectNulls>
            <LabelList dataKey="lineLabel" position="top" fill={seriesColor(1)} fontSize={11} />
          </Line>
        </ComposedChart>
      </ResponsiveContainer>
      <p className="mt-1 text-[11px] text-[#6B6659] dark:text-[#A8A296]">
        Solid = Aktual · Transparan = Proyeksi
      </p>
    </div>
  )
}

function extractQuadrants(payload: ReportPayload): QuadrantData[] | null {
  const p = payload as Record<string, any>

  const perfQuadrants = p.performance_page?.quadrants
  if (Array.isArray(perfQuadrants) && perfQuadrants.length > 0) {
    return perfQuadrants.map((q: any) => ({
      title: q.title ?? "Kuadran kinerja",
      window: q.window,
      labels: Array.isArray(q.labels) ? q.labels.map(String) : [],
      bars: Array.isArray(q.bars) ? q.bars.map((v: unknown) => parseIdnNumber(v)) : [],
      line: Array.isArray(q.line) ? q.line.map((v: unknown) => parseIdnNumber(v)) : [],
      barUnit: q.bar_unit ?? "Rp bn",
      lineUnit: q.line_unit ?? "% yoy",
      barFmt: Array.isArray(q.bar_fmt) ? q.bar_fmt.map(String) : undefined,
      lineFmt: Array.isArray(q.line_fmt) ? q.line_fmt.map(String) : undefined,
      actualN: typeof q.actual_n === "number" ? q.actual_n : 2,
      narrative: q.narrative,
      tieOut: q.tie_out?.block,
    }))
  }

  const kf = p.cover?.slide2?.key_financials ?? p.key_financials
  if (!kf || !Array.isArray(kf.headers) || !Array.isArray(kf.rows)) {
    return null
  }

  const rawHeaders: string[] = kf.headers.map(String)
  const headers = rawHeaders.length > 1 ? rawHeaders.slice(1) : rawHeaders
  const rows: (string | number)[][] = kf.rows

  const findRow = (...needles: string[]) => {
    return rows.find((r) => {
      const label = String(r[0] ?? "").toLowerCase()
      return needles.every((n) => label.includes(n.toLowerCase()))
    })
  }

  const cleanRow = (row?: (string | number)[]) => {
    if (!row) return []
    const cells = row.slice(1)
    return cells.map(parseIdnNumber)
  }

  const revRow = findRow("revenue")
  const ebitdaRow = findRow("ebitda")
  const netRow = findRow("net profit")
  const epsRow = findRow("eps")

  const rev = cleanRow(revRow)
  const ebitda = cleanRow(ebitdaRow)
  const net = cleanRow(netRow)
  const eps = cleanRow(epsRow)

  if (rev.length === 0 && ebitda.length === 0) {
    return null
  }

  const calcGrowth = (series: (number | null)[]) => {
    return series.map((cur, i) => {
      if (i === 0 || cur === null) return null
      const prev = series[i - 1]
      if (prev === null || prev === 0) return null
      return (cur / prev - 1) * 100
    })
  }

  const revGrowth = calcGrowth(rev)
  const ebitdaMargins = ebitda.map((eb, i) => {
    const r = rev[i]
    if (eb === null || r === null || r === 0) return null
    return (eb / r) * 100
  })
  const epsGrowth = calcGrowth(eps)

  let actualN = 0
  for (const h of headers) {
    if (h.trim().toUpperCase().endsWith("A")) {
      actualN += 1
    } else {
      break
    }
  }
  if (actualN === 0) actualN = 2

  const quadrants: QuadrantData[] = [
    {
      title: "Pendapatan dan pertumbuhan pendapatan",
      window: headers.length > 0 ? `${headers[0]}–${headers[headers.length - 1]}` : undefined,
      labels: headers,
      bars: rev,
      line: revGrowth,
      barUnit: "Rp bn",
      lineUnit: "% yoy",
      actualN,
      tieOut: "cover.slide2.key_financials (Revenue)",
    },
    {
      title: "EBITDA dan marjin EBITDA",
      window: headers.length > 0 ? `${headers[0]}–${headers[headers.length - 1]}` : undefined,
      labels: headers,
      bars: ebitda,
      line: ebitdaMargins,
      barUnit: "Rp bn",
      lineUnit: "% marjin",
      actualN,
      tieOut: "cover.slide2.key_financials (EBITDA)",
    },
  ]

  if (net.length > 0) {
    quadrants.push({
      title: "Laba bersih dan pertumbuhan EPS",
      window: headers.length > 0 ? `${headers[0]}–${headers[headers.length - 1]}` : undefined,
      labels: headers,
      bars: net,
      line: epsGrowth,
      barUnit: "Rp bn",
      lineUnit: "% EPS growth",
      actualN,
      tieOut: "cover.slide2.key_financials (Net Profit)",
    })
  }

  return quadrants
}

export function PerformanceQuadrants({ payload }: { payload: ReportPayload }) {
  const quadrants = extractQuadrants(payload)

  if (!quadrants || quadrants.length === 0) {
    return <PendingBlock label="Kuadran kinerja" message="data kinerja keuangan belum tersedia di payload." />
  }

  return (
    <div className="space-y-4 font-sans">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {quadrants.map((q, idx) => (
          <div
            key={idx}
            className="flex flex-col rounded-xl border border-[#E7E3DA] bg-white p-4 shadow-none dark:border-[#2A2822] dark:bg-[#1B1A16]"
          >
            <div className="mb-3 flex items-center justify-between border-b border-[#E7E3DA]/60 pb-2 dark:border-[#2A2822]">
              <span className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">{q.title}</span>
              {q.window && <span className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">{q.window}</span>}
            </div>

            <div className="my-auto">
              <QuadrantComboChart
                labels={q.labels}
                bars={q.bars}
                line={q.line}
                actualN={q.actualN}
                barFmt={q.barFmt}
                lineFmt={q.lineFmt}
                barUnit={q.barUnit}
                lineUnit={q.lineUnit}
                title={q.title}
              />
            </div>

            {q.narrative && (
              <p className="mt-3 rounded-lg border border-[#E7E3DA] bg-[#FBFAF7] p-2.5 text-xs leading-relaxed text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
                {q.narrative}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
