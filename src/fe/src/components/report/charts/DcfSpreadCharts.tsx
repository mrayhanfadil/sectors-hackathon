// DcfSpreadCharts component.
// Renders the FCFF -> Enterprise -> Equity bridge, the WACC x g sensitivity heat grid,
// method comparison spread, and verbatim disclosure notes from payload.valuation_page.

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
    return <PendingBlock label="Bridge DCF & sensitivitas" message={`valuasi intrinsik belum tersedia${missing}.`} />
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
  const baseWacc = sensitivity.base_wacc ?? "—"
  const baseG = sensitivity.base_g ?? "—"
  const baseFv = typeof sensitivity.base_fv === "number" ? sensitivity.base_fv : null
  const swing = sensitivity.swing ?? sensitivity.stats ?? {}

  // Traded price (from cover or valuation drivers)
  const price = typeof p.cover?.rating_box?.price === "number" ? p.cover.rating_box.price : (typeof drivers.price === "number" ? drivers.price : null)

  // Color mapping for sensitivity grid tiers strictly matching PDF rules
  const getBandStyle = (band?: string) => {
    switch (band) {
      case "h-neg2":
        return "bg-[#C0392BD9] text-white" // rgba(192,57,43,0.86)
      case "h-neg1":
        return "bg-[#C0392B57] text-neutral-900 dark:text-neutral-100" // rgba(192,57,43,0.34)
      case "h-mid":
        return "bg-[#F2E9DC] text-[#1A2733]" // parity #F2E9DC
      case "h-pos1":
        return "bg-[#DCEBF7] text-[#1A2733]" // +10%..+50% #DCEBF7
      case "h-pos2":
        return "bg-[#0B1F3A] text-white" // > +50% #0B1F3A
      default:
        return "bg-neutral-50 text-neutral-800 dark:bg-[#181a1f] dark:text-neutral-200"
    }
  }

  // Method spread bars calculations
  const methods = [
    { label: `DCF · Gordon g ${baseG}`, val: fvGordon, bg: "bg-[#0B1F3A]", border: "border-[#0B1F3A]" },
    { label: "DCF · exit multiple", val: fvExit, bg: "bg-[#A9C9E8]", border: "border-[#2C4A6B]" },
    { label: "TP gate-primary", val: typeof legs.ev_ebitda === "number" ? legs.ev_ebitda : null, bg: "bg-[#E4EEF7]", border: "border-[#A9C9E8]" },
  ].filter((m) => m.val !== null && m.val > 0)

  const maxMethodVal = Math.max(
    ...methods.map((m) => m.val as number),
    price ?? 0,
    1
  ) * 1.15

  return (
    <div className="space-y-4 font-sans">
      {/* Header */}
      <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-neutral-200 pb-1.5 dark:border-[#262930]">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-900 dark:text-neutral-100">
            Valuasi Intrinsik &amp; Analisa Sensitivitas (DCF Spread)
          </h3>
          <p className="text-[11px] text-neutral-500 dark:text-neutral-400">
            Model DCF FCFF eksplisit, jembatan ekuitas (Gordon Growth), dan matriks WACC × g
          </p>
        </div>
        <span className="font-mono text-[10px] text-neutral-400">
          CONVENTION: {vp.convention ?? "year-end (1/(1+WACC)^t)"}
        </span>
      </div>

      {/* Summary KPI Chips Strip */}
      <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-3 font-mono">
        <div className="rounded-md border border-neutral-200 bg-neutral-50/70 p-2.5 dark:border-[#262930] dark:bg-[#121418]">
          <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">PV TERMINAL / EV</div>
          <div className="mt-0.5 text-base font-bold text-[#0B1F3A] tabular-nums dark:text-sky-400">
            {tvShare !== null ? `${(tvShare * 100).toFixed(1)}%` : "—"}
          </div>
          <div className="text-[10px] text-neutral-500 dark:text-neutral-400 font-sans">
            Nilai wajar bertumpu di luar periode eksplisit
          </div>
        </div>

        <div className="rounded-md border border-neutral-200 bg-neutral-50/70 p-2.5 dark:border-[#262930] dark:bg-[#121418]">
          <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">NET DEBT / EV</div>
          <div className="mt-0.5 text-base font-bold text-[#0B1F3A] tabular-nums dark:text-sky-400">
            {netDebt !== null && evGordon !== null && evGordon > 0
              ? `${((netDebt / evGordon) * 100).toFixed(1)}%`
              : "—"}
          </div>
          <div className="text-[10px] text-neutral-500 dark:text-neutral-400 font-sans">
            Sisa untuk pemegang saham {equityGordon !== null ? `Rp ${formatIdn(equityGordon / 1e12, 2)} tn` : "—"}
          </div>
        </div>

        <div className="rounded-md border border-neutral-200 bg-neutral-50/70 p-2.5 dark:border-[#262930] dark:bg-[#121418]">
          <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">RENTANG GRID WACC × G</div>
          <div className="mt-0.5 text-base font-bold text-[#0B1F3A] tabular-nums dark:text-sky-400">
            {swing.min !== undefined && swing.max !== undefined
              ? `Rp ${formatIdn(swing.min, 0)} – ${formatIdn(swing.max, 0)}`
              : "—"}
          </div>
          <div className="text-[10px] text-neutral-500 dark:text-neutral-400 font-sans">
            Dasar {baseFv !== null ? `Rp ${formatIdn(baseFv, 0)}` : "—"} (WACC {baseWacc} · g {baseG})
          </div>
        </div>
      </div>

      {/* Grid: Bridge Waterfall Table + Method Comparison Spread */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* EV -> Equity Bridge */}
        <div className="flex flex-col justify-between rounded-lg border border-neutral-200 bg-white p-3.5 shadow-xs dark:border-[#262930] dark:bg-[#121418]">
          <div>
            <div className="mb-2 flex items-center justify-between border-b border-neutral-100 pb-1.5 dark:border-[#1f2228]">
              <span className="text-xs font-bold uppercase tracking-wider text-neutral-900 dark:text-neutral-100">
                Enterprise Value → Ekuitas (Basis Gordon)
              </span>
              <span className="font-mono text-[10px] text-neutral-400">{vp.bridge_basis ?? "Basis Asumsi"}</span>
            </div>

            {/* Visual Stacked Bar Segment */}
            {evGordon !== null && netDebt !== null && equityGordon !== null && evGordon > 0 && (
              <div className="my-2.5 space-y-1">
                <div className="flex h-3 w-full overflow-hidden rounded border border-neutral-200 dark:border-[#262930]">
                  <div
                    style={{ width: `${Math.max(0, Math.min(100, (equityGordon / evGordon) * 100))}%` }}
                    className="bg-[#0B1F3A]"
                    title={`Equity Value: ${((equityGordon / evGordon) * 100).toFixed(1)}%`}
                  />
                  <div
                    style={{ width: `${Math.max(0, Math.min(100, (netDebt / evGordon) * 100))}%` }}
                    className="bg-[#D6E2EE] dark:bg-neutral-600"
                    title={`Net Debt: ${((netDebt / evGordon) * 100).toFixed(1)}%`}
                  />
                </div>
                <div className="flex justify-between font-mono text-[10px] text-neutral-500 dark:text-neutral-400">
                  <span className="flex items-center gap-1">
                    <span className="inline-block h-2 w-2 rounded-xs bg-[#0B1F3A]" /> Ekuitas ({((equityGordon / evGordon) * 100).toFixed(1)}%)
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="inline-block h-2 w-2 rounded-xs bg-[#D6E2EE] dark:bg-neutral-600" /> Net Debt ({((netDebt / evGordon) * 100).toFixed(1)}%)
                  </span>
                </div>
              </div>
            )}

            {/* Footing Table */}
            <div className="mt-3 overflow-hidden rounded border border-neutral-200 dark:border-[#262930]">
              <table className="w-full text-xs font-mono">
                <tbody className="divide-y divide-neutral-200 dark:divide-[#262930]">
                  <tr className="bg-neutral-50/60 dark:bg-[#181a1f]/50">
                    <td className="px-3 py-1.5 text-neutral-800 dark:text-neutral-200">Enterprise Value</td>
                    <td className="px-3 py-1.5 text-right font-bold text-[#0B1F3A] tabular-nums dark:text-neutral-100">
                      {evGordon !== null ? `Rp ${formatIdn(evGordon / 1e12, 2)} tn` : "—"}
                    </td>
                  </tr>
                  <tr>
                    <td className="px-3 py-1.5 text-rose-700 dark:text-rose-400 font-medium">(−) Net Debt</td>
                    <td className="px-3 py-1.5 text-right font-bold text-rose-700 tabular-nums dark:text-rose-400">
                      {netDebt !== null ? `Rp ${formatIdn(netDebt / 1e12, 2)} tn` : "—"}
                    </td>
                  </tr>
                  <tr className="border-t-2 border-neutral-900 bg-neutral-100 font-bold dark:border-neutral-100 dark:bg-[#20242c]">
                    <td className="px-3 py-2 text-neutral-900 dark:text-neutral-100">Equity Value</td>
                    <td className="px-3 py-2 text-right text-neutral-900 tabular-nums dark:text-neutral-100">
                      {equityGordon !== null ? `Rp ${formatIdn(equityGordon / 1e12, 2)} tn` : "—"}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <p className="mt-2.5 font-mono text-[10px] text-neutral-400 leading-tight">
            * Net debt diperlakukan sebagai faktor pengurang langsung (deduction). Nilai dicetak sebagai besaran positif dengan tanda (−) agar kalkulasi footing tepat.
          </p>
        </div>

        {/* Sebaran Metode Valuasi */}
        <div className="flex flex-col justify-between rounded-lg border border-neutral-200 bg-white p-3.5 shadow-xs dark:border-[#262930] dark:bg-[#121418]">
          <div>
            <div className="mb-2 flex items-center justify-between border-b border-neutral-100 pb-1.5 dark:border-[#1f2228]">
              <span className="text-xs font-bold uppercase tracking-wider text-neutral-900 dark:text-neutral-100">
                Sebaran Metode (Rp / Saham)
              </span>
              {price !== null && (
                <span className="font-mono text-[10px] font-bold text-[#C0392B]">
                  Harga Pasar: Rp {formatIdn(price, 0)}
                </span>
              )}
            </div>

            {/* Custom Bar Chart for Methods */}
            {methods.length > 0 ? (
              <div className="relative mt-4 h-36 w-full border-b border-neutral-300 dark:border-[#262930]">
                {/* Reference Market Price Dashed Line */}
                {price !== null && price > 0 && (
                  <div
                    className="absolute left-0 right-0 border-t border-dashed border-[#C0392B] z-10"
                    style={{ bottom: `${Math.min(95, (price / maxMethodVal) * 100)}%` }}
                  >
                    <span className="absolute -top-4 left-1 bg-white px-1 font-mono text-[9px] font-bold text-[#C0392B] dark:bg-[#121418]">
                      Harga Pasar {formatIdn(price, 0)}
                    </span>
                  </div>
                )}

                {/* Bars */}
                <div className="flex h-full items-end justify-around gap-2 px-2">
                  {methods.map((m, idx) => {
                    const heightPct = Math.max(8, ((m.val as number) / maxMethodVal) * 100)
                    return (
                      <div key={idx} className="flex flex-1 flex-col items-center justify-end h-full">
                        <span className="mb-1 font-mono text-[11px] font-bold text-neutral-900 tabular-nums dark:text-neutral-100">
                          {formatIdn(m.val, 0)}
                        </span>
                        <div
                          style={{ height: `${heightPct}%` }}
                          className={`w-full max-w-[64px] rounded-t-xs border ${m.border} ${m.bg}`}
                        />
                        <span className="mt-1.5 text-center font-sans text-[10px] text-neutral-600 dark:text-neutral-400 line-clamp-1">
                          {m.label}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-xs font-mono text-neutral-400">
                Data komparasi metode belum tersedia.
              </div>
            )}
          </div>

          {fvGordon && fvExit && (
            <p className="mt-2.5 text-[10px] leading-relaxed text-neutral-500 dark:text-neutral-400 font-sans">
              Gap Gordon vs Exit Multiple {formatIdn(fvExit / fvGordon, 1)}× pada basis FCFF yang sama — dibaca sebagai asumsi belum tuntas, bukan dirata-rata.
            </p>
          )}
        </div>
      </div>

      {/* Sensitivity Heatmap Matrix (WACC x g) */}
      <div className="rounded-lg border border-neutral-200 bg-white p-3.5 shadow-xs dark:border-[#262930] dark:bg-[#121418]">
        <div className="mb-2.5 flex flex-wrap items-center justify-between gap-2 border-b border-neutral-100 pb-2 dark:border-[#1f2228]">
          <div className="flex items-center gap-2">
            <span className="rounded bg-neutral-900 px-1.5 py-0.5 font-mono text-[10px] font-bold text-amber-400 dark:bg-amber-400/10 dark:text-amber-400">
              HEATMAP
            </span>
            <span className="text-xs font-bold uppercase tracking-wider text-neutral-900 dark:text-neutral-100">
              Analisa Sensitivitas — WACC × Terminal Growth (g)
            </span>
          </div>
          <span className="font-mono text-[10px] text-neutral-400">
            Base Case: WACC {baseWacc} · g {baseG}
          </span>
        </div>

        {sensRows.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-xs font-mono">
              <thead>
                <tr>
                  <th className="border border-neutral-200 bg-[#0B1F3A] px-2.5 py-1.5 text-left font-bold text-white dark:border-[#262930]">
                    WACC \ g
                  </th>
                  {sensCols.map((col, cIdx) => (
                    <th
                      key={cIdx}
                      className="border border-neutral-200 bg-[#0B1F3A] px-2.5 py-1.5 text-right font-bold text-white dark:border-[#262930]"
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sensRows.map((r, rIdx) => (
                  <tr key={rIdx}>
                    <td className="border border-neutral-200 bg-neutral-100 px-2.5 py-1.5 font-bold text-neutral-900 dark:border-[#262930] dark:bg-[#181a1f] dark:text-neutral-100">
                      {r.label}
                    </td>
                    {r.cells.map((cell, cIdx) => {
                      const isBase = Boolean(cell.base)
                      return (
                        <td
                          key={cIdx}
                          className={`border border-neutral-200 px-2.5 py-1.5 text-right font-medium tabular-nums dark:border-[#262930] ${getBandStyle(
                            cell.band
                          )} ${isBase ? "ring-2 ring-inset ring-[#0B1F3A] font-extrabold" : ""}`}
                          title={`WACC ${r.label} x g ${sensCols[cIdx] ?? ""}: ${cell.value}${isBase ? " (BASE CASE)" : ""}`}
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
            <div className="mt-3 flex flex-wrap items-center gap-3 font-mono text-[10px] text-neutral-600 dark:text-neutral-400">
              <span className="font-bold text-neutral-700 dark:text-neutral-300">Posisi vs Base:</span>
              <span className="flex items-center gap-1">
                <span className="inline-block h-3 w-4 rounded-xs bg-[#C0392BD9]" /> &lt; −50%
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block h-3 w-4 rounded-xs bg-[#C0392B57]" /> −50%…−10%
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block h-3 w-4 rounded-xs bg-[#F2E9DC] border border-neutral-300" /> ±10%
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block h-3 w-4 rounded-xs bg-[#DCEBF7]" /> +10%…+50%
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block h-3 w-4 rounded-xs bg-[#0B1F3A]" /> &gt; +50%
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block h-3 w-4 rounded-xs border-2 border-[#0B1F3A]" /> [Base Case]
              </span>
            </div>

            <p className="mt-2 font-mono text-[10px] text-neutral-500 dark:text-neutral-400 leading-normal">
              Base case (WACC {baseWacc} · g {baseG}) dibingkai; isi sel = Fair Value per saham (Rp). Rentang grid: Rp{" "}
              {swing.min !== undefined ? formatIdn(swing.min, 0) : "—"} – Rp{" "}
              {swing.max !== undefined ? formatIdn(swing.max, 0) : "—"}.
            </p>
          </div>
        ) : (
          <div className="py-6 text-center text-xs font-mono text-neutral-400">
            Matriks sensitivitas belum tersedia.
          </div>
        )}
      </div>

      {/* Verbatim Disclosure Notes */}
      {notes.length > 0 && (
        <div className="rounded-lg border border-neutral-200 bg-neutral-50/70 p-3.5 dark:border-[#262930] dark:bg-[#121418]">
          <div className="mb-2 flex items-center gap-2 border-b border-neutral-200 pb-1 text-xs font-bold uppercase tracking-wider text-neutral-900 dark:border-[#262930] dark:text-neutral-100">
            <span>Catatan Pengungkapan &amp; Keterbatasan Asumsi (Verbatim)</span>
          </div>
          <div className="divide-y divide-neutral-200 font-sans text-xs dark:divide-[#262930]">
            {notes.map((note, nIdx) => {
              const [head, ...rest] = note.includes(" — ") ? note.split(" — ") : [null, note]
              const body = head ? rest.join(" — ") : note

              return (
                <div key={nIdx} className="py-2 first:pt-1 last:pb-0 text-neutral-700 dark:text-neutral-300 leading-relaxed">
                  {head ? (
                    <>
                      <span className="font-bold text-neutral-900 dark:text-neutral-100">{head}</span> — {body}
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
