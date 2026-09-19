"""Forever-living cache + gate relocation (19 Sep 2026).

Two rules this file pins, both from Fadil's call after a fresh PDF shipped with a
missing chart and a "collect() failed offline" report:

1. **The cache is forever living.** A row written through `credit_policy.
   cache_ttl_seconds()` carries `NEVER_EXPIRES_AT`: not a miss under
   `SECTORS_STALE_OK=0`, not deletable by `prune_expired()`. Freezes are served
   regardless of mtime unless `FREEZE_TTL_DAYS` is set explicitly.

2. **A gate blocks upstream, never a disk read.** `SECTORS_OFFLINE=1` used to be
   checked inside `collect()` BEFORE the Sectors path was attempted (so a warm
   cache looked empty) and was not honoured at all in `server/sectors._get` (so
   the gate blocked cache reads through one caller while leaving upstream open to
   every other path, and the ADK tools handed back `data: []` for a warm cache).

Every upstream-proof assertion here monkeypatches `httpx.Client` to explode, so a
passing test is proof that no credit could have been spent.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from server.storage import NEVER_EXPIRES_AT, SectorsCache

DAY = 86400.0


class _StubSettings:
    """Keyed settings without touching ~/.config/sectors-be/env (no live billing)."""

    sectors_api_key = "test-key-not-live"
    sectors_base = "https://api.sectors.app/v2"


@pytest.fixture
def keyed(monkeypatch):
    """Pretend a key is configured; conftest already pinned _cache to a tmp DB."""
    import server.sectors as S

    monkeypatch.setattr(S, "get_settings", lambda: _StubSettings())
    return S


@pytest.fixture
def no_upstream(monkeypatch):
    """Any attempt to open an HTTP client raises - a passing test proves 0 credits."""
    import httpx

    def _boom(*args, **kwargs):  # noqa: ARG001
        raise AssertionError("UPSTREAM ATTEMPTED - a credit would have been burned")

    monkeypatch.setattr(httpx, "Client", _boom)
    monkeypatch.setattr(httpx, "get", _boom, raising=False)
    return _boom


# ── 1. forever-living cache ──────────────────────────────────────────────────

def test_default_cache_ttl_is_forever():
    from server.credit_policy import cache_ttl_seconds

    ttl = cache_ttl_seconds("/company/report/AMMN/")
    assert ttl > 50 * 365 * DAY, f"default TTL must be effectively forever, got {ttl}"


def test_cache_ttl_env_override_and_legacy_tiers(monkeypatch):
    from server.credit_policy import cache_ttl_seconds
    from server.sectors import _ttl_for

    monkeypatch.setenv("SECTORS_CACHE_TTL_DAYS", "2")
    assert cache_ttl_seconds("/daily/BBCA/") == pytest.approx(2 * DAY, rel=1e-6)

    monkeypatch.setenv("SECTORS_CACHE_TTL_DAYS", "tiers")
    assert cache_ttl_seconds("/daily/BBCA/") == _ttl_for("/daily/BBCA/")
    assert cache_ttl_seconds("/company/report/BBCA/") == _ttl_for("/company/report/BBCA/")


def test_forever_row_survives_strict_mode_and_prune(tmp_path, monkeypatch):
    cache = SectorsCache(db_path=str(tmp_path / "c.db"))
    cache.set("/daily/BBCA/", {"start": "x", "end": "y"}, {"data": [1]}, ttl_seconds=None)
    cache.set("/news/", {"symbols": "BBCA"}, {"data": []}, ttl_seconds=0)  # expires now

    import sqlite3
    row = cache.conn.execute("SELECT expires_at FROM sectors_cache LIMIT 5").fetchall()
    assert max(r[0] for r in row) == NEVER_EXPIRES_AT

    monkeypatch.setenv("SECTORS_STALE_OK", "0")  # strictest mode
    payload, hit = cache.get("/daily/BBCA/", {"start": "x", "end": "y"})
    assert hit is True, "a forever row must hit even under strict TTL mode"
    assert payload == {"data": [1]}

    time.sleep(0.05)
    deleted = cache.prune_expired()
    assert deleted <= 1, "prune may drop the ttl=0 row only"
    _, still_there = cache.get("/daily/BBCA/", {"start": "x", "end": "y"})
    assert still_there is True, "prune_expired must never delete a forever row"
    cache.close()


# ── 2. the gate moved to the transport layer ─────────────────────────────────

def test_offline_gate_serves_cache_hit_zero_credits(keyed, no_upstream, monkeypatch):
    """Warm cache + SECTORS_OFFLINE=1 -> the hit is served, nothing is billed."""
    S = keyed
    S._cache.set("/daily/BBCA/", {"start": "s", "end": "e"}, {"data": [{"close": 9000}]}, ttl_seconds=None)
    monkeypatch.setenv("SECTORS_OFFLINE", "1")

    out = S.daily("BBCA", "2026-06-01", "2026-08-30")  # drifted window on purpose
    assert out["data"] == [{"close": 9000}], "cache/window-substitute must win over the gate"
    assert out.get("_window_substituted") is True, "the substitution must stay disclosed"


def test_offline_gate_blocks_cold_endpoint_zero_credits(keyed, no_upstream, monkeypatch):
    S = keyed
    monkeypatch.setenv("SECTORS_OFFLINE", "1")

    with pytest.raises(S.SectorsError) as ei:
        S.company_report("BBCA", "valuation")
    assert ei.value.status == 599
    assert "sectors_offline_mode" in str(ei.value)


def test_window_substitute_wins_before_the_gate(keyed, no_upstream, monkeypatch):
    """Credit guard order: exact key -> window substitute -> gate -> upstream."""
    S = keyed
    S._cache.set("/foreign-flow/BBCA/", {"start": "old", "end": "old"}, {"data": [{"net": 1}]}, ttl_seconds=None)
    monkeypatch.setenv("SECTORS_OFFLINE", "1")

    out = S.foreign_flow("BBCA", "2026-01-01", "2026-03-31")
    assert out["data"] == [{"net": 1}]


# ── 3. collect() reads the cache while gated ─────────────────────────────────

@pytest.fixture
def isolated_collector(tmp_path, monkeypatch):
    """collect() with no freeze on disk and a tmp rendered-cache dir."""
    import agents.collector as C

    freeze = tmp_path / "ticker_fill"
    freeze.mkdir()
    legacy = tmp_path / "ammn_fill"
    legacy.mkdir()
    monkeypatch.setattr(C, "_LOCAL_FILL_DIR", freeze)
    monkeypatch.setattr(C, "_LEGACY_FILL_DIR", legacy)
    monkeypatch.setattr(C, "OUTPUT_DIR", tmp_path / "out")
    monkeypatch.setattr(C, "_WINDOW_ANCHOR", {"start": None, "end": None})
    return C


def test_collect_serves_sqlite_cache_under_offline(keyed, no_upstream, isolated_collector, monkeypatch):
    """The exact regression Fadil caught: gate on, cache warm -> collect() works."""
    C = isolated_collector
    S = keyed
    t = "ZZZZ"
    cache = S._cache
    cache.set(f"/company/report/{t}/", {"sections": "overview,financials,dividend"},
              {"symbol": t, "overview": {"symbol": t, "industry": "Test"}, "financials": []},
              ttl_seconds=None)
    cache.set(f"/financials/quarterly/{t}/", {"n_quarters": 8},
              {"data": [{"period": "2026Q1", "revenue": 1}]}, ttl_seconds=None)
    cache.set(f"/daily/{t}/", {"start": "s", "end": "e"},
              {"data": [{"date": "2026-09-18", "close": 1000, "volume": 5}]}, ttl_seconds=None)
    cache.set(f"/company/corporate-actions/{t}/", {}, {"dividend": []}, ttl_seconds=None)
    monkeypatch.setenv("SECTORS_OFFLINE", "1")

    payload = C.collect(t, use_cache=False)
    assert payload["source"] == "sectors", "a warm cache must serve under SECTORS_OFFLINE=1"
    assert len(payload["prices"] or []) == 1
    assert (payload.get("sectors_gaps") or []) == [], "no endpoint should have missed"


def test_collect_names_the_gate_when_cache_is_cold(keyed, no_upstream, isolated_collector, monkeypatch):
    C = isolated_collector
    monkeypatch.setenv("SECTORS_OFFLINE", "1")

    with pytest.raises(RuntimeError, match="sectors_offline_mode"):
        C.collect("QQQQ", use_cache=False)


def test_collect_partial_cache_still_renders(keyed, no_upstream, isolated_collector, monkeypatch):
    """3 of 4 endpoints warm: render what exists and NAME the gap (no collapse)."""
    C = isolated_collector
    S = keyed
    t = "YYYY"
    S._cache.set(f"/daily/{t}/", {"start": "s", "end": "e"},
                 {"data": [{"date": "2026-09-18", "close": 7, "volume": 1}]}, ttl_seconds=None)
    monkeypatch.setenv("SECTORS_OFFLINE", "1")

    payload = C.collect(t, use_cache=False)
    assert payload["source"] == "sectors"
    assert len(payload["prices"] or []) == 1
    gaps = payload.get("sectors_gaps") or []
    assert any("company_report" in g for g in gaps), f"the missing endpoint must be named, got {gaps}"


# ── 4. freezes are served forever unless FREEZE_TTL_DAYS says otherwise ──────

def _write_freeze(dirpath: Path, ticker: str, days_old: float) -> Path:
    p = dirpath / f"company_report_{ticker}_multisection.json"
    p.write_text(json.dumps({"symbol": ticker, "overview": {"symbol": ticker, "industry": "X"}}), encoding="utf-8")
    old = time.time() - days_old * DAY
    os.utime(p, (old, old))
    return p


def test_freeze_is_served_forever_by_default(tmp_path, monkeypatch):
    import agents.collector as C

    freeze = tmp_path / "ticker_fill"
    freeze.mkdir()
    legacy = tmp_path / "ammn_fill"
    legacy.mkdir()
    monkeypatch.setattr(C, "_LOCAL_FILL_DIR", freeze)
    monkeypatch.setattr(C, "_LEGACY_FILL_DIR", legacy)
    _write_freeze(freeze, "ZZZZ", days_old=45)

    out = C._ticker_fill_payload("ZZZZ")
    assert out is not None, "a 45-day-old freeze must still serve when FREEZE_TTL_DAYS is unset"
    assert out["freeze_age_days"] >= 44, "age must stay disclosed"
    assert out["source"] == "ticker_fill_freeze"


def test_freeze_ttl_env_restores_the_gate(tmp_path, monkeypatch):
    import agents.collector as C

    freeze = tmp_path / "ticker_fill"
    freeze.mkdir()
    legacy = tmp_path / "ammn_fill"
    legacy.mkdir()
    monkeypatch.setattr(C, "_LOCAL_FILL_DIR", freeze)
    monkeypatch.setattr(C, "_LEGACY_FILL_DIR", legacy)
    _write_freeze(freeze, "ZZZZ", days_old=8)

    assert C._ticker_fill_payload("ZZZZ") is not None
    monkeypatch.setenv("FREEZE_TTL_DAYS", "7")
    assert C._ticker_fill_payload("ZZZZ") is None, "FREEZE_TTL_DAYS=7 must refuse an 8-day freeze"


def test_cache_only_fill_tops_up_a_thin_freeze(tmp_path, monkeypatch):
    """A thin freeze (overview only) must not hide richer rows already on disk."""
    import agents.collector as C
    from server.storage import SectorsCache

    freeze = tmp_path / "ticker_fill"
    freeze.mkdir()
    legacy = tmp_path / "ammn_fill"
    legacy.mkdir()
    monkeypatch.setattr(C, "_LOCAL_FILL_DIR", freeze)
    monkeypatch.setattr(C, "_LEGACY_FILL_DIR", legacy)
    monkeypatch.setattr(C, "OUTPUT_DIR", tmp_path / "out")
    _write_freeze(freeze, "ZZZZ", days_old=30)  # overview only, 30 days old

    tmp_cache = SectorsCache(db_path=str(tmp_path / "fill.db"))
    tmp_cache.set("/daily/ZZZZ/", {"start": "s", "end": "e"},
                  {"data": [{"date": "2026-09-18", "close": 4242, "volume": 9}]}, ttl_seconds=None)
    tmp_cache.set("/financials/quarterly/ZZZZ/", {"n_quarters": 8},
                  {"data": [{"period": "2026Q1"}]}, ttl_seconds=None)
    monkeypatch.setattr("server.storage.SectorsCache", lambda *a, **k: tmp_cache)

    payload = C.collect("ZZZZ", use_cache=False)
    assert payload["source"] == "ticker_fill_freeze"
    assert payload["prices"][0]["close"] == 4242
    assert payload["prices_source"] == "sectors_cache"
    assert payload["financials"]["quarterly"][0]["period"] == "2026Q1"
    assert payload["financials_source"] == "sectors_cache"
    assert payload["_freeze_age_days"] >= 29


def test_foreign_flow_chart_survives_an_old_freeze(monkeypatch):
    """The exact chart that went missing from the 19 Sep PDF."""
    from server.report.industry_page import _foreign_flow_series

    repo = Path(__file__).resolve().parents[1]
    fill = repo / "output" / "cache" / "ticker_fill"
    fill.mkdir(parents=True, exist_ok=True)
    ticker = "ZZZZ"
    p = fill / f"foreign_flow_{ticker}_90d.json"
    p.write_text(json.dumps({"data": [
        {"date": "2026-09-01", "net_foreign_inflow": -1_000_000_000},
        {"date": "2026-09-02", "net_foreign_inflow": 2_000_000_000},
    ]}), encoding="utf-8")
    old = time.time() - 9 * DAY
    os.utime(p, (old, old))
    try:
        series = _foreign_flow_series({"meta": {"ticker": ticker}})
        assert series["available"] is True, f"9-day-old freeze must still chart, got {series}"
        assert series["values_bn"] == [-1.0, 2.0]
        assert "freeze 9 hari" in series["source"], "freshness must be disclosed in the source line"

        monkeypatch.setenv("FREEZE_TTL_DAYS", "7")
        gated = _foreign_flow_series({"meta": {"ticker": ticker}})
        assert gated["available"] is False
        assert "kedaluwarsa" in gated["source"]
    finally:
        p.unlink(missing_ok=True)


# ── 5. ADK tools no longer hand back empty data for a warm cache ─────────────

def test_adk_tool_precheck_does_not_short_circuit_on_gates(keyed, monkeypatch):
    from agents.adk.tools.sectors_financial_tools import _error_dict, _missing_key_dict

    # The tools import get_settings from server.config at call time.
    import server.config as CFG

    monkeypatch.setattr(CFG, "get_settings", lambda: _StubSettings())

    monkeypatch.setenv("SECTORS_OFFLINE", "1")
    monkeypatch.setenv("SECTORS_CACHE_ONLY", "1")
    assert _missing_key_dict("BBCA", "now") is None, (
        "gates must not pre-empt the call - the transport layer decides hit vs miss"
    )

    import server.sectors as S

    offline = _error_dict("BBCA", "now", S.SectorsError(599, "sectors_offline_mode: cold"))
    assert offline["source"] == "sectors_offline" and offline["data"] == []

    cache_only = _error_dict("BBCA", "now", S.SectorsError(599, "sectors_cache_only: cold"))
    assert cache_only["source"] == "sectors_cache_only"

    other = _error_dict("BBCA", "now", ValueError("boom"))
    assert other["source"] == "sectors_error"


def test_cache_only_gate_labels_itself_when_offline_is_absent(keyed, no_upstream, monkeypatch):
    """Both gates can be set; the restricted one must not hide the other's label.

    NOTE: importing the FastAPI app force-loads ~/.config/sectors-be/env, so a bare
    test run can inherit SECTORS_OFFLINE=1 from a previous test in the same process.
    Pin it off explicitly - this test is about CACHE_ONLY's own label.
    """
    S = keyed
    monkeypatch.delenv("SECTORS_OFFLINE", raising=False)
    monkeypatch.setenv("SECTORS_CACHE_ONLY", "1")

    with pytest.raises(S.SectorsError) as ei:
        S.quarterly("BBCA", 8)
    assert ei.value.status == 599
    assert "sectors_cache_only" in str(ei.value)
    assert "sectors_offline_mode" not in str(ei.value)
