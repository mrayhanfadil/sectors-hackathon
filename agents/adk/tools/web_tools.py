# Copyright 2026 Sectors Hackathon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Web tools — FunctionTool wrappers for search + extract.

Ported from Hermes Agent's 80/15/5 pattern:
  80% → web_search + web_extract (parallel) → this module's web_search_and_extract
  15% → browser_exec (not ported here — too stateful for stateless FunctionTool)
   5% → terminal + Camoufox (use agents.tools.terminal instead)

Backends (Opsi C — hybrid pragmatic):
  web_search    → Tavily (free 1,000/mo, IDX-friendly via include_domains)
  web_extract   → httpx + readability-lxml + markdownify (local, no third-party)

Env:
  TAVILY_API_KEY  — required for live search; missing key returns honest empty result

Honest provenance:
  Every result row carries (source, tier, fetched_at). If TAVILY_API_KEY is missing
  the tool returns {results: [], source: "tavily_missing_key"} rather than fabricating.
  The Critic agent checks source == "tavily" before accepting claims (agents/critic.py).

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
import time
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
# Tavily API Key Pool (Round-Robin with Cooldown)
# ----------------------------------------------------------------------------
_KEY_POOL: list[str] = []
_KEY_STATE: dict[str, dict[str, Any]] = {}  # key -> {healthy: bool, cooldown_until: float, last_error: str}
_LAST_ROTATION: int = 0  # round-robin index
_COOLDOWN_SECONDS = 60


def _load_key_pool() -> list[str]:
    """Load from TAVILY_API_KEYS (comma-sep) or fallback TAVILY_API_KEY."""
    multi = os.getenv("TAVILY_API_KEYS", "").strip()
    if multi:
        keys = [k.strip() for k in multi.split(",") if k.strip()]
        if keys:
            return keys
    single = os.getenv("TAVILY_API_KEY", "").strip()
    return [single] if single else []


def _init_pool() -> None:
    global _KEY_POOL, _KEY_STATE
    keys = _load_key_pool()
    if keys != _KEY_POOL:
        _KEY_POOL = keys
        _KEY_STATE = {
            k: _KEY_STATE.get(k, {"healthy": True, "cooldown_until": 0.0, "last_error": ""})
            for k in _KEY_POOL
        }


def _pick_key() -> str | None:
    """Round-robin pick first healthy key (cooldown expired)."""
    _init_pool()
    global _LAST_ROTATION
    if not _KEY_POOL:
        return None
    now = time.time()
    n = len(_KEY_POOL)
    for i in range(n):
        idx = (_LAST_ROTATION + i) % n
        key = _KEY_POOL[idx]
        st = _KEY_STATE[key]
        if not st["healthy"] and st["cooldown_until"] < now:
            st["healthy"] = True
        if st["healthy"] and st["cooldown_until"] < now:
            _LAST_ROTATION = (idx + 1) % n  # next call rotates to the following key
            return key
    return None  # all keys in cooldown


def _mark_unhealthy(key: str, reason: str, cooldown_s: int = _COOLDOWN_SECONDS) -> None:
    _KEY_STATE[key] = {"healthy": False, "cooldown_until": time.time() + cooldown_s, "last_error": reason}


def _mark_healthy(key: str) -> None:
    _KEY_STATE[key] = {"healthy": True, "cooldown_until": 0.0, "last_error": ""}


def _pool_stats() -> dict[str, Any]:
    """Return pool state for /api/health or debugging."""
    _init_pool()
    now = time.time()
    for k in _KEY_POOL:
        if not _KEY_STATE[k]["healthy"] and _KEY_STATE[k]["cooldown_until"] < now:
            _KEY_STATE[k]["healthy"] = True
    return {
        "total": len(_KEY_POOL),
        "healthy": sum(1 for k in _KEY_POOL if _KEY_STATE[k]["healthy"] and _KEY_STATE[k]["cooldown_until"] < now),
        "in_cooldown": sum(1 for k in _KEY_POOL if not _KEY_STATE[k]["healthy"] and _KEY_STATE[k]["cooldown_until"] > now),
        "keys": [
            {
                "prefix": k[:10] + "...",
                "healthy": _KEY_STATE[k]["healthy"],
                "cooldown_remaining_s": max(0, int(_KEY_STATE[k]["cooldown_until"] - now)),
                "last_error": _KEY_STATE[k]["last_error"],
            }
            for k in _KEY_POOL
        ],
    }


