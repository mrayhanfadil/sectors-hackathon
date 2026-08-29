# IDX — Financials & Transaction Data

> **Lane 1 — IDX + Mining ONLY.** Sectors Financial API v2 reference for IDX
> quarterly financials, daily transactions (per-symbol + universe), IDX market
> summary (total market cap), and index daily data. Source docs:
> `https://docs.sectors.app/api-references/v2/indonesia/...` (verified 29 Aug 2026).

All endpoints live under `https://api.sectors.app/v2/`. Auth is a raw API key in the `Authorization` header (no `Bearer ` prefix).

> **IDX symbol convention**: 4 letters, optionally followed by `.jk` (case-insensitive). E.g. `BBCA`, `BMRI`, `TLKM`.

> **Date range rule (90-day window)**: All `start`/`end` date endpoints default to the last 30 days. Maximum window is **90 days** — wider ranges are silently clamped to the most recent 90 days ending at `end`. Future `end` dates return 400.

---

### `GET /v2/financials/quarterly/{symbol}/` — Company Quarterly Financials

- **Purpose:** Quarterly financial data for one IDX symbol. **Fields vary by sector** — financial-sector companies (banks, insurance) have additional metrics in `financials_sector_metrics` (`net_interest_income`, `gross_loan`, `total_deposit`, etc.).
- **Hackathon applicability:** **all tracks**. Agent tracks drive comparative analyses; automation tracks build earnings calendars; market-intel tracks power valuation models.

