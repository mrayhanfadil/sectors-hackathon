import { createFileRoute, Link } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import {
  MousePointerClick,
  FileText,
  Target,
  ArrowRight,
  ChevronRight,
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

/** Positive → green, negative → red. Returns "" when unparseable. */
function upsideTone(upside: string | null | undefined): string {
  if (!upside) return ""
  const v = parseFloat(upside.replace(/\./g, "").replace(",", ".").replace(/[^0-9.\-]/g, ""))
  if (Number.isNaN(v)) return ""
  if (v > 0) return "text-[#007f56]"
  if (v < 0) return "text-[#e00]"
  return "text-[#666]"
}

function LogoChip({ ticker }: { ticker: string }) {
  return (
    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-[#eaeaea] bg-[#fafafa] text-[12px] font-bold text-black">
      {ticker.charAt(0)}
    </span>
  )
}

/** Dense market-snapshot strip — live report data only, same query keys as rows (shared cache). */
function MarketStrip() {
  const queries = QUINTET.map((t) =>
    // eslint-disable-next-line react-hooks/rules-of-hooks
    useQuery({ queryKey: ["report", t], queryFn: () => fetchReport(t) }),
  )
  const loading = queries.some((q) => q.isLoading)
  const allFailed = queries.every((q) => q.isError || !q.data)

  return (
    <section aria-label="Ringkasan pasar" className="overflow-hidden rounded-lg border border-[#eaeaea] bg-white">
      <div className="flex items-center justify-between border-b border-[#eaeaea] px-4 py-2">
        <span className="text-[12px] font-medium text-[#666]">Ringkasan pasar · data live</span>
        {loading && <Loader2 className="h-3.5 w-3.5 animate-spin text-[#999]" />}
      </div>
      {allFailed && !loading ? (
        <p className="px-4 py-3 text-[12px] text-[#666]">
          Data pasar belum tersedia — periksa koneksi lalu muat ulang.
        </p>
      ) : (
        <div className="grid grid-cols-2 divide-[#eaeaea] max-sm:divide-y sm:grid-cols-5 sm:divide-x">
          {QUINTET.map((t, i) => {
            const q = queries[i]
            const r = q.data as Report | undefined
            return (
              <Link
                key={t}
                to="/report/$ticker"
                params={{ ticker: t }}
                className="block px-4 py-2.5 transition-colors hover:bg-[#fafafa]"
              >
                <div className="text-[12px] font-bold tracking-tight text-black">{t}</div>
                {q.isLoading ? (
                  <div className="mt-1.5 space-y-1">
                    <div className="h-3 w-16 animate-pulse rounded bg-[#eaeaea]" />
                    <div className="h-3 w-12 animate-pulse rounded bg-[#eaeaea]" />
                  </div>
                ) : !r ? (
                  <div className="tnum mt-1 text-[12px] text-[#999]">—</div>
                ) : (
                  <div className="tnum mt-1 flex items-baseline gap-2 text-[12px]">
                    <span className="font-medium text-black">{formatIDR(r.price)}</span>
                    {r.upside && <span className={`font-medium ${upsideTone(r.upside)}`}>{r.upside}</span>}
                  </div>
                )}
              </Link>
            )
          })}
        </div>
      )}
    </section>
  )
}

function QuintetRow({ ticker }: { ticker: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["report", ticker],
    queryFn: () => fetchReport(ticker),
  })

  const report = data as Report | undefined

  return (
    <Link
      to="/report/$ticker"
      params={{ ticker }}
      className="group grid grid-cols-[1fr_auto] items-center gap-3 px-4 py-3 transition-colors hover:bg-[#fafafa] sm:grid-cols-[minmax(0,2fr)_minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)_auto] sm:gap-4"
    >
      <div className="flex min-w-0 items-center gap-3">
        <LogoChip ticker={ticker} />
        <div className="min-w-0">
          <div className="text-[13px] font-bold tracking-tight text-black">{ticker}</div>
          <div className="truncate text-[12px] text-[#666]">
            {isLoading ? "Memuat..." : (report?.name ?? ticker)}
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="col-span-1 h-4 w-20 animate-pulse rounded bg-[#eaeaea] sm:col-span-3" />
      ) : isError || !report ? (
        <div className="tnum text-[12px] text-[#999] sm:col-span-3">
          Klik untuk membuka laporannya.
        </div>
      ) : (
        <>
          <div className="tnum hidden text-[13px] text-black sm:block">{formatIDR(report.price)}</div>
          <div className="tnum hidden text-[13px] text-black sm:block">{formatIDR(report.target)}</div>
          <div className={`tnum text-right text-[13px] font-medium sm:text-left ${upsideTone(report.upside)}`}>
            {report.upside ?? "—"}
          </div>
          {/* mobile: price under upside */}
          <div className="tnum text-[12px] text-[#666] sm:hidden">{formatIDR(report.price)}</div>
        </>
      )}

      <div className="hidden items-center gap-2 sm:flex">
        {!isLoading && report?.rating ? (
          <Badge variant={ratingBadgeVariant(report.rating)}>{report.rating}</Badge>
        ) : (
          <span className="w-10" />
        )}
        <ChevronRight className="h-4 w-4 text-[#999] transition-transform group-hover:translate-x-0.5 group-hover:text-black" />
      </div>
      <ChevronRight className="h-4 w-4 justify-self-end text-[#999] sm:hidden" />
    </Link>
  )
}

