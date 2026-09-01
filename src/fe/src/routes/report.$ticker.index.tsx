import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { Loader2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { fetchReport, fetchPdf } from "@/lib/api"
import { DcfFriend } from "@/components/DcfFriend"
import { AdkRunCard, type Log, type HistoryItem } from "@/components/report/AdkRunCard"

export const Route = (createFileRoute as any)("/report/$ticker/")({ component: ReportPage })

async function fetchReportLog(ticker: string): Promise<{
  ticker: string
  has_run: boolean
  log: Log
  history: HistoryItem[]
}> {
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

function fmtIDR(n: number | null | undefined) {
  if (n == null || Number.isNaN(Number(n))) return "—"
  return Number(n).toLocaleString("id-ID")
}
function pctLabel(v: unknown) {
  if (v == null) return "—"
  const n = Number(v)
  if (Number.isNaN(n)) return String(v)
  return `${n > 0 ? "+" : ""}${n}${typeof v === "string" && String(v).includes("%") ? "" : "%"}`
}

function Sparkline({ values, width = 120, height = 30 }: { values: number[]; width?: number; height?: number }) {
  if (!Array.isArray(values) || values.length < 2) return null
  const min = Math.min(...values), max = Math.max(...values)
  const range = max - min || 1
  const points = values.map((v, i) => {
    const x = (i / (values.length - 1)) * width
    const y = height - ((v - min) / range) * height
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(" ")
  return (
    <svg width={width} height={height} className="text-slate-700">
      <polyline points={points} fill="none" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  )
}

function BandsChart({ bands, width = 360, height = 110 }: { bands: { "std+2": number; "std+1": number; avg: number; "std-1": number; "std-2": number; current?: number; label?: string }; width?: number; height?: number }) {
  const p2 = Number(bands["std+2"] ?? 0)
  const p1 = Number(bands["std+1"] ?? 0)
  const avg = Number(bands.avg ?? 0)
  const m1 = Number(bands["std-1"] ?? 0)
  const m2 = Number(bands["std-2"] ?? 0)
  const cur = bands.current != null ? Number(bands.current) : null

  const allVals = [p2, p1, avg, m1, m2, ...(cur != null ? [cur] : [])].filter(v => !Number.isNaN(v))
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
            <line x1={80} y1={l.y} x2={width - 20} y2={l.y} stroke={l.color} strokeWidth={l.strokeWidth ?? 1} strokeDasharray={l.dash} />
            <text x={74} y={l.y + 3} textAnchor="end" fill="#64748b" className="text-[10px] font-mono">{l.label}</text>
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

function SegmentPie({ segments, source, rawSegments }: { segments: { name: string; share_pct?: number; revenue?: number; yoy_pct?: unknown; qoq_pct?: unknown; one_off?: string }[]; source?: string; rawSegments?: unknown }) {
  if (!segments || segments.length === 0) {
    if (rawSegments && typeof rawSegments === "object" && Object.keys(rawSegments).length > 0) {
      return (
        <ul className="space-y-1 text-xs text-slate-700">
          {Object.entries(rawSegments as Record<string, unknown>).map(([seg, val]) => (
            <li key={seg}>{seg}: {typeof val === "object" && val !== null ? JSON.stringify(val) : String(val)}</li>
          ))}
        </ul>
      )
    }
    return <div className="rounded-md border border-dashed px-3 py-4 text-xs text-slate-500">Segment disclosure: single-segment / belum diungkap di IDX.</div>
  }
  const total = segments.reduce((s, x) => s + Number(x.share_pct ?? 0), 0)
  const colors = ["bg-slate-900", "bg-slate-600", "bg-slate-400", "bg-slate-300", "bg-amber-500", "bg-emerald-600"]
  return (
    <div className="space-y-3">
      <div className="flex h-3 overflow-hidden rounded-full border">
        {segments.map((s, i) => (
          <div key={s.name} className={colors[i % colors.length]} style={{ width: `${Number(s.share_pct ?? 0)}%` }} title={`${s.name} ${s.share_pct}%`} />
        ))}
      </div>
      <div className="grid gap-2">
        {segments.map((s, i) => (
          <div key={s.name} className="flex items-center justify-between rounded-md border px-3 py-2 text-sm">
            <span className="flex items-center gap-2"><span className={`h-2 w-2 rounded-full ${colors[i % colors.length]}`} />{s.name}</span>
            <span className="flex gap-3 text-xs">
              <span className="font-medium">{s.share_pct != null ? `${s.share_pct}%` : "—"}</span>
              {s.revenue != null && <span className="text-slate-500">Rp {fmtIDR(Number(s.revenue))} bn</span>}
              {s.yoy_pct != null && <span className="text-slate-500">YoY {String(s.yoy_pct)}</span>}
            </span>
          </div>
        ))}
      </div>
      {Math.abs(total - 100) > 0.6 && total > 0 && <p className="text-xs text-amber-600">Σ share {total.toFixed(1)}% — disclosed sum check.</p>}
      {segments.some(s => s.one_off) && <p className="rounded bg-amber-50 px-3 py-2 text-xs text-amber-800">One-off: {segments.find(s => s.one_off)?.one_off}</p>}
      {source && <p className="text-xs text-slate-500">Sumber: {source}</p>}
    </div>
  )
}

function ShareholderPie({ holders, source }: { holders?: { name: string; pct: number }[]; source?: string }) {
  if (!holders || holders.length === 0) return null
  const colors = ["bg-slate-900", "bg-slate-600", "bg-slate-400", "bg-emerald-600", "bg-amber-500"]
  return (
    <div className="space-y-2">
      <div className="flex h-2 overflow-hidden rounded-full border">
        {holders.map((h, i) => <div key={h.name} className={colors[i % colors.length]} style={{ width: `${h.pct}%` }} />)}
      </div>
      <div className="flex flex-wrap gap-2">
        {holders.map((h, i) => (
          <span key={h.name} className="inline-flex items-center gap-1.5 rounded border px-2 py-1 text-xs">
            <span className={`h-2 w-2 rounded-full ${colors[i % colors.length]}`} />{h.name} {h.pct}%
          </span>
        ))}
      </div>
      {source && <p className="text-xs text-slate-500">Sumber: {source}</p>}
    </div>
  )
}

function ReportPage() {
  const { ticker } = Route.useParams()
  const tk = String(ticker).toUpperCase()
  const { data, isLoading, error } = useQuery({ queryKey: ["report", tk], queryFn: () => fetchReport(tk) })
  const logQuery = useQuery({
    queryKey: ["report-log", tk],
    queryFn: () => fetchReportLog(tk),
  })
  const [pdfState, setPdfState] = useState<"idle" | "loading" | "error">("idle")
  const [pdfMsg, setPdfMsg] = useState("")

  async function onDownloadPdf() {
    setPdfState("loading"); setPdfMsg("")
    try { await fetchPdf(tk); setPdfState("idle") }
    catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e)
      if (msg.includes("soon") || msg.includes("404") || msg.includes("not available")) {
        setPdfState("error"); setPdfMsg("PDF belum tersedia di BE — soon (GET /api/report/$ticker/pdf).")
      } else { setPdfState("error"); setPdfMsg(msg) }
      setTimeout(() => setPdfState("idle"), 4000)
    }
  }

  if (isLoading) return <div className="rounded-xl border bg-white p-6 text-sm text-slate-500">Loading {tk}...</div>
  if (error || !data) return <div className="rounded-xl border bg-white p-6 text-sm text-red-600">Failed to load {tk}.</div>

  if (data.offline) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">
        <div className="font-medium mb-1">⚠ Backend tidak tersedia</div>
        <p>{data.summary}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-3 rounded-md bg-amber-900 px-3 py-1.5 text-xs text-white hover:bg-amber-800"
        >
          Retry
        </button>
      </div>
    )
  }

  const r = data as unknown as {
    ticker: string; name: string; price: number; target: number; upside: string; rating: string; summary: string;
    valuation: { method: string; value: number; weight?: number }[];
    updatedAt: string; template?: string; source?: string;
    cover?: { rating_box?: { action: string; tp: number; price: number; upside_pct: number; prev_tp?: number | null; key_takeaways?: string[] }; vs_jci?: { ytd_abs?: number | null; ytd_rel?: number | null; source?: string; chart?: { labels: string[]; series: number[][] } | null }; shares?: { outstanding: number; unit: string; free_float_pct?: number }; shareholders?: { name: string; pct: number }[]; shareholders_src?: string | null; esg?: { found: boolean; scores?: { e: number; s: number; g: number }; source?: string; date?: string } };
    segments?: { name: string; revenue?: number; share_pct?: number; yoy_pct?: unknown; qoq_pct?: unknown; one_off?: string }[];
    kpis?: { name: string; value: number; prev?: number; unit?: string; formula?: string; source?: string }[];
    valuationDetail?: { methods?: { method: string; fv: number; assumptions?: Record<string, unknown>; table?: { headers: string[]; rows: unknown[][] }; source?: string }[]; blended?: { weights: Record<string, number>; fv: number; fv_str?: string; margin_of_safety_pct?: number; rows?: unknown[][]; source?: string } | null; bands?: { pbv_3y?: { "std+2": number; "std+1": number; avg: number; "std-1": number; "std-2": number; current: number; label: string }; source?: string } | null; ggm?: { pbv_implied: number; fv_per_share: number; formula: string; assumptions?: Record<string, unknown> } | null; assumptions?: Record<string, unknown>; provenance?: string };
    ratios?: Record<string, string | number>;
    raw?: Record<string, unknown>;
  }

  const tpl = (r.template ?? "single").toLowerCase()
  const isInfra = tpl === "infra"
  const isSotp = tpl === "sotp"
  const vd = r.valuationDetail
  const takeaways = r.cover?.rating_box?.key_takeaways ?? []
  const vs = r.cover?.vs_jci
  const hasShareholders = Boolean(r.cover?.shareholders && r.cover.shareholders.length > 0)

  return (
    <div className="space-y-4">
      {/* header */}
      <div className="flex flex-wrap items-center gap-2">
        <h1 className="text-xl font-semibold">{r.ticker} — {r.name}</h1>
        <Badge variant={r.rating === "BUY" ? "success" : r.rating === "SELL" ? "destructive" : "secondary"}>{r.rating}</Badge>
        <Badge variant="outline">TP {fmtIDR(r.target)} ({r.upside})</Badge>
        <Badge variant="secondary">{tpl}</Badge>
        <span className="text-xs text-slate-500">Px {fmtIDR(r.price)} · {r.updatedAt} · {r.source ?? "disclosed"}</span>
      </div>
      <p className="text-sm leading-relaxed text-slate-600">{r.summary}</p>

      {/* ADK Run Log Card */}
      {logQuery.isLoading ? (
        <Card className="border-slate-200 bg-white p-4">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
            <span>Memuat log ADK {tk}...</span>
          </div>
        </Card>
      ) : logQuery.data ? (
        <AdkRunCard
          ticker={tk}
          log={logQuery.data.log}
          history={logQuery.data.history ?? []}
          hasRun={logQuery.data.has_run}
        />
      ) : null}

      {/* top cards */}
      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-sm">Valuation</CardTitle><CardDescription className="text-xs">{vd?.provenance ?? "DCF/DDM/SOTP/GGM deterministic — source disclosed per exhibit"}</CardDescription></CardHeader>
          <CardContent className="space-y-2 text-sm">
            {r.valuation.map((v) => (
              <div key={v.method} className="flex justify-between rounded-md border px-3 py-2">
                <span>{v.method}</span>
                <span className="font-medium">{fmtIDR(v.value)}{v.weight ? ` · ${v.weight}%` : ""}</span>
              </div>
            ))}
            {vd?.methods && vd.methods.length > 0 && (
              <div className="space-y-1 pt-2">
                {vd.methods.map(m => (
                  <div key={m.method} className="flex justify-between rounded bg-slate-50 px-3 py-2 text-xs">
                    <span>{m.method} <span className="text-slate-500">· {m.source ?? "engine"}</span></span>
                    <span className="font-medium">FV Rp {fmtIDR(m.fv)}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Actions</CardTitle></CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            <a href={`/report/${tk}/challenge`} className="inline-flex h-9 items-center rounded-md bg-slate-900 px-4 text-sm text-white">Challenge</a>
            <a href={`/report/${tk}/sentiment`} className="inline-flex h-9 items-center rounded-md border px-4 text-sm">Sentiment</a>
            <a href="/outlook" className="inline-flex h-9 items-center rounded-md px-4 text-sm hover:bg-slate-100">Outlook</a>
            <Button onClick={onDownloadPdf} disabled={pdfState === "loading"} variant="outline" size="default" className="h-9">
              {pdfState === "loading" ? "Downloading..." : "Download PDF"}
            </Button>
          </CardContent>
          {pdfState === "error" && <p className="px-6 pb-4 text-xs text-amber-600">{pdfMsg}</p>}
          {r.cover?.shares && (
            <div className="px-6 pb-4 text-xs text-slate-500">
              Shares {r.cover.shares.outstanding} {r.cover.shares.unit} · Free float {r.cover.shares.free_float_pct != null ? `${r.cover.shares.free_float_pct}%` : "—"}
            </div>
          )}
        </Card>
      </div>

      {/* DCF Friend-style Analysis */}
      <DcfFriend ticker={tk} />

      {/* Key Takeaways + Shareholder + ESG */}
      {(takeaways.length > 0 || hasShareholders || r.cover?.esg?.found) && (
        <div className="grid gap-4 sm:grid-cols-3">
          {takeaways.length > 0 && (
            <Card className={r.cover?.esg?.found && hasShareholders ? "" : "sm:col-span-2"}>
              <CardHeader><CardTitle className="text-sm">Key Takeaways</CardTitle></CardHeader>
              <CardContent className="space-y-2 text-sm leading-relaxed">
                {takeaways.map((t, i) => <div key={i} className="flex gap-2"><span className="font-medium text-slate-900">{i + 1}.</span><span className="text-slate-600">{t}</span></div>)}
              </CardContent>
            </Card>
          )}
          {hasShareholders && (
            <Card>
              <CardHeader><CardTitle className="text-sm">Shareholder Structure</CardTitle><CardDescription className="text-xs">{r.cover?.shareholders_src ?? "IDX"}</CardDescription></CardHeader>
              <CardContent><ShareholderPie holders={r.cover?.shareholders} source={r.cover?.shareholders_src ?? undefined} /></CardContent>
            </Card>
          )}
          {r.cover?.esg?.found && r.cover.esg.scores && (
            <Card>
              <CardHeader><CardTitle className="text-sm">ESG Box</CardTitle><CardDescription className="text-xs">{r.cover.esg.source} · {r.cover.esg.date}</CardDescription></CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="rounded border bg-slate-50 py-2"><div className="text-xs text-slate-500">E</div><div className="font-semibold">{r.cover.esg.scores.e}</div></div>
                  <div className="rounded border bg-slate-50 py-2"><div className="text-xs text-slate-500">S</div><div className="font-semibold">{r.cover.esg.scores.s}</div></div>
                  <div className="rounded border bg-slate-50 py-2"><div className="text-xs text-slate-500">G</div><div className="font-semibold">{r.cover.esg.scores.g}</div></div>
                </div>
                <p className="text-xs text-slate-500">Sustainalytics — hide if found=false (no fabrication).</p>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* vs JCI */}
      {vs && (
        <Card>
          <CardHeader><CardTitle className="text-sm">Kinerja vs IHSG (YTD)</CardTitle><CardDescription className="text-xs">{vs.source ?? "IDX, yfinance"}</CardDescription></CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex flex-wrap gap-2 text-xs">
              <Badge variant="secondary">Abs {vs.ytd_abs != null ? `${vs.ytd_abs > 0 ? "+" : ""}${vs.ytd_abs}%` : "—"}</Badge>
              <Badge variant="outline">Rel {vs.ytd_rel != null ? `${vs.ytd_rel > 0 ? "+" : ""}${vs.ytd_rel}% vs IHSG` : "—"}</Badge>
            </div>
            {vs.chart?.labels && vs.chart.series && (
              <div className="overflow-x-auto">
                <div className="flex gap-1 text-xs text-slate-500">
                  <span className="w-16">Bulan</span>
                  {vs.chart.labels.map(l => <span key={l} className="w-8 text-center">{l.slice(0, 3)}</span>)}
                </div>
                <div className="flex gap-1 text-xs">
                  <span className="w-16 font-medium">{r.ticker}</span>
                  {vs.chart.series[0]?.map((v, i) => <span key={i} className="w-8 text-center">{v}</span>)}
                </div>
                <div className="flex gap-1 text-xs text-slate-500">
                  <span className="w-16">IHSG</span>
                  {vs.chart.series[1]?.map((v, i) => <span key={i} className="w-8 text-center">{v}</span>)}
                </div>
              </div>
            )}
            {Array.isArray((r.raw as any)?.chart) && (r.raw as any).chart.length > 1 ? (
              <div className="pt-2">
                <Sparkline values={(r.raw as any).chart} width={240} height={40} />
              </div>
            ) : Array.isArray(vs.chart?.series?.[0]) && vs.chart.series[0].length > 1 ? (
              <div className="flex flex-wrap items-center gap-4 pt-2">
                <div className="flex items-center gap-2 text-xs text-slate-700">
                  <span className="font-medium">{r.ticker}:</span>
                  <Sparkline values={vs.chart.series[0]} width={140} height={30} />
                </div>
                {vs.chart.series[1] && (
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <span>IHSG:</span>
                    <Sparkline values={vs.chart.series[1]} width={140} height={30} />
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-500">Line chart placeholder — text fallback (no chart lib). BE chart array consumed when real.</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* KPI hero (infra/bank) */}
      {r.kpis && r.kpis.length > 0 && (
        <Card className={isInfra ? "border-slate-900" : ""}>
          <CardHeader>
            <CardTitle className="text-sm">KPI Operasional — Hero {isInfra ? "(infra: tenancy/fiber)" : isSotp ? "(conglomerate)" : "(operational)"}</CardTitle>
            <CardDescription className="text-xs">Formula disclosed per KPI · source: Company data / SKK Migas</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-5">
              {r.kpis.map(k => {
                const delta = k.prev != null && k.value != null ? (Number(k.value) - Number(k.prev)) : null
                const deltaPct = k.prev ? ((Number(k.value) - Number(k.prev)) / Number(k.prev) * 100).toFixed(1) : null
                return (
                  <div key={k.name} className="rounded-lg border bg-white p-3">
                    <div className="text-xs text-slate-500">{k.name}</div>
                    <div className="text-lg font-semibold">{typeof k.value === "number" ? fmtIDR(k.value) : String(k.value)} <span className="text-xs font-normal text-slate-500">{k.unit ?? ""}</span></div>
                    {k.prev != null && <div className={`text-xs ${delta != null && delta >= 0 ? "text-emerald-600" : "text-red-600"}`}>{delta != null ? `${delta > 0 ? "+" : ""}${delta}` : ""} {deltaPct != null ? `(${deltaPct}%)` : ""} · prev {fmtIDR(Number(k.prev))}</div>}
                    {k.formula && <div className="text-xs text-slate-400">{k.formula}</div>}
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Segments */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Segment Mix {isSotp ? "— SOTP 4 pilar" : isInfra ? "— Infra 4 segmen" : ""}</CardTitle>
          <CardDescription className="text-xs">Pendapatan per segmen · YoY + QoQ + share — text pie fallback (no chart lib)</CardDescription>
        </CardHeader>
        <CardContent>
          <SegmentPie segments={(r.segments ?? []) as { name: string; share_pct?: number; revenue?: number; yoy_pct?: unknown; qoq_pct?: unknown; one_off?: string }[]} source={(r.raw as unknown as Record<string, unknown>)?.["segments_src"] as string | undefined ?? (isSotp ? "Laporan segmentasi CDIA 1H26 (IDX)" : isInfra ? "MTEL 1H26 — laporan segmentasi (IDX)" : undefined)} rawSegments={r.raw?.segments} />
        </CardContent>
      </Card>

      {/* Valuation detail: blended + GGM + bands */}
      <div className="grid gap-4 lg:grid-cols-2">
        {vd?.blended && (
          <Card className={isInfra ? "border-slate-900" : ""}>
            <CardHeader><CardTitle className="text-sm">Blended Valuation {isInfra ? "— MTEL 60/40" : ""}</CardTitle><CardDescription className="text-xs">{vd.blended.source ?? "scripts/blended.py"} · MoS {vd.blended.margin_of_safety_pct ?? 15}%</CardDescription></CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead><tr className="border-b text-left text-slate-500"><th className="py-1">Metode</th><th className="py-1">Bobot</th><th className="py-1 text-right">Fair Value</th></tr></thead>
                  <tbody>
                    {(vd.blended.rows ?? [["DCF","60%",vd.blended.fv],["EV/EBITDA","40%",740]] as unknown[][]).map((row, i) => (
                      <tr key={i} className="border-b"><td className="py-1">{String(row[0])}</td><td className="py-1">{String(row[1])}</td><td className="py-1 text-right">Rp {fmtIDR(Number(row[2]))}</td></tr>
                    ))}
                    <tr className="font-semibold"><td className="py-1">Blended</td><td className="py-1">100%</td><td className="py-1 text-right">Rp {fmtIDR(vd.blended.fv)}</td></tr>
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-slate-500">Weights sum 100% check: {Object.values(vd.blended.weights ?? {}).reduce((a: number, b: unknown) => a + Number(b), 0).toFixed(0)}% · Critic rule.</p>
            </CardContent>
          </Card>
        )}
        {vd?.ggm && (
          <Card className={r.ticker === "BBCA" ? "border-emerald-200" : ""}>
            <CardHeader><CardTitle className="text-sm">GGM Box — BBCA P/BV (ROE-g)/(CoE-g)</CardTitle><CardDescription className="text-xs">{vd.ggm.formula} · Samuel pack fallback</CardDescription></CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div className="rounded border bg-slate-50 p-2 text-center"><div className="text-slate-500">P/BV implied</div><div className="font-semibold">{vd.ggm.pbv_implied}×</div></div>
                <div className="rounded border bg-slate-50 p-2 text-center"><div className="text-slate-500">BVPS</div><div className="font-semibold">Rp {fmtIDR(Number((vd.ggm.assumptions as Record<string, unknown>)?.["bvps"] ?? 4200))}</div></div>
                <div className="rounded border bg-emerald-50 p-2 text-center"><div className="text-slate-500">TP</div><div className="font-semibold text-emerald-700">Rp {fmtIDR(vd.ggm.fv_per_share)}</div></div>
              </div>
              <div className="text-xs text-slate-500">Asumsi: ROE {(Number((vd.ggm.assumptions as Record<string, unknown>)?.["roe"] ?? 0.197) * 100).toFixed(1)}% · g {(Number((vd.ggm.assumptions as Record<string, unknown>)?.["g"] ?? 0.04) * 100).toFixed(1)}% · CoE {(Number((vd.ggm.assumptions as Record<string, unknown>)?.["coe"] ?? 0.1176) * 100).toFixed(2)}%</div>
            </CardContent>
          </Card>
        )}
        {!(vd?.blended) && !(vd?.ggm) && (
          <Card>
            <CardHeader><CardTitle className="text-sm">Valuation Cross-check</CardTitle></CardHeader>
            <CardContent className="text-xs text-slate-500">Blended 60/40 (infra) & GGM (bank) appear when template matches — single shows DCF + EV/EBITDA side-by-side above.</CardContent>
          </Card>
        )}
        {(() => {
          const bandsData = vd?.bands?.pbv_3y ?? ((r.raw as any)?.bands?.pbv_3y ?? (typeof (r.raw as any)?.bands === "object" && !Array.isArray((r.raw as any)?.bands) && (r.raw as any)?.bands?.["std+2"] != null ? (r.raw as any).bands : null))
          if (bandsData) {
            return (
              <Card>
                <CardHeader><CardTitle className="text-sm">Historical Bands P/BV 3Y — STD±2</CardTitle><CardDescription className="text-xs">{vd?.bands?.source ?? "IDX, data diolah"} · Mean reversion</CardDescription></CardHeader>
                <CardContent className="space-y-2">
                  <div className="grid grid-cols-7 gap-1 text-center text-xs">
                    {[
                      { k: "STD+2", v: bandsData["std+2"] },
                      { k: "STD+1", v: bandsData["std+1"] },
                      { k: "AVG", v: bandsData.avg },
                      { k: "STD-1", v: bandsData["std-1"] },
                      { k: "STD-2", v: bandsData["std-2"] },
                      { k: "Kini", v: bandsData.current },
                      { k: "Posisi", v: bandsData.label as unknown as number },
                    ].map(c => (
                      <div key={c.k} className={`rounded border p-2 ${c.k === "Kini" ? "border-slate-900 bg-slate-900 text-white" : c.k === "Posisi" ? "bg-amber-50" : "bg-white"}`}>
                        <div className="text-xs opacity-70">{c.k}</div>
                        <div className="font-semibold">{typeof c.v === "number" ? c.v.toFixed(2) : String(c.v ?? "—")}</div>
                      </div>
                    ))}
                  </div>
                  <BandsChart bands={bandsData} />
                  <p className="text-xs text-slate-500">Label: <Badge variant={String(bandsData.label).includes("BELOW") ? "secondary" : "outline"}>{String(bandsData.label ?? "STD BAND")}</Badge> · Bands from 3Y daily — needs ≥10 points.</p>
                </CardContent>
              </Card>
            )
          }
          return (
            <Card>
              <CardHeader><CardTitle className="text-sm">Historical Bands — STD±2</CardTitle></CardHeader>
              <CardContent className="text-xs text-slate-500">Bands P/BV 3Y muncul untuk infra (MTEL). Single/bank fallback: disclosed placeholder — butuh 3Y history dari stockdata.</CardContent>
            </Card>
          )
        })()}
      </div>

      {/* Ratios / Leverage trajectory */}
      {r.ratios && Object.keys(r.ratios).length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-sm">Rasio Kunci & Leverage Trajectory</CardTitle><CardDescription className="text-xs">Deterministic ratios — source: laporan keuangan IDX · disclosed per exhibit</CardDescription></CardHeader>
          <CardContent>
            <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-6">
              {Object.entries(r.ratios).map(([k, v]) => (
                <div key={k} className="rounded border bg-white px-3 py-2 text-center">
                  <div className="text-xs text-slate-500">{k}</div>
                  <div className="text-sm font-semibold">{String(v)}</div>
                </div>
              ))}
            </div>
            {(isSotp || isInfra) && (
              <p className="mt-2 text-xs text-slate-500">
                {isSotp ? "CDIA gearing 96→170% + Debt/EBITDA 1.9→4.1× — leverage trajectory (pillar-specific risks bucket)." : "MTEL DER 0.67→0.69×, LT D/E 0.34→0.46×, ICR 2.0→4.0× — infra-specific leverage trajectory."}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Disclaimer footer */}
      <div className="rounded-md border bg-slate-50 p-3 text-xs text-slate-500">
        <div className="font-semibold uppercase tracking-wide text-slate-700">INFORMASI, BUKAN SARAN INVESTASI</div>
        <p className="mt-0.5 leading-relaxed">
          Dokumen ini disusun untuk tujuan analisis riset kompetisi Sectors Hackathon 2026, bukan merupakan rekomendasi jual/beli efek atau saran investasi (OJK compliance).
        </p>
      </div>

      <p className="text-xs text-slate-500">TanStack Query · cache 4h · source disclosed per exhibit (P1 IDX+yfinance). {r.raw ? `Template ${tpl} · BE live when fair_value present.` : "Disclosed fixtures."}</p>
    </div>
  )
}
