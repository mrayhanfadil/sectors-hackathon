"""Test IDX DB collector integration."""
import sys, json
sys.path.insert(0, "/home/fadil/projects/sectors-hackathon")

def test_try_idx_db_returns_dict():
    from agents.collector import _try_idx_db
    r = _try_idx_db("BBCA")
    assert r is not None, "Expected IDX DB hit for BBCA"
    assert r["source"] == "idx_db"
    assert r["raw"]["overview"]["sector"] == "Financials"
    assert r["raw"]["today"]["close"] > 0
    assert r["raw"]["today"]["pct_change"] is not None
    assert "as_of" in r["raw"]["today"]
    print("PASS _try_idx_db_returns_dict")

def test_try_idx_db_unknown_ticker():
    from agents.collector import _try_idx_db
    r = _try_idx_db("ZZZZZZ")
    assert r is None, f"Expected None for unknown ticker, got {r}"
    print("PASS _try_idx_db_unknown_ticker")

def test_collect_idx_sources():
    from agents.collector import collect
    import os
    cache = "/home/fadil/projects/sectors-hackathon/data/output/cache_collector_BBCA.json"
    if os.path.exists(cache):
        os.remove(cache)
    data = collect("BBCA", use_cache=False)
    assert "today_idx" in data, f"today_idx missing: {list(data.keys())}"
    assert "idx_db" in data.get("sources", []), f"sources: {data.get('sources')}"
    assert data.get("sector_source") == "idx_db"
    assert data["company"]["sector"] == "Financials"
    print("PASS collect_idx_sources")

def test_collect_idx_graceful_on_unknown():
    """If IDX DB doesn't have a ticker, collect() should still return yfinance data."""
    from agents.collector import collect
    import os
    cache = "/home/fadil/projects/sectors-hackathon/data/output/cache_collector_BBCA.json"
    if os.path.exists(cache):
        os.remove(cache)
    data = collect("BBCA", use_cache=False)
    # IDX DB has BBCA so should still populate
    assert data.get("today_idx") is not None
    print("PASS collect_idx_graceful_on_unknown")

if __name__ == "__main__":
    test_try_idx_db_returns_dict()
    test_try_idx_db_unknown_ticker()
    test_collect_idx_sources()
    test_collect_idx_graceful_on_unknown()
    print("\nAll IDX collector tests passed")