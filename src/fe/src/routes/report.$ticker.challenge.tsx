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

// LOUD policy: no seeded debate history. Real user runs persist via localStorage below.
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
            // House format (docs/rules/house-report-format.md): exhibits are numbered by
            // the renderer's global counter, so a user-facing string must cite the
            // exhibit by TITLE. A literal number here drifts the moment a chart moves.
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
      <div className="space-y-4">
        <ReportHeader ticker={tk} activeTab="challenge" />
        <div className="border border-neutral-300 bg-white p-8 text-center font-mono text-xs dark:border-[#262930] dark:bg-[#121316]">
          <div className="flex flex-col items-center justify-center space-y-2">
            <Loader2 className="h-5 w-5 animate-spin text-amber-600 dark:text-amber-400" />
            <p className="font-semibold text-neutral-800 dark:text-neutral-200">
              TERMINAL :: MENYIAPKAN MODUL TANTANGAN TESIS &amp; DEBAT UNTUK {tk}...
            </p>
            <p className="text-[11px] text-neutral-500 dark:text-neutral-400">
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
      <div className="space-y-4">
        <ReportHeader
          ticker={tk}
          activeTab="challenge"
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

  return (
    <div className="space-y-4 pb-12">
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

      {/* Terminal Section Header */}
      <div className="border-l-2 border-l-rose-500 border border-neutral-300 bg-neutral-900/[0.02] px-3 py-2 text-[10px] font-mono font-semibold uppercase tracking-wider text-neutral-600 dark:border-[#262930] dark:bg-[#15171c] dark:text-neutral-300">
        // 03. ADVERSARIAL RED TEAM AUDIT // {tk} IJ &lt;EQUITY&gt; CHAL
      </div>

      {/* Analyst notice banner */}
      <div className="border border-neutral-300 bg-white p-3 font-mono text-[11px] leading-relaxed text-neutral-600 dark:border-[#262930] dark:bg-[#121316] dark:text-neutral-300">
        <span className="font-bold text-amber-600 dark:text-amber-400">PROMPT :: ADVERSARIAL PROTOCOL NOTICE &gt; </span>
        <span className="font-sans text-xs">
          Uji ketahanan asumsi valuasi emiten (WACC, terminal growth, operating margin, capex). Agen penilai independen akan menguji kritik Anda terhadap data keuangan audited IDX dan memberikan putusan DEFEND, CONCEDE, atau REJECT.
        </span>
      </div>

      {/* 2-Column Responsive Layout: Left Form, Right History */}
      <div className="grid gap-4 md:grid-cols-12 items-start">
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
          Dokumen ini disusun untuk tujuan analisis riset kompetisi Sectors Hackathon 2026, bukan merupakan rekomendasi jual atau beli efek, maupun saran investasi profesional (kepatuhan regulasi OJK). Argumen pembelaan dihasilkan oleh sistem multi-agent berbasis data publik emiten.
        </p>
      </div>
    </div>
  )
}
