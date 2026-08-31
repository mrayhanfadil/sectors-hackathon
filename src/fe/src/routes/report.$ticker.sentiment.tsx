import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { fetchSentiment, type SentimentData, type Ticker } from "@/lib/api"

export const Route = (createFileRoute as any)("/report/$ticker/sentiment")({ component: SentimentPage })

const TICKERS: { ticker: Ticker; name: string }[] = [
  { ticker: "RATU", name: "Ratu Prabu Energi" },
  { ticker: "CDIA", name: "Chandra Daya Investasi" },
  { ticker: "MTEL", name: "Mitratel" },
  { ticker: "BBCA", name: "Bank Central Asia" },
  { ticker: "ADRO", name: "Adaro Energy" },
]

function SentimentPage() {
  const { ticker } = Route.useParams()
  const tk = String(ticker).toUpperCase()
  const { data, isLoading, error } = useQuery({
    queryKey: ["sentiment", tk],
    queryFn: () => fetchSentiment(tk),
  })

  if (isLoading) {
    return (
      <div className="flex min-h-[320px] items-center justify-center rounded-xl border bg-white p-12 text-sm text-slate-500">
        <div className="flex flex-col items-center gap-2">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-900 border-t-transparent" />
          <span>Mengumpulkan sinyal sentimen media sosial untuk {tk}...</span>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="rounded-xl border border-red-200 bg-white p-6 text-sm text-red-600">
        Gagal memuat data sentimen untuk {tk}.
      </div>
    )
  }

  const s = data as SentimentData

  // Determine meter color & width
  const gaugePct = Math.max(0, Math.min(100, s.gauge))
  const gaugeColor =
    gaugePct > 65
      ? "bg-emerald-600"
      : gaugePct > 50
      ? "bg-emerald-500"
      : gaugePct > 40
      ? "bg-amber-500"
      : "bg-rose-600"

  const badgeVariant =
    s.gauge > 60 ? "success" : s.gauge < 40 ? "destructive" : "secondary"

  return (
    <div className="space-y-6">
      {/* Header & Switcher */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Retail Social Narrative Tracker · P0-P1 (0 Sectors Credit)
            </span>
            <Badge variant="outline" className="border-blue-600 text-blue-700 bg-blue-50">
              X + Reddit + Stockbit
            </Badge>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Retail Sentiment — {s.name} ({s.ticker})
          </h1>
          <p className="text-sm text-slate-600">
            Agregasi narasi ritel media sosial 14 hari terakhir vs tesis valuasi institusional.
          </p>
        </div>

        {/* Ticker Quick Switcher */}
        <div className="flex flex-wrap gap-1.5 rounded-lg border bg-white p-1 shadow-sm">
          {TICKERS.map((t) => (
            <a
              key={t.ticker}
              href={`/report/${t.ticker}/sentiment`}
              className={`rounded-md px-3 py-1 text-xs font-medium transition ${
                t.ticker === tk ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {t.ticker}
            </a>
          ))}
        </div>
      </div>

      {/* Grid: Gauge & Top Summary */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* Sentiment Gauge Card */}
        <Card className="bg-white shadow-sm md:col-span-1 border-slate-200">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-bold uppercase tracking-wider text-slate-500">
                Sentiment Gauge
              </CardTitle>
              <Badge variant={badgeVariant}>{s.label}</Badge>
            </div>
            <CardDescription className="text-xs">Skala 0 (Extreme Bear) – 100 (Extreme Bull)</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-extrabold text-slate-900">{s.gauge}</span>
              <span className="text-base text-slate-400 font-medium">/ 100</span>
              <span className="ml-auto text-xs text-slate-500 font-medium">
                Keyakinan: {Math.round((s.confidence || 0.8) * 100)}%
              </span>
            </div>

            {/* Visual Gauge Bar */}
            <div className="space-y-1.5">
              <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100 flex">
                <div
                  className={`h-full transition-all duration-500 ${gaugeColor}`}
                  style={{ width: `${gaugePct}%` }}
                />
              </div>
              <div className="flex justify-between text-[10px] font-medium text-slate-400">
                <span>0 Bear</span>
                <span>40 Netral</span>
                <span>60 Bull</span>
                <span>100</span>
              </div>
            </div>

            {/* Alignment Box */}
            {s.retailVsThesis && (
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 space-y-1.5 text-xs">
                <div className="font-semibold text-slate-700">Tesis vs Crowd:</div>
                <div className="text-slate-600">
                  <span className="font-medium text-slate-900">Ritel:</span> {s.retailVsThesis.retailSentiment}
                </div>
                <div className="text-slate-600">
                  <span className="font-medium text-slate-900">Institusi:</span> {s.retailVsThesis.institutionalView}
                </div>
                <div className="text-[11px] font-medium text-blue-700 pt-1">
                  Kesesuaian: {s.retailVsThesis.alignment}
                </div>
              </div>
            )}

            <div className="rounded border border-amber-200 bg-amber-50/70 p-2.5 text-[11px] text-amber-900 leading-tight">
              <b>Disklaimer:</b> {s.disclaimer || "Sentimen media sosial ≠ saran investasi."}
            </div>
          </CardContent>
        </Card>

        {/* Top 3 Narratives & Mindshare */}
        <Card className="bg-white shadow-sm md:col-span-2 border-slate-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-bold uppercase tracking-wider text-slate-500">
              Top 3 Narasi Ritel Teratas &amp; Uji Realitas
            </CardTitle>
            <CardDescription className="text-xs">
              Topik yang paling banyak diperbincangkan di komunitas investor IDX beserta verifikasi model institusi.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {s.narratives.map((n) => (
              <div
                key={n.rank}
                className="rounded-lg border border-slate-200 bg-slate-50/50 p-3.5 space-y-2 hover:bg-slate-50 transition"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-slate-900 text-[11px] font-bold text-white">
                      {n.rank}
                    </span>
                    <h3 className="text-sm font-semibold text-slate-900">{n.title}</h3>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge variant={n.sentiment === "bull" ? "success" : n.sentiment === "bear" ? "destructive" : "secondary"}>
                      {n.sentiment.toUpperCase()}
                    </Badge>
                    <span className="text-xs font-semibold text-slate-600">{n.sharePct}% share</span>
                  </div>
                </div>
                <div className="rounded border border-slate-200/80 bg-white p-2.5 text-xs text-slate-700">
                  <span className="font-semibold text-slate-900">Uji Realitas Modeler:</span> {n.realityCheck}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Two Column Section: Timeline & Platforms */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Timeline Evolution */}
        <Card className="bg-white shadow-sm border-slate-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-bold uppercase tracking-wider text-slate-500">
              Evolusi Kronologis Narasi (14 Hari)
            </CardTitle>
            <CardDescription className="text-xs">
              Bagaimana diskusi ritel berkembang merespon katalis pasar dan berita resmi emiten.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {s.timeline.map((t, idx) => (
              <div key={idx} className="flex gap-3 text-xs border-l-2 border-slate-300 pl-3 py-1">
                <div className="font-mono text-slate-500 shrink-0 font-medium">{t.date}</div>
                <div className="space-y-0.5">
                  <div className="font-semibold text-slate-900">{t.event}</div>
                  <div className="text-[11px] text-emerald-700 font-medium">Dampak sentimen: {t.impact}</div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Platform Breakdown */}
        <Card className="bg-white shadow-sm border-slate-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-bold uppercase tracking-wider text-slate-500">
              Rincian Per Platform (X · Reddit · Stockbit)
            </CardTitle>
            <CardDescription className="text-xs">
              Data sentimen dan volume perbincangan spesifik kanal retail.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {s.platforms.map((p) => (
              <div key={p.platform} className="rounded-lg border border-slate-200 p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm text-slate-900">{p.platform}</span>
                    <span className="text-xs text-slate-500">({p.volume})</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-slate-900">{p.score}/100</span>
                    <Badge variant={p.score > 60 ? "success" : p.score < 40 ? "destructive" : "secondary"}>
                      {p.label}
                    </Badge>
                  </div>
                </div>
                {p.sampleText && (
                  <p className="text-xs italic text-slate-600 bg-slate-50 p-2 rounded">
                    "{p.sampleText}"
                  </p>
                )}
                <div className="pt-1 flex justify-end">
                  <a
                    href={p.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs text-blue-600 hover:underline inline-flex items-center gap-1 font-medium"
                  >
                    Buka pencarian sinyal di {p.platform} ↗
                  </a>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Navigation Buttons */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
        <a
          href={`/report/${tk}`}
          className="inline-flex h-9 items-center rounded-md border border-slate-300 bg-white px-4 text-xs font-semibold text-slate-700 hover:bg-slate-50"
        >
          ← Kembali ke Report {tk}
        </a>
        <div className="flex gap-2">
          <a
            href={`/report/${tk}/challenge`}
            className="inline-flex h-9 items-center rounded-md bg-slate-900 px-4 text-xs font-semibold text-white hover:bg-slate-800"
          >
            Tantang Thesis ({tk}) di Adversarial UI →
          </a>
          <a
            href="/sentiment"
            className="inline-flex h-9 items-center rounded-md border border-slate-300 bg-white px-4 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            Lihat Pasar Keseluruhan (Market Sentiment)
          </a>
        </div>
      </div>
    </div>
  )
}

