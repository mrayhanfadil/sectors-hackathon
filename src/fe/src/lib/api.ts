export type Ticker = "RATU" | "CDIA" | "MTEL" | "BBCA" | "ADRO"

export type Report = {
  ticker: string
  name: string
  price: number
  target: number
  upside: string
  rating: "BUY" | "HOLD" | "SELL"
  summary: string
  valuation: { method: string; value: number; weight?: number }[]
  updatedAt: string
}

export type ChallengeRequest = {
  ticker: string
  claim: string
  context?: string
}

export type ChallengeResponse = {
  ticker: string
  claim: string
  verdict: "defend" | "concede"
  evidence: string
  exhibit_ref?: string | null
  source_citation?: string | null
  correction?: string | null
  debate_id: string
  timestamp: string
}

export type PlatformSentiment = {
  platform: string
  score: number
  label: string
  volume: string
  url: string
  sampleText?: string
}

export type SentimentData = {
  ticker: string
  name: string
  gauge: number
  label: "Bullish" | "Bearish" | "Neutral"
  confidence: number
  narratives: { rank: number; title: string; sharePct: number; sentiment: "bull" | "bear" | "neutral"; realityCheck: string }[]
  timeline: { date: string; event: string; impact: string }[]
  platforms: PlatformSentiment[]
  retailVsThesis: { retailSentiment: string; institutionalView: string; alignment: string }
  disclaimer: string
}

const MOCK_REPORTS: Record<string, Report> = {
  RATU: {
    ticker: "RATU",
    name: "Ratu Prabu Energi Tbk (Oil & Gas Holding)",
    price: 7150,
    target: 7880,
    upside: "+10.2%",
    rating: "BUY",
    summary: "Pure-play Cepu PSC holding — DCF 8.4% WACC (beta 0.7, ERP 6.9%, g 5.0%) + EV/EBITDA 22.6x. Bottom line +28% meski revenue -13% didorong lifting Cepu 169k BOPD.",
    valuation: [
      { method: "DCF (WACC 8.4%)", value: 7880, weight: 60 },
      { method: "EV/EBITDA (22.6x)", value: 6960, weight: 40 },
    ],
    updatedAt: "31 Agt 2026",
  },
  CDIA: {
    ticker: "CDIA",
    name: "Chandra Daya Investasi Tbk (Conglomerate SOTP)",
    price: 742,
    target: 815,
    upside: "+9.8%",
    rating: "BUY",
    summary: "Conglomerate 4-Pilar (Energy, Water, Port, Logistics) — DCF 815 + DDM 810. Bauran pendapatan: Energy 55% (US$23mn), Logistics 34% (+44.7% YoY, US$14mn). One-off US$15.9mn dinormalisasi.",
    valuation: [
      { method: "DCF 4-Pillar", value: 815 },
      { method: "DDM (Payout 40%)", value: 810 },
    ],
    updatedAt: "31 Agt 2026",
  },
  MTEL: {
    ticker: "MTEL",
    name: "Dayamitra Telekomunikasi Tbk (Mitratel)",
    price: 460,
    target: 635,
    upside: "+38.0%",
    rating: "BUY",
    summary: "Infra recurring model — Blended DCF 60% (Rp 630) + EV/EBITDA 10x 40% (Rp 745) → TP Rp 635. Tenancy ratio 1.57x (40,563 menara, 63,866 penyewa), fiber optic 59,239 km (+9% YoY).",
    valuation: [
      { method: "DCF (WACC 10.10%, g 1.5%)", value: 630, weight: 60 },
      { method: "EV/EBITDA (10.0x)", value: 745, weight: 40 },
    ],
    updatedAt: "31 Agt 2026",
  },
  BBCA: {
    ticker: "BBCA",
    name: "Bank Central Asia Tbk",
    price: 7890,
    target: 9600,
    upside: "+21.9%",
    rating: "BUY",
    summary: "Gordon Growth Model (GGM) implied P/BV — (ROE-g)/(CoE-g) target P/BV 3.3x, ROE 19.7%, CASA franchise 81.2%, asset quality stabil NPL 1.8%.",
    valuation: [
      { method: "GGM Implied P/BV (3.3x)", value: 9600 },
      { method: "Peer Average Multiples", value: 9150 },
    ],
    updatedAt: "31 Agt 2026",
  },
  ADRO: {
    ticker: "ADRO",
    name: "Adaro Energy Indonesia Tbk",
    price: 2080,
    target: 2450,
    upside: "+17.8%",
    rating: "BUY",
    summary: "SOTP Post Spin-off AADI US$6.1bn + thermal coal holdco discount 15% — dual DCF + SOTP aggregate fair value Rp 2,450.",
    valuation: [
      { method: "SOTP (Holdco Discount 15%)", value: 2450 },
      { method: "DCF Cash Flow Model", value: 2380 },
    ],
    updatedAt: "31 Agt 2026",
  },
}

