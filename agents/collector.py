"""
Collector - Sectors-first, LOUD on gaps (synthetic fallback RETIRED, Sep 2026).

Sectors API v2 is the single gateway (overview, quarterly, daily prices,
corporate actions). Keyless or mis-shaped responses raise RuntimeError with
sectors_missing_key - gaps stay missing, never invented. Output feeds Modeler
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

# Paths - relative to repo root (where plan.md lives)
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_IDX_DIR = REPO_ROOT / "data" / "idx"
OUTPUT_DIR = REPO_ROOT / "data" / "output"
ASSUMPTIONS_DIR = REPO_ROOT / "data" / "assumptions"
PEERS_PATH = REPO_ROOT / "data" / "peers.json"

CACHE_TTL_S = 4 * 3600  # 4h per plan §4

# Quintet that covers every engine (plan §11)
QUINTET = ["RATU", "CDIA", "MTEL", "BBCA", "ADRO"]

# NOTE (Sep 2026): seed-42 synthetic fallback retired (LOUD policy).
# _synthetic() below raises RuntimeError by design (pinned by tests);
# no SYNTHETIC_SEED/UNIVERSE constants - do not reintroduce invention paths.

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
    """Try data/idx/{TICKER}.json or .csv or .parquet - user-owned dumps."""
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

    Keyless or mis-shaped -> None (honest; caller raises sectors_missing_key,
    never invents). Never a silent legacy vendor fallback.
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
    """RETIRED (LOUD policy, Sep 2026): seed-42 synthetic fallback removed.

    It generated uniform(400,12000) prices and invented financials that flowed
    into Sectors-stamped payloads. Callers must use Sectors v2 or fail loud.
    """
    raise RuntimeError(
        "sectors_missing_key: synthetic fallback retired - set SECTORS_API_KEY "
        "or provide user-owned data/idx/{TICKER}.json"
    )



def _peers_for(ticker: str) -> Dict[str, Any]:
    """Load data/peers.json if exists, else empty + sectors_missing_key note (LOUD: no invented multiples)."""
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

    # LOUD policy: no invented peer multiples - Sectors peers only.
    peers = []
    return {"mode": "single", "peers": peers, "source": "sectors_missing_key",
            "note": "peer multiples await Sectors peers (no uniform() invention)"}


# ── Public API ─────────────────────────────────────────────────────────────

def collect(ticker: str, use_cache: bool = True, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Collect all data for a ticker - local IDX dumps → Sectors v2 → LOUD raise.

    No synthetic fallback (retired LOUD policy): no source -> RuntimeError
    with sectors_missing_key. Gaps stay None with *_source flags.

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
            "esg": raw.get("esg") or {"found": False, "note": "Sectors tidak provide ESG - try search, kalau tidak ada hide"},
            "ratios": raw.get("ratios"),
            "kpi": raw.get("kpi"),
            "_cache_hit": False,
        }
        # LOUD policy: missing IDX fields stay missing (no synthetic supplement).
        for k in ("segments", "peers", "jci", "prices", "kpi", "ratios"):
            if payload.get(k) is None:
                payload[f"{k}_source"] = "sectors_missing_key"
        _save_cache(t, payload)
        return payload

    # 2) Sectors v2 (single gateway) - Sectors fields only, gaps stay empty.
    sec_hit = _try_sectors(t)
    if sec_hit is not None:
        payload = {
            "ticker": t,
            "as_of": _now_iso(),
            "source": "sectors",
            "symbol": sec_hit.get("symbol"),
            "company": sec_hit.get("info") or {"symbol": t},
            "financials": sec_hit.get("financials"),
            "balance": sec_hit.get("balance"),
            "cashflow": sec_hit.get("cashflow"),
            "prices": sec_hit.get("prices"),
            "dividends": sec_hit.get("dividends") or {},
            "segments": None,
            "segments_source": "sectors_missing_key",
            "peers": _peers_for(t),
            "jci": None,
            "jci_source": "sectors_missing_key",
            "holders": None,
            "holders_source": "sectors_missing_key",
            "ratios": None,
            "ratios_source": "sectors_missing_key",
            "kpi": None,
            "kpi_source": "sectors_missing_key",
            "esg": {"found": False, "note": "Sectors tidak provide ESG - hide if not found"},
            "sectors_history_rows": sec_hit.get("history_rows"),
            "_cache_hit": False,
        }
        # Mark Sectors-absent fields explicitly (no synthetic backfill).
        if sec_hit.get("financials") is None:
            payload["financials_source"] = "sectors_missing_key"
        _save_cache(t, payload)
        return payload

    # 3) No source available - LOUD (synthetic fallback retired).
    raise RuntimeError(
        "sectors_missing_key: no IDX dump and no Sectors key for "
        f"{t} - set SECTORS_API_KEY or provide data/idx/{t}.json (synthetic fallback retired)"
    )


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
                """Collect Sectors/IDX data for a ticker (Sectors-first, loud when keyless)."""
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
            description="Data Collector - Sectors v2 + peers + JCI + KPI (cache 4h)",
            instruction=(
                "You are the Data Collector. Given a ticker, call collect(ticker) "
                "and return the JSON. Sectors v2 is the single gateway; "
                "no synthetic fallback - gaps stay missing with "
                "sectors_missing_key. Always disclose source per exhibit. "
                "Cache 4h. Never hallucinate prices - call the tool."
            ),
            tools=[tool] if tool is not None else [],
        )
        return agent
    except ImportError:
        return {
            "name": "collector",
            "description": "Data Collector (ADK not installed - use collect() directly)",
            "tool": collector_as_tool(),
        }


__all__ = ["collect", "collect_batch", "collector_as_tool", "build_collector_agent", "CACHE_TTL_S", "QUINTET"]
