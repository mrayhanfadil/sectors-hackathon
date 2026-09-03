# Copyright 2026 Sectors Hackathon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Tests for Tavily round-robin key pool failover and cooldown management."""

from __future__ import annotations

import importlib
import os
import sys
import time
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


def test_load_pool_multi():
    """Test 1: Load multiple comma-separated keys from TAVILY_API_KEYS."""
    os.environ["TAVILY_API_KEYS"] = "k1,k2,k3,k4"
    os.environ.pop("TAVILY_API_KEY", None)
    # Force reload (the module caches the pool)
    importlib.reload(wt)
    pool = wt._load_key_pool()
    assert pool == ["k1", "k2", "k3", "k4"]


def test_load_pool_single_fallback():
    """Test 2: Fallback to single TAVILY_API_KEY when TAVILY_API_KEYS is unset."""
    os.environ["TAVILY_API_KEY"] = "k_old"
    os.environ.pop("TAVILY_API_KEYS", None)
    importlib.reload(wt)
    assert wt._load_key_pool() == ["k_old"]


def test_load_pool_empty():
    """Test 3: Empty pool when neither env var is set."""
    os.environ.pop("TAVILY_API_KEYS", None)
    os.environ.pop("TAVILY_API_KEY", None)
    importlib.reload(wt)
    assert wt._load_key_pool() == []


def test_pick_key_round_robin():
    """Test 4: Round-robin rotation across healthy keys."""
    os.environ["TAVILY_API_KEYS"] = "a,b,c"
    os.environ.pop("TAVILY_API_KEY", None)
    importlib.reload(wt)
    picks = [wt._pick_key() for _ in range(6)]
    # Should cycle: a, b, c, a, b, c (round-robin increments after each pick)
    assert picks == ["a", "b", "c", "a", "b", "c"]


def test_pick_key_skips_unhealthy():
    """Test 5: Skip keys in cooldown and pick the healthy ones."""
    os.environ["TAVILY_API_KEYS"] = "a,b,c"
    os.environ.pop("TAVILY_API_KEY", None)
    importlib.reload(wt)
    wt._mark_unhealthy("a", "test 401", cooldown_s=60)
    wt._mark_unhealthy("b", "test 429", cooldown_s=60)
    # Next 3 picks should all be "c"
    picks = [wt._pick_key() for _ in range(3)]
    assert picks == ["c", "c", "c"]


def test_pick_key_returns_none_when_all_cooldown():
    """Test 6: Return None when all keys are in cooldown."""
    os.environ["TAVILY_API_KEYS"] = "a,b"
    os.environ.pop("TAVILY_API_KEY", None)
    importlib.reload(wt)
    wt._mark_unhealthy("a", "test", cooldown_s=60)
    wt._mark_unhealthy("b", "test", cooldown_s=60)
    assert wt._pick_key() is None


def test_pool_stats_summary():
    """Test 7: Pool stats reporting total, healthy, cooldown, and masked keys."""
    os.environ["TAVILY_API_KEYS"] = "k1_1234567890,k2_1234567890,k3_1234567890"
    os.environ.pop("TAVILY_API_KEY", None)
    importlib.reload(wt)
    wt._mark_unhealthy("k2_1234567890", "rate limit", cooldown_s=60)
    stats = wt._pool_stats()
    assert stats["total"] == 3
    assert stats["healthy"] == 2
    assert stats["in_cooldown"] == 1
    assert len(stats["keys"]) == 3
    # Keys are exposed only as 10-char prefixes for safety
    for entry in stats["keys"]:
        assert entry["prefix"].endswith("...")
        assert len(entry["prefix"]) == 13  # 10 chars + "..."


def test_health_recovery_after_cooldown():
    """Test 8: Key becomes healthy again once cooldown expires."""
    os.environ["TAVILY_API_KEYS"] = "k1"
    os.environ.pop("TAVILY_API_KEY", None)
    importlib.reload(wt)
    wt._mark_unhealthy("k1", "test", cooldown_s=1)
    assert wt._pick_key() is None
    time.sleep(1.1)
    # Cooldown expired → key is healthy again
    assert wt._pick_key() == "k1"


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