const MOCK_SENTIMENTS: Record<string, SentimentData> = {
  RATU: {
    ticker: "RATU",
    name: "Ratu Prabu Energi",
    gauge: 58,
    label: "Neutral",
    confidence: 0.82,
    narratives: [
      { rank: 1, title: "Lifting Cepu 169k BOPD & optimisme bagi hasil PSC", sharePct: 45, sentiment: "bull", realityCheck: "Tercermin dalam DCF dengan asumsi decline 5% p.a." },
      { rank: 2, title: "Kekhawatiran penurunan harga minyak mentah Brent", sharePct: 35, sentiment: "bear", realityCheck: "Sensitivitas: setiap US$5/bbl perubahan Brent berdampak ±Rp 320 pada fair value." },
      { rank: 3, title: "Likuiditas saham & free float 31.2%", sharePct: 20, sentiment: "neutral", realityCheck: "Free float stabil, masuk konstituen indeks IDX80." },
    ],
    timeline: [
      { date: "2026-08-15", event: "Diskusi kuartalan lifting minyak Cepu di forum investor", impact: "+4 poin sentiment" },
      { date: "2026-08-22", event: "OPEC+ review kuota produksi & volatilitas minyak global", impact: "-2 poin sentiment" },
      { date: "2026-08-29", event: "Laporan kinerja konsolidasi 1H26 rilis ke publik", impact: "+3 poin sentiment" },
    ],
    platforms: [
      { platform: "X (Twitter)", score: 56, label: "Neutral", volume: "1.4k posts", url: "https://x.com/search?q=%24RATU", sampleText: "RATU margin operasi masih kuat berkat cost recovery Cepu #IDX" },
      { platform: "Reddit", score: 62, label: "Bullish", volume: "320 comments", url: "https://www.reddit.com/search/?q=RATU+saham", sampleText: "Analisis fundamental RATU vs emiten migas lain di IDX" },
      { platform: "Stockbit", score: 60, label: "Bullish", volume: "3.8k streams", url: "https://stockbit.com/symbol/RATU", sampleText: "DCF fair value RATU konsisten di kisaran 7.800+" },
    ],
    retailVsThesis: {
      retailSentiment: "Cenderung menunggu katalis harga minyak global",
      institutionalView: "DCF WACC 8.4% memberikan upside +10.2% yang terukur",
      alignment: "Moderate — retail fokus jangka pendek, institusi fokus arus kas Cepu",
    },
    disclaimer: "Sentiment data is derived from retail social signals and is for market intelligence only. Sentiment ≠ Investment Advice.",
  },
  CDIA: {
    ticker: "CDIA",
    name: "Chandra Daya Investasi",
    gauge: 64,
    label: "Bullish",
    confidence: 0.85,
    narratives: [
      { rank: 1, title: "Ekspansi logistik laut & tangki sewa kimia", sharePct: 48, sentiment: "bull", realityCheck: "Sektor logistik tumbuh +44.7% YoY menjadi pilar pendorong terbesar 2H26." },
      { rank: 2, title: "Normalisasi one-off expense US$15.9mn", sharePct: 32, sentiment: "bull", realityCheck: "Normalisasi one-off telah diverifikasi pada laporan keuangan audited." },
      { rank: 3, title: "Sensitivitas harga gas industri untuk pilar energi", sharePct: 20, sentiment: "neutral", realityCheck: "Margin dilindungi skema take-or-pay jangka panjang." },
    ],
    timeline: [
      { date: "2026-08-10", event: "Pengumuman penambahan armada kapal tanker kimia", impact: "+5 poin sentiment" },
      { date: "2026-08-20", event: "Diskusi SOTP 4 pilar di grup Telegram & komunitas analis", impact: "+3 poin sentiment" },
      { date: "2026-08-28", event: "Analisis dividen yield DDM 40% payout", impact: "+2 poin sentiment" },
    ],
    platforms: [
      { platform: "X (Twitter)", score: 65, label: "Bullish", volume: "2.1k posts", url: "https://x.com/search?q=%24CDIA", sampleText: "CDIA pilar logistik + port cash cow banget di Cilegon #saham" },
      { platform: "Reddit", score: 59, label: "Neutral", volume: "410 comments", url: "https://www.reddit.com/search/?q=CDIA+saham", sampleText: "DDM vs SOTP valuation CDIA conglomerate breakdown" },
      { platform: "Stockbit", score: 67, label: "Bullish", volume: "5.2k streams", url: "https://stockbit.com/symbol/CDIA", sampleText: "Valuasi pilar energi & air stabil, logistik fastest growing" },
    ],
    retailVsThesis: {
      retailSentiment: "Optimis terhadap sinergi infrastruktur industri Cilegon",
      institutionalView: "SOTP DCF Rp 815 + DDM Rp 810 memberikan konvergensi valuasi yang kokoh",
      alignment: "High — pandangan retail dan model institusi selaras pada pertumbuhan logistik",
    },
    disclaimer: "Sentiment data is derived from retail social signals and is for market intelligence only. Sentiment ≠ Investment Advice.",
  },
  MTEL: {
    ticker: "MTEL",
    name: "Dayamitra Telekomunikasi (Mitratel)",
    gauge: 78,
    label: "Bullish",
    confidence: 0.91,
    narratives: [
      { rank: 1, title: "Katalis Merger Operator & lelang spektrum 700MHz/2.6GHz", sharePct: 52, sentiment: "bull", realityCheck: "Potensi +3.000-3.500 tenant baru dan +IDR 360-420 miliar pendapatan tahunan." },
      { rank: 2, title: "Pertumbuhan masif fiber optik 59.239 km (+9% YoY)", sharePct: 30, sentiment: "bull", realityCheck: "Fiberisasi menara mendorong ARPU dan rasio kolokasi di luar Jawa." },
      { rank: 3, title: "Yield dividen 3.7% & valuasi PBV band di bawah rata-rata historis", sharePct: 18, sentiment: "bull", realityCheck: "PBV 1.47x saat ini berada di area 'BELOW AVG' (STD -1.2) memberikan margin of safety." },
    ],
    timeline: [
      { date: "2026-08-05", event: "Pengumuman penyelesaian integrasi fiberisasi 59k km", impact: "+6 poin sentiment" },
      { date: "2026-08-18", event: "Update merger operator seluler efektif 1 Juli 2026", impact: "+8 poin sentiment" },
      { date: "2026-08-27", event: "Rilis riset institusi dengan target harga blended Rp 635", impact: "+5 poin sentiment" },
    ],
    platforms: [
      { platform: "X (Twitter)", score: 76, label: "Bullish", volume: "3.4k posts", url: "https://x.com/search?q=%24MTEL", sampleText: "MTEL tenancy ratio 1.57x makin solid, yield dividen menarik banget #IHSG" },
      { platform: "Reddit", score: 74, label: "Bullish", volume: "620 comments", url: "https://www.reddit.com/search/?q=MTEL+saham", sampleText: "Mitratel tower defensive play with strong recurring revenue and fiber expansion" },
      { platform: "Stockbit", score: 81, label: "Bullish", volume: "8.9k streams", url: "https://stockbit.com/symbol/MTEL", sampleText: "Buy MTEL, target 635 upside 38%, katalis spektrum 700MHz jelas" },
    ],
    retailVsThesis: {
      retailSentiment: "Sangat bullish pada yield dividen dan katalis fiberisasi 5G",
      institutionalView: "Model blended 60% DCF + 40% EV/EBITDA menghasilkan TP Rp 635 (+38% upside)",
      alignment: "Strong — antusiasme retail didukung metrik operasional tenancy ratio dan arus kas riil",
    },
    disclaimer: "Sentiment data is derived from retail social signals and is for market intelligence only. Sentiment ≠ Investment Advice.",
  },
  BBCA: {
    ticker: "BBCA",
    name: "Bank Central Asia",
    gauge: 72,
    label: "Bullish",
    confidence: 0.89,
    narratives: [
      { rank: 1, title: "Inflow dana asing & katalis Danantara Value-Up", sharePct: 46, sentiment: "bull", realityCheck: "Danantara dry powder US$12bn mendorong minat institusi pada perbankan tier-1." },
      { rank: 2, title: "Kekuatan CASA franchise 81.2% tahan siklus suku bunga", sharePct: 34, sentiment: "bull", realityCheck: "CoF rendah melindungi Net Interest Margin saat BI rate turun." },
      { rank: 3, title: "Valuasi P/BV 3.3x vs rata-rata historis", sharePct: 20, sentiment: "neutral", realityCheck: "Model GGM (ROE-g)/(CoE-g) mengindikasikan fair value Rp 9.600." },
    ],
    timeline: [
      { date: "2026-08-12", event: "Rilis pertumbuhan laba bersih perbankan bulanan", impact: "+4 poin sentiment" },
      { date: "2026-08-21", event: "Komentar pasar mengenai alokasi portofolio Danantara", impact: "+6 poin sentiment" },
      { date: "2026-08-28", event: "Akumulasi asing bersih di pasar reguler", impact: "+3 poin sentiment" },
    ],
    platforms: [
      { platform: "X (Twitter)", score: 71, label: "Bullish", volume: "5.8k posts", url: "https://x.com/search?q=%24BBCA", sampleText: "BBCA tetap standar emas IHSG, CASA kuat dividen konsisten #BBCA" },
      { platform: "Reddit", score: 70, label: "Bullish", volume: "850 comments", url: "https://www.reddit.com/search/?q=BBCA+saham", sampleText: "Why BBCA remains the ultimate core holding in Indonesia equity portfolio" },
      { platform: "Stockbit", score: 74, label: "Bullish", volume: "14.2k streams", url: "https://stockbit.com/symbol/BBCA", sampleText: "GGM target 9.600 terjangkau, asing terus net buy" },
    ],
    retailVsThesis: {
      retailSentiment: "Keyakinan defensif tinggi sebagai 'saham tabungan'",
      institutionalView: "GGM implied P/BV 3.3x target Rp 9.600 (+21.9% upside)",
      alignment: "High — konsensus luas bahwa franchise ritel BCA adalah yang terbaik di ASEAN",
    },
    disclaimer: "Sentiment data is derived from retail social signals and is for market intelligence only. Sentiment ≠ Investment Advice.",
  },
  ADRO: {
    ticker: "ADRO",
    name: "Adaro Energy Indonesia",
    gauge: 52,
    label: "Neutral",
    confidence: 0.80,
    narratives: [
      { rank: 1, title: "Pembagian dividen jumbo & demerger spin-off AADI", sharePct: 50, sentiment: "bull", realityCheck: "Spin-off AADI US$6.1bn membuka nilai pilar energi hijau Adaro." },
      { rank: 2, title: "Holdco discount pasca spin-off batubara termal", sharePct: 30, sentiment: "bear", realityCheck: "Model SOTP memasukkan holdco discount 15% untuk post-spin entity." },
      { rank: 3, title: "Diversifikasi ke smelter aluminium & energi terbarukan", sharePct: 20, sentiment: "neutral", realityCheck: "Capex smelter Kaltara berjalan sesuai jadwal, kontribusi laba mulai FY27." },
    ],
    timeline: [
      { date: "2026-08-08", event: "Rapat pemegang saham terkait skema spin-off AADI", impact: "+5 poin sentiment" },
      { date: "2026-08-19", event: "Koreksi harga batubara Newcastle", impact: "-4 poin sentiment" },
      { date: "2026-08-30", event: "Analisis SOTP post-spin holdco discount di media finansial", impact: "+2 poin sentiment" },
    ],
    platforms: [
      { platform: "X (Twitter)", score: 51, label: "Neutral", volume: "2.8k posts", url: "https://x.com/search?q=%24ADRO", sampleText: "ADRO dividen yield masih juara, tapi wait and see efek spin-off AADI #saham" },
      { platform: "Reddit", score: 48, label: "Neutral", volume: "490 comments", url: "https://www.reddit.com/search/?q=ADRO+saham", sampleText: "Adaro SOTP breakdown: coal holdco vs renewable/aluminum valuation" },
      { platform: "Stockbit", score: 56, label: "Neutral", volume: "6.5k streams", url: "https://stockbit.com/symbol/ADRO", sampleText: "Target SOTP 2.450, holdco discount 15% udah realistis" },
    ],
    retailVsThesis: {
      retailSentiment: "Fokus pada besaran dividen kas dan dividen saham AADI",
      institutionalView: "SOTP dual model menghasilkan target harga Rp 2.450 (+17.8% upside)",
      alignment: "Moderate — institusi menekankan struktural holdco discount pasca pemisahan aset",
    },
    disclaimer: "Sentiment data is derived from retail social signals and is for market intelligence only. Sentiment ≠ Investment Advice.",
  },
}

