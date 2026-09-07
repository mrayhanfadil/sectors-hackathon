import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
const badgeVariants = cva("inline-flex items-center rounded-md px-2.5 py-0.5 text-xs font-semibold transition-colors", {
  variants: { variant: { default: "bg-neutral-900 text-white dark:bg-neutral-100 dark:text-black", secondary: "bg-neutral-100 text-neutral-900 dark:bg-neutral-800 dark:text-neutral-100", outline: "border text-neutral-700 dark:text-neutral-300", success: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200", destructive: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200" } },
  defaultVariants: { variant: "default" },
})
export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}
function Badge({ className, variant, ...props }: BadgeProps) { return <div className={cn(badgeVariants({ variant }), className)} {...props} /> }
export { Badge, badgeVariants }
