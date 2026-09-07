export type Ticker = "RATU" | "CDIA" | "MTEL" | "BBCA" | "ADRO"

// --- enriched report type ---
export type Report = {
  ticker: string
  name: string
  price: number | null
  target: number | null
  upside: string | null
  rating: "BUY" | "HOLD" | "SELL" | string | null
  summary: string
  valuation: { method: string; value: number; weight?: number }[]
  updatedAt: string
  source?: string
  offline?: boolean
  // enriched optional
  template?: string
  cover?: {
    rating_box?: { action: string; tp: number; price: number; upside_pct: number; prev_tp?: number | null; key_takeaways?: string[] }
    vs_jci?: { ytd_abs?: number | null; ytd_rel?: number | null; source?: string; chart?: { labels: string[]; series: number[][] } | null }
    shares?: { outstanding: number; unit: string; free_float_pct?: number }
    shareholders?: { name: string; pct: number }[]
    shareholders_src?: string | null
    esg?: { found: boolean; scores?: { e: number; s: number; g: number }; source?: string; date?: string }
  }
  segments?: { name: string; revenue?: number; share_pct?: number; yoy_pct?: number | string; qoq_pct?: number | string; row?: unknown[]; one_off?: string }[]
  kpis?: { name: string; value: number; prev?: number; unit?: string; formula?: string; row?: unknown[]; source?: string }[]
  kpi?: unknown
  valuationDetail?: {
    methods?: { method: string; fv: number; assumptions?: Record<string, unknown>; table?: { headers: string[]; rows: unknown[][]; footers?: unknown[][] }; source?: string }[]
    blended?: { weights: Record<string, number>; fv: number; fv_str?: string; margin_of_safety_pct?: number; rows?: unknown[][]; source?: string; weights_sum_100?: boolean } | null
    bands?: { pbv_3y?: { "std+2": number; "std+1": number; avg: number; "std-1": number; "std-2": number; current: number; label: string }; source?: string } | null
    ggm?: { pbv_implied: number; fv_per_share: number; formula: string; assumptions?: Record<string, unknown> } | null
    assumptions?: Record<string, unknown>
    dcf?: unknown
    ev?: unknown
    provenance?: string
  }
  ratios?: Record<string, number | string>
  forecast_revision?: unknown
  cover_boxes?: unknown
  raw?: Record<string, unknown>
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

// Live-only: laporan dibaca apa adanya dari BE, gagal = objek offline jujur.

// --- live-only helpers (tanpa fixture, tanpa angka fabrikasi) ---
// BE /api/report/{ticker} dikembalikan apa adanya; field kosong = kosong, bukan ditempel fixture.
function liveSegments(raw: Record<string, unknown>): Report["segments"] {
  const s = raw["segments"] as unknown
  if (Array.isArray(s)) return s as Report["segments"]
  if (s && typeof s === "object" && Array.isArray((s as Record<string, unknown>)["segments"])) {
    return (s as Record<string, unknown>)["segments"] as Report["segments"]
  }
  return []
}

function liveKpis(raw: Record<string, unknown>): Report["kpis"] {
  const k = (raw["kpis"] ?? raw["kpi"]) as unknown
  if (Array.isArray(k)) {
    if (k.length === 0) return []
    if (typeof k[0] === "object" && k[0] !== null && "name" in (k[0] as Record<string, unknown>)) {
      return k as Report["kpis"]
    }
    return []
  }
  return []
}

function liveValuationDetail(raw: Record<string, unknown>): Report["valuationDetail"] {
  type VD = NonNullable<Report["valuationDetail"]>
  const val = (raw["valuation"] as Record<string, unknown>) ?? {}
  const methods: VD["methods"] = []
  const dcf = val["dcf"] as Record<string, unknown> | undefined
  if (dcf && typeof dcf === "object") {
    const fv = Number(dcf["fv_per_share"] ?? dcf["fv"] ?? 0)
    if (fv) methods.push({ method: "DCF", fv, assumptions: (val["assumptions"] as Record<string, unknown>) ?? {}, source: "engines.dcf" })
  }
  const ev = val["ev"] as Record<string, unknown> | undefined
  if (ev && typeof ev === "object") {
    const fv = Number(ev["fv_per_share"] ?? ev["fv"] ?? 0)
    if (fv) methods.push({ method: "EV/EBITDA", fv, source: "engines.ev_ebitda" })
  }
  const blendedRaw = val["blended"] as Record<string, unknown> | null | undefined
  let blended: VD["blended"] = null
  if (blendedRaw && typeof blendedRaw === "object") {
    const bv = Number(blendedRaw["blended"] ?? 0) || Number(raw["fair_value"] ?? 0) || 0
    if (bv) {
      blended = {
        weights: (blendedRaw["weights"] as Record<string, number>) ?? {},
        fv: bv,
        fv_str: String(Math.round(bv)),
        margin_of_safety_pct: (blendedRaw["margin_of_safety_pct"] as number) ?? undefined,
        source: "engines.blended",
      }
    }
  }
  return {
    methods,
    blended,
    bands: ((val["bands"] ?? raw["bands"] ?? null) as VD["bands"]),
    ggm: ((val["ggm"] ?? null) as VD["ggm"]),
    assumptions: val["assumptions"] as Record<string, unknown> | undefined,
    dcf: val["dcf"],
    ev: val["ev"],
    provenance: val["provenance"] as string | undefined,
  }
}

export async function fetchReport(ticker: string): Promise<Report> {
  const k = ticker.toUpperCase()
  const live = await apiFetch<Report>(`/api/report/${encodeURIComponent(k)}`, async () => {
    // Honest offline fallback - NEVER fabricated numbers
    return {
      ticker: k,
      name: `${k} - Offline`,
      price: null,
      target: null,
      upside: null,
      rating: null,
      summary: `BE tidak tersedia saat ini. Data untuk ${k} belum dapat dimuat - coba lagi nanti atau buka langsung https://report.server-fadil.my.id/api/report/${k}`,
      valuation: [],
      updatedAt: new Date().toISOString().slice(0, 10),
      source: "offline",
      offline: true,
    } as Report
  })
  if (live.offline) {
    return live
  }
  const anyLive = live as unknown as Record<string, unknown>
  if (anyLive && typeof anyLive["fair_value"] === "number") {
    const fv = anyLive["fair_value"] as number
    const price = (anyLive["price"] as number) || 0
    const upside = anyLive["upside_pct"] as number | null
    const val = anyLive["valuation"] as Record<string, unknown> | undefined
    const base: Report = {
      ticker: k,
      name: (anyLive["company_name"] as string) || (anyLive["name"] as string) || `${k} - Live`,
      price,
      target: Math.round(fv),
      upside: upside != null ? `${upside > 0 ? "+" : ""}${upside.toFixed(1)}%` : "-",
      rating: (anyLive["rating"] as Report["rating"]) ?? "HOLD",
      summary: (anyLive["summary"] as string) || `Live DCF engine - ${(val?.["method"] as string) ?? "dcf"}`,
      valuation: [{ method: String(val?.["method"] ?? "DCF"), value: Math.round(fv) }],
      updatedAt: String(anyLive["generated_at"] ?? new Date().toISOString().slice(0, 10)),
      source: (anyLive["source"] as string) ?? "live",
    }
    const withLive: Report = {
      ...base,
      template: (anyLive["template"] as string) ?? "single",
      cover: (anyLive["cover"] as Report["cover"]) ?? undefined,
      segments: liveSegments(anyLive),
      kpis: liveKpis(anyLive),
      kpi: (anyLive["kpi"] ?? anyLive["kpis"] ?? undefined) as Report["kpi"],
      valuationDetail: liveValuationDetail(anyLive),
      ratios: ((anyLive["ratios"] as Report["ratios"]) ?? {}) as Report["ratios"],
      raw: anyLive,
    }
    return withLive
  }
  // sudah bentuk Report — kembalikan apa adanya, tanpa fixture
  return live
}

// --- outlook ---
export type Outlook = {
  jci: { base: number; bull: number; bear: number; pe: number; epsGrowth: string }
  sectors: { name: string; call: string }[]
  picks: unknown[]
  jci_price?: unknown
  thematics?: { name: string; detail: string; source?: string }[]
  flows?: { narrative: string; table?: { headers: string[]; rows: unknown[][] }; source?: string }
  danantara?: { narrative: string; table?: { headers: string[]; rows: unknown[][] }; source?: string }
  source?: string
  raw?: unknown
  offline?: boolean
  note?: string
}

// Live-only: outlook dibaca apa adanya dari BE, gagal = objek offline jujur.

export async function fetchOutlook(): Promise<Outlook> {
  // live-only: BE /api/outlook apa adanya; gagal = objek offline jujur, bukan angka fixture
  const live = await apiFetch<Record<string, unknown> | null>("/api/outlook", async () => null)
  if (!live) {
    return {
      jci: { base: 0, bull: 0, bear: 0, pe: 0, epsGrowth: "-" },
      sectors: [],
      picks: [],
      thematics: [],
      source: "offline",
      offline: true,
      note: "BE tidak tersedia saat ini — outlook belum dapat dimuat. Coba lagi nanti.",
    }
  }
  const num = (v: unknown): number => {
    const n = Number(v)
    return Number.isFinite(n) ? n : 0
  }
  const jciLive = live["jci"] as Record<string, unknown> | undefined
  const epsLive = live["eps_growth"]
  const epsStr = typeof jciLive?.["epsGrowth"] === "string" ? (jciLive["epsGrowth"] as string) : "-"
  const jci = {
    base: num(live["jci_base"] ?? live["jci_target"] ?? jciLive?.["base"]),
    bull: num(live["jci_bull"] ?? jciLive?.["bull"]),
    bear: num(live["jci_bear"] ?? jciLive?.["bear"]),
    pe: num(live["pe"] ?? jciLive?.["pe"]),
    epsGrowth: epsLive != null ? `${Math.round(Number(epsLive) * 100)}%` : epsStr,
  }
  const ow = (live["ow"] as string[]) ?? []
  const uw = (live["uw"] as string[]) ?? []
  const neutral = (live["neutral"] as string[]) ?? []
  const sectors = [
    ...ow.map((n: string) => ({ name: n, call: "OW" })),
    ...neutral.map((n: string) => ({ name: n, call: "N" })),
    ...uw.map((n: string) => ({ name: n, call: "UW" })),
  ]
  const picks = (live["picks"] as unknown[]) ?? []
  const strat = (live["strategy"] as Record<string, unknown>) ?? {}
  const thematics = ((strat["thematics"] ?? live["thematics"] ?? []) as Outlook["thematics"])
  const flows = ((strat["flows"] ?? live["flows"]) as Outlook["flows"])
  const danantara = ((strat["danantara"] ?? live["danantara"]) as Outlook["danantara"])
  return {
    jci,
    sectors,
    picks,
    jci_price: live["jci_price"],
    thematics,
    flows,
    danantara,
    source: (live["source"] as string) ?? "live",
    raw: live,
  }
}

export type Sentiment = {
  ticker: string
  gauge: number | null
  label?: string | null
  narratives: string[]
  top_narratives?: string[]
  timeline: { date: string; note: string }[]
  sources: { platform: string; url: string }[]
  items?: {
    platform?: string
    text?: string
    sentiment?: string
    date?: string
    url?: string
    score?: number
    timestamp?: string
    author?: string
  }[]
  confidence?: number | null
  empty?: boolean
  note?: string
}

export async function fetchSentiment(ticker: string): Promise<Sentiment> {
  const k = ticker.toUpperCase()
  return apiFetch<Sentiment>(`/api/sentiment?ticker=${encodeURIComponent(k)}`, async () => {
    return {
      ticker: k,
      gauge: null,
      label: null,
      narratives: [],
      timeline: [],
      sources: [],
      empty: true,
      note: "Sentiment belum tersedia - BE offline atau news Harvester belum return hasil.",
    }
  })
}

// --- pdf ---
export async function fetchPdf(ticker: string): Promise<void> {
  const tk = ticker.toUpperCase()
  const path = `/api/report/${encodeURIComponent(tk)}/pdf`
  const url = API_BASE ? `${API_BASE}${path}` : path
  let r: Response
  try {
    r = await fetch(url)
  } catch (e) {
    throw new Error(`network error - PDF endpoint unreachable (${API_BASE || "same-origin"}${path} - is the API up? ${(e as Error)?.message ?? String(e)})`)
  }
  if (!r.ok) {
    const text = await r.text().catch(() => "")
    // surface real backend message + hint
    const hint = r.status === 404 ? " - check API url / tunnel" : r.status >= 500 ? " - server error" : ""
    throw new Error((text?.slice(0, 400) || `PDF not available (${r.status})`) + hint)
  }
  // defensive: backend sometimes returns JSON error with 200
  const ctype = r.headers.get("content-type") || ""
  if (ctype.includes("application/json")) {
    const j = await r.json().catch(() => null) as Record<string, unknown> | null
    throw new Error((j?.["detail"] as string) || (j?.["message"] as string) || `unexpected JSON from PDF endpoint`)
  }
  const blob = await r.blob()
  const cd = r.headers.get("content-disposition") || ""
  const m = cd.match(/filename=\"?([^\";]+)\"?/i)
  const filename = m?.[1] || `${tk}_report.pdf`
  const href = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = href
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(href), 4000)
}

// --- adk report log ---
export type ReportLogItem = {
  run_id: string
  status: "completed" | "interrupted" | "failed" | "running" | string
  started_at: number
  finished_at: number | null
  duration_s: number | null
  provider: string
  model: string
  n_events: number
  last_text_preview: string | null
  error: string | null
}

export type ReportLogHistoryItem = {
  run_id: string
  status: string
  started_at: number
  n_events: number
  duration_s: number | null
}

export type ReportLogResponse = {
  ticker: string
  has_run: boolean
  log: ReportLogItem | null
  history: ReportLogHistoryItem[]
}

export async function fetchReportLog(ticker: string): Promise<ReportLogResponse> {
  const base = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") || ""
  try {
    const res = await fetch(`${base}/api/report/${encodeURIComponent(ticker.toUpperCase())}/log`)
    if (!res.ok) throw new Error(String(res.status))
    return await res.json()
  } catch {
    return {
      ticker: ticker.toUpperCase(),
      has_run: false,
      log: null,
      history: [],
    }
  }
}

// ---------------------------------------------------------------------------
// Sectors API v2 — single data gateway (see server/sectors.py)
// ---------------------------------------------------------------------------

export type DividendItem = {
  ex_date: string
  payment_date: string
  amount_per_share: number
  currency: string
  type: string
}

export type StockSplitItem = {
  date: string
  ratio: number
}

export type AgmItem = {
  date: string
  type: string
  agenda: string
}

export type CorporateActionsResponse = {
  dividend: DividendItem[]
  upcoming_dividend?: unknown[]
  stock_split?: StockSplitItem[]
  right_issue?: unknown[]
  warrant?: unknown[]
  bonus?: unknown[]
  agm?: AgmItem[]
  symbol: string
  note?: string
}

export type QuarterlyFinancialItem = {
  symbol: string
  date: string
  revenue: number | null
  earnings: number | null
  total_assets: number | null
  total_equity: number | null
  operating_cash_flow: number | null
  non_interest_income?: number | null
  operating_expense?: number | null
  operating_pnl?: number | null
  earnings_before_tax?: number | null
  tax?: number | null
  gross_profit?: number | null
  ebit?: number | null
  ebitda?: number | null
  cost_of_revenue?: number | null
  total_liabilities?: number | null
  total_debt?: number | null
  stockholders_equity?: number | null
  cash_only?: number | null
  current_liabilities?: number | null
  total_current_asset?: number | null
  financing_cash_flow?: number | null
  investing_cash_flow?: number | null
  net_cash_flow?: number | null
}

export type QuarterlyFinancialsResponse = {
  pagination: {
    limit: number
    offset: number
    total: number
  }
  data: QuarterlyFinancialItem[]
  note?: string
}

export type NewsArticleItem = {
  title: string
  body: string
  source: string
  timestamp: string
  sector?: string
  sub_sector?: string[]
  tags?: string[]
  symbols?: string[]
  thumbnail?: string | null
  dimension?: {
    sentiment: "bullish" | "bearish" | "neutral" | string
    relevance: number
  }
}

export type NewsResponse = {
  pagination: {
    limit: number
    offset: number
    total: number
  }
  data: NewsArticleItem[]
  note?: string
}

export async function fetchDividends(ticker: string): Promise<CorporateActionsResponse> {
  const tk = ticker.toUpperCase().trim()
  return apiFetch<CorporateActionsResponse>(
    `/api/corporate-actions?symbol=${encodeURIComponent(tk)}`,
    () => ({
      dividend: [],
      upcoming_dividend: [],
      stock_split: [],
      right_issue: [],
      warrant: [],
      bonus: [],
      agm: [],
      symbol: tk,
      note: `BE tidak tersedia saat ini — corporate actions ${tk} belum dapat dimuat.`,
    })
  )
}

export async function fetchQuarterly(ticker: string, nQuarters = 8): Promise<QuarterlyFinancialsResponse> {
  const tk = ticker.toUpperCase().trim()
  return apiFetch<QuarterlyFinancialsResponse>(
    `/api/quarterly-financials?symbol=${encodeURIComponent(tk)}&n_quarters=${nQuarters}`,
    () => ({
      pagination: { limit: nQuarters, offset: 0, total: 0 },
      data: [],
      note: `BE tidak tersedia saat ini — quarterly financials ${tk} belum dapat dimuat.`,
    })
  )
}

export async function fetchNews(ticker: string, limit = 30): Promise<NewsResponse> {
  const tk = ticker.toUpperCase().trim()
  // live-only: BE /api/news (harvester) — bukan endpoint tiruan; gagal = feed kosong jujur
  const live = await apiFetch<{ items?: Record<string, unknown>[]; note?: string; source?: string }>(
    `/api/news?ticker=${encodeURIComponent(tk)}&limit=${limit}`,
    () => ({ items: [], note: `BE tidak tersedia saat ini — berita ${tk} belum dapat dimuat.` })
  )
  const items = Array.isArray(live.items) ? live.items : []
  return {
    pagination: { limit, offset: 0, total: items.length },
    data: items.map((it) => ({
      title: String(it["title"] ?? "-"),
      body: String(it["snippet"] ?? it["body"] ?? ""),
      source: String(it["source"] ?? "unknown"),
      timestamp: String(it["date"] ?? it["timestamp"] ?? ""),
      symbols: [tk],
      tags: [],
      dimension: { sentiment: "neutral", relevance: Number(it["relevance"] ?? 0) },
    })),
    note: live.note ?? (live.source ? `Sumber: ${live.source}` : undefined),
  }
}

// ---------------------------------------------------------------------------
// DCF Friend-Style Engine Types & API
// ---------------------------------------------------------------------------

export type DcfWaccResult = {
  rf: number
  beta: number
  erp: number
  cod: number
  ke: number
  kd_pretax: number
  kd_aftertax: number
  tax_rate: number
  size_premium: number
  equity_value_mkt?: number
  debt_book?: number
  weight_equity: number
  weight_debt: number
  wacc_raw?: number
  wacc: number
  warnings?: string[]
  provenance?: string
}

export type DcfWaccTableRow = {
  label: string
  value: string
}

export type DcfProjectionRow = {
  year: number
  growth: number
  revenue: number
  ebit: number
  ebit_margin: number
  nopat: number
  da: number
  capex: number
  nwc: number
  delta_nwc: number
  fcff: number
  reinvestment_rate?: number | null
  roic?: number | null
  implied_growth?: number | null
}

export type DcfTerminal = {
  value?: number | null
  pv?: number | null
  implied_ev_ebitda?: number | null
  dependency_pct?: number | null
  dependency_flag?: boolean
}

export type DcfValuation = {
  pv_explicit?: number | null
  pv_terminal?: number | null
  enterprise_value?: number | null
  cash?: number | null
  total_debt?: number | null
  minority?: number | null
  equity_value?: number | null
  fair_value_per_share?: number | null
  market_price?: number | null
  upside?: number | null
}

export type DcfRecommendation = {
  rating: "BUY" | "HOLD" | "SELL" | "Review Required" | string
  upside?: number | null
  label?: string
  note?: string
  reason_override?: string
}

export type DcfSensitivity = {
  fair_value: (number | null)[][]
  upside: (number | null)[][]
  wacc_axis: number[]
  g_axis: number[]
  stats?: {
    min?: number | null
    max?: number | null
    median?: number | null
    n_valid?: number
    n_cells?: number
  }
}

export type DcfScenarioItem = {
  scenario: "BEAR" | "BASE" | "BULL" | string
  revenue_growth_y1: number
  ebit_margin: number
  terminal_growth: number
  fair_value_per_share: number | null
  upside: number | null
  rating: string
  note?: string
}

export type DcfFriendPayload = {
  wacc: DcfWaccResult
  wacc_table: DcfWaccTableRow[]
  projection: DcfProjectionRow[]
  terminal: DcfTerminal
  valuation: DcfValuation
  recommendation: DcfRecommendation
  sensitivity: DcfSensitivity
  scenarios: Record<string, DcfScenarioItem>
  provenance?: string
  error?: string
}

export async function fetchDcfFull(ticker: string): Promise<DcfFriendPayload | { error: string }> {
  const base = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") || ""
  const r = await fetch(`${base}/api/dcf/${encodeURIComponent(ticker)}`)
  if (!r.ok) return { error: `HTTP ${r.status}` }
  return await r.json()
}


