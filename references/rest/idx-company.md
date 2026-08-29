# IDX — Per-Company Reports

> **Lane 1 — IDX + Mining ONLY.** Sectors Financial API v2 reference for IDX
> per-company reports, revenue segments, corporate actions, shareholders
> composition, and IPO listing performance. Source docs:
> `https://docs.sectors.app/api-references/v2/indonesia/...` (verified 29 Aug 2026).

All endpoints live under `https://api.sectors.app/v2/`. Auth is a raw API key in the `Authorization` header (no `Bearer ` prefix).

> **IDX symbol convention**: 4 letters, optionally followed by `.jk` (case-insensitive). E.g. `BBCA`, `BMRI`, `TLKM`, `BREN`. All paths accept either form.

---

### `GET /v2/company/report/{symbol}/` — Company Report

- **Purpose:** Comprehensive company report organized into 8 distinct sections. By default ALL sections are included. Use `sections=` to request only the data you need and reduce response size.
- **Hackathon applicability:** **ai-agents** (primary), **market-intel** (deep dives). The single most useful endpoint for stock-picker agents.

#### Available sections

| Section | Content |
|---|---|
| `overview` | Listing board, industry/sector/subsector, market cap, address, employee count, ESG score, tags, indices, affiliates, price history (YTD/52w/90d/all-time). |
| `valuation` | Latest close, daily change, forward PE, intrinsic value, historical PB/PE/PS/PCF/PEG by year (+ peer averages, EV/EBITDA, EV/revenue). |
| `future` | Analyst value/growth forecasts (EPS/revenue estimate by year) + analyst rating breakdown (strong_buy / buy / hold / sell / strong_sell / n_analyst). |
| `financials` | EPS, historical EPS, historical financials (revenue, earnings, ebit, ebitda, total_assets, total_equity, free_cash_flow, etc.) per year, ratios (gross/operating/net margin, ROA, ROE, ROIC, current ratio, asset turnover), YoY quarter growth. |
| `dividend` | Historical dividends by year with breakdown (date, total, yield), upcoming dividends, yield TTM, payout ratio, last ex-dividend date. |
| `management` | Key executives with their position + shareholdings (name, share_amount, share_percentage). |
| `ownership` | Major shareholders (name, share_value, share_amount, share_percentage), top institutional transactions, top buyers/sellers, institutional flow, whale investors, conglomerate group. |
| `peers` | Peer comparison within the same subsector — each peer has year, group_self marker, pb_mrq, pe_ttm, market_cap, net_income, total_assets/equity/revenue, operating_expense, point_summaries (scoring breakdown). |

#### Path + query parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `symbol` | path | required | IDX ticker. E.g. `BREN`, `BBCA`. |
| `sections` | array | all 8 | Comma-separated subset. Allowed: `dividend`, `financials`, `future`, `management`, `overview`, `ownership`, `peers`, `valuation`. |

#### Sample request

```bash
curl -G "https://api.sectors.app/v2/company/report/BBCA/" \
  -H "Authorization: <api-key>" \
  --data-urlencode "sections=overview,valuation,dividend"
```

```python
import requests
r = requests.get(
    "https://api.sectors.app/v2/company/report/BBCA/",
    headers={"Authorization": "<api-key>"},
    params={"sections": "overview,valuation,dividend"},
    timeout=30,
)
r.raise_for_status()
```

#### Sample response (BBCA, full payload truncated)

```json
{
  "symbol": "BBCA.JK",
  "company_name": "PT Bank Central Asia Tbk.",
  "overview": {
    "listing_board": "Main", "industry": "Banks", "sub_industry": "Banks",
    "sector": "Financials", "sub_sector": "Banks",
    "market_cap": 753611199412500, "market_cap_rank": 1,
    "address": "Menara BCA, Grand Indonesia\r\nJalan MH Thamrin No. 1\r\nJakarta 10310",
    "employee_num": 27937, "employee_num_rank": 15,
    "listing_date": "2000-05-31", "website": "www.bca.co.id",
    "phone": "021-23588000", "email": "investor_relations@bca.co.id",
    "last_close_price": 6175, "latest_close_date": "2026-07-08",
    "daily_close_change": -0.0198412698412698,
    "all_time_price": {
      "ytd_low": {"2026-06-09": 4820}, "52_w_low": {"2026-06-09": 4820},
      "ytd_high": {"2026-01-06": 8175}, "52_w_high": {"2025-08-13": 8975},
      "all_time_low": {"2004-06-08": 175}, "all_time_high": {"2024-09-23": 10950}
    },
    "esg_score": 21.44,
    "tags": ["dividend-yield-ttm-above-5-percent", "esg-under-25", "top-90d-transaction-value"],
    "indices": ["IDXESGL", "ECONOMIC30", "IDXG30", "IDX30", "LQ45", "FTSE", "SRIKEHATI", "KOMPAS100", "IDXHIDIV20", "IDXQ30"],
    "affiliates": ["Djarum", "Hartono"]
  },
  "dividend": {
    "historical_dividends": {
      "2026": { "breakdown": [{"date": "2026-06-17", "total": 20, "yield": 0.00323886639676113}], "total_yield": 0.0487449392712551, "total_dividend": 301 }
    },
    "upcoming_dividends": null,
    "yield_ttm": 0.0576518218623482, "dividend_ttm": 356,
    "payout_ratio": 0.748637602001087, "cash_payout_ratio": 0.687782037617804,
    "last_ex_dividend_date": "2026-06-17"
  }
}
```

