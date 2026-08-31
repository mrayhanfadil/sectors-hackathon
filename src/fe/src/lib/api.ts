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

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") || ""

async function apiFetch<T>(path: string, fallback: () => Promise<T> | T): Promise<T> {
  const url = API_BASE ? `${API_BASE}${path}` : path
  try {
    const r = await fetch(url)
    if (!r.ok) throw new Error(String(r.status))
    return (await r.json()) as T
  } catch {
    return await fallback()
  }
}

const MOCK: Record<string, Report> = {

  RATU: { ticker: "RATU", name: "Ratu Prabu Energi (Oil & Gas)", price: 7150, target: 7880, upside: "+10.2%", rating: "BUY", summary: "Pure-play Cepu PSC — DCF 8.4% WACC + EV/EBITDA 22.6x. Bottom line +28% meski revenue -13%.", valuation: [{ method: "DCF", value: 7880, weight: 60 }, { method: "EV/EBITDA 22.6x", value: 6960, weight: 40 }], updatedAt: "2026-08-31" },
  CDIA: { ticker: "CDIA", name: "Chandra Daya Investasi (Conglomerate)", price: 742, target: 815, upside: "+9.8%", rating: "BUY", summary: "SOTP 4 pilar Energy/Water/Port/Logistics — DCF 815 + DDM 810. Segment mix Energy 55% / Logistics +44.7%.", valuation: [{ method: "DCF", value: 815 }, { method: "DDM", value: 810 }], updatedAt: "2026-08-31" },
  MTEL: { ticker: "MTEL", name: "Dayamitra Telekomunikasi (Tower)", price: 460, target: 635, upside: "+38.0%", rating: "BUY", summary: "Infra recurring — blended DCF 60% + EV/EBITDA 10x 40% → 635. Tenancy 1.57x, fiber 59,239 km.", valuation: [{ method: "DCF 60%", value: 630 }, { method: "EV/EBITDA 10x 40%", value: 635 }], updatedAt: "2026-08-31" },
  BBCA: { ticker: "BBCA", name: "Bank Central Asia", price: 7890, target: 9600, upside: "+21.9%", rating: "BUY", summary: "GGM P/BV (ROE-g)/(CoE-g) — 8p Samuel pack. Bank comp peer avg P/BV 3.3x.", valuation: [{ method: "GGM P/BV", value: 9600 }], updatedAt: "2026-08-31" },
  ADRO: { ticker: "ADRO", name: "Adaro Energy (SOTP spin-off)", price: 2080, target: 2450, upside: "+17.8%", rating: "BUY", summary: "BRIDS SOTP AADI US$6.1bn + post-spin holdco discount — dual DCF+SOTP.", valuation: [{ method: "SOTP", value: 2450 }], updatedAt: "2026-08-31" },
}

export async function fetchReport(ticker: string): Promise<Report> {
  const k = ticker.toUpperCase()
  const live = await apiFetch<Report>(`/api/report/${encodeURIComponent(k)}`, async () => {
    await new Promise(r => setTimeout(r, 120))
    if (MOCK[k]) return MOCK[k]
    return { ticker: k, name: `${k} — Synthetic`, price: 1000, target: 1200, upside: "+20%", rating: "BUY", summary: "Synthetic placeholder — data seed=42.", valuation: [{ method: "DCF", value: 1200 }], updatedAt: "2026-08-31" }
  })
  // BE returns { ticker, template, price, fair_value, upside_pct, rating, valuation: { method, fair_value, assumptions } }
  // Normalize to FE Report shape
  const anyLive = live as unknown as Record<string, unknown>
  if (anyLive && typeof anyLive["fair_value"] === "number") {
    const fv = anyLive["fair_value"] as number
    const price = (anyLive["price"] as number) || (MOCK[k]?.price ?? 1000)
    const upside = anyLive["upside_pct"] as number | null
    const val = anyLive["valuation"] as Record<string, unknown> | undefined
    return {
      ticker: k,
      name: MOCK[k]?.name ?? `${k} — Live`,
      price,
      target: Math.round(fv),
      upside: upside != null ? `${upside > 0 ? "+" : ""}${upside.toFixed(1)}%` : "—",
      rating: (anyLive["rating"] as Report["rating"]) ?? "HOLD",
      summary: MOCK[k]?.summary ?? `Live DCF engine — ${(val?.["method"] as string) ?? "dcf"}`,
      valuation: [{ method: String(val?.["method"] ?? "DCF"), value: Math.round(fv) }],
      updatedAt: String(anyLive["generated_at"] ?? new Date().toISOString().slice(0,10)),
    }
  }
  return live
}
export async function fetchOutlook(): Promise<{ jci: { base: number; bull: number; bear: number; pe: number; epsGrowth: string }; sectors: { name: string; call: string }[]; picks: unknown[]; jci_price?: unknown }> {
  return apiFetch("/api/outlook", async () => {
    await new Promise(r => setTimeout(r, 80))
    return { jci: { base: 9100, bull: 10000, bear: 7800, pe: 15, epsGrowth: "8%" }, sectors: [{ name: "Industrials", call: "OW" }, { name: "Materials", call: "OW" }, { name: "Consumer", call: "OW" }, { name: "Property", call: "OW" }, { name: "Financials", call: "N" }, { name: "Energy", call: "UW" }], picks: [] as unknown[] } as unknown as Awaited<ReturnType<typeof fetchOutlook>>
  })
}
export async function fetchSentiment(ticker: string): Promise<{ ticker: string; gauge: number; label?: string; narratives: string[]; timeline: { date: string; note: string }[]; sources: { platform: string; url: string }[] }> {
  const k = ticker.toUpperCase()
  return apiFetch(`/api/sentiment?ticker=${encodeURIComponent(k)}`, async () => {
    await new Promise(r => setTimeout(r, 80))
    return { ticker: k, gauge: 62, label: "Bullish", narratives: ["Danantara catalyst rotation", "Earnings beat chatter on Stockbit", "Foreign flow UW reversal watch"], timeline: [{ date: "2026-08-24", note: "BBCA earnings thread +1.2k likes" }, { date: "2026-08-28", note: "Danantara $12bn dry powder narrative" }], sources: [{ platform: "X", url: `https://x.com/search?q=%24${k}` }, { platform: "Reddit", url: `https://www.reddit.com/search/?q=${k}` }] } as unknown as Awaited<ReturnType<typeof fetchSentiment>>
  })
}
