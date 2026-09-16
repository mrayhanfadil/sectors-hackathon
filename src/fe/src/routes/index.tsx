import { createFileRoute, Link } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import {
  Loader2,
  ChevronRight,
  Database,
  ArrowUpRight,
  HelpCircle,
  ShieldAlert,
} from "lucide-react"
import {
  fetchReport,
  fetchDcfFull,
  fetchRunsSummary,
  type Report,
  type DcfFriendPayload,
  type RunsSummary,
  type RunsSummaryTicker,
} from "@/lib/api"

export const Route = (createFileRoute as any)("/")({ component: MarketMonitorHub })

// The hub lists only what has actually run. A ticker whose pipeline never ran, or whose last attempt failed, has no
// report behind it - listing it just hands the reader an error page.
const VISIBLE_STATUS = new Set(["running", "completed"])
// Four uppercase letters, IDX-style. The run store also holds rows from the test suite (DT1ABD957, LOCK69786C,
// OTH5F0F99) which are not emiten anything and would otherwise flood the list.
const REAL_CODE = /^[A-Z]{4}$/

function visibleTickers(summary: RunsSummary | undefined): RunsSummaryTicker[] {
  if (!summary?.tickers) return []
  return Object.values(summary.tickers)
    .filter((t) => REAL_CODE.test(String(t.ticker)) && VISIBLE_STATUS.has(String(t.latest_run?.status)))
    .sort((a, b) => {
      const rank = (s?: string | null) => (s === "running" ? 0 : 1)
      const byStatus = rank(a.latest_run?.status) - rank(b.latest_run?.status)
      return byStatus !== 0 ? byStatus : (b.latest_run?.started_at ?? 0) - (a.latest_run?.started_at ?? 0)
    })
}

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
  if (!upside || upside === "-" || upside === "-") {
    return { text: "MENUNGGU", isPositive: false, isNegative: false, isPending: true }
  }
  const clean = upside.replace(/\./g, "").replace(",", ".").replace(/[^0-9.-]/g, "")
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

function RatingBadge({ rating }: { rating: string | null | undefined }) {
  if (!rating || rating === "Review Required") {
    return (
      <span className="inline-flex items-center rounded-md border border-[#E7E3DA] bg-[#E7E3DA]/40 px-2.5 py-0.5 text-xs font-medium text-[#6B6659] dark:border-[#2A2822] dark:bg-[#2A2822]/60 dark:text-[#A8A296]">
        MENUNGGU
      </span>
    )
  }
  if (rating === "BUY") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-md border border-[#157F3D]/20 bg-[#157F3D]/10 px-2.5 py-0.5 text-xs font-semibold text-[#157F3D] dark:border-[#157F3D]/40 dark:bg-[#157F3D]/20 dark:text-[#4ADE80]">
        <span className="h-1.5 w-1.5 rounded-full bg-[#157F3D] dark:bg-[#4ADE80]" />
        BUY
      </span>
    )
  }
  if (rating === "SELL") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-md border border-[#B4232A]/20 bg-[#B4232A]/10 px-2.5 py-0.5 text-xs font-semibold text-[#B4232A] dark:border-[#B4232A]/40 dark:bg-[#B4232A]/20 dark:text-[#F87171]">
        <span className="h-1.5 w-1.5 rounded-full bg-[#B4232A] dark:bg-[#F87171]" />
        SELL
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-md border border-[#A16207]/20 bg-[#A16207]/10 px-2.5 py-0.5 text-xs font-semibold text-[#A16207] dark:border-[#A16207]/40 dark:bg-[#A16207]/20 dark:text-[#FBBF24]">
      <span className="h-1.5 w-1.5 rounded-full bg-[#A16207] dark:bg-[#FBBF24]" />
      HOLD
    </span>
  )
}

