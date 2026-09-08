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

  // Collapse aggressively by default: only auto-expand running step or first unfinished
  const defaultStageId = firstRunningId ?? (done ? null : firstUnfinishedId ?? PIPELINE_STAGES[0].id)
  const [expandedId, setExpandedId] = useState<string | null>(() => defaultStageId)

  // Track running stage changes so the active step auto-expands as pipeline progresses
  const prevRunningRef = useRef<string | null>(null)
  useEffect(() => {
    if (running && firstRunningId && firstRunningId !== prevRunningRef.current) {
      setExpandedId(firstRunningId)
      prevRunningRef.current = firstRunningId
    }
  }, [running, firstRunningId])

  // When run completes, collapse all by default for a clean summary
  const prevDoneRef = useRef<typeof done>(done)
  useEffect(() => {
    if (done !== null && prevDoneRef.current === null) {
      setExpandedId(null)
    }
    prevDoneRef.current = done
  }, [done])

  // If user selected an author externally, expand the stage containing that agent
  useEffect(() => {
    if (selectedAuthor && selectedAuthor !== "all") {
      const matched = PIPELINE_STAGES.find((st) => st.allAgents.includes(selectedAuthor))
      if (matched) {
        setExpandedId(matched.id)
      }
    }
  }, [selectedAuthor])

  const globalStatus = done !== null ? "SELESAI" : running ? "JALAN" : "SIAGA"

  return (
    <div className={cn("w-full rounded-lg border border-neutral-800 bg-neutral-950 p-4 font-sans shadow-md", className)}>
      {/* Header: title + global status + progress bar */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-neutral-900 border border-neutral-800 text-emerald-400">
            <Layers className="h-4 w-4" />
          </div>
          <div className="min-w-0">
            <h3 className="text-sm font-bold text-neutral-100 truncate">
              Alur kerja mesin
            </h3>
            <p className="text-xs text-neutral-400">
              {completedStages}/{PIPELINE_STAGES.length} tahap selesai
            </p>
          </div>
        </div>
        <span
          className={cn(
            "shrink-0 rounded-full border px-3 py-1 text-xs font-bold",
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
            "h-full rounded-full transition-all duration-300",
            globalStatus === "JALAN" ? "bg-amber-400" : "bg-emerald-400"
          )}
          style={{ width: `${(completedStages / PIPELINE_STAGES.length) * 100}%` }}
        />
      </div>

      {/* Vertical Stepper Timeline */}
      <div className="mt-4 space-y-2.5">
        {PIPELINE_STAGES.map((stage, idx) => {
          const { status, finishedCount, totalCount } = getStageStatus(
            stage,
            agentStatuses,
            done,
            running
          )
          const isExpanded = expandedId === stage.id
          const isLast = idx === PIPELINE_STAGES.length - 1

          let ringClass = "border-neutral-700 bg-neutral-900 text-neutral-400"
          let pillClass = "bg-neutral-900 border-neutral-700 text-neutral-400 font-medium"
          let statusLabel = "ANTRI"

          if (status === "running") {
            ringClass = "border-amber-500 bg-amber-950 text-amber-200 ring-2 ring-amber-500/20 shadow-sm shadow-amber-950"
            pillClass = "bg-amber-950/90 border-amber-700/80 text-amber-200 font-bold"
            statusLabel = "JALAN"
          } else if (status === "finished") {
            ringClass = "border-emerald-600 bg-emerald-950 text-emerald-300 shadow-sm shadow-emerald-950"
            pillClass = "bg-emerald-950/80 border-emerald-700/80 text-emerald-300 font-medium"
            statusLabel = "SELESAI"
          } else if (status === "error") {
            ringClass = "border-rose-600 bg-rose-950 text-rose-200 shadow-sm shadow-rose-950"
            pillClass = "bg-rose-950/90 border-rose-700/80 text-rose-200 font-bold"
            statusLabel = "GAGAL"
          }

          // Combined list of primary agents and any active subagents
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
              {/* Left rail with node circle + vertical connecting line */}
              <div className="relative flex flex-col items-center shrink-0 w-8">
                <div
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-full border text-xs font-bold transition-all z-10",
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
                {!isLast && (
                  <div
                    className={cn(
                      "w-0.5 grow min-h-4 my-1 transition-colors",
                      status === "finished" ? "bg-emerald-800/60" : "bg-neutral-800"
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
                    ? "border-amber-700/70 bg-amber-950/20"
                    : status === "finished"
                    ? "border-emerald-800/50 bg-emerald-950/15"
                    : status === "error"
                    ? "border-rose-800/60 bg-rose-950/20"
                    : "border-neutral-800/90 bg-neutral-900/40 hover:border-neutral-700"
                )}
              >
                {/* Row Header - Clickable toggle button */}
                <button
                  type="button"
                  onClick={() => setExpandedId(isExpanded ? null : stage.id)}
                  className="w-full flex items-center justify-between gap-3 p-3 text-left transition-colors rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-600"
                  aria-expanded={isExpanded}
                  title={isExpanded ? "Ketuk untuk ringkas" : "Ketuk untuk rincian tahap ini"}
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-bold text-neutral-100">
                        {stage.title}
                      </span>
                      <span
                        className={cn(
                          "inline-flex items-center gap-1 rounded px-2 py-0.5 text-[11px] font-mono border",
                          pillClass
                        )}
                      >
                        {status === "running" && (
                          <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
                        )}
                        {statusLabel}
                      </span>
                    </div>
                    <div className="mt-0.5 text-xs text-neutral-400">
                      {finishedCount}/{totalCount} mesin · {STATUS_ID[status] || status}
                    </div>
                  </div>

                  <div className="flex items-center gap-1 shrink-0 text-neutral-400">
                    <ChevronDown
                      className={cn(
                        "h-4 w-4 text-neutral-400 transition-transform duration-200",
                        isExpanded && "rotate-180"
                      )}
                    />
                  </div>
                </button>

                {/* Expanded content */}
                {isExpanded && (
                  <div className="border-t border-neutral-800/80 p-3 pt-2.5 space-y-2.5">
                    <p className="text-xs leading-relaxed text-neutral-300">
                      {stage.description}
                    </p>

                    <div>
                      <div className="text-[11px] font-mono text-neutral-500 uppercase tracking-wider mb-1.5">
                        Mesin Terlibat ({displayAgents.length}):
                      </div>
                      <div className="flex flex-wrap gap-2">
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
                                  ? "border-emerald-400 bg-emerald-950 text-emerald-200 font-bold ring-1 ring-emerald-500/30"
                                  : aStatus === "running"
                                  ? "border-amber-700 bg-amber-950/80 text-amber-200 font-semibold"
                                  : aStatus === "finished"
                                  ? "border-neutral-700 bg-neutral-900 text-neutral-300 hover:border-neutral-500 hover:text-white"
                                  : "border-neutral-800 bg-neutral-950 text-neutral-400 hover:border-neutral-700 hover:text-neutral-300"
                              )}
                              title={`${aMeta.title} (${STATUS_ID[aStatus] ?? aStatus}) — klik untuk saring catatan`}
                            >
                              {aStatus === "running" ? (
                                <Loader2 className="h-3 w-3 animate-spin text-amber-400 shrink-0" />
                              ) : aStatus === "finished" ? (
                                <CheckCircle2 className="h-3 w-3 text-emerald-400 shrink-0" />
                              ) : aStatus === "error" ? (
                                <AlertCircle className="h-3 w-3 text-rose-400 shrink-0" />
                              ) : (
                                <span className="h-1.5 w-1.5 rounded-full bg-neutral-600 shrink-0" />
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

      <p className="mt-3 text-xs text-neutral-500">
        Ketuk tiap tahap untuk melihat mesin di dalamnya · ketuk nama mesin untuk menyaring catatan langkah.
      </p>
    </div>
  )
})
