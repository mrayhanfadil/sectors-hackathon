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
    """Hit /api/mock/quarterly-financials?symbol=BBCA, assert each item has all 29 required fields."""
    resp = client.get("/api/mock/quarterly-financials?symbol=BBCA&n_quarters=8")
    assert resp.status_code == 200
    assert resp.headers.get("cache-control") == "no-store"
    data = resp.json()
    assert "pagination" in data
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0, "BBCA quarterly financials should not be empty"

    for item in data["data"]:
        missing = QUARTERLY_REQUIRED_FIELDS - set(item.keys())
        assert not missing, f"Quarterly item missing fields: {missing}"
        assert item["symbol"] == "BBCA"
        assert item["date"] is not None
        assert len(item["date"]) == 10  # YYYY-MM-DD format


def test_unknown_ticker_returns_empty_data():
    """Unknown ticker symbol=ZZZZZZ returns 200 OK with empty data + honest note."""
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
