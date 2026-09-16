"""Mock Sectors Router - server/routers/mock_sectors.py
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
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Response

from ..cache import cached_endpoint

logger = logging.getLogger(__name__)

router_mock_sectors = APIRouter()

# Upstream data sources provenance (Sectors-only; legacy removed, Lane E)
UPSTREAM_SOURCES: dict[str, str] = {
    "filings": "sectors filings (scrapers killed Sep 2026)",
    "news": "sectors news (scrapers+curated killed Sep 2026)",
    "corporate_actions": "sectors corporate-actions (scrapers killed Sep 2026)",
    "quarterly_financials": "sectors quarterly-financials",
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

# (Sep 2026, Sectors-only rule): IDX-scrape cache killed with the scrapers.



# ── Metadata Helpers ────────────────────────────────────────────────────────

def _resolve_taxonomy(symbol: str) -> tuple[str, str]:
    """Dynamically resolve (sector, sub_sector) slugs without hardcoded taxonomy table.

    1. Tries data/assumptions/<SYM>.json -> reads provenance.sector + archetype
    2. Falls back to data/peers.json by_ticker.<SYM>.sector
    3. Falls back to Sectors company report overview sector (keyless -> skip honestly)
    4. Returns ("unknown", "unknown") honestly - no fabrication
    """
    sym = symbol.upper().strip().replace(".JK", "")

    def _slugify(val: str) -> str:
        return val.lower().strip().replace(" ", "-").replace("_", "-")

    # 1. Tries data/assumptions/<SYM>.json -> reads provenance.sector + archetype
    assump_path = DATA_ASSUMPTIONS_DIR / f"{sym}.json"
    if assump_path.exists():
        try:
            data = json.loads(assump_path.read_text(encoding="utf-8"))
            sec = data.get("provenance", {}).get("sector") or data.get("sector")
            arch = data.get("archetype") or data.get("provenance", {}).get("archetype") or data.get("template")
            if sec:
                sec_slug = _slugify(sec)
                if arch:
                    sub_slug = _slugify(arch)
                else:
                    sub_slug = "banks" if sec_slug in ("financials", "financial-services") and sym.startswith("BB") else sec_slug
                return sec_slug, sub_slug
        except Exception:
            pass

    # 2. Falls back to data/peers.json by_ticker.<SYM>.sector
    if DATA_PEERS_PATH.exists():
        try:
            peers_data = json.loads(DATA_PEERS_PATH.read_text(encoding="utf-8"))
            by_t = peers_data.get("by_ticker", {}).get(sym, {})
            sec = by_t.get("sector")
            arch = by_t.get("archetype") or by_t.get("sub_sector") or by_t.get("subsector")
            if sec:
                sec_slug = _slugify(sec)
                if arch:
                    sub_slug = _slugify(arch)
                else:
                    sub_slug = "banks" if sec_slug in ("financials", "financial-services") and sym.startswith("BB") else sec_slug
                return sec_slug, sub_slug
        except Exception:
            pass

    # 3. Sectors company report overview sector (keyless -> skip honestly)
    try:
        from ..sectors import company_report as _sectors_report

        rep = _sectors_report(sym, "overview") or {}
        sec = rep.get("sector") or rep.get("industry") or (rep.get("overview") or {}).get("sector")
        ind = rep.get("industry") or (rep.get("overview") or {}).get("industry")
        if sec:
            sec_slug = _slugify(sec)
            sub_slug = _slugify(ind) if ind else sec_slug
            return sec_slug, sub_slug
    except Exception:
        pass

    # 4. Returns ("unknown", "unknown") honestly - no fabrication
    return "unknown", "unknown"


def _get_sector_and_subsector(symbol: str) -> tuple[str, str]:
    """Retrieve sector and sub_sector slug for a symbol (delegates to _resolve_taxonomy)."""
    return _resolve_taxonomy(symbol)
# ── Required Top-Level Helpers ──────────────────────────────────────────────

# KILLED (Sep 2026, Sectors-only rule): _scrape_idx_disclosures +
# _scrape_idx_agm_announcements lived here (Camoufox scraping of idx.co.id -
# external source, prohibited). Filings/AGMs come exclusively from the Sectors
# API now; keyless endpoints return honest empty. Do not re-add scrapers.
def _derive_sectors_dividends(symbol: str) -> list[dict[str, Any]]:
    """Historic cash dividends via Sectors corporate-actions. Keyless -> [] honest."""
    sym = symbol.upper().strip().replace(".JK", "")
    try:
        from ..sectors import corporate_actions as _sectors_acts

        acts = _sectors_acts(sym) or {}
        divs = acts.get("dividend") or acts.get("dividends") or []
        out: list[dict[str, Any]] = []
        for d in divs:
            if not isinstance(d, dict):
                continue
            dt_str = str(d.get("ex_date") or d.get("exDate") or d.get("date") or "")[:10]
            pay_str = str(d.get("payment_date") or d.get("paymentDate") or dt_str)[:10]
            amt = d.get("amount_per_share") or d.get("amount") or d.get("dividend_per_share")
            try:
                amt_f = float(amt) if amt is not None else 0.0
            except (TypeError, ValueError):
                continue
            out.append({
                "ex_date": dt_str,
                "payment_date": pay_str,
                "amount_per_share": amt_f,
                "currency": d.get("currency", "IDR"),
                "type": d.get("type", "cash"),
            })

        out.sort(key=lambda x: str(x.get("ex_date", "")), reverse=True)
        return out
    except Exception as e:
        logger.info("sectors dividends skipped for %s: %s", sym, e)
        return []


def _sectors_quarterly(symbol: str, n_quarters: int = 8) -> list[dict[str, Any]]:
    """Quarterly financial statements via Sectors (schema already mirrors v2 item).

    Keyless/mis-shaped -> [] honest (caller adds a sectors_missing_key note).
    """
    sym = symbol.upper().strip().replace(".JK", "")
    try:
        from ..sectors import quarterly as _sectors_quarterly_fn

        raw = _sectors_quarterly_fn(sym, n_quarters) or {}
        items = raw.get("data") or raw.get("results") or []
        out: list[dict[str, Any]] = []
        for it in items[:n_quarters]:
            if not isinstance(it, dict):
                continue
            row = dict(it)
            row.setdefault("symbol", sym)
            out.append(row)
        return out
    except Exception as e:
        logger.info("sectors quarterly skipped for %s: %s", sym, e)
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
    """Fetch IDX disclosures and insider transactions mirroring Sectors v2 IdxFilingsItem.

    Sectors-first when keyed; keyless falls back to the IDX scraper honestly.
    """
    response.headers["Cache-Control"] = "no-store"
    sym = symbol.upper().strip().replace(".JK", "")

    # Sectors-first (single gateway); keyless/mis-shaped -> honest empty.
    items: list[dict[str, Any]] = []
    try:
        from ..sectors import filings as _sectors_filings

        _raw = await asyncio.to_thread(_sectors_filings, sym)
        _rows = (_raw or {}).get("data") or (_raw or {}).get("results") or []
        if isinstance(_rows, list):
            sec_s, sub_s = _get_sector_and_subsector(sym)
            for _r in _rows:
                if not isinstance(_r, dict):
                    continue
                _title = str(_r.get("title") or _r.get("headline") or "")
                _body = str(_r.get("body") or _r.get("description") or _r.get("summary") or "")[:500]
                _tx = str(_r.get("transaction_type") or _r.get("transactionType") or "others").lower()
                if _tx not in ("buy", "sell"):
                    _tx = "others"
                _holder = str(_r.get("holder_type") or _r.get("holderType") or "others").lower()
                if _holder not in ("insider", "institution"):
                    _holder = "others"
                items.append({
                    "title": _title,
                    "body": _body,
                    "source": _r.get("source") or _r.get("url") or "sectors",
                    "timestamp": str(_r.get("timestamp") or _r.get("date") or datetime.now(timezone.utc).astimezone().isoformat()),
                    "sector": sec_s,
                    "sub_sector": sub_s,
                    "tags": _r.get("tags") or ["filings", sym.lower()],
                    "symbol": sym,
                    "transaction_type": _tx,
                    "holder_type": _holder,
                    "holder_name": _r.get("holder_name"),
                    "holding_before": _r.get("holding_before"),
                    "holding_after": _r.get("holding_after"),
                    "amount_transaction": _r.get("amount_transaction"),
                    "price": _r.get("price"),
                    "transaction_value": _r.get("transaction_value"),
                    "share_percentage_before": _r.get("share_percentage_before"),
                    "share_percentage_after": _r.get("share_percentage_after"),
                    "share_percentage_transaction": _r.get("share_percentage_transaction"),
                    "idx_investor_slug": _r.get("idx_investor_slug"),
                    "idx_conglomerates_group_slug": _r.get("idx_conglomerates_group_slug"),
                })
    except Exception as e:
        logger.info("sectors filings skipped for %s: %s", sym, e)

    if not items:
        # Sectors-only (Sep 2026): IDX Camoufox scraper killed (external
        # source). Empty until the Sectors key lands - never scraped.
        pass
    elif transaction_type:
        items = [it for it in items if it.get("transaction_type") == transaction_type]

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
        res["note"] = "no insider filings (Sectors keyless: set the Sectors key)"
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
        # 1. Sectors news when keyed (single gateway); keyless -> curated only, honest
        try:
            from ..sectors import news as _sectors_news

            if target_symbols:
                _raw = await asyncio.to_thread(_sectors_news, ",".join(target_symbols))
                _rows = (_raw or {}).get("data") or (_raw or {}).get("results") or []
                for _it in _rows[: min(max(1, limit), 10)]:
                    if not isinstance(_it, dict):
                        continue
                    t = _it.get("title", "")
                    b = str(_it.get("summary") or _it.get("content") or _it.get("body") or "")[:500]
                    u = _it.get("url") or _it.get("link") or ""
                    if t:
                        primary_sym = target_symbols[0] if target_symbols else "IDX"
                        sec_s, sub_s = _get_sector_and_subsector(primary_sym)
                        dim = _classify_sentiment(t, b)
                        raw_articles.append({
                            "title": t,
                            "body": b,
                            "source": u,
                            "timestamp": str(_it.get("timestamp") or _it.get("date") or datetime.now(timezone.utc).astimezone().isoformat()),
                            "sector": sec_s,
                            "sub_sector": [sub_s],
                            "tags": [t for t in (_it.get("tags") or ["news", dim.get("sentiment", "neutral")]) if t],
                            "symbols": [primary_sym],
                            "thumbnail": _it.get("thumbnail"),
                            "dimension": dim,
                        })
        except Exception as e:
            logger.info("sectors news skipped: %s", e)

        # (Sep 2026, no-fabrication sweep): curated block killed with
        # scripts/news.py CURATED_NEWS - no hand-written news served here.
        # News flows from Sectors (+ IDX scrape); empty until then, never invented.

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
        # Dividends from Sectors corporate-actions (legacy removed)
        div_list = _derive_sectors_dividends(sym)

        # Splits from Sectors corporate-actions (legacy removed)
        splits_list: list[dict[str, Any]] = []
        try:
            from ..sectors import corporate_actions as _sectors_acts_fn

            _acts = _sectors_acts_fn(sym) or {}
            for s in _acts.get("stock_split") or _acts.get("splits") or []:
                if not isinstance(s, dict):
                    continue
                s_date = str(s.get("date") or s.get("split_date") or "")[:10]
                try:
                    ratio = float(s.get("ratio") or s.get("split_ratio") or 0)
                except (TypeError, ValueError):
                    continue
                if s_date and ratio:
                    splits_list.append({"date": s_date, "ratio": ratio})
        except Exception:
            pass

        # AGMs: Sectors-only (Sep 2026) - IDX disclosure scrape killed
        # (external source). Empty until Sectors exposes meeting actions.
        agm_list: list[dict[str, Any]] = []

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
        items = _sectors_quarterly(sym, n_quarters=n_quarters)

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
            res["note"] = "no quarterly financials available for symbol (source=sectors_missing_key)"
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching quarterly financials for %s: %s", sym, e)
        raise HTTPException(status_code=503, detail=f"Upstream quarterly financials source unavailable: {e}")

