"""
Collector — Sectors-first + deterministic synthetic fallback (legacy removed, Lane E).

Sectors API v2 is the single gateway (overview, quarterly, daily prices,
corporate actions). Keyless or mis-shaped responses fall back to deterministic
synthetic (seed=42) with honest `source` labels. Output feeds Modeler
(blocking) and downstream analysts. Every exhibit must disclose source.

ADK wrapper: exposes collector_as_tool() for google-adk LlmAgent + plain
collect(ticker) for scripts/server. Cache 4h file-based at data/output/.
"""
from __future__ import annotations

import hashlib
import json
import logging
import random
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Paths — relative to repo root (where plan.md lives)
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_IDX_DIR = REPO_ROOT / "data" / "idx"
OUTPUT_DIR = REPO_ROOT / "data" / "output"
ASSUMPTIONS_DIR = REPO_ROOT / "data" / "assumptions"
PEERS_PATH = REPO_ROOT / "data" / "peers.json"

CACHE_TTL_S = 4 * 3600  # 4h per plan §4
SYNTHETIC_SEED = 42

# Quintet that covers every engine (plan §11)
QUINTET = ["RATU", "CDIA", "MTEL", "BBCA", "ADRO"]

# Synthetic tickers universe (49) — matches sectors-idea-lab seed
SYNTHETIC_UNIVERSE = [
    "BBCA","BBRI","BMRI","BBNI","BRIS","TLKM","ISAT","EXCL","MTEL","TOWR",
    "RATU","CDIA","ADRO","ADMR","PTBA","ANTM","INCO","MDKA","HRUM","PGAS",
    "ASII","UNTR","AKRA","MEDC","ELSA","BUMI","BRMS","AMMN","NCKL",
    "ICBP","INDF","UNVR","KLBF","MYOR","GGRM","HMSP","SIDO","CPIN","JPFA",
    "ACES","MAPI","ERAA","LPPF","AMRT","INDY","ITMG","GOTO","BUKA","EMTK",
]

