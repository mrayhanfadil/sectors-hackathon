"""Ticker-format guard on /api/agent/start and /api/agent/run.

Credit safety (15 Sep 2026): a spawned ADK run fetches Sectors for whatever
ticker it is handed, and unknown symbols still cost 1 credit per addressed
endpoint on their 404s. The live-BE integration tests posted fake fixtures
(DT1A2B3C, LOCK4F2A1B) at :8777 and burned ~71 credits. The BE now refuses any
ticker that is not a 4-letter IDX code BEFORE a run exists.

Request count is kept deliberately low (2 endpoint calls; the ticker matrix runs
against the helper directly) because the app carries a 60-req/min limiter that
the rest of the suite already presses against.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from server.routers.agent import _TICKER_RE, _invalid_ticker_response  # noqa: E402

FAKE_TICKERS = ["DT1A2B3C", "LOCK4F2A1B", "OTH99FF01", "!!!", "TOOLONGTICKER", "AB", ""]
REAL_TICKERS = ["BBCA", "AMMN", "RATU", "CDIA", "MTEL", "ADRO", "IHSG"]


@pytest.mark.parametrize("ticker", FAKE_TICKERS)
def test_guard_helper_refuses_junk_tickers(ticker: str) -> None:
    """Unit level — no request, no run, no credit."""
    res = _invalid_ticker_response(ticker)
    assert res is not None, f"{ticker!r} must be refused"
    assert res.status_code == 400
    assert b"bukan kode IDX yang valid" in res.body, "the refusal must say why"


@pytest.mark.parametrize("ticker", REAL_TICKERS)
def test_guard_helper_passes_real_idx_codes(ticker: str) -> None:
    assert _invalid_ticker_response(ticker) is None, f"{ticker} must be accepted"
    assert _TICKER_RE.match(ticker)


def test_start_endpoint_refuses_junk_ticker_without_spawning_a_run() -> None:
    """The fire-and-forget endpoint must 400 before any run row exists."""
    import server.main  # noqa: F401  (ensures app import path is available)
    from fastapi.testclient import TestClient

    from server.main import app

    client = TestClient(app)
    res = client.post("/api/agent/start", json={"ticker": "DT1A2B3C"})
    assert res.status_code == 400, f"expected 400, got {res.status_code}: {res.text[:200]}"
    body = res.json()
    assert body["error"] == "invalid_ticker"
    assert "run_id" not in body, "no run may be created for a junk ticker"


def test_blocking_run_endpoint_refuses_junk_ticker() -> None:
    from fastapi.testclient import TestClient

    from server.main import app

    client = TestClient(app)
    res = client.post("/api/agent/run", json={"ticker": "LOCK4F2A1B"})
    assert res.status_code == 400, f"expected 400, got {res.status_code}"
    assert res.json()["error"] == "invalid_ticker"


def test_guard_is_env_overridable(monkeypatch) -> None:
    """SECTORS_TICKER_RE escape hatch exists for non-4-letter instruments."""
    import importlib

    import server.routers.agent as A

    monkeypatch.setenv("SECTORS_TICKER_RE", r"^[A-Z]{2,6}$")
    try:
        reloaded = importlib.reload(A)
        assert reloaded._TICKER_RE.match("AB")
        assert reloaded._TICKER_RE.match("ABCDEF")
    finally:
        monkeypatch.delenv("SECTORS_TICKER_RE", raising=False)
        importlib.reload(A)
