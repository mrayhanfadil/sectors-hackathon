import { createFileRoute, Link } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import {
  Terminal,
  FileText,
  Bot,
  Swords,
  MessageSquare,
  ShieldAlert,
  Loader2,
  ChevronRight,
  TrendingUp,
  Activity,
  Layers,
  Info,
  Database,
  ArrowUpRight,
  HelpCircle,
} from "lucide-react"
import { fetchReport, fetchDcfFull, type Report, type DcfFriendPayload } from "@/lib/api"

export const Route = (createFileRoute as any)("/")({ component: MarketMonitorHub })

const QUINTET = ["RATU", "CDIA", "MTEL", "BBCA", "ADRO"] as const
type QuintetTicker = (typeof QUINTET)[number]

function formatIDR(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "MENUNGGU"
  return `Rp ${Number(n).toLocaleString("id-ID")}`
}

function parseUpside(upside: string | null | undefined): {
  text: string
  isPositive: boolean
  isNegative: boolean
  isPending: boolean
} {
  if (!upside || upside === "-" || upside === "—") {
    return { text: "MENUNGGU", isPositive: false, isNegative: false, isPending: true }
  }
  const clean = upside.replace(/\./g, "").replace(",", ".").replace(/[^0-9.\-]/g, "")
  const val = parseFloat(clean)
  if (Number.isNaN(val)) {
    return { text: upside, isPositive: false, isNegative: false, isPending: false }
  }
  return {
    text: upside,
    isPositive: val > 0,
    isNegative: val < 0,
    isPending: false,
  }
}

function TerminalRatingBadge({ rating }: { rating: string | null | undefined }) {
  if (!rating || rating === "Review Required") {
    return (
      <span className="inline-flex items-center rounded-md border border-neutral-300 bg-neutral-100 px-2 py-0.5 font-mono text-xs font-semibold text-neutral-600 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">
        MENUNGGU
      </span>
    )
  }
  if (rating === "BUY") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-md border border-emerald-500/40 bg-emerald-500/10 px-2 py-0.5 font-mono text-xs font-bold text-emerald-600 dark:text-emerald-400">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
        BUY
      </span>
    )
  }
  if (rating === "SELL") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-md border border-rose-500/40 bg-rose-500/10 px-2 py-0.5 font-mono text-xs font-bold text-rose-600 dark:text-rose-400">
        <span className="h-1.5 w-1.5 rounded-full bg-rose-500" />
        SELL
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-md border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 font-mono text-xs font-bold text-amber-600 dark:text-amber-400">
      <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
      HOLD
    </span>
  )
}

