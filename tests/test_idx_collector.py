"""Test Sectors-backed collector (Lane E rewrite) — keyless honest behavior.

Legacy removed: no yfinance, no IDX Postgres stockdata, no silent fallbacks.
Keyless runs return labeled synthetic; keyed runs return source=sectors.
"""
import sys, json, os
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


def test_collect_keyless_honest_source():
    """Keyless collect() -> labeled synthetic (or local idx), never legacy vendors."""
    _keyless()
    from agents.collector import collect
    _clear("BBCA")
    data = collect("BBCA", use_cache=False)
    assert data["source"] in ("sectors", "synthetic", "idx"), f"source: {data.get('source')}"
    assert "today_idx" not in data, "legacy idx_db supplement must be gone"
    assert "sector_source" not in data or data.get("sector_source") != "idx_db"
    blob = json.dumps(data, default=str)
    assert "yfinance" not in blob, "legacy vendor leaked into payload"
    assert "stockdata:15437" not in blob, "legacy DB leaked into payload"
    print("PASS collect_keyless_honest_source")


def test_collect_unknown_ticker_is_labeled_synthetic():
    """Unknown ticker keyless -> synthetic fallback with honest seed note."""
    _keyless()
    from agents.collector import collect
    _clear("ZZZZZZ")
    data = collect("ZZZZZZ", use_cache=False)
    assert data["source"] == "synthetic", f"source: {data.get('source')}"
    assert "seed=42" in str(data.get("note", "")), f"note: {data.get('note')}"
    print("PASS collect_unknown_ticker_is_labeled_synthetic")


if __name__ == "__main__":
    test_try_sectors_keyless_returns_none()
    test_try_sectors_unknown_ticker_keyless()
    test_collect_keyless_honest_source()
    test_collect_unknown_ticker_is_labeled_synthetic()
    print("ALL COLLECTOR TESTS PASSED")
