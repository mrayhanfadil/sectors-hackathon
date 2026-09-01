import { createRootRoute, Outlet, Link, useRouterState } from "@tanstack/react-router"

export const Route = createRootRoute({
  component: RootComponent,
})

function RootComponent() {
  const routerState = useRouterState()
  const pathname = routerState.location.pathname

  const isHomeActive = pathname === "/"
  const isMockActive = pathname.startsWith("/mock-sectors")
  const isAgentActive = pathname.startsWith("/agent")

  const getNavClass = (isActive: boolean) =>
    `rounded-md px-3 py-1.5 text-xs sm:text-sm font-medium transition-colors ${
      isActive
        ? "bg-slate-900 text-white"
        : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
    }`

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-10 border-b border-slate-200/80 bg-white/85 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link to="/" className="font-semibold tracking-tight text-slate-900">
            Sektoral<span className="text-slate-500">.id</span>{" "}
            <span className="ml-2 rounded bg-slate-900 px-1.5 py-0.5 text-xs font-medium text-white">
              Institutional Report
            </span>
          </Link>
          <nav className="flex items-center gap-1">
            <Link to="/" className={getNavClass(isHomeActive)}>
              Home
            </Link>
            <Link to="/mock-sectors/$ticker" params={{ ticker: "BBCA" }} className={getNavClass(isMockActive)}>
              Mock Data
            </Link>
            <Link to="/agent" className={getNavClass(isAgentActive)}>
              ADK Live
            </Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>
      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
        ADK live trace (Muse Spark 1M via CommandCode bridge) - BE FastAPI :8777 - Mock Sectors v2 endpoints (corporate-actions, quarterly-financials, news, filings) - FE CSR Vite + TanStack Query/Router - Pages *.pages.dev - Bukan saran investasi
      </footer>
    </div>
  )
}