#### Path + query parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `symbol` | path | required | E.g. `BMRI`, `BBCA`, `TLKM`. |
| `n_quarters` | integer | — | Number of most recent quarters to return. Min 1. |
| `report_date` | string (date) | — | Specific `YYYY-MM-DD`. Get valid values from [`/v2/company/get_quarterly_financial_dates/{symbol}/`](./idx-screener.md#get-v2companyget_quarterly_financial_datessymbol--quarterly-financial-dates-per-symbol). |
| `approx` | boolean | `true` | If `true`, approximate-quarter matching when exact date not found. |

#### Sample request

```bash
curl -G "https://api.sectors.app/v2/financials/quarterly/BBCA/" \
  -H "Authorization: <api-key>" \
  --data-urlencode "n_quarters=4"
```

```python
r = requests.get(
    "https://api.sectors.app/v2/financials/quarterly/BBCA/",
    headers={"Authorization": "<api-key>"},
    params={"n_quarters": 4},
    timeout=30,
)
```

#### Sample response (banking — full `financials_sector_metrics` block present)

```json
[
  {
    "symbol": "BBCA.JK",
    "financials_sector_metrics": {
      "interest_income": 24592248000000, "interest_expense": 3483815000000,
      "net_interest_income": 21108433000000,
      "gross_loan": 970701203000000, "allowance_for_loans": 30526805000000,
      "net_loan": 940174398000000, "total_earning_assets": null,
      "current_account": 447811289000000, "savings_account": 634224104000000,
      "time_deposit": 194373518000000, "total_deposit": 1276408911000000,
      "other_interest_bearing_liabilities": null,
      "total_cash_and_due_from_banks": 90242485000000
    },
    "date": "2026-03-31",
    "premium_income": 532089000000, "premium_expense": 0,
    "net_premium_income": 532089000000, "non_interest_income": 6793596000000,
    "revenue": 28434118000000, "operating_expense": 8673143000000,
    "provision": -1232275000000, "operating_pnl": 18077072000000,
    "non_operating_income_or_loss": 0,
    "earnings_before_tax": 18077072000000, "tax": 3387273000000,
    "minorities": 5676000000, "earnings": 14695475000000,
    "gross_profit": null, "interest_expense_non_operating": null,
    "ebit": 18077072000000, "ebitda": 18762398000000,
    "cost_of_revenue": null, "total_assets": 1640830566000000,
    "non_interest_bearing_liabilities": null, "cash_only": 23963776000000,
    "total_liabilities": 1370360247000000, "total_equity": 259358793000000,
    "total_debt": null, "stockholders_equity": 259132407000000,
    "total_non_current_assets": null, "current_liabilities": null,
    "cash_and_short_term_investments": null, "non_loan_assets": null,
    "total_current_asset": null, "total_non_current_liabilities": null,
    "financing_cash_flow": -1072636000000,
    "operating_cash_flow": 47920728000000,
    "investing_cash_flow": -16987375000000,
    "net_cash_flow": 29860717000000,
    "free_cash_flow": 47485515000000,
    "realized_capital_goods_investment": -435213000000
  }
]
```

#### Common fields (all sectors)

| Field | Type | Notes |
|---|---|---|
| `symbol` | string | Ticker. |
| `date` | string | Quarterly report date (YYYY-MM-DD). |
| `revenue` | integer | IDR. Nullable for some sectors. |
| `earnings` | integer | Net earnings in IDR. |
| `total_assets`, `total_liabilities`, `total_equity` | integer | IDR. |
| `operating_cash_flow`, `investing_cash_flow`, `financing_cash_flow`, `net_cash_flow`, `free_cash_flow` | integer | IDR. |
| `operating_expense`, `operating_pnl`, `earnings_before_tax`, `tax`, `ebit`, `ebitda`, `minorities` | number | IDR. |
| `cost_of_revenue`, `gross_profit` | number | IDR. Many sectors return null. |

#### Banking extras (`financials_sector_metrics`)

`interest_income`, `interest_expense`, `net_interest_income`, `gross_loan`, `allowance_for_loans`, `net_loan`, `current_account`, `savings_account`, `time_deposit`, `total_deposit`, `total_cash_and_due_from_banks`, `other_interest_bearing_liabilities`, `total_earning_assets`, `non_interest_income`, `non_interest_bearing_liabilities`, `non_loan_assets`.

#### Insurance extras

`premium_income`, `premium_expense`, `net_premium_income`.

#### Gotchas

- **Costs 1 credit per quarter returned.** So `n_quarters=4` = 4 credits. Use sparingly in agent loops.
- Mix of `integer` and `number` (`double`) types in OpenAPI schema — be defensive when parsing.
- Many nullable fields per the OpenAPI schema. Use `if "field" in obj and obj["field"] is not None` checks.
- For a specific quarter → use `report_date`. For most-recent → `n_quarters=1` (cheapest).

---

### `GET /v2/close/` — Daily Full-Universe Close

- **Purpose:** Returns the daily closing price for **every** IDX ticker on one trading day, in one paginated feed — replaces 950 per-symbol calls.
- **Hackathon applicability:** **automation** (daily EOD snapshot jobs), **market-intel** (universe screening).

#### Query parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `date` | string (date) | most recent trading day | `YYYY-MM-DD`. Future dates return 400. |
| `limit` | integer | 20 | 1–30, max 30. |
| `offset` | integer | 0 | Pagination. |

#### Sample request

```bash
curl -G "https://api.sectors.app/v2/close/" \
  -H "Authorization: <api-key>" \
  --data-urlencode "date=2025-05-02" \
  --data-urlencode "limit=30"
```

#### Sample response

```json
{
  "results": [{ "symbol": "AADI.JK", "date": "2025-05-02", "close": 7150 }],
  "pagination": {
    "total_count": 942, "showing": 1, "limit": 30, "offset": 0,
    "has_next": true, "has_previous": false,
    "next_offset": 30, "previous_offset": null
  }
}
```

#### Gotchas

- **Costs 1 credit per page.** Full ~950-ticker universe = ~32 pages at max `limit=30` (~32 credits).
- **Tickers with no recorded close for the requested day are omitted** — count will be lower on holidays/half-days.
- **This is the right endpoint for EOD snapshot jobs.** For history of one symbol → use [`/v2/daily/{symbol}/`](#get-v2dailysymbol--daily-transaction-data) instead.
- For batches > 30 → loop `offset += limit` until `has_next = false`.

---

### `GET /v2/daily/{symbol}/` — Daily Transaction Data (per-symbol)

- **Purpose:** Daily close price, volume, and market cap for one IDX symbol over a date range of up to 90 days.
- **Hackathon applicability:** **ai-agents** (historical context for a symbol), **market-intel** (charting, technical analysis).

#### Path + query parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `symbol` | path | required | E.g. `BBCA`, `GOTO`, `TLKM`. |
| `start` | string (date) | 30 days before `end` | `YYYY-MM-DD`. |
| `end` | string (date) | today | `YYYY-MM-DD`. Future dates → 400. |

> **Range clamping**: ranges wider than 90 days are silently clamped to the most recent 90 days ending at `end`.

#### Sample request

```bash
curl -G "https://api.sectors.app/v2/daily/BBCA/" \
  -H "Authorization: <api-key>" \
  --data-urlencode "start=2025-05-01" \
  --data-urlencode "end=2025-05-14"
```

#### Sample response

```json
[
  {
    "symbol": "BBCA.JK", "date": "2025-05-02",
    "close": 8975, "volume": 92219000, "market_cap": 1095329638012500
  }
]
```

#### Gotchas

- Costs 1 credit per call (regardless of range up to 90 days).
- A valid ticker with no rows in the window returns 200 with empty list. Unknown ticker → 404 (charges 1 credit per docs).
- `market_cap` is in IDR (raw integer, not formatted).
- For long histories → page in 90-day windows.

---

### `GET /v2/idx-total/` — IDX Market Summary

- **Purpose:** Historical total IDX market capitalization for a date range of up to 90 days. Powers macro dashboards.
- **Hackathon applicability:** **market-intel** (market breadth dashboards), **automation** (macro indicators).

#### Query parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `start` | string (date) | 30 days before `end` | `YYYY-MM-DD`. **Earliest valid: `2021-01-01`** — earlier dates return 400. |
| `end` | string (date) | today | Future dates → 400. |

> **Range clamping**: ranges wider than 90 days are silently clamped to the most recent 90 days.

#### Sample request

```bash
curl -G "https://api.sectors.app/v2/idx-total/" \
  -H "Authorization: <api-key>" \
  --data-urlencode "start=2025-05-01" \
  --data-urlencode "end=2025-05-14"
```

#### Sample response

```json
[{ "date": "2026-06-09", "idx_total_market_cap": 10095511071726246 }]
```

#### Gotchas

- Costs 1 credit per call.
- Earliest available data: **January 1, 2021**. Pre-2021 dates → 400.
- `idx_total_market_cap` is in raw IDR.

---

### `GET /v2/index-daily/{index_code}/` — Index Daily Transaction Data

- **Purpose:** Daily closing price for one IDX index over a date range of up to 90 days.
- **Hackathon applicability:** **market-intel** (benchmark overlays), **automation** (index-based signals).

#### Path + query parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `index_code` | path | required | E.g. `lq45`, `ihsg`, `idx30`. See list below. |
| `start` | string (date) | 30 days before `end` | `YYYY-MM-DD`. **Earliest valid: `2019-01-02`**. |
| `end` | string (date) | today | Future dates → 400. |

> **Range clamping**: ranges wider than 90 days are silently clamped to the most recent 90 days.

#### Available index codes (verified list)

`ftse`, `idx30`, `idxbumn20`, `idxesgl`, `idxg30`, `idxhidiv20`, `idxq30`, `idxv30`, **`ihsg`** (composite), `jii70`, `kompas100`, **`lq45`** (blue-chip 45), `sminfra18`, `srikehati`, `sti`, `economic30`, `idxvesta28`.

#### Sample request

```bash
curl -G "https://api.sectors.app/v2/index-daily/lq45/" \
  -H "Authorization: <api-key>" \
  --data-urlencode "start=2025-05-02" \
  --data-urlencode "end=2025-05-09"
```

#### Sample response

```json
[
  { "index_code": "LQ45", "date": "2025-05-05", "price": 767.32 }
]
```

#### Gotchas

- Costs 1 credit per call.
- Invalid index code → `400 Please provide a valid index code.`
- Earliest available data: **January 2, 2019**. Pre-2019 dates → 400.
- `price` is the index closing value (NOT market cap).

---

## Cross-references

- TOC anchor: [`sectors-api-and-mcp.md`](../sectors-api-and-mcp.md)
- Screener + helper lists: [`idx-screener.md`](./idx-screener.md)
- Per-company reports: [`idx-company.md`](./idx-company.md)
- Rankings, brokers, news: [`idx-rankings-brokers-news.md`](./idx-rankings-brokers-news.md)
