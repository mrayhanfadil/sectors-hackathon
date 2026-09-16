# Copyright 2026 Sectors Hackathon
"""ADK Agent orchestration router - streaming trace for step-by-step visibility.

Exposes ADK 11-agent graph (Muse Spark 1M via CommandCode bridge) as:

  GET  /api/agent/health          - wiring check (spark reachable, keys, graph)
  POST /api/agent/run             - blocking full run (BBCA → full state)
  GET  /api/agent/stream?ticker=BBCA  - SSE live trace, one event per agent step

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
import re
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
    ticker: str
    prompt: str | None = None


# IDX equity codes are exactly 4 capital letters (BBCA, AMMN, RATU…). Anything
# else - test fixtures like DT1A2B3C, typos, pasted junk - is rejected BEFORE a
# run spawns, because every spawned run bills Sectors: unknown symbols still cost
# 1 credit per addressed endpoint on their 404s (15 Sep 2026: the live-BE
# integration tests burned ~71 credits posting fake tickers at :8777).
# Override with SECTORS_TICKER_RE when a non-4-letter instrument is genuinely needed.
_TICKER_RE = re.compile(os.getenv("SECTORS_TICKER_RE", r"^[A-Z]{4}$"))


def _invalid_ticker_response(raw: str | None) -> JSONResponse | None:
    """None when the ticker is a plausible IDX code, else the 400 to return.

    Shared by /api/agent/start and /api/agent/run so neither path can spawn a
    billable run for junk input.
    """
    ticker = (raw or "").upper().strip()
    if _TICKER_RE.match(ticker):
        return None
    log.warning("agent run rejected ticker=%r (not a 4-letter IDX code)", raw)
    return JSONResponse(
        {
            "ok": False,
            "error": "invalid_ticker",
            "ticker": ticker,
            "message": (
                f"'{raw}' bukan kode IDX yang valid - harus 4 huruf kapital "
                "(contoh: BBCA, AMMN, RATU). Run dibatalkan sebelum jalan supaya "
                "tidak membakar credit Sectors."
            ),
        },
        status_code=400,
    )


@router_agent.get("/api/agent/health", summary="ADK wiring + Spark/minimax health")
async def agent_health():
    """Check if ADK graph can be built with minimax (preferred) or Spark bridge."""
    started = time.time()
    # 0. Explicit opencode-go (Muse Spark 1.3 via Responses API) - honors
    # ADK_PROVIDER first so health reports the ACTIVE provider, not minimax.
    if os.getenv("ADK_PROVIDER", "").lower() in ("opencode-go", "opencode", "opengo", "spark-1.3", "spark13"):
        from agents.adk.providers import spark13_model
        from agents.adk.providers.opencode_responses import _opencode_go_key

        key = _opencode_go_key()
        info: dict[str, Any] = {
            "ok": False,
            "provider": "opencode-go",
            "model": os.getenv("SPARK13_MODEL") or "muse-spark-1.3-contributor",
            "api_base": os.getenv("OPENCODE_GO_BASE_URL") or "https://opencode.ai/zen/go/v1",
        }
        try:
            from google.adk.models.llm_request import LlmRequest
            from google.genai import types as _gt

            info["bridge_key_present"] = bool(key)
            info["bridge_key_prefix"] = (key[:10] + "…") if key else None
            model = spark13_model()
            req = LlmRequest(
                contents=[_gt.Content(role="user", parts=[_gt.Part.from_text(text="PONG")])]
            )
            out = [x async for x in model.generate_content_async(req)]
            content = getattr(out[0], "content", None)
            txt = "".join(p.text or "" for p in (getattr(content, "parts", None) or []) if getattr(p, "text", None))
            info["bridge_ping"] = txt.strip()[:50]
            info["bridge_ok"] = bool("PONG" in txt.upper() or "PING" in txt.upper())
            info["bridge_error"] = None
        except Exception as e:
            info["bridge_error"] = str(e)[:600]
            info["bridge_ok"] = False
        try:
            from agents.adk.app import build_graph

            g = build_graph(ticker="BBCA")
            info["graph"] = {
                "name": getattr(g, "name", ""),
                "n_subagents": len(getattr(g, "sub_agents", []) or []),
                "subagents": [getattr(a, "name", str(a)) for a in (getattr(g, "sub_agents", []) or [])],
            }
            info["ok"] = bool(info.get("bridge_ok") and info["graph"].get("n_subagents"))
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
    """Blocking run - drives full 11-agent graph and returns final state + event trace."""
    if (bad := _invalid_ticker_response(req.ticker)) is not None:
        return bad
    ticker = (req.ticker or "").upper().strip()
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


# === Detached executor (background task, SSE-free) ===

async def _wait_for_session_state(
    session_service,
    ticker: str,
    session_id: str,
    *,
    attempts: int = 12,
    base_delay_s: float = 0.1,
) -> tuple[dict | None, int]:
    """Read session.state, polling until ``debate_output`` has settled.

    The ADK runner exits its async loop the instant ``runner.run_async``
    drains, but the in-memory ``SessionService`` can lag the last
    ``output_key`` write by a few ms. If the injector grabs ``state``
    before ``debate_output["debate"]`` is populated, the audit returns
    ``verdict=PASS, required_flags=[]`` even when debate rounds exist -
    then the post-hoc ``/tmp/reinject_run.py`` patch has to repair it.

    "Settled" means: debate_output is a dict whose ``debate`` key is a
    non-empty list. We poll ``parse_rounds`` (the same parser the audit
    uses) for up to ~3.5s (12 attempts, exponential backoff) waiting
    for rounds to appear. If they never show up, the state we have is
    returned and the audit will correctly return PASS - which is the
    honest answer when no debate rounds exist.
    """
    from agents.valuation.dissent_audit import parse_rounds as _parse
    last_state: dict | None = None
    for attempt in range(attempts):
        try:
            session = await session_service.get_session(
                app_name="sectors-equity-report", user_id="user", session_id=session_id
            )
            st = dict(session.state) if session and session.state else None
        except Exception:
            st = None
        last_state = st
        if st is not None:
            try:
                rounds = _parse(st)
            except Exception:
                rounds = []
            if rounds:
                return st, attempt + 1
        await asyncio.sleep(base_delay_s * (1.5 ** attempt))
    return last_state, attempts


def _inject_post_audit(t: str, final_state: dict | None) -> dict | None:
    """Run the deterministic dissent-audit injector against ``final_state``.

    Mechanical, no LLM. Mirrors the block in agents/adk/runner.run_report
    so every entry point (``/api/agent/start`` background, ``/api/agent/stream``
    SSE, ``/api/agent/run`` blocking) ships the same ``gate_flags`` shape.
    Returns the (possibly-mutated) state or the original ``None``.
    """
    if final_state is None:
        return final_state
    try:
        from pathlib import Path as _Path
        import json as _json
        _spot = None
        _apath = _Path(__file__).resolve().parents[2] / "data" / "assumptions" / f"{t.upper()}.json"
        if _apath.exists():
            _spot = _json.loads(_apath.read_text(encoding="utf-8")).get("last_price")
        from agents.adk.post_audit_inject import apply_audit_to_state
        # Diagnostic: log parsed-rounds count + debate_output shape to
        # disambiguate race vs audit-bug vs shape mismatch.
        try:
            from agents.valuation.dissent_audit import parse_rounds as _pr
            _parsed = len(_pr(final_state))
            _deb = final_state.get("debate_output")
            _deb_type = type(_deb).__name__ if _deb is not None else "None"
            if isinstance(_deb, dict):
                _deb_keys = sorted(_deb.keys())
                _deb_has_debate = "debate" in _deb
                _deb_len = len(_deb.get("debate") or []) if _deb_has_debate else "?"
            elif isinstance(_deb, str):
                _deb_keys = f"len={len(_deb)} first60={_deb[:60]!r}"
                _deb_len = "?"
            else:
                _deb_keys = _deb_len = "n/a"
        except Exception as _exc:
            log.warning("post_audit_inject shape diag failed for %s: %s", t, _exc)
            _parsed = -1
            _deb_type = _deb_keys = _deb_len = _deb_has_debate = "?"
        _before = final_state.get("writer_output")
        final_state = apply_audit_to_state(final_state, price=_spot)
        _after = final_state.get("writer_output") != _before
        _audit = final_state.get("__audit__") or {}
        log.info(
            "post_audit_inject %s: parsed_rounds=%d state_changed=%s audit=%s "
            "injected_flags=%d deb_type=%s deb_keys=%s deb_len=%s",
            t, _parsed, _after, _audit.get("verdict"),
            _audit.get("injected_flags", 0),
            _deb_type, _deb_keys, _deb_len,
        )
    except Exception as _exc:  # noqa: BLE001 - inject must never break the run
        log.warning("post_audit_inject raised during %s: %s", t, _exc)
    return final_state


async def _execute_run_to_sqlite(t: str, p: str, session_id: str) -> None:
    """Run ADK graph and persist every event to SQLite. No SSE - client-independent.

    Called as asyncio.Task from /api/agent/start. Run continues even if all
    clients disconnect; errors/interruptions persist with reason in SQLite so
    users can resume the same run_id later.
    """
    from server.storage import AgentRunStore
    from server.stream_lifecycle import StreamLifecycleManager

    store = AgentRunStore()
    lifecycle = StreamLifecycleManager(
        run_id=session_id,
        ticker=t,
        prompt=p,
        provider=os.getenv("ADK_PROVIDER", "minimax"),
        model=os.getenv("MINIMAX_MODEL", "minimax/MiniMax-M3"),
        store=store,
        flush_every_n=1,
        flush_interval_sec=1.0,
    )
    await lifecycle.start()

    seq = lifecycle.base_seq
    try:
        from agents.adk.app import build_graph
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types as genai_types

        root = build_graph(ticker=t)
        session_service = InMemorySessionService()
        runner = Runner(agent=root, app_name="sectors-equity-report", session_service=session_service)
        await session_service.create_session(app_name="sectors-equity-report", user_id="user", session_id=session_id)
        content = genai_types.Content(role="user", parts=[genai_types.Part(text=p)])

        try:
            async for ev in runner.run_async(user_id="user", session_id=session_id, new_message=content):
                await lifecycle.on_event(seq, ev)
                seq += 1
                await asyncio.sleep(0)
        except asyncio.CancelledError as exc:
            log.warning("run_to_sqlite cancelled for %s after %d events", t, seq)
            await lifecycle.on_interrupt(exc=exc, error_msg=f"task cancelled after {seq} events")
            raise
        except Exception as exc:
            log.exception("run_to_sqlite execution error for %s after %d events", t, seq)
            await lifecycle.on_error(exc=exc, error_msg=str(exc)[:2000])
            return

        # POST-AUDIT INJECTION (16 Sep 2026): the writer ran before the
        # adversarial_loop, so it cannot know what the red team conceded.
        # The dissent-audit is deterministic and reads the rounds; we wire
        # its required_flags into writer_output.gate_flags AFTER the run
        # and, if the anchor was contested, surface the bear/mid/bull
        # ladder under non_anchored_fvs_disclosed. Mechanical, no LLM
        # in the loop. Two ordering notes that the live injector relies
        # on (16 Sep 2026 E2E bug):
        #   1. session.state['debate_output'] is the adversarial agent's
        #      raw narrative text - not parsed JSON. The StreamLifecycle
        #      backfill (on_complete) rewrites it as {debate:[rounds], ...}
        #      by lifting the last accepted submit_debate payload. We must
        #      run the injector AFTER on_complete to read the parsed shape.
        #   2. lifecycle.accumulated_state is what gets persisted in
        #      finish_run, so injecting into it propagates to the DB.
        final_state, _ = await _wait_for_session_state(session_service, t, session_id)
        await lifecycle.on_complete(final_state=final_state)
        final_state = dict(lifecycle.accumulated_state)
        final_state = _inject_post_audit(t, final_state)

        # Repersist the injected state so the PDF gate reads it from DB.
        try:
            from server.storage import AgentRunStore
            AgentRunStore().update_state(session_id, final_state)
        except Exception as _exc:  # noqa: BLE001 - persist is best-effort
            log.warning("post_audit persist failed for %s: %s", t, _exc)

        log.info("run_to_sqlite completed run_id=%s ticker=%s events=%d", session_id, t, seq)
    except Exception as e:
        log.exception("run_to_sqlite failed for %s", t)
        try:
            await lifecycle.on_error(exc=e, error_msg=str(e)[:2000])
        except Exception:
            pass
    finally:
        try:
            await lifecycle.close()
        except Exception:
            pass


# In-memory registry of active background tasks (keyed by run_id)
_ACTIVE_TASKS: dict[str, asyncio.Task] = {}


@router_agent.post("/api/agent/start", summary="Fire-and-forget ADK run; returns run_id immediately")
async def agent_start(req: AgentRunRequest):
    """Start ADK run as background task. Returns immediately with run_id.

    Client polls /api/agent/runs/{run_id} to track progress (every 2s).
    Tab close/navigate/refresh does NOT affect the run; BE drives it to completion.
    """
    from server.storage import AgentRunStore

    if (bad := _invalid_ticker_response(req.ticker)) is not None:
        return bad
    ticker = (req.ticker or "").upper().strip()

    from server.storage import AgentRunStore
    store = AgentRunStore()

    # Concurrency lock: refuse to start if there is already an active run for this ticker.
    # Active = status='running' AND has events in last 60 seconds (avoid stale rows).
    active_for_ticker = [
        r for r in store.list_runs(ticker=ticker, limit=10)
        if r["status"] == "running" and (time.time() - r.get("started_at", 0)) < 60
    ]
    if active_for_ticker:
        log.info("agent_start refused for ticker=%s: %d active run(s) already", ticker, len(active_for_ticker))
        return JSONResponse({
            "ok": False,
            "ticker": ticker,
            "error": "active_run_exists",
            "message": f"Ticker {ticker} sudah ada run berjalan. Tunggu sampai selesai atau klik row yang sedang jalan.",
            "active_run_id": active_for_ticker[0]["run_id"],
            "n_active": len(active_for_ticker),
        }, status_code=409)

    # Smart session_id: reuse recent interrupted run (resume) or allocate fresh
    recent = store.get_recent_interrupted_run(ticker, within_seconds=600.0)
    if recent and recent.get("run_id"):
        session_id = recent["run_id"]
        log.info("agent_start reusing recent interrupted run_id=%s for ticker=%s", session_id, ticker)
    else:
        session_id = f"{ticker.lower()}-{os.urandom(4).hex()}"

    p = req.prompt or f"Generate an institutional equity report for {ticker} (IDX). Use Sectors MCP/tools for every number via calc_* tools; when SECTORS_API_KEY is absent, STOP with sectors_missing_key - never synthetic disclosures."

    # Spawn background task; do NOT await it
    task = asyncio.create_task(_execute_run_to_sqlite(ticker, p, session_id))
    _ACTIVE_TASKS[session_id] = task
    task.add_done_callback(lambda t: _ACTIVE_TASKS.pop(session_id, None))

    return {
        "ok": True,
        "run_id": session_id,
        "ticker": ticker,
        "status": "started",
        "message": "Run started in background. Poll /api/agent/runs/{run_id} or /api/agent/runs/{run_id}/status to track progress.",
    }


@router_agent.get("/api/agent/runs/{run_id}/status", summary="Lightweight status endpoint for polling")
def get_run_status(run_id: str):
    """Returns just status + n_events + finished_at + reason. Cheap for polling."""
    from server.storage import AgentRunStore
    store = AgentRunStore()
    run = store.get_run(run_id)
    if not run:
        return Response(status_code=404)
    return {
        "run_id": run["run_id"],
        "ticker": run.get("ticker"),
        "status": run.get("status"),
        "n_events": run.get("n_events", 0),
        "finished_at": run.get("finished_at"),
        "started_at": run.get("started_at"),
        "reason": run.get("reason"),
        "is_active": run_id in _ACTIVE_TASKS,
    }


@router_agent.get("/api/agent/stream", summary="SSE live trace - step-by-step agent activity")
async def agent_stream(
    ticker: str = Query("BBCA", description="IDX ticker, e.g. BBCA"),
    prompt: str | None = Query(None, description="optional prompt override"),
):
    """SSE stream - yields one JSON per ADK Event as the graph runs.

    Client: `new EventSource('/api/agent/stream?ticker=BBCA')` or
    `fetch('/api/agent/stream?ticker=BBCA').then(r=>r.body.getReader()...)`
    Each `data: {...}\n\n` chunk is a serialized event; final chunk has `done:true`.
    """
    t = (ticker or "BBCA").upper().strip()[:10]
    if not t.isalnum():
        return JSONResponse({"error": "invalid ticker"}, status_code=400)

    async def _gen() -> AsyncGenerator[str, None]:
        # open
        yield f"data: {json.dumps({'seq': -1, 'event_type': 'start', 'ticker': t, 'ts': round(time.time(),3)})}\n\n"

        from server.storage import AgentRunStore
        from server.stream_lifecycle import StreamLifecycleManager

        # Smart session_id: if there is a recent interrupted run for this ticker
        # (within 10 minutes), reuse its run_id so new events append to the same row
        # instead of creating a duplicate run row. Otherwise allocate a fresh id.
        store_for_resume = AgentRunStore()
        recent = store_for_resume.get_recent_interrupted_run(t, within_seconds=600.0)
        if recent and recent.get("run_id"):
            session_id = recent["run_id"]
            log.info("agent_stream reusing recent interrupted run_id=%s for ticker=%s", session_id, t)
        else:
            session_id = f"{t.lower()}-{os.urandom(4).hex()}"

        p = prompt or f"Generate an institutional equity report for {t} (IDX). Use Sectors MCP/tools for every number via calc_* tools; when SECTORS_API_KEY is absent, STOP with sectors_missing_key - never synthetic disclosures."

        store = store_for_resume
        lifecycle = StreamLifecycleManager(
            run_id=session_id,
            ticker=t,
            prompt=p,
            provider=os.getenv("ADK_PROVIDER", "minimax"),
            model=os.getenv("MINIMAX_MODEL", "minimax/MiniMax-M3"),
            store=store,
            flush_every_n=1,
            flush_interval_sec=1.0,
        )
        await lifecycle.start()

        # Start seq after lifecycle has set base_seq (handles resume correctly)
        seq = lifecycle.base_seq
        try:
            from agents.adk.app import build_graph
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            from google.genai import types as genai_types

            root = build_graph(ticker=t)
            session_service = InMemorySessionService()
            runner = Runner(agent=root, app_name="sectors-equity-report", session_service=session_service)
            await session_service.create_session(app_name="sectors-equity-report", user_id="user", session_id=session_id)
            content = genai_types.Content(role="user", parts=[genai_types.Part(text=p)])

            try:
                async for ev in runner.run_async(user_id="user", session_id=session_id, new_message=content):
                    frame = await lifecycle.on_event(seq, ev)
                    yield f"data: {json.dumps(frame, ensure_ascii=False)}\n\n"
                    seq += 1
                    # small yield to flush
                    await asyncio.sleep(0)
            except (GeneratorExit, asyncio.CancelledError) as exc:
                # SSE client disconnected mid-stream - mark run as interrupted with client_disconnect reason
                log.warning("agent_stream client disconnected for %s after %d events", t, seq)
                await lifecycle.on_interrupt(exc=exc, error_msg=f"client disconnected after {seq} events")
                raise
            except Exception as exc:
                log.exception("agent_stream execution error for %s after %d events", t, seq)
                await lifecycle.on_error(exc=exc, error_msg=str(exc)[:2000])
                yield f"data: {json.dumps({'seq': 9999, 'event_type': 'error', 'ticker': t, 'error': str(exc)[:2000]})}\n\n"
                return

            # POST-AUDIT INJECTION (16 Sep 2026): see _inject_post_audit /
            # _wait_for_session_state for the rationale. Same path as
            # run_to_sqlite so SSE consumers see the gate_flags surface.
            # Order matters: on_complete backfills debate_output from the
            # event trail; we inject AFTER so we read the parsed shape.
            final_state, _ = await _wait_for_session_state(session_service, t, session_id)
            await lifecycle.on_complete(final_state=final_state)
            final_state = dict(lifecycle.accumulated_state)
            final_state = _inject_post_audit(t, final_state)
            try:
                from server.storage import AgentRunStore
                AgentRunStore().update_state(session_id, final_state)
            except Exception as _exc:  # noqa: BLE001
                log.warning("post_audit persist failed for %s: %s", t, _exc)
            state = lifecycle.accumulated_state

            # summarize state keys + small preview
            preview: dict[str, Any] = {}
            for k, v in state.items():
                s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
                preview[k] = (s[:800] + "…") if len(s) > 800 else v
            yield f"data: {json.dumps({'seq': seq, 'event_type': 'done', 'ticker': t, 'session_id': session_id, 'n_events': seq, 'state_keys': list(state.keys()), 'state_preview': preview, 'ts': round(time.time(),3)}, ensure_ascii=False)}\n\n"
        except (GeneratorExit, asyncio.CancelledError):
            raise
        except Exception as e:
            log.exception("agent_stream failed for %s", t)
            try:
                await lifecycle.on_error(exc=e, error_msg=str(e)[:2000])
            except Exception:
                pass
            yield f"data: {json.dumps({'seq': 9999, 'event_type': 'error', 'ticker': t, 'error': str(e)[:2000]})}\n\n"
        finally:
            await lifecycle.close()

    return StreamingResponse(_gen(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
    })


@router_agent.get("/api/agent/runs", summary="List recent ADK runs")
def list_agent_runs(ticker: str | None = Query(None), limit: int = Query(20, le=100)):
    from server.storage import AgentRunStore
    return {"runs": AgentRunStore().list_runs(ticker=ticker, limit=limit)}


@router_agent.get("/api/agent/runs/summary", summary="Summary of agent runs per-ticker and interrupt reason distribution")
def get_agent_runs_summary():
    """Returns total runs, per-ticker latest run and status counts, and interrupt reason distribution.

    Each ticker also carries `report_ready`: whether data/assumptions/<TICKER>.json exists. That is the same condition
    that makes /api/report/<TICKER> answer 422, so the hub can refuse to list a report a reader cannot open. Deriving it
    here means the frontend needs no per-ticker probe, which otherwise showed up as one console error per unavailable
    ticker.
    """
    from server.routers.pdf import ASSUMPTIONS_DIR
    from server.storage import AgentRunStore

    summary = AgentRunStore().get_runs_summary()
    for ticker, info in (summary.get("tickers") or {}).items():
        if isinstance(info, dict):
            info["report_ready"] = (ASSUMPTIONS_DIR / f"{str(ticker).upper()}.json").exists()
    return summary


@router_agent.get("/api/agent/runs/latest", summary="Get latest completed/terminal ADK run + event trace")
def get_latest_agent_run(ticker: str | None = Query(None, description="IDX ticker, e.g. BBCA")):
    from server.storage import AgentRunStore
    store = AgentRunStore()
    t = ticker.upper().strip() if ticker and ticker.strip() else None
    run = store.get_latest_completed(t)
    if not run:
        return Response(status_code=204)
    run_with_events = store.get_run_with_events(run["run_id"])
    return run_with_events or run


@router_agent.get("/api/agent/runs/{run_id}", summary="Get one ADK run + its event trace")
def get_agent_run(run_id: str):
    from server.storage import AgentRunStore
    store = AgentRunStore()
    run = store.get_run_with_events(run_id)
    if not run:
        return JSONResponse({"error": "not found"}, status_code=404)
    return run

