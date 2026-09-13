import React from "react"
import {
  ShieldAlert,
  AlertTriangle,
  FileText,
  Database,
  Scale,
  DollarSign,
  TrendingDown,
  Info,
  CheckCircle2,
} from "lucide-react"
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
  if (v == null || v === "" || v === "—" || v === "-") return "—"
  if (typeof v === "string") {
    const lower = v.trim().toLowerCase()
    if (lower === "n/a" || lower === "na") return "n/a"
    const num = Number(v.replace(/\./g, "").replace(",", "."))
    if (Number.isNaN(num)) return v
    v = num
  }
  if (typeof v === "number") {
    if (Number.isNaN(v)) return "—"
    if (Math.abs(v) < 1e-6) return "0"
    const rounded = Math.round(Math.abs(v))
    const formatted = rounded.toLocaleString("id-ID")
    return v < 0 ? `(${formatted})` : formatted
  }
  return String(v)
}

function fmtRatioNumber(v: number | string | null | undefined, digits: number = 1): string {
  if (v == null || v === "" || v === "—" || v === "-") return "—"
  if (typeof v === "string") {
    const lower = v.trim().toLowerCase()
    if (lower === "n/a" || lower === "na") return "n/a"
    const num = Number(v.replace(/\./g, "").replace(",", "."))
    if (Number.isNaN(num)) return v
    v = num
  }
  if (typeof v === "number") {
    if (Number.isNaN(v)) return "—"
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
    <div className="rounded-md border border-[#D6E2EE] bg-[#F4F8FC] p-4 text-center font-mono text-xs text-[#63748A] dark:border-[#262930] dark:bg-[#121316]">
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

  // Resolve Income Statement data (statements_page or financial_statements)
  const incomeBlock = stmts?.income || finStmts?.income
  const hasIncome = Boolean(incomeBlock && (stmts?.available !== false))
  const incomeHeaders = stmts?.income?.headers || finStmts?.income?.headers || ["Pos (Rp bn)", ...(stmts?.years || [])]
  const incomeRows = normalizeRows(stmts?.income?.rows || finStmts?.income?.rows)
  const incomeSource = stmts?.sources?.[0] || finStmts?.income?.source || "Laporan Keuangan IDX"

  // Resolve Balance Sheet data (statements_page or financial_statements)
  const balanceBlock = stmts?.balance || finStmts?.balance
  const hasBalance = Boolean(balanceBlock && (stmts?.available !== false))
  const balanceHeaders = stmts?.balance?.headers || finStmts?.balance?.headers || ["Pos (Rp bn)", ...(stmts?.years || [])]
  const balanceRows = normalizeRows(stmts?.balance?.rows || finStmts?.balance?.rows)
  const balanceSource = stmts?.balance?.source || stmts?.sources?.[0] || finStmts?.balance?.source || "Laporan Keuangan IDX"

  // Resolve Cash Flow data
  const finCf = finStmts?.cashflow
  const hasCashflow = Boolean(cf && cf.available !== false) || Boolean(finCf)

  // Resolve Key Ratios data
  const finRatios = finStmts?.ratios
  const hasKeyRatio = Boolean(keyRatio && keyRatio.available !== false) || Boolean(finRatios)

  return (
    <div className="space-y-6">
      {/* ========================================================================= */}
      {/* BAB 7: LAPORAN KEUANGAN — LABA RUGI & NERACA                             */}
      {/* ========================================================================= */}
      <section id="financial-statements" className="scroll-mt-28 space-y-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#D6E2EE] pb-2 dark:border-[#262930]">
          <div className="flex items-center gap-2">
            <span className="rounded bg-[#0B1F3A] px-1.5 py-0.5 font-mono text-[10px] font-bold text-[#E4EEF7] dark:bg-[#0B1F3A] dark:text-[#A9C9E8]">
              07
            </span>
            <h2 className="font-sans text-sm font-bold tracking-tight text-[#0B1F3A] dark:text-neutral-100 uppercase">
              Laporan Keuangan — Laba Rugi &amp; Neraca // {tk}
            </h2>
          </div>
          <span className="font-mono text-[11px] text-[#63748A]">
            {balanceSource}
          </span>
        </div>

        {hasIncome || hasBalance ? (
          <div className="space-y-4">
            {/* Income Statement Table */}
            {hasIncome && (
              <Card className="rounded-lg border border-[#D6E2EE] bg-white shadow-xs dark:border-[#262930] dark:bg-[#121418]">
                <CardHeader className="border-b border-[#D6E2EE] bg-[#F4F8FC] p-3.5 pb-2.5 dark:border-[#1f2228] dark:bg-[#181a1f]">
                  <div className="flex items-center justify-between">
                    <CardTitle className="font-mono text-xs font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-neutral-100">
                      {stmts?.income?.title || finStmts?.income?.title || "Laporan Laba Rugi (Income Statement)"}
                    </CardTitle>
                    <span className="font-mono text-[10px] text-[#63748A]">
                      {incomeSource}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="p-4 space-y-2">
                  <div className="overflow-x-auto rounded border border-[#D6E2EE] font-mono text-xs dark:border-[#262930]">
                    <table className="w-full">
                      <thead>
                        <tr className="bg-[#0B1F3A] text-white text-right text-[11px]">
                          {incomeHeaders.map((h, i) => (
                            <th key={i} className={`py-2 px-3 ${i === 0 ? "text-left" : ""}`}>
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {incomeRows.map((r, rIdx) => {
                          if (r.kind === "section") {
                            return (
                              <tr
                                key={rIdx}
                                className="bg-[#F4F8FC] font-bold text-[#0B1F3A] uppercase tracking-wider text-[11px] dark:bg-[#181a1f] dark:text-[#A9C9E8]"
                              >
                                <td colSpan={incomeHeaders.length} className="py-2 px-3">
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
                              className={`border-b border-[#D6E2EE]/60 last:border-0 ${
                                isHighlight
                                  ? "bg-[#E4EEF7] font-bold text-[#0B1F3A] dark:bg-[#0B1F3A]/40 dark:text-[#A9C9E8]"
                                  : isSubtotal
                                  ? "font-bold text-[#0B1F3A] border-t border-t-[#0B1F3A] dark:text-neutral-100"
                                  : rIdx % 2 === 1
                                  ? "bg-[#F4F8FC] dark:bg-[#181a1f]"
                                  : "bg-white dark:bg-[#121316]"
                              }`}
                            >
                              <td className="py-1.5 px-3 text-left">
                                <span className={isSubtotal || isHighlight ? "font-bold" : "font-normal"}>
                                  {r.label}
                                </span>
                                {r.kind === "deduction" && <span className="ml-1 text-[10px] text-[#63748A]">(-)</span>}
                                {r.note && <span className="ml-1.5 text-[10px] italic text-[#63748A]">{r.note}</span>}
                              </td>
                              {r.cells.map((c, cIdx) => (
                                <td key={cIdx} className="py-1.5 px-3 text-right tabular-nums">
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
              <Card className="rounded-lg border border-[#D6E2EE] bg-white shadow-xs dark:border-[#262930] dark:bg-[#121418]">
                <CardHeader className="border-b border-[#D6E2EE] bg-[#F4F8FC] p-3.5 pb-2.5 dark:border-[#1f2228] dark:bg-[#181a1f]">
                  <div className="flex items-center justify-between">
                    <CardTitle className="font-mono text-xs font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-neutral-100">
                      {stmts?.balance?.title || finStmts?.balance?.title || "Neraca Keuangan (Balance Sheet)"}
                    </CardTitle>
                    <span className="font-mono text-[10px] text-[#63748A]">
                      {balanceSource}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="p-4 space-y-3">
                  <div className="overflow-x-auto rounded border border-[#D6E2EE] font-mono text-xs dark:border-[#262930]">
                    <table className="w-full">
                      <thead>
                        <tr className="bg-[#0B1F3A] text-white text-right text-[11px]">
                          {balanceHeaders.map((h, i) => (
                            <th key={i} className={`py-2 px-3 ${i === 0 ? "text-left" : ""}`}>
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {balanceRows.map((r, rIdx) => {
                          if (r.kind === "section") {
                            return (
                              <tr
                                key={rIdx}
                                className="bg-[#F4F8FC] font-bold text-[#0B1F3A] uppercase tracking-wider text-[11px] dark:bg-[#181a1f] dark:text-[#A9C9E8]"
                              >
                                <td colSpan={balanceHeaders.length} className="py-2 px-3">
                                  {r.label}
                                </td>
                              </tr>
                            )
                          }
                          const isSubtotal = r.kind === "subtotal"
                          return (
                            <tr
                              key={rIdx}
                              className={`border-b border-[#D6E2EE]/60 last:border-0 ${
                                isSubtotal
                                  ? "font-bold text-[#0B1F3A] border-t border-t-[#0B1F3A] dark:text-neutral-100"
                                  : rIdx % 2 === 1
                                  ? "bg-[#F4F8FC] dark:bg-[#181a1f]"
                                  : "bg-white dark:bg-[#121316]"
                              }`}
                            >
                              <td className="py-1.5 px-3 text-left">
                                <span className={isSubtotal ? "font-bold" : "font-normal"}>
                                  {r.label}
                                </span>
                                {r.kind === "deduction" && <span className="ml-1 text-[10px] text-[#63748A]">(-)</span>}
                                {r.note && <span className="ml-1.5 text-[10px] italic text-[#63748A]">{r.note}</span>}
                              </td>
                              {r.cells.map((c, cIdx) => (
                                <td key={cIdx} className="py-1.5 px-3 text-right tabular-nums">
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
                    <div className="rounded border-l-2 border-[#1E8F5F] bg-[#F4F8FC] p-2.5 font-mono text-xs text-[#0B1F3A] dark:border-[#1E8F5F] dark:bg-[#181a1f] dark:text-neutral-200">
                      <strong>Balance check:</strong> Total Liabilities &amp; Equity − Total Assets ={" "}
                      {stmts.years?.map((y, i) => (
                        <span key={y}>
                          {y}: {fmtStatementNumber(stmts.tie_out?.[y])}
                          {i < (stmts.years?.length || 1) - 1 ? " · " : ""}
                        </span>
                      ))}{" "}
                      (Rp bn) — {stmts.tied ? "neraca seimbang persis di semua kolom" : "selisih pembulatan"}.
                    </div>
                  )}

                  {/* Notes */}
                  {stmts?.notes && stmts.notes.length > 0 && (
                    <div className="space-y-1 text-[11px] text-[#63748A] border-t border-[#D6E2EE] pt-2.5 dark:border-[#262930]">
                      <div className="font-bold uppercase text-[#0B1F3A] dark:text-neutral-300">
                        Catatan metode &amp; keterbatasan data:
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
          <PendingCard label="Laporan keuangan (income statement & balance sheet)" />
        )}
      </section>

      {/* ========================================================================= */}
      {/* BAB 8: ARUS KAS & RASIO KUNCI                                             */}
      {/* ========================================================================= */}
      <section id="cashflow-ratios" className="scroll-mt-28 space-y-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#D6E2EE] pb-2 dark:border-[#262930]">
          <div className="flex items-center gap-2">
            <span className="rounded bg-[#0B1F3A] px-1.5 py-0.5 font-mono text-[10px] font-bold text-[#E4EEF7] dark:bg-[#0B1F3A] dark:text-[#A9C9E8]">
              08
            </span>
            <h2 className="font-sans text-sm font-bold tracking-tight text-[#0B1F3A] dark:text-neutral-100 uppercase">
              Arus Kas &amp; Rasio Kunci // {tk}
            </h2>
          </div>
          <span className="font-mono text-[11px] text-[#63748A]">
            {cf?.sources?.[0] || keyRatio?.sources?.[0] || "Laporan Keuangan & Rasio IDX"}
          </span>
        </div>

        {hasCashflow || hasKeyRatio ? (
          <div className="space-y-4">
            {/* 1. Cash Flow Statement */}
            {hasCashflow && (
              <Card className="rounded-lg border border-[#D6E2EE] bg-white shadow-xs dark:border-[#262930] dark:bg-[#121418]">
                <CardHeader className="border-b border-[#D6E2EE] bg-[#F4F8FC] p-3.5 pb-2.5 dark:border-[#1f2228] dark:bg-[#181a1f]">
                  <div className="flex items-center justify-between">
                    <CardTitle className="font-mono text-xs font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-neutral-100">
                      {finCf?.title || "Cash Flow Statement"}
                    </CardTitle>
                    <span className="font-mono text-[10px] text-[#63748A]">
                      {cf?.sources?.[0] || finCf?.source || "Laporan Keuangan IDX"}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="p-4 space-y-3">
                  <div className="overflow-x-auto rounded border border-[#D6E2EE] font-mono text-xs dark:border-[#262930]">
                    <table className="w-full">
                      <thead>
                        <tr className="bg-[#0B1F3A] text-white text-right text-[11px]">
                          {(cf?.headers || finCf?.headers || ["Pos Arus Kas (Rp bn)", ...(cf?.years || [])]).map((h, i) => (
                            <th key={i} className={`py-2 px-3 ${i === 0 ? "text-left" : ""}`}>
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {/* Sections from cashflow_page */}
                        {cf?.sections?.map((sec, sIdx) => (
                          <React.Fragment key={sIdx}>
                            <tr className="bg-[#F4F8FC] font-bold text-[#0B1F3A] uppercase tracking-wider text-[11px] dark:bg-[#181a1f] dark:text-[#A9C9E8]">
                              <td colSpan={(cf.headers?.length || 5) + 1} className="py-2 px-3">
                                {sec.title}
                              </td>
                            </tr>
                            {sec.rows.map((r, rIdx) => {
                              const isSubtotal = r.kind === "subtotal"
                              return (
                                <tr
                                  key={rIdx}
                                  className={`border-b border-[#D6E2EE]/60 last:border-0 ${
                                    isSubtotal
                                      ? "font-bold text-[#0B1F3A] border-t border-t-[#0B1F3A] dark:text-neutral-100"
                                      : "text-[#0B1F3A] dark:text-neutral-300"
                                  }`}
                                >
                                  <td className="py-1.5 px-3 text-left">
                                    <span className={isSubtotal ? "font-bold" : "font-normal"}>{r.label}</span>
                                    {r.kind === "deduction" && <span className="ml-1 text-[10px] text-[#63748A]">(-)</span>}
                                    {r.note && <span className="ml-1.5 text-[10px] italic text-[#63748A]">{r.note}</span>}
                                  </td>
                                  {r.cells?.map((c, cIdx) => (
                                    <td key={cIdx} className="py-1.5 px-3 text-right tabular-nums">
                                      {fmtStatementNumber(c)}
                                    </td>
                                  ))}
                                </tr>
                              )
                            })}
                          </React.Fragment>
                        ))}

                        {/* Closing Rows from cashflow_page */}
                        {cf?.closing?.map((r, idx) => (
                          <tr
                            key={`closing-${idx}`}
                            className="border-b border-[#D6E2EE]/60 font-bold text-[#0B1F3A] bg-[#F4F8FC] dark:bg-[#181a1f] dark:text-neutral-100"
                          >
                            <td className="py-1.5 px-3 text-left">
                              {r.label}
                              {r.note && <span className="ml-1.5 text-[10px] italic font-normal text-[#63748A]">{r.note}</span>}
                            </td>
                            {r.cells?.map((c, cIdx) => (
                              <td key={cIdx} className="py-1.5 px-3 text-right tabular-nums">
                                {fmtStatementNumber(c)}
                              </td>
                            ))}
                          </tr>
                        ))}

                        {/* Memo Rows from cashflow_page */}
                        {cf?.memo?.map((r, idx) => (
                          <tr
                            key={`memo-${idx}`}
                            className="border-t border-[#0B1F3A] italic font-semibold text-[#0B1F3A] bg-[#E4EEF7]/50 dark:bg-[#0B1F3A]/20 dark:text-[#A9C9E8]"
                          >
                            <td className="py-1.5 px-3 text-left">
                              {r.label}
                              {r.note && <span className="ml-1.5 text-[10px] italic font-normal text-[#63748A]">{r.note}</span>}
                            </td>
                            {r.cells?.map((c, cIdx) => (
                              <td key={cIdx} className="py-1.5 px-3 text-right tabular-nums">
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
                                className={`border-b border-[#D6E2EE]/60 last:border-0 ${
                                  r.kind === "subtotal"
                                    ? "font-bold text-[#0B1F3A] border-t border-t-[#0B1F3A] dark:text-neutral-100"
                                    : "text-[#0B1F3A] dark:text-neutral-300"
                                }`}
                              >
                                <td className="py-1.5 px-3 text-left font-medium">{r.label}</td>
                                {r.cells.map((c, cIdx) => (
                                  <td key={cIdx} className="py-1.5 px-3 text-right tabular-nums">
                                    {fmtStatementNumber(c)}
                                  </td>
                                ))}
                              </tr>
                            ))}
                            {normalizeRows(finCf.footers).map((r, rIdx) => (
                              <tr
                                key={`fin-cf-foot-${rIdx}`}
                                className="border-b border-[#D6E2EE]/60 font-bold text-[#0B1F3A] bg-[#F4F8FC] dark:bg-[#181a1f] dark:text-neutral-100"
                              >
                                <td className="py-1.5 px-3 text-left font-medium">{r.label}</td>
                                {r.cells.map((c, cIdx) => (
                                  <td key={cIdx} className="py-1.5 px-3 text-right tabular-nums">
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
              <Card className="rounded-lg border border-[#D6E2EE] bg-white shadow-xs dark:border-[#262930] dark:bg-[#121418]">
                <CardHeader className="border-b border-[#D6E2EE] bg-[#F4F8FC] p-3.5 pb-2.5 dark:border-[#1f2228] dark:bg-[#181a1f]">
                  <div className="flex items-center justify-between">
                    <CardTitle className="font-mono text-xs font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-neutral-100">
                      {keyRatio?.exhibit_title || finRatios?.title || "Key Ratio (Rasio Kunci & Efisiensi)"}
                    </CardTitle>
                    <span className="font-mono text-[10px] text-[#63748A]">
                      {keyRatio?.sources?.[0] || finRatios?.source || "Sectors — data historis & proyeksi"}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="p-4 space-y-3">
                  <div className="overflow-x-auto rounded border border-[#D6E2EE] font-mono text-xs dark:border-[#262930]">
                    <table className="w-full">
                      <thead>
                        <tr className="bg-[#0B1F3A] text-white text-right text-[11px]">
                          {(keyRatio?.headers || finRatios?.headers || ["Rasio Kunci", ...(keyRatio?.years || [])]).map((h, i) => (
                            <th key={i} className={`py-2 px-3 ${i === 0 ? "text-left" : ""}`}>
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {/* Sections from key_ratio_page */}
                        {keyRatio?.sections?.map((sec, sIdx) => (
                          <React.Fragment key={sIdx}>
                            <tr className="bg-[#F4F8FC] font-bold text-[#0B1F3A] uppercase tracking-wider text-[11px] dark:bg-[#181a1f] dark:text-[#A9C9E8]">
                              <td colSpan={(keyRatio.headers?.length || 5) + 1} className="py-2 px-3">
                                {sec.title}
                              </td>
                            </tr>
                            {sec.rows.map((r, rIdx) => (
                              <tr
                                key={rIdx}
                                className={`border-b border-[#D6E2EE]/60 last:border-0 ${
                                  rIdx % 2 === 1 ? "bg-[#F4F8FC] dark:bg-[#181a1f]" : "bg-white dark:bg-[#121316]"
                                }`}
                              >
                                <td className="py-1.5 px-3 text-left font-medium text-[#0B1F3A] dark:text-neutral-200">
                                  {r.label}
                                  {r.note && <span className="ml-1.5 text-[10px] italic text-[#63748A]">{r.note}</span>}
                                </td>
                                {r.cells?.map((c, cIdx) => (
                                  <td key={cIdx} className="py-1.5 px-3 text-right tabular-nums">
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
                                  className="bg-[#F4F8FC] font-bold text-[#0B1F3A] uppercase tracking-wider text-[11px] dark:bg-[#181a1f] dark:text-[#A9C9E8]"
                                >
                                  <td colSpan={(finRatios.headers?.length || 5) + 1} className="py-2 px-3">
                                    {r.label}
                                  </td>
                                </tr>
                              )
                            }
                            return (
                              <tr
                                key={`fin-ratio-${rIdx}`}
                                className={`border-b border-[#D6E2EE]/60 last:border-0 ${
                                  rIdx % 2 === 1 ? "bg-[#F4F8FC] dark:bg-[#181a1f]" : "bg-white dark:bg-[#121316]"
                                }`}
                              >
                                <td className="py-1.5 px-3 text-left font-medium text-[#0B1F3A] dark:text-neutral-200">
                                  {r.label}
                                </td>
                                {r.cells.map((c, cIdx) => (
                                  <td key={cIdx} className="py-1.5 px-3 text-right tabular-nums">
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

                  {/* Growth Basis Callout Line */}
                  {keyRatio?.growth_basis && Object.keys(keyRatio.growth_basis).length > 0 && (
                    <div className="rounded border-l-2 border-[#0B1F3A] bg-[#F4F8FC] p-2.5 font-mono text-xs text-[#0B1F3A] dark:border-[#A9C9E8] dark:bg-[#181a1f] dark:text-neutral-200">
                      <strong>Basis pertumbuhan tahun awal (FY2024A vs FY2023A):</strong>{" "}
                      {Object.entries(keyRatio.growth_basis)
                        .map(([k, v]) => `${k.toUpperCase()}: ${fmtRatioNumber(v, 1)}%`)
                        .join(" · ")}
                    </div>
                  )}

                  {/* Structured Visual Cards */}
                  {keyRatio && <KeyRatioCharts keyRatio={keyRatio} />}

                  {/* Notes for Cash Flow and Key Ratios */}
                  {((cf?.notes && cf.notes.length > 0) || (keyRatio?.notes && keyRatio.notes.length > 0)) && (
                    <div className="space-y-1 text-[11px] text-[#63748A] border-t border-[#D6E2EE] pt-2.5 dark:border-[#262930]">
                      <div className="font-bold uppercase text-[#0B1F3A] dark:text-neutral-300">
                        Catatan tie-out &amp; keterbatasan data:
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
          <PendingCard label="Arus kas & rasio kunci" />
        )}
      </section>

      {/* ========================================================================= */}
      {/* BAB 9: FAKTOR RISIKO                                                      */}
      {/* ========================================================================= */}
      <section id="risk-factors" className="scroll-mt-28 space-y-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#D6E2EE] pb-2 dark:border-[#262930]">
          <div className="flex items-center gap-2">
            <span className="rounded bg-[#0B1F3A] px-1.5 py-0.5 font-mono text-[10px] font-bold text-[#E4EEF7] dark:bg-[#0B1F3A] dark:text-[#A9C9E8]">
              09
            </span>
            <h2 className="font-sans text-sm font-bold tracking-tight text-[#0B1F3A] dark:text-neutral-100 uppercase">
              Faktor Risiko Utama // {tk}
            </h2>
          </div>
          <span className="font-mono text-[11px] text-[#63748A]">
            Severity &amp; Sensitivitas
          </span>
        </div>

        {risks.length > 0 ? (
          <Card className="rounded-lg border border-[#D6E2EE] bg-white shadow-xs dark:border-[#262930] dark:bg-[#121418]">
            <CardHeader className="border-b border-[#D6E2EE] bg-[#F4F8FC] p-4 pb-3 dark:border-[#1f2228] dark:bg-[#181a1f]">
              <CardTitle className="font-mono text-xs font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-neutral-100">
                Faktor Risiko &amp; Mitigasi Teridentifikasi ({risks.length} Poin)
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 sm:p-5 space-y-3">
              <div className="space-y-3 font-mono">
                {risks.map((r, idx) => (
                  <div
                    key={idx}
                    className="grid grid-cols-[32px_1fr_auto] gap-3 items-start border-t border-[#D6E2EE] pt-3 first:border-0 first:pt-0 dark:border-[#262930]"
                  >
                    {/* Numbering badge */}
                    <span className="text-base font-black text-[#C0392B] dark:text-[#F87171]">
                      {String(idx + 1).padStart(2, "0")}
                    </span>

                    {/* Content */}
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h4 className="text-xs font-bold text-[#0B1F3A] dark:text-neutral-100">
                          {r.bucket}
                        </h4>
                        {r.severity != null && (
                          <span className="rounded bg-[#C0392B]/10 px-1.5 py-0.5 text-[9px] font-bold text-[#C0392B] dark:bg-[#C0392B]/20">
                            SEVERITY: {String(r.severity)}
                          </span>
                        )}
                      </div>
                      <p className="text-xs leading-relaxed text-[#63748A]">
                        {r.detail}
                      </p>
                      {r.source && (
                        <p className="text-[10px] text-[#63748A]/80 italic">
                          Sumber: {r.source}
                        </p>
                      )}
                    </div>

                    {/* Stat Anchor */}
                    {r.stat && (
                      <div className="text-right pl-3 shrink-0">
                        <div className="text-xs font-bold text-[#0B1F3A] tabular-nums dark:text-neutral-100">
                          {r.stat}
                        </div>
                        {r.stat_label && (
                          <div className="text-[9px] uppercase text-[#63748A]">
                            {r.stat_label}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {payload?.risks_note && (
                <div className="text-[11px] text-[#63748A] border-t border-[#D6E2EE] pt-2.5 dark:border-[#262930]">
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
      {/* BAB 10: SUMBER DATA, DAFTAR EXHIBIT & DISKLAIMER                          */}
      {/* ========================================================================= */}
      <section id="sources-disclaimer" className="scroll-mt-28 space-y-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#D6E2EE] pb-2 dark:border-[#262930]">
          <div className="flex items-center gap-2">
            <span className="rounded bg-[#0B1F3A] px-1.5 py-0.5 font-mono text-[10px] font-bold text-[#E4EEF7] dark:bg-[#0B1F3A] dark:text-[#A9C9E8]">
              10
            </span>
            <h2 className="font-sans text-sm font-bold tracking-tight text-[#0B1F3A] dark:text-neutral-100 uppercase">
              Sumber Data, Daftar Exhibit &amp; Disklaimer // {tk}
            </h2>
          </div>
          <span className="font-mono text-[11px] text-[#63748A]">
            Kepatuhan Riset &amp; Transparansi Provenance
          </span>
        </div>

        {/* Exhibits List */}
        {exhibits.length > 0 && (
          <Card className="rounded-lg border border-[#D6E2EE] bg-white shadow-xs dark:border-[#262930] dark:bg-[#121418]">
            <CardHeader className="border-b border-[#D6E2EE] bg-[#F4F8FC] p-3.5 pb-2.5 dark:border-[#1f2228] dark:bg-[#181a1f]">
              <CardTitle className="font-mono text-xs font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-neutral-100">
                Daftar Exhibit Terverifikasi ({exhibits.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-2 font-mono text-xs">
              <div className="grid gap-2 sm:grid-cols-2">
                {exhibits.map((ex, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between rounded border border-[#D6E2EE] bg-[#F4F8FC] p-2 dark:border-[#262930] dark:bg-[#181a1f]"
                  >
                    <span className="font-medium text-[#0B1F3A] dark:text-neutral-200 truncate mr-2">
                      {ex.title}
                    </span>
                    {ex.source && (
                      <span className="text-[10px] text-[#63748A] shrink-0">
                        {ex.source}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Sector Data Overview if present */}
        {sectorData && (
          <Card className="rounded-lg border border-[#D6E2EE] bg-white shadow-xs dark:border-[#262930] dark:bg-[#121418]">
            <CardHeader className="border-b border-[#D6E2EE] bg-[#F4F8FC] p-3.5 pb-2.5 dark:border-[#1f2228] dark:bg-[#181a1f]">
              <div className="flex items-center justify-between">
                <CardTitle className="font-mono text-xs font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-neutral-100">
                  Data Sektoral: {sectorData.subsector || meta?.subsector || meta?.sector || "IDX Sector"}
                </CardTitle>
                <span className="font-mono text-[10px] text-[#63748A]">
                  Source: {sectorData.source || "Sectors Sektoral Engine"}
                </span>
              </div>
            </CardHeader>
            <CardContent className="p-4 space-y-2 font-mono text-xs">
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                {sectorData.growth_forecast_2026 && (
                  <>
                    <div className="rounded border border-[#D6E2EE] bg-[#F4F8FC] p-2 text-center dark:border-[#262930] dark:bg-[#181a1f]">
                      <div className="text-[10px] text-[#63748A]">PROYEKSI REV 2026</div>
                      <div className="font-bold text-[#0B1F3A] tabular-nums mt-0.5 dark:text-neutral-100">
                        {sectorData.growth_forecast_2026.revenue_pct != null
                          ? `${sectorData.growth_forecast_2026.revenue_pct > 0 ? "+" : ""}${sectorData.growth_forecast_2026.revenue_pct}%`
                          : "—"}
                      </div>
                    </div>
                    <div className="rounded border border-[#D6E2EE] bg-[#F4F8FC] p-2 text-center dark:border-[#262930] dark:bg-[#181a1f]">
                      <div className="text-[10px] text-[#63748A]">PROYEKSI EPS 2026</div>
                      <div className="font-bold text-[#0B1F3A] tabular-nums mt-0.5 dark:text-neutral-100">
                        {sectorData.growth_forecast_2026.eps_pct != null
                          ? `${sectorData.growth_forecast_2026.eps_pct > 0 ? "+" : ""}${sectorData.growth_forecast_2026.eps_pct}%`
                          : "—"}
                      </div>
                    </div>
                  </>
                )}
                {sectorData.growth_actual_2025 && (
                  <>
                    <div className="rounded border border-[#D6E2EE] bg-[#F4F8FC] p-2 text-center dark:border-[#262930] dark:bg-[#181a1f]">
                      <div className="text-[10px] text-[#63748A]">AKTUAL REV 2025</div>
                      <div className="font-bold text-[#0B1F3A] tabular-nums mt-0.5 dark:text-neutral-100">
                        {sectorData.growth_actual_2025.revenue_pct != null
                          ? `${sectorData.growth_actual_2025.revenue_pct > 0 ? "+" : ""}${sectorData.growth_actual_2025.revenue_pct}%`
                          : "—"}
                      </div>
                    </div>
                    <div className="rounded border border-[#D6E2EE] bg-[#F4F8FC] p-2 text-center dark:border-[#262930] dark:bg-[#181a1f]">
                      <div className="text-[10px] text-[#63748A]">AKTUAL EPS 2025</div>
                      <div className="font-bold text-[#0B1F3A] tabular-nums mt-0.5 dark:text-neutral-100">
                        {sectorData.growth_actual_2025.eps_pct != null
                          ? `${sectorData.growth_actual_2025.eps_pct > 0 ? "+" : ""}${sectorData.growth_actual_2025.eps_pct}%`
                          : "—"}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Regulatory Disclaimer Block */}
        <div className="rounded-lg border border-[#D6E2EE] bg-[#F4F8FC] p-4 text-xs font-mono space-y-2 dark:border-[#262930] dark:bg-[#121316]">
          <div className="flex items-center gap-2 font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-[#A9C9E8]">
            <FileText className="h-4 w-4 text-[#0B1F3A] dark:text-[#A9C9E8]" />
            <span>INFORMASI, BUKAN SARAN INVESTASI</span>
          </div>
          <p className="leading-relaxed text-[#63748A] dark:text-neutral-300 font-sans">
            Laporan ini dihasilkan oleh sistem multi-agent untuk keperluan informasi dan analisis data pasar modal
            Indonesia. Seluruh output adalah data historis dan agregat — bukan rekomendasi, prediksi, atau saran investasi.
            Keputusan investasi sepenuhnya tanggung jawab pembaca. Selalu lakukan riset mandiri dan konsultasikan dengan
            penasihat keuangan berlisensi sebelum berinvestasi. Performa masa lalu tidak menjamin hasil di masa depan.
            Akurasi data tunduk pada kualitas data sumber.
          </p>
          {meta?.prepared_by && (
            <div className="pt-2 border-t border-[#D6E2EE] text-[11px] text-[#63748A] dark:border-[#262930]">
              Disiapkan oleh {meta.prepared_by} · {meta.date} · Bahasa: {meta.language?.toUpperCase() || "ID"}
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
