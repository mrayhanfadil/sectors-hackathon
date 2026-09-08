# Copyright 2026 Sectors Hackathon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Runner helper — programmatic single-shot run via google.adk.runners.Runner.

The ADK launcher (adk run / adk web) is for REPL/web. For one-shot CLI
(--ticker BBCA → drive graph → dump outputs) use Runner directly.

Usage:
  from agents.adk.runner import run_report
  result = await run_report(ticker="BBCA", prompt="Generate report for BBCA")
  # or sync wrapper:
  result = run_report_sync(ticker="BBCA")

Env: DEEPSEEK_API_KEY or GOOGLE_API_KEY, SECTORS_API_KEY optional.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from .app import build_graph

logger = logging.getLogger(__name__)

DEFAULT_APP_NAME = "sectors-equity-report"


async def run_report(
    ticker: str = "BBCA",
    prompt: str | None = None,
    user_id: str = "user",
    session_id: str | None = None,
    app_name: str = DEFAULT_APP_NAME,
    **build_kw: Any,
) -> dict[str, Any]:
    """Run the full graph for one ticker and return session state + events.

    Args:
        ticker: IDX ticker.
        prompt: User prompt to seed the graph. Defaults to ticker-specific prompt.
        user_id: ADK user id.
        session_id: ADK session id (auto-generated if None).
        app_name: ADK app name (isolates session store).
        **build_kw: Passed to build_graph (deepseek_api_key, gemini_api_key, etc.).

    Returns:
        Dict with session_id, events, state (collector_output etc.), last_text.
    """
    prompt = prompt or f"Generate an institutional equity report for {ticker} (IDX). Use Sectors MCP/tools for every number via calc_* tools; when SECTORS_API_KEY is absent, STOP with sectors_missing_key — never synthetic disclosures."

    root = build_graph(ticker=ticker, **build_kw)

    session_service = InMemorySessionService()
    runner = Runner(
        agent=root,
        app_name=app_name,
        session_service=session_service,
    )

    # create session
    session_id = session_id or f"{ticker.lower()}-{os.urandom(4).hex()}"
    await session_service.create_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )

    content = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=prompt)],
    )

    from .storage import AgentRunStore

    store = AgentRunStore()
    store.start_run(
        session_id,
        ticker,
        prompt,
        provider=os.getenv("ADK_PROVIDER", "minimax"),
        model=os.getenv("MINIMAX_MODEL", "minimax/MiniMax-M3"),
    )

    events: list[Any] = []
    last_text = ""
    seq = 0
    try:
        async for event in runner.run_async(
            user_id=user_id, session_id=session_id, new_message=content
        ):
            events.append(event)
            store.append_event(session_id, seq, event)
            seq += 1
            # collect text for debugging
            if event.content and event.content.parts:
                for p in event.content.parts:
                    if p.text:
                        last_text = p.text

        # pull session state (output_key values land here)
        session = await session_service.get_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )
        state = dict(session.state) if session and session.state else {}
        store.finish_run(
            session_id, status="completed", last_text=last_text, state=state
        )
    except Exception as e:
        store.finish_run(
            session_id, status="failed", last_text=last_text, error=str(e)[:2000]
        )
        raise

    return {
        "session_id": session_id,
        "ticker": ticker,
        "events": events,
        "state": state,
        "last_text": last_text,
        "n_events": len(events),
    }


def run_report_sync(ticker: str = "BBCA", **kw: Any) -> dict[str, Any]:
    """Sync wrapper for run_report."""
    return asyncio.run(run_report(ticker=ticker, **kw))
