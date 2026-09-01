import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft } from "lucide-react"
import { fetchOutlook } from "@/lib/api"

export const Route = (createFileRoute as any)("/outlook")({ component: Outlook })

function Outlook() {
  const { data, isLoading } = useQuery({ queryKey: ["outlook"], queryFn: fetchOutlook })
  if (isLoading) return <div className="text-sm text-slate-500">Loading outlook...</div>
  if (!data) return <div className="text-sm text-red-600">Failed to load.</div>
  const d = data as {
    jci: { base: number; bull: number; bear: number; pe: number; epsGrowth: string }
    sectors: { name: string; call: string }[]
    picks?: unknown[]
    thematics?: { name: string; detail: string; source?: string }[]
    flows?: { narrative: string; table?: { headers: string[]; rows: unknown[][] }; source?: string }
    danantara?: { narrative: string; table?: { headers: string[]; rows: unknown[][] }; source?: string }
    source?: string
  }
  const thematics = d.thematics ?? []
  const flows = d.flows
  const danantara = d.danantara
  const picks = (d.picks ?? []) as { ticker?: string; cap?: string; rationale?: string; reason?: string; sector?: string }[]

  return (
    <div className="space-y-6">
      <a href="/agent" className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-900"><ArrowLeft className="h-3.5 w-3.5" /> Back to ADK Live</a>
      <div>
        <h1 className="text-xl font-semibold">Market Outlook — JCI 9100 base</h1>
        <p className="text-xs text-slate-500">JPM Indonesia 2026 Outlook · EPS +{d.jci?.epsGrowth ?? "8%"} × {d.jci?.pe ?? 15}x · {d.source ?? "JPM + plan §5"}</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card><CardHeader><CardTitle className="text-sm">Bear {d.jci.bear.toLocaleString("id-ID")}</CardTitle><CardDescription className="text-xs">Downside · EPS × Multiple stress + outflow asing</CardDescription></CardHeader><CardContent className="text-xs text-slate-600">Slowdown + foreign UW persisten. Skenario penulis — bukan JPM tunggal.</CardContent></Card>
        <Card className="border-slate-900"><CardHeader><CardTitle className="text-sm">Base {d.jci.base.toLocaleString("id-ID")} · {d.jci.pe}x · {d.jci.epsGrowth} EPS</CardTitle><CardDescription className="text-xs">JPM 2026 base · Priced assumption</CardDescription></CardHeader><CardContent className="text-xs text-slate-600">Index target = EPS growth × target multiple × basis kini. JPM method.</CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">Bull {d.jci.bull.toLocaleString("id-ID")}</CardTitle><CardDescription className="text-xs">Upside · Danantara Value-Up + foreign re-rating</CardDescription></CardHeader><CardContent className="text-xs text-slate-600">Re-rating penuh + flows kembali + policy reform (PP 28/2025).</CardContent></Card>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-sm">Sector OW / N / UW</CardTitle><CardDescription className="text-xs">OW: Industrials · Materials · Consumer Staples/Discretionary · Property — per JPM p9</CardDescription></CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {d.sectors.map((s) => (
            <Badge key={s.name} variant={s.call === "OW" ? "success" : s.call === "UW" ? "destructive" : "secondary"}>{s.name} — {s.call}</Badge>
          ))}
        </CardContent>
      </Card>

      {thematics.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-sm">JPM 5 Thematics 2026</CardTitle><CardDescription className="text-xs">Konsumsi · TSR · Dana asing · Fiskal · Danantara (swing factor)</CardDescription></CardHeader>
          <CardContent className="space-y-3">
            {thematics.map((t) => (
              <div key={t.name} className="rounded-lg border bg-white p-3">
                <div className="text-sm font-medium">{t.name}</div>
                <div className="text-xs leading-relaxed text-slate-600">{t.detail}</div>
                {t.source && <div className="text-xs text-slate-400">Sumber: {t.source}</div>}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {flows && (
        <Card>
          <CardHeader><CardTitle className="text-sm">Flows & MSCI + Positioning</CardTitle><CardDescription className="text-xs">{flows.source ?? "IDX, Bloomberg — data historis"}</CardDescription></CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm leading-relaxed text-slate-600">{flows.narrative}</p>
            {flows.table && (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead><tr className="border-b text-left text-slate-500">{flows.table.headers.map(h => <th key={h} className="py-1">{h}</th>)}</tr></thead>
                  <tbody>{flows.table.rows.map((r, i) => <tr key={i} className="border-b">{(r as unknown[]).map((c, j) => <td key={j} className="py-1">{String(c)}</td>)}</tr>)}</tbody>
                </table>
              </div>
            )}
            <p className="text-xs text-slate-500">Retail 58% ADTV Rp 14.5tn · Asing -US$2.2bn YTD / -2.6bn 2Y · MSCI Adjusted Free Float Mei 2026 (event risiko) — JPM Fig. p23-27.</p>
          </CardContent>
        </Card>
      )}

      {danantara && (
        <Card className="border-amber-200">
          <CardHeader><CardTitle className="text-sm">Danantara & Policy Catalyst — Value-Up Indonesia</CardTitle><CardDescription className="text-xs">{danantara.source ?? "Danantara — rilis publik"}</CardDescription></CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm leading-relaxed text-slate-600">{danantara.narrative}</p>
            {danantara.table && (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead><tr className="border-b text-left text-slate-500">{danantara.table.headers.map(h => <th key={h} className="py-1">{h}</th>)}</tr></thead>
                  <tbody>{danantara.table.rows.map((r, i) => <tr key={i} className="border-b">{(r as unknown[]).map((c, j) => <td key={j} className="py-1">{String(c)}</td>)}</tr>)}</tbody>
                </table>
              </div>
            )}
            <div className="text-xs text-slate-500 space-y-1">
              <div>Struktur: BPI Danantara (Holding) + DAM + DIM — segregasi PSO vs profitability (JPM p1).</div>
              <div>9 sektor prioritas (Vale-GEM HPAL, Chandra Asri chemical) · Financing &gt;US$14bn SWF · SOE ex-bank +25% YTD vs MXID (Fig.55).</div>
              <div>Execution risk: 2025 likuiditas parkir di SBN/neraca; 2026 deployment = swing factor re-rating (0.8% PDB).</div>
            </div>
          </CardContent>
        </Card>
      )}

      {picks.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-sm">Top Picks (JPM + domestic)</CardTitle></CardHeader>
          <CardContent>
            <div className="grid gap-2 sm:grid-cols-2">
              {picks.map((p, i) => (
                <div key={`${p.ticker}-${i}`} className="flex items-center justify-between rounded-md border px-3 py-2 text-sm">
                  <span className="font-medium">{p.ticker} <span className="ml-1 text-xs text-slate-500">{p.cap ?? p.sector ?? ""}</span></span>
                  <span className="text-xs text-slate-600">{p.rationale ?? p.reason ?? ""}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <p className="text-xs text-slate-500">Data pasar dari JPM Indonesia 2026 Outlook (52 halaman, publik) — proyeksi penulis bukan saran investasi. Source: JPM Indonesia 2026 Outlook (JCI 9100 base) + plan §5 · Cache 4h · Thematics/flows/Danantara dari BE strategy overlay bila ada, else fixtures references/global/jpm-indonesia-2026-outlook.md.</p>
      <p className="mt-4 text-xs text-slate-500 text-center">
        Disclaimer: Produk ini adalah informasi, bukan saran investasi. Keputusan investasi sepenuhnya menjadi tanggung jawab pengguna.
      </p>
    </div>
  )
}
