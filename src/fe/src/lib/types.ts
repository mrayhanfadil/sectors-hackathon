export type ReportArchetype =
  | "pure-oil"          // RATU style: Cepu PSC, single pilar, DCF + EV/EBITDA
  | "conglomerate-sotp" // CDIA style: 4 pilars (Energy/Water/Port/Logistics), DCF + DDM, Revision
  | "infra-recurring"   // MTEL style: Tower/Fiber, Tenancy ratio, Blended 60/40, Historical Bands, ESG, Key Takeaways
  | "bank-ggm"          // BBCA style: GGM (ROE-g)/(CoE-g) fallback, CASA, NIM, Bank Comps
  | "spin-off-sotp"     // ADRO style: AADI Spin-off + Holdco discount, dual DCF+SOTP
  | "standard-dcf"      // Synthetic / General universe coverage

export type RecommendationRating =
  | "BUY"
  | "TRADING BUY"
  | "HOLD"
  | "TRADING SELL"
  | "SELL"

export interface Shareholder {
  name: string
  percentage: number
  isControlling?: boolean
}

export interface EsgScore {
  environmental: number
  social: number
  governance: number
  composite: number
  rating: "AAA" | "AA" | "A" | "BBB" | "BB" | "B" | "CCC"
}

export interface KeyTakeaway {
  bullet: string
  highlight: string
  implication: string
}

export interface ThesisPillar {
  title: string
  thesis: string
  quantitativeMetric: string
  metricLabel: string
}

export interface CatalystQuantified {
  catalystName: string
  effectiveDate: string
  operationalImpact: string
  annualizedFinancialImpact: string
  probability: string
}

export interface SegmentMixItem {
  segment: string
  revenueIdrBn: number
  revenueSharePct: number
  growthYoY: string
  marginEbitdaPct: number
}

export interface DcfScheduleRow {
  period: string
  revenue: number
  ebit: number
  taxRatePct: number
  nopat: number
  deprAmort: number
  capex: number
  deltaWorkingCap: number
  fcff: number
  discountFactor: number
  presentValue: number
}

export interface SotpPillarItem {
  pillar: string
  keyAsset: string
  ebitdaOrMetric: number
  targetMultiple: string
  enterpriseValueBn: number
  equityValueBn: number
  perShareIdr: number
  shareOfNavPct: number
}

export interface HistoricalBandMultiples {
  metricName: string // e.g. "PBV 3Y" or "EV/EBITDA 3Y"
  current: number
  stdPlus2: number
  stdPlus1: number
  average: number
  stdMinus1: number
  stdMinus2: number
  label: "DEEP VALUE" | "BELOW AVG" | "FAIR" | "ABOVE AVG" | "OVERVALUED"
}

export interface BlendedValuationComponent {
  methodology: string
  fairValuePerShare: number
  weightPct: number
  weightedValue: number
  note: string
}

export interface ValuationEngineData {
  primaryTargetPrice: number
  currentPrice: number
  upsidePct: number
  marginOfSafetyPct: number
  waccAssumptions: {
    wacc: number
    beta: number
    riskFreeRate: number
    equityRiskPremium: number
    costOfEquity: number
    costOfDebtAfterTax: number
    weightEquity: number
    weightDebt: number
    terminalGrowth: number
  }
  blendedBreakdown?: BlendedValuationComponent[]
  dcfSchedule?: DcfScheduleRow[]
  sotpPillars?: SotpPillarItem[]
  historicalBands?: HistoricalBandMultiples[]
  ggmMath?: {
    roe: number
    costOfEquity: number
    terminalGrowth: number
    impliedPbv: number
    targetPrice: number
    formula: string
  }
  forecastRevision?: {
    metric: string
    priorForecast: string
    revisedForecast: string
    deltaPct: string
    rationale: string
  }[]
}

export interface OperationalKpiItem {
  metricKey: string
  label: string
  currentValue: string | number
  unit: string
  period: string
  yoyDelta?: string
  qoqDelta?: string
  industryContext?: string
}

export interface FinancialStatementPeriodData {
  period: string
  isActual: boolean
  values: Record<string, number | string>
}

export interface FinancialStatementSection {
  title: string
  unit: string
  periods: string[]
  rows: {
    key: string
    label: string
    isBold?: boolean
    isHeader?: boolean
    indent?: boolean
    values: Record<string, number | string>
  }[]
}

export interface FinancialRatiosGroup {
  groupName: string
  ratios: {
    label: string
    unit: string
    values: Record<string, string | number>
    historicalAverage?: string | number
    benchmark?: string
  }[]
}

export interface PeerCompanyComp {
  ticker: string
  name: string
  marketCapIdrTn: number
  priceIdr: number
  peFY26: number
  pbvFY26: number
  evEbitdaFY26: number
  roePct: number
  ebitdaMarginPct: number
  dividendYieldPct: number
  rating: RecommendationRating
}

export interface RiskBucketItem {
  category: "Commodity & Pricing" | "Operational & Asset" | "Regulatory & Policy" | "Financial & Gearing" | "Market & Competition"
  severity: "HIGH" | "MEDIUM" | "LOW"
  likelihood: "HIGH" | "MEDIUM" | "LOW"
  riskTitle: string
  detail: string
  mitigant: string
}

