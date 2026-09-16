import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowRight, Terminal, FileText, AlertTriangle } from "lucide-react"

export const Route = (createFileRoute as any)("/mock-sectors/$ticker")({
  component: MockSectorsRedirect,
})

// Halaman lama sudah dipensiunkan - data tiruan dihapus, semua laporan live-only.
function MockSectorsRedirect() {
  const params = Route.useParams() as { ticker?: string }
  const rawTicker = (params?.ticker || "BBCA").toUpperCase()
  const validQuintet = ["RATU", "CDIA", "MTEL", "BBCA", "ADRO"]
  const tk = validQuintet.includes(rawTicker) ? rawTicker : "BBCA"

  return (
    <div className="mx-auto max-w-xl py-12 font-mono">
      <div className="rounded-md border border-amber-500/40 bg-white p-5 shadow-xs dark:border-[#262930] dark:bg-[#121418]">
        {/* Header Ribbon */}
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400">
          <AlertTriangle className="h-4 w-4" />
          <span>[SYSTEM NOTICE] ROUTE DEPRECATED // MOCK DATA RETIRED</span>
        </div>

        <div className="mt-3 space-y-2">
          <h1 className="text-base font-bold text-neutral-900 dark:text-neutral-100">
            Halaman Data Tiruan Sudah Dipensiunkan
          </h1>
          <p className="text-xs leading-relaxed text-neutral-600 dark:text-neutral-400">
            Seluruh data tiruan telah dihapus permanen untuk menjamin integritas riset. Sistem Sektoral.id
            kini beroperasi secara <span className="font-semibold text-emerald-600 dark:text-emerald-400">100% Live-Only</span>{" "}
            menggunakan data keuangan audited IDX via Sectors API dan engine deterministik.
          </p>
        </div>

        <div className="mt-6 flex flex-wrap gap-2.5 pt-4 border-t border-neutral-200 dark:border-[#1e2229]">
          <Link
            to={`/report/${tk}` as any}
            className="inline-flex h-8 items-center gap-1.5 rounded-lg bg-[#0E6E63] px-3 text-xs font-medium text-white transition-opacity hover:opacity-90"
          >
            <FileText className="h-3.5 w-3.5" />
            <span>Buka laporan {tk}</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>

          <Link
            to="/"
            className="inline-flex h-8 items-center gap-1.5 rounded border border-neutral-300 bg-neutral-100 px-3 text-xs font-bold text-neutral-800 transition-colors hover:bg-neutral-200 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-200 dark:hover:bg-neutral-700"
          >
            <Terminal className="h-3.5 w-3.5 text-neutral-400" />
            <span>[ESC] Market Monitor Hub</span>
          </Link>
        </div>

        <div className="mt-4 text-[10px] text-neutral-400 dark:text-neutral-500">
          STATUS: 301 DEPRECATION // DESTINATION: /report/{tk}
        </div>
      </div>
    </div>
  )
}

