import { Shield, BookOpen, Cpu, Database } from "lucide-react"

export function Footer() {
  return (
    <footer className="mt-16 border-t border-[#1e232d] bg-[#0c0e12] py-8 text-xs text-slate-400 font-sans">
      <div className="mx-auto max-w-7xl px-4 space-y-6">
        {/* Disclosures & Regulatory Notice */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 p-4 rounded-lg bg-[#111317] border border-[#1f242e]">
          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5 font-mono text-amber-400 font-semibold text-xs">
              <Shield className="h-3.5 w-3.5" />
              <span>OJK COMPLIANCE & DISCLOSURE</span>
            </div>
            <p className="text-[11px] leading-relaxed text-slate-400">
              Sektoral.id produces deterministic algorithmic and fundamental equity research intelligence for educational and informational purposes. No automated trade placement or brokerage execution is conducted.
            </p>
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5 font-mono text-slate-200 font-semibold text-xs">
              <BookOpen className="h-3.5 w-3.5 text-amber-400" />
              <span>BENCHMARK RESEARCH CORPUS</span>
            </div>
            <p className="text-[11px] leading-relaxed text-slate-400">
              Calibrated against 15 institutional equity reports: HP RATU (Oil pure-play), BCA CDIA (Conglomerate SOTP), Kiwoom MTEL (Recurring infra), JPM Strategy 2026 (JCI 9,100), Samuel BBCA & BRIDS ADRO.
            </p>
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5 font-mono text-slate-200 font-semibold text-xs">
              <Database className="h-3.5 w-3.5 text-amber-400" />
              <span>DATA LAYER ARCHITECTURE</span>
            </div>
            <p className="text-[11px] leading-relaxed text-slate-400">
              P0-P1 Data Mode: 49 Indonesian equities seeded from <code className="text-amber-300 font-mono">data/sectors.db</code> SQLite with verified 5-year price series, sector KPIs, and synthetic financial model statements.
            </p>
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5 font-mono text-slate-200 font-semibold text-xs">
              <Cpu className="h-3.5 w-3.5 text-amber-400" />
              <span>LOCKED FRONTEND STACK (§6)</span>
            </div>
            <p className="text-[11px] leading-relaxed text-slate-400">
              CSR-only Architecture: Vite + React 19 + TypeScript + TanStack Query + Tailwind CSS v4. No Next.js SSR overhead; optimized for high-performance static rendering and PDF generation.
            </p>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] text-slate-500 font-mono pt-2 border-t border-[#181c24]">
          <div>
            © 2026 Sektoral.id — Institutional-Grade Equity Research for Indonesian Retail Investors
          </div>
          <div className="flex items-center gap-4">
            <span className="text-amber-400/80">Track: AI Agents & Market Intelligence</span>
            <span>Workdir: wt/t03-fe</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
