import type { RetailSentimentData } from '../types'

export const RETAIL_SENTIMENT_DATA: Record<string, RetailSentimentData> = {
  MTEL: {
    ticker: 'MTEL',
    name: 'Dayamitra Telekomunikasi Tbk.',
    compositeScore: 78,
    sentimentLabel: 'Bullish',
    mentionsCount30d: 4820,
    sentimentVelocity: '+24% WoW',
    divergenceAlert: {
      isDivergent: true,
      type: 'CONTRARIAN_OPPORTUNITY',
      description: 'Institutional accumulation underway while retail social chatter focuses on slow immediate stock price movement, creating high-conviction value setup.'
    },
    topNarratives: [
      {
        rank: 1,
        title: 'Telco Mega Merger Colocation Wave',
        summary: 'Retail discussion on Stockbit & X highlighting Smartfren-XL consolidation as a net positive catalyst for MTEL outside-Java towers.',
        sentimentScore: 84,
        channels: ['Stockbit Stream', 'X (Twitter)', 'Telegram IDX']
      },
      {
        rank: 2,
        title: 'Fiberization Portfolio Undervaluation',
        summary: 'Investors comparing MTEL 59k km fiber assets with standalone valuation of privatized fiber companies.',
        sentimentScore: 76,
        channels: ['Reddit r/finansial', 'X (Twitter)']
      },
      {
        rank: 3,
        title: 'High Dividend Payout & Telkom Group Stability',
        summary: 'Retail income investors treating MTEL as a bond proxy with 3.7% expanding dividend yield.',
        sentimentScore: 75,
        channels: ['Stockbit Stream', 'YouTube IDX Analysts']
      }
    ],
    timelineEvolution: [
      { date: '2026-08-01', sentimentScore: 62, stockPrice: 420, keyEvent: '1H26 Earnings Release (+2% YoY Net Profit)' },
      { date: '2026-08-10', sentimentScore: 68, stockPrice: 435, keyEvent: 'Telco Ministry 700MHz Spectrum Finalization' },
      { date: '2026-08-20', sentimentScore: 74, stockPrice: 450, keyEvent: 'Danantara Infrastructure Priority Leaks' },
      { date: '2026-08-27', sentimentScore: 78, stockPrice: 460, keyEvent: 'Institutional Upgrade to BUY TP 635' }
    ],
    platformBreakdown: [
      {
        platform: 'Stockbit Stream',
        sentimentScore: 82,
        volumeSharePct: 48,
        samplePost: {
          platform: 'Stockbit',
          author: '@cuan_investor_jkt',
          timestamp: '2026-08-27 09:45 WIB',
          content: '$MTEL tenancy 1.57x ini real monster recurring cashflow. Merger PST-UMT malah bikin operator butuh colocation cepet di luar Jawa. TP 635 realistis banget.',
          sentiment: 'BULLISH',
          engagement: '342 likes · 48 reposts',
          url: 'https://stockbit.com/symbol/MTEL'
        }
      },
      {
        platform: 'X / Twitter ($MTEL)',
        sentimentScore: 76,
        volumeSharePct: 34,
        samplePost: {
          platform: 'X / Twitter',
          author: '@IdxQuantTracker',
          timestamp: '2026-08-26 14:12 WIB',
          content: 'Multiple valuation band MTEL di 8.47x EV/EBITDA udah di bawah minus 2 standard deviasi historical 3Y. Asymmetric risk reward buat long term infra play. $MTEL $TOWR $TBIG',
          sentiment: 'BULLISH',
          engagement: '1.2k likes · 185 bookmarks',
          url: 'https://x.com/search?q=%24MTEL'
        }
      },
      {
        platform: 'Reddit r/finansial',
        sentimentScore: 74,
        volumeSharePct: 18,
        samplePost: {
          platform: 'Reddit',
          author: 'u/fundamental_idx_guy',
          timestamp: '2026-08-25 18:30 WIB',
          content: 'Deep dive MTEL vs TOWR: Balance sheet MTEL jauh lebih sehat dengan net debt/EBITDA 1.8x vs TOWR >4x. Kalau suku bunga BI turun, MTEL punya leverage paling aman buat ekspansi fiber.',
          sentiment: 'BULLISH',
          engagement: '215 upvotes · 64 comments',
          url: 'https://reddit.com/r/finansial'
        }
      }
    ]
  },
  RATU: {
    ticker: 'RATU',
    name: 'Ratu Prabu Energi Tbk.',
    compositeScore: 68,
    sentimentLabel: 'Bullish',
    mentionsCount30d: 3120,
    sentimentVelocity: '+15% WoW',
    divergenceAlert: {
      isDivergent: false,
      type: 'ALIGNED',
      description: 'Retail enthusiasm aligned with upstream crude oil cash recovery.'
    },
    topNarratives: [
      {
        rank: 1,
        title: 'Cepu Block 169k BOPD Production Continuity',
        summary: 'Strong confidence in Banyu Urip secondary recovery reservoir longevity.',
        sentimentScore: 78,
        channels: ['Stockbit', 'X']
      },
      {
        rank: 2,
        title: 'Bottom Line Turnaround (+28% Net Profit)',
        summary: 'Traders noting gross margin widening as high-cost rig depreciation expires.',
        sentimentScore: 72,
        channels: ['X (Twitter)', 'Stockbit Stream']
      }
    ],
    timelineEvolution: [
      { date: '2026-08-01', sentimentScore: 58, stockPrice: 6500, keyEvent: 'SKK Migas National Lifting Briefing' },
      { date: '2026-08-15', sentimentScore: 64, stockPrice: 6900, keyEvent: 'Oil Price ICP Stability at $76/bbl' },
      { date: '2026-08-27', sentimentScore: 68, stockPrice: 7150, keyEvent: 'Institutional BUY Report Circulation' }
    ],
    platformBreakdown: [
      {
        platform: 'Stockbit Stream',
        sentimentScore: 72,
        volumeSharePct: 55,
        samplePost: {
          platform: 'Stockbit',
          author: '@oil_gas_analyst',
          timestamp: '2026-08-27 10:00 WIB',
          content: '$RATU lifting cost $4.2/bbl itu benchmark terendah se-Asia Tenggara. Laba bersih naik 28% padahal revenue flat.',
          sentiment: 'BULLISH',
          engagement: '180 likes',
          url: 'https://stockbit.com/symbol/RATU'
        }
      }
    ]
  },
  CDIA: {
    ticker: 'CDIA',
    name: 'Chandra Daya Investasi Tbk.',
    compositeScore: 64,
    sentimentLabel: 'Bullish',
    mentionsCount30d: 2150,
    sentimentVelocity: '+8% WoW',
    topNarratives: [
      {
        rank: 1,
        title: 'SOTP 4-Pilar Value Unlocking',
        summary: 'Conglomerate sum-of-the-parts tracking independent valuations for energy and water assets.',
        sentimentScore: 70,
        channels: ['Stockbit', 'X']
      }
    ],
    timelineEvolution: [
      { date: '2026-08-01', sentimentScore: 56, stockPrice: 720, keyEvent: 'Logistics Fleet Expansion Announcement' },
      { date: '2026-08-27', sentimentScore: 64, stockPrice: 742, keyEvent: 'SOTP Valuation Consensus' }
    ],
    platformBreakdown: [
      {
        platform: 'Stockbit Stream',
        sentimentScore: 66,
        volumeSharePct: 60,
        samplePost: {
          platform: 'Stockbit',
          author: '@infra_hunter',
          timestamp: '2026-08-27 11:30 WIB',
          content: '$CDIA pilar logistik kapal kimia tumbuh 44.7%. SOTP target 815 masih ada upside.',
          sentiment: 'BULLISH',
          engagement: '95 likes',
          url: 'https://stockbit.com/symbol/CDIA'
        }
      }
    ]
  },
  BBCA: {
    ticker: 'BBCA',
    name: 'Bank Central Asia Tbk.',
    compositeScore: 82,
    sentimentLabel: 'Euphoria',
    mentionsCount30d: 14200,
    sentimentVelocity: '+18% WoW',
    topNarratives: [
      {
        rank: 1,
        title: 'CASA 81.2% & Unshakable Deposit Moat',
        summary: 'Retail discussions unanimously praise BCA mobile banking transaction volume dominance.',
        sentimentScore: 90,
        channels: ['Stockbit', 'X', 'Reddit']
      }
    ],
    timelineEvolution: [
      { date: '2026-08-01', sentimentScore: 76, stockPrice: 7400, keyEvent: '1H26 Net Profit Beat (IDR 26.9 Tn)' },
      { date: '2026-08-27', sentimentScore: 82, stockPrice: 7890, keyEvent: 'All-Time High Price Action' }
    ],
    platformBreakdown: [
      {
        platform: 'X / Twitter ($BBCA)',
        sentimentScore: 86,
        volumeSharePct: 52,
        samplePost: {
          platform: 'X / Twitter',
          author: '@FinansialId',
          timestamp: '2026-08-27 13:00 WIB',
          content: 'BBCA gak ada lawan di likuiditas. CASA 81.2% bikin cost of fund cuma 1.4%. GGM target Rp 9.600.',
          sentiment: 'BULLISH',
          engagement: '3.4k likes',
          url: 'https://x.com/search?q=%24BBCA'
        }
      }
    ]
  },
  ADRO: {
    ticker: 'ADRO',
    name: 'Adaro Energy Indonesia Tbk.',
    compositeScore: 71,
    sentimentLabel: 'Bullish',
    mentionsCount30d: 8900,
    sentimentVelocity: '+30% WoW',
    topNarratives: [
      {
        rank: 1,
        title: 'AADI Demerger Special Dividend Windfall',
        summary: 'Retail coal investors calculating expected US$2.6 Bn dividend yield post spin-off.',
        sentimentScore: 88,
        channels: ['Stockbit', 'Telegram IDX']
      }
    ],
    timelineEvolution: [
      { date: '2026-08-01', sentimentScore: 60, stockPrice: 1950, keyEvent: 'EGMS Approval for AADI Spin-off' },
      { date: '2026-08-27', sentimentScore: 71, stockPrice: 2080, keyEvent: 'Special Dividend Prospectus Filing' }
    ],
    platformBreakdown: [
      {
        platform: 'Stockbit Stream',
        sentimentScore: 78,
        volumeSharePct: 65,
        samplePost: {
          platform: 'Stockbit',
          author: '@dividend_king_id',
          timestamp: '2026-08-27 15:20 WIB',
          content: '$ADRO spin-off AADI bakal kasih dividen jumbo. SOTP BRIDS target 2450.',
          sentiment: 'BULLISH',
          engagement: '620 likes',
          url: 'https://stockbit.com/symbol/ADRO'
        }
      }
    ]
  }
}

