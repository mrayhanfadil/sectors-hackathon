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
    ? "border-[#BCE2C9] bg-[#EBF6EE] text-[#157F3D] dark:border-[#157F3D]/40 dark:bg-[#157F3D]/20 dark:text-[#34D399]"
    : isSell
    ? "border-[#F8C8CB] bg-[#FDF2F2] text-[#B4232A] dark:border-[#B4232A]/40 dark:bg-[#B4232A]/20 dark:text-[#F87171]"
    : isHold
    ? "border-[#F6E3B8] bg-[#FEF9EE] text-[#A16207] dark:border-[#A16207]/40 dark:bg-[#A16207]/20 dark:text-[#FBBF24]"
    : "border-[#E7E3DA] bg-[#F4F1EA] text-[#6B6659] dark:border-[#2A2822] dark:bg-[#1B1A16] dark:text-[#A8A296]"

  const upsideColor = isBuy
    ? "text-[#157F3D] dark:text-[#34D399]"
    : isSell
    ? "text-[#B4232A] dark:text-[#F87171]"
    : "text-[#A16207] dark:text-[#FBBF24]"

  const formattedUpside = (() => {
    if (upside == null) return null
    if (typeof upside === "number") {
      return `${upside > 0 ? "+" : ""}${upside.toFixed(1)}%`
    }
    const str = String(upside).trim()
    if (!str || str === "-" || str === "-") return null
    return str
  })()

  const sizeClasses = {
    sm: "text-xs px-2 py-0.5 font-medium",
    md: "text-xs px-2.5 py-1 font-semibold",
    lg: "text-sm px-3 py-1.5 font-bold",
  }

  const displayRating = normRating || "MENUNGGU"

  return (
    <div className={`inline-flex flex-wrap items-center gap-1.5 ${className}`}>
      <span
        className={`inline-flex items-center gap-1.5 rounded-md border font-sans ${ratingStyles} ${sizeClasses[size]}`}
      >
        {isBuy && <TrendingUp className="h-3.5 w-3.5 shrink-0" />}
        {isSell && <TrendingDown className="h-3.5 w-3.5 shrink-0" />}
        {isHold && <Minus className="h-3.5 w-3.5 shrink-0" />}
        <span>{displayRating}</span>
      </span>

      {showTarget && targetPrice != null && (
        <span
          className={`inline-flex items-center rounded-md border border-[#E7E3DA] bg-[#FBFAF7] font-sans font-medium text-[#1C1B17] dark:border-[#2A2822] dark:bg-[#1B1A16] dark:text-[#EDEAE3] ${sizeClasses[size]}`}
        >
          <span>Nilai wajar Rp <span className="font-mono tabular-nums">{fmtIDR(targetPrice)}</span></span>
          {formattedUpside && (
            <span className={`ml-1 font-semibold font-mono tabular-nums ${upsideColor}`}>
              ({formattedUpside})
            </span>
          )}
        </span>
      )}
    </div>
  )
}
