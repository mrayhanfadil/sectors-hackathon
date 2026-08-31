import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { fetchReport } from "@/lib/api"

export const Route = (createFileRoute as any)("/report/$ticker/")({ component: ReportPage })

function ReportPage() {
  const { ticker } = Route.useParams()
  const tk = String(ticker).toUpperCase()
  const { data, isLoading, error } = useQuery({ queryKey: ["report", tk], queryFn: () => fetchReport(tk) })
  if (isLoading) return <div className="rounded-xl border bg-white p-6 text-sm text-slate-500">Loading {tk}...</div>
  if (error || !data) return <div className="rounded-xl border bg-white p-6 text-sm text-red-600">Failed to load {tk}.</div>
  const r = data as { ticker: string; name: string; price: number; target: number; upside: string; rating: string; summary: string; valuation: { method: string; value: number; weight?: number }[]; updatedAt: string }
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <h1 className="text-xl font-semibold">{r.ticker} - {r.name}</h1>
        <Badge variant={r.rating === "BUY" ? "success" : r.rating === "SELL" ? "destructive" : "secondary"}>{r.rating}</Badge>
        <Badge variant="outline">TP {r.target.toLocaleString("id-ID")} ({r.upside})</Badge>
        <span className="text-xs text-slate-500">Px {r.price.toLocaleString("id-ID")} - {r.updatedAt}</span>
      </div>
      <p className="text-sm leading-relaxed text-slate-600">{r.summary}</p>
      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-sm">Valuation</CardTitle><CardDescription className="text-xs">Mock - deterministic engines in P2</CardDescription></CardHeader>
          <CardContent className="space-y-2 text-sm">
            {r.valuation.map((v) => (
              <div key={v.method} className="flex justify-between rounded-md border px-3 py-2">
                <span>{v.method}</span>
                <span className="font-medium">{v.value.toLocaleString("id-ID")}{v.weight ? ` - ${v.weight}%` : ""}</span>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Actions</CardTitle></CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            <a href={`/report/${tk}/challenge`} className="inline-flex h-9 items-center rounded-md bg-slate-900 px-4 text-sm text-white">Challenge</a>
            <a href={`/report/${tk}/sentiment`} className="inline-flex h-9 items-center rounded-md border px-4 text-sm">Sentiment</a>
            <a href="/outlook" className="inline-flex h-9 items-center rounded-md px-4 text-sm hover:bg-slate-100">Outlook</a>
            <a href="#" onClick={e => e.preventDefault()} className="inline-flex h-9 items-center rounded-md border px-4 text-sm">Download PDF (soon)</a>
          </CardContent>
        </Card>
      </div>
      <p className="text-xs text-slate-500">TanStack Query - cache 4h - source disclosed per exhibit (P1 IDX+yfinance).</p>
    </div>
  )
}
