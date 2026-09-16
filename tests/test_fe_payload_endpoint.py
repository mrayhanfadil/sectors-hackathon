"""Tests for the PDF payload HTTP endpoint: GET /api/report/{ticker}/payload.

Verifies:
1. Parity: for a ticker with assumptions (AMMN), GET /api/report/AMMN/payload returns a payload
   whose top-level key set equals render_html_for_ticker("AMMN", None)[2] keys (frozen 45 sections).
2. Honesty: for a ticker without assumptions (BBCA), the endpoint returns 422 and the body
   carries the missing list - no fabricated fallback payload.
3. JSON: the response parses cleanly with json.loads - no unserializable objects (e.g. DataFrame, datetime).
4. Section filter: ?section=cover filters payload and sections envelope cleanly.
5. Template override: ?template=infra passes template override to builder.
6. Availability flags: sections envelope accurately reflects data availability.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from server.main import app
from server.routers.pdf import render_html_for_ticker


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_parity_ammn_payload_keys(client):
    """Parity: GET /api/report/AMMN/payload returns a payload with exact same top-level keys as the PDF."""
    res = client.get("/api/report/AMMN/payload")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

    body = res.json()
    assert body.get("ticker") == "AMMN"
    assert "payload" in body, "Envelope must contain 'payload'"
    assert "sections" in body, "Envelope must contain 'sections'"

    # Extract direct payload from PDF renderer
    _, _, raw_pdf_payload = render_html_for_ticker("AMMN", None)

    endpoint_keys = set(body["payload"].keys())
    pdf_keys = set(raw_pdf_payload.keys())

    assert endpoint_keys == pdf_keys, (
        f"Key parity drift detected!\n"
        f"In endpoint only: {endpoint_keys - pdf_keys}\n"
        f"In PDF only: {pdf_keys - endpoint_keys}"
    )
    assert len(endpoint_keys) == 45, f"Expected 45 frozen contract sections, got {len(endpoint_keys)}"


def test_honesty_bbca_missing_assumptions_422(client):
    """Honesty: GET /api/report/BBCA/payload returns 422 with missing list, no fabricated numbers."""
    res = client.get("/api/report/BBCA/payload")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}: {res.text}"

    body = res.json()
    detail = body.get("detail")
    assert isinstance(detail, dict), f"Expected detail object, got {type(detail)}: {detail}"
    assert detail.get("ticker") == "BBCA"

    missing = detail.get("missing")
    assert isinstance(missing, list), f"Expected 'missing' to be a list, got {type(missing)}"
    assert len(missing) > 0, "Missing field list must not be empty"


def test_json_serializability(client):
    """JSON: Response is valid RFC 8259 JSON and deserializes cleanly without non-standard types."""
    res = client.get("/api/report/AMMN/payload")
    assert res.status_code == 200

    # Test raw text parsing with standard json.loads
    parsed = json.loads(res.text)
    assert isinstance(parsed, dict)
    assert parsed["ticker"] == "AMMN"
    assert isinstance(parsed["payload"], dict)
    assert isinstance(parsed["sections"], dict)

    # Verify nested structures (e.g. sensitivity grid from DataFrame)
    valuation_page = parsed["payload"].get("valuation_page")
    assert valuation_page is not None
    sensitivity = valuation_page.get("sensitivity")
    assert sensitivity is not None
    assert "fair_value" in sensitivity
    assert isinstance(sensitivity["fair_value"], dict)


def test_sections_availability_flags(client):
    """Availability flags: sections dict carries boolean flags matching data presence."""
    res = client.get("/api/report/AMMN/payload")
    assert res.status_code == 200

    body = res.json()
    sections = body["sections"]
    payload = body["payload"]

    assert set(sections.keys()) == set(payload.keys())
    assert all(isinstance(v, bool) for v in sections.values())

    # AMMN has cover, valuation_page, performance_page, etc.
    assert sections.get("cover") is True
    assert sections.get("valuation_page") is True
    assert sections.get("performance_page") is True
    assert sections.get("statements_page") is True

    # AMMN strategy section is None in live payload
    assert sections.get("strategy") is False


def test_section_filter_query_param(client):
    """Filter: ?section=cover returns envelope restricted to the requested section."""
    res = client.get("/api/report/AMMN/payload?section=cover")
    assert res.status_code == 200

    body = res.json()
    assert body.get("ticker") == "AMMN"
    assert list(body["payload"].keys()) == ["cover"]
    assert list(body["sections"].keys()) == ["cover"]
    assert body["sections"]["cover"] is True

    # Non-existent section -> 404
    res_404 = client.get("/api/report/AMMN/payload?section=nonexistent_section_xyz")
    assert res_404.status_code == 404


def test_template_override_query_param(client):
    """Template override: ?template=strategy passes template override to the builder."""
    res = client.get("/api/report/AMMN/payload?template=strategy")
    assert res.status_code == 200

    body = res.json()
    _, _, raw_strategy = render_html_for_ticker("AMMN", template_override="strategy")
    assert set(body["payload"].keys()) == set(raw_strategy.keys())
