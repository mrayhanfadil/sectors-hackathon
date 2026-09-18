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
      <div className="flex items-center justify-between text-xs text-[#666666] dark:text-[#666666] px-1">
        <span className="font-medium text-[#333333] dark:text-[#f1f5f9] flex items-center gap-1.5">
          <Cpu className="h-3.5 w-3.5 text-[#0928B1] dark:text-[#7596FF]" />
          <span>Status seluruh agen</span>
        </span>
        <div className="flex items-center gap-3 text-[11px]">
          <span className="flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-[#666666] dark:bg-[#666666]" />
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

      <div className="rounded-xl border border-[#D9D9D9] dark:border-[#262930] bg-white dark:bg-[#090a0c] p-3">
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
                      ? "border-[#0928B1] dark:border-[#7596FF] bg-[#0928B1]/10 dark:bg-[#7596FF]/15 text-[#0928B1] dark:text-[#7596FF]"
                      : status === "running"
                      ? "border-amber-200 dark:border-amber-800/60 bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300"
                      : status === "finished"
                      ? "border-[#D9D9D9] dark:border-[#262930] bg-white dark:bg-[#090a0c] text-[#333333] dark:text-[#f1f5f9] hover:border-[#0928B1]/40"
                      : "border-[#D9D9D9] dark:border-[#262930] bg-[#f1f5f9] dark:bg-[#1e2229] text-[#666666] dark:text-[#666666]"
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
                        <span className="h-1.5 w-1.5 rounded-full bg-[#666666] dark:bg-[#666666] shrink-0" />
                      )}
                      <span className="font-medium truncate">
                        {agent.label}
                      </span>
                    </div>
                  </div>

                  <div className="text-[10px] text-[#666666] dark:text-[#666666]">
                    <span>{agent.phase}</span>
                  </div>
                </button>

                {showDivider && index < knownAgents.length - 1 && (
                  <ChevronRight className="h-3.5 w-3.5 text-[#666666]/50 dark:text-[#666666]/50 shrink-0" />
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
})
