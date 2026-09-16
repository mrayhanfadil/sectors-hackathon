import { memo, useMemo } from "react"
import { Link } from "@tanstack/react-router"
import { CheckCircle2, Loader2, Circle, ArrowRight } from "lucide-react"
import { cn } from "@/lib/utils"
import {
  PIPELINE_STAGES,
  getFriendlyAgent,
  translateFunctionName,
  type TraceEvent,
} from "./AGENT_FRIENDLY_META"

export interface RetailStoryProps {
  events: TraceEvent[]
  running: boolean
  done: { n_events: number; state_keys: string[]; ms: number } | null
  ticker: string
  agentStatuses: Record<string, "idle" | "running" | "finished" | "error">
  className?: string
}

const RETAIL_SUBTITLE: Record<string, string> = {
  intake: "Ambil laporan IDX dan berita terbaru",
  valuation: "Hitung nilai wajar (DCF/DDM/PE) secara deterministik",
  research: "Kaji kinerja keuangan, persaingan industri, dan risiko",
  writing: "Susun kesimpulan dan grafik yang mudah dibaca",
  qa: "Pengujian kritis antar-agen untuk verifikasi mutu",
}

function retailLine(ev: TraceEvent): string | null {
  if (ev.function_calls && ev.function_calls.length > 0) {
    const t = translateFunctionName(ev.function_calls[0].name)
    return t.replace(/\s*\([a-z_]+\)\s*$/i, "").trim()
  }
  if (ev.function_responses && ev.function_responses.length > 0) {
    return `${translateFunctionName(ev.function_responses[0].name)} selesai`
  }
  if (ev.transfer_to) return null
  if (ev.state_delta_keys && ev.state_delta_keys.length > 0) {
    const stage = getFriendlyAgent(ev.author).stageId
    const label: Record<string, string> = {
      intake: "Data terkumpul, lanjut perhitungan",
      valuation: "Angka valuasi telah dihitung",
      research: "Temuan riset telah dicatat",
      writing: "Draf laporan telah disusun",
      qa: "Hasil uji penjaminan mutu telah dicatat",
    }
    return label[stage] || "Hasil tahap ini dicatat"
  }
  if (ev.text) {
    const first = ev.text.trim().split("\n")[0].replace(/[#*_`>\[\]]/g, "").trim()
    if (!first) return null
    if (/^(node|branch|transfer_to|state_delta|function_calls)\s*:/i.test(first)) return null
    return first.length > 140 ? `${first.slice(0, 140)}…` : first
  }
  return null
}

type StageStatus = "idle" | "running" | "finished"

function stageStatus(
  stageId: string,
  primaryAgents: string[],
  agentStatuses: Record<string, StageStatus | string>,
  running: boolean,
  done: RetailStoryProps["done"],
): StageStatus {
  if (done) return "finished"
  let run = false
  let fin = 0
  for (const k of primaryAgents) {
    const s = agentStatuses[k]
    if (s === "running") run = true
    if (s === "finished") fin += 1
  }
  if (run) return "running"
  if (fin === primaryAgents.length && primaryAgents.length > 0) return "finished"
  if (fin > 0 && running) return "running"
  return "idle"
}

export const RetailStory = memo(function RetailStory({
  events,
  running,
  done,
  ticker,
  agentStatuses,
  className,
}: RetailStoryProps) {
  const t = ticker.toUpperCase() || "Emiten"

  const steps = useMemo(() => {
    return PIPELINE_STAGES.map((stage) => {
      const status = stageStatus(stage.id, stage.primaryAgents, agentStatuses, running, done)
      const stageEvents = events.filter(
        (e) => getFriendlyAgent(e.author).stageId === stage.id,
      )
      let line: string | null = null
      for (let i = stageEvents.length - 1; i >= 0; i--) {
        line = retailLine(stageEvents[i])
        if (line) break
      }
      if (!line) {
        line =
          status === "finished"
            ? "Selesai."
            : status === "running"
              ? "Sedang diproses…"
              : "Menunggu giliran."
      }
      return { stage, status, line, count: stageEvents.length }
    })
  }, [events, running, done, agentStatuses])

  const finishedCount = steps.filter((s) => s.status === "finished").length

  return (
    <div className={cn("rounded-xl border border-[#E7E3DA] dark:border-[#2A2822] bg-white dark:bg-[#1B1A16] shadow-none overflow-hidden font-sans", className)}>
      <div className="border-b border-[#E7E3DA] dark:border-[#2A2822] px-5 py-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="font-serif text-lg font-medium text-[#1C1B17] dark:text-[#EDEAE3]">
              Alur analisis {t}
            </h2>
            <p className="mt-0.5 text-xs text-[#6B6659] dark:text-[#A8A296]">
              {done
                ? "Selesai. Hasil utama terangkum di kartu ringkasan di atas."
                : running
                ? "Proses analisis sedang berjalan…"
                : "Tekan tombol jalankan untuk memulai analisis."}
            </p>
          </div>
          <span className="rounded-full border border-[#E7E3DA] dark:border-[#2A2822] bg-[#F5F2EB] dark:bg-[#23211C] px-3 py-1 text-xs text-[#6B6659] dark:text-[#A8A296]">
            {finishedCount} dari 5 tahap selesai
          </span>
        </div>
      </div>

      <ol className="divide-y divide-[#E7E3DA]/60 dark:divide-[#2A2822]/60">
        {steps.map(({ stage, status, line }, idx) => {
          return (
            <li key={stage.id} className="flex gap-3 px-5 py-4">
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    "flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs",
                    status === "finished" && "border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300",
                    status === "running" && "border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300",
                    status === "idle" && "border-[#E7E3DA] dark:border-[#2A2822] bg-[#F5F2EB] dark:bg-[#23211C] text-[#6B6659] dark:text-[#A8A296]",
                  )}
                >
                  {status === "finished" ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : status === "running" ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <span>{stage.stageNumber}</span>
                  )}
                </div>
                {idx < steps.length - 1 && <div className="mt-1 w-px flex-1 bg-[#E7E3DA] dark:bg-[#2A2822]" />}
              </div>
              <div className="min-w-0 flex-1 pb-1">
                <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                  <span className="text-sm font-medium text-[#1C1B17] dark:text-[#EDEAE3]">{stage.title}</span>
                  {status === "running" && (
                    <span className="rounded-full bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 text-[10px] text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800/60">
                      Sedang diproses
                    </span>
                  )}
                </div>
                <p className="mt-0.5 text-xs text-[#6B6659] dark:text-[#A8A296]">{RETAIL_SUBTITLE[stage.id] || stage.description}</p>
                <p className="mt-1.5 text-xs text-[#1C1B17] dark:text-[#EDEAE3] leading-relaxed">{line}</p>
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
})
