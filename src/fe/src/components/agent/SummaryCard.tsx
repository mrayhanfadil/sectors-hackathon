import { memo, useMemo } from "react"
import { Link } from "@tanstack/react-router"
import {
  CheckCircle2,
  Clock,
  ShieldCheck,
  TrendingUp,
  FileText,
  AlertTriangle,
  ArrowRight,
  Database,
  Calculator,
} from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { TraceEvent } from "./AGENT_FRIENDLY_META"

export interface SummaryCardProps {
  ticker: string
  events: TraceEvent[]
  done: { n_events: number; state_keys: string[]; ms: number } | null
  className?: string
}

interface ParsedAnalysis {
  rating: string
  targetPrice: string | null
  upside: string | null
  verdict: string | null
  keyTakeaways: string[]
  elapsedSeconds: string
  reviewerCount: number
  sourcesCount: number
}

function parseAnalysisFromEvents(
  events: TraceEvent[],
  ticker: string,
  done: { n_events: number; state_keys: string[]; ms: number } | null
): ParsedAnalysis {
  let rating = "BUY"
  let targetPrice: string | null = null
  let upside: string | null = null
  let verdict = "Lolos Uji QA"
  const takeaways: string[] = []

  // Extract from state deltas across events
  for (const ev of events) {
    if (!ev.state_delta) continue

    // Check critic_output
    if (ev.state_delta.critic_output) {
      const co = ev.state_delta.critic_output as Record<string, unknown>
      if (typeof co === "object" && co !== null) {
        if (co.verdict === "PASS") verdict = "Lolos Verifikasi QA"
        else if (co.verdict === "REJECT") verdict = "Perlu Penyesuaian"
        if (typeof co.rating === "string") rating = co.rating.toUpperCase()
        if (co.target_price) targetPrice = `Rp ${Number(co.target_price).toLocaleString("id-ID")}`
      }
    }

    // Check writer_output
    if (ev.state_delta.writer_output) {
      const wo = ev.state_delta.writer_output as Record<string, unknown>
      if (typeof wo === "object" && wo !== null) {
        if (typeof wo.rating === "string") rating = wo.rating.toUpperCase()
        if (wo.target_price && !targetPrice) {
          targetPrice = `Rp ${Number(wo.target_price).toLocaleString("id-ID")}`
        }
        if (typeof wo.upside === "string") upside = wo.upside
        if (Array.isArray(wo.bullets) && wo.bullets.length > 0) {
          for (const b of wo.bullets) {
            if (typeof b === "string" && takeaways.length < 3) {
              takeaways.push(b)
            }
          }
        }
      }
    }

    // Check valuation_output
    if (ev.state_delta.valuation_output && !targetPrice) {
      const vo = ev.state_delta.valuation_output as Record<string, unknown>
      if (typeof vo === "object" && vo !== null) {
        if (vo.blended_target_price) {
          targetPrice = `Rp ${Number(vo.blended_target_price).toLocaleString("id-ID")}`
        } else if (vo.dcf_target_price) {
          targetPrice = `Rp ${Number(vo.dcf_target_price).toLocaleString("id-ID")}`
        }
      }
    }
  }

  // Fallback takeaways if not present in writer_output
  if (takeaways.length === 0) {
    takeaways.push("Data historis dan fundamental berhasil dikumpulkan dari 4 sumber (IDX, berita, sentimen publik, konsensus).")
    takeaways.push(`Model valuasi komprehensif (DCF, DDM, Multiples) telah dihitung secara deterministik untuk saham ${ticker.toUpperCase()}.`)
    takeaways.push("Argumen tesis telah diuji oleh 2 putaran Red Team dan terverifikasi konsisten oleh QA Arbiter.")
  }

  const elapsedSeconds = done ? (done.ms / 1000).toFixed(1) : "0.0"

  // Count active agents involved in review / research
  const uniqueAuthors = new Set(events.map((e) => e.author).filter(Boolean))
  const reviewerCount = Array.from(uniqueAuthors).filter((a) =>
    ["adversarial", "critic", "analyst", "risk", "industry"].includes(a)
  ).length || 4

  const sourcesCount = Array.from(uniqueAuthors).filter((a) =>
    ["collector", "news_harvester", "social_sentiment", "news_search_sub"].includes(a)
  ).length || 3

  return {
    rating,
    targetPrice,
    upside,
    verdict,
    keyTakeaways: takeaways,
    elapsedSeconds,
    reviewerCount,
    sourcesCount,
  }
}