const MOCK_DEFENSES: Record<string, { patterns: string[]; defend: ChallengeResponse; fallback: ChallengeResponse }> = {
  RATU: {
    patterns: ["wacc", "8.4", "discount rate", "cost of capital", "beta", "optimistic"],
    defend: {
      ticker: "RATU",
      claim: "WACC 8.4% is too optimistic for an oil & gas holding company.",
      verdict: "defend",
      evidence: "WACC 8.4% dihitung secara deterministik: Rf 6.96% (SUN 10Y per 28 Agt 2026), ERP 6.90% (Damodaran Indonesia risk premium), Beta 0.70 (3Y weekly raw vs IHSG), CoE 10.0%, CoD 3.5% (effective tax-adjusted PSC debt facility), Debt/Equity 20/80. Seluruh komponen didokumentasikan di Exhibit 4.",
      exhibit_ref: "Exhibit 4: Valuation DCF Assumptions & WACC Derivation",
      source_citation: "data/assumptions/RATU.json · scripts/dcf_engine.py · Bloomberg / SKK Migas",
      debate_id: "ratu-wacc-84",
      timestamp: new Date().toISOString(),
    },
    fallback: {
      ticker: "RATU",
      claim: "General risk challenge on RATU cash flow projections.",
      verdict: "defend",
      evidence: "Model arus kas mengasumsikan lifting stabil 169k BOPD di Blok Cepu sesuai PSC work program 2026-2028 dengan asumsi natural decline 5.0% p.a., didukung cadangan 2P terverifikasi SKK Migas.",
      exhibit_ref: "Exhibit 2: Cepu PSC Operational Profile",
      source_citation: "data/assumptions/RATU.json · SKK Migas Laporan Tahunan",
      debate_id: "ratu-gen-def",
      timestamp: new Date().toISOString(),
    },
  },
  MTEL: {
    patterns: ["tenancy", "1.57", "colocation", "tower", "over-optimistic", "merger", "spectrum"],
    defend: {
      ticker: "MTEL",
      claim: "Tenancy ratio 1.57x is too optimistic and cannot be sustained.",
      verdict: "defend",
      evidence: "Tenancy ratio 1.57x adalah fakta historis per 1H26 (63.866 tenant / 40.563 tower = 1.574x, naik dari 1.53x di 1H25). Kenaikan rasio didukung penambahan 2.150 colocation tenant pasca merger PST-UMT dan lelang spektrum 700MHz/2.6GHz dengan 3.000-3.500 tenant baru terkuantifikasi.",
      exhibit_ref: "Exhibit 3: Operational KPIs & Tenancy Ratio Trajectory",
      source_citation: "data/assumptions/MTEL.json · scripts/blended_engine.py · MTEL 1H26 Financial Disclosure",
      debate_id: "mtel-tenancy-157",
      timestamp: new Date().toISOString(),
    },
    fallback: {
      ticker: "MTEL",
      claim: "General challenge on MTEL blended valuation.",
      verdict: "defend",
      evidence: "Valuasi blended 60% DCF (Rp 630) + 40% EV/EBITDA 10.0x (Rp 745) menghasilkan nilai wajar Rp 635 setelah margin of safety 15%. Bobot 60/40 merefleksikan model recurring infra standar KSI/Kiwoom.",
      exhibit_ref: "Exhibit 5: Blended Valuation Matrix",
      source_citation: "templates/report_infra.html · scripts/blended_engine.py",
      debate_id: "mtel-blend-def",
      timestamp: new Date().toISOString(),
    },
  },
  CDIA: {
    patterns: ["one-off", "15.9", "normalization", "logistics", "segment", "energy", "sotp"],
    defend: {
      ticker: "CDIA",
      claim: "One-off normalization of US$15.9mn is unjustified.",
      verdict: "defend",
      evidence: "Normalisasi US$15.9mn merupakan biaya restrukturisasi M&A non-operasional yang tidak berulang pada pilar logistik maritim. Setelah penyesuaian, laba bersih operasional (adjusted net profit) adalah US$4.82mn, yang digunakan sebagai basis proyeksi DCF pilar logistik.",
      exhibit_ref: "Exhibit 1: Segment Mix & One-off Normalization Bridge",
      source_citation: "data/assumptions/CDIA.json · BCA Sekuritas CDIA Initiation",
      debate_id: "cdia-oneoff-norm",
      timestamp: new Date().toISOString(),
    },
    fallback: {
      ticker: "CDIA",
      claim: "General challenge on CDIA SOTP valuation.",
      verdict: "defend",
      evidence: "SOTP 4-pilar menggunakan peer-average EV/EBITDA dan P/E spesifik per industri: Energy (POWR, Sembcorp), Water, Port (Westports), dan Logistics (HATM), menghasilkan fair value Rp 815 yang terkonvergensi dengan DDM Rp 810.",
      exhibit_ref: "Exhibit 4: 4-Pillar Peer Comps & SOTP Bridge",
      source_citation: "data/assumptions/CDIA.json · scripts/sotp_engine.py",
      debate_id: "cdia-sotp-def",
      timestamp: new Date().toISOString(),
    },
  },
  BBCA: {
    patterns: ["ggm", "roe", "19.7", "pbv", "3.3", "nim", "rate cut"],
    defend: {
      ticker: "BBCA",
      claim: "GGM target P/BV 3.3x is too high in a declining interest rate environment.",
      verdict: "defend",
      evidence: "Formula GGM: P/BV = (ROE - g) / (CoE - g) = (19.7% - 6.5%) / (10.5% - 6.5%) = 13.2% / 4.0% = 3.30x. CASA franchise 81.2% memungkinkan cost of funds BBCA tetap di bawah 2.0%, mempertahankan ROE >19% meski BI rate dipangkas.",
      exhibit_ref: "Exhibit 4: GGM Derivation & Sensitivity Matrix",
      source_citation: "data/assumptions/BBCA.json · Samuel Sekuritas BBCA Research (21 Oct 2025)",
      debate_id: "bbca-ggm-def",
      timestamp: new Date().toISOString(),
    },
    fallback: {
      ticker: "BBCA",
      claim: "General challenge on BBCA banking multiples.",
      verdict: "defend",
      evidence: "Kualitas aset BBCA dengan LAR <5% dan NPL 1.8% memberikan ruang coverage ratio >250%, membenarkan premium valuasi terhadap peer bank BUMN.",
      exhibit_ref: "Exhibit 3: Asset Quality & Loan Growth Trajectory",
      source_citation: "data/assumptions/BBCA.json · IDX Financials",
      debate_id: "bbca-mult-def",
      timestamp: new Date().toISOString(),
    },
  },
  ADRO: {
    patterns: ["spin-off", "aadi", "holdco", "discount", "15", "coal", "thermal"],
    defend: {
      ticker: "ADRO",
      claim: "Holdco discount of 15% is too narrow post AADI spin-off.",
      verdict: "defend",
      evidence: "Diskon holdco 15% mencerminkan likuiditas dividen tunai pasca pemisahan AADI serta kepemilikan langsung pada smelter aluminium Kaltara dan proyek PLTA yang memiliki kontrak jangka panjang dengan PLN.",
      exhibit_ref: "Exhibit 4: SOTP Spin-off Bridge & Holdco Discount Matrix",
      source_citation: "data/assumptions/ADRO.json · BRIDS Research (18 Nov 2024)",
      debate_id: "adro-holdco-def",
      timestamp: new Date().toISOString(),
    },
    fallback: {
      ticker: "ADRO",
      claim: "General challenge on ADRO thermal coal transition.",
      verdict: "defend",
      evidence: "DCF konservatif menggunakan asumsi harga batubara termal Newcastle US$115/ton dengan penurunan bertahap ke US$95/ton, diimbangi oleh pertumbuhan EBITDA pilar non-batubara hingga 35% pada FY28F.",
      exhibit_ref: "Exhibit 2: Revenue Transition & Commodity Price Assumptions",
      source_citation: "data/assumptions/ADRO.json · scripts/dcf_engine.py",
      debate_id: "adro-dcf-def",
      timestamp: new Date().toISOString(),
    },
  },
}

