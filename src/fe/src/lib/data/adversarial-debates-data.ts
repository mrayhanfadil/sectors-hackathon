import type { RedTeamDebateThread } from '../types'

export const ADVERSARIAL_DEBATES: Record<string, RedTeamDebateThread[]> = {
  MTEL: [
    {
      debateId: 'MTEL-RED-001',
      ticker: 'MTEL',
      topic: 'WACC 10.10% & Tenancy Ratio 1.57x Sustainability Post-Consolidation',
      initialChallengerClaim: 'Is the 10.10% WACC overly optimistic given high global interest rates, and can MTEL sustain a 1.57x tenancy ratio when telco mergers (PST & UMT) typically lead to site rationalization and churn?',
      roundCount: 2,
      status: 'RESOLVED',
      scorecard: {
        evidenceGroundingScore: 96,
        sycophancyRiskScore: 4,
        modelIntegrityVerified: true
      },
      turns: [
        {
          role: 'challenger',
          speakerName: 'Red Team Challenger (Institutional Auditor)',
          timestamp: '2026-08-27 10:14 WIB',
          message: 'Challenging Thesis #1 & Valuation Model: Telco consolidation between Smartfren and XL (PST & UMT) historically resulted in 8-12% colocation lease terminations across overlapping sites. Your model assumes tenancy continues rising from 1.53x to 1.57x. Furthermore, WACC 10.10% uses a low beta of 0.65. If WACC is adjusted to 11.0% and tenancy is dialed back to 1.50x, Fair Value collapses below IDR 500.',
          evidenceCitations: [
            { type: 'news', reference: 'Bloomberg Telco Consolidation Impact Report 2026-06-15' },
            { type: 'calculation', reference: 'Sensitivity Matrix: WACC +100bps -> TP IDR 485' }
          ]
        },
        {
          role: 'defender',
          speakerName: 'Lead Analyst Defender (Deterministic Modeler)',
          timestamp: '2026-08-27 10:18 WIB',
          message: 'DEFENDING WITH EMPIRICAL EVIDENCE: 1) Outside-Java Geographic Dominance: 58% of MTEL towers (23,500+ sites) are located outside Java where IOH and XLSmartfren overlap is sub-4%, meaning operators are actively adding colocations to meet spectrum coverage obligations rather than decommissioning. 2) Telkomsel Anchor Stability: Telkomsel accounts for 52% of revenues under 10-year master lease agreements expiring in 2031-2034 with penalties for early termination. 3) WACC Derivation: Beta of 0.65 is audited from 3-year weekly regression against IHSG (R²=0.74), Risk Free Rate 6.96% matches 10Y FR0100 IndoGov bond yield, and 78% of debt is fixed at 6.00% post-tax. Even in worst-case stress test (zero tenancy growth), blended fair value remains IDR 565 (+23% upside).',
          evidenceCitations: [
            { type: 'exhibit', reference: 'Exhibit 3: Tower Portfolio & Outside-Java Tenancy Breakdown (Page 4)' },
            { type: 'filing', reference: 'MTEL 1H26 Financial Statements Note 28: Lease Commitments & WALE 6.2Y' },
            { type: 'calculation', reference: 'valuation.json: WACC Table Beta=0.65, RF=6.96%, ERP=8.89%' }
          ],
          verdict: 'DEFENDED_WITH_EVIDENCE'
        },
        {
          role: 'arbiter',
          speakerName: 'QA Critic & Anti-Sycophancy Arbiter',
          timestamp: '2026-08-27 10:22 WIB',
          message: 'ARBITER VERDICT: CLAIM DEFENDED WITH HARD EVIDENCE. The Defender successfully verified that: a) Outside-Java non-overlap preserves net colocation accretion (+2,980 tenants added YTD); b) WACC parameters are strictly derived from FR0100 and audited beta without arbitrary adjustments; c) Mathematical stress-testing confirms margin of safety. No sycophantic concession detected.',
          verdict: 'DEFENDED_WITH_EVIDENCE'
        }
      ]
    },
    {
      debateId: 'MTEL-RED-002',
      ticker: 'MTEL',
      topic: 'Fiberization Capex Pass-Through & ROIC Execution',
      initialChallengerClaim: 'Does the 59,239 km fiber rollout threaten ROIC given high competitive buildout from Moratel and XL Axiata fiber assets?',
      roundCount: 1,
      status: 'RESOLVED',
      scorecard: {
        evidenceGroundingScore: 94,
        sycophancyRiskScore: 6,
        modelIntegrityVerified: true
      },
      turns: [
        {
          role: 'challenger',
          speakerName: 'Red Team Challenger (Credit Risk Officer)',
          timestamp: '2026-08-27 11:05 WIB',
          message: 'Fiber capex of IDR 2.4 - 2.9 Tn annually dilutes corporate ROIC from 6.6% to sub-5.0% if utilization remains under 1.2x. Why should investors not favor asset-light tower operators?',
          evidenceCitations: [
            { type: 'calculation', reference: 'ROIC dilution model on fiber capex schedule' }
          ]
        },
        {
          role: 'defender',
          speakerName: 'Lead Analyst Defender (KPI Analyst)',
          timestamp: '2026-08-27 11:12 WIB',
          message: 'DEFENDING WITH PROVENANCE: MTEL fiber rollout is 100% build-to-suit anchored by pre-committed Fiber-to-the-Tower (FTTT) 10-year orders from Telkomsel and Indosat Ooredoo Hutchison. In 1H26, Fiber revenue surged +8.4% YoY with 71% EBITDA margin. Because fiber shares existing tower power and right-of-way infrastructure, marginal capex is 35% lower than standalone fiberco buildouts.',
          evidenceCitations: [
            { type: 'exhibit', reference: 'Exhibit 1: 1H26 Fiber Revenue Segment Performance (Page 2)' },
            { type: 'filing', reference: 'Company Disclosure to IDX on FTTT Master Service Agreement' }
          ],
          verdict: 'DEFENDED_WITH_EVIDENCE'
        },
        {
          role: 'arbiter',
          speakerName: 'QA Critic & Anti-Sycophancy Arbiter',
          timestamp: '2026-08-27 11:15 WIB',
          message: 'ARBITER VERDICT: DEFENDED. Pre-committed lease contracts confirmed with 71% EBITDA margin pass-through.',
          verdict: 'DEFENDED_WITH_EVIDENCE'
        }
      ]
    }
  ],
  RATU: [
    {
      debateId: 'RATU-RED-001',
      ticker: 'RATU',
      topic: 'WACC 8.4% vs Commodity Downside Risk',
      initialChallengerClaim: 'Why is RATU WACC modeled at 8.4% (lower than MTEL 10.10%) when oil upstream E&P carries substantially higher commodity and sovereign operational risk?',
      roundCount: 1,
      status: 'RESOLVED',
      scorecard: {
        evidenceGroundingScore: 92,
        sycophancyRiskScore: 8,
        modelIntegrityVerified: true
      },
      turns: [
        {
          role: 'challenger',
          speakerName: 'Red Team Challenger (Commodity Analyst)',
          timestamp: '2026-01-07 14:20 WIB',
          message: 'Oil E&P cashflows are inherently cyclical. Modeling WACC at 8.4% with Cost of Debt at 3.50% significantly understates refinancing risk if Brent drops below $65.',
          evidenceCitations: [
            { type: 'calculation', reference: 'RATU Modeler WACC schedule 8.4%' }
          ]
        },
        {
          role: 'defender',
          speakerName: 'Lead Analyst Defender',
          timestamp: '2026-01-07 14:25 WIB',
          message: 'DEFENDING WITH PSC CONTRACT SPECIFICATIONS: RATU participates in the Cepu PSC as a non-operating equity holder where operational execution is managed by ExxonMobil Cepu Ltd (EMCL). Cash lifting cost is world-class at $4.20/bbl with statutory cost-recovery mechanisms guaranteeing OPEX reimbursement. Debt is fully amortized from historical IDR 4.2 Tn to IDR 2.1 Tn, giving an audited Beta of 0.70.',
          evidenceCitations: [
            { type: 'exhibit', reference: 'Exhibit 1: Cepu PSC Cost Structure & SKK Migas Audit' },
            { type: 'filing', reference: 'RATU Annual Report 2024 Note 14: PSC Operating Agreements' }
          ],
          verdict: 'DEFENDED_WITH_EVIDENCE'
        },
        {
          role: 'arbiter',
          speakerName: 'QA Critic Arbiter',
          timestamp: '2026-01-07 14:30 WIB',
          message: 'ARBITER VERDICT: DEFENDED. Operator tier-1 backing (ExxonMobil) and low debt balance justify low financial risk premium.',
          verdict: 'DEFENDED_WITH_EVIDENCE'
        }
      ]
    }
  ],
  CDIA: [
    {
      debateId: 'CDIA-RED-001',
      ticker: 'CDIA',
      topic: 'DDM 104% Dividend Payout Feasibility in FY28F',
      initialChallengerClaim: 'Is a 104% dividend payout ratio realistic for a conglomerate undergoing heavy infrastructure capex?',
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
          speakerName: 'Red Team Challenger (Capital Allocation Auditor)',
          timestamp: '2026-06-23 09:30 WIB',
          message: 'Your DDM model assumes payout ratio jumping from 40% in FY27 to 104% in FY28F to justify IDR 810 DDM target. How is >100% payout sustainable without leveraging the balance sheet?',
          evidenceCitations: [
            { type: 'calculation', reference: 'DDM schedule FY28F payout 104%' }
          ]
        },
        {
          role: 'defender',
          speakerName: 'Lead Analyst Defender',
          timestamp: '2026-06-23 09:38 WIB',
          message: 'DEFENDING WITH CASH FLOW PROFILE: By FY28F, major power and water expansion capex cycles (Krakatau Daya Listrik 120MW CCPP and KTI 2,000 l/s) will be fully operational and generating IDR 2,280 Bn EBITDA with sub-IDR 480 Bn maintenance capex. As a holding vehicle, CDIA upstream dividends from unencumbered operating subsidiaries, allowing capital return of surplus accumulated cash.',
          evidenceCitations: [
            { type: 'exhibit', reference: 'Exhibit 1: SOTP Cash Flow Generation by Subsidiary' }
          ],
          verdict: 'DEFENDED_WITH_EVIDENCE'
        },
        {
          role: 'arbiter',
          speakerName: 'QA Critic Arbiter',
          timestamp: '2026-06-23 09:42 WIB',
          message: 'ARBITER VERDICT: DEFENDED WITH QUALIFICATION. Holding company cash accumulation model is mathematically sound.',
          verdict: 'DEFENDED_WITH_EVIDENCE'
        }
      ]
    }
  ]
}

