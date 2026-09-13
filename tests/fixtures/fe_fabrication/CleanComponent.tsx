import React from "react"
import type { ReportPayload } from "@/lib/reportPayload"
import { formatIdn, PendingBlock } from "@/components/report/charts/tokens"

interface CleanReportViewProps {
  payload?: ReportPayload
}

export function CleanReportView({ payload }: CleanReportViewProps) {
  const valuation = payload?.valuation as Record<string, unknown> | undefined
  const targetPrice = typeof valuation?.target_price === "number" ? valuation.target_price : null

  if (targetPrice === null) {
    return <PendingBlock label="Target Price" message="belum tersedia di payload." />
  }

  return (
    <div className="report-clean">
      <h2>Target Price: Rp {formatIdn(targetPrice, 0)}</h2>
    </div>
  )
}
