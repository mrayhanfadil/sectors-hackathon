# Copyright 2026 Sectors Hackathon
"""Startup hook for BE server environment loading and diagnostic endpoints.

Loads environment variables from ~/.config/sectors-be/env and local .env files
during lifespan startup to ensure the worker process has all required API keys.
Also provides a diagnostic endpoint for inspecting the Tavily key pool without
exposing secret values.
"""

from __future__ import annotations

import logging
import os
import pathlib
from typing import Any
from fastapi import APIRouter

log = logging.getLogger(__name__)

router_diagnostic = APIRouter(prefix="/api/diagnostic", tags=["diagnostic"])


def load_env_files() -> None:
    """Load env vars from ~/.config/sectors-be/env and local .env files into os.environ."""
    candidates = (
        pathlib.Path.home() / ".config" / "sectors-be" / "env",
        pathlib.Path(__file__).resolve().parents[1] / ".env",
        pathlib.Path(".env"),
        pathlib.Path.home() / ".hermes" / ".env",
        pathlib.Path.home() / ".env",
    )
    for p in candidates:
        if p.exists():
            try:
                for line in p.read_text().splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k and v:
                            os.environ.setdefault(k, v)
            except Exception as e:
                log.warning("Failed loading env from %s: %s", p, e)


async def startup_hook() -> None:
    """Async startup hook called from FastAPI lifespan context manager."""
    load_env_files()
    log.info("Startup hook completed: environment loaded")


@router_diagnostic.get("/tavily-pool", summary="Tavily key pool statistics")
def get_tavily_pool_stats() -> dict[str, Any]:
    """Diagnostic endpoint exposing Tavily pool size and health without leaking secrets."""
    try:
        from agents.adk.tools.web_tools import _pool_stats
        return {"ok": True, "pool": _pool_stats()}
    except Exception as e:
        return {"ok": False, "error": str(e)}