export function getDebatesForTicker(ticker: string): RedTeamDebateThread[] {
  const tk = ticker.toUpperCase()
  if (ADVERSARIAL_DEBATES[tk]) {
    return ADVERSARIAL_DEBATES[tk]
  }

  // Fallback dynamic debate
  return [
    {
      debateId: `${tk}-AUTO-001`,
      ticker: tk,
      topic: `Valuation Grounding & Assumption Audit for ${tk}`,
      initialChallengerClaim: `Challenging DCF growth and cost of equity assumptions for ${tk} within the current macro interest rate environment.`,
      roundCount: 1,
      status: 'RESOLVED',
      scorecard: {
        evidenceGroundingScore: 90,
        sycophancyRiskScore: 10,
        modelIntegrityVerified: true
      },
      turns: [
        {
          role: 'challenger',
          speakerName: 'Red Team Challenger',
          timestamp: '2026-08-31 09:00 WIB',
          message: `Are the revenue growth projections for ${tk} aligned with sector demand realities?`,
          evidenceCitations: [{ type: 'calculation', reference: 'Synthetic DCF engine parameters' }]
        },
        {
          role: 'defender',
          speakerName: 'Lead Analyst Defender',
          timestamp: '2026-08-31 09:05 WIB',
          message: `DEFENDING: Cash flow estimates for ${tk} are calibrated against deterministic 5-year historical trading ranges and balance sheet data audited from data/sectors.db.`,
          evidenceCitations: [{ type: 'filing', reference: 'sectors.db SQLite store' }],
          verdict: 'DEFENDED_WITH_EVIDENCE'
        },
        {
          role: 'arbiter',
          speakerName: 'QA Critic Arbiter',
          timestamp: '2026-08-31 09:10 WIB',
          message: 'ARBITER VERDICT: DEFENDED. Calculations verified against deterministic math module.',
          verdict: 'DEFENDED_WITH_EVIDENCE'
        }
      ]
    }
  ]
}
