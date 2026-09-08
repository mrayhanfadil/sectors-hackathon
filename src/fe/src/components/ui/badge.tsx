import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
const badgeVariants = cva(
  "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default: "bg-neutral-900 text-white dark:bg-neutral-100 dark:text-black",
        secondary: "bg-neutral-100 text-neutral-800 border border-neutral-200 dark:bg-neutral-800/80 dark:text-neutral-200 dark:border-neutral-700",
        outline: "border border-neutral-300 text-neutral-700 dark:border-[#262930] dark:text-neutral-300",
        success: "border border-emerald-500/30 bg-emerald-50 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800",
        destructive: "border border-rose-500/30 bg-rose-50 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 dark:border-rose-800",
      },
    },
    defaultVariants: { variant: "default" },
  }
)
export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}
function Badge({ className, variant, ...props }: BadgeProps) { return <div className={cn(badgeVariants({ variant }), className)} {...props} /> }
export { Badge, badgeVariants }
