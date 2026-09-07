import { Link } from "@tanstack/react-router"
import {
  AlertTriangle,
  ShieldAlert,
  ArrowRight,
  TrendingDown,
  Activity,
  Layers,
  Scale,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

export interface RiskFactorsProps {
  ticker: string
  template?: string
  ratios?: Record<string, string | number>
}

export function RiskFactors({
  ticker,
  template = "single",
  ratios,
}: RiskFactorsProps) {
  const tk = ticker.toUpperCase()
  const isSotp = template.toLowerCase() === "sotp"
  const isInfra = template.toLowerCase() === "infra"

  const leverageTrajectoryNote = isSotp
    ? "CDIA gearing 96 → 170% + Debt/EBITDA 1.9 → 4.1x : lintasan utang pada pilar-pilar ekspansif memerlukan pemantauan ketat terhadap profil jatuh tempo."
    : isInfra
    ? "MTEL DER 0.67 → 0.69x, LT D/E 0.34 → 0.46x, ICR 2.0 → 4.0x : lintasan utang infrastruktur terkendali dengan arus kas kontraktual jangka panjang."
    : null

  return (
    <section id="risk-factors" className="space-y-4 scroll-mt-28">
      <div>
        <h2 className="text-[15px] font-semibold tracking-tight text-[#0a0a0a] dark:text-white">
          4. Faktor Risiko & Analisis Solvabilitas
        </h2>
        <p className="text-xs text-neutral-500 dark:text-neutral-400">
          Evaluasi sensitivitas utang, risiko pasar, dan potensi hambatan terhadap tesis investasi
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Card 1: Lintasan Solvabilitas & Struktur Utang */}
        <Card className="border-neutral-200 bg-white shadow-2xs dark:border-neutral-800 dark:bg-[#111111]">
          <CardHeader className="p-4 pb-2">
            <div className="flex items-center gap-2">
              <Scale className="h-4 w-4 text-neutral-700 dark:text-neutral-300" />
              <CardTitle className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
                Struktur Utang & Lintasan Solvabilitas
              </CardTitle>
            </div>
            <CardDescription className="text-[11px] text-neutral-400">
              Evaluasi risiko rasio utang dan ketahanan kas
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-2 space-y-3">
            {leverageTrajectoryNote ? (
              <div className="rounded-lg border border-amber-200 bg-amber-50/70 p-3 text-xs text-amber-900 leading-relaxed font-mono dark:border-amber-800 dark:bg-amber-950/70 dark:text-amber-100">
                {leverageTrajectoryNote}
              </div>
            ) : (
              <p className="text-xs text-neutral-600 leading-relaxed dark:text-neutral-400">
                Struktur utang dievaluasi berkala berdasarkan rasio liabilitas berbunga terhadap ekuitas dan kemampuan pembayaran bunga (ICR).
              </p>
            )}

            {ratios && Object.keys(ratios).length > 0 && (
              <div className="space-y-1.5 border-t border-neutral-100 pt-2.5 dark:border-neutral-800">
                <div className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wider dark:text-neutral-400">
                  Metrik Profil Risiko:
                </div>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(ratios).slice(0, 4).map(([k, v]) => (
                    <span
                      key={k}
                      className="inline-flex items-center gap-1.5 rounded-md border border-neutral-200 bg-neutral-50 px-2 py-1 text-xs text-neutral-700 font-mono dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-300"
                    >
                      <span className="text-neutral-500 font-sans dark:text-neutral-400">{k}:</span>
                      <span className="font-semibold text-neutral-900 dark:text-neutral-100">{String(v)}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Card 2: Risiko Makroekonomi & Regulasi */}
        <Card className="border-neutral-200 bg-white shadow-2xs dark:border-neutral-800 dark:bg-[#111111]">
          <CardHeader className="p-4 pb-2">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
              <CardTitle className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
                Risiko Makro & Regulasi Industri
              </CardTitle>
            </div>
            <CardDescription className="text-[11px] text-neutral-400">
              Faktor eksternal yang dapat mempengaruhi proyeksi laba
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-2 space-y-2.5 text-xs text-neutral-700 dark:text-neutral-300">
            <div className="flex items-start gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-neutral-400 mt-1.5 shrink-0 dark:bg-neutral-600" />
              <span>
                <strong className="text-neutral-900 dark:text-neutral-100">Volatilitas Suku Bunga & Biaya Dana:</strong> Kenaikan yield obligasi pemerintah dapat meningkatkan Cost of Capital (WACC) dan menekan valuasi diskonto.
              </span>
            </div>
            <div className="flex items-start gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-neutral-400 mt-1.5 shrink-0 dark:bg-neutral-600" />
              <span>
                <strong className="text-neutral-900 dark:text-neutral-100">Kepatuhan Regulasi & Kebijakan Fiskal:</strong> Perubahan ketentuan tarif, kepemilikan asing, atau kebijakan dividen BUMN / swasta.
              </span>
            </div>
            <div className="flex items-start gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-neutral-400 mt-1.5 shrink-0 dark:bg-neutral-600" />
              <span>
                <strong className="text-neutral-900 dark:text-neutral-100">Dinamika Kompetisi & Belanja Modal:</strong> Penurunan tarif layanan atau intensitas capex ekspansi yang melampaui estimasi awal.
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Card 3: Uji Tesis / Challenge Box */}
      <Card className="border-neutral-300 bg-neutral-900 text-white shadow-2xs dark:border-neutral-700 dark:bg-neutral-800">
        <CardContent className="p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-amber-400" />
              <h3 className="text-sm font-bold tracking-tight">
                Pusat Uji Tesis & Verifikasi Adversarial (Challenge Mode)
              </h3>
            </div>
            <p className="text-xs text-neutral-300 max-w-xl leading-relaxed">
              Memiliki pandangan berbeda terhadap asumsi WACC, margin operasional, atau pertumbuhan terminal? Ajukan kritik untuk memverifikasi ketahanan model riset.
            </p>
          </div>
          <Link
            to="/report/$ticker/challenge"
            params={{ ticker: tk }}
            className="inline-flex items-center justify-center gap-1.5 rounded-md bg-white px-4 py-2 text-xs font-semibold text-neutral-900 hover:bg-neutral-100 transition-colors shrink-0 shadow-xs dark:bg-white dark:text-black dark:hover:bg-neutral-200"
          >
            <span>Uji Asumsi Sekarang</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </CardContent>
      </Card>
    </section>
  )
}
