import { memo } from "react"
import { CheckCircle2, AlertCircle, ChevronRight, Cpu, Loader2 } from "lucide-react"
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

const STATUS_LABELS: Record<AgentStatus, string> = {
  running: "Sedang diproses",
  finished: "Selesai",
  error: "Gagal",
  idle: "Menunggu",
}

export const AgentRail = memo(function AgentRail({
  agentStatuses,
  selectedAuthor = "all",
  onFilterAuthor,
  knownAgents = KNOWN_AGENTS,
  className,
}: AgentRailProps) {
  return (
    <div className={cn("w-full space-y-2 font-sans", className)}>
      <div className="flex items-center justify-between text-xs text-[#6B6659] dark:text-[#A8A296] px-1">
        <span className="font-medium text-[#1C1B17] dark:text-[#EDEAE3] flex items-center gap-1.5">
          <Cpu className="h-3.5 w-3.5 text-[#0E6E63] dark:text-[#4FD1B5]" />
          <span>Status seluruh agen</span>
        </span>
        <div className="flex items-center gap-3 text-[11px]">
          <span className="flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-[#6B6659] dark:bg-[#A8A296]" />
            <span>Menunggu</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-ping" />
            <span className="text-amber-800 dark:text-amber-300">Sedang diproses</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            <span className="text-emerald-800 dark:text-emerald-300">Selesai</span>
          </span>
        </div>
      </div>

      <div className="rounded-xl border border-[#E7E3DA] dark:border-[#2A2822] bg-white dark:bg-[#1B1A16] p-3">
        <div className="flex items-center gap-2 overflow-x-auto pb-1 pt-0.5">
          {knownAgents.map((agent, index) => {
            const status = agentStatuses[agent.key] || "idle"
            const isSelected = selectedAuthor === agent.key
            const showDivider =
              index === 4 || index === 5 || index === 10 || index === 13 || index === 14

            return (
              <div key={agent.key} className="flex items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => onFilterAuthor?.(isSelected ? "all" : agent.key)}
                  className={cn(
                    "flex flex-col items-start gap-0.5 rounded-lg border p-2 text-left transition-all cursor-pointer text-xs",
                    isSelected
                      ? "border-[#0E6E63] dark:border-[#4FD1B5] bg-[#0E6E63]/10 dark:bg-[#4FD1B5]/15 text-[#0E6E63] dark:text-[#4FD1B5]"
                      : status === "running"
                      ? "border-amber-200 dark:border-amber-800/60 bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300"
                      : status === "finished"
                      ? "border-[#E7E3DA] dark:border-[#2A2822] bg-white dark:bg-[#1B1A16] text-[#1C1B17] dark:text-[#EDEAE3] hover:border-[#0E6E63]/40"
                      : "border-[#E7E3DA] dark:border-[#2A2822] bg-[#FBFAF7] dark:bg-[#14130F] text-[#6B6659] dark:text-[#A8A296]"
                  )}
                  title={`${agent.label} (${agent.phase}) - ${STATUS_LABELS[status]}`}
                >
                  <div className="flex items-center gap-1.5 w-full justify-between">
                    <div className="flex items-center gap-1 min-w-0">
                      {status === "running" ? (
                        <Loader2 className="h-3 w-3 animate-spin text-amber-600 dark:text-amber-400 shrink-0" />
                      ) : status === "finished" ? (
                        <CheckCircle2 className="h-3 w-3 text-emerald-600 dark:text-emerald-400 shrink-0" />
                      ) : status === "error" ? (
                        <AlertCircle className="h-3 w-3 text-rose-600 dark:text-rose-400 shrink-0" />
                      ) : (
                        <span className="h-1.5 w-1.5 rounded-full bg-[#6B6659] dark:bg-[#A8A296] shrink-0" />
                      )}
                      <span className="font-medium truncate">
                        {agent.label}
                      </span>
                    </div>
                  </div>

                  <div className="text-[10px] text-[#6B6659] dark:text-[#A8A296]">
                    <span>{agent.phase}</span>
                  </div>
                </button>

                {showDivider && index < knownAgents.length - 1 && (
                  <ChevronRight className="h-3.5 w-3.5 text-[#6B6659]/50 dark:text-[#A8A296]/50 shrink-0" />
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
})
