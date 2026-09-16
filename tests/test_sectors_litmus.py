"""Sectors Litmus Test - MCP is deliberately OFF (credit-thin mode, 15 Sep 2026).

History: the graph used to attach a Sectors MCP toolset to the collector. MCP
bypasses the SQLite credit-saving cache (every call = 1 credit, no stale-serve,
no neg-404) and times out on this host, so the toolset was removed from the
graph. `maybe_sectors_mcp_toolset` still lives in tools/mcp_sectors.py for
manual/opt-in use and is now reachable only via SECTORS_MCP=1.

What this litmus proves:
1. Default (SECTORS_MCP unset) - graph builds, collector carries NO MCP toolset,
   and the log states the cached-FunctionTools-only (0-credit) path.
2. SECTORS_MCP=1 - the opt-in escape hatch attaches the toolset for real.

Run: .venv/bin/python -m pytest tests/test_sectors_litmus.py -v
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.adk.app import build_graph  # noqa: E402


def _collector(graph):
    """The collector LlmAgent inside the first (intake) stage."""
    intake = graph.sub_agents[0]
    collector = next((a for a in intake.sub_agents if a.name == "collector"), None)
    assert collector is not None, "Collector agent must exist in intake stage"
    return collector


def test_sectors_mcp_is_off_by_default_and_graph_still_builds(caplog, monkeypatch):
    """Default = MCP OFF: graph builds, collector has no MCP toolset, 0-credit path logged."""
    monkeypatch.delenv("SECTORS_MCP", raising=False)

    with caplog.at_level(logging.INFO, logger="agents.adk.app"):
        graph = build_graph(ticker="BBCA")

    assert graph is not None, "Graph must build successfully without Sectors MCP"
    assert graph.name == "equity_report_orchestrator", f"Unexpected graph name: {graph.name}"
    assert any("Sectors MCP disabled" in r.message for r in caplog.records), (
        f"Expected a 'Sectors MCP disabled' log line, got: {[r.message for r in caplog.records]}"
    )

    from google.adk.tools.mcp_tool import McpToolset  # type: ignore

    collector = _collector(graph)
    assert [t for t in collector.tools if isinstance(t, McpToolset)] == [], (
        "Collector must carry NO Sectors MCP toolset by default - every MCP call bills a credit"
    )


def test_sectors_mcp_opt_in_attaches_when_env_set(caplog, monkeypatch):
    """SECTORS_MCP=1 is the documented escape hatch: the toolset IS attached."""
    monkeypatch.setenv("SECTORS_MCP", "1")
    mock_toolset = MagicMock(name="mock_sectors_mcp_toolset")

    with patch(
        "agents.adk.tools.mcp_sectors.maybe_sectors_mcp_toolset", return_value=mock_toolset
    ):
        with caplog.at_level(logging.INFO, logger="agents.adk.app"):
            graph = build_graph(ticker="BBCA")

    assert graph is not None
    assert any("Sectors MCP toolset attached" in r.message for r in caplog.records), (
        f"Expected an attach log line, got: {[r.message for r in caplog.records]}"
    )
    assert mock_toolset in _collector(graph).tools, "Collector must contain the opt-in toolset"


def test_mcp_toolset_is_never_on_the_default_path() -> None:
    """Structural guard: the graph wires MCP only behind the SECTORS_MCP env check."""
    src = (REPO_ROOT / "agents" / "adk" / "app.py").read_text(encoding="utf-8")
    assert 'getenv("SECTORS_MCP", "0")' in src, "MCP must stay behind an opt-in env check"
    assert "if sectors_toolset is not None:" in src, "toolset must be attached conditionally"
