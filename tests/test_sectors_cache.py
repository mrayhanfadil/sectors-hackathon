"""Sectors payload cache - minimize Sectors API credit burn.

Round-trip tests against server.storage.SectorsCache. Uses a per-test tmp DB
so a populated cache never bleeds across tests. No fixture, no Sectors key
needed - these tests target the cache class directly.

Gate: every assertion is on the cache layer itself. The Sectors API is wrapped
transparently in production; one Sectors _get() call -> one credit saved on hit.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

import pytest

from server.storage import SectorsCache


@pytest.fixture
def cache(tmp_path: Path) -> SectorsCache:
    """Fresh per-test DB so cache hits/misses don't bleed."""
    return SectorsCache(db_path=str(tmp_path / "sectors_cache.db"))


def test_round_trip_set_get_returns_payload(cache: SectorsCache) -> None:
    payload = {"sectors": ["BBCA", "BBRI"], "score": 0.91}
    cache.set("/company/peers/", {"symbol": "BBCA"}, payload, ttl_seconds=3600)
    out, hit = cache.get("/company/peers/", {"symbol": "BBCA"})
    assert hit is True, "freshly-set entry must hit"
    assert out == payload, "round-trip must preserve payload bytes-equal"


def test_key_is_stable_under_param_reorder(cache: SectorsCache) -> None:
    payload1 = {"id": 1}
    cache.set("/company/quarterly-financials/", {"symbol": "BBCA", "n_quarters": 8}, payload1, ttl_seconds=3600)
    out, hit = cache.get("/company/quarterly-financials/", {"n_quarters": 8, "symbol": "BBCA"})
    assert hit is True, "param-order must not change cache key"
    assert out == payload1


def test_distinct_params_distinct_keys(cache: SectorsCache) -> None:
    cache.set("/transaction/daily/", {"symbol": "BBCA"}, {"a": 1}, ttl_seconds=3600)
    cache.set("/transaction/daily/", {"symbol": "BBRI"}, {"a": 2}, ttl_seconds=3600)
    out_a, hit_a = cache.get("/transaction/daily/", {"symbol": "BBCA"})
    out_b, hit_b = cache.get("/transaction/daily/", {"symbol": "BBRI"})
    assert hit_a and hit_b
    assert out_a == {"a": 1} and out_b == {"a": 2}


def test_expired_entry_serves_stale_by_default(cache: SectorsCache) -> None:
    """NO-EXPIRY (15 Sep 2026, credit-thin mode): cached rows NEVER expire -
    TTL=0 + sleep, then get() must still HIT with _stale flag."""
    import os

    os.environ.pop("SECTORS_STALE_OK", None)
    payload = {"expired": True}
    cache.set("/news/news/", {"symbols": "BBCA"}, payload, ttl_seconds=0)
    # Sleep one full second so expires_at <= now.
    time.sleep(1.05)
    out, hit = cache.get("/news/news/", {"symbols": "BBCA"})
    assert hit is True, "expired entry must serve stale by default (credit-thin mode)"
    assert out is not None and out.get("_stale") is True
    assert "expired" in out


def test_expired_entry_misses_under_strict_mode(cache: SectorsCache, monkeypatch) -> None:
    """SECTORS_STALE_OK=0 restores strict expiry (fresh pull, burns credit)."""
    monkeypatch.setenv("SECTORS_STALE_OK", "0")
    payload = {"expired": True}
    cache.set("/news/news/", {"symbols": "BBCA"}, payload, ttl_seconds=0)
    time.sleep(1.05)
    out, hit = cache.get("/news/news/", {"symbols": "BBCA"})
    assert hit is False, "strict mode: expired entry must be a miss"
    assert out is None


def test_bust_endpoint_prefix_only(cache: SectorsCache) -> None:
    cache.set("/news/news/", {"symbols": "BBCA"}, {}, ttl_seconds=3600)
    cache.set("/news/news/", {"symbols": "BBRI"}, {}, ttl_seconds=3600)
    cache.set("/company/quarterly-financials/", {"symbol": "BBCA"}, {}, ttl_seconds=3600)
    n = cache.bust(endpoint_prefix="/news/news/")
    assert n == 2, "prefix-bust must delete only matching endpoint family"
    out, hit = cache.get("/company/quarterly-financials/", {"symbol": "BBCA"})
    assert hit is True, "non-matching endpoint must survive prefix-bust"


def test_bust_all_returns_total_count(cache: SectorsCache) -> None:
    for i in range(5):
        cache.set("/ipo/listing-performance/", {"symbol": f"T{i}"}, {}, ttl_seconds=3600)
    n = cache.bust()
    assert n == 5, "unbounded bust must delete all entries"
    s = cache.stats()
    assert s["n_entries"] == 0, "unbounded bust must empty the cache"


