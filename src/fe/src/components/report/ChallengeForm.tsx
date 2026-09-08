import * as React from "react"
import {
  Swords,
  Send,
  Loader2,
  Sparkles,
  ShieldCheck,
  AlertCircle,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export type ChallengeFormProps = {
  ticker: string
  onSubmit: (question: string) => Promise<void>
  loading: boolean
  error: string | null
}

const DEFAULT_SUGGESTIONS: Record<string, string[]> = {
  BBCA: [
    "WACC 11.1% terlalu tinggi dibanding cost of fund CASA 75%?",
    "NIM 5.8% berisiko tertekan tren penurunan suku bunga BI?",
    "Pertumbuhan kredit 10-12% FY26F terlalu agresif di tengah daya beli lesu?",
  ],
  MTEL: [
    "WACC 10.1% terlalu konservatif dibanding rata-rata industri menara?",
    "Tenancy ratio 1.57x berisiko melambat akibat konsolidasi telco?",
    "Capex fiber optik Rp 2.9 T dapat menekan arus kas bebas jangka pendek?",
  ],
  RATU: [
    "WACC 8.4% terlalu rendah untuk profil risiko migas Cepu?",
    "Asumsi harga minyak mentah US$75/bbl terlalu optimis?",
    "Target produksi 169k BOPD rentan terhadap jadwal perawatan sumur?",
  ],
  CDIA: [
    "Gearing CDIA melonjak 170%, apakah struktur utang masih aman?",
    "Margin petrokimia berisiko tertekan oversupply regional dari China?",
    "Valuasi SOTP 4 pilar terlalu bergantung pada segmen energi?",
  ],
  ADRO: [
    "Holdco discount 15% pada SOTP pasca spin-off AADI sudah memadai?",
    "Harga batu bara termal global berisiko turun ke bawah US$100/t?",
    "Diversifikasi ke energi hijau memerlukan capex besar yang membatasi dividen?",
  ],
}

export function ChallengeForm({
  ticker,
  onSubmit,
  loading,
  error,
}: ChallengeFormProps) {
  const tk = ticker.toUpperCase()
  const [question, setQuestion] = React.useState("")
  const [validationError, setValidationError] = React.useState<string | null>(null)

  const suggestions = DEFAULT_SUGGESTIONS[tk] || [
    `Apakah asumsi WACC dan pertumbuhan terminal ${tk} sudah realistis?`,
    `Bagaimana mitigasi risiko penurunan margin operasi pada model DCF?`,
    `Apakah belanja modal (capex) yang diproyeksikan mencukupi kebutuhan ekspansi?`,
  ]

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const q = question.trim()
    if (!q) {
      setValidationError("Ketik pertanyaan atau kritik sebelum mengeksekusi.")
      return
    }
    if (q.length < 5) {
      setValidationError("Pertanyaan minimal 5 karakter agar agent dapat menganalisis argumen secara tepat.")
      return
    }
    setValidationError(null)
    await onSubmit(q)
    setQuestion("")
  }

  const handleSelectSuggestion = (sug: string) => {
    setQuestion(sug)
    setValidationError(null)
  }

  return (
    <Card className="rounded-lg border border-neutral-200 bg-white shadow-xs dark:border-[#262930] dark:bg-[#121418]">
      <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-4 sm:p-5 pb-3 dark:border-[#262930] dark:bg-[#181a1f]/70">
        <div className="flex items-center gap-2">
          <Swords className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0" />
          <CardTitle className="text-xs font-mono font-semibold uppercase tracking-wider text-neutral-900 dark:text-neutral-100">
            KONSOL UJI SILANG TESIS // {tk} &lt;EQUITY&gt;
          </CardTitle>
        </div>
      </CardHeader>

      <CardContent className="p-4 sm:p-5 space-y-4 font-sans">
        {/* Anti-Sycophancy Principle Banner */}
        <div className="rounded-md border border-amber-200 bg-amber-50/60 p-3 text-xs leading-relaxed text-neutral-700 dark:border-amber-900/40 dark:bg-amber-950/20 dark:text-neutral-300">
          <div className="flex items-center gap-1.5 font-mono text-[11px] font-bold text-amber-800 dark:text-amber-300">
            <ShieldCheck className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
            <span>[PROTOKOL] ARBITRASE INDEPENDEN (ANTI-SYCOPHANCY)</span>
          </div>
          <p className="mt-1 text-xs text-neutral-600 dark:text-neutral-400">
            Agen evaluasi dirancang independen dan tidak akan menyetujui klaim pengguna tanpa verifikasi data audited IDX. Jika kritik terbukti valid secara empiris, model akan melakukan penyesuaian (CONCEDE). Jika tidak valid, kritik akan ditolak (REJECT) disertai argumen pembuktian.
          </p>
        </div>

        {/* Suggestion Chips */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 font-mono text-[10px] font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
            <Sparkles className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
            <span>CONTOH TOPIK KRITIK TESIS:</span>
          </div>
          <div className="flex flex-col gap-1.5">
            {suggestions.map((sug, i) => (
              <button
                key={i}
                type="button"
                onClick={() => handleSelectSuggestion(sug)}
                disabled={loading}
                className="text-left rounded-md border border-neutral-200 bg-neutral-50/50 px-3 py-2 text-xs text-neutral-700 hover:border-neutral-300 hover:bg-neutral-100 transition-colors disabled:opacity-50 cursor-pointer dark:border-[#262930] dark:bg-[#15171c] dark:text-neutral-300 dark:hover:border-neutral-600 dark:hover:bg-[#181a1f]"
              >
                <span className="font-mono text-amber-600 dark:text-amber-400 mr-1.5 font-bold">&gt;</span>
                <span>{sug}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Form Input */}
        <form onSubmit={handleSubmit} className="space-y-3 pt-1">
          <div className="space-y-1.5">
            <label className="font-mono text-[10px] font-semibold uppercase tracking-wider text-neutral-600 dark:text-neutral-400">
              TERMINAL PROMPT &gt; MASUKKAN KRITIK ATAU PERTANYAAN
            </label>
            <textarea
              rows={3}
              value={question}
              onChange={(e) => {
                setQuestion(e.target.value)
                if (validationError) setValidationError(null)
              }}
              placeholder={`Contoh: WACC 8.4% terlalu rendah dibanding profil risiko emiten migas, bagaimana sensitivitas fair value jika dinaikkan ke 10%?`}
              disabled={loading}
              className="w-full rounded-md border border-neutral-300 bg-white p-3 font-sans text-xs leading-relaxed text-neutral-900 outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 disabled:opacity-50 resize-none dark:border-[#262930] dark:bg-[#121418] dark:text-neutral-100 dark:focus:border-amber-400"
            />
          </div>

          {validationError && (
            <div className="flex items-center gap-2 rounded-md border border-amber-300 bg-amber-500/10 p-2.5 font-mono text-[11px] text-amber-800 dark:border-amber-800 dark:text-amber-300">
              <AlertCircle className="h-3.5 w-3.5 text-amber-600 shrink-0 dark:text-amber-400" />
              <span>[VALIDATION ERROR] {validationError}</span>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 rounded-md border border-rose-300 bg-rose-500/10 p-2.5 font-mono text-[11px] text-rose-800 dark:border-rose-800 dark:text-rose-300">
              <AlertCircle className="h-3.5 w-3.5 text-rose-600 shrink-0 dark:text-rose-400" />
              <div>
                <span className="font-bold">[SUBMIT ERROR] </span>
                <span>{error}</span>
              </div>
            </div>
          )}

          <Button
            type="submit"
            disabled={loading || !question.trim()}
            className="w-full h-9 gap-2 rounded-md bg-neutral-900 text-white hover:bg-neutral-800 font-mono text-xs font-semibold tracking-wider cursor-pointer dark:bg-amber-400 dark:text-black dark:hover:bg-amber-300 disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                <span>[EXECUTING] MEMVERIFIKASI ARGUMEN &amp; BUKTI AUDIT...</span>
              </>
            ) : (
              <>
                <Send className="h-3.5 w-3.5" />
                <span>[ENTER] EKSEKUSI TANTANGAN TESIS</span>
              </>
            )}
          </Button>
        </form>

        <div className="font-mono text-[10px] text-neutral-400 dark:text-neutral-500 text-center sm:text-left">
          ENDPOINT :: POST /api/challenge // ENCRYPTED AUDIT LOG (debate.json)
        </div>
      </CardContent>
    </Card>
  )
}
