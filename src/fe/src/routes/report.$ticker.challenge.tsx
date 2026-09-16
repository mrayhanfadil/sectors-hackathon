import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import * as React from "react"
import { Loader2, RefreshCw, AlertTriangle, ShieldCheck } from "lucide-react"
import { Button } from "@/components/ui/button"
import { fetchReport, fetchReportLog } from "@/lib/api"
import { ReportHeader } from "@/components/report/ReportHeader"
import { ChallengeForm } from "@/components/report/ChallengeForm"
import { ChallengeHistoryList, type ChallengeEntry } from "@/components/report/ChallengeHistoryList"
import { AdkRunCard, type Log, type HistoryItem } from "@/components/report/AdkRunCard"

export const Route = (createFileRoute as any)("/report/$ticker/challenge")({
  component: ChallengePage,
})

const SEED_CHALLENGES: Record<string, ChallengeEntry[]> = {}

function getInitialLog(tk: string): ChallengeEntry[] {
  try {
    const saved = localStorage.getItem(`challenge_log_${tk}`)
    if (saved) {
      const parsed = JSON.parse(saved)
      if (Array.isArray(parsed) && parsed.length > 0) return parsed
    }
  } catch {
    // localStorage not available or error parsing
  }
  return SEED_CHALLENGES[tk] || []
}

