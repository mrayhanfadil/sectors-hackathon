import asyncio
import os
import polars as pl
import yfinance as yf
import requests
import re
import time
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Config
DB_URL = "postgresql+asyncpg://postgres:password@localhost:15437/stockdata"
CAMOUFOX_URL = "http://127.0.0.1:9377"
USER_ID = "fadil"

GLOBAL_SYMBOLS = {
    "Dow Jones": "^DJI", "Nasdaq": "^IXIC", "S&P 500": "^GSPC",
    "FTSE 100": "^FTSE", "Dax Index": "^GDAXI", "CAC 40": "^FCHI",
    "Nikkei 225": "^N225", "Hang Seng": "^HSI", "Shanghai": "000001.SS",
    "LQ45": "^JKLQ45",
    "Oil (WTI)": "CL=F", "Oil (Brent)": "BZ=F", "Gold Spot": "GC=F",
    "Silver": "SI=F", "Copper": "HG=F", "Ntrl Gas": "NG=F",
    "US 10Yr": "^TNX", "USD/IDR": "IDR=X",
    "VIX Index": "^VIX", "Euro/USD": "EURUSD=X"
}

INVESTING_PATHS = {
    "IDX Comp": "indices/idx-composite",
    "LQ45 Index": "indices/jakarta-lq45",
    "Indo 10Y": "rates-bonds/indonesia-10-year-bond-yield",
    "Energy": "indices/indonesia-se-energy",
    "Basic Mat": "indices/indonesia-se-basic-materials",
    "Industrials": "indices/indonesia-se-industrials",
    "Non-Cyclic": "indices/indonesia-se-consumer-non-cyclicals",
    "Healthcare": "indices/indonesia-se-healthcare",
    "Cyclicals": "indices/indonesia-se-consumer-cyclicals",
    "Technology": "indices/indonesia-se-technology",
    "Transport": "indices/indonesia-se-transportation",
    "Infra": "indices/indonesia-se-infrastructure",
    "Financials": "indices/indonesia-se-financials",
    "Properties": "indices/indonesia-se-properties"
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
    match = re.search(r'([\\d,]{3,}\.\d{2})\s*([+\-]?\d+\.\d{2})\s*([+\-]?\d+\.\d{2})%', snapshot)
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
    try:
        engine = create_async_engine(DB_URL)
        query = """
            SELECT s.kode_saham, s.penutupan::float as close, s.sebelumnya::float as prev, 
                   (s.volume::float * s.penutupan::float) as turnover, t.sector
            FROM stock_data s 
            JOIN tickers t ON s.kode_saham = t.kode_saham
            WHERE s.time = (SELECT MAX(time) FROM stock_data)
            ORDER BY turnover DESC
        """
        async with engine.connect() as conn:
            result = await conn.execute(text(query))
            rows = result.fetchall()
        await engine.dispose()
        return rows
    except: return []

def fetch_yfinance_data():
    results = {}
    tickers = yf.Tickers(" ".join(GLOBAL_SYMBOLS.values()))
    for name, sym in GLOBAL_SYMBOLS.items():
        try:
            hist = tickers.tickers[sym].history(period="5d")
            if not hist.empty and len(hist) >= 2:
                curr = hist.iloc[-1]['Close']
                prev = hist.iloc[-2]['Close']
                results[name] = {"val": curr, "chg": curr-prev, "pct": (curr-prev)/prev*100}
        except: pass
    return results

async def main():
    print("Beautifying and gathering data...")
    sem = asyncio.Semaphore(2)
    
    investing_tasks = {name: get_investing_quote(path, sem) for name, path in INVESTING_PATHS.items()}
    names = list(investing_tasks.keys())
    results = await asyncio.gather(*investing_tasks.values())
    investing_data = {n: (r if r else {"val": 0, "chg": 0, "pct": 0}) for n, r in zip(names, results)}
    
    market_task = asyncio.to_thread(fetch_yfinance_data)
    jisdor_task = get_jisdor(sem)
    db_task = get_db_data()
    
    market, jisdor, db_rows = await asyncio.gather(market_task, jisdor_task, db_task)
    
    # Calculate fallback sectors
    df = pl.DataFrame(db_rows, schema=["kode", "close", "prev", "turnover", "sector"], orient="row")
    df = df.with_columns(((pl.col("close") - pl.col("prev")) / pl.col("prev") * 100).alias("pct_change"))
    db_sectors = df.group_by("sector").agg([pl.col("pct_change").mean().alias("avg_perf")])
    db_sectors_dict = {row[0]: row[1] for row in db_sectors.iter_rows() if row[0]}

    date_str = datetime.now().strftime('%B %d, %Y')
    
    # BEAUTIFIED FORMAT
    brief =  "══════════════════════════════════════════════════════════════════════\n"
    brief += f" 📈 IDX MORNING BRIEFING | {date_str.upper()}\n"
    brief += "══════════════════════════════════════════════════════════════════════\n\n"
    
    brief += "── GLOBAL MARKET INDICES ─────────────────────────────────────────────\n"
    for n in ["Dow Jones", "Nasdaq", "S&P 500", "FTSE 100", "Dax Index", "CAC 40", "Nikkei 225", "Hang Seng", "Shanghai"]:
        d = market.get(n, {"val":0, "chg":0, "pct":0})
        brief += format_line(n, d['val'], d['chg'], d['pct']) + "\n"
    
    brief += "\n── INDONESIA BENCHMARKS ──────────────────────────────────────────────\n"
    idx_val = investing_data["IDX Comp"] if investing_data["IDX Comp"]["val"] > 0 else market.get("IDX Comp", {"val":0, "chg":0, "pct":0})
    lq45_val = investing_data["LQ45 Index"] if investing_data["LQ45 Index"]["val"] > 0 else market.get("LQ45 Index", {"val":0, "chg":0, "pct":0})
    brief += format_line("IDX Composite", idx_val['val'], idx_val['chg'], idx_val['pct']) + "\n"
    brief += format_line("LQ45 Index", lq45_val['val'], lq45_val['chg'], lq45_val['pct']) + "\n"
    
    brief += "\n── IDX SECTORAL PERFORMANCE ──────────────────────────────────────────\n"
    sector_list = [
        ("Energy", "Energy"), ("Basic Mat", "Basic Materials"), ("Industrials", "Industrials"),
        ("Non-Cyclic", "Consumer Non-Cy"), ("Healthcare", "Healthcare"), ("Cyclicals", "Consumer Cyclic"),
        ("Technology", "Technology"), ("Transport", "Transportation"), ("Infra", "Infrastructures"),
        ("Financials", "Financials"), ("Properties", "Properties & Re")
    ]
    
    sectors_data = []
    for s_id, s_display in sector_list:
        d = investing_data.get(s_id)
        if d and d['val'] > 0:
            sectors_data.append((s_display, d['pct'], False))
        else:
            db_val = db_sectors_dict.get(s_display, 0)
            sectors_data.append((s_display, db_val, True))
    
    sectors_data.sort(key=lambda x: x[1], reverse=True)
    for s_name, pct, is_est in sectors_data:
        mark = "‼️" if is_est else ""
        brief += f"{s_name:<20} .. {pct:>+10.2f}% {get_emoji(pct)} {mark}\n"
            
    brief += "\n── MACRO, BONDS & FOREX ──────────────────────────────────────────────\n"
    i10y = investing_data["Indo 10Y"]
    brief += format_line("Indo 10Y Bond", i10y['val'], i10y['chg'], i10y['pct'], decimals=4, suffix=" ❗️") + "\n"
    u10y = market.get("US 10Yr", {"val":0, "chg":0, "pct":0})
    brief += format_line("US 10Yr Yield", u10y['val'], u10y['chg'], u10y['pct']) + "\n"
    vix = market.get("VIX Index", {"val":0, "chg":0, "pct":0})
    brief += format_line("VIX Volatility", vix['val'], vix['chg'], vix['pct'], suffix=" ‼️") + "\n"
    
    usdidr = market.get("USD/IDR", {"val":0, "chg":0, "pct":0})
    brief += format_line("USD/IDR Spot", usdidr['val'], usdidr['chg'], usdidr['pct'], suffix=" ‼️") + "\n"
    brief += f"{'JISDOR (BI)':<14} .. {jisdor['val']:>11,.0f} {'':>9} {'':>9} ‼️\n"
        
    brief += "\n── COMMODITIES ───────────────────────────────────────────────────────\n"
    for n in ["Oil (WTI)", "Oil (Brent)", "Gold Spot", "Silver", "Copper", "Ntrl Gas"]:
        d = market.get(n, {"val":0, "chg":0, "pct":0})
        brief += format_line(n, d['val'], d['chg'], d['pct']) + "\n"
    
    brief += "\n── TOP TURNOVER (IDX) ────────────────────────────────────────────────\n"
    for row in df.sort("turnover", descending=True).head(5).iter_rows():
        # row: kode, close, prev, turnover, sector, pct_change
        brief += f"{row[0]:<14} .. {row[1]:>11,.0f} {row[5]:>+9.2f}% {get_emoji(row[5])}\n"

    brief += "\n══════════════════════════════════════════════════════════════════════\n"
    brief += " SOURCE: PHINTRACO-ALIGNED BENCHMARK (INVESTING.COM + BI + IDX DB)\n"
    brief += "══════════════════════════════════════════════════════════════════════"

    print(brief)

if __name__ == "__main__":
    asyncio.run(main())
