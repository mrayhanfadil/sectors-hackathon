import { createFileRoute } from "@tanstack/react-router"
import { useEffect, useRef, useState, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

export const Route = (createFileRoute as any)("/agent")({ component: AgentTrace })

type TraceEvent = {
  seq: number
  ts: number
  author: string
  node: string
  branch?: string | null
  event_type: string
  text: string
  function_calls: { name: string; args: Record<string, unknown>; id: string }[]
  function_responses: { name: string; response: unknown; id: string }[]
  state_delta_keys: string[]
  state_delta?: Record<string, unknown> | null
  transfer_to?: string | null
}

const AGENT_META: Record<string, { label: string; phase: string; color: string }> = {
  collector: { label: "Collector", phase: "Intake (parallel)", color: "bg-sky-100 text-sky-800 border-sky-300" },
  news_harvester: { label: "News Harvester", phase: "Intake (parallel)", color: "bg-amber-100 text-amber-800 border-amber-300" },
  social_sentiment: { label: "Social Sentiment", phase: "Intake (parallel)", color: "bg-violet-100 text-violet-800 border-violet-300" },
  news_search_sub: { label: "News Search Sub", phase: "Intake → Search", color: "bg-amber-50 text-amber-800 border-amber-200" },
  social_search_sub: { label: "Social Search Sub", phase: "Intake → Search", color: "bg-violet-50 text-violet-800 border-violet-200" },
  industry_search_sub: { label: "Industry Search Sub", phase: "Research → Search", color: "bg-emerald-50 text-emerald-800 border-emerald-200" },
  modeler: { label: "Modeler (THE BRAIN)", phase: "Valuation", color: "bg-emerald-100 text-emerald-800 border-emerald-400 font-semibold" },
  analyst: { label: "Analyst", phase: "Research (parallel)", color: "bg-slate-100 text-slate-800 border-slate-300" },
  industry: { label: "Industry", phase: "Research (parallel)", color: "bg-teal-100 text-teal-800 border-teal-300" },
  risk: { label: "Risk", phase: "Research (parallel)", color: "bg-red-100 text-red-800 border-red-300" },
  kpi: { label: "KPI", phase: "Research (parallel)", color: "bg-cyan-100 text-cyan-800 border-cyan-300" },
  writer: { label: "Writer", phase: "Narrative", color: "bg-indigo-100 text-indigo-800 border-indigo-300" },
  visualizer: { label: "Visualizer", phase: "Charts", color: "bg-pink-100 text-pink-800 border-pink-300" },
  sotp: { label: "SOTP", phase: "Aggregation", color: "bg-orange-100 text-orange-800 border-orange-300" },
  adversarial: { label: "Adversarial (Red Team)", phase: "Red Team Loop", color: "bg-rose-100 text-rose-800 border-rose-300" },
  critic: { label: "Critic (QA Arbiter)", phase: "QA", color: "bg-slate-900 text-white border-slate-900" },
  system: { label: "System", phase: "-", color: "bg-slate-50 text-slate-500 border-slate-200" },
}

function AgentBadge({ author }: { author: string }) {
  const m = AGENT_META[author] ?? { label: author || "—", phase: "", color: "bg-slate-100 text-slate-700 border-slate-200" }
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs ${m.color}`}>
      {m.label}
    </span>
  )
}

function PhaseDot({ author }: { author: string }) {
  const m = AGENT_META[author]
  if (!m) return null
  return <span className="text-[11px] text-slate-500">{m.phase}</span>
}

function AgentTrace() {
  const [ticker, setTicker] = useState("BBCA")
  const [events, setEvents] = useState<TraceEvent[]>([])
  const [running, setRunning] = useState(false)
  const [done, setDone] = useState<{ n_events: number; state_keys: string[]; ms: number } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [health, setHealth] = useState<any>(null)
  const [filter, setFilter] = useState<string>("all")
  const listRef = useRef<HTMLDivElement>(null)
  const startRef = useRef<number>(0)

  const apiBase = (import.meta as any).env?.VITE_API_URL || ""

  const fetchHealth = useCallback(async () => {
    try {
      const r = await fetch(`${apiBase}/api/agent/health`)
      const j = await r.json()
      setHealth(j)
    } catch (e: any) {
      setHealth({ ok: false, error: String(e) })
    }
  }, [apiBase])

  useEffect(() => { fetchHealth() }, [fetchHealth])

  // auto-scroll to bottom as events stream
  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight
  }, [events])

  const run = useCallback(async (mode: "stream" | "blocking") => {
    setError(null); setDone(null); setEvents([]); setRunning(true)
    startRef.current = Date.now()
    const t = ticker.trim().toUpperCase() || "BBCA"

    if (mode === "blocking") {
      try {
        const r = await fetch(`${apiBase}/api/agent/run`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ticker: t }),
        })
        const j = await r.json()
        if (!j.ok) throw new Error(j.error || JSON.stringify(j).slice(0, 800))
        setEvents((j.trace || []) as TraceEvent[])
        setDone({ n_events: j.n_events, state_keys: j.state_keys || [], ms: j.elapsed_ms })
      } catch (e: any) {
        setError(String(e.message || e).slice(0, 1000))
      } finally { setRunning(false) }
      return
    }

    // SSE stream mode — preferred for step-by-step visibility
    try {
      const es = new EventSource(`${apiBase}/api/agent/stream?ticker=${encodeURIComponent(t)}`)
      let n = 0
      es.onmessage = (ev) => {
        try {
          const frame = JSON.parse(ev.data) as TraceEvent & { done?: boolean; state_keys?: string[]; state_preview?: any; ticker?: string; error?: string }
          if (frame.event_type === "start") {
            // ignore
            return
          }
          if (frame.event_type === "error") {
            setError(frame.error || frame.text || "stream error")
            es.close(); setRunning(false)
            return
          }
          if ((frame as any).event_type === "done") {
            const d = frame as any
            setDone({ n_events: d.n_events, state_keys: d.state_keys || [], ms: Date.now() - startRef.current })
            es.close(); setRunning(false)
            return
          }
          // normal event
          setEvents(prev => [...prev, frame as TraceEvent])
          n++
        } catch {}
      }
      es.onerror = () => {
        // EventSource will auto-retry; treat close as done if we have events
        // Small grace: if still running and no error frame, just close
        setTimeout(() => {
          if (es.readyState === EventSource.CLOSED) setRunning(false)
        }, 1200)
      }
      // safety timeout 15 min
      setTimeout(() => { try { es.close() } catch {}; setRunning(false) }, 15 * 60 * 1000)
    } catch (e: any) {
      setError(String(e.message || e).slice(0, 1000))
      setRunning(false)
    }
  }, [ticker, apiBase])

  const filtered = filter === "all" ? events : events.filter(e => e.author === filter || e.event_type === filter)

  const authors = Array.from(new Set(events.map(e => e.author).filter(Boolean))).sort()

  return (
    <div className="space-y-4">
      <div className="rounded-xl border bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold tracking-tight">ADK Orchestrator — Live Trace</h1>
            <p className="mt-1 max-w-2xl text-sm leading-relaxed text-slate-600">
              11 agents → <span className="font-medium">Muse Spark 1M</span> via CommandCode bridge <code className="rounded bg-slate-100 px-1">127.0.0.1:9992</code> · intake_parallel(collector+news+social) → modeler(THE BRAIN, calc_* tools) → research_parallel(analyst+industry+risk+kpi) → writer→visualizer→sotp→adversarial×4→critic. Stream SSE <code className="rounded bg-slate-100 px-1">/api/agent/stream</code> for step-by-step.
            </p>
            {health && (
              <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
                <Badge variant={health.ok ? "default" : "secondary"}>{health.ok ? "● Spark OK" : "○ bridge ping: " + (health.bridge_ping || health.bridge_error || "?").slice(0, 40)}</Badge>
                <Badge variant="outline">{health.model || "meta/muse-spark-1.2-contributor"}</Badge>
                <Badge variant="outline">{health.graph?.name || "equity_report_orchestrator"} · {health.graph?.n_subagents ?? 8} nodes</Badge>
                <span className="text-slate-500">provider: {health.provider || "spark (commandcode bridge)"} · {health.elapsed_ms ?? "?"}ms health</span>
                <Button size="sm" variant="outline" className="h-6 px-2 text-xs" onClick={fetchHealth}>Refresh health</Button>
              </div>
            )}
          </div>
          <Badge variant="secondary" className="shrink-0">SSE + blocking</Badge>
        </div>

        <div className="mt-4 flex flex-wrap items-end gap-2">
          <label className="text-xs text-slate-600">Ticker
            <input value={ticker} onChange={e => setTicker(e.target.value.toUpperCase())} placeholder="BBCA" className="ml-2 h-8 w-24 rounded-md border px-2 text-sm font-mono" maxLength={10} />
          </label>
          <Button onClick={() => run("stream")} disabled={running} className="h-8">
            {running ? "Running… (SSE live)" : "▶ Run ADK (SSE live trace)"}
          </Button>
          <Button onClick={() => run("blocking")} disabled={running} variant="outline" className="h-8">
            Run (blocking POST)
          </Button>
          <Button onClick={() => { setEvents([]); setDone(null); setError(null) }} variant="ghost" className="h-8" disabled={running}>
            Clear
          </Button>
          <span className="text-xs text-slate-500">{events.length} events {done ? `· done ${done.n_events} events · keys: ${done.state_keys.join(", ") || "—"} · ${done.ms}ms` : running ? "· streaming…" : ""}</span>
        </div>
        {error && <div className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800">{error}</div>}
      </div>

      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant={filter === "all" ? "default" : "outline"} className="h-7 text-xs" onClick={() => setFilter("all")}>All ({events.length})</Button>
        {authors.map(a => (
          <Button key={a} size="sm" variant={filter === a ? "default" : "outline"} className="h-7 text-xs" onClick={() => setFilter(a)}>
            <span className="mr-1"><AgentBadge author={a} /></span>
          </Button>
        ))}
        <Button size="sm" variant={filter === "function_call" ? "default" : "outline"} className="h-7 text-xs" onClick={() => setFilter("function_call")}>🔧 function_call ({events.filter(e=>e.event_type==="function_call").length})</Button>
      </div>

      {/* Timeline + raw log */}
      <div className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
        <Card className="overflow-hidden">
          <CardHeader className="py-3"><CardTitle className="text-sm">Timeline — {filtered.length} events {running && <span className="ml-2 inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-500" />}</CardTitle></CardHeader>
          <CardContent className="p-0">
            <div ref={listRef} className="max-h-[68vh] overflow-auto divide-y">
              {filtered.length === 0 && <div className="px-4 py-10 text-center text-sm text-slate-500">Belum ada event — klik <span className="font-medium">▶ Run ADK (SSE live trace)</span> untuk mulai. Ticker default BBCA.</div>}
              {filtered.map((ev) => (
                <div key={ev.seq} className="px-3 py-2.5 hover:bg-slate-50">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="font-mono text-[11px] text-slate-400">#{ev.seq}</span>
                      <AgentBadge author={ev.author} />
                      <span className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[11px] text-slate-600">{ev.event_type}</span>
                      {ev.branch && <span className="text-[11px] text-slate-400">{ev.branch}</span>}
                    </div>
                    <span className="shrink-0 font-mono text-[11px] text-slate-400">{new Date(ev.ts * 1000).toLocaleTimeString()}</span>
                  </div>
                  <div className="mt-1 flex items-center gap-2"><PhaseDot author={ev.author} /></div>
                  {ev.text && <div className="mt-1.5 whitespace-pre-wrap break-words rounded bg-slate-50 px-2 py-1.5 font-mono text-[11px] leading-relaxed text-slate-700">{ev.text.slice(0, 1200)}</div>}
                  {ev.function_calls.length > 0 && (
                    <div className="mt-1.5 space-y-1">
                      {ev.function_calls.map((fc, i) => (
                        <div key={i} className="rounded border border-amber-200 bg-amber-50 px-2 py-1.5">
                          <div className="font-mono text-[11px] font-semibold text-amber-900">🔧 {fc.name}</div>
                          <pre className="mt-1 max-h-32 overflow-auto whitespace-pre-wrap break-words text-[11px] text-amber-900/80">{JSON.stringify(fc.args, null, 2).slice(0, 2000)}</pre>
                        </div>
                      ))}
                    </div>
                  )}
                  {ev.function_responses.length > 0 && (
                    <div className="mt-1.5 space-y-1">
                      {ev.function_responses.map((fr, i) => (
                        <div key={i} className="rounded border border-emerald-200 bg-emerald-50 px-2 py-1.5">
                          <div className="font-mono text-[11px] font-semibold text-emerald-900">↩ {fr.name}</div>
                          <pre className="mt-1 max-h-28 overflow-auto whitespace-pre-wrap break-words text-[11px] text-emerald-900/80">{typeof fr.response === "string" ? fr.response.slice(0, 1500) : JSON.stringify(fr.response, null, 2).slice(0, 1500)}</pre>
                        </div>
                      ))}
                    </div>
                  )}
                  {ev.state_delta_keys.length > 0 && (
                    <div className="mt-1.5 flex flex-wrap gap-1">
                      {ev.state_delta_keys.map(k => <Badge key={k} variant="secondary" className="text-[11px]">{k}</Badge>)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="overflow-hidden">
          <CardHeader className="py-3"><CardTitle className="text-sm">Graph — 11 agents (Sequential + Parallel + Loop)</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-xs leading-relaxed text-slate-600">
            <div className="rounded-md border bg-white p-3 font-mono text-[11px] leading-5">
              <div>intake_parallel (3× parallel)</div>
              <div className="ml-3">├─ collector <span className="text-slate-400">(Sectors MCP or synthetic, Spark)</span></div>
              <div className="ml-3">├─ news_harvester → news_search_sub <span className="text-slate-400">(AgentTool, Spark 0-credit)</span></div>
              <div className="ml-3">└─ social_sentiment → social_search_sub <span className="text-slate-400">(AgentTool, Spark 0-credit)</span></div>
              <div>↓</div>
              <div>modeler <span className="font-semibold text-emerald-700">THE BRAIN</span> <span className="text-slate-400">calc_wacc/dcf/ddm/ggm/bands/ratios/blended (FunctionTools)</span></div>
              <div>↓</div>
              <div>research_parallel (4× parallel)</div>
              <div className="ml-3">├─ analyst ├─ industry(→search_sub) ├─ risk ├─ kpi</div>
              <div>↓</div>
              <div>writer → visualizer → sotp → adversarial_loop(×4) → critic</div>
            </div>
            <div className="rounded-md bg-slate-50 p-3 text-[11px]">
              <div className="font-medium text-slate-700">Deterministic engines (no LLM math):</div>
              <div className="mt-1 flex flex-wrap gap-1">
                {["calc_wacc","calc_dcf","calc_ddm","calc_ggm","calc_multiples","calc_sotp","calc_blended","calc_historical_bands","calc_ratios"].map(n => (
                  <Badge key={n} variant="outline" className="font-mono text-[11px]">{n}</Badge>
                ))}
              </div>
              <div className="mt-2 font-medium text-slate-700">State keys (output_key):</div>
              <div className="mt-1 flex flex-wrap gap-1">
                {["collector_output","news_output","social_output","valuation_output","analyst_output","industry_output","risk_output","kpi_output","writer_output","visuals_output","sotp_output","debate_output","critic_output"].map(k => (
                  <Badge key={k} variant="secondary" className="font-mono text-[11px]">{k}</Badge>
                ))}
              </div>
            </div>
            <div className="text-[11px] text-slate-500">
              P0-P1: 0 Sectors credit, search grounding disabled (<code className="rounded bg-slate-100 px-1">ADK_ENABLE_GOOGLE_SEARCH=true</code> to enable with real GOOGLE_API_KEY). Bridge <code className="rounded bg-slate-100 px-1">BRIDGE_API_KEY</code> auto-read from <code className="rounded bg-slate-100 px-1">~/.config/commandcode-bridge/env</code>.
            </div>
          </CardContent>
        </Card>
      </div>
      <p className="mt-4 text-xs text-slate-500 text-center">
        Disclaimer: Produk ini adalah informasi, bukan saran investasi. Keputusan investasi sepenuhnya menjadi tanggung jawab pengguna.
      </p>
    </div>
  )
}