function Home() {
  return (
    <div className="space-y-8">
      <MarketStrip />

      {/* Hero */}
      <section className="py-2">
        <Badge className="mb-3">Riset saham · Bahasa sederhana</Badge>
        <h1 className="max-w-2xl text-[24px] font-bold leading-tight tracking-tight text-black sm:text-[32px]">
          Riset saham Indonesia yang rumit, diterjemahkan untuk pemula.
        </h1>
        <p className="mt-2 max-w-2xl text-[14px] leading-relaxed text-[#666]">
          Sektoral.id merangkum laporan analis menjadi kesimpulan 1 menit: layak dilirik atau
          tidak, dan kenapa — tanpa jargon.
        </p>

        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          {STEPS.map((s) => {
            const Icon = s.icon
            return (
              <div key={s.title} className="rounded-lg border border-[#eaeaea] bg-white p-4">
                <Icon className="h-4 w-4 text-black" />
                <div className="mt-2.5 text-[13px] font-semibold text-black">{s.title}</div>
                <p className="mt-1 text-[12px] leading-relaxed text-[#666]">{s.desc}</p>
              </div>
            )
          })}
        </div>

        <div className="mt-6 flex flex-wrap items-center gap-3">
          <a
            href="#saham"
            className="inline-flex items-center gap-2 rounded-md bg-black px-4 py-2 text-[13px] font-medium text-white transition-colors hover:bg-[#333]"
          >
            Mulai dari 5 saham di bawah
            <ArrowRight className="h-4 w-4" />
          </a>
          <a
            href="#cara-baca"
            className="inline-flex items-center gap-2 rounded-md border border-[#eaeaea] bg-white px-4 py-2 text-[13px] font-medium text-black transition-colors hover:bg-[#fafafa]"
          >
            Cara baca laporan
          </a>
        </div>
      </section>

      {/* Quintet — dense ticker rows */}
      <section id="saham" className="scroll-mt-20 space-y-3">
        <div>
          <h2 className="text-[16px] font-bold tracking-tight text-black">
            5 saham yang kami ulas tuntas
          </h2>
          <p className="mt-1 max-w-2xl text-[13px] leading-relaxed text-[#666]">
            Angka di daftar diambil langsung dari laporan terbaru — bukan angka contoh. Klik baris
            mana pun untuk membaca analisis lengkapnya.
          </p>
        </div>
        <div className="overflow-hidden rounded-lg border border-[#eaeaea] bg-white">
          <div className="hidden grid-cols-[minmax(0,2fr)_minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)_auto] gap-4 border-b border-[#eaeaea] bg-[#fafafa] px-4 py-2 text-[11px] font-medium uppercase tracking-wide text-[#666] sm:grid">
            <span>Saham</span>
            <span>Harga</span>
            <span>Target</span>
            <span>Upside</span>
            <span className="w-16" />
          </div>
          <div className="divide-y divide-[#eaeaea]">
            {QUINTET.map((t) => (
              <QuintetRow key={t} ticker={t} />
            ))}
          </div>
        </div>
      </section>

      {/* Cara baca */}
      <section id="cara-baca" className="scroll-mt-20 space-y-3">
        <div>
          <h2 className="text-[16px] font-bold tracking-tight text-black">
            Cara membaca laporan (2 menit)
          </h2>
          <p className="mt-1 max-w-2xl text-[13px] leading-relaxed text-[#666]">
            Setiap laporan memakai tiga istilah yang sama. Kalau paham tiga ini, kamu sudah bisa
            membaca semua laporan di sini.
          </p>
        </div>

        <div className="grid gap-3 sm:grid-cols-3">
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <ThumbsUp className="h-4 w-4 text-[#007f56]" />
                <CardTitle className="text-sm">BUY = layak dilirik</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="text-xs leading-relaxed text-[#666]">
              Riset menilai harga sekarang masih murah dibanding nilai wajarnya. Bukan perintah
              beli — tetap cek apakah cocok dengan uang dan tujuanmu.
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <Minus className="h-4 w-4 text-[#666]" />
                <CardTitle className="text-sm">HOLD = tunggu dulu</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="text-xs leading-relaxed text-[#666]">
              Harganya sudah wajar — tidak murah, tidak mahal. Kalau sudah punya, tidak perlu
              buru-buru jual; kalau belum punya, sabar menunggu harga lebih baik.
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <ThumbsDown className="h-4 w-4 text-[#e00]" />
                <CardTitle className="text-sm">SELL = hati-hati</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="text-xs leading-relaxed text-[#666]">
              Riset menilai harga sekarang sudah kemahalan dibanding nilainya. Bukan perintah
              jual — tapi pahami alasannya sebelum menambah.
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardContent className="grid gap-4 p-5 text-xs leading-relaxed text-[#666] sm:grid-cols-2">
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
      <div className="flex items-start gap-3 rounded-lg border border-[#eaeaea] border-l-2 border-l-[#f5a623] bg-[#fffdf5] p-4">
        <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-[#8a6d00]" />
        <p className="text-xs leading-relaxed text-[#666]">
          <span className="font-semibold text-black">Penting:</span> semua isi Sektoral.id adalah informasi
          dan edukasi, <span className="font-semibold text-black">bukan saran investasi</span>. Investasi
          saham bisa untung dan bisa rugi. Jangan pakai uang kebutuhan harian, dan keputusan
          sepenuhnya tanggung jawabmu.
        </p>
      </div>
    </div>
  )
}
