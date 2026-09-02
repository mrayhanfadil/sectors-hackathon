import { TrendingUp, TrendingDown, Minus } from "lucide-react"
import { Badge } from "@/components/ui/badge"

export interface RecommendationBadgeProps {
  rating?: string | null
  targetPrice?: number | null
  upside?: string | number | null
  size?: "sm" | "md" | "lg"
  showTarget?: boolean
  className?: string
}

function fmtIDR(n: number | null | undefined): string {
  if (n == null || Number.isNaN(Number(n))) return "-"
  return Number(n).toLocaleString("id-ID")
}

export function RecommendationBadge({
  rating,
  targetPrice,
  upside,
  size = "md",
  showTarget = false,
  className = "",
}: RecommendationBadgeProps) {
  const normRating = (rating || "HOLD").toUpperCase()
  const isBuy = normRating.includes("BUY")
  const isSell = normRating.includes("SELL")
  const isHold = !isBuy && !isSell

  const ratingVariant = isBuy ? "success" : isSell ? "destructive" : "secondary"
  
  const formattedUpside = (() => {
    if (upside == null) return null
    if (typeof upside === "number") {
      return `${upside > 0 ? "+" : ""}${upside.toFixed(1)}%`
    }
    const str = String(upside).trim()
    if (!str || str === "-") return null
    return str
  })()

  const sizeClasses = {
    sm: "text-[11px] px-2 py-0.5",
    md: "text-xs px-2.5 py-1",
    lg: "text-sm px-3 py-1.5 font-bold",
  }

  return (
    <div className={`inline-flex flex-wrap items-center gap-1.5 ${className}`}>
      <Badge variant={ratingVariant} className={`${sizeClasses[size]} gap-1 tracking-wide uppercase`}>
        {isBuy && <TrendingUp className="h-3 w-3" />}
        {isSell && <TrendingDown className="h-3 w-3" />}
        {isHold && <Minus className="h-3 w-3" />}
        <span>{normRating}</span>
      </Badge>

      {showTarget && targetPrice != null && (
        <Badge variant="outline" className={`${sizeClasses[size]} font-mono font-medium text-slate-700 bg-white`}>
          <span>TP Rp {fmtIDR(targetPrice)}</span>
          {formattedUpside && (
            <span className={`ml-1 ${isBuy ? "text-emerald-600" : isSell ? "text-red-600" : "text-slate-600"}`}>
              ({formattedUpside})
            </span>
          )}
        </Badge>
      )}
    </div>
  )
}
