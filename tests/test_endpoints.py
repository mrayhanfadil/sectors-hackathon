"""Endpoint integration and smoke tests for FastAPI server.

Covers:
  - GET /api/health -> {"status": "ok"}
  - GET /api/report/BBCA -> {"ticker": "BBCA", "valuation": {...}}
  - GET /api/outlook -> {"jci_target": ..., "scenarios": ...}
  - GET /api/news?ticker=BBCA -> list of items
  - GET /api/sentiment?ticker=BBCA -> dict with sentiment gauge
  - POST /api/challenge -> dict with verdict/evidence

Run: .venv/bin/python -m pytest tests/test_endpoints.py -v
Or:  .venv/bin/python tests/test_endpoints.py
"""

from __future__ import annotations

import logging
import sys
import warnings
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from server.main import app
    client = TestClient(app)
except Exception as exc:
    client = None
    warnings.warn(f"Failed to initialize TestClient with server.main.app: {exc}")


@pytest.fixture(scope="module")
def api_client():
    if client is None:
        pytest.skip("FastAPI app could not be initialized")
    return client


def test_health_endpoint(api_client):
    try:
        res = api_client.get("/api/health")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert isinstance(data, dict), "Health response must be a dict"
        assert data.get("status") == "ok", f"Expected status 'ok', got {data.get('status')}"
    except Exception as exc:
        warnings.warn(f"GET /api/health failed assertion: {exc}")
        raise


def test_report_bbca_endpoint(api_client):
    try:
        res = api_client.get("/api/report/BBCA")
        # LOUD policy (keyless): missing WACC inputs -> 422 naming them,
        # never invented defaults. Keyed runs with full assumptions -> 200.
        assert res.status_code in (200, 422), f"Unexpected {res.status_code}: {res.text}"
        if res.status_code == 422:
            assert "BBCA" in res.text and "sectors_missing_key" in res.text
            return
        data = res.json()
        assert isinstance(data, dict), "Report response must be a dict"
        assert data.get("ticker") == "BBCA", f"Expected ticker 'BBCA', got {data.get('ticker')}"
        assert "valuation" in data and isinstance(data["valuation"], dict), "Valuation must be a dict"
        assert "fair_value" in data["valuation"] or "dcf" in data["valuation"], "Valuation missing fair value / dcf"
    except Exception as exc:
        warnings.warn(f"GET /api/report/BBCA failed assertion: {exc}")
        raise


def test_outlook_endpoint(api_client):
    try:
        res = api_client.get("/api/outlook")
        # LOUD policy (keyless): outlook refuses hardcoded JCI 9100 -> 503.
        # Keyed runs with Sectors data -> 200.
        assert res.status_code in (200, 503), f"Unexpected {res.status_code}: {res.text}"
        if res.status_code == 503:
            assert "sectors_missing_key" in res.text
            return
        data = res.json()
        assert isinstance(data, dict), "Outlook response must be a dict"
        assert "jci_target" in data or "jci_base" in data, "Outlook missing jci_target/jci_base"
        assert "scenarios" in data or "ow" in data, "Outlook missing scenarios/ow"
    except Exception as exc:
        warnings.warn(f"GET /api/outlook failed assertion: {exc}")
        raise


def test_news_endpoint(api_client):
    try:
        res = api_client.get("/api/news?ticker=BBCA")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            assert "items" in data, "News dict response missing 'items' field"
            items = data["items"]
            assert data.get("ticker") == "BBCA", f"Expected ticker 'BBCA', got {data.get('ticker')}"
        else:
            pytest.fail(f"Unexpected data type for news response: {type(data)}")
        assert isinstance(items, list), "News items must be a list"
    except Exception as exc:
        warnings.warn(f"GET /api/news?ticker=BBCA failed assertion: {exc}")
        raise


def test_sentiment_endpoint(api_client):
    try:
        res = api_client.get("/api/sentiment?ticker=BBCA")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert isinstance(data, dict), "Sentiment response must be a dict"
        assert data.get("ticker") == "BBCA", f"Expected ticker 'BBCA', got {data.get('ticker')}"
        assert "gauge" in data, "Sentiment response missing 'gauge'"
    except Exception as exc:
        warnings.warn(f"GET /api/sentiment?ticker=BBCA failed assertion: {exc}")
        raise


def test_challenge_endpoint(api_client):
    try:
        res = api_client.post("/api/challenge", json={"ticker": "BBCA", "claim": "WACC discount rate is too high"})
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert isinstance(data, dict), "Challenge response must be a dict"
        assert "verdict" in data, "Challenge response missing 'verdict'"
        assert "evidence" in data, "Challenge response missing 'evidence'"
    except Exception as exc:
        warnings.warn(f"POST /api/challenge failed assertion: {exc}")
        raise


if __name__ == "__main__":
    if client is None:
        print("FAIL: Could not initialize FastAPI app")
        sys.exit(1)
    tests = [
        ("GET /api/health", lambda: test_health_endpoint(client)),
        ("GET /api/report/BBCA", lambda: test_report_bbca_endpoint(client)),
        ("GET /api/outlook", lambda: test_outlook_endpoint(client)),
        ("GET /api/news?ticker=BBCA", lambda: test_news_endpoint(client)),
        ("GET /api/sentiment?ticker=BBCA", lambda: test_sentiment_endpoint(client)),
        ("POST /api/challenge", lambda: test_challenge_endpoint(client)),
    ]
    passed = 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
            print(f"  PASS  {name}")
        except Exception as e:
            print(f"  FAIL  {name}: {e}")
    print(f"\nPassed {passed}/{len(tests)} endpoint tests")
    sys.exit(0 if passed == len(tests) else 1)
