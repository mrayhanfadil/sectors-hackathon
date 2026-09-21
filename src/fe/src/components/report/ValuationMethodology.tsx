import React from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { DcfSpreadCharts, PeersCharts } from "@/components/report/charts"
import { formatIdn, formatPct } from "@/components/report/charts/tokens"
import type { FullReportPayload, ValuationPage, PeersPage, PeerRow, PeerStat } from "@/lib/reportTypes"

export interface ValuationMethodologyProps {
  ticker: string
  payload?: FullReportPayload | null
}

function fmtIDR(n: number | null | undefined): string {
  if (n == null || Number.isNaN(Number(n))) return "-"
  return Number(n).toLocaleString("id-ID")
}

function fmtDec(n: number | null | undefined, digits: number = 2): string {
  if (n == null || Number.isNaN(Number(n))) return "-"
  return Number(n).toLocaleString("id-ID", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

function getSensitivityBandStyle(band?: string): string {
  switch (band) {
    case "h-neg2":
      return "bg-[#F7E1D7] text-[#762D1A] dark:bg-[#4A261D] dark:text-[#FCA5A5]"
    case "h-neg1":
      return "bg-[#FDF1EB] text-[#8A432F] dark:bg-[#38231E] dark:text-[#FDBA74]"
    case "h-mid":
      return "bg-[#FAF7F0] text-[#333333] dark:bg-[#26282B] dark:text-[#E2E8F0]"
    case "h-pos1":
      return "bg-[#EAF2EC] text-[#294A34] dark:bg-[#1E3327] dark:text-[#8CE0A8]"
    case "h-pos2":
      return "bg-[#DCE8E0] text-[#1C3A27] dark:bg-[#2D4536] dark:text-[#A3D9B5]"
    default:
      return "bg-[#FAF7F0] text-[#333333] dark:bg-[#26282B] dark:text-[#E2E8F0]"
  }
}

function getPeerColumnType(
  col: string,
  idx: number
): "symbol" | "name" | "pe" | "pbv" | "ev_ebitda" | "roe" | "market_cap" | "other" {
  const c = col.toLowerCase()
  if (c.includes("ticker") || c.includes("symbol") || (idx === 0 && !c.includes("("))) return "symbol"
  if (c.includes("perusahaan") || c.includes("company") || c.includes("emiten") || (idx === 1 && !c.includes("("))) return "name"
  if (c.includes("p/e") || c.includes("per") || c === "pe") return "pe"
  if (c.includes("p/bv") || c.includes("pbv") || c === "pb" || c.includes("p/b")) return "pbv"
  if (c.includes("ev/ebitda") || c.includes("ev_ebitda")) return "ev_ebitda"
  if (c.includes("roe")) return "roe"
  if (c.includes("market cap") || c.includes("mcap") || c.includes("kapitalisasi")) return "market_cap"
  return "other"
}

function renderPeerCell(r: PeerRow, col: string, idx: number): React.ReactNode {
  const type = getPeerColumnType(col, idx)
  switch (type) {
    case "symbol":
      return <span className="font-semibold">{r.symbol || "-"}</span>
    case "name":
      return <span className="truncate max-w-[180px] block">{r.name || r.symbol || "-"}</span>
    case "pe":
      if (r.pe_nm) return "n.m."
      if (r.pe != null) return fmtDec(r.pe, 2)
      return "-"
    case "pbv":
      if (r.pbv != null) return fmtDec(r.pbv, 2)
      return "-"
    case "ev_ebitda":
      if (r.ev_ebitda_nm) return "n.m."
      if (r.ev_ebitda != null) return fmtDec(r.ev_ebitda, 2)
      return "-"
    case "roe":
      if (r.roe != null) return fmtDec(r.roe * 100, 1)
      return "-"
    case "market_cap":
      if (r.market_cap != null) return `${fmtDec(r.market_cap / 1e12, 2)} tn`
      return "-"
    case "other": {
      const raw = (r as Record<string, unknown>)[col]
      if (typeof raw === "number") return fmtDec(raw, 2)
      if (raw != null) return String(raw)
      return "-"
    }
  }
}

function renderPeerStatCell(
  stat: PeerStat | undefined,
  col: string,
  idx: number,
  isMedian: boolean,
  counts?: { pe_ttm?: number }
): React.ReactNode {
  const type = getPeerColumnType(col, idx)
  switch (type) {
    case "symbol":
      return stat?.symbol || (isMedian ? "Median" : "Rata-rata")
    case "name":
      return isMedian
        ? counts?.pe_ttm != null
          ? `Kelompok peer (${counts.pe_ttm} nama valid)`
          : "Kelompok peer"
        : "Kelompok peer"
    case "pe":
      if (stat?.pe != null) return fmtDec(stat.pe, 2)
      return "-"
    case "pbv":
      if (stat?.pbv != null) return fmtDec(stat.pbv, 2)
      return "-"
    case "ev_ebitda":
      if (stat?.ev_ebitda != null) return fmtDec(stat.ev_ebitda, 2)
      return "-"
    case "roe":
      if (stat?.roe != null) return fmtDec(stat.roe * 100, 1)
      return "-"
    case "market_cap":
      return "-"
    case "other":
      return "-"
  }
}

function PendingCard({ label }: { label: string }) {
  return (
    <div className="rounded-xl border border-[#D9D9D9] bg-white p-6 text-center text-xs text-[#666666] dark:border-[#262930] dark:bg-[#090a0c] dark:text-[#666666]">
      {label} belum tersedia di payload.
    </div>
  )
}

export function ValuationMethodology({ ticker, payload }: ValuationMethodologyProps) {
  const tk = ticker.toUpperCase()
  const valPage: ValuationPage | undefined = payload?.valuation_page
  const peersPage: PeersPage | undefined = payload?.peers_page
  const partA = peersPage?.part_a
  const partB = peersPage?.part_b
  const br = valPage?.bridge
  const sens = valPage?.sensitivity
  const priceNow = payload?.cover?.rating_box?.price || valPage?.drivers?.price

  const hasValuation = valPage && valPage.available !== false

  return (
    <div className="space-y-8">
      {/* ========================================================================= */}
      {/* SECTION 4: VALUATION SPREAD (DCF)                                         */}
      {/* ========================================================================= */}
      <section id="valuation-spread" className="scroll-mt-28 space-y-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#D9D9D9] pb-2 dark:border-[#262930]">
          <h2 className="font-serif text-xl font-medium tracking-tight text-[#333333] dark:text-[#f1f5f9]">
            Nilai wajar dan sensitivitas DCF
          </h2>
          <span className="text-xs text-[#666666] dark:text-[#666666]">
            Model DCF FCFF
          </span>
        </div>

        {hasValuation ? (
          <div className="space-y-4">
            {valPage.subtitle && (
              <p className="text-sm text-[#666666] leading-relaxed dark:text-[#666666]">
                {valPage.subtitle}
              </p>
            )}

            {/* Lane B Chart: DcfSpreadCharts */}
            {payload && <DcfSpreadCharts payload={payload} />}

            {/* Three Block Tables */}
            <Card className="rounded-xl border border-[#D9D9D9] bg-white dark:border-[#262930] dark:bg-[#090a0c]">
              <CardHeader className="border-b border-[#D9D9D9] p-5 pb-3 dark:border-[#262930]">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-semibold text-[#333333] dark:text-[#f1f5f9]">
                    {valPage.exhibit8_title || "Proyeksi FCFF, nilai terminal dan jembatan ekuitas"}
                  </CardTitle>
                  <span className="text-xs text-[#666666] dark:text-[#666666]">
                    {valPage.sources?.[2] || valPage.sources?.[0] || "Model FCFF deterministik"}
                  </span>
                </div>
              </CardHeader>
              <CardContent className="p-5 space-y-5">
                {/* Blok 1: Periode Proyeksi Eksplisit */}
                {valPage.block1_rows && valPage.block1_rows.length > 0 && (
                  <div className="space-y-1.5">
                    <div className="text-xs font-semibold text-[#333333] dark:text-[#f1f5f9]">
                      Periode proyeksi eksplisit (Rp bn)
                    </div>
                    <div className="overflow-x-auto rounded-lg border border-[#D9D9D9] dark:border-[#262930]">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="border-b border-[#D9D9D9] bg-[#f1f5f9] text-right text-[#666666] dark:border-[#262930] dark:bg-[#1e2229] dark:text-[#666666]">
                            {(
                              valPage.block1_headers || [
                                "Pos arus kas",
                                ...(valPage.periods || []),
                              ]
                            ).map((h, idx) => (
                              <th key={idx} className={`py-2.5 px-3 font-semibold ${idx === 0 ? "text-left text-[#333333] dark:text-[#f1f5f9]" : ""}`}>
                                {h}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#D9D9D9]/60 dark:divide-[#262930]/60">
                          {valPage.block1_rows.map(([label, series], rIdx) => {
                            const isBold =
                              label === "FCFF (build-up)" ||
                              label === "PV of FCFF" ||
                              label.includes("FCFF growth");
                            return (
                              <tr
                                key={rIdx}
                                className={`${
                                  rIdx % 2 === 1 ? "bg-[#f1f5f9]/50 dark:bg-[#1e2229]/30" : "bg-white dark:bg-[#090a0c]"
                                } ${isBold ? "font-semibold text-[#333333] dark:text-[#f1f5f9]" : "text-[#333333] dark:text-[#f1f5f9]/90"}`}
                              >
                                <td className="py-2 px-3 text-left font-sans">{label}</td>
                                {Array.isArray(series) ? (
                                  series.map((val, cIdx) => (
                                    <td key={cIdx} className="py-2 px-3 text-right font-mono tabular-nums">
                                      {val != null ? String(val) : "-"}
                                    </td>
                                  ))
                                ) : (
                                  <td className="py-2 px-3 text-right font-mono tabular-nums">{String(series)}</td>
                                )}
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Blok 2: Terminal Value */}
                {valPage.block2_rows && valPage.block2_rows.length > 0 && (
                  <div className="space-y-1.5">
                    <div className="text-xs font-semibold text-[#333333] dark:text-[#f1f5f9]">
                      Nilai terminal (Terminal value)
                    </div>
                    <div className="overflow-x-auto rounded-lg border border-[#D9D9D9] dark:border-[#262930]">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="border-b border-[#D9D9D9] bg-[#f1f5f9] text-right text-[#666666] dark:border-[#262930] dark:bg-[#1e2229] dark:text-[#666666]">
                            {(
                              valPage.block2_headers || [
                                "Komponen",
                                "Gordon Growth",
                                `Exit Multiple ${valPage.drivers?.multiple != null ? valPage.drivers.multiple.toFixed(1) : ""}×`,
                              ]
                            ).map((h, idx) => (
                              <th key={idx} className={`py-2.5 px-3 font-semibold ${idx === 0 ? "text-left text-[#333333] dark:text-[#f1f5f9]" : ""}`}>
                                {h}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#D9D9D9]/60 dark:divide-[#262930]/60">
                          {valPage.block2_rows.map(([label, a, b], rIdx) => {
                            const isBold = label.includes("PV of Terminal") || label.includes("Terminal Value");
                            return (
                              <tr
                                key={rIdx}
                                className={`${
                                  rIdx % 2 === 1 ? "bg-[#f1f5f9]/50 dark:bg-[#1e2229]/30" : "bg-white dark:bg-[#090a0c]"
                                } ${isBold ? "font-semibold text-[#333333] dark:text-[#f1f5f9]" : "text-[#333333] dark:text-[#f1f5f9]/90"}`}
                              >
                                <td className="py-2 px-3 text-left font-sans">{label}</td>
                                <td className="py-2 px-3 text-right font-mono tabular-nums">{a != null ? String(a) : "-"}</td>
                                <td className="py-2 px-3 text-right font-mono tabular-nums">{b != null ? String(b) : "-"}</td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Blok 3: Bridge ke Equity Value */}
                {valPage.block3_rows && valPage.block3_rows.length > 0 && (
                  <div className="space-y-1.5">
                    <div className="text-xs font-semibold text-[#333333] dark:text-[#f1f5f9]">
                      Jembatan ke nilai ekuitas (Equity value)
                    </div>
                    <div className="overflow-x-auto rounded-lg border border-[#D9D9D9] dark:border-[#262930]">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="border-b border-[#D9D9D9] bg-[#f1f5f9] text-right text-[#666666] dark:border-[#262930] dark:bg-[#1e2229] dark:text-[#666666]">
                            {(
                              valPage.block3_headers || [
                                "Komponen jembatan",
                                "Rp bn",
                                "Per saham (Rp)",
                              ]
                            ).map((h, idx) => (
                              <th key={idx} className={`py-2.5 px-3 font-semibold ${idx === 0 ? "text-left text-[#333333] dark:text-[#f1f5f9]" : ""}`}>
                                {h}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#D9D9D9]/60 dark:divide-[#262930]/60">
                          {valPage.block3_rows.map(([label, a, b], rIdx) => {
                            const isFv = label.includes("Fair Value");
                            const isBold = isFv || label.includes("Enterprise Value") || label.includes("Equity Value");
                            return (
                              <tr
                                key={rIdx}
                                className={`${
                                  isFv
                                    ? "bg-[#0928B1]/10 font-semibold text-[#0928B1] dark:bg-[#7596FF]/15 dark:text-[#7596FF]"
                                    : isBold
                                    ? "font-semibold text-[#333333] dark:text-[#f1f5f9]"
                                    : "text-[#333333] dark:text-[#f1f5f9]/90"
                                }`}
                              >
                                <td className="py-2 px-3 text-left font-sans">{label}</td>
                                <td className="py-2 px-3 text-right font-mono tabular-nums">
                                  {typeof a === "number" ? fmtDec(a, 2) : a != null ? String(a) : "-"}
                                </td>
                                <td className="py-2 px-3 text-right font-mono tabular-nums">
                                  {typeof b === "number" ? fmtIDR(b) : b != null ? String(b) : "-"}
                                </td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* WACC Components */}
            {valPage.wacc_rows && valPage.wacc_rows.length > 0 && (
              <Card className="rounded-xl border border-[#D9D9D9] bg-white dark:border-[#262930] dark:bg-[#090a0c]">
                <CardHeader className="border-b border-[#D9D9D9] p-5 pb-3 dark:border-[#262930]">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-semibold text-[#333333] dark:text-[#f1f5f9]">
                      Komponen WACC
                    </CardTitle>
                    <span className="text-xs text-[#666666] dark:text-[#666666]">
                      Sumber per komponen
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="p-5 space-y-2">
                  <div className="overflow-x-auto rounded-lg border border-[#D9D9D9] dark:border-[#262930]">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-[#D9D9D9] bg-[#f1f5f9] text-[#666666] dark:border-[#262930] dark:bg-[#1e2229] dark:text-[#666666]">
                          <th className="py-2.5 px-3 text-left font-semibold text-[#333333] dark:text-[#f1f5f9]">Parameter</th>
                          <th className="py-2.5 px-3 text-right font-semibold">Nilai</th>
                          <th className="py-2.5 px-3 text-left font-semibold">Sumber data</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#D9D9D9]/60 dark:divide-[#262930]/60">
                        {valPage.wacc_rows.map((row, idx) => (
                          <tr
                            key={idx}
                            className={`${
                              idx % 2 === 1 ? "bg-[#f1f5f9]/50 dark:bg-[#1e2229]/30" : "bg-white dark:bg-[#090a0c]"
                            }`}
                          >
                            <td className="py-2 px-3 text-left font-medium text-[#333333] dark:text-[#f1f5f9]">{row[0]}</td>
                            <td className="py-2 px-3 text-right font-medium text-[#333333] font-mono tabular-nums dark:text-[#f1f5f9]">
                              {row[1]}
                            </td>
                            <td className="py-2 px-3 text-left text-xs text-[#666666] dark:text-[#666666]">{row[2]}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Sensitivity Analysis Matrix */}
            {sens && sens.columns && sens.rows && (
              <Card className="rounded-xl border border-[#D9D9D9] bg-white dark:border-[#262930] dark:bg-[#090a0c]">
                <CardHeader className="border-b border-[#D9D9D9] p-5 pb-3 dark:border-[#262930]">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-semibold text-[#333333] dark:text-[#f1f5f9]">
                      Matriks sensitivitas - WACC × Pertumbuhan terminal
                    </CardTitle>
                    <span className="text-xs text-[#666666] dark:text-[#666666]">
                      Kasus dasar (WACC {sens.base_wacc} · g {sens.base_g})
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="p-5 space-y-3">
                  <div className="overflow-x-auto rounded-lg border border-[#D9D9D9] dark:border-[#262930]">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-[#D9D9D9] bg-[#f1f5f9] text-[#666666] dark:border-[#262930] dark:bg-[#1e2229] dark:text-[#666666]">
                          <th className="py-2.5 px-3 text-left font-semibold text-[#333333] dark:text-[#f1f5f9]">WACC \ g</th>
                          {sens.columns.map((col, idx) => (
                            <th key={idx} className="py-2.5 px-3 text-right font-semibold">
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#D9D9D9]/60 dark:divide-[#262930]/60">
                        {sens.rows.map((r, rIdx) => (
                          <tr key={rIdx}>
                            <td className="py-2 px-3 font-semibold text-[#333333] bg-[#f1f5f9]/70 dark:bg-[#1e2229]/50 dark:text-[#f1f5f9]">
                              {r.label}
                            </td>
                            {r.cells.map((c, cIdx) => (
                              <td
                                key={cIdx}
                                className={`py-2 px-3 text-right font-mono tabular-nums ${getSensitivityBandStyle(
                                  c.band
                                )} ${
                                  c.base
                                    ? "font-bold ring-[1.5px] ring-inset ring-[#333333] dark:ring-[#f1f5f9]"
                                    : ""
                                }`}
                              >
                                {c.value != null ? (typeof c.value === "number" ? fmtIDR(c.value) : String(c.value)) : "-"}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Heatmap Legend */}
                  <div className="mt-3.5 flex flex-wrap items-center gap-3 text-xs text-[#666666] dark:text-[#666666]">
                    <span className="font-medium text-[#333333] dark:text-[#f1f5f9]">Keterangan sel:</span>
                    <span className="flex items-center gap-1.5">
                      <span className="inline-block h-3 w-3.5 rounded-xs bg-[#F7E1D7] border border-[#E8C5B8] dark:bg-[#4A261D] dark:border-[#5C3025]" /> Rendah
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="inline-block h-3 w-3.5 rounded-xs bg-[#FAF7F0] border border-[#E5DFD3] dark:bg-[#26282B] dark:border-[#383B40]" /> Netral
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="inline-block h-3 w-3.5 rounded-xs bg-[#DCE8E0] border border-[#BFD5C6] dark:bg-[#2D4536] dark:border-[#3D5C49]" /> Tinggi
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="inline-block h-3 w-3.5 rounded-xs border-[1.5px] border-[#333333] dark:border-[#f1f5f9]" /> Kasus dasar
                    </span>
                  </div>

                  {sens.swing && (
                    <p className="text-xs text-[#666666] leading-relaxed dark:text-[#666666]">
                      Dasar Rp {fmtIDR(sens.base_fv)} (WACC {sens.base_wacc} · g {sens.base_g}). Rentang nilai: Rp{" "}
                      {fmtIDR(sens.swing.min)} – Rp {fmtIDR(sens.swing.max)}.
                    </p>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Metode Pembanding */}
            {valPage.crosscheck_rows && valPage.crosscheck_rows.length > 0 && (
              <Card className="rounded-xl border border-[#D9D9D9] bg-white dark:border-[#262930] dark:bg-[#090a0c]">
                <CardHeader className="border-b border-[#D9D9D9] p-5 pb-3 dark:border-[#262930]">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-semibold text-[#333333] dark:text-[#f1f5f9]">
                      Metode pembanding nilai wajar
                    </CardTitle>
                    <span className="text-xs text-[#666666] dark:text-[#666666]">
                      Uji silang kelipatan valuasi
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="p-5 space-y-2">
                  <div className="overflow-x-auto rounded-lg border border-[#D9D9D9] dark:border-[#262930]">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-[#D9D9D9] bg-[#f1f5f9] text-[#666666] dark:border-[#262930] dark:bg-[#1e2229] dark:text-[#666666]">
                          <th className="py-2.5 px-3 text-left font-semibold text-[#333333] dark:text-[#f1f5f9]">Metode</th>
                          <th className="py-2.5 px-3 text-right font-semibold">Nilai wajar (Rp)</th>
                          <th className="py-2.5 px-3 text-left font-semibold">Peran</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#D9D9D9]/60 dark:divide-[#262930]/60">
                        {valPage.crosscheck_rows.map((row, idx) => (
                          <tr
                            key={idx}
                            className={`${
                              idx % 2 === 1 ? "bg-[#f1f5f9]/50 dark:bg-[#1e2229]/30" : "bg-white dark:bg-[#090a0c]"
                            }`}
                          >
                            <td className="py-2 px-3 font-medium text-[#333333] dark:text-[#f1f5f9]">{row[0]}</td>
                            <td className="py-2 px-3 text-right font-medium text-[#333333] font-mono tabular-nums dark:text-[#f1f5f9]">
                              {typeof row[1] === "number" ? `Rp ${fmtIDR(row[1])}` : String(row[1])}
                            </td>
                            <td className="py-2 px-3 text-xs text-[#666666] dark:text-[#666666]">{row[2]}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        ) : (
          <PendingCard label="Halaman valuasi" />
        )}
      </section>

      {/* ========================================================================= */}
      {/* SECTION 5: PEERS 5A - CROSS-SECTIONAL VALUATION                           */}
      {/* ========================================================================= */}
      <section id="peers-5a" className="scroll-mt-28 space-y-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#D9D9D9] pb-2 dark:border-[#262930]">
          <h2 className="font-serif text-xl font-medium tracking-tight text-[#333333] dark:text-[#f1f5f9]">
            Valuasi komparasi peer (Cross-sectional)
          </h2>
          <span className="text-xs text-[#666666] dark:text-[#666666]">
            Komparasi satu tanggal
          </span>
        </div>

        {partA && partA.rows && partA.rows.length > 0 ? (
          <Card className="rounded-xl border border-[#D9D9D9] bg-white dark:border-[#262930] dark:bg-[#090a0c]">
            <CardHeader className="border-b border-[#D9D9D9] p-5 pb-3 dark:border-[#262930]">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-semibold text-[#333333] dark:text-[#f1f5f9]">
                  {partA.title || "Valuasi komparasi peer"}
                </CardTitle>
                <span className="text-xs text-[#666666] dark:text-[#666666]">
                  {partA.sources?.[0] || "Sectors API"}
                </span>
              </div>
              <CardDescription className="text-xs text-[#666666] mt-1 dark:text-[#666666]">
                Membandingkan posisi kelipatan emiten dengan kelompok sejenis pada tanggal harga acuan.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5 space-y-4">
              <div className="overflow-x-auto rounded-lg border border-[#D9D9D9] dark:border-[#262930]">
                {(() => {
                  const columns =
                    partA.columns && partA.columns.length > 0
                      ? partA.columns
                      : ["Ticker", "Perusahaan", "P/E (x)", "P/BV (x)", "EV/EBITDA (x)", "ROE (%)", "Market Cap"]

                  return (
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-[#D9D9D9] bg-[#f1f5f9] text-[#666666] dark:border-[#262930] dark:bg-[#1e2229] dark:text-[#666666]">
                          {columns.map((col, idx) => {
                            const type = getPeerColumnType(col, idx)
                            const isLeft = type === "symbol" || type === "name"
                            return (
                              <th key={idx} className={`py-2.5 px-3 font-semibold ${isLeft ? "text-left text-[#333333] dark:text-[#f1f5f9]" : "text-right"}`}>
                                {col}
                              </th>
                            )
                          })}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#D9D9D9]/60 dark:divide-[#262930]/60">
                        {partA.rows.map((r, idx) => {
                          const isCovered = Boolean(r.is_covered)
                          return (
                            <tr
                              key={idx}
                              className={`${
                                isCovered
                                  ? "bg-[#0928B1]/10 font-semibold text-[#0928B1] dark:bg-[#7596FF]/15 dark:text-[#7596FF]"
                                  : idx % 2 === 1
                                  ? "bg-[#f1f5f9]/50 dark:bg-[#1e2229]/30"
                                  : "bg-white dark:bg-[#090a0c]"
                              }`}
                            >
                              {columns.map((col, cIdx) => {
                                const type = getPeerColumnType(col, cIdx)
                                const isLeft = type === "symbol" || type === "name"
                                return (
                                  <td
                                    key={cIdx}
                                    className={`py-2 px-3 ${isLeft ? "text-left font-sans" : "text-right font-mono tabular-nums"}`}
                                  >
                                    {renderPeerCell(r, col, cIdx)}
                                  </td>
                                )
                              })}
                            </tr>
                          )
                        })}
                      </tbody>
                      <tfoot>
                        {partA.median && (
                          <tr className="border-t-2 border-[#D9D9D9] bg-[#f1f5f9] font-semibold text-[#333333] dark:border-[#262930] dark:bg-[#1e2229] dark:text-[#f1f5f9]">
                            {columns.map((col, cIdx) => {
                              const type = getPeerColumnType(col, cIdx)
                              const isLeft = type === "symbol" || type === "name"
                              return (
                                <td
                                  key={cIdx}
                                  className={`py-2 px-3 ${
                                    isLeft ? "text-left font-sans" : "text-right font-mono tabular-nums"
                                  }`}
                                >
                                  {renderPeerStatCell(partA.median, col, cIdx, true, partA.counts)}
                                </td>
                              )
                            })}
                          </tr>
                        )}
                        {partA.average && (
                          <tr className="border-t border-[#D9D9D9] bg-[#f1f5f9] font-semibold text-[#333333] dark:border-[#262930] dark:bg-[#1e2229] dark:text-[#f1f5f9]">
                            {columns.map((col, cIdx) => {
                              const type = getPeerColumnType(col, cIdx)
                              const isLeft = type === "symbol" || type === "name"
                              return (
                                <td
                                  key={cIdx}
                                  className={`py-2 px-3 ${
                                    isLeft ? "text-left font-sans" : "text-right font-mono tabular-nums"
                                  }`}
                                >
                                  {renderPeerStatCell(partA.average, col, cIdx, false, partA.counts)}
                                </td>
                              )
                            })}
                          </tr>
                        )}
                      </tfoot>
                    </table>
                  )
                })()}
              </div>

              {(partA.criteria || partA.basis) && (
                <div className="text-xs text-[#666666] dark:text-[#666666]">
                  {partA.criteria ? `${partA.criteria} ` : ""}
                  {partA.basis ? `Basis: ${partA.basis}. ` : ""}
                  Baris berarsir menandai emiten yang dianalisis.
                </div>
              )}
              {partA.narrative_text && (
                <p className="text-sm leading-relaxed text-[#333333] dark:text-[#f1f5f9]/90">
                  {partA.narrative_text}
                </p>
              )}
              {!partA.narrative_text && partA.narrative && partA.narrative.length > 0 && (
                <div className="space-y-2 text-sm leading-relaxed text-[#333333] dark:text-[#f1f5f9]/90">
                  {partA.narrative.map((p, idx) => (
                    <p key={idx}>{p}</p>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        ) : (
          <PendingCard label="Valuasi peer komparasi" />
        )}
      </section>

      {/* ========================================================================= */}
      {/* SECTION 6: OWN HISTORY 5B - RELATIVE VALUATION                            */}
      {/* ========================================================================= */}
      <section id="peers-5b" className="scroll-mt-28 space-y-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#D9D9D9] pb-2 dark:border-[#262930]">
          <h2 className="font-serif text-xl font-medium tracking-tight text-[#333333] dark:text-[#f1f5f9]">
            Valuasi relatif historis (Own history)
          </h2>
          <span className="text-xs text-[#666666] dark:text-[#666666]">
            Rentang kelipatan waktu
          </span>
        </div>

        {partB ? (
          <div className="space-y-4">
            {partB.methodology && (
              <p className="text-sm text-[#666666] leading-relaxed dark:text-[#666666]">
                {partB.methodology}
              </p>
            )}

            {/* Lane B Chart: PeersCharts */}
            {payload && <PeersCharts payload={payload} />}

            {/* Implied Price Judgement Table */}
            {partB.implied && partB.implied.length > 0 && (
              <Card className="rounded-xl border border-[#D9D9D9] bg-white dark:border-[#262930] dark:bg-[#090a0c]">
                <CardHeader className="border-b border-[#D9D9D9] p-5 pb-3 dark:border-[#262930]">
                  <CardTitle className="text-sm font-semibold text-[#333333] dark:text-[#f1f5f9]">
                    Penilaian harga implisit (Implied price)
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-5 space-y-3">
                  <div className="overflow-x-auto rounded-lg border border-[#D9D9D9] dark:border-[#262930]">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-[#D9D9D9] bg-[#f1f5f9] text-[#666666] dark:border-[#262930] dark:bg-[#1e2229] dark:text-[#666666]">
                          <th className="py-2.5 px-3 text-left font-semibold text-[#333333] dark:text-[#f1f5f9]">Kelipatan</th>
                          <th className="py-2.5 px-3 text-right font-semibold">Kembali ke rata-rata (Rp)</th>
                          <th className="py-2.5 px-3 text-right font-semibold">Kembali ke median (Rp)</th>
                          <th className="py-2.5 px-3 text-right font-semibold">Rentang</th>
                          <th className="py-2.5 px-3 text-right font-semibold">Selisih</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#D9D9D9]/60 dark:divide-[#262930]/60">
                        {partB.implied.map((r, idx) => (
                          <tr
                            key={idx}
                            className={`${
                              idx % 2 === 1 ? "bg-[#f1f5f9]/50 dark:bg-[#1e2229]/30" : "bg-white dark:bg-[#090a0c]"
                            }`}
                          >
                            <td className="py-2 px-3 font-semibold text-[#333333] dark:text-[#f1f5f9]">{r.label}</td>
                            <td className="py-2 px-3 text-right font-medium text-[#333333] font-mono tabular-nums dark:text-[#f1f5f9]">
                              Rp {fmtIDR(r.to_mean)}
                            </td>
                            <td className="py-2 px-3 text-right font-medium text-[#333333] font-mono tabular-nums dark:text-[#f1f5f9]">
                              Rp {fmtIDR(r.to_median)}
                            </td>
                            <td className="py-2 px-3 text-right font-mono tabular-nums text-[#666666] dark:text-[#666666]">
                              {r.is_range && r.low != null && r.high != null
                                ? `Rp ${fmtIDR(r.low)} – ${fmtIDR(r.high)}`
                                : "konvergen"}
                            </td>
                            <td className="py-2 px-3 text-right font-semibold font-mono tabular-nums text-[#333333] dark:text-[#f1f5f9]">
                              {r.delta_pct != null ? `${r.delta_pct.toFixed(0)}%` : "-"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="text-xs text-[#666666] dark:text-[#666666]">
                    Harga acuan terakhir: {partB.last_close != null ? `Rp ${fmtIDR(partB.last_close)}` : "-"} ·{" "}
                    {partB.driver_note}
                  </div>

                  {partB.disclaimer && (
                    <div className="rounded-lg border border-[#D9D9D9] bg-[#f1f5f9] p-3 text-xs text-[#333333] dark:border-[#262930] dark:bg-[#1e2229] dark:text-[#f1f5f9]">
                      <strong>Catatan:</strong> {partB.disclaimer}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        ) : (
          <PendingCard label="Valuasi relatif historis" />
        )}
      </section>
    </div>
  )
}
