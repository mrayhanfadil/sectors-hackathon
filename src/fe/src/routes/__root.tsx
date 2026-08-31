import { createRootRoute, Outlet } from "@tanstack/react-router"
import { Link as _Link } from "@tanstack/react-router"
const Link: any = _Link

export const Route = createRootRoute({
  component: () => (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-10 border-b bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link to="/" className="font-semibold tracking-tight">Sektoral<span className="text-slate-500">.id</span> <span className="ml-2 rounded bg-slate-900 px-1.5 py-0.5 text-xs font-medium text-white">Institutional Report</span></Link>
          <nav className="flex items-center gap-1 text-sm">
            <a href="/" className="rounded-md px-3 py-1.5 hover:bg-slate-100">Home</a>
            <a href="/outlook" className="rounded-md px-3 py-1.5 hover:bg-slate-100">Outlook</a>
            <a href="/report/RATU" className="rounded-md px-3 py-1.5 hover:bg-slate-100">Report</a>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>
      <footer className="border-t bg-white py-4 text-center text-xs text-slate-500">CSR - Vite + TanStack Query/Router -&gt; Cloudflare Pages - P0-P1 IDX+yfinance (0 credit)</footer>
    </div>
  ),
})