function CompanyCard({ ticker, pipeline }: { ticker: string; pipeline?: RunsSummaryTicker }) {
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
  const archetype = report?.template ? report.template : "Saham"
  const method = report?.valuation?.[0]?.method ?? "DCF Model"
  const wacc = dcfData?.wacc?.wacc != null ? `${(dcfData.wacc.wacc * 100).toFixed(1)}%` : null
  const summarySnippet =
    report?.cover?.rating_box?.key_takeaways?.[0] ||
    report?.summary ||
    "Data laporan keuangan terverifikasi sedang disinkronisasikan dari backend..."

  const upsideInfo = parseUpside(upsideRaw)

  const runStatus = String(pipeline?.latest_run?.status ?? "")
  const pipelineLine = runStatus
    ? `${runStatus === "running" ? "Sedang diproses" : "Selesai"}${pipeline?.total_runs ? ` · ${pipeline.total_runs} putaran` : ""}`
    : report?.updatedAt
      ? `Diperbarui: ${report.updatedAt}`
      : "Data snapshot"

  return (
    <div className="flex flex-col justify-between rounded-xl border border-[#E7E3DA] bg-white p-5 shadow-xs transition-all hover:border-[#0E6E63]/40 dark:border-[#2A2822] dark:bg-[#1B1A16] dark:hover:border-[#4FD1B5]/40">
      <div className="space-y-4">
        {/* 1. Header Strip */}
        <div className="flex items-start justify-between gap-3 border-b border-[#E7E3DA] pb-3 dark:border-[#2A2822]">
          <div>
            <div className="flex items-center gap-2">
              <Link
                to={`/report/${ticker}` as any}
                className="text-base font-bold text-[#1C1B17] hover:text-[#0E6E63] dark:text-[#EDEAE3] dark:hover:text-[#4FD1B5] transition-colors"
              >
                {ticker}
              </Link>
              <span className="text-xs text-[#6B6659] dark:text-[#A8A296]">
                · {archetype}
              </span>
            </div>
            <div className="flex items-center gap-2 mt-0.5 text-xs text-[#6B6659] dark:text-[#A8A296]">
              <span className="truncate">{companyName}</span>
              <span>·</span>
              <span className="shrink-0">{pipelineLine}</span>
            </div>
          </div>

          <div className="shrink-0">
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin text-[#6B6659] dark:text-[#A8A296]" />
            ) : (
              <RatingBadge rating={rating} />
            )}
          </div>
        </div>

        {/* 2. Key Valuation Metrics Grid */}
        <div className="grid grid-cols-3 gap-2 rounded-lg bg-[#FBFAF7] p-3 text-xs dark:bg-[#14130F] border border-[#E7E3DA] dark:border-[#2A2822]">
          <div>
            <div className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">Harga pasar</div>
            <div className="tnum mt-1 font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
              {isLoading ? "..." : formatIDR(price)}
            </div>
          </div>

          <div>
            <div className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">Nilai wajar</div>
            <div className="tnum mt-1 font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
              {isLoading ? "..." : formatIDR(target)}
            </div>
          </div>

          <div>
            <div className="text-[11px] text-[#6B6659] dark:text-[#A8A296]">Potensi</div>
            <div
              className={`tnum mt-1 font-semibold ${
                upsideInfo.isPending
                  ? "text-[#6B6659] dark:text-[#A8A296]"
                  : upsideInfo.isPositive
                  ? "text-[#157F3D] dark:text-[#4ADE80]"
                  : upsideInfo.isNegative
                  ? "text-[#B4232A] dark:text-[#F87171]"
                  : "text-[#1C1B17] dark:text-[#EDEAE3]"
              }`}
            >
              {isLoading
                ? "..."
                : upsideInfo.isPending
                ? "MENUNGGU"
                : `${upsideInfo.isPositive ? "+" : ""}${upsideInfo.text}`}
            </div>
          </div>
        </div>

        {/* 3. Valuation Details */}
        <div className="space-y-1.5 text-xs text-[#6B6659] dark:text-[#A8A296]">
          <div className="flex items-center justify-between">
            <span>Metode:</span>
            <span className="font-medium text-[#1C1B17] dark:text-[#EDEAE3]">{method}</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Cost of capital (WACC):</span>
            <span className="tnum font-medium text-[#1C1B17] dark:text-[#EDEAE3]">
              {wacc ? wacc : "MENUNGGU"}
            </span>
          </div>
        </div>

        {/* 4. Takeaway / Summary snippet */}
        <div className="rounded-lg bg-[#FBFAF7] p-3 text-xs leading-relaxed text-[#6B6659] dark:bg-[#14130F] dark:text-[#A8A296] border border-[#E7E3DA] dark:border-[#2A2822]">
          <p className="line-clamp-2">{summarySnippet}</p>
        </div>
      </div>

      {/* 5. Action Links */}
      <div className="mt-4 pt-3 border-t border-[#E7E3DA] dark:border-[#2A2822] flex items-center justify-between gap-2">
        <Link
          to={`/report/${ticker}` as any}
          className="inline-flex items-center gap-1.5 rounded-lg bg-[#0E6E63] px-3.5 py-1.5 text-xs font-medium text-white hover:bg-[#0C5A52] dark:bg-[#0E6E63] dark:hover:bg-[#128275] transition-colors"
        >
          <span>Buka laporan</span>
          <ArrowUpRight className="h-3.5 w-3.5" />
        </Link>

        <div className="flex items-center gap-1.5">
          <Link
            to="/agent"
            search={{ ticker } as any}
            className="rounded-lg border border-[#E7E3DA] bg-white px-2.5 py-1.5 text-xs text-[#6B6659] hover:text-[#1C1B17] hover:bg-[#FBFAF7] dark:border-[#2A2822] dark:bg-[#1B1A16] dark:text-[#A8A296] dark:hover:text-[#EDEAE3] dark:hover:bg-[#23211B] transition-colors"
          >
            Mesin
          </Link>
          <Link
            to={`/report/${ticker}/challenge` as any}
            className="rounded-lg border border-[#E7E3DA] bg-white px-2.5 py-1.5 text-xs text-[#6B6659] hover:text-[#1C1B17] hover:bg-[#FBFAF7] dark:border-[#2A2822] dark:bg-[#1B1A16] dark:text-[#A8A296] dark:hover:text-[#EDEAE3] dark:hover:bg-[#23211B] transition-colors"
          >
            Uji silang
          </Link>
        </div>
      </div>
    </div>
  )
}

