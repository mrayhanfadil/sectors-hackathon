import { memo, useState } from "react"
import {
  CheckCircle2,
  AlertCircle,
  Loader2,
  ChevronRight,
  Layers,
} from "lucide-react"
import { cn } from "@/lib/utils"
import {
  PIPELINE_STAGES,
  getFriendlyAgent,
  type PipelineStageConfig,
} from "./AGENT_FRIENDLY_META"

export interface PhaseTimelineProps {
  agentStatuses: Record<string, "idle" | "running" | "finished" | "error">
  selectedAuthor?: string
  onFilterAuthor?: (author: string) => void
  running?: boolean
  done?: { n_events: number; state_keys: string[]; ms: number } | null
  className?: string
}

function getStageStatus(
  stage: PipelineStageConfig,
  agentStatuses: Record<string, "idle" | "running" | "finished" | "error">,
  done: { n_events: number; state_keys: string[]; ms: number } | null,
  running?: boolean
): {
  status: "idle" | "running" | "finished" | "error"
  finishedCount: number
  totalCount: number
} {
  const primaryKeys = stage.primaryAgents
  let errCount = 0
  let runCount = 0
  let finCount = 0

  for (const k of primaryKeys) {
    const s = agentStatuses[k] || "idle"
    if (s === "error") errCount += 1
    else if (s === "running") runCount += 1
    else if (s === "finished") finCount += 1
  }

  // Check subagents if any
  for (const k of stage.allAgents) {
    if (!primaryKeys.includes(k)) {
      const s = agentStatuses[k]
      if (s === "error") errCount += 1
      if (s === "running") runCount += 1
    }
  }

  if (errCount > 0) {
    return { status: "error", finishedCount: finCount, totalCount: primaryKeys.length }
  }

  if (done !== null) {
    return { status: "finished", finishedCount: primaryKeys.length, totalCount: primaryKeys.length }
  }

  if (runCount > 0) {
    return { status: "running", finishedCount: finCount, totalCount: primaryKeys.length }
  }

  if (finCount === primaryKeys.length && primaryKeys.length > 0) {
    return { status: "finished", finishedCount: finCount, totalCount: primaryKeys.length }
  }

  if (finCount > 0 && running) {
    return { status: "running", finishedCount: finCount, totalCount: primaryKeys.length }
  }

  return { status: "idle", finishedCount: finCount, totalCount: primaryKeys.length }
}

const STATUS_ID: Record<string, string> = {
  running: "berjalan",
  finished: "selesai",
  error: "gagal",
  idle: "antri",
}