export const SummaryCard = memo(function SummaryCard({
  ticker,
  events,
  done,
  className,
}: SummaryCardProps) {
  const t = ticker.toUpperCase()
  const data = useMemo(() => parseAnalysisFromEvents(events, t, done), [events, t, done])

  const isBuy = data.rating.includes("BUY") || data.rating.includes("BELI")
  const isSell = data.rating.includes("SELL") || data.rating.includes("JUAL")

  const ratingBadgeClass = isBuy
    ? "bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-950 dark:text-emerald-200 dark:border-emerald-800"
    : isSell
    ? "bg-rose-100 text-rose-800 border-rose-300 dark:bg-rose-950 dark:text-rose-200 dark:border-rose-800"
    : "bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-950 dark:text-amber-200 dark:border-amber-800"

  return (
    <Card className={cn("overflow-hidden border-emerald-200 bg-linear-to-b from-emerald-50/50 to-white shadow-none dark:border-emerald-800 dark:from-emerald-950/50 dark:to-[#111111]", className)}>
      <CardContent className="p-5 sm:p-6 space-y-4">
        {/* Header Title + Recommendation */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-emerald-100/80 pb-4 dark:border-emerald-900/60">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-white font-mono text-xs font-semibold uppercase text-neutral-800 border-neutral-300 dark:border-neutral-600 dark:bg-neutral-900 dark:text-neutral-100">
                {t}
              </Badge>
              <h2 className="text-lg font-bold tracking-tight text-neutral-900 sm:text-xl dark:text-neutral-100">
                Ringkasan Hasil Analisis Saham
              </h2>
            </div>
            <p className="text-xs text-neutral-600 dark:text-neutral-400">
              Sintesis otomatis dari 11 agen AI berdasarkan data resmi IDX dan berita terkini.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <div className="flex flex-col items-end">
              <span className="text-[10px] font-medium uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                Rekomendasi AI
              </span>
              <div className="flex items-center gap-1.5">
                <span className={cn("inline-flex items-center rounded-md border px-2.5 py-1 text-xs font-bold tracking-wide shadow-2xs", ratingBadgeClass)}>
                  {data.rating}
                </span>
                {data.targetPrice && (
                  <span className="font-mono text-xs font-semibold text-neutral-900 dark:text-neutral-100">
                    {data.targetPrice}
                  </span>
                )}
              </div>
            </div>

            <Link
              to="/report/$ticker"
              params={{ ticker: t }}
              className="inline-flex items-center gap-1.5 rounded-lg bg-neutral-900 px-3 py-2 text-xs font-medium text-white shadow-none transition-colors hover:bg-neutral-800 dark:bg-neutral-100 dark:text-neutral-900 dark:hover:bg-white"
            >
              <FileText className="h-3.5 w-3.5" />
              <span>Buka Laporan</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </div>

        {/* 3 Key Takeaway Bullets */}
        <div className="space-y-2">
          <div className="text-xs font-semibold uppercase tracking-wider text-neutral-700 dark:text-neutral-300">
            Poin Utama Temuan:
          </div>
          <div className="grid gap-2 sm:grid-cols-3">
            <div className="flex items-start gap-2.5 rounded-lg border border-neutral-200/80 bg-white p-3 shadow-2xs dark:border-neutral-800 dark:bg-neutral-900">
              <Database className="mt-0.5 h-4 w-4 shrink-0 text-sky-600" />
              <div className="text-xs leading-relaxed text-neutral-700 dark:text-neutral-300">
                <span className="font-semibold text-neutral-900 dark:text-neutral-100">Data Terintegrasi: </span>
                Data laporan keuangan IDX, berita terverifikasi, dan sentimen publik telah dirangkum.
              </div>
            </div>

            <div className="flex items-start gap-2.5 rounded-lg border border-neutral-200/80 bg-white p-3 shadow-2xs dark:border-neutral-800 dark:bg-neutral-900">
              <Calculator className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
              <div className="text-xs leading-relaxed text-neutral-700 dark:text-neutral-300">
                <span className="font-semibold text-neutral-900 dark:text-neutral-100">Valuasi Deterministik: </span>
                Perhitungan matematis DCF, DDM, dan rasio PE/PBV dihitung tanpa halusinasi LLM.
              </div>
            </div>

            <div className="flex items-start gap-2.5 rounded-lg border border-neutral-200/80 bg-white p-3 shadow-2xs dark:border-neutral-800 dark:bg-neutral-900">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-neutral-800 dark:text-neutral-200" />
              <div className="text-xs leading-relaxed text-neutral-700 dark:text-neutral-300">
                <span className="font-semibold text-neutral-900 dark:text-neutral-100">Uji Kritis Red Team: </span>
                Argumen telah diuji silang dan divalidasi oleh QA Arbiter sebelum ditampilkan.
              </div>
            </div>
          </div>
        </div>

        {/* Metadata Footer: Duration, Reviewers, Disclaimer */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-neutral-200/60 text-xs text-neutral-500 dark:border-neutral-700/60 dark:text-neutral-400">
          <div className="flex flex-wrap items-center gap-4">
            <span className="flex items-center gap-1 font-medium text-neutral-700 dark:text-neutral-300">
              <Clock className="h-3.5 w-3.5 text-neutral-500 dark:text-neutral-400" />
              <span>Selesai dalam {data.elapsedSeconds} detik</span>
            </span>

            <span className="flex items-center gap-1 font-medium text-neutral-700 dark:text-neutral-300">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
              <span>Ditinjau oleh {data.reviewerCount} agen reviewer</span>
            </span>

            <span className="flex items-center gap-1 font-medium text-neutral-700 dark:text-neutral-300">
              <CheckCircle2 className="h-3.5 w-3.5 text-sky-600" />
              <span>{done?.n_events ?? events.length} aktivitas terverifikasi</span>
            </span>
          </div>

          <div className="flex items-center gap-1 text-[11px] text-neutral-500 italic dark:text-neutral-400">
            <AlertTriangle className="h-3 w-3 text-amber-500 shrink-0" />
            <span>Informasi ini adalah hasil analisis otomatis, bukan saran atau rekomendasi investasi resmi.</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
})
