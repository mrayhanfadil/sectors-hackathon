// Universe emiten IDX untuk /agent — sumber: GET /api/tickers (Sectors universe feed).
// (data/assumptions/*.json) kalau endpoint belum kebaca.

export interface UniverseTicker {
  kode: string
  nama: string | null
  sector: string | null
}

// Full engines: DCF/SOTP/infra/bank/coal + fixtures + template archetype.
export const ENGINE_TICKERS = ["ADRO", "BBCA", "CDIA", "MTEL", "POWR", "RATU"] as const

// Kompat: dropdown 6-only sebelum universe datang.
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
      if (!Array.isArray(j.tickers) || j.tickers.length === 0) throw new Error("empty universe")
      _cache = j.tickers
    } catch {
      _cache = fallback()
    }
    return _cache
  })()
  return _inflight
}

export function optionLabel(t: UniverseTicker): string {
  return t.nama ? `${t.kode} — ${t.nama}` : t.kode
}

export function isEngineTicker(kode: string): boolean {
  return (ENGINE_TICKERS as readonly string[]).includes(kode)
}

export function normalizeTicker(raw: unknown, known?: readonly string[]): string {
  const t = String(raw ?? "")
    .toUpperCase()
    .trim()
  const list = known ?? ENGINE_TICKERS
  // TIDAK ada fallback: ticker asing = string kosong = tidak bisa jalan.
  return (list as readonly string[]).includes(t) ? t : ""
}
