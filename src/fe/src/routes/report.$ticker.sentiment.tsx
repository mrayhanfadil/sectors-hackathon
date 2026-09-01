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
  if (!data) return <div className="text-sm text-red-600">Failed to load sentiment.</div>
  const s = data as any

  if (s.empty || s.gauge == null) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold">Retail Sentiment - {tk}</h1>
          <a href={`/report/${tk}`} className="text-xs text-slate-500 underline hover:text-slate-900">← Back to Report</a>
        </div>
        <Card className="border-amber-200 bg-amber-50/50">
          <CardHeader>
            <CardTitle className="text-sm text-amber-900">Sentiment Belum Tersedia</CardTitle>
            <CardDescription className="text-xs text-amber-700">
              {s.note || "Sentiment belum tersedia — BE offline atau news Harvester belum return hasil."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-slate-600">
              Data sentimen ritel (X, Reddit, Stockbit) diagregasi secara dinamis saat News Harvester dan Social Sentiment agents berjalan.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Retail Sentiment - {tk}</h1>
        <a href={`/report/${tk}`} className="text-xs text-slate-500 underline hover:text-slate-900">← Back to Report</a>
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="sm:col-span-1">
          <CardHeader><CardTitle className="text-sm">Gauge</CardTitle><CardDescription className="text-xs">0 bear - 100 bull</CardDescription></CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">{s.gauge}<span className="text-base font-normal text-slate-500">/100</span></div>
            <Badge variant={Number(s.gauge) > 60 ? "success" : Number(s.gauge) < 40 ? "destructive" : "secondary"} className="mt-2">{s.label ?? "Neutral"}</Badge>
            <p className="mt-2 text-xs text-slate-500">Disclaimer: sentiment is not advice.</p>
          </CardContent>
        </Card>
        <Card className="sm:col-span-2">
          <CardHeader><CardTitle className="text-sm">Top narratives</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            {s.narratives && s.narratives.length > 0 ? (
              s.narratives.map((n: string, i: number) => <div key={i} className="rounded-md border px-3 py-2">#{i+1} {n}</div>)
            ) : (
              <p className="text-xs text-slate-500">Belum ada narasi yang terdeteksi.</p>
            )}
            {s.timeline && s.timeline.length > 0 && (
              <div className="pt-2">
                <div className="text-xs font-medium text-slate-700">Timeline</div>
                {s.timeline.map((t: { date: string; note: string }) => <div key={t.date} className="text-xs text-slate-600">{t.date} - {t.note}</div>)}
              </div>
            )}
            {s.sources && s.sources.length > 0 && (
              <div className="flex gap-2 pt-2">
                {s.sources.map((src: { platform: string; url: string }) => <a key={src.platform} href={src.url} target="_blank" rel="noreferrer" className="text-xs underline">{src.platform}</a>)}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
