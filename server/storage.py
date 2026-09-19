# Copyright 2026 Sectors Hackathon
"""SQLite persistence layer for ADK agent runs, lifecycle states, and event traces.

Schema:
- agent_runs: run metadata, status, reason taxonomy, started/finished timestamps, state_json, and errors.
- agent_events: granular event-by-event traces per run, indexed by sequence number.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import pathlib
import sqlite3
import threading
import time
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class InterruptReason(str, Enum):
    """Reason taxonomy for interrupted or failed agent runs."""
    CLIENT_DISCONNECT = "client_disconnect"
    AGENT_ERROR = "agent_error"
    PROVIDER_TIMEOUT = "provider_timeout"
    UNKNOWN = "unknown"


def classify_interruption(exc: BaseException | str | None) -> str:
    """Classify an exception or error string into the InterruptReason taxonomy."""
    if exc is None:
        return InterruptReason.UNKNOWN.value

    # Direct type checking if an exception instance was passed
    if isinstance(exc, (GeneratorExit,)):
        return InterruptReason.CLIENT_DISCONNECT.value

    # Check for asyncio/httpx cancelled or timeout
    exc_type_name = type(exc).__name__ if isinstance(exc, BaseException) else ""
    if "CancelledError" in exc_type_name or "GeneratorExit" in exc_type_name:
        return InterruptReason.CLIENT_DISCONNECT.value
    if "Timeout" in exc_type_name or isinstance(exc, (TimeoutError,)):
        return InterruptReason.PROVIDER_TIMEOUT.value

    exc_str = str(exc).lower()
    if not exc_str.strip():
        return InterruptReason.UNKNOWN.value

    # Check disconnect patterns
    if any(k in exc_str for k in ("client disconnect", "client_disconnect", "disconnect", "broken pipe", "connection reset", "cancelled")):
        return InterruptReason.CLIENT_DISCONNECT.value

    # Check timeout patterns
    if any(k in exc_str for k in ("timeout", "timed out", "readtimeout", "connecttimeout", "deadline exceeded", "deadline_exceeded")):
        return InterruptReason.PROVIDER_TIMEOUT.value

    # Check agent error patterns
    if isinstance(exc, Exception) or any(k in exc_str for k in ("error", "exception", "failed", "invalid", "keyerror", "valueerror")):
        return InterruptReason.AGENT_ERROR.value

    return InterruptReason.UNKNOWN.value


def default_db_path() -> str:
    """Return {project_root}/data/agent_runs.db. project_root inferred from this file's location."""
    try:
        import agents.adk.storage as _adk_storage
        return _adk_storage.default_db_path()
    except Exception:
        project_root = pathlib.Path(__file__).resolve().parents[1]
        return str(project_root / "data" / "agent_runs.db")


