import { createFileRoute, Link } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, Compass, TrendingUp, TrendingDown, Minus } from "lucide-react"
import { fetchOutlook } from "@/lib/api"

export const Route = (createFileRoute as any)("/outlook")({ component: Outlook })

function Outlook() {
  const { data, isLoading } = useQuery({ queryKey: ["outlook"], queryFn: fetchOutlook })
  if (isLoading) return <div className="text-sm text-slate-500">Memuat outlook pasar...</div>
  if (!data) return <div className="text-sm text-red-600">Gagal memuat. Coba muat ulang halaman.</div>
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
      <Link to="/" className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-900">
        <ArrowLeft className="h-3.5 w-3.5" /> Kembali ke Beranda
      </Link>

      <div>
        <Badge className="mb-2">Outlook pasar 2026</Badge>
        <h1 className="text-xl font-bold tracking-tight sm:text-2xl">
          Ke mana arah pasar saham Indonesia?
        </h1>
        <p className="mt-1 max-w-3xl text-sm leading-relaxed text-slate-600">
          IHSG (indeks harga semua saham di BEI) ditargetkan di{" "}
          <span className="font-semibold text-slate-900">
            {d.jci.base.toLocaleString("id-ID")}
          </span>{" "}
          pada skenario normal. Artinya: kalau skenario ini terjadi, nilai gabungan pasar saham
          diperkirakan naik menuju level itu — bukan janji, tapi perkiraan berdasarkan laba
          perusahaan.
        </p>
        <p className="mt-1 text-xs text-slate-500">
          Sumber: {d.source ?? "JPM Indonesia 2026 Outlook"} · Laba perusahaan +{d.jci?.epsGrowth ?? "8%"} · Valuasi {d.jci?.pe ?? 15}x
        </p>
      </div>

      {/* Scenarios in plain language */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="border-red-200">
          <CardHeader>
            <div className="flex items-center gap-2">
              <TrendingDown className="h-4 w-4 text-red-600" />
              <CardTitle className="text-sm">Kalau jelek: {d.jci.bear.toLocaleString("id-ID")}</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Skenario pesimis — ekonomi melambat dan investor asing terus keluar.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-xs leading-relaxed text-slate-600">
            Pasar turun dari posisi sekarang. Saat seperti ini biasanya waktu untuk hati-hati dan
            pegang saham yang keuangannya paling kuat.
          </CardContent>
        </Card>
        <Card className="border-slate-900">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Minus className="h-4 w-4 text-slate-700" />
              <CardTitle className="text-sm">Skenario normal: {d.jci.base.toLocaleString("id-ID")}</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Skenario dasar — laba perusahaan tumbuh {d.jci.epsGrowth}, valuasi {d.jci.pe}x.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-xs leading-relaxed text-slate-600">
            Kondisi berjalan seperti perkiraan: perusahaan untung lebih besar, harga saham ikut
            naik. Target ini dihitung dari pertumbuhan laba × harga wajar saham.
          </CardContent>
        </Card>
        <Card className="border-emerald-200">
          <CardHeader>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-emerald-700" />
              <CardTitle className="text-sm">Kalau bagus: {d.jci.bull.toLocaleString("id-ID")}</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Skenario optimis — reformasi jalan dan investor asing kembali masuk.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-xs leading-relaxed text-slate-600">
            Pasar naik lebih tinggi dari perkiraan karena kepercayaan investor pulih dan ada
            sentimen positif dari kebijakan pemerintah.
          </CardContent>
        </Card>
      </div>

      {/* Sector calls, explained */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Compass className="h-4 w-4 text-slate-700" />
            <CardTitle className="text-sm">Sektor mana yang diunggulkan?</CardTitle>
          </div>
          <CardDescription className="text-xs leading-relaxed">
            Setiap sektor diberi label: <span className="font-semibold">OW</span> artinya
            diunggulkan (porsinya disarankan lebih besar dari pasar) ·{" "}
            <span className="font-semibold">N</span> artinya netral (porsinya mengikuti pasar) ·{" "}
            <span className="font-semibold">UW</span> artinya kurang diunggulkan (porsinya lebih
            kecil dari pasar).
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {d.sectors.map((s) => (
            <Badge key={s.name} variant={s.call === "OW" ? "success" : s.call === "UW" ? "destructive" : "secondary"}>{s.name} — {s.call}</Badge>
          ))}
        </CardContent>
      </Card>

      {thematics.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">5 tema besar yang menggerakkan pasar 2026</CardTitle>
            <CardDescription className="text-xs">
              Faktor-faktor yang menurut riset paling menentukan naik-turunnya pasar tahun ini.
            </CardDescription>
          </CardHeader>
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
          <CardHeader>
            <CardTitle className="text-sm">Uang investor: siapa beli, siapa jual?</CardTitle>
            <CardDescription className="text-xs">{flows.source ?? "IDX, Bloomberg — data historis"}</CardDescription>
          </CardHeader>
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
            <p className="text-xs leading-relaxed text-slate-500">
              Intinya: investor lokal (ritel) kini mendominasi transaksi harian, sementara investor
              asing masih jual bersih. Kalau asing kembali beli, biasanya pasar naik lebih kencang.
            </p>
          </CardContent>
        </Card>
      )}

      {danantara && (
        <Card className="border-amber-200">
          <CardHeader>
            <CardTitle className="text-sm">Danantara: faktor penentu tahun ini</CardTitle>
            <CardDescription className="text-xs">{danantara.source ?? "Danantara — rilis publik"}</CardDescription>
          </CardHeader>
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
            <p className="text-xs leading-relaxed text-slate-500">
              Singkatnya: Danantara adalah badan pengelola investasi negara. Kalau dananya benar-benar
              masuk ke proyek nyata tahun ini, itu kabar baik buat pasar. Kalau macet, pasar bisa
              kecewa — makanya disebut faktor penentu.
            </p>
          </CardContent>
        </Card>
      )}

      {picks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Saham pilihan untuk 2026</CardTitle>
            <CardDescription className="text-xs">
              Daftar saham yang menurut gabungan riset layak dipelajari lebih lanjut — bukan daftar
              belanja.
            </CardDescription>
          </CardHeader>
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

      <p className="text-xs leading-relaxed text-slate-500">
        Data pasar dari JPM Indonesia 2026 Outlook (publik). Angka target adalah perkiraan analis,
        bukan jaminan hasil.
      </p>
      <p className="mt-4 text-center text-xs text-slate-500">
        Disclaimer: Produk ini adalah informasi, bukan saran investasi. Keputusan investasi
        sepenuhnya menjadi tanggung jawab pengguna.
      </p>
    </div>
  )
}