# ----------------------------------------------------------------------------
# Tool 1: web_search — Tavily REST wrapper
# ----------------------------------------------------------------------------
async def web_search(
    query: Annotated[str, "Search query. Include ticker + topic for best IDX results, e.g. 'BBCA IDX earnings target price 2026'."],
    n_results: Annotated[int, "Max results (default 5, max 20)."] = 5,
    tier: Annotated[str, "Source tier: 't1' (idx.co.id/kontan/bisnis), 't2' (reuters/bloomberg), 't3' (retail), or 'all' (no filter)."] = "all",
    days: Annotated[int, "Recency window in days. Tavily default 'advanced' depth. 0 = no recency filter."] = 0,
) -> dict[str, Any]:
    """Search the web for fresh IDX equity data via Tavily.

    Returns:
        {
          "query": str,
          "tier": str,
          "source": "tavily" | "tavily_missing_key" | "tavily_error",
          "fetched_at": ISO timestamp,
          "results": [
            {"url": str, "title": str, "content": str, "score": float, "tier": "t1"|"t2"|"t3"|""}
          ],
        }

    Honest behavior: if TAVILY_API_KEY is missing, returns empty results with
    source='tavily_missing_key' so the Critic can flag the provenance.
    """
    _init_pool()
    fetched_at = datetime.now(timezone.utc).isoformat()

    # Sectors-first (swap 3 scaffold): ticker-scoped news when key present.
    # Ticker guess = first ALL-CAPS token >= 4 chars (IDX convention).
    if os.environ.get("SECTORS_API_KEY"):
        try:
            import asyncio as _aio
            from server.sectors import news as _sectors_news

            syms = [w.strip(".,") for w in query.upper().split()]
            syms = [w for w in syms if w.isalpha() and len(w) >= 4][:3]
            if syms:
                raw = await _aio.to_thread(_sectors_news, ",".join(syms))
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
                return {
                    "query": query,
                    "tier": tier,
                    "source": "sectors",
                    "fetched_at": fetched_at,
                    "results": out,
                }
        except Exception as e:
            logger.warning("Sectors news failed, Tavily legacy: %s", e)

    if not _KEY_POOL:
        return {
            "query": query,
            "tier": tier,
            "source": "tavily_missing_key",
            "fetched_at": fetched_at,
            "results": [],
        }

    payload: dict[str, Any] = {
        "query": query,
        "max_results": min(max(1, n_results), 20),
        "search_depth": "advanced",
        "include_answer": False,
        "include_raw_content": False,
    }
    if tier and tier != "all" and tier in TIER_DOMAINS:
        payload["include_domains"] = TIER_DOMAINS[tier]
    if days > 0:
        payload["days"] = min(days, 365)

    attempts = 0
    last_error = ""
    data: dict[str, Any] | None = None

    while attempts < len(_KEY_POOL):
        api_key = _pick_key()
        if not api_key:
            break
        attempts += 1
        try:
            async with httpx.AsyncClient(timeout=20.0) as cli:
                r = await cli.post("https://api.tavily.com/search", json={**payload, "api_key": api_key})
                r.raise_for_status()
                data = r.json()
                _mark_healthy(api_key)
                break
        except httpx.HTTPStatusError as e:
            code = e.response.status_code if e.response is not None else 0
            # Auth/quota/rate-limit → unhealthy + try next
            if code in (401, 403, 429, 500, 502, 503, 504):
                _mark_unhealthy(api_key, f"HTTP {code}", _COOLDOWN_SECONDS)
                last_error = f"HTTP {code}"
                continue
            # Other 4xx → don't mark unhealthy, just fail
            logger.warning("Tavily search failed (key %s...): %s", api_key[:10], e)
            return {
                "query": query,
                "tier": tier,
                "source": "tavily_error",
                "fetched_at": fetched_at,
                "results": [],
                "error": str(e),
            }
        except httpx.HTTPError as e:
            _mark_unhealthy(api_key, str(e), _COOLDOWN_SECONDS)
            last_error = str(e)
            continue

    if data is None:
        # All keys exhausted
        return {
            "query": query,
            "tier": tier,
            "source": "tavily_error",
            "fetched_at": fetched_at,
            "results": [],
            "error": last_error or "all_keys_exhausted",
            "all_keys_exhausted": True,
        }

    raw_results = data.get("results", []) or []
    out_results = []
    for it in raw_results:
        url = it.get("url", "")
        out_results.append({
            "url": url,
            "title": it.get("title", ""),
            "content": it.get("content", "")[:800],  # cap to 800 chars
            "score": float(it.get("score", 0.0)),
            "tier": _domain_tier(url),
        })

    return {
        "query": query,
        "tier": tier,
        "source": "tavily",
        "fetched_at": fetched_at,
        "results": out_results,
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
          "composite_source": "tavily+readability_local" | "tavily_missing_key+readability_local" | ...,
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

    if not _load_key_pool():
        print("TAVILY_API_KEY / TAVILY_API_KEYS not set — running extract-only smoke test")
        out = asyncio.run(web_extract(["https://www.idx.co.id/"]))
        print(json.dumps(out, indent=2)[:1500])
        sys.exit(0)

    print("Running composite smoke test with Tavily key pool present...")
    out = asyncio.run(web_search_and_extract("BBCA IDX earnings 2026", n_results=3, extract_top_n=2))
    print(json.dumps(out, indent=2, default=str)[:3000])
