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

const MOCK: Record<string, Report> = {
  RATU: { ticker: "RATU", name: "Ratu Prabu Energi (Oil & Gas)", price: 7150, target: 7880, upside: "+10.2%", rating: "BUY", summary: "Pure-play Cepu PSC — DCF 8.4% WACC + EV/EBITDA 22.6x. Bottom line +28% meski revenue -13%.", valuation: [{ method: "DCF", value: 7880, weight: 60 }, { method: "EV/EBITDA 22.6x", value: 6960, weight: 40 }], updatedAt: "2026-08-31" },
  CDIA: { ticker: "CDIA", name: "Chandra Daya Investasi (Conglomerate)", price: 742, target: 815, upside: "+9.8%", rating: "BUY", summary: "SOTP 4 pilar Energy/Water/Port/Logistics — DCF 815 + DDM 810. Segment mix Energy 55% / Logistics +44.7%.", valuation: [{ method: "DCF", value: 815 }, { method: "DDM", value: 810 }], updatedAt: "2026-08-31" },
  MTEL: { ticker: "MTEL", name: "Dayamitra Telekomunikasi (Tower)", price: 460, target: 635, upside: "+38.0%", rating: "BUY", summary: "Infra recurring — blended DCF 60% + EV/EBITDA 10x 40% → 635. Tenancy 1.57x, fiber 59,239 km.", valuation: [{ method: "DCF 60%", value: 630 }, { method: "EV/EBITDA 10x 40%", value: 635 }], updatedAt: "2026-08-31" },
  BBCA: { ticker: "BBCA", name: "Bank Central Asia", price: 7890, target: 9600, upside: "+21.9%", rating: "BUY", summary: "GGM P/BV (ROE-g)/(CoE-g) — 8p Samuel pack. Bank comp peer avg P/BV 3.3x.", valuation: [{ method: "GGM P/BV", value: 9600 }], updatedAt: "2026-08-31" },
  ADRO: { ticker: "ADRO", name: "Adaro Energy (SOTP spin-off)", price: 2080, target: 2450, upside: "+17.8%", rating: "BUY", summary: "BRIDS SOTP AADI US$6.1bn + post-spin holdco discount — dual DCF+SOTP.", valuation: [{ method: "SOTP", value: 2450 }], updatedAt: "2026-08-31" },
}

export async function fetchReport(ticker: string): Promise<Report> {
  await new Promise(r => setTimeout(r, 280))
  const k = ticker.toUpperCase()
  if (MOCK[k]) return MOCK[k]
  return { ticker: k, name: `${k} — Synthetic`, price: 1000, target: 1200, upside: "+20%", rating: "BUY", summary: "Synthetic placeholder — data seed=42.", valuation: [{ method: "DCF", value: 1200 }], updatedAt: "2026-08-31" }
}
export async function fetchOutlook() {
  await new Promise(r => setTimeout(r, 180))
  return { jci: { base: 9100, bull: 10000, bear: 7800, pe: 15, epsGrowth: "8%" }, sectors: [{ name: "Industrials", call: "OW" }, { name: "Materials", call: "OW" }, { name: "Consumer", call: "OW" }, { name: "Property", call: "OW" }, { name: "Financials", call: "N" }, { name: "Energy", call: "UW" }] }
}
export async function fetchSentiment(ticker: string) {
  await new Promise(r => setTimeout(r, 180))
  return { ticker: ticker.toUpperCase(), gauge: 62, label: "Bullish", narratives: ["Danantara catalyst rotation", "Earnings beat chatter on Stockbit", "Foreign flow UW reversal watch"], timeline: [{ date: "2026-08-24", note: "BBCA earnings thread +1.2k likes" }, { date: "2026-08-28", note: "Danantara $12bn dry powder narrative" }], sources: [{ platform: "X", url: "https://x.com/search?q=%24BBCA" }, { platform: "Reddit", url: "https://www.reddit.com/search/?q=BBCA" }] }
}
