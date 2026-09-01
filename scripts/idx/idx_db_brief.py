import asyncio
import os
import polars as pl
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://postgres:password@localhost:15437/stockdata"

async def get_latest_idx_data():
    engine = create_async_engine(DB_URL)
    query = """
    SELECT s.kode_saham, s.penutupan::float, s.sebelumnya::float, s.volume::float, s.nilai::float, t.sector
    FROM stock_data s
    JOIN tickers t ON s.kode_saham = t.kode_saham
    WHERE s.time = (SELECT MAX(time) FROM stock_data)
    """
    async with engine.connect() as conn:
        result = await conn.execute(text(query))
        rows = result.fetchall()
    await engine.dispose()
    
    # Force float conversion here
    df = pl.DataFrame(rows, schema=["kode", "close", "prev", "vol", "val", "sector"], orient="row")
    
    # Calculate performance safely
    df = df.with_columns(
        ((pl.col("close") - pl.col("prev")) / pl.col("prev") * 100).fill_nan(0).fill_null(0).alias("pct_change"),
        (pl.col("close") * pl.col("vol")).fill_null(0).alias("turnover")
    )
    return df

def generate_institutional_brief(df):
    brief = f"Good morning, {datetime.now().strftime('%B %d, %Y')}\n\n"
    brief += "Market Summary (Official IDX Data):\n\n"
    
    brief += "--- SECTORAL PERFORMANCE ---\n"
    sectors = df.filter(pl.col("sector").is_not_null()).group_by("sector").agg([
        pl.col("pct_change").mean().alias("avg_perf")
    ]).sort("avg_perf", descending=True)
    
    for row in sectors.iter_rows():
        brief += f"{row[0][:15]:<15}: {row[1]:>+7.2f}%\n"
        
    brief += "\n--- TOP TURNOVER ---\n"
    movers = df.sort("turnover", descending=True).head(5)
    for row in movers.iter_rows():
        brief += f"{row[0]:<10}: {row[1]:,.0f} (Vol: {row[3]:,.0f}) ({row[6]:>+6.2f}%)\n"
    return brief

async def main():
    df = await get_latest_idx_data()
    print(generate_institutional_brief(df))

if __name__ == "__main__":
    asyncio.run(main())