export interface ExhibitProvenanceItem {
  exhibitNumber: number
  title: string
  sourceOrganization: string
  dataTimestamp: string
}

export interface InstitutionalEquityReport {
  ticker: string
  name: string
  sector: string
  subsector: string
  archetype: ReportArchetype
  recommendation: RecommendationRating
  targetPrice: number
  currentPrice: number
  upsidePct: number
  previousTargetPrice?: number
  marketCapIdrTn: number
  sharesOutstandingBn: number
  freeFloatPct: number
  turnoverAdtvIdrBn: number
  indexInclusion: string[]
  coverageDate: string
  leadAnalyst: {
    name: string
    title: string
    email: string
  }
  esgScore: EsgScore
  shareholders: Shareholder[]
  keyTakeaways: KeyTakeaway[]
  executiveThesis: {
    narrative: string
    pillars: ThesisPillar[]
    catalystQuantified?: CatalystQuantified
  }
  segmentMix?: SegmentMixItem[]
  priceVsJciHistory: {
    date: string
    stockNormalized: number
    jciNormalized: number
    stockPrice: number
    jciIndex: number
    volume: number
  }[]
  valuation: ValuationEngineData
  operationalKpis: OperationalKpiItem[]
  financialStatements: {
    incomeStatement: FinancialStatementSection
    balanceSheet: FinancialStatementSection
    cashFlowStatement: FinancialStatementSection
  }
  financialRatios: FinancialRatiosGroup[]
  peerComps: PeerCompanyComp[]
  risks: RiskBucketItem[]
  exhibits: ExhibitProvenanceItem[]
}

export interface JciScenario {
  scenario: "Bull" | "Base" | "Bear"
  targetIndex: number
  peMultiple: number
  epsGrowthPct: number
  impliedUpsidePct: number
  coreDrivers: string
}

export interface SectorAllocationCall {
  sectorName: string
  stance: "OVERWEIGHT" | "NEUTRAL" | "UNDERWEIGHT"
  allocationWeightPct: number
  topPicks: string[]
  keyDrivers: string
  catalysts: string
}

export interface TopPickStock {
  ticker: string
  name: string
  sector: string
  marketCapTier: "Large Cap" | "SMID"
  targetPrice: number
  currentPrice: number
  upsidePct: number
  targetPeMultiple: number
  keyInvestmentThesis: string
  keyCatalyst: string
}

export interface MacroThematic {
  number: number
  themeTitle: string
  subtitle: string
  coreNarrative: string
  beneficiarySectors: string[]
  keyDataPoints: { label: string; value: string }[]
}

export interface MarketOutlookData {
  reportDate: string
  title: string
  themeTagline: string
  jciScenarios: JciScenario[]
  valuationMethodologyNote: string
  sectorAllocations: SectorAllocationCall[]
  topPicks: TopPickStock[]
  thematics: MacroThematic[]
  marketFlows: {
    foreignOwnershipPct: number
    foreignYtdNetFlowUsdBn: number
    retailAdtvSharePct: number
    danantaraDryPowderUsdBn: number
    msciFreeFloatRiskNotice: string
  }
}

export interface DebateTurn {
  role: "challenger" | "defender" | "arbiter"
  speakerName: string
  timestamp: string
  message: string
  evidenceCitations?: {
    type: "exhibit" | "filing" | "calculation" | "news"
    reference: string
  }[]
  verdict?: "DEFENDED_WITH_EVIDENCE" | "CONCEDED_AND_ADJUSTED" | "ARBITER_REJECTED"
}

export interface RedTeamDebateThread {
  debateId: string
  ticker: string
  topic: string
  initialChallengerClaim: string
  roundCount: number
  status: "RESOLVED" | "CONCEDED" | "UNDER_REVIEW"
  turns: DebateTurn[]
  scorecard: {
    evidenceGroundingScore: number
    sycophancyRiskScore: number
    modelIntegrityVerified: boolean
  }
}

export interface SocialMention {
  platform: "X / Twitter" | "Reddit" | "Stockbit"
  author: string
  timestamp: string
  content: string
  sentiment: "BULLISH" | "BEARISH" | "NEUTRAL"
  engagement: string
  url: string
}

export interface RetailSentimentData {
  ticker: string
  name: string
  compositeScore: number
  sentimentLabel: "Extreme Fear" | "Bearish" | "Neutral" | "Bullish" | "Euphoria"
  mentionsCount30d: number
  sentimentVelocity: string
  divergenceAlert?: {
    isDivergent: boolean
    type: "RETAIL_EUPHORIA_OVERPRICED" | "CONTRARIAN_OPPORTUNITY" | "ALIGNED"
    description: string
  }
  topNarratives: {
    rank: number
    title: string
    summary: string
    sentimentScore: number
    channels: string[]
  }[]
  timelineEvolution: {
    date: string
    sentimentScore: number
    stockPrice: number
    keyEvent: string
  }[]
  platformBreakdown: {
    platform: string
    sentimentScore: number
    volumeSharePct: number
    samplePost: SocialMention
  }[]
}
