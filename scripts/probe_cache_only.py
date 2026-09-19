#!/usr/bin/env python3
"""Prove whether a ticker can be served from the disk cache at ZERO credits.

Why this exists: "the cache is cold, refreshing will burn credits" is a claim to
test, never to hand the user. Several policy gates (an offline short-circuit, a
freeze mtime TTL) refuse to serve data that is sitting on disk, and from the
outside they all look exactly like a cold cache.

How it proves it: `httpx.Client` is replaced with a constructor that raises, and
`SECTORS_CACHE_ONLY=1` is set. If `collect()` still returns a payload, every byte
came off the disk - a credit could not have been spent, because no HTTP client
could even be constructed.

It also reports the `sectors_cache` row counts before/after, which must not grow:
a growing count means params drifted between calls and a later live run would bill
for data it already had.

Usage:
    .venv/bin/python scripts/probe_cache_only.py --ticker AMMN
    .venv/bin/python scripts/probe_cache_only.py --ticker AMMN --raw   # payload keys
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _rows(db: Path, ticker: str) -> tuple[int, int, int]:
    """(total, live, forever-ish newest-expiry days left) for a ticker's cache rows."""
    if not db.exists():
        return (0, 0, 0)
    con = sqlite3.connect(str(db))
    try:
        total = con.execute(
            "SELECT COUNT(*) FROM sectors_cache WHERE cache_key LIKE ?", (f"%{ticker}%",)
        ).fetchone()[0]
        live = con.execute(
            "SELECT COUNT(*) FROM sectors_cache WHERE cache_key LIKE ? AND expires_at > ?",
            (f"%{ticker}%", time.time()),
        ).fetchone()[0]
    finally:
        con.close()
    return (total, live, 0)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ticker", required=True, help="bare IDX ticker, e.g. AMMN")
    ap.add_argument("--db", default=str(REPO_ROOT / "data" / "agent_runs.db"), help="sectors_cache SQLite path")
    ap.add_argument("--raw", action="store_true", help="also print the payload's top-level keys")
    args = ap.parse_args()

    ticker = args.ticker.strip().upper().removesuffix(".JK")
    sys.path.insert(0, str(REPO_ROOT))
    os.chdir(REPO_ROOT)

    db = Path(args.db)
    before_total, before_live, _ = _rows(db, ticker)
    print(f"sectors_cache[{ticker}] before: total={before_total} live={before_live}")

    # Cache-or-nothing, and make any upstream attempt a hard failure.
    os.environ["SECTORS_CACHE_ONLY"] = "1"
    os.environ.pop("SECTORS_OFFLINE", None)
    os.environ.setdefault("SECTORS_STALE_OK", "1")

    import httpx

    def _boom(*_a, **_k):  # noqa: ANN002, ANN003
        raise AssertionError("UPSTREAM ATTEMPTED - a credit would have been burned")

    httpx.Client = _boom  # type: ignore[assignment]
    httpx.get = _boom  # type: ignore[assignment]

    from agents.collector import _ticker_fill_payload, collect

    freeze = _ticker_fill_payload(ticker)
    print(f"freeze           : {'present' if freeze else 'none'}"
          + (f" (age {freeze.get('freeze_age_days')} days)" if freeze else ""))

    started = time.time()
    try:
        payload = collect(ticker, use_cache=False)
    except Exception as exc:  # honest failure, not a fabricated payload
        print(f"collect() FAILED  : {type(exc).__name__}: {str(exc)[:300]}")
        after_total, after_live, _ = _rows(db, ticker)
        print(f"sectors_cache[{ticker}] after : total={after_total} live={after_live} (grew by {after_total - before_total})")
        print("=> the cache could NOT serve this ticker; a live pull would be needed.")
        return 1

    elapsed = time.time() - started
    after_total, after_live, _ = _rows(db, ticker)
    prices = payload.get("prices") or []
    fin = payload.get("financials")
    quarters = len((fin or {}).get("quarterly") or []) if isinstance(fin, dict) else 0

    print(f"collect() OK      : {elapsed:.2f}s  0 credits (httpx was trapped)")
    print(f"  source          : {payload.get('source')}")
    print(f"  prices          : {len(prices)} rows  (source: {payload.get('prices_source', '-')})")
    print(f"  financials      : {quarters} quarters  (source: {payload.get('financials_source', '-')})")
    print(f"  sectors_gaps    : {payload.get('sectors_gaps')}")
    print(f"  freeze age days : {payload.get('_freeze_age_days')}")
    if args.raw:
        print(f"  top-level keys  : {sorted(payload.keys())}")
    print(f"sectors_cache[{ticker}] after : total={after_total} live={after_live} (grew by {after_total - before_total})")
    print("=> served from disk. Do NOT tell the user this needs a credit refresh.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
