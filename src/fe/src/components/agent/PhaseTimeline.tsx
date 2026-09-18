import { memo, useState, useEffect, useRef } from "react"
import {
  CheckCircle2,
  AlertCircle,
  Loader2,
  ChevronDown,
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

  // Check subagents
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

const STATUS_LABELS: Record<string, string> = {
  running: "Sedang diproses",
  finished: "Selesai",
  error: "Gagal",
  idle: "Menunggu",
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
  let firstUnfinishedId: string | null = null

  for (const st of PIPELINE_STAGES) {
    const { status } = getStageStatus(st, agentStatuses, done, running)
    if (status === "finished") {
      completedStages++
    } else if (!firstUnfinishedId) {
      firstUnfinishedId = st.id
    }
    if (status === "running" && firstRunningId === null) {
      firstRunningId = st.id
    }
  }

  const defaultStageId = firstRunningId ?? (done ? null : firstUnfinishedId ?? PIPELINE_STAGES[0].id)
  const [expandedId, setExpandedId] = useState<string | null>(() => defaultStageId)

  const prevRunningRef = useRef<string | null>(null)
  useEffect(() => {
    if (running && firstRunningId && firstRunningId !== prevRunningRef.current) {
      setExpandedId(firstRunningId)
      prevRunningRef.current = firstRunningId
    }
  }, [running, firstRunningId])

  const prevDoneRef = useRef<typeof done>(done)
  useEffect(() => {
    if (done !== null && prevDoneRef.current === null) {
      setExpandedId(null)
    }
    prevDoneRef.current = done
  }, [done])

  useEffect(() => {
    if (selectedAuthor && selectedAuthor !== "all") {
      const matched = PIPELINE_STAGES.find((st) => st.allAgents.includes(selectedAuthor))
      if (matched) {
        setExpandedId(matched.id)
      }
    }
  }, [selectedAuthor])

  const globalStatus = done !== null ? "Selesai" : running ? "Sedang diproses" : "Siaga"

  return (
    <div className={cn("w-full rounded-xl border border-[#D9D9D9] dark:border-[#262930] bg-white dark:bg-[#090a0c] p-5 sm:p-6 font-sans shadow-none", className)}>
      {/* Header */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#B4C7FF] dark:bg-[#1e2229] text-[#0928B1] dark:text-[#7596FF] border border-[#D9D9D9] dark:border-[#262930]">
            <Layers className="h-4 w-4" />
          </div>
          <div className="min-w-0">
            <h2 className="font-serif text-lg font-medium text-[#333333] dark:text-[#f1f5f9] truncate">
              Tahapan alur kerja
            </h2>
            <p className="text-xs text-[#666666] dark:text-[#666666]">
              {completedStages} dari {PIPELINE_STAGES.length} tahap selesai
            </p>
          </div>
        </div>

        <span
          className={cn(
            "shrink-0 rounded-full border px-3 py-1 text-xs font-medium",
            globalStatus === "Sedang diproses"
              ? "border-amber-200 dark:border-amber-800/60 bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300"
              : globalStatus === "Selesai"
              ? "border-emerald-200 dark:border-emerald-800/60 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300"
              : "border-[#D9D9D9] dark:border-[#262930] bg-[#B4C7FF] dark:bg-[#1e2229] text-[#666666] dark:text-[#666666]"
          )}
        >
          {globalStatus === "Sedang diproses" ? (
            <span className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse" />
              Sedang diproses
            </span>
          ) : (
            globalStatus
          )}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-[#B4C7FF] dark:bg-[#1e2229]">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-300",
            globalStatus === "Sedang diproses" ? "bg-amber-500" : "bg-[#0928B1] dark:bg-[#7596FF]"
          )}
          style={{ width: `${(completedStages / PIPELINE_STAGES.length) * 100}%` }}
        />
      </div>

      {/* Vertical Stepper Timeline */}
      <div className="mt-5 space-y-3">
        {PIPELINE_STAGES.map((stage, idx) => {
          const { status, finishedCount, totalCount } = getStageStatus(
            stage,
            agentStatuses,
            done,
            running
          )
          const isExpanded = expandedId === stage.id
          const isLast = idx === PIPELINE_STAGES.length - 1

          let ringClass = "border-[#D9D9D9] dark:border-[#262930] bg-[#B4C7FF] dark:bg-[#1e2229] text-[#666666] dark:text-[#666666]"
          let pillClass = "bg-[#B4C7FF] dark:bg-[#1e2229] border-[#D9D9D9] dark:border-[#262930] text-[#666666] dark:text-[#666666]"
          const statusText = STATUS_LABELS[status] || "Menunggu"

          if (status === "running") {
            ringClass = "border-amber-400 dark:border-amber-600 bg-amber-50 dark:bg-amber-950/60 text-amber-800 dark:text-amber-200"
            pillClass = "bg-amber-50 dark:bg-amber-950/60 border-amber-200 dark:border-amber-800/60 text-amber-800 dark:text-amber-300 font-medium"
          } else if (status === "finished") {
            ringClass = "border-emerald-300 dark:border-emerald-700 bg-emerald-50 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300"
            pillClass = "bg-emerald-50 dark:bg-emerald-950/60 border-emerald-200 dark:border-emerald-800/60 text-emerald-800 dark:text-emerald-300 font-medium"
          } else if (status === "error") {
            ringClass = "border-rose-300 dark:border-rose-700 bg-rose-50 dark:bg-rose-950/60 text-rose-800 dark:text-rose-200"
            pillClass = "bg-rose-50 dark:bg-rose-950/60 border-rose-200 dark:border-rose-800/60 text-rose-800 dark:text-rose-200 font-medium"
          }

          const displayAgents = Array.from(
            new Set([
              ...stage.primaryAgents,
              ...stage.allAgents.filter(
                (k) =>
                  agentStatuses[k] === "running" ||
                  agentStatuses[k] === "finished" ||
                  agentStatuses[k] === "error" ||
                  selectedAuthor === k
              ),
            ])
          )

          return (
            <div key={stage.id} className="relative flex items-stretch gap-3">
              {/* Left rail */}
              <div className="relative flex flex-col items-center shrink-0 w-8">
                <div
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-full border text-xs font-medium transition-all z-10",
                    ringClass
                  )}
                >
                  {status === "finished" ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                  ) : status === "running" ? (
                    <Loader2 className="h-4 w-4 animate-spin text-amber-600 dark:text-amber-400" />
                  ) : status === "error" ? (
                    <AlertCircle className="h-4 w-4 text-rose-600 dark:text-rose-400" />
                  ) : (
                    <span>{stage.stageNumber}</span>
                  )}
                </div>
                {!isLast && (
                  <div
                    className={cn(
                      "w-px grow min-h-4 my-1 transition-colors",
                      status === "finished" ? "bg-emerald-300 dark:bg-emerald-800" : "bg-[#D9D9D9] dark:bg-[#262930]"
                    )}
                    aria-hidden="true"
                  />
                )}
              </div>

              {/* Right step card */}
              <div
                className={cn(
                  "flex-1 min-w-0 rounded-lg border transition-colors",
                  status === "running"
                    ? "border-amber-200 dark:border-amber-800/40 bg-amber-50/30 dark:bg-amber-950/10"
                    : status === "finished"
                    ? "border-emerald-200/80 dark:border-emerald-800/30 bg-emerald-50/20 dark:bg-emerald-950/10"
                    : status === "error"
                    ? "border-rose-200 dark:border-rose-800/40 bg-rose-50/30 dark:bg-rose-950/10"
                    : "border-[#D9D9D9] dark:border-[#262930] bg-[#f1f5f9]/50 dark:bg-[#090a0c]/50 hover:border-[#0928B1]/30"
                )}
              >
                {/* Row Header */}
                <button
                  type="button"
                  onClick={() => setExpandedId(isExpanded ? null : stage.id)}
                  className="w-full flex items-center justify-between gap-3 p-3.5 text-left transition-colors rounded-lg focus:outline-none"
                  aria-expanded={isExpanded}
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-medium text-[#333333] dark:text-[#f1f5f9]">
                        {stage.title}
                      </span>
                      <span
                        className={cn(
                          "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] border",
                          pillClass
                        )}
                      >
                        {status === "running" && (
                          <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse" />
                        )}
                        {statusText}
                      </span>
                    </div>
                    <div className="mt-0.5 text-xs text-[#666666] dark:text-[#666666]">
                      {finishedCount} dari {totalCount} agen selesai
                    </div>
                  </div>

                  <div className="flex items-center gap-1 shrink-0 text-[#666666] dark:text-[#666666]">
                    <ChevronDown
                      className={cn(
                        "h-4 w-4 text-[#666666] dark:text-[#666666] transition-transform duration-200",
                        isExpanded && "rotate-180"
                      )}
                    />
                  </div>
                </button>

                {/* Expanded content */}
                {isExpanded && (
                  <div className="border-t border-[#D9D9D9] dark:border-[#262930] p-3.5 pt-3 space-y-3">
                    <p className="text-xs leading-relaxed text-[#666666] dark:text-[#666666]">
                      {stage.description}
                    </p>

                    <div>
                      <div className="text-[11px] font-medium text-[#666666] dark:text-[#666666] mb-1.5">
                        Agen terlibat:
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {displayAgents.map((aKey) => {
                          const aMeta = getFriendlyAgent(aKey)
                          const aStatus = done !== null ? "finished" : (agentStatuses[aKey] || "idle")
                          const isSelected = selectedAuthor === aKey

                          return (
                            <button
                              key={aKey}
                              type="button"
                              onClick={() => onFilterAuthor?.(isSelected ? "all" : aKey)}
                              className={cn(
                                "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs transition-colors border select-none",
                                isSelected
                                  ? "border-[#0928B1] dark:border-[#7596FF] bg-[#0928B1]/10 dark:bg-[#7596FF]/20 text-[#0928B1] dark:text-[#7596FF] font-medium"
                                  : aStatus === "running"
                                  ? "border-amber-200 dark:border-amber-800/60 bg-amber-50 dark:bg-amber-950/50 text-amber-800 dark:text-amber-300 font-medium"
                                  : aStatus === "finished"
                                  ? "border-[#D9D9D9] dark:border-[#262930] bg-white dark:bg-[#090a0c] text-[#333333] dark:text-[#f1f5f9] hover:border-[#0928B1]/40"
                                  : "border-[#D9D9D9] dark:border-[#262930] bg-[#B4C7FF] dark:bg-[#1e2229] text-[#666666] dark:text-[#666666]"
                              )}
                              title={`${aMeta.title} (${STATUS_LABELS[aStatus] ?? aStatus}) - saring catatan`}
                            >
                              {aStatus === "running" ? (
                                <Loader2 className="h-3 w-3 animate-spin text-amber-600 dark:text-amber-400 shrink-0" />
                              ) : aStatus === "finished" ? (
                                <CheckCircle2 className="h-3 w-3 text-emerald-600 dark:text-emerald-400 shrink-0" />
                              ) : aStatus === "error" ? (
                                <AlertCircle className="h-3 w-3 text-rose-600 dark:text-rose-400 shrink-0" />
                              ) : (
                                <span className="h-1.5 w-1.5 rounded-full bg-[#666666] dark:bg-[#666666] shrink-0" />
                              )}
                              <span>{aMeta.shortLabel}</span>
                            </button>
                          )
                        })}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      <p className="mt-4 text-xs text-[#666666] dark:text-[#666666]">
        Klik nama agen untuk menyaring catatan langkah alur kerja di bawah.
      </p>
    </div>
  )
})
