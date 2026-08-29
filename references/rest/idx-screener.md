# IDX — Companies Screener & Helper Lists

> **Lane 1 — IDX + Mining ONLY.** Sectors Financial API v2 reference for the
> IDX companies screener and reference helper lists. Source docs:
> `https://docs.sectors.app/api-references/v2/indonesia/...` (verified 29 Aug 2026).

All endpoints live under `https://api.sectors.app/v2/`. Auth is a raw API key in the `Authorization` header (no `Bearer ` prefix — MCP uses Bearer, REST does NOT).

## Quick taxonomy of helper lists

These tiny endpoints exist only to **discover valid slugs** for the screener's `sector`, `sub_sector`, `industry`, `sub_industry`, `tags`, and the `report_date` lookup for [Quarterly Financials](./idx-financials-transactions.md#company-quarterly-financials). Each costs **1 API credit** — call once and cache.

---

### `GET /v2/companies/` — Companies Screener

- **Purpose:** High-performance API for filtering and sorting IDX-listed companies. Supports both SQL-like structured queries (`where` + `order_by`) and natural-language queries (`q`). Returns a paginated list.
- **Hackathon applicability:** **all tracks**. Agent tracks build natural-language screeners; automation tracks run scheduled universe screens; market-intel tracks produce ranked watchlists.

#### Query parameters

| Name | Type | Default | Allowed / Notes |
|---|---|---|---|
| `q` | string | — | Natural-language query (e.g. `top 10 tech companies by revenue in 2023`). Overrides `where`/`order_by` when present. Successful `q` screen costs **3 credits**. |
| `where` | string | — | SQL-like filter. Operators: `=`, `!=`, `>`, `>=`, `<`, `<=`, `like`, `in`. Combine with `and` / `or`. Strings in single/double quotes. Lists via `tags in ['blue-chip','dividend']`. Arithmetic on both sides: `revenue[2024] / total_assets[2024] > 0.5`. Bracket notation for time-series: `revenue[2024]`. Successful structured screen costs **1 credit**. |
| `order_by` | string | — | Field name with optional `-` prefix for desc, e.g. `-market_cap`, `revenue[2024]`. |
| `limit` | integer | 50 | 1–200. |
| `offset` | integer | 0 | Pagination. |
| `include_query_values` | bool | false | When `true`, each `results[]` row gets a `query_values` map echoing the interpreted field values. |

#### Field categories (high-level)

- **Direct fields** — `symbol`, `company_name`, `listing_board`, `industry`, `sub_industry`, `sector`, `sub_sector`, `market_cap`, `market_cap_rank`, `employee_num`, `employee_num_rank`, `listing_date`, `last_ex_dividend_date`, `last_close_price`, `daily_close_change`, `forward_pe`, `intrinsic_value`, `esg_score`, `yield_ttm`, `dividend_ttm`, `payout_ratio`, `cash_payout_ratio`, `yoy_quarter_earnings_growth`, `yoy_quarter_revenue_growth`.
- **Array fields** — `tags` (analyst sentiment), `indices` (LQ45, IDX30, …), `affiliates` (related tickers). Filter with `in`.
- **JSON-object fields (TTM / MRQ)** — `pe_ttm`, `pb_mrq`, `ps_ttm`, `dar_mrq`, `der_mrq`, `roa_ttm`, `roe_ttm`, `total_assets_mrq`, `total_equity_mrq`, `total_revenue_mrq`, `earnings_mrq`, `total_liabilities_mrq`, `yearly_mcap_change`, `dividend_yield_avg_period`, `dividend_yield_avg`, plus YTD / 52w / 90d / all-time price windows (`ytd_low_price`, `52_w_high_date`, `all_time_high_price`, etc.).
- **Yearly fields** — bracket-notation: `revenue[2024]`, `earnings[2024]`, `eps[2024]`, `total_assets[2024]`, `total_equity[2024]`, plus banking/insurance sector extras (`gross_loan[2024]`, `net_interest_income[2024]`, `total_deposit[2024]`, `non_performing_loan[2024]`, `casa_ratio[2024]`, etc.). Forecast fields: `forecast_eps_growth[2025]`, `forecast_revenue_estimate[2025]`.
- **Quarterly fields** — `revenue_q[Q1-2024]`, `earnings_q[Q1-2024]`, `net_loan_q[Q1-2024]` (banking), `total_deposit_q[Q1-2024]` (banking).

