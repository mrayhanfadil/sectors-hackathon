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
      <div className="space-y-4">
        <ReportHeader ticker={tk} activeTab="sentiment" />
        <div className="border border-neutral-300 bg-white p-8 text-center font-mono text-xs dark:border-[#262930] dark:bg-[#121316]">
          <div className="flex flex-col items-center justify-center space-y-2">
            <Loader2 className="h-5 w-5 animate-spin text-amber-600 dark:text-amber-400" />
            <p className="font-semibold text-neutral-800 dark:text-neutral-200">
              TERMINAL :: MEMUAT SENTIMEN RITEL &amp; ANALISIS NARASI {tk}...
            </p>
            <p className="text-[11px] text-neutral-500 dark:text-neutral-400">
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
      <div className="space-y-4">
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
        <div className="border border-rose-300 bg-rose-50/70 p-4 font-mono text-xs text-neutral-800 dark:border-rose-800 dark:bg-rose-950/70 dark:text-neutral-200">
          <div className="flex items-start gap-2.5">
            <AlertCircle className="h-4 w-4 text-rose-600 shrink-0 mt-0.5 dark:text-rose-400" />
            <div className="space-y-2">
              <h3 className="font-semibold text-rose-900 dark:text-rose-200">
                GALAT :: GAGAL MEMUAT DATA SENTIMEN UNTUK {tk}
              </h3>
              <p className="font-sans text-xs text-neutral-700 dark:text-neutral-300">
                Terjadi kendala saat menghubungi modul agregasi sentimen backend.
              </p>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  sentimentQuery.refetch()
                  newsQuery.refetch()
                }}
                className="h-7 gap-1.5 rounded-none border border-neutral-300 bg-white font-mono text-[11px] cursor-pointer dark:border-[#262930] dark:bg-[#121316]"
              >
                <RefreshCw className="h-3 w-3" />
                <span>[RETRY] COBA LAGI</span>
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
      <div className="space-y-4">
        <ReportHeader
          ticker={tk}
          activeTab="sentiment"
          companyName={reportData.name}
          updatedAt={reportData.updatedAt}
        />
        <div className="border border-amber-300 bg-amber-50 p-4 font-mono text-xs text-amber-900 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-100">
          <div className="font-bold mb-1">[WARNING] BACKEND OFFLINE</div>
          <p className="font-sans text-xs leading-relaxed text-amber-800 dark:text-amber-200">
            {reportData.summary}
          </p>
          <Button
            size="sm"
            onClick={() => window.location.reload()}
            className="mt-3 h-7 rounded-none bg-amber-900 text-white hover:bg-amber-800 font-mono text-[11px]"
          >
            [F5] MUAT ULANG
          </Button>
        </div>
      </div>
    )
  }

  // Prepare news articles and social items
  const articles = newsData?.data || []
  const socialItems = sentimentData?.items || []

  return (
    <div className="space-y-4 pb-12">
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

      {/* Terminal Section Header */}
      <div className="border-l-2 border-l-amber-500 border border-neutral-300 bg-neutral-900/[0.02] px-3 py-2 text-[10px] font-mono font-semibold uppercase tracking-wider text-neutral-600 dark:border-[#262930] dark:bg-[#15171c] dark:text-neutral-300">
        // 02. SENTIMENT HARVESTER &amp; SOCIAL DIAL // {tk} IJ &lt;EQUITY&gt; SENT
      </div>

      {/* Analyst notice banner */}
      <div className="border border-neutral-300 bg-white p-3 font-mono text-[11px] leading-relaxed text-neutral-600 dark:border-[#262930] dark:bg-[#121316] dark:text-neutral-300">
        <span className="font-bold text-amber-600 dark:text-amber-400">PROMPT :: ANALYST NOTICE &gt; </span>
        <span className="font-sans text-xs">
          Pemantauan opini ritel memetakan konsensus pasar di media sosial (Stockbit, X) dan pemberitaan pers IDX. Berguna untuk mendeteksi divergensi antara model valuasi fundamental institusional dan ekspektasi harga ritel jangka pendek.
        </span>
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
          <div className="border-l-2 border-l-cyan-500 border border-neutral-300 bg-neutral-900/[0.02] px-3 py-1.5 text-[10px] font-mono font-semibold uppercase tracking-wider text-neutral-600 dark:border-[#262930] dark:bg-[#15171c] dark:text-neutral-300">
            // AI AGENT REASONING AUDIT // TRACE LOG ({tk})
          </div>
          <AdkRunCard
            ticker={tk}
            log={logData.log as Log}
            history={(logData.history || []) as HistoryItem[]}
            hasRun={logData.has_run}
          />
        </div>
      ) : null}

      {/* Shared Footer Disclaimer */}
      <div className="border border-neutral-300 bg-neutral-50/70 p-3 font-mono text-[10px] text-neutral-500 dark:border-[#262930] dark:bg-[#15171c] dark:text-neutral-400">
        <div className="font-bold uppercase tracking-wider text-neutral-700 dark:text-neutral-300">
          // 05. DATA PROVENANCE &amp; OJK COMPLIANCE //
        </div>
        <p className="mt-1 font-sans text-[11px] leading-relaxed text-neutral-600 dark:text-neutral-400">
          Dokumen ini disusun untuk tujuan analisis riset kompetisi Sectors Hackathon 2026, bukan merupakan rekomendasi jual atau beli efek, maupun saran investasi profesional (kepatuhan regulasi OJK). Data sentimen bersumber dari agregasi publikasi pihak ketiga tanpa rekayasa bobot.
        </p>
      </div>
    </div>
  )
}
