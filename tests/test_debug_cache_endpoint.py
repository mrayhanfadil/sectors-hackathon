"""Tests for /api/debug/cache endpoints (Sectors payload cache surface).

Honest unit-style tests: assertions go through FastAPI TestClient against a
fresh app instance, no live Sectors API required. The cache layer is exercised
end-to-end (stats include real SectorsCache fields); bust/prune go against an
empty cache (keyless) and just verify they don't 500.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from server.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def isolated_client(tmp_path, monkeypatch) -> TestClient:
    """Fresh app wired to a tmp SQLite DB.

    The global app reads the PROD cache file, which legitimately holds
    rows (each one a billed credit) - emptiness assertions must never run
    against it.
    """
    from server.storage import SectorsCache
    import server.main as _M

    iso_path = str(tmp_path / "dbg-iso.db")
    monkeypatch.setattr(
        _M, "SectorsCache", lambda *a, **k: SectorsCache(db_path=iso_path)
    )
    return TestClient(_M.create_app())


def test_debug_cache_endpoint_returns_stats_shape(client: TestClient) -> None:
    """Keyless (no SECTORS_API_KEY in test env) - stats must still return."""
    r = client.get("/api/debug/cache")
    assert r.status_code == 200, f"got {r.status_code}: {r.text[:400]}"
    body = r.json()
    assert "n_entries" in body, "missing n_entries"
    assert "n_expired" in body, "missing n_expired"
    assert "by_endpoint" in body, "missing by_endpoint list"
    assert "db_path" in body, "debug endpoint should expose db_path"
    assert "fetched_at_iso" in body, "debug endpoint should expose fetched_at_iso"
    assert isinstance(body["by_endpoint"], list), "by_endpoint must be a list"


def test_debug_cache_empty_state_initial_values(
    isolated_client: TestClient,
) -> None:
    """First call from a fresh DB must see 0 entries (no Sectors data fetched)."""
    body = isolated_client.get("/api/debug/cache").json()
    assert body["n_entries"] == 0, "fresh DB must have 0 entries"
    assert body["n_expired"] == 0, "fresh DB must have 0 expired"


def test_debug_cache_bust_empty_returns_zero(
    isolated_client: TestClient,
) -> None:
    """Bust against empty cache must return deleted=0, not 500."""
    r = isolated_client.post("/api/debug/cache/bust")
    assert r.status_code == 200, f"got {r.status_code}: {r.text[:400]}"
    body = r.json()
    assert body["deleted"] == 0
    assert body["prefix"] is None


def test_debug_cache_bust_with_prefix_no_match(client: TestClient) -> None:
    """Bust with a prefix that doesn't match anything must still 200 cleanly."""
    r = client.post("/api/debug/cache/bust?prefix=/no/such/endpoint/")
    assert r.status_code == 200
    assert r.json()["deleted"] == 0


def test_debug_cache_prune_empty_returns_zero(isolated_client: TestClient) -> None:
    """Prune on an empty DB - no rows to delete - must be a 200, deleted=0.

    Runs against the isolated tmp DB, NOT the prod cache file: the prod cache
    legitimately holds expired rows (each one a billed credit), so asserting
    "deleted == 0" against it made this test order-dependent and red whenever
    a live run had left expired entries behind.
    """
    r = isolated_client.post("/api/debug/cache/prune")
    assert r.status_code == 200, f"got {r.status_code}: {r.text[:400]}"
    assert r.json()["deleted"] == 0


def test_debug_cache_prune_deletes_only_expired(tmp_path, isolated_client: TestClient) -> None:
    """Prune must drop expired rows, report the real count, and keep live ones.

    The fixture wires the app to tmp_path/"dbg-iso.db", so seeding through a
    SectorsCache on that same path exercises the real prune path end-to-end.
    """
    from server.storage import SectorsCache

    seed = SectorsCache(db_path=str(tmp_path / "dbg-iso.db"))
    seed.set("/v2/test/expired", None, {"x": 1}, ttl_seconds=-5)
    seed.set("/v2/test/live", None, {"x": 2}, ttl_seconds=3600)

    r = isolated_client.post("/api/debug/cache/prune")
    assert r.status_code == 200, f"got {r.status_code}: {r.text[:400]}"
    assert r.json()["deleted"] == 1, "prune must delete exactly the expired row"

    stats = isolated_client.get("/api/debug/cache").json()
    assert stats["n_entries"] == 1, "the unexpired row must survive prune"
    assert stats["n_expired"] == 0


def test_debug_endpoints_listed_in_root(client: TestClient) -> None:
    """Root GET must surface /api/debug/cache so it's discoverable."""
    body = client.get("/").json()
    endpoints = body.get("endpoints", [])
    joined = "\n".join(endpoints)
    assert "/api/debug/cache" in joined, "root must mention /api/debug/cache"
    assert "/api/debug/cache/bust" in joined, "root must mention /api/debug/cache/bust"
    assert "/api/debug/cache/prune" in joined, "root must mention /api/debug/cache/prune"


def test_debug_cache_openapi_tagged_debug(client: TestClient) -> None:
    """OpenAPI spec should tag the debug endpoints so /docs groups them."""
    spec = client.get("/openapi.json").json()
    paths = spec.get("paths", {})
    debug_paths = [p for p in paths if "/debug/" in p]
    assert len(debug_paths) >= 3, f"expected 3+ /debug/ paths, got {debug_paths}"
    for p in debug_paths:
        op = next(iter(paths[p].values()))
        assert "debug" in op.get("tags", []), f"{p} must be tagged 'debug'"
