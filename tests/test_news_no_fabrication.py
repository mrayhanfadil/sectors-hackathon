"""No-fabrication gates for news path (LOUD policy, Sep 2026).

Pins: CURATED_NEWS items served via search_news always carry
provenance="curated-unverified", and unknown tickers return []
(never a generated idx.co.id disclosure entry — that is fabrication).
"""

import asyncio


def _run(coro):
    return asyncio.run(coro)


def test_search_news_unknown_ticker_returns_empty():
    from scripts.news import search_news

    assert _run(search_news("ZZZZ")) == []
    assert _run(search_news("GOTO")) == []
    assert _run(search_news("BRIS")) == []


def test_search_news_curated_items_tagged_unverified():
    from scripts.news import search_news

    for t in ("RATU", "CDIA", "MTEL", "BBCA", "ADRO"):
        items = _run(search_news(t))
        assert items, f"expected curated items for {t}"
        for it in items:
            assert it.get("provenance") == "curated-unverified", it
            assert it.get("url") and it.get("date") and it.get("title"), it
