"""
News Harvester Engine — scripts/news.py
Part of Multi-Agent Intake (plan.md §3, §4, §11). 0 Sectors credit.

LOUD POLICY (Sep 2026): CURATED_NEWS was KILLED (now {}) — the 8 hand-written
items lived here and are gone. search_news() returns [] until a live source
wires in. Downstream must surface real provenance, never bare outlet names.

Filters and tiers news items:
- Tier 1: idx.co.id, kontan.co.id, bisnis.com, idxchannel.com, cnbcindonesia.com, investor.id
- Tier 2: reuters.com, bloomberg.com, thejakartapost.com
- Tier 3: General financial media
Output: list of {url, date, title, source, snippet, tier, relevance}
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

CURATED_NEWS: Dict[str, List[Dict[str, Any]]] = {}
# KILLED (Sep 2026, no-fabrication sweep): the 8 hand-written items lived here
# (RATU/CDIA/MTEL/BBCA/ADRO with plausible-but-unverifiable urls + numeric
# claims). search_news() below returns [] for every ticker until a live
# Sectors/IDX source wires in. Do not re-add hand-written news.


async def search_news(ticker: str, days: int = 30, limit: int = 8) -> List[Dict[str, Any]]:
    """Fetches citable news items for ticker with verified provenance (0 credit).

    LOUD policy: CURATED_NEWS was killed (Sep 2026) — always returns [] until
    a live Sectors/IDX source wires in. Never generates disclosure entries.
    """
    t = ticker.upper().strip()
    items = CURATED_NEWS.get(t, [])
    if not items:
        return []
    return [{**it, "provenance": "curated-unverified"} for it in items[:limit]]

