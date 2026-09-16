import React from "react"
import { FileText } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import type {
  FullReportPayload,
  StatementsPage,
  CashflowPage,
  KeyRatioPage,
  RiskItem,
  ExhibitItem,
  SectorData,
  StatementRow,
} from "@/lib/reportTypes"
import { KeyRatioCharts } from "./charts/KeyRatioCharts"

export interface RiskFactorsProps {
  ticker: string
  payload?: FullReportPayload | null
}

type NormalizedRow = {
  label: string
  cells: (number | string | null)[]
  kind?: string
  note?: string
}

function fmtStatementNumber(v: number | string | null | undefined): string {
  if (v == null || v === "" || v === "-" || v === "-") return "-"
  if (typeof v === "string") {
    const lower = v.trim().toLowerCase()
    if (lower === "n/a" || lower === "na") return "n/a"
    const num = Number(v.replace(/\./g, "").replace(",", "."))
    if (Number.isNaN(num)) return v
    v = num
  }
  if (typeof v === "number") {
    if (Number.isNaN(v)) return "-"
    if (Math.abs(v) < 1e-6) return "0"
    const rounded = Math.round(Math.abs(v))
    const formatted = rounded.toLocaleString("id-ID")
    return v < 0 ? `(${formatted})` : formatted
  }
  return String(v)
}

function fmtRatioNumber(v: number | string | null | undefined, digits: number = 1): string {
  if (v == null || v === "" || v === "-" || v === "-") return "-"
  if (typeof v === "string") {
    const lower = v.trim().toLowerCase()
    if (lower === "n/a" || lower === "na") return "n/a"
    const num = Number(v.replace(/\./g, "").replace(",", "."))
    if (Number.isNaN(num)) return v
    v = num
  }
  if (typeof v === "number") {
    if (Number.isNaN(v)) return "-"
    const isZero = Math.abs(v) < 1e-6
    const fixed = (isZero ? 0 : Math.abs(v)).toFixed(digits).replace(".", ",")
    return v < 0 ? `(${fixed})` : fixed
  }
  return String(v)
}

function normalizeRows(
  rawRows?: (StatementRow | (string | number | null)[])[] | null,
  boldRows?: number[]
): NormalizedRow[] {
  if (!rawRows || !Array.isArray(rawRows)) return []
  return rawRows.map((r, idx) => {
    if (Array.isArray(r)) {
      const label = String(r[0] ?? "")
      const cells = r.slice(1)
      const isBold = boldRows?.includes(idx)
      const isAllEmpty = cells.every((c) => c === null || c === "" || c === undefined)
      return {
        label,
        cells,
        kind: isAllEmpty ? "section" : isBold ? "subtotal" : "",
      }
    }
    const isBold = boldRows?.includes(idx)
    return {
      label: r.label,
      cells: r.cells || [],
      kind: r.kind || (isBold ? "subtotal" : ""),
      note: r.note,
    }
  })
}

function PendingCard({ label }: { label: string }) {
  return (
    <div className="rounded-xl border border-[#E7E3DA] bg-white p-6 text-center text-xs text-[#6B6659] dark:border-[#2A2822] dark:bg-[#1B1A16] dark:text-[#A8A296]">
      {label} belum tersedia di payload.
    </div>
  )
}

