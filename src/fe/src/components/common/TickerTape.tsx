import { useQuery } from "@tanstack/react-query"
import { fetchUniverse } from "@/lib/api"
import { TrendingUp, TrendingDown } from "lucide-react"

export function TickerTape() {
  const { data: universe } = useQuery({
    queryKey: ["universe"],
    queryFn: fetchUniverse,
  })

  if (!universe || universe.length === 0) return null

  // Take top 18 tickers for tape
  const items = universe.slice(0, 18)

  return (
    <div className="border-b border-[#1b2029] bg-[#0b0d10] py-1 text-[11px] font-mono overflow-hidden select-none">
      <div className="flex items-center">
        <div className="flex items-center gap-1.5 px-3 font-sans font-semibold text-amber-400 shrink-0 border-r border-[#1b2029] bg-[#0b0d10] z-10">
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>IDX COMPOSITE</span>
          <span className="text-slate-200">7,850.4</span>
          <span className="text-emerald-400 text-[10px]">+0.42%</span>
        </div>

        <div className="flex items-center gap-6 overflow-x-auto no-scrollbar whitespace-nowrap pl-4 py-0.5">
          {items.map((item) => {
            const isPos = item.changePct >= 0
            return (
              <a
                key={item.ticker}
                href={`/report/${item.ticker}`}
                className="flex items-center gap-1.5 text-slate-300 hover:text-amber-300 transition-colors"
              >
                <span className="font-semibold text-slate-200">{item.ticker}</span>
                <span className="text-slate-400">{item.lastPrice.toLocaleString("id-ID")}</span>
                <span
                  className={`flex items-center text-[10px] ${
                    isPos ? "text-emerald-400" : "text-red-400"
                  }`}
                >
                  {isPos ? (
                    <TrendingUp className="h-2.5 w-2.5 mr-0.5" />
                  ) : (
                    <TrendingDown className="h-2.5 w-2.5 mr-0.5" />
                  )}
                  {isPos ? `+${item.changePct}%` : `${item.changePct}%`}
                </span>
              </a>
            )
          })}
        </div>
      </div>
    </div>
  )
}
