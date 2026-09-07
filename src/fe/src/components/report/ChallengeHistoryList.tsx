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
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

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
        <Badge variant="success" className="inline-flex items-center gap-1 font-mono text-[11px]">
          <ShieldCheck className="h-3 w-3" />
          DEFEND (Dipertahankan)
        </Badge>
      )
    }
    if (v === "concede") {
      return (
        <Badge variant="outline" className="border-amber-300 bg-amber-50 text-amber-800 inline-flex items-center gap-1 font-mono text-[11px]">
          <AlertTriangle className="h-3 w-3 text-amber-600" />
          CONCEDE (Disesuaikan)
        </Badge>
      )
    }
    if (v === "reject") {
      return (
        <Badge variant="destructive" className="inline-flex items-center gap-1 font-mono text-[11px]">
          <XCircle className="h-3 w-3" />
          REJECT (Premis Ditolak)
        </Badge>
      )
    }
    return <Badge variant="secondary">{verdict.toUpperCase()}</Badge>
  }

  return (
    <Card className="border-neutral-200 bg-white shadow-2xs">
      <CardHeader className="border-b border-neutral-100 bg-neutral-50/50 p-4 pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="h-4 w-4 text-neutral-700" />
            <CardTitle className="text-sm font-semibold text-neutral-900">
              Riwayat Debat & Pembelaan Tesis ({log.length})
            </CardTitle>
          </div>
          {log.length > 0 && onClear && (
            <button
              type="button"
              onClick={onClear}
              className="inline-flex items-center gap-1 text-[11px] text-neutral-500 hover:text-neutral-900 transition-colors cursor-pointer"
            >
              <Trash2 className="h-3 w-3" />
              <span>Bersihkan Riwayat</span>
            </button>
          )}
        </div>
        <CardDescription className="text-xs text-neutral-500">
          Transkrip verifikasi argumen berhadapan dengan agent penilai independen
        </CardDescription>
      </CardHeader>

      <CardContent className="p-4 sm:p-6">
        {log.length === 0 ? (
          <div className="rounded-xl border border-dashed border-neutral-200 bg-neutral-50/50 p-8 text-center">
            <MessageSquareQuote className="mx-auto h-8 w-8 text-neutral-400" />
            <p className="mt-2 text-sm font-medium text-neutral-800">
              Belum ada tantangan tesis yang diajukan untuk {tk}
            </p>
            <p className="mt-1 text-xs text-neutral-500 max-w-sm mx-auto">
              Gunakan formulir di sebelah kiri untuk menguji asumsi WACC, margin operasi, atau proyeksi pertumbuhan emiten.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {log.map((entry, index) => (
              <div
                key={index}
                className="rounded-xl border border-neutral-200 bg-white p-4 transition-all hover:border-neutral-300 hover:shadow-2xs"
              >
                {/* Header: Question & Verdict */}
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between border-b border-neutral-100 pb-2.5">
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold font-mono uppercase tracking-wider text-neutral-400">
                      Tantangan #{log.length - index}
                    </span>
                    <h4 className="text-xs font-semibold text-neutral-900 leading-snug">
                      "{entry.q}"
                    </h4>
                  </div>
                  <div>{renderVerdictBadge(entry.verdict)}</div>
                </div>

                {/* Evidence Content */}
                {entry.evidence && (
                  <div className="mt-3 space-y-1 text-xs leading-relaxed text-neutral-700">
                    <div className="font-semibold text-neutral-900 flex items-center gap-1.5">
                      <ShieldAlert className="h-3.5 w-3.5 text-neutral-600" />
                      <span>Argumen Pembelaan / Penjelasan Model:</span>
                    </div>
                    <p className="rounded-lg bg-neutral-50 p-3 text-neutral-700 font-sans border border-neutral-100">
                      {entry.evidence}
                    </p>
                  </div>
                )}

                {/* Correction if conceded */}
                {entry.correction && (
                  <div className="mt-2 text-xs text-amber-900 bg-amber-50/70 p-2.5 rounded-lg border border-amber-200">
                    <span className="font-semibold">Penyesuaian Model: </span>
                    <span>{entry.correction}</span>
                  </div>
                )}

                {/* Exhibit Reference & Metadata */}
                <div className="mt-3 flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-neutral-100 text-[11px] text-neutral-500">
                  {entry.exhibit_ref ? (
                    <div className="flex items-center gap-1 font-mono text-neutral-600">
                      <FileSearch className="h-3 w-3 text-neutral-400" />
                      <span>Ref: {entry.exhibit_ref}</span>
                    </div>
                  ) : (
                    <span className="text-neutral-400">Rujukan: Laporan Keuangan Audited IDX</span>
                  )}

                  {entry.debate_id && (
                    <span className="font-mono text-[10px] text-neutral-400">
                      ID: {entry.debate_id}
                    </span>
                  )}
                </div>

                {/* Error Banner */}
                {entry.error && (
                  <div className="mt-2 rounded-md bg-rose-50 p-2 text-xs text-rose-700 border border-rose-200">
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
