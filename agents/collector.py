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
import os
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


# Cache paths - two layers:
#   (1) per-ticker file under data/output/ (4h TTL) - the rendered payload
#   (2) per-ticker freeze under output/cache/ticker_fill/ (7d TTL). The directory
#       is named `ticker_fill` (not `ammn_fill`) so any ticker's freeze lives
#       there without renaming. The historical `ammn_fill/` path is still
#       consulted as a legacy alias - AMMN's existing freeze (kanban t_2c5f420e)
#       was dropped there before the rename, and forcing a move would invalidate
#       any in-flight runs that hold the path. A different lane wanting the same
#       behaviour just drops a `*_{TICKER}.json` set into output/cache/ticker_fill/.
_LOCAL_FILL_DIR = REPO_ROOT / "output" / "cache" / "ticker_fill"
_LEGACY_FILL_DIR = REPO_ROOT / "output" / "cache" / "ammn_fill"


def _freeze_path_for(ticker: str) -> Path | None:
    """Return the existing freeze directory for a ticker (ticker_fill first, ammn_fill fallback).

    The freeze is a set of `*_{TICKER}.json` files written by a separate lane. Any ticker
    that has been pre-populated (regardless of who populated it) is served here at zero
    Sectors cost. New lanes should write to `ticker_fill/`; `ammn_fill/` is kept for the
    historical AMMN freeze only.
    """
    for d in (_LOCAL_FILL_DIR, _LEGACY_FILL_DIR):
        if (d / f"company_report_{ticker}_multisection.json").exists() \
                or (d / f"company_report_{ticker}.json").exists():
            return d
    return None


def _ticker_fill_payload(ticker: str) -> Optional[Dict[str, Any]]:
    """Return the per-ticker freeze payload if a freeze exists and is <7d old.

    The freeze carries the four endpoints the rate log was burning (corporate-actions,
    quarterly, company/report, daily), so reusing it lets the collector serve a full
    payload with zero Sectors API calls. The directory is owned by the freeze lane;
    another lane wanting the same behaviour just drops a matching `*_{TICKER}.json`
    set into output/cache/ticker_fill/ (or output/cache/ammn_fill/ as legacy alias).
    """
    fill_dir = _freeze_path_for(ticker)
    if fill_dir is None:
        return None
    fill_path = fill_dir / f"company_report_{ticker}_multisection.json"
    if not fill_path.exists():
        alt = fill_dir / f"company_report_{ticker}.json"
        if alt.exists():
            fill_path = alt
        else:
            return None
    age = time.time() - fill_path.stat().st_mtime
    # Freeze TTL = 7 days. The freeze lane is the canonical source for any ticker's
    # data; if the freeze is older than 7 days the analyst should either refresh it
    # or accept that the collector says sectors_missing_key instead of burning
    # upstream on a render. The shorter the TTL, the more often this fires when only
    # ~1 person is editing the freeze by hand.
    if age > 7 * 24 * 3600:
        return None
    try:
        raw = json.loads(fill_path.read_text(encoding="utf-8"))
        overview = (raw.get("overview") or {}) if isinstance(raw, dict) else {}
        # Surface the freeze as a Sector-shaped dict so the rest of the pipeline
        # (modeler, analyst) can run unchanged.
        return {
            "source": "ticker_fill_freeze",
            "legacy_source": "ammn_fill_freeze" if fill_dir == _LEGACY_FILL_DIR else None,
            "symbol": ticker,
            "info": overview if isinstance(overview, dict) else {"symbol": ticker},
            "financials": None,
            "balance": None,
            "cashflow": None,
            "prices": None,
            "dividends": {},
            "freeze_path": str(fill_path),
            "freeze_age_s": int(age),
        }
    except Exception as e:
        logger.warning("ticker-fill freeze corrupt %s: %s", ticker, e)
        return None


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
    _mirror_to_sectors_cache(ticker, payload)


