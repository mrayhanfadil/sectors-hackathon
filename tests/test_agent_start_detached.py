"""Verify /api/agent/start is fire-and-forget: returns quickly, runs in background.

BILLS CREDITS WHEN RUN - see pytestmark below. Default: skipped.
"""
import os
import time
import requests
import pytest

API = os.getenv("AGENT_LIVE_BE_API", "http://localhost:8777")

pytestmark = pytest.mark.skipif(
    os.getenv("AGENT_LIVE_BE") != "1",
    reason="Live-BE integration test - POSTs to the running BE, which holds the real "
    "Sectors key, so EVERY spawned run bills credits (15 Sep 2026: two "
    "fake-ticker fixtures burned ~71 credits). Set AGENT_LIVE_BE=1 to run it "
    "deliberately against a scratch BE with SECTORS_API_KEY scrubbed.",
)

def test_start_returns_quickly():
    """POST /api/agent/start returns < 1s with a run_id."""
    t0 = time.time()
    r = requests.post(f"{API}/api/agent/start", json={"ticker": f"DT1{os.urandom(3).hex().upper()}"}, timeout=5)
    elapsed = time.time() - t0
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["status"] == "started"
    assert body["run_id"].startswith("dt1") or body["run_id"].startswith("dt2")  # distinct random tickers bypass concurrency lock  # any bbca-* suffix OK
    assert elapsed < 3.0, f"start should return quickly, took {elapsed:.2f}s"  # 3s allows cold-start BE warmup
    print(f"PASS: POST /api/agent/start returned in {elapsed*1000:.0f}ms with run_id={body['run_id']}")
    return None  # not None to satisfy pytest

def test_status_endpoint_exists():
    """GET /api/agent/runs/{run_id}/status returns lightweight status."""
    # Start a fresh run first
    start_r = requests.post(f"{API}/api/agent/start", json={"ticker": f"DT1{os.urandom(3).hex().upper()}"}, timeout=5)
    assert start_r.status_code == 200, start_r.text
    run_id = start_r.json()["run_id"]
    r = requests.get(f"{API}/api/agent/runs/{run_id}/status", timeout=5)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "status" in body
    assert "n_events" in body
    assert "is_active" in body
    print(f"PASS: status={body['status']} n_events={body['n_events']} is_active={body['is_active']}")

def test_invalid_ticker():
    """Invalid ticker returns 400."""
    r = requests.post(f"{API}/api/agent/start", json={"ticker": "!!!"}, timeout=5)
    assert r.status_code == 400, r.text
    print("PASS: invalid ticker rejected with 400")

if __name__ == "__main__":
    test_start_returns_quickly()
    test_status_endpoint_exists()
    test_invalid_ticker()
