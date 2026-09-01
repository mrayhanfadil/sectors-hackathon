import { createFileRoute } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export const Route = (createFileRoute as any)("/")({ component: Home })

function Home() {
  return (
    <div className="space-y-6">
      <div className="rounded-xl border bg-white p-6">
        <h1 className="text-2xl font-semibold tracking-tight">Institutional-Grade Equity Report - untuk Retail</h1>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-600">Deep 1 product kredibel (bukan 31 demo shallow). Benchmark RATU + CDIA + MTEL + JPM 2026 Outlook + 4 local. Multi-agent + deterministic math (DCF/DDM/SOTP/Blended/Bands/GGM). Frontend CSR Vite -&gt; Pages.dev (bukan Next SSR).</p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Badge>T03 - Frontend</Badge>
          <Badge variant="outline">React Vite + TS + TanStack Query/Router</Badge>
          <Badge variant="secondary">CSR - vite build -&gt; dist</Badge>
        </div>
      </div>
      <Card>
        <CardHeader><CardTitle className="text-sm">Locked tech 6</CardTitle></CardHeader>
        <CardContent className="text-sm leading-relaxed text-slate-600">
          Frontend React+Vite+TS+TanStack Query/Router CSR only (no SSR). <code className="rounded bg-slate-100 px-1">vite build -&gt; dist</code> static -&gt; Cloudflare Pages <code className="rounded bg-slate-100 px-1">*.pages.dev</code>. Overkill Next.js dihindari: no SSR, bundle kecil, dev cepat.
        </CardContent>
      </Card>
      <p className="mt-4 text-xs text-slate-500 text-center">
        Disclaimer: Produk ini adalah informasi, bukan saran investasi. Keputusan investasi sepenuhnya menjadi tanggung jawab pengguna.
      </p>
    </div>
  )
}
