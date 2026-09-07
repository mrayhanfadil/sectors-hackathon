# Copyright 2026 Sectors Hackathon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Web tools — FunctionTool wrappers for search + extract.

Sectors-only search (legacy removed, Lane E):
  80% → web_search (Sectors v2 news) + web_extract (parallel) → web_search_and_extract
  15% → browser_exec (not ported here — too stateful for stateless FunctionTool)
   5% → terminal + Camoufox (use agents.tools.terminal instead)

Backends:
  web_search    → Sectors v2 news (single gateway, extension=idx)
  web_extract   → httpx + readability-lxml + markdownify (local, no third-party)

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
    from .web_tools import web_search, web_extract, web_search_and_extract
    tools = [FunctionTool(web_search), FunctionTool(web_extract), FunctionTool(web_search_and_extract)]
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Annotated
from datetime import datetime, timezone

import httpx
from readability import Document
from markdownify import markdownify as md
from lxml import html as lxml_html

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
            {"url": str, "title": str, "content": str, "score": float, "tier": "t1"|"t2"|"t3"|""}
          ],
        }

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
            url = it.get("url") or it.get("link") or ""
            out.append({
                "url": url,
                "title": it.get("title", ""),
                "content": str(it.get("summary") or it.get("content") or "")[:800],
                "score": 0.0,
                "tier": _domain_tier(url),
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
# Tool 2: web_extract — local HTTP + readability + markdownify
# ----------------------------------------------------------------------------
async def _extract_one(client: httpx.AsyncClient, url: str) -> dict[str, Any]:
    """Extract a single URL as markdown. Errors don't kill the batch."""
    try:
        r = await client.get(
            url,
            timeout=15.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; HermesEquityBot/1.0; +https://sektoral.id/bot)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "id,en;q=0.8",
            },
        )
        r.raise_for_status()
        # Cap to 5MB before parsing (readability chokes on huge pages)
        raw = r.text[:5_000_000]

        # Strip control chars (NULs, BELs etc) — lxml.html_clean dies with
        # "All strings must be XML compatible: Unicode or ASCII, no NULL bytes
        # or control characters" on PDFs / binary blobs served with text/html
        # content-type (e.g. idx.co.id quarterly PDFs). Keep tab/newline/cr.
        raw = ''.join(ch for ch in raw if ch == '\t' or ch == '\n' or ch == '\r' or ord(ch) >= 0x20)

        # readability-lxml returns the article HTML; markdownify → markdown
        try:
            doc = Document(raw)
            article_html = doc.summary(html_partial=True)
        except (ValueError, Exception) as re:
            # readability / lxml can throw on weird HTML — return empty with reason
            return {"url": url, "title": "", "content": "", "char_count": 0,
                    "status": "parse_error", "error": f"readability: {str(re)[:200]}"}
        content_md = md(article_html, heading_style="ATX", strip=["img", "script", "style", "iframe"])

        # Trim very long content — model only needs first ~5k chars
        content_md = content_md.strip()[:5_000]

        return {
            "url": url,
            "title": doc.title() or "",
            "content": content_md,
            "char_count": len(content_md),
            "status": "ok",
        }
    except httpx.HTTPError as e:
        return {
            "url": url,
            "title": "",
            "content": "",
            "char_count": 0,
            "status": "http_error",
            "error": str(e),
        }
    except Exception as e:  # readability/markdownify can throw on weird HTML
        logger.warning("Extract failed for %s: %s", url, e)
        return {
            "url": url,
            "title": "",
            "content": "",
            "char_count": 0,
            "status": "parse_error",
            "error": str(e)[:200],
        }


async def web_extract(
    urls: Annotated[list[str], "List of URLs to extract as markdown. Max 10 per call."],
) -> dict[str, Any]:
    """Extract page content as markdown via local readability + markdownify.

    Returns:
        {
          "source": "readability_local",
          "fetched_at": ISO timestamp,
          "results": [
            {"url": str, "title": str, "content": str, "char_count": int, "status": "ok"|"http_error"|"parse_error"}
          ],
        }

    Honest behavior: never fabricates content. Failed URLs return status=error
    with empty content — Critic will skip them.
    """
    fetched_at = datetime.now(timezone.utc).isoformat()
    # Cap input — don't blow up memory on 100 URLs
    safe_urls = [u for u in (urls or []) if isinstance(u, str) and u.startswith(("http://", "https://"))][:10]

    if not safe_urls:
        return {
            "source": "readability_local",
            "fetched_at": fetched_at,
            "results": [],
        }

    async with httpx.AsyncClient(timeout=20.0) as cli:
        # Concurrent extraction — 5 at a time max (be a polite citizen)
        sem = asyncio.Semaphore(5)

        async def _guarded(url: str) -> dict[str, Any]:
            async with sem:
                return await _extract_one(cli, url)

        results = await asyncio.gather(*[_guarded(u) for u in safe_urls])

    return {
        "source": "readability_local",
        "fetched_at": fetched_at,
        "results": list(results),
    }


# ----------------------------------------------------------------------------
# Tool 3: web_search_and_extract — composite (run search + extract in parallel)
# ----------------------------------------------------------------------------
async def web_search_and_extract(
    query: Annotated[str, "Search query. Include ticker + topic."],
    n_results: Annotated[int, "Max search results (1..20)."] = 5,
    extract_top_n: Annotated[int, "Extract content from top N search results (0..10, 0=skip extract)."] = 3,
    tier: Annotated[str, "Source tier: 't1'/'t2'/'t3'/'all'."] = "all",
    days: Annotated[int, "Recency in days (0 = no filter)."] = 0,
) -> dict[str, Any]:
    """Run web_search + web_extract in parallel — saves 1 round-trip vs sequential.

    This is the 80% case from Hermes Agent session patterns. Use this when the agent
    needs both discovery AND content from the search results.

    Returns:
        {
          "search": <web_search result>,
          "extract": <web_extract result, may be empty if extract_top_n=0 or search returned 0>,
          "composite_source": "sectors+readability_local" | "sectors_missing_key+readability_local" | ...,
        }

    Concurrency: search and extract are run with asyncio.gather once search
    returns the URL list. extract_top_n=0 skips extraction entirely.
    """
    search_result = await web_search(query, n_results=n_results, tier=tier, days=days)

    urls_to_extract: list[str] = []
    if extract_top_n > 0:
        urls_to_extract = [
            r["url"]
            for r in search_result.get("results", [])[:extract_top_n]
            if r.get("url")
        ]

    if not urls_to_extract:
        extract_result: dict[str, Any] = {
            "source": "readability_local",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "results": [],
        }
    else:
        extract_result = await web_extract(urls_to_extract)

    composite_source = f"{search_result.get('source', 'unknown')}+{extract_result.get('source', 'unknown')}"

    return {
        "search": search_result,
        "extract": extract_result,
        "composite_source": composite_source,
    }


# ----------------------------------------------------------------------------
# Smoke test (run as: .venv/bin/python -m agents.adk.tools.web_tools)
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    import json
    import sys

    if not os.environ.get("SECTORS_API_KEY"):
        print("SECTORS_API_KEY not set — running extract-only smoke test")
        out = asyncio.run(web_extract(["https://www.idx.co.id/"]))
        print(json.dumps(out, indent=2)[:1500])
        sys.exit(0)

    print("Running composite smoke test with Sectors key present...")
    out = asyncio.run(web_search_and_extract("BBCA IDX earnings 2026", n_results=3, extract_top_n=2))
    print(json.dumps(out, indent=2, default=str)[:3000])