export async function fetchReport(ticker: string): Promise<Report> {
  const tk = ticker.toUpperCase().trim()
  try {
    const res = await fetch(`/api/report/${tk}`, { headers: { Accept: "application/json" } })
    if (res.ok) {
      const data = await res.json()
      if (data && data.meta) {
        const cover = data.cover || {}
        const rb = cover.rating_box || {}
        return {
          ticker: data.meta.ticker || tk,
          name: data.meta.company_name || `${tk} Tbk`,
          price: rb.price || 1000,
          target: rb.tp || 1200,
          upside: rb.upside_pct ? `${rb.upside_pct > 0 ? "+" : ""}${rb.upside_pct}%` : "+20.0%",
          rating: (rb.action as any) || "BUY",
          summary: data.performance?.narrative || data.meta?.reason || "Institutional equity report generated via multi-agent deterministic system.",
          valuation: (data.valuation?.methods || []).map((m: any) => ({
            method: m.method,
            value: m.fv,
            weight: data.valuation?.blended?.weights?.[m.method],
          })),
          updatedAt: data.meta.date || "31 Agt 2026",
        }
      }
    }
  } catch {
    // offline / mock fallback
  }

  await new Promise((r) => setTimeout(r, 200))
  if (MOCK_REPORTS[tk]) return MOCK_REPORTS[tk]
  return {
    ticker: tk,
    name: `${tk} Tbk (Synthetic)`,
    price: 1000,
    target: 1200,
    upside: "+20.0%",
    rating: "BUY",
    summary: "Synthetic initiation report — deterministic valuation models seed=42.",
    valuation: [{ method: "DCF Model", value: 1200, weight: 100 }],
    updatedAt: "31 Agt 2026",
  }
}

