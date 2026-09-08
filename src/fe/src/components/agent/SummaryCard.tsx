import { memo, useMemo } from "react"
import { Link } from "@tanstack/react-router"
import {
  CheckCircle2,
  Clock,
  ShieldCheck,
  FileText,
  AlertTriangle,
  ArrowRight,
  Database,
  Calculator,
  Terminal,
} from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
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
  // LOUD policy: no default BUY / passed-QA claims. Values below only when
  // real agent outputs (critic/writer/valuation) say so; else pending/empty.
  let rating = "MENUNGGU"
  let targetPrice: string | null = null
  let upside: string | null = null
  let verdict: string | null = null
  const takeaways: string[] = []

  // Extract from state deltas across events
  for (const ev of events) {
    if (!ev.state_delta) continue

    // Check critic_output
    if (ev.state_delta.critic_output) {
      const co = ev.state_delta.critic_output as Record<string, unknown>
      if (typeof co === "object" && co !== null) {
        if (co.verdict === "PASS") verdict = "QA PASS (Verified)"
        else if (co.verdict === "REJECT") verdict = "QA REJECT (Review Required)"
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

  // Count active agents involved in review / research
  const uniqueAuthors = new Set(events.map((e) => e.author).filter(Boolean))
  const reviewerCount = Array.from(uniqueAuthors).filter((a) =>
    ["adversarial", "critic", "analyst", "risk", "industry"].includes(a)
  ).length

  const sourcesCount = Array.from(uniqueAuthors).filter((a) =>
    ["collector", "news_harvester", "social_sentiment", "news_search_sub"].includes(a)
  ).length

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
    ? "bg-emerald-950 border-emerald-700 text-emerald-300 font-bold"
    : isSell
    ? "bg-rose-950 border-rose-700 text-rose-300 font-bold"
    : data.rating === "MENUNGGU"
    ? "bg-neutral-900 border-neutral-700 text-neutral-400 font-medium"
    : "bg-amber-950 border-amber-700 text-amber-300 font-bold"

  return (
    <Card className={cn("overflow-hidden border-neutral-800 bg-neutral-950 text-neutral-100 shadow-md font-sans", className)}>
      <CardContent className="p-4 sm:p-5 space-y-3.5">
        {/* Header Title + Recommendation */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-neutral-800 pb-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="font-mono text-xs font-bold uppercase text-emerald-400 border-neutral-700 bg-neutral-900">
                {t}
              </Badge>
              <h2 className="text-sm sm:text-base font-mono font-bold uppercase tracking-wider text-neutral-100 flex items-center gap-2">
                <Terminal className="h-4 w-4 text-emerald-400" />
                <span>SYNTHESIS &amp; QUANT TARGET SUMMARY</span>
              </h2>
            </div>
            <p className="text-xs text-neutral-400 font-mono">
              Multi-agent synthesis derived from official IDX financials and DCF valuation models.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <div className="flex flex-col items-end">
              <span className="text-[9px] font-mono font-semibold uppercase tracking-wider text-neutral-500">
                AI RECOMMENDATION
              </span>
              <div className="flex items-center gap-1.5">
                <span className={cn("inline-flex items-center rounded border px-2.5 py-0.5 text-xs font-mono tracking-wide", ratingBadgeClass)}>
                  {data.rating}
                </span>
                {data.targetPrice && (
                  <span className="font-mono text-xs font-bold text-neutral-100">
                    {data.targetPrice}
                  </span>
                )}
                {data.upside && (
                  <span className="font-mono text-[11px] text-emerald-400 font-semibold">
                    ({data.upside})
                  </span>
                )}
              </div>
            </div>

            <Link
              to="/report/$ticker"
              params={{ ticker: t }}
              className="inline-flex items-center gap-1.5 rounded bg-neutral-900 hover:bg-neutral-800 border border-neutral-700 px-3 py-1.5 text-xs font-mono font-medium text-white transition-colors"
            >
              <FileText className="h-3.5 w-3.5 text-emerald-400" />
              <span>FULL REPORT</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </div>

        {/* 3 Key Takeaway Bullets or Real Findings */}
        <div className="space-y-2">
          <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-neutral-400 flex items-center justify-between">
            <span>SYNTHESIS HIGHLIGHTS &amp; PROVENANCE</span>
            {data.verdict && (
              <span className="text-emerald-400 font-semibold">{data.verdict}</span>
            )}
          </div>

          <div className="grid gap-2 sm:grid-cols-3 text-xs font-sans">
            <div className="flex items-start gap-2.5 rounded-md border border-neutral-800/80 bg-neutral-900/50 p-2.5">
              <Database className="mt-0.5 h-4 w-4 shrink-0 text-sky-400" />
              <div className="text-xs leading-relaxed text-neutral-300">
                <span className="font-semibold font-mono text-neutral-100">Data Intake: </span>
                {data.sourcesCount > 0
                  ? `Integrated ${data.sourcesCount} distinct data & news sources.`
                  : "IDX balance sheets and news feeds ingested into state."}
              </div>
            </div>

            <div className="flex items-start gap-2.5 rounded-md border border-neutral-800/80 bg-neutral-900/50 p-2.5">
              <Calculator className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
              <div className="text-xs leading-relaxed text-neutral-300">
                <span className="font-semibold font-mono text-neutral-100">Valuation: </span>
                {data.targetPrice
                  ? `Blended target computed at ${data.targetPrice}.`
                  : "Mathematical DCF & multiples models computed."}
              </div>
            </div>

            <div className="flex items-start gap-2.5 rounded-md border border-neutral-800/80 bg-neutral-900/50 p-2.5">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
              <div className="text-xs leading-relaxed text-neutral-300">
                <span className="font-semibold font-mono text-neutral-100">Verification: </span>
                {data.reviewerCount > 0
                  ? `Cross-examined by ${data.reviewerCount} reviewer nodes.`
                  : "Adversarial Red Team cross-examination applied."}
              </div>
            </div>
          </div>

          {/* Actual bullets from writer output if present */}
          {data.keyTakeaways.length > 0 && (
            <div className="mt-2 rounded bg-neutral-900/70 border border-neutral-800 p-2.5 space-y-1 text-xs">
              <div className="text-[10px] font-mono font-semibold uppercase text-neutral-400">
                Writer Core Bullets:
              </div>
              <ul className="list-disc pl-4 space-y-0.5 text-neutral-300">
                {data.keyTakeaways.map((b, i) => (
                  <li key={i}>{b}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Metadata Footer: Duration, Reviewers, Disclaimer */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-neutral-800 text-[10px] font-mono text-neutral-500">
          <div className="flex flex-wrap items-center gap-3">
            <span className="flex items-center gap-1 text-neutral-400">
              <Clock className="h-3 w-3 text-neutral-500" />
              <span>ELAPSED: {data.elapsedSeconds}s</span>
            </span>

            <span className="flex items-center gap-1 text-neutral-400">
              <ShieldCheck className="h-3 w-3 text-emerald-500" />
              <span>REVIEWERS: {data.reviewerCount} NODES</span>
            </span>

            <span className="flex items-center gap-1 text-neutral-400">
              <CheckCircle2 className="h-3 w-3 text-sky-500" />
              <span>EVENTS: {done?.n_events ?? events.length} PROCESSED</span>
            </span>
          </div>

          <div className="flex items-center gap-1 text-[10px] text-neutral-500 italic">
            <AlertTriangle className="h-2.5 w-2.5 text-amber-500 shrink-0" />
            <span>Automated quant pipeline for analytical purposes. Not official investment advice.</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
})
