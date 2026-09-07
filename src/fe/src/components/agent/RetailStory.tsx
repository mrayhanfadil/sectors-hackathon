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
  intake: "Ambil laporan IDX + berita terbaru",
  valuation: "Hitung harga wajar (DCF/DDM/PE), bukan tebak-tebakan",
  research: "Cek untung-rugi, kompetitor, dan risiko rugi",
  writing: "Susun cerita + grafik yang gampang dibaca",
  qa: "Agen lain uji argumen biar ga ngawur",
}

/** Ubah 1 event teknis jadi 1 kalimat ritel. Buang semua istilah dev. */
function retailLine(ev: TraceEvent): string | null {
  if (ev.function_calls && ev.function_calls.length > 0) {
    const t = translateFunctionName(ev.function_calls[0].name)
    // translateFunctionName kadang masih bawa "(name)" dari caller — RetailStory selalu bersih
    return t.replace(/\s*\([a-z_]+\)\s*$/i, "").trim()
  }
  if (ev.function_responses && ev.function_responses.length > 0) {
    return `${translateFunctionName(ev.function_responses[0].name)} selesai`
  }
  if (ev.transfer_to) return null // serah-terima antar agen = noise buat ritel
  if (ev.state_delta_keys && ev.state_delta_keys.length > 0) {
    const stage = getFriendlyAgent(ev.author).stageId
    const label: Record<string, string> = {
      intake: "Data terkumpul, lanjut hitung",
      valuation: "Angka valuasi ketemu",
      research: "Temuan riset dicatat",
      writing: "Draf laporan jadi",
      qa: "Hasil cek kualitas dicatat",
    }
    return label[stage] || "Hasil tahap ini dicatat"
  }
  if (ev.text) {
    const first = ev.text.trim().split("\n")[0].replace(/[#*_`>\[\]]/g, "").trim()
    if (!first) return null
    // buang sisa artefak teknis
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
  // tahap awal selesai kalau tahap berikutnya sudah jalan
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
  const t = ticker.toUpperCase() || "SAHAM"

  const steps = useMemo(() => {
    return PIPELINE_STAGES.map((stage) => {
      const status = stageStatus(stage.id, stage.primaryAgents, agentStatuses, running, done)
      const stageEvents = events.filter(
        (e) => getFriendlyAgent(e.author).stageId === stage.id,
      )
      // 1 kalimat per tahap: event terakhir yang bisa dibahasakan ritel
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
              ? "Lagi dikerjain…"
              : "Menunggu giliran."
      }
      return { stage, status, line, count: stageEvents.length }
    })
  }, [events, running, done, agentStatuses])

  const finishedCount = steps.filter((s) => s.status === "finished").length
  const activeStep = steps.findIndex((s) => s.status === "running")

  return (
    <div className={cn("rounded-lg border border-neutral-200 bg-white shadow-none overflow-hidden dark:border-neutral-800 dark:bg-[#111111]", className)}>
      <div className="border-b border-neutral-100 px-4 py-3.5 sm:px-5 dark:border-neutral-800">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-sm font-bold text-neutral-900 sm:text-base dark:text-neutral-100">
              Cerita analisis {t} — 5 langkah
            </h2>
            <p className="mt-0.5 text-xs leading-relaxed text-neutral-500 dark:text-neutral-400">
              {done
                ? `Selesai. Hasil paling atas yang penting, sisanya cara sampainya.`
                : running
                  ? activeStep >= 0
                    ? `Langkah ${activeStep + 1} dari 5 lagi jalan: ${steps[activeStep].stage.title}. Tunggu ya.`
                    : `Lagi mulai…`
                  : `Belum jalan. Tekan Jalankan, terus baca dari atas ke bawah.`}
            </p>
          </div>
          <span className="rounded-full border border-neutral-200 bg-neutral-50 px-2.5 py-1 font-mono text-[11px] font-medium text-neutral-600 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-300">
            {finishedCount}/5 selesai
          </span>
        </div>
      </div>

      <ol className="divide-y divide-neutral-100 dark:divide-neutral-800">
        {steps.map(({ stage, status, line }, idx) => {
          const StageIcon = stage.icon
          return (
            <li key={stage.id} className="flex gap-3 px-4 py-3.5 sm:px-5">
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-full border",
                    status === "finished" && "border-emerald-300 bg-emerald-100 text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-200",
                    status === "running" && "border-amber-300 bg-amber-100 text-amber-900 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200",
                    status === "idle" && "border-neutral-200 bg-neutral-50 text-neutral-400 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-500",
                  )}
                >
                  {status === "finished" ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : status === "running" ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Circle className="h-4 w-4" />
                  )}
                </div>
                {idx < steps.length - 1 && <div className="mt-1 w-px flex-1 bg-neutral-200 dark:bg-neutral-800" />}
              </div>
              <div className="min-w-0 flex-1 pb-1">
                <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                  <span className="font-mono text-[10px] font-medium uppercase tracking-wider text-neutral-400 dark:text-neutral-500">
                    Langkah {stage.stageNumber}
                  </span>
                  <span className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">{stage.title}</span>
                  {status === "running" && (
                    <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-900 dark:bg-amber-950 dark:text-amber-200">
                      Lagi jalan
                    </span>
                  )}
                </div>
                <p className="mt-0.5 text-xs text-neutral-500 dark:text-neutral-400">{RETAIL_SUBTITLE[stage.id] || stage.description}</p>
                <p className="mt-1.5 text-[13px] leading-relaxed text-neutral-800 dark:text-neutral-200">{line}</p>
              </div>
            </li>
          )
        })}
      </ol>

      <div className="border-t border-neutral-100 bg-neutral-50/70 px-4 py-3.5 sm:px-5 dark:border-neutral-800 dark:bg-neutral-900/70">
        <p className="text-xs font-semibold text-neutral-800 dark:text-neutral-100">Apa artinya buat saya?</p>
        <ul className="mt-1.5 list-disc space-y-1 pl-5 text-xs leading-relaxed text-neutral-600 dark:text-neutral-400">
          <li>
            {done
              ? `Keputusan ada di kartu hijau paling atas + laporan lengkap. Cerita 5 langkah ini cuma jejak cara sampainya.`
              : `Nanti keputusan (BUY/HOLD/SELL + harga wajar) muncul di kartu hijau paling atas. Bagian ini cuma nunjukin progres.`}
          </li>
          <li>
            Ga perlu paham tiap langkah. Kalau mau bukti, buka{" "}
            <Link
              to="/report/$ticker"
              params={{ ticker: t }}
              className="inline-flex items-center gap-0.5 font-semibold text-neutral-900 underline underline-offset-2 dark:text-neutral-100"
            >
              laporan {t} <ArrowRight className="h-3 w-3" />
            </Link>
            .
          </li>
        </ul>
        <p className="mt-2 text-[11px] italic leading-relaxed text-neutral-400 dark:text-neutral-500">
          Ini info otomatis, bukan saran beli/jual. Keputusan tetap di kamu.
        </p>
      </div>
    </div>
  )
})
