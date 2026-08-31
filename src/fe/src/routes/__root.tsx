import { createRootRoute, Outlet } from "@tanstack/react-router"
import { Navbar } from "@/components/layout/Navbar"
import { TickerTape } from "@/components/common/TickerTape"
import { Footer } from "@/components/layout/Footer"

export const Route = createRootRoute({
  component: () => (
    <div className="min-h-screen flex flex-col bg-[#0d0f12] text-slate-100 font-sans antialiased selection:bg-amber-500/30 selection:text-amber-200">
      <Navbar />
      <TickerTape />
      <main className="flex-1 mx-auto w-full max-w-7xl px-4 py-6">
        <Outlet />
      </main>
      <Footer />
    </div>
  ),
})
