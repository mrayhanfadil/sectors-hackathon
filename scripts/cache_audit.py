#!/usr/bin/env python
"""Audit + pin the Sectors credit cache for one ticker. Zero credits, ever.

Why this exists (15 Sep 2026, credit-thin mode): every endpoint call costs a
credit, and the only way to know whether the next run will pay is to compare the
calls it *will* make against the rows already in `sectors_cache`. This tool
recovers that call set from the ticker's own run history instead of guessing:

1. read the newest run's event log for the ticker,
2. replay the recorded tool calls against `server.sectors` with `_get` stubbed
   out, capturing the exact (endpoint, params) each wrapper would request,
3. look each key up in the cache and report fresh / expired / missing.

`--pin` extends `expires_at` on the rows it can see (free — an UPDATE, not a
fetch). `--clean-junk` drops rows left behind by test fixtures with fake tickers.

Usage:
    python scripts/cache_audit.py --ticker AMMN
    python scripts/cache_audit.py --ticker AMMN --pin 90 --clean-junk
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from server import sectors as S  # noqa: E402
from server.storage import SectorsCache  # noqa: E402

DB = ROOT / "data" / "agent_runs.db"
JUNK_RE = re.compile(r"/(DT|OTH|LOCK)[0-9A-F]{4,}/")


def calls_from_run_history(ticker: str) -> list[tuple[str, str, dict]]:
    """Recover (tool, endpoint, params) from the newest run that used the ticker.

    `_get` is stubbed so the wrappers only build their request; nothing is sent.
    """
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    row = con.execute(
        "select run_id from agent_runs where upper(ticker)=? order by started_at desc limit 1",
        (ticker.upper(),),
    ).fetchone()
    if not row:
        raise SystemExit(f"no run found for {ticker} — run the pipeline once, then audit")
    run_id = row[0]

    recorded: list[tuple[str, dict]] = []
    for (pj,) in con.execute(
        "select payload_json from agent_events where run_id=? order by seq", (run_id,)
    ):
        try:
            ev = json.loads(pj)
        except json.JSONDecodeError:
            continue
        for fc in ev.get("function_calls") or []:
            name, args = fc.get("name") or "", fc.get("args") or {}
            if name.startswith("sectors_"):
                recorded.append((name, args))

    real_get = S._get
    captured: list[tuple[str, str, dict]] = []
    raw: list[tuple[str, dict]] = []
    try:
        def stub(path, params=None, allow_window_substitute=False):  # noqa: ANN001
            raw.append((path, params or {}))
            return {"_dry_run": True}

        S._get = stub
        # The agent tools name their arg `ticker`; the wrappers take `symbol`.
        # Without this alias every call dies on TypeError and the audit silently
        # audits one endpoint instead of all of them.
        aliases = {"ticker": "symbol"}
        skipped: list[str] = []
        for tool, args in recorded:
            fn = getattr(S, tool[len("sectors_"):], None)
            if fn is None:
                skipped.append(f"{tool} (no wrapper)")
                continue
            kwargs = {aliases.get(k, k): v for k, v in args.items()}
            before = len(raw)
            try:
                fn(**kwargs)
            except TypeError as e:
                skipped.append(f"{tool} ({e})")
                continue
            if len(raw) > before:
                path, params = raw[-1]
                entry = (tool, path, params)
                if entry not in captured:
                    captured.append(entry)  # dedupe: same tool twice == one row
        if skipped:
            print("WARNING: could not replay: " + "; ".join(skipped), file=sys.stderr)
    finally:
        S._get = real_get
    return captured


def key_for(endpoint: str, params: dict) -> str:
    return SectorsCache._key(endpoint, params)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--pin", type=int, default=0, metavar="DAYS",
                    help="extend expires_at this many days for every row in scope")
    ap.add_argument("--clean-junk", action="store_true",
                    help="delete cache rows left by fake-ticker test fixtures")
    a = ap.parse_args()
    ticker = a.ticker.upper()

    con = sqlite3.connect(DB)
    now = time.time()

    if a.clean_junk:
        rows = con.execute("select cache_key, endpoint from sectors_cache").fetchall()
        junk = [(k, e) for k, e in rows if JUNK_RE.search(e)]
        if junk:
            con.executemany("delete from sectors_cache where cache_key=?", [(k,) for k, _ in junk])
            con.commit()
        print(f"clean-junk: removed {len(junk)} fake-ticker rows")

    calls = calls_from_run_history(ticker)
    print(f"\n{ticker}: {len(calls)} Sectors calls recovered from run history\n")
    print(f"{'tool':26s} {'state':9s} {'age_h':>7s} {'ttl_h':>6s} {'bytes':>8s}")
    print("-" * 62)

    in_scope: set[str] = set()
    missing: list[tuple[str, str, dict]] = []
    for tool, endpoint, params in calls:
        k = key_for(endpoint, params)
        in_scope.add(k)
        r = con.execute(
            "select fetched_at, expires_at, length(payload_json) from sectors_cache where cache_key=?",
            (k,),
        ).fetchone()
        if not r:
            print(f"{tool:26s} {'MISSING':9s} {'-':>7s} {'-':>6s} {'-':>8s}")
            missing.append((tool, endpoint, params))
            continue
        fetched, expires, n = r
        age = (now - fetched) / 3600
        ttl = (expires - fetched) / 3600
        # An aged row is still a HIT unless SECTORS_STALE_OK=0 — say so, or the
        # audit reports a pending charge that the next run will never make.
        state = "aged*" if expires < now else "fresh"
        print(f"{tool:26s} {state:9s} {age:7.1f} {ttl:6.1f} {n:8d}")

    if a.pin:
        until = now + a.pin * 86400
        targets = set(in_scope)
        targets |= {
            k for (k,) in con.execute(
                "select cache_key from sectors_cache where endpoint like ?", (f"%{ticker}%",)
            )
        }
        rows = con.execute(
            f"select cache_key, expires_at from sectors_cache where cache_key in ({','.join('?' * len(targets))})",
            tuple(targets),
        ).fetchall()
        stale_rows = [(k, e) for k, e in rows if e < until]
        con.executemany("update sectors_cache set expires_at=? where cache_key=?",
                        [(until, k) for k, _ in stale_rows])
        con.commit()
        print(f"\npin: extended {len(stale_rows)} rows to now+{a.pin}d "
              f"({len(targets)} in scope: the run's calls + every {ticker} row)")
        # re-read so the verdict below reflects the pin
        missing = []
        for tool, endpoint, params in calls:
            r = con.execute(
                "select expires_at from sectors_cache where cache_key=?",
                (key_for(endpoint, params),),
            ).fetchone()
            if not r:
                missing.append((tool, endpoint, params))

    print()
    if missing:
        print(f"VERDICT: {len(calls) - len(missing)}/{len(calls)} calls serve from cache; "
              f"{len(missing)} have NO row and would BILL on the next run:")
        for tool, endpoint, params in missing:
            print(f"  {tool}: {endpoint} {json.dumps(params, sort_keys=True)}")
        print("\nDo NOT fetch blindly with thin credit — decide per endpoint whether the data is worth the credit.")
        return 1
    print(f"VERDICT: all {len(calls)} calls serve from cache — the next {ticker} run costs 0 credits.")
    print("aged* rows are HITS too: SECTORS_STALE_OK defaults to 1, so only a MISSING key can bill.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