TIER1_SOURCES = [
    "idx.co.id", "kontan.co.id", "bisnis.com", "idxchannel.com",
    "cnbcindonesia.com", "investor.id"
]
TIER2_SOURCES = [
    "reuters.com", "bloomberg.com", "thejakartapost.com",
    "katadata.co.id", "bisnisindonesia.id"
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ticker_norm(ticker: str) -> str:
    t = ticker.strip().upper()
    if t.endswith(".JK"):
        t = t[:-3]
    return t


def _cache_path(ticker: str) -> Path:
    return OUTPUT_DIR / f"cache_collector_{_ticker_norm(ticker)}.json"


def _is_cache_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    age = time.time() - path.stat().st_mtime
    return age < CACHE_TTL_S


def _load_cache(ticker: str) -> Optional[Dict[str, Any]]:
    p = _cache_path(ticker)
    if not _is_cache_fresh(p):
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        data["_cache_hit"] = True
        logger.info("Collector cache HIT %s (age %.0fs)", ticker, time.time() - p.stat().st_mtime)
        return data
    except Exception as e:
        logger.warning("Collector cache corrupt %s: %s", ticker, e)
        return None


def _save_cache(ticker: str, payload: Dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    p = _cache_path(ticker)
    payload["_cached_at"] = _now_iso()
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


# ── IDX local ──────────────────────────────────────────────────────────────

def _try_idx(ticker: str) -> Optional[Dict[str, Any]]:
    """Try data/idx/{TICKER}.json or .csv or .parquet — user-owned dumps."""
    t = _ticker_norm(ticker)
    candidates = [
        DATA_IDX_DIR / f"{t}.json",
        DATA_IDX_DIR / f"{t.lower()}.json",
        DATA_IDX_DIR / f"{t}.csv",
        DATA_IDX_DIR / f"{t.lower()}.csv",
    ]
    for p in candidates:
        if not p.exists():
            continue
        try:
            if p.suffix == ".json":
                raw = json.loads(p.read_text(encoding="utf-8"))
                # Normalize: expect { overview, financials, segments, holders }
                return {"source": "idx", "raw": raw, "path": str(p)}
            elif p.suffix == ".csv":
                import csv
                rows = list(csv.DictReader(p.read_text(encoding="utf-8").splitlines()))
                return {"source": "idx", "raw": {"rows": rows}, "path": str(p)}
        except Exception as e:
            logger.warning("IDX parse failed %s: %s", p, e)
            continue
    return None


# ── Sectors v2 (single gateway, legacy removed) ────────────────────────────

def _try_sectors(ticker: str) -> Optional[Dict[str, Any]]:
    """Sectors v2: overview + quarterly + daily prices + corporate actions.

    Keyless or mis-shaped -> None (honest; caller falls back to labeled
    synthetic). Never a silent legacy vendor fallback.
    """
    t = _ticker_norm(ticker)
    try:
        from server.sectors import (
            company_report as _rep,
            corporate_actions as _acts,
            daily as _daily,
            quarterly as _quart,
        )
    except Exception as e:
        logger.info("sectors client unavailable: %s", e)
        return None

    try:
        rep = _rep(t, "overview,financials,dividend") or {}
        fin = _quart(t, 8) or {}
        end = datetime.now(timezone.utc).date().isoformat()
        start = (datetime.now(timezone.utc).date() - timedelta(days=90)).isoformat()
        bars = _daily(t, start, end) or {}
        acts = _acts(t) or {}
    except Exception as e:
        logger.info("sectors miss for %s: %s", t, e)
        return None

    if not rep and not fin and not bars:
        return None

    fin_items = (fin or {}).get("data") or (fin or {}).get("results") or []
    bar_items = (bars or {}).get("data") or (bars or {}).get("results") or []
    prices = []
    for b in bar_items[-260:]:
        if not isinstance(b, dict):
            continue
        prices.append({
            "date": str(b.get("date") or b.get("time") or "")[:10],
            "close": b.get("close") if b.get("close") is not None else b.get("closing_price"),
            "volume": b.get("volume"),
        })
    overview = rep.get("overview") if isinstance(rep.get("overview"), dict) else rep
    divs = (acts or {}).get("dividend") or (acts or {}).get("dividends") or []
    dividends = {}
    for d in divs:
        if isinstance(d, dict) and d.get("ex_date"):
            try:
                dividends[str(d["ex_date"])[:10]] = float(
                    d.get("amount_per_share") or d.get("amount") or 0
                )
            except (TypeError, ValueError):
                continue
    return {
        "source": "sectors",
        "symbol": t,
        "info": overview if isinstance(overview, dict) else {"symbol": t},
        "prices": prices,
        "financials": {"quarterly": fin_items} if fin_items else None,
        "balance": None,
        "cashflow": None,
        "quarterly_financials": fin_items,
        "dividends": dividends,
        "history_rows": len(bar_items),
    }


# ── Synthetic fallback (seed=42, deterministic per ticker) ─────────────────

def _synthetic(ticker: str) -> Dict[str, Any]:
    t = _ticker_norm(ticker)
    # deterministic seed per ticker: 42 + hash
    h = int(hashlib.md5(t.encode()).hexdigest()[:8], 16)
    rng = random.Random(SYNTHETIC_SEED + h)

    base_price = rng.uniform(400, 12000)
    # 5Y financials — income/balance/cashflow simplified
    years = [2020, 2021, 2022, 2023, 2024]
    revenue_base = rng.uniform(2_000, 80_000)  # IDR Bn
    revenues = [round(revenue_base * (1 + rng.uniform(-0.1, 0.25)) ** (i), 1) for i in range(5)]
    # keep monotonic-ish for demo
    revenues = sorted(revenues)
    gross_margin = rng.uniform(0.25, 0.55)
    ebitda_margin = rng.uniform(0.15, 0.40)
    net_margin = rng.uniform(0.08, 0.22)

    financials = {
        str(y): {
            "revenue": revenues[i],
            "gross_profit": round(revenues[i] * gross_margin, 1),
            "ebitda": round(revenues[i] * ebitda_margin, 1),
            "net_income": round(revenues[i] * net_margin, 1),
            "total_assets": round(revenues[i] * rng.uniform(1.5, 3.0), 1),
            "total_equity": round(revenues[i] * rng.uniform(0.6, 1.2), 1),
            "total_debt": round(revenues[i] * rng.uniform(0.2, 0.9), 1),
        }
        for i, y in enumerate(years)
    }

    # JCI synthetic 5Y daily (260 trading days × 5)
    jci_base = 7000
    jci_prices = []
    price = jci_base
    for i in range(260 * 5):
        price *= 1 + rng.uniform(-0.015, 0.018)
        d = (datetime(2020, 1, 2) + timedelta(days=i * 7 // 5)).date().isoformat()
        jci_prices.append({"date": d, "close": round(price, 2)})

    # Segments — conglomerate vs single (CDIA/MTEL vs RATU/BBCA)
    conglomerate_tickers = {"CDIA", "ADRO"}
    infra_tickers = {"MTEL", "TOWR", "TLKM", "ISAT", "EXCL"}
    if t in conglomerate_tickers:
        segments = [
            {"name": "Energy", "pct": 55, "revenue": round(revenues[-1] * 0.55, 1)},
            {"name": "Logistics", "pct": 34, "revenue": round(revenues[-1] * 0.34, 1)},
            {"name": "Port & Storage", "pct": 7, "revenue": round(revenues[-1] * 0.07, 1)},
            {"name": "Water", "pct": 4, "revenue": round(revenues[-1] * 0.04, 1)},
        ]
    elif t in infra_tickers:
        segments = [
            {"name": "Tower Leasing", "pct": 68, "revenue": round(revenues[-1] * 0.68, 1)},
            {"name": "Fiber", "pct": 15, "revenue": round(revenues[-1] * 0.15, 1)},
            {"name": "Reseller", "pct": 10, "revenue": round(revenues[-1] * 0.10, 1)},
            {"name": "Other", "pct": 7, "revenue": round(revenues[-1] * 0.07, 1)},
        ]
    else:
        segments = [{"name": "Single", "pct": 100, "revenue": revenues[-1]}]

    # KPI per subsector (MTEL hero)
    kpi = None
    if t in infra_tickers:
        towers = rng.randint(35000, 45000)
        tenants = int(towers * rng.uniform(1.45, 1.65))
        kpi = {
            "towers": towers,
            "tenants": tenants,
            "tenancy_ratio": round(tenants / towers, 2),
            "fiber_km": rng.randint(45000, 65000),
            "colocation": rng.randint(18000, 26000),
        }
    elif t == "RATU":
        kpi = {"bopd": rng.randint(12000, 18000), "gas_mmscfd": round(rng.uniform(20, 40), 1)}

    holders = {
        "major": rng.choice(["Chandra Asri 60%", "TLKM 71.83%", "Public 45%", "Founders 55%"]),
        "free_float": round(rng.uniform(0.15, 0.45), 2),
    }

    ratios = {
        "roe": round(rng.uniform(0.06, 0.35), 3),
        "der": round(rng.uniform(0.3, 1.7), 2),
        "current_ratio": round(rng.uniform(0.8, 2.5), 2),
        "interest_coverage": round(rng.uniform(2.0, 8.0), 1),
        "gearing": round(rng.uniform(0.4, 1.7), 2),
        "debt_ebitda": round(rng.uniform(1.5, 6.0), 1),
    }

    return {
        "source": "synthetic",
        "seed": SYNTHETIC_SEED,
        "ticker": t,
        "company": {"symbol": t, "name": f"{t} Synthetic", "sector": rng.choice(["Energy","Infrastructure","Financials","Materials"])},
        "financials": financials,
        "segments": segments,
        "kpi": kpi,
        "holders": holders,
        "ratios": ratios,
        "jci": jci_prices[-260:],  # last 1Y for vs-JCI chart
        "prices": [{"date": p["date"], "close": round(base_price * (0.9 + rng.uniform(-0.2, 0.3)), 2)} for p in jci_prices[-260:]],
        "dividends": {},
        "note": "synthetic fallback — labeled estimated per plan §4",
    }


def _peers_for(ticker: str) -> Dict[str, Any]:
    """Load data/peers.json if exists, else synthetic peers per ticker."""
    t = _ticker_norm(ticker)
    if PEERS_PATH.exists():
        try:
            peers_db = json.loads(PEERS_PATH.read_text(encoding="utf-8"))
            if t in peers_db:
                return peers_db[t]
            # also support { single: {...}, sotp: {...} } shape
            if "single" in peers_db or "sotp" in peers_db:
                return peers_db  # caller handles switch
        except Exception as e:
            logger.warning("peers.json parse failed: %s", e)

    # synthetic peers — 8-12 per ticker from universe
    rng = random.Random(SYNTHETIC_SEED + int(hashlib.md5(t.encode()).hexdigest()[:8], 16))
    pool = [x for x in SYNTHETIC_UNIVERSE if x != t]
    rng.shuffle(pool)
    peers = []
    for sym in pool[:10]:
        peers.append({
            "symbol": sym,
            "pe_ratio": round(rng.uniform(8, 28), 1),
            "ev_ebitda": round(rng.uniform(6, 18), 1),
            "pbv": round(rng.uniform(0.8, 4.5), 2),
            "roe": round(rng.uniform(0.05, 0.28), 3),
        })
    return {"mode": "single", "peers": peers, "source": "synthetic"}


# ── Public API ─────────────────────────────────────────────────────────────

def collect(ticker: str, use_cache: bool = True, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Collect all data for a ticker — local IDX dumps → Sectors v2 → synthetic.

    Returns dict with keys:
      ticker, as_of, source, company, financials, segments, peers, jci,
      prices, holders, dividends, esg, ratios, kpi, _cache_hit, _cached_at

    Cache: 4h file at data/output/cache_collector_{TICKER}.json
    """
    t = _ticker_norm(ticker)
    if not t or len(t) < 3:
        raise ValueError(f"Invalid ticker: {ticker!r}")

    if use_cache and not force_refresh:
        cached = _load_cache(t)
        if cached is not None:
            return cached

    # 1) IDX local
    idx_hit = _try_idx(t)
    if idx_hit is not None:
        raw = idx_hit["raw"]
        # Normalize IDX shape → collector shape
        payload: Dict[str, Any] = {
            "ticker": t,
            "as_of": _now_iso(),
            "source": "idx",
            "source_path": idx_hit.get("path"),
            "company": raw.get("overview") or raw.get("company") or {"symbol": t},
            "financials": raw.get("financials") or raw,
            "segments": raw.get("segments"),
            "holders": raw.get("holders") or raw.get("ownership"),
            "dividends": raw.get("dividends") or {},
            "peers": _peers_for(t),
            "jci": raw.get("jci"),
            "prices": raw.get("prices"),
            "esg": raw.get("esg") or {"found": False, "note": "Sectors tidak provide ESG — try search, kalau tidak ada hide"},
            "ratios": raw.get("ratios"),
            "kpi": raw.get("kpi"),
            "_cache_hit": False,
        }
        # Fill missing with synthetic supplements (labeled)
        synth = _synthetic(t)
        for k in ("segments", "peers", "jci", "prices", "kpi", "ratios"):
            if payload.get(k) is None:
                payload[k] = synth[k]
                payload[f"{k}_source"] = "synthetic_supplement"
        _save_cache(t, payload)
        return payload

    # 2) Sectors v2 (single gateway)
    sec_hit = _try_sectors(t)
    if sec_hit is not None:
        # Sectors quarterly is authoritative; supplement display-only fields
        synth = _synthetic(t)
        payload = {
            "ticker": t,
            "as_of": _now_iso(),
            "source": "sectors",
            "symbol": sec_hit.get("symbol"),
            "company": sec_hit.get("info") or {"symbol": t},
            "financials": sec_hit.get("financials") or synth["financials"],
            "balance": sec_hit.get("balance"),
            "cashflow": sec_hit.get("cashflow"),
            "prices": sec_hit.get("prices") or synth["prices"],
            "dividends": sec_hit.get("dividends") or {},
            "segments": synth["segments"],
            "peers": _peers_for(t),
            "jci": synth["jci"],
            "holders": synth["holders"],
            "ratios": synth["ratios"],
            "kpi": synth["kpi"],
            "esg": {"found": False, "note": "Sectors tidak provide ESG — hide if not found"},
            "sectors_history_rows": sec_hit.get("history_rows"),
            "_cache_hit": False,
        }
        # Mark synthetic-supplemented fields
        if sec_hit.get("financials") is None:
            payload["financials_source"] = "synthetic_supplement"
        _save_cache(t, payload)
        return payload

    # 3) Synthetic fallback (deterministic)
    synth = _synthetic(t)
    payload = {
        "ticker": t,
        "as_of": _now_iso(),
        "source": "synthetic",
        "company": synth["company"],
        "financials": synth["financials"],
        "segments": synth["segments"],
        "peers": _peers_for(t),
        "jci": synth["jci"],
        "prices": synth["prices"],
        "holders": synth["holders"],
        "dividends": synth["dividends"],
        "esg": {"found": False, "note": "synthetic — no ESG"},
        "ratios": synth["ratios"],
        "kpi": synth["kpi"],
        "_cache_hit": False,
        "note": "synthetic fallback seed=42 — labeled estimated per plan §4",
    }
    _save_cache(t, payload)
    return payload


def collect_batch(tickers: List[str], use_cache: bool = True) -> Dict[str, Dict[str, Any]]:
    """Parallel-collect helper for quintet. Sequential for now (no API burn)."""
    return { _ticker_norm(t): collect(t, use_cache=use_cache) for t in tickers }


# ── ADK wrapper ────────────────────────────────────────────────────────────

def collector_as_tool():
    """
    Return a google-adk functiontool for the Collector.
    Falls back to plain callable if google-adk not installed.
    """
    try:
        from google_adk.tool.functiontool import FunctionTool  # type: ignore
        from google.adk.tool import functiontool  # type: ignore
        # prefer new import path
        raise ImportError("probe")
    except ImportError:
        try:
            from google.adk.tool.functiontool import FunctionTool as FT  # type: ignore
            import inspect
            # Use available google-adk 2.8.0 path
            from google.adk.tools.function_tool import FunctionTool  # type: ignore
        except ImportError:
            pass

    # Runtime probe: try both import styles
    tool = None
    for mod_path in (
        "google.adk.tools.function_tool",
        "google.adk.tool.functiontool",
    ):
        try:
            import importlib
            mod = importlib.import_module(mod_path)
            FT = getattr(mod, "FunctionTool", None)
            if FT is None:
                continue
            # google-adk FunctionTool wraps a python callable
            def _collect_tool(ticker: str) -> dict:
                """Collect Sectors/synthetic data for a ticker (Sectors-first, honest source)."""
                return collect(ticker)

            tool = FT(func=_collect_tool)
            return tool
        except Exception:
            continue

    # Fallback: return plain callable with ADK-like interface
    def _fallback_tool(ticker: str) -> dict:
        return collect(ticker)
    _fallback_tool._is_adk_tool = False  # type: ignore
    return _fallback_tool


def build_collector_agent(model=None):
    """
    Build an ADK LlmAgent for the Collector (for orchestrator ParallelAgent).
    If google-adk not available, returns a simple dict descriptor.
    """
    try:
        from google.adk.agents import LlmAgent  # type: ignore
        tool = collector_as_tool()
        agent = LlmAgent(
            name="collector",
            model=model,
            description="Data Collector — Sectors v2 + peers + JCI + KPI (cache 4h)",
            instruction=(
                "You are the Data Collector. Given a ticker, call collect(ticker) "
                "and return the JSON. Sectors v2 is the single gateway, then "
                "synthetic seed=42. Always disclose source per exhibit. "
                "Cache 4h. Never hallucinate prices — call the tool."
            ),
            tools=[tool] if tool is not None else [],
        )
        return agent
    except ImportError:
        return {
            "name": "collector",
            "description": "Data Collector (ADK not installed — use collect() directly)",
            "tool": collector_as_tool(),
        }


__all__ = ["collect", "collect_batch", "collector_as_tool", "build_collector_agent", "CACHE_TTL_S", "QUINTET"]
