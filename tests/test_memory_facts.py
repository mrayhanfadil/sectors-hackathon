"""Tests for server/routers/memory.py (cross-run verdict store).

Uses an isolated tmp SQLite file - never touches data/agent_runs.db.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from server.routers.memory import get_facts, init_db, write_fact  # noqa: E402


def test_write_and_read_back(tmp_path):
    db = str(tmp_path / "mem.db")
    init_db(db)
    id1 = write_fact("run-1", "bbca", "BUY", 9645.0, ["dcm ok"], db_path=db)
    id2 = write_fact("run-2", "BBCA", "HOLD", 9000.0, {"note": "x"}, db_path=db)
    assert id1 > 0 and id2 > id1
    facts = get_facts("BBCA", db_path=db)
    assert len(facts) == 2
    assert facts[0]["run_id"] == "run-2"  # newest first
    assert facts[0]["rating"] == "HOLD"
    assert facts[1]["reasons"] == ["dcm ok"]


def test_limit_respected(tmp_path):
    db = str(tmp_path / "mem.db")
    for i in range(5):
        write_fact(f"run-{i}", "MTEL", "BUY", 600.0 + i, [], db_path=db)
    assert len(get_facts("MTEL", limit=3, db_path=db)) == 3


def test_unknown_and_empty_ticker(tmp_path):
    db = str(tmp_path / "mem.db")
    assert get_facts("ZZZZ", db_path=db) == []
    assert get_facts("", db_path=db) == []
    assert get_facts("   ", db_path=db) == []
