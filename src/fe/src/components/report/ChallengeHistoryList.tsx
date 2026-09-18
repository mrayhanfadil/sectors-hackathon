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
        <span className="inline-flex items-center gap-1.5 rounded-md border border-[#BCE2C9] bg-[#EBF6EE] px-2.5 py-1 text-xs font-semibold text-[#157F3D] dark:border-[#157F3D]/40 dark:bg-[#157F3D]/20 dark:text-[#34D399]">
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>Putusan: Dipertahankan</span>
        </span>
      )
    }
    if (v === "concede") {
      return (
        <span className="inline-flex items-center gap-1.5 rounded-md border border-[#F6E3B8] bg-[#FEF9EE] px-2.5 py-1 text-xs font-semibold text-[#A16207] dark:border-[#A16207]/40 dark:bg-[#A16207]/20 dark:text-[#FBBF24]">
          <AlertTriangle className="h-3.5 w-3.5" />
          <span>Putusan: Disesuaikan</span>
        </span>
      )
    }
    if (v === "reject") {
      return (
        <span className="inline-flex items-center gap-1.5 rounded-md border border-[#F8C8CB] bg-[#FDF2F2] px-2.5 py-1 text-xs font-semibold text-[#B4232A] dark:border-[#B4232A]/40 dark:bg-[#B4232A]/20 dark:text-[#F87171]">
          <XCircle className="h-3.5 w-3.5" />
          <span>Putusan: Premis ditolak</span>
        </span>
      )
    }
    return (
      <span className="rounded-md border border-[#D9D9D9] bg-[#f1f5f9] px-2.5 py-1 text-xs font-medium text-[#333333] dark:border-[#262930] dark:bg-[#090a0c] dark:text-[#f1f5f9]">
        {verdict}
      </span>
    )
  }

  return (
    <Card className="rounded-xl border border-[#D9D9D9] bg-white dark:border-[#262930] dark:bg-[#090a0c]">
      <CardHeader className="border-b border-[#D9D9D9] p-5 pb-3 dark:border-[#262930]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="h-4 w-4 text-[#0928B1] dark:text-[#7596FF] shrink-0" />
            <CardTitle className="text-sm font-semibold text-[#333333] dark:text-[#f1f5f9]">
              Catatan uji silang tesis ({log.length})
            </CardTitle>
          </div>
          {log.length > 0 && onClear && (
            <button
              type="button"
              onClick={onClear}
              className="inline-flex items-center gap-1 text-xs text-[#666666] hover:text-[#B4232A] transition-colors cursor-pointer dark:text-[#666666] dark:hover:text-[#F87171]"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>Bersihkan riwayat</span>
            </button>
          )}
        </div>
      </CardHeader>

      <CardContent className="p-5">
        {log.length === 0 ? (
          <div className="rounded-xl border border-dashed border-[#D9D9D9] bg-[#f1f5f9] p-8 text-center text-xs dark:border-[#262930] dark:bg-[#1e2229]">
            <MessageSquareQuote className="mx-auto h-8 w-8 text-[#666666] mb-2" />
            <p className="font-semibold text-[#333333] dark:text-[#f1f5f9]">
              Belum ada riwayat uji silang untuk {tk}
            </p>
            <p className="mt-1 text-xs text-[#666666] max-w-sm mx-auto dark:text-[#666666]">
              Gunakan formulir di sebelah kiri untuk menguji asumsi WACC, margin operasi, atau proyeksi pertumbuhan emiten.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {log.map((entry, index) => (
              <div
                key={index}
                className="rounded-xl border border-[#D9D9D9] bg-[#f1f5f9] p-4 sm:p-5 transition-colors dark:border-[#262930] dark:bg-[#1e2229]"
              >
                {/* Proposal & Putusan */}
                <div className="flex flex-col gap-2.5 sm:flex-row sm:items-start sm:justify-between border-b border-[#D9D9D9] pb-3 dark:border-[#262930]">
                  <div className="space-y-1 min-w-0 pr-2">
                    <span className="text-[11px] font-medium text-[#666666] dark:text-[#666666]">
                      Tantangan #{log.length - index}
                    </span>
                    <h4 className="text-sm font-semibold text-[#333333] leading-snug dark:text-[#f1f5f9]">
                      &ldquo;{entry.q}&rdquo;
                    </h4>
                  </div>
                  <div className="shrink-0">{renderVerdictBadge(entry.verdict)}</div>
                </div>

                {/* Evidence & Argumen */}
                {entry.evidence && (
                  <div className="mt-3.5 space-y-1.5">
                    <div className="text-xs font-semibold text-[#666666] flex items-center gap-1.5 dark:text-[#666666]">
                      <ShieldAlert className="h-3.5 w-3.5 text-[#0928B1] dark:text-[#7596FF]" />
                      <span>Argumen dan bukti pemeriksaan</span>
                    </div>
                    <div className="rounded-lg border border-[#D9D9D9] bg-white p-3.5 text-xs leading-relaxed text-[#333333] dark:border-[#262930] dark:bg-[#090a0c] dark:text-[#f1f5f9]">
                      {entry.evidence}
                    </div>
                  </div>
                )}

                {/* Correction if conceded */}
                {entry.correction && (
                  <div className="mt-3 rounded-lg border border-[#F6E3B8] bg-[#FEF9EE] p-3 text-xs text-[#A16207] dark:border-[#A16207]/40 dark:bg-[#A16207]/20 dark:text-[#FBBF24]">
                    <span className="font-semibold">[Penyesuaian Model] </span>
                    <span>{entry.correction}</span>
                  </div>
                )}

                {/* Exhibit Reference & Metadata */}
                <div className="mt-3.5 flex flex-wrap items-center justify-between gap-2 pt-2.5 border-t border-[#D9D9D9] text-[11px] text-[#666666] dark:border-[#262930] dark:text-[#666666]">
                  {entry.exhibit_ref ? (
                    <div className="flex items-center gap-1">
                      <FileSearch className="h-3.5 w-3.5 text-[#666666] dark:text-[#666666]" />
                      <span>Referensi bukti: {entry.exhibit_ref}</span>
                    </div>
                  ) : (
                    <span>Rujukan: Laporan keuangan audited IDX</span>
                  )}

                  {entry.debate_id && (
                    <span className="text-[#666666] dark:text-[#666666]">
                      ID Uji: {entry.debate_id}
                    </span>
                  )}
                </div>

                {/* Error Banner */}
                {entry.error && (
                  <div className="mt-3 rounded-lg border border-[#F8C8CB] bg-[#FDF2F2] p-3 text-xs text-[#B4232A] dark:border-[#B4232A]/40 dark:bg-[#B4232A]/20 dark:text-[#F87171]">
                    <span className="font-semibold">Galat: </span>
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
