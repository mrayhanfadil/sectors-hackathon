# Sectors MCP — Tool Reference

> Source: https://docs.sectors.app/recipes/sectors-for-ai-agents/00-sectors-mcp-guide#tools-reference
> Verified: 29 Aug 2026

**65+ tools** exposed by the Sectors MCP server. All are tool names that LLMs call directly (kebab-cased). Below: parameter signature, sample call, sample response, and the equivalent REST endpoint where one exists.

**Coverage legend**
- **IDX** — Indonesia Stock Exchange (primary for this hackathon)
- **Mining** — Indonesian mining commodity / company / site data
- **SGX** — Singapore Exchange (FYI, cross-link only)
- **KLSE** — Bursa Malaysia (FYI, cross-link only)

**IDX + Mining breakdown at the bottom.**

> **Auth on every call:** `Authorization: Bearer <YOUR_API_KEY>` header to `https://sectors-mcp.supertype.ai/mcp` (Streamable HTTP). See [setup.md](./setup.md).

---

## Company analysis (IDX)

### `fetch-company-report`
- **Purpose:** Full company report with selectable sections.
- **Coverage:** IDX (primary) | SGX (variant: `fetch-sgx-company-report`) | KLSE (variant: `fetch-klse-company-report`) | Mining (N/A)
- **Parameters:** `symbol` (required), `sections` (optional: `overview`, `valuation`, `future`, `peers`, `financials`, `dividend`, `management`, `ownership` — comma-separated; default = all)
- **Returns:** JSON object with `symbol`, `company_name`, and the requested sections.
- **Equivalent REST:** `GET /v2/company/report/{symbol}/?sections=...` → see [`../rest/company-report.md`](../rest/)
- **Sample call:**
  ```json
  { "ticker": "BBCA", "sections": "overview" }
  ```
- **Sample response (truncated):**
  ```json
  {
    "symbol": "BBCA.JK",
    "company_name": "PT Bank Central Asia Tbk.",
    "overview": {
      "sector": "Financials",
      "sub_sector": "Banks",
      "market_cap": 887857728862500,
      "market_cap_rank": 2,
      "employee_num": 27937,
      "listing_date": "2000-05-31",
      "last_close_price": 7275,
      "indices": ["LQ45", "IDX30", "KOMPAS100", "IDXHIDIV20"]
    }
  }
  ```
- **Hackathon use:** Most flexible starting point for any "tell me about stock X" prompt. **Always pass `sections=` to save credits.**

### `fetch-company-segments`
- **Purpose:** Sankey-graph-ready revenue + cost segment breakdown for a financial year.
- **Coverage:** IDX only (some companies have segment data; check first).
- **Parameters:** `symbol` (required), `financial_year` (required, int)
- **Returns:** JSON with `revenue_segments[]` and `cost_segments[]`.
- **Equivalent REST:** `GET /v2/company/segments/{symbol}/{financial_year}/` → see [`../rest/company-segments.md`](../rest/)
- **Hackathon use:** Visually rich — perfect for a "where does this company make money" chart in Market Intelligence track.

### `fetch-listing-performance`
- **Purpose:** Price performance since IPO across 7d / 30d / 90d / 365d windows.
- **Coverage:** IDX only.
- **Parameters:** `symbol` (required)
- **Returns:** `{ "symbol": "GOTO.JK", "chg_7d": -0.0105, "chg_30d": -0.419, "chg_90d": -0.115, "chg_365d": -0.741 }` (fraction, not %)
- **Equivalent REST:** `GET /v2/ipo/listing-performance/{symbol}/` → see [`../rest/listing-performance.md`](../rest/)
- **Hackathon use:** Quick "which IPOs are hot" filter.