def test_stats_groups_by_endpoint(cache: SectorsCache) -> None:
    cache.set("/company/quarterly-financials/", {"symbol": "BBCA"}, {}, ttl_seconds=3600)
    cache.set("/company/quarterly-financials/", {"symbol": "BBRI"}, {}, ttl_seconds=3600)
    cache.set("/news/news/", {"symbols": "BBCA"}, {}, ttl_seconds=3600)
    s = cache.stats()
    assert s["n_entries"] == 3
    by_ep = {row["endpoint"]: row["n"] for row in s["by_endpoint"]}
    assert by_ep.get("/company/quarterly-financials/") == 2
    assert by_ep.get("/news/news/") == 1


def test_prune_expired_removes_only_past_entries(cache: SectorsCache) -> None:
    cache.set("/ipo/listing-performance/", {"symbol": "ALIVE"}, {}, ttl_seconds=3600)
    cache.set("/ipo/listing-performance/", {"symbol": "DEAD"}, {}, ttl_seconds=0)
    time.sleep(1.05)
    n = cache.prune_expired()
    assert n == 1, "only the expired row should be pruned"
    out, hit = cache.get("/ipo/listing-performance/", {"symbol": "ALIVE"})
    assert hit is True, "live entry must survive pruning"


def test_set_overwrites_existing_key(cache: SectorsCache) -> None:
    """Same key + different payload = upsert (ON CONFLICT DO UPDATE)."""
    cache.set("/ipo/listing-performance/", {"symbol": "CDIA"}, {"v": 1}, ttl_seconds=3600)
    cache.set("/ipo/listing-performance/", {"symbol": "CDIA"}, {"v": 2}, ttl_seconds=3600)
    out, hit = cache.get("/ipo/listing-performance/", {"symbol": "CDIA"})
    assert hit is True
    assert out["v"] == 2, "set() with same key must overwrite payload"


def test_endpoint_classification_tiers():
    """TTL classification honors the 4-tier policy in server/sectors.py."""
    from server.sectors import _ttl_for

    # TIER 1 - intra-day (6h)
    assert _ttl_for("/daily/BBCA/") == 6 * 3600
    assert _ttl_for("/foreign-flow/BBCA/") == 6 * 3600
    # TIER 2 - fundamentals/news (12h)
    assert _ttl_for("/financials/quarterly/BBCA/") == 12 * 3600
    assert _ttl_for("/news/") == 12 * 3600
    # TIER 3 - slow-moving (24h)
    assert _ttl_for("/subsector/report/banks/") == 24 * 3600
    assert _ttl_for("/companies/") == 24 * 3600
    # Universe feed (4h)
    assert _ttl_for("/close/") == 4 * 3600
    # Catch-all (default)
    assert _ttl_for("/completely/new/path/") == 6 * 3600


def test_persistence_across_sessions(tmp_path: Path) -> None:
    """Two cache instances on same DB file must share state - proves SQLite
    actually persists (not in-memory). Without this, the whole storage layer
    is just a more complicated cache.py."""
    db = str(tmp_path / "persist_test.db")
    c1 = SectorsCache(db_path=db)
    c1.set("/ipo/listing-performance/", {"symbol": "PERSIST"}, {"hello": "world"}, ttl_seconds=3600)
    c1.close()
    c2 = SectorsCache(db_path=db)
    out, hit = c2.get("/ipo/listing-performance/", {"symbol": "PERSIST"})
    assert hit is True
    assert out == {"hello": "world"}


def test_cache_does_not_store_errors(tmp_path: Path) -> None:
    """When Sectors returns 4xx/5xx we raise - nothing must land in the cache,
    so the next call retries the API."""
    cache = SectorsCache(db_path=str(tmp_path / "no_err_cache.db"))
    # Simulate the cache-miss path: nothing was set, get returns no-hit.
    out, hit = cache.get("/ipo/listing-performance/", {"symbol": "MISS"})
    assert hit is False
    assert out is None
    # Confirm stats reflect zero entries (errors must NOT pollute the table).
    assert cache.stats()["n_entries"] == 0


# ──────────────────────────────────────────────────────────────────────────────
# Window-drift credit guard (15 Sep 2026).
#
# Incident: collector asked foreign_flow/index_daily for a window 10 days off
# the cached one → distinct cache keys → 2 fresh credits per run, every run.
# Guard: once a date-windowed endpoint has ANY cached row, a drifted window is
# served from cache (disclosed via _window_substituted) instead of billed again.
# ──────────────────────────────────────────────────────────────────────────────

