import { useState } from "react"
import { Link } from "@tanstack/react-router"
import {
  ArrowLeft,
  Download,
  Bot,
  Loader2,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { fetchPdf } from "@/lib/api"
import { RecommendationBadge } from "./RecommendationBadge"

export type ReportHeaderProps = {
  ticker: string
  activeTab?: "overview" | "valuation" | "challenge"
  name?: string | null
  companyName?: string | null
  rating?: string | null
  price?: number | null
  target?: number | null
  targetPrice?: number | null
  upside?: string | number | null
  updatedAt?: string | null
  template?: string | null
  source?: string | null
  onDownloadPdf?: () => void
  pdfLoading?: boolean
  pdfState?: "idle" | "loading" | "error"
  pdfMsg?: string | null
}

function fmtIDR(n: number | null | undefined): string {
  if (n == null || Number.isNaN(Number(n))) return "-"
  const parts = Math.abs(Number(n)).toFixed(0).split(".")
  const intPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".")
  const sign = Number(n) < 0 ? "-" : ""
  return `${sign}${intPart}`
}

function parseUpside(upside?: string | number | null): number | null {
  if (upside == null) return null
  if (typeof upside === "number") return upside
  const m = String(upside).replace(",", ".").match(/-?\d+(\.\d+)?/)
  return m ? Number(m[0]) : null
}

function formatUpside(val?: string | number | null): string {
  if (val == null) return "-"
  const num = parseUpside(val)
  if (num == null) return String(val).trim().replace(/,\s+(\d)/g, ",$1")
  const sign = num > 0 ? "+" : num < 0 ? "-" : ""
  const abs = Math.abs(num)
  const parts = abs.toFixed(1).split(".")
  const intPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".")
  const decPart = parts[1]
  return `${sign}${intPart},${decPart}%`
}

function formatArchetype(tpl?: string | null): string {
  if (!tpl) return "Tunggal"
  const map: Record<string, string> = {
    single: "Tunggal",
    sotp: "SOTP",
    bank: "Bank",
    banking: "Perbankan",
    mining: "Pertambangan",
    coal: "Batubara",
    infra: "Infrastruktur",
    infrastructure: "Infrastruktur",
    conglomerate: "Konglomerasi",
    unknown: "Tunggal",
  }
  return map[tpl.toLowerCase()] || tpl.charAt(0).toUpperCase() + tpl.slice(1)
}

function formatIndonesianDate(dateStr?: string | null): string | null {
  if (!dateStr) return null
  const trimmed = dateStr.trim()
  const isoMatch = trimmed.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (isoMatch) {
    const [, y, m, d] = isoMatch
    const months = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    const mIdx = parseInt(m, 10) - 1
    if (mIdx >= 0 && mIdx < 12) {
      return `${parseInt(d, 10)} ${months[mIdx]} ${y}`
    }
  }
  const enToId: Record<string, string> = {
    May: "Mei",
    August: "Agustus",
    Aug: "Agu",
    October: "Oktober",
    Oct: "Okt",
    December: "Desember",
    Dec: "Des",
    January: "Januari",
    February: "Februari",
    March: "Maret",
    June: "Juni",
    July: "Juli",
  }
  let result = trimmed
  for (const [en, id] of Object.entries(enToId)) {
    result = result.replace(new RegExp(`\\b${en}\\b`, "gi"), id)
  }
  return result
}

