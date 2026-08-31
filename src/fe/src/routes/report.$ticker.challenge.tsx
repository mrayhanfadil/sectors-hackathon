import { createFileRoute } from "@tanstack/react-router"
import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { submitChallenge, type ChallengeResponse, type Ticker } from "@/lib/api"

export const Route = (createFileRoute as any)("/report/$ticker/challenge")({ component: ChallengePage })

const SUGGESTED_CHALLENGES: Record<string, string[]> = {
  RATU: [
    "WACC 8.4% is too low vs MTEL 10.1% given single-asset oil risk and market beta.",
    "Lifting assumption 169k BOPD may overestimate Cepu PSC natural decline rate.",
    "EV/EBITDA multiple 22.6x is at a premium vs regional pure-play oil peers.",
  ],
  CDIA: [
    "One-off normalization of US$15.9mn appears aggressive for maritime logistics restructuring.",
    "Port & Logistics revenue growth of +44.7% YoY is vulnerable to regional shipping rate slowdown.",
    "DDM payout assumption of 40% in FY27 may compete with Cilegon port capex requirements.",
  ],
  MTEL: [
    "Tenancy ratio 1.57x is already elevated — can colocation reach 1.60x post-merger?",
    "Quantified catalyst +IDR 360-420bn from 700MHz spectrum lelang assumes zero operator churn.",
    "Blended weighting of 60% DCF / 40% EV/EBITDA overweights cash flow over replacement cost.",
  ],
  BBCA: [
    "GGM target P/BV 3.3x is unsustainable if BI rate cuts compress net interest margins.",
    "Credit cost and LAR risk could rise in SME and consumer portfolio during 2H26.",
    "Peer multiple expansion of BBCA vs BBRI/BMRI is already at +2 standard deviations.",
  ],
  ADRO: [
    "Holdco discount of 15% on AADI spin-off is too narrow compared to regional conglomerate average of 25%.",
    "Thermal coal Newcastle export price normalization could impair post-spin cash flow buffer.",
    "Kaltara aluminum smelter capex payback period exceeds initial 6-year target.",
  ],
}

const TICKERS: { ticker: Ticker; name: string }[] = [
  { ticker: "RATU", name: "Ratu Prabu Energi (Single)" },
  { ticker: "CDIA", name: "Chandra Daya (SOTP)" },
  { ticker: "MTEL", name: "Mitratel (Infra)" },
  { ticker: "BBCA", name: "BCA (GGM Bank)" },
  { ticker: "ADRO", name: "Adaro (SOTP Demerger)" },
]

