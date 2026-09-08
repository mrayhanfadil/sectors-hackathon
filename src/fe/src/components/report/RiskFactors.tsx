import { Link } from "@tanstack/react-router"
import {
  AlertTriangle,
  ShieldAlert,
  ArrowRight,
  Scale,
  Shield,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"

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

  // LOUD policy: ticker-specific leverage figures were hardcoded demo text
  // rendered on arbitrary tickers. No leverage note until BE supplies ratios.
  const leverageTrajectoryNote: string | null = null
  void isSotp
  void isInfra

  return (
    <section id="risk-factors" className="space-y-3 scroll-mt-28">
      {/* Terminal Section Header */}
      <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-neutral-200 pb-1.5 dark:border-[#262930]">
        <div className="flex items-center gap-2">
          <span className="rounded bg-neutral-900 px-1.5 py-0.5 font-mono text-[10px] font-bold text-amber-400 dark:bg-amber-400/10 dark:text-amber-400">
            04
          </span>
          <h2 className="font-mono text-xs font-bold uppercase tracking-wider text-neutral-900 dark:text-neutral-100">
            {tk} IJ &lt;EQUITY&gt; // RISK FACTORS &amp; SOLVENCY TRAJECTORY
          </h2>
        </div>
        <span className="font-mono text-[10px] text-neutral-400">
          STRESS TEST: WACC DRIFT · LEVERAGE · MACRO DRIVERS
        </span>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {/* Card 1: Lintasan Solvabilitas & Struktur Utang */}
        <Card className="rounded-md border border-neutral-300 bg-white shadow-none dark:border-[#262930] dark:bg-[#121316]">
          <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3 pb-2 dark:border-[#1f2228] dark:bg-[#181a1f]/70">
            <div className="flex items-center gap-2">
              <Scale className="h-4 w-4 text-amber-500" />
              <CardTitle className="font-mono text-xs font-bold uppercase tracking-wide text-neutral-900 dark:text-neutral-100">
                DEBT STRUCTURE &amp; SOLVENCY TRAJECTORY
              </CardTitle>
            </div>
            <CardDescription className="font-mono text-[10px] text-neutral-400">
              EVALUATION OF INTEREST-BEARING DEBT &amp; CASH RUNWAY
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 p-3 pt-2.5">
            {leverageTrajectoryNote ? (
              <div className="rounded border border-amber-300 bg-amber-50 p-2.5 font-mono text-xs text-amber-900 dark:border-amber-800/60 dark:bg-amber-950/60 dark:text-amber-200">
                {leverageTrajectoryNote}
              </div>
            ) : (
              <p className="text-xs leading-relaxed text-neutral-700 dark:text-neutral-300">
                Struktur utang dievaluasi berkala berdasarkan rasio liabilitas berbunga terhadap ekuitas (DER), maturities schedule, dan kemampuan pembayaran bunga (Interest Coverage Ratio).
              </p>
            )}

            {ratios && Object.keys(ratios).length > 0 && (
              <div className="space-y-1.5 border-t border-neutral-200 pt-2 font-mono text-xs dark:border-[#1f2228]">
                <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                  SOLVENCY METRICS PROFILE:
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(ratios).slice(0, 4).map(([k, v]) => (
                    <span
                      key={k}
                      className="inline-flex items-center gap-1.5 rounded border border-neutral-200 bg-neutral-50 px-2 py-0.5 text-xs dark:border-[#262930] dark:bg-[#181a1f]"
                    >
                      <span className="text-[10px] uppercase text-neutral-500 dark:text-neutral-400">{k}:</span>
                      <span className="font-bold text-neutral-900 tabular-nums dark:text-neutral-100">{String(v)}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Card 2: Macro & Regulatory Risks */}
        <Card className="rounded-md border border-neutral-300 bg-white shadow-none dark:border-[#262930] dark:bg-[#121316]">
          <CardHeader className="border-b border-neutral-200 bg-neutral-50/70 p-3 pb-2 dark:border-[#1f2228] dark:bg-[#181a1f]/70">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              <CardTitle className="font-mono text-xs font-bold uppercase tracking-wide text-neutral-900 dark:text-neutral-100">
                MACRO &amp; INDUSTRY REGULATORY RISKS
              </CardTitle>
            </div>
            <CardDescription className="font-mono text-[10px] text-neutral-400">
              EXTERNAL DOWNSIDE DRIVERS &amp; DISCOUNT SENSITIVITY
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 p-3 pt-2.5 text-xs leading-relaxed text-neutral-700 dark:text-neutral-300">
            <div className="flex items-start gap-2 rounded border border-neutral-200 bg-neutral-50/60 p-2 dark:border-[#262930] dark:bg-[#181a1f]/60">
              <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
              <div>
                <strong className="font-semibold text-neutral-900 dark:text-neutral-100">Volatilitas Suku Bunga &amp; Biaya Dana: </strong>
                Kenaikan yield obligasi pemerintah dapat mengerek Cost of Capital (WACC) dan menekan valuasi diskonto arus kas.
              </div>
            </div>
            <div className="flex items-start gap-2 rounded border border-neutral-200 bg-neutral-50/60 p-2 dark:border-[#262930] dark:bg-[#181a1f]/60">
              <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
              <div>
                <strong className="font-semibold text-neutral-900 dark:text-neutral-100">Kepatuhan Regulasi &amp; Kebijakan Sektoral: </strong>
                Perubahan tarif batas atas/bawah, regulasi DMO energi, kepemilikan asing, atau kebijakan dividen BUMN / swasta.
              </div>
            </div>
            <div className="flex items-start gap-2 rounded border border-neutral-200 bg-neutral-50/60 p-2 dark:border-[#262930] dark:bg-[#181a1f]/60">
              <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
              <div>
                <strong className="font-semibold text-neutral-900 dark:text-neutral-100">Dinamika Kompetisi &amp; Intensitas Capex: </strong>
                Perang tarif antar operator atau kenaikan belanja modal ekspansi yang memperlambat laju arus kas bebas (FCFF).
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Card 3: Uji Tesis / Red Team Challenge Banner */}
      <Card className="rounded-md border border-neutral-800 bg-[#0c0d0e] text-white shadow-none dark:border-[#262930] dark:bg-[#0c0d0e]">
        <CardContent className="flex flex-col items-start justify-between gap-3 p-3.5 sm:flex-row sm:items-center sm:p-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-amber-400" />
              <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-amber-400">
                RED TEAM THESIS VERIFICATION // ADVERSARIAL AUDIT
              </h3>
            </div>
            <p className="max-w-xl text-xs leading-relaxed text-neutral-300">
              Memiliki pandangan berbeda terhadap asumsi WACC, margin operasional, atau pertumbuhan terminal? Ajukan kritik ke agent adversarial untuk memverifikasi ketahanan model.
            </p>
          </div>
          <Link
            to="/report/$ticker/challenge"
            params={{ ticker: tk }}
            className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded border border-amber-400/40 bg-amber-400/10 px-3 py-1.5 font-mono text-xs font-bold text-amber-300 hover:bg-amber-400/20 transition-colors"
          >
            <Shield className="h-3.5 w-3.5" />
            <span>[F3] UJI TESIS &gt;</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </CardContent>
      </Card>
    </section>
  )
}

