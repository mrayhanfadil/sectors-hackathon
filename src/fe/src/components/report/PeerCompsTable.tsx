import type { PeerCompanyComp } from "@/lib/types"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Users2 } from "lucide-react"

interface PeerCompsTableProps {
  peers: PeerCompanyComp[]
  targetTicker: string
}

export function PeerCompsTable({ peers, targetTicker }: PeerCompsTableProps) {
  if (!peers || peers.length === 0) return null

  return (
    <Card className="border-[#262d3a] bg-[#111317]">
      <CardHeader className="pb-2 border-b border-[#1d222c]">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold flex items-center gap-2 text-slate-100">
            <Users2 className="h-4 w-4 text-amber-400" />
            <span>Peer Group Benchmarking & Multiple Valuation Comparison</span>
          </CardTitle>
          <Badge variant="outline" className="font-mono text-[10px]">
            DOMESTIC & REGIONAL PEERS
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-2">
        <div className="overflow-x-auto">
          <table className="w-full text-xs font-sans">
            <thead>
              <tr className="border-b border-[#212631] text-slate-400 font-mono text-[11px] text-right">
                <th className="pb-2 text-left font-medium">Company</th>
                <th className="pb-2 font-medium">Price (IDR)</th>
                <th className="pb-2 font-medium">Mkt Cap (Tn)</th>
                <th className="pb-2 font-medium">P/E FY26</th>
                <th className="pb-2 font-medium">P/BV FY26</th>
                <th className="pb-2 font-medium">EV/EBITDA</th>
                <th className="pb-2 font-medium">ROE (%)</th>
                <th className="pb-2 font-medium">Div Yield</th>
                <th className="pb-2 font-medium text-center">Rating</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#181c24] font-mono text-[11px]">
              {peers.map((p) => {
                const isTarget = p.ticker === targetTicker
                return (
                  <tr
                    key={p.ticker}
                    className={`hover:bg-[#161a22] transition-colors ${
                      isTarget ? "bg-[#181d26] font-bold border-l-2 border-amber-400" : ""
                    }`}
                  >
                    <td className="py-2.5 text-left font-medium">
                      <a href={`/report/${p.ticker}`} className="hover:underline">
                        <span className={isTarget ? "text-amber-300" : "text-white"}>
                          {p.ticker}
                        </span>
                        <span className="text-slate-400 text-[10px] ml-1.5 font-sans font-normal">
                          {p.name}
                        </span>
                      </a>
                    </td>
                    <td className="py-2.5 text-right text-slate-200">
                      {p.priceIdr.toLocaleString("id-ID")}
                    </td>
                    <td className="py-2.5 text-right text-slate-300">{p.marketCapIdrTn}</td>
                    <td className="py-2.5 text-right font-semibold text-amber-300">
                      {p.peFY26 > 0 ? `${p.peFY26}x` : "—"}
                    </td>
                    <td className="py-2.5 text-right text-slate-300">
                      {p.pbvFY26 > 0 ? `${p.pbvFY26}x` : "—"}
                    </td>
                    <td className="py-2.5 text-right text-slate-300">
                      {p.evEbitdaFY26 > 0 ? `${p.evEbitdaFY26}x` : "—"}
                    </td>
                    <td className="py-2.5 text-right text-emerald-400 font-medium">
                      {p.roePct}%
                    </td>
                    <td className="py-2.5 text-right text-slate-300">
                      {p.dividendYieldPct > 0 ? `${p.dividendYieldPct}%` : "—"}
                    </td>
                    <td className="py-2.5 text-center">
                      <Badge
                        variant={
                          p.rating === "BUY"
                            ? "buy"
                            : p.rating === "HOLD"
                            ? "hold"
                            : "secondary"
                        }
                        className="text-[9px] px-1.5 py-0"
                      >
                        {p.rating}
                      </Badge>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
