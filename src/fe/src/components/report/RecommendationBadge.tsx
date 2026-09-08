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
  const normRating = rating ? rating.trim().toUpperCase() : null
  const isBuy = normRating ? normRating.includes("BUY") || normRating.includes("OUTPERFORM") : false
  const isSell = normRating ? normRating.includes("SELL") || normRating.includes("UNDERPERFORM") : false
  const isHold = normRating ? !isBuy && !isSell : false

  const ratingStyles = isBuy
    ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-600 dark:border-emerald-500/50 dark:bg-emerald-950/40 dark:text-emerald-400"
    : isSell
    ? "border-rose-500/40 bg-rose-500/10 text-rose-600 dark:border-rose-500/50 dark:bg-rose-950/40 dark:text-rose-400"
    : isHold
    ? "border-amber-500/40 bg-amber-500/10 text-amber-700 dark:border-amber-500/50 dark:bg-amber-950/40 dark:text-amber-400"
    : "border-neutral-300 bg-neutral-100 text-neutral-600 dark:border-neutral-700 dark:bg-neutral-800/60 dark:text-neutral-400"

  const upsideColor = isBuy
    ? "text-emerald-600 dark:text-emerald-400"
    : isSell
    ? "text-rose-600 dark:text-rose-400"
    : "text-amber-600 dark:text-amber-400"

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
    sm: "text-[10px] px-1.5 py-0.5 tracking-wider",
    md: "text-xs px-2 py-0.5 tracking-wide",
    lg: "text-xs sm:text-sm px-2.5 py-1 font-bold tracking-wider",
  }

  const displayRating = normRating || "MENUNGGU"

  return (
    <div className={`inline-flex flex-wrap items-center gap-1.5 ${className}`}>
      <span
        className={`inline-flex items-center gap-1 rounded border font-mono font-bold uppercase tabular-nums ${ratingStyles} ${sizeClasses[size]}`}
      >
        {isBuy && <TrendingUp className="h-3 w-3 shrink-0" />}
        {isSell && <TrendingDown className="h-3 w-3 shrink-0" />}
        {isHold && <Minus className="h-3 w-3 shrink-0" />}
        <span>{displayRating}</span>
      </span>

      {showTarget && targetPrice != null && (
        <span
          className={`inline-flex items-center rounded border border-neutral-300 bg-neutral-50 font-mono font-medium tabular-nums text-neutral-900 ${sizeClasses[size]} dark:border-[#262930] dark:bg-[#121316] dark:text-neutral-200`}
        >
          <span>TP Rp {fmtIDR(targetPrice)}</span>
          {formattedUpside && <span className={`ml-1 font-semibold ${upsideColor}`}>({formattedUpside})</span>}
        </span>
      )}
    </div>
  )
}
