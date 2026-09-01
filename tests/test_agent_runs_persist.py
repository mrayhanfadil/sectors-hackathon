# Copyright 2026 Sectors Hackathon
"""Unit and integration tests for ADK agent run persistence helpers and endpoints."""

from __future__ import annotations

import pathlib
import time
import pytest
from fastapi.testclient import TestClient

from agents.adk.storage import AgentRunStore


@pytest.fixture
def tmp_store(tmp_path: pathlib.Path) -> AgentRunStore:
    """Fixture providing an isolated AgentRunStore backed by a temporary SQLite file."""
    db_file = str(tmp_path / "test_persist.db")
    return AgentRunStore(db_path=db_file)


def test_get_latest_completed_no_runs(tmp_store: AgentRunStore) -> None:
    """Case 1: When no runs exist for a ticker, get_latest_completed returns None."""
    assert tmp_store.get_latest_completed("BBCA") is None
    assert tmp_store.get_latest_completed("NONEXISTENT") is None


def test_get_latest_completed_ordering_and_statuses(tmp_store: AgentRunStore) -> None:
    """Case 2: Test ordering and terminal status filtering.
    Status 'running' must be excluded; newest terminal run ('completed', 'interrupted', 'failed') wins.
    """
    ticker = "BBCA"

    # 1. Start and finish an older completed run
    tmp_store.start_run("bbca-run-1", ticker, "First prompt")
    time.sleep(0.01)
    tmp_store.finish_run("bbca-run-1", status="completed", last_text="First run text")

    # 2. Start and finish a newer failed run
    time.sleep(0.01)
    tmp_store.start_run("bbca-run-2", ticker, "Second prompt")
    time.sleep(0.01)
    tmp_store.finish_run("bbca-run-2", status="failed", error="LLM provider rate limited")

    # 3. Start and finish a newer completed run
    time.sleep(0.01)
    tmp_store.start_run("bbca-run-3", ticker, "Third prompt")
    time.sleep(0.01)
    tmp_store.finish_run("bbca-run-3", status="completed", last_text="Third run text", state={"summary": "Success"})

    # 4. Start a run currently still in 'running' status (should be ignored by get_latest_completed)
    time.sleep(0.01)
    tmp_store.start_run("bbca-run-4", ticker, "Fourth prompt (in-progress)")

    latest = tmp_store.get_latest_completed(ticker)
    assert latest is not None
    assert latest["run_id"] == "bbca-run-3"
    assert latest["status"] == "completed"
    assert latest["last_text"] == "Third run text"
    assert latest["state"] == {"summary": "Success"}


def test_get_latest_completed_ticker_case_insensitive(tmp_store: AgentRunStore) -> None:
    """Case 3: Ticker queries must be case-insensitive (e.g., 'bbca', 'Bbca', 'BBCA')."""
    tmp_store.start_run("run-case-1", "bbca", "Prompt lower")
    tmp_store.finish_run("run-case-1", status="completed")

    res_lower = tmp_store.get_latest_completed("bbca")
    res_upper = tmp_store.get_latest_completed("BBCA")
    res_mixed = tmp_store.get_latest_completed("BbCa")

    assert res_lower is not None
    assert res_upper is not None
    assert res_mixed is not None
    assert res_lower["run_id"] == "run-case-1"
    assert res_upper["run_id"] == "run-case-1"
    assert res_mixed["run_id"] == "run-case-1"


def test_get_run_with_events(tmp_store: AgentRunStore) -> None:
    """Case 4: get_run_with_events retrieves run metadata and ordered event trace in one step."""
    run_id = "test-run-events-1"
    tmp_store.start_run(run_id, "TLKM", "TLKM Prompt")
    tmp_store.append_event(
        run_id,
        seq=1,
        event={"author": "modeler", "node": "val_node", "event_type": "function_call", "text": "calc dcf"},
    )
    tmp_store.append_event(
        run_id,
        seq=0,
        event={"author": "collector", "node": "data_node", "event_type": "agent_message", "text": "fetching data"},
    )
    tmp_store.finish_run(run_id, status="completed", last_text="Done")

    # Non-existent run returns None
    assert tmp_store.get_run_with_events("nonexistent-id") is None

    # Existing run returns metadata and sorted events
    result = tmp_store.get_run_with_events(run_id)
    assert result is not None
    assert result["run_id"] == run_id
    assert result["status"] == "completed"
    assert len(result["events"]) == 2
    assert result["events"][0]["seq"] == 0
    assert result["events"][0]["author"] == "collector"
    assert result["events"][0]["text"] == "fetching data"
    assert result["events"][1]["seq"] == 1
    assert result["events"][1]["author"] == "modeler"
    assert result["events"][1]["text"] == "calc dcf"


def test_api_runs_latest_and_report_run_endpoints(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Case 5: Integration test for GET /api/agent/runs/latest and GET /api/report/{ticker}/run."""
    from server.main import app

    test_db = str(tmp_path / "api_latest_test.db")
    store = AgentRunStore(db_path=test_db)
    monkeypatch.setattr("agents.adk.storage.default_db_path", lambda: test_db)

    client = TestClient(app)

    # 1. When no run exists for BBCA
    res_latest_empty = client.get("/api/agent/runs/latest?ticker=BBCA")
    assert res_latest_empty.status_code == 204

    res_report_empty = client.get("/api/report/BBCA/run")
    assert res_report_empty.status_code == 200
    assert res_report_empty.json() == {
        "has_run": False,
        "run_id": None,
        "status": None,
        "n_events": 0,
        "started_at": None,
        "finished_at": None,
        "last_text": None,
        "error": None,
    }

    # 2. Populate a completed run for BBCA
    run_id = "bbca-session-999"
    store.start_run(run_id, "BBCA", "BBCA analysis prompt", provider="minimax", model="MiniMax-M3")
    store.append_event(run_id, 0, {"author": "collector", "text": "Found 4 filings"})
    store.finish_run(run_id, status="completed", last_text="BBCA TP 9600 BUY", state={"rating": "BUY"})

    # 3. GET /api/agent/runs/latest returns 200 with run metadata + events
    res_latest = client.get("/api/agent/runs/latest?ticker=bbca")
    assert res_latest.status_code == 200
    latest_data = res_latest.json()
    assert latest_data["run_id"] == run_id
    assert latest_data["status"] == "completed"
    assert latest_data["last_text"] == "BBCA TP 9600 BUY"
    assert len(latest_data["events"]) == 1
    assert latest_data["events"][0]["author"] == "collector"

    # 4. GET /api/report/BBCA/run returns 200 with has_run=True
    res_report = client.get("/api/report/BBCA/run")
    assert res_report.status_code == 200
    report_data = res_report.json()
    assert report_data["has_run"] is True
    assert report_data["run_id"] == run_id
    assert report_data["status"] == "completed"
    assert report_data["n_events"] == 1
    assert report_data["last_text"] == "BBCA TP 9600 BUY"
    assert report_data["error"] is None