#### Sample request

```bash
curl -G "https://api.sectors.app/v2/companies/" \
  -H "Authorization: <api-key>" \
  --data-urlencode "where=market_cap > 500000000000000" \
  --data-urlencode "order_by=-market_cap" \
  --data-urlencode "limit=20"
```

```python
import requests
r = requests.get(
    "https://api.sectors.app/v2/companies/",
    headers={"Authorization": "<api-key>"},
    params={
        "q": "top 3 banks by market cap",
        "include_query_values": "true",
    },
    timeout=30,
)
r.raise_for_status()
data = r.json()
```

#### Sample response (natural-language `q`)

```json
{
  "results": [
    {
      "symbol": "BBCA.JK",
      "company_name": "PT Bank Central Asia Tbk.",
      "query_values": { "sub_sector": "Banks", "market_cap": 753611199412500 }
    }
  ],
  "pagination": {
    "total_count": 48, "showing": 1, "limit": 3, "offset": 0,
    "has_next": true, "has_previous": false,
    "next_offset": 3, "previous_offset": null
  },
  "llm_translation": {
    "natural_query": "top 3 banks by market cap",
    "translated_params": {
      "where": "sub_sector = 'Banks' and market_cap IS NOT NULL",
      "order_by": "-market_cap",
      "limit": 3, "offset": null, "include_query_values": true
    },
    "message": null
  }
}
```

#### Errors worth knowing

- `400 INVALID_WHERE_CLAUSE` — invalid field name. Documents say: use bracket notation, not `revenue_in_2024`. Use `revenue[2024]`.
- `400 TYPE_MISMATCH` — operator/field type mismatch (e.g. `like` on a numeric field).
- `400 INVALID_LIMIT` — `limit` must be 1–200.
- `400 NON_TRANSLATABLE_QUERY` — `q` references a field that doesn't exist. **Charges 1 credit** (model already ran). Other 400s on structured queries are free.
- `429 RATE_LIMIT_EXCEEDED`.

#### Gotchas