### `fetch-corporate-actions`
- **Purpose:** Splits, rights issues, warrants, bonus shares, AGM events, dividend history.
- **Coverage:** IDX only.
- **Parameters:** `symbol` (required)
- **Returns:** JSON list of actions with date and type.
- **Equivalent REST:** `GET /v2/company/corporate-actions/{symbol}/` → see [`../rest/corporate-actions.md`](../rest/)

### `fetch-shareholders-composition`
- **Purpose:** Monthly local vs foreign investor breakdown for a year.
- **Coverage:** IDX only.
- **Parameters:** `symbol` (required), `year` (required, int)
- **Returns:** Monthly composition `%`.
- **Equivalent REST:** `GET /v2/company/shareholders-composition/{symbol}/{year}/` → see [`../rest/shareholders-composition.md`](../rest/)
- **Hackathon use:** Spot retail-vs-foreign rotation.

---

## Market screening & rankings (IDX)

### `fetch-companies-by-subsector`
- **Purpose:** Filter and sort IDX companies — structured SQL-like or natural-language.
- **Coverage:** IDX (primary). SGX variant exists for SGX-only filtering.
- **Parameters:**
  - `q` (optional) — natural-language query, e.g. `"banks with PE < 10"`
  - `where` (optional) — SQL-like, e.g. `"sub_sector = 'banks'"`
  - `order_by` (optional) — `-market_cap`, `revenue[2024]`, `pe_ttm`, etc. **Prefix `-` for descending.**
  - `limit` (optional, 1–200, default 50)
- **Returns:** `results[]` with `symbol`, `company_name`, and the filtered fields. Includes `pagination{}` and `llm_translation{}` if `q` was used.
- **Equivalent REST:** `GET /v2/companies/?where=...&order_by=...` → see [`../rest/companies-screener.md`](../rest/)
- **Sample call:**
  ```json
  {
    "where": "sub_sector = 'banks'",
    "order_by": "-market_cap",
    "limit": 5
  }
  ```
- **Sample response (truncated):**
  ```json
  { "symbol": "BBCA.JK", "company_name": "PT Bank Central Asia Tbk.", "market_cap": 887857728862500 }
  ```
- **Hackathon use:** **The workhorse tool.** Every "find me..." prompt routes here. Use `where` for deterministic filtering, `q` for fuzzy NL.
- **Bracket notation:** `revenue[2024]` works inside `where`. Use it for time-series filters.

### `fetch-companies-top-changes`
- **Purpose:** Top gainers and losers across 1d / 7d / 14d / 30d / 365d periods.
- **Coverage:** IDX only.
- **Parameters:** `classifications` (required: `top_gainers`, `top_losers` — comma-separated), `periods` (required: `1d`, `7d`, `14d`, `30d`, `365d` — comma-separated), `sub_sector` (optional), `n_stock` (optional, default 10)
- **Returns:** JSON keyed by classification × period.
- **Equivalent REST:** `GET /v2/ranking/top-changes/?classifications=...&periods=...` → see [`../rest/top-changes.md`](../rest/)
- **Hackathon use:** "What moved today?" dashboards.

### `fetch-most-traded-stocks`
- **Purpose:** Most-traded IDX stocks by transaction volume over a date range.
- **Coverage:** IDX only.
- **Parameters:** `start` (required, `YYYY-MM-DD`), `end` (required, `YYYY-MM-DD`), `n_stock` (optional, default 20), `sub_sector` (optional)
- **Returns:** Results keyed by date with `symbol`, `company_name`, `volume`, `price`.
- **Equivalent REST:** `GET /v2/ranking/most-traded/?start=...&end=...` → see [`../rest/most-traded.md`](../rest/)
- **Max range:** 90 days per call.

### `fetch-close`
- **Purpose:** Closing price for **every** IDX ticker on a single trading day.
- **Coverage:** IDX only.
- **Parameters:** `date` (required, `YYYY-MM-DD`)
- **Returns:** Paginated array of `{symbol, company_name, close, ...}`.
- **Equivalent REST:** `GET /v2/transaction/close/{date}/` → see [`../rest/transaction-close.md`](../rest/)
- **Hackathon use:** **Universe feed.** One call beats ~900 per-symbol calls when you need breadth.

