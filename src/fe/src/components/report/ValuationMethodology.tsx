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
    <div className="rounded-xl border border-[#E7E3DA] bg-white p-6 text-center text-xs text-[#6B6659] dark:border-[#2A2822] dark:bg-[#1B1A16] dark:text-[#A8A296]">
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
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#E7E3DA] pb-2 dark:border-[#2A2822]">
          <h2 className="font-serif text-xl font-medium tracking-tight text-[#1C1B17] dark:text-[#EDEAE3]">
            Nilai wajar dan sensitivitas DCF
          </h2>
          <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
            Model DCF FCFF
          </span>
        </div>

        {hasValuation ? (
          <div className="space-y-4">
            {valPage.subtitle && (
              <p className="text-sm text-[#6B6659] leading-relaxed dark:text-[#A8A296]">
                {valPage.subtitle}
              </p>
            )}

            {/* Lane B Chart: DcfSpreadCharts */}
            {payload && <DcfSpreadCharts payload={payload} />}

            {/* Three Block Tables */}
            <Card className="rounded-xl border border-[#E7E3DA] bg-white dark:border-[#2A2822] dark:bg-[#1B1A16]">
              <CardHeader className="border-b border-[#E7E3DA] p-5 pb-3 dark:border-[#2A2822]">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                    {valPage.exhibit8_title || "Proyeksi FCFF, nilai terminal dan jembatan ekuitas"}
                  </CardTitle>
                  <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
                    {valPage.sources?.[2] || valPage.sources?.[0] || "Model FCFF deterministik"}
                  </span>
                </div>
              </CardHeader>
              <CardContent className="p-5 space-y-5">
                {/* Blok 1: Periode Proyeksi Eksplisit */}
                {valPage.block1_rows && valPage.block1_rows.length > 0 && (
                  <div className="space-y-1.5">
                    <div className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                      Periode proyeksi eksplisit (Rp bn)
                    </div>
                    <div className="overflow-x-auto rounded-lg border border-[#E7E3DA] dark:border-[#2A2822]">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="border-b border-[#E7E3DA] bg-[#FBFAF7] text-right text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
                            {(
                              valPage.block1_headers || [
                                "Pos arus kas",
                                ...(valPage.periods || []),
                              ]
                            ).map((h, idx) => (
                              <th key={idx} className={`py-2.5 px-3 font-semibold ${idx === 0 ? "text-left text-[#1C1B17] dark:text-[#EDEAE3]" : ""}`}>
                                {h}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#E7E3DA]/60 dark:divide-[#2A2822]/60">
                          {valPage.block1_rows.map(([label, series], rIdx) => {
                            const isBold =
                              label === "FCFF (build-up)" ||
                              label === "PV of FCFF" ||
                              label.includes("FCFF growth");
                            return (
                              <tr
                                key={rIdx}
                                className={`${
                                  rIdx % 2 === 1 ? "bg-[#FBFAF7]/50 dark:bg-[#14130F]/30" : "bg-white dark:bg-[#1B1A16]"
                                } ${isBold ? "font-semibold text-[#1C1B17] dark:text-[#EDEAE3]" : "text-[#1C1B17] dark:text-[#EDEAE3]/90"}`}
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
                    <div className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                      Nilai terminal (Terminal value)
                    </div>
                    <div className="overflow-x-auto rounded-lg border border-[#E7E3DA] dark:border-[#2A2822]">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="border-b border-[#E7E3DA] bg-[#FBFAF7] text-right text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
                            {(
                              valPage.block2_headers || [
                                "Komponen",
                                "Gordon Growth",
                                `Exit Multiple ${valPage.drivers?.multiple != null ? valPage.drivers.multiple.toFixed(1) : ""}×`,
                              ]
                            ).map((h, idx) => (
                              <th key={idx} className={`py-2.5 px-3 font-semibold ${idx === 0 ? "text-left text-[#1C1B17] dark:text-[#EDEAE3]" : ""}`}>
                                {h}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#E7E3DA]/60 dark:divide-[#2A2822]/60">
                          {valPage.block2_rows.map(([label, a, b], rIdx) => {
                            const isBold = label.includes("PV of Terminal") || label.includes("Terminal Value");
                            return (
                              <tr
                                key={rIdx}
                                className={`${
                                  rIdx % 2 === 1 ? "bg-[#FBFAF7]/50 dark:bg-[#14130F]/30" : "bg-white dark:bg-[#1B1A16]"
                                } ${isBold ? "font-semibold text-[#1C1B17] dark:text-[#EDEAE3]" : "text-[#1C1B17] dark:text-[#EDEAE3]/90"}`}
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
                    <div className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                      Jembatan ke nilai ekuitas (Equity value)
                    </div>
                    <div className="overflow-x-auto rounded-lg border border-[#E7E3DA] dark:border-[#2A2822]">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="border-b border-[#E7E3DA] bg-[#FBFAF7] text-right text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
                            {(
                              valPage.block3_headers || [
                                "Komponen jembatan",
                                "Rp bn",
                                "Per saham (Rp)",
                              ]
                            ).map((h, idx) => (
                              <th key={idx} className={`py-2.5 px-3 font-semibold ${idx === 0 ? "text-left text-[#1C1B17] dark:text-[#EDEAE3]" : ""}`}>
                                {h}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#E7E3DA]/60 dark:divide-[#2A2822]/60">
                          {valPage.block3_rows.map(([label, a, b], rIdx) => {
                            const isFv = label.includes("Fair Value");
                            const isBold = isFv || label.includes("Enterprise Value") || label.includes("Equity Value");
                            return (
                              <tr
                                key={rIdx}
                                className={`${
                                  isFv
                                    ? "bg-[#0E6E63]/10 font-semibold text-[#0E6E63] dark:bg-[#4FD1B5]/15 dark:text-[#4FD1B5]"
                                    : isBold
                                    ? "font-semibold text-[#1C1B17] dark:text-[#EDEAE3]"
                                    : "text-[#1C1B17] dark:text-[#EDEAE3]/90"
                                }`}
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
              </CardContent>
            </Card>

            {/* WACC Components */}
            {valPage.wacc_rows && valPage.wacc_rows.length > 0 && (
              <Card className="rounded-xl border border-[#E7E3DA] bg-white dark:border-[#2A2822] dark:bg-[#1B1A16]">
                <CardHeader className="border-b border-[#E7E3DA] p-5 pb-3 dark:border-[#2A2822]">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                      Komponen WACC
                    </CardTitle>
                    <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
                      Sumber per komponen
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="p-5 space-y-2">
                  <div className="overflow-x-auto rounded-lg border border-[#E7E3DA] dark:border-[#2A2822]">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-[#E7E3DA] bg-[#FBFAF7] text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
                          <th className="py-2.5 px-3 text-left font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">Parameter</th>
                          <th className="py-2.5 px-3 text-right font-semibold">Nilai</th>
                          <th className="py-2.5 px-3 text-left font-semibold">Sumber data</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E7E3DA]/60 dark:divide-[#2A2822]/60">
                        {valPage.wacc_rows.map((row, idx) => (
                          <tr
                            key={idx}
                            className={`${
                              idx % 2 === 1 ? "bg-[#FBFAF7]/50 dark:bg-[#14130F]/30" : "bg-white dark:bg-[#1B1A16]"
                            }`}
                          >
                            <td className="py-2 px-3 text-left font-medium text-[#1C1B17] dark:text-[#EDEAE3]">{row[0]}</td>
                            <td className="py-2 px-3 text-right font-medium text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
                              {row[1]}
                            </td>
                            <td className="py-2 px-3 text-left text-xs text-[#6B6659] dark:text-[#A8A296]">{row[2]}</td>
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
              <Card className="rounded-xl border border-[#E7E3DA] bg-white dark:border-[#2A2822] dark:bg-[#1B1A16]">
                <CardHeader className="border-b border-[#E7E3DA] p-5 pb-3 dark:border-[#2A2822]">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                      Matriks sensitivitas - WACC × Pertumbuhan terminal
                    </CardTitle>
                    <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
                      Kasus dasar (WACC {sens.base_wacc} · g {sens.base_g})
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="p-5 space-y-3">
                  <div className="overflow-x-auto rounded-lg border border-[#E7E3DA] dark:border-[#2A2822]">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-[#E7E3DA] bg-[#FBFAF7] text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
                          <th className="py-2.5 px-3 text-left font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">WACC \ g</th>
                          {sens.columns.map((col, idx) => (
                            <th key={idx} className="py-2.5 px-3 text-right font-semibold">
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E7E3DA]/60 dark:divide-[#2A2822]/60">
                        {sens.rows.map((r, rIdx) => (
                          <tr key={rIdx}>
                            <td className="py-2 px-3 font-semibold text-[#1C1B17] bg-[#FBFAF7]/70 dark:bg-[#14130F]/50 dark:text-[#EDEAE3]">
                              {r.label}
                            </td>
                            {r.cells.map((c, cIdx) => (
                              <td
                                key={cIdx}
                                className={`py-2 px-3 text-right font-mono tabular-nums ${
                                  c.base
                                    ? "font-bold text-[#0E6E63] bg-[#0E6E63]/10 ring-1 ring-inset ring-[#0E6E63] dark:bg-[#4FD1B5]/20 dark:text-[#4FD1B5]"
                                    : "text-[#1C1B17] dark:text-[#EDEAE3]/90"
                                }`}
                              >
                                {c.value != null ? String(c.value) : "-"}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {sens.swing && (
                    <p className="text-xs text-[#6B6659] leading-relaxed dark:text-[#A8A296]">
                      Dasar Rp {fmtIDR(sens.base_fv)} (WACC {sens.base_wacc} · g {sens.base_g}). Rentang nilai: Rp{" "}
                      {fmtIDR(sens.swing.min)} – Rp {fmtIDR(sens.swing.max)}.
                    </p>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Metode Pembanding */}
            {valPage.crosscheck_rows && valPage.crosscheck_rows.length > 0 && (
              <Card className="rounded-xl border border-[#E7E3DA] bg-white dark:border-[#2A2822] dark:bg-[#1B1A16]">
                <CardHeader className="border-b border-[#E7E3DA] p-5 pb-3 dark:border-[#2A2822]">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                      Metode pembanding nilai wajar
                    </CardTitle>
                    <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
                      Uji silang kelipatan valuasi
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="p-5 space-y-2">
                  <div className="overflow-x-auto rounded-lg border border-[#E7E3DA] dark:border-[#2A2822]">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-[#E7E3DA] bg-[#FBFAF7] text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
                          <th className="py-2.5 px-3 text-left font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">Metode</th>
                          <th className="py-2.5 px-3 text-right font-semibold">Nilai wajar (Rp)</th>
                          <th className="py-2.5 px-3 text-left font-semibold">Peran</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E7E3DA]/60 dark:divide-[#2A2822]/60">
                        {valPage.crosscheck_rows.map((row, idx) => (
                          <tr
                            key={idx}
                            className={`${
                              idx % 2 === 1 ? "bg-[#FBFAF7]/50 dark:bg-[#14130F]/30" : "bg-white dark:bg-[#1B1A16]"
                            }`}
                          >
                            <td className="py-2 px-3 font-medium text-[#1C1B17] dark:text-[#EDEAE3]">{row[0]}</td>
                            <td className="py-2 px-3 text-right font-medium text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
                              {typeof row[1] === "number" ? `Rp ${fmtIDR(row[1])}` : String(row[1])}
                            </td>
                            <td className="py-2 px-3 text-xs text-[#6B6659] dark:text-[#A8A296]">{row[2]}</td>
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
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#E7E3DA] pb-2 dark:border-[#2A2822]">
          <h2 className="font-serif text-xl font-medium tracking-tight text-[#1C1B17] dark:text-[#EDEAE3]">
            Valuasi komparasi peer (Cross-sectional)
          </h2>
          <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
            Komparasi satu tanggal
          </span>
        </div>

        {partA && partA.rows && partA.rows.length > 0 ? (
          <Card className="rounded-xl border border-[#E7E3DA] bg-white dark:border-[#2A2822] dark:bg-[#1B1A16]">
            <CardHeader className="border-b border-[#E7E3DA] p-5 pb-3 dark:border-[#2A2822]">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                  {partA.title || "Valuasi komparasi peer"}
                </CardTitle>
                <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
                  {partA.sources?.[0] || "Sectors API"}
                </span>
              </div>
              <CardDescription className="text-xs text-[#6B6659] mt-1 dark:text-[#A8A296]">
                Membandingkan posisi kelipatan emiten dengan kelompok sejenis pada tanggal harga acuan.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5 space-y-4">
              <div className="overflow-x-auto rounded-lg border border-[#E7E3DA] dark:border-[#2A2822]">
                {(() => {
                  const columns =
                    partA.columns && partA.columns.length > 0
                      ? partA.columns
                      : ["Ticker", "Perusahaan", "P/E (x)", "P/BV (x)", "EV/EBITDA (x)", "ROE (%)", "Market Cap"]

                  return (
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-[#E7E3DA] bg-[#FBFAF7] text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
                          {columns.map((col, idx) => {
                            const type = getPeerColumnType(col, idx)
                            const isLeft = type === "symbol" || type === "name"
                            return (
                              <th key={idx} className={`py-2.5 px-3 font-semibold ${isLeft ? "text-left text-[#1C1B17] dark:text-[#EDEAE3]" : "text-right"}`}>
                                {col}
                              </th>
                            )
                          })}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E7E3DA]/60 dark:divide-[#2A2822]/60">
                        {partA.rows.map((r, idx) => {
                          const isCovered = Boolean(r.is_covered)
                          return (
                            <tr
                              key={idx}
                              className={`${
                                isCovered
                                  ? "bg-[#0E6E63]/10 font-semibold text-[#0E6E63] dark:bg-[#4FD1B5]/15 dark:text-[#4FD1B5]"
                                  : idx % 2 === 1
                                  ? "bg-[#FBFAF7]/50 dark:bg-[#14130F]/30"
                                  : "bg-white dark:bg-[#1B1A16]"
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
                          <tr className="border-t-2 border-[#E7E3DA] bg-[#FBFAF7] font-semibold text-[#1C1B17] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#EDEAE3]">
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
                          <tr className="border-t border-[#E7E3DA] bg-[#FBFAF7] font-semibold text-[#1C1B17] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#EDEAE3]">
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
                <div className="text-xs text-[#6B6659] dark:text-[#A8A296]">
                  {partA.criteria ? `${partA.criteria} ` : ""}
                  {partA.basis ? `Basis: ${partA.basis}. ` : ""}
                  Baris berarsir menandai emiten yang dianalisis.
                </div>
              )}
              {partA.narrative_text && (
                <p className="text-sm leading-relaxed text-[#1C1B17] dark:text-[#EDEAE3]/90">
                  {partA.narrative_text}
                </p>
              )}
              {!partA.narrative_text && partA.narrative && partA.narrative.length > 0 && (
                <div className="space-y-2 text-sm leading-relaxed text-[#1C1B17] dark:text-[#EDEAE3]/90">
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
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#E7E3DA] pb-2 dark:border-[#2A2822]">
          <h2 className="font-serif text-xl font-medium tracking-tight text-[#1C1B17] dark:text-[#EDEAE3]">
            Valuasi relatif historis (Own history)
          </h2>
          <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
            Rentang kelipatan waktu
          </span>
        </div>

        {partB ? (
          <div className="space-y-4">
            {partB.methodology && (
              <p className="text-sm text-[#6B6659] leading-relaxed dark:text-[#A8A296]">
                {partB.methodology}
              </p>
            )}

            {/* Lane B Chart: PeersCharts */}
            {payload && <PeersCharts payload={payload} />}

            {/* Implied Price Judgement Table */}
            {partB.implied && partB.implied.length > 0 && (
              <Card className="rounded-xl border border-[#E7E3DA] bg-white dark:border-[#2A2822] dark:bg-[#1B1A16]">
                <CardHeader className="border-b border-[#E7E3DA] p-5 pb-3 dark:border-[#2A2822]">
                  <CardTitle className="text-sm font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                    Penilaian harga implisit (Implied price)
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-5 space-y-3">
                  <div className="overflow-x-auto rounded-lg border border-[#E7E3DA] dark:border-[#2A2822]">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-[#E7E3DA] bg-[#FBFAF7] text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
                          <th className="py-2.5 px-3 text-left font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">Kelipatan</th>
                          <th className="py-2.5 px-3 text-right font-semibold">Kembali ke rata-rata (Rp)</th>
                          <th className="py-2.5 px-3 text-right font-semibold">Kembali ke median (Rp)</th>
                          <th className="py-2.5 px-3 text-right font-semibold">Rentang</th>
                          <th className="py-2.5 px-3 text-right font-semibold">Selisih</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E7E3DA]/60 dark:divide-[#2A2822]/60">
                        {partB.implied.map((r, idx) => (
                          <tr
                            key={idx}
                            className={`${
                              idx % 2 === 1 ? "bg-[#FBFAF7]/50 dark:bg-[#14130F]/30" : "bg-white dark:bg-[#1B1A16]"
                            }`}
                          >
                            <td className="py-2 px-3 font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">{r.label}</td>
                            <td className="py-2 px-3 text-right font-medium text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
                              Rp {fmtIDR(r.to_mean)}
                            </td>
                            <td className="py-2 px-3 text-right font-medium text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
                              Rp {fmtIDR(r.to_median)}
                            </td>
                            <td className="py-2 px-3 text-right font-mono tabular-nums text-[#6B6659] dark:text-[#A8A296]">
                              {r.is_range && r.low != null && r.high != null
                                ? `Rp ${fmtIDR(r.low)} – ${fmtIDR(r.high)}`
                                : "konvergen"}
                            </td>
                            <td className="py-2 px-3 text-right font-semibold font-mono tabular-nums text-[#1C1B17] dark:text-[#EDEAE3]">
                              {r.delta_pct != null ? `${r.delta_pct.toFixed(0)}%` : "-"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="text-xs text-[#6B6659] dark:text-[#A8A296]">
                    Harga acuan terakhir: {partB.last_close != null ? `Rp ${fmtIDR(partB.last_close)}` : "-"} ·{" "}
                    {partB.driver_note}
                  </div>

                  {partB.disclaimer && (
                    <div className="rounded-lg border border-[#E7E3DA] bg-[#FBFAF7] p-3 text-xs text-[#1C1B17] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#EDEAE3]">
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
