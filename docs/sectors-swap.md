# Sectors swap list — mechanical wiring once SECTORS_API_KEY lands

> Qualifying rule, verbatim (rules.md §06): "Projects must use **Sectors MCP
> or the Sectors REST API as a core data source**, not as a single decorative
> call. The product should **lose its core functionality if Sectors data is
> removed**." No all-Sectors mandate, no external ban — externals allowed as
> long as core verdicts are Sectors-grounded. We exceed it: every data path
> is Sectors-or-503, so the kill-Sectors test passes trivially. Other hard
> gates: all members onboarded (§03), repo public ≥90d post-winners, ZERO
> commits after freeze/submit (even bugfixes), strip API keys pre-submit,
> deadline 30 Sep 2026 23:59 WIB.

Client: `server/sectors.py` (raw-key auth, bare tickers, loud 503 when keyless).
23 helpers: 8 base (daily/universe/quarterly/report/actions/news/filings/flow)
+ 15 ranked (peers/future/valuation/ownership/management/broker-top/
suspensions/subsector/listing/screener/index-daily/idx-mcap/mining).
Tests: `tests/test_sectors_client.py` (keyless-loud over all 23).

## Pricing (discovered from docs, was unknown)
1 credit/section on reports; most endpoints 1; structured screener 1, NL ?q= 3
(NEVER ?q=); 404 bills 1 (validate tickers first); 400/401/429/5xx free;
empty-200 STILL bills (check quarterly-financial-dates before pulling).
Quintet Tier 1+2 probe budget ≈ <60 credits of the 1,000.
Cache rule: every new call goes behind the existing 4h `cached_endpoint` layer.
Credit rule: universe feeds > per-symbol loops, minimal `sections=`, quintet only.

## Call-site swaps (in wiring order — cheapest/highest-value first)

| # | File : line | Now (external) | Swap to | Notes |
|---|---|---|---|---|
| 1 | `server/routers/endpoints.py:172-235` `_infer_archetype` yfinance fallback | `yf.Ticker.info.sector` | `sectors.company_report(sym, "overview")` → sector field | Kills a runtime yfinance import in the hot path |
| 2 | `server/stockdata.py` whole module | IDX Postgres `stockdata:15437` + yfinance fallback | `sectors.universe_close(date)` for breadth, `sectors.daily(sym,…)` for depth | Docstring already says "Sectors P2 gated" — this IS P2 |
| 3 | `agents/adk/tools/web_tools.py` `web_search` | Tavily key | `sectors.news(symbols)` | Tavily becomes backup/removed; kills external cost entirely |
| 4 | `server/routers/mock_sectors.py` (758 lines) | yfinance/IDX harvester mimicking v2 schemas | Thin proxy to real v2 (`quarterly`, `news`, `filings`, `corporate_actions`) + cache | File keeps its routes/tests; only the fetch layer changes |
| 5 | `agents/collector.py` (27 ext refs) | yfinance statements | `sectors.quarterly(sym, 8)` (+ bank extras free) | Check bank field mapping: `net_interest_income`, `gross_loan`, `total_deposit` |
| 6 | `scripts/yfinance_fallback.py` | yfinance batch | `sectors.daily` / `universe_close` | Rename file to `sectors_backfill.py` when wired |
| 7 | `scripts/seed_assumptions.py`, `seed_synthetic.py` | hand-built/manual | `sectors.company_report(sym, "valuation,peers,financials,dividend")` | Assumptions files become Sectors-grounded, keep manual override |

## 503 wiring pattern (endpoints.py)

```python
from server.sectors import SectorsNotConfigured, SectorsError
try:
    data = sectors.daily(t, start, end)
except SectorsNotConfigured:
    raise HTTPException(503, "Sectors API key belum dipasang — data live belum tersedia")
except SectorsError as e:
    raise HTTPException(502, f"Sectors upstream {e.status}")
```

NEVER `except: fallback_to_yfinance()`. Explicit failure is the rule.

## New signals unlocked (had nothing before)

- `foreign_flow(sym,…)` — net foreign-broker inflow, 90d (feeds Thesis/Risk)
- `company_report` sections `future,management,ownership` — analyst-grade narrative
- `universe_close` — breadth scans (movers/screener) in 1 call

## Verification gate (needs key — do NOT run keyless)

1. `set -a && source .env && set +a` (never echo key)
2. One cheap probe: `company_report("BBCA","dividend")` → 200 + shape assert
3. Quintet sweep × 5 tickers, count calls, confirm < 40 total (budget check)
4. `pytest tests/ -q` full green, then FE rebuild + Pages deploy