export async function fetchOutlook() {
  try {
    const res = await fetch("/api/outlook", { headers: { Accept: "application/json" } })
    if (res.ok) {
      const data = await res.json()
      if (data && data.index_target) {
        return {
          jci: {
            base: data.index_target.base || 9100,
            bull: data.index_target.bull || 10000,
            bear: data.index_target.bear || 7800,
            pe: data.index_target.multiple || 15,
            epsGrowth: `${data.index_target.eps_growth_pct || 8}%`,
          },
          sectors: (data.sectors || []).map((s: any) => ({
            name: s.name,
            call: s.view || s.call || "OW",
          })),
        }
      }
    }
  } catch {
    // mock fallback
  }

  await new Promise((r) => setTimeout(r, 150))
  return {
    jci: { base: 9100, bull: 10000, bear: 7800, pe: 15, epsGrowth: "8%" },
    sectors: [
      { name: "Industrials", call: "OW" },
      { name: "Materials", call: "OW" },
      { name: "Consumer Staples & Discretionary", call: "OW" },
      { name: "Property & Real Estate", call: "OW" },
      { name: "Financials", call: "N" },
      { name: "Telecommunication Infrastructure", call: "OW" },
      { name: "Energy & Utilities", call: "UW" },
    ],
  }
}

export async function fetchSentiment(ticker: string): Promise<SentimentData> {
  const tk = ticker.toUpperCase().trim()
  try {
    const res = await fetch(`/api/sentiment?ticker=${tk}&days=14`, { headers: { Accept: "application/json" } })
    if (res.ok) {
      const data = await res.json()
      if (data && typeof data.gauge === "number") {
        const base = MOCK_SENTIMENTS[tk] || MOCK_SENTIMENTS.RATU
        return {
          ...base,
          ticker: tk,
          gauge: data.gauge,
          label: data.gauge > 60 ? "Bullish" : data.gauge < 40 ? "Bearish" : "Neutral",
          confidence: data.confidence || base.confidence,
        }
      }
    }
  } catch {
    // fallback
  }

  await new Promise((r) => setTimeout(r, 180))
  if (MOCK_SENTIMENTS[tk]) return MOCK_SENTIMENTS[tk]
  return {
    ticker: tk,
    name: `${tk} Tbk`,
    gauge: 55,
    label: "Neutral",
    confidence: 0.75,
    narratives: [
      { rank: 1, title: "Pembahasan kinerja fundamental kuartalan di forum ritel", sharePct: 50, sentiment: "neutral", realityCheck: "Data historis konsisten dengan disclosure IDX." },
      { rank: 2, title: "Ekspektasi dividen dan arus modal domestik", sharePct: 30, sentiment: "bull", realityCheck: "Payout ratio historis stabil." },
      { rank: 3, title: "Volatilitas sektoral dan pergerakan IHSG", sharePct: 20, sentiment: "neutral", realityCheck: "Korelasi beta terhadap IHSG terkontrol." },
    ],
    timeline: [
      { date: "2026-08-20", event: "Diskusi sentimen ritel terkini", impact: "+2 poin" },
      { date: "2026-08-28", event: "Update transaksi harian pasar reguler", impact: "+1 poin" },
    ],
    platforms: [
      { platform: "X (Twitter)", score: 55, label: "Neutral", volume: "1.2k posts", url: `https://x.com/search?q=%24${tk}` },
      { platform: "Reddit", score: 54, label: "Neutral", volume: "250 comments", url: `https://www.reddit.com/search/?q=${tk}+saham` },
      { platform: "Stockbit", score: 58, label: "Neutral", volume: "2.8k streams", url: `https://stockbit.com/symbol/${tk}` },
    ],
    retailVsThesis: {
      retailSentiment: "Sentimen ritel berada dalam zona netral",
      institutionalView: "Valuasi deterministik mendasari rekomendasi fundamental",
      alignment: "Moderate alignment",
    },
    disclaimer: "Sentiment data is derived from retail social signals and is for market intelligence only. Sentiment ≠ Investment Advice.",
  }
}

