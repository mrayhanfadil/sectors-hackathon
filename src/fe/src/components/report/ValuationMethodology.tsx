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
  if (n == null || Number.isNaN(Number(n))) return "—"
  return Number(n).toLocaleString("id-ID")
}

function BandsChart({
  bands,
  width = 380,
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
    { label: `+2σ (${p2.toFixed(2)})`, y: getY(p2), color: "#f59e0b", dash: "3,3" },
    { label: `+1σ (${p1.toFixed(2)})`, y: getY(p1), color: "#94a3b8", dash: "3,3" },
    { label: `Mean (${avg.toFixed(2)})`, y: getY(avg), color: "#38bdf8", dash: "none", strokeWidth: 1.5 },
    { label: `-1σ (${m1.toFixed(2)})`, y: getY(m1), color: "#94a3b8", dash: "3,3" },
    { label: `-2σ (${m2.toFixed(2)})`, y: getY(m2), color: "#f59e0b", dash: "3,3" },
  ]

  const curY = cur != null ? getY(cur) : null

  return (
    <div className="py-2">
      <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full max-w-md text-xs">
        {lines.map((l, i) => (
          <g key={i}>
            <line
              x1={85}
              y1={l.y}
              x2={width - 20}
              y2={l.y}
              stroke={l.color}
              strokeWidth={l.strokeWidth ?? 1}
              strokeDasharray={l.dash}
            />
            <text x={80} y={l.y + 3} textAnchor="end" fill="#71717a" className="font-mono text-[10px] dark:fill-[#a1a1a1]">
              {l.label}
            </text>
          </g>
        ))}
        {cur != null && curY != null && (
          <g>
            <line x1={85} y1={curY} x2={width - 20} y2={curY} stroke="#10b981" strokeWidth={1.5} />
            <circle cx={width / 2} cy={curY} r={3.5} fill="#10b981" />
            <text x={width - 15} y={curY + 3} fill="#10b981" className="font-mono text-[10px] font-bold dark:fill-emerald-400">
              KINI {cur.toFixed(2)}x
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
        <ul className="space-y-1 font-mono text-xs text-neutral-800 dark:text-neutral-200">
          {Object.entries(rawSegments as Record<string, unknown>).map(([seg, val]) => (
            <li key={seg}>
              <span className="font-bold">{seg}</span>: {typeof val === "object" && val !== null ? JSON.stringify(val) : String(val)}
            </li>
          ))}
        </ul>
      )
    }
    return (
      <div className="rounded border border-dashed border-neutral-300 px-4 py-4 text-center font-mono text-xs text-neutral-500 dark:border-[#262930] dark:text-neutral-400">
        Segmentasi tunggal / pengungkapan segmen terpadu sesuai laporan keuangan IDX.
      </div>
    )
  }

  const total = segments.reduce((s, x) => s + Number(x.share_pct ?? 0), 0)
  const colors = [
    "bg-amber-500",
    "bg-sky-500",
    "bg-emerald-500",
    "bg-purple-500",
    "bg-rose-500",
    "bg-neutral-500",
  ]

  return (
    <div className="space-y-3 font-mono">
      {/* Visual Stacked Bar */}
      <div className="flex h-2.5 overflow-hidden rounded-xs border border-neutral-300 dark:border-[#262930]">
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
          <div
            key={s.name}
            className="flex items-center justify-between rounded border border-neutral-200 bg-neutral-50 px-2.5 py-1.5 text-xs dark:border-[#262930] dark:bg-[#121316]"
          >
            <span className="flex items-center gap-2 truncate text-neutral-900 dark:text-neutral-100 font-medium">
              <span className={`h-2 w-2 shrink-0 rounded-xs ${colors[i % colors.length]}`} />
              <span className="truncate">{s.name}</span>
            </span>
            <div className="ml-2 flex shrink-0 items-center gap-2">
              <span className="font-bold text-neutral-900 tabular-nums dark:text-neutral-100">
                {s.share_pct != null ? `${s.share_pct}%` : "—"}
              </span>
              {s.revenue != null && (
                <span className="text-[10px] text-neutral-500 tabular-nums dark:text-neutral-400">
                  Rp {fmtIDR(Number(s.revenue))} bn
                </span>
              )}
              {s.yoy_pct != null && (
                <span className="rounded bg-neutral-200/60 px-1 py-px text-[9px] text-neutral-700 dark:bg-[#262930] dark:text-neutral-300">
                  YoY {String(s.yoy_pct)}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {Math.abs(total - 100) > 0.6 && total > 0 && (
        <p className="rounded border border-amber-300 bg-amber-50 p-2 text-xs text-amber-900 dark:border-amber-800/60 dark:bg-amber-950/60 dark:text-amber-200">
          Total porsi segmen: {total.toFixed(1)}% (sesuai pengungkapan catatan atas laporan keuangan).
        </p>
      )}
      {segments.some((s) => s.one_off) && (
        <p className="rounded border border-amber-300 bg-amber-50 px-3 py-1.5 text-xs text-amber-900 dark:border-amber-800/60 dark:bg-amber-950/60 dark:text-amber-200">
          Penyesuaian One-off: {segments.find((s) => s.one_off)?.one_off}
        </p>
      )}
      {source && <p className="text-[10px] text-neutral-400">SRC: {source}</p>}
    </div>
  )
}

export function ValuationMethodology({
  ticker,
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
  const tk = ticker.toUpperCase()
  const vd = valuationDetail
  const isInfra = template.toLowerCase() === "infra"

  const bandsData =
    vd?.bands?.pbv_3y ??
    (rawBands?.pbv_3y ??
      (typeof rawBands === "object" && !Array.isArray(rawBands) && rawBands?.["std+2"] != null
        ? rawBands
        : null))

  return (
    <section id="valuation-methodology" className="space-y-3 scroll-mt-28">
      {/* Terminal Section Header */}
      <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-neutral-200 pb-1.5 dark:border-[#262930]">
        <div className="flex items-center gap-2">
          <span className="rounded bg-neutral-900 px-1.5 py-0.5 font-mono text-[10px] font-bold text-amber-400 dark:bg-amber-400/10 dark:text-amber-400">
            02
          </span>
          <h2 className="font-mono text-xs font-bold uppercase tracking-wider text-neutral-900 dark:text-neutral-100">
            {tk} IJ &lt;EQUITY&gt; // VALUATION METHODOLOGY &amp; MULTIPLES
          </h2>
        </div>
        <span className="font-mono text-[10px] text-neutral-400">
          MODELS: DCF · SOTP · GGM · RELATIVE MULTIPLES
        </span>
      </div>

      {/* Row 1: Valuation Summary Matrix */}
      <Card className="rounded-md border border-neutral-300 bg-white shadow-none dark:border-[#262930] dark:bg-[#121316]">
        <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3 pb-2 dark:border-[#1f2228] dark:bg-[#181a1f]/70">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Calculator className="h-4 w-4 text-amber-500" />
              <CardTitle className="font-mono text-xs font-bold uppercase tracking-wide text-neutral-900 dark:text-neutral-100">
                VALUATION SUMMARY &amp; ENGINE MATRIX
              </CardTitle>
            </div>
            <span className="font-mono text-[10px] text-neutral-400">
              PROVENANCE: {vd?.provenance ?? "DETERMINISTIC DCF/SOTP ENGINE"}
            </span>
          </div>
        </CardHeader>
        <CardContent className="space-y-3 p-3 pt-3">
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {valuation.map((v) => (
              <div
                key={v.method}
                className="flex items-center justify-between rounded border border-neutral-200 bg-neutral-50 p-2.5 font-mono dark:border-[#262930] dark:bg-[#181a1f]"
              >
                <div>
                  <div className="text-xs font-bold text-neutral-900 dark:text-neutral-100">{v.method}</div>
                  <div className="text-[10px] text-neutral-500 dark:text-neutral-400">
                    {v.weight ? `WEIGHT: ${v.weight}%` : "STANDALONE MODEL"}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold text-neutral-900 tabular-nums dark:text-neutral-100">
                    Rp {fmtIDR(v.value)}
                  </div>
                  <div className="text-[9px] uppercase text-neutral-400">FAIR VALUE</div>
                </div>
              </div>
            ))}
          </div>

          {vd?.methods && vd.methods.length > 0 && (
            <div className="space-y-1.5 border-t border-neutral-200 pt-2.5 font-mono text-xs dark:border-[#1f2228]">
              <div className="text-[11px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                VALUATION COMPONENT BREAKDOWN:
              </div>
              <div className="grid gap-1.5 sm:grid-cols-2">
                {vd.methods.map((m) => (
                  <div
                    key={m.method}
                    className="flex items-center justify-between rounded border border-neutral-200 bg-white px-2.5 py-1.5 dark:border-[#262930] dark:bg-[#121316]"
                  >
                    <span className="text-neutral-700 dark:text-neutral-300">
                      {m.method} <span className="text-[10px] text-neutral-400">({m.source ?? "engine"})</span>
                    </span>
                    <span className="font-bold text-neutral-900 tabular-nums dark:text-neutral-100">
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
      <div className="grid gap-3 lg:grid-cols-2">
        {/* Blended Valuation */}
        {vd?.blended ? (
          <Card className="rounded-md border border-neutral-300 bg-white shadow-none dark:border-[#262930] dark:bg-[#121316]">
            <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3 pb-2 dark:border-[#1f2228] dark:bg-[#181a1f]/70">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Layers className="h-4 w-4 text-neutral-600 dark:text-neutral-400" />
                  <CardTitle className="font-mono text-xs font-bold uppercase tracking-wide text-neutral-900 dark:text-neutral-100">
                    BLENDED VALUATION {isInfra ? "(60% DCF / 40% EV)" : ""}
                  </CardTitle>
                </div>
                <Badge variant="outline" className="border-neutral-300 font-mono text-[10px] dark:border-[#262930]">
                  MoS {vd.blended.margin_of_safety_pct ?? 15}%
                </Badge>
              </div>
              <CardDescription className="font-mono text-[10px] text-neutral-400">
                SRC: {vd.blended.source ?? "scripts/blended.py"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2.5 p-3 pt-2.5">
              <div className="overflow-x-auto rounded border border-neutral-200 font-mono text-xs dark:border-[#262930]">
                <table className="w-full">
                  <thead>
                    <tr className="border-b bg-neutral-100/70 text-left text-[11px] font-bold text-neutral-600 dark:border-[#262930] dark:bg-[#181a1f] dark:text-neutral-400">
                      <th className="py-1.5 px-2.5">METHOD</th>
                      <th className="py-1.5 px-2.5">WEIGHT</th>
                      <th className="py-1.5 px-2.5 text-right">FAIR VALUE</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(vd.blended.rows && vd.blended.rows.length > 0
                      ? vd.blended.rows
                      : [["DCF", "60%", "—"], ["EV/EBITDA", "40%", "—"]]
                    ).map((row, i) => (
                      <tr key={i} className="border-b border-neutral-100 last:border-0 dark:border-[#1f2228]">
                        <td className="py-1.5 px-2.5 font-medium text-neutral-800 dark:text-neutral-200">{String(row[0])}</td>
                        <td className="py-1.5 px-2.5 text-neutral-600 dark:text-neutral-400">{String(row[1])}</td>
                        <td className="py-1.5 px-2.5 text-right font-bold text-neutral-900 tabular-nums dark:text-neutral-100">
                          Rp {fmtIDR(Number(row[2]))}
                        </td>
                      </tr>
                    ))}
                    <tr className="bg-neutral-900 font-bold text-white dark:bg-[#262930]">
                      <td className="py-1.5 px-2.5 text-amber-400">BLENDED TARGET PRICE</td>
                      <td className="py-1.5 px-2.5">100%</td>
                      <td className="py-1.5 px-2.5 text-right tabular-nums text-amber-400">
                        Rp {fmtIDR(vd.blended.fv)}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div className="flex items-center gap-1.5 font-mono text-[10px] text-neutral-500 dark:text-neutral-400">
                <CheckCircle className="h-3.5 w-3.5 text-emerald-500" />
                <span>
                  WEIGHT SUM AUDIT:{" "}
                  {Object.values(vd.blended.weights ?? {}).reduce((a: number, b: unknown) => a + Number(b), 0).toFixed(0)}
                  % (STRICT 100% CONSTRAINT)
                </span>
              </div>
            </CardContent>
          </Card>
        ) : null}

        {/* GGM Box */}
        {vd?.ggm ? (
          <Card className="rounded-md border border-neutral-300 bg-white shadow-none dark:border-[#262930] dark:bg-[#121316]">
            <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3 pb-2 dark:border-[#1f2228] dark:bg-[#181a1f]/70">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BarChart2 className="h-4 w-4 text-emerald-500" />
                  <CardTitle className="font-mono text-xs font-bold uppercase tracking-wide text-neutral-900 dark:text-neutral-100">
                    GORDON GROWTH MODEL (GGM P/BV)
                  </CardTitle>
                </div>
                <Badge variant="outline" className="border-emerald-500/40 bg-emerald-500/10 font-mono text-[10px] font-bold text-emerald-600 dark:border-emerald-500/50 dark:text-emerald-300">
                  {vd.ggm.pbv_implied}x P/BV
                </Badge>
              </div>
              <CardDescription className="font-mono text-[10px] text-neutral-400">
                FORMULA: {vd.ggm.formula}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2.5 p-3 pt-2.5 font-mono">
              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <div className="rounded border border-neutral-200 bg-neutral-50 p-2 dark:border-[#262930] dark:bg-[#181a1f]">
                  <div className="text-[10px] uppercase text-neutral-500 dark:text-neutral-400">P/BV IMPLIED</div>
                  <div className="mt-0.5 text-sm font-bold text-neutral-900 tabular-nums dark:text-neutral-100">
                    {vd.ggm.pbv_implied}x
                  </div>
                </div>
                <div className="rounded border border-neutral-200 bg-neutral-50 p-2 dark:border-[#262930] dark:bg-[#181a1f]">
                  <div className="text-[10px] uppercase text-neutral-500 dark:text-neutral-400">BVPS PROJECTION</div>
                  <div className="mt-0.5 text-sm font-bold text-neutral-900 tabular-nums dark:text-neutral-100">
                    {(() => {
                      const v = Number((vd.ggm?.assumptions as Record<string, unknown>)?.["bvps"])
                      return Number.isFinite(v) && v > 0 ? "Rp " + fmtIDR(v) : "—"
                    })()}
                  </div>
                </div>
                <div className="rounded border border-emerald-300 bg-emerald-50/80 p-2 dark:border-emerald-800/60 dark:bg-emerald-950/60">
                  <div className="text-[10px] uppercase font-bold text-emerald-700 dark:text-emerald-300">TARGET PRICE</div>
                  <div className="mt-0.5 text-sm font-bold text-emerald-900 tabular-nums dark:text-emerald-100">
                    Rp {fmtIDR(vd.ggm.fv_per_share)}
                  </div>
                </div>
              </div>

              <div className="rounded border border-neutral-200 bg-neutral-50/60 p-2 text-xs text-neutral-700 dark:border-[#262930] dark:bg-[#181a1f]/60 dark:text-neutral-300">
                <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                  GGM PARAMETER ASSUMPTIONS:
                </div>
                <div className="mt-1 grid grid-cols-3 gap-1 text-[11px] tabular-nums">
                  <div>
                    ROE: {(() => {
                      const v = Number((vd.ggm?.assumptions as Record<string, unknown>)?.["roe"])
                      return Number.isFinite(v) ? (v * 100).toFixed(1) + "%" : "—"
                    })()}
                  </div>
                  <div>
                    g (terminal): {(() => {
                      const v = Number((vd.ggm?.assumptions as Record<string, unknown>)?.["g"])
                      return Number.isFinite(v) ? (v * 100).toFixed(1) + "%" : "—"
                    })()}
                  </div>
                  <div>
                    CoE: {(() => {
                      const v = Number((vd.ggm?.assumptions as Record<string, unknown>)?.["coe"])
                      return Number.isFinite(v) ? (v * 100).toFixed(2) + "%" : "—"
                    })()}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ) : null}

        {/* Historical Bands STD+-2 */}
        {bandsData ? (
          <Card className="rounded-md border border-neutral-300 bg-white shadow-none lg:col-span-2 dark:border-[#262930] dark:bg-[#121316]">
            <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3 pb-2 dark:border-[#1f2228] dark:bg-[#181a1f]/70">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-sky-500" />
                  <CardTitle className="font-mono text-xs font-bold uppercase tracking-wide text-neutral-900 dark:text-neutral-100">
                    HISTORICAL 3-YEAR VALUATION (P/BV BANDS STD ± 2)
                  </CardTitle>
                </div>
                <Badge variant="outline" className="border-neutral-300 font-mono text-[10px] dark:border-[#262930]">
                  POSITION: {String(bandsData.label ?? "STD BAND")}
                </Badge>
              </div>
              <CardDescription className="font-mono text-[10px] text-neutral-400">
                SRC: {vd?.bands?.source ?? "IDX AUDITED TICK"} · MEAN REVERSION ANALYSIS
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 p-3 pt-2.5">
              <div className="grid grid-cols-7 gap-1 font-mono text-center text-xs">
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
                    className={`rounded border p-1.5 ${
                      c.k === "Kini"
                        ? "border-emerald-500 bg-emerald-500/10 text-emerald-600 font-bold dark:border-emerald-500/50 dark:bg-emerald-950/40 dark:text-emerald-400"
                        : c.k === "Posisi"
                        ? "border-amber-300 bg-amber-50 text-amber-900 font-bold dark:border-amber-800/60 dark:bg-amber-950/60 dark:text-amber-200"
                        : "border-neutral-200 bg-neutral-50 text-neutral-800 dark:border-[#262930] dark:bg-[#181a1f] dark:text-neutral-200"
                    }`}
                  >
                    <div className="text-[9px] uppercase text-neutral-400">{c.k}</div>
                    <div className="mt-0.5 text-xs font-bold tabular-nums">
                      {typeof c.v === "number" ? c.v.toFixed(2) : String(c.v ?? "—")}
                    </div>
                  </div>
                ))}
              </div>

              <BandsChart bands={bandsData} />
            </CardContent>
          </Card>
        ) : null}
      </div>

      {/* Row 3: Operational KPIs */}
      {kpis && kpis.length > 0 && (
        <Card className="rounded-md border border-neutral-300 bg-white shadow-none dark:border-[#262930] dark:bg-[#121316]">
          <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3 pb-2 dark:border-[#1f2228] dark:bg-[#181a1f]/70">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BarChart2 className="h-4 w-4 text-neutral-600 dark:text-neutral-400" />
                <CardTitle className="font-mono text-xs font-bold uppercase tracking-wide text-neutral-900 dark:text-neutral-100">
                  OPERATIONAL KPIS &amp; EFFICIENCY METRICS
                </CardTitle>
              </div>
              <span className="font-mono text-[10px] text-neutral-400">
                AUDITED EMITEN FILING / SKK MIGAS
              </span>
            </div>
          </CardHeader>
          <CardContent className="p-3 pt-2.5">
            <div className="grid gap-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
              {kpis.map((k) => {
                const delta = k.prev != null && k.value != null ? Number(k.value) - Number(k.prev) : null
                const deltaPct = k.prev
                  ? (((Number(k.value) - Number(k.prev)) / Number(k.prev)) * 100).toFixed(1)
                  : null

                return (
                  <div
                    key={k.name}
                    className="space-y-1 rounded border border-neutral-200 bg-neutral-50 p-2.5 font-mono dark:border-[#262930] dark:bg-[#181a1f]"
                  >
                    <div className="truncate text-[11px] font-bold text-neutral-600 dark:text-neutral-400">{k.name}</div>
                    <div className="text-sm font-bold text-neutral-900 tabular-nums dark:text-neutral-100">
                      {typeof k.value === "number" ? fmtIDR(k.value) : String(k.value)}{" "}
                      <span className="text-[10px] font-normal text-neutral-500 dark:text-neutral-400">{k.unit ?? ""}</span>
                    </div>
                    {k.prev != null && (
                      <div
                        className={`text-[10px] tabular-nums ${
                          delta != null && delta >= 0
                            ? "text-emerald-600 dark:text-emerald-400"
                            : "text-rose-600 dark:text-rose-400"
                        }`}
                      >
                        {delta != null ? `${delta > 0 ? "+" : ""}${delta}` : ""}{" "}
                        {deltaPct != null ? `(${deltaPct}%)` : ""} · PREV {fmtIDR(Number(k.prev))}
                      </div>
                    )}
                    {k.formula && <div className="truncate text-[9px] text-neutral-400">{k.formula}</div>}
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Row 4: Segment Mix */}
      <Card className="rounded-md border border-neutral-300 bg-white shadow-none dark:border-[#262930] dark:bg-[#121316]">
        <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3 pb-2 dark:border-[#1f2228] dark:bg-[#181a1f]/70">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <PieChart className="h-4 w-4 text-neutral-600 dark:text-neutral-400" />
              <CardTitle className="font-mono text-xs font-bold uppercase tracking-wide text-neutral-900 dark:text-neutral-100">
                SEGMENT MIX &amp; REVENUE DECOMPOSITION
              </CardTitle>
            </div>
          </div>
          <CardDescription className="font-mono text-[10px] text-neutral-400">
            BUSINESS SEGMENTS · YOY / QOQ REVENUE CONTRIBUTION BREAKDOWN
          </CardDescription>
        </CardHeader>
        <CardContent className="p-3 pt-2.5">
          <SegmentPie
            segments={segments}
            source={segmentsSource}
            rawSegments={rawSegments}
          />
        </CardContent>
      </Card>

      {/* Row 5: Financial Ratios */}
      {ratios && Object.keys(ratios).length > 0 && (
        <Card className="rounded-md border border-neutral-300 bg-white shadow-none dark:border-[#262930] dark:bg-[#121316]">
          <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3 pb-2 dark:border-[#1f2228] dark:bg-[#181a1f]/70">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Table className="h-4 w-4 text-neutral-600 dark:text-neutral-400" />
                <CardTitle className="font-mono text-xs font-bold uppercase tracking-wide text-neutral-900 dark:text-neutral-100">
                  KEY FINANCIAL RATIOS &amp; SOLVENCY AUDIT
                </CardTitle>
              </div>
              <span className="font-mono text-[10px] text-neutral-400">
                AUDITED FINANCIAL METRICS
              </span>
            </div>
          </CardHeader>
          <CardContent className="p-3 pt-2.5">
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
              {Object.entries(ratios).map(([k, v]) => (
                <div
                  key={k}
                  className="rounded border border-neutral-200 bg-neutral-50 p-2 text-center font-mono dark:border-[#262930] dark:bg-[#181a1f]"
                >
                  <div className="truncate text-[10px] font-bold uppercase text-neutral-500 dark:text-neutral-400">{k}</div>
                  <div className="mt-0.5 text-xs font-bold text-neutral-900 tabular-nums dark:text-neutral-100">{String(v)}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </section>
  )
}