---

## Financial data (IDX)

### `fetch-quarterly-financials`
- **Purpose:** Quarterly income statement + balance sheet.
- **Coverage:** IDX only.
- **Parameters:** `symbol` (required), `n_quarters` (required, default 4), `report_date` (optional, `YYYY-Qn`)
- **Returns:** Quarterly rows. **Banks/insurance have extra fields:** `net_interest_income`, `gross_loan`, `total_deposit`.
- **Equivalent REST:** `GET /v2/company/quarterly-financials/{symbol}/?n_quarters=4` → see [`../rest/quarterly-financials.md`](../rest/)
- **Hackathon use:** Core input for any AI Agents track "analyze my stock" demo.

### `fetch-quarterly-financial-dates`
- **Purpose:** Available quarterly report dates for a single symbol, grouped by year.
- **Coverage:** IDX only.
- **Parameters:** `symbol` (required)
- **Returns:** `{ "2024": ["2024-Q1", "2024-Q2", ...], ... }`
- **Equivalent REST:** `GET /v2/company/quarterly-financial-dates/{symbol}/` → see [`../rest/quarterly-financial-dates.md`](../rest/)
- **Use this first** before calling `fetch-quarterly-financials` to discover the `report_date` values.

### `fetch-companies-quarterly-financial-dates`
- **Purpose:** Latest available report date for **every** IDX company — universe freshness feed.
- **Coverage:** IDX only.
- **Parameters:** `since` (optional, `YYYY-MM-DD`), `year` (optional, int)
- **Returns:** Paginated `{symbol, latest_report_date, quarter}` list.
- **Equivalent REST:** `GET /v2/companies/quarterly-financial-dates/?since=...` → see [`../rest/latest-quarterly-dates.md`](../rest/)
- **Hackathon use:** Drive a "what's new this week" cron cheaply. One call covers the whole IDX.

---

## Market indices & daily data (IDX)

### `fetch-index-daily`
- **Purpose:** Daily closing price for a market index over a date range.
- **Coverage:** IDX only.
- **Parameters:** `index_code` (required — see list below), `start` (required, `YYYY-MM-DD`), `end` (required, `YYYY-MM-DD`)
- **Available indices:** `ftse`, `idx30`, `idxbumn20`, `idxesgl`, `idxg30`, `idxhidiv20`, `idxq30`, `idxv30`, `jii70`, `kompas100`, `lq45`, `sminfra18`, `srikehati`, `economic30`, `idxvesta28`
- **Equivalent REST:** `GET /v2/transaction/index-daily/{index_code}/` → see [`../rest/index-daily.md`](../rest/)
- **Max range:** 90 days.

### `fetch-idx-market-cap`
- **Purpose:** Historical total IDX market capitalization.
- **Coverage:** IDX only.
- **Parameters:** `start` (required), `end` (required)
- **Returns:** Daily `{date, market_cap}` rows.
- **Equivalent REST:** `GET /v2/transaction/idx-total/` → see [`../rest/idx-total.md`](../rest/)

### `fetch-daily-transaction`
- **Purpose:** Daily close, volume, market cap for a single stock.
- **Coverage:** IDX only.
- **Parameters:** `symbol` (required), `start` (required), `end` (required)
- **Equivalent REST:** `GET /v2/transaction/daily/{symbol}/` → see [`../rest/transaction-daily.md`](../rest/)
- **Max range:** 90 days.

### `fetch-foreign-flow`
- **Purpose:** Daily net foreign-broker inflow (IDR) for a single stock.
- **Coverage:** IDX only.
- **Parameters:** `symbol` (required), `start` (required), `end` (required)
- **Returns:** Daily `{date, net_foreign_inflow}` rows. Positive = net foreign buying.
- **Equivalent REST:** `GET /v2/brokers/foreign-flow/{symbol}/` → see [`../rest/foreign-flow.md`](../rest/)
- **Hackathon use:** "Foreigners are buying X" — a clean signal for Market Intelligence track.

