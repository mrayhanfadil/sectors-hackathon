import React from "react"
import type { ReportPayload } from "@/lib/reportPayload"
import { TOKENS, PendingBlock, formatIdn, formatPct, parseIdnNumber } from "./tokens"

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
 * Inline SVG combo chart rendering bars and a line on a secondary axis.
 */
function SvgComboChart({
  labels,
  bars,
  line,
  actualN,
  barFmt,
  lineFmt,
  barUnit,
  lineUnit,
}: {
  labels: string[]
  bars: (number | null)[]
  line: (number | null)[]
  actualN: number
  barFmt?: string[]
  lineFmt?: string[]
  barUnit: string
  lineUnit: string
}) {
  const W = 360
  const H = 190
  const padL = 44
  const padR = 44
  const padT = 24
  const padB = 30
  const chartW = W - padL - padR
  const chartH = H - padT - padB

  const n = labels.length
  if (n === 0) return null

  // Bars scale
  const validBars = bars.filter((v): v is number => v !== null && Number.isFinite(v))
  const bmax = validBars.length > 0 ? Math.max(...validBars) : 1

  // Line scale
  const validLine = line.filter((v): v is number => v !== null && Number.isFinite(v))
  const lmin = validLine.length > 0 ? Math.min(...validLine) : 0
  const lmax = validLine.length > 0 ? Math.max(...validLine) : 1
  const lLo = Math.min(lmin, 0)
  const lHi = Math.max(lmax, 0)
  const lSpan = lHi - lLo > 0 ? lHi - lLo : 1

  const step = chartW / n
  const bw = step * 0.52

  // Line points
  const linePoints: { x: number; y: number; val: number; fmt?: string; barTop: number }[] = []
  labels.forEach((_, i) => {
    const lv = line[i]
    const bv = bars[i]
    const bh = bv !== null && bv !== undefined ? (bv / bmax) * chartH : 0
    const barTop = padT + chartH - bh
    if (lv !== null && lv !== undefined && Number.isFinite(lv)) {
      const lx = padL + i * step + step / 2
      const ly = padT + chartH - ((lv - lLo) / lSpan) * chartH
      linePoints.push({ x: lx, y: ly, val: lv, fmt: lineFmt?.[i], barTop })
    }
  })

  // Zero line for secondary axis
  const zeroY = lLo < 0 ? padT + chartH - ((0 - lLo) / lSpan) * chartH : null

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="w-full h-auto block select-none"
      role="img"
      aria-label={`Grafik kinerja ${labels.join(", ")}`}
    >
      <rect x="0" y="0" width={W} height={H} rx="6" fill="#ffffff" stroke={TOKENS.rule} strokeWidth="0.75" />

      {/* Gridlines & Left axis */}
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

      {/* Zero line */}
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

      {/* Right axis ticks */}
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

      {/* Units */}
      <text x={padL} y={padT - 8} fontSize="7" fontWeight="bold" fill={TOKENS.muted} textAnchor="start">
        {barUnit}
      </text>
      <text x={W - padR} y={padT - 8} fontSize="7" fontWeight="bold" fill={TOKENS.muted} textAnchor="end">
        {lineUnit}
      </text>

      {/* Bars */}
      {labels.map((_, i) => {
        const v = bars[i]
        if (v === null || v === undefined) return null
        const bh = (v / bmax) * chartH
        const bx = padL + i * step + (step - bw) / 2
        const by = padT + chartH - bh
        const isActual = i < actualN

        return (
          <g key={`bar-${i}`}>
            <rect
              x={bx}
              y={by}
              width={bw}
              height={Math.max(bh, 0.5)}
              rx="2"
              fill={TOKENS.teal}
              opacity={isActual ? 1 : 0.4}
            />
            {/* Bar top label */}
            <text
              x={bx + bw / 2}
              y={by - 3}
              fontSize="7"
              fontWeight="bold"
              fill={TOKENS.teal}
              textAnchor="middle"
              fontFamily="monospace"
              className="tabular-nums"
            >
              {barFmt?.[i] ?? formatIdn(v, v >= 100 ? 0 : 1)}
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

      {/* Line Points & Labels */}
      {linePoints.map((p, idx) => {
        const text = p.fmt && p.fmt.trim() !== "" ? p.fmt : formatPct(p.val, 1)
        const isAboveBar = p.y < p.barTop - 10
        const lblY = isAboveBar ? p.y - 5 : Math.min(p.y + 11, padT + chartH - 2)

        return (
          <g key={`pt-${idx}`}>
            <circle cx={p.x} cy={p.y} r="2.8" fill={TOKENS.buy} stroke="#ffffff" strokeWidth="1" />
            {text && text !== "-" && (
              <g>
                <rect
                  x={p.x - text.length * 2.2 - 2}
                  y={lblY - 6.5}
                  width={text.length * 4.4 + 4}
                  height="8"
                  rx="2"
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
                  {text}
                </text>
              </g>
            )}
          </g>
        )
      })}

      {/* X Axis Labels */}
      {labels.map((lab, i) => {
        const lx = padL + i * step + step / 2
        return (
          <text
            key={`xlab-${i}`}
            x={lx}
            y={H - 12}
            fontSize="7.5"
            fill={TOKENS.muted}
            textAnchor="middle"
            fontFamily="monospace"
            fontWeight="bold"
          >
            {lab}
          </text>
        )
      })}

      {/* Legend */}
      <text x={padL} y={H - 3} fontSize="6.5" fill={TOKENS.muted}>
        Solid = Aktual · Transparan = Proyeksi
      </text>
    </svg>
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
              <SvgComboChart
                labels={q.labels}
                bars={q.bars}
                line={q.line}
                actualN={q.actualN}
                barFmt={q.barFmt}
                lineFmt={q.lineFmt}
                barUnit={q.barUnit}
                lineUnit={q.lineUnit}
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
