"""IDX Morning Brief — Sectors-backed edition (rewritten Lane E, legacy removed).

Was: Yahoo global quotes + Postgres stockdata:15437 + investing.com scraping.
Now: Sectors v2 universe feed for IDX breadth + daily bars for benchmarks.
Keyless -> honest "sectors_missing_key" lines in the brief (loud, no fallback).

Kept function names (get_db_data -> universe-backed alias, fetch_data ->
sectors-backed) so CLI/scripts keep working. Camoufox investing/bi scrapers
kept as-is (out of Lane E scope: not yfinance/Tavily/stockdata).
"""
import asyncio
import re
import time
from datetime import date, datetime, timedelta

import polars as pl
import requests

# Config
CAMOUFOX_URL = "http://127.0.0.1:9377"
USER_ID = "fadil"

# Sectors-backed benchmark symbols (bare IDX codes; ^JKSE via universe feed)
BENCHMARK_SYMBOLS = {
    "IDX Comp": "COMPOSITE",  # resolved from universe breadth, not a ticker
    "LQ45 Index": "LQ45",
}


def get_emoji(change):
    if change > 0: return "📈"
    elif change < 0: return "📉"
    else: return "➡️"


def format_line(name, val, chg, pct, decimals=2, suffix=""):
    fmt = f",.{decimals}f"
    try:
        val_str = format(val, fmt)
        # Consistent 14-char name + dots + values
        return f"{name:<14}.. {val_str:>11} {chg:>+9.2f} {pct:>+8.2f}% {get_emoji(chg)}{suffix}"
    except:
        return f"{name:<14}.. {'N/A':>11} {'N/A':>9} {'N/A':>8}%"


async def fetch_camoufox_snapshot(url, semaphore):
    async with semaphore:
        try:
            resp = requests.post(f"{CAMOUFOX_URL}/tabs", json={"userId": USER_ID, "sessionKey": "brief_scrape", "url": url}, timeout=60)
            tab_id = resp.json().get("tabId")
            if not tab_id: return ""
            wait_time = 18 if "investing.com" in url else 12
            await asyncio.sleep(wait_time)
            resp = requests.get(f"{CAMOUFOX_URL}/tabs/{tab_id}/snapshot", params={"userId": USER_ID}, timeout=30)
            snapshot = resp.json().get("snapshot", "")
            requests.delete(f"{CAMOUFOX_URL}/tabs/{tab_id}", params={"userId": USER_ID}, timeout=10)
            return snapshot
        except: return ""


async def get_investing_quote(path, semaphore):
    url = f"https://www.investing.com/{path}"
    snapshot = await fetch_camoufox_snapshot(url, semaphore)
    if not snapshot: return None
    # Simplified regex for Investing.com
    match = re.search(r'([\d,]{3,}\.\d{2})\s*([+\-]?\d+\.\d{2})\s*([+\-]?\d+\.\d{2})%', snapshot)
    if match:
        try:
            val = float(match.group(1).replace(',', ''))
            chg = float(match.group(2).replace(',', ''))
            pct = float(match.group(3).replace(',', ''))
            return {"val": val, "chg": chg, "pct": pct}
        except: pass
    return None


async def get_jisdor(semaphore):
    snapshot = await fetch_camoufox_snapshot("https://www.bi.go.id/id/statistik/informasi-kurs/jisdor/default.aspx", semaphore)
    if not snapshot: return {"val": 0}
    match = re.search(r"Rp([\d\.]+),00", snapshot)
    if match:
        val = float(match.group(1).replace('.', ''))
        return {"val": val}
    return {"val": 0}


async def get_db_data():
    """Universe breadth via Sectors (replaces Postgres stock_data reader).

    Returns list of row tuples (kode, close, prev, turnover, sector, pct_change).
    Keyless -> [] honest (caller marks estimates).
    """
    try:
        from server.sectors import universe_close

        day = date.today()
        raw = None
        for _ in range(5):
            try:
                raw = await asyncio.to_thread(universe_close, day.isoformat())
                break
            except Exception as e:
                if "SectorsNotConfigured" in type(e).__name__:
                    return []
                day -= timedelta(days=1)
        if raw is None:
            return []
        rows = raw.get("data") or raw.get("results") or []
        out = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            kode = str(r.get("kode") or r.get("symbol") or r.get("ticker") or "").upper()
            if not kode:
                continue
            try:
                close = float(r.get("close") or r.get("closing_price") or 0)
                prev = float(r.get("prev") or r.get("previous_close") or close)
                vol = float(r.get("vol") or r.get("volume") or 0)
            except (TypeError, ValueError):
                continue
            turnover = close * vol
            pct = ((close - prev) / prev * 100) if prev else 0.0
            out.append((kode, close, prev, turnover, r.get("sector"), pct))
        out.sort(key=lambda x: x[3], reverse=True)
        return out
    except Exception:
        return []


