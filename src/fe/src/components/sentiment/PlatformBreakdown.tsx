import type { SocialMention } from "@/lib/types"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ExternalLink, Share2 } from "lucide-react"

interface PlatformItem {
  platform: string
  sentimentScore: number
  volumeSharePct: number
  samplePost: SocialMention
}

interface PlatformBreakdownProps {
  platforms: PlatformItem[]
}

export function PlatformBreakdown({ platforms }: PlatformBreakdownProps) {
  return (
    <Card className="border-[#262d3a] bg-[#111317]">
      <CardHeader className="pb-2 border-b border-[#1d222c]">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xs font-semibold flex items-center gap-2 text-slate-200">
            <Share2 className="h-3.5 w-3.5 text-amber-400" />
            <span>Cross-Platform Social Volume & Verbatim Mentions</span>
          </CardTitle>
          <Badge variant="outline" className="font-mono text-[10px]">
            X • REDDIT • STOCKBIT
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-3 space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {platforms.map((p, idx) => (
            <div
              key={idx}
              className="p-3.5 rounded-lg bg-[#161a22] border border-[#212734] space-y-2 flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-xs text-amber-300">
                    {p.platform}
                  </span>
                  <Badge variant="secondary" className="text-[10px] font-mono">
                    {p.volumeSharePct}% Vol
                  </Badge>
                </div>

                <div className="flex justify-between items-baseline font-mono text-xs">
                  <span className="text-slate-400 text-[11px]">Sentiment Score:</span>
                  <span className="text-emerald-400 font-bold">{p.sentimentScore}/100</span>
                </div>

                {/* Sample Verbatim Quote */}
                <div className="p-2.5 rounded bg-[#101318] border border-[#222836] space-y-1 text-xs">
                  <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
                    <span>{p.samplePost.author}</span>
                    <span>{p.samplePost.engagement}</span>
                  </div>
                  <p className="text-slate-200 font-sans italic text-[11px] leading-relaxed">
                    &ldquo;{p.samplePost.content}&rdquo;
                  </p>
                </div>
              </div>

              <a
                href={p.samplePost.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center justify-between text-[10px] font-mono text-slate-400 hover:text-amber-300 pt-1 border-t border-[#1e2430] transition-colors"
              >
                <span>View Live Feed Thread</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
