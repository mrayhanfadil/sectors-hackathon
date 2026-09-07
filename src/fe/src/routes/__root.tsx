import { useState } from "react"
import { createRootRoute, Outlet, Link, useRouterState } from "@tanstack/react-router"
import { Menu, X } from "lucide-react"

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
    `px-1 py-1 text-[13px] transition-colors ${
      isActive ? "font-medium text-black" : "text-[#666] hover:text-black"
    }`

  const maxWidthClass = isAgentActive ? "max-w-[1440px]" : "max-w-5xl"

  const closeMenu = () => setMenuOpen(false)

  return (
    <div className="min-h-screen bg-white text-[#0a0a0a]">
      <header className="sticky top-0 z-10 border-b border-[#eaeaea] bg-white">
        <div className={`mx-auto flex ${maxWidthClass} h-12 items-center justify-between px-4 sm:px-6`}>
          <Link
            to="/"
            className="text-[14px] font-bold tracking-tight text-black"
            onClick={closeMenu}
          >
            Sektoral<span className="font-normal text-[#666]">.id</span>
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
          </nav>

          {/* Mobile toggle */}
          <button
            type="button"
            className="rounded p-1.5 text-[#666] hover:text-black sm:hidden"
            onClick={() => setMenuOpen((v) => !v)}
            aria-label={menuOpen ? "Tutup menu" : "Buka menu"}
          >
            {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {/* Mobile nav */}
        {menuOpen && (
          <nav className="border-t border-[#eaeaea] bg-white px-4 py-2 sm:hidden">
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

      <footer className="border-t border-[#eaeaea] bg-white py-6">
        <div className="mx-auto max-w-5xl space-y-1 px-4 text-center text-[12px] text-[#666] sm:px-6">
          <p className="font-medium text-black">
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
