# server/collector — IDX + yfinance Data Layer (P0-P1)

Locked plan §4: **stockdata:15437 is P0-P1 primary — no Sectors credit**.

## DB

- `postgresql://postgres:password@localhost:15437/stockdata` (TimescaleDB)
- Tables: `stock_data(time, kode_saham, open_price, tertinggi, terendah, penutupan, volume, nilai, foreign_buy/sell, listed_shares, sebelumnya, ...)` + `tickers(kode_saham, sector, industry)` + `corporate_actions`
- Rows 2026-08-26: 989 tickers, 1,348,545 stock_data rows (2020-01-02 → 2026-08-26)
- Env var: `DATABASE_URL` (also `DB_URL`), default `postgresql+asyncpg://postgres:password@localhost:15437/stockdata`

## Adapter

`server/collector/idx_postgres.py`

```python
from server.collector.idx_postgres import IDXPostgres
db = IDXPostgres()  # reads DATABASE_URL / DB_URL
await db.health()                          # counts + min/max time
await db.get_ticker("BBCA")                # sector/industry
await db.get_tickers(sector="Financials")  # list
await db.get_prices("BBCA", period="5y")   # ASC time series {time,open,high,low,close,volume,nilai,foreign_buy/sell,listed_shares}
await db.get_stock_data("RATU", limit=1)   # latest raw row
await db.get_corporate_actions("ADRO")
```

`period` supports `5y / 1y / 6m / 90d`. Closes gaps by falling back to synthetic `data/sectors.db` (seed=42) when IDX is empty — label `estimated`.

## yfinance fallback

`scripts/yfinance_fallback.py` — only for large-cap gap-fill (BBCA). Small caps are IDX-primary; if yfinance empty, label `estimated`.

```python
from scripts.yfinance_fallback import get_yfinance_prices, get_yfinance_fundamentals, gap_summary
get_yfinance_prices("BBCA", period="5y")   # cached 4h, rate-limit 1.2s, disclose source: yfinance per exhibit
get_yfinance_fundamentals("BBCA")          # financials/balance/cashflow — often empty for IDX small caps
gap_summary()                              # per-ticker gap table
```

Cache: `.cache/yfinance/` TTL 14400 (4h), env `YFINANCE_CACHE_DIR` / `YFINANCE_TTL_SECONDS`.
Rate-limit `YFINANCE_RATE_LIMIT=1.2`. Disclosure: every exhibit must state `source: idx|yfinance` via `data/assumptions/{ticker}.json`.
Network note 2026-08-31: `fc.yahoo.com` is unreachable from this host (curl 7) — yfinance probes return `rows=0` + error; IDX remains primary.

## yfinance gap table

| ticker | posture | gap |
|---|---|---|
| RATU | idx primary | thin — IPO 2025, yfinance history short; rely IDX |
| CDIA | idx primary | thin — 2025 listing, sparse; rely IDX |
| MTEL | idx primary | moderate — yfinance has prices but fundamentals patchy |
| BBCA | idx primary, yfinance usable | good — large cap, yfinance complete (fallback only) |
| ADRO | idx primary | moderate — yfinance ok, cross-check IDX foreign flow |

All quintet source in `data/assumptions/*.json` is `idx` on this host (yfinance blocked). When network recovers, BBCA may flip to `yfinance` per `verify_e2e.py` policy.

## Synthetic fallback

- `data/sectors.db` (seed=42, 3.5M) — `synthetic_prices` + `synthetic_tickers` + `sector_kpi`
- `data/peers.json` — dual mode + SOTP pillars + KPI list
- `data/assumptions/{ticker}.json` — per-ticker `source: idx|yfinance`, provenance, `no_sectors_hit: true`
- `scripts/seed_synthetic.py` — regen both
- `scripts/seed_assumptions.py` — stubs

Seeds: universe 49 tickers + 5y business-day walk, deterministic.

## Verify E2E

```bash
python3 scripts/verify_e2e.py
```

Proves: 5 tickers have `prices 5y + foreign flow + sector`, prints markdown table, writes provenance to `data/assumptions/`, hard-fails if any sector/close/foreign missing. Example 2026-08-31:

| kode | sector | close | vol | nilai | foreign_buy/sell | listed_shares | 5y rows | 5d rows | latest |
|---|---|---|---|---|---|---|---|---|---|
| RATU | Energy | 4200 | 6764600 | 29075601000 | 513800/2308200 | 2715053800 | 383 | 1 | 2026-08-26 |
| CDIA | Infrastructures | 645 | 97538300 | 65272647500 | 14255700/14172500 | 124829374700 | 272 | 1 | 2026-08-26 |
| MTEL | Infrastructures | 460 | 174442800 | 81105739000 | 53677700/79357900 | 83559677444 | 1138 | 1 | 2026-08-26 |
| BBCA | Financials | 6350 | 86115900 | 550008087500 | 58278500/45666300 | 122042299500 | 1195 | 1 | 2026-08-26 |
| ADRO | Energy | 2610 | 50134700 | 131487531000 | 28877000/22015300 | 28800494200 | 1195 | 1 | 2026-08-26 |

yfinance 5d probe: 0 rows for all 5 (fc.yahoo.com unreachable — expected; IDX covers).

## No Sectors yet

Per plan §4 + §7 P1: **Sectors deferred to P2 gate**. P0-P1 is 0 Sectors credit (IDX+yfinance+synthetic).
