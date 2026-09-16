# Copyright 2026 Sectors Hackathon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Tests for the Sectors gateway stats shim (legacy removed, Lane E).

Replaces the Tavily round-robin key pool tests: there is no third-party pool
anymore - _pool_stats reports the single Sectors gateway (key present or not).
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

# Ensure repo root on path so 'agents.adk.tools.web_tools' resolves
_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

import agents.adk.tools.web_tools as wt


@pytest.fixture(autouse=True)
def restore_env():
    """Ensure environment is isolated between tests and restored afterwards."""
    saved = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(saved)
    importlib.reload(wt)


def test_pool_stats_keyless_reports_empty_gateway():
    """No SECTORS_API_KEY → total 0, healthy 0, no key material."""
    os.environ.pop("SECTORS_API_KEY", None)
    os.environ.pop("TAVILY_API_KEY", None)
    os.environ.pop("TAVILY_API_KEYS", None)
    importlib.reload(wt)
    stats = wt._pool_stats()
    assert stats["total"] == 0
    assert stats["healthy"] == 0
    assert stats["in_cooldown"] == 0
    assert stats["gateway"] == "sectors"
    assert stats["keys"] == []


def test_pool_stats_keyed_masks_secret():
    """SECTORS_API_KEY set → total 1, prefix masked, no full key leaked."""
    os.environ["SECTORS_API_KEY"] = "k1_1234567890abcdef"
    os.environ.pop("TAVILY_API_KEY", None)
    os.environ.pop("TAVILY_API_KEYS", None)
    importlib.reload(wt)
    stats = wt._pool_stats()
    assert stats["total"] == 1
    assert stats["healthy"] == 1
    assert stats["in_cooldown"] == 0
    assert len(stats["keys"]) == 1
    entry = stats["keys"][0]
    assert entry["prefix"].endswith("...")
    assert entry["prefix"] == "k1_1234567..."
    assert "k1_1234567890abcdef" not in str(stats)
    assert entry["healthy"] is True


def test_legacy_tavily_pool_helpers_are_gone():
    """Legacy pool machinery must not exist anymore (fail loud if resurrected)."""
    for name in ("_KEY_POOL", "_KEY_STATE", "_LAST_ROTATION", "_COOLDOWN_SECONDS",
                 "_load_key_pool", "_init_pool", "_pick_key",
                 "_mark_unhealthy", "_mark_healthy"):
        assert not hasattr(wt, name), f"legacy helper still present: {name}"


def test_legacy_keys_do_not_enable_search():
    """TAVILY_API_KEY[S] without SECTORS_API_KEY → still sectors_missing_key."""
    import asyncio

    os.environ["TAVILY_API_KEY"] = "tvly-fake-key"
    os.environ["TAVILY_API_KEYS"] = "a,b,c"
    os.environ.pop("SECTORS_API_KEY", None)
    importlib.reload(wt)
    out = asyncio.run(wt.web_search("BBCA earnings", n_results=3))
    assert out["source"] == "sectors_missing_key"
    assert out["results"] == []


if __name__ == "__main__":
    failed = 0
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    saved = dict(os.environ)
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as e:
            failed += 1
            print(f"  FAIL  {t.__name__}: {type(e).__name__}: {e}")
        finally:
            os.environ.clear()
            os.environ.update(saved)
            importlib.reload(wt)
    print(f"\n{'='*50}\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