### `fetch-free-float`
- **Purpose:** Free float percentage for IDX companies, optionally filtered by sector taxonomy.
- **Coverage:** IDX only.
- **Parameters:** `sector` (optional), `sub_sector` (optional), `industry` (optional)
- **Returns:** Sorted by `free_float` descending.
- **Equivalent REST:** `GET /v2/screener/free-float/` → see [`../rest/free-float.md`](../rest/)

---

## Sector & industry classification (IDX)

### `get-subsectors`
- **Purpose:** List all sector/subsector pairs as kebab-case slugs.
- **Coverage:** IDX (also `fetch-sgx-subsectors`, `fetch-klse-sectors`).
- **Parameters:** none
- **Returns:** `[{ "sector": "Financials", "sub_sector": "banks" }, ...]`
- **Equivalent REST:** `GET /v2/subsectors/` → see [`../rest/subsectors.md`](../rest/)
- **Always call this first** to get canonical sub_sector values for `where=` clauses.

### `fetch-industries`
- **Purpose:** All subsector/industry pairs as kebab-case slugs.
- **Parameters:** none
- **Equivalent REST:** `GET /v2/industries/` → see [`../rest/industries.md`](../rest/)

### `fetch-subindustries`
- **Purpose:** All industry/sub-industry pairs.
- **Parameters:** none
- **Equivalent REST:** `GET /v2/subindustries/` → see [`../rest/subindustries.md`](../rest/)

### `fetch-subsector-report`
- **Purpose:** Aggregated metrics + company list for a subsector, with selectable sections.
- **Coverage:** IDX only.
- **Parameters:** `sub_sector` (required — kebab slug from `get-subsectors`), `sections` (optional — same section names as `fetch-company-report`)
- **Equivalent REST:** `GET /v2/subsector/report/{sub_sector}/?sections=...` → see [`../rest/subsector-report.md`](../rest/)
- **Hackathon use:** "Sector report card" demos — one call per subsector.

### `fetch-companies-with-segments`
- **Purpose:** Discovery of which companies have revenue/cost segment data, and for which years.
- **Coverage:** IDX only.
- **Parameters:** none
- **Returns:** `{symbol: [year, year, ...]}` map.
- **Equivalent REST:** `GET /v2/companies/?with_segments=true` / the `companies-segments-list` helper. → see [`../rest/companies-segments-list.md`](../rest/)

---

## News, filings & events (IDX)

### `fetch-news`
- **Purpose:** IDX and mining news, filterable by sector, symbol, tag, keyword, or date.
- **Coverage:** IDX + Mining (set `extension='mining'` for mining news).
- **Parameters:**
  - `extension` (required) — `"idx"` or `"mining"`
  - `sector` (optional)
  - `sub_sector` (optional)
  - `symbols` (optional, comma-separated)
  - `keyword` (optional)
  - `tags` (optional, comma-separated — fetch valid slugs via `fetch-tags`)
  - `start` (optional, `YYYY-MM-DD`)
  - `end` (optional, `YYYY-MM-DD`)
- **Returns:** Paginated news articles.
- **Equivalent REST:** `GET /v2/news/news/?extension=idx|mining&...` → see [`../rest/news.md`](../rest/)
- **Hackathon use:** RAG context, daily digest, sentiment scoring.

### `fetch-filings`
- **Purpose:** IDX insider trading buy/sell filings.
- **Coverage:** IDX only.
- **Parameters:** `symbol` (optional), `transaction_type` (optional: `buy` | `sell`), `holder_type` (optional), `sector` (optional), `start` (optional), `end` (optional)
- **Equivalent REST:** `GET /v2/news/filings/` → see [`../rest/filings.md`](../rest/)
- **Hackathon use:** Insider activity → "smart money" signal.

