"""LOUD policy regression tests (AGY-1): missing Sectors data returns honest 422/503.

Covers keyless environment invariants:
- GET /api/report/BBCA -> 422, body names missing keys
- GET /api/report/NOPEXYZ -> 422 (unknown ticker missing assumptions)
- GET /api/dcf/RATU bare -> 422 mentioning RATU
- GET /api/dcf/RATU?overrides={"rf":0.0696,"beta":0.9,"erp":0.07,"cod":0.06} -> 200 with wacc + valuation keys
- GET /api/outlook keyless -> 503 with sectors_missing_key / SECTORS_API_KEY requirement
- GET /api/tickers keyless -> 503 (sectors screener pending)
- GET /api/report/BBCA/pdf keyless -> 422 (no verified assumptions)
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from server.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_report_bbca_keyless_422_names_missing_keys(client):
    """GET /api/report/BBCA -> 422, body names missing keys."""
    res = client.get("/api/report/BBCA")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}: {res.text}"
    detail = str(res.json().get("detail", ""))
    assert "BBCA" in detail, "422 detail must name the ticker BBCA"
    for key in ("rf", "beta", "erp", "cod"):
        assert key in detail, f"422 detail must name missing key '{key}'"


def test_report_unknown_ticker_422(client):
    """GET /api/report/NOPEXYZ -> 422."""
    res = client.get("/api/report/NOPEXYZ")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}: {res.text}"
    detail = str(res.json().get("detail", ""))
    assert "NOPEXYZ" in detail, "422 detail must name the unknown ticker NOPEXYZ"
    assert "assumptions" in detail, "422 detail must mention missing assumptions"


def test_dcf_ratu_bare_422(client):
    """GET /api/dcf/RATU bare -> 422 mentioning RATU."""
    res = client.get("/api/dcf/RATU")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}: {res.text}"
    detail = str(res.json().get("detail", ""))
    assert "RATU" in detail, "422 detail must mention RATU"
    for key in ("rf", "beta", "erp", "cod"):
        assert key in detail, f"422 detail must mention missing key '{key}'"


def test_dcf_ratu_with_declared_overrides_200(client):
    """GET /api/dcf/RATU with fully-declared overrides -> 200 with wacc + valuation keys."""
    overrides = json.dumps({
        "rf": 0.0696, "beta": 0.9, "erp": 0.07, "cod": 0.06,
        "revenue": 5000e9, "ebit_margin": 0.20, "g1": 0.08, "g": 0.03,
        "tax": 0.22, "capex_pct": 0.06, "nwc_pct": 0.05,
        "shares_out": 5e9, "last_price": 2000.0,
    })
    res = client.get(f"/api/dcf/RATU?overrides={overrides}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert isinstance(data, dict), "Response must be a JSON object"
    assert "wacc" in data, "Response must contain 'wacc' key"
    assert "valuation" in data, "Response must contain 'valuation' key"
    assert data["valuation"].get("fair_value_per_share") is not None, "Valuation must have fair_value_per_share"


def test_outlook_keyless_503(client):
    """GET /api/outlook keyless -> 503 with sectors_missing_key."""
    res = client.get("/api/outlook")
    assert res.status_code == 503, f"Expected 503, got {res.status_code}: {res.text}"
    detail = str(res.json().get("detail", ""))
    assert "SECTORS_API_KEY" in detail or "sectors" in detail.lower(), "503 must mention SECTORS_API_KEY or sectors"
    assert "unavailable" in detail.lower(), "503 detail must state unavailable status"


def test_tickers_keyless_503(client):
    """GET /api/tickers keyless -> 503."""
    res = client.get("/api/tickers")
    assert res.status_code == 503, f"Expected 503, got {res.status_code}: {res.text}"
    detail = str(res.json().get("detail", ""))
    assert "SECTORS_API_KEY" in detail or "sectors" in detail.lower(), "503 must mention SECTORS_API_KEY or sectors"
    assert "unavailable" in detail.lower(), "503 detail must state unavailable status"


def test_report_bbca_pdf_keyless_422(client):
    """GET /api/report/BBCA/pdf keyless -> 422."""
    res = client.get("/api/report/BBCA/pdf")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}: {res.text}"
    detail = str(res.json().get("detail", ""))
    assert "BBCA" in detail, "422 detail must name the ticker BBCA"
    assert "generic fallback" in detail or "assumptions" in detail, "422 detail must explain missing verified assumptions"