function ChallengePage() {
  const { ticker } = Route.useParams()
  const tk = String(ticker).toUpperCase()
  const [q, setQ] = React.useState("")
  const [loading, setLoading] = React.useState(false)
  const [debates, setDebates] = React.useState<ChallengeResponse[]>([])
  const [error, setError] = React.useState<string | null>(null)

  const suggestions = SUGGESTED_CHALLENGES[tk] || SUGGESTED_CHALLENGES.RATU

  async function handleChallenge(claimText: string) {
    if (!claimText.trim() || loading) return
    setLoading(true)
    setError(null)
    try {
      const resp = await submitChallenge({ ticker: tk, claim: claimText })
      setDebates((prev) => [resp, ...prev])
      setQ("")
    } catch (err: any) {
      setError(err?.message || "Failed to reach adversarial defense agent.")
    } finally {
      setLoading(false)
    }
  }

  function handleFormSubmit(e: React.FormEvent) {
    e.preventDefault()
    handleChallenge(q)
  }

  function downloadDebateJson() {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(debates, null, 2))
    const dl = document.createElement("a")
    dl.setAttribute("href", dataStr)
    dl.setAttribute("download", `debate_user_${tk.toLowerCase()}.json`)
    dl.click()
  }

  return (
    <div className="space-y-6">
      {/* Header & Navigation */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Adversarial Red Team · Multi-Agent Debate</span>
            <Badge variant="outline" className="border-emerald-600 text-emerald-700 bg-emerald-50">
              Anti-Sycophancy Active
            </Badge>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Challenge &amp; Defense — {tk}
          </h1>
          <p className="text-sm text-slate-600">
            Ajukan kritik terhadap valuasi, asumsi, atau KPI. Agent wajib <b>defend pakai bukti</b> (Exhibit + kalkulasi + sumber) atau <b>concede dengan koreksi</b>.
          </p>
        </div>

        {/* Ticker Switcher */}
        <div className="flex flex-wrap gap-1.5 rounded-lg border bg-white p-1 shadow-sm">
          {TICKERS.map((t) => (
            <a
              key={t.ticker}
              href={`/report/${t.ticker}/challenge`}
              className={`rounded-md px-3 py-1 text-xs font-medium transition ${
                t.ticker === tk ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {t.ticker}
            </a>
          ))}
        </div>
      </div>

      {/* Main Interactive Box */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left 2 Cols: Form & Debates */}
        <div className="space-y-6 lg:col-span-2">
          <Card className="border-slate-300 shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Ajukan Kritik ke Agent Modeler / Analyst</CardTitle>
              <CardDescription className="text-xs text-slate-500">
                Rule §3: Defender tidak boleh menyetujui tanpa bukti aritmatika. Critic akan menolak jika argumen berupa halusinasi.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <form onSubmit={handleFormSubmit} className="space-y-3">
                <textarea
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  rows={3}
                  placeholder={`Contoh untuk ${tk}: ${suggestions[0]}`}
                  className="w-full rounded-md border border-slate-300 p-3 text-sm outline-none transition focus:border-slate-900 focus:ring-1 focus:ring-slate-900"
                />
                <div className="flex items-center justify-between">
                  <div className="text-xs text-slate-500">
                    Endpoint: <code className="bg-slate-100 px-1 py-0.5 rounded">/api/challenge</code>
                  </div>
                  <Button type="submit" disabled={loading || !q.trim()}>
                    {loading ? "Agent sedang menganalisis..." : "Kirim Challenge"}
                  </Button>
                </div>
              </form>

              {/* Preset Prompts */}
              <div className="border-t pt-3">
                <div className="text-xs font-medium text-slate-700 mb-2">Preset Tantangan Institusional ({tk}):</div>
                <div className="flex flex-col gap-1.5">
                  {suggestions.map((s, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleChallenge(s)}
                      className="text-left rounded-md border border-slate-200 bg-slate-50/70 p-2 text-xs text-slate-700 hover:bg-slate-100 hover:border-slate-300 transition"
                    >
                      💬 <span className="font-medium text-slate-900">"{s}"</span>
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Error notice */}
          {error && (
            <div className="rounded-md border border-red-300 bg-red-50 p-3 text-xs text-red-700">
              <b>Error:</b> {error}
            </div>
          )}

          {/* Debate Transcript Stream */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
                Log Debat Adversarial ({debates.length})
              </h2>
              {debates.length > 0 && (
                <button
                  onClick={downloadDebateJson}
                  className="text-xs text-slate-600 hover:text-slate-900 underline flex items-center gap-1"
                >
                  Export debate_user.json
                </button>
              )}
            </div>

            {debates.length === 0 && !loading && (
              <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
                Belum ada perdebatan yang diajukan. Klik salah satu preset tantangan di atas atau ketik kritik spesifik mengenai WACC, segmen, atau KPI untuk memicu pembelaan agent.
              </div>
            )}

            {debates.map((item, i) => (
              <Card key={item.debate_id || i} className="border-l-4 border-l-slate-900 shadow-sm">
                <CardContent className="pt-4 space-y-3">
                  {/* User Claim */}
                  <div className="rounded-md bg-slate-100 p-3">
                    <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tantangan Pengguna</div>
                    <div className="mt-1 text-sm font-medium text-slate-900">"{item.claim}"</div>
                  </div>

                  {/* Agent Defense */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold uppercase text-slate-500">Respon Agent:</span>
                        <Badge
                          variant={item.verdict === "defend" ? "success" : "destructive"}
                          className="font-bold text-[11px]"
                        >
                          {item.verdict === "defend" ? "DEFEND (Bukti Terverifikasi)" : "CONCEDE (Koreksi Diperlukan)"}
                        </Badge>
                      </div>
                      <span className="text-[11px] text-slate-400 font-mono">ID: {item.debate_id}</span>
                    </div>

                    <p className="text-sm leading-relaxed text-slate-800 bg-emerald-50/40 p-3 rounded border border-emerald-100">
                      {item.evidence}
                    </p>

                    {/* Citations */}
                    {(item.exhibit_ref || item.source_citation) && (
                      <div className="grid gap-2 sm:grid-cols-2 pt-1">
                        {item.exhibit_ref && (
                          <div className="rounded border bg-slate-50 p-2 text-xs">
                            <span className="font-semibold text-slate-600">Sitasi Exhibit:</span>{" "}
                            <span className="text-slate-900 font-medium">{item.exhibit_ref}</span>
                          </div>
                        )}
                        {item.source_citation && (
                          <div className="rounded border bg-slate-50 p-2 text-xs">
                            <span className="font-semibold text-slate-600">Sumber &amp; Engine:</span>{" "}
                            <span className="text-slate-700 italic font-mono text-[11px]">{item.source_citation}</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Right Col: Institutional Context & Links */}
        <div className="space-y-4">
          <Card className="bg-white">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Aturan Adversarial Red Team</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-xs text-slate-600">
              <div className="border-l-2 border-slate-900 pl-2">
                <b>1. Tidak Boleh Menjadi Yes-Man:</b> Defender harus mempertahankan tesis jika asumsi didukung data historis IDX atau konsensus industri.
              </div>
              <div className="border-l-2 border-emerald-600 pl-2">
                <b>2. Sitasi Wajib:</b> Setiap pembelaan harus merujuk ke nomor Exhibit, formula (WACC/GGM/SOTP), atau tanggal berita.
              </div>
              <div className="border-l-2 border-amber-600 pl-2">
                <b>3. Concede Secara Jujur:</b> Jika pengguna menemukan inkonsistensi matematis riil, agent wajib mencatat koreksi pada <code className="bg-slate-100 px-1">debate.json</code>.
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Navigasi Terkait {tk}</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2 text-xs">
              <a
                href={`/report/${tk}`}
                className="flex items-center justify-between rounded-md border p-2.5 hover:bg-slate-50 transition font-medium"
              >
                <span>Lihat Ringkasan Report {tk}</span>
                <span className="text-slate-400">→</span>
              </a>
              <a
                href={`/report/${tk}/sentiment`}
                className="flex items-center justify-between rounded-md border p-2.5 hover:bg-slate-50 transition font-medium"
              >
                <span>Analisis Retail Sentiment {tk}</span>
                <span className="text-slate-400">→</span>
              </a>
              <a
                href="/outlook"
                className="flex items-center justify-between rounded-md border p-2.5 hover:bg-slate-50 transition font-medium"
              >
                <span>Market Strategy Outlook (JCI 9.100)</span>
                <span className="text-slate-400">→</span>
              </a>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

