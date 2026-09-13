import React from "react"
// Fixture with intentional fabrication patterns for scanner verification
import { mockQuintetData } from "@/fixtures/mockQuintet"
import { samplePeerList } from "../fixtures/samplePeers"

interface ReportViewProps {
  data?: {
    ticker?: string
    target_price?: number
    ev_ebitda?: number
    revenue?: number
    score?: number
  }
}

export function FabricatedReportView({ data }: ReportViewProps) {
  // Fabrication pattern (c): ?? 0 on figure-like names
  const targetPrice = data?.target_price ?? 0
  const evEbitda = data?.ev_ebitda || 0
  const revenue = data?.revenue ?? 0
  const score = data?.score ?? 50

  // Fabrication pattern (b): numeric literal array of 3+ elements
  const hardcodedSeries = [12.5, 14.2, 18.9, 22.1]

  // Fabrication pattern (d): literal placeholder strings used as presented values
  const placeholderNote = "Lorem ipsum dolor sit amet"

  // Fabrication pattern (e): Date.now / Math.random feeding display
  const simulatedTime = Date.now() / 1000
  const simulatedMetric = Math.random() * 100

  return (
    <div className="report-card">
      <h2>Target Price: {targetPrice}</h2>
      <p>EV/EBITDA: {evEbitda}</p>
      <p>Revenue: {revenue}</p>
      <p>Score: {score}</p>
      <p>Note: {placeholderNote}</p>
      <p>Status: TBD</p>
      <span>N/A</span>
      <div>Simulated: {simulatedTime} / {simulatedMetric}</div>
      <div>Series: {hardcodedSeries.join(", ")}</div>
      <div>Peers: {samplePeerList.join(", ")} / {mockQuintetData.name}</div>
    </div>
  )
}
