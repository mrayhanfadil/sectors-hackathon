import { createFileRoute, Link } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import {
  MousePointerClick,
  FileText,
  Target,
  ArrowRight,
  TrendingUp,
  ShieldAlert,
  ThumbsUp,
  Minus,
  ThumbsDown,
  Loader2,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { fetchReport, type Report } from "@/lib/api"

export const Route = (createFileRoute as any)("/")({ component: Home })

const QUINTET = ["RATU", "CDIA", "MTEL", "BBCA", "ADRO"] as const

const STEPS = [
  {
    icon: MousePointerClick,
    title: "1. Pilih saham",
    desc: "Klik salah satu dari 5 saham di bawah — semuanya perusahaan besar Indonesia.",
  },
  {
    icon: FileText,
    title: "2. Baca ringkasan",
    desc: "Setiap laporan dibuka dengan kesimpulan 1 menit: layak dilirik atau tidak, dan kenapa.",
  },
  {
    icon: Target,
    title: "3. Cek target & risiko",
    desc: "Lihat harga wajar menurut riset, lalu baca risikonya sebelum memutuskan apa pun.",
  },
]

function ratingBadgeVariant(rating: string | null) {
  if (rating === "BUY") return "success" as const
  if (rating === "SELL") return "destructive" as const
  return "secondary" as const
}

function formatIDR(n: number | null) {
  if (n === null || n === undefined) return "—"
  return `Rp ${n.toLocaleString("id-ID")}`
}

function QuintetCard({ ticker }: { ticker: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["report", ticker],
    queryFn: () => fetchReport(ticker),
  })

  const report = data as Report | undefined

  return (
    <Link
      to="/report/$ticker"
      params={{ ticker }}
      className="group block rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="text-lg font-bold tracking-tight text-slate-900">{ticker}</div>
          <div className="mt-0.5 line-clamp-1 text-xs text-slate-500">
            {isLoading ? "Memuat..." : (report?.name ?? ticker)}
          </div>
        </div>
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
        ) : report?.rating ? (
          <Badge variant={ratingBadgeVariant(report.rating)}>{report.rating}</Badge>
        ) : null}
      </div>

      <div className="mt-4">
        {isLoading ? (
          <div className="space-y-2">
            <div className="h-4 w-2/3 animate-pulse rounded bg-slate-100" />
            <div className="h-4 w-1/2 animate-pulse rounded bg-slate-100" />
          </div>
        ) : isError || !report ? (
          <p className="text-xs text-slate-500">Klik untuk membuka laporannya.</p>
        ) : (
          <dl className="space-y-1.5 text-xs">
            <div className="flex justify-between">
              <dt className="text-slate-500">Harga sekarang</dt>
              <dd className="font-semibold text-slate-900">{formatIDR(report.price)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Harga wajar riset</dt>
              <dd className="font-semibold text-slate-900">{formatIDR(report.target)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Potensi naik</dt>
              <dd className="flex items-center gap-1 font-semibold text-emerald-700">
                <TrendingUp className="h-3.5 w-3.5" />
                {report.upside ?? "—"}
              </dd>
            </div>
          </dl>
        )}
      </div>

      <div className="mt-4 flex items-center gap-1 border-t border-slate-100 pt-3 text-xs font-medium text-slate-700 transition-colors group-hover:text-slate-900">
        Baca laporan
        <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
      </div>
    </Link>
  )
}

