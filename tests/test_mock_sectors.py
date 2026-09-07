"""Tests for Mock Sectors Layer — tests/test_mock_sectors.py
Validates the 4 mock routes mirroring Sectors v2 endpoints:
1. test_filings_bcca_returns_schema
2. test_news_bca_returns_schema
3. test_corporate_actions_bca_returns_schema
4. test_quarterly_bca_returns_schema
5. test_unknown_ticker_returns_empty_data
6. test_no_fabrication_grep
"""
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

FILINGS_REQUIRED_FIELDS = {
    "title",
    "body",
    "source",
    "timestamp",
    "sector",
    "sub_sector",
    "tags",
    "symbol",
    "transaction_type",
    "holder_type",
    "holder_name",
    "holding_before",
    "holding_after",
    "amount_transaction",
    "price",
    "transaction_value",
    "share_percentage_before",
    "share_percentage_after",
    "share_percentage_transaction",
    "idx_investor_slug",
    "idx_conglomerates_group_slug",
}

NEWS_REQUIRED_FIELDS = {
    "title",
    "body",
    "source",
    "timestamp",
    "sector",
    "sub_sector",
    "tags",
    "symbols",
    "thumbnail",
    "dimension",
}

CORPORATE_ACTIONS_REQUIRED_KEYS = {
    "dividend",
    "upcoming_dividend",
    "stock_split",
    "right_issue",
    "warrant",
    "bonus",
    "agm",
}

QUARTERLY_REQUIRED_FIELDS = {
    "symbol",
    "date",
    "revenue",
    "earnings",
    "total_assets",
    "total_equity",
    "operating_cash_flow",
    "non_interest_income",
    "operating_expense",
    "operating_pnl",
    "earnings_before_tax",
    "tax",
    "gross_profit",
    "ebit",
    "ebitda",
    "cost_of_revenue",
    "non_interest_bearing_liabilities",
    "cash_only",
    "total_liabilities",
    "total_debt",
    "stockholders_equity",
    "total_non_current_assets",
    "current_liabilities",
    "cash_and_short_term_investments",
    "total_current_asset",
    "total_non_current_liabilities",
    "financing_cash_flow",
    "investing_cash_flow",
    "net_cash_flow",
}


def test_filings_bcca_returns_schema():
    """Hit /api/mock/filings?symbol=BBCA, assert each item has all required fields per IdxFilingsItem."""
    resp = client.get("/api/mock/filings?symbol=BBCA")
    assert resp.status_code == 200
    assert resp.headers.get("cache-control") == "no-store"
    data = resp.json()
    assert "pagination" in data
    assert "data" in data
    assert isinstance(data["data"], list)
    assert data["pagination"]["limit"] == 30
    assert data["pagination"]["offset"] == 0

    for item in data["data"]:
        missing = FILINGS_REQUIRED_FIELDS - set(item.keys())
        assert not missing, f"Filing item missing fields: {missing}"
        assert item["symbol"] == "BBCA"
        assert item["transaction_type"] in ("buy", "sell", "others")
        assert item["holder_type"] in ("insider", "institution", "others")


def test_news_bca_returns_schema():
    """Hit /api/mock/news?symbols=BBCA, assert shape and required fields."""
    resp = client.get("/api/mock/news?symbols=BBCA")
    assert resp.status_code == 200
    assert resp.headers.get("cache-control") == "no-store"
    data = resp.json()
    assert "pagination" in data
    assert "data" in data
    assert isinstance(data["data"], list)

    for item in data["data"]:
        missing = NEWS_REQUIRED_FIELDS - set(item.keys())
        assert not missing, f"News item missing fields: {missing}"
        assert "sentiment" in item["dimension"]
        assert "relevance" in item["dimension"]
        assert item["dimension"]["sentiment"] in ("bullish", "bearish", "neutral")
        assert isinstance(item["sub_sector"], list)
        assert isinstance(item["tags"], list)
        assert isinstance(item["symbols"], list)


def test_corporate_actions_bca_returns_schema():
    """Hit /api/mock/corporate-actions?symbol=BBCA, assert all 7 keys present."""
    resp = client.get("/api/mock/corporate-actions?symbol=BBCA")
    assert resp.status_code == 200
    assert resp.headers.get("cache-control") == "no-store"
    data = resp.json()

    missing_keys = CORPORATE_ACTIONS_REQUIRED_KEYS - set(data.keys())
    assert not missing_keys, f"Corporate actions missing required keys: {missing_keys}"

    assert isinstance(data["dividend"], list)
    assert isinstance(data["upcoming_dividend"], list)
    assert isinstance(data["stock_split"], list)
    assert isinstance(data["right_issue"], list)
    assert isinstance(data["warrant"], list)
    assert isinstance(data["bonus"], list)
    assert isinstance(data["agm"], list)

    # Check dividend item structure if dividends exist
    for d in data["dividend"]:
        assert "ex_date" in d
        assert "payment_date" in d
        assert "amount_per_share" in d
        assert "currency" in d
        assert "type" in d


def test_quarterly_bca_returns_schema():
    """Hit /api/mock/quarterly-financials?symbol=BBCA.

    Keyed Sectors -> items validated against the 29-field schema.
    Keyless -> honest empty with source=sectors_missing_key note
    (legacy removed, Lane E — no yfinance).
    """
    resp = client.get("/api/mock/quarterly-financials?symbol=BBCA&n_quarters=8")
    assert resp.status_code == 200
    assert resp.headers.get("cache-control") == "no-store"
    data = resp.json()
    assert "pagination" in data
    assert "data" in data
    assert isinstance(data["data"], list)

    if not data["data"]:
        # Keyless honest-empty (CI without SECTORS_API_KEY)
        assert "note" in data
        assert "sectors_missing_key" in data["note"]
        return

    for item in data["data"]:
        missing = QUARTERLY_REQUIRED_FIELDS - set(item.keys())
        assert not missing, f"Quarterly item missing fields: {missing}"
        assert item["symbol"] == "BBCA"
        assert item["date"] is not None
        assert len(item["date"]) == 10  # YYYY-MM-DD format