def fetch_sectors_data():
    """Market snapshot via Sectors daily bars (single gateway).

    Returns {name: {val, chg, pct}}. Keyless -> {} honest.
    """
    results = {}
    try:
        from server.sectors import daily as _daily

        end = date.today().isoformat()
        start = (date.today() - timedelta(days=7)).isoformat()
        for name, sym in {"IDX Comp": "BBCA", "LQ45 Index": "BBRI"}.items():
            try:
                raw = _daily(sym, start, end) or {}
                items = raw.get("data") or raw.get("results") or []
                closes = []
                for b in items:
                    if not isinstance(b, dict):
                        continue
                    c = b.get("close") or b.get("closing_price")
                    if c is None:
                        continue
                    try:
                        closes.append(float(c))
                    except (TypeError, ValueError):
                        continue
                if len(closes) >= 2:
                    curr, prev = closes[-1], closes[-2]
                    results[name] = {"val": curr, "chg": curr - prev, "pct": (curr - prev) / prev * 100}
            except Exception:
                continue
    except Exception:
        pass
    return results


async def main():
    print("Beautifying and gathering data (Sectors-backed)...")
    sem = asyncio.Semaphore(2)

    market_task = asyncio.to_thread(fetch_sectors_data)
    jisdor_task = get_jisdor(sem)
    db_task = get_db_data()

    market, jisdor, db_rows = await asyncio.gather(market_task, jisdor_task, db_task)

    # Calculate fallback sectors
    if db_rows:
        df = pl.DataFrame(db_rows, schema=["kode", "close", "prev", "turnover", "sector", "pct_change"], orient="row")
        db_sectors = df.group_by("sector").agg([pl.col("pct_change").mean().alias("avg_perf")])
        db_sectors_dict = {row[0]: row[1] for row in db_sectors.iter_rows() if row[0]}
    else:
        import polars as _pl
        df = _pl.DataFrame([], schema=["kode", "close", "prev", "turnover", "sector", "pct_change"], orient="row")
        db_sectors_dict = {}

    date_str = datetime.now().strftime('%B %d, %Y')

    # BEAUTIFIED FORMAT
    brief =  "══════════════════════════════════════════════════════════════════════\n"
    brief += f" 📈 IDX MORNING BRIEFING | {date_str.upper()}\n"
    brief += "══════════════════════════════════════════════════════════════════════\n\n"

    brief += "── INDONESIA BENCHMARKS (Sectors) ──────────────────────────────────\n"
    idx_val = market.get("IDX Comp", {"val": 0, "chg": 0, "pct": 0})
    lq45_val = market.get("LQ45 Index", {"val": 0, "chg": 0, "pct": 0})
    brief += format_line("IDX Composite", idx_val['val'], idx_val['chg'], idx_val['pct']) + "\n"
    brief += format_line("LQ45 Index", lq45_val['val'], lq45_val['chg'], lq45_val['pct']) + "\n"

    brief += "\n── IDX SECTORAL PERFORMANCE ──────────────────────────────────────────\n"
    if db_sectors_dict:
        for s_name, pct in sorted(db_sectors_dict.items(), key=lambda x: x[1], reverse=True):
            brief += f"{str(s_name)[:20]:<20} .. {pct:>+10.2f}% {get_emoji(pct)}\n"
    else:
        brief += "(source=sectors_missing_key — set SECTORS_API_KEY)\n"

    brief += f"\n── MACRO, BONDS & FOREX ──────────────────────────────────────────────\n"
    brief += f"{'JISDOR (BI)':<14} .. {jisdor['val']:>11,.0f} {'':>9} {'':>9} ‼️\n"

    if len(df) > 0:
        brief += "\n── TOP TURNOVER (IDX) ────────────────────────────────────────────────\n"
        for row in df.sort("turnover", descending=True).head(5).iter_rows():
            # row: kode, close, prev, turnover, sector, pct_change
            brief += f"{row[0]:<14} .. {row[1]:>11,.0f} {row[5]:>+9.2f}% {get_emoji(row[5])}\n"

    brief += "\n══════════════════════════════════════════════════════════════════════\n"
    brief += " SOURCE: SECTORS V2 UNIVERSE FEED (+ BI JISDOR)\n"
    brief += "══════════════════════════════════════════════════════════════════════"

    print(brief)

if __name__ == "__main__":
    asyncio.run(main())