export function getSentimentForTicker(ticker: string): RetailSentimentData {
  const tk = ticker.toUpperCase()
  if (RETAIL_SENTIMENT_DATA[tk]) {
    return RETAIL_SENTIMENT_DATA[tk]
  }

  return {
    ticker: tk,
    name: `${tk} Tbk.`,
    compositeScore: 60,
    sentimentLabel: 'Neutral',
    mentionsCount30d: 850,
    sentimentVelocity: '+5% WoW',
    divergenceAlert: {
      isDivergent: false,
      type: 'ALIGNED',
      description: 'Retail sentiment is balanced with institutional consensus.'
    },
    topNarratives: [
      {
        rank: 1,
        title: `${tk} Sector Growth & Earnings Momentum`,
        summary: `Retail discussions focusing on fundamental sector positioning for ${tk}.`,
        sentimentScore: 62,
        channels: ['Stockbit Stream', 'X (Twitter)']
      }
    ],
    timelineEvolution: [
      { date: '2026-08-01', sentimentScore: 55, stockPrice: 1000, keyEvent: '1H26 Result Filing' },
      { date: '2026-08-27', sentimentScore: 60, stockPrice: 1050, keyEvent: 'Consensus Target Update' }
    ],
    platformBreakdown: [
      {
        platform: 'Stockbit Stream',
        sentimentScore: 62,
        volumeSharePct: 60,
        samplePost: {
          platform: 'Stockbit',
          author: '@retail_idx',
          timestamp: '2026-08-27 12:00 WIB',
          content: `$${tk} volume transaksi mulai ada akumulasi bertahap.`,
          sentiment: 'NEUTRAL',
          engagement: '45 likes',
          url: `https://stockbit.com/symbol/${tk}`
        }
      }
    ]
  }
}
