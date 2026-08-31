"""
IDX Postgres adapter — server/collector/idx_postgres.py
Locked plan §4: stockdata:15437 is P0-P1 primary (no Sectors credit).

Tables (TimescaleDB hypertables):
  stock_data(time, kode_saham, open_price, tertinggi, terendah, penutupan,
             volume, nilai, foreign_buy/sell, listed_shares, sebelumnya, ...)
  tickers(kode_saham, nama_saham, sector, industry)
  corporate_actions(time, kode_saham, action_type, value)

Env:
  DATABASE_URL  default postgresql+asyncpg://postgres:password@localhost:15437/stockdata
  (also accepts DB_URL / postgres:// alias; driver coerced to asyncpg)

Usage:
  from server.collector.idx_postgres import IDXPostgres
  db = IDXPostgres()
  df = await db.get_prices("BBCA", period="5y")
  tickers = await db.get_tickers(sector="Financials")
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import asyncpg

DEFAULT_DB_URL = "postgresql+asyncpg://postgres:password@localhost:15437/stockdata"


def _resolve_db_url(url: Optional[str] = None) -> str:
    raw = url or os.getenv("DATABASE_URL") or os.getenv("DB_URL") or DEFAULT_DB_URL
    # asyncpg URL must be postgresql:// (no +asyncpg, no query)
    raw = raw.replace("postgresql+asyncpg://", "postgresql://")
    # strip asyncpg-unsupported query params if present
    if "?" in raw:
        raw = raw.split("?")[0]
    return raw


PERIOD_RE = re.compile(r"^\s*(\d+)\s*([yYmMdD])\s*$")


def _period_to_days(period: str) -> int:
    """Map '5y'/'1y'/'6m'/'90d' etc to days. Default 5y = 1825."""
    if not period:
        return 1825
    m = PERIOD_RE.match(str(period).strip())
    if not m:
        # allow '5y' variants, fallback
        s = str(period).strip().lower()
        if s.endswith("y"):
            try:
                return int(s[:-1]) * 365
            except Exception:
                return 1825
        if s.endswith("m"):
            try:
                return int(s[:-1]) * 30
            except Exception:
                return 180
        if s.endswith("d"):
            try:
                return int(s[:-1])
            except Exception:
                return 1825
        return 1825
    n = int(m.group(1))
    unit = m.group(2).lower()
    if unit == "y":
        return n * 365
    if unit == "m":
        return n * 30
    return n


class IDXPostgres:
    """Async adapter over stockdata:15437."""

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = _resolve_db_url(db_url)
        self._pool: Optional[asyncpg.Pool] = None

    async def _pool_or_conn(self):
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self.db_url, min_size=1, max_size=5)
        return self._pool

    async def close(self):
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    # ---- helpers ----

    async def health(self) -> dict:
        """Lightweight health probe: counts + min/max time."""
        pool = await self._pool_or_conn()
        async with pool.acquire() as conn:
            tickers = await conn.fetchval("SELECT count(*) FROM tickers")
            rows = await conn.fetchval("SELECT count(*) FROM stock_data")
            rng = await conn.fetchrow("SELECT min(time) as mn, max(time) as mx FROM stock_data")
            return {
                "tickers": int(tickers or 0),
                "stock_data_rows": int(rows or 0),
                "min_time": str(rng["mn"]) if rng and rng["mn"] else None,
                "max_time": str(rng["mx"]) if rng and rng["mx"] else None,
                "db_url_host": self.db_url.split("@")[-1] if "@" in self.db_url else self.db_url,
            }

    async def get_stock_data(self, kode: str, limit: int = 1) -> list[dict]:
        """Latest raw stock_data rows for kode (most recent first)."""
        kode = kode.strip().upper()
        pool = await self._pool_or_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT time, kode_saham, open_price, tertinggi, terendah, penutupan,
                       volume, nilai, foreign_buy, foreign_sell, listed_shares,
                       sebelumnya, frekuensi, bid, offer
                FROM stock_data
                WHERE kode_saham = $1
                ORDER BY time DESC
                LIMIT $2
                """,
                kode,
                limit,
            )
            return [dict(r) for r in rows]

    async def get_ticker(self, kode: str) -> Optional[dict]:
        kode = kode.strip().upper()
        pool = await self._pool_or_conn()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT kode_saham, nama_saham, sector, industry FROM tickers WHERE kode_saham=$1",
                kode,
            )
            return dict(row) if row else None

    async def get_tickers(self, sector: Optional[str] = None) -> list[dict]:
        pool = await self._pool_or_conn()
        async with pool.acquire() as conn:
            if sector:
                rows = await conn.fetch(
                    "SELECT kode_saham, nama_saham, sector, industry FROM tickers WHERE sector=$1 ORDER BY kode_saham",
                    sector,
                )
            else:
                rows = await conn.fetch(
                    "SELECT kode_saham, nama_saham, sector, industry FROM tickers ORDER BY kode_saham"
                )
            return [dict(r) for r in rows]

    async def get_prices(
        self,
        ticker: str,
        period: str = "5y",
        include_foreign_flow: bool = True,
    ) -> list[dict]:
        """
        Time series for ticker over period.
        Returns list of {time, open, high, low, close, volume, nilai, foreign_buy, foreign_sell, listed_shares}
        sorted ASC (oldest first). Empty list if ticker not found.
        """
        kode = ticker.strip().upper().removesuffix(".JK")
        days = _period_to_days(period)
        # Jakarta time for cutoff; DB stores midnight WIB
        cutoff = datetime.now(timezone(timedelta(hours=7))).date() - timedelta(days=days)
        pool = await self._pool_or_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT time, open_price, tertinggi, terendah, penutupan,
                       volume, nilai, foreign_buy, foreign_sell, listed_shares,
                       sebelumnya
                FROM stock_data
                WHERE kode_saham = $1 AND time::date >= $2::date
                ORDER BY time ASC
                """,
                kode,
                cutoff,
            )
            out: list[dict] = []
            for r in rows:
                out.append(
                    {
                        "time": r["time"].isoformat() if r["time"] else None,
                        "open": float(r["open_price"]) if r["open_price"] is not None else None,
                        "high": float(r["tertinggi"]) if r["tertinggi"] is not None else None,
                        "low": float(r["terendah"]) if r["terendah"] is not None else None,
                        "close": float(r["penutupan"]) if r["penutupan"] is not None else None,
                        "volume": float(r["volume"]) if r["volume"] is not None else None,
                        "nilai": float(r["nilai"]) if r["nilai"] is not None else None,
                        "foreign_buy": float(r["foreign_buy"]) if r["foreign_buy"] is not None else None,
                        "foreign_sell": float(r["foreign_sell"]) if r["foreign_sell"] is not None else None,
                        "listed_shares": float(r["listed_shares"]) if r["listed_shares"] is not None else None,
                    }
                )
            return out

    async def get_corporate_actions(self, kode: str) -> list[dict]:
        kode = kode.strip().upper()
        pool = await self._pool_or_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT time, kode_saham, action_type, value FROM corporate_actions WHERE kode_saham=$1 ORDER BY time ASC",
                kode,
            )
            return [dict(r) for r in rows]

    async def latest_date(self) -> Optional[str]:
        pool = await self._pool_or_conn()
        async with pool.acquire() as conn:
            v = await conn.fetchval("SELECT max(time) FROM stock_data")
            return str(v) if v else None
