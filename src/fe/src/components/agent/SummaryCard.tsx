import { memo, useMemo } from "react"
import { Link } from "@tanstack/react-router"
import {
  FileText,
  ArrowRight,
  Database,
  Calculator,
  ShieldCheck,
  CheckCircle2,
  Clock,
} from "lucide-react"
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
  done: { n_events: number; state_keys: string[]; ms: number } | null
): ParsedAnalysis {
  let rating = "MENUNGGU"
  let targetPrice: string | null = null
  let upside: string | null = null
  let verdict: string | null = null
  const takeaways: string[] = []

  for (const ev of events) {
    if (!ev.state_delta) continue

    // Check critic_output
    if (ev.state_delta.critic_output) {
      const co = ev.state_delta.critic_output as Record<string, unknown>
      if (typeof co === "object" && co !== null) {
        if (co.verdict === "PASS") verdict = "Terverifikasi QA"
        else if (co.verdict === "REJECT") verdict = "Perlu peninjauan ulang"
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

  const elapsedSeconds = done ? (done.ms / 1000).toFixed(1) : "0.0"

  const uniqueAuthors = new Set(events.map((e) => e.author).filter(Boolean))
  const reviewerCount = Array.from(uniqueAuthors).filter((a) =>
    ["adversarial", "critic", "analyst", "risk", "industry"].includes(a)
  ).length

  const sourcesCount = Array.from(uniqueAuthors).filter((a) =>
    ["collector", "news_harvester", "news_search_sub"].includes(a)
  ).length;

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
  const data = useMemo(() => parseAnalysisFromEvents(events, done), [events, done])

  const isBuy = data.rating.includes("BUY") || data.rating.includes("BELI")
  const isSell = data.rating.includes("SELL") || data.rating.includes("JUAL")
  const isHold = data.rating.includes("HOLD")

  const ratingBadgeClass = isBuy
    ? "bg-[#157F3D]/10 text-[#157F3D] border-[#157F3D]/30 dark:bg-[#157F3D]/20 dark:text-[#4ade80]"
    : isSell
    ? "bg-[#B4232A]/10 text-[#B4232A] border-[#B4232A]/30 dark:bg-[#B4232A]/20 dark:text-[#f87171]"
    : isHold
    ? "bg-[#A16207]/10 text-[#A16207] border-[#A16207]/30 dark:bg-[#A16207]/20 dark:text-[#facc15]"
    : "bg-[#B4C7FF] text-[#666666] border-[#D9D9D9] dark:bg-[#1e2229] dark:text-[#666666] dark:border-[#262930]"

  return (
    <div
      className={cn(
        "rounded-xl border border-[#D9D9D9] dark:border-[#262930] bg-white dark:bg-[#090a0c] p-5 sm:p-6 space-y-4 font-sans shadow-none",
        className
      )}
    >
      {/* Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#D9D9D9]/60 dark:border-[#262930]/60">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h2 className="font-serif text-lg font-medium text-[#333333] dark:text-[#f1f5f9]">
              Ringkasan hasil riset {t}
            </h2>
          </div>
          <p className="text-xs text-[#666666] dark:text-[#666666]">
            Sintesis multi-agen berdasarkan laporan keuangan resmi IDX dan model valuasi deterministik.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex flex-col items-end">
            <span className="text-[11px] text-[#666666] dark:text-[#666666]">Rekomendasi</span>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={cn("inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold", ratingBadgeClass)}>
                {data.rating}
              </span>
              {data.targetPrice && (
                <span className="text-xs font-semibold text-[#333333] dark:text-[#f1f5f9]">
                  {data.targetPrice}
                </span>
              )}
              {data.upside && (
                <span className="text-[11px] font-medium text-[#157F3D] dark:text-[#4ade80]">
                  ({data.upside})
                </span>
              )}
            </div>
          </div>

          <Link
            to="/report/$ticker"
            params={{ ticker: t }}
            className="inline-flex items-center gap-1.5 rounded-lg bg-[#0928B1] text-white hover:bg-[#0c5c53] px-3.5 py-1.5 text-xs font-medium transition-colors"
          >
            <FileText className="h-3.5 w-3.5" />
            <span>Lihat laporan lengkap</span>
            <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
      </div>

      {/* Highlights Grid */}
      <div className="grid gap-3 sm:grid-cols-3 text-xs">
        <div className="flex items-start gap-3 rounded-lg border border-[#D9D9D9] dark:border-[#262930] bg-[#f1f5f9]/60 dark:bg-[#1e2229]/40 p-3">
          <Database className="mt-0.5 h-4 w-4 shrink-0 text-sky-600 dark:text-sky-400" />
          <div className="space-y-0.5">
            <span className="font-medium text-[#333333] dark:text-[#f1f5f9]">Pengumpulan data</span>
            <p className="text-[#666666] dark:text-[#666666] leading-relaxed">
              {data.sourcesCount > 0
                ? `Menggabungkan ${data.sourcesCount} sumber data laporan IDX dan berita terkini.`
                : "Data neraca keuangan IDX dan keterbukaan informasi telah diproses."}
            </p>
          </div>
        </div>

        <div className="flex items-start gap-3 rounded-lg border border-[#D9D9D9] dark:border-[#262930] bg-[#f1f5f9]/60 dark:bg-[#1e2229]/40 p-3">
          <Calculator className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
          <div className="space-y-0.5">
            <span className="font-medium text-[#333333] dark:text-[#f1f5f9]">Valuasi nilai wajar</span>
            <p className="text-[#666666] dark:text-[#666666] leading-relaxed">
              {data.targetPrice
                ? `Perhitungan nilai wajar gabungan berada di ${data.targetPrice}.`
                : "Model matematika DCF dan rasio kelipatan telah dihitung."}
            </p>
          </div>
        </div>

        <div className="flex items-start gap-3 rounded-lg border border-[#D9D9D9] dark:border-[#262930] bg-[#f1f5f9]/60 dark:bg-[#1e2229]/40 p-3">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-[#0928B1] dark:text-[#7596FF]" />
          <div className="space-y-0.5">
            <span className="font-medium text-[#333333] dark:text-[#f1f5f9]">Uji silang &amp; penelaahan</span>
            <p className="text-[#666666] dark:text-[#666666] leading-relaxed">
              {data.reviewerCount > 0
                ? `Ditinjau oleh ${data.reviewerCount} agen reviewer dan penguji kritis.`
                : "Uji kritis argumen dan verifikasi data selesai dilakukan."}
            </p>
          </div>
        </div>
      </div>

      {/* Writer bullets if available */}
      {data.keyTakeaways.length > 0 && (
        <div className="rounded-lg border border-[#D9D9D9] dark:border-[#262930] bg-[#f1f5f9]/60 dark:bg-[#1e2229]/40 p-3.5 space-y-2 text-xs">
          <div className="font-medium text-[#333333] dark:text-[#f1f5f9]">
            Poin-poin kesimpulan riset:
          </div>
          <ul className="list-disc pl-4 space-y-1 text-[#666666] dark:text-[#666666] leading-relaxed">
            {data.keyTakeaways.map((b, i) => (
              <li key={i}>{b}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Footer Info */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-[#D9D9D9]/60 dark:border-[#262930]/60 text-xs text-[#666666] dark:text-[#666666]">
        <div className="flex flex-wrap items-center gap-3">
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            <span>Durasi: {data.elapsedSeconds} detik</span>
          </span>
          <span className="flex items-center gap-1">
            <CheckCircle2 className="h-3 w-3 text-emerald-600 dark:text-emerald-400" />
            <span>{done?.n_events ?? events.length} langkah diproses</span>
          </span>
        </div>

        <p className="text-[11px] italic text-[#666666]/80 dark:text-[#666666]/80">
          Otomatisasi kalkulasi riset untuk referensi analitis. Bukan ajakan beli atau jual efek.
        </p>
      </div>
    </div>
  )
})
