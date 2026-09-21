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
  const isEquityReportActive = pathname.startsWith("/report")
  const isLaporanActive = isHomeActive || isEquityReportActive

  const closeMenu = () => setMenuOpen(false)

  return (
    <div className="min-h-screen bg-[#f1f5f9] text-[#333333] dark:bg-[#1e2229] dark:text-[#f1f5f9] font-sans antialiased">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-[#D9D9D9] bg-[#f1f5f9]/95 backdrop-blur-sm dark:border-[#262930] dark:bg-[#1e2229]/95">
        <div className="mx-auto flex max-w-[1360px] h-14 items-center justify-between px-4 sm:px-6">
          {/* Left: Brand & Desktop Nav */}
          <div className="flex items-center gap-8">
            <Link
              to="/"
              className="flex items-center"
              onClick={closeMenu}
              aria-label="Sectoral - beranda"
            >
              <img src="/sectoral-logo.svg" alt="Sectoral" className="h-6 w-auto dark:hidden" />
              <img src="/sectoral-logo-dark.svg" alt="Sectoral" className="hidden h-6 w-auto dark:block" />
            </Link>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-6 text-sm">
              <Link
                to="/"
                className={`transition-colors ${
                  isLaporanActive
                    ? "text-[#0928B1] dark:text-[#7596FF] font-semibold"
                    : "text-[#666666] hover:text-[#333333] dark:text-[#666666] dark:hover:text-[#f1f5f9]"
                }`}
              >
                Laporan
              </Link>

              <Link
                to="/agent"
                className={`transition-colors ${
                  isAgentActive
                    ? "text-[#0928B1] dark:text-[#7596FF] font-semibold"
                    : "text-[#666666] hover:text-[#333333] dark:text-[#666666] dark:hover:text-[#f1f5f9]"
                }`}
              >
                Mesin
              </Link>
            </nav>
          </div>

          {/* Right Controls */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={toggleTheme}
              className="rounded-lg border border-[#D9D9D9] bg-white p-2 text-[#666666] hover:text-[#333333] hover:bg-[#F3EFE6] dark:border-[#262930] dark:bg-[#090a0c] dark:text-[#666666] dark:hover:text-[#f1f5f9] dark:hover:bg-[#23211B] transition-colors cursor-pointer"
              aria-label={theme === "dark" ? "Ganti ke mode terang" : "Ganti ke mode gelap"}
              title={theme === "dark" ? "Ganti ke mode terang" : "Ganti ke mode gelap"}
            >
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>

            {/* Mobile Hamburger */}
            <button
              type="button"
              className="rounded-lg border border-[#D9D9D9] bg-white p-2 text-[#666666] hover:text-[#333333] hover:bg-[#F3EFE6] dark:border-[#262930] dark:bg-[#090a0c] dark:text-[#666666] dark:hover:text-[#f1f5f9] dark:hover:bg-[#23211B] md:hidden transition-colors cursor-pointer"
              onClick={() => setMenuOpen((v) => !v)}
              aria-label={menuOpen ? "Tutup menu" : "Buka menu"}
            >
              {menuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            </button>
          </div>
        </div>

        {/* Mobile Dropdown Menu */}
        {menuOpen && (
          <div className="border-t border-[#D9D9D9] bg-[#f1f5f9] px-4 py-4 md:hidden dark:border-[#262930] dark:bg-[#1e2229] space-y-2">
            <Link
              to="/"
              onClick={closeMenu}
              className={`block px-3 py-2 rounded-lg text-sm transition-colors ${
                isLaporanActive
                  ? "bg-[#D9D9D9]/40 text-[#0928B1] font-semibold dark:bg-[#262930]/60 dark:text-[#7596FF]"
                  : "text-[#666666] hover:text-[#333333] hover:bg-[#D9D9D9]/20 dark:text-[#666666] dark:hover:text-[#f1f5f9] dark:hover:bg-[#262930]/30"
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
                  ? "bg-[#D9D9D9]/40 text-[#0928B1] font-semibold dark:bg-[#262930]/60 dark:text-[#7596FF]"
                  : "text-[#666666] hover:text-[#333333] hover:bg-[#D9D9D9]/20 dark:text-[#666666] dark:hover:text-[#f1f5f9] dark:hover:bg-[#262930]/30"
              }`}
            >
              Mesin
            </Link>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-[1360px] px-4 py-8 sm:px-6">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-[#D9D9D9] bg-[#f1f5f9] py-4 text-xs text-[#666666] dark:border-[#262930] dark:bg-[#1e2229] dark:text-[#666666]">
        <div className="mx-auto max-w-[1360px] px-4 sm:px-6 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center">
            <img src="/sectoral-logo.svg" alt="Sectoral" className="h-5 w-auto dark:hidden" />
            <img src="/sectoral-logo-dark.svg" alt="Sectoral" className="hidden h-5 w-auto dark:block" />
          </div>
          <div className="text-xs text-[#666666] dark:text-[#666666]">
            © {new Date().getFullYear()} Sektoral · Riset fundamental &amp; analisis multi-agen saham Indonesia
          </div>
        </div>
      </footer>
    </div>
  )
}
