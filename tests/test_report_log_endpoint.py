# Copyright 2026 Sectors Hackathon
"""Unit and integration tests for GET /api/report/{ticker}/log endpoint."""

from __future__ import annotations

import pathlib
import time
import pytest
from fastapi.testclient import TestClient

from agents.adk.storage import AgentRunStore
from server.main import app


@pytest.fixture
def test_db_store(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> AgentRunStore:
    """Fixture providing an isolated AgentRunStore backed by a temporary SQLite database."""
    test_db = str(tmp_path / "test_report_runs.db")
    monkeypatch.setattr("agents.adk.storage.default_db_path", lambda: test_db)
    store = AgentRunStore(db_path=test_db)
    return store


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_404_free_on_ticker_without_runs(client: TestClient, test_db_store: AgentRunStore) -> None:
    """Case 1: 404-free on ticker without runs (returns 200 + has_run=false, log=null, history=[])."""
    res = client.get("/api/report/NORUNS/log")
    assert res.status_code == 200
    data = res.json()
    assert data["ticker"] == "NORUNS"
    assert data["has_run"] is False
    assert data["log"] is None
    assert data["history"] == []


def test_returns_latest_run_as_log(client: TestClient, test_db_store: AgentRunStore) -> None:
    """Case 2: Returns latest run as `log` with all metadata and text preview."""
    start_ts = 1700000000.0
    finish_ts = 1700000120.5
    test_db_store.start_run(
        "run-1",
        "BBCA",
        "Generate report",
        provider="minimax",
        model="minimax/MiniMax-M3",
    )
    # Manually backdate started_at for deterministic testing
    with test_db_store._lock:
        test_db_store.conn.execute(
            "UPDATE agent_runs SET started_at = ? WHERE run_id = ?",
            (start_ts, "run-1"),
        )
        test_db_store.conn.commit()

    test_db_store.finish_run(
        "run-1",
        status="completed",
        last_text="This is a long summary text describing the equity valuation for BBCA and its key metrics.",
        error=None,
    )
    with test_db_store._lock:
        test_db_store.conn.execute(
            "UPDATE agent_runs SET finished_at = ? WHERE run_id = ?",
            (finish_ts, "run-1"),
        )
        test_db_store.conn.commit()

    res = client.get("/api/report/BBCA/log")
    assert res.status_code == 200
    data = res.json()
    assert data["ticker"] == "BBCA"
    assert data["has_run"] is True
    log = data["log"]
    assert log is not None
    assert log["run_id"] == "run-1"
    assert log["status"] == "completed"
    assert log["started_at"] == start_ts
    assert log["finished_at"] == finish_ts
    assert log["duration_s"] == 120.5
    assert log["provider"] == "minimax"
    assert log["model"] == "minimax/MiniMax-M3"
    assert log["error"] is None
    assert "This is a long summary text" in log["last_text_preview"]


def test_returns_up_to_5_in_history_newest_first(client: TestClient, test_db_store: AgentRunStore) -> None:
    """Case 3: Returns up to 5 runs in history, ordered newest-first."""
    base_ts = 1700000000.0
    for i in range(7):
        run_id = f"bbca-run-{i}"
        test_db_store.start_run(run_id, "BBCA", f"prompt {i}")
        # update started_at
        with test_db_store._lock:
            test_db_store.conn.execute(
                "UPDATE agent_runs SET started_at = ?, finished_at = ?, status = ? WHERE run_id = ?",
                (base_ts + i * 100, base_ts + i * 100 + 50, "completed", run_id),
            )
            test_db_store.conn.commit()

    res = client.get("/api/report/BBCA/log")
    assert res.status_code == 200
    data = res.json()
    assert data["has_run"] is True
    assert len(data["history"]) == 5
    # Check newest first order: run-6, run-5, run-4, run-3, run-2
    expected_ids = ["bbca-run-6", "bbca-run-5", "bbca-run-4", "bbca-run-3", "bbca-run-2"]
    actual_ids = [h["run_id"] for h in data["history"]]
    assert actual_ids == expected_ids
    assert data["log"]["run_id"] == "bbca-run-6"


def test_ticker_case_insensitive(client: TestClient, test_db_store: AgentRunStore) -> None:
    """Case 4: Ticker is case-insensitive (bbca -> BBCA, Bbca -> BBCA)."""
    test_db_store.start_run("bbca-case-1", "BBCA", "prompt")
    test_db_store.finish_run("bbca-case-1", status="completed")

    res_lower = client.get("/api/report/bbca/log")
    assert res_lower.status_code == 200
    data_lower = res_lower.json()
    assert data_lower["ticker"] == "BBCA"
    assert data_lower["has_run"] is True
    assert data_lower["log"]["run_id"] == "bbca-case-1"

    res_mixed = client.get("/api/report/BbCa/log")
    assert res_mixed.status_code == 200
    data_mixed = res_mixed.json()
    assert data_mixed["ticker"] == "BBCA"
    assert data_mixed["has_run"] is True


def test_duration_math_finished_vs_unfinished(client: TestClient, test_db_store: AgentRunStore) -> None:
    """Case 5: duration_s math: finished_at - started_at, or null if unfinished / running."""
    # Unfinished run
    test_db_store.start_run("run-running", "ADRO", "prompt")
    res_running = client.get("/api/report/ADRO/log")
    assert res_running.status_code == 200
    data_running = res_running.json()
    assert data_running["has_run"] is True
    assert data_running["log"]["status"] == "running"
    assert data_running["log"]["finished_at"] is None
    assert data_running["log"]["duration_s"] is None
    assert data_running["history"][0]["duration_s"] is None

    # Finished run with precise duration math
    test_db_store.finish_run("run-running", status="completed")
    res_finished = client.get("/api/report/ADRO/log")
    assert res_finished.status_code == 200
    data_finished = res_finished.json()
    assert data_finished["log"]["status"] == "completed"
    assert data_finished["log"]["finished_at"] is not None
    assert isinstance(data_finished["log"]["duration_s"], float)
    assert data_finished["log"]["duration_s"] >= 0