### `fetch-suspensions`
- **Purpose:** Historical IDX stock suspensions with date + official reason + PDF link.
- **Coverage:** IDX only.
- **Parameters:** `symbol` (optional), `start` (optional), `end` (optional)
- **Equivalent REST:** `GET /v2/news/suspensions/` → see [`../rest/suspensions.md`](../rest/)

### `fetch-tags`
- **Purpose:** All valid tag slugs for news/filings filter.
- **Parameters:** none
- **Equivalent REST:** `GET /v2/tags/` → see [`../rest/tags.md`](../rest/)

---

## Broker data (IDX)

### `fetch-brokers`
- **Purpose:** IDX broker registry with `origin` (foreign/domestic) and `cohort` (retail/mixed/institutional/unknown).
- **Parameters:** `origin` (optional), `cohort` (optional)
- **Returns:** List of brokers with codes and classifications.
- **Equivalent REST:** `GET /v2/brokers/registry/` → see [`../rest/broker-registry.md`](../rest/)

### `fetch-top-brokers`
- **Purpose:** Brokers ranked by gross trade value or net flow for a single date.
- **Parameters:** `date` (required), `metric` (required: `gross_value` | `n_abs_net_flow`), `n_brokers` (optional, default 20), `origin` (optional), `cohort` (optional)
- **Equivalent REST:** `GET /v2/brokers/top/` → see [`../rest/top-brokers.md`](../rest/)

### `fetch-broker-summary`
- **Purpose:** Per-broker daily trading rows for a single stock.
- **Parameters:** `symbol` (required), `broker_code` (required), `start` (required), `end` (required)
- **Returns:** Daily broker activity grouped by date.
- **Equivalent REST:** `GET /v2/brokers/broker-summary/{broker_code}/{symbol}/` → see [`../rest/broker-summary.md`](../rest/)
- **Max range:** 14 days.

### `fetch-broker-summary-top`
- **Purpose:** Top accumulating and distributing brokers for a single stock.
- **Parameters:** `symbol` (required), `start` (required), `end` (required), `n_brokers` (optional, default 20)
- **Returns:** `{top_buyers: [...], top_sellers: [...]}` ranked by net IDR.
- **Equivalent REST:** `GET /v2/brokers/broker-summary/top/{symbol}/` → see [`../rest/broker-summary-top.md`](../rest/)

### `fetch-broker-activity`
- **Purpose:** All stocks traded by a single broker over a date range.
- **Parameters:** `broker_code` (required), `symbol` (optional filter), `start` (required), `end` (required)
- **Equivalent REST:** `GET /v2/brokers/broker-activity/{broker_code}/` → see [`../rest/broker-activity.md`](../rest/)

### `fetch-broker-activity-top`
- **Purpose:** Top accumulations/distributions by a single broker.
- **Parameters:** `broker_code` (required), `start` (required), `end` (required)
- **Equivalent REST:** `GET /v2/brokers/broker-activity/top/{broker_code}/` → see [`../rest/broker-activity-top.md`](../rest/)

---

## Mining (IDX extension)

> Indonesian mining coverage is **unique to Sectors** — REST or MCP. Commodities, companies, sites, production, exports, licenses, and auctions from the ESDM Minerba portal. All money in USD millions.

### `fetch-mining-commodities`
- **Purpose:** List commodities with price-database coverage metadata.
- **Coverage:** Mining only.
- **Parameters:** none
- **Returns:** Array of commodity slugs + coverage info.
- **Equivalent REST:** `GET /v2/mining/commodities/` → see [`../rest/commodities.md`](../rest/)