function CompanyTableRow({ ticker }: { ticker: string }) {
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
    <tr className="hover:bg-[#FBFAF7] dark:hover:bg-[#23211B] transition-colors">
      <td className="py-3 px-4">
        <Link to={`/report/${ticker}` as any} className="flex items-center gap-2 group">
          <span className="font-bold text-[#1C1B17] dark:text-[#EDEAE3] group-hover:text-[#0E6E63] dark:group-hover:text-[#4FD1B5] transition-colors">
            {ticker}
          </span>
          <span className="text-[#6B6659] dark:text-[#A8A296] truncate max-w-[180px] sm:max-w-none">
            {report?.name || `${ticker} Tbk`}
          </span>
        </Link>
      </td>
      <td className="py-3 px-4 text-right tnum font-medium text-[#1C1B17] dark:text-[#EDEAE3]">
        {reportQuery.isLoading ? "..." : formatIDR(price)}
      </td>
      <td className="py-3 px-4 text-right tnum font-medium text-[#1C1B17] dark:text-[#EDEAE3]">
        {reportQuery.isLoading ? "..." : formatIDR(target)}
      </td>
      <td
        className={`py-3 px-4 text-right tnum font-semibold ${
          upsideInfo.isPending
            ? "text-[#6B6659] dark:text-[#A8A296]"
            : upsideInfo.isPositive
            ? "text-[#157F3D] dark:text-[#4ADE80]"
            : upsideInfo.isNegative
            ? "text-[#B4232A] dark:text-[#F87171]"
            : "text-[#1C1B17] dark:text-[#EDEAE3]"
        }`}
      >
        {reportQuery.isLoading
          ? "..."
          : upsideInfo.isPending
          ? "MENUNGGU"
          : `${upsideInfo.isPositive ? "+" : ""}${upsideInfo.text}`}
      </td>
      <td className="py-3 px-4 text-center">
        <RatingBadge rating={rating} />
      </td>
      <td className="py-3 px-4 text-right">
        <Link
          to={`/report/${ticker}` as any}
          className="inline-flex items-center gap-1 text-xs font-medium text-[#0E6E63] hover:underline dark:text-[#4FD1B5]"
        >
          <span>Laporan</span>
          <ChevronRight className="h-3.5 w-3.5" />
        </Link>
      </td>
    </tr>
  )
}

