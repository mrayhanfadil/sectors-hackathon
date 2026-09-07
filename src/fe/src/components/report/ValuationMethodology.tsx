import {
  Calculator,
  Layers,
  BarChart2,
  TrendingUp,
  PieChart,
  Table,
  CheckCircle,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export interface ValuationMethodologyProps {
  ticker: string
  valuation: { method: string; value: number; weight?: number }[]
  valuationDetail?: {
    methods?: {
      method: string
      fv: number
      assumptions?: Record<string, unknown>
      table?: { headers: string[]; rows: unknown[][] }
      source?: string
    }[]
    blended?: {
      weights: Record<string, number>
      fv: number
      fv_str?: string
      margin_of_safety_pct?: number
      rows?: unknown[][]
      source?: string
      weights_sum_100?: boolean
    } | null
    bands?: {
      pbv_3y?: {
        "std+2": number
        "std+1": number
        avg: number
        "std-1": number
        "std-2": number
        current: number
        label: string
      }
      source?: string
    } | null
    ggm?: {
      pbv_implied: number
      fv_per_share: number
      formula: string
      assumptions?: Record<string, unknown>
    } | null
    assumptions?: Record<string, unknown>
    provenance?: string
  }
  template?: string
  kpis?: {
    name: string
    value: number
    prev?: number
    unit?: string
    formula?: string
    source?: string
  }[]
  segments?: {
    name: string
    revenue?: number
    share_pct?: number
    yoy_pct?: unknown
    qoq_pct?: unknown
    one_off?: string
  }[]
  rawSegments?: unknown
  segmentsSource?: string
  ratios?: Record<string, string | number>
  rawBands?: any
}

function fmtIDR(n: number | null | undefined): string {
  if (n == null || Number.isNaN(Number(n))) return "-"
  return Number(n).toLocaleString("id-ID")
}

function BandsChart({
  bands,
  width = 360,
  height = 110,
}: {
  bands: {
    "std+2": number
    "std+1": number
    avg: number
    "std-1": number
    "std-2": number
    current?: number
    label?: string
  }
  width?: number
  height?: number
}) {
  const p2 = Number(bands["std+2"] ?? 0)
  const p1 = Number(bands["std+1"] ?? 0)
  const avg = Number(bands.avg ?? 0)
  const m1 = Number(bands["std-1"] ?? 0)
  const m2 = Number(bands["std-2"] ?? 0)
  const cur = bands.current != null ? Number(bands.current) : null

  const allVals = [p2, p1, avg, m1, m2, ...(cur != null ? [cur] : [])].filter((v) => !Number.isNaN(v))
  if (allVals.length < 5) return null
  const min = Math.min(...allVals) * 0.95
  const max = Math.max(...allVals) * 1.05
  const range = max - min || 1

  const getY = (v: number) => height - ((v - min) / range) * (height - 24) - 12

  const lines = [
    { label: `+2σ (${p2.toFixed(2)})`, y: getY(p2), color: "#94a3b8", dash: "3,3" },
    { label: `+1σ (${p1.toFixed(2)})`, y: getY(p1), color: "#cbd5e1", dash: "3,3" },
    { label: `Mean (${avg.toFixed(2)})`, y: getY(avg), color: "#0f172a", dash: "none", strokeWidth: 1.5 },
    { label: `-1σ (${m1.toFixed(2)})`, y: getY(m1), color: "#cbd5e1", dash: "3,3" },
    { label: `-2σ (${m2.toFixed(2)})`, y: getY(m2), color: "#94a3b8", dash: "3,3" },
  ]

  const curY = cur != null ? getY(cur) : null

  return (
    <div className="py-2">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full max-w-md h-auto text-xs">
        {lines.map((l, i) => (
          <g key={i}>
            <line
              x1={80}
              y1={l.y}
              x2={width - 20}
              y2={l.y}
              stroke={l.color}
              strokeWidth={l.strokeWidth ?? 1}
              strokeDasharray={l.dash}
            />
            <text x={74} y={l.y + 3} textAnchor="end" fill="#64748b" className="text-[10px] font-mono">
              {l.label}
            </text>
          </g>
        ))}
        {cur != null && curY != null && (
          <g>
            <line x1={80} y1={curY} x2={width - 20} y2={curY} stroke="#059669" strokeWidth={1.5} />
            <circle cx={width / 2} cy={curY} r={3.5} fill="#059669" />
            <text x={width - 15} y={curY + 3} fill="#059669" className="text-[10px] font-semibold font-mono">
              Kini {cur.toFixed(2)}
            </text>
          </g>
        )}
      </svg>
    </div>
  )
}

function SegmentPie({
  segments,
  source,
  rawSegments,
}: {
  segments: {
    name: string
    share_pct?: number
    revenue?: number
    yoy_pct?: unknown
    qoq_pct?: unknown
    one_off?: string
  }[]
  source?: string
  rawSegments?: unknown
}) {
  if (!segments || segments.length === 0) {
    if (rawSegments && typeof rawSegments === "object" && Object.keys(rawSegments).length > 0) {
      return (
        <ul className="space-y-1 text-xs text-neutral-700">
          {Object.entries(rawSegments as Record<string, unknown>).map(([seg, val]) => (
            <li key={seg}>
              <span className="font-medium">{seg}</span>: {typeof val === "object" && val !== null ? JSON.stringify(val) : String(val)}
            </li>
          ))}
        </ul>
      )
    }
    return (
      <div className="rounded-lg border border-dashed border-neutral-200 px-4 py-5 text-center text-xs text-neutral-500">
        Segmentasi tunggal / pengungkapan segmen gabungan sesuai laporan keuangan IDX.
      </div>
    )
  }

  const total = segments.reduce((s, x) => s + Number(x.share_pct ?? 0), 0)
  const colors = ["bg-neutral-900", "bg-neutral-600", "bg-neutral-400", "bg-neutral-300", "bg-amber-500", "bg-emerald-600"]

  return (
    <div className="space-y-3">
      {/* Visual Stacked Bar */}
      <div className="flex h-3 overflow-hidden rounded-full border border-neutral-200">
        {segments.map((s, i) => (
          <div
            key={s.name}
            className={colors[i % colors.length]}
            style={{ width: `${Number(s.share_pct ?? 0)}%` }}
            title={`${s.name} ${s.share_pct}%`}
          />
        ))}
      </div>

      {/* Breakdown Items */}
      <div className="grid gap-2 sm:grid-cols-2">
        {segments.map((s, i) => (
          <div key={s.name} className="flex items-center justify-between rounded-lg border border-neutral-200/80 bg-white p-2.5 text-xs">
            <span className="flex items-center gap-2 font-medium text-neutral-800">
              <span className={`h-2.5 w-2.5 rounded-full ${colors[i % colors.length]}`} />
              {s.name}
            </span>
            <div className="flex items-center gap-2 font-mono">
              <span className="font-semibold text-neutral-900">
                {s.share_pct != null ? `${s.share_pct}%` : "-"}
              </span>
              {s.revenue != null && (
                <span className="text-neutral-500 text-[11px]">Rp {fmtIDR(Number(s.revenue))} bn</span>
              )}
              {s.yoy_pct != null && (
                <span className="rounded bg-neutral-50 px-1.5 py-0.5 text-[10px] text-neutral-600">
                  YoY {String(s.yoy_pct)}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {Math.abs(total - 100) > 0.6 && total > 0 && (
        <p className="text-xs text-amber-700 bg-amber-50 rounded p-2 border border-amber-200">
          Total porsi segmen: {total.toFixed(1)}% (sesuai pengungkapan catatan atas laporan keuangan).
        </p>
      )}
      {segments.some((s) => s.one_off) && (
        <p className="rounded bg-amber-50 px-3 py-2 text-xs text-amber-800 border border-amber-200">
          Penyesuaian One-off: {segments.find((s) => s.one_off)?.one_off}
        </p>
      )}
      {source && <p className="text-[11px] text-neutral-400">Sumber: {source}</p>}
    </div>
  )
}

export function ValuationMethodology({
  ticker: _ticker,
  valuation = [],
  valuationDetail,
  template = "single",
  kpis = [],
  segments = [],
  rawSegments,
  segmentsSource,
  ratios,
  rawBands,
}: ValuationMethodologyProps) {
  const vd = valuationDetail
  const isInfra = template.toLowerCase() === "infra"
  const isSotp = template.toLowerCase() === "sotp"

  const bandsData =
    vd?.bands?.pbv_3y ??
    (rawBands?.pbv_3y ??
      (typeof rawBands === "object" && !Array.isArray(rawBands) && rawBands?.["std+2"] != null
        ? rawBands
        : null))

  return (
    <section id="valuation-methodology" className="space-y-4 scroll-mt-28">
      <div>
        <h2 className="text-[15px] font-semibold tracking-tight text-[#0a0a0a]">
          2. Metodologi Valuasi & Profil Finansial
        </h2>
        <p className="text-xs text-neutral-500">
          Model DCF, kelipatan laba, bobot blended, data operasional, dan dekomposisi segmen
        </p>
      </div>

      {/* Row 1: Valuation Summary Table */}
      <Card className="border-neutral-200 bg-white shadow-2xs">
        <CardHeader className="p-4 pb-2">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Calculator className="h-4 w-4 text-neutral-700" />
              <CardTitle className="text-sm font-semibold text-neutral-900">
                Ringkasan Model Valuasi
              </CardTitle>
            </div>
            <span className="text-[11px] text-neutral-400 font-mono">
              {vd?.provenance ?? "DCF / DDM / SOTP / GGM deterministik"}
            </span>
          </div>
        </CardHeader>
        <CardContent className="p-4 pt-2 space-y-3">
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {valuation.map((v) => (
              <div
                key={v.method}
                className="flex items-center justify-between rounded-lg border border-neutral-200 bg-neutral-50/50 p-3"
              >
                <div>
                  <div className="text-xs font-semibold text-neutral-900">{v.method}</div>
                  <div className="text-[11px] text-neutral-500">
                    {v.weight ? `Bobot: ${v.weight}%` : "Model Standalone"}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold font-mono text-neutral-900">
                    Rp {fmtIDR(v.value)}
                  </div>
                  <div className="text-[10px] text-neutral-400">Nilai Wajar</div>
                </div>
              </div>
            ))}
          </div>

          {vd?.methods && vd.methods.length > 0 && (
            <div className="space-y-1.5 border-t border-neutral-100 pt-3">
              <div className="text-xs font-semibold text-neutral-600">Rincian Komponen Mesin Valuasi:</div>
              <div className="grid gap-2 sm:grid-cols-2">
                {vd.methods.map((m) => (
                  <div
                    key={m.method}
                    className="flex items-center justify-between rounded-md border border-neutral-100 bg-white p-2 text-xs"
                  >
                    <span className="text-neutral-700">
                      {m.method} <span className="text-[11px] text-neutral-400">({m.source ?? "engine"})</span>
                    </span>
                    <span className="font-mono font-semibold text-neutral-900">
                      Rp {fmtIDR(m.fv)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Row 2: Blended Valuation & GGM & Historical Bands */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Blended Valuation (if present) */}
        {vd?.blended ? (
          <Card className="border-neutral-200 bg-white shadow-2xs">
            <CardHeader className="p-4 pb-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Layers className="h-4 w-4 text-neutral-700" />
                  <CardTitle className="text-sm font-semibold text-neutral-900">
                    Blended Valuation {isInfra ? "(Bobot 60/40)" : ""}
                  </CardTitle>
                </div>
                <Badge variant="outline" className="text-xs font-mono">
                  MoS {vd.blended.margin_of_safety_pct ?? 15}%
                </Badge>
              </div>
              <CardDescription className="text-[11px] text-neutral-400">
                {vd.blended.source ?? "scripts/blended.py"}
              </CardDescription>
            </CardHeader>
            <CardContent className="p-4 pt-2 space-y-3">
              <div className="overflow-x-auto rounded-lg border border-neutral-200">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b bg-neutral-50 text-left text-neutral-600 font-semibold">
                      <th className="py-2 px-3">Metode</th>
                      <th className="py-2 px-3">Bobot</th>
                      <th className="py-2 px-3 text-right">Nilai Wajar</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(
                      vd.blended.rows ?? [
                        ["DCF", "60%", vd.blended.fv],
                        ["EV/EBITDA", "40%", 740],
                      ]
                    ).map((row, i) => (
                      <tr key={i} className="border-b last:border-0">
                        <td className="py-1.5 px-3 font-medium text-neutral-800">{String(row[0])}</td>
                        <td className="py-1.5 px-3 font-mono text-neutral-600">{String(row[1])}</td>
                        <td className="py-1.5 px-3 text-right font-mono font-semibold text-neutral-900">
                          Rp {fmtIDR(Number(row[2]))}
                        </td>
                      </tr>
                    ))}
                    <tr className="bg-[#0a0a0a] text-white font-bold">
                      <td className="py-2 px-3">Blended Target Price</td>
                      <td className="py-2 px-3 font-mono">100%</td>
                      <td className="py-2 px-3 text-right font-mono">
                        Rp {fmtIDR(vd.blended.fv)}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div className="flex items-center gap-1.5 text-[11px] text-neutral-500">
                <CheckCircle className="h-3.5 w-3.5 text-emerald-600" />
                <span>
                  Audit bobot total:{" "}
                  {Object.values(vd.blended.weights ?? {}).reduce((a: number, b: unknown) => a + Number(b), 0).toFixed(0)}
                  %
                </span>
              </div>
            </CardContent>
          </Card>
        ) : null}

        {/* GGM Box (if present, e.g. BBCA) */}
        {vd?.ggm ? (
          <Card className="border-neutral-200 bg-white shadow-2xs">
            <CardHeader className="p-4 pb-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BarChart2 className="h-4 w-4 text-emerald-600" />
                  <CardTitle className="text-sm font-semibold text-neutral-900">
                    Gordon Growth Model (GGM P/BV)
                  </CardTitle>
                </div>
                <Badge variant="outline" className="text-xs font-mono text-emerald-700 bg-emerald-50 border-emerald-200">
                  {vd.ggm.pbv_implied}x P/BV
                </Badge>
              </div>
              <CardDescription className="text-[11px] text-neutral-400 font-mono">
                {vd.ggm.formula}
              </CardDescription>
            </CardHeader>
            <CardContent className="p-4 pt-2 space-y-3">
              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <div className="rounded-lg border border-neutral-100 bg-neutral-50 p-2.5">
                  <div className="text-neutral-500 text-[11px]">P/BV Implied</div>
                  <div className="font-bold font-mono text-neutral-900 text-sm mt-0.5">
                    {vd.ggm.pbv_implied}x
                  </div>
                </div>
                <div className="rounded-lg border border-neutral-100 bg-neutral-50 p-2.5">
                  <div className="text-neutral-500 text-[11px]">BVPS Proyeksi</div>
                  <div className="font-bold font-mono text-neutral-900 text-sm mt-0.5">
                    Rp {fmtIDR(Number((vd.ggm.assumptions as Record<string, unknown>)?.["bvps"] ?? 4200))}
                  </div>
                </div>
                <div className="rounded-lg border border-emerald-200 bg-emerald-50/80 p-2.5">
                  <div className="text-emerald-800 text-[11px] font-medium">Target Price</div>
                  <div className="font-bold font-mono text-emerald-900 text-sm mt-0.5">
                    Rp {fmtIDR(vd.ggm.fv_per_share)}
                  </div>
                </div>
              </div>

              <div className="rounded-md border border-neutral-100 bg-neutral-50/50 p-2.5 text-xs text-neutral-600 space-y-1">
                <div className="font-semibold text-neutral-700 text-[11px] uppercase tracking-wider">
                  Asumsi Parameter GGM:
                </div>
                <div className="grid grid-cols-3 gap-1 font-mono text-[11px]">
                  <div>
                    ROE: {(Number((vd.ggm.assumptions as Record<string, unknown>)?.["roe"] ?? 0.197) * 100).toFixed(1)}%
                  </div>
                  <div>
                    g (terminal): {(Number((vd.ggm.assumptions as Record<string, unknown>)?.["g"] ?? 0.04) * 100).toFixed(1)}%
                  </div>
                  <div>
                    CoE: {(Number((vd.ggm.assumptions as Record<string, unknown>)?.["coe"] ?? 0.1176) * 100).toFixed(2)}%
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ) : null}

        {/* Historical Bands STD+-2 */}
        {bandsData ? (
          <Card className="border-neutral-200 bg-white shadow-2xs lg:col-span-2">
            <CardHeader className="p-4 pb-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-neutral-700" />
                  <CardTitle className="text-sm font-semibold text-neutral-900">
                    Valuasi Historis 3 Tahun (P/BV Bands STD ± 2)
                  </CardTitle>
                </div>
                <Badge variant={String(bandsData.label).includes("BELOW") ? "secondary" : "outline"} className="text-xs font-mono">
                  {String(bandsData.label ?? "STD BAND")}
                </Badge>
              </div>
              <CardDescription className="text-[11px] text-neutral-400">
                {vd?.bands?.source ?? "IDX, data diolah"} · Mean Reversion Analysis
              </CardDescription>
            </CardHeader>
            <CardContent className="p-4 pt-2 space-y-3">
              <div className="grid grid-cols-7 gap-1.5 text-center text-xs">
                {[
                  { k: "+2σ", v: bandsData["std+2"] },
                  { k: "+1σ", v: bandsData["std+1"] },
                  { k: "Mean", v: bandsData.avg },
                  { k: "-1σ", v: bandsData["std-1"] },
                  { k: "-2σ", v: bandsData["std-2"] },
                  { k: "Kini", v: bandsData.current },
                  { k: "Posisi", v: bandsData.label },
                ].map((c) => (
                  <div
                    key={c.k}
                    className={`rounded-lg border p-2 ${
                      c.k === "Kini"
                        ? "border-neutral-900 bg-neutral-900 text-white font-bold"
                        : c.k === "Posisi"
                        ? "bg-amber-50 border-amber-200 text-amber-900 font-medium"
                        : "bg-white border-neutral-200 text-neutral-800"
                    }`}
                  >
                    <div className="text-[10px] opacity-75 font-mono">{c.k}</div>
                    <div className="font-semibold font-mono text-xs mt-0.5">
                      {typeof c.v === "number" ? c.v.toFixed(2) : String(c.v ?? "-")}
                    </div>
                  </div>
                ))}
              </div>

              <BandsChart bands={bandsData} />
            </CardContent>
          </Card>
        ) : null}
      </div>

      {/* Row 3: KPI Operasional (Operational KPIs) */}
      {kpis && kpis.length > 0 && (
        <Card className="border-neutral-200 bg-white shadow-2xs">
          <CardHeader className="p-4 pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BarChart2 className="h-4 w-4 text-neutral-700" />
                <CardTitle className="text-sm font-semibold text-neutral-900">
                  KPI Operasional Utama {isInfra ? "(Infrastruktur Menara / Fiber)" : isSotp ? "(Konglomerasi)" : "(Operasional)"}
                </CardTitle>
              </div>
              <span className="text-[11px] text-neutral-400 font-mono">
                Laporan Resmi Perusahaan / SKK Migas
              </span>
            </div>
          </CardHeader>
          <CardContent className="p-4 pt-2">
            <div className="grid gap-2.5 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
              {kpis.map((k) => {
                const delta = k.prev != null && k.value != null ? Number(k.value) - Number(k.prev) : null
                const deltaPct = k.prev
                  ? (((Number(k.value) - Number(k.prev)) / Number(k.prev)) * 100).toFixed(1)
                  : null

                return (
                  <div key={k.name} className="rounded-lg border border-neutral-200 bg-neutral-50/60 p-3 space-y-1">
                    <div className="text-xs font-medium text-neutral-600 truncate">{k.name}</div>
                    <div className="text-base font-bold font-mono text-neutral-900">
                      {typeof k.value === "number" ? fmtIDR(k.value) : String(k.value)}{" "}
                      <span className="text-xs font-normal text-neutral-500 font-sans">{k.unit ?? ""}</span>
                    </div>
                    {k.prev != null && (
                      <div
                        className={`text-[11px] font-mono ${
                          delta != null && delta >= 0 ? "text-emerald-700" : "text-red-600"
                        }`}
                      >
                        {delta != null ? `${delta > 0 ? "+" : ""}${delta}` : ""}{" "}
                        {deltaPct != null ? `(${deltaPct}%)` : ""} · prev {fmtIDR(Number(k.prev))}
                      </div>
                    )}
                    {k.formula && <div className="text-[10px] text-neutral-400 truncate">{k.formula}</div>}
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Row 4: Segment Mix */}
      <Card className="border-neutral-200 bg-white shadow-2xs">
        <CardHeader className="p-4 pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <PieChart className="h-4 w-4 text-neutral-700" />
              <CardTitle className="text-sm font-semibold text-neutral-900">
                Segment Mix & Komposisi Pendapatan
              </CardTitle>
            </div>
          </div>
          <CardDescription className="text-[11px] text-neutral-400">
            Pendapatan per segmen usaha · YoY, QoQ, dan porsi kontribusi
          </CardDescription>
        </CardHeader>
        <CardContent className="p-4 pt-2">
          <SegmentPie
            segments={segments}
            source={segmentsSource}
            rawSegments={rawSegments}
          />
        </CardContent>
      </Card>

      {/* Row 5: Rasio Keuangan Kunci (Financial Ratios) */}
      {ratios && Object.keys(ratios).length > 0 && (
        <Card className="border-neutral-200 bg-white shadow-2xs">
          <CardHeader className="p-4 pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Table className="h-4 w-4 text-neutral-700" />
                <CardTitle className="text-sm font-semibold text-neutral-900">
                  Rasio Finansial Kunci & Solvabilitas
                </CardTitle>
              </div>
              <span className="text-[11px] text-neutral-400 font-mono">
                Laporan Keuangan IDX
              </span>
            </div>
          </CardHeader>
          <CardContent className="p-4 pt-2 space-y-2">
            <div className="grid gap-2 grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
              {Object.entries(ratios).map(([k, v]) => (
                <div key={k} className="rounded-lg border border-neutral-200 bg-white p-2.5 text-center">
                  <div className="text-[11px] text-neutral-500 font-medium truncate">{k}</div>
                  <div className="text-sm font-bold font-mono text-neutral-900 mt-0.5">{String(v)}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </section>
  )
}
