import { memo } from "react"
import {
  CheckCircle2,
  AlertCircle,
  Loader2,
  ChevronRight,
  Activity,
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

export const PhaseTimeline = memo(function PhaseTimeline({
  agentStatuses,
  selectedAuthor = "all",
  onFilterAuthor,
  running = false,
  done = null,
  className,
}: PhaseTimelineProps) {
  let completedStages = 0
  for (const st of PIPELINE_STAGES) {
    const { status } = getStageStatus(st, agentStatuses, done, running)
    if (status === "finished") completedStages++
  }

  return (
    <div className={cn("w-full rounded-lg border border-neutral-800 bg-neutral-950 p-3.5 space-y-3 font-sans shadow-md", className)}>
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-neutral-800 pb-2.5">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded bg-neutral-900 border border-neutral-800 text-emerald-400">
            <Layers className="h-3.5 w-3.5" />
          </div>
          <div>
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-100 flex items-center gap-2">
              <span>ALUR KERJA MESIN</span>
              <span className="text-[10px] text-neutral-500 font-normal">
                ({completedStages}/5 TAHAP SELESAI)
              </span>
            </h3>
          </div>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-3 text-[10px] font-mono text-neutral-400">
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-neutral-700" />
            <span>ANTRI</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-amber-400 animate-ping" />
            <span className="text-amber-300 font-bold">JALAN</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            <span className="text-emerald-300">SELESAI</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-rose-500" />
            <span className="text-rose-300">GAGAL</span>
          </span>
        </div>
      </div>

      {/* 5 Stages Grid / Horizontal Rail */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-2">
        {PIPELINE_STAGES.map((stage, idx) => {
          const { status } = getStageStatus(
            stage,
            agentStatuses,
            done,
            running
          )
          const StageIcon = stage.icon

          let borderClass = "border-neutral-800 bg-neutral-900/40 text-neutral-400"
          let statusPill = "bg-neutral-900 border-neutral-700 text-neutral-500"
          let statusLabel = "ANTRI"

          if (status === "running") {
            borderClass = "border-amber-700/80 bg-amber-950/20 text-neutral-100 ring-1 ring-amber-500/50"
            statusPill = "bg-amber-950 border-amber-700 text-amber-300 font-bold"
            statusLabel = "AKTIF"
          } else if (status === "finished") {
            borderClass = "border-emerald-800/80 bg-emerald-950/20 text-neutral-200"
            statusPill = "bg-emerald-950 border-emerald-700 text-emerald-300"
            statusLabel = "SELESAI"
          } else if (status === "error") {
            borderClass = "border-rose-800/80 bg-rose-950/30 text-rose-200"
            statusPill = "bg-rose-950 border-rose-700 text-rose-300 font-bold"
            statusLabel = "GAGAL"
          }

          return (
            <div
              key={stage.id}
              className={cn(
                "flex flex-col justify-between rounded-md border p-2.5 transition-all text-xs font-sans",
                borderClass
              )}
            >
              <div>
                {/* Stage Header */}
                <div className="flex items-start justify-between gap-1">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <div
                      className={cn(
                        "flex h-6 w-6 shrink-0 items-center justify-center rounded border text-[11px]",
                        status === "running"
                          ? "border-amber-700 bg-amber-950 text-amber-300"
                          : status === "finished"
                          ? "border-emerald-700 bg-emerald-950 text-emerald-300"
                          : status === "error"
                          ? "border-rose-700 bg-rose-950 text-rose-300"
                          : "border-neutral-800 bg-neutral-900 text-neutral-500"
                      )}
                    >
                      <StageIcon className="h-3 w-3" />
                    </div>
                    <div className="min-w-0">
                      <div className="text-[9px] font-mono font-medium uppercase tracking-wider text-neutral-500">
                        PHASE 0{stage.stageNumber}
                      </div>
                      <div className="text-xs font-bold font-mono tracking-tight text-neutral-200 truncate">
                        {stage.title.toUpperCase()}
                      </div>
                    </div>
                  </div>

                  <span
                    className={cn(
                      "rounded border px-1.5 py-0.2 text-[9px] font-mono",
                      statusPill
                    )}
                  >
                    {statusLabel}
                  </span>
                </div>

                {/* Subtitle */}
                <p className="mt-1.5 text-[10px] text-neutral-400 line-clamp-2 leading-tight">
                  {stage.description}
                </p>
              </div>

              {/* Subagents Chips */}
              <div className="mt-2.5 pt-2 border-t border-neutral-800/80 flex flex-wrap gap-1">
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
                        "flex items-center gap-1 rounded px-1.5 py-0.5 text-[9px] font-mono transition-colors border",
                        isSelected
                          ? "border-emerald-400 bg-emerald-950 text-emerald-200 font-bold"
                          : aStatus === "running"
                          ? "border-amber-700 bg-amber-950/80 text-amber-200 font-semibold"
                          : aStatus === "finished"
                          ? "border-neutral-700 bg-neutral-900 text-neutral-300 hover:border-neutral-500"
                          : "border-neutral-800/80 bg-neutral-950 text-neutral-500 hover:border-neutral-700"
                      )}
                      title={`${aMeta.title} (${aStatus}) - Click to filter events`}
                    >
                      {aStatus === "running" ? (
                        <Loader2 className="h-2 w-2 animate-spin text-amber-400" />
                      ) : aStatus === "finished" ? (
                        <CheckCircle2 className="h-2 w-2 text-emerald-400" />
                      ) : aStatus === "error" ? (
                        <AlertCircle className="h-2 w-2 text-rose-400" />
                      ) : (
                        <span className="h-1.5 w-1.5 rounded-full bg-neutral-700" />
                      )}
                      <span>{aMeta.shortLabel}</span>
                    </button>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
})