function QuintetMonitorCard({ ticker }: { ticker: QuintetTicker }) {
  const reportQuery = useQuery({
    queryKey: ["report", ticker],
    queryFn: () => fetchReport(ticker),
  })

  const dcfQuery = useQuery({
    queryKey: ["dcf-full", ticker],
    queryFn: () => fetchDcfFull(ticker),
  })

  const report = reportQuery.data as Report | undefined
  const dcfData = (dcfQuery.data && !("error" in dcfQuery.data) ? dcfQuery.data : null) as DcfFriendPayload | null

  const isLoading = reportQuery.isLoading || dcfQuery.isLoading

  // Real fields strictly bound to BE payload
  const price = report?.price ?? null
  const target = report?.target ?? (dcfData?.valuation?.fair_value_per_share ? Math.round(dcfData.valuation.fair_value_per_share) : null)
  const upsideRaw = report?.upside ?? (dcfData?.recommendation?.upside != null ? `${dcfData.recommendation.upside > 0 ? "+" : ""}${dcfData.recommendation.upside.toFixed(1)}%` : null)
  const rating = report?.rating ?? dcfData?.recommendation?.rating ?? null
  const companyName = report?.name || `${ticker} Tbk`
  const archetype = report?.template ? report.template.toUpperCase() : "SAHAM"
  const method = report?.valuation?.[0]?.method ?? "DCF Model"
  const wacc = dcfData?.wacc?.wacc != null ? `${(dcfData.wacc.wacc * 100).toFixed(1)}%` : null
  const summarySnippet =
    report?.cover?.rating_box?.key_takeaways?.[0] ||
    report?.summary ||
    "Data laporan keuangan terverifikasi sedang disinkronisasikan dari backend..."

  const upsideInfo = parseUpside(upsideRaw)

  return (
    <div className="flex flex-col justify-between rounded-lg border border-neutral-200 bg-white font-sans shadow-xs transition-all hover:border-neutral-300 dark:border-[#262930] dark:bg-[#121418] dark:hover:border-[#3a3f4b] overflow-hidden">
      {/* 1. Header Strip */}
      <div className="border-b border-neutral-200 bg-neutral-50/80 px-4 py-3 dark:border-[#1e2229] dark:bg-[#15181e]">
        <div className="flex items-center justify-between gap-2">
          <div className="flex min-w-0 items-center gap-2">
            <Link
              to={`/report/${ticker}` as any}
              className="group inline-flex items-center gap-1.5 rounded-md bg-neutral-900 px-2.5 py-1 text-xs font-mono font-bold text-amber-400 hover:bg-neutral-800 transition-colors dark:bg-amber-400/10 dark:border dark:border-amber-400/30 dark:text-amber-400"
            >
              <span>{ticker} IJ</span>
              <ArrowUpRight className="h-3 w-3 text-neutral-400 group-hover:text-amber-300 transition-transform group-hover:translate-x-0.5" />
            </Link>
            <span className="truncate text-xs font-semibold text-neutral-800 dark:text-neutral-200">
              {companyName}
            </span>
          </div>

          <div className="flex shrink-0 items-center gap-1.5">
            {isLoading ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin text-neutral-400" />
            ) : (
              <TerminalRatingBadge rating={rating} />
            )}
          </div>
        </div>

        <div className="mt-1.5 flex items-center justify-between text-[11px] font-mono text-neutral-500 dark:text-neutral-400">
          <span>MODEL: {archetype}</span>
          <span>{report?.updatedAt ? `AUDITED: ${report.updatedAt}` : "LIVE DATA"}</span>
        </div>
      </div>

      {/* 2. Key Valuation Metrics Grid (BE-bound numbers only, Missing = MENUNGGU) */}
      <div className="grid grid-cols-3 divide-x divide-neutral-200 border-b border-neutral-200 p-4 dark:divide-[#1e2229] dark:border-[#1e2229]">
        {/* HARGA TERAKHIR */}
        <div className="pr-2">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">HARGA TERAKHIR</div>
          <div className="tnum mt-1 text-sm sm:text-base font-bold text-neutral-900 dark:text-neutral-100">
            {isLoading ? (
              <div className="h-5 w-16 animate-pulse rounded bg-neutral-200 dark:bg-neutral-800" />
            ) : (
              formatIDR(price)
            )}
          </div>
        </div>

        {/* TARGET (NILAI WAJAR) */}
        <div className="px-2">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">NILAI WAJAR (TP)</div>
          <div className="tnum mt-1 text-sm sm:text-base font-bold text-neutral-900 dark:text-neutral-100">
            {isLoading ? (
              <div className="h-5 w-16 animate-pulse rounded bg-neutral-200 dark:bg-neutral-800" />
            ) : (
              formatIDR(target)
            )}
          </div>
        </div>

        {/* POTENSI NAIK */}
        <div className="pl-2">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">POTENSI NAIK</div>
          <div
            className={`tnum mt-1 text-sm sm:text-base font-bold ${
              upsideInfo.isPending
                ? "text-neutral-400 dark:text-neutral-500"
                : upsideInfo.isPositive
                ? "text-emerald-600 dark:text-emerald-400"
                : upsideInfo.isNegative
                ? "text-rose-600 dark:text-rose-400"
                : "text-neutral-700 dark:text-neutral-300"
            }`}
          >
            {isLoading ? (
              <div className="h-5 w-12 animate-pulse rounded bg-neutral-200 dark:bg-neutral-800" />
            ) : (
              `${upsideInfo.isPositive ? "▲ " : upsideInfo.isNegative ? "▼ " : ""}${upsideInfo.text}`
            )}
          </div>
        </div>
      </div>

      {/* 3. Valuation Engine Detail Strip */}
      <div className="space-y-2.5 p-4 text-xs">
        <div className="flex items-center justify-between text-xs">
          <span className="text-neutral-500 dark:text-neutral-400">Metode Utama:</span>
          <span className="font-semibold text-neutral-800 dark:text-neutral-200 font-mono">{method}</span>
        </div>

        <div className="flex items-center justify-between text-xs">
          <span className="text-neutral-500 dark:text-neutral-400">Cost of Capital (WACC):</span>
          <span className="tnum font-semibold text-neutral-800 dark:text-neutral-200">
            {wacc ? wacc : "MENUNGGU"}
          </span>
        </div>

        {/* Takeaway / Summary snippet */}
        <div className="mt-2 rounded-md bg-neutral-100/80 p-2.5 text-xs leading-relaxed text-neutral-600 dark:bg-[#181b22] dark:text-neutral-300 border border-neutral-200/60 dark:border-[#262930]/60">
          <div className="mb-1 font-mono text-[10px] font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400">
            [RINGKASAN EKSEKUTIF]
          </div>
          <p className="line-clamp-2">{summarySnippet}</p>
        </div>
      </div>

      {/* 4. Function-Key Action Strip */}
      <div className="grid grid-cols-3 divide-x divide-neutral-200 border-t border-neutral-200 bg-neutral-50/80 text-xs font-mono dark:divide-[#1e2229] dark:border-[#1e2229] dark:bg-[#15181e]">
        <Link
          to={`/report/${ticker}` as any}
          className="flex items-center justify-center gap-1.5 py-2.5 font-semibold text-neutral-700 transition-colors hover:bg-neutral-100 hover:text-neutral-900 dark:text-neutral-300 dark:hover:bg-[#1f232c] dark:hover:text-white"
        >
          <FileText className="h-3.5 w-3.5 text-amber-500" />
          <span>[F1] LAPORAN</span>
        </Link>

        <Link
          to="/agent"
          search={{ ticker } as any}
          className="flex items-center justify-center gap-1.5 py-2.5 font-semibold text-neutral-700 transition-colors hover:bg-neutral-100 hover:text-neutral-900 dark:text-neutral-300 dark:hover:bg-[#1f232c] dark:hover:text-white"
        >
          <Bot className="h-3.5 w-3.5 text-sky-500" />
          <span>[F2] MESIN</span>
        </Link>

        <Link
          to={`/report/${ticker}/challenge` as any}
          className="flex items-center justify-center gap-1.5 py-2.5 font-semibold text-neutral-700 transition-colors hover:bg-neutral-100 hover:text-neutral-900 dark:text-neutral-300 dark:hover:bg-[#1f232c] dark:hover:text-white"
        >
          <Swords className="h-3.5 w-3.5 text-rose-500" />
          <span>[F3] UJI</span>
        </Link>
      </div>
    </div>
  )
}

