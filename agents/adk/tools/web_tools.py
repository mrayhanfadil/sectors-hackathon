# Copyright 2026 Sectors Hackathon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Web tools — FunctionTool wrapper for Sectors search (Sectors-only).

Sectors-only search (extract killed Sep 2026, Sectors-only rule):
  web_search → Sectors v2 news (single gateway, extension=idx). No other tool:
  web_extract + web_search_and_extract (arbitrary-URL fetching) were removed
  as external sources. Agents cite Sectors urls only.

Env:
  SECTORS_API_KEY — required for live search; missing key returns honest empty result

Honest provenance:
  Every result row carries (source, tier, fetched_at). Without SECTORS_API_KEY
  the tool returns {results: [], source: "sectors_missing_key"} rather than fabricating.
  The Critic agent checks source == "sectors" before accepting claims (agents/critic.py).

FunctionTool wrapping:
  google.adk.tools.function_tool.FunctionTool(func) is applied at import time
  in agents/adk/app.py. We expose plain callables here — ADK introspects them.

Usage:
    from .web_tools import web_search
    tools = [FunctionTool(web_search)]
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Annotated
from datetime import datetime, timezone


logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------------
# Tier domain allowlist — Indonesian equity research priority
# ----------------------------------------------------------------------------
TIER_DOMAINS: dict[str, list[str]] = {
    "t1": [  # Highest trust: official IDX + major Indonesian finance outlets
        "idx.co.id",
        "kontan.co.id",
        "bisnis.com",
        "idxchannel.com",
        "cnbcindonesia.com",
        "investor.id",
    ],
    "t2": [  # International finance + Indonesia English
        "reuters.com",
        "bloomberg.com",
        "thejakartapost.com",
        "jakartaglobe.id",
        "nikkei.com",
    ],
    "t3": [  # Retail / blog — include only if T1/T2 < 3
        "stockbit.com",
        "ipotan.co.id",
        "infovesta.com",
        "bareksa.com",
    ],
}


def _domain_tier(url: str) -> str:
    """Return tier ('t1'/'t2'/'t3') for a URL. Empty string if unknown."""
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)
    except Exception:
        return ""
    host = (parsed.hostname or "").lower()
    if not host:
        return ""
    # Strip leading www.
    if host.startswith("www."):
        host = host[4:]
    for tier, domains in TIER_DOMAINS.items():
        for d in domains:
            if host == d or host.endswith("." + d):
                return tier
    return ""


# ----------------------------------------------------------------------------
# IDX ticker allowlist — failed-closed extraction (Lane A).
# The old heuristic (first ALL-CAPS token >= 4 chars) misfired on English
# words (BUY, TARGET, EARNINGS...). Now: only known IDX codes extract;
# unknown tokens yield NO ticker rather than a wrong ticker.
# ----------------------------------------------------------------------------
KNOWN_IDX_TICKERS: frozenset[str] = frozenset({
    # Quintet (assumption-backed core coverage)
    "BBCA", "ADRO", "RATU", "MTEL", "CDIA",
    # Banks / digital banks
    "BBRI", "BMRI", "BBNI", "BRIS", "ARTO",
    # Infra / telco / towers
    "TOWR", "TLKM", "ISAT", "EXCL",
    # Conglomerates / heavy equipment
    "ASII", "UNTR", "AMMN", "TPIA", "SSIA", "SSMS",
    # Oil / gas / power
    "MEDC", "ELSA", "PGAS", "PGEO", "POWR",
    # Mining / coal
    "PTBA", "ITMG", "BUMI",
    # Other assumption-file issuers
    "VKTR",
})


def _known_tickers() -> frozenset[str]:
    """Static allowlist ∪ data/assumptions/<T>.json stems (best-effort)."""
    try:
        from pathlib import Path as _Path

        stems = {p.stem.upper() for p in (_Path(__file__).resolve().parents[3] / "data" / "assumptions").glob("*.json")}
        stems = {s for s in stems if 3 <= len(s) <= 4 and s.isalpha()}
        return KNOWN_IDX_TICKERS | frozenset(stems)
    except Exception:
        return KNOWN_IDX_TICKERS


def _extract_tickers(query: str, limit: int = 3) -> list[str]:
    """Extract known IDX tickers from free text — failed-closed.

    Accepts 3-4 char bare codes, comma/space-separated, case-insensitive,
    with optional `.JK` suffix. Tokens not on the allowlist are ignored;
    no allowlisted token -> [] (caller emits 'no IDX ticker detected').
    """
    known = _known_tickers()
    out: list[str] = []
    for raw in (query or "").upper().replace(",", " ").split():
        w = raw.strip(".,;:!?()[]{}\"'")
        if w.endswith(".JK"):
            w = w[:-3]
        if not (3 <= len(w) <= 4):
            continue
        if not w.isalpha():
            continue
        if w not in known:
            continue
        if w not in out:
            out.append(w)
        if len(out) >= limit:
            break
    return out


# ----------------------------------------------------------------------------
# Gateway stats (legacy removed: Sectors single key, no third-party pool).
# Kept as _pool_stats for the key-pool diagnostic + health callers.
# ----------------------------------------------------------------------------
def _pool_stats() -> dict[str, Any]:
    """Return gateway state for /api/health or debugging (no secrets)."""
    key = os.environ.get("SECTORS_API_KEY", "").strip()
    if key:
        return {
            "total": 1,
            "healthy": 1,
            "in_cooldown": 0,
            "gateway": "sectors",
            "keys": [
                {
                    "prefix": key[:10] + "...",
                    "healthy": True,
                    "cooldown_remaining_s": 0,
                    "last_error": "",
                }
            ],
        }
    return {
        "total": 0,
        "healthy": 0,
        "in_cooldown": 0,
        "gateway": "sectors",
        "keys": [],
    }


