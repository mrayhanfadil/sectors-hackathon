import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import {
  AlertTriangle,
  RefreshCw,
  ShieldAlert,
  Info,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { fetchReportPayload, fetchPdf } from "@/lib/api"
import { type Log, type HistoryItem } from "@/components/report/AdkRunCard"
import { ReportHeader } from "@/components/report/ReportHeader"
import { ExecutiveSummary } from "@/components/report/ExecutiveSummary"
import { ValuationMethodology } from "@/components/report/ValuationMethodology"
import { RiskFactors } from "@/components/report/RiskFactors"
import { ADKRunSidebar } from "@/components/report/ADKRunSidebar"
import { PerformanceQuadrants } from "@/components/report/charts"
import type { FullReportPayload } from "@/lib/reportTypes"

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
    queryKey: ["report-payload", tk],
    queryFn: () => fetchReportPayload(tk),
  })

  const logQuery = useQuery({
    queryKey: ["report-log", tk],
    queryFn: () => fetchReportLog(tk),
  })

  useEffect(() => {
    document.title = `${tk} · Sektoral`
    return () => {
      document.title = "Sektoral · Laporan Saham"
    }
  }, [tk])

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
        setPdfMsg("Dokumen PDF belum tersedia di server backend.")
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
      <div className="mx-auto max-w-[1100px] px-4 py-8 space-y-6">
        <div className="rounded-xl border border-[#E7E3DA] bg-white p-6 text-center text-sm text-[#6B6659] dark:border-[#2A2822] dark:bg-[#1B1A16] dark:text-[#A8A296]">
          Menyiapkan laporan analisis lengkap {tk}…
        </div>
        <div className="h-16 animate-pulse rounded-xl border border-[#E7E3DA] bg-[#F4F1EA]/60 dark:border-[#2A2822] dark:bg-[#1B1A16]" />
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
          <div className="space-y-6">
            <div className="h-56 animate-pulse rounded-xl border border-[#E7E3DA] bg-[#F4F1EA]/60 dark:border-[#2A2822] dark:bg-[#1B1A16]" />
            <div className="h-72 animate-pulse rounded-xl border border-[#E7E3DA] bg-[#F4F1EA]/60 dark:border-[#2A2822] dark:bg-[#1B1A16]" />
          </div>
          <div className="h-96 animate-pulse rounded-xl border border-[#E7E3DA] bg-[#F4F1EA]/60 dark:border-[#2A2822] dark:bg-[#1B1A16]" />
        </div>
      </div>
    )
  }

  // Error State (Network failure / unhandled)
  if (error || !data) {
    return (
      <div className="mx-auto max-w-[1100px] px-4 py-8">
        <Card className="rounded-xl border border-[#F8C8CB] bg-[#FDF2F2] p-6 dark:border-[#B4232A]/40 dark:bg-[#B4232A]/20">
          <div className="flex items-start gap-3.5">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-[#B4232A] dark:text-[#F87171]" />
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-[#B4232A] dark:text-[#F87171]">
                Laporan {tk} tidak dapat dimuat
              </h3>
              <p className="text-xs text-[#6B6659] leading-relaxed dark:text-[#A8A296]">
                Terjadi kesalahan saat memuat data laporan dari server backend. Pastikan koneksi dan server aktif.
              </p>
              <Button
                onClick={() => refetch()}
                size="sm"
                variant="outline"
                className="h-8 gap-1.5 border-[#F8C8CB] bg-white text-xs font-medium text-[#B4232A] hover:bg-[#FDF2F2] dark:border-[#B4232A]/40 dark:bg-[#1B1A16] dark:text-[#F87171] cursor-pointer"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                <span>Coba lagi</span>
              </Button>
            </div>
          </div>
        </Card>
      </div>
    )
  }

  // 422 Honest State: Ticker not covered / verified assumptions missing
  if (data.is422) {
    return (
      <div className="min-h-screen pb-12">
        <ReportHeader
          ticker={tk}
          rating={null}
          price={null}
          target={null}
          upside={null}
          updatedAt={null}
          template="unknown"
          source="assumptions_gate"
          activeTab="valuation"
          onDownloadPdf={onDownloadPdf}
          pdfState={pdfState}
          pdfMsg={pdfMsg}
        />

        <div className="mx-auto max-w-[1100px] px-4">
          <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-[1fr_320px]">
            {/* Honest Uncovered State */}
            <div className="space-y-6">
              <Card className="rounded-xl border border-[#E7E3DA] bg-white p-6 space-y-4 dark:border-[#2A2822] dark:bg-[#1B1A16]">
                <div className="flex items-start gap-3.5">
                  <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-[#0E6E63] dark:text-[#4FD1B5]" />
                  <div className="space-y-3 flex-1">
                    <div>
                      <span className="inline-block rounded-md bg-[#F4F1EA] px-2.5 py-0.5 text-xs font-semibold text-[#1C1B17] dark:bg-[#2A2822] dark:text-[#EDEAE3]">
                        Belum Tersedia
                      </span>
                      <h3 className="font-serif text-lg font-medium text-[#1C1B17] mt-2 dark:text-[#EDEAE3]">
                        Asumsi valuasi belum tersedia untuk {tk}
                      </h3>
                    </div>

                    <p className="text-xs leading-relaxed text-[#6B6659] dark:text-[#A8A296]">
                      {data.summary}
                    </p>

                    {data.missing && data.missing.length > 0 && (
                      <div className="space-y-2 border-t border-[#E7E3DA] pt-3 dark:border-[#2A2822]">
                        <div className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                          Daftar parameter yang Belum Terverifikasi ({data.missing.length}):
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {data.missing.map((param) => (
                            <span
                              key={param}
                              className="rounded-md border border-[#E7E3DA] bg-[#FBFAF7] px-2 py-0.5 text-xs text-[#1C1B17] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#EDEAE3]"
                            >
                              {param}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="rounded-lg border border-[#E7E3DA] bg-[#FBFAF7] p-3.5 text-xs text-[#6B6659] leading-relaxed dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
                      <strong>Kebijakan integritas data:</strong> Seluruh output model riset wajib bersumber
                      dari data terverifikasi. Sistem menolak membuat angka tiruan ketika asumsi dasar emiten belum tersedia.
                    </div>

                    <div className="pt-2">
                      <Button
                        onClick={() => refetch()}
                        size="sm"
                        variant="outline"
                        className="h-8 gap-1.5 rounded-lg border-[#E7E3DA] bg-white text-xs font-medium text-[#1C1B17] hover:bg-[#F4F1EA] dark:border-[#2A2822] dark:bg-[#1B1A16] dark:text-[#EDEAE3] cursor-pointer"
                      >
                        <RefreshCw className="h-3.5 w-3.5" />
                        <span>Muat ulang data</span>
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            </div>

            {/* Right Sidebar */}
            <div className="space-y-4 lg:sticky lg:top-24">
              <ADKRunSidebar
                ticker={tk}
                price={null}
                target={null}
                upside={null}
                rating={null}
                template="unknown"
                logLoading={logQuery.isLoading}
                logData={logQuery.data}
              />
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Offline State
  if (data.offline) {
    return (
      <div className="mx-auto max-w-[1100px] px-4 py-8">
        <Card className="rounded-xl border border-[#F6E3B8] bg-[#FEF9EE] p-6 text-xs text-[#A16207] dark:border-[#A16207]/40 dark:bg-[#A16207]/20 dark:text-[#FBBF24]">
          <div className="flex items-start gap-3.5">
            <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-[#A16207] dark:text-[#FBBF24]" />
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-[#A16207] dark:text-[#FBBF24]">
                Mode offline - server backend belum tersedia untuk {tk}
              </h3>
              <p className="text-xs leading-relaxed text-[#6B6659] dark:text-[#A8A296]">{data.summary}</p>
              <Button
                onClick={() => window.location.reload()}
                size="sm"
                className="h-8 rounded-lg bg-[#0E6E63] text-xs font-medium text-white hover:bg-[#0B5B52] dark:bg-[#4FD1B5] dark:text-[#14130F] cursor-pointer"
              >
                <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
                <span>Muat ulang</span>
              </Button>
            </div>
          </div>
        </Card>
      </div>
    )
  }

  const payload: FullReportPayload = data.payload || {}
  const meta = payload.meta
  const ratingBox = payload.cover?.rating_box
  const tpl = meta?.template || (ratingBox ? "single" : "unknown")
  const price = ratingBox?.price
  const target = ratingBox?.tp
  const upside = ratingBox?.upside_pct != null
    ? `${ratingBox.upside_pct > 0 ? "+" : ""}${ratingBox.upside_pct.toFixed(1)}%`
    : null
  const rating = ratingBox?.action || null

  return (
    <div className="min-h-screen pb-16">
      {/* Sticky Header */}
      <ReportHeader
        ticker={tk}
        name={meta?.company_name}
        price={price}
        target={target}
        upside={upside}
        rating={rating}
        updatedAt={meta?.date}
        template={tpl}
        source={meta?.prepared_by}
        activeTab="valuation"
        onDownloadPdf={onDownloadPdf}
        pdfState={pdfState}
        pdfMsg={pdfMsg}
      />

      <div className="mx-auto max-w-[1100px] px-4 space-y-6">
        {/* Analyst Notice Box */}
        <div className="flex items-start gap-3 rounded-xl border border-[#E7E3DA] bg-white p-4 text-xs leading-relaxed text-[#6B6659] dark:border-[#2A2822] dark:bg-[#1B1A16] dark:text-[#A8A296]">
          <Info className="mt-0.5 h-4 w-4 shrink-0 text-[#0E6E63] dark:text-[#4FD1B5]" />
          <div>
            <span className="font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">Standar riset institusional: </span>
            <span>
              Seluruh angka berasal dari data berlisensi dan dihitung deterministik. Istilah pasar dipertahankan dalam
              bentuk aslinya: BUY/HOLD/SELL, DCF, WACC, EV/EBITDA, PER, PBV.
            </span>
          </div>
        </div>

        {/* 2-Column Responsive Layout */}
        <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-[1fr_320px]">
          {/* Main Content Area: Sections */}
          <div className="min-w-0 space-y-8">
            {/* 1. Cover & Rating, 2. Key Financials */}
            <ExecutiveSummary ticker={tk} payload={payload} />

            {/* 3. Performance: The Four Quadrants */}
            <section id="performance-quadrants" className="space-y-4 scroll-mt-28">
              <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#E7E3DA] pb-2 dark:border-[#2A2822]">
                <h2 className="font-serif text-xl font-medium tracking-tight text-[#1C1B17] dark:text-[#EDEAE3]">
                  {payload.performance_page?.title || "Visualisasi kinerja keuangan dan proyeksi"}
                </h2>
                <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
                  4 Kuadran kinerja
                </span>
              </div>

              {payload.performance_page?.subtitle && (
                <p className="text-sm text-[#6B6659] leading-relaxed dark:text-[#A8A296]">
                  {payload.performance_page.subtitle}
                </p>
              )}

              {/* Performance Quadrants Chart */}
              <PerformanceQuadrants payload={payload} />

              {payload.performance_page?.sources && payload.performance_page.sources.length > 0 && (
                <p className="text-xs text-[#6B6659] dark:text-[#A8A296]">
                  Basis data: {payload.performance_page.sources.join("; ")}
                </p>
              )}
            </section>

            {/* 4. Valuation Spread (DCF), 5. Peers 5A, 6. Own History 5B */}
            <ValuationMethodology ticker={tk} payload={payload} />

            {/* 7. Statements, 8. Cash Flow & Ratios, 9. Risks, 10. Sources & Disclaimer */}
            <RiskFactors ticker={tk} payload={payload} />
          </div>

          {/* Right Sticky Sidebar */}
          <div className="space-y-4 lg:sticky lg:top-24">
            <ADKRunSidebar
              ticker={tk}
              name={meta?.company_name}
              price={price}
              target={target}
              upside={upside}
              rating={rating}
              template={tpl}
              shares={
                payload.cover?.shares?.outstanding != null && payload.cover.shares.unit != null
                  ? {
                      outstanding: payload.cover.shares.outstanding,
                      unit: payload.cover.shares.unit,
                      free_float_pct: payload.cover.shares.free_float_pct ?? undefined,
                    }
                  : undefined
              }
              provenance={payload.valuation_page?.sources?.[0]}
              logLoading={logQuery.isLoading}
              logData={logQuery.data}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
