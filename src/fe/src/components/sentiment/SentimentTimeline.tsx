import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { History, Calendar } from "lucide-react"

interface TimelinePoint {
  date: string
  sentimentScore: number
  stockPrice: number
  keyEvent: string
}

interface SentimentTimelineProps {
  timeline: TimelinePoint[]
  ticker: string
}

export function SentimentTimeline({ timeline }: SentimentTimelineProps) {
  return (
    <Card className="border-[#262d3a] bg-[#111317]">
      <CardHeader className="pb-2 border-b border-[#1d222c]">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xs font-semibold flex items-center gap-2 text-slate-200">
            <History className="h-3.5 w-3.5 text-amber-400" />
            <span>Narrative Shift Timeline & Corporate Event Impact</span>
          </CardTitle>
          <Badge variant="outline" className="font-mono text-[10px]">
            EVENT CORRELATION
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-3">
        <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-[#202633]">
          {timeline.map((item, idx) => (
            <div key={idx} className="relative group">
              {/* Dot on line */}
              <div className="absolute -left-6 top-1.5 h-3 w-3 rounded-full bg-amber-400 border-2 border-[#111317] group-hover:scale-125 transition-transform" />

              <div className="p-3 rounded-lg bg-[#161a22] border border-[#212734] space-y-1">
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
                  <span className="flex items-center gap-1 text-slate-400 font-semibold">
                    <Calendar className="h-3 w-3 text-amber-400" />
                    <span>{item.date}</span>
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-slate-300">
                      Price: IDR {item.stockPrice.toLocaleString("id-ID")}
                    </span>
                    <Badge variant="amber" className="text-[10px]">
                      Score {item.sentimentScore}/100
                    </Badge>
                  </div>
                </div>

                <div className="text-xs font-sans text-slate-200 font-medium pt-0.5">
                  {item.keyEvent}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
