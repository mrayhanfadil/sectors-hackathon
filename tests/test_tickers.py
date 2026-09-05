"""GET /api/tickers — IDX universe from Morning Brief DB.

Live test against the local stockdata Postgres (same DB the
idx-morning-brief cron reads). Skipped cleanly if DB is unreachable.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from server.main import app  # noqa: E402

client = TestClient(app)


def test_tickers_shape():
    try:
        r = client.get("/api/tickers")
    except Exception as exc:
        pytest.skip(f"ticker DB unreachable: {type(exc).__name__}")
    if r.status_code == 503:
        pytest.skip("ticker universe unavailable (503)")
    assert r.status_code == 200
    d = r.json()
    assert d["source"] == "stockdata.tickers"
    assert d["count"] >= 900, d["count"]
    assert len(d["tickers"]) == d["count"]
    by_kode = {t["kode"]: t for t in d["tickers"]}
    for must in ("BBCA", "ADRO", "MTEL", "POWR", "RATU", "CDIA"):
        assert must in by_kode, must
    assert "Bank Central Asia" in (by_kode["BBCA"]["nama"] or "")
    assert all(set(t.keys()) == {"kode", "nama", "sector"} for t in d["tickers"])


def test_tickers_cached_second_hit():
    r1 = client.get("/api/tickers")
    if r1.status_code != 200:
        pytest.skip("ticker universe unavailable")
    r2 = client.get("/api/tickers")
    assert r2.status_code == 200
    assert r2.json()["count"] == r1.json()["count"]
