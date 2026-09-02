# Copyright 2026 Sectors Hackathon
"""Tests for /api/agent/runs/summary and /api/agent/runs/latest ticker filtering."""

from __future__ import annotations

import pathlib
import time
import pytest
from fastapi.testclient import TestClient

from server.main import app
from server.storage import AgentRunStore, InterruptReason


@pytest.fixture
def tmp_store(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> AgentRunStore:
    """Fixture providing an isolated AgentRunStore and patching default_db_path."""
    db_file = str(tmp_path / "test_summary.db")
    monkeypatch.setattr("server.storage.default_db_path", lambda: db_file)
    monkeypatch.setattr("agents.adk.storage.default_db_path", lambda: db_file)
    store = AgentRunStore(db_path=db_file)
    return store


def test_runs_summary_and_ticker_filtering(tmp_store: AgentRunStore) -> None:
    """POST / populate 3 runs:
      1. BBCA completed
      2. VKTR interrupted (reason=client_disconnect)
      3. BBCA failed (reason=agent_error)
    Then GET /api/agent/runs/summary and verify:
      - total_runs == 3
      - per-ticker counts: BBCA=2, VKTR=1
      - interrupt reason distribution contains client_disconnect and agent_error
      - latest run per ticker is accurate
      - GET /api/agent/runs/latest?ticker=VKTR returns VKTR and NOT BBCA
      - GET /api/agent/runs/latest (no ticker) returns latest completed/terminal run
    """
    client = TestClient(app)

    # 1. Run 1: BBCA completed
    t1 = time.time()
    tmp_store.start_run("bbca-run-completed", "BBCA", "BBCA prompt", provider="minimax", model="MiniMax-M3")
    tmp_store.append_event("bbca-run-completed", 0, {"author": "collector", "text": "collector done", "state_delta": {"stage": "collector"}})
    tmp_store.finish_run(
        "bbca-run-completed",
        status="completed",
        last_text="BBCA Final Report",
        state={"valuation": "BUY", "tp": 10500},
    )

    # 2. Run 2: VKTR interrupted (client_disconnect)
    time.sleep(0.01)
    tmp_store.start_run("vktr-run-interrupted", "VKTR", "VKTR prompt", provider="minimax", model="MiniMax-M3")
    tmp_store.append_event("vktr-run-interrupted", 0, {"author": "collector", "text": "c", "state_delta": {"filings": 3}})
    tmp_store.append_event("vktr-run-interrupted", 1, {"author": "news", "text": "n", "state_delta": {"news": 5}})
    tmp_store.finish_run(
        "vktr-run-interrupted",
        status="interrupted",
        last_text="",
        state={"filings": 3, "news": 5},
        error="client disconnected after 2 events",
        reason=InterruptReason.CLIENT_DISCONNECT,
    )

    # 3. Run 3: BBCA failed (agent_error)
    time.sleep(0.01)
    tmp_store.start_run("bbca-run-failed", "BBCA", "BBCA second prompt", provider="minimax", model="MiniMax-M3")
    tmp_store.append_event("bbca-run-failed", 0, {"author": "modeler", "text": "error in dcf"})
    tmp_store.finish_run(
        "bbca-run-failed",
        status="failed",
        last_text="",
        error="calc_dcf failed: Division by zero",
        reason=InterruptReason.AGENT_ERROR,
    )

    # ---------- Test GET /api/agent/runs/summary ----------
    res = client.get("/api/agent/runs/summary")
    assert res.status_code == 200
    summary = res.json()

    assert summary["total_runs"] == 3

    # Check status counts
    assert summary["status_counts"]["completed"] == 1
    assert summary["status_counts"]["interrupted"] == 1
    assert summary["status_counts"]["failed"] == 1

    # Check interrupt reason distribution
    assert summary["interrupt_reasons"]["client_disconnect"] == 1
    assert summary["interrupt_reasons"]["agent_error"] == 1

    # Check per-ticker counts
    tickers = summary.get("tickers") or summary.get("by_ticker")
    assert "BBCA" in tickers
    assert "VKTR" in tickers

    assert tickers["BBCA"]["total_runs"] == 2
    assert tickers["BBCA"]["status_counts"]["completed"] == 1
    assert tickers["BBCA"]["status_counts"]["failed"] == 1
    assert tickers["BBCA"]["latest_run"]["run_id"] == "bbca-run-failed"

    assert tickers["VKTR"]["total_runs"] == 1
    assert tickers["VKTR"]["status_counts"]["interrupted"] == 1
    assert tickers["VKTR"]["latest_run"]["run_id"] == "vktr-run-interrupted"
    assert tickers["VKTR"]["latest_run"]["reason"] == "client_disconnect"
    assert tickers["VKTR"]["latest_run"]["state"] == {"filings": 3, "news": 5}

    # ---------- Test GET /api/agent/runs/latest?ticker=VKTR ----------
    # Must return VKTR run and never BBCA
    res_vktr = client.get("/api/agent/runs/latest?ticker=VKTR")
    assert res_vktr.status_code == 200
    vktr_run = res_vktr.json()
    assert vktr_run["ticker"] == "VKTR"
    assert vktr_run["run_id"] == "vktr-run-interrupted"
    assert vktr_run["status"] == "interrupted"
    assert vktr_run["reason"] == "client_disconnect"

    # ---------- Test GET /api/agent/runs/latest?ticker=BBCA ----------
    res_bbca = client.get("/api/agent/runs/latest?ticker=BBCA")
    assert res_bbca.status_code == 200
    bbca_run = res_bbca.json()
    assert bbca_run["ticker"] == "BBCA"
    assert bbca_run["run_id"] == "bbca-run-failed"  # Most recent terminal BBCA run

    # ---------- Test GET /api/agent/runs/latest with unknown ticker ----------
    res_unknown = client.get("/api/agent/runs/latest?ticker=UNKNOWN")
    assert res_unknown.status_code == 204

    # ---------- Test GET /api/agent/runs/latest (no ticker filter) ----------
    res_latest_any = client.get("/api/agent/runs/latest")
    assert res_latest_any.status_code == 200
    latest_any = res_latest_any.json()
    assert latest_any["run_id"] == "bbca-run-failed"  # Chronologically latest terminal run overall
