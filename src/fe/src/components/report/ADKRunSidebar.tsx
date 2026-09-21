import { useEffect, useState } from "react"
import { Link } from "@tanstack/react-router"
import { Loader2, ChevronRight, Info, Compass } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { AdkRunCard, type Log, type HistoryItem } from "./AdkRunCard"

export interface ADKRunSidebarProps {
  ticker: string
  provenance?: string
  logLoading?: boolean
  logData?: {
    has_run: boolean
    log: Log
    history: HistoryItem[]
  } | null
}

const CHAPTERS = [
  { href: "#cover-rating", label: "Ringkasan dan peringkat" },
  { href: "#key-financials", label: "Ringkasan keuangan & proyeksi" },
  { href: "#performance-quadrants", label: "Visualisasi kinerja keuangan" },
  { href: "#valuation-spread", label: "Nilai wajar dan sensitivitas DCF" },
  { href: "#peers-5a", label: "Valuasi komparasi peer" },
  { href: "#peers-5b", label: "Valuasi relatif historis" },
  { href: "#financial-statements", label: "Laporan keuangan (Laba rugi & neraca)" },
  { href: "#cashflow-ratios", label: "Arus kas dan rasio" },
  { href: "#risk-factors", label: "Faktor risiko" },
  { href: "#sources-disclaimer", label: "Cara membaca dan disklaimer" },
]

export function ADKRunSidebar({
  ticker,
  provenance,
  logLoading = false,
  logData,
}: ADKRunSidebarProps) {
  const tk = ticker.toUpperCase()
  const [activeChapter, setActiveChapter] = useState<string>(CHAPTERS[0].href)

  // Scrollspy: highlight the chapter currently in view. Sections mount
  // asynchronously after the payload loads, so re-scan the DOM on mutations.
  useEffect(() => {
    const seen = new Set<Element>()
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) setActiveChapter(`#${e.target.id}`)
        }
      },
      { rootMargin: "-25% 0px -60% 0px" },
    )
    const scan = () => {
      for (const c of CHAPTERS) {
        const el = document.querySelector(c.href)
        if (el && !seen.has(el)) {
          seen.add(el)
          io.observe(el)
        }
      }
    }
    scan()
    const mo = new MutationObserver(scan)
    mo.observe(document.body, { childList: true, subtree: true })
    return () => {
      io.disconnect()
      mo.disconnect()
    }
  }, [ticker])

  return (
    <aside className="w-full shrink-0 space-y-4 lg:w-[320px]">
      {/* 1. ADK Run Card */}
      {logLoading ? (
        <Card className="rounded-xl border border-[#D9D9D9] bg-white p-5 dark:border-[#262930] dark:bg-[#090a0c]">
          <div className="flex items-center gap-2 text-xs text-[#666666] dark:text-[#666666]">
            <Loader2 className="h-4 w-4 animate-spin text-[#0928B1] dark:text-[#7596FF]" />
            <span>Menghubungkan ke proses analisis...</span>
          </div>
        </Card>
      ) : logData ? (
        <AdkRunCard
          ticker={tk}
          log={logData.log}
          history={logData.history ?? []}
          hasRun={logData.has_run}
        />
      ) : (
        <AdkRunCard
          ticker={tk}
          log={null}
          history={[]}
          hasRun={false}
        />
      )}

      {/* 2. Fast Section Jump Navigation (with scrollspy) */}
      <Card className="rounded-xl border border-[#D9D9D9] bg-white dark:border-[#262930] dark:bg-[#090a0c]">
        <CardHeader className="border-b border-[#D9D9D9] p-4 pb-3 dark:border-[#262930]">
          <div className="flex items-center gap-2">
            <Compass className="h-4 w-4 text-[#0928B1] dark:text-[#7596FF]" />
            <CardTitle className="text-xs font-semibold text-[#333333] dark:text-[#f1f5f9]">
              Daftar bab laporan
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent className="p-3">
          <nav className="space-y-0.5 text-xs">
            {CHAPTERS.map((item, idx) => {
              const isActive = activeChapter === item.href
              return (
                <a
                  key={item.href}
                  href={item.href}
                  aria-current={isActive ? "true" : undefined}
                  className={`flex items-center justify-between rounded-md px-2.5 py-1.5 transition-colors ${
                    isActive
                      ? "bg-[#B4C7FF] font-semibold text-[#333333] dark:bg-[#1e2229] dark:text-[#f1f5f9]"
                      : "text-[#333333] hover:bg-[#B4C7FF] dark:text-[#f1f5f9] dark:hover:bg-[#1e2229]"
                  }`}
                >
                  <span className="truncate">
                    <span className="text-[#666666] mr-1.5 dark:text-[#666666]">{idx + 1}.</span>
                    {item.label}
                  </span>
                  <ChevronRight className="h-3 w-3 text-[#666666] shrink-0 dark:text-[#666666]" />
                </a>
              )
            })}
          </nav>

          {provenance && (
            <div className="mt-3 flex flex-wrap items-start gap-1.5 border-t border-[#D9D9D9] pt-2.5 text-[11px] text-[#666666] dark:border-[#262930] dark:text-[#666666]">
              <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#0928B1] dark:text-[#7596FF]" />
              <span className="min-w-0 flex-1 break-words text-ellipsis" title={provenance}>
                {provenance}
              </span>
            </div>
          )}
        </CardContent>
      </Card>
    </aside>
  )
}
