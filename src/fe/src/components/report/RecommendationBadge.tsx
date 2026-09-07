import { TrendingUp, TrendingDown, Minus } from "lucide-react"

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

  const ratingStyles = isBuy
    ? "border-emerald-200 bg-emerald-50 text-emerald-700"
    : isSell
    ? "border-red-200 bg-red-50 text-red-700"
    : "border-neutral-200 bg-neutral-50 text-neutral-700"

  const upsideColor = isBuy ? "text-emerald-600" : isSell ? "text-red-600" : "text-neutral-500"

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
    sm: "text-[11px] px-1.5 py-px",
    md: "text-xs px-2 py-0.5",
    lg: "text-sm px-2.5 py-1 font-bold",
  }

  return (
    <div className={`inline-flex flex-wrap items-center gap-1.5 ${className}`}>
      <span
        className={`inline-flex items-center gap-1 rounded border font-semibold uppercase tracking-wide tabular-nums ${ratingStyles} ${sizeClasses[size]}`}
      >
        {isBuy && <TrendingUp className="h-3 w-3" />}
        {isSell && <TrendingDown className="h-3 w-3" />}
        {isHold && <Minus className="h-3 w-3" />}
        <span>{normRating}</span>
      </span>

      {showTarget && targetPrice != null && (
        <span
          className={`inline-flex items-center rounded border border-neutral-200 bg-white font-mono font-medium tabular-nums text-[#0a0a0a] ${sizeClasses[size]}`}
        >
          <span>TP Rp {fmtIDR(targetPrice)}</span>
          {formattedUpside && <span className={`ml-1 ${upsideColor}`}>({formattedUpside})</span>}
        </span>
      )}
    </div>
  )
}