export const PhaseTimeline = memo(function PhaseTimeline({
  agentStatuses,
  selectedAuthor = "all",
  onFilterAuthor,
  running = false,
  done = null,
  className,
}: PhaseTimelineProps) {
  let completedStages = 0
  let firstRunningId: string | null = null
  for (const st of PIPELINE_STAGES) {
    const { status } = getStageStatus(st, agentStatuses, done, running)
    if (status === "finished") completedStages++
    if (status === "running" && firstRunningId === null) firstRunningId = st.id
  }

  const [expandedId, setExpandedId] = useState<string | null>(firstRunningId)

  const globalStatus = done !== null ? "SELESAI" : running ? "JALAN" : "SIAGA"

  return (
    <div className={cn("w-full rounded-lg border border-neutral-800 bg-neutral-950 p-4 font-sans shadow-md", className)}>
      {/* Header: title + global status + progress bar */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-neutral-900 border border-neutral-800 text-emerald-400">
            <Layers className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-neutral-100">
              Alur kerja mesin
            </h3>
            <p className="text-[11px] text-neutral-500">
              {completedStages}/{PIPELINE_STAGES.length} tahap selesai
            </p>
          </div>
        </div>
        <span
          className={cn(
            "rounded-full border px-3 py-1 text-[11px] font-bold",
            globalStatus === "JALAN"
              ? "border-amber-700 bg-amber-950 text-amber-300"
              : globalStatus === "SELESAI"
              ? "border-emerald-700 bg-emerald-950 text-emerald-300"
              : "border-neutral-700 bg-neutral-900 text-neutral-400"
          )}
        >
          {globalStatus === "JALAN" ? (
            <span className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
              JALAN
            </span>
          ) : (
            globalStatus
          )}
        </span>
      </div>
      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-neutral-800">
        <div
          className={cn(
            "h-full rounded-full transition-all",
            globalStatus === "JALAN" ? "bg-amber-400" : "bg-emerald-400"
          )}
          style={{ width: `${(completedStages / PIPELINE_STAGES.length) * 100}%` }}
        />
      </div>

      {/* Stages: compact cards, tap to expand */}
      <div className="mt-3 grid grid-cols-1 gap-2.5 md:grid-cols-5">
        {PIPELINE_STAGES.map((stage) => {
          const { status, finishedCount, totalCount } = getStageStatus(
            stage,
            agentStatuses,
            done,
            running
          )
          const isExpanded = expandedId === stage.id

          let ringClass = "border-neutral-700 bg-neutral-900 text-neutral-400"
          let pillClass = "bg-neutral-900 border-neutral-700 text-neutral-400"
          let statusLabel = "ANTRI"

          if (status === "running") {
            ringClass = "border-amber-400 bg-amber-950 text-amber-200"
            pillClass = "bg-amber-950 border-amber-700 text-amber-200 font-bold"
            statusLabel = "JALAN"
          } else if (status === "finished") {
            ringClass = "border-emerald-600 bg-emerald-950 text-emerald-200"
            pillClass = "bg-emerald-950 border-emerald-700 text-emerald-200"
            statusLabel = "SELESAI"
          } else if (status === "error") {
            ringClass = "border-rose-500 bg-rose-950 text-rose-200"
            pillClass = "bg-rose-950 border-rose-700 text-rose-200 font-bold"
            statusLabel = "GAGAL"
          }

          return (
            <div
              key={stage.id}
              className={cn(
                "rounded-lg border bg-neutral-900/40 transition-colors",
                status === "running"
                  ? "border-amber-700/70"
                  : status === "finished"
                  ? "border-emerald-800/60"
                  : status === "error"
                  ? "border-rose-800/70"
                  : "border-neutral-800"
              )}
            >
              <div
                role="button"
                tabIndex={0}
                onClick={() => setExpandedId(isExpanded ? null : stage.id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault()
                    setExpandedId(isExpanded ? null : stage.id)
                  }
                }}
                className="flex cursor-pointer items-center gap-2.5 p-3"
                title={isExpanded ? "Ketuk untuk ringkas" : "Ketuk untuk lihat mesin di tahap ini"}
              >
                <div
                  className={cn(
                    "flex h-9 w-9 shrink-0 items-center justify-center rounded-full border-2 text-sm font-bold",
                    ringClass
                  )}
                >
                  {status === "finished" ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : status === "running" ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : status === "error" ? (
                    <AlertCircle className="h-4 w-4" />
                  ) : (
                    stage.stageNumber
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-bold text-neutral-100">
                    {stage.title}
                  </div>
                  <div className="mt-0.5 text-[11px] text-neutral-500">
                    {finishedCount}/{totalCount} mesin · {statusLabel}
                  </div>
                </div>
                <ChevronRight
                  className={cn(
                    "h-4 w-4 shrink-0 text-neutral-500 transition-transform",
                    isExpanded && "rotate-90"
                  )}
                />
              </div>

              {isExpanded && (
                <div className="border-t border-neutral-800 px-3 pb-3 pt-2.5">
                  <p className="text-xs leading-relaxed text-neutral-400">
                    {stage.description}
                  </p>
                  <div className="mt-2.5 flex flex-wrap gap-1.5">
                    {stage.primaryAgents.map((aKey) => {
                      const aMeta = getFriendlyAgent(aKey)
                      const aStatus = done !== null ? "finished" : (agentStatuses[aKey] || "idle")
                      const isSelected = selectedAuthor === aKey

                      return (
                        <button
                          key={aKey}
                          type="button"
                          onClick={() => onFilterAuthor?.(isSelected ? "all" : aKey)}
                          className={cn(
                            "flex items-center gap-1.5 rounded-md px-2 py-1 text-[11px] transition-colors border",
                            isSelected
                              ? "border-emerald-400 bg-emerald-950 text-emerald-200 font-bold"
                              : aStatus === "running"
                              ? "border-amber-700 bg-amber-950/80 text-amber-200 font-semibold"
                              : aStatus === "finished"
                              ? "border-neutral-700 bg-neutral-900 text-neutral-300 hover:border-neutral-500"
                              : "border-neutral-800 bg-neutral-950 text-neutral-500 hover:border-neutral-600"
                          )}
                          title={`${aMeta.title} (${STATUS_ID[aStatus] ?? aStatus}) — klik untuk saring catatan`}
                        >
                          {aStatus === "running" ? (
                            <Loader2 className="h-2.5 w-2.5 animate-spin text-amber-400" />
                          ) : aStatus === "finished" ? (
                            <CheckCircle2 className="h-2.5 w-2.5 text-emerald-400" />
                          ) : aStatus === "error" ? (
                            <AlertCircle className="h-2.5 w-2.5 text-rose-400" />
                          ) : (
                            <span className="h-1.5 w-1.5 rounded-full bg-neutral-600" />
                          )}
                          <span>{aMeta.shortLabel}</span>
                        </button>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      <p className="mt-3 text-[11px] text-neutral-600">
        Ketuk tiap tahap untuk melihat mesin di dalamnya · ketuk nama mesin untuk menyaring catatan langkah.
      </p>
    </div>
  )
})
