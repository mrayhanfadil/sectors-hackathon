"""Test Sectors-only collector (LOUD policy, Sep 2026) - no synthetic fallback.

Keyless runs raise RuntimeError(sectors_missing_key); keyed runs return
source=sectors. No yfinance, no IDX Postgres, no silent fallbacks, no seed-42.
"""
import sys, json, os

import pytest

sys.path.insert(0, "/home/fadil/projects/sectors-hackathon")

_CACHE = "/home/fadil/projects/sectors-hackathon/data/output/cache_collector_{t}.json"


def _clear(ticker: str) -> None:
    p = _CACHE.format(t=ticker)
    if os.path.exists(p):
        os.remove(p)


def _keyless() -> None:
    os.environ.pop("SECTORS_API_KEY", None)


def test_try_sectors_keyless_returns_none():
    """Keyless Sectors -> _try_sectors returns None (honest, no exception, no legacy)."""
    _keyless()
    from agents.collector import _try_sectors
    r = _try_sectors("BBCA")
    assert r is None, f"Expected None keyless, got {r}"
    print("PASS try_sectors_keyless_returns_none")


def test_try_sectors_unknown_ticker_keyless():
    _keyless()
    from agents.collector import _try_sectors
    r = _try_sectors("ZZZZZZ")
    assert r is None, f"Expected None for unknown ticker keyless, got {r}"
    print("PASS try_sectors_unknown_ticker_keyless")


def test_collect_keyless_raises_loud():
    """Keyless collect() with no IDX dump -> RuntimeError naming sectors_missing_key."""
    _keyless()
    from agents.collector import collect
    _clear("BBCA")
    with pytest.raises(RuntimeError, match="sectors_missing_key"):
        collect("BBCA", use_cache=False)
    print("PASS collect_keyless_raises_loud")


def test_collect_unknown_ticker_keyless_raises_loud():
    """Unknown ticker keyless -> RuntimeError, never invented company."""
    _keyless()
    from agents.collector import collect
    _clear("ZZZZZZ")
    with pytest.raises(RuntimeError, match="sectors_missing_key"):
        collect("ZZZZZZ", use_cache=False)
    print("PASS collect_unknown_ticker_keyless_raises_loud")


def test_synthetic_generator_retired():
    """_synthetic() raises - seed-42 invention is gone."""
    from agents.collector import _synthetic
    with pytest.raises(RuntimeError, match="synthetic fallback retired"):
        _synthetic("BBCA")
    print("PASS synthetic_generator_retired")


if __name__ == "__main__":
    test_try_sectors_keyless_returns_none()
    test_try_sectors_unknown_ticker_keyless()
    test_collect_keyless_raises_loud()
    test_collect_unknown_ticker_keyless_raises_loud()
    test_synthetic_generator_retired()
    print("ALL COLLECTOR TESTS PASSED")
