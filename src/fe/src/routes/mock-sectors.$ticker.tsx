import { createFileRoute } from "@tanstack/react-router"
import { ArrowRight, Home, FileText } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"

export const Route = (createFileRoute as any)("/mock-sectors/$ticker")({
  component: MockSectorsRedirect,
})

// Halaman lama sudah dipensiunkan — data tiruan dihapus, semua laporan live-only.
function MockSectorsRedirect() {
  const btn =
    "inline-flex h-8 items-center gap-1.5 rounded-md px-3 text-xs font-medium transition-colors"
  return (
    <div className="mx-auto max-w-xl py-10">
      <Card className="border-slate-200 bg-white p-2 shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg font-bold text-slate-900">
            Halaman ini sudah pindah
          </CardTitle>
          <CardDescription className="text-xs leading-relaxed text-slate-600">
            Data tiruan sudah dihapus. Semua laporan sekarang dibaca langsung dari backend
            (live-only). Buka laporan live BBCA atau kembali ke beranda.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <a href="/report/BBCA" className={`${btn} bg-slate-900 text-white hover:bg-slate-700`}>
            <FileText className="h-3.5 w-3.5" />
            Buka laporan BBCA
            <ArrowRight className="h-3.5 w-3.5" />
          </a>
          <a
            href="/"
            className={`${btn} border border-slate-200 bg-white text-slate-700 hover:bg-slate-50`}
          >
            <Home className="h-3.5 w-3.5" />
            Beranda
          </a>
        </CardContent>
      </Card>
    </div>
  )
}
