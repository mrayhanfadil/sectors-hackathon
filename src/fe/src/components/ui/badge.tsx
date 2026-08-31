import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center gap-1 font-mono text-[11px] font-semibold tracking-wide uppercase px-2 py-0.5 rounded border transition-colors",
  {
    variants: {
      variant: {
        default: "bg-[#181b22] text-amber-400 border-amber-500/30",
        secondary: "bg-[#161920] text-slate-300 border-slate-700/60",
        outline: "bg-transparent text-slate-400 border-slate-700/80",
        amber: "bg-amber-500/15 text-amber-300 border-amber-500/40",
        success: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
        destructive: "bg-red-500/15 text-red-300 border-red-500/40",
        buy: "bg-emerald-500 text-black font-bold border-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.3)]",
        hold: "bg-amber-500 text-black font-bold border-amber-400 shadow-[0_0_12px_rgba(245,158,11,0.3)]",
        sell: "bg-red-500 text-white font-bold border-red-400 shadow-[0_0_12px_rgba(239,68,68,0.3)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