#### Gotchas

- **Costs 1 credit per section** requested. Default (all 8 sections) = **8 credits**. ALWAYS pass `sections=` to control cost.
- For a fund manager agent: `overview,valuation,dividend` = 3 credits per call. Sufficient for most "should I buy this?" questions.
- For a deep dive: add `financials,ownership` (5 credits).
- Peer comparison (`peers`) is the most expensive per-symbol call outside of full financials; useful for relative-value ranking within a subsector.
- `400 InvalidSymbol` for missing/invalid symbol. `404` for valid-format but unknown ticker (1 credit).

---

### `GET /v2/company/get-segments/{symbol}/` — Company Revenue Segments

- **Purpose:** Sankey-graph-ready revenue and cost segment breakdown for one company and one financial year.
- **Hackathon applicability:** **market-intel** (visual dashboards), **ai-agents** (revenue mix queries).

#### Path + query parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `symbol` | path | required | E.g. `BUMI`, `TLKM`, `ASII`. |
| `financial_year` | integer | latest available | 1900–2026. |

> **Important**: Not all companies have segment data. Call [`/v2/companies/list_companies_with_segments/`](./idx-screener.md#get-v2companieslist_companies_with_segments--companies-with-revenue-segments) FIRST to check availability and valid years.

#### Sample request

```bash
curl -G "https://api.sectors.app/v2/company/get-segments/BBCA/" \
  -H "Authorization: <api-key>" \
  --data-urlencode "financial_year=2025"
```

#### Sample response (banking-style)

```json
{
  "symbol": "BBCA.JK",
  "financial_year": 2025,
  "revenue_breakdown": [
    { "value": 67446394000000, "source": "Loans", "target": "Interest Income" }
  ]
}
```

For non-financial companies the breakdown is segment-name → segment-name (e.g. `Palm Oil → Revenue`, `Plantation → COGS`).

#### Gotchas

- Costs 1 credit.
- `404 Invalid stock symbol and/or data for the specified financial year does not exist.` charges 1 credit (per docs).
- `400 Please provide a valid financial year.` is free.
- Default response uses the latest available year — specify `financial_year` if comparing across years.

---

### `GET /v2/company/corporate-actions/{symbol}/` — Corporate Actions

- **Purpose:** All corporate action history for one IDX company: stock splits, right issues, warrants, bonus shares, AGM events, **upcoming dividends**, historical dividends.
- **Hackathon applicability:** **ai-agents** (dividend calendar, split detection), **market-intel** (catalyst surfacing).

#### Path parameters

| Name | Type | Notes |
|---|---|---|
| `symbol` | string | IDX symbol, `.jk` optional. E.g. `BBCA`, `BMRI`. |

#### Sample request

```bash
curl "https://api.sectors.app/v2/company/corporate-actions/BBCA/" \
  -H "Authorization: <api-key>"
```

#### Sample response

```json
{
  "symbol": "BBCA.JK",
  "corporate_actions": {
    "agm": [
      { "agm_date": "2025-03-12", "agm_time": "09:30:00",
        "agm_place": "Menara Bca, Grand Indonesia, Jl. M. H. Thamrin No. 1, Jakarta 10310 Kota Adm. Jakarta Pusat",
        "agm_result": null }
    ],
    "bonus": null, "warrant": null,
    "dividend": [
      { "ex_date": "2025-12-03", "payment_date": "2025-12-22",
        "dividend_yield": 0.00641717, "dividend_amount": 55 }
    ],
    "right_issue": null,
    "stock_split": [ { "date": "2021-10-13", "split_ratio": 5 } ],
    "upcoming_dividend": null
  }
}
```

#### Gotchas

- Costs 1 credit.
- Each category (`dividend`, `upcoming_dividend`, `stock_split`, `right_issue`, `warrant`, `bonus`, `agm`) is a separate array — `null` when empty (not omitted).
- For `upcoming_dividend`: announced but ex-date hasn't passed yet. Use this for forward-looking dividend yield calendars.

---

### `GET /v2/company/shareholders-composition/{symbol}/` — Shareholders Composition

- **Purpose:** Monthly shareholder composition snapshots for one IDX company within a single calendar year, broken down by investor category (insurance, corporate, pension fund, financial institutions, individual, mutual fund, securities companies, foundation, other) for both **local** (`_l`) and **foreign** (`_f`) investors.
- **Hackathon applicability:** **ai-agents** (foreign-flow sentiment), **market-intel** (ownership drift over time).

#### Path + query parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `symbol` | path | required | E.g. `BBCA`, `BMRI`. |
| `year` | integer | current year | 1900–2026. **Data only available from 2021 onwards** — earlier years return empty `data`. Future years rejected. |

#### Sample request

```bash
curl -G "https://api.sectors.app/v2/company/shareholders-composition/BBCA/" \
  -H "Authorization: <api-key>" \
  --data-urlencode "year=2026"
```

#### Sample response

```json
{
  "symbol": "BBCA.JK", "year": 2026,
  "data": [
    {
      "date": "2026-06-30", "shares_number": 123275050000,
      "insurance_l": 2347930190, "corporate_l": 676811585,
      "pension_fund_l": 326033400, "financial_institutions_l": 437363600,
      "individual_l": 11100401696, "mutual_fund_l": 1218211444,
      "securities_companies_l": 109436679, "foundation_l": 73544460,
      "other_l": 14203600, "total_l": 16303936654,
      "insurance_f": 551962796, "corporate_f": 1223361552,
      "pension_fund_f": 5139363015, "financial_institutions_f": 2811510529,
      "individual_f": 326180480, "mutual_fund_f": 19268413209,
      "securities_companies_f": 558727363, "foundation_f": 298788705,
      "other_f": 5971446817, "total_f": 36149754466,
      "numbers_of_shareholders": 797115, "change_in_shareholders": 29745
    }
  ]
}
```

#### Gotchas

- Costs 1 credit.
- Each row = end-of-month snapshot. To get a full year → call once per year.
- Foreign-investor sentiment tracking: monitor `total_f` trend month-over-month (rising = net foreign buying).
- The `change_in_shareholders` field is net change vs previous snapshot (NOT absolute count of trades).

---

### `GET /v2/listing-performance/{symbol}/` — Company IPO & Listing Performance

- **Purpose:** Price change percentages since listing date for one IDX ticker, across 7, 30, 90, and 365-day windows. Also includes full IPO metadata (book-building range, offering price, distribution date, prospectus URL).
- **Hackathon applicability:** **market-intel** (recent IPO performance), **ai-agents** (post-IPO momentum scanner).

#### Path parameters

| Name | Type | Notes |
|---|---|---|
| `symbol` | string | E.g. `ARTO`, `BREN`, `GOTO`. |

#### Sample request

```bash
curl "https://api.sectors.app/v2/listing-performance/BREN/" \
  -H "Authorization: <api-key>"
```

#### Sample response

```json
{
  "symbol": "BREN.JK",
  "chg_7d": 2.52564, "chg_30d": 4.64103,
  "chg_90d": 8.26282, "chg_365d": 7.58974,
  "company_name": "PT Barito Renewables Energy Tbk.",
  "listing_date": null,
  "shares_offered": 4015000000, "percent_total_shares": 0.03,
  "book_building_start_date": "2023-09-18", "book_building_end_date": "2023-09-25",
  "book_building_lower_bound": 670, "book_building_upper_bound": 780,
  "offering_start_date": "2023-10-03", "offering_end_date": "2023-10-05",
  "offering_price": 780, "distribution_date": "2023-10-06",
  "prospectus_url": "https://e-ipo.co.id/en/pipeline/get-prospectus-file?id=266&type=",
  "additional_info_url": "https://e-ipo.co.id/en/pipeline/get-additional-info?id=266"
}
```

#### Gotchas

- Costs 1 credit.
- **Only available for tickers listed after May 2005.** Pre-2005 listings → 404.
- `chg_*` values are decimals (multiplier, not percent): `chg_7d: 2.52564` = +252.564% from listing date.
- `listing_date: null` is possible — the symbol exists but the actual listing date wasn't captured.
- `prospectus_url` and `additional_info_url` point to the official e-IPO portal (`e-ipo.co.id`).

---

## Cross-references

- TOC anchor: [`sectors-api-and-mcp.md`](../sectors-api-and-mcp.md)
- Screener + helper lists: [`idx-screener.md`](./idx-screener.md)
- Financials + daily transactions: [`idx-financials-transactions.md`](./idx-financials-transactions.md)
- Rankings, brokers, news: [`idx-rankings-brokers-news.md`](./idx-rankings-brokers-news.md)
