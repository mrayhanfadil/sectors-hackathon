import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { AlertTriangle, RefreshCw, ShieldAlert, FileText, Database } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { fetchReport, fetchPdf } from "@/lib/api"
import { DcfFriend } from "@/components/DcfFriend"
import { type Log, type HistoryItem } from "@/components/report/AdkRunCard"
import { ReportHeader } from "@/components/report/ReportHeader"
import { ExecutiveSummary } from "@/components/report/ExecutiveSummary"
import { ValuationMethodology } from "@/components/report/ValuationMethodology"
import { RiskFactors } from "@/components/report/RiskFactors"
import { ADKRunSidebar } from "@/components/report/ADKRunSidebar"

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

function ReportPage() {
  const { ticker } = Route.useParams()
  const tk = String(ticker).toUpperCase()

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["report", tk],
    queryFn: () => fetchReport(tk),
  })

  const logQuery = useQuery({
    queryKey: ["report-log", tk],
    queryFn: () => fetchReportLog(tk),
  })

  const [pdfState, setPdfState] = useState<"idle" | "loading" | "error">("idle")
  const [pdfMsg, setPdfMsg] = useState("")

  async function onDownloadPdf() {
    setPdfState("loading")
    setPdfMsg("")
    try {
      await fetchPdf(tk)
      setPdfState("idle")
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e)
      if (msg.includes("soon") || msg.includes("404") || msg.includes("not available")) {
        setPdfState("error")
        setPdfMsg("PDF belum tersedia di BE (GET /api/report/$ticker/pdf).")
      } else {
        setPdfState("error")
        setPdfMsg(msg)
      }
      setTimeout(() => setPdfState("idle"), 4000)
    }
  }

  // Loading State
  if (isLoading) {
    return (
      <div className="space-y-4">
        <p className="text-center text-xs text-slate-500">
          Lagi nyiapin laporan {tk}... datanya diambil langsung dari backend, tunggu sebentar ya.
        </p>
        <div className="h-20 animate-pulse rounded-xl border border-slate-200 bg-white p-4" />
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
          <div className="space-y-4">
            <div className="h-64 animate-pulse rounded-xl border border-slate-200 bg-white" />
            <div className="h-80 animate-pulse rounded-xl border border-slate-200 bg-white" />
          </div>
          <div className="h-96 animate-pulse rounded-xl border border-slate-200 bg-white" />
        </div>
      </div>
    )
  }

  // Error State
  if (error || !data) {
    return (
      <Card className="border-red-200 bg-red-50/50 p-6">
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-red-900">
              Gagal Memuat Laporan Riset {tk}
            </h3>
            <p className="text-xs text-red-700 leading-relaxed">
              Terjadi kesalahan saat memuat data laporan dari backend. Pastikan server API aktif.
            </p>
            <Button
              onClick={() => refetch()}
              size="sm"
              variant="outline"
              className="mt-2 h-8 gap-1.5 bg-white text-xs border-red-200 text-red-800 hover:bg-red-50"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              <span>Coba Lagi</span>
            </Button>
          </div>
        </div>
      </Card>
    )
  }

  // Offline State (Honest fallback)
  if (data.offline) {
    return (
      <div className="space-y-4">
        <Card className="border-amber-200 bg-amber-50/80 p-6 text-sm text-amber-900 shadow-2xs">
          <div className="flex items-start gap-3">
            <ShieldAlert className="h-5 w-5 text-amber-700 shrink-0 mt-0.5" />
            <div className="space-y-2">
              <h3 className="font-semibold text-amber-950">Backend Tidak Tersedia (Mode Offline)</h3>
              <p className="text-xs leading-relaxed text-amber-800">{data.summary}</p>
              <Button
                onClick={() => window.location.reload()}
                size="sm"
                className="mt-2 h-8 bg-amber-900 text-xs text-white hover:bg-amber-800"
              >
                <RefreshCw className="h-3.5 w-3.5 mr-1" />
                <span>Muat Ulang Halaman</span>
              </Button>
            </div>
          </div>
        </Card>
      </div>
    )
  }

  const r = data as unknown as {
    ticker: string
    name: string
    price: number | null
    target: number | null
    upside: string | null
    rating: string | null
    summary: string
    valuation: { method: string; value: number; weight?: number }[]
    updatedAt: string
    template?: string
    source?: string
    cover?: {
      rating_box?: {
        action: string
        tp: number
        price: number
        upside_pct: number
        prev_tp?: number | null
        key_takeaways?: string[]
      }
      vs_jci?: {
        ytd_abs?: number | null
        ytd_rel?: number | null
        source?: string
        chart?: { labels: string[]; series: number[][] } | null
      }
      shares?: { outstanding: number; unit: string; free_float_pct?: number }
      shareholders?: { name: string; pct: number }[]
      shareholders_src?: string | null
      esg?: {
        found: boolean
        scores?: { e: number; s: number; g: number }
        source?: string
        date?: string
      }
    }
    segments?: {
      name: string
      revenue?: number
      share_pct?: number
      yoy_pct?: unknown
      qoq_pct?: unknown
      one_off?: string
    }[]
    kpis?: {
      name: string
      value: number
      prev?: number
      unit?: string
      formula?: string
      source?: string
    }[]
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
    ratios?: Record<string, string | number>
    raw?: Record<string, unknown>
  }

  const tpl = (r.template ?? "single").toLowerCase()
  const isInfra = tpl === "infra"
  const isSotp = tpl === "sotp"
  const vd = r.valuationDetail
  const takeaways = r.cover?.rating_box?.key_takeaways ?? []
  const vs = r.cover?.vs_jci
  const rawChart = Array.isArray((r.raw as any)?.chart) ? ((r.raw as any).chart as number[]) : undefined

  return (
    <div className="min-h-screen pb-12">
      {/* 1. Sticky Top Navigation & Header */}
      <ReportHeader
        ticker={tk}
        name={r.name}
        price={r.price}
        target={r.target}
        upside={r.upside}
        rating={r.rating}
        updatedAt={r.updatedAt}
        template={tpl}
        source={r.source}
        activeTab="valuation"
        onDownloadPdf={onDownloadPdf}
        pdfState={pdfState}
        pdfMsg={pdfMsg}
      />

      {/* Panduan pemula: rating + upside dalam 2 kalimat */}
      <div className="rounded-xl border border-sky-200 bg-sky-50 p-4 text-xs leading-relaxed text-sky-900">
        <span className="font-semibold">Baru mulai baca laporan saham? </span>
        BUY artinya analis menilai saham ini layak dibeli, HOLD artinya ditahan dulu, SELL artinya
        sebaiknya dihindari. Upside = potensi kenaikan harga ke harga wajar (target) — makin besar
        prosentasenya, makin besar potensi cuannya, tapi risikonya tetap perlu dicek di bagian bawah.
      </div>

      {/* 2. Responsive 2-Column Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6 items-start">
        {/* Main Content Area (Center / Scrollable) */}
        <div className="space-y-8 min-w-0">
          {/* Section 1: Ringkasan Eksekutif */}
          <ExecutiveSummary
            ticker={tk}
            name={r.name}
            price={r.price}
            target={r.target}
            upside={r.upside}
            rating={r.rating}
            summary={r.summary}
            takeaways={takeaways}
            vsJci={vs}
            rawChart={rawChart}
            shareholders={r.cover?.shareholders}
            shareholdersSrc={r.cover?.shareholders_src}
            esg={r.cover?.esg}
          />

          {/* Section 2: Metodologi Valuasi */}
          <ValuationMethodology
            ticker={tk}
            valuation={r.valuation ?? []}
            valuationDetail={vd}
            template={tpl}
            kpis={r.kpis}
            segments={r.segments}
            rawSegments={r.raw?.segments}
            segmentsSource={
              ((r.raw as unknown as Record<string, unknown>)?.["segments_src"] as string | undefined) ??
              (isSotp
                ? "Laporan segmentasi CDIA 1H26 (IDX)"
                : isInfra
                ? "MTEL 1H26 - laporan segmentasi (IDX)"
                : undefined)
            }
            ratios={r.ratios}
            rawBands={r.raw?.bands}
          />

          {/* Section 3: Analisis Sensitivitas & Model DCF Interaktif */}
          <section id="sensitivity-analysis" className="space-y-4 scroll-mt-28">
            <div>
              <h2 className="text-lg font-bold tracking-tight text-slate-900">
                3. Coba Ubah Asumsinya Sendiri (Model DCF Interaktif)
              </h2>
              <p className="text-xs text-slate-500">
                Geser-geser asumsi (mis. biaya modal & pertumbuhan) lalu lihat harga wajarnya berubah
                — termasuk skenario jelek (Bear), wajar (Base), dan bagus (Bull)
              </p>
            </div>
            <DcfFriend ticker={tk} />
          </section>

          {/* Section 4: Faktor Risiko & Solvabilitas */}
          <RiskFactors
            ticker={tk}
            template={tpl}
            ratios={r.ratios}
          />

          {/* Section 5: Sumber Data, Kepatuhan & Disclaimer */}
          <section id="sources-disclaimer" className="space-y-3 scroll-mt-28 border-t border-slate-200 pt-6">
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-800">
                <FileText className="h-4 w-4 text-slate-600" />
                <span>INFORMASI RISET - BUKAN SARAN INVESTASI</span>
              </div>
              <p className="text-xs leading-relaxed text-slate-600">
                Dokumen ini disusun untuk tujuan analisis riset kompetisi Sectors Hackathon 2026, bukan merupakan rekomendasi jual/beli efek atau saran investasi resmi (kepatuhan regulasi OJK). Seluruh estimasi dan nilai wajar dihitung secara deterministik berdasarkan data historis dan asumsi yang diungkapkan secara transparan.
              </p>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400 font-mono px-1">
              <div className="flex items-center gap-1.5">
                <Database className="h-3.5 w-3.5" />
                <span>Sumber: Laporan Keuangan IDX via Sectors API, SKK Migas, Sustainalytics</span>
              </div>
              <div>TanStack Query · Cache 4h · Template {tpl}</div>
            </div>
          </section>
        </div>

        {/* Right Column: Persistent Sticky Sidebar */}
        <div className="lg:sticky lg:top-28 space-y-4">
          <ADKRunSidebar
            ticker={tk}
            name={r.name}
            price={r.price}
            target={r.target}
            upside={r.upside}
            rating={r.rating}
            template={tpl}
            shares={r.cover?.shares}
            provenance={vd?.provenance}
            logLoading={logQuery.isLoading}
            logData={logQuery.data}
          />
        </div>
      </div>
    </div>
  )
}
