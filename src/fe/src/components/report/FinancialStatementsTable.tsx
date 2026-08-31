import * as React from "react"
import type { FinancialStatementSection } from "@/lib/types"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { FileText } from "lucide-react"

interface FinancialStatementsTableProps {
  incomeStatement: FinancialStatementSection
  balanceSheet: FinancialStatementSection
  cashFlowStatement: FinancialStatementSection
}

export function FinancialStatementsTable({
  incomeStatement,
  balanceSheet,
  cashFlowStatement,
}: FinancialStatementsTableProps) {
  const [activeTab, setActiveTab] = React.useState<"income" | "balance" | "cashflow">("income")

  const currentSection =
    activeTab === "income"
      ? incomeStatement
      : activeTab === "balance"
      ? balanceSheet
      : cashFlowStatement

  return (
    <Card className="border-[#262d3a] bg-[#111317]">
      <CardHeader className="pb-2 border-b border-[#1d222c]">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-amber-400" />
            <CardTitle className="text-sm font-semibold text-slate-100">
              6-Year Financial Exhibits (2023A – 2028F)
            </CardTitle>
          </div>

          {/* Statement Tab Switcher */}
          <div className="flex rounded-md bg-[#161a22] p-0.5 border border-[#232936] text-xs font-mono">
            <button
              onClick={() => setActiveTab("income")}
              className={`px-3 py-1 rounded transition-colors cursor-pointer ${
                activeTab === "income"
                  ? "bg-amber-500 text-black font-bold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Income Statement
            </button>
            <button
              onClick={() => setActiveTab("balance")}
              className={`px-3 py-1 rounded transition-colors cursor-pointer ${
                activeTab === "balance"
                  ? "bg-amber-500 text-black font-bold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Balance Sheet
            </button>
            <button
              onClick={() => setActiveTab("cashflow")}
              className={`px-3 py-1 rounded transition-colors cursor-pointer ${
                activeTab === "cashflow"
                  ? "bg-amber-500 text-black font-bold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Cash Flow
            </button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-2">
        <div className="overflow-x-auto">
          <table className="w-full text-xs font-sans">
            <thead>
              <tr className="border-b border-[#212631] text-slate-400 font-mono text-[11px] text-right">
                <th className="pb-2 text-left font-medium">Line Item ({currentSection.unit})</th>
                {currentSection.periods.map((p) => (
                  <th key={p} className="pb-2 font-medium">
                    {p}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#181c24] font-mono text-[11px]">
              {currentSection.rows.map((row) => {
                const isHeader = row.isHeader
                const isBold = row.isBold
                return (
                  <tr
                    key={row.key}
                    className={`hover:bg-[#161a22] ${
                      isHeader ? "bg-[#161920] font-bold text-amber-300" : ""
                    }`}
                  >
                    <td
                      className={`py-2 text-left ${
                        row.indent ? "pl-4 text-slate-400" : isBold ? "font-semibold text-white" : "text-slate-300"
                      }`}
                    >
                      {row.label}
                    </td>
                    {currentSection.periods.map((p) => {
                      const val = row.values[p]
                      return (
                        <td
                          key={p}
                          className={`py-2 text-right ${
                            isBold ? "font-bold text-slate-100" : "text-slate-300"
                          }`}
                        >
                          {typeof val === "number" ? val.toLocaleString("id-ID") : val || "—"}
                        </td>
                      )
                    })}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
