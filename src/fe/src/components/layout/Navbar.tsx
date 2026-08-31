import * as React from "react"
import { Search, ShieldAlert, Sparkles, TrendingUp, BarChart3, Radio } from "lucide-react"
import { SearchModal } from "@/components/common/SearchModal"
import { Badge } from "@/components/ui/badge"

export function Navbar() {
  const [isSearchOpen, setIsSearchOpen] = React.useState(false)

  // Current path detection for active styling
  const path = typeof window !== "undefined" ? window.location.pathname : "/"

  return (
    <>
      <header className="sticky top-0 z-30 border-b border-[#212631] bg-[#111317]/95 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-2.5">
          {/* Brand Logo & Tag */}
          <div className="flex items-center gap-3">
            <a href="/" className="flex items-center gap-2 group">
              <div className="h-7 w-7 rounded bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center font-mono font-bold text-black text-sm shadow-[0_0_12px_rgba(245,158,11,0.35)]">
                S
              </div>
              <div className="flex flex-col">
                <span className="font-serif text-base font-semibold tracking-tight text-slate-100 group-hover:text-amber-400 transition-colors">
                  Sektoral<span className="text-amber-500 font-sans">.id</span>
                </span>
                <span className="text-[10px] font-mono tracking-wider text-slate-400 -mt-1 uppercase">
                  Institutional Equity Research
                </span>
              </div>
            </a>

            <div className="hidden lg:flex items-center gap-1 ml-2 pl-3 border-l border-[#212631]">
              <Badge variant="amber" className="text-[10px]">T03 Frontend</Badge>
              <Badge variant="secondary" className="text-[10px]">CSR Vite + React + TS</Badge>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1 text-xs font-medium">
            <a
              href="/"
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 transition-colors ${
                path === "/"
                  ? "bg-[#1d222c] text-amber-400 font-semibold border border-amber-500/20"
                  : "text-slate-300 hover:bg-[#181b22] hover:text-slate-100"
              }`}
            >
              <BarChart3 className="h-3.5 w-3.5" />
              <span>Terminal</span>
            </a>

            <a
              href="/report/MTEL"
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 transition-colors ${
                path.startsWith("/report") && !path.includes("/challenge") && !path.includes("/sentiment")
                  ? "bg-[#1d222c] text-amber-400 font-semibold border border-amber-500/20"
                  : "text-slate-300 hover:bg-[#181b22] hover:text-slate-100"
              }`}
            >
              <Sparkles className="h-3.5 w-3.5 text-amber-400" />
              <span>Equity Reports</span>
            </a>

            <a
              href="/outlook"
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 transition-colors ${
                path === "/outlook"
                  ? "bg-[#1d222c] text-amber-400 font-semibold border border-amber-500/20"
                  : "text-slate-300 hover:bg-[#181b22] hover:text-slate-100"
              }`}
            >
              <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
              <span>Market Outlook (JCI 9,100)</span>
            </a>

            <a
              href="/challenge"
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 transition-colors ${
                path.includes("/challenge")
                  ? "bg-[#1d222c] text-amber-400 font-semibold border border-amber-500/20"
                  : "text-slate-300 hover:bg-[#181b22] hover:text-slate-100"
              }`}
            >
              <ShieldAlert className="h-3.5 w-3.5 text-red-400" />
              <span>Red Team Debate</span>
            </a>

            <a
              href="/sentiment"
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 transition-colors ${
                path.includes("/sentiment")
                  ? "bg-[#1d222c] text-amber-400 font-semibold border border-amber-500/20"
                  : "text-slate-300 hover:bg-[#181b22] hover:text-slate-100"
              }`}
            >
              <Radio className="h-3.5 w-3.5 text-purple-400" />
              <span>Retail Sentiment</span>
            </a>
          </nav>

          {/* Quick Search Button */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsSearchOpen(true)}
              className="flex items-center gap-2 rounded-md border border-[#2a303d] bg-[#161920] px-3 py-1.5 text-xs text-slate-400 hover:border-amber-500/40 hover:text-slate-200 transition-all cursor-pointer"
            >
              <Search className="h-3.5 w-3.5 text-amber-400" />
              <span className="hidden sm:inline">Search tickers...</span>
              <kbd className="rounded bg-[#0f1115] px-1.5 py-0.5 font-mono text-[10px] text-slate-400 border border-[#232834]">
                ⌘K
              </kbd>
            </button>
          </div>
        </div>
      </header>

      <SearchModal isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />
    </>
  )
}