function MarketMonitorHub() {
  // One call tells us which tickers have a pipeline that actually ran, and in what state. Polled so a live run shows up.
  const runsQuery = useQuery({
    queryKey: ["runs-summary"],
    queryFn: fetchRunsSummary,
    refetchInterval: 15000,
  })
  const summary = runsQuery.data as RunsSummary | undefined
  const listed = visibleTickers(summary)
  const listedCount = listed.length
  // A finished pipeline is not a readable report: 8 of the 9 tickers whose run completed answer 422 because their
  // assumptions file does not exist. The backend marks that per ticker (`report_ready`), so no per-ticker probe is
  // needed here - probing used to leave one console error per unavailable ticker.
  const readyKnown = listed.some((t) => typeof t.report_ready === "boolean")
  const shown = listed.filter((t) => t.report_ready === true)
  const shownCount = shown.length
  const runningCount = shown.filter((t) => t.latest_run?.status === "running").length
  const completedCount = shownCount - runningCount
  const pendingReportCount = listedCount - shownCount
  const hiddenCount = Math.max(0, Object.keys(summary?.tickers ?? {}).length - listedCount)
  const jumpTicker = shown[0] ? String(shown[0].ticker) : null

  return (
    <div className="space-y-8">
      {/* 1. Market Monitor Header & Overview */}
      <div className="rounded-xl border border-[#E7E3DA] bg-white p-6 shadow-xs dark:border-[#2A2822] dark:bg-[#1B1A16]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-2">
            <h1 className="text-2xl sm:text-3xl font-normal tracking-tight text-[#1C1B17] dark:text-[#EDEAE3] font-['Newsreader',serif]">
              {runsQuery.isLoading
                ? "Menyiapkan daftar emiten…"
                : shownCount > 0
                  ? `Ringkasan pasar · ${shownCount} emiten siap dibaca`
                  : "Ringkasan pasar"}
            </h1>
            <p className="text-xs sm:text-sm leading-relaxed text-[#6B6659] dark:text-[#A8A296] max-w-2xl">
              Hanya emiten yang analisisnya telah selesai atau sedang diproses dan laporannya siap dibuka yang ditampilkan di sini.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-xs">
            <div className="inline-flex items-center gap-2 rounded-lg border border-[#E7E3DA] bg-[#FBFAF7] px-3 py-1.5 font-medium text-[#1C1B17] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#EDEAE3]">
              <span className="h-2 w-2 rounded-full bg-[#0E6E63] dark:bg-[#4FD1B5]" />
              <span>
                {runningCount} sedang diproses · {completedCount} siap
              </span>
            </div>
          </div>
        </div>

        {/* Data Provenance & Servicing Notice */}
        <div className="mt-5 flex flex-col sm:flex-row sm:items-center justify-between border-t border-[#E7E3DA] pt-4 text-xs text-[#6B6659] dark:border-[#2A2822] dark:text-[#A8A296] gap-2">
          <div className="flex items-center gap-2">
            <Database className="h-3.5 w-3.5 text-[#0E6E63] dark:text-[#4FD1B5] shrink-0" />
            <span>Sumber data: snapshot laporan keuangan terverifikasi IDX · Model DCF &amp; WACC</span>
          </div>
          <div className="text-xs text-[#6B6659] dark:text-[#A8A296]">
            {runsQuery.isLoading
              ? "Memuat status pipeline…"
              : runsQuery.isError
                ? "Status pipeline tidak terbaca - daftar belum tentu lengkap"
                : `${pendingReportCount} emiten selesai tapi laporan belum siap · ${hiddenCount} belum diproses`}
          </div>
        </div>
      </div>

      {/* 2. Listed Equities Cards Grid */}
      <section aria-label="Emiten yang siap dibaca" className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-normal text-[#1C1B17] dark:text-[#EDEAE3] font-['Newsreader',serif]">
              Laporan emiten
            </h2>
            <p className="text-xs text-[#6B6659] dark:text-[#A8A296] mt-0.5">
              Pilih emiten untuk melihat laporan valuasi DCF dan analisis mendalam.
            </p>
          </div>
        </div>

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {runsQuery.isLoading ? (
            <div className="rounded-xl border border-dashed border-[#E7E3DA] p-6 text-center text-xs text-[#6B6659] dark:border-[#2A2822] dark:text-[#A8A296] sm:col-span-2 lg:col-span-3">
              Memuat status pipeline…
            </div>
          ) : runsQuery.isError ? (
            <div className="rounded-xl border border-[#B4232A]/30 bg-[#B4232A]/5 p-6 text-xs leading-relaxed text-[#B4232A] dark:text-[#F87171] sm:col-span-2 lg:col-span-3">
              Status pipeline tidak terbaca dari /api/agent/runs/summary. Daftar dibiarkan kosong daripada menampilkan emiten yang belum tentu punya laporan.
            </div>
          ) : shown.length === 0 ? (
            <div className="rounded-xl border border-dashed border-[#E7E3DA] p-6 text-center text-xs leading-relaxed text-[#6B6659] dark:border-[#2A2822] dark:text-[#A8A296] sm:col-span-2 lg:col-span-3">
              {listedCount > 0 && !readyKnown
                ? "Backend belum mengirim status ketersediaan laporan (report_ready). Restart BE ke versi terbaru - daftar sengaja dibiarkan kosong daripada menampilkan laporan yang belum tentu bisa dibuka."
                : listedCount === 0
                  ? "Belum ada pipeline yang berjalan atau selesai. Jalankan dulu dari halaman Mesin - daftar ini terisi sendiri begitu sebuah analisis selesai."
                  : `${listedCount} emiten pipeline-nya sudah selesai, tapi laporannya belum bisa dibuka karena asumsinya belum dibuat. Daftar terisi sendiri begitu laporan tersedia.`}
            </div>
          ) : (
            shown.map((t) => <CompanyCard key={String(t.ticker)} ticker={String(t.ticker)} pipeline={t} />)
          )}

          {/* Multi-Agent Helper Card */}
          <div className="flex flex-col justify-between rounded-xl border border-dashed border-[#E7E3DA] bg-[#FBFAF7] p-5 dark:border-[#2A2822] dark:bg-[#1B1A16]/50">
            <div className="space-y-2">
              <h3 className="text-base font-normal text-[#1C1B17] dark:text-[#EDEAE3] font-['Newsreader',serif]">
                Penalaran multi-agen
              </h3>
              <p className="text-xs leading-relaxed text-[#6B6659] dark:text-[#A8A296]">
                Jalankan atau pantau mesin AI yang mengaudit laporan keuangan, memvalidasi model valuasi DCF, dan mendeteksi risiko secara mandiri.
              </p>
            </div>
            {jumpTicker ? (
              <Link
                to="/agent"
                search={{ ticker: jumpTicker } as any}
                className="mt-4 inline-flex items-center justify-center gap-2 rounded-lg bg-[#1C1B17] py-2 px-4 text-xs font-medium text-white transition-colors hover:bg-neutral-800 dark:bg-[#EDEAE3] dark:text-[#1C1B17] dark:hover:bg-white"
              >
                <span>Buka ruang mesin</span>
                <ChevronRight className="h-3.5 w-3.5" />
              </Link>
            ) : (
              <div className="mt-4 rounded-lg border border-dashed border-[#E7E3DA] px-4 py-2 text-center text-xs text-[#6B6659] dark:border-[#2A2822] dark:text-[#A8A296]">
                Belum ada emiten untuk dibuka
              </div>
            )}
          </div>
        </div>
      </section>

      {/* 3. Comparative Matrix */}
      {shown.length > 0 && (
        <section aria-label="Tabel perbandingan nilai wajar" className="space-y-4">
          <div>
            <h2 className="text-xl font-normal text-[#1C1B17] dark:text-[#EDEAE3] font-['Newsreader',serif]">
              Perbandingan nilai wajar
            </h2>
            <p className="text-xs text-[#6B6659] dark:text-[#A8A296] mt-0.5">
              Ikhtisar harga pasar dan estimasi nilai wajar dari emiten yang telah selesai dianalisis.
            </p>
          </div>

          <div className="overflow-x-auto rounded-xl border border-[#E7E3DA] bg-white dark:border-[#2A2822] dark:bg-[#1B1A16]">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="border-b border-[#E7E3DA] bg-[#FBFAF7] text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
                <tr>
                  <th className="py-3 px-4 font-semibold">Emiten</th>
                  <th className="py-3 px-4 font-semibold text-right">Harga pasar</th>
                  <th className="py-3 px-4 font-semibold text-right">Nilai wajar</th>
                  <th className="py-3 px-4 font-semibold text-right">Potensi</th>
                  <th className="py-3 px-4 font-semibold text-center">Rekomendasi</th>
                  <th className="py-3 px-4 font-semibold text-right">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E7E3DA] dark:divide-[#2A2822]">
                {shown.map((t) => (
                  <CompanyTableRow key={String(t.ticker)} ticker={String(t.ticker)} />
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* 4. Educational Reference & Valuation Methodology Guide */}
      <section id="cara-baca" className="scroll-mt-20 space-y-4">
        <div>
          <h2 className="text-xl font-normal text-[#1C1B17] dark:text-[#EDEAE3] font-['Newsreader',serif]">
            Cara membaca analisis
          </h2>
          <p className="text-xs text-[#6B6659] dark:text-[#A8A296] mt-0.5">
            Panduan memahami istilah valuasi fundamental dan metodologi Discounted Cash Flow.
          </p>
        </div>

        {/* Intro Box */}
        <div className="rounded-xl border border-[#E7E3DA] bg-[#FBFAF7] p-4 text-xs leading-relaxed text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
          <div className="flex items-start gap-2.5">
            <HelpCircle className="mt-0.5 h-4 w-4 shrink-0 text-[#0E6E63] dark:text-[#4FD1B5]" />
            <div>
              <span className="font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">Panduan istilah: </span>
              <span>
                Penjelasan di bawah disusun untuk memudahkan pembaca memahami istilah analisis fundamental. Angka pada kartu emiten dihitung secara deterministik dari laporan keuangan terverifikasi (jika belum tersedia, ditandai MENUNGGU).
              </span>
            </div>
          </div>
        </div>

        {/* 3 Terminology Explainer Cards */}
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-xl border border-[#E7E3DA] bg-white p-5 dark:border-[#2A2822] dark:bg-[#1B1A16]">
            <div className="flex items-center gap-2 text-xs font-semibold text-[#157F3D] dark:text-[#4ADE80]">
              <span className="h-2 w-2 rounded-full bg-[#157F3D] dark:bg-[#4ADE80]" />
              <span>BUY (Undervalued)</span>
            </div>
            <p className="mt-2 text-xs leading-relaxed text-[#6B6659] dark:text-[#A8A296]">
              Harga pasar saat ini berada di bawah estimasi nilai wajar fundamental (Fair Value) berdasarkan proyeksi arus kas. Menandakan tersedianya ruang keamanan (margin of safety) yang memadai.
            </p>
          </div>

          <div className="rounded-xl border border-[#E7E3DA] bg-white p-5 dark:border-[#2A2822] dark:bg-[#1B1A16]">
            <div className="flex items-center gap-2 text-xs font-semibold text-[#A16207] dark:text-[#FBBF24]">
              <span className="h-2 w-2 rounded-full bg-[#A16207] dark:bg-[#FBBF24]" />
              <span>HOLD (Fair Value)</span>
            </div>
            <p className="mt-2 text-xs leading-relaxed text-[#6B6659] dark:text-[#A8A296]">
              Harga pasar telah merefleksikan nilai intrinsik perusahaan secara wajar. Pertahankan kepemilikan aset atau tunggu konfirmasi katalis baru sebelum menambah posisi.
            </p>
          </div>

          <div className="rounded-xl border border-[#E7E3DA] bg-white p-5 dark:border-[#2A2822] dark:bg-[#1B1A16]">
            <div className="flex items-center gap-2 text-xs font-semibold text-[#B4232A] dark:text-[#F87171]">
              <span className="h-2 w-2 rounded-full bg-[#B4232A] dark:bg-[#F87171]" />
              <span>SELL (Overvalued)</span>
            </div>
            <p className="mt-2 text-xs leading-relaxed text-[#6B6659] dark:text-[#A8A296]">
              Harga pasar dinilai telah melampaui valuasi fundamental konservatif. Risiko koreksi harga lebih besar daripada potensi apresiasi jangka pendek.
            </p>
          </div>
        </div>

        {/* Detailed Mechanics (Upside & Fair Value) */}
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-xl border border-[#E7E3DA] bg-white p-5 text-xs dark:border-[#2A2822] dark:bg-[#1B1A16]">
            <div className="font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
              Bagaimana potensi naik (upside) dihitung?
            </div>
            <p className="mt-2 leading-relaxed text-[#6B6659] dark:text-[#A8A296]">
              Upside dihitung dari persentase selisih antara nilai wajar (Fair Value) hasil model DCF dan harga pasar terakhir: <code className="bg-[#FBFAF7] dark:bg-[#14130F] px-1.5 py-0.5 rounded border border-[#E7E3DA] dark:border-[#2A2822] text-[#1C1B17] dark:text-[#EDEAE3]">((Nilai Wajar - Harga) / Harga) * 100%</code>.
            </p>
          </div>

          <div className="rounded-xl border border-[#E7E3DA] bg-white p-5 text-xs dark:border-[#2A2822] dark:bg-[#1B1A16]">
            <div className="font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
              Apa itu Discounted Cash Flow (DCF)?
            </div>
            <p className="mt-2 leading-relaxed text-[#6B6659] dark:text-[#A8A296]">
              Metode valuasi intrinsik yang memproyeksikan arus kas bebas (Free Cash Flow to Firm) masa depan dan mendiskontokannya ke nilai sekarang menggunakan WACC (Weighted Average Cost of Capital).
            </p>
          </div>
        </div>
      </section>

      {/* 5. Compliance & Attestation Notice */}
      <div className="flex items-start gap-3 rounded-xl border border-[#E7E3DA] bg-[#FBFAF7] p-5 text-xs dark:border-[#2A2822] dark:bg-[#1B1A16]">
        <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-[#0E6E63] dark:text-[#4FD1B5]" />
        <div className="space-y-1">
          <div className="font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
            Pemberitahuan kepatuhan riset
          </div>
          <p className="leading-relaxed text-[#6B6659] dark:text-[#A8A296]">
            Seluruh analisis riset pada platform ini diproduksi secara deterministik dari laporan keuangan audited IDX. Sektoral.id tidak menyajikan angka sintetis atau rekayasa data. Informasi ini disajikan untuk tujuan riset kompetisi dan edukasi pasar, bukan merupakan rekomendasi transaksi efek dari penasihat investasi berlisensi.
          </p>
        </div>
      </div>
    </div>
  )
}
