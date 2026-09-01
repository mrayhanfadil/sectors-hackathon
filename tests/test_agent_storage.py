# Copyright 2026 Sectors Hackathon
"""Unit and integration tests for ADK agent run persistence layer (SQLite)."""

from __future__ import annotations

import os
import pathlib
import threading
import time
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from agents.adk.storage import (
    AgentRunStore,
    default_db_path,
    serialize_event,
)


@pytest.fixture
def tmp_store(tmp_path: pathlib.Path) -> AgentRunStore:
    """Fixture providing an isolated AgentRunStore backed by a temporary SQLite file."""
    db_file = str(tmp_path / "test_agent_runs.db")
    store = AgentRunStore(db_path=db_file)
    return store


def test_init_creates_tables(tmp_path: pathlib.Path) -> None:
    """Test that initializing AgentRunStore on a fresh DB creates required tables and indexes."""
    db_file = str(tmp_path / "fresh_init.db")
    store = AgentRunStore(db_path=db_file)

    cur = store.conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cur.fetchall()}
    assert "agent_runs" in tables
    assert "agent_events" in tables

    cur.execute("SELECT name FROM sqlite_master WHERE type='index';")
    indexes = {row[0] for row in cur.fetchall()}
    assert "idx_agent_runs_ticker" in indexes
    assert "idx_agent_runs_started" in indexes
    assert "idx_agent_events_run" in indexes


def test_start_run_inserts_row(tmp_store: AgentRunStore) -> None:
    """Test start_run inserts a row with status='running', started_at set, and provider metadata."""
    run_id = "bbca-test1234"
    ticker = "BBCA"
    prompt = "Test prompt for BBCA"
    tmp_store.start_run(
        run_id,
        ticker,
        prompt,
        provider="minimax",
        model="minimax/MiniMax-M3",
    )

    run = tmp_store.get_run(run_id)
    assert run is not None
    assert run["run_id"] == run_id
    assert run["ticker"] == "BBCA"
    assert run["status"] == "running"
    assert run["started_at"] is not None
    assert run["started_at"] > 0
    assert run["finished_at"] is None
    assert run["provider"] == "minimax"
    assert run["model"] == "minimax/MiniMax-M3"
    assert run["prompt"] == prompt
    assert run["n_events"] == 0


def test_append_event_inserts_row(tmp_store: AgentRunStore) -> None:
    """Test append_event inserts an event row with correct seq, author, event_type, and payload."""
    run_id = "bbca-append-test"
    tmp_store.start_run(run_id, "BBCA", "prompt")

    mock_event = {
        "author": "collector",
        "node": "collector_node",
        "event_type": "function_call",
        "text": "Fetching financial data",
        "function_calls": [{"name": "calc_dcf", "args": {"wacc": 0.08}}],
    }

    tmp_store.append_event(run_id, seq=0, event=mock_event)

    events = tmp_store.get_events(run_id)
    assert len(events) == 1
    ev = events[0]
    assert ev["run_id"] == run_id
    assert ev["seq"] == 0
    assert ev["author"] == "collector"
    assert ev["node"] == "collector_node"
    assert ev["event_type"] == "function_call"
    assert ev["payload"]["text"] == "Fetching financial data"
    assert ev["payload"]["function_calls"][0]["name"] == "calc_dcf"

    # Also check run's n_events counter updated
    run = tmp_store.get_run(run_id)
    assert run is not None
    assert run["n_events"] == 1


def test_finish_run_updates_status(tmp_store: AgentRunStore) -> None:
    """Test finish_run updates finished_at, status, last_text, error, and JSON state."""
    run_id = "bbca-finish-test"
    tmp_store.start_run(run_id, "BBCA", "prompt")
    tmp_store.append_event(run_id, 0, {"author": "writer", "text": "Draft report"})

    state = {"valuation": {"target_price": 10500, "recommendation": "BUY"}}
    tmp_store.finish_run(
        run_id,
        status="completed",
        last_text="Report generated successfully.",
        state=state,
    )

    run = tmp_store.get_run(run_id)
    assert run is not None
    assert run["status"] == "completed"
    assert run["finished_at"] is not None
    assert run["finished_at"] >= run["started_at"]
    assert run["last_text"] == "Report generated successfully."
    assert run["n_events"] == 1
    assert run["state"] == state
    assert run["error"] is None


