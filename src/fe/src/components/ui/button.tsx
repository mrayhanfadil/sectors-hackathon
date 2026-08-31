import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-xs font-medium transition-all focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-amber-400 disabled:pointer-events-none disabled:opacity-50 cursor-pointer",
  {
    variants: {
      variant: {
        default: "bg-amber-500 text-black font-semibold hover:bg-amber-400 shadow-sm",
        charcoal: "bg-[#181c24] text-slate-200 border border-slate-700 hover:bg-[#202530] hover:text-white",
        outline: "border border-slate-700 bg-transparent text-slate-300 hover:bg-slate-800/80 hover:text-white",
        ghost: "text-slate-300 hover:bg-slate-800/60 hover:text-white",
        secondary: "bg-slate-800 text-slate-200 hover:bg-slate-700",
        destructive: "bg-red-500/20 text-red-300 border border-red-500/40 hover:bg-red-500/30",
        emerald: "bg-emerald-500 text-black font-semibold hover:bg-emerald-400",
      },
      size: {
        default: "h-8 px-3 py-1.5",
        sm: "h-7 rounded px-2.5 text-[11px]",
        lg: "h-10 rounded-md px-5 text-sm",
        icon: "h-8 w-8",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button
      className={cn(buttonVariants({ variant, size, className }))}
      ref={ref}
      {...props}
    />
  )
)
Button.displayName = "Button"

export { Button, buttonVariants }
