"""
yfinance fallback — scripts/yfinance_fallback.py
Locked plan §4: yfinance .JK is fallback when IDX primary is thin / stale.
Cache 4h, disclose source per exhibit, rate-limit, tiny fundamentals.

Env:
  YFINANCE_CACHE_DIR  default .cache/yfinance
  YFINANCE_TTL_SECONDS default 14400 (4h)

No Sectors hit. Small-cap gaps fall back to IDX + label 'estimated'.
"""
from __future__ import annotations

import json
import os
import time
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

CACHE_DIR = Path(os.getenv("YFINANCE_CACHE_DIR", ".cache/yfinance"))
TTL_SECONDS = int(os.getenv("YFINANCE_TTL_SECONDS", "14400"))
JKT = timezone(timedelta(hours=7))

# polite delay between yfinance calls (seconds)
RATE_LIMIT_SECONDS = float(os.getenv("YFINANCE_RATE_LIMIT", "1.2"))


def _cache_path(ticker: str, kind: str) -> Path:
    safe = ticker.strip().upper().replace("/", "_")
    h = hashlib.sha256(f"{safe}:{kind}".encode()).hexdigest()[:12]
    return CACHE_DIR / f"{safe}__{kind}__{h}.json"


def _read_cache(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        age = time.time() - path.stat().st_mtime
        if age > TTL_SECONDS:
            return None
        return json.loads(path.read_text())
    except Exception:
        return None


def _write_cache(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload["_cached_at"] = datetime.now(JKT).isoformat()
    payload["_ttl_seconds"] = TTL_SECONDS
    path.write_text(json.dumps(payload, default=str, ensure_ascii=False, indent=2))


def _normalize_ticker(ticker: str) -> str:
    t = ticker.strip().upper()
    if not t.endswith(".JK"):
        t = t + ".JK"
    return t


def get_yfinance_prices(ticker: str, period: str = "5y", force_refresh: bool = False) -> dict:
    """
    Returns dict:
      { ticker, yahoo_ticker, period, source: 'yfinance', rows: [...], fetched_at, cache_hit, error? }
    rows: [{time, open, high, low, close, volume}] ASC.
    On network failure returns cached rows if present, else error + empty rows.
    Disclosure: caller must label exhibit source as 'yfinance' (see assumptions json).
    """
    base = ticker.strip().upper().removesuffix(".JK")
    yahoo_ticker = _normalize_ticker(base)
    cache_path = _cache_path(base, f"prices_{period}")
    if not force_refresh:
        cached = _read_cache(cache_path)
        if cached is not None:
            cached["cache_hit"] = True
            return cached

    # rate limit file
    lock = CACHE_DIR / "_last_yf_call_ts"
    try:
        if lock.exists():
            last = float(lock.read_text().strip() or "0")
            wait = RATE_LIMIT_SECONDS - (time.time() - last)
            if wait > 0:
                time.sleep(wait)
    except Exception:
        pass

    try:
        import yfinance as yf  # lazy import
    except ImportError as e:
        return {
            "ticker": base,
            "yahoo_ticker": yahoo_ticker,
            "period": period,
            "source": "yfinance",
            "rows": [],
            "fetched_at": datetime.now(JKT).isoformat(),
            "cache_hit": False,
            "error": f"yfinance not installed: {e}",
        }

    try:
        t = yf.Ticker(yahoo_ticker)
        hist = t.history(period=period, auto_adjust=False)
        # yfinance may return empty for illiquid tickers
        rows = []
        if hist is not None and not hist.empty:
            hist = hist.reset_index()
            # column name is usually 'Date' or 'Datetime'
            date_col = hist.columns[0]
            for _, r in hist.iterrows():
                ts = r[date_col]
                # pandas Timestamp -> iso
                try:
                    iso = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
                except Exception:
                    iso = str(ts)
                rows.append(
                    {
                        "time": iso,
                        "open": float(r.get("Open")) if r.get("Open") == r.get("Open") else None,
                        "high": float(r.get("High")) if r.get("High") == r.get("High") else None,
                        "low": float(r.get("Low")) if r.get("Low") == r.get("Low") else None,
                        "close": float(r.get("Close")) if r.get("Close") == r.get("Close") else None,
                        "volume": float(r.get("Volume")) if r.get("Volume") == r.get("Volume") else None,
                    }
                )
        payload = {
            "ticker": base,
            "yahoo_ticker": yahoo_ticker,
            "period": period,
            "source": "yfinance",
            "rows": rows,
            "row_count": len(rows),
            "fetched_at": datetime.now(JKT).isoformat(),
            "cache_hit": False,
        }
        if rows:
            _write_cache(cache_path, payload)
        # update rate-limit marker
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            lock.write_text(str(time.time()))
        except Exception:
            pass
        return payload
    except Exception as e:
        # on failure, try stale cache
        stale = None
        if cache_path.exists():
            try:
                stale = json.loads(cache_path.read_text())
                stale["cache_hit"] = True
                stale["stale"] = True
                stale["error"] = str(e)
                return stale
            except Exception:
                pass
        return {
            "ticker": base,
            "yahoo_ticker": yahoo_ticker,
            "period": period,
            "source": "yfinance",
            "rows": [],
            "row_count": 0,
            "fetched_at": datetime.now(JKT).isoformat(),
            "cache_hit": False,
            "error": str(e),
        }


def get_yfinance_fundamentals(ticker: str, force_refresh: bool = False) -> dict:
    """
    Thin fundamentals via yfinance (small caps often empty — caller must gap-fill from IDX).
    Returns {ticker, yahoo_ticker, source:'yfinance', financials, balance_sheet, cashflow, info_subset, fetched_at, warnings}
    financials/balance_sheet/cashflow are dicts of {metric: {period: value}} or {} if unavailable.
    Disclosure: label 'estimated' when yfinance gap-filled from IDX.
    """
    base = ticker.strip().upper().removesuffix(".JK")
    yahoo_ticker = _normalize_ticker(base)
    cache_path = _cache_path(base, "fundamentals")
    if not force_refresh:
        cached = _read_cache(cache_path)
        if cached is not None:
            cached["cache_hit"] = True
            return cached

    try:
        import yfinance as yf
    except ImportError as e:
        return {
            "ticker": base,
            "yahoo_ticker": yahoo_ticker,
            "source": "yfinance",
            "financials": {},
            "balance_sheet": {},
            "cashflow": {},
            "info_subset": {},
            "fetched_at": datetime.now(JKT).isoformat(),
            "cache_hit": False,
            "error": str(e),
            "warnings": ["yfinance not installed"],
        }

    # rate limit
    lock = CACHE_DIR / "_last_yf_call_ts"
    try:
        if lock.exists():
            last = float(lock.read_text().strip() or "0")
            wait = RATE_LIMIT_SECONDS - (time.time() - last)
            if wait > 0:
                time.sleep(wait)
    except Exception:
        pass

    warnings: list[str] = []
    financials: dict = {}
    balance_sheet: dict = {}
    cashflow: dict = {}
    info_subset: dict = {}

    try:
        t = yf.Ticker(yahoo_ticker)
        # financials etc are DataFrames with metrics as index, columns as dates
        def df_to_dict(df) -> dict:
            if df is None or getattr(df, "empty", True):
                return {}
            try:
                # transpose to {metric: {date: value}}
                d = {}
                for idx in df.index:
                    row = {}
                    for col in df.columns:
                        v = df.loc[idx, col]
                        # NaN -> None
                        if v != v:  # NaN check
                            continue
                        try:
                            row[str(col)[:10]] = float(v)
                        except Exception:
                            row[str(col)[:10]] = str(v)
                    if row:
                        d[str(idx)] = row
                return d
            except Exception:
                return {}

        try:
            financials = df_to_dict(getattr(t, "financials", None))
        except Exception as e:
            warnings.append(f"financials: {e}")
        try:
            balance_sheet = df_to_dict(getattr(t, "balance_sheet", None))
        except Exception as e:
            warnings.append(f"balance_sheet: {e}")
        try:
            cashflow = df_to_dict(getattr(t, "cashflow", None))
        except Exception as e:
            warnings.append(f"cashflow: {e}")
        try:
            info = getattr(t, "info", None) or {}
            # keep small subset to avoid huge cache
            for k in ["longName", "sector", "industry", "marketCap", "sharesOutstanding", "trailingPE", "priceToBook", "dividendYield"]:
                if k in info:
                    info_subset[k] = info[k]
        except Exception as e:
            warnings.append(f"info: {e}")

        if not financials and not balance_sheet and not cashflow:
            warnings.append("yfinance fundamentals empty — small-cap gap: fallback to IDX + label estimated")

        payload = {
            "ticker": base,
            "yahoo_ticker": yahoo_ticker,
            "source": "yfinance",
            "financials": financials,
            "balance_sheet": balance_sheet,
            "cashflow": cashflow,
            "info_subset": info_subset,
            "fetched_at": datetime.now(JKT).isoformat(),
            "cache_hit": False,
            "warnings": warnings,
        }
        _write_cache(cache_path, payload)
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            lock.write_text(str(time.time()))
        except Exception:
            pass
        return payload
    except Exception as e:
        return {
            "ticker": base,
            "yahoo_ticker": yahoo_ticker,
            "source": "yfinance",
            "financials": {},
            "balance_sheet": {},
            "cashflow": {},
            "info_subset": {},
            "fetched_at": datetime.now(JKT).isoformat(),
            "cache_hit": False,
            "error": str(e),
            "warnings": warnings + [str(e)],
        }


# ---- gap table helper ----
YFINANCE_GAPS = {
    "note": "yfinance IDX small-cap coverage is thin (financials/balance often empty). Use IDX stock_data as primary; yfinance only as fallback with disclosed source.",
    "by_ticker": {
         "RATU": "thin — IPO 2025, yfinance history short; rely IDX",
         "CDIA": "thin — 2025 listing, yfinance sparse; rely IDX",
         "MTEL": "moderate — yfinance has prices but fundamentals patchy",
         "BBCA": "good — large cap, yfinance complete",
         "ADRO": "moderate — yfinance ok, cross-check IDX foreign flow",
    },
}


def gap_summary() -> dict:
    return YFINANCE_GAPS


if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "BBCA"
    print(json.dumps(get_yfinance_prices(ticker, period="5d"), indent=2, ensure_ascii=False))
    print("--- fundamentals ---")
    print(json.dumps(get_yfinance_fundamentals(ticker), indent=2, ensure_ascii=False))
