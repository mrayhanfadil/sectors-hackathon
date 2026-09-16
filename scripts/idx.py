#!/usr/bin/env python3
"""IDX Morning Brief data layer - Sectors-backed CLI (rewritten Lane E).

Standalone CLI for the institutional-grade equity report data pipeline.
Reads from the Sectors v2 universe feed (legacy removed: no Postgres stockdata).
"""
from __future__ import annotations
import argparse
import asyncio
import json
import sys
from pathlib import Path

# Make sibling modules importable when invoked as a script
_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))

from idx.idx_db_brief import get_latest_idx_data, generate_institutional_brief
# idx_brief_scraper / idx_master_brief exist but their internals (fetch_data, get_db_data,
# get_investing_quote, get_jisdor, main) are intertwined with the original cron pipeline.
# We only export `get_latest_idx_data` + `generate_institutional_brief` from the data layer
# and leave the legacy helpers unimported here. Master brief is run by its own CLI in the
# original idx-morning-brief project.


async def cmd_snapshot(ticker: str | None) -> int:
    """Print latest row(s) for one ticker (or all if None) as JSON."""
    df = await get_latest_idx_data()
    if ticker:
        sub = df.filter(df["kode"].str.to_uppercase() == ticker.upper())
        if sub.height == 0:
            print(json.dumps({"ok": False, "error": f"ticker {ticker} not found in latest snapshot", "rows": df.height}, indent=2))
            return 1
        rows = sub.to_dicts()
    else:
        rows = df.head(50).to_dicts()  # cap for human-readable output
    print(json.dumps({"ok": True, "ticker": ticker, "rows": df.height if not ticker else sub.height, "data": rows}, indent=2, default=str))
    return 0


def cmd_brief() -> int:
    """Print the human-readable institutional brief (sector perf + top turnover)."""
    df = asyncio.run(get_latest_idx_data())
    print(generate_institutional_brief(df))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="IDX Morning Brief data layer CLI")
    sub = ap.add_subparsers(dest="cmd_name", required=True)

    p_snap = sub.add_parser("snapshot", help="Latest IDX snapshot (JSON) for a ticker or all")
    p_snap.add_argument("ticker", nargs="?", help="Ticker code (e.g. BBCA); omit for top-50")
    p_snap.set_defaults(func=lambda a: asyncio.run(cmd_snapshot(a.ticker)))

    sub.add_parser("brief", help="Human-readable institutional brief (sectoral + turnover)").set_defaults(func=lambda a: cmd_brief())

    args = ap.parse_args()
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