function Home() {
  return (
    <div className="space-y-10">
      {/* Hero */}
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm sm:p-10">
        <Badge className="mb-4">Riset saham · Bahasa sederhana</Badge>
        <h1 className="max-w-3xl text-2xl font-bold tracking-tight text-slate-900 sm:text-4xl">
          Sektoral.id menerjemahkan riset saham Indonesia yang rumit menjadi ringkasan yang bisa
          dipahami pemula.
        </h1>

        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          {STEPS.map((s) => {
            const Icon = s.icon
            return (
              <div key={s.title} className="rounded-lg border border-slate-200 bg-slate-50/60 p-4">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-900 text-white">
                  <Icon className="h-4.5 w-4.5" />
                </div>
                <div className="mt-3 text-sm font-semibold text-slate-900">{s.title}</div>
                <p className="mt-1 text-xs leading-relaxed text-slate-600">{s.desc}</p>
              </div>
            )
          })}
        </div>

        <div className="mt-8 flex flex-wrap items-center gap-3">
          <a
            href="#saham"
            className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-slate-800"
          >
            Mulai dari 5 saham di bawah
            <ArrowRight className="h-4 w-4" />
          </a>
          <a
            href="#cara-baca"
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
          >
            Cara baca laporan
          </a>
        </div>
      </section>

      {/* Quintet */}
      <section id="saham" className="scroll-mt-20 space-y-4">
        <div>
          <h2 className="text-lg font-bold tracking-tight text-slate-900 sm:text-xl">
            5 saham yang kami ulas tuntas
          </h2>
          <p className="mt-1 max-w-2xl text-sm leading-relaxed text-slate-600">
            Angka di kartu diambil langsung dari laporan terbaru — bukan angka contoh. Klik kartu
            mana pun untuk membaca analisis lengkapnya.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {QUINTET.map((t) => (
            <QuintetCard key={t} ticker={t} />
          ))}
        </div>
      </section>

      {/* Cara baca */}
      <section id="cara-baca" className="scroll-mt-20 space-y-4">
        <div>
          <h2 className="text-lg font-bold tracking-tight text-slate-900 sm:text-xl">
            Cara membaca laporan (2 menit)
          </h2>
          <p className="mt-1 max-w-2xl text-sm leading-relaxed text-slate-600">
            Setiap laporan memakai tiga istilah yang sama. Kalau paham tiga ini, kamu sudah bisa
            membaca semua laporan di sini.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <Card className="border-emerald-200 bg-emerald-50/50">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <ThumbsUp className="h-4 w-4 text-emerald-700" />
                <CardTitle className="text-sm">BUY = layak dilirik</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="text-xs leading-relaxed text-slate-600">
              Riset menilai harga sekarang masih murah dibanding nilai wajarnya. Bukan perintah
              beli — tetap cek apakah cocok dengan uang dan tujuanmu.
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <Minus className="h-4 w-4 text-slate-500" />
                <CardTitle className="text-sm">HOLD = tunggu dulu</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="text-xs leading-relaxed text-slate-600">
              Harganya sudah wajar — tidak murah, tidak mahal. Kalau sudah punya, tidak perlu
              buru-buru jual; kalau belum punya, sabar menunggu harga lebih baik.
            </CardContent>
          </Card>
          <Card className="border-red-200 bg-red-50/50">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <ThumbsDown className="h-4 w-4 text-red-600" />
                <CardTitle className="text-sm">SELL = hati-hati</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="text-xs leading-relaxed text-slate-600">
              Riset menilai harga sekarang sudah kemahalan dibanding nilainya. Bukan perintah
              jual — tapi pahami alasannya sebelum menambah.
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardContent className="grid gap-4 p-5 text-xs leading-relaxed text-slate-600 sm:grid-cols-2">
            <div>
              <CardTitle className="mb-1 text-sm">Potensi naik (upside) itu apa?</CardTitle>
              <CardDescription className="text-xs leading-relaxed">
                Selisih antara harga sekarang dan harga wajar menurut riset. Contoh: harga Rp 1.000,
                harga wajar Rp 1.200 — potensinya 20%. Makin besar belum tentu makin bagus: cek juga
                risikonya.
              </CardDescription>
            </div>
            <div>
              <CardTitle className="mb-1 text-sm">Harga wajar (target) itu apa?</CardTitle>
              <CardDescription className="text-xs leading-relaxed">
                Perkiraan analis tentang nilai pantas saham ini setahun ke depan, dihitung dari
                keuntungan perusahaan. Ini perkiraan, bukan janji — harga asli bisa di atas atau di
                bawahnya.
              </CardDescription>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Disclaimer */}
      <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
        <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-amber-700" />
        <p className="text-xs leading-relaxed text-amber-900">
          <span className="font-semibold">Penting:</span> semua isi Sektoral.id adalah informasi
          dan edukasi, <span className="font-semibold">bukan saran investasi</span>. Investasi
          saham bisa untung dan bisa rugi. Jangan pakai uang kebutuhan harian, dan keputusan
          sepenuhnya tanggung jawabmu.
        </p>
      </div>
    </div>
  )
}
