# Copyright 2026 Sectors Hackathon
"""Stream lifecycle management for SSE live traces and SQLite persistence.

Handles:
- Reason taxonomy (client_disconnect, agent_error, provider_timeout, unknown).
- State delta accumulation from streaming events.
- Periodic / threshold-based background flushing of partial state_json.
- Graceful termination on client disconnect, timeouts, exceptions, or completion.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from .storage import AgentRunStore, InterruptReason, classify_interruption, serialize_event, to_json_safe

log = logging.getLogger(__name__)


class StreamLifecycleManager:
    """Manages the lifecycle, state accumulation, and persistence for an active agent run."""

    def __init__(
        self,
        run_id: str,
        ticker: str,
        prompt: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        store: AgentRunStore | None = None,
        flush_every_n: int = 1,
        flush_interval_sec: float = 2.0,
    ) -> None:
        self.run_id = run_id
        self.ticker = ticker.upper()
        self.prompt = prompt
        self.provider = provider
        self.model = model
        self.store = store or AgentRunStore()
        self.flush_every_n = flush_every_n
        self.flush_interval_sec = flush_interval_sec

        self.accumulated_state: dict[str, Any] = {}
        self.event_count: int = 0
        self._last_flush_time: float = time.time()
        self._is_dirty: bool = False
        self._closed: bool = False
        self._bg_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the run in the database and spawn background periodic flusher."""
        self.store.start_run(
            run_id=self.run_id,
            ticker=self.ticker,
            prompt=self.prompt,
            provider=self.provider,
            model=self.model,
        )
        self._last_flush_time = time.time()
        if self.flush_interval_sec > 0:
            self._bg_task = asyncio.create_task(self._periodic_flusher())

    async def _periodic_flusher(self) -> None:
        """Periodic background task to flush dirty state at regular intervals."""
        while not self._closed:
            try:
                await asyncio.sleep(self.flush_interval_sec)
                if self._closed:
                    break
                if self._is_dirty:
                    self.flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.warning("Background flush error for %s: %s", self.run_id, e)

    def _extract_state_delta(self, ev: Any, serialized_frame: dict[str, Any]) -> dict[str, Any] | None:
        """Extract state_delta dictionary from event object or serialized frame."""
        # 1. From event.actions.state_delta
        actions = getattr(ev, "actions", None)
        if actions is not None:
            sd = getattr(actions, "state_delta", None)
            if sd and isinstance(sd, (dict, list)):
                try:
                    return dict(sd) if isinstance(sd, dict) else {"delta": sd}
                except Exception:
                    pass

        # 2. From event.state_delta directly
        if hasattr(ev, "state_delta"):
            sd = getattr(ev, "state_delta", None)
            if sd and isinstance(sd, dict):
                return sd

        # 3. From serialized_frame["state_delta"]
        sd_frame = serialized_frame.get("state_delta")
        if sd_frame and isinstance(sd_frame, dict):
            return sd_frame

        return None

    async def on_event(self, seq: int, ev: Any) -> dict[str, Any]:
        """Record event, accumulate state delta, check flush conditions, and return frame."""
        frame = serialize_event(ev)
        frame["seq"] = seq

        # Append to SQLite agent_events
        self.store.append_event(self.run_id, seq, ev)
        self.event_count += 1

        # Extract and accumulate state_delta
        delta = self._extract_state_delta(ev, frame)
        if delta and isinstance(delta, dict):
            for k, v in delta.items():
                self.accumulated_state[k] = v
            self._is_dirty = True

        # Check flush triggers (by event count or elapsed time)
        now = time.time()
        if self._is_dirty:
            if (self.flush_every_n > 0 and self.event_count % self.flush_every_n == 0) or (
                now - self._last_flush_time >= self.flush_interval_sec
            ):
                self.flush()

        return frame

    def flush(self) -> None:
        """Synchronously persist accumulated state to SQLite."""
        try:
            self.store.update_state(self.run_id, self.accumulated_state)
            self._is_dirty = False
            self._last_flush_time = time.time()
        except Exception as e:
            log.warning("Failed to flush state for %s: %s", self.run_id, e)

    async def on_interrupt(
        self,
        exc: BaseException | None = None,
        error_msg: str | None = None,
        reason: str | InterruptReason | None = None,
    ) -> None:
        """Handle stream interruption (e.g. client disconnect). Persist final partial state."""
        self._closed = True
        self.flush()

        if reason is None:
            if isinstance(exc, (GeneratorExit, asyncio.CancelledError)):
                reason = InterruptReason.CLIENT_DISCONNECT
            else:
                reason = classify_interruption(exc or error_msg)

        err = error_msg or (str(exc) if exc is not None else "Stream interrupted")
        try:
            self.store.finish_run(
                self.run_id,
                status="interrupted",
                last_text="",
                state=self.accumulated_state,
                error=err,
                reason=reason,
            )
        except Exception:
            log.exception("finish_run (interrupted) failed for %s", self.run_id)

    async def on_error(
        self,
        exc: BaseException,
        error_msg: str | None = None,
        reason: str | InterruptReason | None = None,
    ) -> None:
        """Handle agent or provider error. Persist final partial state."""
        self._closed = True
        self.flush()

        if reason is None:
            reason = classify_interruption(exc or error_msg)

        err = error_msg or str(exc)
        # Determine status: if provider timeout, we can mark as failed or interrupted with reason provider_timeout
        try:
            self.store.finish_run(
                self.run_id,
                status="failed",
                last_text="",
                state=self.accumulated_state,
                error=err,
                reason=reason,
            )
        except Exception:
            log.exception("finish_run (failed) failed for %s", self.run_id)

    async def on_complete(
        self,
        final_state: dict | None = None,
        last_text: str = "",
    ) -> None:
        """Handle successful run completion. Persist full state."""
        self._closed = True
        if final_state and isinstance(final_state, dict):
            self.accumulated_state.update(final_state)
        self.flush()

        try:
            self.store.finish_run(
                self.run_id,
                status="completed",
                last_text=last_text,
                state=self.accumulated_state,
                error=None,
                reason=None,
            )
        except Exception:
            log.exception("finish_run (completed) failed for %s", self.run_id)

    async def close(self) -> None:
        """Cancel background flusher and guarantee state flush."""
        self._closed = True
        if self._bg_task and not self._bg_task.done():
            self._bg_task.cancel()
            try:
                await self._bg_task
            except (asyncio.CancelledError, Exception):
                pass
        if self._is_dirty:
            self.flush()
