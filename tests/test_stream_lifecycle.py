# Copyright 2026 Sectors Hackathon
"""Tests for SSE stream lifecycle, reason taxonomy, and partial state persistence."""

from __future__ import annotations

import asyncio
import pathlib
import pytest
from types import SimpleNamespace
from typing import Any

from server.storage import AgentRunStore, InterruptReason, classify_interruption
from server.stream_lifecycle import StreamLifecycleManager


@pytest.fixture
def tmp_store(tmp_path: pathlib.Path) -> AgentRunStore:
    """Fixture providing an isolated AgentRunStore backed by a temporary SQLite file."""
    db_file = str(tmp_path / "test_lifecycle.db")
    return AgentRunStore(db_path=db_file)


def test_interruption_reason_classification() -> None:
    """Test classification of various exceptions and error messages into InterruptReason taxonomy."""
    # 1. Client disconnect
    assert classify_interruption(GeneratorExit()) == InterruptReason.CLIENT_DISCONNECT.value
    assert classify_interruption(asyncio.CancelledError()) == InterruptReason.CLIENT_DISCONNECT.value
    assert classify_interruption("client disconnected after 3 events") == InterruptReason.CLIENT_DISCONNECT.value
    assert classify_interruption("Client disconnect detected") == InterruptReason.CLIENT_DISCONNECT.value

    # 2. Provider timeout
    assert classify_interruption(asyncio.TimeoutError()) == InterruptReason.PROVIDER_TIMEOUT.value
    assert classify_interruption(TimeoutError()) == InterruptReason.PROVIDER_TIMEOUT.value
    assert classify_interruption("LLM bridge connection timed out after 30s") == InterruptReason.PROVIDER_TIMEOUT.value
    assert classify_interruption("ReadTimeout from litellm") == InterruptReason.PROVIDER_TIMEOUT.value

    # 3. Agent error
    assert classify_interruption(RuntimeError("Division by zero in calc_dcf")) == InterruptReason.AGENT_ERROR.value
    assert classify_interruption(ValueError("Invalid financial metric")) == InterruptReason.AGENT_ERROR.value
    assert classify_interruption("Tool calc_wacc failed with KeyError") == InterruptReason.AGENT_ERROR.value

    # 4. Unknown
    assert classify_interruption(None) == InterruptReason.UNKNOWN.value
    assert classify_interruption("") == InterruptReason.UNKNOWN.value


