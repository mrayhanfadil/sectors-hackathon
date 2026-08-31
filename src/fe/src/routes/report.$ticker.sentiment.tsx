import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { fetchSentiment } from "@/lib/api"

export const Route = (createFileRoute as any)("/report/$ticker/sentiment")({ component: SentimentPage })

function SentimentPage() {
  const { ticker } = Route.useParams()
  const tk = String(ticker).toUpperCase()
  const { data, isLoading } = useQuery({ queryKey: ["sentiment", tk], queryFn: () => fetchSentiment(tk) })
  if (isLoading) return <div className="text-sm text-slate-500">Loading sentiment {tk}...</div>
  const s = data as { gauge: number; label: string; narratives: string[]; timeline: { date: string; note: string }[]; sources: { platform: string; url: string }[] }
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Retail Sentiment - {tk}</h1>
      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="sm:col-span-1">
          <CardHeader><CardTitle className="text-sm">Gauge</CardTitle><CardDescription className="text-xs">0 bear - 100 bull</CardDescription></CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">{s.gauge}<span className="text-base font-normal text-slate-500">/100</span></div>
            <Badge variant={s.gauge > 60 ? "success" : s.gauge < 40 ? "destructive" : "secondary"} className="mt-2">{s.label}</Badge>
            <p className="mt-2 text-xs text-slate-500">Disclaimer: sentiment is not advice.</p>
          </CardContent>
        </Card>
        <Card className="sm:col-span-2">
          <CardHeader><CardTitle className="text-sm">Top 3 narratives</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            {s.narratives.map((n, i) => <div key={i} className="rounded-md border px-3 py-2">#{i+1} {n}</div>)}
            <div className="pt-2">
              <div className="text-xs font-medium text-slate-700">Timeline</div>
              {s.timeline.map((t) => <div key={t.date} className="text-xs text-slate-600">{t.date} - {t.note}</div>)}
            </div>
            <div className="flex gap-2 pt-2">
              {s.sources.map((src) => <a key={src.platform} href={src.url} target="_blank" rel="noreferrer" className="text-xs underline">{src.platform}</a>)}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
