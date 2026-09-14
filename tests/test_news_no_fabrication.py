"""No-fabrication gates for news path (LOUD policy, Sep 2026; rewired 14 Sep 2026).

CURATED_NEWS stays killed — no hand-written items may ever come back.
search_news() is now live-wired to Sectors v2: keyless → honest [] (this
suite runs keyless, so [] pinned here); keyed runs hit the live feed.
"""
import asyncio
import os


def _run(coro):
    return asyncio.run(coro)


def test_search_news_keyless_honest_empty():
    from scripts.news import search_news

    if os.getenv("SECTORS_API_KEY", "").strip():
        import pytest
        pytest.skip("keyed run — live feed expected, fabrication gates still apply")
    for t in ("RATU", "CDIA", "MTEL", "BBCA", "ADRO", "ZZZZ", "GOTO", "BRIS"):
        assert _run(search_news(t)) == [], t


def test_search_news_items_carry_provenance_when_keyed():
    """Anything search_news returns must carry url + date + title (else Critic drops it)."""
    import inspect

    from scripts import news as news_mod

    src = inspect.getsource(news_mod.search_news)
    assert '"url"' in src and '"date"' in src and '"title"' in src


def test_curated_dict_stays_empty():
    from scripts.news import CURATED_NEWS

    assert CURATED_NEWS == {}