def test_latest_for_endpoint_serves_freshest_row_any_params(cache: SectorsCache) -> None:
    cache.set("/foreign-flow/AMMN/", {"start": "2026-06-01", "end": "2026-09-06"},
              {"data": [1]}, ttl_seconds=3600)
    time.sleep(0.02)
    cache.set("/foreign-flow/AMMN/", {"start": "2026-05-01", "end": "2026-08-06"},
              {"data": [2]}, ttl_seconds=3600)
    got = cache.latest_for_endpoint("/foreign-flow/AMMN/")
    assert got is not None, "endpoint with rows must resolve"
    payload, meta = got
    assert payload == {"data": [2]}, "must serve the FRESHEST row, not the first"
    assert meta["fetched_at"] > 0, "provenance timestamp must travel with the payload"


def test_latest_for_endpoint_ignores_neg404_markers(cache: SectorsCache) -> None:
    """A cached 404 is an error marker, never data - must not be served."""
    cache.set("/company/get-segments/AMMN/", {}, {"data": [], "_neg404": True}, ttl_seconds=3600)
    assert cache.latest_for_endpoint("/company/get-segments/AMMN/") is None


def test_latest_for_endpoint_absent_returns_none(cache: SectorsCache) -> None:
    assert cache.latest_for_endpoint("/never/fetched/") is None


def test_window_drift_serves_cache_and_never_calls_http(monkeypatch) -> None:
    """THE guarantee: a drifted date window costs 0 credits once the endpoint
    is cached. HTTP must not be touched, and the substitution is disclosed."""
    import server.sectors as S

    S._cache.set("/foreign-flow/AMMN/", {"start": "2026-06-01", "end": "2026-09-06"},
                 {"data": [{"n": 1}]}, ttl_seconds=3600)

    def _boom(*_a, **_k):
        raise AssertionError("HTTP must not fire when a cached row exists")

    monkeypatch.setattr(S.httpx, "Client", _boom)
    out = S._get("/foreign-flow/AMMN/", {"start": "2026-06-17", "end": "2026-09-15"},
                 allow_window_substitute=True)
    assert out["_window_substituted"] is True, "drift must be disclosed"
    assert out["_requested_params"] == {"start": "2026-06-17", "end": "2026-09-15"}
    assert out["data"] == [{"n": 1}]
    assert out["_cached_fetched_at"], "caller must be able to show the real as-of date"


def test_exact_params_still_hit_without_substitution_flag(monkeypatch) -> None:
    """Substitution is a fallback, not the norm - same params = plain cache HIT."""
    import server.sectors as S

    S._cache.set("/index-daily/ihsg/", {"start": "2021-01-01", "end": "2026-09-06"},
                 {"data": [{"close": 7000}]}, ttl_seconds=3600)
    out = S._get("/index-daily/ihsg/", {"start": "2021-01-01", "end": "2026-09-06"},
                 allow_window_substitute=True)
    assert "_window_substituted" not in out, "exact hit must not be flagged as substituted"
    assert out["data"] == [{"close": 7000}]


@pytest.mark.skipif(os.getenv("SECTORS_LIVE") == "1", reason="keyless-only assertion")
def test_window_guard_is_opt_in_per_endpoint(monkeypatch) -> None:
    """Non-window endpoints (e.g. /close/{date}) must NOT inherit the guard -
    a different date there is genuinely different data."""
    import server.sectors as S
    from server.sectors import SectorsNotConfigured

    S._cache.set("/close/", {"date": "2026-09-15"}, {"data": []}, ttl_seconds=3600)
    with pytest.raises(SectorsNotConfigured):
        S._get("/close/", {"date": "2026-09-16"})  # no allow_window_substitute → live path


@pytest.mark.skipif(os.getenv("SECTORS_LIVE") == "1", reason="keyless-only assertion")
def test_window_guard_disabled_by_env(monkeypatch) -> None:
    """SECTORS_WINDOW_SUBSTITUTE=0 is the documented escape hatch (strict keys)."""
    import server.sectors as S
    from server.sectors import SectorsNotConfigured

    S._cache.set("/foreign-flow/AMMN/", {"start": "2026-06-01", "end": "2026-09-06"},
                 {"data": []}, ttl_seconds=3600)
    monkeypatch.setenv("SECTORS_WINDOW_SUBSTITUTE", "0")
    with pytest.raises(SectorsNotConfigured):
        S._get("/foreign-flow/AMMN/", {"start": "2026-06-17"}, allow_window_substitute=True)
