# Copyright 2026 Sectors Hackathon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Tests for web_tools — Tavily search + local readability extract.

Three layers:
  1) Pure unit: domain tier classification, schema validation
  2) Behavioral: missing key → honest empty; bad key → tavily_error
  3) Live extract (network): kontan.co.id / wikipedia — skipped in CI without network

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

from agents.adk.tools.web_tools import (  # noqa: E402
    _domain_tier,
    TIER_DOMAINS,
    web_search,
    web_extract,
    web_search_and_extract,
)


# ----------------------------------------------------------------------------
# Unit tests — domain tier classification
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
# Behavioral — missing TAVILY_API_KEY returns honest empty
# ----------------------------------------------------------------------------
def test_web_search_missing_key_returns_empty():
    """No TAVILY_API_KEY → source=tavily_missing_key, empty results, no exception."""
    # Save and clear env
    saved = os.environ.pop("TAVILY_API_KEY", None)
    try:
        out = asyncio.run(web_search("BBCA earnings", n_results=3))
        assert out["source"] == "tavily_missing_key", f"expected tavily_missing_key, got {out['source']}"
        assert out["results"] == []
        assert "fetched_at" in out
    finally:
        if saved is not None:
            os.environ["TAVILY_API_KEY"] = saved


def test_web_search_bad_key_returns_tavily_error():
    """Bogus TAVILY_API_KEY → source=tavily_error (401), no exception."""
    saved = os.environ.get("TAVILY_API_KEY")
    os.environ["TAVILY_API_KEY"] = "dummy_key_12345_definitely_invalid"
    try:
        out = asyncio.run(web_search("BBCA earnings", n_results=3))
        assert out["source"] == "tavily_error", f"expected tavily_error, got {out['source']}"
        assert out["results"] == []
        assert "error" in out
        # Should be 401 unauthorized
        assert "401" in str(out["error"]) or "unauthorized" in str(out["error"]).lower()
    finally:
        if saved is None:
            os.environ.pop("TAVILY_API_KEY", None)
        else:
            os.environ["TAVILY_API_KEY"] = saved


def test_web_search_and_extract_missing_key():
    """Composite tool with no Tavily key → extract skipped, search empty, honest composite_source."""
    saved = os.environ.pop("TAVILY_API_KEY", None)
    try:
        out = asyncio.run(web_search_and_extract("BBCA", n_results=3, extract_top_n=2))
        assert out["search"]["source"] == "tavily_missing_key"
        assert out["extract"]["results"] == []
        assert out["composite_source"] == "tavily_missing_key+readability_local"
    finally:
        if saved is not None:
            os.environ["TAVILY_API_KEY"] = saved


def test_web_extract_ignores_non_http_urls():
    """Non-http URLs are silently dropped — no exception."""
    out = asyncio.run(web_extract(["file:///etc/passwd", "javascript:alert(1)", "not-a-url", "https://example.com"]))
    assert out["source"] == "readability_local"
    # Only the one https URL even attempts
    assert len(out["results"]) == 1
    assert out["results"][0]["url"] == "https://example.com"


# ----------------------------------------------------------------------------
# Live network test — only runs if explicitly enabled
# ----------------------------------------------------------------------------
def test_web_extract_live_kontan_skipped_without_network():
    """Opt-in live extract test. Skipped unless LIVE_WEB_TESTS=1."""
    if os.environ.get("LIVE_WEB_TESTS") != "1":
        print("    (skipped — set LIVE_WEB_TESTS=1 to run live network tests)")
        return  # graceful no-op when run as __main__ (no pytest)
    out = asyncio.run(web_extract(["https://www.kontan.co.id/"]))
    assert out["results"][0]["status"] == "ok"
    assert out["results"][0]["char_count"] > 0


# ----------------------------------------------------------------------------
# Tool registration smoke — FunctionTool compatibility
# ----------------------------------------------------------------------------
def test_web_search_live_with_real_key():
    """Live test — only runs if TAVILY_API_KEY is present AND set in env.

    Skipped silently otherwise (CI without secrets, or test isolation).
    Verifies source=tavily and at least 1 result returned.
    """
    if not os.environ.get("TAVILY_API_KEY"):
        print("    (skipped — TAVILY_API_KEY not in env)")
        return
    out = asyncio.run(web_search("BBCA earnings 2026", n_results=3))
    assert out["source"] == "tavily", f"expected tavily, got {out['source']}"
    assert len(out["results"]) > 0, "expected at least 1 result"
    assert all(r.get("url") for r in out["results"]), "all results must have url"


def test_function_tool_wraps_cleanly():
    """Verify all 3 tools can be wrapped by ADK FunctionTool without errors."""
    from google.adk.tools.function_tool import FunctionTool
    for fn in [web_search, web_extract, web_search_and_extract]:
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
