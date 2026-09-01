"""Sectors Litmus Test — rules.md §06 validation.

Validates that:
1. When Sectors MCP is removed / disabled (monkey-patching `maybe_sectors_mcp_toolset` to return None),
   the graph built via `agents.adk.app.build_graph()` gracefully degrades without crashing,
   and logs 'Sectors MCP skipped'.
2. The collector agent in the graph operates without the MCP toolset attached.
3. When Sectors MCP toolset is present, it is attached to the collector agent and logged.

Run: .venv/bin/python -m pytest tests/test_sectors_litmus.py -v
Or:  .venv/bin/python tests/test_sectors_litmus.py
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import agents.adk.app as app_mod
from agents.adk.app import build_graph


def test_sectors_mcp_graceful_degradation_when_none(caplog):
    """Monkey-patch maybe_sectors_mcp_toolset to return None; graph must build and log 'Sectors MCP skipped'."""
    with patch.object(app_mod, "maybe_sectors_mcp_toolset", return_value=None):
        with caplog.at_level(logging.INFO, logger="agents.adk.app"):
            graph = build_graph(ticker="BBCA")

    assert graph is not None, "Graph must build successfully"
    assert graph.name == "equity_report_orchestrator", f"Unexpected graph name: {graph.name}"

    # Assert logs contain 'Sectors MCP skipped'
    assert any("Sectors MCP skipped" in record.message for record in caplog.records), (
        f"Expected 'Sectors MCP skipped' in log records, got: {[r.message for r in caplog.records]}"
    )

    # Validate collector agent structure under degraded mode
    intake = graph.sub_agents[0]
    collector = next((a for a in intake.sub_agents if a.name == "collector"), None)
    assert collector is not None, "Collector agent must exist in intake stage"
    # Collector should have no MCP toolset attached
    assert collector.tools == [], "Collector tools should be empty when Sectors MCP is skipped"


def test_sectors_mcp_attached_when_available(caplog):
    """When maybe_sectors_mcp_toolset returns a toolset, graph attaches it and logs 'Sectors MCP toolset attached'."""
    mock_toolset = MagicMock(name="mock_sectors_mcp_toolset")
    with patch.object(app_mod, "maybe_sectors_mcp_toolset", return_value=mock_toolset):
        with caplog.at_level(logging.INFO, logger="agents.adk.app"):
            graph = build_graph(ticker="BBCA")

    assert graph is not None
    assert any("Sectors MCP toolset attached" in record.message for record in caplog.records), (
        f"Expected 'Sectors MCP toolset attached' in log records, got: {[r.message for r in caplog.records]}"
    )

    # Validate collector agent has the toolset attached
    intake = graph.sub_agents[0]
    collector = next((a for a in intake.sub_agents if a.name == "collector"), None)
    assert collector is not None
    assert mock_toolset in collector.tools, "Collector must contain the Sectors MCP toolset"


if __name__ == "__main__":
    failed = 0
    test_funcs = [
        test_sectors_mcp_graceful_degradation_when_none,
        test_sectors_mcp_attached_when_available,
    ]
    for fn in test_funcs:
        try:
            class SimpleCaplog:
                def __init__(self):
                    self.records = []
                def at_level(self, lvl, logger=None):
                    class Ctx:
                        def __enter__(inner): pass
                        def __exit__(inner, *args): pass
                    return Ctx()

            cl = SimpleCaplog()
            handler = logging.Handler()
            handler.emit = lambda record: cl.records.append(record)
            logging.getLogger("agents.adk.app").addHandler(handler)
            logging.getLogger("agents.adk.app").setLevel(logging.INFO)
            fn(cl)
            logging.getLogger("agents.adk.app").removeHandler(handler)
            print(f"  PASS  {fn.__name__}")
        except Exception as e:
            failed += 1
            print(f"  FAIL  {fn.__name__}: {e}")

    print(f"\nPassed {len(test_funcs) - failed}/{len(test_funcs)} litmus tests")
    sys.exit(1 if failed else 0)
