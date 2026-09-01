# Copyright 2026 Sectors Hackathon
"""ADK Agent orchestration router — streaming trace for step-by-step visibility.

Exposes ADK 11-agent graph (Muse Spark 1M via CommandCode bridge) as:

  GET  /api/agent/health          — wiring check (spark reachable, keys, graph)
  POST /api/agent/run             — blocking full run (BBCA → full state)
  GET  /api/agent/stream?ticker=BBCA  — SSE live trace, one event per agent step

Every SSE chunk is JSON: {seq, author, event_type, text, function_calls, state_delta, ts}
Clients should use EventSource / fetch+readableStream. FE /agent page streams this.

Muse Spark 1M is wired via providers.spark_model() → LiteLlm(openai/meta/muse-spark-1.2-contributor
@ http://127.0.0.1:9992/v1, max_tokens=4096). Bridge key from BRIDGE_API_KEY or file.
No fallback secrets are echoed in responses.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import logging
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Query, Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

log = logging.getLogger(__name__)
router_agent = APIRouter()


def _serialize_event(ev: Any, seq: int) -> dict[str, Any]:
    """Convert ADK Event → JSON-serializable trace frame."""
    author = getattr(ev, "author", "") or ""
    invocation_id = getattr(ev, "invocation_id", "") or ""
    branch = getattr(ev, "branch", None)
    # Node info (best-effort)
    node_info = getattr(ev, "node_info", None)
    node_name = ""
    if node_info is not None:
        node_name = getattr(node_info, "name", "") or getattr(node_info, "path", "") or ""
    # Content parts
    text_parts: list[str] = []
    function_calls: list[dict[str, Any]] = []
    function_responses: list[dict[str, Any]] = []
    content = getattr(ev, "content", None)
    if content is not None:
        parts = getattr(content, "parts", None) or []
        for p in parts:
            t = getattr(p, "text", None)
            if t:
                text_parts.append(t)
            fc = getattr(p, "function_call", None)
            if fc is not None:
                function_calls.append(
                    {
                        "name": getattr(fc, "name", ""),
                        "args": getattr(fc, "args", {}),
                        "id": getattr(fc, "id", ""),
                    }
                )
            fr = getattr(p, "function_response", None)
            if fr is not None:
                try:
                    resp = getattr(fr, "response", fr)
                    if isinstance(resp, dict):
                        resp_s = resp
                    else:
                        resp_s = str(resp)[:2000]
                except Exception:
                    resp_s = str(fr)[:2000]
                function_responses.append(
                    {
                        "name": getattr(fr, "name", ""),
                        "response": resp_s,
                        "id": getattr(fr, "id", ""),
                    }
                )
    # Actions
    actions = getattr(ev, "actions", None)
    state_delta = None
    transfer = None
    if actions is not None:
        sd = getattr(actions, "state_delta", None)
        if sd:
            try:
                # state_delta is dict of output_key → value (often large)
                # truncate large values for SSE
                state_delta = {}
                for k, v in dict(sd).items():
                    s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
                    if len(s) > 4000:
                        s = s[:4000] + "…(truncated)"
                        try:
                            state_delta[k] = json.loads(s) if s.startswith("{") else s
                        except Exception:
                            state_delta[k] = s
                    else:
                        state_delta[k] = v
            except Exception:
                state_delta = str(sd)[:3000]
        transfer = getattr(actions, "transfer_to_agent", None)
    # Event type hint
    event_type = "message"
    if function_calls:
        event_type = "function_call"
    elif function_responses:
        event_type = "function_response"
    elif transfer:
        event_type = "transfer"
    elif text_parts and author:
        event_type = "agent_message"

    return {
        "seq": seq,
        "ts": round(time.time(), 3),
        "author": author,
        "node": node_name,
        "branch": branch,
        "invocation_id": invocation_id,
        "event_type": event_type,
        "text": "\n".join(text_parts)[:8000] if text_parts else "",
        "function_calls": function_calls,
        "function_responses": function_responses,
        "state_delta_keys": list(state_delta.keys()) if isinstance(state_delta, dict) else [],
        "state_delta": state_delta,
        "transfer_to": transfer,
    }


class AgentRunRequest(BaseModel):
    ticker: str = "BBCA"
    prompt: str | None = None


@router_agent.get("/api/agent/health", summary="ADK wiring + Spark/minimax health")
async def agent_health():
    """Check if ADK graph can be built with minimax (preferred) or Spark bridge."""
    started = time.time()
    from agents.adk.providers import _minimax_api_key

    direct_minimax_key = _minimax_api_key()
    prefer_minimax = bool(
        direct_minimax_key
        or (os.getenv("ADK_PROVIDER", "").lower().startswith("minimax"))
        or (os.getenv("COMMANDCODE_API_KEY"))
        or (os.getenv("MINIMAX_MODEL"))
    )
    # Also probe disk for COMMANDCODE_API_KEY if not in env
    if not prefer_minimax:
        try:
            import pathlib, re as _re2
            p = pathlib.Path.home() / ".config" / "commandcode-bridge" / "env"
            if p.exists() and _re2.search(r'COMMANDCODE_API_KEY="[^"]+"', p.read_text()):
                prefer_minimax = True
        except Exception:
            pass

    if direct_minimax_key:
        provider = "minimax"
        model_id = os.getenv("MINIMAX_MODEL") or "MiniMax-M3"
        api_base = os.getenv("MINIMAX_BASE_URL") or "https://api.minimax.io/v1"
        info: dict[str, Any] = {
            "ok": False,
            "provider": provider,
            "model": f"minimax/{model_id}",
            "api_base": api_base,
            "bridge_error": None,
        }
        try:
            import litellm
            info["bridge_key_present"] = True
            info["bridge_key_prefix"] = (direct_minimax_key[:10] + "…") if direct_minimax_key else None
            resp = await asyncio.to_thread(
                lambda: litellm.completion(
                    model=f"minimax/{model_id}",
                    api_base=api_base,
                    api_key=direct_minimax_key,
                    messages=[{"role": "user", "content": "Reply with PONG"}],
                    max_tokens=256,
                )
            )
            txt = resp.choices[0].message.content or ""
            info["bridge_ping"] = txt.strip()[:50]
            info["bridge_ok"] = bool("PONG" in txt or "PING" in txt or "Pong" in txt or txt.strip())
            info["bridge_error"] = None
        except Exception as e:
            info["bridge_error"] = str(e)[:600]
            info["bridge_ok"] = False
    elif prefer_minimax:
        provider = "minimax/minimax-m3-free"
        model_id = os.getenv("MINIMAX_MODEL") or "minimax/minimax-m3-free"
        api_base = os.getenv("MINIMAX_API_BASE") or "https://api.commandcode.ai/provider/v1"
        info: dict[str, Any] = {"ok": False, "provider": provider, "model": model_id, "api_base": api_base}
        try:
            import pathlib, re as _re, litellm
            key = os.getenv("COMMANDCODE_API_KEY") or ""
            if not key:
                t = pathlib.Path.home().joinpath(".config/commandcode-bridge/env").read_text()
                m = _re.search(r'COMMANDCODE_API_KEY="([^"]+)"', t)
                if m: key = m.group(1)
            info["bridge_key_present"] = bool(key)
            info["bridge_key_prefix"] = (key[:10] + "…") if key else None
            resp = await asyncio.to_thread(
                lambda: litellm.completion(
                    model=f"openai/{model_id}",
                    api_base=api_base,
                    api_key=key,
                    messages=[{"role": "user", "content": "PONG"}],
                    max_tokens=16,
                )
            )
            txt = resp.choices[0].message.content or ""
            info["bridge_ping"] = txt.strip()[:50]
            info["bridge_ok"] = ("PONG" in txt or "PING" in txt or "Pong" in txt)
        except Exception as e:
            info["bridge_error"] = str(e)[:600]
            info["bridge_ok"] = False
    else:
        info: dict[str, Any] = {"ok": False, "provider": "spark (commandcode bridge)", "model": "meta/muse-spark-1.2-contributor"}
        try:
            from agents.adk.providers import spark_model, _bridge_key

            key = _bridge_key()
            info["bridge_key_present"] = bool(key)
            info["bridge_key_prefix"] = (key[:10] + "…") if key else None
            import litellm

            resp = await asyncio.to_thread(
                lambda: litellm.completion(
                    model="openai/meta/muse-spark-1.2-contributor",
                    api_base="http://127.0.0.1:9992/v1",
                    api_key=key,
                    messages=[{"role": "user", "content": "PONG"}],
                    max_tokens=256,
                )
            )
            txt = resp.choices[0].message.content or ""
            info["bridge_ping"] = txt.strip()[:50]
            info["bridge_ok"] = ("PONG" in txt or "PING" in txt)
        except Exception as e:
            info["bridge_error"] = str(e)[:500]
            info["bridge_ok"] = False

    # Try building graph (without running)
    try:
        from agents.adk.app import build_graph

        g = build_graph(ticker="BBCA")
        info["graph"] = {
            "name": getattr(g, "name", ""),
            "n_subagents": len(getattr(g, "sub_agents", []) or []),
            "subagents": [getattr(a, "name", str(a)) for a in (getattr(g, "sub_agents", []) or [])],
        }
        info["ok"] = bool(info.get("bridge_ok"))
    except Exception as e:
        info["graph_error"] = str(e)[:800]
        info["ok"] = False

    info["elapsed_ms"] = round((time.time() - started) * 1000)
    try:
        from .mock_sectors import get_mock_sectors_status

        info["mock_sectors"] = get_mock_sectors_status()
    except Exception:
        pass
    return info


@router_agent.post("/api/agent/run", summary="Blocking ADK full run (no stream)")
async def agent_run(req: AgentRunRequest):
    """Blocking run — drives full 11-agent graph and returns final state + event trace."""
    ticker = (req.ticker or "BBCA").upper().strip()[:10]
    if not ticker.isalnum():
        return JSONResponse({"error": "invalid ticker"}, status_code=400)
    try:
        from agents.adk.runner import run_report

        started = time.time()
        result = await run_report(ticker=ticker, prompt=req.prompt)
        events = result.get("events", [])
        # serialize trace (light)
        trace = [_serialize_event(ev, i) for i, ev in enumerate(events)]
        # keep only last 200 if huge
        if len(trace) > 200:
            trace = trace[:120] + [{"seq": -1, "author": "system", "event_type": "truncated", "text": f"… {len(events)-200} events truncated …"}] + trace[-80:]
        state = result.get("state", {})
        # truncate large state values for JSON response
        state_preview: dict[str, Any] = {}
        for k, v in (state or {}).items():
            s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
            if len(s) > 6000:
                s = s[:6000] + "…(truncated)"
                try:
                    state_preview[k] = json.loads(s) if s.strip().startswith("{") else s
                except Exception:
                    state_preview[k] = s[:6000]
            else:
                state_preview[k] = v
        return {
            "ok": True,
            "ticker": ticker,
            "elapsed_ms": round((time.time() - started) * 1000),
            "n_events": len(events),
            "session_id": result.get("session_id"),
            "last_text": (result.get("last_text") or "")[:8000],
            "state_keys": list((state or {}).keys()),
            "state": state_preview,
            "trace": trace,
        }
    except Exception as e:
        log.exception("agent_run failed for %s", ticker)
        return JSONResponse({"ok": False, "error": str(e)[:2000], "ticker": ticker}, status_code=500)


@router_agent.get("/api/agent/stream", summary="SSE live trace — step-by-step agent activity")
async def agent_stream(
    ticker: str = Query("BBCA", description="IDX ticker, e.g. BBCA"),
    prompt: str | None = Query(None, description="optional prompt override"),
):
    """SSE stream — yields one JSON per ADK Event as the graph runs.

    Client: `new EventSource('/api/agent/stream?ticker=BBCA')` or
    `fetch('/api/agent/stream?ticker=BBCA').then(r=>r.body.getReader()...)`
    Each `data: {...}\\n\\n` chunk is a serialized event; final chunk has `done:true`.
    """
    t = (ticker or "BBCA").upper().strip()[:10]
    if not t.isalnum():
        return JSONResponse({"error": "invalid ticker"}, status_code=400)

    async def _gen() -> AsyncGenerator[str, None]:
        # open
        yield f"data: {json.dumps({'seq': -1, 'event_type': 'start', 'ticker': t, 'ts': round(time.time(),3)})}\n\n"
        try:
            from agents.adk.app import build_graph
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            from google.genai import types as genai_types
            import os

            root = build_graph(ticker=t)
            session_service = InMemorySessionService()
            runner = Runner(agent=root, app_name="sectors-equity-report", session_service=session_service)
            session_id = f"{t.lower()}-{os.urandom(4).hex()}"
            await session_service.create_session(app_name="sectors-equity-report", user_id="user", session_id=session_id)
            p = prompt or f"Generate an institutional equity report for {t} (IDX). Use Sectors MCP if available; otherwise use synthetic disclosures. Every number must be via calc_* tools."
            content = genai_types.Content(role="user", parts=[genai_types.Part(text=p)])

            from agents.adk.storage import AgentRunStore
            store = AgentRunStore()
            store.start_run(session_id, t, p, provider=os.getenv("ADK_PROVIDER", "minimax"), model=os.getenv("MINIMAX_MODEL", "minimax/MiniMax-M3"))

            seq = 0
            interrupted = False
            try:
                async for ev in runner.run_async(user_id="user", session_id=session_id, new_message=content):
                    frame = _serialize_event(ev, seq)
                    store.append_event(session_id, seq, ev)
                    yield f"data: {json.dumps(frame, ensure_ascii=False)}\n\n"
                    seq += 1
                    # small yield to flush
                    await asyncio.sleep(0)
            except (GeneratorExit, asyncio.CancelledError):
                # SSE client disconnected mid-stream — mark run as interrupted,
                # don't leave it stuck at status='running'.
                interrupted = True
                log.warning("agent_stream interrupted for %s after %d events", t, seq)
                raise
            finally:
                try:
                    if interrupted:
                        store.finish_run(session_id, status="interrupted", last_text="", error=f"client disconnected after {seq} events")
                    # else: completed path below will handle finish_run
                except Exception:
                    log.exception("store.finish_run failed in finally for %s", session_id)

            # final state
            session = await session_service.get_session(app_name="sectors-equity-report", user_id="user", session_id=session_id)
            state = dict(session.state) if session and session.state else {}
            store.finish_run(session_id, status="completed", last_text="", state=state, error=None)

            # summarize state keys + small preview
            preview: dict[str, Any] = {}
            for k, v in state.items():
                s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
                preview[k] = (s[:800] + "…") if len(s) > 800 else v
            yield f"data: {json.dumps({'seq': seq, 'event_type': 'done', 'ticker': t, 'session_id': session_id, 'n_events': seq, 'state_keys': list(state.keys()), 'state_preview': preview, 'ts': round(time.time(),3)}, ensure_ascii=False)}\n\n"
        except Exception as e:
            log.exception("agent_stream failed for %s", t)
            try:
                if 'store' in locals() and 'session_id' in locals():
                    store.finish_run(session_id, status="failed", error=str(e)[:2000])
            except Exception:
                pass
            yield f"data: {json.dumps({'seq': 9999, 'event_type': 'error', 'ticker': t, 'error': str(e)[:2000]})}\n\n"

    return StreamingResponse(_gen(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
    })


@router_agent.get("/api/agent/runs", summary="List recent ADK runs")
def list_agent_runs(ticker: str | None = Query(None), limit: int = Query(20, le=100)):
    from agents.adk.storage import AgentRunStore
    return {"runs": AgentRunStore().list_runs(ticker=ticker, limit=limit)}


@router_agent.get("/api/agent/runs/latest", summary="Get latest completed/terminal ADK run + event trace")
def get_latest_agent_run(ticker: str = Query("BBCA", description="IDX ticker, e.g. BBCA")):
    from agents.adk.storage import AgentRunStore
    store = AgentRunStore()
    t = (ticker or "BBCA").upper().strip()
    run = store.get_latest_completed(t)
    if not run:
        return Response(status_code=204)
    run_with_events = store.get_run_with_events(run["run_id"])
    return run_with_events or run


@router_agent.get("/api/agent/runs/{run_id}", summary="Get one ADK run + its event trace")
def get_agent_run(run_id: str):
    from agents.adk.storage import AgentRunStore
    store = AgentRunStore()
    run = store.get_run_with_events(run_id)
    if not run:
        return JSONResponse({"error": "not found"}, status_code=404)
    return run

