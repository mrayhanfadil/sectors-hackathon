import React from "react"
import { Calculator, Layers, TrendingUp, Info, ArrowUpRight, CheckCircle2 } from "lucide-react"
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
      return <span className="font-bold">{r.symbol || "-"}</span>
    case "name":
      return <span className="font-sans truncate max-w-[160px] block">{r.name || r.symbol || "-"}</span>
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
      return stat?.symbol || (isMedian ? "MEDIAN" : "AVERAGE")
    case "name":
      return isMedian
        ? counts?.pe_ttm != null
          ? `Peer set (${counts.pe_ttm} nama ber-P/E valid)`
          : "Peer set"
        : "Peer set"
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
    <div className="rounded-md border border-[#D6E2EE] bg-[#F4F8FC] p-4 text-center font-mono text-xs text-[#63748A] dark:border-[#262930] dark:bg-[#121316]">
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
    <div className="space-y-6">
      {/* ========================================================================= */}
      {/* BAB 4: VALUATION SPREAD (DCF)                                             */}
      {/* ========================================================================= */}
      <section id="valuation-spread" className="scroll-mt-28 space-y-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#D6E2EE] pb-2 dark:border-[#262930]">
          <div className="flex items-center gap-2">
            <span className="rounded bg-[#0B1F3A] px-1.5 py-0.5 font-mono text-[10px] font-bold text-[#E4EEF7] dark:bg-[#0B1F3A] dark:text-[#A9C9E8]">
              04
            </span>
            <h2 className="font-sans text-sm font-bold tracking-tight text-[#0B1F3A] dark:text-neutral-100 uppercase">
              Valuasi Spread DCF &amp; Sensitivitas WACC // {tk}
            </h2>
          </div>
          <span className="font-mono text-[11px] text-[#63748A]">
            Model Deterministik
          </span>
        </div>

        {hasValuation ? (
          <div className="space-y-4">
            {valPage.subtitle && (
              <p className="text-xs text-[#63748A] leading-relaxed">
                {valPage.subtitle}
              </p>
            )}

            {/* Lane B Chart: DcfSpreadCharts */}
            {payload && <DcfSpreadCharts payload={payload} />}

            {/* Three Block Tables (Blok 1, 2, 3) */}
            <Card className="rounded-lg border border-[#D6E2EE] bg-white shadow-xs dark:border-[#262930] dark:bg-[#121418]">
              <CardHeader className="border-b border-[#D6E2EE] bg-[#F4F8FC] p-4 pb-3 dark:border-[#1f2228] dark:bg-[#181a1f]">
                <div className="flex items-center justify-between">
                  <CardTitle className="font-mono text-xs font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-neutral-100">
                    {valPage.exhibit8_title || "FCFF Forecast, Terminal Value and Bridge to Equity"}
                  </CardTitle>
                  <span className="font-mono text-[10px] text-[#63748A]">
                    Engine: {valPage.sources?.[2] || valPage.sources?.[0] || "Deterministic FCFF"}
                  </span>
                </div>
              </CardHeader>
              <CardContent className="p-4 sm:p-5 space-y-4">
                {/* Blok 1: Periode Proyeksi Eksplisit */}
                {valPage.block1_rows && valPage.block1_rows.length > 0 && (
                  <div className="space-y-1">
                    <div className="overflow-x-auto rounded border border-[#D6E2EE] font-mono text-xs dark:border-[#262930]">
                      <table className="w-full">
                        <thead>
                          <tr className="bg-[#0B1F3A] text-white text-right text-[11px]">
                            {(
                              valPage.block1_headers || [
                                "Blok 1 - Periode proyeksi eksplisit (Rp bn)",
                                ...(valPage.periods || []),
                              ]
                            ).map((h, idx) => (
                              <th key={idx} className={`py-2 px-3 ${idx === 0 ? "text-left" : ""}`}>
                                {h}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {valPage.block1_rows.map(([label, series], rIdx) => {
                            const isBold =
                              label === "FCFF (build-up)" ||
                              label === "PV of FCFF" ||
                              label.includes("FCFF growth");
                            return (
                              <tr
                                key={rIdx}
                                className={`border-b border-[#D6E2EE]/60 last:border-0 ${
                                  rIdx % 2 === 1 ? "bg-[#F4F8FC] dark:bg-[#181a1f]" : "bg-white dark:bg-[#121316]"
                                } ${isBold ? "font-bold text-[#0B1F3A] dark:text-neutral-100" : "text-[#0B1F3A] dark:text-neutral-300"}`}
                              >
                                <td className="py-1.5 px-3 text-left">{label}</td>
                                {Array.isArray(series) ? (
                                  series.map((val, cIdx) => (
                                    <td key={cIdx} className="py-1.5 px-3 text-right tabular-nums">
                                      {val != null ? String(val) : "-"}
                                    </td>
                                  ))
                                ) : (
                                  <td className="py-1.5 px-3 text-right tabular-nums">{String(series)}</td>
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
                  <div className="space-y-1">
                    <div className="overflow-x-auto rounded border border-[#D6E2EE] font-mono text-xs dark:border-[#262930]">
                      <table className="w-full">
                        <thead>
                          <tr className="bg-[#0B1F3A] text-white text-right text-[11px]">
                            {(
                              valPage.block2_headers || [
                                "Blok 2 - Terminal value",
                                "Gordon Growth",
                                `Exit Multiple ${valPage.drivers?.multiple != null ? valPage.drivers.multiple.toFixed(1) : ""}×`,
                              ]
                            ).map((h, idx) => (
                              <th key={idx} className={`py-2 px-3 ${idx === 0 ? "text-left" : ""}`}>
                                {h}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {valPage.block2_rows.map(([label, a, b], rIdx) => {
                            const isBold = label.includes("PV of Terminal") || label.includes("Terminal Value");
                            return (
                              <tr
                                key={rIdx}
                                className={`border-b border-[#D6E2EE]/60 last:border-0 ${
                                  rIdx % 2 === 1 ? "bg-[#F4F8FC] dark:bg-[#181a1f]" : "bg-white dark:bg-[#121316]"
                                } ${isBold ? "font-bold text-[#0B1F3A] dark:text-neutral-100" : "text-[#0B1F3A] dark:text-neutral-300"}`}
                              >
                                <td className="py-1.5 px-3 text-left">{label}</td>
                                <td className="py-1.5 px-3 text-right tabular-nums">{a != null ? String(a) : "-"}</td>
                                <td className="py-1.5 px-3 text-right tabular-nums">{b != null ? String(b) : "-"}</td>
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
                  <div className="space-y-1">
                    <div className="overflow-x-auto rounded border border-[#D6E2EE] font-mono text-xs dark:border-[#262930]">
                      <table className="w-full">
                        <thead>
                          <tr className="bg-[#0B1F3A] text-white text-right text-[11px]">
                            {(
                              valPage.block3_headers || [
                                "Blok 3 - Bridge ke equity value",
                                "Rp bn",
                                "Per saham (Rp)",
                              ]
                            ).map((h, idx) => (
                              <th key={idx} className={`py-2 px-3 ${idx === 0 ? "text-left" : ""}`}>
                                {h}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {valPage.block3_rows.map(([label, a, b], rIdx) => {
                            const isFv = label.includes("Fair Value");
                            const isBold = isFv || label.includes("Enterprise Value") || label.includes("Equity Value");
                            return (
                              <tr
                                key={rIdx}
                                className={`border-b border-[#D6E2EE]/60 last:border-0 ${
                                  isFv
                                    ? "bg-[#E4EEF7] font-bold text-[#0B1F3A] dark:bg-[#0B1F3A]/40 dark:text-[#A9C9E8]"
                                    : isBold
                                    ? "font-bold text-[#0B1F3A] dark:text-neutral-100"
                                    : "text-[#0B1F3A] dark:text-neutral-300"
                                }`}
                              >
                                <td className="py-1.5 px-3 text-left">{label}</td>
                                <td className="py-1.5 px-3 text-right tabular-nums">{a != null ? String(a) : "-"}</td>
                                <td className="py-1.5 px-3 text-right tabular-nums">{b != null ? String(b) : "-"}</td>
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
              <Card className="rounded-lg border border-[#D6E2EE] bg-white shadow-xs dark:border-[#262930] dark:bg-[#121418]">
                <CardHeader className="border-b border-[#D6E2EE] bg-[#F4F8FC] p-3.5 pb-2.5 dark:border-[#1f2228] dark:bg-[#181a1f]">
                  <div className="flex items-center justify-between">
                    <CardTitle className="font-mono text-xs font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-neutral-100">
                      WACC Components
                    </CardTitle>
                    <span className="font-mono text-[10px] text-[#63748A]">
                      Sumber per komponen tercantum di kolom ketiga
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="p-4 space-y-2">
                  <div className="overflow-x-auto rounded border border-[#D6E2EE] font-mono text-xs dark:border-[#262930]">
                    <table className="w-full">
                      <thead>
                        <tr className="bg-[#0B1F3A] text-white text-[11px]">
                          <th className="py-2 px-3 text-left">Parameter</th>
                          <th className="py-2 px-3 text-right">Nilai</th>
                          <th className="py-2 px-3 text-left">Sumber</th>
                        </tr>
                      </thead>
                      <tbody>
                        {valPage.wacc_rows.map((row, idx) => (
                          <tr
                            key={idx}
                            className={`border-b border-[#D6E2EE]/60 last:border-0 ${
                              idx % 2 === 1 ? "bg-[#F4F8FC] dark:bg-[#181a1f]" : "bg-white dark:bg-[#121316]"
                            }`}
                          >
                            <td className="py-1.5 px-3 font-medium text-[#0B1F3A] dark:text-neutral-200">{row[0]}</td>
                            <td className="py-1.5 px-3 text-right font-bold text-[#0B1F3A] tabular-nums dark:text-neutral-100">
                              {row[1]}
                            </td>
                            <td className="py-1.5 px-3 text-[#63748A] text-[11px]">{row[2]}</td>
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
              <Card className="rounded-lg border border-[#D6E2EE] bg-white shadow-xs dark:border-[#262930] dark:bg-[#121418]">
                <CardHeader className="border-b border-[#D6E2EE] bg-[#F4F8FC] p-3.5 pb-2.5 dark:border-[#1f2228] dark:bg-[#181a1f]">
                  <div className="flex items-center justify-between">
                    <CardTitle className="font-mono text-xs font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-neutral-100">
                      Sensitivity Analysis - WACC × Terminal Growth
                    </CardTitle>
                    <span className="font-mono text-[10px] text-[#63748A]">
                      Base case (WACC {sens.base_wacc} · g {sens.base_g}) dibingkai
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="p-4 space-y-3 font-mono">
                  <div className="overflow-x-auto rounded border border-[#D6E2EE] text-xs dark:border-[#262930]">
                    <table className="w-full">
                      <thead>
                        <tr className="bg-[#0B1F3A] text-white text-[11px]">
                          <th className="py-2 px-3 text-left">WACC \ g</th>
                          {sens.columns.map((col, idx) => (
                            <th key={idx} className="py-2 px-3 text-right">
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {sens.rows.map((r, rIdx) => (
                          <tr key={rIdx} className="border-b border-[#D6E2EE]/60 last:border-0">
                            <td className="py-1.5 px-3 font-bold text-[#0B1F3A] bg-[#F4F8FC] dark:bg-[#181a1f] dark:text-neutral-200">
                              {r.label}
                            </td>
                            {r.cells.map((c, cIdx) => (
                              <td
                                key={cIdx}
                                className={`py-1.5 px-3 text-right tabular-nums ${
                                  c.base
                                    ? "font-black text-[#0B1F3A] bg-[#E4EEF7] ring-2 ring-[#0B1F3A] dark:bg-[#0B1F3A]/40 dark:text-[#A9C9E8]"
                                    : "text-[#0B1F3A] dark:text-neutral-200"
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
                    <p className="text-[11px] text-[#63748A] leading-relaxed">
                      Dasar Rp {fmtIDR(sens.base_fv)} (WACC {sens.base_wacc} · g {sens.base_g}). Rentang grid: Rp{" "}
                      {fmtIDR(sens.swing.min)} – Rp {fmtIDR(sens.swing.max)}.
                    </p>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Sensitivity Strip & Method Comparison */}
            {br && sens && (
              <Card className="rounded-lg border border-[#D6E2EE] bg-[#F4F8FC] p-4 font-mono shadow-xs dark:border-[#262930] dark:bg-[#121418]">
                <div className="text-xs font-bold uppercase tracking-wider text-[#0B1F3A] mb-3 dark:text-[#A9C9E8]">
                  Analisa Sensitivitas &amp; Keterkaitan Asumsi
                </div>

                <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-3 mb-4">
                  <div className="rounded border border-[#D6E2EE] bg-white p-2.5 dark:border-[#262930] dark:bg-[#181a1f]">
                    <div className="text-[10px] font-bold uppercase text-[#63748A]">PV TERMINAL / EV</div>
                    <div className="text-sm font-bold text-[#0B1F3A] tabular-nums mt-0.5 dark:text-neutral-100">
                      {br.tv_share != null ? formatPct(br.tv_share * 100, 1, true) : "-"}
                    </div>
                    <div className="text-[10px] text-[#63748A] mt-0.5">nilai wajar bertumpu di luar proyeksi</div>
                  </div>

                  <div className="rounded border border-[#D6E2EE] bg-white p-2.5 dark:border-[#262930] dark:bg-[#181a1f]">
                    <div className="text-[10px] font-bold uppercase text-[#63748A]">NET DEBT / EV</div>
                    <div className="text-sm font-bold text-[#0B1F3A] tabular-nums mt-0.5 dark:text-neutral-100">
                      {br.net_debt_share != null ? formatPct(br.net_debt_share * 100, 1, true) : "-"}
                    </div>
                    <div className="text-[10px] text-[#63748A] mt-0.5">
                      sisa ekuitas Rp {formatIdn(br.equity_gordon != null ? br.equity_gordon / 1e12 : null, 2)} tn
                    </div>
                  </div>

                  <div className="rounded border border-[#D6E2EE] bg-white p-2.5 dark:border-[#262930] dark:bg-[#181a1f]">
                    <div className="text-[10px] font-bold uppercase text-[#63748A]">RENTANG GRID WACC × G</div>
                    <div className="text-sm font-bold text-[#0B1F3A] tabular-nums mt-0.5 dark:text-neutral-100">
                      Rp {sens.swing ? `${fmtIDR(sens.swing.min)} – ${fmtIDR(sens.swing.max)}` : "-"}
                    </div>
                    <div className="text-[10px] text-[#63748A] mt-0.5">
                      dasar Rp {fmtIDR(sens.base_fv)} ({sens.base_wacc} · g {sens.base_g})
                    </div>
                  </div>
                </div>

                {/* Narrative & Notes */}
                {valPage.narrative && valPage.narrative.length > 0 && (
                  <div className="space-y-1.5 border-t border-[#D6E2EE] pt-3 text-xs leading-relaxed text-[#0B1F3A] dark:text-neutral-300">
                    {valPage.narrative.map((p, idx) => (
                      <p key={idx}>{p}</p>
                    ))}
                  </div>
                )}

                {valPage.notes && valPage.notes.length > 0 && (
                  <div className="space-y-1 border-t border-[#D6E2EE] pt-2.5 text-[11px] text-[#63748A]">
                    {valPage.notes.map((n, idx) => (
                      <div key={idx} className="flex items-start gap-1.5">
                        <span className="font-bold text-[#0B1F3A] shrink-0 dark:text-neutral-300">·</span>
                        <span>{n}</span>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            )}

            {/* Metode Pembanding / Crosscheck Rows */}
            {valPage.crosscheck_rows && valPage.crosscheck_rows.length > 0 && (
              <Card className="rounded-lg border border-[#D6E2EE] bg-white shadow-xs dark:border-[#262930] dark:bg-[#121418]">
                <CardHeader className="border-b border-[#D6E2EE] bg-[#F4F8FC] p-3.5 pb-2.5 dark:border-[#1f2228] dark:bg-[#181a1f]">
                  <div className="flex items-center justify-between">
                    <CardTitle className="font-mono text-xs font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-neutral-100">
                      Metode Pembanding (Anchor Target Price)
                    </CardTitle>
                    <span className="font-mono text-[10px] text-[#63748A]">
                      Sectors Annual EBITDA / Multiples Crosscheck
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="p-4 space-y-2">
                  <div className="overflow-x-auto rounded border border-[#D6E2EE] font-mono text-xs dark:border-[#262930]">
                    <table className="w-full">
                      <thead>
                        <tr className="bg-[#0B1F3A] text-white text-[11px]">
                          <th className="py-2 px-3 text-left">Metode</th>
                          <th className="py-2 px-3 text-right">Fair Value (Rp)</th>
                          <th className="py-2 px-3 text-left">Peran</th>
                        </tr>
                      </thead>
                      <tbody>
                        {valPage.crosscheck_rows.map((row, idx) => (
                          <tr
                            key={idx}
                            className={`border-b border-[#D6E2EE]/60 last:border-0 ${
                              idx % 2 === 1 ? "bg-[#F4F8FC] dark:bg-[#181a1f]" : "bg-white dark:bg-[#121316]"
                            }`}
                          >
                            <td className="py-1.5 px-3 font-medium text-[#0B1F3A] dark:text-neutral-200">{row[0]}</td>
                            <td className="py-1.5 px-3 text-right font-bold text-[#0B1F3A] tabular-nums dark:text-neutral-100">
                              {typeof row[1] === "number" ? `Rp ${fmtIDR(row[1])}` : String(row[1])}
                            </td>
                            <td className="py-1.5 px-3 text-[#63748A] text-[11px]">{row[2]}</td>
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
      {/* BAB 5: PEERS 5A - CROSS-SECTIONAL VALUATION                               */}
      {/* ========================================================================= */}
      <section id="peers-5a" className="scroll-mt-28 space-y-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#D6E2EE] pb-2 dark:border-[#262930]">
          <div className="flex items-center gap-2">
            <span className="rounded bg-[#0B1F3A] px-1.5 py-0.5 font-mono text-[10px] font-bold text-[#E4EEF7] dark:bg-[#0B1F3A] dark:text-[#A9C9E8]">
              05
            </span>
            <h2 className="font-sans text-sm font-bold tracking-tight text-[#0B1F3A] dark:text-neutral-100 uppercase">
              Peer Valuation - Cross-Sectional // {tk}
            </h2>
          </div>
          <span className="font-mono text-[11px] text-[#63748A]">
            Komparasi Satu Tanggal
          </span>
        </div>

        {partA && partA.rows && partA.rows.length > 0 ? (
          <Card className="rounded-lg border border-[#D6E2EE] bg-white shadow-xs dark:border-[#262930] dark:bg-[#121418]">
            <CardHeader className="border-b border-[#D6E2EE] bg-[#F4F8FC] p-4 pb-3 dark:border-[#1f2228] dark:bg-[#181a1f]">
              <div className="flex items-center justify-between">
                <CardTitle className="font-mono text-xs font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-neutral-100">
                  {partA.title || "Peer Valuation - Cross-Sectional"}
                </CardTitle>
                <span className="font-mono text-[10px] text-[#63748A]">
                  {partA.sources?.[0] || "Sectors API"}
                </span>
              </div>
              <CardDescription className="text-xs text-[#63748A] mt-1 font-sans">
                Bagian A dari dua metodologi berbeda filosofi. Membandingkan emiten dengan peer set pada satu tanggal harga.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-4 sm:p-5 space-y-3 font-mono">
              <div className="overflow-x-auto rounded border border-[#D6E2EE] text-xs dark:border-[#262930]">
                {(() => {
                  const columns =
                    partA.columns && partA.columns.length > 0
                      ? partA.columns
                      : ["Ticker", "Perusahaan", "P/E (x)", "P/BV (x)", "EV/EBITDA (x)", "ROE (%)", "Market Cap"]

                  return (
                    <table className="w-full">
                      <thead>
                        <tr className="bg-[#0B1F3A] text-white text-[11px]">
                          {columns.map((col, idx) => {
                            const type = getPeerColumnType(col, idx)
                            const isLeft = type === "symbol" || type === "name"
                            return (
                              <th key={idx} className={`py-2 px-3 ${isLeft ? "text-left" : "text-right"}`}>
                                {col}
                              </th>
                            )
                          })}
                        </tr>
                      </thead>
                      <tbody>
                        {partA.rows.map((r, idx) => {
                          const isCovered = Boolean(r.is_covered)
                          return (
                            <tr
                              key={idx}
                              className={`border-b border-[#D6E2EE]/60 last:border-0 ${
                                isCovered
                                  ? "bg-[#E4EEF7] font-bold text-[#0B1F3A] border-l-4 border-l-[#0B1F3A] dark:bg-[#0B1F3A]/40 dark:text-[#A9C9E8]"
                                  : idx % 2 === 1
                                  ? "bg-[#F4F8FC] dark:bg-[#181a1f]"
                                  : "bg-white dark:bg-[#121316]"
                              }`}
                            >
                              {columns.map((col, cIdx) => {
                                const type = getPeerColumnType(col, cIdx)
                                const isLeft = type === "symbol" || type === "name"
                                return (
                                  <td
                                    key={cIdx}
                                    className={`py-1.5 px-3 ${isLeft ? "text-left" : "text-right tabular-nums"}`}
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
                          <tr className="border-t-2 border-[#0B1F3A] bg-[#F4F8FC] font-bold text-[#0B1F3A] dark:bg-[#181a1f] dark:text-neutral-100">
                            {columns.map((col, cIdx) => {
                              const type = getPeerColumnType(col, cIdx)
                              const isLeft = type === "symbol" || type === "name"
                              return (
                                <td
                                  key={cIdx}
                                  className={`py-2 px-3 ${
                                    isLeft ? "text-left font-sans text-xs" : "text-right tabular-nums"
                                  }`}
                                >
                                  {renderPeerStatCell(partA.median, col, cIdx, true, partA.counts)}
                                </td>
                              )
                            })}
                          </tr>
                        )}
                        {partA.average && (
                          <tr className="border-b-2 border-[#0B1F3A] bg-[#F4F8FC] font-bold text-[#0B1F3A] dark:bg-[#181a1f] dark:text-neutral-100">
                            {columns.map((col, cIdx) => {
                              const type = getPeerColumnType(col, cIdx)
                              const isLeft = type === "symbol" || type === "name"
                              return (
                                <td
                                  key={cIdx}
                                  className={`py-2 px-3 ${
                                    isLeft ? "text-left font-sans text-xs" : "text-right tabular-nums"
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
                <div className="text-[11px] text-[#63748A]">
                  {partA.criteria ? `${partA.criteria} ` : ""}
                  {partA.basis ? `Basis: ${partA.basis}. ` : ""}
                  Baris ber-shading = emiten yang dicover.
                </div>
              )}
              {partA.narrative_text && (
                <p className="text-xs text-[#0B1F3A] leading-relaxed dark:text-neutral-300">
                  {partA.narrative_text}
                </p>
              )}
              {!partA.narrative_text && partA.narrative && partA.narrative.length > 0 && (
                <div className="space-y-1.5 text-xs text-[#0B1F3A] leading-relaxed dark:text-neutral-300">
                  {partA.narrative.map((p, idx) => (
                    <p key={idx}>{p}</p>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        ) : (
          <PendingCard label="Peer Valuation 5A" />
        )}
      </section>

      {/* ========================================================================= */}
      {/* BAB 6: OWN HISTORY 5B - RELATIVE VALUATION                                */}
      {/* ========================================================================= */}
      <section id="peers-5b" className="scroll-mt-28 space-y-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#D6E2EE] pb-2 dark:border-[#262930]">
          <div className="flex items-center gap-2">
            <span className="rounded bg-[#0B1F3A] px-1.5 py-0.5 font-mono text-[10px] font-bold text-[#E4EEF7] dark:bg-[#0B1F3A] dark:text-[#A9C9E8]">
              06
            </span>
            <h2 className="font-sans text-sm font-bold tracking-tight text-[#0B1F3A] dark:text-neutral-100 uppercase">
              Valuasi Relatif Historis (Own History 5B) // {tk}
            </h2>
          </div>
          <span className="font-mono text-[11px] text-[#63748A]">
            Time-Series Bands &amp; Implied
          </span>
        </div>

        {partB ? (
          <div className="space-y-4">
            {partB.methodology && (
              <p className="text-xs text-[#63748A] leading-relaxed">
                {partB.methodology}
              </p>
            )}

            {/* Lane B Chart: PeersCharts */}
            {payload && <PeersCharts payload={payload} />}

            {/* Implied Price Judgement Table */}
            {partB.implied && partB.implied.length > 0 && (
              <Card className="rounded-lg border border-[#D6E2EE] bg-white shadow-xs dark:border-[#262930] dark:bg-[#121418]">
                <CardHeader className="border-b border-[#D6E2EE] bg-[#F4F8FC] p-3.5 pb-2.5 dark:border-[#1f2228] dark:bg-[#181a1f]">
                  <CardTitle className="font-mono text-xs font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-neutral-100">
                    Implied Price Judgement
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-4 space-y-3 font-mono">
                  <div className="overflow-x-auto rounded border border-[#D6E2EE] text-xs dark:border-[#262930]">
                    <table className="w-full">
                      <thead>
                        <tr className="bg-[#0B1F3A] text-white text-[11px]">
                          <th className="py-2 px-3 text-left">Multiple</th>
                          <th className="py-2 px-3 text-right">Reversion ke Mean (Rp)</th>
                          <th className="py-2 px-3 text-right">Reversion ke Median (Rp)</th>
                          <th className="py-2 px-3 text-right">Rentang</th>
                          <th className="py-2 px-3 text-right">Selisih</th>
                        </tr>
                      </thead>
                      <tbody>
                        {partB.implied.map((r, idx) => (
                          <tr
                            key={idx}
                            className={`border-b border-[#D6E2EE]/60 last:border-0 ${
                              idx % 2 === 1 ? "bg-[#F4F8FC] dark:bg-[#181a1f]" : "bg-white dark:bg-[#121316]"
                            }`}
                          >
                            <td className="py-1.5 px-3 font-bold text-[#0B1F3A] dark:text-neutral-200">{r.label}</td>
                            <td className="py-1.5 px-3 text-right font-bold text-[#0B1F3A] tabular-nums dark:text-neutral-100">
                              Rp {fmtIDR(r.to_mean)}
                            </td>
                            <td className="py-1.5 px-3 text-right font-bold text-[#0B1F3A] tabular-nums dark:text-neutral-100">
                              Rp {fmtIDR(r.to_median)}
                            </td>
                            <td className="py-1.5 px-3 text-right tabular-nums text-[#63748A]">
                              {r.is_range && r.low != null && r.high != null
                                ? `Rp ${fmtIDR(r.low)} – ${fmtIDR(r.high)}`
                                : "konvergen"}
                            </td>
                            <td className="py-1.5 px-3 text-right font-bold tabular-nums">
                              {r.delta_pct != null ? `${r.delta_pct.toFixed(0)}%` : "-"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="text-[11px] text-[#63748A]">
                    Harga terakhir: {partB.last_close != null ? `Rp ${fmtIDR(partB.last_close)}` : "-"} ·{" "}
                    {partB.driver_note}
                  </div>

                  {partB.disclaimer && (
                    <div className="rounded border-l-2 border-[#0B1F3A] bg-[#F4F8FC] p-2.5 text-xs text-[#0B1F3A] dark:border-[#A9C9E8] dark:bg-[#181a1f] dark:text-neutral-300">
                      <strong>Catatan:</strong> {partB.disclaimer}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        ) : (
          <PendingCard label="Own history 5B" />
        )}
      </section>
    </div>
  )
}