def test_finish_run_with_error(tmp_store: AgentRunStore) -> None:
    """Test finish_run with status='failed' and error message."""
    run_id = "bbca-fail-test"
    tmp_store.start_run(run_id, "BBCA", "prompt")

    tmp_store.finish_run(
        run_id,
        status="failed",
        error="Connection refused to LLM provider",
    )

    run = tmp_store.get_run(run_id)
    assert run is not None
    assert run["status"] == "failed"
    assert "Connection refused" in run["error"]


def test_get_run_returns_dict(tmp_store: AgentRunStore) -> None:
    """Test get_run returns a dictionary representing the run and parses state_json."""
    run_id = "bbca-dict-test"
    tmp_store.start_run(run_id, "BBCA", "prompt")
    tmp_store.finish_run(run_id, status="completed", state={"k": "v"})

    run = tmp_store.get_run(run_id)
    assert isinstance(run, dict)
    assert run["run_id"] == run_id
    assert run["state"] == {"k": "v"}


def test_get_run_404_when_missing(tmp_store: AgentRunStore) -> None:
    """Test get_run returns None when run_id is not in database."""
    run = tmp_store.get_run("nonexistent-run-id-999")
    assert run is None


def test_list_runs_filters_by_ticker(tmp_store: AgentRunStore) -> None:
    """Test list_runs returns only runs matching the given ticker filter."""
    tmp_store.start_run("bbca-1", "BBCA", "prompt 1")
    tmp_store.start_run("bbri-1", "BBRI", "prompt 2")
    tmp_store.start_run("bbca-2", "BBCA", "prompt 3")

    bbca_runs = tmp_store.list_runs(ticker="BBCA")
    assert len(bbca_runs) == 2
    assert all(r["ticker"] == "BBCA" for r in bbca_runs)

    bbri_runs = tmp_store.list_runs(ticker="bbri")
    assert len(bbri_runs) == 1
    assert bbri_runs[0]["ticker"] == "BBRI"

    all_runs = tmp_store.list_runs()
    assert len(all_runs) == 3


def test_list_runs_orders_newest_first(tmp_store: AgentRunStore) -> None:
    """Test list_runs orders results newest first (started_at DESC)."""
    tmp_store.start_run("run-first", "BBCA", "prompt 1")
    time.sleep(0.01)
    tmp_store.start_run("run-second", "BBCA", "prompt 2")
    time.sleep(0.01)
    tmp_store.start_run("run-third", "BBCA", "prompt 3")

    runs = tmp_store.list_runs(limit=10)
    run_ids = [r["run_id"] for r in runs]
    assert run_ids == ["run-third", "run-second", "run-first"]


def test_get_events_orders_by_seq(tmp_store: AgentRunStore) -> None:
    """Test get_events returns all events for a run in strict ascending seq order."""
    run_id = "bbca-seq-test"
    tmp_store.start_run(run_id, "BBCA", "prompt")

    # Insert events out of order
    tmp_store.append_event(run_id, seq=2, event={"author": "writer", "text": "step 2"})
    tmp_store.append_event(run_id, seq=0, event={"author": "intake", "text": "step 0"})
    tmp_store.append_event(run_id, seq=1, event={"author": "modeler", "text": "step 1"})

    events = tmp_store.get_events(run_id)
    seqs = [e["seq"] for e in events]
    assert seqs == [0, 1, 2]
    assert events[0]["payload"]["text"] == "step 0"
    assert events[1]["payload"]["text"] == "step 1"
    assert events[2]["payload"]["text"] == "step 2"


def test_append_event_resilient_to_unknown_run(tmp_store: AgentRunStore) -> None:
    """Test that append_event defensively skips unknown run_ids without raising an exception."""
    # Should silently succeed/skip without crashing
    tmp_store.append_event("unknown-run-id", seq=0, event={"author": "test"})
    events = tmp_store.get_events("unknown-run-id")
    assert events == []


