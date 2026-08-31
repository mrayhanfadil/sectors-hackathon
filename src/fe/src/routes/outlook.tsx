import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { fetchOutlook } from "@/lib/api"

export const Route = (createFileRoute as any)("/outlook")({ component: Outlook })

function Outlook() {
  const { data, isLoading } = useQuery({ queryKey: ["outlook"], queryFn: fetchOutlook })
  if (isLoading) return <div className="text-sm text-slate-500">Loading outlook...</div>
  if (!data) return <div className="text-sm text-red-600">Failed to load.</div>
  const d = data as { jci: { base: number; bull: number; bear: number; pe: number; epsGrowth: string }; sectors: { name: string; call: string }[] }
  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Market Outlook - JCI 9100 base</h1>
      <div className="grid gap-4 sm:grid-cols-3">
        <Card><CardHeader><CardTitle className="text-sm">Bear 7,800</CardTitle></CardHeader><CardContent className="text-xs text-slate-600">Downside - EPS x Multiple stress.</CardContent></Card>
        <Card className="border-slate-900"><CardHeader><CardTitle className="text-sm">Base 9,100 - 15x - 8% EPS</CardTitle></CardHeader><CardContent className="text-xs text-slate-600">JPM 2026 Outlook base. Priced assumption.</CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">Bull 10,000</CardTitle></CardHeader><CardContent className="text-xs text-slate-600">Upside - Danantara Value-Up + foreign re-rating.</CardContent></Card>
      </div>
      <Card>
        <CardHeader><CardTitle className="text-sm">Sector OW/N/UW</CardTitle></CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {d.sectors.map((s) => (
            <Badge key={s.name} variant={s.call === "OW" ? "success" : s.call === "UW" ? "destructive" : "secondary"}>{s.name} - {s.call}</Badge>
          ))}
        </CardContent>
      </Card>
      <p className="text-xs text-slate-500">Source: JPM Indonesia 2026 Outlook (mock) - TanStack Query cache 4h.</p>
    </div>
  )
}
