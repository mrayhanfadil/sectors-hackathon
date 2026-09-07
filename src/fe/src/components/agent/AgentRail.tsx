import { memo } from "react"
import { CheckCircle2, AlertCircle, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"
import {
  KNOWN_AGENTS,
  type AgentMeta,
  type AgentStatus,
} from "./useAgentProgress"

export interface AgentRailProps {
  agentStatuses: Record<string, AgentStatus>
  selectedAuthor?: string
  onFilterAuthor?: (author: string) => void
  knownAgents?: AgentMeta[]
  className?: string
}

function StatusDot({ status }: { status: AgentStatus }) {
  if (status === "running") {
    return (
      <span className="relative flex h-2.5 w-2.5 items-center justify-center shrink-0">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
        <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-amber-500 shadow-none" />
      </span>
    )
  }

  if (status === "finished") {
    return (
      <span className="inline-flex h-2.5 w-2.5 items-center justify-center rounded-full bg-emerald-500 text-white shrink-0 shadow-none">
        <CheckCircle2 className="h-2 w-2" />
      </span>
    )
  }

  if (status === "error") {
    return (
      <span className="inline-flex h-2.5 w-2.5 items-center justify-center rounded-full bg-rose-600 text-white shrink-0 shadow-none">
        <AlertCircle className="h-2 w-2" />
      </span>
    )
  }

  // idle / queued
  return (
    <span className="h-2.5 w-2.5 rounded-full border border-neutral-300 bg-neutral-200 shrink-0" />
  )
}

function getStatusBadge(status: AgentStatus): { text: string; className: string } {
  switch (status) {
    case "running":
      return { text: "RUNNING", className: "bg-amber-100 text-amber-900 border-amber-300" }
    case "finished":
      return { text: "DONE", className: "bg-emerald-100 text-emerald-800 border-emerald-300" }
    case "error":
      return { text: "ERROR", className: "bg-rose-100 text-rose-800 border-rose-300" }
    default:
      return { text: "QUEUED", className: "bg-neutral-100 text-neutral-500 border-neutral-200" }
  }
}

export const AgentRail = memo(function AgentRail({
  agentStatuses,
  selectedAuthor = "all",
  onFilterAuthor,
  knownAgents = KNOWN_AGENTS,
  className,
}: AgentRailProps) {
  return (
    <div className={cn("w-full space-y-2", className)}>
      <div className="flex items-center justify-between px-1 text-xs text-neutral-500">
        <span className="font-medium tracking-wide uppercase text-[11px] text-neutral-600">
          Agent Status Rail
        </span>
        <div className="flex items-center gap-3 text-[11px]">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-neutral-300" />
            <span>Queued</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-amber-500" />
            <span>Running</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            <span>Finished</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-rose-600" />
            <span>Error</span>
          </span>
        </div>
      </div>

      <div className="relative rounded-lg border border-neutral-200 bg-neutral-50/60 p-2">
        <div className="flex items-center gap-2 overflow-x-auto pb-1 pt-0.5 scrollbar-thin">
          {knownAgents.map((agent, index) => {
            const status = agentStatuses[agent.key] || "idle"
            const isSelected = selectedAuthor === agent.key
            const badge = getStatusBadge(status)
            const showDivider =
              index === 4 || index === 5 || index === 10 || index === 13 || index === 14

            return (
              <div key={agent.key} className="flex items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => onFilterAuthor?.(agent.key)}
                  className={cn(
                    "group flex flex-col items-start gap-1 rounded-md border p-2 text-left transition-all",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neutral-900",
                    isSelected
                      ? "border-neutral-800 bg-white ring-2 ring-neutral-800 shadow-none"
                      : "border-neutral-200 bg-white hover:border-neutral-300 hover:bg-neutral-50 shadow-2xs",
                    status === "running" && !isSelected && "border-amber-300 bg-amber-50/40"
                  )}
                  title={`${agent.label} (${agent.phase}) - Click to filter timeline`}
                >
                  <div className="flex items-center gap-1.5 w-full justify-between">
                    <div className="flex items-center gap-1.5">
                      <StatusDot status={status} />
                      <span className="font-mono text-xs font-semibold text-neutral-800 tracking-tight">
                        {agent.label}
                      </span>
                    </div>
                    <span
                      className={cn(
                        "rounded border px-1 py-0.2 text-[9px] font-mono font-medium uppercase tracking-wider",
                        badge.className
                      )}
                    >
                      {badge.text}
                    </span>
                  </div>

                  <div className="flex items-center gap-1 text-[10px] text-neutral-500 font-medium">
                    <span>{agent.phase}</span>
                  </div>
                </button>

                {showDivider && index < knownAgents.length - 1 && (
                  <ChevronRight className="h-3.5 w-3.5 text-neutral-300 shrink-0" />
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
})