def to_json_safe(obj: Any) -> Any:
    """Recursively convert object to JSON-safe primitives."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [to_json_safe(x) for x in obj]
    if hasattr(obj, "model_dump") and callable(obj.model_dump):
        try:
            return to_json_safe(obj.model_dump())
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        try:
            return to_json_safe(obj.__dict__)
        except Exception:
            pass
    return str(obj)


def serialize_event(event: Any) -> dict[str, Any]:
    """Extract {author, node, event_type, ts, text, function_calls, state_delta, transfer_to}
    from google.adk Event or dict. JSON-safe.
    """
    if isinstance(event, dict):
        author = event.get("author", "") or ""
        node = event.get("node", "") or ""
        event_type = event.get("event_type", "") or ""
        ts = event.get("ts", time.time())
        text = event.get("text", "") or ""
        function_calls = event.get("function_calls", []) or []
        function_responses = event.get("function_responses", []) or []
        state_delta = event.get("state_delta", None)
        transfer_to = event.get("transfer_to", None)
        if not event_type:
            if function_calls:
                event_type = "function_call"
            elif function_responses:
                event_type = "function_response"
            elif transfer_to:
                event_type = "transfer"
            elif text and author:
                event_type = "agent_message"
            else:
                event_type = "message"
        return {
            "author": author,
            "node": node,
            "event_type": event_type,
            "ts": ts,
            "text": text,
            "function_calls": to_json_safe(function_calls),
            "function_responses": to_json_safe(function_responses),
            "state_delta": to_json_safe(state_delta),
            "transfer_to": transfer_to,
        }

    author = getattr(event, "author", "") or ""
    node_info = getattr(event, "node_info", None)
    node = ""
    if node_info is not None:
        node = getattr(node_info, "name", "") or getattr(node_info, "path", "") or ""
    if not node:
        node = getattr(event, "node", "") or ""

    ts = getattr(event, "ts", None)
    if ts is None:
        ts = getattr(event, "timestamp", None)
    if ts is None:
        ts = time.time()

    text_parts: list[str] = []
    function_calls: list[dict[str, Any]] = []
    function_responses: list[dict[str, Any]] = []

    content = getattr(event, "content", None)
    if content is not None:
        parts = getattr(content, "parts", None) or []
        for p in parts:
            t = getattr(p, "text", None)
            if t:
                text_parts.append(t)
            fc = getattr(p, "function_call", None)
            if fc is not None:
                function_calls.append(
                    {
                        "name": getattr(fc, "name", ""),
                        "args": to_json_safe(getattr(fc, "args", {})),
                        "id": getattr(fc, "id", ""),
                    }
                )
            fr = getattr(p, "function_response", None)
            if fr is not None:
                resp = getattr(fr, "response", fr)
                function_responses.append(
                    {
                        "name": getattr(fr, "name", ""),
                        "response": to_json_safe(resp),
                        "id": getattr(fr, "id", ""),
                    }
                )

    raw_text = getattr(event, "text", "")
    if raw_text and not text_parts:
        text_parts.append(str(raw_text))

    raw_fcs = getattr(event, "function_calls", None)
    if raw_fcs and not function_calls:
        function_calls = [to_json_safe(fc) for fc in raw_fcs]

    actions = getattr(event, "actions", None)
    state_delta = None
    transfer_to = None
    if actions is not None:
        sd = getattr(actions, "state_delta", None)
        if sd:
            try:
                state_delta = dict(sd)
            except Exception:
                state_delta = str(sd)
        transfer_to = getattr(actions, "transfer_to_agent", None)

    if state_delta is None and hasattr(event, "state_delta"):
        state_delta = getattr(event, "state_delta", None)
    if transfer_to is None and hasattr(event, "transfer_to"):
        transfer_to = getattr(event, "transfer_to", None)

    event_type = getattr(event, "event_type", None) or getattr(event, "type", None)
    if not event_type:
        if function_calls:
            event_type = "function_call"
        elif function_responses:
            event_type = "function_response"
        elif transfer_to:
            event_type = "transfer"
        elif text_parts and author:
            event_type = "agent_message"
        else:
            event_type = "message"

    return {
        "author": author,
        "node": node,
        "event_type": str(event_type),
        "ts": ts,
        "text": "\n".join(text_parts)[:8000] if text_parts else "",
        "function_calls": to_json_safe(function_calls),
        "function_responses": to_json_safe(function_responses),
        "state_delta": to_json_safe(state_delta),
        "transfer_to": transfer_to,
    }


class AgentRunStore:
    def __init__(self, db_path: str | None = None):
        """Default db_path = project_root / 'data' / 'agent_runs.db'.
        Auto-create data/ dir if missing.
        Open connection with check_same_thread=False.
        Run schema migrations on init (CREATE TABLE IF NOT EXISTS + ALTER TABLE if needed).
        """
        self.db_path = db_path or default_db_path()
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        self._lock = threading.Lock()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL;")
            cur.execute("PRAGMA busy_timeout=5000;")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_runs (
                    run_id        TEXT PRIMARY KEY,
                    ticker        TEXT NOT NULL,
                    started_at    REAL NOT NULL,
                    finished_at   REAL,
                    status        TEXT NOT NULL,
                    reason        TEXT,
                    provider      TEXT,
                    model         TEXT,
                    prompt        TEXT,
                    n_events      INTEGER DEFAULT 0,
                    last_text     TEXT,
                    state_json    TEXT,
                    error         TEXT
                );
                """
            )
            # Schema migration: Ensure 'reason' column exists on older tables
            cur.execute("PRAGMA table_info(agent_runs);")
            cols = [row[1] for row in cur.fetchall()]
            if "reason" not in cols:
                try:
                    cur.execute("ALTER TABLE agent_runs ADD COLUMN reason TEXT;")
                except sqlite3.OperationalError:
                    pass

            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_agent_runs_ticker ON agent_runs(ticker);"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_agent_runs_started ON agent_runs(started_at DESC);"
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_events (
                    run_id        TEXT NOT NULL,
                    seq           INTEGER NOT NULL,
                    author        TEXT,
                    node          TEXT,
                    event_type    TEXT,
                    ts            REAL,
                    payload_json  TEXT NOT NULL,
                    PRIMARY KEY (run_id, seq),
                    FOREIGN KEY (run_id) REFERENCES agent_runs(run_id) ON DELETE CASCADE
                );
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_agent_events_run ON agent_events(run_id, seq);"
            )
            # Sectors payload cache - minimize Sectors API credit burn.
            # Key = sha256(endpoint_path + normalized_params), payload = raw JSON
            # blob, expires_at = unix seconds. Wrapped by sectors._get().
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sectors_cache (
                    cache_key    TEXT PRIMARY KEY,
                    endpoint     TEXT NOT NULL,
                    fetched_at   REAL NOT NULL,
                    expires_at   REAL NOT NULL,
                    payload_json TEXT NOT NULL
                );
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_sectors_cache_expiry ON sectors_cache(expires_at);"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_sectors_cache_endpoint ON sectors_cache(endpoint);"
            )
            self.conn.commit()

    def start_run(
        self,
        run_id: str,
        ticker: str,
        prompt: str | None,
        provider: str | None = None,
        model: str | None = None,
    ) -> int:
        """Set status='running', started_at=now() on agent_runs row for run_id.

        If a row with this run_id already exists (e.g. resume after interrupt),
        UPDATE in place to preserve the existing event count, finished_at, and
        accumulated state. Otherwise INSERT a fresh row.

        Returns base_seq - the next event seq to use (n_events of the existing row
        if resuming, 0 if fresh). The SSE handler must add its local counter to
        base_seq when appending events, so new events never collide with prior seqs.
        """
        started_at = time.time()
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("SELECT n_events FROM agent_runs WHERE run_id = ?", (run_id,))
            row = cur.fetchone()
            if row is not None:
                # Resume: keep existing events, just flip status + reset started_at
                base_seq = int(row["n_events"] or 0)
                cur.execute(
                    """
                    UPDATE agent_runs
                    SET status = 'running',
                        started_at = ?,
                        finished_at = NULL,
                        reason = NULL,
                        error = NULL,
                        provider = COALESCE(?, provider),
                        model = COALESCE(?, model),
                        prompt = COALESCE(?, prompt)
                    WHERE run_id = ?
                    """,
                    (started_at, provider, model, prompt, run_id),
                )
            else:
                # Fresh run
                base_seq = 0
                cur.execute(
                    """
                    INSERT INTO agent_runs (
                        run_id, ticker, started_at, finished_at, status, reason,
                        provider, model, prompt, n_events, last_text, state_json, error
                    ) VALUES (?, ?, ?, NULL, 'running', NULL, ?, ?, ?, 0, NULL, NULL, NULL)
                    """,
                    (run_id, ticker.upper(), started_at, provider, model, prompt),
                )
            self.conn.commit()
            return base_seq

    def append_event(self, run_id: str, seq: int, event: Any) -> None:
        """Insert one agent_events row. Extract author/node/event_type/ts from event;
        serialize full event to JSON for payload_json.
        Skip if run_id unknown (defensive - run_id may not exist if start_run race).
        Commit after each insert.
        """
        serialized = serialize_event(event)
        author = serialized.get("author", "")
        node = serialized.get("node", "")
        event_type = serialized.get("event_type", "message")
        ts = serialized.get("ts", time.time())
        payload_json = json.dumps(serialized, ensure_ascii=False, default=str)

        with self._lock:
            cur = self.conn.cursor()
            cur.execute("SELECT 1 FROM agent_runs WHERE run_id = ?", (run_id,))
            if cur.fetchone() is None:
                return
            cur.execute(
                """
                INSERT OR REPLACE INTO agent_events (run_id, seq, author, node, event_type, ts, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, seq, author, node, event_type, ts, payload_json),
            )
            cur.execute(
                "UPDATE agent_runs SET n_events = (SELECT COUNT(*) FROM agent_events WHERE run_id = ?) WHERE run_id = ?",
                (run_id, run_id),
            )
            self.conn.commit()

    def update_state(self, run_id: str, state: dict | Any) -> None:
        """Update state_json for an active or interrupted run without altering finished_at or status."""
        state_json = (
            json.dumps(to_json_safe(state), ensure_ascii=False, default=str)
            if state is not None
            else None
        )
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(
                """
                UPDATE agent_runs
                SET state_json = ?,
                    n_events = (SELECT COUNT(*) FROM agent_events WHERE run_id = ?)
                WHERE run_id = ?
                """,
                (state_json, run_id, run_id),
            )
            self.conn.commit()

    def finish_run(
        self,
        run_id: str,
        *,
        status: str,
        last_text: str = "",
        state: dict | None = None,
        error: str | None = None,
        reason: str | InterruptReason | None = None,
    ) -> None:
        """Update agent_runs: finished_at=now, status, reason, n_events, last_text, state_json, error."""
        finished_at = time.time()
        last_text_trunc = (last_text or "")[:8000]
        error_trunc = str(error)[:2000] if error is not None else None

        reason_str: str | None = None
        if reason is not None:
            reason_str = reason.value if hasattr(reason, "value") else str(reason)
        elif status in ("interrupted", "failed"):
            reason_str = classify_interruption(error)

        with self._lock:
            cur = self.conn.cursor()
            if state is not None:
                state_json = json.dumps(to_json_safe(state), ensure_ascii=False, default=str)
                cur.execute(
                    """
                    UPDATE agent_runs
                    SET finished_at = ?,
                        status = ?,
                        reason = ?,
                        n_events = (SELECT COUNT(*) FROM agent_events WHERE run_id = ?),
                        last_text = ?,
                        state_json = ?,
                        error = ?
                    WHERE run_id = ?
                    """,
                    (
                        finished_at,
                        status,
                        reason_str,
                        run_id,
                        last_text_trunc,
                        state_json,
                        error_trunc,
                        run_id,
                    ),
                )
            else:
                cur.execute(
                    """
                    UPDATE agent_runs
                    SET finished_at = ?,
                        status = ?,
                        reason = ?,
                        n_events = (SELECT COUNT(*) FROM agent_events WHERE run_id = ?),
                        last_text = ?,
                        error = ?
                    WHERE run_id = ?
                    """,
                    (
                        finished_at,
                        status,
                        reason_str,
                        run_id,
                        last_text_trunc,
                        error_trunc,
                        run_id,
                    ),
                )
            self.conn.commit()

    def get_run(self, run_id: str) -> dict | None:
        """Return agent_runs row as dict (parse state_json). None if not found."""
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM agent_runs WHERE run_id = ?", (run_id,))
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            if d.get("state_json"):
                try:
                    d["state"] = json.loads(d["state_json"])
                except Exception:
                    d["state"] = d["state_json"]
            else:
                d["state"] = {}
            return d

    def list_runs(self, ticker: str | None = None, limit: int = 50) -> list[dict]:
        """Return recent runs, optionally filtered by ticker. Newest first."""
        with self._lock:
            cur = self.conn.cursor()
            if ticker and ticker.strip():
                cur.execute(
                    "SELECT * FROM agent_runs WHERE UPPER(ticker) = ? ORDER BY started_at DESC LIMIT ?",
                    (ticker.upper().strip(), limit),
                )
            else:
                cur.execute(
                    "SELECT * FROM agent_runs ORDER BY started_at DESC LIMIT ?",
                    (limit,),
                )
            rows = cur.fetchall()
            results: list[dict] = []
            for row in rows:
                d = dict(row)
                if d.get("state_json"):
                    try:
                        d["state"] = json.loads(d["state_json"])
                    except Exception:
                        d["state"] = d["state_json"]
                else:
                    d["state"] = {}
                results.append(d)
            return results

    def get_recent_interrupted_run(self, ticker: str, within_seconds: float = 600.0) -> dict | None:
        """Return most recent 'interrupted' run for ticker if it finished within the last `within_seconds`.

        Used by SSE stream to append new events to an existing interrupted row instead of
        creating a duplicate row when the client reconnects shortly after disconnect.
        Returns None if no recent interrupted run exists.
        """
        import time as _time
        cutoff = _time.time() - within_seconds
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(
                """
                SELECT * FROM agent_runs
                WHERE UPPER(ticker) = ?
                  AND status = 'interrupted'
                  AND finished_at >= ?
                ORDER BY finished_at DESC
                LIMIT 1
                """,
                (ticker.upper().strip(), cutoff),
            )
            row = cur.fetchone()
            if not row:
                return None
            return dict(row)

    def get_latest_completed(self, ticker: str | None = None) -> dict | None:
        """Return latest run with status in ('completed', 'interrupted', 'failed') for ticker (or across all tickers if ticker is None), or None."""
        with self._lock:
            cur = self.conn.cursor()
            if ticker and ticker.strip():
                cur.execute(
                    """
                    SELECT * FROM agent_runs
                    WHERE UPPER(ticker) = ?
                      AND status IN ('completed', 'interrupted', 'failed')
                    ORDER BY started_at DESC
                    LIMIT 1
                    """,
                    (ticker.upper().strip(),),
                )
            else:
                cur.execute(
                    """
                    SELECT * FROM agent_runs
                    WHERE status IN ('completed', 'interrupted', 'failed')
                    ORDER BY started_at DESC
                    LIMIT 1
                    """
                )
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            if d.get("state_json"):
                try:
                    d["state"] = json.loads(d["state_json"])
                except Exception:
                    d["state"] = d["state_json"]
            else:
                d["state"] = {}
            return d

    def get_run_with_events(self, run_id: str) -> dict | None:
        """Return run dict with its ordered events attached in a single transaction/lock."""
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM agent_runs WHERE run_id = ?", (run_id,))
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            if d.get("state_json"):
                try:
                    d["state"] = json.loads(d["state_json"])
                except Exception:
                    d["state"] = d["state_json"]
            else:
                d["state"] = {}

            cur.execute(
                "SELECT * FROM agent_events WHERE run_id = ? ORDER BY seq ASC",
                (run_id,),
            )
            event_rows = cur.fetchall()
            events: list[dict] = []
            for erow in event_rows:
                ed = dict(erow)
                if ed.get("payload_json"):
                    try:
                        ed["payload"] = json.loads(ed["payload_json"])
                    except Exception:
                        ed["payload"] = ed["payload_json"]
                else:
                    ed["payload"] = {}
                if isinstance(ed["payload"], dict):
                    for k in ("text", "function_calls", "function_responses", "state_delta", "transfer_to"):
                        if k in ed["payload"] and k not in ed:
                            ed[k] = ed["payload"][k]
                    if "state_delta" in ed["payload"] and isinstance(ed["payload"]["state_delta"], dict):
                        ed["state_delta_keys"] = list(ed["payload"]["state_delta"].keys())
                    elif "state_delta_keys" not in ed:
                        ed["state_delta_keys"] = []
                events.append(ed)
            d["events"] = events
            return d

    def get_events(self, run_id: str) -> list[dict]:
        """Return all events for run_id, ordered by seq. Parse payload_json."""
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT * FROM agent_events WHERE run_id = ? ORDER BY seq ASC",
                (run_id,),
            )
            rows = cur.fetchall()
            results: list[dict] = []
            for row in rows:
                d = dict(row)
                if d.get("payload_json"):
                    try:
                        d["payload"] = json.loads(d["payload_json"])
                    except Exception:
                        d["payload"] = d["payload_json"]
                else:
                    d["payload"] = {}
                if isinstance(d["payload"], dict):
                    for k in ("text", "function_calls", "function_responses", "state_delta", "transfer_to"):
                        if k in d["payload"] and k not in d:
                            d[k] = d["payload"][k]
                    if "state_delta" in d["payload"] and isinstance(d["payload"]["state_delta"], dict):
                        ed_keys = list(d["payload"]["state_delta"].keys())
                        d["state_delta_keys"] = ed_keys
                    elif "state_delta_keys" not in d:
                        d["state_delta_keys"] = []
                results.append(d)
            return results

    def get_runs_summary(self) -> dict[str, Any]:
        """Return per-ticker latest run + total runs + interrupt reason distribution."""
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM agent_runs ORDER BY started_at DESC")
            rows = cur.fetchall()

            total_runs = len(rows)
            status_counts = {
                "completed": 0,
                "interrupted": 0,
                "failed": 0,
                "running": 0,
            }
            interrupt_reasons = {
                "client_disconnect": 0,
                "agent_error": 0,
                "provider_timeout": 0,
                "unknown": 0,
            }
            tickers_map: dict[str, dict[str, Any]] = {}

            for row in rows:
                d = dict(row)
                t = d["ticker"].upper()
                st = d["status"]
                reason = d.get("reason")

                if d.get("state_json"):
                    try:
                        d["state"] = json.loads(d["state_json"])
                    except Exception:
                        d["state"] = d["state_json"]
                else:
                    d["state"] = {}

                # Global counts
                status_counts[st] = status_counts.get(st, 0) + 1
                if reason:
                    interrupt_reasons[reason] = interrupt_reasons.get(reason, 0) + 1
                elif st in ("interrupted", "failed"):
                    inferred_reason = classify_interruption(d.get("error"))
                    interrupt_reasons[inferred_reason] = interrupt_reasons.get(inferred_reason, 0) + 1

                # Per-ticker breakdown
                if t not in tickers_map:
                    tickers_map[t] = {
                        "ticker": t,
                        "total_runs": 0,
                        "latest_run": d,
                        "status_counts": {"completed": 0, "interrupted": 0, "failed": 0, "running": 0},
                        "interrupt_reasons": {"client_disconnect": 0, "agent_error": 0, "provider_timeout": 0, "unknown": 0},
                    }
                t_entry = tickers_map[t]
                t_entry["total_runs"] += 1
                t_entry["status_counts"][st] = t_entry["status_counts"].get(st, 0) + 1
                if reason:
                    t_entry["interrupt_reasons"][reason] = t_entry["interrupt_reasons"].get(reason, 0) + 1
                elif st in ("interrupted", "failed"):
                    inferred_reason = classify_interruption(d.get("error"))
                    t_entry["interrupt_reasons"][inferred_reason] = t_entry["interrupt_reasons"].get(inferred_reason, 0) + 1

            return {
                "total_runs": total_runs,
                "status_counts": status_counts,
                "status_distribution": status_counts,
                "interrupt_reasons": interrupt_reasons,
                "interrupt_reason_distribution": interrupt_reasons,
                "tickers": tickers_map,
                "by_ticker": tickers_map,
            }

    def close(self) -> None:
        """Close SQLite connection."""
        with self._lock:
            try:
                self.conn.close()
            except Exception:
                pass


# ──────────────────────────────────────────────────────────────────────────────
# Sectors payload cache - minimize Sectors API credit burn.
#
# Lives in the same SQLite file as Storage but is a separate singleton so
# hot-path lookups don't acquire the Storage row lock. Wrapped by sectors._get()
# so every endpoint transparently caches. TTL is per-endpoint (see sectors.py
# _TTL_BY_PREFIX).
# ──────────────────────────────────────────────────────────────────────────────

# ── Cache lifetime sentinel (19 Sep 2026) ────────────────────────────────────
# Fadil: "make cache forever living". A row stamped with NEVER_EXPIRES_AT is a
# permanent hit: `get()` never treats it as expired (so `SECTORS_STALE_OK=0`
# can't miss it either) and `prune_expired()` can never delete it (the DELETE
# only matches `expires_at <= now`). server/credit_policy.py derives every TTL
# from this constant; nothing else may invent its own.
NEVER_EXPIRES_AT = 4102444800.0  # 2100-01-01T00:00:00Z


class SectorsCache:
    """SQLite-backed cache for Sectors v2 responses.

    Schema:
      sectors_cache(cache_key PK, endpoint, fetched_at, expires_at, payload_json)

    Usage:
      cache.get_or_set(endpoint, params, ttl_fn) -> dict
      cache.bust(endpoint_prefix=...) -> n  # manual invalidation
      cache.stats() -> {n_entries, n_expired, by_endpoint}
    """

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or default_db_path()
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._lock = threading.Lock()
        # Ensure the sectors_cache table exists. Forward ref to Storage keeps
        # circular import out: we inline the schema-evolution guard.
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        # Bootstrap SQLite with the same pragmas Storage uses (WAL + busy_timeout).
        bootstrap = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
        bootstrap.execute("CREATE TABLE IF NOT EXISTS sectors_cache ("
                         "cache_key TEXT PRIMARY KEY, endpoint TEXT NOT NULL, "
                         "fetched_at REAL NOT NULL, expires_at REAL NOT NULL, "
                         "payload_json TEXT NOT NULL);")
        bootstrap.execute("CREATE INDEX IF NOT EXISTS idx_sectors_cache_expiry "
                         "ON sectors_cache(expires_at);")
        bootstrap.execute("CREATE INDEX IF NOT EXISTS idx_sectors_cache_endpoint "
                         "ON sectors_cache(endpoint);")
        bootstrap.commit()
        bootstrap.close()
        # Open a separate connection so the hot path doesn't contend on Storage
        # run-locks. check_same_thread=False + timeout=30 is the same pattern as
        # Storage; WAL mode allows one writer + many readers concurrently.
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA busy_timeout=5000;")

    @staticmethod
    def _key(endpoint: str, params: dict | None) -> str:
        """Stable sha256 over endpoint + sorted params."""
        norm = json.dumps(params or {}, sort_keys=True, separators=(",", ":"), default=str)
        h = hashlib.sha256(f"{endpoint}?{norm}".encode("utf-8")).hexdigest()
        return f"sc:{endpoint[:32]}:{h[:32]}"

    def get(self, endpoint: str, params: dict | None) -> tuple[Any, bool]:
        """Return (payload, hit). hit=False means absent.

        NO-EXPIRY (15 Sep 2026, credit-thin mode): every cached row is a HIT
        regardless of age - Sectors data never expires from cache. The payload
        carries ``_stale_age_h`` (hours since TTL passed) so the Critic and
        callers see freshness transparently. Set SECTORS_STALE_OK=0 to restore
        strict TTL expiry (fresh pull, burns 1 credit per endpoint).
        Absent rows still miss. Cached 404 markers are NOT unwrapped here -
        server/sectors._get() re-raises them as SectorsError.

        FOREVER ROWS (19 Sep 2026): rows written through `credit_policy.
        cache_ttl_seconds()` carry `NEVER_EXPIRES_AT`, so even
        SECTORS_STALE_OK=0 cannot miss them - they are permanently warm, by
        Fadil's "make cache forever living" rule.
        """
        import os as _os

        key = self._key(endpoint, params)
        now = time.time()
        with self._lock:
            row = self.conn.execute(
                "SELECT expires_at, payload_json FROM sectors_cache WHERE cache_key=?",
                (key,),
            ).fetchone()
        if not row:
            return (None, False)
        try:
            payload = json.loads(row["payload_json"])
        except json.JSONDecodeError:
            return (None, False)
        if _os.getenv("SECTORS_STALE_OK", "1").strip() in ("0", "false", "no"):
            if row["expires_at"] <= now:
                return (None, False)
            return (payload, True)
        if isinstance(payload, dict) and row["expires_at"] <= now:
            payload = dict(payload)
            payload["_stale"] = True
            try:
                payload["_stale_age_h"] = round((now - row["expires_at"]) / 3600.0, 1)
            except Exception:
                pass
        return (payload, True)

    def latest_for_endpoint(self, endpoint: str) -> tuple[Any, dict] | None:
        """Freshest cached payload for an endpoint, ANY params.

        Credit guard (15 Sep 2026): once a date-windowed endpoint has been paid
        for, a drifting window must never burn a second credit - the caller
        serves the freshest cached row instead and discloses the substitution.
        Returns (payload, meta{fetched_at,expires_at}) or None when the endpoint
        has no rows. Negative-404 markers are never eligible (errors, not data).
        """
        with self._lock:
            row = self.conn.execute(
                "SELECT fetched_at, expires_at, payload_json FROM sectors_cache "
                "WHERE endpoint=? ORDER BY fetched_at DESC LIMIT 1",
                (endpoint,),
            ).fetchone()
        if not row:
            return None
        try:
            payload = json.loads(row["payload_json"])
        except json.JSONDecodeError:
            return None
        if isinstance(payload, dict) and payload.get("_neg404"):
            return None
        return payload, {"fetched_at": row["fetched_at"], "expires_at": row["expires_at"]}

    def is_forever(self, expires_at: float) -> bool:
        """True when a stored expiry is the forever sentinel (never a miss)."""
        return float(expires_at) >= NEVER_EXPIRES_AT

    def set(self, endpoint: str, params: dict | None, payload: Any, ttl_seconds: int | float | None) -> None:
        """Persist payload with TTL (seconds). `None` = forever (NEVER_EXPIRES_AT).

        `ttl_seconds=0` keeps its historical meaning (expires immediately) - some
        tests and callers rely on it. Use `ttl_seconds=None` for forever.
        """
        key = self._key(endpoint, params)
        now = time.time()
        body = json.dumps(payload, separators=(",", ":"), default=str)
        expires_at = NEVER_EXPIRES_AT if ttl_seconds is None else min(now + float(ttl_seconds), NEVER_EXPIRES_AT)
        with self._lock:
            self.conn.execute(
                """
                INSERT INTO sectors_cache(cache_key, endpoint, fetched_at, expires_at, payload_json)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    fetched_at   = excluded.fetched_at,
                    expires_at   = excluded.expires_at,
                    payload_json = excluded.payload_json
                """,
                (key, endpoint, now, expires_at, body),
            )
            self.conn.commit()

    def bust(self, endpoint_prefix: str | None = None) -> int:
        """Delete entries; with prefix, only that endpoint family. Returns n deleted."""
        with self._lock:
            if endpoint_prefix:
                cur = self.conn.execute(
                    "DELETE FROM sectors_cache WHERE endpoint LIKE ?",
                    (endpoint_prefix + "%",),
                )
            else:
                cur = self.conn.execute("DELETE FROM sectors_cache;")
            self.conn.commit()
            return cur.rowcount

    def prune_expired(self) -> int:
        """Drop rows past their expires_at. Call occasionally from cron / admin.

        Forever rows (`expires_at >= NEVER_EXPIRES_AT`) are excluded by the WHERE
        clause so no clock skew can ever drop a permanently-warm payload.
        """
        now = time.time()
        with self._lock:
            cur = self.conn.execute(
                "DELETE FROM sectors_cache WHERE expires_at <= ? AND expires_at < ?;",
                (now, NEVER_EXPIRES_AT),
            )
            self.conn.commit()
            return cur.rowcount

    def stats(self) -> dict:
        """Inspect cache state - used by a /api/debug/cache endpoint."""
        now = time.time()
        with self._lock:
            total = self.conn.execute("SELECT COUNT(*) AS n FROM sectors_cache;").fetchone()["n"]
            expired = self.conn.execute(
                "SELECT COUNT(*) AS n FROM sectors_cache WHERE expires_at <= ?;",
                (now,),
            ).fetchone()["n"]
            forever = self.conn.execute(
                "SELECT COUNT(*) AS n FROM sectors_cache WHERE expires_at >= ?;",
                (NEVER_EXPIRES_AT,),
            ).fetchone()["n"]
            by_ep = self.conn.execute(
                """
                SELECT endpoint, COUNT(*) AS n, AVG(expires_at - fetched_at) AS avg_ttl
                FROM sectors_cache GROUP BY endpoint ORDER BY n DESC LIMIT 20;
                """
            ).fetchall()
        return {
            "n_entries": total,
            "n_expired": expired,
            "n_forever": forever,
            "by_endpoint": [
                {"endpoint": r["endpoint"], "n": r["n"], "avg_ttl_s": r["avg_ttl"]}
                for r in by_ep
            ],
        }

    def close(self) -> None:
        with self._lock:
            try:
                self.conn.close()
            except Exception:
                pass
