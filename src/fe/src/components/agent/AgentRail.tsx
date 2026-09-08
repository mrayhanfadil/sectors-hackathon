import { memo } from "react"
import { CheckCircle2, AlertCircle, ChevronRight, Cpu } from "lucide-react"
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
      <span className="relative flex h-2 w-2 items-center justify-center shrink-0">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
        <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-500 shadow-none" />
      </span>
    )
  }

  if (status === "finished") {
    return (
      <span className="inline-flex h-2 w-2 items-center justify-center rounded-full bg-emerald-500 text-black shrink-0 shadow-none">
        <CheckCircle2 className="h-2 w-2" />
      </span>
    )
  }

  if (status === "error") {
    return (
      <span className="inline-flex h-2 w-2 items-center justify-center rounded-full bg-rose-500 text-white shrink-0 shadow-none">
        <AlertCircle className="h-2 w-2" />
      </span>
    )
  }

  // idle / queued
  return (
    <span className="h-2 w-2 rounded-full bg-neutral-700 shrink-0" />
  )
}

function getStatusBadge(status: AgentStatus): { text: string; className: string } {
  switch (status) {
    case "running":
      return { text: "RUNNING", className: "bg-amber-950 border-amber-800 text-amber-300 font-bold" }
    case "finished":
      return { text: "DONE", className: "bg-emerald-950 border-emerald-800 text-emerald-300" }
    case "error":
      return { text: "FAIL", className: "bg-rose-950 border-rose-800 text-rose-300 font-bold" }
    default:
      return { text: "QUEUED", className: "bg-neutral-900 border-neutral-800 text-neutral-500" }
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
    <div className={cn("w-full space-y-1.5 font-mono", className)}>
      <div className="flex items-center justify-between px-1 text-[10px] text-neutral-400">
        <span className="font-bold tracking-wider uppercase text-neutral-300 flex items-center gap-1.5">
          <Cpu className="h-3 w-3 text-emerald-400" />
          <span>AGENT MESH STATUS RAIL</span>
        </span>
        <div className="flex items-center gap-2.5 text-[9px]">
          <span className="flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-neutral-700" />
            <span>QUEUED</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-ping" />
            <span className="text-amber-300">RUNNING</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            <span className="text-emerald-300">DONE</span>
          </span>
        </div>
      </div>

      <div className="rounded-lg border border-neutral-800 bg-neutral-950 p-2 shadow-inner">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 pt-0.5 scrollbar-thin">
          {knownAgents.map((agent, index) => {
            const status = agentStatuses[agent.key] || "idle"
            const isSelected = selectedAuthor === agent.key
            const badge = getStatusBadge(status)
            const showDivider =
              index === 4 || index === 5 || index === 10 || index === 13 || index === 14

            return (
              <div key={agent.key} className="flex items-center gap-1.5 shrink-0">
                <button
                  type="button"
                  onClick={() => onFilterAuthor?.(agent.key)}
                  className={cn(
                    "group flex flex-col items-start gap-0.5 rounded border p-1.5 text-left transition-all cursor-pointer",
                    "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-emerald-400",
                    isSelected
                      ? "border-emerald-500 bg-neutral-900 ring-1 ring-emerald-500 shadow-sm"
                      : "border-neutral-800 bg-neutral-950 hover:border-neutral-700 hover:bg-neutral-900/60",
                    status === "running" && !isSelected && "border-amber-700 bg-amber-950/30"
                  )}
                  title={`${agent.label} (${agent.phase}) - Click to filter transcript`}
                >
                  <div className="flex items-center gap-1.5 w-full justify-between">
                    <div className="flex items-center gap-1 min-w-0">
                      <StatusDot status={status} />
                      <span className="font-mono text-[11px] font-bold text-neutral-200 tracking-tight truncate">
                        {agent.label}
                      </span>
                    </div>
                    <span
                      className={cn(
                        "rounded border px-1 py-0.2 text-[8px] font-mono uppercase tracking-wider ml-1",
                        badge.className
                      )}
                    >
                      {badge.text}
                    </span>
                  </div>

                  <div className="flex items-center gap-1 text-[9px] text-neutral-500">
                    <span>{agent.phase}</span>
                  </div>
                </button>

                {showDivider && index < knownAgents.length - 1 && (
                  <ChevronRight className="h-3 w-3 text-neutral-700 shrink-0" />
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
})
