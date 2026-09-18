import React from "react"
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from "recharts"
import type { KeyRatioPage } from "@/lib/reportTypes"
import { formatIdn } from "./tokens"
import {
  seriesColor,
  SECTORAL_GRID,
  SECTORAL_ZERO_BASELINE,
  SECTORAL_TICK,
  SECTORAL_TOOLTIP_STYLE,
  SECTORAL_LEGEND_STYLE,
} from "./sectoralSeries"

export interface KeyRatioChartsProps {
  keyRatio?: KeyRatioPage
}

function fmtRatioVal(v: number | null | undefined, unit: string = "%"): string {
  if (v == null || !Number.isFinite(v)) return "-"
  const formatted = formatIdn(Math.abs(v), 1)
  if (v < 0) {
    return `(${formatted})${unit}`
  }
  return `${formatted}${unit}`
}

interface TrendSeries {
  key: string
  label: string
  values: (number | null)[]
}

/**
 * Sectoral multiline trend chart. Series colors follow SECTORAL_SERIES order.
 * Tables below remain the source of truth; this chart only visualizes them.
 */
function RatioTrendChart({ years, series, unit }: { years: string[]; series: TrendSeries[]; unit: string }) {
  const data = years.map((year, i) => {
    const row: Record<string, string | number | null> = { name: year }
    for (const s of series) {
      row[s.key] = s.values[i] ?? null
    }
    return row
  })

  return (
    <ResponsiveContainer width="100%" height={180}>
      <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={SECTORAL_GRID} />
        <XAxis dataKey="name" tick={SECTORAL_TICK} axisLine={false} tickLine={false} />
        <YAxis tick={SECTORAL_TICK} axisLine={false} tickLine={false} tickFormatter={(v: number) => formatIdn(v, 0)} width={44} />
        <Tooltip
          contentStyle={SECTORAL_TOOLTIP_STYLE}
          formatter={(value: unknown, name: unknown) => [
            typeof value === "number" ? fmtRatioVal(value, unit) : "-",
            String(name),
          ]}
          labelFormatter={(label: unknown) => String(label)}
        />
        <Legend iconType="square" wrapperStyle={SECTORAL_LEGEND_STYLE} />
        <ReferenceLine y={0} stroke={SECTORAL_ZERO_BASELINE} />
        {series.map((s, idx) => (
          <Line
            key={s.key}
            type="monotone"
            dataKey={s.key}
            name={s.label}
            stroke={seriesColor(idx)}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}

export function KeyRatioCharts({ keyRatio }: KeyRatioChartsProps) {
  if (!keyRatio || keyRatio.available === false || !keyRatio.sections || keyRatio.sections.length === 0) {
    return null
  }

  const years = keyRatio.years || ["2024A", "2025A", "2026F", "2027F", "2028F"]

  const rowMap = new Map<string, (number | string | null)[]>()
  for (const sec of keyRatio.sections) {
    for (const r of sec.rows || []) {
      const normalizedLabel = r.label.trim().toLowerCase()
      rowMap.set(normalizedLabel, r.cells || [])
    }
  }

  const getSeries = (labelKey: string): (number | null)[] => {
    for (const [k, cells] of rowMap.entries()) {
      if (k.includes(labelKey.toLowerCase())) {
        return cells.map((c) => (typeof c === "number" && Number.isFinite(c) ? c : null))
      }
    }
    return []
  }

  const gm = getSeries("gross margin")
  const ebitdaM = getSeries("ebitda margin")
  const netM = getSeries("net margin")
  const roae = getSeries("roae")
  const roaa = getSeries("roaa")
  const gearing = getSeries("net gearing")
  const coverage = getSeries("interest coverage")
  const salesG = getSeries("sales")
  const netG = getSeries("net profit")

  const hasMarginData = gm.some((v) => v !== null) || ebitdaM.some((v) => v !== null)
  const hasReturnData = roae.some((v) => v !== null) || roaa.some((v) => v !== null)
  const hasLevData = gearing.some((v) => v !== null) || coverage.some((v) => v !== null)
  const hasGrowthData = salesG.some((v) => v !== null) || netG.some((v) => v !== null)

  if (!hasMarginData && !hasReturnData && !hasLevData && !hasGrowthData) {
    return null
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 font-sans">
      {/* 1. Profitability Margins Trend */}
      {hasMarginData && (
        <div className="rounded-xl border border-[#D9D9D9] bg-white p-4 dark:border-[#262930] dark:bg-[#090a0c] space-y-2">
          <div className="flex items-center justify-between border-b border-[#D9D9D9]/60 pb-2 dark:border-[#262930]">
            <span className="text-xs font-semibold text-[#333333] dark:text-[#f1f5f9]">
              Profil margin profitabilitas
            </span>
            <span className="text-[11px] text-[#666666] dark:text-[#666666]">% pendapatan</span>
          </div>
          <RatioTrendChart
            years={years}
            unit="%"
            series={[
              { key: "gm", label: "Gross margin", values: gm },
              { key: "ebitdaM", label: "EBITDA margin", values: ebitdaM },
              { key: "netM", label: "Net margin", values: netM },
            ].filter((s) => s.values.length > 0)}
          />
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-right text-[#666666] border-b border-[#D9D9D9]/60 dark:border-[#262930] dark:text-[#666666]">
                  <th className="text-left py-1.5 font-medium">Metrik</th>
                  {years.map((y) => (
                    <th key={y} className="py-1.5 px-2 font-medium">
                      {y}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D9D9D9]/40 dark:divide-[#262930]/40">
                {gm.length > 0 && (
                  <tr>
                    <td className="py-1.5 text-[#333333] font-medium dark:text-[#f1f5f9]">Gross margin</td>
                    {gm.map((v, i) => (
                      <td key={i} className="py-1.5 px-2 text-right font-mono tabular-nums text-[#333333] dark:text-[#f1f5f9]">
                        {fmtRatioVal(v)}
                      </td>
                    ))}
                  </tr>
                )}
                {ebitdaM.length > 0 && (
                  <tr>
                    <td className="py-1.5 text-[#333333] font-medium dark:text-[#f1f5f9]">EBITDA margin</td>
                    {ebitdaM.map((v, i) => (
                      <td key={i} className="py-1.5 px-2 text-right font-mono tabular-nums font-semibold text-[#157F3D] dark:text-[#34D399]">
                        {fmtRatioVal(v)}
                      </td>
                    ))}
                  </tr>
                )}
                {netM.length > 0 && (
                  <tr>
                    <td className="py-1.5 text-[#333333] font-medium dark:text-[#f1f5f9]">Net margin</td>
                    {netM.map((v, i) => (
                      <td key={i} className="py-1.5 px-2 text-right font-mono tabular-nums text-[#333333] dark:text-[#f1f5f9]">
                        {fmtRatioVal(v)}
                      </td>
                    ))}
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 2. Return on Equity & Return on Assets */}
      {hasReturnData && (
        <div className="rounded-xl border border-[#D9D9D9] bg-white p-4 dark:border-[#262930] dark:bg-[#090a0c] space-y-2">
          <div className="flex items-center justify-between border-b border-[#D9D9D9]/60 pb-2 dark:border-[#262930]">
            <span className="text-xs font-semibold text-[#333333] dark:text-[#f1f5f9]">
              Imbal hasil (ROAE dan ROAA)
            </span>
            <span className="text-[11px] text-[#666666] dark:text-[#666666]">Saldo rata-rata</span>
          </div>
          <RatioTrendChart
            years={years}
            unit="%"
            series={[
              { key: "roae", label: "ROAE", values: roae },
              { key: "roaa", label: "ROAA", values: roaa },
            ].filter((s) => s.values.length > 0)}
          />
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-right text-[#666666] border-b border-[#D9D9D9]/60 dark:border-[#262930] dark:text-[#666666]">
                  <th className="text-left py-1.5 font-medium">Metrik</th>
                  {years.map((y) => (
                    <th key={y} className="py-1.5 px-2 font-medium">
                      {y}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D9D9D9]/40 dark:divide-[#262930]/40">
                {roae.length > 0 && (
                  <tr>
                    <td className="py-1.5 text-[#333333] font-medium dark:text-[#f1f5f9]">ROAE</td>
                    {roae.map((v, i) => (
                      <td key={i} className="py-1.5 px-2 text-right font-mono tabular-nums font-semibold text-[#0928B1] dark:text-[#7596FF]">
                        {fmtRatioVal(v)}
                      </td>
                    ))}
                  </tr>
                )}
                {roaa.length > 0 && (
                  <tr>
                    <td className="py-1.5 text-[#333333] font-medium dark:text-[#f1f5f9]">ROAA</td>
                    {roaa.map((v, i) => (
                      <td key={i} className="py-1.5 px-2 text-right font-mono tabular-nums text-[#666666] dark:text-[#666666]">
                        {fmtRatioVal(v)}
                      </td>
                    ))}
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 3. Leverage & Coverage */}
      {hasLevData && (
        <div className="rounded-xl border border-[#D9D9D9] bg-white p-4 dark:border-[#262930] dark:bg-[#090a0c] space-y-2">
          <div className="flex items-center justify-between border-b border-[#D9D9D9]/60 pb-2 dark:border-[#262930]">
            <span className="text-xs font-semibold text-[#333333] dark:text-[#f1f5f9]">
              Solvabilitas dan cakupan bunga
            </span>
            <span className="text-[11px] text-[#666666] dark:text-[#666666]">Rasio (x)</span>
          </div>
          <RatioTrendChart
            years={years}
            unit="x"
            series={[
              { key: "gearing", label: "Net gearing (x)", values: gearing },
              { key: "coverage", label: "Interest coverage (x)", values: coverage },
            ].filter((s) => s.values.length > 0)}
          />
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-right text-[#666666] border-b border-[#D9D9D9]/60 dark:border-[#262930] dark:text-[#666666]">
                  <th className="text-left py-1.5 font-medium">Metrik</th>
                  {years.map((y) => (
                    <th key={y} className="py-1.5 px-2 font-medium">
                      {y}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D9D9D9]/40 dark:divide-[#262930]/40">
                {gearing.length > 0 && (
                  <tr>
                    <td className="py-1.5 text-[#333333] font-medium dark:text-[#f1f5f9]">Net gearing (x)</td>
                    {gearing.map((v, i) => (
                      <td key={i} className="py-1.5 px-2 text-right font-mono tabular-nums text-[#333333] dark:text-[#f1f5f9]">
                        {fmtRatioVal(v, "x")}
                      </td>
                    ))}
                  </tr>
                )}
                {coverage.length > 0 && (
                  <tr>
                    <td className="py-1.5 text-[#333333] font-medium dark:text-[#f1f5f9]">Interest coverage (x)</td>
                    {coverage.map((v, i) => (
                      <td key={i} className="py-1.5 px-2 text-right font-mono tabular-nums font-semibold text-[#157F3D] dark:text-[#34D399]">
                        {fmtRatioVal(v, "x")}
                      </td>
                    ))}
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 4. Growth Rates */}
      {hasGrowthData && (
        <div className="rounded-xl border border-[#D9D9D9] bg-white p-4 dark:border-[#262930] dark:bg-[#090a0c] space-y-2">
          <div className="flex items-center justify-between border-b border-[#D9D9D9]/60 pb-2 dark:border-[#262930]">
            <span className="text-xs font-semibold text-[#333333] dark:text-[#f1f5f9]">
              Laju pertumbuhan (YoY)
            </span>
            <span className="text-[11px] text-[#666666] dark:text-[#666666]">% pertumbuhan</span>
          </div>
          <RatioTrendChart
            years={years}
            unit="%"
            series={[
              { key: "salesG", label: "Pertumbuhan pendapatan", values: salesG },
              { key: "netG", label: "Pertumbuhan laba bersih", values: netG },
            ].filter((s) => s.values.length > 0)}
          />
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-right text-[#666666] border-b border-[#D9D9D9]/60 dark:border-[#262930] dark:text-[#666666]">
                  <th className="text-left py-1.5 font-medium">Metrik</th>
                  {years.map((y) => (
                    <th key={y} className="py-1.5 px-2 font-medium">
                      {y}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D9D9D9]/40 dark:divide-[#262930]/40">
                {salesG.length > 0 && (
                  <tr>
                    <td className="py-1.5 text-[#333333] font-medium dark:text-[#f1f5f9]">Pertumbuhan pendapatan</td>
                    {salesG.map((v, i) => (
                      <td key={i} className="py-1.5 px-2 text-right font-mono tabular-nums text-[#333333] dark:text-[#f1f5f9]">
                        {fmtRatioVal(v)}
                      </td>
                    ))}
                  </tr>
                )}
                {netG.length > 0 && (
                  <tr>
                    <td className="py-1.5 text-[#333333] font-medium dark:text-[#f1f5f9]">Pertumbuhan laba bersih</td>
                    {netG.map((v, i) => (
                      <td key={i} className="py-1.5 px-2 text-right font-mono tabular-nums font-semibold text-[#0928B1] dark:text-[#7596FF]">
                        {fmtRatioVal(v)}
                      </td>
                    ))}
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
