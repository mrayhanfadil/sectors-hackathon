import { memo } from "react"
import { Link } from "@tanstack/react-router"
import {
  ArrowLeft,
  Play,
  Square,
  FileText,
  CheckCircle2,
  Clock,
  AlertCircle,
  RotateCcw,
  Sparkles,
} from "lucide-react"

export interface PipelineHeaderProps {
  ticker: string
  companyName?: string | null
  running: boolean
  done: { n_events: number; state_keys: string[]; ms: number } | null
  error: string | null
  activeCount: number
  totalCount: number
  etaText: string
  isInterrupted: boolean
  onRun: () => void
  onStop: () => void
  onClear?: () => void
}

export const PipelineHeader = memo(function PipelineHeader({
  ticker,
  companyName,
  running,
  done,
  error,
  activeCount,
  totalCount,
  etaText,
  isInterrupted,
  onRun,
  onStop,
}: PipelineHeaderProps) {
  const t = ticker.toUpperCase()

  return (
    <div className="space-y-4">
      {/* Top back navigation */}
      <div>
        <Link
          to="/agent"
          search={{}}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-[#6B6659] dark:text-[#A8A296] hover:text-[#0E6E63] dark:hover:text-[#4FD1B5] transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Kembali ke daftar emiten</span>
        </Link>
      </div>

      {/* Main header card */}
      <div className="rounded-xl border border-[#E7E3DA] dark:border-[#2A2822] bg-white dark:bg-[#1B1A16] p-5 sm:p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex flex-wrap items-baseline gap-2.5">
              <h1 className="font-serif text-2xl sm:text-3xl font-medium tracking-tight text-[#1C1B17] dark:text-[#EDEAE3]">
                {t}
              </h1>
              {companyName && (
                <span className="text-sm font-normal text-[#6B6659] dark:text-[#A8A296]">
                  {companyName}
                </span>
              )}
            </div>
            <p className="text-xs text-[#6B6659] dark:text-[#A8A296] leading-relaxed max-w-xl">
              Alur kerja mesin otomatis: ekstraksi laporan keuangan resmi IDX, kalkulasi nilai wajar (DCF/DDM/PE), dan penelaahan kritis multi-agen.
            </p>
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap items-center gap-2 self-start sm:self-center">
            {running ? (
              <button
                type="button"
                onClick={onStop}
                className="inline-flex items-center gap-1.5 rounded-lg border border-rose-300 dark:border-rose-900/60 bg-rose-50 dark:bg-rose-950/40 px-4 py-2 text-sm font-medium text-[#B4232A] dark:text-rose-300 hover:bg-rose-100 dark:hover:bg-rose-950/70 transition-colors"
              >
                <Square className="h-3.5 w-3.5 fill-current" />
                <span>Hentikan proses</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={onRun}
                className="inline-flex items-center gap-1.5 rounded-lg bg-[#0E6E63] text-white hover:bg-[#0c5c53] px-4 py-2 text-sm font-medium transition-colors"
              >
                <Play className="h-3.5 w-3.5 fill-current" />
                <span>{done ? "Jalankan ulang" : "Jalankan analisis"}</span>
              </button>
            )}

            <Link
              to="/report/$ticker"
              params={{ ticker: t }}
              className="inline-flex items-center gap-1.5 rounded-lg border border-[#E7E3DA] dark:border-[#2A2822] bg-white dark:bg-[#1B1A16] px-4 py-2 text-sm font-medium text-[#1C1B17] dark:text-[#EDEAE3] hover:bg-[#F5F2EB] dark:hover:bg-[#23211C] transition-colors"
            >
              <FileText className="h-4 w-4 text-[#0E6E63] dark:text-[#4FD1B5]" />
              <span>Buka laporan</span>
            </Link>
          </div>
        </div>

        {/* Status Line */}
        <div className="pt-3 border-t border-[#E7E3DA]/60 dark:border-[#2A2822]/60 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="text-[#6B6659] dark:text-[#A8A296] font-medium">Status mesin:</span>
            {running ? (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800/60 px-3 py-1 text-xs font-medium">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-500" />
                </span>
                <span>Sedang diproses</span>
                <span className="text-amber-600 dark:text-amber-400">·</span>
                <span>{activeCount} dari {totalCount} agen aktif</span>
                <span className="text-amber-600 dark:text-amber-400">·</span>
                <span className="inline-flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  <span>Sisa {etaText}</span>
                </span>
              </span>
            ) : done ? (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60 px-3 py-1 text-xs font-medium">
                <Sparkles className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                <span>Analisis selesai</span>
                <span className="text-emerald-600 dark:text-emerald-400">·</span>
                <span>{done.n_events} langkah</span>
                <span className="text-emerald-600 dark:text-emerald-400">·</span>
                <span>{(done.ms / 1000).toFixed(1)} detik</span>
              </span>
            ) : isInterrupted ? (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800/60 px-3 py-1 text-xs font-medium">
                <AlertCircle className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
                <span>Proses terhenti</span>
              </span>
            ) : error ? (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-50 dark:bg-rose-950/40 text-[#B4232A] dark:text-rose-300 border border-rose-200 dark:border-rose-900/60 px-3 py-1 text-xs font-medium">
                <AlertCircle className="h-3.5 w-3.5 text-[#B4232A]" />
                <span>Terjadi kendala</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-[#F5F2EB] dark:bg-[#23211C] text-[#6B6659] dark:text-[#A8A296] border border-[#E7E3DA] dark:border-[#2A2822] px-3 py-1 text-xs font-medium">
                <span className="h-1.5 w-1.5 rounded-full bg-[#6B6659] dark:bg-[#A8A296]" />
                <span>Mesin siaga</span>
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
})
