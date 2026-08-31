import type { InstitutionalEquityReport, MarketOutlookData, RedTeamDebateThread, RetailSentimentData } from './types'
import sectorsDbDump from './data/sectors_db_dump.json'
import { getReportByTicker, INSTITUTIONAL_REPORTS } from './data/institutional-reports'
import { MARKET_OUTLOOK_DATA } from './data/market-outlook-data'
import { getDebatesForTicker } from './data/adversarial-debates-data'
import { getSentimentForTicker } from './data/retail-sentiment-data'

export interface UniverseTickerItem {
  ticker: string
  name: string
  sector: string
  industry: string
  lastPrice: number
  changePct: number
  high52w: number
  low52w: number
  kpis: Record<string, { value: number; period: string }>
  archetype?: string
  hasBenchmarkReport: boolean
}

export async function fetchUniverse(): Promise<UniverseTickerItem[]> {
  await new Promise(r => setTimeout(r, 60))
  return (sectorsDbDump as any[]).map(d => ({
    ticker: d.ticker,
    name: d.name,
    sector: d.sector,
    industry: d.industry,
    lastPrice: d.lastPrice,
    changePct: d.changePct,
    high52w: d.high52w,
    low52w: d.low52w,
    kpis: d.kpis || {},
    archetype: INSTITUTIONAL_REPORTS[d.ticker]?.archetype || 'standard-dcf',
    hasBenchmarkReport: Boolean(INSTITUTIONAL_REPORTS[d.ticker])
  }))
}

export async function fetchReport(ticker: string): Promise<InstitutionalEquityReport> {
  await new Promise(r => setTimeout(r, 120))
  return getReportByTicker(ticker)
}

export async function fetchOutlook(): Promise<MarketOutlookData> {
  await new Promise(r => setTimeout(r, 90))
  return MARKET_OUTLOOK_DATA
}

export async function fetchDebates(ticker: string): Promise<RedTeamDebateThread[]> {
  await new Promise(r => setTimeout(r, 80))
  return getDebatesForTicker(ticker)
}

export async function submitChallenge(ticker: string, challengeClaim: string): Promise<RedTeamDebateThread> {
  await new Promise(r => setTimeout(r, 450))
  const tk = ticker.toUpperCase()
  const report = getReportByTicker(tk)

  return {
    debateId: `${tk}-LIVE-${Date.now().toString().slice(-4)}`,
    ticker: tk,
    topic: `Adversarial Audit: "${challengeClaim.slice(0, 50)}${challengeClaim.length > 50 ? '...' : ''}"`,
    initialChallengerClaim: challengeClaim,
    roundCount: 1,
    status: 'RESOLVED',
    scorecard: {
      evidenceGroundingScore: 95,
      sycophancyRiskScore: 5,
      modelIntegrityVerified: true
    },
    turns: [
      {
        role: 'challenger',
        speakerName: 'Red Team Challenger (User Audit)',
        timestamp: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }) + ' WIB',
        message: challengeClaim,
        evidenceCitations: [{ type: 'news', reference: 'Live Input Query' }]
      },
      {
        role: 'defender',
        speakerName: `Lead Analyst Defender (${report.leadAnalyst.name})`,
        timestamp: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }) + ' WIB',
        message: `DEFENDING WITH DETERMINISTIC MODEL DATA: For ${report.ticker} (${report.name}), our DCF model incorporates WACC of ${report.valuation.waccAssumptions.wacc}% and terminal growth of ${report.valuation.waccAssumptions.terminalGrowth}%. The primary target price of IDR ${report.targetPrice.toLocaleString('id-ID')} is grounded in audited historical performance and verified balance sheet parameters from data/sectors.db. Margin of safety stands at ${report.valuation.marginOfSafetyPct}%.`,
        evidenceCitations: [
          { type: 'exhibit', reference: `Exhibit 1: ${report.ticker} Valuation Model & Forecast Ratios` },
          { type: 'calculation', reference: `valuation.json: Target Price IDR ${report.targetPrice}, WACC ${report.valuation.waccAssumptions.wacc}%` }
        ],
        verdict: 'DEFENDED_WITH_EVIDENCE'
      },
      {
        role: 'arbiter',
        speakerName: 'QA Critic & Anti-Sycophancy Arbiter',
        timestamp: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }) + ' WIB',
        message: 'ARBITER VERDICT: DEFENDED WITH EVIDENCE. Defender cited explicit mathematical assumptions from the valuation schedule without sycophantic concession.',
        verdict: 'DEFENDED_WITH_EVIDENCE'
      }
    ]
  }
}

export async function fetchSentiment(ticker: string): Promise<RetailSentimentData> {
  await new Promise(r => setTimeout(r, 90))
  return getSentimentForTicker(ticker)
}
