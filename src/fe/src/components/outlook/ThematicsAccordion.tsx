import * as React from "react"
import type { MacroThematic } from "@/lib/types"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Compass, ChevronDown, ChevronUp } from "lucide-react"

interface ThematicsAccordionProps {
  thematics: MacroThematic[]
}

export function ThematicsAccordion({ thematics }: ThematicsAccordionProps) {
  const [openIndex, setOpenIndex] = React.useState<number | null>(0)

  return (
    <Card className="border-[#262d3a] bg-[#111317]">
      <CardHeader className="pb-2 border-b border-[#1d222c]">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold flex items-center gap-2 text-slate-100">
            <Compass className="h-4 w-4 text-amber-400" />
            <span>5 Structural Macro Thematics: Catalysts Driving Indonesia 2026</span>
          </CardTitle>
          <Badge variant="outline" className="font-mono text-[10px]">
            STRATEGY THEMATICS
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-3 divide-y divide-[#1e2430]">
        {thematics.map((t, idx) => {
          const isOpen = openIndex === idx
          return (
            <div key={t.number} className="py-3 first:pt-0 last:pb-0">
              <button
                onClick={() => setOpenIndex(isOpen ? null : idx)}
                className="w-full flex items-center justify-between text-left py-1 group cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <div className="h-6 w-6 rounded bg-amber-500/10 border border-amber-500/30 flex items-center justify-center font-mono font-bold text-xs text-amber-400">
                    #{t.number}
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-100 group-hover:text-amber-300 transition-colors font-sans">
                      {t.themeTitle}
                    </div>
                    <div className="text-[11px] text-slate-400 font-sans">{t.subtitle}</div>
                  </div>
                </div>

                <div className="text-slate-400 group-hover:text-slate-200">
                  {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </div>
              </button>

              {isOpen && (
                <div className="mt-3 pl-9 space-y-3 font-sans text-xs animate-in fade-in duration-150">
                  <p className="text-slate-300 leading-relaxed">{t.coreNarrative}</p>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 font-mono text-[11px]">
                    {t.keyDataPoints.map((dp, i) => (
                      <div key={i} className="p-2.5 rounded bg-[#161a22] border border-[#212734]">
                        <div className="text-[10px] text-slate-400 uppercase">{dp.label}</div>
                        <div className="text-slate-200 font-bold mt-0.5">{dp.value}</div>
                      </div>
                    ))}
                  </div>

                  <div className="flex items-center gap-2 pt-1">
                    <span className="text-slate-400 text-[11px] font-mono">Key Beneficiaries:</span>
                    <div className="flex flex-wrap gap-1.5 font-mono text-[10px]">
                      {t.beneficiarySectors.map((sec) => (
                        <span key={sec} className="rounded bg-[#1a1f29] px-2 py-0.5 text-amber-300 border border-[#262f3f]">
                          {sec}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
