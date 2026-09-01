import { createFileRoute } from "@tanstack/react-router"
import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

export const Route = (createFileRoute as any)("/report/$ticker/challenge")({ component: ChallengePage })

type ChallengeEntry = {
  q: string
  verdict?: string
  evidence?: string
  exhibit_ref?: string | null
  error?: string
}

function ChallengePage() {
  const { ticker } = Route.useParams()
  const tk = String(ticker).toUpperCase()
  const [q, setQ] = React.useState("")
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [log, setLog] = React.useState<ChallengeEntry[]>([])

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    const question = q.trim()
    if (!question || loading) return

    setLoading(true)
    setError(null)

    try {
      const apiBase = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") || ""
      const path = "/api/challenge"
      const url = apiBase ? `${apiBase}${path}` : path

      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker: tk, question: question, claim: question }),
      })

      if (!res.ok) {
        const text = await res.text().catch(() => "")
        let detail = `Request failed (${res.status})`
        try {
          const j = JSON.parse(text)
          detail = j.detail || j.error || j.message || detail
        } catch {
          if (text) detail = text
        }
        throw new Error(detail)
      }

      const data = await res.json()
      if (data.error) {
        setLog(prev => [{ q: question, error: String(data.error) }, ...prev])
      } else {
        setLog(prev => [
          {
            q: question,
            verdict: data.verdict,
            evidence: data.evidence,
            exhibit_ref: data.exhibit_ref,
          },
          ...prev,
        ])
      }
      setQ("")
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setError(msg)
      setLog(prev => [{ q: question, error: msg }, ...prev])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Challenge & Defense — {tk}</h1>
        <a href={`/report/${tk}`} className="text-xs text-slate-500 underline hover:text-slate-900">← Back to Report</a>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Ketik kritik — agent harus defend pakai bukti</CardTitle>
          <CardDescription className="text-xs">Anti-sycophancy: tidak boleh agree without evidence. Critic REJECT kalau hallu.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="flex gap-2">
            <input
              value={q}
              onChange={e => setQ(e.target.value)}
              placeholder="mis: WACC 8.4% too low vs MTEL 10.1%?"
              disabled={loading}
              className="flex-1 rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-900 disabled:opacity-50"
            />
            <Button type="submit" disabled={loading || !q.trim()}>
              {loading ? "Challenging..." : "Challenge"}
            </Button>
          </form>

          {error && (
            <div className="mt-3 rounded-md border border-red-200 bg-red-50 p-2 text-xs text-red-700">
              {error}
            </div>
          )}

          {log.length > 0 && (
            <div className="mt-4 space-y-3">
              {log.map((l, i) => (
                <div key={i} className="rounded-md border p-3 text-sm">
                  <div className="flex items-center justify-between">
                    <div className="font-medium text-slate-900">Q: {l.q}</div>
                    {l.verdict && (
                      <Badge variant={l.verdict.toLowerCase() === "defend" ? "default" : "secondary"}>
                        {l.verdict.toUpperCase()}
                      </Badge>
                    )}
                  </div>
                  {l.evidence && (
                    <div className="mt-2 text-slate-700 leading-relaxed">
                      <span className="font-medium text-slate-900">Defense: </span>
                      {l.evidence}
                    </div>
                  )}
                  {l.exhibit_ref && (
                    <div className="mt-1 text-xs text-slate-500 font-mono">
                      Ref: {l.exhibit_ref}
                    </div>
                  )}
                  {l.error && (
                    <div className="mt-2 text-xs text-red-600">
                      Error: {l.error}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
          <p className="mt-3 text-xs text-slate-500">Log: debate.json — adversarial verification endpoint (/api/challenge).</p>
        </CardContent>
      </Card>
    </div>
  )
}
