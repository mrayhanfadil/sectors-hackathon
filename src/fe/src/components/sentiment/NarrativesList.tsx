import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Flame } from "lucide-react"

interface NarrativeItem {
  rank: number
  title: string
  summary: string
  sentimentScore: number
  channels: string[]
}

interface NarrativesListProps {
  narratives: NarrativeItem[]
  ticker: string
}

export function NarrativesList({ narratives, ticker }: NarrativesListProps) {
  return (
    <Card className="border-[#262d3a] bg-[#111317]">
      <CardHeader className="pb-2 border-b border-[#1d222c]">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xs font-semibold flex items-center gap-2 text-slate-200">
            <Flame className="h-3.5 w-3.5 text-amber-400" />
            <span>Top Retail Narratives & Social Themes for {ticker}</span>
          </CardTitle>
          <Badge variant="outline" className="font-mono text-[10px]">
            RANKED BY ENGAGEMENT
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-3 space-y-2.5">
        {narratives.map((n) => (
          <div
            key={n.rank}
            className="p-3 rounded-lg bg-[#161a22] border border-[#212734] space-y-1.5 hover:border-slate-600 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="h-5 w-5 rounded bg-amber-500/10 border border-amber-500/30 flex items-center justify-center font-mono font-bold text-xs text-amber-400">
                  #{n.rank}
                </span>
                <span className="text-xs font-semibold text-slate-100 font-sans">
                  {n.title}
                </span>
              </div>
              <Badge variant="amber" className="font-mono text-[10px]">
                Score {n.sentimentScore}/100
              </Badge>
            </div>

            <p className="text-xs text-slate-300 font-sans leading-relaxed">
              {n.summary}
            </p>

            <div className="flex items-center gap-1.5 pt-1">
              <span className="text-[10px] font-mono text-slate-500">Channels:</span>
              <div className="flex flex-wrap gap-1 font-mono text-[10px]">
                {n.channels.map((ch) => (
                  <span
                    key={ch}
                    className="rounded bg-[#101318] px-1.5 py-0.5 text-slate-400 border border-[#232936]"
                  >
                    {ch}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
