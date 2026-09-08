"""Loud-failure guards (ACES 2026-09-05): no fabricated valuations, no empty duels.

- GET /api/report/{ticker} without data/assumptions/{ticker}.json -> 422
  (was: 200 with default-assumption FV, e.g. ACES upside 2079% BUY).
- Engine tickers (BBCA) keyless -> 422 naming missing WACC inputs
  (was: 200 via invented defaults; LOUD policy Sep 2026).
- adversarial_instruction must contain the EXIT GUARD (no exit_loop on
  iteration 1, debate needs calc+source evidence).

Run: .venv/bin/python -m pytest tests/test_report_loud_failure.py -v
"""

from __future__ import annotations

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


def test_report_unknown_ticker_is_422_not_fabricated(api_client):
    res = api_client.get("/api/report/ZZZZ")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}: {res.text[:500]}"
    body = res.json()
    detail = body.get("detail", {})
    if isinstance(detail, dict):
        assert detail.get("ticker") == "ZZZZ", "422 must name the ticker"
        assert "/api/agent/start" in detail.get("summary", ""), "422 must point to the full agent path"
    else:
        assert "ZZZZ" in str(detail), "422 must name the ticker"
        assert "/api/agent/start" in str(detail), "422 must point to the full agent path"


def test_report_engine_ticker_keyless_422_names_inputs(api_client):
    res = api_client.get("/api/report/BBCA")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}: {res.text[:500]}"
    body = res.json()
    detail = body.get("detail", {})
    if isinstance(detail, dict):
        assert detail.get("ticker") == "BBCA", "422 must name the ticker"
        assert "rf" in detail.get("missing", []), "422 must disclose missing WACC keys"
        assert "/api/agent/start" in detail.get("summary", ""), "422 must point to the full agent path"
    else:
        detail_str = str(detail)
        assert "BBCA" in detail_str, "422 must name the ticker"
        assert "sectors_missing_key" in detail_str, "422 must disclose keyless cause"
        assert "/api/agent/start" in detail_str, "422 must point to the full agent path"


def test_adversarial_exit_guard_present():
    text = (REPO_ROOT / "agents" / "adk" / "agents" / "instructions.py").read_text(encoding="utf-8")
    assert "EXIT GUARD" in text, "adversarial_instruction lost its EXIT GUARD"
    assert "NEVER call exit_loop on your first iteration" in text
    assert "calc_* recomputation" in text


def test_debate_schema_rules_present():
    text = (REPO_ROOT / "agents" / "adk" / "agents" / "instructions.py").read_text(encoding="utf-8")
    assert "defense: {mode: defend|concede, calc_refs:" in text
    assert "Debate is structured JSON?" in text
    assert "REJECT plain strings / placeholders" in text


def test_writer_anchor_rules_present():
    text = (REPO_ROOT / "agents" / "adk" / "agents" / "instructions.py").read_text(encoding="utf-8")
    assert "ANCHOR RULE" in text
    assert "target_anchor: primary|dcf|secondary|tertiary|blended" in text
    assert "GATE RULE" in text
    assert "gate_flags" in text
    assert "Thesis anchored?" in text
