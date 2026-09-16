# Copyright 2026 Sectors Hackathon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Tests for web_tools - Sectors search only (extract killed Sep 2026, Sectors-only rule).

Two layers:
  1) Pure unit: domain tier classification, schema validation
  2) Behavioral: missing key → sectors_missing_key honest empty; legacy keys ignored

Run: .venv/bin/python -m pytest agents/adk/tests/test_web_tools.py -v
Or:  .venv/bin/python agents/adk/tests/test_web_tools.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Ensure repo root on path so 'agents.adk.tools.web_tools' resolves
_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from agents.adk.tools.web_tools import _domain_tier, TIER_DOMAINS, web_search  # noqa: E402


# ----------------------------------------------------------------------------
# Unit tests - domain tier classification
# ----------------------------------------------------------------------------
def test_domain_tier_t1_indonesian_official():
    assert _domain_tier("https://www.idx.co.id/news") == "t1"
    assert _domain_tier("https://kontan.co.id/article/123") == "t1"
    assert _domain_tier("https://bisnis.com/finance/x") == "t1"
    assert _domain_tier("https://idxchannel.com/article") == "t1"
    assert _domain_tier("https://cnbcindonesia.com/market") == "t1"
    assert _domain_tier("https://investor.id/market") == "t1"


def test_domain_tier_t2_international():
    assert _domain_tier("https://reuters.com/article") == "t2"
    assert _domain_tier("https://bloomberg.com/news/x") == "t2"
    assert _domain_tier("https://www.thejakartapost.com/x") == "t2"


def test_domain_tier_t3_retail():
    assert _domain_tier("https://stockbit.com/post/123") == "t3"
    assert _domain_tier("https://ipotan.co.id/x") == "t3"


def test_domain_tier_unknown_returns_empty():
    assert _domain_tier("https://random-blog.com/x") == ""
    assert _domain_tier("https://not-a-domain") == ""


def test_domain_tier_strips_www():
    assert _domain_tier("https://www.kontan.co.id/x") == "t1"
    assert _domain_tier("https://www.reuters.com/x") == "t2"


# ----------------------------------------------------------------------------
# Behavioral - missing SECTORS_API_KEY returns honest empty (legacy removed)
# ----------------------------------------------------------------------------
def test_web_search_missing_key_returns_empty():
    """No SECTORS_API_KEY → source=sectors_missing_key, empty results, no exception."""
    saved = os.environ.pop("SECTORS_API_KEY", None)
    try:
        out = asyncio.run(web_search("BBCA earnings", n_results=3))
        assert out["source"] == "sectors_missing_key", f"expected sectors_missing_key, got {out['source']}"
        assert out["results"] == []
        assert "fetched_at" in out
    finally:
        if saved is not None:
            os.environ["SECTORS_API_KEY"] = saved


def test_web_search_legacy_keys_ignored():
    """Bogus TAVILY_API_KEY[S] are ignored - Sectors gateway only, honest empty keyless."""
    saved_single = os.environ.pop("TAVILY_API_KEY", None)
    saved_multi = os.environ.pop("TAVILY_API_KEYS", None)
    saved_sectors = os.environ.pop("SECTORS_API_KEY", None)
    os.environ["TAVILY_API_KEY"] = "dummy_key_12345_definitely_invalid"
    try:
        out = asyncio.run(web_search("BBCA earnings", n_results=3))
        assert out["source"] == "sectors_missing_key", f"expected sectors_missing_key, got {out['source']}"
        assert out["results"] == []
    finally:
        os.environ.pop("TAVILY_API_KEY", None)
        if saved_single is not None:
            os.environ["TAVILY_API_KEY"] = saved_single
        if saved_multi is not None:
            os.environ["TAVILY_API_KEYS"] = saved_multi
        if saved_sectors is not None:
            os.environ["SECTORS_API_KEY"] = saved_sectors
# Live network test - only runs if explicitly enabled
# Tool registration smoke - FunctionTool compatibility
# ----------------------------------------------------------------------------
def test_web_search_live_with_real_key():
    """Live test - only runs if SECTORS_API_KEY is set in env.

    Skipped silently otherwise (CI without secrets or test isolation).
    Verifies source=sectors and result schema.
    """
    if not os.environ.get("SECTORS_API_KEY"):
        print("    (skipped - no SECTORS_API_KEY in env)")
        return
    out = asyncio.run(web_search("BBCA earnings 2026", n_results=3))
    assert out["source"] == "sectors", f"expected sectors, got {out['source']}"
    assert all(r.get("url") is not None for r in out["results"]), "all results must have url key"


def test_web_search_maps_sectors_news_shape():
    """Sectors v2 news rows carry link in `source`, prose in `body`, time in
    `timestamp` - the tool must surface all three (plus dimension-sum score),
    not empty url/content with hardcoded 0.0."""
    from unittest import mock as _mock

    saved = os.environ.get("SECTORS_API_KEY")
    os.environ["SECTORS_API_KEY"] = "test_key_mapping_only"
    row = {
        "title": "UBS buys AMMN amid copper rally",
        "body": "UBS Sekuritas net-bought Rp92bn of AMMN shares.",
        "source": "https://www.bloombergtechnoz.com/detail-news/120995/x",
        "timestamp": "2026-09-09T09:17:00",
        "symbols": ["AMMN.JK"],
        "dimension": {"future": 0, "dividend": 0, "ownership": 1,
                      "technical": 1, "valuation": 2, "financials": 0,
                      "management": 0, "sustainability": 0},
    }
    fake_raw = {"results": [row],
                "pagination": {"total_count": 1}}
    try:
        with _mock.patch("server.sectors.news", return_value=fake_raw):
            out = asyncio.run(web_search("AMMN copper", n_results=5))
        assert out["source"] == "sectors", out["source"]
        assert len(out["results"]) == 1
        r = out["results"][0]
        assert r["url"] == row["source"], r["url"]
        assert "Rp92bn" in r["content"], r["content"]
        assert r["date"] == "2026-09-09", r["date"]
        assert r["symbols"] == ["AMMN.JK"], r["symbols"]
        assert r["score"] == 4.0, r["score"]
        assert r["tier"] == "", r["tier"]  # bloombergtechnoz not allowlisted
    finally:
        if saved is None:
            os.environ.pop("SECTORS_API_KEY", None)
        else:
            os.environ["SECTORS_API_KEY"] = saved


def test_function_tool_wraps_cleanly():
    """Verify web_search (sole survivor, Sectors-only) wraps cleanly."""
    from google.adk.tools.function_tool import FunctionTool
    for fn in [web_search]:
        ft = FunctionTool(fn)
        assert ft.name == fn.__name__
        assert ft.description  # non-empty


# ----------------------------------------------------------------------------
# Test runner
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    failed = 0
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as e:
            failed += 1
            print(f"  FAIL  {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{'='*50}\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
