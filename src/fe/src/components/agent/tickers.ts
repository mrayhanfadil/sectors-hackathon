// Daftar emiten IDX untuk /agent - sumber: GET /api/tickers.

export interface UniverseTicker {
  kode: string
  nama: string | null
  sector: string | null
}

export type TickerInfo = UniverseTicker

// Full engines: DCF/SOTP/infra/bank/coal + fixtures + template archetype.
export const ENGINE_TICKERS = ["ADRO", "BBCA", "CDIA", "MTEL", "POWR", "RATU"] as const

// Kompat: dropdown sebelum daftar emiten datang.
export const SUPPORTED_TICKERS = ENGINE_TICKERS

let _cache: UniverseTicker[] | null = null
let _inflight: Promise<UniverseTicker[]> | null = null

function fallback(): UniverseTicker[] {
  return ENGINE_TICKERS.map((kode) => ({ kode, nama: null, sector: null }))
}

export function fetchUniverse(apiBase: string): Promise<UniverseTicker[]> {
  if (_cache) return Promise.resolve(_cache)
  if (_inflight) return _inflight
  _inflight = (async () => {
    try {
      const r = await fetch(`${apiBase}/api/tickers`)
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      const j = (await r.json()) as { tickers?: UniverseTicker[] }
      if (!Array.isArray(j.tickers) || j.tickers.length === 0) throw new Error("empty list")
      _cache = j.tickers
    } catch {
      _cache = fallback()
    }
    return _cache
  })()
  return _inflight
}

export function optionLabel(t: UniverseTicker): string {
  return t.nama ? `${t.kode} - ${t.nama}` : t.kode
}

export function isEngineTicker(kode: string): boolean {
  return (ENGINE_TICKERS as readonly string[]).includes(kode)
}

export function normalizeTicker(raw: unknown, known?: readonly string[]): string {
  const t = String(raw ?? "")
    .toUpperCase()
    .trim()
  if (!t) return ""
  if (known && known.length > 0) {
    return known.includes(t) ? t : t
  }
  return /^[A-Z]{4}$/.test(t) ? t : ""
}
