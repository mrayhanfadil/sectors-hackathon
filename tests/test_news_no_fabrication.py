"""No-fabrication gates for news path (LOUD policy, Sep 2026).

CURATED_NEWS was killed — search_news returns [] for every ticker until a
live Sectors/IDX source wires in. These gates pin the empty behavior so no
hand-written or generated disclosure entry can ever come back silently.
"""

import asyncio


def _run(coro):
    return asyncio.run(coro)


def test_search_news_always_empty_until_live_source():
    from scripts.news import search_news

    for t in ("RATU", "CDIA", "MTEL", "BBCA", "ADRO", "ZZZZ", "GOTO", "BRIS"):
        assert _run(search_news(t)) == [], t


def test_curated_dict_stays_empty():
    from scripts.news import CURATED_NEWS

    assert CURATED_NEWS == {}