export function RiskFactors({ ticker, payload }: RiskFactorsProps) {
  const tk = ticker.toUpperCase()
  const stmts: StatementsPage | undefined = payload?.statements_page
  const finStmts = payload?.financial_statements
  const cf: CashflowPage | undefined = payload?.cashflow_page
  const keyRatio: KeyRatioPage | undefined = payload?.key_ratio_page
  const risks: RiskItem[] = payload?.risks || []
  const exhibits: ExhibitItem[] = payload?.exhibits || []
  const sectorData: SectorData | undefined = payload?.sector_data
  const meta = payload?.meta

  // Resolve Income Statement data
  const incomeBlock = stmts?.income || finStmts?.income
  const hasIncome = Boolean(incomeBlock && (stmts?.available !== false))
  const incomeHeaders = stmts?.income?.headers || finStmts?.income?.headers || ["Pos (Rp bn)", ...(stmts?.years || [])]
  const incomeRows = normalizeRows(stmts?.income?.rows || finStmts?.income?.rows)
  const incomeSource = stmts?.sources?.[0] || finStmts?.income?.source || "Laporan keuangan IDX"

  // Resolve Balance Sheet data
  const balanceBlock = stmts?.balance || finStmts?.balance
  const hasBalance = Boolean(balanceBlock && (stmts?.available !== false))
  const balanceHeaders = stmts?.balance?.headers || finStmts?.balance?.headers || ["Pos (Rp bn)", ...(stmts?.years || [])]
  const balanceRows = normalizeRows(stmts?.balance?.rows || finStmts?.balance?.rows)
  const balanceSource = stmts?.balance?.source || stmts?.sources?.[0] || finStmts?.balance?.source || "Laporan keuangan IDX"

  // Resolve Cash Flow data
  const finCf = finStmts?.cashflow
  const hasCashflow = Boolean(cf && cf.available !== false) || Boolean(finCf)

  // Resolve Key Ratios data
  const finRatios = finStmts?.ratios
  const hasKeyRatio = Boolean(keyRatio && keyRatio.available !== false) || Boolean(finRatios)

  return (
    <div className="space-y-8">
      {/* ========================================================================= */}
      {/* SECTION 7: LAPORAN KEUANGAN - LABA RUGI & NERACA                         */}
      {/* ========================================================================= */}
      <section id="financial-statements" className="scroll-mt-28 space-y-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#E7E3DA] pb-2 dark:border-[#2A2822]">
          <h2 className="font-serif text-xl font-medium tracking-tight text-[#1C1B17] dark:text-[#EDEAE3]">
            Laporan keuangan - Laba rugi dan neraca
          </h2>
          <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
            {balanceSource}
          </span>
        </div>

        {hasIncome || hasBalance ? (
          <div className="space-y-5">
            {/* Income Statement Table */}
            {hasIncome && (
              <Card className="rounded-xl border border-[#E7E3DA] bg-white dark:border-[#2A2822] dark:bg-[#1B1A16]">
                <CardHeader className="border-b border-[#E7E3DA] p-5 pb-3 dark:border-[#2A2822]">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                      {stmts?.income?.title || finStmts?.income?.title || "Laporan laba rugi (Income statement)"}
                    </CardTitle>
                    <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
                      {incomeSource}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="p-5 space-y-2">
                  <div className="overflow-x-auto rounded-lg border border-[#E7E3DA] dark:border-[#2A2822]">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-[#E7E3DA] bg-[#FBFAF7] text-right text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
                          {incomeHeaders.map((h, i) => (
                            <th key={i} className={`py-2.5 px-3 font-semibold ${i === 0 ? "text-left text-[#1C1B17] dark:text-[#EDEAE3]" : ""}`}>
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E7E3DA]/60 dark:divide-[#2A2822]/60">
                        {incomeRows.map((r, rIdx) => {
                          if (r.kind === "section") {
                            return (
                              <tr
                                key={rIdx}
                                className="bg-[#FBFAF7] font-semibold text-[#1C1B17] text-xs dark:bg-[#14130F] dark:text-[#EDEAE3]"
                              >
                                <td colSpan={incomeHeaders.length} className="py-2.5 px-3">
                                  {r.label}
                                </td>
                              </tr>
                            )
                          }
                          const isSubtotal = r.kind === "subtotal"
                          const isHighlight = r.kind === "highlight" || r.label.toLowerCase().includes("net profit")
                          return (
                            <tr
                              key={rIdx}
                              className={`${
                                isHighlight
                                  ? "bg-[#0E6E63]/10 font-semibold text-[#0E6E63] dark:bg-[#4FD1B5]/15 dark:text-[#4FD1B5]"
                                  : isSubtotal
                                  ? "font-semibold text-[#1C1B17] border-t border-t-[#E7E3DA] dark:border-t-[#2A2822] dark:text-[#EDEAE3]"
                                  : rIdx % 2 === 1
                                  ? "bg-[#FBFAF7]/50 dark:bg-[#14130F]/30"
                                  : "bg-white dark:bg-[#1B1A16]"
                              }`}
                            >
                              <td className="py-2 px-3 text-left font-sans">
                                <span className={isSubtotal || isHighlight ? "font-semibold" : "font-normal"}>
                                  {r.label}
                                </span>
                                {r.kind === "deduction" && <span className="ml-1 text-[11px] text-[#6B6659] dark:text-[#A8A296]">(-)</span>}
                                {r.note && <span className="ml-1.5 text-[11px] italic text-[#6B6659] dark:text-[#A8A296]">{r.note}</span>}
                              </td>
                              {r.cells.map((c, cIdx) => (
                                <td key={cIdx} className="py-2 px-3 text-right font-mono tabular-nums text-[#1C1B17] dark:text-[#EDEAE3]">
                                  {fmtStatementNumber(c)}
                                </td>
                              ))}
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Balance Sheet Table */}
            {hasBalance && (
              <Card className="rounded-xl border border-[#E7E3DA] bg-white dark:border-[#2A2822] dark:bg-[#1B1A16]">
                <CardHeader className="border-b border-[#E7E3DA] p-5 pb-3 dark:border-[#2A2822]">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                      {stmts?.balance?.title || finStmts?.balance?.title || "Neraca keuangan (Balance sheet)"}
                    </CardTitle>
                    <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
                      {balanceSource}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="p-5 space-y-3">
                  <div className="overflow-x-auto rounded-lg border border-[#E7E3DA] dark:border-[#2A2822]">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-[#E7E3DA] bg-[#FBFAF7] text-right text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
                          {balanceHeaders.map((h, i) => (
                            <th key={i} className={`py-2.5 px-3 font-semibold ${i === 0 ? "text-left text-[#1C1B17] dark:text-[#EDEAE3]" : ""}`}>
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E7E3DA]/60 dark:divide-[#2A2822]/60">
                        {balanceRows.map((r, rIdx) => {
                          if (r.kind === "section") {
                            return (
                              <tr
                                key={rIdx}
                                className="bg-[#FBFAF7] font-semibold text-[#1C1B17] text-xs dark:bg-[#14130F] dark:text-[#EDEAE3]"
                              >
                                <td colSpan={balanceHeaders.length} className="py-2.5 px-3">
                                  {r.label}
                                </td>
                              </tr>
                            )
                          }
                          const isSubtotal = r.kind === "subtotal"
                          return (
                            <tr
                              key={rIdx}
                              className={`${
                                isSubtotal
                                  ? "font-semibold text-[#1C1B17] border-t border-t-[#E7E3DA] dark:border-t-[#2A2822] dark:text-[#EDEAE3]"
                                  : rIdx % 2 === 1
                                  ? "bg-[#FBFAF7]/50 dark:bg-[#14130F]/30"
                                  : "bg-white dark:bg-[#1B1A16]"
                              }`}
                            >
                              <td className="py-2 px-3 text-left font-sans">
                                <span className={isSubtotal ? "font-semibold" : "font-normal"}>
                                  {r.label}
                                </span>
                                {r.kind === "deduction" && <span className="ml-1 text-[11px] text-[#6B6659] dark:text-[#A8A296]">(-)</span>}
                                {r.note && <span className="ml-1.5 text-[11px] italic text-[#6B6659] dark:text-[#A8A296]">{r.note}</span>}
                              </td>
                              {r.cells.map((c, cIdx) => (
                                <td key={cIdx} className="py-2 px-3 text-right font-mono tabular-nums text-[#1C1B17] dark:text-[#EDEAE3]">
                                  {fmtStatementNumber(c)}
                                </td>
                              ))}
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>

                  {/* Balance Check Tie-out Note */}
                  {stmts?.tie_out && (
                    <div className="rounded-lg border border-[#BCE2C9] bg-[#EBF6EE] p-3 text-xs text-[#157F3D] dark:border-[#157F3D]/40 dark:bg-[#157F3D]/10 dark:text-[#34D399]">
                      <strong>Pemeriksaan neraca:</strong> Total Liabilitas &amp; Ekuitas − Total Aset ={" "}
                      {stmts.years?.map((y, i) => (
                        <span key={y}>
                          {y}: {fmtStatementNumber(stmts.tie_out?.[y])}
                          {i < (stmts.years?.length || 1) - 1 ? " · " : ""}
                        </span>
                      ))}{" "}
                      (Rp bn) - {stmts.tied ? "neraca seimbang persis di semua kolom" : "selisih pembulatan"}.
                    </div>
                  )}

                  {/* Notes */}
                  {stmts?.notes && stmts.notes.length > 0 && (
                    <div className="space-y-1 text-xs text-[#6B6659] border-t border-[#E7E3DA] pt-3 dark:border-[#2A2822] dark:text-[#A8A296]">
                      <div className="font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                        Catatan metode dan keterbatasan data:
                      </div>
                      {stmts.notes.map((n, idx) => (
                        <p key={idx}>· {n}</p>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        ) : (
          <PendingCard label="Laporan keuangan (laba rugi dan neraca)" />
        )}
      </section>

      {/* ========================================================================= */}
      {/* SECTION 8: ARUS KAS & RASIO KUNCI                                         */}
      {/* ========================================================================= */}
      <section id="cashflow-ratios" className="scroll-mt-28 space-y-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#E7E3DA] pb-2 dark:border-[#2A2822]">
          <h2 className="font-serif text-xl font-medium tracking-tight text-[#1C1B17] dark:text-[#EDEAE3]">
            Arus kas dan rasio keuangan
          </h2>
          <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
            {cf?.sources?.[0] || keyRatio?.sources?.[0] || "Laporan keuangan & rasio IDX"}
          </span>
        </div>

        {hasCashflow || hasKeyRatio ? (
          <div className="space-y-5">
            {/* 1. Cash Flow Statement */}
            {hasCashflow && (
              <Card className="rounded-xl border border-[#E7E3DA] bg-white dark:border-[#2A2822] dark:bg-[#1B1A16]">
                <CardHeader className="border-b border-[#E7E3DA] p-5 pb-3 dark:border-[#2A2822]">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                      {finCf?.title || "Laporan arus kas (Cash flow statement)"}
                    </CardTitle>
                    <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
                      {cf?.sources?.[0] || finCf?.source || "Laporan keuangan IDX"}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="p-5 space-y-3">
                  <div className="overflow-x-auto rounded-lg border border-[#E7E3DA] dark:border-[#2A2822]">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-[#E7E3DA] bg-[#FBFAF7] text-right text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
                          {(cf?.headers || finCf?.headers || ["Pos arus kas (Rp bn)", ...(cf?.years || [])]).map((h, i) => (
                            <th key={i} className={`py-2.5 px-3 font-semibold ${i === 0 ? "text-left text-[#1C1B17] dark:text-[#EDEAE3]" : ""}`}>
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E7E3DA]/60 dark:divide-[#2A2822]/60">
                        {/* Sections from cashflow_page */}
                        {cf?.sections?.map((sec, sIdx) => (
                          <React.Fragment key={sIdx}>
                            <tr className="bg-[#FBFAF7] font-semibold text-[#1C1B17] text-xs dark:bg-[#14130F] dark:text-[#EDEAE3]">
                              <td colSpan={(cf.headers?.length || 5) + 1} className="py-2.5 px-3">
                                {sec.title}
                              </td>
                            </tr>
                            {sec.rows.map((r, rIdx) => {
                              const isSubtotal = r.kind === "subtotal"
                              return (
                                <tr
                                  key={rIdx}
                                  className={`${
                                    isSubtotal
                                      ? "font-semibold text-[#1C1B17] border-t border-t-[#E7E3DA] dark:border-t-[#2A2822] dark:text-[#EDEAE3]"
                                      : "text-[#1C1B17] dark:text-[#EDEAE3]/90"
                                  }`}
                                >
                                  <td className="py-2 px-3 text-left font-sans">
                                    <span className={isSubtotal ? "font-semibold" : "font-normal"}>{r.label}</span>
                                    {r.kind === "deduction" && <span className="ml-1 text-[11px] text-[#6B6659] dark:text-[#A8A296]">(-)</span>}
                                    {r.note && <span className="ml-1.5 text-[11px] italic text-[#6B6659] dark:text-[#A8A296]">{r.note}</span>}
                                  </td>
                                  {r.cells?.map((c, cIdx) => (
                                    <td key={cIdx} className="py-2 px-3 text-right font-mono tabular-nums text-[#1C1B17] dark:text-[#EDEAE3]">
                                      {fmtStatementNumber(c)}
                                    </td>
                                  ))}
                                </tr>
                              )
                            })}
                          </React.Fragment>
                        ))}

                        {/* Closing Rows */}
                        {cf?.closing?.map((r, idx) => (
                          <tr
                            key={`closing-${idx}`}
                            className="font-semibold text-[#1C1B17] bg-[#FBFAF7] dark:bg-[#14130F] dark:text-[#EDEAE3]"
                          >
                            <td className="py-2 px-3 text-left font-sans">
                              {r.label}
                              {r.note && <span className="ml-1.5 text-[11px] italic font-normal text-[#6B6659] dark:text-[#A8A296]">{r.note}</span>}
                            </td>
                            {r.cells?.map((c, cIdx) => (
                              <td key={cIdx} className="py-2 px-3 text-right font-mono tabular-nums text-[#1C1B17] dark:text-[#EDEAE3]">
                                {fmtStatementNumber(c)}
                              </td>
                            ))}
                          </tr>
                        ))}

                        {/* Memo Rows */}
                        {cf?.memo?.map((r, idx) => (
                          <tr
                            key={`memo-${idx}`}
                            className="italic text-[#0E6E63] bg-[#0E6E63]/5 dark:bg-[#4FD1B5]/10 dark:text-[#4FD1B5]"
                          >
                            <td className="py-2 px-3 text-left font-sans">
                              {r.label}
                              {r.note && <span className="ml-1.5 text-[11px] italic font-normal text-[#6B6659] dark:text-[#A8A296]">{r.note}</span>}
                            </td>
                            {r.cells?.map((c, cIdx) => (
                              <td key={cIdx} className="py-2 px-3 text-right font-mono tabular-nums">
                                {fmtStatementNumber(c)}
                              </td>
                            ))}
                          </tr>
                        ))}

                        {/* Fallback rows from financial_statements.cashflow */}
                        {!cf?.sections && finCf?.rows && (
                          <>
                            {normalizeRows(finCf.rows, finCf.bold_rows).map((r, rIdx) => (
                              <tr
                                key={`fin-cf-${rIdx}`}
                                className={`${
                                  r.kind === "subtotal"
                                    ? "font-semibold text-[#1C1B17] border-t border-t-[#E7E3DA] dark:border-t-[#2A2822] dark:text-[#EDEAE3]"
                                    : "text-[#1C1B17] dark:text-[#EDEAE3]/90"
                                }`}
                              >
                                <td className="py-2 px-3 text-left font-sans font-medium">{r.label}</td>
                                {r.cells.map((c, cIdx) => (
                                  <td key={cIdx} className="py-2 px-3 text-right font-mono tabular-nums text-[#1C1B17] dark:text-[#EDEAE3]">
                                    {fmtStatementNumber(c)}
                                  </td>
                                ))}
                              </tr>
                            ))}
                            {normalizeRows(finCf.footers).map((r, rIdx) => (
                              <tr
                                key={`fin-cf-foot-${rIdx}`}
                                className="font-semibold text-[#1C1B17] bg-[#FBFAF7] dark:bg-[#14130F] dark:text-[#EDEAE3]"
                              >
                                <td className="py-2 px-3 text-left font-sans font-medium">{r.label}</td>
                                {r.cells.map((c, cIdx) => (
                                  <td key={cIdx} className="py-2 px-3 text-right font-mono tabular-nums text-[#1C1B17] dark:text-[#EDEAE3]">
                                    {fmtStatementNumber(c)}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </>
                        )}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* 2. Key Ratios Table & Visualisation */}
            {hasKeyRatio && (
              <Card className="rounded-xl border border-[#E7E3DA] bg-white dark:border-[#2A2822] dark:bg-[#1B1A16]">
                <CardHeader className="border-b border-[#E7E3DA] p-5 pb-3 dark:border-[#2A2822]">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                      {keyRatio?.exhibit_title || finRatios?.title || "Rasio keuangan dan efisiensi"}
                    </CardTitle>
                    <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
                      {keyRatio?.sources?.[0] || finRatios?.source || "Sectors - data historis dan proyeksi"}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="p-5 space-y-4">
                  <div className="overflow-x-auto rounded-lg border border-[#E7E3DA] dark:border-[#2A2822]">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-[#E7E3DA] bg-[#FBFAF7] text-right text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
                          {(keyRatio?.headers || finRatios?.headers || ["Rasio kunci", ...(keyRatio?.years || [])]).map((h, i) => (
                            <th key={i} className={`py-2.5 px-3 font-semibold ${i === 0 ? "text-left text-[#1C1B17] dark:text-[#EDEAE3]" : ""}`}>
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E7E3DA]/60 dark:divide-[#2A2822]/60">
                        {/* Sections from key_ratio_page */}
                        {keyRatio?.sections?.map((sec, sIdx) => (
                          <React.Fragment key={sIdx}>
                            <tr className="bg-[#FBFAF7] font-semibold text-[#1C1B17] text-xs dark:bg-[#14130F] dark:text-[#EDEAE3]">
                              <td colSpan={(keyRatio.headers?.length || 5) + 1} className="py-2.5 px-3">
                                {sec.title}
                              </td>
                            </tr>
                            {sec.rows.map((r, rIdx) => (
                              <tr
                                key={rIdx}
                                className={`${
                                  rIdx % 2 === 1 ? "bg-[#FBFAF7]/50 dark:bg-[#14130F]/30" : "bg-white dark:bg-[#1B1A16]"
                                }`}
                              >
                                <td className="py-2 px-3 text-left font-sans font-medium text-[#1C1B17] dark:text-[#EDEAE3]">
                                  {r.label}
                                  {r.note && <span className="ml-1.5 text-[11px] italic text-[#6B6659] dark:text-[#A8A296]">{r.note}</span>}
                                </td>
                                {r.cells?.map((c, cIdx) => (
                                  <td key={cIdx} className="py-2 px-3 text-right font-mono tabular-nums text-[#1C1B17] dark:text-[#EDEAE3]">
                                    {fmtRatioNumber(c, 1)}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </React.Fragment>
                        ))}

                        {/* Fallback rows from financial_statements.ratios */}
                        {!keyRatio?.sections && finRatios?.rows && (
                          normalizeRows(finRatios.rows).map((r, rIdx) => {
                            if (r.kind === "section") {
                              return (
                                <tr
                                  key={`fin-ratio-${rIdx}`}
                                  className="bg-[#FBFAF7] font-semibold text-[#1C1B17] text-xs dark:bg-[#14130F] dark:text-[#EDEAE3]"
                                >
                                  <td colSpan={(finRatios.headers?.length || 5) + 1} className="py-2.5 px-3">
                                    {r.label}
                                  </td>
                                </tr>
                              )
                            }
                            return (
                              <tr
                                key={`fin-ratio-${rIdx}`}
                                className={`${
                                  rIdx % 2 === 1 ? "bg-[#FBFAF7]/50 dark:bg-[#14130F]/30" : "bg-white dark:bg-[#1B1A16]"
                                }`}
                              >
                                <td className="py-2 px-3 text-left font-sans font-medium text-[#1C1B17] dark:text-[#EDEAE3]">
                                  {r.label}
                                </td>
                                {r.cells.map((c, cIdx) => (
                                  <td key={cIdx} className="py-2 px-3 text-right font-mono tabular-nums text-[#1C1B17] dark:text-[#EDEAE3]">
                                    {fmtRatioNumber(c, 1)}
                                  </td>
                                ))}
                              </tr>
                            )
                          })
                        )}
                      </tbody>
                    </table>
                  </div>

                  {/* Growth Basis Line */}
                  {keyRatio?.growth_basis && Object.keys(keyRatio.growth_basis).length > 0 && (
                    <div className="rounded-lg border border-[#E7E3DA] bg-[#FBFAF7] p-3 text-xs text-[#1C1B17] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#EDEAE3]">
                      <strong>Basis pertumbuhan tahun awal (FY2024A vs FY2023A):</strong>{" "}
                      {Object.entries(keyRatio.growth_basis)
                        .map(([k, v]) => `${k}: ${fmtRatioNumber(v, 1)}%`)
                        .join(" · ")}
                    </div>
                  )}

                  {/* Visual Cards */}
                  {keyRatio && <KeyRatioCharts keyRatio={keyRatio} />}

                  {/* Notes */}
                  {((cf?.notes && cf.notes.length > 0) || (keyRatio?.notes && keyRatio.notes.length > 0)) && (
                    <div className="space-y-1 text-xs text-[#6B6659] border-t border-[#E7E3DA] pt-3 dark:border-[#2A2822] dark:text-[#A8A296]">
                      <div className="font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                        Catatan rekonsiliasi dan keterbatasan data:
                      </div>
                      {cf?.notes?.map((n, idx) => (
                        <p key={`cf-n-${idx}`}>· {n}</p>
                      ))}
                      {keyRatio?.notes?.map((n, idx) => (
                        <p key={`kr-n-${idx}`}>· {n}</p>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        ) : (
          <PendingCard label="Arus kas dan rasio kunci" />
        )}
      </section>

      {/* ========================================================================= */}
      {/* SECTION 9: FAKTOR RISIKO                                                  */}
      {/* ========================================================================= */}
      <section id="risk-factors" className="scroll-mt-28 space-y-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#E7E3DA] pb-2 dark:border-[#2A2822]">
          <h2 className="font-serif text-xl font-medium tracking-tight text-[#1C1B17] dark:text-[#EDEAE3]">
            Faktor risiko
          </h2>
          <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
            Tingkat keparahan dan mitigasi
          </span>
        </div>

        {risks.length > 0 ? (
          <Card className="rounded-xl border border-[#E7E3DA] bg-white dark:border-[#2A2822] dark:bg-[#1B1A16]">
            <CardHeader className="border-b border-[#E7E3DA] p-5 pb-3 dark:border-[#2A2822]">
              <CardTitle className="text-sm font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                Faktor risiko dan mitigasi teridentifikasi ({risks.length} poin)
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5 space-y-4">
              <div className="space-y-4">
                {risks.map((r, idx) => (
                  <div
                    key={idx}
                    className="grid grid-cols-[28px_1fr_auto] gap-3 items-start border-t border-[#E7E3DA] pt-4 first:border-0 first:pt-0 dark:border-[#2A2822]"
                  >
                    <span className="font-serif text-base font-semibold text-[#B4232A] dark:text-[#F87171]">
                      {idx + 1}.
                    </span>

                    <div className="space-y-1.5">
                      <div className="flex flex-wrap items-center gap-2">
                        <h4 className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                          {r.bucket}
                        </h4>
                        {r.severity != null && (
                          <span className="rounded bg-[#FDF2F2] px-2 py-0.5 text-[11px] font-medium text-[#B4232A] dark:bg-[#B4232A]/20 dark:text-[#F87171]">
                            Tingkat keparahan: {String(r.severity)}
                          </span>
                        )}
                      </div>
                      <p className="text-xs leading-relaxed text-[#6B6659] dark:text-[#A8A296]">
                        {r.detail}
                      </p>
                      {r.source && (
                        <p className="text-[11px] text-[#6B6659]/80 italic dark:text-[#A8A296]/80">
                          Sumber: {r.source}
                        </p>
                      )}
                    </div>

                    {r.stat && (
                      <div className="text-right pl-3 shrink-0">
                        <div className="text-xs font-semibold text-[#1C1B17] font-mono tabular-nums dark:text-[#EDEAE3]">
                          {r.stat}
                        </div>
                        {r.stat_label && (
                          <div className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">
                            {r.stat_label}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {payload?.risks_note && (
                <div className="text-xs text-[#6B6659] border-t border-[#E7E3DA] pt-3 dark:border-[#2A2822] dark:text-[#A8A296]">
                  {payload.risks_note}
                </div>
              )}
            </CardContent>
          </Card>
        ) : (
          <PendingCard label="Faktor risiko" />
        )}
      </section>

      {/* ========================================================================= */}
      {/* SECTION 10: SUMBER DATA & DISKLAIMER                                      */}
      {/* ========================================================================= */}
      <section id="sources-disclaimer" className="scroll-mt-28 space-y-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#E7E3DA] pb-2 dark:border-[#2A2822]">
          <h2 className="font-serif text-xl font-medium tracking-tight text-[#1C1B17] dark:text-[#EDEAE3]">
            Cara membaca dan disklaimer
          </h2>
          <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
            Kepatuhan dan transparansi
          </span>
        </div>

        {/* Exhibits List */}
        {exhibits.length > 0 && (
          <Card className="rounded-xl border border-[#E7E3DA] bg-white dark:border-[#2A2822] dark:bg-[#1B1A16]">
            <CardHeader className="border-b border-[#E7E3DA] p-5 pb-3 dark:border-[#2A2822]">
              <CardTitle className="text-sm font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                Daftar exhibit terverifikasi ({exhibits.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5">
              <div className="grid gap-2.5 sm:grid-cols-2 text-xs">
                {exhibits.map((ex, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between rounded-lg border border-[#E7E3DA] bg-[#FBFAF7] p-2.5 dark:border-[#2A2822] dark:bg-[#14130F]"
                  >
                    <span className="font-medium text-[#1C1B17] truncate mr-2 dark:text-[#EDEAE3]">
                      {ex.title}
                    </span>
                    {ex.source && (
                      <span className="text-[11px] text-[#6B6659] shrink-0 dark:text-[#A8A296]">
                        {ex.source}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Sector Data */}
        {sectorData && (
          <Card className="rounded-xl border border-[#E7E3DA] bg-white dark:border-[#2A2822] dark:bg-[#1B1A16]">
            <CardHeader className="border-b border-[#E7E3DA] p-5 pb-3 dark:border-[#2A2822]">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                  Data sektoral: {sectorData.subsector || meta?.subsector || meta?.sector || "Sektor IDX"}
                </CardTitle>
                <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
                  Sumber: {sectorData.source || "Sektoral Engine"}
                </span>
              </div>
            </CardHeader>
            <CardContent className="p-5 text-xs">
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                {sectorData.growth_forecast_2026 && (
                  <>
                    <div className="rounded-lg border border-[#E7E3DA] bg-[#FBFAF7] p-3 text-center dark:border-[#2A2822] dark:bg-[#14130F]">
                      <div className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">Proyeksi pendapatan 2026</div>
                      <div className="font-semibold text-[#1C1B17] font-mono tabular-nums mt-1 text-sm dark:text-[#EDEAE3]">
                        {sectorData.growth_forecast_2026.revenue_pct != null
                          ? `${sectorData.growth_forecast_2026.revenue_pct > 0 ? "+" : ""}${sectorData.growth_forecast_2026.revenue_pct}%`
                          : "-"}
                      </div>
                    </div>
                    <div className="rounded-lg border border-[#E7E3DA] bg-[#FBFAF7] p-3 text-center dark:border-[#2A2822] dark:bg-[#14130F]">
                      <div className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">Proyeksi EPS 2026</div>
                      <div className="font-semibold text-[#1C1B17] font-mono tabular-nums mt-1 text-sm dark:text-[#EDEAE3]">
                        {sectorData.growth_forecast_2026.eps_pct != null
                          ? `${sectorData.growth_forecast_2026.eps_pct > 0 ? "+" : ""}${sectorData.growth_forecast_2026.eps_pct}%`
                          : "-"}
                      </div>
                    </div>
                  </>
                )}
                {sectorData.growth_actual_2025 && (
                  <>
                    <div className="rounded-lg border border-[#E7E3DA] bg-[#FBFAF7] p-3 text-center dark:border-[#2A2822] dark:bg-[#14130F]">
                      <div className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">Realisasi pendapatan 2025</div>
                      <div className="font-semibold text-[#1C1B17] font-mono tabular-nums mt-1 text-sm dark:text-[#EDEAE3]">
                        {sectorData.growth_actual_2025.revenue_pct != null
                          ? `${sectorData.growth_actual_2025.revenue_pct > 0 ? "+" : ""}${sectorData.growth_actual_2025.revenue_pct}%`
                          : "-"}
                      </div>
                    </div>
                    <div className="rounded-lg border border-[#E7E3DA] bg-[#FBFAF7] p-3 text-center dark:border-[#2A2822] dark:bg-[#14130F]">
                      <div className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">Realisasi EPS 2025</div>
                      <div className="font-semibold text-[#1C1B17] font-mono tabular-nums mt-1 text-sm dark:text-[#EDEAE3]">
                        {sectorData.growth_actual_2025.eps_pct != null
                          ? `${sectorData.growth_actual_2025.eps_pct > 0 ? "+" : ""}${sectorData.growth_actual_2025.eps_pct}%`
                          : "-"}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Regulatory Disclaimer Block */}
        <div className="rounded-xl border border-[#E7E3DA] bg-[#FBFAF7] p-5 text-xs space-y-3 dark:border-[#2A2822] dark:bg-[#1B1A16]">
          <div className="flex items-center gap-2 font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
            <FileText className="h-4 w-4 text-[#0E6E63] dark:text-[#4FD1B5]" />
            <span>Informasi dan disklaimer kepatuhan</span>
          </div>
          <p className="leading-relaxed text-[#6B6659] dark:text-[#A8A296]">
            Laporan ini disusun untuk keperluan informasi dan analisis data pasar modal Indonesia. Seluruh konten didasarkan pada data historis dan publik emiten - bukan merupakan rekomendasi jual atau beli efek, maupun saran investasi profesional. Keputusan investasi sepenuhnya menjadi tanggung jawab pembaca. Selalu lakukan riset mandiri dan konsultasikan dengan penasihat keuangan berlisensi sebelum mengambil keputusan investasi. Kinerja masa lalu tidak menjamin hasil di masa depan.
          </p>
          {meta?.prepared_by && (
            <div className="pt-2.5 border-t border-[#E7E3DA] text-[11px] text-[#6B6659] dark:border-[#2A2822] dark:text-[#A8A296]">
              Disiapkan oleh {meta.prepared_by} · {meta.date} · Bahasa: {meta.language?.toUpperCase() || "ID"}
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
