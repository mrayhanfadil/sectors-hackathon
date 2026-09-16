import React from "react"
import type { KeyRatioPage } from "@/lib/reportTypes"
import { formatIdn } from "./tokens"

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
        <div className="rounded-xl border border-[#E7E3DA] bg-white p-4 dark:border-[#2A2822] dark:bg-[#1B1A16] space-y-2">
          <div className="flex items-center justify-between border-b border-[#E7E3DA]/60 pb-2 dark:border-[#2A2822]">
            <span className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
              Profil margin profitabilitas
            </span>
            <span className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">% pendapatan</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-right text-[#6B6659] border-b border-[#E7E3DA]/60 dark:border-[#2A2822] dark:text-[#A8A296]">
                  <th className="text-left py-1.5 font-medium">Metrik</th>
                  {years.map((y) => (
                    <th key={y} className="py-1.5 px-2 font-medium">
                      {y}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E7E3DA]/40 dark:divide-[#2A2822]/40">
                {gm.length > 0 && (
                  <tr>
                    <td className="py-1.5 text-[#1C1B17] font-medium dark:text-[#EDEAE3]">Gross margin</td>
                    {gm.map((v, i) => (
                      <td key={i} className="py-1.5 px-2 text-right font-mono tabular-nums text-[#1C1B17] dark:text-[#EDEAE3]">
                        {fmtRatioVal(v)}
                      </td>
                    ))}
                  </tr>
                )}
                {ebitdaM.length > 0 && (
                  <tr>
                    <td className="py-1.5 text-[#1C1B17] font-medium dark:text-[#EDEAE3]">EBITDA margin</td>
                    {ebitdaM.map((v, i) => (
                      <td key={i} className="py-1.5 px-2 text-right font-mono tabular-nums font-semibold text-[#157F3D] dark:text-[#34D399]">
                        {fmtRatioVal(v)}
                      </td>
                    ))}
                  </tr>
                )}
                {netM.length > 0 && (
                  <tr>
                    <td className="py-1.5 text-[#1C1B17] font-medium dark:text-[#EDEAE3]">Net margin</td>
                    {netM.map((v, i) => (
                      <td key={i} className="py-1.5 px-2 text-right font-mono tabular-nums text-[#1C1B17] dark:text-[#EDEAE3]">
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
        <div className="rounded-xl border border-[#E7E3DA] bg-white p-4 dark:border-[#2A2822] dark:bg-[#1B1A16] space-y-2">
          <div className="flex items-center justify-between border-b border-[#E7E3DA]/60 pb-2 dark:border-[#2A2822]">
            <span className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
              Imbal hasil (ROAE dan ROAA)
            </span>
            <span className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">Saldo rata-rata</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-right text-[#6B6659] border-b border-[#E7E3DA]/60 dark:border-[#2A2822] dark:text-[#A8A296]">
                  <th className="text-left py-1.5 font-medium">Metrik</th>
                  {years.map((y) => (
                    <th key={y} className="py-1.5 px-2 font-medium">
                      {y}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E7E3DA]/40 dark:divide-[#2A2822]/40">
                {roae.length > 0 && (
                  <tr>
                    <td className="py-1.5 text-[#1C1B17] font-medium dark:text-[#EDEAE3]">ROAE</td>
                    {roae.map((v, i) => (
                      <td key={i} className="py-1.5 px-2 text-right font-mono tabular-nums font-semibold text-[#0E6E63] dark:text-[#4FD1B5]">
                        {fmtRatioVal(v)}
                      </td>
                    ))}
                  </tr>
                )}
                {roaa.length > 0 && (
                  <tr>
                    <td className="py-1.5 text-[#1C1B17] font-medium dark:text-[#EDEAE3]">ROAA</td>
                    {roaa.map((v, i) => (
                      <td key={i} className="py-1.5 px-2 text-right font-mono tabular-nums text-[#6B6659] dark:text-[#A8A296]">
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
        <div className="rounded-xl border border-[#E7E3DA] bg-white p-4 dark:border-[#2A2822] dark:bg-[#1B1A16] space-y-2">
          <div className="flex items-center justify-between border-b border-[#E7E3DA]/60 pb-2 dark:border-[#2A2822]">
            <span className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
              Solvabilitas dan cakupan bunga
            </span>
            <span className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">Rasio (x)</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-right text-[#6B6659] border-b border-[#E7E3DA]/60 dark:border-[#2A2822] dark:text-[#A8A296]">
                  <th className="text-left py-1.5 font-medium">Metrik</th>
                  {years.map((y) => (
                    <th key={y} className="py-1.5 px-2 font-medium">
                      {y}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E7E3DA]/40 dark:divide-[#2A2822]/40">
                {gearing.length > 0 && (
                  <tr>
                    <td className="py-1.5 text-[#1C1B17] font-medium dark:text-[#EDEAE3]">Net gearing (x)</td>
                    {gearing.map((v, i) => (
                      <td key={i} className="py-1.5 px-2 text-right font-mono tabular-nums text-[#1C1B17] dark:text-[#EDEAE3]">
                        {fmtRatioVal(v, "x")}
                      </td>
                    ))}
                  </tr>
                )}
                {coverage.length > 0 && (
                  <tr>
                    <td className="py-1.5 text-[#1C1B17] font-medium dark:text-[#EDEAE3]">Interest coverage (x)</td>
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
        <div className="rounded-xl border border-[#E7E3DA] bg-white p-4 dark:border-[#2A2822] dark:bg-[#1B1A16] space-y-2">
          <div className="flex items-center justify-between border-b border-[#E7E3DA]/60 pb-2 dark:border-[#2A2822]">
            <span className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
              Laju pertumbuhan (YoY)
            </span>
            <span className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">% pertumbuhan</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-right text-[#6B6659] border-b border-[#E7E3DA]/60 dark:border-[#2A2822] dark:text-[#A8A296]">
                  <th className="text-left py-1.5 font-medium">Metrik</th>
                  {years.map((y) => (
                    <th key={y} className="py-1.5 px-2 font-medium">
                      {y}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E7E3DA]/40 dark:divide-[#2A2822]/40">
                {salesG.length > 0 && (
                  <tr>
                    <td className="py-1.5 text-[#1C1B17] font-medium dark:text-[#EDEAE3]">Pertumbuhan pendapatan</td>
                    {salesG.map((v, i) => (
                      <td key={i} className="py-1.5 px-2 text-right font-mono tabular-nums text-[#1C1B17] dark:text-[#EDEAE3]">
                        {fmtRatioVal(v)}
                      </td>
                    ))}
                  </tr>
                )}
                {netG.length > 0 && (
                  <tr>
                    <td className="py-1.5 text-[#1C1B17] font-medium dark:text-[#EDEAE3]">Pertumbuhan laba bersih</td>
                    {netG.map((v, i) => (
                      <td key={i} className="py-1.5 px-2 text-right font-mono tabular-nums font-semibold text-[#0E6E63] dark:text-[#4FD1B5]">
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
