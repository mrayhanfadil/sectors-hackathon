"""Verify /api/agent/start refuses concurrent runs for the same ticker.

BILLS CREDITS WHEN RUN - see pytestmark below. Default: skipped.
"""
import time
import requests
import os
import pytest

API = os.getenv("AGENT_LIVE_BE_API", "http://localhost:8777")

pytestmark = pytest.mark.skipif(
    os.getenv("AGENT_LIVE_BE") != "1",
    reason="Live-BE integration test - POSTs to the running BE, which holds the real "
    "Sectors key, so EVERY spawned run bills credits (15 Sep 2026: two "
    "fake-ticker fixtures burned ~71 credits). Set AGENT_LIVE_BE=1 to run it "
    "deliberately against a scratch BE with SECTORS_API_KEY scrubbed.",
)

def test_concurrency_lock_active_ticker():
    """If a run is currently active for ticker X, second start for X returns 409."""
    # Use a unique ticker for this test
    ticker = f"LOCK{os.urandom(3).hex().upper()}"
    # First start should succeed
    r1 = requests.post(f"{API}/api/agent/start", json={"ticker": ticker}, timeout=5)
    assert r1.status_code == 200, r1.text
    body1 = r1.json()
    assert body1["ok"] is True
    run_id_1 = body1["run_id"]
    print(f"PASS: first start succeeded: {run_id_1}")

    # Second start should be 409
    r2 = requests.post(f"{API}/api/agent/start", json={"ticker": ticker}, timeout=5)
    assert r2.status_code == 409, f"expected 409, got {r2.status_code}: {r2.text}"
    body2 = r2.json()
    assert body2["ok"] is False
    assert body2["error"] == "active_run_exists"
    assert body2["active_run_id"] == run_id_1
    print(f"PASS: second start blocked with 409, active_run_id={body2['active_run_id']}")

    # Different ticker should be allowed
    other_ticker = f"OTH{os.urandom(3).hex().upper()}"
    r3 = requests.post(f"{API}/api/agent/start", json={"ticker": other_ticker}, timeout=5)
    assert r3.status_code == 200, f"different ticker should succeed: {r3.text}"
    print(f"PASS: different ticker {other_ticker} allowed despite {ticker} lock")

if __name__ == "__main__":
    test_concurrency_lock_active_ticker()
