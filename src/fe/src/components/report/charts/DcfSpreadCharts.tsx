import React from "react"
import type { ReportPayload } from "@/lib/reportPayload"
import { TOKENS, PendingBlock, formatIdn } from "./tokens"

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
        return "bg-[#FBFAF7] text-[#1C1B17] dark:bg-[#14130F] dark:text-[#EDEAE3]"
      case "h-pos1":
        return "bg-[#EBF6EE] text-[#157F3D] dark:bg-[#157F3D]/20 dark:text-[#34D399]"
      case "h-pos2":
        return "bg-[#0E6E63] text-white dark:bg-[#4FD1B5] dark:text-[#14130F]"
      default:
        return "bg-white text-[#1C1B17] dark:bg-[#1B1A16] dark:text-[#EDEAE3]"
    }
  }

  // Method spread bars calculations
  const methods = [
    { label: `DCF · Gordon g ${baseG}`, val: fvGordon, bg: "bg-[#0E6E63]", border: "border-[#0E6E63]" },
    { label: "DCF · exit multiple", val: fvExit, bg: "bg-[#4FD1B5]", border: "border-[#0E6E63]" },
    { label: "Kelipatan EV/EBITDA", val: typeof legs.ev_ebitda === "number" ? legs.ev_ebitda : null, bg: "bg-[#E7E3DA]", border: "border-[#A8A296]" },
  ].filter((m) => m.val !== null && m.val > 0)

  const maxMethodVal = Math.max(
    ...methods.map((m) => m.val as number),
    price ?? 0,
    1
  ) * 1.15

  return (
    <div className="space-y-5 font-sans">
      {/* Summary KPI Chips Strip */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-xl border border-[#E7E3DA] bg-white p-4 dark:border-[#2A2822] dark:bg-[#1B1A16]">
          <div className="text-xs text-[#6B6659] dark:text-[#A8A296]">PV terminal / EV</div>
          <div className="mt-1 text-lg font-semibold text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
            {tvShare !== null ? `${(tvShare * 100).toFixed(1)}%` : "-"}
          </div>
          <div className="text-[11px] text-[#6B6659] mt-0.5 dark:text-[#A8A296]">
            Nilai wajar bertumpu di luar periode eksplisit
          </div>
        </div>

        <div className="rounded-xl border border-[#E7E3DA] bg-white p-4 dark:border-[#2A2822] dark:bg-[#1B1A16]">
          <div className="text-xs text-[#6B6659] dark:text-[#A8A296]">Net debt / EV</div>
          <div className="mt-1 text-lg font-semibold text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
            {netDebt !== null && evGordon !== null && evGordon > 0
              ? `${((netDebt / evGordon) * 100).toFixed(1)}%`
              : "-"}
          </div>
          <div className="text-[11px] text-[#6B6659] mt-0.5 dark:text-[#A8A296]">
            Sisa ekuitas pemegang saham {equityGordon !== null ? `Rp ${formatIdn(equityGordon / 1e12, 2)} tn` : "-"}
          </div>
        </div>

        <div className="rounded-xl border border-[#E7E3DA] bg-white p-4 dark:border-[#2A2822] dark:bg-[#1B1A16]">
          <div className="text-xs text-[#6B6659] dark:text-[#A8A296]">Rentang grid WACC × g</div>
          <div className="mt-1 text-lg font-semibold text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
            {swing.min !== undefined && swing.max !== undefined
              ? `Rp ${formatIdn(swing.min, 0)} – ${formatIdn(swing.max, 0)}`
              : "-"}
          </div>
          <div className="text-[11px] text-[#6B6659] mt-0.5 dark:text-[#A8A296]">
            Kasus dasar {baseFv !== null ? `Rp ${formatIdn(baseFv, 0)}` : "-"} (WACC {baseWacc} · g {baseG})
          </div>
        </div>
      </div>

      {/* Grid: Bridge Waterfall Table + Method Comparison Spread */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {/* EV -> Equity Bridge */}
        <div className="flex flex-col justify-between rounded-xl border border-[#E7E3DA] bg-white p-5 dark:border-[#2A2822] dark:bg-[#1B1A16]">
          <div>
            <div className="mb-3 flex items-center justify-between border-b border-[#E7E3DA]/60 pb-2 dark:border-[#2A2822]">
              <span className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                Enterprise Value → Ekuitas (Basis Gordon)
              </span>
              <span className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">{vp.bridge_basis ?? "Basis Asumsi"}</span>
            </div>

            {/* Visual Stacked Bar Segment */}
            {evGordon !== null && netDebt !== null && equityGordon !== null && evGordon > 0 && (
              <div className="my-3 space-y-1.5">
                <div className="flex h-3.5 w-full overflow-hidden rounded-md border border-[#E7E3DA] dark:border-[#2A2822]">
                  <div
                    style={{ width: `${Math.max(0, Math.min(100, (equityGordon / evGordon) * 100))}%` }}
                    className="bg-[#0E6E63]"
                    title={`Equity Value: ${((equityGordon / evGordon) * 100).toFixed(1)}%`}
                  />
                  <div
                    style={{ width: `${Math.max(0, Math.min(100, (netDebt / evGordon) * 100))}%` }}
                    className="bg-[#E7E3DA] dark:bg-[#2A2822]"
                    title={`Net Debt: ${((netDebt / evGordon) * 100).toFixed(1)}%`}
                  />
                </div>
                <div className="flex justify-between text-xs text-[#6B6659] dark:text-[#A8A296]">
                  <span className="flex items-center gap-1.5">
                    <span className="inline-block h-2 w-2 rounded-xs bg-[#0E6E63]" /> Ekuitas ({((equityGordon / evGordon) * 100).toFixed(1)}%)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="inline-block h-2 w-2 rounded-xs bg-[#E7E3DA] dark:bg-[#2A2822]" /> Net debt ({((netDebt / evGordon) * 100).toFixed(1)}%)
                  </span>
                </div>
              </div>
            )}

            {/* Footing Table */}
            <div className="mt-4 overflow-hidden rounded-lg border border-[#E7E3DA] dark:border-[#2A2822]">
              <table className="w-full text-xs">
                <tbody className="divide-y divide-[#E7E3DA]/60 dark:divide-[#2A2822]/60">
                  <tr className="bg-[#FBFAF7]/50 dark:bg-[#14130F]/30">
                    <td className="px-3.5 py-2 text-[#1C1B17] dark:text-[#EDEAE3]">Enterprise Value</td>
                    <td className="px-3.5 py-2 text-right font-medium text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
                      {evGordon !== null ? `Rp ${formatIdn(evGordon / 1e12, 2)} tn` : "-"}
                    </td>
                  </tr>
                  <tr>
                    <td className="px-3.5 py-2 text-[#B4232A] dark:text-[#F87171] font-medium">(−) Net Debt</td>
                    <td className="px-3.5 py-2 text-right font-medium text-[#B4232A] font-mono tabular-nums dark:text-[#F87171]">
                      {netDebt !== null ? `Rp ${formatIdn(netDebt / 1e12, 2)} tn` : "-"}
                    </td>
                  </tr>
                  <tr className="bg-[#FBFAF7] font-semibold dark:bg-[#14130F]">
                    <td className="px-3.5 py-2.5 text-[#1C1B17] dark:text-[#EDEAE3]">Equity Value</td>
                    <td className="px-3.5 py-2.5 text-right text-[#0E6E63] font-mono tabular-nums dark:text-[#4FD1B5]">
                      {equityGordon !== null ? `Rp ${formatIdn(equityGordon / 1e12, 2)} tn` : "-"}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <p className="mt-3 text-[11px] text-[#6B6659] leading-normal dark:text-[#A8A296]">
            Net debt diperlakukan sebagai faktor pengurang langsung. Nilai dicetak sebagai besaran positif dengan tanda (−) agar kalkulasi footing tepat.
          </p>
        </div>

        {/* Sebaran Metode Valuasi */}
        <div className="flex flex-col justify-between rounded-xl border border-[#E7E3DA] bg-white p-5 dark:border-[#2A2822] dark:bg-[#1B1A16]">
          <div>
            <div className="mb-3 flex items-center justify-between border-b border-[#E7E3DA]/60 pb-2 dark:border-[#2A2822]">
              <span className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                Sebaran metode (Rp / saham)
              </span>
              {price !== null && (
                <span className="text-xs font-medium text-[#B4232A] dark:text-[#F87171]">
                  Harga pasar: Rp {formatIdn(price, 0)}
                </span>
              )}
            </div>

            {/* Custom Bar Chart for Methods */}
            {methods.length > 0 ? (
              <div className="relative mt-4 h-36 w-full border-b border-[#E7E3DA] dark:border-[#2A2822]">
                {/* Reference Market Price Dashed Line */}
                {price !== null && price > 0 && (
                  <div
                    className="absolute left-0 right-0 border-t border-dashed border-[#B4232A] z-10"
                    style={{ bottom: `${Math.min(95, (price / maxMethodVal) * 100)}%` }}
                  >
                    <span className="absolute -top-4 left-1 bg-white px-1 text-[10px] font-medium text-[#B4232A] dark:bg-[#1B1A16] dark:text-[#F87171]">
                      Harga pasar {formatIdn(price, 0)}
                    </span>
                  </div>
                )}

                {/* Bars */}
                <div className="flex h-full items-end justify-around gap-3 px-2">
                  {methods.map((m, idx) => {
                    const heightPct = Math.max(8, ((m.val as number) / maxMethodVal) * 100)
                    return (
                      <div key={idx} className="flex flex-1 flex-col items-center justify-end h-full">
                        <span className="mb-1 text-xs font-semibold text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
                          {formatIdn(m.val, 0)}
                        </span>
                        <div
                          style={{ height: `${heightPct}%` }}
                          className={`w-full max-w-[56px] rounded-t-md ${m.bg}`}
                        />
                        <span className="mt-2 text-center text-xs text-[#6B6659] dark:text-[#A8A296] line-clamp-1">
                          {m.label}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-xs text-[#6B6659] dark:text-[#A8A296]">
                Data komparasi metode belum tersedia.
              </div>
            )}
          </div>

          {fvGordon && fvExit && (
            <p className="mt-3 text-xs leading-relaxed text-[#6B6659] dark:text-[#A8A296]">
              Selisih Gordon vs Exit Multiple {formatIdn(fvExit / fvGordon, 1)}× pada basis FCFF yang sama - dibaca sebagai komparasi skenario, bukan dirata-rata.
            </p>
          )}
        </div>
      </div>

      {/* Sensitivity Heatmap Matrix (WACC x g) */}
      <div className="rounded-xl border border-[#E7E3DA] bg-white p-5 dark:border-[#2A2822] dark:bg-[#1B1A16]">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2 border-b border-[#E7E3DA]/60 pb-2 dark:border-[#2A2822]">
          <span className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
            Analisa sensitivitas - WACC × Pertumbuhan terminal (g)
          </span>
          <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
            Kasus dasar: WACC {baseWacc} · g {baseG}
          </span>
        </div>

        {sensRows.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-xs">
              <thead>
                <tr>
                  <th className="border border-[#E7E3DA] bg-[#FBFAF7] px-3 py-2 text-left font-semibold text-[#1C1B17] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#EDEAE3]">
                    WACC \ g
                  </th>
                  {sensCols.map((col, cIdx) => (
                    <th
                      key={cIdx}
                      className="border border-[#E7E3DA] bg-[#FBFAF7] px-3 py-2 text-right font-semibold text-[#1C1B17] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#EDEAE3]"
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sensRows.map((r, rIdx) => (
                  <tr key={rIdx}>
                    <td className="border border-[#E7E3DA] bg-[#FBFAF7]/70 px-3 py-2 font-semibold text-[#1C1B17] dark:border-[#2A2822] dark:bg-[#14130F]/50 dark:text-[#EDEAE3]">
                      {r.label}
                    </td>
                    {r.cells.map((cell, cIdx) => {
                      const isBase = Boolean(cell.base)
                      return (
                        <td
                          key={cIdx}
                          className={`border border-[#E7E3DA] px-3 py-2 text-right font-mono tabular-nums dark:border-[#2A2822] ${getBandStyle(
                            cell.band
                          )} ${isBase ? "ring-2 ring-inset ring-[#0E6E63] font-bold dark:ring-[#4FD1B5]" : ""}`}
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
            <div className="mt-3.5 flex flex-wrap items-center gap-3 text-xs text-[#6B6659] dark:text-[#A8A296]">
              <span className="font-medium text-[#1C1B17] dark:text-[#EDEAE3]">Keterangan sel:</span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-3 w-3.5 rounded-xs bg-[#FDF2F2] border border-[#F8C8CB]" /> Rendah
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-3 w-3.5 rounded-xs bg-[#FBFAF7] border border-[#E7E3DA]" /> Netral
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-3 w-3.5 rounded-xs bg-[#EBF6EE] border border-[#BCE2C9]" /> Tinggi
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-3 w-3.5 rounded-xs border-2 border-[#0E6E63]" /> Kasus dasar
              </span>
            </div>

            <p className="mt-2 text-xs text-[#6B6659] dark:text-[#A8A296]">
              Kasus dasar (WACC {baseWacc} · g {baseG}) dibingkai; isi sel = nilai wajar per saham (Rp). Rentang grid: Rp{" "}
              {swing.min !== undefined ? formatIdn(swing.min, 0) : "-"} – Rp{" "}
              {swing.max !== undefined ? formatIdn(swing.max, 0) : "-"}.
            </p>
          </div>
        ) : (
          <div className="py-6 text-center text-xs text-[#6B6659] dark:text-[#A8A296]">
            Matriks sensitivitas belum tersedia.
          </div>
        )}
      </div>

      {/* Disclosure Notes */}
      {notes.length > 0 && (
        <div className="rounded-xl border border-[#E7E3DA] bg-[#FBFAF7] p-4 space-y-2 dark:border-[#2A2822] dark:bg-[#14130F]">
          <div className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
            Catatan keterbatasan asumsi
          </div>
          <div className="divide-y divide-[#E7E3DA]/60 text-xs dark:divide-[#2A2822]/60">
            {notes.map((note, nIdx) => {
              const [head, ...rest] = note.includes(" - ") ? note.split(" - ") : [null, note]
              const body = head ? rest.join(" - ") : note

              return (
                <div key={nIdx} className="py-2 first:pt-1 last:pb-0 text-[#6B6659] leading-relaxed dark:text-[#A8A296]">
                  {head ? (
                    <>
                      <span className="font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">{head}</span> - {body}
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
