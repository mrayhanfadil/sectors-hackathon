"""
Social Media Sentiment Engine - scripts/social.py
Part of Multi-Agent Intake (plan.md §3, §4, §11). 0 Sectors credit.

Retail narrative tracker across X, Reddit, and Stockbit.
Output: list of {platform, url, date, text, sentiment, score, relevance}
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

CURATED_SOCIAL: Dict[str, List[Dict[str, Any]]] = {}
# KILLED (Sep 2026, Sectors-only rule): hand-written stockbit/x/reddit items
# removed (unverifiable non-Sectors data). search_social() returns [] until a
# live Sectors-gated source wires in. Do not re-add hand-written social.


async def search_social(ticker: str, days: int = 14, limit: int = 8) -> List[Dict[str, Any]]:
    """Retail sentiment (0 credit) - KILLED Sep 2026, always returns [] until a
    live Sectors-gated source wires in. Never fabricates Stockbit/X/Reddit URLs."""
    return []

