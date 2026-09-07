import { useState } from "react"
import { createRootRoute, Outlet, Link, useRouterState } from "@tanstack/react-router"
import { Menu, X, CandlestickChart } from "lucide-react"

export const Route = createRootRoute({
  component: RootComponent,
})

function RootComponent() {
  const routerState = useRouterState()
  const pathname = routerState.location.pathname
  const [menuOpen, setMenuOpen] = useState(false)

  const isHomeActive = pathname === "/"
  const isReportActive = pathname.startsWith("/report")
  const isAgentActive = pathname.startsWith("/agent")

  const getNavClass = (isActive: boolean) =>
    `rounded-md px-3 py-1.5 text-xs sm:text-sm font-medium transition-colors ${
      isActive
        ? "bg-slate-900 text-white"
        : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
    }`

  const maxWidthClass = isAgentActive ? "max-w-[1440px]" : "max-w-6xl"

  const closeMenu = () => setMenuOpen(false)

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-10 border-b border-slate-200/80 bg-white/85 backdrop-blur">
        <div className={`mx-auto flex ${maxWidthClass} items-center justify-between px-4 py-3`}>
          <Link to="/" className="flex items-center gap-2 font-semibold tracking-tight text-slate-900" onClick={closeMenu}>
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-slate-900 text-white">
              <CandlestickChart className="h-4 w-4" />
            </span>
            Sektoral<span className="-ml-2 text-slate-500">.id</span>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden items-center gap-1 sm:flex">
            <Link to="/" className={getNavClass(isHomeActive)}>
              Beranda
            </Link>
            <a
              href="/#saham"
              className={getNavClass(isReportActive)}
            >
              Laporan
            </a>
            <Link to="/agent" className={getNavClass(isAgentActive)}>
              Live Analisis
            </Link>
          </nav>

          {/* Mobile toggle */}
          <button
            type="button"
            className="rounded-md p-2 text-slate-600 hover:bg-slate-100 sm:hidden"
            onClick={() => setMenuOpen((v) => !v)}
            aria-label={menuOpen ? "Tutup menu" : "Buka menu"}
          >
            {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {/* Mobile nav */}
        {menuOpen && (
          <nav className="border-t border-slate-200 bg-white px-4 py-2 sm:hidden">
            <div className="flex flex-col gap-1">
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

      <main className={`mx-auto ${maxWidthClass} px-4 py-6`}>
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 bg-white py-5">
        <div className="mx-auto max-w-6xl space-y-1.5 px-4 text-center text-xs text-slate-500">
          <p className="font-medium text-slate-700">
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
