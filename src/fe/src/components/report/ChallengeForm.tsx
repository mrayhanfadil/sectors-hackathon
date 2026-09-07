import * as React from "react"
import {
  Swords,
  Send,
  Loader2,
  Sparkles,
  ShieldCheck,
  AlertCircle,
  HelpCircle,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
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
      setValidationError("Ketik pertanyaan atau kritik sebelum mengirim.")
      return
    }
    if (q.length < 5) {
      setValidationError("Pertanyaan minimal 5 karakter agar agent dapat menganalisis secara tepat.")
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
    <Card className="border-neutral-200 bg-white shadow-2xs dark:border-neutral-800 dark:bg-[#111111]">
      <CardHeader className="border-b border-neutral-100 bg-neutral-50/50 p-4 pb-3 dark:border-neutral-800 dark:bg-neutral-900/50">
        <div className="flex items-center gap-2">
          <Swords className="h-4 w-4 text-neutral-700 dark:text-neutral-300" />
          <CardTitle className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
            Uji & Tantang Tesis Valuasi ({tk})
          </CardTitle>
        </div>
        <CardDescription className="text-xs text-neutral-500 dark:text-neutral-400">
          Uji ketahanan model dengan kritik tajam - agent wajib mempertahankan tesis berbasis bukti
        </CardDescription>
      </CardHeader>

      <CardContent className="p-4 sm:p-6 space-y-4">
        {/* Anti-Sycophancy Principle Banner */}
        <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3 text-xs leading-relaxed text-neutral-600 dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-400">
          <div className="flex items-center gap-1.5 font-semibold text-neutral-800 dark:text-neutral-200">
            <ShieldCheck className="h-4 w-4 text-neutral-700 dark:text-neutral-300" />
            <span>Protokol Verifikasi Berimbang (Anti-Sycophancy)</span>
          </div>
          <p className="mt-1">
            Agent dirancang independen: dilarang menyetujui klaim pengguna tanpa bukti empiris. Jika kritik didukung data laporan keuangan IDX, model akan melakukan penyesuaian (CONCEDE). Jika argumen tidak valid, kritik akan ditolak (REJECT) disertai pembuktian data.
          </p>
        </div>

        {/* Suggestion Chips */}
        <div className="space-y-1.5">
          <div className="flex items-center gap-1.5 text-xs font-medium text-neutral-700 dark:text-neutral-300">
            <Sparkles className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
            <span>Pilihan Contoh Kritik Tesis:</span>
          </div>
          <div className="flex flex-col gap-1.5">
            {suggestions.map((sug, i) => (
              <button
                key={i}
                type="button"
                onClick={() => handleSelectSuggestion(sug)}
                disabled={loading}
                className="text-left rounded-md border border-neutral-200 bg-white px-3 py-2 text-xs text-neutral-700 hover:border-neutral-300 hover:bg-neutral-50 transition-colors disabled:opacity-50 cursor-pointer dark:border-neutral-800 dark:bg-[#111111] dark:text-neutral-300 dark:hover:border-neutral-700 dark:hover:bg-neutral-900"
              >
                {sug}
              </button>
            ))}
          </div>
        </div>

        {/* Form Input */}
        <form onSubmit={handleSubmit} className="space-y-3 pt-2">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-neutral-700 dark:text-neutral-300">
              Kritik atau Pertanyaan Pengguna
            </label>
            <textarea
              rows={3}
              value={question}
              onChange={(e) => {
                setQuestion(e.target.value)
                if (validationError) setValidationError(null)
              }}
              placeholder={`Contoh: WACC 8.4% terlalu rendah dibanding emiten sejenis, bagaimana sensitivitas fair value jika dinaikkan ke 10%?`}
              disabled={loading}
              className="w-full rounded-md border border-neutral-200 bg-white p-3 text-xs leading-relaxed text-neutral-900 outline-none focus:border-neutral-900 focus:ring-1 focus:ring-neutral-900 disabled:opacity-50 resize-none font-sans dark:border-neutral-800 dark:bg-[#111111] dark:text-neutral-100 dark:focus:border-neutral-700 dark:focus:ring-neutral-100"
            />
          </div>

          {validationError && (
            <div className="flex items-center gap-1.5 rounded-md border border-amber-200 bg-amber-50 p-2 text-xs text-amber-800 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200">
              <AlertCircle className="h-3.5 w-3.5 text-amber-600 shrink-0 dark:text-amber-400" />
              <span>{validationError}</span>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-1.5 rounded-md border border-rose-200 bg-rose-50 p-2.5 text-xs text-rose-800 dark:border-rose-800 dark:bg-rose-950 dark:text-rose-200">
              <AlertCircle className="h-4 w-4 text-rose-600 shrink-0 dark:text-rose-400" />
              <div>
                <span className="font-semibold">Gagal memproses tantangan: </span>
                <span>{error}</span>
              </div>
            </div>
          )}

          <Button
            type="submit"
            disabled={loading || !question.trim()}
            className="w-full h-9 gap-2 bg-neutral-900 text-white hover:bg-neutral-800 text-xs font-medium cursor-pointer dark:bg-neutral-800"
          >
            {loading ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                <span>Memverifikasi Argumen & Menguji Bukti...</span>
              </>
            ) : (
              <>
                <Send className="h-3.5 w-3.5" />
                <span>Kirim Tantangan ke Agent</span>
              </>
            )}
          </Button>
        </form>

        <div className="pt-2 text-[11px] text-neutral-400">
          Endpoint: POST /api/challenge - log terenkripsi di berkas audit sistem (debate.json).
        </div>
      </CardContent>
    </Card>
  )
}