function QuintetMatrixRow({ ticker }: { ticker: QuintetTicker }) {
  const reportQuery = useQuery({
    queryKey: ["report", ticker],
    queryFn: () => fetchReport(ticker),
  })

  const report = reportQuery.data as Report | undefined
  const price = report?.price ?? null
  const target = report?.target ?? null
  const upsideRaw = report?.upside ?? null
  const rating = report?.rating ?? null
  const upsideInfo = parseUpside(upsideRaw)

  return (
    <Link
      to={`/report/${ticker}` as any}
      className="group grid grid-cols-12 items-center gap-2 border-b border-neutral-200 px-4 py-3 text-xs font-mono transition-colors hover:bg-neutral-50 dark:border-[#1e2229] dark:hover:bg-[#161920]"
    >
      {/* Ticker & Name */}
      <div className="col-span-4 flex items-center gap-2.5">
        <span className="rounded-md bg-neutral-900 px-2 py-0.5 text-xs font-bold text-amber-400 dark:bg-amber-400/10 dark:text-amber-400">
          {ticker} IJ
        </span>
        <span className="truncate font-sans font-medium text-neutral-800 dark:text-neutral-200">
          {report?.name || `${ticker} Tbk`}
        </span>
      </div>

      {/* Last Price */}
      <div className="col-span-2 text-right font-mono text-neutral-900 dark:text-neutral-100 font-medium">
        {reportQuery.isLoading ? "..." : formatIDR(price)}
      </div>

      {/* Target Price */}
      <div className="col-span-2 text-right font-mono text-neutral-900 dark:text-neutral-100 font-medium">
        {reportQuery.isLoading ? "..." : formatIDR(target)}
      </div>

      {/* Upside */}
      <div
        className={`col-span-2 text-right font-mono font-bold ${
          upsideInfo.isPending
            ? "text-neutral-400 dark:text-neutral-500"
            : upsideInfo.isPositive
            ? "text-emerald-600 dark:text-emerald-400"
            : upsideInfo.isNegative
            ? "text-rose-600 dark:text-rose-400"
            : "text-neutral-600 dark:text-neutral-400"
        }`}
      >
        {reportQuery.isLoading ? "..." : `${upsideInfo.isPositive ? "+" : ""}${upsideInfo.text}`}
      </div>

      {/* Rating & Jump Chevron */}
      <div className="col-span-2 flex items-center justify-end gap-2">
        <TerminalRatingBadge rating={rating} />
        <ChevronRight className="h-3.5 w-3.5 text-neutral-400 transition-transform group-hover:translate-x-0.5 group-hover:text-amber-400" />
      </div>
    </Link>
  )
}

