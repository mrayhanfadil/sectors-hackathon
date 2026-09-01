# Copyright 2026 Sectors Hackathon
"""SQLite persistence layer for ADK agent runs and event traces.

Schema:
- agent_runs: run metadata, status, started/finished timestamps, final state, and errors.
- agent_events: granular event-by-event traces per run, indexed by sequence number.
"""

from __future__ import annotations

import json
import logging
import os
import pathlib
import sqlite3
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)


def default_db_path() -> str:
    """Return {project_root}/data/agent_runs.db. project_root inferred from this file's location."""
    # agents/adk/storage.py -> project_root = parents[2]
    project_root = pathlib.Path(__file__).resolve().parents[2]
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
    from google.adk Event. JSON-safe (no Event objects). Use event.model_dump() or .__dict__.
    Use getattr with defaults to handle missing fields safely.
    """
    if isinstance(event, dict):
        author = event.get("author", "") or ""
        node = event.get("node", "") or ""
        event_type = event.get("event_type", "") or ""
        ts = event.get("ts", time.time())
        text = event.get("text", "") or ""
        function_calls = event.get("function_calls", []) or []
        state_delta = event.get("state_delta", None)
        transfer_to = event.get("transfer_to", None)
        if not event_type:
            if function_calls:
                event_type = "function_call"
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
        Open connection with check_same_thread=False (we may be called from BE's worker thread).
        Run schema migrations on init (CREATE TABLE IF NOT EXISTS).
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
            self.conn.commit()

    def start_run(
        self,
        run_id: str,
        ticker: str,
        prompt: str | None,
        provider: str | None = None,
        model: str | None = None,
    ) -> None:
        """Insert agent_runs row with status='running', started_at=now()."""
        started_at = time.time()
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO agent_runs (
                    run_id, ticker, started_at, finished_at, status,
                    provider, model, prompt, n_events, last_text, state_json, error
                ) VALUES (?, ?, ?, NULL, 'running', ?, ?, ?, 0, NULL, NULL, NULL)
                """,
                (run_id, ticker.upper(), started_at, provider, model, prompt),
            )
            self.conn.commit()

    def append_event(self, run_id: str, seq: int, event: Any) -> None:
        """Insert one agent_events row. Extract author/node/event_type/ts from event;
        serialize full event to JSON for payload_json.
        Skip if run_id unknown (defensive — run_id may not exist if start_run race).
        Commit after each insert (no batching — durability > perf for ~50 events/run).
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
                # defensive: skip if run_id unknown
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

    def finish_run(
        self,
        run_id: str,
        *,
        status: str,
        last_text: str = "",
        state: dict | None = None,
        error: str | None = None,
    ) -> None:
        """Update agent_runs: finished_at=now, status, n_events, last_text, state_json, error."""
        finished_at = time.time()
        last_text_trunc = (last_text or "")[:8000]
        state_json = (
            json.dumps(to_json_safe(state), ensure_ascii=False, default=str)
            if state is not None
            else None
        )
        error_trunc = str(error)[:2000] if error is not None else None

        with self._lock:
            cur = self.conn.cursor()
            cur.execute(
                """
                UPDATE agent_runs
                SET finished_at = ?,
                    status = ?,
                    n_events = (SELECT COUNT(*) FROM agent_events WHERE run_id = ?),
                    last_text = ?,
                    state_json = ?,
                    error = ?
                WHERE run_id = ?
                """,
                (
                    finished_at,
                    status,
                    run_id,
                    last_text_trunc,
                    state_json,
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
            if ticker:
                cur.execute(
                    "SELECT * FROM agent_runs WHERE UPPER(ticker) = ? ORDER BY started_at DESC LIMIT ?",
                    (ticker.upper(), limit),
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

    def get_latest_completed(self, ticker: str) -> dict | None:
        """Return latest run with status in ('completed', 'interrupted', 'failed') for ticker, or None."""
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(
                """
                SELECT * FROM agent_runs
                WHERE UPPER(ticker) = ?
                  AND status IN ('completed', 'interrupted', 'failed')
                ORDER BY started_at DESC
                LIMIT 1
                """,
                (ticker.upper(),),
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
                        d["state_delta_keys"] = list(d["payload"]["state_delta"].keys())
                    elif "state_delta_keys" not in d:
                        d["state_delta_keys"] = []
                results.append(d)
            return results

    def close(self) -> None:
        """Close SQLite connection."""
        with self._lock:
            try:
                self.conn.close()
            except Exception:
                pass