export function ReportHeader({
  ticker,
  activeTab = "valuation",
  name,
  companyName,
  rating,
  price,
  target,
  targetPrice,
  upside,
  updatedAt,
  template = "single",
  source,
  onDownloadPdf,
  pdfLoading: externalPdfLoading,
  pdfState: externalPdfState,
  pdfMsg,
}: ReportHeaderProps) {
  const tk = ticker.toUpperCase()
  const [internalPdfLoading, setInternalPdfLoading] = useState(false)
  const [internalPdfError, setInternalPdfError] = useState<string | null>(null)

  const finalName = name || companyName || ""
  const finalTarget = targetPrice != null ? targetPrice : target
  const isPdfBusy = externalPdfLoading ?? (externalPdfState === "loading" || internalPdfLoading)
  const errorMsg = pdfMsg || internalPdfError

  const upsideNum = parseUpside(upside)
  const upsidePositive = upsideNum != null && upsideNum > 0
  const upsideNegative = upsideNum != null && upsideNum < 0
  const upsideDisplay = formatUpside(upside)

  async function handlePdfDownload() {
    if (onDownloadPdf) {
      onDownloadPdf()
      return
    }
    setInternalPdfLoading(true)
    setInternalPdfError(null)
    try {
      await fetchPdf(tk)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      if (msg.includes("404") || msg.includes("not available") || msg.includes("soon")) {
        setInternalPdfError("Dokumen PDF belum tersedia di sistem")
      } else {
        setInternalPdfError(msg)
      }
      setTimeout(() => setInternalPdfError(null), 4000)
    } finally {
      setInternalPdfLoading(false)
    }
  }

  return (
    <div className="sticky top-0 z-20 -mx-4 -mt-6 mb-8 border-b border-[#E7E2D9] bg-[#FAF8F5]/95 backdrop-blur-sm dark:border-[#262930] dark:bg-[#090a0c]/95">
      {/* 2. Main Header Key-Stats Strip */}
      <div className="mx-auto max-w-[1100px] px-4 pt-4 pb-3">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          {/* Company Identity */}
          <div className="flex min-w-0 items-start gap-3.5">
            <Link
              to="/"
              className="mt-1 inline-flex items-center justify-center rounded-lg border border-[#E7E2D9] bg-[#FDFCF7] p-2 text-[#666666] hover:bg-[#FAF8F5] hover:text-[#333333] transition-colors dark:border-[#262930] dark:bg-[#090a0c] dark:text-[#666666] dark:hover:bg-[#1e2229] dark:hover:text-[#f1f5f9]"
              title="Kembali ke beranda"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>

            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2.5">
                <span className="rounded-md bg-[#1B365D]/10 px-2 py-0.5 text-xs font-bold text-[#1B365D] dark:bg-[#7596FF]/20 dark:text-[#7596FF]">
                  {tk}
                </span>
                <h1 className="truncate font-serif text-xl sm:text-2xl font-normal tracking-tight text-[#333333] dark:text-[#f1f5f9]">
                  {finalName || `${tk} Tbk.`}
                </h1>
                <RecommendationBadge rating={rating} size="md" />
              </div>

              <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-[#666666] dark:text-[#666666]">
                {template && (
                  <span className="rounded bg-[#FAF8F5] px-2 py-0.5 text-[11px] font-medium text-[#333333] border border-[#E7E2D9] dark:bg-[#262930] dark:border-[#262930] dark:text-[#f1f5f9]">
                    Arketipe: {formatArchetype(template)}
                  </span>
                )}
                {template && updatedAt && <span className="text-[#666666]">·</span>}
                {updatedAt && (
                  <span>
                    Diperbarui {formatIndonesianDate(updatedAt)} {source ? `(${source})` : ""}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Key Numbers & Actions */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-4 rounded-xl border border-[#E7E2D9] bg-[#FDFCF7] px-4 py-2.5 dark:border-[#262930] dark:bg-[#090a0c]">
              <div>
                <div className="text-[11px] text-[#666666] dark:text-[#666666]">Harga pasar</div>
                <div className="text-sm font-semibold text-[#333333] font-mono tabular-nums dark:text-[#f1f5f9]">
                  {price != null ? `Rp ${fmtIDR(price)}` : "-"}
                </div>
              </div>

              <div className="h-7 w-px bg-[#E7E2D9] dark:bg-[#262930]" />

              <div>
                <div className="text-[11px] text-[#666666] dark:text-[#666666]">Nilai wajar</div>
                <div className="text-sm font-semibold text-[#333333] font-mono tabular-nums dark:text-[#f1f5f9]">
                  {finalTarget != null ? `Rp ${fmtIDR(finalTarget)}` : "-"}
                </div>
              </div>

              <div className="h-7 w-px bg-[#E7E2D9] dark:bg-[#262930]" />

              <div>
                <div className="text-[11px] text-[#666666] dark:text-[#666666]">Potensi return</div>
                <div
                  className={`text-sm font-semibold font-mono tabular-nums ${
                    upsidePositive
                      ? "text-[#157F3D] dark:text-[#34D399]"
                      : upsideNegative
                      ? "text-[#B4232A] dark:text-[#F87171]"
                      : "text-[#666666] dark:text-[#666666]"
                  }`}
                >
                  {upsidePositive ? "▲ " : upsideNegative ? "▼ " : ""}
                  {upsideDisplay}
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handlePdfDownload}
                disabled={isPdfBusy}
                className="h-9 gap-1.5 rounded-lg border-[#E7E2D9] bg-[#FDFCF7] px-3.5 text-xs font-medium text-[#333333] hover:bg-[#FAF8F5] dark:border-[#262930] dark:bg-[#090a0c] dark:text-[#f1f5f9] dark:hover:bg-[#1e2229] cursor-pointer"
              >
                {isPdfBusy ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-[#1B365D] dark:text-[#7596FF]" />
                ) : (
                  <Download className="h-3.5 w-3.5 text-[#1B365D] dark:text-[#7596FF]" />
                )}
                <span>Unduh PDF</span>
              </Button>

              <Link
                to="/agent"
                search={{ ticker: tk } as any}
                className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-[#1B365D] px-3.5 text-xs font-medium text-white hover:bg-[#1B365D]/90 transition-colors dark:bg-[#7596FF] dark:text-[#090a0c] dark:hover:bg-[#3EBAA0]"
              >
                <Bot className="h-3.5 w-3.5" />
                <span>Proses analisis</span>
              </Link>
            </div>
          </div>
        </div>

        {errorMsg && (
          <div className="mt-3 rounded-lg border border-[#F8C8CB] bg-[#FDF2F2] px-3.5 py-2 text-xs text-[#B4232A] dark:border-[#B4232A]/40 dark:bg-[#B4232A]/20 dark:text-[#F87171]">
            {errorMsg}
          </div>
        )}
      </div>
    </div>
  )
}