# ----------------------------------------------------------------------------
# Tool 1: web_search — Sectors v2 news wrapper (single gateway)
# ----------------------------------------------------------------------------
async def web_search(
    query: Annotated[str, "Search query. Include ticker + topic for best IDX results, e.g. 'BBCA IDX earnings target price 2026'."],
    n_results: Annotated[int, "Max results (default 5, max 20)."] = 5,
    tier: Annotated[str, "Source tier: 't1' (idx.co.id/kontan/bisnis), 't2' (reuters/bloomberg), 't3' (retail), or 'all' (no filter)."] = "all",
    days: Annotated[int, "Recency window in days. 0 = no recency filter."] = 0,
) -> dict[str, Any]:
    """Search IDX equity news via Sectors v2 (single gateway).

    Returns:
        {
          "query": str,
          "tier": str,
          "source": "sectors" | "sectors_missing_key" | "sectors_error",
          "fetched_at": ISO timestamp,
          "results": [
            {"url": str, "title": str, "content": str, "score": float,
             "tier": "t1"|"t2"|"t3"|"", "date": str, "symbols": list[str]}
          ],
        },

    Sectors v2 news shape (GET /v2/news/news/): each row carries the article
    link in `source` (no separate `url` key), prose in `body`, publish time
    in `timestamp`, tickers in `symbols`, and a per-article `dimension` map
    (future/dividend/ownership/technical/valuation/financials/management/
    sustainability, each 0-2). `score` is the dimension sum (0-16) so callers
    can rank by signal density instead of a hardcoded 0.0.

    Honest behavior: without SECTORS_API_KEY returns empty results with
    source='sectors_missing_key' (legacy removed — no third-party search).
    """
    from server.sectors import SectorsNotConfigured as _SNC
    from server.sectors import news as _sectors_news

    fetched_at = datetime.now(timezone.utc).isoformat()

    # Ticker guess = allowlisted IDX codes only (failed-closed: English words
    # like BUY/TARGET never extract; unknown -> 'no IDX ticker detected').
    try:
        import asyncio as _aio
        from datetime import date as _date
        from datetime import timedelta as _td

        syms = _extract_tickers(query)
        if not syms:
            return {
                "query": query,
                "tier": tier,
                "source": "sectors",
                "fetched_at": fetched_at,
                "results": [],
                "note": "no IDX ticker detected in query",
            }
        kwargs: dict[str, str] = {}
        if days > 0:
            _end = _date.today()
            kwargs = {
                "start": (_end - _td(days=min(days, 365))).isoformat(),
                "end": _end.isoformat(),
            }
        raw = await _aio.to_thread(_sectors_news, ",".join(syms), **kwargs)
        items = (raw or {}).get("data") or (raw or {}).get("results") or []
        out = []
        for it in items[: min(max(1, n_results), 20)]:
            if not isinstance(it, dict):
                continue
            # Sectors v2 news shape: link lives in `source` (no `url` key),
            # prose in `body`, publish time in `timestamp`, tickers in
            # `symbols`; legacy `url`/`link`/`summary`/`content` keys kept as
            # fallbacks so other feeds don't break.
            url = it.get("source") or it.get("url") or it.get("link") or ""
            body = it.get("body") or it.get("summary") or it.get("content") or ""
            dim = it.get("dimension") or {}
            score = (sum(float(v) for v in dim.values()
                         if isinstance(v, (int, float)))
                     if isinstance(dim, dict) else 0.0)
            out.append({
                "url": url,
                "title": it.get("title", ""),
                "content": str(body)[:800],
                "score": score,
                "tier": _domain_tier(url),
                "date": str(it.get("timestamp") or it.get("date") or "")[:10],
                "symbols": it.get("symbols") or [],
            })
        # Tier filter is advisory — applied post-hoc, never fabricates.
        if tier and tier != "all" and tier in TIER_DOMAINS:
            _tf = [r for r in out if r.get("tier") == tier]
            out = _tf or out
        return {
            "query": query,
            "tier": tier,
            "source": "sectors",
            "fetched_at": fetched_at,
            "results": out,
        }
    except _SNC:
        return {
            "query": query,
            "tier": tier,
            "source": "sectors_missing_key",
            "fetched_at": fetched_at,
            "results": [],
        }
    except Exception as e:
        logger.warning("Sectors news failed: %s", e)
        return {
            "query": query,
            "tier": tier,
            "source": "sectors_error",
            "fetched_at": fetched_at,
            "results": [],
            "error": str(e)[:300],
        }


# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
# KILLED (Sep 2026, Sectors-only rule): web_extract + web_search_and_extract
# lived here (arbitrary-URL fetching via httpx+readability — external source,
# prohibited). Only Sectors-backed web_search survives below. Agents must cite
# Sectors urls; no third-party page extraction. Do not re-add fetchers.
# Smoke test (run as: .venv/bin/python -m agents.adk.tools.web_tools)
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    import json
    import sys

    if not os.environ.get("SECTORS_API_KEY"):
        print("SECTORS_API_KEY not set — web_search returns honest empty (extract killed Sep 2026)")
        out = asyncio.run(web_search("BBCA IDX earnings 2026", n_results=3))
        print(json.dumps(out, indent=2)[:800])
        sys.exit(0)

    print("Running Sectors search smoke test...")
    out = asyncio.run(web_search("BBCA IDX earnings 2026", n_results=3))
    print(json.dumps(out, indent=2, default=str)[:3000])
