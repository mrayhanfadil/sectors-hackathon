"""IDX Morning Brief data layer - Sectors-backed (rewritten Lane E, legacy removed).

Was: Postgres `stockdata:15437` reader. Now: Sectors v2 universe feed
(`transaction/close/{date}`) mapped to the same polars schema so downstream
formatters keep working. Keyless -> SectorsNotConfigured (loud, no fallback).
"""
import asyncio
from datetime import date, timedelta

import polars as pl

# Kept for CLI compat: latest trading snapshot is derived from the Sectors
# universe feed, not a local DB (legacy removed).


async def get_latest_idx_data() -> pl.DataFrame:
    """Universe snapshot for the latest trading day via Sectors.

    Returns polars DataFrame [kode, close, prev, vol, val, sector, pct_change, turnover].
    Raises SectorsNotConfigured when keyless - callers must fail loud.
    """
    from server.sectors import universe_close

    day = date.today()
    raw = None
    last_error: Exception | None = None
    for _ in range(5):  # walk back over weekends/holidays
        try:
            raw = await asyncio.to_thread(universe_close, day.isoformat())
            break
        except Exception as e:
            last_error = e
            if "SectorsNotConfigured" in type(e).__name__:
                raise
            day -= timedelta(days=1)
    if raw is None:
        raise RuntimeError(f"sectors universe feed unavailable: {last_error}")

    rows = raw.get("data") or raw.get("results") or []
    recs = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        kode = str(r.get("kode") or r.get("symbol") or r.get("ticker") or "").upper()
        if not kode:
            continue
        try:
            close = float(r.get("close") or r.get("closing_price") or 0)
        except (TypeError, ValueError):
            close = 0.0
        try:
            prev = float(r.get("prev") or r.get("previous_close") or r.get("prev_close") or close)
        except (TypeError, ValueError):
            prev = close
        try:
            vol = float(r.get("vol") or r.get("volume") or 0)
        except (TypeError, ValueError):
            vol = 0.0
        try:
            val = float(r.get("val") or r.get("value") or r.get("turnover") or 0)
        except (TypeError, ValueError):
            val = 0.0
        recs.append({
            "kode": kode,
            "close": close,
            "prev": prev,
            "vol": vol,
            "val": val,
            "sector": r.get("sector"),
        })

    df = pl.DataFrame(
        recs,
        schema=["kode", "close", "prev", "vol", "val", "sector"],
        orient="row",
    )

    # Calculate performance safely
    df = df.with_columns(
        ((pl.col("close") - pl.col("prev")) / pl.col("prev") * 100).fill_nan(0).fill_null(0).alias("pct_change"),
        (pl.col("close") * pl.col("vol")).fill_null(0).alias("turnover"),
    )
    return df


def generate_institutional_brief(df):
    from datetime import datetime
    brief = f"Good morning, {datetime.now().strftime('%B %d, %Y')}\n\n"
    brief += "Market Summary (Sectors universe feed):\n\n"

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
