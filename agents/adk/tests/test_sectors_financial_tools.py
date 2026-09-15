"""Tests for Sectors financial FunctionTools (gap-fix Lane A) — keyless CI green.

- All 6 tools keyless -> {data: [], source: 'sectors_missing_key'}, never raise.
- Ticker normalization: '.JK' suffix + lowercase -> bare upper code.
- Heuristic (_extract_tickers): allowlist-only, multi-ticker, failed-closed
  on English words and unknown codes.
- Graph smoke: collector owns the 6 financial FunctionTools.
"""
import asyncio

from agents.adk.tools.sectors_financial_tools import (
    SECTORS_FINANCIAL_TOOLS,
    sectors_company_report,
    sectors_filings,
    sectors_foreign_flow,
    sectors_index_daily,
    sectors_peers,
    sectors_quarterly,
    sectors_segments,
)
from agents.adk.tools.web_tools import _extract_tickers


def _keyless(out, ticker="BBCA"):
    assert out["source"] == "sectors_missing_key", out
    assert out["data"] == []
    assert out["ticker"] == ticker
    assert out["fetched_at"]


def test_all_six_tools_keyless():
    outs = [
        asyncio.run(sectors_quarterly("BBCA")),
        asyncio.run(sectors_company_report("BBCA", "valuation")),
        asyncio.run(sectors_peers("BBCA")),
        asyncio.run(sectors_filings("BBCA")),
        asyncio.run(sectors_foreign_flow("BBCA")),
        asyncio.run(sectors_segments("BBCA")),
        asyncio.run(sectors_index_daily("IHSG", "2026-06-01", "2026-09-01")),
    ]
    assert len(SECTORS_FINANCIAL_TOOLS) == 7
    for out in outs[:-1]:
        _keyless(out)
    _keyless(outs[-1], ticker="IHSG")


def test_ticker_normalization():
    out = asyncio.run(sectors_quarterly(" bbca.jk "))
    assert out["ticker"] == "BBCA"
    assert out["source"] == "sectors_missing_key"


def test_heuristic_multi_ticker():
    assert _extract_tickers("BBCA, adro MTEL") == ["BBCA", "ADRO", "MTEL"]
    assert _extract_tickers("bbca.jk earnings") == ["BBCA"]


def test_heuristic_failed_closed_on_english():
    assert _extract_tickers("BUY TARGET EARNINGS GROWTH") == []
    assert _extract_tickers("ZZZZ top pick") == []
    assert _extract_tickers("") == []


def test_collector_owns_financial_tools(monkeypatch):
    """Collector tool list includes the 6 Sectors financial FunctionTools."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-fake")
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-gemini")

    from unittest.mock import patch
    from google.adk.tools.function_tool import FunctionTool

    with patch("agents.adk.app.maybe_sectors_mcp_toolset", return_value=None):
        from agents.adk.app import build_graph

        root = build_graph(ticker="BBCA")

    intake = root.sub_agents[0]
    collector = next(a for a in intake.sub_agents if a.name == "collector")
    wrapped = {
        t.func.__name__ for t in (collector.tools or []) if isinstance(t, FunctionTool)
    }
    expected = {fn.__name__ for fn in SECTORS_FINANCIAL_TOOLS}
    assert expected <= wrapped, f"collector missing: {expected - wrapped}"