- **Smart FY handling**: between Jan–Apr, "latest year" queries default to the **previous** audited year (e.g. early 2026 → 2024 data).
- **String comparisons** are case-insensitive.
- **`order_by` accepts arbitrary fields** — top-company-rankings v1 endpoints were folded into this one via `order_by`.
- **Universe feeds beat per-symbol loops** — for daily EOD, prefer [`/v2/close/`](./idx-financials-transactions.md#daily-full-universe-close) over calling `/v2/companies/?...` + extracting symbols.

---

### `GET /v2/free-float/` — Free Float Market Analysis

- **Purpose:** Returns free float percentage for IDX-listed companies, optionally filtered by one level of the sector taxonomy. Results ordered by `free_float` descending.
- **Hackathon applicability:** **all tracks**. Common filter for institutional-investable universe (`free_float > 0.5`).

#### Query parameters

| Name | Type | Allowed values / Notes |
|---|---|---|
| `sector` | string | kebab-case — e.g. `infrastructures`, `healthcare`, `transportation-logistic`. Get valid list from [`/v2/subsectors/`](#get-v2subsectors--subsectors). |
| `sub_sector` | string | kebab-case — e.g. `banks`, `basic-materials`, `food-beverage`. |
| `industry` | string | kebab-case — e.g. `oil-gas`, `electrical`, `chemicals`. |
| `sub_industry` | string | kebab-case — e.g. `coal-production`, `gold`, `healthcare-providers`. |

> ⚠️ **Mutually exclusive** — pass at most ONE filter per request.

#### Sample request

```bash
curl -G "https://api.sectors.app/v2/free-float/" \
  -H "Authorization: <api-key>" \
  --data-urlencode "sub_sector=banks"
```

```python
r = requests.get(
    "https://api.sectors.app/v2/free-float/",
    headers={"Authorization": "<api-key>"},
    params={"sub_sector": "banks"},
    timeout=30,
)
```

#### Sample response

```json
[
  { "symbol": "PADI.JK", "company_name": "Minna Padi Investama Sekuritas Tbk", "free_float": 0.999 }
]
```

#### Gotchas

- Free float = `share_percentage` of the **Public** entry in a company's major shareholders list.
- Costs **1 credit per 100 companies returned, rounded up** (different from most "1 credit flat" endpoints).
- **Mutually exclusive** — combining filters returns 400.

---

### `GET /v2/companies/list_companies_with_segments/` — Companies with Revenue Segments

- **Purpose:** Dictionary of all companies that have revenue/cost segment data available, keyed by symbol (uppercase, `.JK` suffix), with the list of available `financial_year`s.
- **Hackathon applicability:** **ai-agents / market-intel** — gate before calling per-symbol [Segments](./idx-company.md#company-revenue-segments).

#### Query parameters

None.

#### Sample request

```bash
curl "https://api.sectors.app/v2/companies/list_companies_with_segments/" \
  -H "Authorization: <api-key>"
```

#### Sample response

```json
{
  "BBCA.JK": { "financial_year": [2022, 2023, 2024, 2025] },
  "BMRI.JK": { "financial_year": [2022, 2023, 2024, 2025] },
  "TLKM.JK": { "financial_year": [2022, 2023, 2024] }
}
```

#### Gotchas

- **Costs 1 credit.** Use this once at startup to populate a local "has_segments?" cache — avoid 404s on `/v2/company/get-segments/{symbol}/`.
- A 404 from per-symbol segments endpoint will charge 1 credit (per docs), so guard with this list first.

---

### `GET /v2/companies/quarterly-financial-dates/` — Latest Quarterly Financial Dates (Universe)

- **Purpose:** Returns the **latest** available quarterly report date and quarter label for every IDX company in one paginated feed. Built for **freshness polling** with `?since=`.
- **Hackathon applicability:** **automation** (cron polling for newly-reported quarters) and **ai-agents** (just-in-time figure retrieval).

#### Query parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `year` | integer | — | Restrict to report dates within this calendar year (e.g. `2024`). |
| `limit` | integer | 20 | 1–30, max 30. |
| `offset` | integer | 0 | Pagination. |
| `since` | string (date) | — | Return only companies whose latest quarter-end is on/after this `YYYY-MM-DD`. Empty result for future date. |

#### Sample request

```bash
curl -G "https://api.sectors.app/v2/companies/quarterly-financial-dates/" \
  -H "Authorization: <api-key>" \
  --data-urlencode "since=2025-09-30" \
  --data-urlencode "limit=30"
```

#### Sample response

```json
{
  "results": [
    { "symbol": "AADI.JK", "date": "2026-03-31", "quarter": "q1" }
  ],
  "pagination": {
    "total_count": 959, "showing": 1, "limit": 30, "offset": 0,
    "has_next": true, "has_previous": false,
    "next_offset": 30, "previous_offset": null
  }
}
```

#### Gotchas

- One row per company (~950), sorted by symbol. Companies with no quarterly data omitted.
- Costs **1 credit per page**. Full sweep ~32 pages at max `limit=30`.
- **Use `since` to poll incrementally** — far cheaper than full-sweep polling.

---

### `GET /v2/company/get_quarterly_financial_dates/{symbol}/` — Quarterly Financial Dates (per-symbol)

- **Purpose:** Returns all available quarterly report dates for one symbol, grouped by year. Use the `report_date` values returned as inputs to [Quarterly Financials](./idx-financials-transactions.md#company-quarterly-financials).

#### Path parameters

| Name | Type | Notes |
|---|---|---|
| `symbol` | string | IDX symbol, 4 letters, `.jk` optional. E.g. `ASII`, `BBCA`, `BMRI`. |

#### Sample request

```bash
curl "https://api.sectors.app/v2/company/get_quarterly_financial_dates/BBCA/" \
  -H "Authorization: <api-key>"
```

#### Sample response

```json
{
  "2026": [["2026-03-31", "q1"]],
  "2025": [["2025-12-31", "q4"], ["2025-09-30", "q3"], ["2025-06-30", "q2"], ["2025-03-31", "q1"]]
}
```

#### Errors

- `400` — invalid symbol format.
- `404` — symbol well-formed but no quarterly data. **Charges 1 credit.**

#### Gotchas

- Costs 1 credit. Prefer [universe `/v2/companies/quarterly-financial-dates/`](#get-v2companiesquarterly-financial-dates--latest-quarterly-financial-dates-universe) for fresh-data polling; this endpoint is for deep lookups on one symbol.

---

### `GET /v2/subsectors/` — Subsectors

- **Purpose:** Returns all available sector/subsector pairs as kebab-case slugs.
- **Hackathon applicability:** **all tracks** — used as input validation for `sector`/`sub_sector` on screener + free-float.

#### Query parameters

None.

#### Sample request

```bash
curl "https://api.sectors.app/v2/subsectors/" -H "Authorization: <api-key>"
```

#### Sample response

```json
[
  { "sector": "transportation-logistic", "subsector": "transportation" }
]
```

#### Gotchas

- Costs 1 credit. Cache the result.
- Field is `subsector` (not `sub_sector`) in the response — but the **request parameters** are `sector` and `sub_sector`.

---

### `GET /v2/industries/` — Industries

- **Purpose:** Returns all available subsector/industry pairs as kebab-case slugs.

#### Sample request / response

```bash
curl "https://api.sectors.app/v2/industries/" -H "Authorization: <api-key>"
```

```json
[{ "subsector": "investment-service", "industry": "investment-services" }]
```

#### Gotchas

- Costs 1 credit. Cache. Used as input for the `industry` parameter on screener + free-float.

---

### `GET /v2/subindustries/` — Subindustries

- **Purpose:** Returns all available industry/sub-industry pairs as kebab-case slugs.

#### Sample request / response

```bash
curl "https://api.sectors.app/v2/subindustries/" -H "Authorization: <api-key>"
```

```json
[{ "industry": "metals-minerals", "sub_industry": "diversified-metals-minerals" }]
```

#### Gotchas

- Costs 1 credit. Cache. Used as input for the `sub_industry` parameter.

---

### `GET /v2/tags/` — News Tags

- **Purpose:** Returns a sorted alphabetical array of all available tag slugs used across [news](./idx-rankings-brokers-news.md#news-articles) and [filings](./idx-rankings-brokers-news.md#company-filings).

#### Sample request / response

```bash
curl "https://api.sectors.app/v2/tags/" -H "Authorization: <api-key>"
```

```json
["analyst-ratings", "blue-chip", "dividend", "esg", ...]
```

#### Gotchas

- Costs 1 credit. Cache.
- Input to the `tags` parameter on news/filings (e.g. `where=tags in ['blue-chip','dividend']` for screener; `?tags=` for news).

---

## Cross-references

- TOC anchor: [`sectors-api-and-mcp.md`](../sectors-api-and-mcp.md)
- Per-company reports: [`idx-company.md`](./idx-company.md)
- Financials + daily transactions: [`idx-financials-transactions.md`](./idx-financials-transactions.md)
- Rankings, brokers, news: [`idx-rankings-brokers-news.md`](./idx-rankings-brokers-news.md)
- Mining endpoints: [`mining-*.md`](./)
