import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { Loader2, AlertCircle, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { fetchReport, fetchSentiment, fetchNews, fetchReportLog } from "@/lib/api"
import { ReportHeader } from "@/components/report/ReportHeader"
import { SentimentStatCards } from "@/components/report/SentimentStatCards"
import { SentimentChart } from "@/components/report/SentimentChart"
import { SentimentNewsList } from "@/components/report/SentimentNewsList"
import { AdkRunCard, type Log, type HistoryItem } from "@/components/report/AdkRunCard"

export const Route = (createFileRoute as any)("/report/$ticker/sentiment")({
  component: SentimentPage,
})

function SentimentPage() {
  const { ticker } = Route.useParams()
  const tk = String(ticker).toUpperCase()

  // Queries
  const reportQuery = useQuery({
    queryKey: ["report", tk],
    queryFn: () => fetchReport(tk),
  })

  const sentimentQuery = useQuery({
    queryKey: ["sentiment", tk],
    queryFn: () => fetchSentiment(tk),
  })

  const newsQuery = useQuery({
    queryKey: ["news", tk],
    queryFn: () => fetchNews(tk, 30),
  })

  const logQuery = useQuery({
    queryKey: ["report-log", tk],
    queryFn: () => fetchReportLog(tk),
  })

  const isLoading = reportQuery.isLoading || sentimentQuery.isLoading
  const reportData = reportQuery.data
  const sentimentData = sentimentQuery.data
  const newsData = newsQuery.data
  const logData = logQuery.data

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="space-y-6">
        <ReportHeader ticker={tk} activeTab="sentiment" />
        <div className="rounded-xl border border-neutral-200 bg-white p-8 text-center shadow-2xs dark:border-neutral-800 dark:bg-[#111111]">
          <div className="flex flex-col items-center justify-center space-y-3">
            <Loader2 className="h-6 w-6 animate-spin text-neutral-700 dark:text-neutral-300" />
            <p className="text-sm font-medium text-neutral-800 dark:text-neutral-200">
              Memuat data sentimen ritel & analisis narasi untuk {tk}...
            </p>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">
              Mengagregasi sinyal sentimen dari Stockbit, X (Twitter), dan media finansial IDX.
            </p>
          </div>
        </div>
      </div>
    )
  }

  // Error State
  if (sentimentQuery.isError && !sentimentData) {
    return (
      <div className="space-y-6">
        <ReportHeader
          ticker={tk}
          activeTab="sentiment"
          companyName={reportData?.name}
          rating={reportData?.rating}
          price={reportData?.price}
          targetPrice={reportData?.target}
          upside={reportData?.upside}
          updatedAt={reportData?.updatedAt}
        />
        <div className="rounded-xl border border-rose-200 bg-rose-50/70 p-6 text-neutral-800 shadow-2xs dark:border-rose-800 dark:bg-rose-950/70 dark:text-neutral-200">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-rose-600 shrink-0 mt-0.5 dark:text-rose-400" />
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-rose-900 dark:text-rose-100">
                Gagal memuat data sentimen untuk {tk}
              </h3>
              <p className="text-xs text-neutral-600 leading-relaxed dark:text-neutral-400">
                Terjadi kendala saat menghubungi modul agregasi sentimen. Anda dapat mencoba memuat ulang atau memeriksa status koneksi backend.
              </p>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  sentimentQuery.refetch()
                  newsQuery.refetch()
                }}
                className="h-8 gap-1.5 text-xs bg-white cursor-pointer dark:bg-[#111111]"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                <span>Coba Lagi</span>
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Offline or Backend unavailable state
  if (reportData?.offline) {
    return (
      <div className="space-y-6">
        <ReportHeader
          ticker={tk}
          activeTab="sentiment"
          companyName={reportData.name}
          updatedAt={reportData.updatedAt}
        />
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900 shadow-2xs dark:border-amber-800 dark:bg-amber-950 dark:text-amber-100">
          <div className="font-semibold mb-1">Peringatan: Backend Offline</div>
          <p className="text-xs leading-relaxed text-amber-800 dark:text-amber-200">
            {reportData.summary}
          </p>
          <Button
            size="sm"
            onClick={() => window.location.reload()}
            className="mt-3 bg-amber-900 text-white hover:bg-amber-800 text-xs"
          >
            Muat Ulang Halaman
          </Button>
        </div>
      </div>
    )
  }

  // Prepare news articles and social items
  const articles = newsData?.data || []
  const socialItems = sentimentData?.items || []

  return (
    <div className="space-y-6 pb-12">
      {/* Shared Report Header */}
      <ReportHeader
        ticker={tk}
        activeTab="sentiment"
        companyName={reportData?.name}
        rating={reportData?.rating}
        price={reportData?.price}
        targetPrice={reportData?.target}
        upside={reportData?.upside}
        updatedAt={reportData?.updatedAt}
        source={reportData?.source}
      />

      {/* Panduan pemula: rating + upside dalam 2 kalimat */}
      <div className="rounded-md border border-neutral-200 border-l-2 border-l-[#0070f3] bg-white p-3 text-xs leading-relaxed text-neutral-600 dark:border-neutral-800 dark:bg-[#111111] dark:text-neutral-400">
        <span className="font-semibold text-[#0a0a0a] dark:text-white">Baru mulai baca sentimen saham? </span>
        BUY artinya analis menilai saham ini layak dibeli, HOLD artinya ditahan dulu, SELL artinya
        sebaiknya dihindari. Upside = potensi kenaikan harga ke harga wajar — halaman ini nunjukkin
        apakah omongan pasar (berita & medsos) sejalan atau malah beda arah sama penilaian analis.
      </div>

      {/* Intro Description */}
      <div className="space-y-1">
        <h2 className="text-base font-bold tracking-tight text-neutral-900 dark:text-neutral-100">
          Kata Orang Tentang Saham Ini ({tk})
        </h2>
        <p className="text-xs leading-relaxed text-neutral-600 max-w-3xl dark:text-neutral-400">
          Pemantauan opini ritel publik secara real-time yang memetakan optimisme vs pesimisme pasar di media sosial (Stockbit, X) dan pemberitaan pers IDX. Berguna untuk mengidentifikasi potensi divergensi antara valuasi fundamental institusional dan ekspektasi harga ritel.
        </p>
      </div>

      {/* Top Stat Cards */}
      <SentimentStatCards
        ticker={tk}
        sentiment={sentimentData}
        newsCount={articles.length}
        socialCount={socialItems.length}
      />

      {/* Visual Sentiment Chart & Narrative Dial */}
      <SentimentChart
        ticker={tk}
        sentiment={sentimentData}
        isLoading={sentimentQuery.isLoading}
      />

      {/* News & Social Feed */}
      <SentimentNewsList
        ticker={tk}
        articles={articles}
        socialItems={socialItems}
        isLoading={newsQuery.isLoading}
      />

      {/* ADK Run Card - Accessible directly from sentiment sub-route */}
      {logData ? (
        <div className="space-y-2 pt-2">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-600 dark:text-neutral-400">
            Riwayat Analisis AI Agent ({tk})
          </h3>
          <AdkRunCard
            ticker={tk}
            log={logData.log as Log}
            history={(logData.history || []) as HistoryItem[]}
            hasRun={logData.has_run}
          />
        </div>
      ) : null}

      {/* Shared Footer Disclaimer */}
      <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-4 text-xs text-neutral-500 shadow-2xs dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-400">
        <div className="font-semibold uppercase tracking-wider text-neutral-700 dark:text-neutral-300">
          INFORMASI, BUKAN SARAN INVESTASI
        </div>
        <p className="mt-1 leading-relaxed text-[11px] text-neutral-600 dark:text-neutral-400">
          Dokumen ini disusun untuk tujuan analisis riset kompetisi Sectors Hackathon 2026, bukan merupakan rekomendasi jual atau beli efek, maupun saran investasi profesional (kepatuhan regulasi OJK). Data sentimen bersumber dari publikasi pihak ketiga yang diagregasikan secara otomatis.
        </p>
      </div>
    </div>
  )
}
