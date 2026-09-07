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


# --- Tier 1: report sections that fix open gaps (1 credit each) ---

def report_sections(symbol: str, sections: str) -> Any:
    """Thin wrapper so callers name sections explicitly (credit discipline)."""
    return company_report(symbol, sections)


def peers(symbol: str) -> Any:
    """Subsector peer comparison — feeds PRIMARY-MULTIPLE provenance."""
    return company_report(symbol, "peers")


def future(symbol: str) -> Any:
    """Analyst forecasts + EPS growth — grounds our forward numbers."""
    return company_report(symbol, "future")


def valuation_section(symbol: str) -> Any:
    """Forward PE, intrinsic value, historical PB/PE/PS/PCF/PEG — DCF cross-check."""
    return company_report(symbol, "valuation")


def ownership(symbol: str) -> Any:
    """Major shareholders + ownership structure."""
    return company_report(symbol, "ownership")


def management(symbol: str) -> Any:
    """Key executives and their shareholdings."""
    return company_report(symbol, "management")


# --- Tier 2: new signals ---

def broker_top(symbol: str, start: str, end: str, n_brokers: int = 20) -> Any:
    """Top accumulators/distributors for one stock — Asing-flow radar."""
    return _get(f"/brokers/broker-summary/top/{bare_ticker(symbol)}/",
                {"start": start, "end": end, "n_brokers": n_brokers})


def suspensions(symbol: str = "", start: str = "", end: str = "") -> Any:
    """IDX suspensions with official PDF links — risk factors with provenance."""
    p: dict[str, Any] = {}
    if symbol:
        p["symbol"] = bare_ticker(symbol)
    if start:
        p["start"] = start
    if end:
        p["end"] = end
    return _get("/news/suspensions/", p)


def subsector_report(sub_sector: str, sections: str) -> Any:
    """Subsector stats/mcap/valuation/growth/companies — sector context (1/s)."""
    return _get(f"/subsector/report/{sub_sector.strip().lower()}/",
                {"sections": sections})


def listing_performance(symbol: str) -> Any:
    """7/30/90/365d price change since listing — IPO-name context (CDIA)."""
    return _get(f"/ipo/listing-performance/{bare_ticker(symbol)}/")


# --- Tier 3: breadth, cheap ---

def screener(where: str = "", order_by: str = "", limit: int = 50) -> Any:
    """Structured screener ONLY (1 credit) — never ?q= (3 credits)."""
    p: dict[str, Any] = {"limit": min(max(1, limit), 200)}
    if where:
        p["where"] = where
    if order_by:
        p["order_by"] = order_by
    return _get("/companies/", p)


def index_daily(index_code: str, start: str, end: str) -> Any:
    """Index daily close — honest IHSG benchmark for vs-JCI charts."""
    return _get(f"/transaction/index-daily/{index_code.strip().upper()}/",
                {"start": start, "end": end})


def idx_market_cap(start: str, end: str) -> Any:
    """Total IDX market cap history (max 90 days)."""
    return _get("/transaction/idx-total/", {"start": start, "end": end})


def mining_company_financials(slug: str, year: str = "") -> Any:
    """Mining extension — ADRO coal ops (USD millions)."""
    p: dict[str, Any] = {}
    if year:
        p["year"] = year
    return _get(f"/mining/companies/{slug.strip().lower()}/financials/", p)