@pytest.mark.anyio
async def test_stream_interrupted_at_event_3_persists_partial_state_and_reason(tmp_store: AgentRunStore) -> None:
    """Feed 5-event SSE stream, abort at event 3, verify run row in SQLite has
    status='interrupted', reason='client_disconnect', and state_json has partial events flushed.
    """
    run_id = "vktr-stream-test-01"
    ticker = "VKTR"
    lifecycle = StreamLifecycleManager(
        run_id=run_id,
        ticker=ticker,
        prompt="Generate report for VKTR",
        store=tmp_store,
        flush_every_n=1,
    )
    await lifecycle.start()

    # Create 5 mock events with incremental state deltas
    events = [
        SimpleNamespace(
            author="collector",
            node_info=SimpleNamespace(name="collector_node", path=""),
            content=SimpleNamespace(parts=[SimpleNamespace(text="Collector starting", function_call=None, function_response=None)]),
            actions=SimpleNamespace(state_delta={"collector_output": {"filings_count": 5}}, transfer_to_agent=None),
        ),
        SimpleNamespace(
            author="news_harvester",
            node_info=SimpleNamespace(name="news_node", path=""),
            content=SimpleNamespace(parts=[SimpleNamespace(text="News search", function_call=None, function_response=None)]),
            actions=SimpleNamespace(state_delta={"news_output": {"articles_count": 8}}, transfer_to_agent=None),
        ),
        SimpleNamespace(
            author="modeler",
            node_info=SimpleNamespace(name="modeler_node", path=""),
            content=SimpleNamespace(parts=[SimpleNamespace(text="DCF calculation", function_call=None, function_response=None)]),
            actions=SimpleNamespace(state_delta={"modeler_output": {"tp": 12500}}, transfer_to_agent=None),
        ),
        SimpleNamespace(
            author="writer",
            node_info=SimpleNamespace(name="writer_node", path=""),
            content=SimpleNamespace(parts=[SimpleNamespace(text="Drafting section 1", function_call=None, function_response=None)]),
            actions=SimpleNamespace(state_delta={"writer_output": {"draft": "partial"}}, transfer_to_agent=None),
        ),
        SimpleNamespace(
            author="critic",
            node_info=SimpleNamespace(name="critic_node", path=""),
            content=SimpleNamespace(parts=[SimpleNamespace(text="Report critique", function_call=None, function_response=None)]),
            actions=SimpleNamespace(state_delta={"critic_output": {"grade": "A"}}, transfer_to_agent=None),
        ),
    ]

    # Process first 3 events (seq 0, 1, 2), then simulate client disconnect
    seq = 0
    try:
        for ev in events:
            if seq == 3:
                # Abort at event index 3 (after processing seq 0, 1, 2)
                raise GeneratorExit("Client disconnected mid-stream")
            await lifecycle.on_event(seq, ev)
            seq += 1
    except GeneratorExit as exc:
        await lifecycle.on_interrupt(exc=exc, error_msg=f"client disconnected after {seq} events")
    finally:
        await lifecycle.close()

    # Verify SQLite row
    run = tmp_store.get_run(run_id)
    assert run is not None
    assert run["run_id"] == run_id
    assert run["ticker"] == "VKTR"
    assert run["status"] == "interrupted"
    assert run["reason"] == "client_disconnect"
    assert "client disconnected after 3 events" in (run["error"] or "")
    assert run["n_events"] == 3

    # Verify partial state_json contains collector_output, news_output, and modeler_output
    state = run["state"]
    assert isinstance(state, dict)
    assert "collector_output" in state
    assert state["collector_output"] == {"filings_count": 5}
    assert "news_output" in state
    assert state["news_output"] == {"articles_count": 8}
    assert "modeler_output" in state
    assert state["modeler_output"] == {"tp": 12500}

    # Verify events beyond event 3 are not in state
    assert "writer_output" not in state
    assert "critic_output" not in state


@pytest.mark.anyio
async def test_stream_provider_timeout_persists_reason(tmp_store: AgentRunStore) -> None:
    """Test that a provider timeout sets status='failed' or 'interrupted' with reason='provider_timeout'."""
    run_id = "timeout-stream-test"
    lifecycle = StreamLifecycleManager(
        run_id=run_id,
        ticker="BBCA",
        prompt="Timeout prompt",
        store=tmp_store,
    )
    await lifecycle.start()

    ev = {"author": "intake", "text": "start", "state_delta": {"intake": "done"}}
    await lifecycle.on_event(0, ev)

    # Provider timeout exception
    timeout_exc = TimeoutError("CommandCode bridge timeout after 60s")
    await lifecycle.on_error(exc=timeout_exc)
    await lifecycle.close()

    run = tmp_store.get_run(run_id)
    assert run is not None
    assert run["status"] == "failed"
    assert run["reason"] == "provider_timeout"
    assert run["state"] == {"intake": "done"}
    assert "CommandCode bridge timeout" in run["error"]


@pytest.mark.anyio
async def test_stream_completion_persists_full_state(tmp_store: AgentRunStore) -> None:
    """Test that normal stream completion sets status='completed', reason=None, and full state."""
    run_id = "completed-stream-test"
    lifecycle = StreamLifecycleManager(
        run_id=run_id,
        ticker="ASII",
        prompt="Full ASII report",
        store=tmp_store,
    )
    await lifecycle.start()

    await lifecycle.on_event(0, {"author": "collector", "text": "c", "state_delta": {"step1": "ok"}})
    await lifecycle.on_event(1, {"author": "writer", "text": "w", "state_delta": {"step2": "ok"}})
    await lifecycle.on_complete(final_state={"step3": "final"}, last_text="Institutional Report for ASII")
    await lifecycle.close()

    run = tmp_store.get_run(run_id)
    assert run is not None
    assert run["status"] == "completed"
    assert run["reason"] is None
    assert run["error"] is None
    assert run["last_text"] == "Institutional Report for ASII"
    assert run["state"] == {"step1": "ok", "step2": "ok", "step3": "final"}
    assert run["n_events"] == 2
