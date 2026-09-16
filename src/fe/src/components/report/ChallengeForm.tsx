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
    "WACC 11,1% terlalu tinggi dibanding cost of fund CASA 75%?",
    "NIM 5,8% berisiko tertekan tren penurunan suku bunga BI?",
    "Pertumbuhan kredit 10-12% FY26F terlalu agresif di tengah daya beli lesu?",
  ],
  MTEL: [
    "WACC 10,1% terlalu konservatif dibanding rata-rata industri menara?",
    "Tenancy ratio 1,57x berisiko melambat akibat konsolidasi telco?",
    "Capex fiber optik Rp 2,9 T dapat menekan arus kas bebas jangka pendek?",
  ],
  RATU: [
    "WACC 8,4% terlalu rendah untuk profil risiko migas Cepu?",
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
      setValidationError("Ketik pertanyaan atau kritik sebelum mengirim.")
      return
    }
    if (q.length < 5) {
      setValidationError("Pertanyaan minimal 5 karakter agar argumen dapat dianalisis secara tepat.")
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
    <Card className="rounded-xl border border-[#E7E3DA] bg-white dark:border-[#2A2822] dark:bg-[#1B1A16]">
      <CardHeader className="border-b border-[#E7E3DA] p-5 pb-3 dark:border-[#2A2822]">
        <div className="flex items-center gap-2">
          <Swords className="h-4 w-4 text-[#0E6E63] dark:text-[#4FD1B5] shrink-0" />
          <CardTitle className="text-sm font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
            Proposal uji silang tesis {tk}
          </CardTitle>
        </div>
      </CardHeader>

      <CardContent className="p-5 space-y-4">
        {/* Protocol Notice Banner */}
        <div className="rounded-lg border border-[#E7E3DA] bg-[#FBFAF7] p-3.5 text-xs leading-relaxed text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
          <div className="flex items-center gap-1.5 font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
            <ShieldCheck className="h-4 w-4 text-[#0E6E63] dark:text-[#4FD1B5] shrink-0" />
            <span>Protokol arbitrase independen</span>
          </div>
          <p className="mt-1 text-xs text-[#6B6659] dark:text-[#A8A296]">
            Agen evaluasi menguji kritik Anda secara objektif terhadap data keuangan audited IDX. Jika kritik terbukti valid secara empiris, model akan melakukan penyesuaian (Disesuaikan). Jika asumsi awal terbukti konsisten, kritik akan dijawab dengan pembuktian (Dipertahankan).
          </p>
        </div>

        {/* Suggestion Chips */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
            <Sparkles className="h-3.5 w-3.5 text-[#0E6E63] dark:text-[#4FD1B5]" />
            <span>Contoh topik kritik tesis:</span>
          </div>
          <div className="flex flex-col gap-2">
            {suggestions.map((sug, i) => (
              <button
                key={i}
                type="button"
                onClick={() => handleSelectSuggestion(sug)}
                disabled={loading}
                className="text-left rounded-lg border border-[#E7E3DA] bg-[#FBFAF7] px-3.5 py-2.5 text-xs text-[#1C1B17] hover:border-[#0E6E63] hover:bg-white transition-colors disabled:opacity-50 cursor-pointer dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#EDEAE3] dark:hover:border-[#4FD1B5] dark:hover:bg-[#1B1A16]"
              >
                <span>{sug}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Form Input */}
        <form onSubmit={handleSubmit} className="space-y-3 pt-1">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#1C1B17] dark:text-[#EDEAE3]">
              Kritik atau pertanyaan analisis
            </label>
            <textarea
              rows={3}
              value={question}
              onChange={(e) => {
                setQuestion(e.target.value)
                if (validationError) setValidationError(null)
              }}
              placeholder={`Contoh: WACC 8,4% terlalu rendah dibanding profil risiko emiten migas, bagaimana sensitivitas nilai wajar jika dinaikkan ke 10%?`}
              disabled={loading}
              className="w-full rounded-lg border border-[#E7E3DA] bg-white p-3 text-xs leading-relaxed text-[#1C1B17] outline-none focus:border-[#0E6E63] focus:ring-1 focus:ring-[#0E6E63] disabled:opacity-50 resize-none dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#EDEAE3] dark:focus:border-[#4FD1B5]"
            />
          </div>

          {validationError && (
            <div className="flex items-center gap-2 rounded-lg border border-[#F6E3B8] bg-[#FEF9EE] p-3 text-xs text-[#A16207] dark:border-[#A16207]/40 dark:bg-[#A16207]/20 dark:text-[#FBBF24]">
              <AlertCircle className="h-4 w-4 text-[#A16207] shrink-0" />
              <span>{validationError}</span>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 rounded-lg border border-[#F8C8CB] bg-[#FDF2F2] p-3 text-xs text-[#B4232A] dark:border-[#B4232A]/40 dark:bg-[#B4232A]/20 dark:text-[#F87171]">
              <AlertCircle className="h-4 w-4 text-[#B4232A] shrink-0" />
              <div>
                <span className="font-semibold">Galat pengiriman: </span>
                <span>{error}</span>
              </div>
            </div>
          )}

          <Button
            type="submit"
            disabled={loading || !question.trim()}
            className="w-full h-10 gap-2 rounded-lg bg-[#0E6E63] text-white hover:bg-[#0B5B52] text-xs font-medium cursor-pointer dark:bg-[#4FD1B5] dark:text-[#14130F] dark:hover:bg-[#3EBAA0] disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Memverifikasi argumen dan bukti audit...</span>
              </>
            ) : (
              <>
                <Send className="h-4 w-4" />
                <span>Kirim tantangan tesis</span>
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
