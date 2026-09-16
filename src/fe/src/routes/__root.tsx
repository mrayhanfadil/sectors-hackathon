import { useEffect, useState, useMemo } from "react"
import { createRootRoute, Outlet, Link, useRouterState } from "@tanstack/react-router"
import { Moon, Sun, Menu, X } from "lucide-react"

export const Route = createRootRoute({
  component: RootComponent,
})

function RootComponent() {
  const routerState = useRouterState()
  const pathname = routerState.location.pathname
  const searchParams = (routerState.location.search || {}) as Record<string, unknown>

  const [menuOpen, setMenuOpen] = useState(false)
  const [theme, setTheme] = useState<"light" | "dark">("light")

  // Extract active ticker from pathname or search
  const activeTicker = useMemo(() => {
    if (pathname.startsWith("/report/")) {
      const parts = pathname.split("/")
      const tk = parts[2]?.toUpperCase()
      if (tk) return tk
    }
    if (typeof searchParams.ticker === "string" && searchParams.ticker) {
      return searchParams.ticker.toUpperCase()
    }
    return "BBCA"
  }, [pathname, searchParams])

  useEffect(() => {
    try {
      const stored = localStorage.getItem("sektoral-theme")
      const initial = stored === "dark" ? "dark" : "light"
      setTheme(initial)
      document.documentElement.classList.toggle("dark", initial === "dark")
    } catch {
      setTheme("light")
      document.documentElement.classList.remove("dark")
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

  const isHomeActive = pathname === "/"
  const isAgentActive = pathname.startsWith("/agent")
  const isDebateActive = pathname.includes("/challenge")
  const isEquityReportActive = pathname.startsWith("/report") && !isDebateActive
  const isLaporanActive = isHomeActive || isEquityReportActive

  const closeMenu = () => setMenuOpen(false)

  return (
    <div className="min-h-screen bg-[#FBFAF7] text-[#1C1B17] dark:bg-[#14130F] dark:text-[#EDEAE3] font-sans antialiased">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-[#E7E3DA] bg-[#FBFAF7]/95 backdrop-blur-sm dark:border-[#2A2822] dark:bg-[#14130F]/95">
        <div className="mx-auto flex max-w-[1100px] h-14 items-center justify-between px-4 sm:px-6">
          {/* Left: Brand & Desktop Nav */}
          <div className="flex items-center gap-8">
            <Link
              to="/"
              className="text-xl font-normal tracking-tight text-[#1C1B17] dark:text-[#EDEAE3] font-['Newsreader',serif]"
              onClick={closeMenu}
            >
              Sektoral.id
            </Link>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-6 text-sm">
              <Link
                to="/"
                className={`transition-colors ${
                  isLaporanActive
                    ? "text-[#0E6E63] dark:text-[#4FD1B5] font-semibold"
                    : "text-[#6B6659] hover:text-[#1C1B17] dark:text-[#A8A296] dark:hover:text-[#EDEAE3]"
                }`}
              >
                Laporan
              </Link>

              <Link
                to="/agent"
                className={`transition-colors ${
                  isAgentActive
                    ? "text-[#0E6E63] dark:text-[#4FD1B5] font-semibold"
                    : "text-[#6B6659] hover:text-[#1C1B17] dark:text-[#A8A296] dark:hover:text-[#EDEAE3]"
                }`}
              >
                Mesin
              </Link>

              <Link
                to={`/report/${activeTicker}/challenge` as any}
                className={`transition-colors ${
                  isDebateActive
                    ? "text-[#0E6E63] dark:text-[#4FD1B5] font-semibold"
                    : "text-[#6B6659] hover:text-[#1C1B17] dark:text-[#A8A296] dark:hover:text-[#EDEAE3]"
                }`}
              >
                Uji silang
              </Link>
            </nav>
          </div>

          {/* Right Controls */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={toggleTheme}
              className="rounded-lg border border-[#E7E3DA] bg-white p-2 text-[#6B6659] hover:text-[#1C1B17] hover:bg-[#F3EFE6] dark:border-[#2A2822] dark:bg-[#1B1A16] dark:text-[#A8A296] dark:hover:text-[#EDEAE3] dark:hover:bg-[#23211B] transition-colors cursor-pointer"
              aria-label={theme === "dark" ? "Ganti ke mode terang" : "Ganti ke mode gelap"}
              title={theme === "dark" ? "Ganti ke mode terang" : "Ganti ke mode gelap"}
            >
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>

            {/* Mobile Hamburger */}
            <button
              type="button"
              className="rounded-lg border border-[#E7E3DA] bg-white p-2 text-[#6B6659] hover:text-[#1C1B17] hover:bg-[#F3EFE6] dark:border-[#2A2822] dark:bg-[#1B1A16] dark:text-[#A8A296] dark:hover:text-[#EDEAE3] dark:hover:bg-[#23211B] md:hidden transition-colors cursor-pointer"
              onClick={() => setMenuOpen((v) => !v)}
              aria-label={menuOpen ? "Tutup menu" : "Buka menu"}
            >
              {menuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            </button>
          </div>
        </div>

        {/* Mobile Dropdown Menu */}
        {menuOpen && (
          <div className="border-t border-[#E7E3DA] bg-[#FBFAF7] px-4 py-4 md:hidden dark:border-[#2A2822] dark:bg-[#14130F] space-y-2">
            <Link
              to="/"
              onClick={closeMenu}
              className={`block px-3 py-2 rounded-lg text-sm transition-colors ${
                isLaporanActive
                  ? "bg-[#E7E3DA]/40 text-[#0E6E63] font-semibold dark:bg-[#2A2822]/60 dark:text-[#4FD1B5]"
                  : "text-[#6B6659] hover:text-[#1C1B17] hover:bg-[#E7E3DA]/20 dark:text-[#A8A296] dark:hover:text-[#EDEAE3] dark:hover:bg-[#2A2822]/30"
              }`}
            >
              Laporan
            </Link>
            <Link
              to="/agent"
              search={{ ticker: activeTicker } as any}
              onClick={closeMenu}
              className={`block px-3 py-2 rounded-lg text-sm transition-colors ${
                isAgentActive
                  ? "bg-[#E7E3DA]/40 text-[#0E6E63] font-semibold dark:bg-[#2A2822]/60 dark:text-[#4FD1B5]"
                  : "text-[#6B6659] hover:text-[#1C1B17] hover:bg-[#E7E3DA]/20 dark:text-[#A8A296] dark:hover:text-[#EDEAE3] dark:hover:bg-[#2A2822]/30"
              }`}
            >
              Mesin
            </Link>
            <Link
              to={`/report/${activeTicker}/challenge` as any}
              onClick={closeMenu}
              className={`block px-3 py-2 rounded-lg text-sm transition-colors ${
                isDebateActive
                  ? "bg-[#E7E3DA]/40 text-[#0E6E63] font-semibold dark:bg-[#2A2822]/60 dark:text-[#4FD1B5]"
                  : "text-[#6B6659] hover:text-[#1C1B17] hover:bg-[#E7E3DA]/20 dark:text-[#A8A296] dark:hover:text-[#EDEAE3] dark:hover:bg-[#2A2822]/30"
              }`}
            >
              Uji silang
            </Link>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-[1100px] px-4 py-8 sm:px-6">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-[#E7E3DA] bg-[#FBFAF7] py-8 text-xs text-[#6B6659] dark:border-[#2A2822] dark:bg-[#14130F] dark:text-[#A8A296]">
        <div className="mx-auto max-w-[1100px] space-y-4 px-4 sm:px-6">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-[#E7E3DA] pb-4 dark:border-[#2A2822]">
            <div className="font-['Newsreader',serif] text-base text-[#1C1B17] dark:text-[#EDEAE3]">
              Sektoral.id
            </div>
            <div className="text-xs text-[#6B6659] dark:text-[#A8A296]">
              Riset fundamental &amp; analisis multi-agen saham Indonesia
            </div>
          </div>

          <div className="space-y-2 text-xs leading-relaxed text-[#6B6659] dark:text-[#A8A296]">
            <p>
              Platform ini menyajikan riset kuantitatif deterministik dan penalaran multi-agen untuk analisis emiten. Kalkulasi nilai wajar dan WACC menggunakan data laporan keuangan terverifikasi dari data historis IDX.
            </p>
            <p>
              Bukan rekomendasi transaksi efek maupun nasihat investasi finansial berlisensi. Keputusan alokasi modal dan risiko investasi sepenuhnya berada di tangan investor.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