### `fetch-mining-commodity-price`
- **Purpose:** Historical commodity price (monthly, up to 3 years).
- **Coverage:** Mining only.
- **Parameters:** `commodity_name` (required — slug from `fetch-mining-commodities`), `start_year` (required, int), `end_year` (required, int)
- **Returns:** Monthly price series.
- **Equivalent REST:** `GET /v2/mining/commodities/price/{commodity}/` → see [`../rest/commodity-price.md`](../rest/)

### `fetch-mining-global-commodity`
- **Purpose:** Global production, reserves, and trade by commodity + country.
- **Parameters:** `commodity_type` (optional), `country` (optional — **at least one required**)
- **Equivalent REST:** `GET /v2/mining/commodities/{commodity}/global/` → see [`../rest/global-commodity.md`](../rest/)

### `fetch-mining-companies`
- **Purpose:** Search mining companies by name, symbol, slug, commodity, or company type.
- **Parameters:** `keyword` (optional), `commodity_type` (optional), `company_type` (optional)
- **Equivalent REST:** `GET /v2/mining/companies/` → see [`../rest/mining-companies.md`](../rest/)

### `fetch-mining-company-detail`
- **Purpose:** Operational detail — activities, licenses, contracts, site count.
- **Parameters:** `slug` (required — from `fetch-mining-companies`)
- **Equivalent REST:** `GET /v2/mining/companies/{slug}/` → see [`../rest/mining-companies-detail.md`](../rest/)

### `fetch-mining-company-financials`
- **Purpose:** Annual financials in USD millions (assets, revenue, profit + breakdowns).
- **Parameters:** `slug` (required), `year` (optional — default latest)
- **Equivalent REST:** `GET /v2/mining/companies/{slug}/financials/` → see [`../rest/mining-companies-financials.md`](../rest/)

### `fetch-mining-company-ownership`
- **Purpose:** Corporate ownership tree — parents + subsidiaries with % stakes.
- **Parameters:** `slug` (required)
- **Equivalent REST:** `GET /v2/mining/companies/{slug}/ownership/` → see [`../rest/mining-companies-ownership.md`](../rest/)

### `fetch-mining-company-performance`
- **Purpose:** Production volume, sales, strip ratio, reserves for a year.
- **Parameters:** `slug` (required), `commodity_type` (optional), `year` (optional)
- **Equivalent REST:** `GET /v2/mining/companies/{slug}/performance/` → see [`../rest/mining-companies-performance.md`](../rest/)

### `fetch-mining-sites`
- **Purpose:** Mining sites with filters for location, commodity, production.
- **Parameters:** `commodity_type` (optional), `province` (optional), `year` (optional), `min_production` (optional)
- **Equivalent REST:** `GET /v2/mining/sites/` → see [`../rest/mining-sites.md`](../rest/)

### `fetch-mining-site-detail`
- **Purpose:** Full site detail with parsed resources/reserves and lat/long.
- **Parameters:** `slug` (required)
- **Equivalent REST:** `GET /v2/mining/sites/{slug}/` → see [`../rest/mining-site-detail.md`](../rest/)

### `fetch-mining-total-production`
- **Purpose:** National total production for a commodity across all years (YoY %).
- **Parameters:** `commodity_type` (required)
- **Equivalent REST:** `GET /v2/mining/sites/commodity-production/` → see [`../rest/commodity-production.md`](../rest/)

### `fetch-mining-exports`
- **Purpose:** Top export destinations by country for a commodity + year.
- **Parameters:** `commodity_type` (required), `year` (required)
- **Equivalent REST:** `GET /v2/mining/commodities/{commodity}/exports/` → see [`../rest/export-destination.md`](../rest/)

### `fetch-mining-sales-destination`
- **Purpose:** Revenue + volume by destination country for a mining company.
- **Parameters:** `slug` (required), `year` (optional)
- **Equivalent REST:** `GET /v2/mining/commodities/sales-destination/{slug}/` → see [`../rest/sales-destination.md`](../rest/)