def _mirror_to_sectors_cache(ticker: str, payload: Dict[str, Any]) -> None:
    """Best-effort write of the rendered payload into the SQLite sectors_cache
    so subsequent ADK tool calls (sectors_quarterly, sectors_company_report,
    sectors_daily, sectors_corporate_actions, sectors_foreign_flow,
    sectors_filings, sectors_segments) hit the cache instead of upstream.

    The mirror is opportunistic: it writes the rows it can derive from the
    payload, never raises on failure, and never blocks the collector. Cache
    misses (e.g. freeze carries no prices) are simply skipped.

    Each row gets the same TTL the upstream _get() uses (93 days = the
    `_ttl_for()` default in server/storage.py), so the mirror stays warm
    past the 4h file TTL until 93 days from now.

    Two sources feed the mirror:
      (a) the rendered payload (overview + dividends from freeze; prices +
          quarterly from a live Sectors pull).
      (b) the raw freeze files in output/cache/ticker_fill/* (legacy alias: ammn_fill/*) - direct reads
          of the multisection report, daily, quarterly, corporate-actions,
          broker_top, foreign_flow, and segments JSONs. The freeze files
          are richer than the rendered payload, so the mirror catches more
          endpoints this way (without paying for any Sectors call).
    """
    try:
        from server.storage import SectorsCache  # late-bound import
    except Exception:
        return

    t = _ticker_norm(ticker)
    try:
        cache = SectorsCache()
    except Exception:
        return

    ttl_s = 93 * 24 * 3600  # storage default; matches upstream _get()

    # (b) Mirror from freeze files first - richest source, no upstream cost.
    # Any ticker freeze lane writes:
    #   company_report_<TICKER>_multisection.json, daily_<TICKER>_90d.json,
    #   quarterly_<TICKER>_8.json, corporate_actions_<TICKER>.json,
    #   foreign_flow_<TICKER>_90d.json, broker_top_<TICKER>_30d.json,
    #   segments_<TICKER>_<YYYY>.json.
    # The mirror walks both ticker_fill/ (new) and ammn_fill/ (legacy alias) so a
    # ticker's freeze can live in either directory without code change.
    freeze_dirs = [d for d in (_LOCAL_FILL_DIR, _LEGACY_FILL_DIR) if d.exists()]
    freeze_map: dict[str, tuple[str, dict]] = {
        f"/daily/{t}/": (
            f"daily_{t}_90d.json",
            {"start": "freeze", "end": "freeze"},
        ),
        f"/financials/quarterly/{t}/": (
            f"quarterly_{t}_8.json",
            {"n_quarters": 8},
        ),
        f"/company/corporate-actions/{t}/": (
            f"corporate_actions_{t}.json",
            {},
        ),
        f"/foreign-flow/{t}/": (
            f"foreign_flow_{t}_90d.json",
            {"start": "freeze", "end": "freeze"},
        ),
        f"/broker-summary/{t}/top/": (
            f"broker_top_{t}_30d.json",
            {"start": "freeze", "end": "freeze", "n_brokers": 20},
        ),
        f"/company/report/{t}/": (
            f"company_report_{t}_multisection.json",
            {"sections": "overview,financials,dividend,peers,ownership,management,valuation,future"},
        ),
    }
    for endpoint, (fname, params) in freeze_map.items():
        p = None
        for freeze_dir in freeze_dirs:
            cand = freeze_dir / fname
            if cand.exists():
                p = cand
                break
            if endpoint == f"/company/report/{t}/":
                alt = freeze_dir / f"company_report_{t}.json"
                if alt.exists():
                    p = alt
                    break
        if p is None:
            continue
        try:
            body = json.loads(p.read_text(encoding="utf-8"))
            cache.set(endpoint, params, body, ttl_s)
        except Exception:
            pass

    # segments_<TICKER>_<YYYY>.json may exist for 1-2 years; mirror each, walking both
    # directories (new ticker_fill first, then legacy ammn_fill) so a ticker's segments
    # files can live in either without changing the collector.
    for freeze_dir in freeze_dirs:
        for seg in freeze_dir.glob(f"segments_{t}_*.json"):
            try:
                year = seg.stem.rsplit("_", 1)[-1]
                body = json.loads(seg.read_text(encoding="utf-8"))
                cache.set(f"/company/get-segments/{t}/",
                          {"financial_year": year}, body, ttl_s)
            except Exception:
                pass

    # (a) Also mirror anything the rendered payload carries - this covers
    # the live-Sectors path (when freeze absent) AND the dividend table
    # pulled from the corporate-actions freeze above.
    prices = payload.get("prices") or []
    if prices and isinstance(prices, list):
        body = {"data": [{"date": p.get("date"), "close": p.get("close"),
                          "volume": p.get("volume")}
                         for p in prices if isinstance(p, dict)]}
        try:
            cache.set(f"/daily/{t}/", {"start": "freeze", "end": "freeze"}, body, ttl_s)
        except Exception:
            pass

    fin = payload.get("financials")
    if isinstance(fin, dict):
        q = fin.get("quarterly") if isinstance(fin, dict) else None
        if q:
            try:
                cache.set(f"/financials/quarterly/{t}/", {"n_quarters": 8},
                          {"data": q}, ttl_s)
            except Exception:
                pass

    info = payload.get("company") or payload.get("info")
    if info and isinstance(info, dict) and info != {"symbol": t}:
        try:
            cache.set(f"/company/report/{t}/", {"sections": "overview"},
                      {"overview": info}, ttl_s)
        except Exception:
            pass

    divs = payload.get("dividends")
    if divs:
        try:
            items = [{"ex_date": k, "amount_per_share": v}
                     for k, v in divs.items() if isinstance(k, str)]
            cache.set(f"/company/corporate-actions/{t}/", {},
                      {"dividend": items}, ttl_s)
        except Exception:
            pass


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

