import type { MarketOutlookData } from '../types'

export const MARKET_OUTLOOK_DATA: MarketOutlookData = {
  reportDate: '2026-08-31',
  title: 'Indonesia Equity Strategy 2026: Return of Animal Spirits',
  themeTagline: 'Danantara Dry Powder, Consumption Rebound & MSCI Adjusted Free Float Dynamic',
  jciScenarios: [
    {
      scenario: 'Bear',
      targetIndex: 7800,
      peMultiple: 13.5,
      epsGrowthPct: 4.0,
      impliedUpsidePct: -0.6,
      coreDrivers: 'Prolonged global high interest rates, commodity slump, foreign capital outflow acceleration, fiscal deficit expansion beyond 3.0%.'
    },
    {
      scenario: 'Base',
      targetIndex: 9100,
      peMultiple: 15.0,
      epsGrowthPct: 8.0,
      impliedUpsidePct: 15.9,
      coreDrivers: 'J.P. Morgan Benchmark Base Case: 8.0% EPS growth x flat 15.0x P/E multiple. Danantara initial US$1.5bn deployment, domestic consumption recovery, stable rupiah.'
    },
    {
      scenario: 'Bull',
      targetIndex: 10000,
      peMultiple: 16.5,
      epsGrowthPct: 12.5,
      impliedUpsidePct: 27.4,
      coreDrivers: 'Aggressive sovereign fund Danantara re-rating across 9 priority sectors, foreign ownership reversal from multi-decade 44% underweight, aggressive BI rate cuts (-75 bps).'
    }
  ],
  valuationMethodologyNote: 'Methodology: Index Fair Value = Normalized EPS (IDR 606.7) x Target P/E Multiple (15.0x base). Benchmark: J.P. Morgan Indonesia Strategy (Henry Wibowo et al.) + Maybank IBG 74p strategy pack.',
  sectorAllocations: [
    {
      sectorName: 'Industrials',
      stance: 'OVERWEIGHT',
      allocationWeightPct: 22.0,
      topPicks: ['ASII', 'JSMR', 'UNTR'],
      keyDrivers: 'Manufacturing capex rebound, automotive volume recovery, toll road tariff adjustments.',
      catalysts: 'Danantara infrastructure asset consolidation, electric vehicle supply chain policy incentives.'
    },
    {
      sectorName: 'Materials & Metals',
      stance: 'OVERWEIGHT',
      allocationWeightPct: 18.0,
      topPicks: ['ANTM', 'MDKA', 'INCO', 'HRTA'],
      keyDrivers: 'Global copper/gold secular bull cycle, downstream nickel RKEF to HPAL transition.',
      catalysts: 'Domestic bullion bank launch, global supply tightness in critical green transition metals.'
    },
    {
      sectorName: 'Consumer Staples & Discretionary',
      stance: 'OVERWEIGHT',
      allocationWeightPct: 20.0,
      topPicks: ['ICBP', 'MYOR', 'MAPI', 'ACES'],
      keyDrivers: 'Provincial minimum wage uplift (+6.5%), social assistance distribution, election liquidity spillover.',
      catalysts: 'Lower soft commodity input costs (wheat, CPO, packaging) driving gross margin expansion.'
    },
    {
      sectorName: 'Property & Industrial Estates',
      stance: 'OVERWEIGHT',
      allocationWeightPct: 10.0,
      topPicks: ['PWON', 'CTRA', 'SMRA'],
      keyDrivers: 'Government 100% PPN DTP property tax exemption extension, FDI industrial land demand in Batang & Subang.',
      catalysts: 'Mortgage rate easing cycle initiating in 2H26 as Bank Indonesia trims 7-Day Reverse Repo rate.'
    },
    {
      sectorName: 'Financials & Banking',
      stance: 'NEUTRAL',
      allocationWeightPct: 18.0,
      topPicks: ['BBCA', 'BMRI', 'BRIS'],
      keyDrivers: 'Loan growth expanding +10-12% YoY, exceptional asset quality offset by slight NIM compression on deposit repricing.',
      catalysts: 'Higher dividend payout ratios (BBRI/BMRI 70-80%), digital transaction fee revenue expansion.'
    },
    {
      sectorName: 'Telecommunication & Infra',
      stance: 'NEUTRAL',
      allocationWeightPct: 8.0,
      topPicks: ['MTEL', 'ISAT', 'TLKM'],
      keyDrivers: 'Telco market consolidation (PST & UMT merger) elevating ARPUs and colocation demand, fiberization scale.',
      catalysts: 'Spectrum 700MHz & 2.6GHz auction completion unlocking 3,500+ new tower tenancies.'
    },
    {
      sectorName: 'Energy & Thermal Coal',
      stance: 'UNDERWEIGHT',
      allocationWeightPct: 4.0,
      topPicks: ['ADRO', 'RATU'],
      keyDrivers: 'Newcastle thermal coal price normalization towards $110-120/t, rising environmental DMO compliance costs.',
      catalysts: 'Select high-dividend special payouts and demerger value unlocking (AADI spin-off).'
    }
  ],
  topPicks: [
    {
      ticker: 'BBCA',
      name: 'Bank Central Asia Tbk.',
      sector: 'Financials',
      marketCapTier: 'Large Cap',
      targetPrice: 9600,
      currentPrice: 7890,
      upsidePct: 21.9,
      targetPeMultiple: 17.5,
      keyInvestmentThesis: 'Pristine 81.2% CASA funding moat, zero asset quality concern (1.8% NPL), GGM valuation target.',
      keyCatalyst: 'Transactional fee income acceleration and foreign inflow benchmark proxy.'
    },
    {
      ticker: 'MTEL',
      name: 'Dayamitra Telekomunikasi Tbk.',
      sector: 'Infrastructures',
      marketCapTier: 'Large Cap',
      targetPrice: 635,
      currentPrice: 460,
      upsidePct: 38.0,
      targetPeMultiple: 14.5,
      keyInvestmentThesis: 'Deep-value recurring cash flow compounder at 8.47x EV/EBITDA, tenancy ratio 1.57x, 59k km fiber.',
      keyCatalyst: 'PST & UMT merger + 700MHz spectrum refarming adding +IDR 420bn annualized recurring revenue.'
    },
    {
      ticker: 'ASII',
      name: 'Astra International Tbk.',
      sector: 'Industrials',
      marketCapTier: 'Large Cap',
      targetPrice: 6200,
      currentPrice: 5200,
      upsidePct: 19.2,
      targetPeMultiple: 8.5,
      keyInvestmentThesis: 'Hybrid EV model launches stabilizing 4W market share at 53%, massive 7.5% dividend yield.',
      keyCatalyst: 'UNTR gold/nickel mining contribution expanding non-auto EBITDA to 45%.'
    },
    {
      ticker: 'ICBP',
      name: 'Indofood CBP Sukses Makmur Tbk.',
      sector: 'Consumer Staples',
      marketCapTier: 'Large Cap',
      targetPrice: 13500,
      currentPrice: 11200,
      upsidePct: 20.5,
      targetPeMultiple: 15.8,
      keyInvestmentThesis: 'Pinehill Middle East FX debt headwinds fully digested; domestic instant noodle volume +5% YoY.',
      keyCatalyst: 'Wheat and CPO commodity price declines expanding gross margins by 220 bps.'
    },
    {
      ticker: 'ANTM',
      name: 'Aneka Tambang Tbk.',
      sector: 'Materials',
      marketCapTier: 'Large Cap',
      targetPrice: 1850,
      currentPrice: 1480,
      upsidePct: 25.0,
      targetPeMultiple: 16.0,
      keyInvestmentThesis: 'Direct beneficiary of domestic physical gold retail demand and EV battery supply chain JV integration.',
      keyCatalyst: 'National Bullion Bank mandate implementation granting official market maker status.'
    },
    {
      ticker: 'ISAT',
      name: 'Indosat Ooredoo Hutchison Tbk.',
      sector: 'Telecommunication',
      marketCapTier: 'SMID',
      targetPrice: 12500,
      currentPrice: 10400,
      upsidePct: 20.2,
      targetPeMultiple: 18.0,
      keyInvestmentThesis: 'Industry-leading ARPU expansion (+8.2% YoY) post 3-to-4 network integration completion.',
      keyCatalyst: 'GPU-as-a-Service sovereign AI cloud enterprise revenue scaling with BDx data centers.'
    },
    {
      ticker: 'PWON',
      name: 'Pakuwon Jati Tbk.',
      sector: 'Property',
      marketCapTier: 'SMID',
      targetPrice: 540,
      currentPrice: 430,
      upsidePct: 25.6,
      targetPeMultiple: 9.8,
      keyInvestmentThesis: 'Dominant retail mall recurring revenue (68% of total) providing inflation-hedged dividend stability.',
      keyCatalyst: 'New mall expansions in Bekasi and Semarang reaching 90%+ occupancy.'
    }
  ],
  thematics: [
    {
      number: 1,
      themeTitle: 'Consumption Engine Recovery',
      subtitle: 'Minimum Wage Uplift, Discretionary Purchasing Power & Fiscal Aid',
      coreNarrative: 'Indonesian private consumption is experiencing a decisive inflection point supported by 6.5% provincial minimum wage increases, extended social assistance disbursements, and cooling inflation at 2.1%. Retail footfall in Tier-2 and Tier-3 regional centers is outpacing Tier-1 metropolitan areas.',
      beneficiarySectors: ['Consumer Staples', 'Retail Discretionary', 'Automotive & 2-Wheelers', 'Fintech & Consumer Credit'],
      keyDataPoints: [
        { label: 'Minimum Wage Hike', value: '+6.5% average across 38 provinces' },
        { label: 'Headline CPI Inflation', value: '2.1% YoY (comfortably within BI band)' },
        { label: 'Consumer Confidence Index', value: '124.8 (highest in 14 months)' }
      ]
    },
    {
      number: 2,
      themeTitle: 'Danantara Sovereign Fund Value-Up',
      subtitle: 'US$12 Bn Dry Powder Orchestrating SOE Re-Rating',
      coreNarrative: 'The establishment of Badan Pengelola Investasi Danantara (BPI Danantara) marks a structural shift in Indonesian state asset management, separating sovereign wealth investment (DIM) from state holding execution (DAM). With initial dry powder exceeding US$12 Bn (0.8% GDP) and targeting >US$14 Bn, Danantara focuses on capital efficiency and return-on-equity re-rating across 9 strategic economic pillars.',
      beneficiarySectors: ['State-Owned Enterprises', 'Infrastructure & Utilities', 'Renewable Energy', 'Strategic Metals'],
      keyDataPoints: [
        { label: 'Initial Dry Powder', value: 'US$ 12.0 Bn allocated capital' },
        { label: 'SOE ex-Banks YTD Performance', value: '+25% valuation multiple re-rating' },
        { label: 'Priority Focus Sectors', value: '9 National Strategic Economic Corridors' }
      ]
    },
    {
      number: 3,
      themeTitle: 'Foreign Ownership Reversal & MSCI Risk Arbitrage',
      subtitle: '44% Multi-Decade Underweight Position Nearing Inflow Inflection',
      coreNarrative: 'Foreign institutional ownership in Indonesian equities sits at historic lows of ~44% (vs 62% in 2013). While MSCI adjusted free float updates create temporary volatility in selected index heavyweights, fundamental valuation discounts (12.8x trailing P/E vs 10Y mean of 15.6x) create asymmetric risk-reward for active foreign allocators.',
      beneficiarySectors: ['Large-Cap Index Heavyweights', 'Liquid Banking Champions', 'ESG AAA Leaders'],
      keyDataPoints: [
        { label: 'Foreign Institutional Ownership', value: '44.2% (multi-decade underweight)' },
        { label: '2-Year Cumulative Net Outflow', value: '-US$ 2.6 Bn potential reversal pool' },
        { label: 'IDX Retail ADTV Participation', value: '58% (anchoring domestic liquidity)' }
      ]
    },
    {
      number: 4,
      themeTitle: 'Monetary Easing & Rate Sensitivity',
      subtitle: 'Bank Indonesia Easing Cycle Unlocking Leveraged Sectors',
      coreNarrative: 'With the Federal Reserve and Bank Indonesia commencing policy rate reductions, rate-sensitive domestic cyclical sectors (Property, Telco Infrastructure, Auto Finance) are primed for earnings upgrades via lower borrowing costs and mortgage demand expansion.',
      beneficiarySectors: ['Property & Industrial Estates', 'Tower & Fiber Infrastructure', 'Banking SME Book'],
      keyDataPoints: [
        { label: 'BI 7-Day Rate Trajectory', value: 'Target 5.50% by year-end (-75 bps)' },
        { label: 'USD/IDR Exchange Target', value: 'IDR 15,400 - 15,700 band stability' },
        { label: '10Y IndoGov Bond Yield', value: '6.45% (down 55 bps from peak)' }
      ]
    },
    {
      number: 5,
      themeTitle: 'Total Shareholder Return (TSR) & Dividend Culture',
      subtitle: 'Corporate Governance Reform Triggering Payout Expansion',
      coreNarrative: 'Indonesian listed corporate management teams are increasingly adopting formal dividend payout and share repurchase policies to compete for institutional global capital. Cash-rich miners, state-owned banks, and telecom utilities are leading total shareholder return league tables.',
      beneficiarySectors: ['Commercial Banking', 'Thermal Coal & Energy', 'Telecommunication Towers'],
      keyDataPoints: [
        { label: 'Average Top-20 Dividend Yield', value: '6.2% annualized cash yield' },
        { label: 'Corporate Share Buybacks', value: 'IDR 14.5 Tn approved YTD' },
        { label: 'Average Payout Ratio (Big 4 Banks)', value: '68.5% of net recurring earnings' }
      ]
    }
  ],
  marketFlows: {
    foreignOwnershipPct: 44.2,
    foreignYtdNetFlowUsdBn: -2.2,
    retailAdtvSharePct: 58.0,
    danantaraDryPowderUsdBn: 12.0,
    msciFreeFloatRiskNotice: 'MSCI May 2026 Free Float Review: Monitoring conglomerate cross-holding adjustments. Capital shifts favor liquid single-pilar pure plays with transparent shareholder registers (BBCA, MTEL, ICBP).'
  }
}