### `fetch-mining-contracts`
- **Purpose:** Active mining contracts linking mine owners to contractors.
- **Parameters:** `mine_owner` (optional slug), `contractor` (optional slug)
- **Equivalent REST:** `GET /v2/mining/contracts/` → see [`../rest/mining-contracts.md`](../rest/)

### `fetch-mining-licenses`
- **Purpose:** Mining licenses (IUP/IUPK) — ESDM Minerba portal.
- **Parameters:** `commodity_type` (optional), `province` (optional), `license_type` (optional), `expiring_soon` (optional bool)
- **Equivalent REST:** `GET /v2/mining/licenses/` → see [`../rest/mining-licenses.md`](../rest/)

### `fetch-mining-license-auctions`
- **Purpose:** Mining license auctions — list with status filter.
- **Parameters:** `commodity_type` (optional), `province` (optional), `status` (optional: `open` | `closed`)
- **Equivalent REST:** `GET /v2/mining/license-auctions/` → see [`../rest/mining-license-auctions.md`](../rest/)

### `fetch-mining-license-auction-detail`
- **Purpose:** Full auction record including phases timeline + participant list.
- **Parameters:** `wiup_code` (required)
- **Equivalent REST:** `GET /v2/mining/license-auctions/{wiup_code}/` → see [`../rest/mining-license-auctions-detail.md`](../rest/)

### `fetch-mining-resources-reserves`
- **Purpose:** Discovery index of available resources/reserves data by province + commodity.
- **Parameters:** none
- **Equivalent REST:** `GET /v2/mining/sites/commodity-resources-reserves/` → see [`../rest/commodity-resources-reserves.md`](../rest/)

### `fetch-mining-resources-reserves-detail`
- **Purpose:** Resources/reserves data for a province, nested by year then commodity.
- **Parameters:** `province` (required), `commodity_type` (required), `year` (required)
- **Returns:** `exploration_target`, `total_inventory`, `resources`, `reserves`, `unit` per commodity.
- **Equivalent REST:** `GET /v2/mining/sites/commodity-resources-reserves-detail/` → see [`../rest/commodity-resources-reserves-detail.md`](../rest/)

---

## Singapore (SGX — FYI)

> Not deep-dived for this hackathon (Indonesian-only). Cross-link to the docs if a team member needs them.

| Tool | Description | Key parameters |
|------|-------------|----------------|
| `fetch-sgx-sectors` | All SGX sector slugs | — |
| `fetch-sgx-subsectors` | All SGX sector/subsector pairs | — |
| `fetch-sgx-company-report` | SGX company report (overview, valuation, financials, dividend) | `symbol`, `sections` |
| `fetch-sgx-companies-by-sector` | SGX companies in a given sector | `sector` |
| `fetch-sgx-top-companies` | Top SGX by dividend yield / revenue / earnings / market cap / PE | `classifications`, `sector` |
| `fetch-sgx-daily-transaction` | Daily close + volume for an SGX stock | `symbol`, `start`, `end` |
| `fetch-sgx-filings` | SGX insider trading buy/sell filings | `symbol`, `transaction_type`, `holder_type`, `start`, `end` |
| `fetch-sgx-news` | SGX news, filterable by sector / symbol / tag | `sector`, `symbols`, `tags`, `start`, `end` |
| `fetch-sgx-buybacks` | SGX share buyback records | `symbol`, `start`, `end` |
| `fetch-sgx-short-sell` | SGX short sell data | `symbol`, `start`, `end` |
| `fetch-sgx-tags` | All valid tag slugs for SGX news | — |

Full reference: https://docs.sectors.app/recipes/sectors-for-ai-agents/00-sectors-mcp-guide#tools-reference (search "Singapore (SGX)").

---

## Malaysia (KLSE — FYI)

> Thin coverage — basic company report and sector data only. Not in scope for this hackathon.

