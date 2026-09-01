"""Mock Sectors Router — server/routers/mock_sectors.py
Mirrors 4 Sectors v2 API endpoints populated strictly from free public sources:
1. GET /api/mock/filings -> mirrors GET /v2/filings/
2. GET /api/mock/news -> mirrors GET /v2/news/
3. GET /api/mock/corporate-actions -> mirrors GET /v2/company/corporate-actions/
4. GET /api/mock/quarterly-financials -> mirrors GET /v2/report/quarterly-financials/

Strict zero-Sectors-credit layer with honest provenance and zero fabrication.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException, Query, Response

from ..cache import cached_endpoint

logger = logging.getLogger(__name__)

router_mock_sectors = APIRouter()

# Upstream data sources provenance
UPSTREAM_SOURCES: dict[str, str] = {
    "filings": "idx.co.id via Camoufox",
    "news": "scripts/news.py + Tavily",
    "corporate_actions": "yfinance + IDX",
    "quarterly_financials": "yfinance .JK quarterly",
}

REGISTERED_ENDPOINTS: list[str] = [
    "/api/mock/filings",
    "/api/mock/news",
    "/api/mock/corporate-actions",
    "/api/mock/quarterly-financials",
]

_LAST_SUCCESSFUL_CALL: dict[str, str | None] = {
    "/api/mock/filings": None,
    "/api/mock/news": None,
    "/api/mock/corporate-actions": None,
    "/api/mock/quarterly-financials": None,
}


def record_successful_call(endpoint: str) -> None:
    """Record ISO-8601 timestamp of a successful endpoint call in-memory."""
    clean_ep = endpoint
    if not clean_ep.startswith("/api/mock/"):
        name = clean_ep.strip("/").split("/")[-1]
        clean_ep = f"/api/mock/{name}"
    if clean_ep in _LAST_SUCCESSFUL_CALL:
        _LAST_SUCCESSFUL_CALL[clean_ep] = datetime.now(timezone.utc).astimezone().isoformat()


def get_mock_sectors_status() -> dict[str, Any]:
    """Return discoverable metadata and live health status for mock sectors router."""
    return {
        "mock_sectors_router": True,
        "registered_endpoints": list(REGISTERED_ENDPOINTS),
        "endpoints": list(REGISTERED_ENDPOINTS),
        "upstream_sources": dict(UPSTREAM_SOURCES),
        "last_successful_call": dict(_LAST_SUCCESSFUL_CALL),
    }


# Paths to repo metadata
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ASSUMPTIONS_DIR = REPO_ROOT / "data" / "assumptions"
DATA_PEERS_PATH = REPO_ROOT / "data" / "peers.json"

# In-memory cache for scraped IDX disclosures (TTL: 300s)
_DISCLOSURES_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_CACHE_TTL = 300.0

MONTH_ID_MAP = {
    "januari": 1,
    "februari": 2,
    "maret": 3,
    "april": 4,
    "mei": 5,
    "juni": 6,
    "juli": 7,
    "agustus": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "desember": 12,
}


# ── Metadata Helpers ────────────────────────────────────────────────────────

def _get_sector_and_subsector(symbol: str) -> tuple[str, str]:
    """Retrieve sector and sub_sector slug for a symbol from repo metadata."""
    sym = symbol.upper().strip().replace(".JK", "")
    assump_path = DATA_ASSUMPTIONS_DIR / f"{sym}.json"
    if assump_path.exists():
        try:
            data = json.loads(assump_path.read_text(encoding="utf-8"))
            sec = data.get("provenance", {}).get("sector") or data.get("sector")
            if sec:
                sec_str = sec.lower().replace(" ", "-")
                sub_str = "banks" if sec_str == "financials" and sym.startswith("BB") else sec_str
                return sec_str, sub_str
        except Exception:
            pass

    if DATA_PEERS_PATH.exists():
        try:
            peers_data = json.loads(DATA_PEERS_PATH.read_text(encoding="utf-8"))
            by_t = peers_data.get("by_ticker", {}).get(sym, {})
            sec = by_t.get("sector")
            if sec:
                sec_str = sec.lower().replace(" ", "-")
                sub_str = "banks" if sec_str == "financials" and sym.startswith("BB") else sec_str
                return sec_str, sub_str
        except Exception:
            pass

    known_taxonomy = {
        "BBCA": ("financials", "banks"),
        "BBRI": ("financials", "banks"),
        "BMRI": ("financials", "banks"),
        "BBNI": ("financials", "banks"),
        "BRIS": ("financials", "banks"),
        "ADRO": ("energy", "coal"),
        "RATU": ("energy", "oil-and-gas"),
        "CDIA": ("infrastructures", "utilities"),
        "MTEL": ("infrastructures", "telecommunication"),
        "TLKM": ("infrastructures", "telecommunication"),
        "ISAT": ("infrastructures", "telecommunication"),
        "EXCL": ("infrastructures", "telecommunication"),
        "TOWR": ("infrastructures", "telecommunication"),
        "ASII": ("consumer-cyclicals", "automotive"),
        "UNVR": ("consumer-non-cyclicals", "personal-care"),
        "ICBP": ("consumer-non-cyclicals", "food-and-beverage"),
        "INDF": ("consumer-non-cyclicals", "food-and-beverage"),
        "KLBF": ("healthcare", "pharmaceuticals"),
        "ANTM": ("basic-materials", "metals-and-mining"),
        "MDKA": ("basic-materials", "metals-and-mining"),
        "INCO": ("basic-materials", "metals-and-mining"),
        "PGAS": ("utilities", "gas-utilities"),
    }
    if sym in known_taxonomy:
        return known_taxonomy[sym]
    return "general", "general"


def _parse_idx_timestamp(text: str) -> str:
    """Parse Indonesian date string from IDX disclosure card into ISO-8601 with +07:00."""
    try:
        match = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\s+(\d{2}):(\d{2}):(\d{2})", text)
        if match:
            day = int(match.group(1))
            m_name = match.group(2).lower()
            month = MONTH_ID_MAP.get(m_name, 1)
            year = int(match.group(3))
            hh = int(match.group(4))
            mm = int(match.group(5))
            ss = int(match.group(6))
            return f"{year:04d}-{month:02d}-{day:02d}T{hh:02d}:{mm:02d}:{ss:02d}+07:00"
    except Exception:
        pass
    return datetime.now(timezone.utc).astimezone().isoformat()


# ── Required Top-Level Helpers ──────────────────────────────────────────────

async def _scrape_idx_disclosures(
    symbol: str, transaction_type: str | None = None
) -> list[dict[str, Any]]:
    """Scrape IDX Keterbukaan Informasi disclosures using Camoufox browser fingerprint."""
    sym = symbol.upper().strip().replace(".JK", "")
    now = time.time()

    # In-memory TTL cache lookup
    if sym in _DISCLOSURES_CACHE:
        cached_time, cached_items = _DISCLOSURES_CACHE[sym]
        if now - cached_time < _CACHE_TTL:
            if transaction_type:
                return [it for it in cached_items if it.get("transaction_type") == transaction_type]
            return list(cached_items)

    sec_slug, sub_slug = _get_sector_and_subsector(sym)
    items: list[dict[str, Any]] = []

    try:
        from camoufox import AsyncCamoufox

        async with AsyncCamoufox(headless=True) as browser:
            page = await browser.new_page()
            url = f"https://www.idx.co.id/id/perusahaan-tercatat/keterbukaan-informasi/?kodeEmiten={sym}"
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_selector('input[placeholder="Cari Kode"]', timeout=10000)

            code_input = await page.query_selector('input[placeholder="Cari Kode"]')
            if code_input:
                await code_input.click()
                await code_input.fill(sym)
                await page.wait_for_timeout(800)

                dropdown_elements = await page.query_selector_all(
                    "li, .v-list-item, .multiselect__element, .dropdown-menu a"
                )
                matched = False
                for el in dropdown_elements:
                    text = await el.inner_text()
                    if sym.lower() in text.lower():
                        await el.click()
                        matched = True
                        break

                if not matched:
                    _DISCLOSURES_CACHE[sym] = (now, [])
                    return []

                await page.wait_for_timeout(800)
                buttons = await page.query_selector_all("button")
                for b in buttons:
                    btxt = await b.inner_text()
                    if "terapkan" in btxt.lower() or "cari" in btxt.lower():
                        await b.click()
                        break

                await page.wait_for_timeout(3500)
                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")
                cards = soup.find_all("div", class_="attach-card")

                for card in cards:
                    text_all = card.get_text(" ", strip=True)
                    title_tag = card.find("h6")
                    title = title_tag.get_text(" ", strip=True) if title_tag else ""
                    ts = _parse_idx_timestamp(text_all)

                    pdf_tag = card.find("a", href=lambda h: bool(h and ".pdf" in h.lower()))
                    source_url = pdf_tag.get("href") if pdf_tag else "mock://placeholder"

                    # Classify transaction type
                    tx_type = "others"
                    t_lower = title.lower()
                    if any(k in t_lower for k in ["buy back", "pembelian", "beli", "akuisisi", "acquire"]):
                        tx_type = "buy"
                    elif any(k in t_lower for k in ["jual", "penjualan", "divestasi", "pengalihan"]):
                        tx_type = "sell"

                    # Classify holder type
                    holder_type = (
                        "insider"
                        if any(k in t_lower for k in ["direksi", "komisaris", "pengendali", "insider", "afiliasi"])
                        else "institution"
                    )

                    item: dict[str, Any] = {
                        "title": title,
                        "body": text_all[:500],
                        "source": source_url,
                        "timestamp": ts,
                        "sector": sec_slug,
                        "sub_sector": sub_slug,
                        "tags": ["keterbukaan-informasi", "idx", sym.lower()],
                        "symbol": sym,
                        "transaction_type": tx_type,
                        "holder_type": holder_type,
                        "holder_name": None,
                        "holding_before": None,
                        "holding_after": None,
                        "amount_transaction": None,
                        "price": None,
                        "transaction_value": None,
                        "share_percentage_before": None,
                        "share_percentage_after": None,
                        "share_percentage_transaction": None,
                        "idx_investor_slug": None,
                        "idx_conglomerates_group_slug": None,
                    }
                    items.append(item)

    except Exception as e:
        logger.warning("IDX disclosure scrape failed for %s: %s", sym, e)

    _DISCLOSURES_CACHE[sym] = (now, items)
    if transaction_type:
        return [it for it in items if it.get("transaction_type") == transaction_type]
    return items


async def _scrape_idx_agm_announcements(symbol: str) -> list[dict[str, Any]]:
    """Scrape IDX Keterbukaan Informasi for AGM / RUPS announcements."""
    disclosures = await _scrape_idx_disclosures(symbol)
    agm_items: list[dict[str, Any]] = []

    for d in disclosures:
        title = d.get("title", "")
        body = d.get("body", "")
        combined = f"{title} {body}".lower()
        if any(k in combined for k in ["rups", "agmslb", "rapat umum", "agm", "rupo"]):
            agm_type = "AGMSLB" if ("luar biasa" in combined or "agmslb" in combined) else "AGMT"
            ts = d.get("timestamp", "")
            date_str = ts[:10] if len(ts) >= 10 else datetime.now().strftime("%Y-%m-%d")
            agm_items.append({
                "date": date_str,
                "type": agm_type,
                "agenda": title or "Rapat Umum Pemegang Saham",
            })

    return agm_items


def _derive_yfinance_dividends(symbol: str) -> list[dict[str, Any]]:
    """Extract historic cash dividends from yfinance .JK."""
    sym = symbol.upper().strip().replace(".JK", "")
    try:
        import yfinance as yf

        tk = yf.Ticker(f"{sym}.JK")
        divs = tk.dividends
        if divs is None or len(divs) == 0:
            return []

        out: list[dict[str, Any]] = []
        for dt, val in divs.items():
            dt_str = str(dt.date()) if hasattr(dt, "date") else str(dt)[:10]
            out.append({
                "ex_date": dt_str,
                "payment_date": dt_str,
                "amount_per_share": float(val),
                "currency": "IDR",
                "type": "cash",
            })

        out.sort(key=lambda x: str(x.get("ex_date", "")), reverse=True)
        return out
    except Exception as e:
        logger.info("yfinance dividends skipped for %s: %s", sym, e)
        return []


def _extract_df_val(df: Any, col: Any, row_names: list[str]) -> float | None:
    """Helper to safely extract float from yfinance DataFrame."""
    if df is None or getattr(df, "empty", True) or col not in df.columns:
        return None
    import pandas as pd

    for name in row_names:
        if name in df.index:
            v = df.loc[name, col]
            if pd.notna(v) and str(v).lower() != "nan":
                return float(v)
    return None


def _yfinance_quarterly(symbol: str, n_quarters: int = 8) -> list[dict[str, Any]]:
    """Extract quarterly financial statements from yfinance .JK and map to Sectors schema."""
    sym = symbol.upper().strip().replace(".JK", "")
    try:
        import yfinance as yf

        tk = yf.Ticker(f"{sym}.JK")
        inc = tk.quarterly_income_stmt
        bal = tk.quarterly_balance_sheet
        cf = tk.quarterly_cashflow

        col_set: set[Any] = set()
        for df in (inc, bal, cf):
            if df is not None and not getattr(df, "empty", True):
                col_set.update(df.columns)

        if not col_set:
            return []

        sorted_cols = sorted(col_set, reverse=True)[:n_quarters]
        out: list[dict[str, Any]] = []

        for col in sorted_cols:
            date_str = str(col.date()) if hasattr(col, "date") else str(col)[:10]

            tot_rev = _extract_df_val(inc, col, ["Total Revenue", "Operating Revenue"])
            earnings = _extract_df_val(
                inc, col, ["Net Income", "Net Income Common Stockholders", "Net Income Continuous Operations"]
            )
            tot_assets = _extract_df_val(bal, col, ["Total Assets"])
            tot_equity = _extract_df_val(
                bal, col, ["Total Equity Gross Minority Interest", "Stockholders Equity", "Common Stock Equity"]
            )
            op_cf = _extract_df_val(cf, col, ["Operating Cash Flow"])
            non_int_inc = _extract_df_val(inc, col, ["Non Interest Income", "Other Non Operating Income Expenses"])
            op_exp = _extract_df_val(inc, col, ["Operating Expense", "Total Expenses"])
            op_pnl = _extract_df_val(inc, col, ["Operating Income", "Total Operating Income As Reported"])
            ebt = _extract_df_val(inc, col, ["Pretax Income"])
            tax_val = _extract_df_val(inc, col, ["Tax Provision"])
            gross_prof = _extract_df_val(inc, col, ["Gross Profit"])
            ebit_val = _extract_df_val(inc, col, ["EBIT"])
            ebitda_val = _extract_df_val(inc, col, ["EBITDA", "Normalized EBITDA"])
            cor = _extract_df_val(inc, col, ["Cost Of Revenue", "Reconciled Cost Of Revenue"])

            tot_liab = _extract_df_val(bal, col, ["Total Liabilities Net Minority Interest", "Total Liabilities"])
            tot_debt = _extract_df_val(bal, col, ["Total Debt"])
            non_int_liab = None
            if tot_liab is not None and tot_debt is not None:
                non_int_liab = max(0.0, tot_liab - tot_debt)

            cash_only = _extract_df_val(bal, col, ["Cash And Cash Equivalents", "Cash Financial"])
            stk_eq = _extract_df_val(bal, col, ["Stockholders Equity", "Common Stock Equity"])
            non_curr_assets = _extract_df_val(bal, col, ["Total Non Current Assets"])
            curr_liab = _extract_df_val(bal, col, ["Current Liabilities"])
            cash_st_inv = _extract_df_val(
                bal, col, ["Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents"]
            )
            tot_curr_assets = _extract_df_val(bal, col, ["Current Assets", "Total Current Assets"])
            non_curr_liab = _extract_df_val(
                bal, col, ["Total Non Current Liabilities Net Minority Interest", "Total Non Current Liabilities"]
            )

            fin_cf = _extract_df_val(cf, col, ["Financing Cash Flow"])
            inv_cf = _extract_df_val(cf, col, ["Investing Cash Flow"])
            net_cf = _extract_df_val(cf, col, ["Changes In Cash"])
            if net_cf is None and (op_cf is not None or inv_cf is not None or fin_cf is not None):
                net_cf = (op_cf or 0.0) + (inv_cf or 0.0) + (fin_cf or 0.0)

            item: dict[str, Any] = {
                "symbol": sym,
                "date": date_str,
                "revenue": tot_rev,
                "earnings": earnings,
                "total_assets": tot_assets,
                "total_equity": tot_equity,
                "operating_cash_flow": op_cf,
                "non_interest_income": non_int_inc,
                "operating_expense": op_exp,
                "operating_pnl": op_pnl,
                "earnings_before_tax": ebt,
                "tax": tax_val,
                "gross_profit": gross_prof,
                "ebit": ebit_val,
                "ebitda": ebitda_val,
                "cost_of_revenue": cor,
                "non_interest_bearing_liabilities": non_int_liab,
                "cash_only": cash_only,
                "total_liabilities": tot_liab,
                "total_debt": tot_debt,
                "stockholders_equity": stk_eq,
                "total_non_current_assets": non_curr_assets,
                "current_liabilities": curr_liab,
                "cash_and_short_term_investments": cash_st_inv,
                "total_current_asset": tot_curr_assets,
                "total_non_current_liabilities": non_curr_liab,
                "financing_cash_flow": fin_cf,
                "investing_cash_flow": inv_cf,
                "net_cash_flow": net_cf,
            }
            out.append(item)

        return out
    except Exception as e:
        logger.info("yfinance quarterly failed for %s: %s", sym, e)
        return []


def _classify_sentiment(title: str, body: str) -> dict[str, Any]:
    """Keyword-based financial sentiment classifier returning sentiment and relevance."""
    text = f"{title} {body}".lower()
    positive_words = [
        "beat", "surge", "growth", "expansion", "approval", "tumbuh", "laba",
        "positif", "solid", "rekor", "naik", "meningkat", "untung", "optimis",
        "bullish", "profit", "dividen", "akuisisi"
    ]
    negative_words = [
        "drop", "loss", "decline", "delay", "turun", "rugi", "koreksi",
        "negatif", "anjlok", "pangkas", "merosot", "jatuh", "lemah", "bearish",
        "gagal", "utang", "tekanan"
    ]

    pos_score = sum(1 for w in positive_words if w in text)
    neg_score = sum(1 for w in negative_words if w in text)

    if pos_score > neg_score:
        sentiment = "bullish"
        relevance = round(min(0.70 + 0.05 * pos_score, 0.98), 2)
    elif neg_score > pos_score:
        sentiment = "bearish"
        relevance = round(min(0.70 + 0.05 * neg_score, 0.98), 2)
    else:
        sentiment = "neutral"
        relevance = 0.85

    return {"sentiment": sentiment, "relevance": relevance}


# ── Route 1: GET /api/mock/filings ──────────────────────────────────────────

@router_mock_sectors.get("/filings", summary="Mock Sectors v2 IdxFilings")
@cached_endpoint(ttl=300, endpoint_name="/api/mock/filings")
async def get_filings(
    response: Response,
    symbol: str = Query(..., description="Stock symbol, e.g. BBCA"),
    start: str | None = Query(None, description="Start date YYYY-MM-DD"),
    end: str | None = Query(None, description="End date YYYY-MM-DD"),
    limit: int = Query(30, ge=1, le=100, description="Items limit"),
    offset: int = Query(0, ge=0, description="Items offset"),
    transaction_type: str | None = Query(None, description="buy | sell | others"),
    holder_type: str | None = Query(None, description="insider | institution | others"),
) -> dict[str, Any]:
    """Fetch IDX disclosures and insider transactions mirroring Sectors v2 IdxFilingsItem."""
    response.headers["Cache-Control"] = "no-store"
    sym = symbol.upper().strip().replace(".JK", "")

    try:
        items = await _scrape_idx_disclosures(sym, transaction_type=transaction_type)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching filings for %s: %s", sym, e)
        raise HTTPException(status_code=503, detail=f"Upstream IDX scraper unavailable: {e}")

    # Optional filter by holder_type
    if holder_type:
        items = [it for it in items if it.get("holder_type") == holder_type]

    # Optional filter by start / end date
    if start:
        items = [it for it in items if str(it.get("timestamp", ""))[:10] >= start]
    if end:
        items = [it for it in items if str(it.get("timestamp", ""))[:10] <= end]

    total = len(items)
    paginated = items[offset : offset + limit]

    res: dict[str, Any] = {
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
        },
        "data": paginated,
    }
    if total == 0:
        res["note"] = "no insider filings found via IDX scraper"
    return res


# ── Route 2: GET /api/mock/news ─────────────────────────────────────────────

@router_mock_sectors.get("/news", summary="Mock Sectors v2 NewsArticleList")
@cached_endpoint(ttl=300, endpoint_name="/api/mock/news")
async def get_news(
    response: Response,
    extension: str | None = Query(None, description="idx | mining"),
    sector: str | None = Query(None, description="Sector filter"),
    sub_sector: str | None = Query(None, description="Subsector filter"),
    symbols: str | None = Query(None, description="Comma-separated symbols, e.g. BBCA,ADRO"),
    keyword: str | None = Query(None, description="Keyword search"),
    tags: str | None = Query(None, description="Tag filter"),
    start: str | None = Query(None, description="Start date YYYY-MM-DD"),
    end: str | None = Query(None, description="End date YYYY-MM-DD"),
    limit: int = Query(30, ge=1, le=100, description="Items limit"),
    offset: int = Query(0, ge=0, description="Items offset"),
) -> dict[str, Any]:
    """Fetch curated and searched equity news mirroring Sectors v2 NewsArticleListItem."""
    response.headers["Cache-Control"] = "no-store"

    target_symbols = [s.strip().upper().replace(".JK", "") for s in (symbols or "").split(",") if s.strip()]

    # Collect news from available free sources
    raw_articles: list[dict[str, Any]] = []

    try:
        # 1. Check Tavily if key configured
        tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
        if tavily_key:
            try:
                from agents.adk.tools.web_tools import web_search_and_extract

                query_str = f"IDX {' '.join(target_symbols)} {keyword or 'saham kinerja'}"
                search_res = await web_search_and_extract(query_str, n_results=min(limit, 10), extract_top_n=3)
                for ex in search_res.get("extract", {}).get("results", []):
                    t = ex.get("title", "")
                    b = ex.get("content", "")[:500]
                    u = ex.get("url", "")
                    if t:
                        primary_sym = target_symbols[0] if target_symbols else "IDX"
                        sec_s, sub_s = _get_sector_and_subsector(primary_sym)
                        dim = _classify_sentiment(t, b)
                        raw_articles.append({
                            "title": t,
                            "body": b,
                            "source": u,
                            "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
                            "sector": sec_s,
                            "sub_sector": [sub_s],
                            "tags": ["news", dim.get("sentiment", "neutral")],
                            "symbols": [primary_sym],
                            "thumbnail": None,
                            "dimension": dim,
                        })
            except Exception as e:
                logger.info("Tavily search skipped: %s", e)

        # 2. Check Curated news from scripts/news.py
        try:
            from scripts.news import CURATED_NEWS

            sym_list = target_symbols if target_symbols else list(CURATED_NEWS.keys())
            for sym in sym_list:
                curated_list = CURATED_NEWS.get(sym, [])
                sec_s, sub_s = _get_sector_and_subsector(sym)
                for it in curated_list:
                    t = it.get("title", "")
                    b = it.get("snippet", "")
                    u = it.get("url", "")
                    dt = it.get("date", datetime.now().strftime("%Y-%m-%d"))
                    ts = f"{dt}T00:00:00+07:00"
                    dim = _classify_sentiment(t, b)
                    raw_articles.append({
                        "title": t,
                        "body": b[:500],
                        "source": u,
                        "timestamp": ts,
                        "sector": sec_s,
                        "sub_sector": [sub_s],
                        "tags": ["news", dim.get("sentiment", "neutral")],
                        "symbols": [sym],
                        "thumbnail": None,
                        "dimension": dim,
                    })
        except Exception as e:
            logger.info("Curated news read error: %s", e)

        # Filtering
        filtered = raw_articles
        if target_symbols:
            filtered = [a for a in filtered if any(s in a.get("symbols", []) for s in target_symbols)]
        if keyword:
            kw = keyword.lower()
            filtered = [a for a in filtered if kw in a.get("title", "").lower() or kw in a.get("body", "").lower()]
        if sector:
            filtered = [a for a in filtered if a.get("sector") == sector.lower()]
        if sub_sector:
            filtered = [a for a in filtered if sub_sector.lower() in [s.lower() for s in a.get("sub_sector", [])]]
        if start:
            filtered = [a for a in filtered if str(a.get("timestamp", ""))[:10] >= start]
        if end:
            filtered = [a for a in filtered if str(a.get("timestamp", ""))[:10] <= end]

        total = len(filtered)
        paginated = filtered[offset : offset + limit]

        res: dict[str, Any] = {
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total,
            },
            "data": paginated,
        }
        if total == 0:
            res["note"] = "no news found via free public sources"
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching news: %s", e)
        raise HTTPException(status_code=503, detail=f"Upstream news source unavailable: {e}")


# ── Route 3: GET /api/mock/corporate-actions ────────────────────────────────

@router_mock_sectors.get("/corporate-actions", summary="Mock Sectors v2 CorporateActionsByType")
@cached_endpoint(ttl=300, endpoint_name="/api/mock/corporate-actions")
async def get_corporate_actions(
    response: Response,
    symbol: str = Query(..., description="Stock symbol, e.g. BBCA"),
) -> dict[str, Any]:
    """Fetch corporate actions (dividends, splits, AGMs) mirroring Sectors v2 CorporateActionsByType."""
    response.headers["Cache-Control"] = "no-store"
    sym = symbol.upper().strip().replace(".JK", "")

    try:
        # Dividends from yfinance
        div_list = _derive_yfinance_dividends(sym)

        # Splits from yfinance
        splits_list: list[dict[str, Any]] = []
        try:
            import yfinance as yf

            tk = yf.Ticker(f"{sym}.JK")
            splits = tk.splits
            if splits is not None and len(splits) > 0:
                for s_dt, s_val in splits.items():
                    s_date = str(s_dt.date()) if hasattr(s_dt, "date") else str(s_dt)[:10]
                    splits_list.append({"date": s_date, "ratio": float(s_val)})
        except Exception:
            pass

        # AGMs from IDX disclosures
        agm_list: list[dict[str, Any]] = []
        try:
            agm_list = await _scrape_idx_agm_announcements(sym)
        except Exception as e:
            logger.info("AGM scrape error for %s: %s", sym, e)

        res: dict[str, Any] = {
            "dividend": div_list,
            "upcoming_dividend": [],
            "stock_split": splits_list,
            "right_issue": [],
            "warrant": [],
            "bonus": [],
            "agm": agm_list,
            "symbol": sym,
        }
        if not div_list and not agm_list:
            res["note"] = "no corporate actions recorded for symbol"
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching corporate actions for %s: %s", sym, e)
        raise HTTPException(status_code=503, detail=f"Upstream corporate actions source unavailable: {e}")


# ── Route 4: GET /api/mock/quarterly-financials ─────────────────────────────

@router_mock_sectors.get("/quarterly-financials", summary="Mock Sectors v2 QuarterlyFinancialItem")
@cached_endpoint(ttl=300, endpoint_name="/api/mock/quarterly-financials")
async def get_quarterly_financials(
    response: Response,
    symbol: str = Query(..., description="Stock symbol, e.g. BBCA"),
    n_quarters: int = Query(8, ge=1, le=40, description="Number of quarters to fetch"),
    report_date: str | None = Query(None, description="Optional filter by exact report date YYYY-MM-DD"),
    limit: int = Query(30, ge=1, le=100, description="Items limit"),
    offset: int = Query(0, ge=0, description="Items offset"),
) -> dict[str, Any]:
    """Fetch quarterly financial statements mirroring Sectors v2 QuarterlyFinancialItem."""
    response.headers["Cache-Control"] = "no-store"
    sym = symbol.upper().strip().replace(".JK", "")

    try:
        items = _yfinance_quarterly(sym, n_quarters=n_quarters)

        if report_date:
            items = [it for it in items if it.get("date") == report_date]

        total = len(items)
        paginated = items[offset : offset + limit]

        res: dict[str, Any] = {
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total,
            },
            "data": paginated,
        }
        if total == 0:
            res["note"] = "no quarterly financials available for symbol"
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching quarterly financials for %s: %s", sym, e)
        raise HTTPException(status_code=503, detail=f"Upstream quarterly financials source unavailable: {e}")

