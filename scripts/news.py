"""
News Harvester Engine - scripts/news.py
Part of Multi-Agent Intake (plan.md §3, §4, §11). Live Sectors v2 news.

Rewired 14 Sep 2026: search_news() now calls server/sectors.py news()
(live Sectors v2 /news/ feed, extension=idx REQUIRED) instead of returning [].
Cache AMMN proves the feed carries real articles with url + timestamp + tags
(37KB, 30d window). Keyless → honest [] with source sectors_missing_key,
never synthetic.

Filters and tiers news items:
- Tier 1: idx.co.id, kontan.co.id, bisnis.com, idxchannel.com, cnbcindonesia.com, investor.id
- Tier 2: reuters.com, bloomberg.com, thejakartapost.com
- Tier 3: General financial media
Output: list of {url, date, title, source, snippet, tier, relevance}
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

CURATED_NEWS: Dict[str, List[Dict[str, Any]]] = {}
# KILLED (Sep 2026, no-fabrication sweep): the 8 hand-written items lived here
# (RATU/CDIA/MTEL/BBCA/ADRO with plausible-but-unverifiable urls + numeric
# claims). Do not re-add hand-written news - live Sectors feed below.

_TIER_MAP: Dict[str, List[str]] = {
    "T1": ["idx.co.id", "kontan.co.id", "bisnis.com", "idxchannel.com",
           "cnbcindonesia.com", "investor.id"],
    "T2": ["reuters.com", "bloomberg.com", "thejakartapost.com",
           "jakartaglobe.id", "nikkei.com"],
    "T3": ["stockbit.com", "ipotan.co.id", "infovesta.com", "bareksa.com"],
}


def _tier_for(url: str) -> str:
    from urllib.parse import urlparse

    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return ""
    if host.startswith("www."):
        host = host[4:]
    for tier, domains in _TIER_MAP.items():
        for d in domains:
            if host == d or host.endswith("." + d):
                return tier
    return ""


async def search_news(ticker: str, days: int = 30, limit: int = 8) -> List[Dict[str, Any]]:
    """Live Sectors v2 news for ticker with verified provenance.

    Keyless or error → [] (honest empty, callers label sectors_missing_key).
    Never fabricates.
    """
    from server.sectors import SectorsNotConfigured, news as _sectors_news

    t = ticker.upper().strip()
    if not t:
        return []
    end = date.today()
    start = end - timedelta(days=min(max(days, 1), 365))
    try:
        import asyncio as _aio

        raw = await _aio.to_thread(
            _sectors_news, t,
            start=start.isoformat(), end=end.isoformat(),
        )
    except SectorsNotConfigured:
        return []
    except Exception as e:
        logger.warning("search_news(%s) sectors error: %s", t, e)
        return []
    items = (raw or {}).get("data") or (raw or {}).get("results") or []
    out: List[Dict[str, Any]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        url = it.get("source") or it.get("url") or it.get("link") or ""
        body = it.get("body") or it.get("summary") or it.get("content") or ""
        dim = it.get("dimension") or {}
        score = (sum(float(v) for v in dim.values() if isinstance(v, (int, float)))
                 if isinstance(dim, dict) else 0.0)
        out.append({
            "url": url,
            "date": str(it.get("timestamp") or it.get("date") or "")[:10],
            "title": it.get("title", ""),
            "source": url,
            "snippet": str(body)[:800],
            "tier": _tier_for(url),
            "relevance": round(min(score / 16.0, 1.0), 2) if score else 0.5,
        })
        if len(out) >= max(1, limit):
            break
    return out
