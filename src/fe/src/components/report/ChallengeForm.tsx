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
    <Card className="rounded-none border border-neutral-300 bg-white shadow-none dark:border-[#262930] dark:bg-[#121316]">
      <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3 pb-2.5 dark:border-[#262930] dark:bg-[#181a1f]/70">
        <div className="flex items-center gap-2">
          <Swords className="h-4 w-4 text-amber-600 dark:text-amber-400" />
          <CardTitle className="text-xs font-mono font-semibold uppercase tracking-wider text-neutral-900 dark:text-neutral-100">
            AUDIT CONSOLE :: ADVERSARIAL THESIS DEBATE // {tk} &lt;EQUITY&gt;
          </CardTitle>
        </div>
      </CardHeader>

      <CardContent className="p-3 sm:p-4 space-y-3.5">
        {/* Anti-Sycophancy Principle Banner */}
        <div className="border border-neutral-300 bg-neutral-50/50 p-2.5 font-mono text-[10px] leading-relaxed text-neutral-600 dark:border-[#262930] dark:bg-[#15171c] dark:text-neutral-400">
          <div className="flex items-center gap-1.5 font-bold text-neutral-800 dark:text-neutral-200">
            <ShieldCheck className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
            <span>[PROTOCOL] INDEPENDENT RED TEAM ARBITRATION (ANTI-SYCOPHANCY)</span>
          </div>
          <p className="mt-1 font-sans text-xs text-neutral-600 dark:text-neutral-400">
            Agent dirancang independen: dilarang menyetujui klaim pengguna tanpa bukti empiris. Jika kritik didukung data audited IDX, model akan melakukan penyesuaian (CONCEDE). Jika argumen tidak valid, kritik akan ditolak (REJECT) disertai pembuktian data.
          </p>
        </div>

        {/* Suggestion Chips */}
        <div className="space-y-1.5">
          <div className="flex items-center gap-1.5 font-mono text-[10px] font-semibold uppercase tracking-wider text-neutral-600 dark:text-neutral-400">
            <Sparkles className="h-3 w-3 text-amber-600 dark:text-amber-400" />
            <span>PILOT ARGUMENTS // CONTOH KRITIK TESIS:</span>
          </div>
          <div className="flex flex-col gap-1">
            {suggestions.map((sug, i) => (
              <button
                key={i}
                type="button"
                onClick={() => handleSelectSuggestion(sug)}
                disabled={loading}
                className="text-left border border-neutral-300 bg-white px-2.5 py-1.5 font-mono text-[11px] text-neutral-700 hover:border-neutral-400 hover:bg-neutral-50 transition-colors disabled:opacity-50 cursor-pointer dark:border-[#262930] dark:bg-[#15171c] dark:text-neutral-300 dark:hover:border-neutral-600 dark:hover:bg-[#181a1f]"
              >
                <span className="text-amber-600 dark:text-amber-400 mr-1.5">&gt;</span>
                {sug}
              </button>
            ))}
          </div>
        </div>

        {/* Form Input */}
        <form onSubmit={handleSubmit} className="space-y-2.5 pt-1">
          <div className="space-y-1">
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
              className="w-full rounded-none border border-neutral-300 bg-white p-2.5 font-mono text-xs leading-relaxed text-neutral-900 outline-none focus:border-amber-500 focus:ring-0 disabled:opacity-50 resize-none dark:border-[#262930] dark:bg-[#121316] dark:text-neutral-100 dark:focus:border-amber-400"
            />
          </div>

          {validationError && (
            <div className="flex items-center gap-1.5 border border-amber-300 bg-amber-500/10 p-2 font-mono text-[11px] text-amber-800 dark:border-amber-800 dark:text-amber-300">
              <AlertCircle className="h-3.5 w-3.5 text-amber-600 shrink-0 dark:text-amber-400" />
              <span>[VALIDATION ERROR] {validationError}</span>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-1.5 border border-rose-300 bg-rose-500/10 p-2 font-mono text-[11px] text-rose-800 dark:border-rose-800 dark:text-rose-300">
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
            className="w-full h-8 gap-2 rounded-none bg-neutral-900 text-white hover:bg-neutral-800 font-mono text-[11px] font-semibold tracking-wider cursor-pointer dark:bg-amber-400 dark:text-black dark:hover:bg-amber-300 disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                <span>[EXECUTING] MEMVERIFIKASI ARGUMEN &amp; BUKTI AUDIT...</span>
              </>
            ) : (
              <>
                <Send className="h-3 w-3" />
                <span>[ENTER] EKSEKUSI TANTANGAN TESIS</span>
              </>
            )}
          </Button>
        </form>

        <div className="font-mono text-[10px] text-neutral-500 dark:text-neutral-400">
          ENDPOINT :: POST /api/challenge // ENCRYPTED AUDIT LOG (debate.json)
        </div>
      </CardContent>
    </Card>
  )
}
