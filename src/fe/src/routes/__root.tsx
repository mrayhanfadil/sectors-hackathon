import { useEffect, useState, useMemo } from "react"
import { createRootRoute, Outlet, Link, useRouterState, useNavigate } from "@tanstack/react-router"
import { Terminal, Moon, Sun, Menu, X, CornerDownLeft } from "lucide-react"

export const Route = createRootRoute({
  component: RootComponent,
})

const QUINTET = ["RATU", "CDIA", "MTEL", "BBCA", "ADRO"] as const
type QuintetTicker = typeof QUINTET[number]

function RootComponent() {
  const routerState = useRouterState()
  const navigate = useNavigate()
  const pathname = routerState.location.pathname
  const searchParams = (routerState.location.search || {}) as Record<string, unknown>

  const [menuOpen, setMenuOpen] = useState(false)
  const [theme, setTheme] = useState<"light" | "dark">("dark")
  const [cmdInput, setCmdInput] = useState("")
  const [currentTime, setCurrentTime] = useState<string>("")

  // Extract active ticker from pathname or search
  const activeTicker: QuintetTicker = useMemo(() => {
    if (pathname.startsWith("/report/")) {
      const parts = pathname.split("/")
      const tk = parts[2]?.toUpperCase() as QuintetTicker
      if (QUINTET.includes(tk)) return tk
    }
    if (typeof searchParams.ticker === "string") {
      const tk = searchParams.ticker.toUpperCase() as QuintetTicker
      if (QUINTET.includes(tk)) return tk
    }
    return "BBCA"
  }, [pathname, searchParams])

  // Live system clock formatted in WIB (UTC+7)
  useEffect(() => {
    const updateTime = () => {
      const now = new Date()
      const timeStr = now.toLocaleTimeString("id-ID", {
        timeZone: "Asia/Jakarta",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
      setCurrentTime(`${timeStr} WIB`)
    }
    updateTime()
    const timer = setInterval(updateTime, 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    try {
      const stored = localStorage.getItem("sektoral-theme")
      const initial = stored === "light" ? "light" : "dark"
      setTheme(initial)
      document.documentElement.classList.toggle("dark", initial === "dark")
    } catch {
      setTheme("dark")
      document.documentElement.classList.add("dark")
    }
  }, [])

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark"
    setTheme(next)
    try {
      localStorage.setItem("sektoral-theme", next)
    } catch {}
    document.documentElement.classList.toggle("dark", next === "dark")
  }

  // Global keyboard shortcuts for Bloomberg Function Keys (F1, F2, F3) and Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is currently typing in an input or textarea
      const target = e.target as HTMLElement
      const isInput =
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable

      if (e.key === "Escape") {
        setMenuOpen(false)
        return
      }

      if (isInput) return

      if (e.key === "F1") {
        e.preventDefault()
        navigate({ to: "/" as any })
      } else if (e.key === "F2") {
        e.preventDefault()
        navigate({ to: "/agent" as any, search: { ticker: activeTicker } as any })
      } else if (e.key === "F3") {
        e.preventDefault()
        navigate({ to: `/report/${activeTicker}/challenge` as any })
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [activeTicker, navigate])

  const handleCommandSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const raw = cmdInput.trim().toUpperCase()
    if (!raw) return

    if (QUINTET.includes(raw as QuintetTicker)) {
      navigate({ to: `/report/${raw}` as any })
      setCmdInput("")
      setMenuOpen(false)
      return
    }

    if (raw === "EQUITY" || raw === "SAHAM" || raw === "HUB" || raw === "HOME" || raw === "MONITOR" || raw === "F1") {
      navigate({ to: "/" as any })
      setCmdInput("")
      setMenuOpen(false)
      return
    }

    if (raw === "AGENT" || raw === "MESIN" || raw === "TRACE" || raw === "F2") {
      navigate({ to: "/agent" as any, search: { ticker: activeTicker } as any })
      setCmdInput("")
      setMenuOpen(false)
      return
    }

    if (raw === "DEBATE" || raw === "UJI" || raw === "CHALLENGE" || raw === "F3") {
      navigate({ to: `/report/${activeTicker}/challenge` as any })
      setCmdInput("")
      setMenuOpen(false)
      return
    }

    if (raw === "SENTIMENT" || raw === "SENTIMEN" || raw === "SENT" || raw === "NEWS" || raw === "BERITA") {
      navigate({ to: `/report/${activeTicker}/sentiment` as any })
      setCmdInput("")
      setMenuOpen(false)
      return
    }

    // Partial match in quintet
    const match = QUINTET.find((t) => t.startsWith(raw))
    if (match) {
      navigate({ to: `/report/${match}` as any })
      setCmdInput("")
      setMenuOpen(false)
    }
  }

  const isHomeActive = pathname === "/"
  const isAgentActive = pathname.startsWith("/agent")
  const isDebateActive = pathname.includes("/challenge")
  const isEquityReportActive = pathname.startsWith("/report") && !isDebateActive

  const closeMenu = () => setMenuOpen(false)

  return (
    <div className="min-h-screen bg-[#f8f9fa] text-[#0f172a] dark:bg-[#090a0c] dark:text-[#f1f5f9] font-sans antialiased">
      {/* 1. Bloomberg Terminal Top Command Bar */}
      <header className="sticky top-0 z-40 border-b border-neutral-300 bg-neutral-900 text-neutral-100 shadow-md dark:border-[#262930] dark:bg-[#0c0d10]">
        {/* Main Command Console Strip */}
        <div className="mx-auto flex max-w-7xl h-11 items-center justify-between px-3 sm:px-4 font-mono text-xs">
          {/* Left: Terminal Logo & System Status */}
          <div className="flex items-center gap-3">
            <Link
              to="/"
              className="flex items-center gap-2 font-bold tracking-wider text-amber-400 hover:text-amber-300 transition-colors"
              onClick={closeMenu}
            >
              <Terminal className="h-4 w-4 text-amber-400" />
              <span className="tracking-tight font-terminal text-sm">
                SEKTORAL<span className="text-neutral-400"> // DECK</span>
              </span>
            </Link>

            <div className="hidden items-center gap-1.5 rounded border border-neutral-800 bg-[#121418] px-2 py-0.5 text-[10px] text-amber-300 lg:flex" title="Snapshot-based data feed — no streaming prices">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
              <span className="font-semibold tracking-wide">DATA TERAKHIR</span>
            </div>
          </div>

          {/* Center: Function-Key Navigation (EQUITY | AGENT | DEBATE) */}
          <nav className="hidden md:flex items-center gap-1">
            <Link
              to="/"
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-bold tracking-wide transition-all ${
                isHomeActive || isEquityReportActive
                  ? "bg-amber-400/20 text-amber-300 border border-amber-400/40"
                  : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/60 border border-transparent"
              }`}
            >
              <span className="text-amber-400 font-extrabold">[F1]</span>
              <span>SAHAM</span>
            </Link>

            <Link
              to="/agent"
              search={{ ticker: activeTicker } as any}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-bold tracking-wide transition-all ${
                isAgentActive
                  ? "bg-sky-400/20 text-sky-300 border border-sky-400/40"
                  : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/60 border border-transparent"
              }`}
            >
              <span className="text-sky-400 font-extrabold">[F2]</span>
              <span>MESIN</span>
            </Link>

            <Link
              to={`/report/${activeTicker}/challenge` as any}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-bold tracking-wide transition-all ${
                isDebateActive
                  ? "bg-rose-400/20 text-rose-300 border border-rose-400/40"
                  : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/60 border border-transparent"
              }`}
            >
              <span className="text-rose-400 font-extrabold">[F3]</span>
              <span>UJI SILANG</span>
            </Link>
          </nav>

          {/* Center-Right: Ticker Quick-Jump for Quintet Only */}
          <div className="hidden sm:flex items-center gap-2">
            <div className="flex items-center gap-1 bg-[#14171d] px-1.5 py-0.5 rounded border border-neutral-800">
              <span className="text-[10px] text-neutral-500 font-semibold uppercase pr-1">KE:</span>
              {QUINTET.map((tk) => {
                const isActive =
                  pathname.startsWith(`/report/${tk}`) || (isAgentActive && searchParams.ticker === tk)
                return (
                  <Link
                    key={tk}
                    to={`/report/${tk}` as any}
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold font-terminal transition-colors ${
                      isActive
                        ? "bg-amber-400 text-neutral-950 shadow-xs font-bold"
                        : "text-neutral-400 hover:bg-neutral-800 hover:text-neutral-100"
                    }`}
                  >
                    {tk}
                  </Link>
                )
              })}
            </div>

            {/* Direct Command Input */}
            <form onSubmit={handleCommandSubmit} className="relative flex items-center">
              <input
                type="text"
                value={cmdInput}
                onChange={(e) => setCmdInput(e.target.value)}
                placeholder="CMD >"
                aria-label="Terminal Command Quick-Jump"
                className="h-6 w-20 sm:w-24 rounded border border-neutral-700 bg-black/60 px-1.5 text-[11px] font-mono font-bold uppercase text-amber-300 placeholder:text-neutral-600 focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400 transition-all"
                maxLength={8}
              />
              <button
                type="submit"
                aria-label="Submit Command"
                className="absolute right-1 text-neutral-500 hover:text-amber-400"
              >
                <CornerDownLeft className="h-2.5 w-2.5" />
              </button>
            </form>
          </div>

          {/* Right: Clock & Theme Toggle & Mobile Menu */}
          <div className="flex items-center gap-2">
            {currentTime && (
              <span className="hidden xl:inline-block text-[10px] font-mono font-medium text-neutral-400 bg-neutral-800/50 px-2 py-0.5 rounded border border-neutral-800">
                {currentTime}
              </span>
            )}

            <button
              type="button"
              onClick={toggleTheme}
              className="rounded border border-neutral-800 bg-[#121418] p-1 text-neutral-400 hover:text-neutral-100 transition-colors"
              aria-label={theme === "dark" ? "Mode Terang" : "Mode Gelap"}
              title={theme === "dark" ? "Ganti ke mode terang" : "Ganti ke mode gelap"}
            >
              {theme === "dark" ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5 text-amber-400" />}
            </button>

            {/* Mobile Hamburger */}
            <button
              type="button"
              className="rounded border border-neutral-800 bg-[#121418] p-1 text-neutral-400 hover:text-neutral-100 sm:hidden"
              onClick={() => setMenuOpen((v) => !v)}
              aria-label={menuOpen ? "Tutup Command Deck" : "Buka Command Deck"}
            >
              {menuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            </button>
          </div>
        </div>

        {/* Mobile Dropdown Console Menu */}
        {menuOpen && (
          <div className="border-t border-neutral-800 bg-[#0c0d10] px-3 py-3 sm:hidden font-mono space-y-3">
            {/* Function Keys Mobile */}
            <div className="grid grid-cols-3 gap-1.5">
              <Link
                to="/"
                onClick={closeMenu}
                className={`text-center py-1.5 rounded text-xs font-bold border ${
                  isHomeActive || isEquityReportActive
                    ? "bg-amber-400/20 text-amber-300 border-amber-400/40"
                    : "bg-neutral-900 text-neutral-400 border-neutral-800"
                }`}
              >
                [F1] SAHAM
              </Link>
              <Link
                to="/agent"
                search={{ ticker: activeTicker } as any}
                onClick={closeMenu}
                className={`text-center py-1.5 rounded text-xs font-bold border ${
                  isAgentActive
                    ? "bg-sky-400/20 text-sky-300 border-sky-400/40"
                    : "bg-neutral-900 text-neutral-400 border-neutral-800"
                }`}
              >
                [F2] AGENT
              </Link>
              <Link
                to={`/report/${activeTicker}/challenge` as any}
                onClick={closeMenu}
                className={`text-center py-1.5 rounded text-xs font-bold border ${
                  isDebateActive
                    ? "bg-rose-400/20 text-rose-300 border-rose-400/40"
                    : "bg-neutral-900 text-neutral-400 border-neutral-800"
                }`}
              >
                [F3] UJI
              </Link>
            </div>

            {/* Mobile Ticker Quick-Jump */}
            <div className="space-y-1">
              <div className="text-[10px] font-bold uppercase text-neutral-500">PINTASAN EMITEN:</div>
              <div className="grid grid-cols-5 gap-1">
                {QUINTET.map((tk) => (
                  <Link
                    key={tk}
                    to={`/report/${tk}` as any}
                    onClick={closeMenu}
                    className="py-1 text-center rounded bg-neutral-900 border border-neutral-800 text-xs font-bold text-neutral-300 hover:text-amber-400 hover:border-amber-400"
                  >
                    {tk}
                  </Link>
                ))}
              </div>
            </div>

            {/* Mobile Command Input */}
            <form onSubmit={handleCommandSubmit} className="flex gap-1.5 pt-1">
              <input
                type="text"
                value={cmdInput}
                onChange={(e) => setCmdInput(e.target.value)}
                placeholder="CMD > RATU | CDIA | MTEL | BBCA | ADRO"
                className="flex-1 h-8 rounded border border-neutral-700 bg-black px-2 text-xs font-mono font-bold uppercase text-amber-300 placeholder:text-neutral-600 focus:border-amber-400 focus:outline-none"
              />
              <button
                type="submit"
                className="h-8 px-3 rounded bg-amber-500 font-bold text-black text-xs font-mono"
              >
                GO
              </button>
            </form>
          </div>
        )}
      </header>

      {/* 2. Main Terminal Content Canvas */}
      <main className="mx-auto max-w-7xl px-3 py-4 sm:px-6 sm:py-6">
        <Outlet />
      </main>

      {/* 3. Terminal Footer with Provenance & Compliance Attestation */}
      <footer className="border-t border-neutral-300 bg-neutral-100 py-6 font-mono text-xs text-neutral-600 dark:border-[#262930] dark:bg-[#0c0d10] dark:text-neutral-400">
        <div className="mx-auto max-w-7xl space-y-3 px-4 sm:px-6">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-neutral-200 pb-3 dark:border-[#1e2229]">
            <div className="flex items-center gap-2">
              <Terminal className="h-3.5 w-3.5 text-amber-500" />
              <span className="font-bold text-neutral-900 dark:text-neutral-100">
                SEKTORAL.ID COMMAND DECK // TERMINAL SYSTEM v2.6
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-[11px]">
              <span className="text-emerald-600 dark:text-emerald-400 font-semibold">
                ● JALUR DATA AKTIF: /api/report · /api/dcf · /api/news · /api/sentiment
              </span>
              <span className="text-neutral-400">|</span>
              <span className="text-neutral-500">KEYLESS 503: /api/outlook · /api/tickers (OFFLINE)</span>
            </div>
          </div>

          <div className="flex flex-col gap-1 text-[11px] leading-relaxed text-neutral-500 dark:text-neutral-400">
            <p>
              <span className="font-semibold text-neutral-700 dark:text-neutral-300">
                DISCLAIMER RISET:{" "}
              </span>
              Platform ini menyajikan riset kuantitatif deterministik dan multi-agent reasoning untuk analisis kompetisi
              Sectors Hackathon. Kalkulasi Fair Value dan WACC memakai snapshot asumsi terverifikasi dari data historis
              IDX (Sectors API pending — bukan data live maupun rekomendasi resmi).
            </p>
            <p>
              Bukan rekomendasi transaksi efek maupun nasihat investasi finansial resmi. Keputusan alokasi modal
              sepenuhnya berada di tangan investor.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