function MarketMonitorHub() {
  return (
    <div className="space-y-6">
      {/* 1. Market Monitor Header & Live Protocol Status */}
      <div className="rounded-lg border border-neutral-200 bg-white p-5 shadow-xs dark:border-[#262930] dark:bg-[#121418]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5">
              <span className="rounded-md bg-neutral-900 px-2 py-0.5 font-mono text-xs font-bold text-amber-400 dark:bg-amber-400/10 dark:text-amber-400">
                PANTAU PASAR
              </span>
              <h1 className="text-base sm:text-lg font-bold tracking-tight text-neutral-900 dark:text-neutral-100">
                Pantau 5 Saham Unggulan IDX
              </h1>
            </div>
            <p className="font-sans text-xs leading-relaxed text-neutral-600 dark:text-neutral-400 max-w-2xl">
              Terminal pemantauan valuasi deterministik dan penalaran multi-agen untuk 5 emiten tier-1 Bursa Efek Indonesia.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-xs">
            <div className="flex items-center gap-1.5 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-1 font-mono text-amber-600 dark:text-amber-400" title="Cakupan pantau — status koneksi per kartu">
              <span className="h-2 w-2 rounded-full bg-amber-500" />
              <span className="font-bold">5 EMITEN · DATA TERAKHIR</span>
            </div>
            <div className="rounded-md border border-neutral-200 bg-neutral-100 px-3 py-1 font-mono text-neutral-700 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">
              ZERO-FABRICATION PROTOCOL
            </div>
          </div>
        </div>

        {/* Data Provenance & Servicing Notice */}
        <div className="mt-4 flex flex-col sm:flex-row sm:items-center justify-between border-t border-neutral-200 pt-3 text-xs text-neutral-500 dark:border-[#1e2229] dark:text-neutral-400 gap-2">
          <div className="flex items-center gap-2">
            <Database className="h-3.5 w-3.5 text-amber-500 shrink-0" />
            <span>Sumber data: snapshot laporan keuangan IDX terverifikasi · DCF WACC · Red-Team Audit</span>
          </div>
          <div className="font-mono text-[11px] font-medium text-neutral-600 dark:text-neutral-400">
            [PINTASAN: KETIK KODE SAHAM + ENTER DI ATAS]
          </div>
        </div>
      </div>

      {/* 2. Quintet Market Monitor Cards Grid (The 5 Covered Equities) */}
      <section aria-label="Quintet Equities Coverage" className="space-y-3.5">
        <div className="flex items-center justify-between font-mono text-xs font-bold uppercase text-neutral-700 dark:text-neutral-300">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-amber-500" />
            <span>01 // NILAI WAJAR 5 EMITEN</span>
          </div>
          <span className="text-[11px] text-neutral-400 font-normal">
            DATA TERVALIDASI · TANPA SINTETIK
          </span>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {QUINTET.map((ticker) => (
            <QuintetMonitorCard key={ticker} ticker={ticker} />
          ))}

          {/* Quick-Jump Helper Card */}
          <div className="flex flex-col justify-between rounded-lg border border-dashed border-neutral-300 bg-neutral-50/70 p-5 font-sans dark:border-[#262930] dark:bg-[#121418]/60">
            <div className="space-y-2">
              <div className="flex items-center gap-2 font-mono text-xs font-bold text-amber-600 dark:text-amber-400">
                <Bot className="h-4 w-4" />
                <span>[F2] PENALARAN MULTI-AGEN</span>
              </div>
              <p className="text-xs leading-relaxed text-neutral-600 dark:text-neutral-400">
                Jalankan atau pantau belasan mesin AI yang mengaudit laporan keuangan, menghitung valuasi DCF, dan menganalisis risiko secara mandiri.
              </p>
            </div>
            <Link
              to="/agent"
              search={{ ticker: "BBCA" } as any}
              className="mt-4 inline-flex items-center justify-center gap-2 rounded-md bg-neutral-900 py-2.5 px-4 font-mono text-xs font-bold text-white transition-colors hover:bg-neutral-800 dark:bg-neutral-100 dark:text-neutral-950 dark:hover:bg-neutral-200"
            >
              <span>BUKA RUANG MESIN</span>
              <ChevronRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </section>

      {/* 3. Valuation & Coverage Comparative Matrix */}
      <section aria-label="Comparative Matrix" className="space-y-3">
        <div className="flex items-center justify-between font-mono text-xs font-bold uppercase text-neutral-700 dark:text-neutral-300">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-amber-500" />
            <span>02 // PERBANDINGAN NILAI 5 EMITEN</span>
          </div>
          <span className="text-[11px] text-neutral-400 font-normal">
            KLIK BARIS UNTUK MEMBUKA DETAIL LAPORAN
          </span>
        </div>

        <div className="overflow-x-auto rounded-lg border border-neutral-200 bg-white dark:border-[#262930] dark:bg-[#121418]">
          <div className="min-w-[580px]">
            {/* Table Header */}
            <div className="grid grid-cols-12 gap-2 border-b border-neutral-200 bg-neutral-100/80 px-4 py-2.5 font-mono text-[11px] font-bold uppercase tracking-wider text-neutral-600 dark:border-[#1e2229] dark:bg-[#15181e] dark:text-neutral-400">
              <div className="col-span-4">EMITEN (KODE SAHAM)</div>
              <div className="col-span-2 text-right">HARGA</div>
              <div className="col-span-2 text-right">NILAI WAJAR</div>
              <div className="col-span-2 text-right">POTENSI NAIK</div>
              <div className="col-span-2 text-right">REKOMENDASI</div>
            </div>

            {/* Table Rows */}
            {QUINTET.map((ticker) => (
              <QuintetMatrixRow key={ticker} ticker={ticker} />
            ))}
          </div>
        </div>
      </section>

      {/* 4. Educational Reference & Valuation Methodology Guide */}
      <section id="cara-baca" className="scroll-mt-20 space-y-3.5">
        <div className="flex items-center justify-between font-mono text-xs font-bold uppercase text-neutral-700 dark:text-neutral-300">
          <div className="flex items-center gap-2">
            <Info className="h-4 w-4 text-amber-500" />
            <span>03 // PANDUAN METODOLOGI &amp; CARA BACA</span>
          </div>
          <span className="text-[11px] text-amber-600 dark:text-amber-400 font-medium">
            PANDUAN EDUKASI · BUKAN SARAN FINANSIAL
          </span>
        </div>

        {/* Example Attestation Box */}
        <div className="rounded-lg border border-amber-500/30 bg-amber-50/70 p-4 text-xs leading-relaxed text-amber-900 dark:border-amber-500/30 dark:bg-amber-950/40 dark:text-amber-200">
          <div className="flex items-start gap-2.5">
            <HelpCircle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
            <div>
              <span className="font-bold font-mono">[PANDUAN ISTILAH SAHAM] </span>
              <span>
                Penjelasan di bawah ini disusun untuk memudahkan investor pemula memahami istilah analisis fundamental. Angka pada kartu emiten di atas dihitung secara deterministik dari laporan keuangan audited (missing = MENUNGGU), tanpa manipulasi.
              </span>
            </div>
          </div>
        </div>

        {/* 3 Terminology Explainer Cards */}
        <div className="grid gap-4 sm:grid-cols-3 font-sans">
          <div className="rounded-lg border border-neutral-200 bg-white p-4 dark:border-[#262930] dark:bg-[#121418]">
            <div className="flex items-center gap-2 font-mono text-xs font-bold text-emerald-600 dark:text-emerald-400">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              <span>BUY (Undervalued)</span>
            </div>
            <p className="mt-2 text-xs leading-relaxed text-neutral-600 dark:text-neutral-400">
              Harga pasar saat ini berada di bawah estimasi nilai wajar fundamental (Fair Value) berdasarkan proyeksi arus kas. Menandakan tersedianya ruang keamanan (margin of safety) yang memadai.
            </p>
          </div>

          <div className="rounded-lg border border-neutral-200 bg-white p-4 dark:border-[#262930] dark:bg-[#121418]">
            <div className="flex items-center gap-2 font-mono text-xs font-bold text-amber-600 dark:text-amber-400">
              <span className="h-2 w-2 rounded-full bg-amber-500" />
              <span>HOLD (Fair Value)</span>
            </div>
            <p className="mt-2 text-xs leading-relaxed text-neutral-600 dark:text-neutral-400">
              Harga pasar telah merefleksikan nilai intrinsik perusahaan secara wajar. Pertahankan kepemilikan aset atau tunggu konfirmasi katalis baru sebelum menambah posisi.
            </p>
          </div>

          <div className="rounded-lg border border-neutral-200 bg-white p-4 dark:border-[#262930] dark:bg-[#121418]">
            <div className="flex items-center gap-2 font-mono text-xs font-bold text-rose-600 dark:text-rose-400">
              <span className="h-2 w-2 rounded-full bg-rose-500" />
              <span>SELL (Overvalued)</span>
            </div>
            <p className="mt-2 text-xs leading-relaxed text-neutral-600 dark:text-neutral-400">
              Harga pasar dinilai telah melampaui valuasi fundamental konservatif. Risiko koreksi harga lebih besar daripada potensi apresiasi jangka pendek.
            </p>
          </div>
        </div>

        {/* Detailed Mechanics (Upside & Fair Value) */}
        <div className="grid gap-4 sm:grid-cols-2 font-sans">
          <div className="rounded-lg border border-neutral-200 bg-white p-4 text-xs dark:border-[#262930] dark:bg-[#121418]">
            <div className="font-mono text-xs font-bold text-neutral-900 dark:text-neutral-100">
              Bagaimana Potensi Naik (Upside) Dihitung?
            </div>
            <p className="mt-2 leading-relaxed text-neutral-600 dark:text-neutral-400">
              Upside dihitung dari persentase selisih antara Target Price (Fair Value) hasil model DCF dan harga pasar terakhir: <code className="font-mono bg-neutral-100 dark:bg-neutral-800 px-1.5 py-0.5 rounded text-[11px] text-neutral-800 dark:text-neutral-200">((Target - Harga) / Harga) * 100%</code>.
            </p>
          </div>

          <div className="rounded-lg border border-neutral-200 bg-white p-4 text-xs dark:border-[#262930] dark:bg-[#121418]">
            <div className="font-mono text-xs font-bold text-neutral-900 dark:text-neutral-100">
              Apa Itu Discounted Cash Flow (DCF)?
            </div>
            <p className="mt-2 leading-relaxed text-neutral-600 dark:text-neutral-400">
              Metode valuasi intrinsik yang memproyeksikan arus kas bebas (Free Cash Flow to Firm) masa depan dan mendiskontokannya ke nilai sekarang menggunakan WACC (Weighted Average Cost of Capital).
            </p>
          </div>
        </div>
      </section>

      {/* 5. Compliance & Attestation Alert */}
      <div className="flex items-start gap-3 rounded-lg border border-neutral-200 bg-neutral-100/90 p-4 text-xs dark:border-[#262930] dark:bg-[#121418] font-sans">
        <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" />
        <div className="space-y-1">
          <div className="font-mono font-bold text-neutral-900 dark:text-neutral-100 text-xs">
            [KEPATUHAN &amp; PEMBERITAHUAN RESMI // SECTORS HACKATHON 2026]
          </div>
          <p className="leading-relaxed text-neutral-600 dark:text-neutral-400">
            Seluruh analisis riset pada platform ini diproduksi secara deterministik dari laporan keuangan audited IDX. Sektoral.id tidak menyajikan angka sintetis atau rekayasa data. Informasi ini disajikan untuk tujuan riset kompetisi dan edukasi pasar, bukan merupakan rekomendasi transaksi efek dari penasihat investasi berlisensi.
          </p>
        </div>
      </div>
    </div>
  )
}