| Tool | Description | Key parameters |
|------|-------------|----------------|
| `fetch-klse-sectors` | All KLSE sector slugs | — |
| `fetch-klse-company-report` | KLSE company report (overview, valuation, financials, dividend) | `symbol`, `sections` |
| `fetch-klse-companies-by-sector` | KLSE companies in a given sector | `sector` |
| `fetch-klse-top-companies` | Top KLSE by dividend yield / revenue / earnings / market cap / PE | `classifications`, `sector` |

Full reference: https://docs.sectors.app/recipes/sectors-for-ai-agents/00-sectors-mcp-guide#tools-reference (search "Malaysia (KLSE)").

---

## IDX + Mining tool-count breakdown

| Domain | Tool count | Notes |
|--------|-----------:|-------|
| Company analysis (IDX) | 5 | `fetch-company-report`, `fetch-company-segments`, `fetch-listing-performance`, `fetch-corporate-actions`, `fetch-shareholders-composition` |
| Market screening & rankings (IDX) | 4 | `fetch-companies-by-subsector`, `fetch-companies-top-changes`, `fetch-most-traded-stocks`, `fetch-close` |
| Financial data (IDX) | 3 | `fetch-quarterly-financials`, `fetch-quarterly-financial-dates`, `fetch-companies-quarterly-financial-dates` |
| Market indices & daily data (IDX) | 5 | `fetch-index-daily`, `fetch-idx-market-cap`, `fetch-daily-transaction`, `fetch-foreign-flow`, `fetch-free-float` |
| Sector & industry classification (IDX) | 5 | `get-subsectors`, `fetch-industries`, `fetch-subindustries`, `fetch-subsector-report`, `fetch-companies-with-segments` |
| News, filings & events (IDX) | 4 | `fetch-news` (extension=idx), `fetch-filings`, `fetch-suspensions`, `fetch-tags` |
| Broker data (IDX) | 6 | `fetch-brokers`, `fetch-top-brokers`, `fetch-broker-summary`, `fetch-broker-summary-top`, `fetch-broker-activity`, `fetch-broker-activity-top` |
| **IDX total** | **32** | |
| Mining (IDX extension) | 20 | commodities (3) + companies (5) + sites (2) + production/exports (3) + licenses/auctions (3) + resources/reserves (2) + contracts (1) + sales-destination (1) |
| **Mining total** | **20** | |
| SGX (FYI) | 11 | |
| KLSE (FYI) | 4 | |
| **Grand total** | **67** | matches guide's "65+ tools" |

> The `fetch-news` tool counts once even though it serves both `extension=idx` and `extension=mining`. Mining news is the second usage of the same MCP tool.

---

## Cross-links to REST references (Lane 1 — IDX + Mining only)

Every IDX and Mining tool above maps to a REST endpoint documented in [`../rest/`](../rest/) (owned by Lane 1, IDX + Mining only). SGX/KLSE REST endpoints exist at `https://api.sectors.app/v2/sgx/...` and `/v2/klse/...` but are not deep-dived here.

When to prefer MCP over REST:
- Conversational / agent workflows (Claude Code, Cursor, etc.) → MCP
- Cron jobs, dashboards, scripts, n8n flows → REST (cheaper, easier to cache)

When to prefer REST over MCP:
- Anything that doesn't need an LLM in the loop.
- Per-endpoint cost visibility — REST logs the call directly.

---

## See also

- [setup.md](./setup.md) — install + troubleshoot
- [claude-integration.md](./claude-integration.md) — OAuth setup for Claude
- [chatgpt-integration.md](./chatgpt-integration.md) — OAuth setup for ChatGPT
- [`../sectors-api-and-mcp.md`](../sectors-api-and-mcp.md) — REST vs MCP cheat sheet
- [`../recipes/01-generative-ai-bg.md`](../recipes/01-generative-ai-bg.md) … [`06-memory-agents.md`](../recipes/06-memory-agents.md) — agent patterns
