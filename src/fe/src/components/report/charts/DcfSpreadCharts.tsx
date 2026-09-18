import React from "react"
import {
  ResponsiveContainer,
  BarChart,
  Bar,
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
import { PendingBlock, formatIdn } from "./tokens"
import {
  seriesColor,
  SECTORAL_GRID,
  SECTORAL_ZERO_BASELINE,
  SECTORAL_TICK,
  SECTORAL_TOOLTIP_STYLE,
  SECTORAL_LEGEND_STYLE,
} from "./sectoralSeries"

interface SensitivityCell {
  value: string | number
  base?: boolean
  band?: string
}

interface SensitivityRow {
  label: string
  cells: SensitivityCell[]
}

export function DcfSpreadCharts({ payload }: { payload: ReportPayload }) {
  const p = payload as Record<string, any>
  const vp = p.valuation_page

  if (!vp || vp.available === false) {
    const missing = Array.isArray(vp?.missing) && vp.missing.length > 0 ? ` (${vp.missing.join(", ")})` : ""
    return <PendingBlock label="Bridge DCF dan sensitivitas" message={`valuasi intrinsik belum tersedia${missing}.`} />
  }

  const bridge = vp.bridge ?? {}
  const sensitivity = vp.sensitivity ?? {}
  const notes: string[] = Array.isArray(vp.notes) ? vp.notes : []
  const legs = vp.legs ?? p.valuation?.legs ?? {}
  const drivers = vp.drivers ?? {}

  // Bridge numbers
  const evGordon = typeof bridge.ev_gordon === "number" ? bridge.ev_gordon : null
  const netDebt = typeof bridge.net_debt === "number" ? bridge.net_debt : null
  const equityGordon = typeof bridge.equity_gordon === "number" ? bridge.equity_gordon : null
  const fvGordon = typeof bridge.fv_gordon === "number" ? bridge.fv_gordon : null
  const fvExit = typeof bridge.fv_exit === "number" ? bridge.fv_exit : null
  const tvShare = typeof bridge.tv_share === "number" ? bridge.tv_share : null

  // Sensitivity matrix
  const sensRows: SensitivityRow[] = Array.isArray(sensitivity.rows) ? sensitivity.rows : []
  const sensCols: string[] = Array.isArray(sensitivity.columns) ? sensitivity.columns : []
  const baseWacc = sensitivity.base_wacc ?? "-"
  const baseG = sensitivity.base_g ?? "-"
  const baseFv = typeof sensitivity.base_fv === "number" ? sensitivity.base_fv : null
  const swing = sensitivity.swing ?? sensitivity.stats ?? {}

  // Traded price
  const price = typeof p.cover?.rating_box?.price === "number" ? p.cover.rating_box.price : (typeof drivers.price === "number" ? drivers.price : null)

  const getBandStyle = (band?: string) => {
    switch (band) {
      case "h-neg2":
        return "bg-[#FDF2F2] text-[#B4232A] dark:bg-[#B4232A]/20 dark:text-[#F87171]"
      case "h-neg1":
        return "bg-[#FEF9EE] text-[#A16207] dark:bg-[#A16207]/20 dark:text-[#FBBF24]"
      case "h-mid":
        return "bg-[#f1f5f9] text-[#333333] dark:bg-[#333333] dark:text-[#f1f5f9]"
      case "h-pos1":
        return "bg-[#EBF6EE] text-[#157F3D] dark:bg-[#157F3D]/20 dark:text-[#34D399]"
      case "h-pos2":
        return "bg-[#0928B1] text-white dark:bg-[#7596FF] dark:text-[#333333]"
      default:
        return "bg-white text-[#333333] dark:bg-[#090a0c] dark:text-[#f1f5f9]"
    }
  }

  // Method spread bars calculations
  const methods = [
    { label: `DCF · Gordon g ${baseG}`, val: fvGordon },
    { label: "DCF · exit multiple", val: fvExit },
    { label: "Kelipatan EV/EBITDA", val: typeof legs.ev_ebitda === "number" ? legs.ev_ebitda : null },
  ].filter((m) => m.val !== null && (m.val as number) > 0) as { label: string; val: number }[]

  const methodData = methods.map((m) => ({
    name: m.label,
    value: m.val,
    valueLabel: formatIdn(m.val, 0),
  }))

  return (
    <div className="space-y-5 font-sans">
      {/* Summary KPI Chips Strip */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-xl border border-[#D9D9D9] bg-white p-4 dark:border-[#262930] dark:bg-[#090a0c]">
          <div className="text-xs text-[#666666] dark:text-[#666666]">PV terminal / EV</div>
          <div className="mt-1 text-lg font-semibold text-[#333333] font-mono tabular-nums dark:text-[#f1f5f9]">
            {tvShare !== null ? `${(tvShare * 100).toFixed(1)}%` : "-"}
          </div>
          <div className="text-[11px] text-[#666666] mt-0.5 dark:text-[#666666]">
            Nilai wajar bertumpu di luar periode eksplisit
          </div>
        </div>

        <div className="rounded-xl border border-[#D9D9D9] bg-white p-4 dark:border-[#262930] dark:bg-[#090a0c]">
          <div className="text-xs text-[#666666] dark:text-[#666666]">Net debt / EV</div>
          <div className="mt-1 text-lg font-semibold text-[#333333] font-mono tabular-nums dark:text-[#f1f5f9]">
            {netDebt !== null && evGordon !== null && evGordon > 0
              ? `${((netDebt / evGordon) * 100).toFixed(1)}%`
              : "-"}
          </div>
          <div className="text-[11px] text-[#666666] mt-0.5 dark:text-[#666666]">
            Sisa ekuitas pemegang saham {equityGordon !== null ? `Rp ${formatIdn(equityGordon / 1e12, 2)} tn` : "-"}
          </div>
        </div>

        <div className="rounded-xl border border-[#D9D9D9] bg-white p-4 dark:border-[#262930] dark:bg-[#090a0c]">
          <div className="text-xs text-[#666666] dark:text-[#666666]">Rentang grid WACC × g</div>
          <div className="mt-1 text-lg font-semibold text-[#333333] font-mono tabular-nums dark:text-[#f1f5f9]">
            {swing.min !== undefined && swing.max !== undefined
              ? `Rp ${formatIdn(swing.min, 0)} – ${formatIdn(swing.max, 0)}`
              : "-"}
          </div>
          <div className="text-[11px] text-[#666666] mt-0.5 dark:text-[#666666]">
            Kasus dasar {baseFv !== null ? `Rp ${formatIdn(baseFv, 0)}` : "-"} (WACC {baseWacc} · g {baseG})
          </div>
        </div>
      </div>

      {/* Grid: Bridge Waterfall Table + Method Comparison Spread */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {/* EV -> Equity Bridge */}
        <div className="flex flex-col justify-between rounded-xl border border-[#D9D9D9] bg-white p-5 dark:border-[#262930] dark:bg-[#090a0c]">
          <div>
            <div className="mb-3 flex items-center justify-between border-b border-[#D9D9D9]/60 pb-2 dark:border-[#262930]">
              <span className="text-xs font-semibold text-[#333333] dark:text-[#f1f5f9]">
                Enterprise Value → Ekuitas (Basis Gordon)
              </span>
              <span className="text-[11px] text-[#666666] dark:text-[#666666]">{vp.bridge_basis ?? "Basis Asumsi"}</span>
            </div>

            {/* Visual Stacked Bar Segment */}
            {evGordon !== null && netDebt !== null && equityGordon !== null && evGordon > 0 && (
              <div className="my-3 space-y-1.5">
                <div className="flex h-3.5 w-full overflow-hidden rounded-md border border-[#D9D9D9] dark:border-[#262930]">
                  <div
                    style={{ width: `${Math.max(0, Math.min(100, (equityGordon / evGordon) * 100))}%` }}
                    className="bg-[#0928B1]"
                    title={`Equity Value: ${((equityGordon / evGordon) * 100).toFixed(1)}%`}
                  />
                  <div
                    style={{ width: `${Math.max(0, Math.min(100, (netDebt / evGordon) * 100))}%` }}
                    className="bg-[#D9D9D9] dark:bg-[#262930]"
                    title={`Net Debt: ${((netDebt / evGordon) * 100).toFixed(1)}%`}
                  />
                </div>
                <div className="flex justify-between text-xs text-[#666666] dark:text-[#666666]">
                  <span className="flex items-center gap-1.5">
                    <span className="inline-block h-2 w-2 rounded-xs bg-[#0928B1]" /> Ekuitas ({((equityGordon / evGordon) * 100).toFixed(1)}%)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="inline-block h-2 w-2 rounded-xs bg-[#D9D9D9] dark:bg-[#262930]" /> Net debt ({((netDebt / evGordon) * 100).toFixed(1)}%)
                  </span>
                </div>
              </div>
            )}

            {/* Footing Table */}
            <div className="mt-4 overflow-hidden rounded-lg border border-[#D9D9D9] dark:border-[#262930]">
              <table className="w-full text-xs">
                <tbody className="divide-y divide-[#D9D9D9]/60 dark:divide-[#262930]/60">
                  <tr className="bg-[#f1f5f9]/50 dark:bg-[#333333]/30">
                    <td className="px-3.5 py-2 text-[#333333] dark:text-[#f1f5f9]">Enterprise Value</td>
                    <td className="px-3.5 py-2 text-right font-medium text-[#333333] font-mono tabular-nums dark:text-[#f1f5f9]">
                      {evGordon !== null ? `Rp ${formatIdn(evGordon / 1e12, 2)} tn` : "-"}
                    </td>
                  </tr>
                  <tr>
                    <td className="px-3.5 py-2 text-[#B4232A] dark:text-[#F87171] font-medium">(−) Net Debt</td>
                    <td className="px-3.5 py-2 text-right font-medium text-[#B4232A] font-mono tabular-nums dark:text-[#F87171]">
                      {netDebt !== null ? `Rp ${formatIdn(netDebt / 1e12, 2)} tn` : "-"}
                    </td>
                  </tr>
                  <tr className="bg-[#f1f5f9] font-semibold dark:bg-[#333333]">
                    <td className="px-3.5 py-2.5 text-[#333333] dark:text-[#f1f5f9]">Equity Value</td>
                    <td className="px-3.5 py-2.5 text-right text-[#0928B1] font-mono tabular-nums dark:text-[#7596FF]">
                      {equityGordon !== null ? `Rp ${formatIdn(equityGordon / 1e12, 2)} tn` : "-"}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <p className="mt-3 text-[11px] text-[#666666] leading-normal dark:text-[#666666]">
            Net debt diperlakukan sebagai faktor pengurang langsung. Nilai dicetak sebagai besaran positif dengan tanda (−) agar kalkulasi footing tepat.
          </p>
        </div>

        {/* Sebaran Metode Valuasi */}
        <div className="flex flex-col justify-between rounded-xl border border-[#D9D9D9] bg-white p-5 dark:border-[#262930] dark:bg-[#090a0c]">
          <div>
            <div className="mb-3 flex items-center justify-between border-b border-[#D9D9D9]/60 pb-2 dark:border-[#262930]">
              <span className="text-xs font-semibold text-[#333333] dark:text-[#f1f5f9]">
                Sebaran metode (Rp / saham)
              </span>
              {price !== null && (
                <span className="text-xs font-medium text-[#B4232A] dark:text-[#F87171]">
                  Harga pasar: Rp {formatIdn(price, 0)}
                </span>
              )}
            </div>

            {/* Sectoral recharts method comparison */}
            {methods.length > 0 ? (
              <div className="mt-4">
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={methodData} margin={{ top: 20, right: 8, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={SECTORAL_GRID} />
                    <XAxis dataKey="name" tick={SECTORAL_TICK} axisLine={false} tickLine={false} interval={0} height={44} />
                    <YAxis tick={SECTORAL_TICK} axisLine={false} tickLine={false} tickFormatter={(v: number) => formatIdn(v, 0)} width={48} />
                    <Tooltip
                      cursor={{ fill: "rgba(0,0,0,0.04)" }}
                      contentStyle={SECTORAL_TOOLTIP_STYLE}
                      formatter={(value: unknown) => [typeof value === "number" ? formatIdn(value, 0) : "-", "Rp / saham"]}
                      labelFormatter={(label: unknown) => String(label)}
                    />
                    <Legend iconType="square" wrapperStyle={SECTORAL_LEGEND_STYLE} />
                    <ReferenceLine y={0} stroke={SECTORAL_ZERO_BASELINE} />
                    {price !== null && price > 0 && (
                      <ReferenceLine y={price} stroke={seriesColor(4)} strokeDasharray="5 3" label={{ value: `Harga pasar ${formatIdn(price, 0)}`, fontSize: 11, fill: seriesColor(4), position: "insideTopLeft" }} />
                    )}
                    <Bar dataKey="value" name="Nilai wajar (Rp / saham)" maxBarSize={56} radius={[4, 4, 0, 0]}>
                      {methodData.map((_, idx) => (
                        <Cell key={`cell-${idx}`} fill={seriesColor(idx)} />
                      ))}
                      <LabelList dataKey="valueLabel" position="top" fill={seriesColor(0)} fontSize={11} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="py-8 text-center text-xs text-[#666666] dark:text-[#666666]">
                Data komparasi metode belum tersedia.
              </div>
            )}
          </div>

          {fvGordon && fvExit && (
            <p className="mt-3 text-xs leading-relaxed text-[#666666] dark:text-[#666666]">
              Selisih Gordon vs Exit Multiple {formatIdn(fvExit / fvGordon, 1)}× pada basis FCFF yang sama - dibaca sebagai komparasi skenario, bukan dirata-rata.
            </p>
          )}
        </div>
      </div>

      {/* Sensitivity Heatmap Matrix (WACC x g) */}
      <div className="rounded-xl border border-[#D9D9D9] bg-white p-5 dark:border-[#262930] dark:bg-[#090a0c]">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2 border-b border-[#D9D9D9]/60 pb-2 dark:border-[#262930]">
          <span className="text-xs font-semibold text-[#333333] dark:text-[#f1f5f9]">
            Analisa sensitivitas - WACC × Pertumbuhan terminal (g)
          </span>
          <span className="text-xs text-[#666666] dark:text-[#666666]">
            Kasus dasar: WACC {baseWacc} · g {baseG}
          </span>
        </div>

        {sensRows.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-xs">
              <thead>
                <tr>
                  <th className="border border-[#D9D9D9] bg-[#f1f5f9] px-3 py-2 text-left font-semibold text-[#333333] dark:border-[#262930] dark:bg-[#333333] dark:text-[#f1f5f9]">
                    WACC \ g
                  </th>
                  {sensCols.map((col, cIdx) => (
                    <th
                      key={cIdx}
                      className="border border-[#D9D9D9] bg-[#f1f5f9] px-3 py-2 text-right font-semibold text-[#333333] dark:border-[#262930] dark:bg-[#333333] dark:text-[#f1f5f9]"
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sensRows.map((r, rIdx) => (
                  <tr key={rIdx}>
                    <td className="border border-[#D9D9D9] bg-[#f1f5f9]/70 px-3 py-2 font-semibold text-[#333333] dark:border-[#262930] dark:bg-[#333333]/50 dark:text-[#f1f5f9]">
                      {r.label}
                    </td>
                    {r.cells.map((cell, cIdx) => {
                      const isBase = Boolean(cell.base)
                      return (
                        <td
                          key={cIdx}
                          className={`border border-[#D9D9D9] px-3 py-2 text-right font-mono tabular-nums dark:border-[#262930] ${getBandStyle(
                            cell.band
                          )} ${isBase ? "ring-2 ring-inset ring-[#0928B1] font-bold dark:ring-[#7596FF]" : ""}`}
                          title={`WACC ${r.label} x g ${sensCols[cIdx] ?? ""}: ${cell.value}${isBase ? " (Kasus Dasar)" : ""}`}
                        >
                          {cell.value}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Heatmap Legend */}
            <div className="mt-3.5 flex flex-wrap items-center gap-3 text-xs text-[#666666] dark:text-[#666666]">
              <span className="font-medium text-[#333333] dark:text-[#f1f5f9]">Keterangan sel:</span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-3 w-3.5 rounded-xs bg-[#FDF2F2] border border-[#F8C8CB]" /> Rendah
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-3 w-3.5 rounded-xs bg-[#f1f5f9] border border-[#D9D9D9]" /> Netral
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-3 w-3.5 rounded-xs bg-[#EBF6EE] border border-[#BCE2C9]" /> Tinggi
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-3 w-3.5 rounded-xs border-2 border-[#0928B1]" /> Kasus dasar
              </span>
            </div>

            <p className="mt-2 text-xs text-[#666666] dark:text-[#666666]">
              Kasus dasar (WACC {baseWacc} · g {baseG}) dibingkai; isi sel = nilai wajar per saham (Rp). Rentang grid: Rp{" "}
              {swing.min !== undefined ? formatIdn(swing.min, 0) : "-"} – Rp{" "}
              {swing.max !== undefined ? formatIdn(swing.max, 0) : "-"}.
            </p>
          </div>
        ) : (
          <div className="py-6 text-center text-xs text-[#666666] dark:text-[#666666]">
            Matriks sensitivitas belum tersedia.
          </div>
        )}
      </div>

      {/* Disclosure Notes */}
      {notes.length > 0 && (
        <div className="rounded-xl border border-[#D9D9D9] bg-[#f1f5f9] p-4 space-y-2 dark:border-[#262930] dark:bg-[#333333]">
          <div className="text-xs font-semibold text-[#333333] dark:text-[#f1f5f9]">
            Catatan keterbatasan asumsi
          </div>
          <div className="divide-y divide-[#D9D9D9]/60 text-xs dark:divide-[#262930]/60">
            {notes.map((note, nIdx) => {
              const [head, ...rest] = note.includes(" - ") ? note.split(" - ") : [null, note]
              const body = head ? rest.join(" - ") : note

              return (
                <div key={nIdx} className="py-2 first:pt-1 last:pb-0 text-[#666666] leading-relaxed dark:text-[#666666]">
                  {head ? (
                    <>
                      <span className="font-semibold text-[#333333] dark:text-[#f1f5f9]">{head}</span> - {body}
                    </>
                  ) : (
                    body
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
