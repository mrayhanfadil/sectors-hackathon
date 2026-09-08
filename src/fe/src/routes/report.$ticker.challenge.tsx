import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import * as React from "react"
import { Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { fetchReport, fetchReportLog } from "@/lib/api"
import { ReportHeader } from "@/components/report/ReportHeader"
import { ChallengeForm } from "@/components/report/ChallengeForm"
import { ChallengeHistoryList, type ChallengeEntry } from "@/components/report/ChallengeHistoryList"
import { AdkRunCard, type Log, type HistoryItem } from "@/components/report/AdkRunCard"

export const Route = (createFileRoute as any)("/report/$ticker/challenge")({
  component: ChallengePage,
})

// LOUD policy: no seeded debate history. Past "verdict: defend" entries were
// hardcoded narratives presented as completed Red Team runs. Empty history
// renders the clean empty state; real user runs persist via localStorage below.
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
            exhibit_ref: data.exhibit_ref || "Exhibit 3.1 - Sensitivity & DCF Audit",
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
      <div className="space-y-6">
        <ReportHeader ticker={tk} activeTab="challenge" />
        <div className="rounded-xl border border-neutral-200 bg-white p-8 text-center shadow-2xs dark:border-neutral-800 dark:bg-[#111111]">
          <div className="flex flex-col items-center justify-center space-y-3">
            <Loader2 className="h-6 w-6 animate-spin text-neutral-700 dark:text-neutral-300" />
            <p className="text-sm font-medium text-neutral-800 dark:text-neutral-200">
              Menyiapkan modul tantangan tesis & debat untuk {tk}...
            </p>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">
              Menginisialisasi agent adversarial dan matriks bukti audit.
            </p>
          </div>
        </div>
      </div>
    )
  }

  // Offline banner
  if (reportData?.offline) {
    return (
      <div className="space-y-6">
        <ReportHeader
          ticker={tk}
          activeTab="challenge"
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

  return (
    <div className="space-y-6 pb-12">
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

      {/* Panduan pemula: rating + upside dalam 2 kalimat */}
      <div className="rounded-md border border-neutral-200 border-l-2 border-l-[#0070f3] bg-white p-3 text-xs leading-relaxed text-neutral-600 dark:border-neutral-800 dark:bg-[#111111] dark:text-neutral-400">
        <span className="font-semibold text-[#0a0a0a] dark:text-white">Baru mulai baca analisanya? </span>
        BUY artinya analis menilai saham ini layak dibeli, HOLD artinya ditahan dulu, SELL artinya
        sebaiknya dihindari. Upside = potensi kenaikan harga ke harga wajar — di halaman ini kamu
        bisa nanya atau nantang asumsi di balik angka-angka itu, AI-nya bakal jawab pakai data.
      </div>

      {/* Intro Description */}
      <div className="space-y-1">
        <h2 className="text-base font-bold tracking-tight text-neutral-900 dark:text-neutral-100">
          Tantang Asumsi Laporan ({tk})
        </h2>
        <p className="text-xs leading-relaxed text-neutral-600 max-w-3xl dark:text-neutral-400">
          Punya keraguan sama angka di laporan (mis. asumsi pertumbuhan atau biaya modal)? Tulis
          pertanyaanmu di sini — AI-nya bakal bela atau koreksi jawabannya pakai data, bukan asal setuju.
        </p>
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

      {/* ADK Run Card - Accessible directly from challenge sub-route */}
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
          Dokumen ini disusun untuk tujuan analisis riset kompetisi Sectors Hackathon 2026, bukan merupakan rekomendasi jual atau beli efek, maupun saran investasi profesional (kepatuhan regulasi OJK). Argumen pembelaan dihasilkan oleh sistem multi-agent berbasis data publik emiten.
        </p>
      </div>
    </div>
  )
}