def test_concurrent_writes_dont_corrupt(tmp_store: AgentRunStore) -> None:
    """Test that concurrent writes across multiple threads do not corrupt the DB or raise errors."""
    run_id = "bbca-concurrent-test"
    tmp_store.start_run(run_id, "BBCA", "concurrent stress test")

    num_threads = 10
    events_per_thread = 10
    barrier = threading.Barrier(num_threads)
    errors: list[Exception] = []

    def worker(thread_idx: int) -> None:
        try:
            barrier.wait()
            for i in range(events_per_thread):
                seq = thread_idx * events_per_thread + i
                tmp_store.append_event(
                    run_id,
                    seq=seq,
                    event={
                        "author": f"thread_{thread_idx}",
                        "text": f"Event {i} from thread {thread_idx}",
                        "ts": time.time(),
                    },
                )
        except Exception as e:
            errors.append(e)

    threads = [
        threading.Thread(target=worker, args=(t,)) for t in range(num_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Concurrent worker encountered errors: {errors}"
    events = tmp_store.get_events(run_id)
    assert len(events) == num_threads * events_per_thread
    assert sorted([e["seq"] for e in events]) == list(range(num_threads * events_per_thread))


def test_default_db_path_resolves_under_repo() -> None:
    """Test default_db_path resolves to {project_root}/data/agent_runs.db."""
    p = default_db_path()
    assert p.endswith(os.path.join("data", "agent_runs.db"))
    assert os.path.isabs(p)


def test_serialize_event_adk_object_and_dict() -> None:
    """Test serialize_event on various event shapes (dict, ADK-like object with content parts and actions)."""
    # 1. Simple dict
    d_ev = {"author": "analyst", "node": "valuation", "text": "DCF complete", "ts": 123456.0}
    s1 = serialize_event(d_ev)
    assert s1["author"] == "analyst"
    assert s1["node"] == "valuation"
    assert s1["text"] == "DCF complete"
    assert s1["ts"] == 123456.0

    # 2. ADK-like object
    part1 = SimpleNamespace(text="First part", function_call=None, function_response=None)
    fc_part = SimpleNamespace(
        text=None,
        function_call=SimpleNamespace(name="calc_wacc", args={"rf": 0.06}, id="fc_1"),
        function_response=None,
    )
    content = SimpleNamespace(parts=[part1, fc_part])
    node_info = SimpleNamespace(name="intake_node", path="/intake")
    actions = SimpleNamespace(state_delta={"stage": "done"}, transfer_to_agent="writer")

    adk_ev = SimpleNamespace(
        author="intake",
        node_info=node_info,
        content=content,
        actions=actions,
        ts=9999.0,
    )

    s2 = serialize_event(adk_ev)
    assert s2["author"] == "intake"
    assert s2["node"] == "intake_node"
    assert "First part" in s2["text"]
    assert len(s2["function_calls"]) == 1
    assert s2["function_calls"][0]["name"] == "calc_wacc"
    assert s2["state_delta"] == {"stage": "done"}
    assert s2["transfer_to"] == "writer"
    assert s2["event_type"] == "function_call"


def test_api_endpoints_list_and_get(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Integration test for GET /api/agent/runs and GET /api/agent/runs/{run_id} via FastAPI TestClient."""
    from server.main import app

    test_db = str(tmp_path / "api_test.db")
    store = AgentRunStore(db_path=test_db)
    store.start_run("test-run-api-1", "BBCA", "Test prompt", provider="minimax", model="MiniMax-M3")
    store.append_event("test-run-api-1", 0, {"author": "tester", "text": "hello api"})
    store.finish_run("test-run-api-1", status="completed", state={"test_key": "test_val"})

    # Monkeypatch AgentRunStore default_db_path or AgentRunStore in router
    monkeypatch.setattr("agents.adk.storage.default_db_path", lambda: test_db)

    client = TestClient(app)

    # 1. GET /api/agent/runs
    res = client.get("/api/agent/runs?ticker=BBCA")
    assert res.status_code == 200
    data = res.json()
    assert "runs" in data
    assert len(data["runs"]) >= 1
    assert data["runs"][0]["run_id"] == "test-run-api-1"

    # 2. GET /api/agent/runs/{run_id}
    res_single = client.get("/api/agent/runs/test-run-api-1")
    assert res_single.status_code == 200
    single_data = res_single.json()
    assert single_data["run_id"] == "test-run-api-1"
    assert single_data["status"] == "completed"
    assert single_data["state"] == {"test_key": "test_val"}
    assert len(single_data["events"]) == 1
    assert single_data["events"][0]["author"] == "tester"

    # 3. GET /api/agent/runs/{run_id} 404 for missing
    res_404 = client.get("/api/agent/runs/nonexistent-run-999")
    assert res_404.status_code == 404
    assert res_404.json() == {"error": "not found"}


@pytest.mark.anyio
async def test_runner_run_report_persists_to_store(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that runner.run_report() persists all events, state, and status='completed' into AgentRunStore."""
    from unittest.mock import MagicMock, AsyncMock, patch
    from agents.adk import runner as runner_mod

    test_db = str(tmp_path / "runner_test.db")
    monkeypatch.setattr("agents.adk.storage.default_db_path", lambda: test_db)

    # Mock build_graph and Runner
    mock_event = SimpleNamespace(
        author="writer",
        node_info=SimpleNamespace(name="writer_node", path=""),
        content=SimpleNamespace(parts=[SimpleNamespace(text="Generated Report Text", function_call=None, function_response=None)]),
        actions=None,
        ts=time.time(),
    )

    async def fake_run_async(*args: Any, **kwargs: Any):
        yield mock_event

    mock_runner_inst = MagicMock()
    mock_runner_inst.run_async = fake_run_async

    mock_session = SimpleNamespace(state={"summary": "BBCA Report State"})
    mock_session_service = AsyncMock()
    mock_session_service.create_session = AsyncMock()
    mock_session_service.get_session = AsyncMock(return_value=mock_session)

    with patch.object(runner_mod, "build_graph", return_value=MagicMock()), \
         patch.object(runner_mod, "Runner", return_value=mock_runner_inst), \
         patch.object(runner_mod, "InMemorySessionService", return_value=mock_session_service):

        result = await runner_mod.run_report(ticker="BBCA", session_id="bbca-mock-run-001")

        assert result["session_id"] == "bbca-mock-run-001"
        assert result["last_text"] == "Generated Report Text"
        assert result["state"] == {"summary": "BBCA Report State"}

        store = AgentRunStore(db_path=test_db)
        saved_run = store.get_run("bbca-mock-run-001")
        assert saved_run is not None
        assert saved_run["status"] == "completed"
        assert saved_run["ticker"] == "BBCA"
        assert saved_run["last_text"] == "Generated Report Text"
        assert saved_run["state"] == {"summary": "BBCA Report State"}
        assert saved_run["n_events"] == 1

        events = store.get_events("bbca-mock-run-001")
        assert len(events) == 1
        assert events[0]["author"] == "writer"


@pytest.mark.anyio
async def test_runner_run_report_failure_persists_to_store(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that runner.run_report() persists status='failed' and error when run_async fails."""
    from unittest.mock import MagicMock, AsyncMock, patch
    from agents.adk import runner as runner_mod

    test_db = str(tmp_path / "runner_fail_test.db")
    monkeypatch.setattr("agents.adk.storage.default_db_path", lambda: test_db)

    async def fake_run_async_fail(*args: Any, **kwargs: Any):
        raise RuntimeError("LLM bridge connection timeout")
        yield  # make it an async generator

    mock_runner_inst = MagicMock()
    mock_runner_inst.run_async = fake_run_async_fail

    mock_session_service = AsyncMock()
    mock_session_service.create_session = AsyncMock()

    with patch.object(runner_mod, "build_graph", return_value=MagicMock()), \
         patch.object(runner_mod, "Runner", return_value=mock_runner_inst), \
         patch.object(runner_mod, "InMemorySessionService", return_value=mock_session_service):

        with pytest.raises(RuntimeError, match="LLM bridge connection timeout"):
            await runner_mod.run_report(ticker="BBCA", session_id="bbca-fail-run-002")

        store = AgentRunStore(db_path=test_db)
        saved_run = store.get_run("bbca-fail-run-002")
        assert saved_run is not None
        assert saved_run["status"] == "failed"
        assert "LLM bridge connection timeout" in saved_run["error"]