export async function submitChallenge(req: ChallengeRequest): Promise<ChallengeResponse> {
  const tk = req.ticker.toUpperCase().trim()
  try {
    const res = await fetch("/api/challenge", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker: tk, claim: req.claim, context: req.context }),
    })
    if (res.ok) {
      const data = await res.json()
      if (data && data.verdict) {
        return {
          ticker: tk,
          claim: req.claim,
          verdict: data.verdict === "defend" ? "defend" : "concede",
          evidence: data.evidence || "Evidence cited from institutional financial model.",
          exhibit_ref: data.exhibit_ref,
          source_citation: data.source_citation || data.note,
          correction: data.correction,
          debate_id: data.debate_id || `deb-${Date.now().toString(36)}`,
          timestamp: new Date().toISOString(),
        }
      }
    }
  } catch {
    // fallback to rich deterministic adversarial engine
  }

  await new Promise((r) => setTimeout(r, 320))
  const config = MOCK_DEFENSES[tk] || MOCK_DEFENSES.RATU
  const lowerClaim = req.claim.toLowerCase()
  const matched = config.patterns.some((p) => lowerClaim.includes(p))
  const template = matched ? config.defend : config.fallback

  return {
    ...template,
    ticker: tk,
    claim: req.claim,
    debate_id: `deb-${tk.toLowerCase()}-${Date.now().toString(36)}`,
    timestamp: new Date().toISOString(),
  }
}

export async function fetchMarketSentiment(): Promise<{
  averageGauge: number
  marketMood: string
  tickers: { ticker: string; name: string; gauge: number; label: string; volume: string; topNarrative: string }[]
}> {
  const tickers = (["MTEL", "BBCA", "CDIA", "RATU", "ADRO"] as Ticker[]).map((t) => {
    const s = MOCK_SENTIMENTS[t]
    return {
      ticker: t,
      name: s.name,
      gauge: s.gauge,
      label: s.label,
      volume: s.platforms.reduce((acc, p) => acc + parseInt(p.volume.replace(/[^0-9]/g, "") || "0"), 0).toLocaleString() + " signals",
      topNarrative: s.narratives[0]?.title || "Market narrative tracking",
    }
  })

  const avg = Math.round(tickers.reduce((sum, t) => sum + t.gauge, 0) / tickers.length)
  return {
    averageGauge: avg,
    marketMood: avg > 65 ? "Bullish Euphoria" : avg > 50 ? "Constructive Optimism" : "Defensive Caution",
    tickers,
  }
}

