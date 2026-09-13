import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import {
  AlertTriangle,
  RefreshCw,
  ShieldAlert,
  FileText,
  Database,
  Info,
  Layers,
  ChevronRight,
  Compass,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
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
        <div className="rounded border border-[#D6E2EE] bg-[#F4F8FC] p-3 text-center text-xs text-[#0B1F3A] dark:border-[#262930] dark:bg-[#121316] dark:text-[#A9C9E8]">
          [MEMUAT] MENYIAPKAN LAPORAN INSTITUSIONAL LENGKAP {tk}…
        </div>
        <div className="h-16 animate-pulse rounded border border-[#D6E2EE] bg-[#E4EEF7]/40 dark:border-[#262930] dark:bg-[#181a1f]" />
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_320px]">
          <div className="space-y-4">
            <div className="h-48 animate-pulse rounded border border-[#D6E2EE] bg-[#E4EEF7]/40 dark:border-[#262930] dark:bg-[#181a1f]" />
            <div className="h-64 animate-pulse rounded border border-[#D6E2EE] bg-[#E4EEF7]/40 dark:border-[#262930] dark:bg-[#181a1f]" />
          </div>
          <div className="h-80 animate-pulse rounded border border-[#D6E2EE] bg-[#E4EEF7]/40 dark:border-[#262930] dark:bg-[#181a1f]" />
        </div>
      </div>
    )
  }

  // Error State (Network failure / unhandled)
  if (error || !data) {
    return (
      <Card className="rounded-md border border-[#C0392B]/40 bg-[#C0392B]/10 p-4 font-mono dark:border-[#C0392B]/60 dark:bg-[#C0392B]/20">
        <div className="flex items-start gap-3">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[#C0392B]" />
          <div className="space-y-2">
            <h3 className="text-xs font-bold uppercase text-[#C0392B]">
              [SISTEM GAGAL] LAPORAN {tk} TIDAK BISA DIAMBIL
            </h3>
            <p className="text-xs text-[#63748A] leading-relaxed dark:text-neutral-300">
              Terjadi kesalahan saat memuat data laporan dari backend. Pastikan server API aktif.
            </p>
            <Button
              onClick={() => refetch()}
              size="sm"
              variant="outline"
              className="mt-1 h-7 gap-1.5 border-[#C0392B]/40 bg-white font-mono text-xs text-[#C0392B] hover:bg-[#C0392B]/10 dark:border-[#C0392B]/60 dark:bg-[#121316] dark:text-[#F87171]"
            >
              <RefreshCw className="h-3 w-3" />
              <span>&gt; COBA LAGI</span>
            </Button>
          </div>
        </div>
      </Card>
    )
  }

  // 422 Honest State: Ticker not covered / verified assumptions missing
  if (data.is422) {
    return (
      <div className="min-h-screen pb-12 space-y-4">
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

        <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-[1fr_320px]">
          {/* Main Console: Honest Uncovered State */}
          <div className="space-y-4 font-mono">
            <Card className="rounded-lg border border-[#D6E2EE] bg-[#F4F8FC] p-5 dark:border-[#262930] dark:bg-[#121418]">
              <div className="flex items-start gap-3.5">
                <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-[#0B1F3A] dark:text-[#A9C9E8]" />
                <div className="space-y-3">
                  <div>
                    <span className="rounded bg-[#0B1F3A] px-2 py-0.5 text-[10px] font-bold uppercase text-white dark:bg-[#A9C9E8] dark:text-[#0B1F3A]">
                      STATUS JUJUR: EMITEN BELUM DICOVER
                    </span>
                    <h3 className="mt-2 text-sm font-bold text-[#0B1F3A] dark:text-neutral-100">
                      Asumsi Valuasi Belum Tersedia untuk {tk} (HTTP 422)
                    </h3>
                  </div>

                  <p className="text-xs leading-relaxed text-[#0B1F3A] dark:text-neutral-300">
                    {data.summary}
                  </p>

                  {data.missing && data.missing.length > 0 && (
                    <div className="space-y-1.5 border-t border-[#D6E2EE] pt-3 dark:border-[#262930]">
                      <div className="text-[10px] font-bold uppercase tracking-wider text-[#63748A]">
                        Daftar Parameter yang Belum Terverifikasi ({data.missing.length}):
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {data.missing.map((param) => (
                          <span
                            key={param}
                            className="rounded border border-[#D6E2EE] bg-white px-2 py-0.5 text-[10px] font-semibold text-[#0B1F3A] dark:border-[#262930] dark:bg-[#181a1f] dark:text-neutral-300"
                          >
                            {param}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="rounded border-l-2 border-[#0B1F3A] bg-white p-3 text-xs text-[#63748A] leading-relaxed dark:border-[#A9C9E8] dark:bg-[#181a1f] dark:text-neutral-300 font-sans">
                    <strong>Kebijakan Non-Fabrikasi:</strong> Seluruh output mesin riset wajib bersumber
                    dari data terverifikasi. Sistem menolak membuat angka tiruan atau nilai pengganti ketika
                    asumsi dasar emiten belum tersedia.
                  </div>

                  <div className="pt-1">
                    <Button
                      onClick={() => refetch()}
                      size="sm"
                      variant="outline"
                      className="h-8 gap-1.5 border-[#D6E2EE] bg-white text-xs font-mono text-[#0B1F3A] hover:bg-[#E4EEF7] dark:border-[#262930] dark:bg-[#181a1f] dark:text-neutral-200"
                    >
                      <RefreshCw className="h-3 w-3" />
                      <span>&gt; MUAT ULANG DATA</span>
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Right Sidebar */}
          <div className="space-y-3 lg:sticky lg:top-28">
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
    )
  }

  // Offline State
  if (data.offline) {
    return (
      <div className="space-y-4 font-mono">
        <Card className="rounded-md border border-[#D6E2EE] bg-[#F4F8FC] p-4 text-xs text-[#0B1F3A] dark:border-[#262930] dark:bg-[#121316] dark:text-neutral-200">
          <div className="flex items-start gap-3">
            <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-[#0B1F3A] dark:text-[#A9C9E8]" />
            <div className="space-y-2">
              <h3 className="font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-[#A9C9E8]">
                [MODE OFFLINE] SERVER BACKEND BELUM TERSEDIA // {tk}
              </h3>
              <p className="text-xs leading-relaxed text-[#63748A] dark:text-neutral-300">{data.summary}</p>
              <Button
                onClick={() => window.location.reload()}
                size="sm"
                className="mt-1 h-7 bg-[#0B1F3A] font-mono text-xs text-white hover:bg-[#14304F] dark:bg-[#A9C9E8] dark:text-[#0B1F3A]"
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
    <div className="min-h-screen pb-12">
      {/* Sticky Header & Key-Stats Strip */}
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

      {/* Terminal Analyst Notice Box */}
      <div className="mb-4 flex items-start gap-2 rounded border border-[#D6E2EE] bg-[#F4F8FC] p-2.5 font-mono text-xs leading-relaxed text-[#0B1F3A] dark:border-[#262930] dark:bg-[#121316] dark:text-neutral-300">
        <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#0B1F3A] dark:text-[#A9C9E8]" />
        <div>
          <span className="font-bold text-[#0B1F3A] dark:text-[#A9C9E8]">[STANDAR RISET INSTITUSIONAL] </span>
          <span>
            Seluruh data disusun deterministik dalam 10 bab berurutan mengikuti format dokumen PDF resmi. Market terms: BUY/HOLD/SELL, DCF, WACC, EV/EBITDA, PER, PBV.
          </span>
        </div>
      </div>

      {/* 2-Column Responsive Layout */}
      <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-[1fr_320px]">
        {/* Main Content Area: 10 Sections in Exact PDF Order */}
        <div className="min-w-0 space-y-6">
          {/* ================================================================= */}
          {/* 1. Cover & Rating & Investment Thesis (Bab 1)                      */}
          {/* 2. Key Financials (Bab 2)                                         */}
          {/* ================================================================= */}
          <ExecutiveSummary ticker={tk} payload={payload} />

          {/* ================================================================= */}
          {/* 3. Performance: The Four Quadrants (Bab 3)                        */}
          {/* ================================================================= */}
          <section id="performance-quadrants" className="space-y-3 scroll-mt-28">
            <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-[#D6E2EE] pb-2 dark:border-[#262930]">
              <div className="flex items-center gap-2">
                <span className="rounded bg-[#0B1F3A] px-1.5 py-0.5 font-mono text-[10px] font-bold text-[#E4EEF7] dark:bg-[#0B1F3A] dark:text-[#A9C9E8]">
                  03
                </span>
                <h2 className="font-sans text-sm font-bold tracking-tight text-[#0B1F3A] dark:text-neutral-100 uppercase">
                  {payload.performance_page?.title || "Visualisasi Kinerja Keuangan dan Forecasting"} // {tk}
                </h2>
              </div>
              <span className="font-mono text-[11px] text-[#63748A]">
                4 Kuadran Combo Chart
              </span>
            </div>

            {payload.performance_page?.subtitle && (
              <p className="text-xs text-[#63748A] leading-relaxed">
                {payload.performance_page.subtitle}
              </p>
            )}

            {/* Lane B Frozen Chart Import */}
            <PerformanceQuadrants payload={payload} />

            {payload.performance_page?.sources && payload.performance_page.sources.length > 0 && (
              <p className="font-mono text-[10px] text-[#63748A]">
                Basis data: {payload.performance_page.sources.join("; ")}
              </p>
            )}
          </section>

          {/* ================================================================= */}
          {/* 4. Valuation Spread (DCF) (Bab 4)                                 */}
          {/* 5. Peers 5A (Bab 5)                                               */}
          {/* 6. Own History 5B (Bab 6)                                         */}
          {/* ================================================================= */}
          <ValuationMethodology ticker={tk} payload={payload} />

          {/* ================================================================= */}
          {/* 7. Statements (Bab 7)                                             */}
          {/* 8. Cash Flow & Ratios (Bab 8)                                     */}
          {/* 9. Risks (Bab 9)                                                  */}
          {/* 10. Sources & Disclaimer (Bab 10)                                 */}
          {/* ================================================================= */}
          <RiskFactors ticker={tk} payload={payload} />
        </div>

        {/* Right Sticky Sidebar */}
        <div className="space-y-3 lg:sticky lg:top-28">
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

          {/* 10-Section Navigation Quick Jump Card */}
          <Card className="rounded-lg border border-[#D6E2EE] bg-white shadow-xs dark:border-[#262930] dark:bg-[#121418]">
            <CardHeader className="border-b border-[#D6E2EE] bg-[#F4F8FC] p-3.5 pb-2.5 dark:border-[#1f2228] dark:bg-[#181a1f]/70">
              <div className="flex items-center gap-2">
                <Compass className="h-3.5 w-3.5 text-[#0B1F3A] dark:text-[#A9C9E8]" />
                <CardTitle className="text-[11px] font-sans font-bold uppercase tracking-wider text-[#0B1F3A] dark:text-[#A9C9E8]">
                  Daftar 10 Bab Laporan
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent className="p-3.5 pt-2 font-mono">
              <nav className="space-y-1 text-xs font-sans">
                {[
                  { href: "#cover-rating", num: "01", label: "Cover & Rating" },
                  { href: "#key-financials", num: "02", label: "Key Financials" },
                  { href: "#performance-quadrants", num: "03", label: "Performance Quadrants" },
                  { href: "#valuation-spread", num: "04", label: "Valuasi DCF Spread" },
                  { href: "#peers-5a", num: "05", label: "Peers 5A (Cross-Sectional)" },
                  { href: "#peers-5b", num: "06", label: "Own History 5B" },
                  { href: "#financial-statements", num: "07", label: "Laporan Keuangan" },
                  { href: "#cashflow-ratios", num: "08", label: "Arus Kas & Rasio" },
                  { href: "#risk-factors", num: "09", label: "Faktor Risiko" },
                  { href: "#sources-disclaimer", num: "10", label: "Sumber & Disklaimer" },
                ].map((item) => (
                  <a
                    key={item.num}
                    href={item.href}
                    className="flex items-center justify-between rounded-md px-2.5 py-1 text-[#0B1F3A] hover:bg-[#E4EEF7] transition-colors dark:text-neutral-300 dark:hover:bg-[#181a1f] dark:hover:text-neutral-100"
                  >
                    <span className="truncate">
                      <strong className="font-mono text-[#63748A] mr-1.5">{item.num}.</strong>
                      {item.label}
                    </span>
                    <ChevronRight className="h-3 w-3 text-[#63748A] shrink-0" />
                  </a>
                ))}
              </nav>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
