# Copyright 2026 Sectors Hackathon
"""Concurrency probe for Muse Spark 1.3 via opencode-go Responses API.

Probes 4 parallel Responses API calls to verify Spark 1.3 handles concurrency
without 429, 500, or throttling timeouts before flipping ADK graph to parallel.
Gated on OPENCODE_GO_LIVE=1.
"""

from __future__ import annotations

import asyncio
import os
import time

import pytest
from google.adk.models.llm_request import LlmRequest
from google.genai import types

from agents.adk.providers.opencode_responses import spark13_model
from server.report import numfmt as _nf


async def _pong() -> str:
    m = spark13_model()
    req = LlmRequest(contents=[types.Content(role="user", parts=[types.Part.from_text(text="Reply with PONG")])])
    out = [x async for x in m.generate_content_async(req)]
    if not out or not out[0].content or not out[0].content.parts:
        return ""
    texts = [p.text for p in out[0].content.parts if p.text]
    return " ".join(texts)


async def _gather4() -> list[str]:
    return list(await asyncio.gather(*[_pong() for _ in range(4)]))


def test_4x_parallel_pong_live():
    if os.getenv("OPENCODE_GO_LIVE") != "1":
        pytest.skip("gated (OPENCODE_GO_LIVE=1)")
    t0 = time.time()
    texts = asyncio.run(_gather4())
    wall = time.time() - t0
    assert len(texts) == 4, f"Expected 4 responses, got {len(texts)}"
    assert all("PONG" in t.upper() for t in texts), texts
    print(f"\n4 parallel took {_nf.dec(wall, digits=1)}s")
