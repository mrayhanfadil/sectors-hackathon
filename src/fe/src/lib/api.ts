export type Ticker = "RATU" | "CDIA" | "MTEL" | "BBCA" | "ADRO"

// ——— enriched report type ———
export type Report = {
  ticker: string
  name: string
  price: number
  target: number
  upside: string
  rating: "BUY" | "HOLD" | "SELL" | string
  summary: string
  valuation: { method: string; value: number; weight?: number }[]
  updatedAt: string
  // enriched optional
  template?: string
  source?: string
  cover?: {
    rating_box?: { action: string; tp: number; price: number; upside_pct: number; prev_tp?: number | null; key_takeaways?: string[] }
    vs_jci?: { ytd_abs?: number; ytd_rel?: number; source?: string; chart?: { labels: string[]; series: number[][] } }
    shares?: { outstanding: number; unit: string; free_float_pct?: number }
    shareholders?: { name: string; pct: number }[]
    shareholders_src?: string
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

// —— fixed fixtures (mirror scripts/report_fixtures.py, light — enough for cards when BE gaps) ——
const FIXTURE_COVER: Record<string, Report["cover"]> = {
  RATU: {
    rating_box: { action: "BUY", tp: 7880, price: 6200, upside_pct: 27.1, prev_tp: null, key_takeaways: [] },
    vs_jci: { ytd_abs: 18.4, ytd_rel: 6.2, source: "IDX, yfinance (RATU.JK vs ^JKSE)", chart: { labels: ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agt","Sep","Okt","Nov","Des"], series: [[0,4,9,12,15,18,21,19,22,24,26,27],[0,2,5,6,8,9,11,12,12,13,14,15]] } },
    shares: { outstanding: 2.71, unit: "bn", free_float_pct: 31.2 },
    shareholders: [{ name: "Publik", pct: 31.2 }, { name: "RETJ", pct: 45.0 }, { name: "PJUC", pct: 23.8 }],
    shareholders_src: "IDX — struktur pemegang saham",
    esg: { found: false },
  },
  CDIA: {
    rating_box: { action: "HOLD", tp: 815, price: 780, upside_pct: 4.5, prev_tp: null, key_takeaways: [] },
    vs_jci: { ytd_abs: -62.9, ytd_rel: -30.9, source: "IDX, yfinance (CDIA.JK vs ^JKSE)", chart: { labels: ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agt","Sep","Okt","Nov","Des"], series: [[0,-12,-28,-41,-50,-55,-60,-58,-61,-62,-63,-63],[0,2,5,6,8,9,11,12,12,13,14,15]] } },
    shares: { outstanding: 15.0, unit: "bn", free_float_pct: 10.1 },
    shareholders: [{ name: "Publik", pct: 10.1 }, { name: "Chandra Asri", pct: 62.3 }, { name: "Lainnya", pct: 27.6 }],
    shareholders_src: "IDX — struktur pemegang saham",
    esg: { found: false },
  },
  MTEL: {
    rating_box: {
      action: "BUY", tp: 635, price: 460, upside_pct: 38.0, prev_tp: 705,
      key_takeaways: [
        "PST & UMT merger efektif 1 Jul 2026 membuka efisiensi opex/capex dan tenancy >1.6x.",
        "Spectrum 700MHz/2.6GHz berpotensi menambah 3.000-3.500 tenant (+Rp 360-420 bn) by FY27-29.",
        "DCF 60% + EV/EBITDA 40% blended TP Rp 635, margin of safety 15%.",
      ],
    },
    vs_jci: { ytd_abs: 12.1, ytd_rel: -2.9, source: "IDX, yfinance (MTEL.JK vs ^JKSE)", chart: { labels: ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agt","Sep","Okt","Nov","Des"], series: [[0,3,6,8,10,12,14,13,12,12,12,12],[0,2,5,6,8,9,11,12,12,13,14,15]] } },
    shares: { outstanding: 81.5, unit: "bn", free_float_pct: 28.2 },
    shareholders: [{ name: "TLKM", pct: 71.83 }, { name: "Publik", pct: 28.17 }],
    shareholders_src: "IDX — struktur pemegang saham",
    esg: { found: true, scores: { e: 2.23, s: 3.03, g: 5.08 }, source: "Sustainalytics (public summary)", date: "2026" },
  },
  BBCA: {
    rating_box: { action: "BUY", tp: 9600, price: 7890, upside_pct: 21.7, prev_tp: null, key_takeaways: ["CASA >75% — funding advantage terdepan.", "CoC 1.2% & NIM 5.8% — kualitas aset premium.", "GGM P/BV (ROE-g)/(CoE-g) → TP Rp 9.600 (ROE 19.7%, payout 50%)."] },
    vs_jci: { ytd_abs: 4.2, ytd_rel: -3.1, source: "IDX, yfinance (BBCA.JK vs ^JKSE)", chart: { labels: ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agt","Sep","Okt","Nov","Des"], series: [[0,1,3,4,5,6,7,6,7,8,9,9],[0,2,5,6,8,9,11,12,12,13,14,15]] } },
    shares: { outstanding: 123.2, unit: "bn", free_float_pct: 44.8 },
    shareholders: [{ name: "Publik", pct: 44.8 }, { name: "Dwimuria", pct: 54.9 }, { name: "Lainnya", pct: 0.3 }],
    shareholders_src: "IDX — struktur pemegang saham",
    esg: { found: true, scores: { e: 3.1, s: 4.2, g: 6.1 }, source: "Sustainalytics", date: "2026" },
  },
  ADRO: {
    rating_box: { action: "BUY", tp: 2450, price: 2080, upside_pct: 17.8, prev_tp: null, key_takeaways: ["AADI spin-off unlock: SOTP AADI US$6.1bn holdco discount 15%.", "Dual DCF+SOTP cross-check — cash cost US$31/t resilient."] },
    vs_jci: { ytd_abs: -8.4, ytd_rel: -12.1, source: "IDX, yfinance (ADRO.JK vs ^JKSE)", chart: { labels: ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agt","Sep","Okt","Nov","Des"], series: [[0,-2,-5,-6,-7,-8,-9,-8,-8,-9,-9,-8],[0,2,5,6,8,9,11,12,12,13,14,15]] } },
    shares: { outstanding: 28.8, unit: "bn", free_float_pct: 38.5 },
    shareholders: [{ name: "Publik", pct: 38.5 }, { name: "Adaro Strategic", pct: 44.2 }, { name: "Lainnya", pct: 17.3 }],
    shareholders_src: "IDX — struktur pemegang saham",
    esg: { found: false },
  },
}

const FIXTURE_SEGMENTS: Record<string, Report["segments"]> = {
  RATU: [],
  CDIA: [
    { name: "Energi", revenue: 6300, share_pct: 53.4, yoy_pct: "-8%", qoq_pct: "-3%", row: ["Energi", 6300, "-8%", "-3%", "53.4%"], one_off: "Normalisasi one-off Rp 15.9 bn (gain penjualan aset) dikeluarkan dari segmen Energi." },
    { name: "Logistik", revenue: 4010, share_pct: 34.0, yoy_pct: "+44.7%", qoq_pct: "+12.0%", row: ["Logistik", 4010, "+44.7%", "+12.0%", "34.0%"] },
    { name: "Air", revenue: 850, share_pct: 7.2, yoy_pct: "+6%", qoq_pct: "+2%", row: ["Air", 850, "+6%", "+2%", "7.2%"] },
    { name: "Pelabuhan", revenue: 640, share_pct: 5.4, yoy_pct: "+9%", qoq_pct: "+4%", row: ["Pelabuhan", 640, "+9%", "+4%", "5.4%"] },
  ],
  MTEL: [
    { name: "Tower Leasing", revenue: 3833, share_pct: 49.2, yoy_pct: "+1%", qoq_pct: "+2%", row: ["Tower Leasing", 3833, "+1%", "+2%", "49.2%"] },
    { name: "Fiber", revenue: 309, share_pct: 17.8, yoy_pct: "+8%", qoq_pct: "+3%", row: ["Fiber", 309, "+8%", "+3%", "17.8%"] },
    { name: "Tower-Related", revenue: 299, share_pct: 18.2, yoy_pct: "+15%", qoq_pct: "+5%", row: ["Tower-Related", 299, "+15%", "+5%", "18.2%"] },
    { name: "Reseller", revenue: 251, share_pct: 14.8, yoy_pct: "0%", qoq_pct: "0%", row: ["Reseller", 251, "0%", "0%", "14.8%"] },
  ],
  BBCA: [
    { name: "Net Interest Income", revenue: 82000, share_pct: 68.0, yoy_pct: "+7%", qoq_pct: "+2%", row: ["NII", 82000, "+7%", "+2%", "68%"] },
    { name: "Non-Interest Income", revenue: 38500, share_pct: 32.0, yoy_pct: "+9%", qoq_pct: "+3%", row: ["Non-NII", 38500, "+9%", "+3%", "32%"] },
  ],
  ADRO: [
    { name: "Coal Mining", revenue: 14500, share_pct: 62.0, yoy_pct: "-4%", qoq_pct: "-1%", row: ["Coal Mining", 14500, "-4%", "-1%", "62%"] },
    { name: "Coal Trading", revenue: 4200, share_pct: 18.0, yoy_pct: "+5%", qoq_pct: "+2%", row: ["Coal Trading", 4200, "+5%", "+2%", "18%"] },
    { name: "Logistics", revenue: 2800, share_pct: 12.0, yoy_pct: "+8%", qoq_pct: "+3%", row: ["Logistics", 2800, "+8%", "+3%", "12%"] },
    { name: "Others", revenue: 1900, share_pct: 8.0, yoy_pct: "+2%", qoq_pct: "0%", row: ["Others", 1900, "+2%", "0%", "8%"] },
  ],
}

const FIXTURE_KPIS: Record<string, Report["kpis"]> = {
  RATU: [{ name: "Produksi Cepu", value: 169, prev: 152, unit: "k BOPD", formula: "produksi harian rata-rata", source: "SKK Migas", row: ["Produksi Cepu", 169, 152, "+17", "k BOPD", "rata-rata harian", "SKK Migas"] as unknown as unknown[] }],
  CDIA: [],
  MTEL: [
    { name: "Tower", value: 40563, prev: 39767, unit: "unit", formula: "jumlah tower", source: "Company data", row: ["Tower", 40563, 39767, "+796", "unit", "jumlah tower", "Company data"] as unknown as unknown[] },
    { name: "Colocation", value: 23303, prev: 21185, unit: "unit", formula: "colocation", source: "Company data", row: ["Colocation", 23303, 21185, "+2118", "unit", "colocation", "Company data"] as unknown as unknown[] },
    { name: "Tenant", value: 63866, prev: 60825, unit: "tenant", formula: "jumlah tenant", source: "Company data", row: ["Tenant", 63866, 60825, "+3041", "tenant", "jumlah tenant", "Company data"] as unknown as unknown[] },
    { name: "Tenancy Ratio", value: 1.57, prev: 1.53, unit: "x", formula: "tenant/tower", source: "Company data, data diolah", row: ["Tenancy Ratio", 1.57, 1.53, "+0.04", "x", "tenant/tower", "Company data"] as unknown as unknown[] },
    { name: "Fiber", value: 59239, prev: 54348, unit: "km", formula: "panjang jaringan", source: "Company data", row: ["Fiber", 59239, 54348, "+4891", "km", "panjang jaringan", "Company data"] as unknown as unknown[] },
  ],
  BBCA: [
    { name: "CASA Ratio", value: 75.2, prev: 74.1, unit: "%", formula: "CASA / third-party funds", source: "Company", row: ["CASA", 75.2, 74.1, "+1.1pp", "%", "CASA/DPK", "Company"] as unknown as unknown[] },
    { name: "NIM", value: 5.8, prev: 5.6, unit: "%", formula: "net interest margin", source: "Company", row: ["NIM", 5.8, 5.6, "+0.2pp", "%", "NIM", "Company"] as unknown as unknown[] },
    { name: "CoC", value: 1.2, prev: 1.3, unit: "%", formula: "cost of credit", source: "Company", row: ["CoC", 1.2, 1.3, "-0.1pp", "%", "CoC", "Company"] as unknown as unknown[] },
  ],
  ADRO: [
    { name: "Coal Production", value: 62.5, prev: 62.9, unit: "Mt", formula: "annual production", source: "Company", row: ["Coal Prod", 62.5, 62.9, "-0.4", "Mt", "annual", "Company"] as unknown as unknown[] },
    { name: "Stripping Ratio", value: 4.8, prev: 5.1, unit: "x", formula: "waste / coal", source: "Company", row: ["SR", 4.8, 5.1, "-0.3", "x", "SR", "Company"] as unknown as unknown[] },
  ],
}

const FIXTURE_VALUATION: Record<string, Report["valuationDetail"]> = {
  RATU: {
    methods: [
      { method: "DCF", fv: 7880, assumptions: { wacc: 8.4, beta: 0.7, rf: 6.2, erp: 6.9, coe: 10.0, cod: 3.5, we: 85.0, wd: 15.0, g: 5.0 }, table: { headers: ["Item","FY26F","FY27F","FY28F"], rows: [["FCF (Rp bn)",410,432,455],["Discount factor",0.92,0.85,0.78],["PV (Rp bn)",377,367,355]] }, source: "scripts/dcf.py" },
      { method: "EV/EBITDA", fv: 6960, assumptions: { multiple: 22.6 }, table: { headers: ["Item","Nilai"], rows: [["EV/EBITDA target (x)",22.6],["EBITDA FY26F (Rp bn)",585],["EV (Rp bn)",13221]] }, source: "scripts/ev_ebitda.py" },
    ],
    blended: null, bands: null, ggm: null,
    provenance: "engines.dcf+ev_ebitda :: disclosed",
  },
  CDIA: {
    methods: [
      { method: "DCF", fv: 815, assumptions: { wacc: 9.8, beta: 1.05, rf: 6.2, erp: 7.4, coe: 14.0, cod: 5.5, we: 70.0, wd: 30.0, g: 4.0 }, table: { headers: ["Item","FY26F","FY27F","FY28F"], rows: [["FCFE (Rp bn)",700,1400,2100]] }, source: "scripts/dcf.py" },
      { method: "DDM", fv: 810, assumptions: { payout_27: 40.0, payout_28: 104.0, coe: 14.0, g: 4.0 }, table: { headers: ["Item","FY27F","FY28F"], rows: [["Dividen per saham (Rp)",22,55]] }, source: "scripts/ddm.py" },
    ],
    blended: null, bands: null, ggm: null,
  },
  MTEL: {
    methods: [
      { method: "DCF", fv: 630, assumptions: { wacc: 10.1, beta: 0.65, rf: 6.96, erp: 8.89, coe: 12.74, cod: 6.0, we: 60.8, wd: 39.2, g: 1.5 }, table: { headers: ["Rp bn","2026F","2027F","2028F"], rows: [["EBIT",4264,4750,5239],["EBIT(1-tax 6%)",4008,4465,4925],["+ D&A",3188,3423,3658],["− Capex",-2981,-2709,-2437],["+ ΔWC",762,762,762],["FCF",4977,4941,4908],["Terminal value","","",72736]] }, source: "scripts/dcf.py" },
      { method: "EV/EBITDA", fv: 745, assumptions: { multiple: 10.0 }, table: { headers: ["Item","Nilai"], rows: [["EV/EBITDA target (x)",10.0],["EBITDA (Rp tn)",7.45]] }, source: "scripts/ev_ebitda.py" },
    ],
    blended: { weights: { DCF: 60, "EV/EBITDA": 40 }, fv: 635, fv_str: "635", margin_of_safety_pct: 15, rows: [["DCF","60%",630],["EV/EBITDA","40%",745]], source: "scripts/blended.py", weights_sum_100: true },
    bands: { pbv_3y: { "std+2": 2.9, "std+1": 2.5, avg: 2.1, "std-1": 1.7, "std-2": 1.3, current: 1.47, label: "BELOW AVG" }, source: "IDX, yfinance — 3Y band, data diolah" },
    ggm: null,
  },
  BBCA: {
    methods: [
      { method: "DCF", fv: 9650, assumptions: { wacc: 11.1, beta: 0.8, rf: 6.96, erp: 6.0, coe: 11.76, g: 4.0 }, source: "scripts/dcf.py" },
      { method: "GGM P/BV", fv: 9600, assumptions: { roe: 19.7, g: 4.0, coe: 11.76, bvps: 4200 }, source: "scripts/ggm.py" },
    ],
    blended: null, bands: null,
    ggm: { pbv_implied: 2.29, fv_per_share: 9600, formula: "P/BV=(ROE-g)/(CoE-g)", assumptions: { roe: 0.197, g: 0.04, coe: 0.1176, bvps: 4200 } },
  },
  ADRO: {
    methods: [{ method: "SOTP", fv: 2450, assumptions: { holdco_discount: 15, aadi_value_usd_bn: 6.1 }, source: "scripts/sotp.py" }],
    blended: null, bands: null, ggm: null,
  },
}

const FIXTURE_RATIOS: Record<string, Record<string, number|string>> = {
  RATU: { ROE: "88 → 30%", DER: "0.21×", "Interest coverage": "14.2×", NPM: "31%" },
  CDIA: { Gearing: "96 → 170%", "Current ratio": "1.2 → 0.7×", "Debt/EBITDA": "1.9 → 4.1×" },
  MTEL: { "Current ratio": "0.3 → 0.8×", "DER": "0.67 → 0.69×", "LT D/E": "0.34 → 0.46×", "ICR": "2.0 → 4.0×", "Cash ratio": "8 → 57%" },
  BBCA: { ROE: "19.7%", NIM: "5.8%", CASA: "75.2%", CoC: "1.2%", CAR: "29.2%", LDR: "78%" },
  ADRO: { ROE: "12%", DER: "0.31×", "Cash cost": "US$31/t", NPM: "18%" },
}

const MOCK: Record<string, Report> = {
  RATU: { ticker: "RATU", name: "Ratu Prabu Energi (Oil & Gas)", price: 7150, target: 7880, upside: "+10.2%", rating: "BUY", summary: "Pure-play Cepu PSC — DCF 8.4% WACC + EV/EBITDA 22.6x. Bottom line +28% meski revenue -13%.", valuation: [{ method: "DCF", value: 7880, weight: 60 }, { method: "EV/EBITDA 22.6x", value: 6960, weight: 40 }], updatedAt: "2026-08-31" },
  CDIA: { ticker: "CDIA", name: "Chandra Daya Investasi (Conglomerate)", price: 742, target: 815, upside: "+9.8%", rating: "BUY", summary: "SOTP 4 pilar Energy/Water/Port/Logistics — DCF 815 + DDM 810. Segment mix Energy 55% / Logistics +44.7%.", valuation: [{ method: "DCF", value: 815 }, { method: "DDM", value: 810 }], updatedAt: "2026-08-31" },
  MTEL: { ticker: "MTEL", name: "Dayamitra Telekomunikasi (Tower)", price: 460, target: 635, upside: "+38.0%", rating: "BUY", summary: "Infra recurring — blended DCF 60% + EV/EBITDA 10x 40% → 635. Tenancy 1.57x, fiber 59,239 km.", valuation: [{ method: "DCF 60%", value: 630 }, { method: "EV/EBITDA 10x 40%", value: 635 }], updatedAt: "2026-08-31" },
  BBCA: { ticker: "BBCA", name: "Bank Central Asia", price: 7890, target: 9600, upside: "+21.9%", rating: "BUY", summary: "GGM P/BV (ROE-g)/(CoE-g) — 8p Samuel pack. Bank comp peer avg P/BV 3.3x.", valuation: [{ method: "GGM P/BV", value: 9600 }], updatedAt: "2026-08-31" },
  ADRO: { ticker: "ADRO", name: "Adaro Energy (SOTP spin-off)", price: 2080, target: 2450, upside: "+17.8%", rating: "BUY", summary: "BRIDS SOTP AADI US$6.1bn + post-spin holdco discount — dual DCF+SOTP.", valuation: [{ method: "SOTP", value: 2450 }], updatedAt: "2026-08-31" },
}

function mergeFixture(k: string, live: Report, raw: Record<string, unknown>): Report {
  const base = MOCK[k] ?? live
  const tmpl = (raw["template"] as string) || (k === "MTEL" ? "infra" : (FIXTURE_SEGMENTS[k]?.length ?? 0) > 1 && k !== "MTEL" ? "sotp" : "single")
  const liveSegments = Array.isArray(raw["segments"]) ? (raw["segments"] as unknown[]) : (raw["segments"] as { segments?: unknown[] })?.segments
  const segmentsArr = (Array.isArray(liveSegments) && liveSegments.length > 0) ? (liveSegments as Report["segments"]) : FIXTURE_SEGMENTS[k]
  const liveKpi = raw["kpi"] ?? raw["kpis"]
  let kpisArr: Report["kpis"] | undefined
  if (Array.isArray(liveKpi) && liveKpi.length > 0) {
    // normalize kpi object vs array
    if (typeof liveKpi[0] === "object" && "name" in (liveKpi[0] as Record<string, unknown>)) kpisArr = liveKpi as Report["kpis"]
    else kpisArr = FIXTURE_KPIS[k]
  } else if (liveKpi && typeof liveKpi === "object" && !Array.isArray(liveKpi)) {
    // infra kpi is object {tower, tenancy_ratio, fiber_km}
    const o = liveKpi as Record<string, unknown>
    if (o["tenancy_ratio"] != null || o["tower"] != null) {
      kpisArr = [
        { name: "Tower", value: Number(o["tower"] ?? 40563), prev: undefined, unit: "unit", formula: "jumlah tower" },
        { name: "Tenancy Ratio", value: Number(o["tenancy_ratio"] ?? 1.57), prev: 1.53, unit: "x", formula: "tenant/tower" },
        { name: "Fiber", value: Number(o["fiber_km"] ?? 59239), prev: 54348, unit: "km", formula: "panjang jaringan" },
      ]
    } else {
      kpisArr = FIXTURE_KPIS[k]
    }
  } else {
    kpisArr = FIXTURE_KPIS[k]
  }
  // valuation detail merge
  const val = (raw["valuation"] as Record<string, unknown>) || {}
  const fixVal = FIXTURE_VALUATION[k]
  const blendedRaw = (val["blended"] as Record<string, unknown> | null) ?? (raw["blended"] as Record<string, unknown> | null)
  const bandsRaw = (val["bands"] as unknown) ?? raw["bands"]
  // build valuationDetail from live or fixture
  let valuationDetail: Report["valuationDetail"] = (fixVal as Report["valuationDetail"]) ?? { methods: [], blended: null, bands: null, ggm: null }
  if (val && Object.keys(val).length > 0) {
    const liveMethods: NonNullable<Report["valuationDetail"]>["methods"] = []
    if (val["dcf"]) liveMethods.push({ method: "DCF", fv: Number((val["dcf"] as Record<string, unknown>)["fv_per_share"] ?? (val["dcf"] as Record<string, unknown>)["fv"] ?? 0) || Math.round((raw["fair_value"] as number) ?? 0), assumptions: (val["assumptions"] as Record<string, unknown>) ?? {}, source: "engines.dcf" })
    if (val["ev"]) liveMethods.push({ method: "EV/EBITDA", fv: Number((val["ev"] as Record<string, unknown>)["fv_per_share"] ?? 0), source: "engines.ev_ebitda" })
    let ggmVal: NonNullable<Report["valuationDetail"]>["ggm"] = (val["ggm"] as NonNullable<Report["valuationDetail"]>["ggm"]) ?? null
    const fvAny = fixVal as unknown as Record<string, unknown>
    if (!ggmVal && k === "BBCA" && fvAny?.["ggm"]) ggmVal = fvAny["ggm"] as NonNullable<Report["valuationDetail"]>["ggm"]
    let bandsVal: NonNullable<Report["valuationDetail"]>["bands"] = null
    if (bandsRaw && typeof bandsRaw === "object" && (bandsRaw as Record<string, unknown>)["pbv_3y"]) bandsVal = bandsRaw as NonNullable<Report["valuationDetail"]>["bands"]
    else if (fvAny?.["bands"]) bandsVal = fvAny["bands"] as NonNullable<Report["valuationDetail"]>["bands"]
    let blendedVal: NonNullable<Report["valuationDetail"]>["blended"] = null
    if (blendedRaw && typeof blendedRaw === "object") {
      const b = blendedRaw as Record<string, unknown>
      const bv = Number(b["blended"] ?? 0) || Number(raw["fair_value"] ?? 0)
      blendedVal = { weights: (b["weights"] as Record<string, number>) ?? { DCF: 60, "EV/EBITDA": 40 }, fv: bv, fv_str: String(Math.round(bv)), source: "engines.blended", weights_sum_100: true, margin_of_safety_pct: (b["margin_of_safety_pct"] as number) ?? 15 }
    } else if (fvAny?.["blended"]) blendedVal = fvAny["blended"] as NonNullable<Report["valuationDetail"]>["blended"]
    if (liveMethods.length > 0) valuationDetail = { methods: liveMethods.length ? liveMethods : (fixVal as Report["valuationDetail"])?.methods, blended: blendedVal, bands: bandsVal, ggm: ggmVal, assumptions: val["assumptions"] as Record<string, unknown>, dcf: val["dcf"], ev: val["ev"], provenance: val["provenance"] as string }
  }
  return {
    ...base,
    ...live,
    template: tmpl,
    cover: FIXTURE_COVER[k] ?? base.cover,
    segments: segmentsArr as Report["segments"],
    kpis: kpisArr,
    kpi: raw["kpi"] ?? raw["kpis"] ?? kpisArr,
    valuationDetail,
    ratios: FIXTURE_RATIOS[k] as Report["ratios"],
    source: (raw["source"] as string) ?? base.source,
    raw,
  }
}

export async function fetchReport(ticker: string): Promise<Report> {
  const k = ticker.toUpperCase()
  const live = await apiFetch<Report>(`/api/report/${encodeURIComponent(k)}`, async () => {
    await new Promise(r => setTimeout(r, 120))
    if (MOCK[k]) return MOCK[k]
    return { ticker: k, name: `${k} — Synthetic`, price: 1000, target: 1200, upside: "+20%", rating: "BUY", summary: "Synthetic placeholder — data seed=42.", valuation: [{ method: "DCF", value: 1200 }], updatedAt: "2026-08-31" }
  })
  const anyLive = live as unknown as Record<string, unknown>
  if (anyLive && typeof anyLive["fair_value"] === "number") {
    const fv = anyLive["fair_value"] as number
    const price = (anyLive["price"] as number) || (MOCK[k]?.price ?? 1000)
    const upside = anyLive["upside_pct"] as number | null
    const val = anyLive["valuation"] as Record<string, unknown> | undefined
    const base: Report = {
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
    return mergeFixture(k, base, anyLive)
  }
  // already mock shape — enrich with fixtures directly
  const raw: Record<string, unknown> = { ...(anyLive as Record<string, unknown>), template: (anyLive as Record<string, unknown>)["template"] ?? (k === "MTEL" ? "infra" : (FIXTURE_SEGMENTS[k]?.length ?? 0) > 1 ? "sotp" : "single") }
  return mergeFixture(k, live, raw)
}

// ——— outlook ———
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
}

const OUTLOOK_FIXTURE: Outlook = {
  jci: { base: 9100, bull: 10000, bear: 7800, pe: 15, epsGrowth: "8%" },
  sectors: [{ name: "Industrials", call: "OW" }, { name: "Materials", call: "OW" }, { name: "Consumer Staples", call: "OW" }, { name: "Consumer Discretionary", call: "OW" }, { name: "Property", call: "OW" }, { name: "Financials", call: "N" }, { name: "Energy", call: "UW" }, { name: "Utilities", call: "UW" }],
  picks: [
    { ticker: "BBCA", cap: "Large", rationale: "Kualitas aset & CASA — defensif inti portofolio." },
    { ticker: "ASII", cap: "Large", rationale: "Siklus mobil listrik + ekspor ASEAN." },
    { ticker: "ICBP", cap: "Large", rationale: "Pricing power bahan baku turun." },
    { ticker: "GOTO", cap: "Large", rationale: "Jalan menuju profitabilitas terkunci." },
  ] as unknown[],
  thematics: [
    { name: "Pemulihan konsumsi", detail: "Daya beli rumahtangga pulih ditopang inflasi terkendali (BPS, BI easing).", source: "BPS" },
    { name: "Perbaikan TSR", detail: "Buyback & dividen meningkatkan total shareholder return (ITMG/INTP/PWON).", source: "IDX" },
    { name: "Menarik kembali dana asing", detail: "Valuasi vs regional menarik setelah 2 tahun outflow (-US$2.6bn 2Y).", source: "Bloomberg" },
    { name: "Kebijakan fiskal", detail: "Belanja infrastruktur & insentif manufaktur; Danantara US$12bn (0.8% PDB).", source: "Pemerintah" },
    { name: "Danantara sebagai swing factor", detail: "US$12bn dry powder + >US$14bn SWF; SOE ex-bank +25% YTD re-rating.", source: "Danantara" },
  ],
  flows: {
    narrative: "Retail mendominasi 58% ADTV Rp 14.5 tn (puncak COVID). Asing -US$2.2bn YTD / -2.6bn 2Y; 44% kepemilikan asing UW sejak 2003. MSCI Adjusted Free Float Mei 2026 = event risiko. Bid institusional via Danantara US$1.5bn + pensiun.",
    table: { headers: ["Flow","Nilai","Periode"], rows: [["Foreign net sell","-US$2.2bn","YTD 2026"],["Foreign net sell (2Y)","-US$2.6bn","2024-2026"],["FDI","-28%","YTD 2026"],["FPI","-US$14bn","YTD 2026"]] },
    source: "IDX, Bloomberg — data historis",
  },
  danantara: {
    narrative: "Segregasi BPI+DAM+DIM; US$12bn dry powder (0.8% PDB) + >US$14bn SWF; 9 sektor prioritas; SOE ex-bank +25% YTD re-rating.",
    table: { headers: ["Komponen","Nilai"], rows: [["Dry powder","US$12bn"],["SWF eksisting",">US$14bn"],["Sektor prioritas","9"]] },
    source: "Danantara — rilis publik",
  },
  source: "JPM 2026 Outlook (JCI 9100 base) — fixtures",
}

export async function fetchOutlook(): Promise<Outlook> {
  const live = await apiFetch<Record<string, unknown>>("/api/outlook", async () => {
    await new Promise(r => setTimeout(r, 80))
    return OUTLOOK_FIXTURE as unknown as Record<string, unknown>
  })
  // live shape from BE: { jci_base, jci_bull, jci_bear, pe, eps_growth, ow, uw, neutral, picks, source, ... }
  // or already Outlook fixture shape
  const hasJciBase = typeof live["jci_base"] === "number"
  if (hasJciBase || live["jci"] == null) {
    const jci = {
      base: (live["jci_base"] as number) ?? OUTLOOK_FIXTURE.jci.base,
      bull: (live["jci_bull"] as number) ?? OUTLOOK_FIXTURE.jci.bull,
      bear: (live["jci_bear"] as number) ?? OUTLOOK_FIXTURE.jci.bear,
      pe: (live["pe"] as number) ?? OUTLOOK_FIXTURE.jci.pe,
      epsGrowth: live["eps_growth"] != null ? `${Math.round(Number(live["eps_growth"])*100)}%` : OUTLOOK_FIXTURE.jci.epsGrowth,
    }
    const ow = (live["ow"] as string[]) ?? []
    const uw = (live["uw"] as string[]) ?? []
    const neutral = (live["neutral"] as string[]) ?? []
    const sectors = [
      ...ow.map((n: string) => ({ name: n, call: "OW" })),
      ...neutral.map((n: string) => ({ name: n, call: "N" })),
      ...uw.map((n: string) => ({ name: n, call: "UW" })),
    ]
    const picks = (live["picks"] as unknown[]) ?? OUTLOOK_FIXTURE.picks
    // thematics/flows/danantara may be in live.strategy
    const strat = (live["strategy"] as Record<string, unknown>) ?? live
    const thematics = (strat["thematics"] as Outlook["thematics"]) ?? (live["thematics"] as Outlook["thematics"]) ?? OUTLOOK_FIXTURE.thematics
    const flows = (strat["flows"] as Outlook["flows"]) ?? (live["flows"] as Outlook["flows"]) ?? OUTLOOK_FIXTURE.flows
    const danantara = (strat["danantara"] as Outlook["danantara"]) ?? (live["danantara"] as Outlook["danantara"]) ?? OUTLOOK_FIXTURE.danantara
    return {
      jci, sectors: sectors.length ? sectors : OUTLOOK_FIXTURE.sectors,
      picks, jci_price: live["jci_price"],
      thematics, flows, danantara,
      source: (live["source"] as string) ?? OUTLOOK_FIXTURE.source,
      raw: live,
    }
  }
  // already Outlook shape
  return {
    ...OUTLOOK_FIXTURE,
    ...(live as unknown as Outlook),
    thematics: (live["thematics"] as Outlook["thematics"]) ?? OUTLOOK_FIXTURE.thematics,
    flows: (live["flows"] as Outlook["flows"]) ?? OUTLOOK_FIXTURE.flows,
    danantara: (live["danantara"] as Outlook["danantara"]) ?? OUTLOOK_FIXTURE.danantara,
    raw: live,
  }
}
export async function fetchSentiment(ticker: string): Promise<{ ticker: string; gauge: number; label?: string; narratives: string[]; timeline: { date: string; note: string }[]; sources: { platform: string; url: string }[] }> {
  const k = ticker.toUpperCase()
  return apiFetch(`/api/sentiment?ticker=${encodeURIComponent(k)}`, async () => {
    await new Promise(r => setTimeout(r, 80))
    return { ticker: k, gauge: 62, label: "Bullish", narratives: ["Danantara catalyst rotation", "Earnings beat chatter on Stockbit", "Foreign flow UW reversal watch"], timeline: [{ date: "2026-08-24", note: "BBCA earnings thread +1.2k likes" }, { date: "2026-08-28", note: "Danantara $12bn dry powder narrative" }], sources: [{ platform: "X", url: `https://x.com/search?q=%24${k}` }, { platform: "Reddit", url: `https://www.reddit.com/search/?q=${k}` }] } as unknown as Awaited<ReturnType<typeof fetchSentiment>>
  })
}

// ——— pdf ———
export async function fetchPdf(ticker: string): Promise<void> {
  const tk = ticker.toUpperCase()
  const path = `/api/report/${encodeURIComponent(tk)}/pdf`
  const url = API_BASE ? `${API_BASE}${path}` : path
  let r: Response
  try {
    r = await fetch(url)
  } catch (e) {
    throw new Error(`network error — PDF endpoint unreachable (${API_BASE || "same-origin"}${path} — is the API up? ${(e as Error)?.message ?? String(e)})`)
  }
  if (!r.ok) {
    const text = await r.text().catch(() => "")
    // surface real backend message + hint
    const hint = r.status === 404 ? " — check API url / tunnel" : r.status >= 500 ? " — server error" : ""
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
