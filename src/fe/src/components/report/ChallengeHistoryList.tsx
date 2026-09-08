import {
  MessageSquareQuote,
  ShieldAlert,
  ShieldCheck,
  FileSearch,
  XCircle,
  AlertTriangle,
  History,
  Trash2,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export type ChallengeEntry = {
  q: string
  verdict?: "defend" | "concede" | "reject" | string
  evidence?: string
  exhibit_ref?: string | null
  correction?: string | null
  debate_id?: string | null
  timestamp?: string
  error?: string
}

export type ChallengeHistoryListProps = {
  ticker: string
  log: ChallengeEntry[]
  onClear?: () => void
}

export function ChallengeHistoryList({
  ticker,
  log,
  onClear,
}: ChallengeHistoryListProps) {
  const tk = ticker.toUpperCase()

  const renderVerdictBadge = (verdict?: string) => {
    if (!verdict) return null
    const v = verdict.toLowerCase()
    if (v === "defend") {
      return (
        <span className="inline-flex items-center gap-1.5 rounded-md border border-emerald-500/40 bg-emerald-500/10 px-2.5 py-1 font-mono text-[11px] font-bold text-emerald-700 dark:text-emerald-400">
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>[DIPERTAHANKAN // DEFEND]</span>
        </span>
      )
    }
    if (v === "concede") {
      return (
        <span className="inline-flex items-center gap-1.5 rounded-md border border-amber-500/40 bg-amber-500/10 px-2.5 py-1 font-mono text-[11px] font-bold text-amber-700 dark:text-amber-400">
          <AlertTriangle className="h-3.5 w-3.5" />
          <span>[DISESUAIKAN // CONCEDE]</span>
        </span>
      )
    }
    if (v === "reject") {
      return (
        <span className="inline-flex items-center gap-1.5 rounded-md border border-rose-500/40 bg-rose-500/10 px-2.5 py-1 font-mono text-[11px] font-bold text-rose-700 dark:text-rose-400">
          <XCircle className="h-3.5 w-3.5" />
          <span>[PREMIS DITOLAK // REJECT]</span>
        </span>
      )
    }
    return (
      <span className="rounded-md border border-neutral-300 bg-neutral-100 px-2.5 py-1 font-mono text-[11px] font-bold text-neutral-700 dark:border-[#262930] dark:bg-[#181a1f] dark:text-neutral-300">
        [{verdict.toUpperCase()}]
      </span>
    )
  }

  return (
    <Card className="rounded-lg border border-neutral-200 bg-white shadow-xs dark:border-[#262930] dark:bg-[#121418]">
      <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-4 sm:p-5 pb-3 dark:border-[#262930] dark:bg-[#181a1f]/70">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0" />
            <CardTitle className="text-xs font-mono font-semibold uppercase tracking-wider text-neutral-900 dark:text-neutral-100">
              CATATAN UJI SILANG ({log.length})
            </CardTitle>
          </div>
          {log.length > 0 && onClear && (
            <button
              type="button"
              onClick={onClear}
              className="inline-flex items-center gap-1 font-mono text-[10px] text-neutral-500 hover:text-rose-600 transition-colors cursor-pointer dark:text-neutral-400 dark:hover:text-rose-400"
            >
              <Trash2 className="h-3 w-3" />
              <span>[F8] BERSIHKAN CATATAN</span>
            </button>
          )}
        </div>
      </CardHeader>

      <CardContent className="p-4 sm:p-5 font-sans">
        {log.length === 0 ? (
          <div className="rounded-lg border border-dashed border-neutral-200 bg-neutral-50/50 p-8 text-center font-sans text-xs dark:border-[#262930] dark:bg-[#15171c]">
            <MessageSquareQuote className="mx-auto h-8 w-8 text-neutral-400 mb-2" />
            <p className="font-semibold text-neutral-700 dark:text-neutral-300">
              Belum ada riwayat uji silang untuk {tk}
            </p>
            <p className="mt-1 text-xs text-neutral-500 max-w-sm mx-auto dark:text-neutral-400">
              Gunakan formulir di sebelah kiri untuk menguji asumsi WACC, margin operasi, atau proyeksi pertumbuhan emiten.
            </p>
          </div>
        ) : (
          <div className="space-y-3.5">
            {log.map((entry, index) => (
              <div
                key={index}
                className="rounded-lg border border-neutral-200 bg-neutral-50/40 p-3.5 sm:p-4 transition-colors hover:border-neutral-300 dark:border-[#262930] dark:bg-[#15171c] dark:hover:border-neutral-600"
              >
                {/* Header: Question & Verdict */}
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between border-b border-neutral-200 pb-2.5 dark:border-[#262930]">
                  <div className="space-y-0.5 min-w-0 pr-2">
                    <span className="font-mono text-[9px] font-bold uppercase tracking-wider text-neutral-400">
                      CHALLENGE LOG #{log.length - index}
                    </span>
                    <h4 className="text-xs font-semibold text-neutral-900 leading-snug dark:text-neutral-100">
                      T: &ldquo;{entry.q}&rdquo;
                    </h4>
                  </div>
                  <div className="shrink-0">{renderVerdictBadge(entry.verdict)}</div>
                </div>

                {/* Evidence Content */}
                {entry.evidence && (
                  <div className="mt-3 space-y-1.5">
                    <div className="font-mono text-[10px] font-semibold text-neutral-600 flex items-center gap-1 uppercase tracking-wider dark:text-neutral-400">
                      <ShieldAlert className="h-3 w-3 text-amber-600 dark:text-amber-400" />
                      <span>ARGUMEN &amp; BUKTI PEMERIKSAAN INDEPENDEN</span>
                    </div>
                    <div className="rounded-md border border-neutral-200 bg-white p-3 text-xs leading-relaxed text-neutral-800 dark:border-[#262930] dark:bg-[#121418] dark:text-neutral-200">
                      {entry.evidence}
                    </div>
                  </div>
                )}

                {/* Correction if conceded */}
                {entry.correction && (
                  <div className="mt-2.5 rounded-md border border-amber-300 bg-amber-500/10 p-2.5 font-sans text-xs text-amber-800 dark:border-amber-800 dark:text-amber-300">
                    <span className="font-bold font-mono">[PENYESUAIAN MODEL] </span>
                    <span>{entry.correction}</span>
                  </div>
                )}

                {/* Exhibit Reference & Metadata */}
                <div className="mt-3 flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-neutral-200 font-mono text-[10px] text-neutral-500 dark:border-[#262930] dark:text-neutral-400">
                  {entry.exhibit_ref ? (
                    <div className="flex items-center gap-1 text-neutral-600 dark:text-neutral-400">
                      <FileSearch className="h-3 w-3 text-neutral-400" />
                      <span>REFERENSI BUKTI: {entry.exhibit_ref}</span>
                    </div>
                  ) : (
                    <span>RUJUKAN: LAPORAN KEUANGAN AUDITED IDX</span>
                  )}

                  {entry.debate_id && (
                    <span className="text-neutral-400">
                      ID UJI: {entry.debate_id}
                    </span>
                  )}
                </div>

                {/* Error Banner */}
                {entry.error && (
                  <div className="mt-2 rounded-md border border-rose-300 bg-rose-500/10 p-2.5 font-mono text-xs text-rose-800 dark:border-rose-800 dark:text-rose-300">
                    <span className="font-bold">[ERROR] </span>
                    <span>{entry.error}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
