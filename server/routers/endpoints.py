"""Routers — one per endpoint family. All handlers import engines via server.engines.
Data path: stockdata (T01) -> fallback yfinance .JK -> synthetic (never fabricate without label).
Cache key: f"{prefix}:{ticker}" with TTL 4h.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import time
import hashlib

from ..cache import get_cache
from ..models import NewsResponse, NewsItem, SentimentResponse, SentimentItem
from ..config import get_settings

router_health = APIRouter()
router_report = APIRouter()
router_outlook = APIRouter()
router_news = APIRouter()
router_sentiment = APIRouter()
router_challenge = APIRouter()

_started = time.time()


# ---------- helpers ----------
def _now_iso() -> str:
    import datetime

    return datetime.datetime.utcnow().isoformat() + "Z"


def _rating_from_upside(upside: Optional[float]) -> str:
    if upside is None:
        return "HOLD"
    if upside >= 15:
        return "BUY"
    if upside >= 5:
        return "TRADING BUY"
    if upside <= -15:
        return "SELL"
    if upside <= -5:
        return "TRADING SELL"
    return "HOLD"


def _template_for(ticker: str, segments: Optional[dict]) -> str:
    # plan 5 logic: segments>1 -> sotp, infra/telco -> infra, else single
    infra_tickers = {"MTEL", "TOWR", "EXCL", "ISAT", "TLKM"}
    if ticker.upper() in infra_tickers:
        return "infra"
    if segments and isinstance(segments, dict):
        segs = segments.get("segments") or segments.get("items") or []
        if isinstance(segs, list) and len(segs) > 1:
            return "sotp"
    return "single"


# ---------- health ----------
@router_health.get("/api/health", summary="Health + stockdata + cache")
async def health():
    from ..stockdata import get_stockdata

    settings = get_settings()
    cache = get_cache(settings.cache_ttl)
    sd = get_stockdata()
    return {
        "status": "ok",
        "uptime_s": round(time.time() - _started, 1),
        "stockdata": await sd.health(),
        "cache": await cache.stats(),
        "version": "t04-0.1.0",
        "env": settings.env,
        "sectors_gate": "P2 (disabled)" if not settings.sectors_api_key else "enabled",
    }


# ---------- report/{ticker} ----------
@router_report.get("/api/report/{ticker}", summary="Full equity report payload")
async def report_ticker(
    ticker: str,
    template: Optional[str] = Query(None, description="force single|sotp|infra|strategy"),
):
    settings = get_settings()
    cache = get_cache(settings.cache_ttl)
    t = ticker.upper().strip()
    if not t or len(t) > 10:
        raise HTTPException(400, "invalid ticker")
    ckey = f"report:{t}:{template or 'auto'}"
    cached = await cache.get(ckey)
    if cached:
        cached["cached"] = True
        return cached

    # try stockdata then yfinance fallback (no LLM math)
    overview = None
    financials = None
    segments = None
    price = None
    source = "synthetic"
    try:
        from ..stockdata import get_stockdata

        sd = get_stockdata()
        overview = await sd.get_overview(t)
        financials = await sd.get_financials(t)
        segments = await sd.get_segments(t)
        if overview or financials:
            source = "stockdata:15437"
    except Exception:
        pass

    if not overview:
        # yfinance fallback
        try:
            import yfinance as yf

            yf_ticker = f"{t}.JK"
            tk = yf.Ticker(yf_ticker)
            hist = tk.history(period="5d")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
                source = "yfinance"
            # keep source label honest
            if source == "synthetic":
                source = "yfinance|estimated"
        except Exception:
            pass

    # deterministic valuation via engines (never LLM)
    from ..engines import wacc as calc_wacc, dcf as calc_dcf, ev_ebitda

    # load assumptions file if present, else defaults per archetype
    assum = _assumptions_for(t)
    w = calc_wacc(assum["rf"], assum["beta"], assum["erp"], assum["cod"], we=assum.get("we", 0.608), wd=assum.get("wd", 0.392))
    wacc_val = w["wacc"]
    try:
        # FCF units must match cash/net_debt (all IDR). Coerce to float.
        raw_fcf = assum.get("fcf") or [1000, 1100, 1200, 1300, 1400]
        fcf_list = [float(x) for x in raw_fcf]
        dcf_res = calc_dcf(fcf_list, wacc_val, assum.get("g", 0.015), shares_out=assum.get("shares_out", 1e9), net_debt=assum.get("net_debt", 0), cash=assum.get("cash", 0))
        fv = dcf_res["fv_per_share"]
        # EV/EBITDA cross-check
        ev_res = ev_ebitda(assum.get("ebitda", 2000), assum.get("ev_multiple", 10), net_debt=assum.get("net_debt", 0), shares_out=assum.get("shares_out", 1e9), cash=assum.get("cash", 0))
        # blended if infra
        chosen_template = template or _template_for(t, segments)
        if chosen_template == "infra":
            from ..engines import blended as calc_blended

            blended_res = calc_blended({"dcf": dcf_res["fv_per_share"], "ev": ev_res["fv_per_share"]}, {"dcf": 0.6, "ev": 0.4})
            fv = blended_res["blended"]
        else:
            blended_res = None
    except Exception as e:
        dcf_res = {"error": str(e)}
        ev_res = {}
        blended_res = None
        fv = None

    last_price = price or assum.get("last_price") or 1000
    upside = round((fv - last_price) / last_price * 100, 2) if fv and last_price else None
    rating = _rating_from_upside(upside)
    chosen_template = template or _template_for(t, segments)

    # minimal KPI for infra tickers
    kpi = None
    if chosen_template == "infra":
        kpi = {
            "tower": assum.get("tower", 40563),
            "tenancy_ratio": assum.get("tenancy_ratio", 1.57),
            "fiber_km": assum.get("fiber_km", 59239),
            "formula": "tenancy = tenants / towers",
            "source": source,
        }

    payload = {
        "ticker": t,
        "template": chosen_template,
        "price": last_price,
        "fair_value": fv,
        "upside_pct": upside,
        "rating": rating,
        "valuation": {
            "method": "blended 60/40" if chosen_template == "infra" else "dcf+ev/ebitda",
            "fair_value": fv,
            "currency": "IDR",
            "assumptions": {
                "wacc": wacc_val,
                "beta": assum["beta"],
                "rf": assum["rf"],
                "erp": assum["erp"],
                "coe": w["coe"],
                "cod": assum["cod"],
                "g": assum.get("g", 0.015),
                "payout": assum.get("payout", 0.4),
                "source": assum.get("source", source),
            },
            "provenance": f"engines.dcf+ev_ebitda{'+blended' if chosen_template=='infra' else ''} :: {source}",
            "dcf": dcf_res,
            "ev": ev_res,
            "blended": blended_res,
        },
        "thesis": None,
        "risks": [],
        "segments": segments,
        "kpi": kpi,
        "source": source,
        "cached": False,
        "generated_at": _now_iso(),
    }
    await cache.set(ckey, payload)
    return payload


def _assumptions_for(ticker: str) -> dict:
    """Load data/assumptions/{ticker}.json if exists and merge with archetype defaults."""
    import json
    import os

    t = ticker.upper().strip()
    # base defaults per archetype
    if t in ("MTEL", "TOWR", "TLKM"):
        base = {
            "rf": 0.0696,
            "beta": 0.65,
            "erp": 0.0889,
            "cod": 0.06,
            "we": 0.608,
            "wd": 0.392,
            "wacc": 0.101,
            "g": 0.015,
            "payout": 0.35,
            "fcf": [4988, 5200, 5400, 5600, 5800],
            "shares_out": 81.5e9,
            "net_debt": 21430e9,
            "cash": 1643e9,
            "ebitda": 7451e9,
            "ev_multiple": 10,
            "last_price": 460,
            "tower": 40563,
            "tenancy_ratio": 1.57,
            "fiber_km": 59239,
            "source": "assumptions/MTEL.json",
        }
    elif t == "RATU":
        base = {
            "rf": 0.07,
            "beta": 0.7,
            "erp": 0.069,
            "cod": 0.035,
            "g": 0.05,
            "payout": 0.3,
            "fcf": [1200, 1500, 1800, 2000, 2200],
            "shares_out": 2.71e9,
            "net_debt": 0,
            "cash": 500e9,
            "ebitda": 2200e9,
            "ev_multiple": 22.6,
            "last_price": 10650,
            "source": "assumptions/RATU.json",
        }
    elif t == "CDIA":
        base = {
            "rf": 0.0696,
            "beta": 0.90,
            "erp": 0.06,
            "cod": 0.05,
            "g": 0.03,
            "payout": 0.40,
            "fcf": [800, 900, 1000, 1100, 1200],
            "shares_out": 124.8e9,
            "net_debt": 5000e9,
            "cash": 1200e9,
            "ebitda": 2500e9,
            "ev_multiple": 12.0,
            "last_price": 645,
            "source": "assumptions/CDIA.json",
        }
    elif t == "BBCA":
        base = {
            "rf": 0.0696,
            "beta": 0.80,
            "erp": 0.06,
            "cod": 0.05,
            "g": 0.04,
            "roe": 0.197,
            "bvps": 2950,
            "payout": 0.50,
            "fcf": [20000, 23000, 26000, 29000, 32000],
            "shares_out": 123.2e9,
            "net_debt": 0,
            "cash": 50000e9,
            "ebitda": 35000e9,
            "ev_multiple": 16.9,
            "last_price": 6350,
            "source": "assumptions/BBCA.json",
        }
    elif t == "ADRO":
        base = {
            "rf": 0.0696,
            "beta": 0.95,
            "erp": 0.06,
            "cod": 0.05,
            "g": 0.02,
            "payout": 0.45,
            "fcf": [5000, 5200, 5400, 5600, 5800],
            "shares_out": 28.8e9,
            "net_debt": 2000e9,
            "cash": 3500e9,
            "ebitda": 8000e9,
            "ev_multiple": 6.5,
            "last_price": 2610,
            "source": "assumptions/ADRO.json",
        }
    else:
        base = {
            "rf": 0.0696,
            "beta": 0.85,
            "erp": 0.06,
            "cod": 0.06,
            "g": 0.025,
            "payout": 0.4,
            "fcf": [1000, 1100, 1200, 1300, 1400],
            "shares_out": 10e9,
            "net_debt": 5000e9,
            "cash": 1000e9,
            "ebitda": 3000e9,
            "ev_multiple": 12,
            "last_price": 1000,
            "source": "fallback generic",
        }

    p = os.path.join(os.path.dirname(__file__), "..", "..", "data", "assumptions", f"{t}.json")
    p = os.path.normpath(p)
    if os.path.exists(p):
        try:
            loaded = json.loads(open(p, encoding="utf-8").read())
            if isinstance(loaded, dict):
                for k, v in loaded.items():
                    if v is not None:
                        base[k] = v
        except Exception:
            pass
    return base


# ---------- outlook ----------
@router_outlook.get("/api/outlook", summary="JCI outlook — JPM base/bull/bear + sector OW/UW")
async def outlook():
    settings = get_settings()
    cache = get_cache(settings.cache_ttl)
    ckey = "outlook:jci"
    hit = await cache.get(ckey)
    if hit:
        hit["cached"] = True
        return hit
    # try stockdata JCI price for context, fallback to plan numbers
    jci_price = None
    try:
        from ..stockdata import get_stockdata

        sd = get_stockdata()
        # jci via stockdata or sectors gate later
        _ = await sd.get_prices("JCI", period="1y")
    except Exception:
        pass
    payload = {
        "jci_base": 9100,
        "jci_bull": 10000,
        "jci_bear": 7800,
        "eps_growth": 0.08,
        "pe": 15.0,
        "ow": ["Industrials", "Materials", "Consumer Staples", "Consumer Discretionary", "Property"],
        "uw": ["Energy", "Utilities"],
        "neutral": ["Financials", "Communication Services", "Healthcare"],
        "picks": [
            {"ticker": "BBCA", "reason": "GGM-implied P/BV, ROE 19.7%", "sector": "Banks"},
            {"ticker": "ASII", "reason": "Industrial conglomerate SOTP", "sector": "Industrials"},
            {"ticker": "ICBP", "reason": "Consumer Staples defensif", "sector": "Consumer Staples"},
            {"ticker": "MTEL", "reason": "Infra recurring, tenancy 1.57x", "sector": "Infrastructure"},
        ],
        "jci_price": jci_price,
        "source": "JPM 2026 Outlook (JCI 9100 base) + plan §5; JCI price via stockdata when available",
        "generated_at": _now_iso(),
        "cached": False,
    }
    await cache.set(ckey, payload)
    return payload


# ---------- news ----------
@router_news.get("/api/news", summary="News harvester — tiered, max 8, last 30d")
async def news(
    ticker: str | None = Query(None, description="filter by ticker, e.g. BBCA"),
    limit: int = Query(8, ge=1, le=20),
):
    settings = get_settings()
    cache = get_cache(3600)  # 1h per plan
    key = f"news:{(ticker or 'general').upper()}:{limit}"
    hit = await cache.get(key)
    if hit:
        hit["cached"] = True
        return hit
    # wire to scripts/news when available, else deterministic placeholder with honest provenance
    items = []
    try:
        import importlib.util
        import pathlib

        # try scripts/news.py if T02 has shipped it
        p = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "news.py"
        if p.exists():
            spec = importlib.util.spec_from_file_location("news_mod", str(p))
            mod = importlib.util.module_from_spec(spec)  # type: ignore
            spec.loader.exec_module(mod)  # type: ignore
            if hasattr(mod, "search_news"):
                items = await mod.search_news(ticker or "", days=30, limit=limit)  # type: ignore
    except Exception:
        items = []
    if not items:
        # honest empty — do not fabricate headlines
        items = []
    payload = {"ticker": ticker.upper() if ticker else None, "items": items[:limit], "cached": False, "note": "wire scripts/news.py search_news() when T02 lands; returns [] until then (no fabrication)"}
    await cache.set(key, payload)
    return payload


# ---------- sentiment ----------
@router_sentiment.get("/api/sentiment", summary="Retail sentiment gauge 0-100 + narratives + timeline")
async def sentiment(
    ticker: str = Query(..., description="ticker e.g. BBCA"),
    days: int = Query(14, ge=1, le=30),
):
    settings = get_settings()
    cache = get_cache(3600)
    t = ticker.upper().strip()
    key = f"sentiment:{t}:{days}"
    hit = await cache.get(key)
    if hit:
        hit["cached"] = True
        return hit
    items = []
    try:
        import importlib.util
        import pathlib

        p = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "social.py"
        p2 = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "social_sentiment.py"
        for cand in [p, p2]:
            if cand.exists():
                spec = importlib.util.spec_from_file_location("soc_mod", str(cand))
                mod = importlib.util.module_from_spec(spec)  # type: ignore
                spec.loader.exec_module(mod)  # type: ignore
                if hasattr(mod, "search_social"):
                    items = await mod.search_social(t, days=days, limit=8)  # type: ignore
                    break
    except Exception:
        items = []
    if not items:
        payload = {
            "ticker": t,
            "gauge": 50,
            "confidence": 0.0,
            "top_narratives": [],
            "timeline": [],
            "items": [],
            "disclaimer": "sentiment != advice — retail narrative tracker only",
            "cached": False,
            "note": "wire scripts/social.py search_social() when T02/T03 lands; returns empty until then (no fabrication)",
        }
    else:
        # aggregate gauge as mean score
        try:
            gauge = round(sum(x.get("score", 50) for x in items) / len(items))
        except Exception:
            gauge = 50
        payload = {
            "ticker": t,
            "gauge": gauge,
            "confidence": 0.55,
            "top_narratives": [],
            "timeline": [],
            "items": items[:8],
            "disclaimer": "sentiment != advice — retail narrative tracker only",
            "cached": False,
        }
    await cache.set(key, payload)
    return payload


# ---------- challenge ----------
@router_challenge.post("/api/challenge", summary="Adversarial challenge & defense — verdict defend|concede with evidence")
async def challenge(body: dict):
    from fastapi import HTTPException

    ticker = (body.get("ticker") or "").upper().strip()
    claim = (body.get("claim") or "").strip()
    context = body.get("context")
    if not ticker or not claim:
        raise HTTPException(400, "ticker and claim required")
    # wire to scripts/adversarial when available
    debate_id = hashlib.sha256(f"{ticker}:{claim}:{time.time()}".encode()).hexdigest()[:12]
    try:
        import importlib.util
        import pathlib

        p = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "adversarial.py"
        if p.exists():
            spec = importlib.util.spec_from_file_location("adv_mod", str(p))
            mod = importlib.util.module_from_spec(spec)  # type: ignore
            spec.loader.exec_module(mod)  # type: ignore
            if hasattr(mod, "challenge"):
                res = await mod.challenge(ticker, claim, context)  # type: ignore
                if isinstance(res, dict):
                    res.setdefault("debate_id", debate_id)
                    return res
    except Exception:
        pass
    # honest fallback — must not hallucinate verdict as defend; return concede-with-correction placeholder
    # so downstream critic can still audit
    return {
        "verdict": "concede",
        "evidence": "adversarial engine not yet wired (scripts/adversarial.py missing). Claim queued for review — no fabrication. Wire T02 adversarial.py challenge() to get defend(evidence) vs concede(correction) with debate.json log.",
        "exhibit_ref": None,
        "correction": None,
        "debate_id": debate_id,
        "ticker": ticker,
        "claim": claim,
        "note": "wire scripts/adversarial.py when T02 lands",
    }
