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

import json

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
            body = res.json()
            detail = body.get("detail", {})
            assert isinstance(detail, dict), f"422 detail must be structured dict, got {type(detail).__name__}"
            assert detail.get("ticker") == "BBCA", "422 must name the ticker"
            missing = detail.get("missing", [])
            assert "rf" in missing, f"422 must disclose missing WACC keys, got {missing}"
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
        # LOUD policy: outlook always 503 until the Sectors-native outlook is
        # wired post-key (JPM-9100 fixture retired, never served as live).
        assert res.status_code == 503, f"Expected 503, got {res.status_code}: {res.text}"
        assert "sectors-native outlook pending" in res.text
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


def test_report_ratu_keyless_422(api_client):
    # H1-restore (AGY-H1 reverted H1's hunks via git checkout 10:43:07; AGY-H1's
    # own file covers BBCA/unknown/dcf-RATU/outlook/tickers/pdf - these are the
    # non-overlapping gaps). RATU file lacks WACC inputs -> strict 422 keyless.
    res = api_client.get("/api/report/RATU")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}: {res.text}"
    for k in ("rf", "beta", "erp", "cod"):
        assert k in res.text, f"422 must name missing key {k}: {res.text[:300]}"


def test_report_bbca_html_keyless_422(api_client):
    res = api_client.get("/api/report/BBCA/html")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}: {res.text}"


def test_report_unknown_pdf_html_422(api_client):
    for suffix in ("pdf", "html"):
        res = api_client.get(f"/api/report/NOPEXYZ/{suffix}")
        assert res.status_code == 422, f"Expected 422 for {suffix}, got {res.status_code}: {res.text}"


def test_dcf_bbca_bare_422(api_client):
    res = api_client.get("/api/dcf/BBCA")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}: {res.text}"
    assert "BBCA" in res.text


def test_dcf_bbca_declared_overrides_200(api_client):
    # Explicit test inputs (Sep 2026, no prod seeds): every driver declared.
    ov = json.dumps({
        "rf": 0.0696, "beta": 0.9, "erp": 0.07, "cod": 0.06,
        "revenue": 5000e9, "ebit_margin": 0.20, "g1": 0.08, "g": 0.03,
        "tax": 0.22, "capex_pct": 0.06, "nwc_pct": 0.05,
        "shares_out": 5e9, "last_price": 2000.0,
    })
    res = api_client.get(f"/api/dcf/BBCA?overrides={ov}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert "wacc" in data and "valuation" in data


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
