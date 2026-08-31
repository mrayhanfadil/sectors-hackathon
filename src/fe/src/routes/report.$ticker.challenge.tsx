import { createFileRoute } from "@tanstack/react-router"
import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export const Route = (createFileRoute as any)("/report/$ticker/challenge")({ component: ChallengePage })

function ChallengePage() {
  const { ticker } = Route.useParams()
  const tk = String(ticker).toUpperCase()
  const [q, setQ] = React.useState("")
  const [log, setLog] = React.useState<{ q: string; a: string }[]>([])
  function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!q.trim()) return
    const a = `Mock defense for ${tk}: claim checked vs assumptions/valuation/news.json - defend(evidence) or concede(correction). (Wire to /api/challenge in P3 - Adversarial Red Team)`
    setLog(prev => [{ q, a }, ...prev])
    setQ("")
  }
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Challenge & Defense - {tk}</h1>
      <Card>
        <CardHeader><CardTitle className="text-sm">Ketik kritik - agent harus defend pakai bukti</CardTitle><CardDescription className="text-xs">Anti-sycophancy: tidak boleh agree without evidence. Critic REJECT kalau hallu.</CardDescription></CardHeader>
        <CardContent>
          <form onSubmit={submit} className="flex gap-2">
            <input value={q} onChange={e => setQ(e.target.value)} placeholder="mis: WACC 8.4% too low vs MTEL 10.1%?" className="flex-1 rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-900" />
            <Button type="submit">Challenge</Button>
          </form>
          {log.length > 0 && (
            <div className="mt-4 space-y-3">
              {log.map((l, i) => (
                <div key={i} className="rounded-md border p-3 text-sm">
                  <div className="font-medium">Q: {l.q}</div>
                  <div className="mt-1 text-slate-600">A: {l.a}</div>
                </div>
              ))}
            </div>
          )}
          <p className="mt-3 text-xs text-slate-500">Log: debate.json - wired in P3 (agents/adversarial.py).</p>
        </CardContent>
      </Card>
    </div>
  )
}