# Credit guard (12 Sep 2026): pin the window anchor once per process. Two
# `collect(ticker)` calls in the same ADK run used to drift the daily/foreign
# window by 1 day each, generating 9 distinct cache_keys for the same data and
# burning 9 credits when 1 would have done. The dated anchor is set on first
# call and reused for the lifetime of this Python process (matches the
# server/storage.SectorsCache TTL of years). Override via SECTORS_DAILY_END.
from datetime import datetime as _dt, timedelta as _td, timezone as _tz
_WINDOW_ANCHOR: dict[str, str | None] = {"end": None, "start": None}


def _pinned_window() -> tuple[str, str]:
    """Return (start, end) ISO dates; pin for the process so cache_key stays stable."""
    if _WINDOW_ANCHOR["end"] is None:
        end = os.getenv("SECTORS_DAILY_END", "").strip() or _dt.now(_tz.utc).date().isoformat()
        start_dt = _dt.fromisoformat(end).date() - _td(days=90)
        start = start_dt.isoformat()
        _WINDOW_ANCHOR["end"] = end
        _WINDOW_ANCHOR["start"] = start
    # type narrowing: the only way to leave the None branch is to populate both keys
    return _WINDOW_ANCHOR["start"], _WINDOW_ANCHOR["end"]  # type: ignore[return-value]


def _try_sectors(ticker: str) -> Optional[Dict[str, Any]]:
    """Sectors v2: overview + quarterly + daily prices + corporate actions.

    Keyless or mis-shaped -> None (honest; caller raises sectors_missing_key,
    never invents). Never a silent legacy vendor fallback.

    Window is pinned via _pinned_window() so re-renders and adjacent calls in
    the same process share the same cache_key. Without the pin a 9-render burst
    burns 9 credits instead of 1.
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
        start, end = _pinned_window()
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

    # 0) AMMN-FILLD freeze (12h) - serves 4 endpoints at 0 credits when present.
    #    Always consulted BEFORE any Sectors call so a /api/agent/run click does
    #    not re-bill the upstream on each render.
    fill_hit = _ticker_fill_payload(t)
    if fill_hit is not None:
        # Two source labels on offer: the new "ticker_fill_*" (preferred) and the legacy
        # "ammn_fill_*" (for callers that pattern-match the historical string). The freeze
        # itself is the same shape on disk; only the label changed.
        legacy = fill_hit.get("legacy_source") == "ammn_fill_freeze"
        passthrough = "ammn_fill_freeze_passthrough" if legacy else "ticker_fill_freeze_passthrough"
        payload: Dict[str, Any] = {
            "ticker": t,
            "as_of": _now_iso(),
            "source": fill_hit.get("source"),
            "source_path": fill_hit.get("freeze_path"),
            "company": fill_hit.get("info") or {"symbol": t},
            "financials": fill_hit.get("financials"),
            "segments": None,
            "segments_source": passthrough,
            "peers": _peers_for(t),
            "jci": None,
            "jci_source": passthrough,
            "holders": None,
            "holders_source": passthrough,
            "dividends": fill_hit.get("dividends") or {},
            "prices": fill_hit.get("prices"),
            "ratios": None,
            "ratios_source": passthrough,
            "kpi": None,
            "kpi_source": passthrough,
            "esg": {"found": False, "note": "freeze carries no ESG - render bare"},
            "_cache_hit": False,
            "_freeze_age_s": fill_hit.get("freeze_age_s"),
        }
        _save_cache(t, payload)
        return payload

    # 0b) SECTORS_OFFLINE=1 hard short-circuit - refuse to call upstream on purpose.
    #    Lets a run operator pause burns without uninstalling the key. Same
    #    loud-empty contract as keyless: gaps stay missing, never invented.
    if os.getenv("SECTORS_OFFLINE", "").strip().lower() in ("1", "true", "yes"):
        raise RuntimeError(
            f"sectors_offline_mode: SECTORS_OFFLINE=1 set, refusing to call upstream for {t}. "
            f"Either unset SECTORS_OFFLINE or supply a freeze at output/cache/ticker_fill/"
            f"company_report_{t}_multisection.json so the collector can serve from disk."
        )

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


def _typography_rule() -> str:
    """The §12 typography block, so this legacy builder's agent is told the rule too.

    Imported defensively: this path has to keep building when the ADK package is absent. The rule
    lives in one place (agents/adk/agents/instructions.py) for every agent in the pipeline.
    """
    try:
        from agents.adk.agents.instructions import TYPOGRAPHY_RULE

        return TYPOGRAPHY_RULE
    except Exception:  # pragma: no cover - only when google-adk is missing
        return (
            "\nTYPOGRAPHY: never write an em dash (U+2014) or a horizontal bar (U+2015) in any "
            "text, not even in a source string; the house separator is a hyphen with a space on "
            'each side ("Opsi A - DCF FCFF").'
        )


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
            ) + _typography_rule(),
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
