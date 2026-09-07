import { memo } from "react"
import {
  CheckCircle2,
  AlertCircle,
  Loader2,
  ChevronRight,
  Sparkles,
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

  // Also check subagents if any
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
  return (
    <div className={cn("w-full space-y-2.5", className)}>
      <div className="flex flex-wrap items-center justify-between gap-2 px-1 text-xs">
        <div className="flex items-center gap-1.5 font-medium text-neutral-700 dark:text-neutral-300">
          <Sparkles className="h-3.5 w-3.5 text-neutral-500" />
          <span>Alur Pipeline 5 Tahap AI</span>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-[11px] text-neutral-500 dark:text-neutral-400">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-neutral-300" />
            <span>Menunggu</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-amber-500" />
            <span>Sedang Berjalan</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            <span>Selesai</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-rose-500" />
            <span>Kendala</span>
          </span>
        </div>
      </div>

      <div className="overflow-x-auto pb-2 pt-0.5">
        <div className="flex min-w-[760px] items-stretch gap-2">
          {PIPELINE_STAGES.map((stage, idx) => {
            const { status, finishedCount, totalCount } = getStageStatus(
              stage,
              agentStatuses,
              done,
              running
            )
            const StageIcon = stage.icon
            const isLast = idx === PIPELINE_STAGES.length - 1

            let containerStyle = "border-neutral-200 bg-neutral-50/70 text-neutral-600 dark:border-neutral-800 dark:bg-neutral-900/70 dark:text-neutral-400"
            let badgeStyle = "bg-neutral-100 text-neutral-600 border-neutral-200 dark:bg-neutral-800 dark:text-neutral-300 dark:border-neutral-700"
            let statusText = "Menunggu"

            if (status === "running") {
              containerStyle = "border-amber-300 bg-amber-50/40 text-neutral-900 ring-1 ring-amber-300 dark:border-amber-800 dark:bg-amber-950/40 dark:text-neutral-100 dark:ring-amber-800"
              badgeStyle = "bg-amber-100 text-amber-900 border-amber-300 animate-pulse dark:bg-amber-950 dark:text-amber-200 dark:border-amber-800"
              statusText = "Berjalan"
            } else if (status === "finished") {
              containerStyle = "border-emerald-200 bg-emerald-50/30 text-neutral-900 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-neutral-100"
              badgeStyle = "bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-950 dark:text-emerald-200 dark:border-emerald-800"
              statusText = "Selesai"
            } else if (status === "error") {
              containerStyle = "border-rose-300 bg-rose-50/50 text-rose-900 dark:border-rose-800 dark:bg-rose-950/50 dark:text-rose-200"
              badgeStyle = "bg-rose-100 text-rose-800 border-rose-300 dark:bg-rose-950 dark:text-rose-200 dark:border-rose-800"
              statusText = "Gagal"
            }

            return (
              <div key={stage.id} className="flex flex-1 items-center gap-2">
                <div
                  className={cn(
                    "flex flex-1 flex-col justify-between rounded-md border p-3 shadow-2xs transition-all",
                    containerStyle
                  )}
                >
                  {/* Stage Header */}
                  <div>
                    <div className="flex items-center justify-between gap-1.5">
                      <div className="flex items-center gap-2">
                        <div
                          className={cn(
                            "flex h-7 w-7 items-center justify-center rounded-lg border",
                            status === "running"
                              ? "border-amber-300 bg-amber-100 text-amber-900 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200"
                              : status === "finished"
                              ? "border-emerald-300 bg-emerald-100 text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-200"
                              : status === "error"
                              ? "border-rose-300 bg-rose-100 text-rose-800 dark:border-rose-800 dark:bg-rose-950 dark:text-rose-200"
                              : "border-neutral-200 bg-white text-neutral-500 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-400"
                          )}
                        >
                          <StageIcon className="h-3.5 w-3.5" />
                        </div>
                        <div>
                          <div className="text-[10px] font-mono font-medium uppercase tracking-wider text-neutral-400 dark:text-neutral-500">
                            Tahap {stage.stageNumber}
                          </div>
                          <div className="text-xs font-semibold text-neutral-900 dark:text-neutral-100">
                            {stage.title}
                          </div>
                        </div>
                      </div>

                      <span
                        className={cn(
                          "rounded-full border px-2 py-0.5 text-[10px] font-medium",
                          badgeStyle
                        )}
                      >
                        {statusText}
                      </span>
                    </div>

                    {/* Stage Subtitle / Agents list */}
                    <div className="mt-2 text-[11px] leading-tight text-neutral-500 dark:text-neutral-400">
                      {stage.agentSubtitle}
                    </div>
                  </div>

                  {/* Sub-agents Indicator Badges */}
                  <div className="mt-3 flex flex-wrap items-center gap-1.5 pt-2 border-t border-neutral-200/60 dark:border-neutral-700/60">
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
                            "flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px] transition-all",
                            isSelected
                              ? "border-neutral-800 bg-neutral-900 text-white shadow-none dark:border-neutral-200 dark:bg-neutral-100 dark:text-neutral-900"
                              : aStatus === "running"
                              ? "border-amber-300 bg-white text-amber-900 font-medium dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200"
                              : aStatus === "finished"
                              ? "border-emerald-200 bg-white text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-200"
                              : "border-neutral-200 bg-white/80 text-neutral-600 hover:bg-white dark:border-neutral-700 dark:bg-neutral-900/80 dark:text-neutral-300 dark:hover:bg-neutral-900"
                          )}
                          title={`${aMeta.title} - Klik untuk memfilter aktivitas`}
                        >
                          {aStatus === "running" ? (
                            <Loader2 className="h-2.5 w-2.5 animate-spin text-amber-600" />
                          ) : aStatus === "finished" ? (
                            <CheckCircle2 className="h-2.5 w-2.5 text-emerald-600" />
                          ) : aStatus === "error" ? (
                            <AlertCircle className="h-2.5 w-2.5 text-rose-600" />
                          ) : (
                            <span className="h-1.5 w-1.5 rounded-full bg-neutral-300" />
                          )}
                          <span>{aMeta.shortLabel}</span>
                        </button>
                      )
                    })}
                  </div>
                </div>

                {!isLast && (
                  <ChevronRight className="h-4 w-4 shrink-0 text-neutral-300 dark:text-neutral-700" />
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
})
