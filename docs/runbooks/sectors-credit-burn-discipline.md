# Runbook: Sectors credit-burn discipline

**Trigger:** the Sectors credit burn has spiked (rate log shows repeated
`/v2/company/corporate-actions/AMMN/`, `/v2/financials/quarterly/AMMN/`,
`/v2/company/report/AMMN/`, `/v2/daily/AMMN/` Direct API hits within minutes).

**Do not** flip the key off or change the env. The right move is to make
the collector serve from the local freeze and gate any new live call
behind an explicit operator toggle.

## TL;DR

```bash
# Stop the bleed NOW - default-deny upstream until you say go again:
bash scripts/toggle_sectors_offline.sh lock && bash scripts/restart-api.sh

# Re-enable when a deliberate run needs fresh data:
bash scripts/toggle_sectors_offline.sh unlock && bash scripts/restart-api.sh
```

## How the freeze works (`agents/collector.py`)

The collector has a tiered resolution that no caller has to know about:

1. `data/output/cache_collector_{TICKER}.json`  - 4h TTL, written by the
   last successful `collect(ticker)`. Pure read; zero cost; clears after 4h
   if upstream data shifts.
2. `output/cache/ammn_fill/company_report_{TICKER}_multisection.json`  -
   7-day freeze from the AMMN-FILLD lane (kanban t_2c5f420e, set 12 Sep
   2026). This is the source-of-truth payload for AMMN: when present, the
   collector resolves in <1ms with `source: ammn_fill_freeze` and bills
   0 credits. The freeze carries `overview + financials + daily + actions
   + filings + flow + broker_top + quarterly` so an AMMN run is fully
   covered without any Sectors call.
3. `SECTORS_OFFLINE=1` short-circuit  - when neither cache nor freeze is
   available, the collector raises `sectors_offline_mode` instead of
   burning a credit. Wired AFTER the freeze so a frozen ticker still works
   in offline mode.
4. Sectors v2 upstream  - only when 1+2+3 all miss. Billed per the cache
   rules in `references/sectors-credit-leak-guards.md`; window substitution
   keeps the cache key stable across date drift.

## Why the tier-1 cache alone isn't enough

`tier 1` is a 4h TTL written by the LAST `collect()`. If a tab clicks
"Run report" repeatedly and the cache is hit, the cache will be hit.
But the cache is keyed by `(endpoint, params)`  - the call site
`_try_sectors` re-computes `start = today - 90d` every call, so a fresh
window key on every render **bypasses the cache** (the original 2-credit
mystery from the ADK prod run).

The tier-2 freeze bypasses `_try_sectors` entirely  - it returns a
pre-shaped payload without invoking the Sectors adapter, so even if the
window key drifts the freeze short-circuits. For AMMN today the freeze
wins on every call (verified: `collect("AMMN")` returns 0.3ms with
`source: ammn_fill_freeze`, 0 Sectors calls).

## Locking the upstream

```bash
# Set SECTORS_OFFLINE=1 in the env file that docker-compose reads
bash scripts/toggle_sectors_offline.sh lock
# Bounce the api container (script handles the rebuild + recreate)
bash scripts/restart-api.sh
# Confirm: AMMN still serves the report (freeze), BBCA returns 422
curl -s localhost:8777/api/report/AMMN/html | grep "PBV" | head -1
curl -s -o /dev/null -w '%{http_code}\n' localhost:8777/api/report/BBCA/html
```

## Daily discipline

- The live page at `/api/report/AMMN/html` reads `data/assumptions/AMMN.json`
  + `data/drivers/AMMN.json` and never hits Sectors. That's the
  rendering hot-path; safe to refresh in a browser tab.
- The ADK run at `/api/agent/start` (POST) is what burns credits. Operators
  who click "Run Report" in the FE each trigger one full collector pass.
  When the freeze is present (AMMN), the pass costs 0 credits.
- Manual upstream pulls should use `scripts/sectors_harvest.py
  --execute` with the lake directory, NEVER call `server/sectors.*`
  inline.

## Verified workflow

```
$ bash scripts/toggle_sectors_offline.sh lock
$ bash scripts/restart-api.sh
$ .venv/bin/python -c "from agents.collector import collect; print(collect('AMMN', use_cache=False, force_refresh=True)['source'])"
ammn_fill_freeze                # 0 credits
$ .venv/bin/python -c "from agents.collector import collect; collect('BBCA', use_cache=False, force_refresh=True)"
RuntimeError: sectors_offline_mode: SECTORS_OFFLINE=1 set, refusing to call upstream for BBCA
```
