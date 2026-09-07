import { useEffect, useState } from "react"
import { createRootRoute, Outlet, Link, useRouterState } from "@tanstack/react-router"
import { Menu, Moon, Sun, X } from "lucide-react"

export const Route = createRootRoute({
  component: RootComponent,
})

function RootComponent() {
  const routerState = useRouterState()
  const pathname = routerState.location.pathname
  const [menuOpen, setMenuOpen] = useState(false)
  const [theme, setTheme] = useState<"light" | "dark">("light")

  useEffect(() => {
    try {
      const stored = localStorage.getItem("sektoral-theme")
      const initial = stored === "dark" ? "dark" : "light"
      setTheme(initial)
      document.documentElement.classList.toggle("dark", initial === "dark")
    } catch {}
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
  const isReportActive = pathname.startsWith("/report")
  const isAgentActive = pathname.startsWith("/agent")

  const getNavClass = (isActive: boolean) =>
    `px-1 py-1 text-[13px] transition-colors ${
      isActive
        ? "font-medium text-black dark:text-white"
        : "text-[#666] hover:text-black dark:text-[#a1a1a1] dark:hover:text-white"
    }`

  const maxWidthClass = "max-w-5xl"

  const closeMenu = () => setMenuOpen(false)

  return (
    <div className="min-h-screen bg-white text-[#0a0a0a] dark:bg-[#0a0a0a] dark:text-[#ededed]">
      <header className="sticky top-0 z-10 border-b border-[#eaeaea] bg-white dark:border-[#262626] dark:bg-[#0a0a0a]">
        <div className={`mx-auto flex ${maxWidthClass} h-12 items-center justify-between px-4 sm:px-6`}>
          <Link
            to="/"
            className="text-[14px] font-bold tracking-tight text-black dark:text-white"
            onClick={closeMenu}
          >
            Sektoral<span className="font-normal text-[#666] dark:text-[#a1a1a1]">.id</span>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden items-center gap-5 sm:flex">
            <Link to="/" className={getNavClass(isHomeActive)}>
              Beranda
            </Link>
            <a href="/#saham" className={getNavClass(isReportActive)}>
              Laporan
            </a>
            <Link to="/agent" className={getNavClass(isAgentActive)}>
              Live Analisis
            </Link>
            <button
              type="button"
              onClick={toggleTheme}
              className="rounded p-1.5 text-[#666] hover:text-black dark:text-[#a1a1a1] dark:hover:text-white"
              aria-label={theme === "dark" ? "Ganti ke mode terang" : "Ganti ke mode gelap"}
              title={theme === "dark" ? "Mode terang" : "Mode gelap"}
            >
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
          </nav>

          {/* Mobile toggles */}
          <div className="flex items-center gap-1 sm:hidden">
            <button
              type="button"
              onClick={toggleTheme}
              className="rounded p-1.5 text-[#666] hover:text-black dark:text-[#a1a1a1] dark:hover:text-white"
              aria-label={theme === "dark" ? "Ganti ke mode terang" : "Ganti ke mode gelap"}
            >
              {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </button>
            <button
              type="button"
              className="rounded p-1.5 text-[#666] hover:text-black dark:text-[#a1a1a1] dark:hover:text-white sm:hidden"
              onClick={() => setMenuOpen((v) => !v)}
              aria-label={menuOpen ? "Tutup menu" : "Buka menu"}
            >
              {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {/* Mobile nav */}
        {menuOpen && (
          <nav className="border-t border-[#eaeaea] bg-white px-4 py-2 sm:hidden dark:border-[#262626] dark:bg-[#0a0a0a]">
            <div className="flex flex-col">
              <Link to="/" className={getNavClass(isHomeActive)} onClick={closeMenu}>
                Beranda
              </Link>
              <a href="/#saham" className={getNavClass(isReportActive)} onClick={closeMenu}>
                Laporan
              </a>
              <Link to="/agent" className={getNavClass(isAgentActive)} onClick={closeMenu}>
                Live Analisis
              </Link>
            </div>
          </nav>
        )}
      </header>

      <main className={`mx-auto ${maxWidthClass} px-4 py-6 sm:px-6`}>
        <Outlet />
      </main>

      <footer className="border-t border-[#eaeaea] bg-white py-6 dark:border-[#262626] dark:bg-[#0a0a0a]">
        <div className="mx-auto max-w-5xl space-y-1 px-4 text-center text-[12px] text-[#666] sm:px-6 dark:text-[#a1a1a1]">
          <p className="font-medium text-black dark:text-white">
            Sektoral.id — riset saham Indonesia dalam bahasa sederhana. Bukan saran investasi.
          </p>
          <p>
            Semua keputusan investasi sepenuhnya tanggung jawab pengguna. Pelajari dulu, baru putuskan.
          </p>
        </div>
      </footer>
    </div>
  )
}
