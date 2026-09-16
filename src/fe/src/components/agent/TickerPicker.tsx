import { useState, useEffect, useMemo, useCallback } from "react"
import { Link } from "@tanstack/react-router"
import { Search, Loader2, AlertCircle, ArrowRight, CheckCircle2, Clock, RefreshCw } from "lucide-react"
import { fetchRunsSummary, type RunsSummary, type RunsSummaryTicker } from "@/lib/api"
import { fetchUniverse, type UniverseTicker } from "./tickers"

export interface TickerPickerProps {
  onSelectTicker: (ticker: string) => void
}

interface TickerDisplayItem {
  ticker: string
  companyName: string | null
  totalRuns: number
  reportReady: boolean
  status: "running" | "completed"
  startedAt?: number
  finishedAt?: number | null
}

export function TickerPicker({ onSelectTicker }: TickerPickerProps) {
  const [summary, setSummary] = useState<RunsSummary | null>(null)
  const [universe, setUniverse] = useState<UniverseTicker[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterQuery, setFilterQuery] = useState("")

  const apiBase = (import.meta as any).env?.VITE_API_URL || ""

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      // Helper fetchRunsSummary calls GET /api/agent/runs/summary
      const [summaryRes, universeRes] = await Promise.all([
        fetchRunsSummary(),
        fetchUniverse(apiBase).catch(() => []),
      ])
      setSummary(summaryRes)
      setUniverse(universeRes)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setError(`Gagal memuat data dari GET /api/agent/runs/summary (${msg})`)
    } finally {
      setLoading(false)
    }
  }, [apiBase])

  useEffect(() => {
    loadData()
  }, [loadData])

  // Process & filter valid pipeline tickers
  const validItems: TickerDisplayItem[] = useMemo(() => {
    if (!summary || !summary.tickers) return []

    const universeMap = new Map<string, string>()
    for (const u of universe) {
      if (u.kode && u.nama) {
        universeMap.set(u.kode.toUpperCase(), u.nama)
      }
    }

    const tickerCodeRegex = /^[A-Z]{4}$/
    const items: TickerDisplayItem[] = []

    for (const [code, item] of Object.entries(summary.tickers)) {
      const upperCode = code.toUpperCase().trim()
      if (!tickerCodeRegex.test(upperCode)) continue

      const latestStatus = item.latest_run?.status
      if (latestStatus !== "running" && latestStatus !== "completed") continue

      const nameFromUniverse = universeMap.get(upperCode) || null

      items.push({
        ticker: upperCode,
        companyName: nameFromUniverse,
        totalRuns: item.total_runs || 1,
        reportReady: Boolean(item.report_ready),
        status: latestStatus,
        startedAt: item.latest_run?.started_at,
        finishedAt: item.latest_run?.finished_at,
      })
    }

    // Sort by status (running first, then completed) then ticker alphabetical
    items.sort((a, b) => {
      if (a.status === "running" && b.status !== "running") return -1
      if (b.status === "running" && a.status !== "running") return 1
      return a.ticker.localeCompare(b.ticker)
    })

    return items
  }, [summary, universe])

  // Client-side text filter
  const filteredItems = useMemo(() => {
    if (!filterQuery.trim()) return validItems
    const q = filterQuery.toLowerCase().trim()
    return validItems.filter(
      (item) =>
        item.ticker.toLowerCase().includes(q) ||
        (item.companyName && item.companyName.toLowerCase().includes(q))
    )
  }, [validItems, filterQuery])

  return (
    <div className="max-w-[1100px] mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-8 font-sans text-[#1C1B17] dark:text-[#EDEAE3]">
      {/* Header section */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <h1 className="font-serif text-2xl sm:text-3xl font-medium tracking-tight text-[#1C1B17] dark:text-[#EDEAE3]">
              Pilih emiten
            </h1>
            <p className="mt-1.5 text-sm text-[#6B6659] dark:text-[#A8A296] leading-relaxed max-w-2xl">
              Daftar saham yang telah diproses oleh mesin analisis multi-agen. Pilih emiten untuk melihat alur kerja, status valuasi, dan ringkasan hasil riset.
            </p>
          </div>

          <button
            type="button"
            onClick={loadData}
            disabled={loading}
            className="inline-flex items-center gap-2 self-start sm:self-auto rounded-lg border border-[#E7E3DA] dark:border-[#2A2822] bg-white dark:bg-[#1B1A16] px-3 py-1.5 text-xs text-[#6B6659] dark:text-[#A8A296] hover:bg-[#F5F2EB] dark:hover:bg-[#23211C] hover:text-[#1C1B17] dark:hover:text-[#EDEAE3] transition-colors disabled:opacity-50"
            title="Muat ulang daftar emiten"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-[#0E6E63] dark:text-[#4FD1B5]" : ""}`} />
            <span>Segarkan data</span>
          </button>
        </div>

        {/* Filter Input */}
        <div className="pt-2">
          <div className="relative max-w-md">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[#6B6659] dark:text-[#A8A296]" />
            <input
              type="text"
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              placeholder="Cari kode saham…"
              className="w-full rounded-lg border border-[#E7E3DA] dark:border-[#2A2822] bg-white dark:bg-[#1B1A16] pl-10 pr-4 py-2 text-sm text-[#1C1B17] dark:text-[#EDEAE3] placeholder:text-[#6B6659]/70 dark:placeholder:text-[#A8A296]/70 focus:outline-none focus:border-[#0E6E63] dark:focus:border-[#4FD1B5] transition-colors"
            />
          </div>
        </div>
      </div>

      {/* Content states */}
      {loading && !summary ? (
        <div className="rounded-xl border border-[#E7E3DA] dark:border-[#2A2822] bg-white dark:bg-[#1B1A16] p-12 text-center space-y-3">
          <Loader2 className="h-6 w-6 animate-spin text-[#0E6E63] dark:text-[#4FD1B5] mx-auto" />
          <p className="text-sm font-medium text-[#1C1B17] dark:text-[#EDEAE3]">
            Memuat daftar proses mesin…
          </p>
          <p className="text-xs text-[#6B6659] dark:text-[#A8A296]">
            Mengambil status terbaru dari server analisis
          </p>
        </div>
      ) : error ? (
        <div className="rounded-xl border border-rose-200 dark:border-rose-900/60 bg-rose-50/70 dark:bg-rose-950/20 p-6 space-y-3">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-[#B4232A] shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h3 className="text-sm font-semibold text-[#B4232A]">
                Terjadi kesalahan saat memuat data
              </h3>
              <p className="text-xs text-[#6B6659] dark:text-[#A8A296] break-all">
                {error}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={loadData}
            className="inline-flex items-center gap-2 rounded-lg bg-[#0E6E63] text-white px-3.5 py-1.5 text-xs font-medium hover:bg-[#0c5c53] transition-colors"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Coba lagi</span>
          </button>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="rounded-xl border border-[#E7E3DA] dark:border-[#2A2822] bg-white dark:bg-[#1B1A16] p-12 text-center space-y-2">
          <h3 className="font-serif text-lg font-medium text-[#1C1B17] dark:text-[#EDEAE3]">
            {filterQuery ? "Tidak ada emiten yang sesuai" : "Belum ada pipeline yang dijalankan"}
          </h3>
          <p className="text-xs text-[#6B6659] dark:text-[#A8A296] max-w-md mx-auto">
            {filterQuery
              ? `Tidak ditemukan emiten yang cocok dengan kata kunci "${filterQuery}". Coba gunakan kode saham lain.`
              : "Belum ada emiten yang selesai atau sedang diproses oleh mesin analisis."}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-[#6B6659] dark:text-[#A8A296] px-1">
            <span>Menampilkan {filteredItems.length} emiten</span>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {filteredItems.map((item) => {
              const isRunning = item.status === "running"

              return (
                <div
                  key={item.ticker}
                  className="rounded-xl border border-[#E7E3DA] dark:border-[#2A2822] bg-white dark:bg-[#1B1A16] p-5 flex flex-col justify-between gap-4 hover:border-[#0E6E63]/40 dark:hover:border-[#4FD1B5]/40 transition-colors"
                >
                  <div className="space-y-3">
                    {/* Top Row: Ticker & Readiness Badge */}
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-serif text-xl font-medium text-[#1C1B17] dark:text-[#EDEAE3]">
                            {item.ticker}
                          </span>
                        </div>
                        {item.companyName && (
                          <p className="mt-0.5 text-xs text-[#6B6659] dark:text-[#A8A296] line-clamp-1">
                            {item.companyName}
                          </p>
                        )}
                      </div>

                      {/* Small readiness badge */}
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-medium border ${
                          item.reportReady
                            ? "bg-[#0E6E63]/10 text-[#0E6E63] border-[#0E6E63]/25 dark:bg-[#4FD1B5]/15 dark:text-[#4FD1B5] dark:border-[#4FD1B5]/30"
                            : "bg-[#F5F2EB] text-[#6B6659] border-[#E7E3DA] dark:bg-[#23211C] dark:text-[#A8A296] dark:border-[#2A2822]"
                        }`}
                      >
                        {item.reportReady ? "Laporan siap" : "Laporan belum tersedia"}
                      </span>
                    </div>

                    {/* Middle Row: Pipeline status indicator */}
                    <div className="flex items-center gap-2 text-xs">
                      {isRunning ? (
                        <span className="inline-flex items-center gap-1.5 rounded-md bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800/60 px-2 py-0.5 font-medium">
                          <span className="relative flex h-2 w-2">
                            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
                            <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-500" />
                          </span>
                          Sedang diproses
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 rounded-md bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60 px-2 py-0.5 font-medium">
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                          Selesai
                        </span>
                      )}

                      <span className="text-[#6B6659] dark:text-[#A8A296]">
                        {item.totalRuns} kali analisis
                      </span>
                    </div>
                  </div>

                  {/* Primary Action Button */}
                  <div className="pt-2 border-t border-[#E7E3DA]/60 dark:border-[#2A2822]/60">
                    <Link
                      to="/agent"
                      search={{ ticker: item.ticker }}
                      className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-[#0E6E63] text-white hover:bg-[#0c5c53] dark:hover:bg-[#0E6E63]/90 px-4 py-2 text-sm font-medium transition-colors"
                    >
                      <span>Buka pipeline</span>
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
