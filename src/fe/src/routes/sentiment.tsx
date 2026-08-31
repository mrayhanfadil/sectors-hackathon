import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { fetchMarketSentiment } from "@/lib/api"

export const Route = (createFileRoute as any)("/sentiment")({ component: MarketSentimentPage })

function MarketSentimentPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["market-sentiment"],
    queryFn: fetchMarketSentiment,
  })

  if (isLoading) {
    return (
      <div className="flex min-h-[300px] items-center justify-center rounded-xl border bg-white p-8 text-sm text-slate-500">
        Mengagregasi sentimen pasar ritel dari X, Reddit, dan Stockbit...
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="rounded-xl border border-red-200 bg-white p-6 text-sm text-red-600">
        Gagal memuat ringkasan sentimen pasar.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Market Intelligence · Retail Social Sentiment
          </span>
          <Badge variant="outline" className="border-emerald-600 text-emerald-700 bg-emerald-50">
            0 Sectors Credit (P0-P1)
          </Badge>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Retail Sentiment Dashboard — IDX Universe Quintet
        </h1>
        <p className="text-sm text-slate-600">
          Pemantauan narasi ritel di media sosial (X, Reddit, Stockbit) untuk membandingkan sentimen crowd vs model valuasi institusi.
        </p>
      </div>

      {/* Market Overview Card */}
      <div className="grid gap-6 sm:grid-cols-3">
        <Card className="bg-white shadow-sm sm:col-span-1 border-slate-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Rata-Rata Mood Pasar Ritel
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-extrabold text-slate-900">{data.averageGauge}</span>
              <span className="text-base text-slate-400 font-medium">/ 100</span>
            </div>
            <Badge
              variant={data.averageGauge > 60 ? "success" : data.averageGauge < 40 ? "destructive" : "secondary"}
              className="text-xs font-semibold"
            >
              {data.marketMood}
            </Badge>
            <p className="text-[11px] text-slate-500 pt-1">
              Berdasarkan 28.000+ sinyal media sosial 14 hari terakhir.
            </p>
          </CardContent>
        </Card>

        <Card className="bg-white shadow-sm sm:col-span-2 border-slate-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Pilar Metodologi Sentimen Ritel
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-3 text-xs">
            <div className="rounded border bg-slate-50 p-2.5 space-y-1">
              <div className="font-bold text-slate-900">1. Sinyal X &amp; Reddit</div>
              <div className="text-slate-600 text-[11px]">
                Ekstraksi query cashtag <code>$BBCA</code>, <code>$MTEL</code> via xurl &amp; Google Search index.
              </div>
            </div>
            <div className="rounded border bg-slate-50 p-2.5 space-y-1">
              <div className="font-bold text-slate-900">2. Anti-Noise &amp; Dedup</div>
              <div className="text-slate-600 text-[11px]">
                Penyaringan spam bot, tier ranking, dan normalisasi polaritas 0–100.
              </div>
            </div>
            <div className="rounded border bg-slate-50 p-2.5 space-y-1">
              <div className="font-bold text-slate-900">3. Uji Realitas Modeler</div>
              <div className="text-slate-600 text-[11px]">
                Membandingkan euforia ritel vs model DCF deterministik untuk mendeteksi deviasi.
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Universe Table */}
      <Card className="bg-white shadow-sm border-slate-200">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold">Tabel Sentimen Emiten (Quintet)</CardTitle>
          <CardDescription className="text-xs">
            Klik emiten untuk membuka rincian breakdown narasi per platform atau mengajukan tantangan adversarial.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b bg-slate-50 text-xs font-semibold uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Ticker</th>
                  <th className="px-4 py-3">Emiten &amp; Arketipe</th>
                  <th className="px-4 py-3 text-center">Score Gauge</th>
                  <th className="px-4 py-3">Sentimen</th>
                  <th className="px-4 py-3">Narasi Kunci Ritel</th>
                  <th className="px-4 py-3 text-right">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y text-slate-700">
                {data.tickers.map((t) => (
                  <tr key={t.ticker} className="hover:bg-slate-50/80 transition">
                    <td className="px-4 py-3 font-bold text-slate-900">{t.ticker}</td>
                    <td className="px-4 py-3 text-xs">{t.name}</td>
                    <td className="px-4 py-3 text-center">
                      <span className="font-bold text-sm text-slate-900">{t.gauge}</span>
                      <span className="text-xs text-slate-400">/100</span>
                    </td>
                    <td className="px-4 py-3">
                      <Badge
                        variant={t.gauge > 60 ? "success" : t.gauge < 40 ? "destructive" : "secondary"}
                        className="text-[11px]"
                      >
                        {t.label}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-600 max-w-xs truncate">
                      {t.topNarrative}
                    </td>
                    <td className="px-4 py-3 text-right space-x-2">
                      <a
                        href={`/report/${t.ticker}/sentiment`}
                        className="inline-flex items-center rounded border border-slate-300 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50"
                      >
                        Detail Sentimen
                      </a>
                      <a
                        href={`/report/${t.ticker}/challenge`}
                        className="inline-flex items-center rounded bg-slate-900 px-2.5 py-1 text-xs font-medium text-white hover:bg-slate-800"
                      >
                        Challenge
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Compliance Disclaimer */}
      <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-xs text-slate-500">
        <b>Disklaimer OJK &amp; Pasar Modal:</b> Seluruh data sentimen media sosial dihasilkan untuk analisis intelligence dan tidak merepresentasikan rekomendasi beli/jual saham. Keputusan investasi sepenuhnya berada di tangan investor.
      </div>
    </div>
  )
}
