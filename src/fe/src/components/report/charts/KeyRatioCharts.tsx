import React from "react"
import type { KeyRatioPage, StatementRow } from "@/lib/reportTypes"
import { TOKENS, formatIdn } from "./tokens"

export interface KeyRatioChartsProps {
  keyRatio?: KeyRatioPage
}

function fmtRatioVal(v: number | null | undefined, unit: string = "%"): string {
  if (v == null || !Number.isFinite(v)) return "—"
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

  // Find rows across all sections
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
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
      {/* 1. Profitability Margins Trend */}
      {hasMarginData && (
        <div className="rounded border border-[#D6E2EE] bg-white p-3 dark:border-[#262930] dark:bg-[#121418] space-y-2">
          <div className="flex items-center justify-between border-b border-[#D6E2EE] pb-1.5 dark:border-[#262930]">
            <span className="font-mono text-xs font-bold text-[#0B1F3A] uppercase dark:text-neutral-100">
              Profil Margin Profitabilitas
            </span>
            <span className="font-mono text-[10px] text-[#63748A]">% Pendapatan</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full font-mono text-[11px]">
              <thead>
                <tr className="text-right text-[#63748A] border-b border-[#D6E2EE]/60">
                  <th className="text-left py-1 font-medium">Metrik</th>
                  {years.map((y) => (
                    <th key={y} className="py-1 px-1.5 font-medium">
                      {y}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D6E2EE]/40">
                {gm.length > 0 && (
                  <tr>
                    <td className="py-1 text-[#0B1F3A] font-medium dark:text-neutral-200">Gross Margin</td>
                    {gm.map((v, i) => (
                      <td key={i} className="py-1 px-1.5 text-right tabular-nums text-[#0B1F3A] dark:text-neutral-300">
                        {fmtRatioVal(v)}
                      </td>
                    ))}
                  </tr>
                )}
                {ebitdaM.length > 0 && (
                  <tr>
                    <td className="py-1 text-[#0B1F3A] font-medium dark:text-neutral-200">EBITDA Margin</td>
                    {ebitdaM.map((v, i) => (
                      <td key={i} className="py-1 px-1.5 text-right tabular-nums font-bold text-[#1E8F5F] dark:text-[#34D399]">
                        {fmtRatioVal(v)}
                      </td>
                    ))}
                  </tr>
                )}
                {netM.length > 0 && (
                  <tr>
                    <td className="py-1 text-[#0B1F3A] font-medium dark:text-neutral-200">Net Margin</td>
                    {netM.map((v, i) => (
                      <td key={i} className="py-1 px-1.5 text-right tabular-nums text-[#0B1F3A] dark:text-neutral-300">
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
        <div className="rounded border border-[#D6E2EE] bg-white p-3 dark:border-[#262930] dark:bg-[#121418] space-y-2">
          <div className="flex items-center justify-between border-b border-[#D6E2EE] pb-1.5 dark:border-[#262930]">
            <span className="font-mono text-xs font-bold text-[#0B1F3A] uppercase dark:text-neutral-100">
              Imbal Hasil (Return on Equity &amp; Assets)
            </span>
            <span className="font-mono text-[10px] text-[#63748A]">Saldo Rata-rata</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full font-mono text-[11px]">
              <thead>
                <tr className="text-right text-[#63748A] border-b border-[#D6E2EE]/60">
                  <th className="text-left py-1 font-medium">Metrik</th>
                  {years.map((y) => (
                    <th key={y} className="py-1 px-1.5 font-medium">
                      {y}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D6E2EE]/40">
                {roae.length > 0 && (
                  <tr>
                    <td className="py-1 text-[#0B1F3A] font-medium dark:text-neutral-200">ROAE</td>
                    {roae.map((v, i) => (
                      <td key={i} className="py-1 px-1.5 text-right tabular-nums font-bold text-[#0B1F3A] dark:text-[#A9C9E8]">
                        {fmtRatioVal(v)}
                      </td>
                    ))}
                  </tr>
                )}
                {roaa.length > 0 && (
                  <tr>
                    <td className="py-1 text-[#0B1F3A] font-medium dark:text-neutral-200">ROAA</td>
                    {roaa.map((v, i) => (
                      <td key={i} className="py-1 px-1.5 text-right tabular-nums text-[#63748A] dark:text-neutral-400">
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
        <div className="rounded border border-[#D6E2EE] bg-white p-3 dark:border-[#262930] dark:bg-[#121418] space-y-2">
          <div className="flex items-center justify-between border-b border-[#D6E2EE] pb-1.5 dark:border-[#262930]">
            <span className="font-mono text-xs font-bold text-[#0B1F3A] uppercase dark:text-neutral-100">
              Solvabilitas &amp; Cakupan Bunga
            </span>
            <span className="font-mono text-[10px] text-[#63748A]">Rasio (x)</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full font-mono text-[11px]">
              <thead>
                <tr className="text-right text-[#63748A] border-b border-[#D6E2EE]/60">
                  <th className="text-left py-1 font-medium">Metrik</th>
                  {years.map((y) => (
                    <th key={y} className="py-1 px-1.5 font-medium">
                      {y}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D6E2EE]/40">
                {gearing.length > 0 && (
                  <tr>
                    <td className="py-1 text-[#0B1F3A] font-medium dark:text-neutral-200">Net Gearing (x)</td>
                    {gearing.map((v, i) => (
                      <td key={i} className="py-1 px-1.5 text-right tabular-nums text-[#0B1F3A] dark:text-neutral-300">
                        {fmtRatioVal(v, "x")}
                      </td>
                    ))}
                  </tr>
                )}
                {coverage.length > 0 && (
                  <tr>
                    <td className="py-1 text-[#0B1F3A] font-medium dark:text-neutral-200">Interest Coverage (x)</td>
                    {coverage.map((v, i) => (
                      <td key={i} className="py-1 px-1.5 text-right tabular-nums font-bold text-[#1E8F5F] dark:text-[#34D399]">
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
        <div className="rounded border border-[#D6E2EE] bg-white p-3 dark:border-[#262930] dark:bg-[#121418] space-y-2">
          <div className="flex items-center justify-between border-b border-[#D6E2EE] pb-1.5 dark:border-[#262930]">
            <span className="font-mono text-xs font-bold text-[#0B1F3A] uppercase dark:text-neutral-100">
              Laju Pertumbuhan (YoY)
            </span>
            <span className="font-mono text-[10px] text-[#63748A]">% Pertumbuhan</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full font-mono text-[11px]">
              <thead>
                <tr className="text-right text-[#63748A] border-b border-[#D6E2EE]/60">
                  <th className="text-left py-1 font-medium">Metrik</th>
                  {years.map((y) => (
                    <th key={y} className="py-1 px-1.5 font-medium">
                      {y}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D6E2EE]/40">
                {salesG.length > 0 && (
                  <tr>
                    <td className="py-1 text-[#0B1F3A] font-medium dark:text-neutral-200">Sales Growth</td>
                    {salesG.map((v, i) => (
                      <td key={i} className="py-1 px-1.5 text-right tabular-nums text-[#0B1F3A] dark:text-neutral-300">
                        {fmtRatioVal(v)}
                      </td>
                    ))}
                  </tr>
                )}
                {netG.length > 0 && (
                  <tr>
                    <td className="py-1 text-[#0B1F3A] font-medium dark:text-neutral-200">Net Profit Growth</td>
                    {netG.map((v, i) => (
                      <td key={i} className="py-1 px-1.5 text-right tabular-nums font-bold text-[#0B1F3A] dark:text-[#A9C9E8]">
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
