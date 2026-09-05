# Copyright 2026 Sectors Hackathon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Cross-run memory: verdicts persisted to SQLite (NOT vector DB).

Decision D3 (locked 2026-09-05): state per run is ~13 small keys —
exact queries (ticker, date, rating) beat semantic search for audit.
Table lives in the existing data/agent_runs.db next to run storage.
`embedding BLOB NULL` column reserved so a future vector pass needs
no schema migration.

Wiring (Task 7, orchestrator): `app.include_router(router_memory)`
in server/main.py exposes GET /api/memory.
"""

from __future__ import annotations

import json
import sqlite3
import time
from typing import Any, Optional

from fastapi import APIRouter, Query

router_memory = APIRouter()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS memory_facts(
  id INTEGER PRIMARY KEY,
  run_id TEXT NOT NULL,
  ticker TEXT NOT NULL,
  finished_at REAL NOT NULL,
  rating TEXT,
  fair_value REAL,
  reasons_json TEXT,
  embedding BLOB NULL
);
CREATE INDEX IF NOT EXISTS idx_facts_ticker ON memory_facts(ticker);
CREATE INDEX IF NOT EXISTS idx_facts_finished ON memory_facts(finished_at);
"""


def _connect(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
    con.row_factory = sqlite3.Row
    return con


def init_db(db_path: str) -> None:
    con = _connect(db_path)
    try:
        con.executescript(_SCHEMA)
        con.commit()
    finally:
        con.close()


def write_fact(
    run_id: str,
    ticker: str,
    rating: Optional[str],
    fair_value: Optional[float],
    reasons: Any,
    db_path: Optional[str] = None,
    finished_at: Optional[float] = None,
) -> int:
    """Persist one run verdict. Returns the row id."""
    if db_path is None:
        from ..storage import default_db_path

        db_path = default_db_path()
    init_db(db_path)
    reasons_json = json.dumps(reasons, ensure_ascii=False) if not isinstance(reasons, str) else reasons
    con = _connect(db_path)
    try:
        cur = con.execute(
            "INSERT INTO memory_facts(run_id, ticker, finished_at, rating, fair_value, reasons_json)"
            " VALUES(?,?,?,?,?,?)",
            (run_id, ticker.upper().strip(), finished_at or time.time(), rating, fair_value, reasons_json),
        )
        con.commit()
        return int(cur.lastrowid or 0)
    finally:
        con.close()


def get_facts(
    ticker: str,
    limit: int = 20,
    db_path: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Latest verdicts for a ticker, newest first. Unknown ticker → []."""
    t = (ticker or "").upper().strip()
    if not t:
        return []
    if db_path is None:
        from ..storage import default_db_path

        db_path = default_db_path()
    init_db(db_path)
    con = _connect(db_path)
    try:
        rows = con.execute(
            "SELECT run_id, ticker, finished_at, rating, fair_value, reasons_json"
            " FROM memory_facts WHERE ticker=? ORDER BY finished_at DESC LIMIT?",
            (t, max(1, min(limit, 200))),
        ).fetchall()
        out = []
        for r in rows:
            try:
                reasons = json.loads(r["reasons_json"]) if r["reasons_json"] else None
            except Exception:
                reasons = r["reasons_json"]
            out.append(
                {
                    "run_id": r["run_id"],
                    "ticker": r["ticker"],
                    "finished_at": r["finished_at"],
                    "rating": r["rating"],
                    "fair_value": r["fair_value"],
                    "reasons": reasons,
                }
            )
        return out
    finally:
        con.close()


@router_memory.get("/api/memory", summary="Historic run verdicts by ticker")
async def memory(
    ticker: str = Query(..., description="IDX ticker, e.g. BBCA"),
    limit: int = Query(20, ge=1, le=200),
):
    facts = get_facts(ticker, limit)
    return {"ticker": (ticker or '').upper().strip(), "count": len(facts), "facts": facts, "source": "memory_facts"}
