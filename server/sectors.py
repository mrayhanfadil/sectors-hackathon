"""Sectors API v2 client — the single gateway for ALL market data.

Goal: 100% Sectors-sourced, zero external (yfinance/Tavily/scrapers) in prod paths.
Docs: references/sectors-api-and-mcp.md. Base: https://api.sectors.app/v2.

Rules:
- Auth = raw key in `Authorization` header (NO Bearer prefix — that's MCP-only).
- Tickers = bare IDX code (`BBCA`, never `BBCA.JK`) — normalized here.
- No key  -> SectorsNotConfigured (callers map to honest 503, NEVER silent
  fallback to yfinance/Tavily — Fadil's explicit-failure rule).
- Credit discipline: callers must use the 4h `cached_endpoint` layer + universe
  feeds + minimal `sections=` (1,000-credit budget, no published per-call cost).
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from .config import get_settings

log = logging.getLogger(__name__)


class SectorsNotConfigured(RuntimeError):
    """Raised when SECTORS_API_KEY is missing — wire to HTTP 503, not fallback."""


class SectorsError(RuntimeError):
    """Raised on non-2xx from api.sectors.app — carries status + body snippet."""

    def __init__(self, status: int, body: str):
        super().__init__(f"sectors v2 -> {status}: {body[:300]}")
        self.status = status
        self.body = body


def bare_ticker(symbol: str) -> str:
    """`BBCA.JK`/` bbca ` -> `BBCA`. Sectors wants bare IDX codes."""
    return symbol.strip().upper().removesuffix(".JK")


def _client() -> httpx.Client:
    s = get_settings()
    if not s.sectors_api_key:
        raise SectorsNotConfigured(
            "SECTORS_API_KEY missing — onboard at sectors.app/api, "
            "save key to .env (mode 600). No fallback wired on purpose."
        )
    return httpx.Client(
        base_url=s.sectors_base.rstrip("/"),
        headers={"Authorization": s.sectors_api_key},
        timeout=15,
    )


def _get(path: str, params: dict[str, Any] | None = None) -> Any:
    with _client() as c:
        r = c.get(path, params=params or {})
    if r.status_code >= 400:
        raise SectorsError(r.status_code, r.text)
    return r.json()


# --- mapped endpoints (1:1 with the external sources they replace) ---

def daily(symbol: str, start: str, end: str) -> Any:
    """Replaces yfinance OHLCV. Range max 90 days (API limit)."""
    return _get(f"/transaction/daily/{bare_ticker(symbol)}/",
                {"start": start, "end": end})


def universe_close(date: str) -> Any:
    """Replaces IDX Postgres stockdata feed — every ticker, one paginated call."""
    return _get(f"/transaction/close/{date}/")


def quarterly(symbol: str, n_quarters: int = 8) -> Any:
    """Replaces yfinance statements engine (+ bank extras free)."""
    return _get(f"/company/quarterly-financials/{bare_ticker(symbol)}/",
                {"n_quarters": n_quarters})


def company_report(symbol: str, sections: str) -> Any:
    """Replaces assumptions/peers/dividend hand-builds. Keep sections minimal."""
    return _get(f"/company/report/{bare_ticker(symbol)}/", {"sections": sections})


def corporate_actions(symbol: str) -> Any:
    """Replaces dividend/split scraper bits."""
    return _get(f"/company/corporate-actions/{bare_ticker(symbol)}/")


def news(symbols: str, start: str = "", end: str = "") -> Any:
    """Replaces Tavily harvester. extension=idx is REQUIRED by the API."""
    p: dict[str, Any] = {"extension": "idx", "symbols": symbols}
    if start:
        p["start"] = start
    if end:
        p["end"] = end
    return _get("/news/news/", p)


def filings(symbol: str) -> Any:
    """Replaces filings scraper (insider buy/sell + holder_type)."""
    return _get("/news/filings/", {"symbol": bare_ticker(symbol)})


def foreign_flow(symbol: str, start: str, end: str) -> Any:
    """Net foreign-broker inflow — new signal we never had (max 90 days)."""
    return _get(f"/brokers/foreign-flow/{bare_ticker(symbol)}/",
                {"start": start, "end": end})
