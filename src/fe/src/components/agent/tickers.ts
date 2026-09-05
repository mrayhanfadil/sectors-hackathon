// Allowlist emiten yang punya assumptions + engine lengkap di BE.
// Sumber: data/assumptions/*.json. Jangan tambah ticker di sini tanpa
// menambah assumptions + fixtures BE-nya (hasilnya SELL + data sintetis).
export const SUPPORTED_TICKERS = ["ADRO", "BBCA", "CDIA", "MTEL", "POWR", "RATU"] as const

export type SupportedTicker = (typeof SUPPORTED_TICKERS)[number]

export const DEFAULT_TICKER: SupportedTicker = "BBCA"

export function normalizeTicker(raw: unknown): SupportedTicker {
  const t = String(raw ?? "").toUpperCase().trim()
  return (SUPPORTED_TICKERS as readonly string[]).includes(t) ? (t as SupportedTicker) : DEFAULT_TICKER
}