function ChallengePage() {
  const { ticker } = Route.useParams()
  const tk = String(ticker).toUpperCase()

  const [log, setLog] = React.useState<ChallengeEntry[]>(() => getInitialLog(tk))
  const [loading, setLoading] = React.useState(false)
  const [submitError, setSubmitError] = React.useState<string | null>(null)

  // Save to local storage whenever log changes
  React.useEffect(() => {
    try {
      localStorage.setItem(`challenge_log_${tk}`, JSON.stringify(log))
    } catch {
      // ignore
    }
  }, [log, tk])

  React.useEffect(() => {
    document.title = `Uji silang ${tk} · Sektoral`
    return () => {
      document.title = "Sektoral · Laporan Saham"
    }
  }, [tk])

  // Queries
  const reportQuery = useQuery({
    queryKey: ["report", tk],
    queryFn: () => fetchReport(tk),
  })

  const logQuery = useQuery({
    queryKey: ["report-log", tk],
    queryFn: () => fetchReportLog(tk),
  })

  const reportData = reportQuery.data
  const logData = logQuery.data

  async function handleSubmitChallenge(questionText: string) {
    if (!questionText.trim() || loading) return

    setLoading(true)
    setSubmitError(null)

    try {
      const apiBase = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") || ""
      const path = "/api/challenge"
      const url = apiBase ? `${apiBase}${path}` : path

      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker: tk,
          question: questionText,
          claim: questionText,
        }),
      })

      if (!res.ok) {
        const text = await res.text().catch(() => "")
        let detail = `Permintaan gagal (${res.status})`
        try {
          const j = JSON.parse(text)
          detail = j.detail || j.error || j.message || detail
        } catch {
          if (text) detail = text
        }
        throw new Error(detail)
      }

      const data = await res.json()
      if (data.error) {
        setLog((prev) => [
          {
            q: questionText,
            error: String(data.error),
            debate_id: data.debate_id,
          },
          ...prev,
        ])
      } else {
        setLog((prev) => [
          {
            q: questionText,
            verdict: data.verdict || "defend",
            evidence: data.evidence || "Model mempertahankan asumsi berdasarkan konsistensi laporan audited.",
            exhibit_ref: data.exhibit_ref || "Sensitivity & DCF Audit",
            correction: data.correction,
            debate_id: data.debate_id,
          },
          ...prev,
        ])
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setSubmitError(msg)
      setLog((prev) => [
        {
          q: questionText,
          error: msg,
        },
        ...prev,
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleClearHistory = () => {
    setLog([])
    try {
      localStorage.removeItem(`challenge_log_${tk}`)
    } catch {
      // ignore
    }
  }

  // Loading skeleton
  if (reportQuery.isLoading) {
    return (
      <div className="space-y-6 pb-16">
        <ReportHeader ticker={tk} activeTab="challenge" />
        <div className="mx-auto max-w-[1100px] px-4">
          <div className="rounded-xl border border-[#E7E3DA] bg-white p-12 text-center text-xs dark:border-[#2A2822] dark:bg-[#1B1A16]">
            <div className="flex flex-col items-center justify-center space-y-3">
              <Loader2 className="h-6 w-6 animate-spin text-[#0E6E63] dark:text-[#4FD1B5]" />
              <p className="text-sm font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
                Menyiapkan modul uji silang tesis dan debat untuk {tk}…
              </p>
              <p className="text-xs text-[#6B6659] dark:text-[#A8A296]">
                Menginisialisasi agen evaluasi independen dan matriks bukti audit.
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Offline banner
  if (reportData?.offline) {
    return (
      <div className="space-y-6 pb-16">
        <ReportHeader
          ticker={tk}
          activeTab="challenge"
          companyName={reportData.name}
          updatedAt={reportData.updatedAt}
        />
        <div className="mx-auto max-w-[1100px] px-4">
          <div className="rounded-xl border border-[#F6E3B8] bg-[#FEF9EE] p-6 text-xs text-[#A16207] dark:border-[#A16207]/40 dark:bg-[#A16207]/20 dark:text-[#FBBF24]">
            <div className="flex items-start gap-3.5">
              <AlertTriangle className="h-5 w-5 text-[#A16207] shrink-0 dark:text-[#FBBF24]" />
              <div className="space-y-2">
                <div className="text-sm font-semibold">Mode offline - server backend belum aktif</div>
                <p className="text-xs leading-relaxed text-[#6B6659] dark:text-[#A8A296]">
                  {reportData.summary}
                </p>
                <Button
                  size="sm"
                  onClick={() => window.location.reload()}
                  className="mt-2 h-8 rounded-lg bg-[#0E6E63] text-white hover:bg-[#0B5B52] text-xs font-medium dark:bg-[#4FD1B5] dark:text-[#14130F] cursor-pointer"
                >
                  <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
                  <span>Muat ulang</span>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen pb-16">
      {/* Shared Report Header */}
      <ReportHeader
        ticker={tk}
        activeTab="challenge"
        companyName={reportData?.name}
        rating={reportData?.rating}
        price={reportData?.price}
        targetPrice={reportData?.target}
        upside={reportData?.upside}
        updatedAt={reportData?.updatedAt}
        source={reportData?.source}
      />

      <div className="mx-auto max-w-[1100px] px-4 space-y-6">
        {/* Analyst Notice Banner */}
        <div className="flex items-start gap-3 rounded-xl border border-[#E7E3DA] bg-white p-4 text-xs leading-relaxed text-[#6B6659] dark:border-[#2A2822] dark:bg-[#1B1A16] dark:text-[#A8A296]">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-[#0E6E63] dark:text-[#4FD1B5]" />
          <div>
            <span className="font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">Protokol uji silang independen: </span>
            <span>
              Uji ketahanan asumsi valuasi emiten (WACC, pertumbuhan terminal, margin operasi, capex). Agen penilai independen akan menguji kritik Anda terhadap data keuangan audited IDX dan memberikan putusan Dipertahankan, Disesuaikan, atau Premis ditolak.
            </span>
          </div>
        </div>

        {/* 2-Column Responsive Layout: Left Form, Right History */}
        <div className="grid gap-6 md:grid-cols-12 items-start">
          {/* Left Column: Interactive Form */}
          <div className="md:col-span-5 lg:col-span-5">
            <ChallengeForm
              ticker={tk}
              onSubmit={handleSubmitChallenge}
              loading={loading}
              error={submitError}
            />
          </div>

          {/* Right Column: Recent Challenges & Debates History */}
          <div className="md:col-span-7 lg:col-span-7">
            <ChallengeHistoryList
              ticker={tk}
              log={log}
              onClear={handleClearHistory}
            />
          </div>
        </div>

        {/* ADK Run Card */}
        {logData ? (
          <div className="space-y-2 pt-2">
            <AdkRunCard
              ticker={tk}
              log={logData.log as Log}
              history={(logData.history || []) as HistoryItem[]}
              hasRun={logData.has_run}
            />
          </div>
        ) : null}

        {/* Shared Footer Disclaimer */}
        <div className="rounded-xl border border-[#E7E3DA] bg-[#FBFAF7] p-5 text-xs text-[#6B6659] space-y-2 dark:border-[#2A2822] dark:bg-[#1B1A16] dark:text-[#A8A296]">
          <div className="font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
            Kepatuhan dan transparansi data
          </div>
          <p className="leading-relaxed">
            Dokumen ini disusun untuk tujuan analisis riset kompetisi Sectors Hackathon 2026, bukan merupakan rekomendasi jual atau beli efek, maupun saran investasi profesional. Argumen pembelaan dihasilkan oleh sistem multi-agent berbasis data publik emiten.
          </p>
        </div>
      </div>
    </div>
  )
}
