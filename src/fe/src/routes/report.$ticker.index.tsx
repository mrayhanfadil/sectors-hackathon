import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { AlertTriangle, RefreshCw, ShieldAlert, FileText, Database, Sliders, Info } from "lucide-react"
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
      <div className="space-y-4 font-mono">
        <div className="rounded border border-neutral-300 bg-neutral-100 p-3 text-center text-xs text-neutral-600 dark:border-[#262930] dark:bg-[#121316] dark:text-neutral-400">
          [MEMUAT] MENYIAPKAN LAPORAN SAHAM {tk}…...
        </div>
        <div className="h-16 animate-pulse rounded border border-neutral-200 bg-neutral-100 dark:border-[#262930] dark:bg-[#181a1f]" />
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_320px]">
          <div className="space-y-4">
            <div className="h-48 animate-pulse rounded border border-neutral-200 bg-neutral-100 dark:border-[#262930] dark:bg-[#181a1f]" />
            <div className="h-64 animate-pulse rounded border border-neutral-200 bg-neutral-100 dark:border-[#262930] dark:bg-[#181a1f]" />
          </div>
          <div className="h-80 animate-pulse rounded border border-neutral-200 bg-neutral-100 dark:border-[#262930] dark:bg-[#181a1f]" />
        </div>
      </div>
    )
  }

  // Error State
  if (error || !data) {
    return (
      <Card className="rounded-md border border-rose-300 bg-rose-50/70 p-4 font-mono dark:border-rose-800/60 dark:bg-rose-950/60">
        <div className="flex items-start gap-3">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600 dark:text-rose-400" />
          <div className="space-y-2">
            <h3 className="text-xs font-bold uppercase text-rose-900 dark:text-rose-100">
              [SISTEM GAGAL] LAPORAN {tk} TIDAK BISA DIAMBIL
            </h3>
            <p className="text-xs text-rose-700 leading-relaxed dark:text-rose-300">
              Terjadi kesalahan saat memuat data laporan dari backend. Pastikan server API aktif dan ticker terdaftar.
            </p>
            <Button
              onClick={() => refetch()}
              size="sm"
              variant="outline"
              className="mt-1 h-7 gap-1.5 border-rose-300 bg-white font-mono text-xs text-rose-800 hover:bg-rose-50 dark:border-rose-800 dark:bg-[#121316] dark:text-rose-200 dark:hover:bg-rose-950"
            >
              <RefreshCw className="h-3 w-3" />
              <span>&gt; RETRY FETCH</span>
            </Button>
          </div>
        </div>
      </Card>
    )
  }

  // Offline State (Honest fallback)
  if (data.offline) {
    return (
      <div className="space-y-4 font-mono">
        <Card className="rounded-md border border-amber-300 bg-amber-50/80 p-4 text-xs text-amber-900 dark:border-amber-800/60 dark:bg-amber-950/80 dark:text-amber-100">
          <div className="flex items-start gap-3">
            <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
            <div className="space-y-2">
              <h3 className="font-bold uppercase tracking-wider text-amber-950 dark:text-amber-100">
                [MODE OFFLINE] SERVER BELUM NYAMBUNG // {tk}
              </h3>
              <p className="text-xs leading-relaxed text-amber-800 dark:text-amber-200">{data.summary}</p>
              <Button
                onClick={() => window.location.reload()}
                size="sm"
                className="mt-1 h-7 bg-amber-900 font-mono text-xs text-white hover:bg-amber-800 dark:bg-amber-800 dark:hover:bg-amber-700"
              >
                <RefreshCw className="mr-1 h-3 w-3" />
                <span>&gt; MUAT ULANG</span>
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
  const vd = r.valuationDetail
  const takeaways = r.cover?.rating_box?.key_takeaways ?? []
  const vs = r.cover?.vs_jci
  const rawChart = Array.isArray((r.raw as any)?.chart) ? ((r.raw as any).chart as number[]) : undefined

  return (
    <div className="min-h-screen pb-12">
      {/* 1. Sticky Terminal Header & Key-Stats Strip */}
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

      {/* Terminal Analyst Notice Box */}
      <div className="mb-4 flex items-start gap-2 rounded border border-neutral-300 bg-neutral-50/80 p-2.5 font-mono text-xs leading-relaxed text-neutral-700 dark:border-[#262930] dark:bg-[#121316] dark:text-neutral-300">
        <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" />
        <div>
          <span className="font-bold text-neutral-900 dark:text-neutral-100">[ANALYST GUIDE] </span>
          <span>
            BUY: Analis merekomendasikan akumulasi saham (harga wajar &gt; pasar). HOLD: Pertahankan posisi. SELL: Valuasi telah merefleksikan harga penuh. UPSIDE: Potensi apresiasi harga ke target deterministik.
          </span>
        </div>
      </div>

      {/* 2. Responsive 2-Column Grid Layout */}
      <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-[1fr_320px]">
        {/* Main Center Console */}
        <div className="min-w-0 space-y-4">
          {/* Section 1: Executive Summary */}
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

          {/* Section 2: Valuation Methodology */}
          <ValuationMethodology
            ticker={tk}
            valuation={r.valuation ?? []}
            valuationDetail={vd}
            template={tpl}
            kpis={r.kpis}
            segments={r.segments}
            rawSegments={r.raw?.segments}
            segmentsSource={
              ((r.raw as unknown as Record<string, unknown>)?.["segments_src"] as string | undefined)
            }
            ratios={r.ratios}
            rawBands={r.raw?.bands}
          />

          {/* Section 3: Interactive DCF Sensitivity Model */}
          <section id="sensitivity-analysis" className="space-y-3 scroll-mt-28">
            <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-neutral-200 pb-1.5 dark:border-[#262930]">
              <div className="flex items-center gap-2">
                <span className="rounded bg-neutral-900 px-1.5 py-0.5 font-mono text-[10px] font-bold text-amber-400 dark:bg-amber-400/10 dark:text-amber-400">
                  03
                </span>
                <h2 className="font-mono text-xs font-bold uppercase tracking-wider text-neutral-900 dark:text-neutral-100">
                  {tk} IJ &lt;EQUITY&gt; // INTERACTIVE DCF SENSITIVITY MODEL
                </h2>
              </div>
              <span className="font-mono text-[10px] text-neutral-400">
                WACC &amp; TERMINAL GROWTH DYNAMIC MATRIX
              </span>
            </div>
            <DcfFriend ticker={tk} />
          </section>

          {/* Section 4: Risk Factors & Solvency */}
          <RiskFactors
            ticker={tk}
            template={tpl}
            ratios={r.ratios}
          />

          {/* Section 5: Sources & Compliance */}
          <section id="sources-disclaimer" className="scroll-mt-28 space-y-3 border-t border-neutral-200 pt-4 dark:border-[#262930]">
            <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-neutral-200 pb-1.5 dark:border-[#262930]">
              <div className="flex items-center gap-2">
                <span className="rounded bg-neutral-900 px-1.5 py-0.5 font-mono text-[10px] font-bold text-amber-400 dark:bg-amber-400/10 dark:text-amber-400">
                  05
                </span>
                <h2 className="font-mono text-xs font-bold uppercase tracking-wider text-neutral-900 dark:text-neutral-100">
                  {tk} IJ &lt;EQUITY&gt; // DATA PROVENANCE &amp; OJK REGULATORY COMPLIANCE
                </h2>
              </div>
              <span className="font-mono text-[10px] text-neutral-400">
                RESEARCH ATTESTATION · NOT FINANCIAL ADVICE
              </span>
            </div>

            <div className="rounded-md border border-neutral-300 bg-white p-3 font-mono shadow-none dark:border-[#262930] dark:bg-[#121316]">
              <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider text-neutral-800 dark:text-neutral-200">
                <FileText className="h-3.5 w-3.5 text-amber-500" />
                <span>INFORMASI RISET - BUKAN SARAN INVESTASI (OJK COMPLIANCE)</span>
              </div>
              <p className="mt-1 text-xs leading-relaxed text-neutral-600 dark:text-neutral-400">
                Dokumen ini disusun untuk tujuan analisis riset kompetisi Sectors Hackathon 2026, bukan merupakan rekomendasi jual/beli efek atau saran investasi resmi (kepatuhan regulasi OJK). Seluruh estimasi dan nilai wajar dihitung secara deterministik berdasarkan data historis dan asumsi yang diungkapkan secara transparan tanpa angka buatan.
              </p>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2 px-1 font-mono text-[10px] text-neutral-400">
              <div className="flex items-center gap-1.5">
                <Database className="h-3 w-3" />
                <span>SUMBER: IDX Laporan Keuangan via Sectors API, SKK Migas, Sustainalytics</span>
              </div>
              <div>TanStack Query · Cache 4h · Template {tpl}</div>
            </div>
          </section>
        </div>

        {/* Right Sticky Sidebar */}
        <div className="space-y-3 lg:sticky lg:top-28">
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