def test_unknown_ticker_returns_empty_data(monkeypatch):
    """Unknown ticker symbol=ZZZZZZ returns 200 OK with empty data + honest note.

    Runs keyless (no SECTORS_API_KEY) so Sectors-backed endpoints return honest
    empty; curated has no ZZZZZZ ticker, so the result is genuinely empty. This
    avoids live network noise polluting the unknown-ticker contract.
    """
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEYS", raising=False)
    monkeypatch.delenv("SECTORS_API_KEY", raising=False)

    # 1. Filings
    r1 = client.get("/api/mock/filings?symbol=ZZZZZZ")
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1.get("data") == []
    assert "note" in d1

    # 2. News
    r2 = client.get("/api/mock/news?symbols=ZZZZZZ")
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2.get("data") == []
    assert "note" in d2

    # 3. Corporate actions
    r3 = client.get("/api/mock/corporate-actions?symbol=ZZZZZZ")
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3.get("dividend") == []
    assert d3.get("agm") == []
    assert "note" in d3

    # 4. Quarterly financials
    r4 = client.get("/api/mock/quarterly-financials?symbol=ZZZZZZ")
    assert r4.status_code == 200
    d4 = r4.json()
    assert d4.get("data") == []
    assert "note" in d4


def test_no_fabrication_grep():
    """Grep router source to verify no hardcoded fake company names, numbers, or Sectors API calls."""
    router_file = Path(__file__).resolve().parents[1] / "server" / "routers" / "mock_sectors.py"
    assert router_file.exists(), f"Router file {router_file} not found"
    content = router_file.read_text(encoding="utf-8")

    # Check for forbidden fabricated numbers / names
    forbidden_tokens = [
        "25400000000000",
        "5800000000000",
        "1450000000000000",
        "Dharma Satria",
        "fake_company",
        "synthetic_trade",
    ]
    for tok in forbidden_tokens:
        assert tok not in content, f"Fabricated token found in router source: {tok}"

    # Verify no calls to real Sectors API
    forbidden_sectors_apis = [
        "api.sectors.app",
        "sectors-mcp.supertype.ai",
        "SECTORS_API_KEY",
    ]
    for api in forbidden_sectors_apis:
        assert api not in content, f"Forbidden Sectors API call found in router source: {api}"


def test_cache_hit_and_miss_behavior():
    """Verify in-memory TTL cache produces X-Cache: MISS on first call, HIT on subsequent call."""
    import asyncio
    from server.cache import get_mock_cache

    cache = get_mock_cache()
    asyncio.run(cache.clear())

    # Call 1: should be cache MISS
    resp1 = client.get("/api/mock/corporate-actions?symbol=BBCA")
    assert resp1.status_code == 200
    assert resp1.headers.get("x-cache") == "MISS"
    assert resp1.headers.get("cache-control") == "no-store"

    # Call 2: should be cache HIT with identical payload
    resp2 = client.get("/api/mock/corporate-actions?symbol=BBCA")
    assert resp2.status_code == 200
    assert resp2.headers.get("x-cache") == "HIT"
    assert resp2.headers.get("cache-control") == "no-store"
    assert resp1.json() == resp2.json()


def test_health_endpoint_reports_mock_sectors():
    """Verify /api/health returns mock_sectors discovery, upstream sources, and last call timestamps."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()

    assert data.get("status") == "ok"
    assert data.get("mock_sectors_router") is True

    registered = data.get("registered_endpoints", [])
    expected_endpoints = [
        "/api/mock/filings",
        "/api/mock/news",
        "/api/mock/corporate-actions",
        "/api/mock/quarterly-financials",
    ]
    for ep in expected_endpoints:
        assert ep in registered, f"Missing registered endpoint in /api/health: {ep}"

    sources = data.get("upstream_sources", {})
    assert sources.get("filings") == "sectors filings + idx.co.id via Camoufox"
    assert sources.get("news") == "sectors news + scripts/news.py curated"
    assert sources.get("corporate_actions") == "sectors corporate-actions + IDX"
    assert sources.get("quarterly_financials") == "sectors quarterly-financials"

    last_call = data.get("last_successful_call", {})
    assert isinstance(last_call, dict)
    assert "/api/mock/corporate-actions" in last_call


def test_rate_limiter_429_behavior():
    """Verify exceeding 60 requests per minute from one IP returns 429 Too Many Requests."""
    import asyncio
    from server.logging_config import rate_limiter

    test_ip = "203.0.113.99"
    headers = {"X-Forwarded-For": test_ip}

    # Reset rate limiter state for clean test
    asyncio.run(rate_limiter.reset())

    # Send 60 requests (allowed)
    for _ in range(60):
        r = client.get("/api/health", headers=headers)
        assert r.status_code == 200

    # 61st request should be throttled
    r_throttled = client.get("/api/health", headers=headers)
    assert r_throttled.status_code == 429
    assert r_throttled.headers.get("retry-after") is not None
    assert r_throttled.headers.get("x-ratelimit-limit") == "60"
    assert r_throttled.headers.get("x-ratelimit-remaining") == "0"
    body = r_throttled.json()
    assert body.get("error") == "rate_limit_exceeded"

    # Reset again after test
    asyncio.run(rate_limiter.reset())

