# IDX — Rankings, Brokers, News & Filings

> **Lane 1 — IDX + Mining ONLY.** Sectors Financial API v2 reference for IDX
> market rankings (movers, most-traded), broker activity (per-broker / per-symbol
> / top-N / foreign flow), insider filings, news articles, and stock suspensions.
> Source docs: `https://docs.sectors.app/api-references/v2/indonesia/...`
> (verified 29 Aug 2026).

All endpoints live under `https://api.sectors.app/v2/`. Auth is a raw API key in the `Authorization` header (no `Bearer ` prefix).

> **IDX symbol convention**: 4 letters, optionally followed by `.jk` (case-insensitive). E.g. `BBCA`, `BMRI`, `TLKM`.
>
> **Broker code convention**: two-letter IDX exchange-member identifier. E.g. `MG`, `AK`, `CC`, `YP`, `BK`, `KZ`. Get the full list from [`/v2/brokers/`](#get-v2brokers--broker-registry).

---

## A. Rankings

### `GET /v2/companies/top-changes/` — Top Company Movers

- **Purpose:** Top gainers and losers across multiple time periods. Two classifications (`top_gainers`, `top_losers`) × five periods (`1d`, `7d`, `14d`, `30d`, `365d`).
- **Hackathon applicability:** **market-intel** (momentum dashboards), **ai-agents** (catch-the-winner scanners).

#### Query parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `classifications` | array | both | `top_gainers`, `top_losers` (comma-separated). |
| `periods` | array | all 5 | `1d`, `7d`, `14d`, `30d`, `365d` (comma-separated). |
| `n_stock` | integer | 5 | Per period. 1–10. |
| `sub_sector` | string | — | kebab-case. E.g. `banks`. |
| `min_mcap_billion` | integer | 5000 | Minimum market cap in billion IDR. Set to `0` to disable. |

#### Sample request

```bash
curl -G "https://api.sectors.app/v2/companies/top-changes/" \
  -H "Authorization: <api-key>" \
  --data-urlencode "classifications=top_gainers" \
  --data-urlencode "periods=1d,7d" \
  --data-urlencode "n_stock=5"
```

#### Sample response (truncated)

```json
{
  "top_gainers": {
    "1d": [
      { "name": "PT Nitrasanata Dharma Tbk", "symbol": "JECX.JK", "price_change": 0.25,
        "last_close_price": 1950, "latest_close_date": "2026-07-08" }
    ],
    "7d": [
      { "name": "PT Samator Indo Gas Tbk", "symbol": "AGII.JK", "price_change": 0.232,
        "last_close_price": 3080, "latest_close_date": "2026-07-08" }
    ]
  },
  "top_losers": {
    "1d": [
      { "name": "Sentul City Tbk", "symbol": "BKSL.JK", "price_change": -0.0895522388059701,
        "last_close_price": 61, "latest_close_date": "2026-07-08" }
    ]
  }
}
```

#### Gotchas

- **Costs 1 credit per `classification × period` combination.** Default (2 × 5) = **10 credits**.
- `price_change` is a decimal multiplier (`0.25` = +25%, NOT 0.25%). Positive = gainer, negative = loser.
- Default `min_mcap_billion=5000` filters micro-caps. Override to `0` for penny stocks.
- Per docs, invalid classification → 400 (free). Invalid period → 400 (free).

---

### `GET /v2/most-traded/` — Most Traded Stocks

- **Purpose:** Most traded IDX stocks by transaction volume over a date range up to 90 days. Results keyed by date.
- **Hackathon applicability:** **market-intel** (liquidity heatmaps), **automation** (volume anomaly jobs).

#### Query parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `start` | string (date) | 30 days before `end` | `YYYY-MM-DD`. |
| `end` | string (date) | today | Future → 400. |
| `sub_sector` | string | — | kebab-case. |
| `adjusted` | boolean | `false` | `true` = rank by `volume × close` (turnover), `false` = rank by raw `volume`. |
| `n_stock` | integer | 5 | Per day. 1–10. |

#### Sample request

```bash
curl -G "https://api.sectors.app/v2/most-traded/" \
  -H "Authorization: <api-key>" \
  --data-urlencode "start=2025-05-02" \
  --data-urlencode "end=2025-05-02" \
  --data-urlencode "n_stock=3"
```

#### Sample response

```json
{
  "2025-05-02": [
    { "symbol": "GOTO.JK", "company_name": "PT GoTo Gojek Tokopedia Tbk", "volume": 2627450200, "price": 82 },
    { "symbol": "DEWA.JK", "company_name": "Darma Henwa Tbk", "volume": 1563426700, "price": 138 },
    { "symbol": "BUMI.JK", "company_name": "Bumi Resources Tbk", "volume": 1012962400, "price": 112 }
  ]
}
```

#### Gotchas

- **Costs 2 credits** per call (more than the usual 1 — flagged in docs).
- `adjusted=true` gives turnover-ranked (better for liquidity-aware screens).
- Output is a date-keyed dictionary → iterate `results.items()` for each day.

---

## B. News & Filings

### `GET /v2/filings/` — Company Filings (Insider Trading)

- **Purpose:** IDX insider trading filings — buy/sell transactions by company insiders and major shareholders.
- **Hackathon applicability:** **ai-agents** (insider-cluster detection), **market-intel** (sentiment catalysts).

#### Query parameters

| Name | Type | Notes |
|---|---|---|
| `symbol` | string | IDX ticker filter. |
| `sector` | string | kebab-case sector slug. |
| `sub_sector` | string | kebab-case subsector slug. |
| `tags` | string | Comma-separated tag slugs. |
| `transaction_type` | enum | `buy`, `sell`, or `others`. |
| `holder_type` | enum | `insider`, `institution`, `corporate-investor`. |
| `start`, `end` | date | Optional bounds on `timestamp`. |
| `limit` | integer | 1–30. Default 20. |
| `offset` | integer | Default 0. |

#### Sample request

```bash
curl -G "https://api.sectors.app/v2/filings/" \
  -H "Authorization: <api-key>" \
  --data-urlencode "transaction_type=buy" \
  --data-urlencode "holder_type=insider" \
  --data-urlencode "limit=20"
```

#### Sample response

```json
{
  "results": [
    {
      "title": "Samuel Sekuritas Indonesia buys shares of Nusantara Sawit Sejahtera",
      "body": "This is Samuel Sekuritas Indonesia's 5th insider purchase in the last 6 months...",
      "source": "https://www.idx.co.id/StaticData/NewsAndAnnouncement/ANNOUNCEMENTSTOCK/From_KSEI/LK-09072026-5264-00.pdf-0.pdf-0.pdf",
      "timestamp": "2026-07-09T14:29:39",
      "sector": "consumer-non-cyclicals",
      "sub_sector": "food-beverage",
      "tags": ["placement", "repurchase-agreement"],
      "symbol": "NSSS.JK",
      "transaction_type": "buy",
      "holder_type": "institution",
      "holder_name": "Samuel Sekuritas Indonesia",
      "holding_before": 9559919000, "holding_after": 10169179100,
      "amount_transaction": 609260100, "price": 576.478,
      "transaction_value": 351225097500,
      "price_transaction": [{ "date": "2026-07-07", "type": "buy", "price": 580, "amount_transacted": 180108000 }],
      "share_percentage_before": 40.17, "share_percentage_after": 42.73,
      "share_percentage_transaction": 2.56,
      "idx_investor_slug": null,
      "idx_conglomerates_group_slug": null
    }
  ],
  "pagination": { "total_count": 3016, "showing": 1, "limit": 2, "offset": 0,
    "has_next": true, "has_previous": false, "next_offset": 2, "previous_offset": null }
}
```

#### Gotchas

- **Costs 1 credit** per call.
- The `source` URL is the **official IDX PDF notice** (`idx.co.id`). Perfect for source-of-truth citation.
- `price_transaction` is a list — multiple trades in one filing. Aggregate `amount_transacted` for total volume.
- Filter combinations are AND-ed.

---

### `GET /v2/news/` — News Articles

- **Purpose:** Paginated news articles from either the IDX or mining news sources. Use `extension=` to choose.
- **Hackathon applicability:** **market-intel** (news-driven alerts), **ai-agents** (catalyst detection).

#### Query parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `extension` | enum | `idx` | `idx` or `mining`. |
| `sector` | string | — | **IDX only.** Comma-separated kebab-case. |
| `sub_sector` | string | — | **IDX only.** |
| `tags` | string | — | **IDX only.** Comma-separated tag slugs. |
| `symbols` | string | — | **IDX only.** Comma-separated tickers. E.g. `BBCA,BBRI`. |
| `keyword` | string | — | Case-insensitive substring match on title. Both extensions. |
| `commodity_type` | enum | — | **Mining only.** `Bauxite`, `Coal`, `Copper`, `Gold`, `Iron`, `Nickel`, `Non-Metallic Mineral`, `Sand, Stone, Gravel`, `Tin`. |
| `start`, `end` | date | — | Optional bounds on `timestamp`. |
| `limit` | integer | 20 | 1–30. |
| `offset` | integer | 0 | Pagination. |

#### Sample request

```bash
curl -G "https://api.sectors.app/v2/news/" \
  -H "Authorization: <api-key>" \
  --data-urlencode "extension=idx" \
  --data-urlencode "symbols=BBCA,BBRI" \
  --data-urlencode "keyword=dividend"
```

#### Sample response

```json
{
  "results": [
    {
      "title": "OJK says Henry Surya's false statements delayed the investigation...",
      "body": "The Financial Services Authority (OJK) said Henry Surya's lies prolonged...",
      "source": "https://money.kompas.com/read/2026/07/09/180504926/...",
      "thumbnail": "https://asset.kompas.com/crops/.../230x152/data/photo/.../6a4f38026d694.jpg",
      "timestamp": "2026-07-09T18:05:00",
      "sector": "financials",
      "sub_sector": ["insurance"],
      "tags": ["Violation", "Risk & Compliance", "Politics & Regulation", "Bearish"],
      "symbols": [],
      "dimension": { "future": 0, "dividend": 0, "ownership": 0, "technical": 0,
                     "valuation": 0, "financials": 0, "management": 0, "sustainability": 0 }
    }
  ],
  "pagination": { "total_count": 8665, "showing": 1, "limit": 2, "offset": 0,
    "has_next": true, "has_previous": false, "next_offset": 2, "previous_offset": null }
}
```

#### Gotchas

- **Costs 1 credit** per call.
- **Mixing IDX and mining params returns 400.** Example: `extension=mining` + `sector=...` → invalid.
- `dimension` (IDX only): categorical 0/1 scores for 8 analysis dimensions — useful for "tag-the-news-by-theme" workflows.
- `symbols` may be empty `[]` if article is sector-wide.

---

### `GET /v2/suspensions/` — Stock Suspensions

- **Purpose:** Historical IDX stock suspensions with date, official reason, and link to the IDX PDF notice.
- **Hackathon applicability:** **market-intel** (compliance dashboard), **automation** (halt alerts).

#### Query parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `symbol` | string | — | Single-ticker suspension history. |
| `start`, `end` | date | — | Optional bounds on `suspension_date`. |
| `limit` | integer | 20 | 1–30. |
| `offset` | integer | 0 | Pagination. |

#### Sample request

```bash
curl -G "https://api.sectors.app/v2/suspensions/" \
  -H "Authorization: <api-key>" \
  --data-urlencode "symbol=FLMC"
```

#### Sample response

```json
{
  "results": [
    {
      "symbol": "FLMC.JK",
      "suspension_date": "2026-07-03",
      "reason": "Terjadinya penurunan harga kumulatif yang signifikan pada saham FLMC.JK",
      "pdf_url": "https://www.idx.co.id/Portals/0/StaticData/NewsAndAnnouncement/ANNOUNCEMENTSTOCK/Exchange/2026/JUL/20260702-WAS_Suspensi_FLMC.pdf"
    }
  ],
  "pagination": { "total_count": 556, "showing": 1, "limit": 2, "offset": 0,
    "has_next": true, "has_previous": false, "next_offset": 2, "previous_offset": null }
}
```

#### Gotchas

- **Costs 1 credit** per call.
- `reason` is in Bahasa Indonesia — translate before displaying to non-ID audiences.
- `pdf_url` is the **official IDX notice** (`idx.co.id`).

---

## C. Brokers

### `GET /v2/brokers/` — Broker Registry

- **Purpose:** Curated registry of IDX exchange-member brokers with name, origin (`foreign`/`domestic`), cohort, and license type. Authoritative source for valid broker codes.
- **Hackathon applicability:** **all tracks** — feed `broker_code` parameters in the per-broker endpoints.

#### Query parameters

| Name | Type | Notes |
|---|---|---|
| `origin` | enum | `domestic` or `foreign`. |
| `cohort` | enum | `retail`, `mixed`, `institutional`, `unknown`. |

#### Sample request

```bash
curl "https://api.sectors.app/v2/brokers/?cohort=retail" \
  -H "Authorization: <api-key>"
```

#### Sample response

```json
[
  {
    "code": "AD",
    "name": "Sukadana Prima Sekuritas",
    "is_foreign": false,
    "cohort": "institutional",
    "license_type": "Online, Online AO, Penjamin Emisi Efek, Perantara Pedagang Efek, RT AO"
  }
]
```

#### Gotchas

- **Costs 1 credit.** Call once and cache.
- ~88 total brokers. `n_brokers=90` is the max cap across other endpoints.

---

### `GET /v2/foreign-flow/{symbol}/` — Daily Net Foreign Inflow

- **Purpose:** Daily net foreign-broker inflow (IDR) for one IDX ticker up to 90 days. Positive = foreign net buyers; negative = foreign net sellers.
- **Hackathon applicability:** **ai-agents** (foreign-flow sentiment), **automation** (alert when flow crosses threshold).

#### Path + query parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `symbol` | path | required | E.g. `BBCA`, `GOTO`. |
| `start` | date | 30 days before `end` | Max 90 days. |
| `end` | date | today | Future → 400. |

#### Sample request

```bash
curl -G "https://api.sectors.app/v2/foreign-flow/BBCA/" \
  -H "Authorization: <api-key>" \
  --data-urlencode "start=2025-05-01" \
  --data-urlencode "end=2025-05-05"
```

#### Sample response

```json
{
  "symbol": "BBCA.JK", "start": "2025-05-01", "end": "2025-05-05",
  "data": [{ "date": "2025-05-02", "net_foreign_inflow": 199859810000 }]
}
```

#### Gotchas

- **Costs 1 credit.**
- **IDX is a closed market** — domestic flow is just the negative of foreign flow. Don't sum both.
- `net_foreign_inflow` is in raw IDR. Positive = bullish, negative = bearish for that stock.

---

### `GET /v2/broker-summary/{symbol}/` — Broker Activity Per Symbol

- **Purpose:** Per-broker daily trading rows for one IDX ticker up to 14 days, grouped by date. Optionally filter to one broker via `broker_code`.
- **Hackathon applicability:** **ai-agents** (broker clustering on one stock), **market-intel** (institutional footprint).

#### Path + query parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `symbol` | path | required | IDX ticker. |
| `broker_code` | string | — | Optional 2-letter code. |
| `start` | date | `end - 14 days` | Max 14 days. |
| `end` | date | today | — |

#### Sample response (BBCA, broker AF)

```json
{
  "symbol": "BBCA.JK", "start": "2025-05-01", "end": "2025-05-14",
  "data": [
    {
      "date": "2025-05-02",
      "summary": [
        { "broker_code": "AF", "bfreq": 1, "blot": 55, "bval": 48950000, "bavg_per_share": 8900,
          "sfreq": 1, "slot": 50, "sval": 44875000, "savg_per_share": 8975,
          "nlot": 5, "nval": 4075000, "navg_per_share": 8900 }
      ]
    }
  ]
}
```

#### Field glossary (broker summary / activity rows)

| Field | Meaning |
|---|---|
| `bfreq`, `sfreq` | Number of buy / sell transactions. |
| `blot`, `slot`, `nlot` | Buy / sell / net lots (1 lot = 100 shares for most IDX tickers). |
| `bval`, `sval`, `nval` | Buy / sell / net IDR value. |
| `bavg_per_share`, `savg_per_share`, `navg_per_share` | Volume-weighted avg price per share. |

#### Gotchas

- **Costs 1 credit** per call.
- 14-day max range. Older lookups → call in 14-day windows.

---

### `GET /v2/broker-summary/{symbol}/top/` — Top Buyers and Sellers Per Symbol

- **Purpose:** Brokers most actively accumulating / distributing a single ticker. `top_buyers` = largest positive net IDR; `top_sellers` = largest negative net IDR.
- **Hackathon applicability:** **ai-agents** ("smart money" signals).

#### Path + query parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `symbol` | path | required | IDX ticker. |
| `start` | date | `end - 30 days` | Max 90 days. |
| `end` | date | today | — |
| `origin` | enum | `all` | `all`, `domestic`, `foreign`. |
| `cohort` | enum | `all` | `all`, `retail`, `mixed`, `institutional`, `unknown`. |
| `n_brokers` | integer | 10 | 1–90. |

#### Sample response

```json
{
  "symbol": "BBCA.JK", "start": "2025-05-01", "end": "2025-05-14",
  "origin": "all", "cohort": "all",
  "top_buyers": [
    { "rank": 1, "broker_code": "KZ", "net_idr": 645536242500,
      "buy_idr": 1163325432500, "sell_idr": 517789190000 }
  ],
  "top_sellers": [
    { "rank": 1, "broker_code": "BK", "net_idr": -318961117500,
      "buy_idr": 561727337500, "sell_idr": 880688455000 }
  ]
}
```

#### Gotchas

- **Costs 2 credits** per call.
- Use `cohort=institutional` + `origin=foreign` to isolate foreign institutional flow (closer to "smart money").

---

### `GET /v2/broker-activity/{broker_code}/` — Broker Activity By Code

- **Purpose:** All (stock, day) trading for one broker over up to 14 days. Optionally filter to one stock via `symbol`.
- **Hackathon applicability:** **ai-agents** (track a known broker's positioning), **market-intel** (institutional follow).

#### Path + query parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `broker_code` | path | required | 2-letter code, e.g. `MG`, `AK`, `CC`. |
| `symbol` | string | — | Optional ticker filter. |
| `start` | date | `end - 14 days` | Max 14 days. |
| `end` | date | today | — |

#### Sample response

```json
{
  "broker_code": "YP", "start": "2025-05-01", "end": "2025-05-02",
  "data": [
    {
      "date": "2025-05-02",
      "summary": [
        { "symbol": "AADI.JK", "bfreq": 588, "blot": 8591, "bval": 5764735000,
          "bavg_per_share": 6710.2025, "sfreq": 401, "slot": 7301, "sval": 4896690000,
          "savg_per_share": 6706.8758, "nlot": 1290, "nval": 868045000, "navg_per_share": 6710.2025 }
      ]
    }
  ]
}
```

#### Gotchas

- **Costs 1 credit** per call.
- 14-day window max.
- Same `summary` row schema as `/v2/broker-summary/{symbol}/` — only the grouping differs (per-broker vs per-symbol).

---

### `GET /v2/broker-activity/{broker_code}/top/` — Top Accumulations and Distributions Per Broker

- **Purpose:** Stocks one broker has been most actively accumulating / distributing over a date range. `top_accumulations` = largest positive net IDR; `top_distributions` = largest negative net IDR.
- **Hackathon applicability:** **ai-agents** (institutional follow), **market-intel** (sector-rotation detection).

#### Path + query parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `broker_code` | path | required | 2-letter code. |
| `start` | date | `end - 30 days` | Max 90 days. |
| `end` | date | today | — |
| `n_brokers` | integer | 10 | 1–90. (Note: param name in docs is `n_brokers` but it's actually number of **stocks** to return per side.) |

#### Sample response

```json
{
  "broker_code": "YP", "start": "2025-05-01", "end": "2025-05-14",
  "top_accumulations": [
    { "rank": 1, "symbol": "ASII.JK", "net_idr": 58416394000,
      "buy_idr": 117493365000, "sell_idr": 59076971000 }
  ],
  "top_distributions": [
    { "rank": 1, "symbol": "BBCA.JK", "net_idr": -99677162500,
      "buy_idr": 97605242500, "sell_idr": 197282405000 }
  ]
}
```

#### Gotchas

- **Costs 2 credits** per call.
- The `n_brokers` parameter name is misleading — it controls how many **stocks** to return per side, not how many brokers.

---

### `GET /v2/brokers/top/` — Top Brokers Daily Ranking

- **Purpose:** Brokers ranked by gross trade value (default) or absolute net flow for a single date. Optionally filter by origin and cohort.
- **Hackathon applicability:** **market-intel** (liquidity leaderboard), **automation** (anomaly detection — when an unknown broker suddenly top-10s).

#### Query parameters

| Name | Type | Default | Notes |
|---|---|---|---|
| `date` | date | latest available | `YYYY-MM-DD`. |
| `metric` | enum | `gross` | `gross` (buy+sell) or `net` (absolute net flow). |
| `origin` | enum | `all` | `all`, `domestic`, `foreign`. |
| `cohort` | enum | `all` | `all`, `retail`, `mixed`, `institutional`, `unknown`. |
| `n_brokers` | integer | all matching | 1–90. |

#### Sample request

```bash
curl -G "https://api.sectors.app/v2/brokers/top/" \
  -H "Authorization: <api-key>" \
  --data-urlencode "origin=foreign" \
  --data-urlencode "metric=net" \
  --data-urlencode "n_brokers=10"
```

#### Sample response

```json
{
  "date": "2026-07-08", "metric": "gross", "origin": "foreign", "cohort": "all",
  "results": [
    { "rank": 1, "broker_code": "AK", "gross": 1984643350000, "net": -326211642600 }
  ]
}
```

#### Gotchas

- **Costs 2 credits** per call.
- `gross` = total buy + sell IDR (always positive, magnitude = activity). `net` = signed net IDR flow.
- `n_brokers` default = all (~88 total). Max 90.

---

## Cross-references

- TOC anchor: [`sectors-api-and-mcp.md`](../sectors-api-and-mcp.md)
- Screener + helper lists: [`idx-screener.md`](./idx-screener.md)
- Per-company reports: [`idx-company.md`](./idx-company.md)
- Financials + daily transactions: [`idx-financials-transactions.md`](./idx-financials-transactions.md)
- Mining endpoints: [`mining-*.md`](./)
