# 9 minimal ideas from AGY Gemini 3.7 Flash (high effort)

> Generated 2026-08-30 by 3 parallel `agy --model gemini-3.7-flash-high --effort high` runs against the planning artifacts in `sectors-hackathon` repo. Each AGY received a strict-format prompt for one track.
>
> **Not yet scored** — drop into the rubric from [`tracks/idea-scoring.md` (F3 audit branch)](https://github.com/mrayhanfadil/sectors-hackathon/blob/audit/f3-ideas-2026-08-29/tracks/idea-scoring.md) when you're ready to pick.
>
> **Compare with existing brainstorm in [`ideas.md`](../../ideas.md) and [`tracks/idea-scoring.md` (F3)](https://github.com/mrayhanfadil/sectors-hackathon/blob/audit/f3-ideas-2026-08-29/tracks/idea-scoring.md).** If you want a recommendation after scoring all 9, see the F3 prompt template.

## Quick index

| # | Track | Idea | Effort | Daily credits |
|---|---|---|---|---|
| 1 | AI Agents | Saham Jujur (auditable DD agent) | M | ~6 per query |
| 2 | AI Agents | Bandar Radar (smart money + insider) | M | ~5 per query |
| 3 | AI Agents | Tambang Intel (mining cross-domain) | M | varies |
| 4 | Automation | Radar Asing Pagi (08:15 WIB cron) | L | 4/day |
| 5 | Automation | Pantau Orang Dalam (17:30 WIB cron) | L | 3/day |
| 6 | Automation | Siaga Lapkeu IDX (07:30 WIB cron) | L | 3/day |
| 7 | Market Intel | DividenSehat (dividend yield trap screener) | L | varies |
| 8 | Market Intel | BandarDivergence (smart-money index) | M | varies |
| 9 | Market Intel | TambangIntel (mining margin sensitivity) | M | varies |

## Track 01

### 1. Saham Jujur — Auditable IDX Due Diligence Agent

- **Problem statement:** Indonesian retail equity investors need an automated, auditable due diligence agent so they can cut through social media hype ("pom-pom") and make verifiable, data-backed stock selections.
- **Core agent workflow:**
  1. User enters a ticker or comparative question (e.g., "Is PGAS fundamentally solid and can it sustain dividends?"); the agent formulates a multi-part investigation plan and fetches baseline financials via `GET /v2/company/report/{symbol}/?sections=overview,financials,dividend,valuation`.
  2. Agent identifies industry peers and queries the screener via `GET /v2/companies/?where=sub_sector='{sub_sector}'&order_by=-market_cap` to benchmark profitability, leverage, and valuation percentiles against sector medians.
  3. Agent inspects corporate governance and insider sentiment by querying `GET /v2/news/filings/?symbol={symbol}&transaction_type=buy,sell` and checks for regulatory flags with `GET /v2/news/suspensions/?symbol={symbol}`.
  4. Agent runs a deterministic fact-checking pass that maps every LLM conclusion directly to returned JSON fields, outputting a structured Due Diligence Dossier with clickable, verified citation badges.
- **What makes it an AGENT, not a wrapper:** It executes an autonomous multi-step planner-executor-auditor loop with dynamic sub-querying and a custom citation verification engine that programmatically validates LLM claims against raw Sectors JSON payloads before rendering.
- **Effort to ship in 4 weeks solo:** **Medium (M)** — Straightforward deterministic DAG architecture (FastAPI + LangGraph/custom state machine + lightweight React/Streamlit UI) that queries single tickers at a time, keeping implementation focused and well within the 1,000 credit budget.
- **Biggest ship risk:** Handling edge cases where newly listed or thinly traded tickers return incomplete historical or peer data, requiring graceful fallback reasoning.

---

### 2. Bandar Radar — Smart Money & Insider Flow Detective

- **Problem statement:** Indonesian swing and position traders need an autonomous forensic market agent that cross-correlates broker accumulation with insider filings so they can identify institutional accumulation phases before retail price breakouts occur.
- **Core agent workflow:**
  1. Agent receives a ticker or sector watchlist and queries `GET /v2/brokers/foreign-flow/{symbol}/?start={date}&end={date}` to calculate 30-day foreign institutional accumulation momentum.
  2. Agent calls `GET /v2/brokers/broker-summary/top/{symbol}/?start={date}&end={date}&n_brokers=10` to isolate top institutional buyer vs retail distributor broker codes (e.g., foreign institutional desks vs retail brokers).
  3. Agent queries `GET /v2/news/filings/?symbol={symbol}&transaction_type=buy` to check whether corporate insiders/directors have accumulated shares during the same period.
  4. Agent queries `GET /v2/transaction/daily/{symbol}/?start={date}&end={date}` to compute volume-price divergence, tests its smart-money accumulation hypothesis across the combined data, and generates a structured flow verdict with risk warnings.
- **What makes it an AGENT, not a wrapper:** It formulates and iteratively validates a multi-source hypothesis (detecting divergence across foreign flow, broker concentration, insider transactions, and price action) using domain-specific heuristics rather than delegating generic analysis to a single chat prompt.
- **Effort to ship in 4 weeks solo:** **Low-to-Medium (M)** — Clear data pipelines across 4 distinct Sectors endpoints, cleanly deliverable via a focused Telegram bot or single-page dashboard with clear anomaly score cards.
- **Biggest ship risk:** Over-consuming the 1,000 API credits during development if broker-summary endpoints are called repeatedly over large date ranges without local caching.

---

### 3. Tambang Intel — Indonesian Mining & Concession Intelligence Agent

- **Problem statement:** Indonesian commodity investors and supply chain analysts need an autonomous intelligence agent that bridges corporate equity fundamentals with concession-level operational data so they can evaluate the true operational risk and reserve runway of listed mining companies.
- **Core agent workflow:**
  1. User specifies a mining stock (e.g., ANTM, NCKL, MBMA) or commodity theme (e.g., "nickel downstreaming"); the agent resolves the corporate entity and calls `GET /v2/mining/companies/{slug}/` and `GET /v2/mining/companies/{slug}/financials/` for site-level operating metrics.
  2. Agent queries `GET /v2/mining/sites/?commodity_type={type}&province={province}` and `GET /v2/mining/licenses/?commodity_type={type}&expiring_soon=true` to cross-reference concession locations, active output volumes, and upcoming IUP license expiration risks.
  3. Agent fetches macroeconomic supply-demand context via `GET /v2/mining/commodities/price/{commodity}/` and `GET /v2/mining/commodities/{commodity}/exports/?year={year}`.
  4. Agent cross-analyzes concession sustainability against reported quarterly revenue (`GET /v2/company/quarterly-financials/{symbol}/`), generating an interactive asset-level operational intelligence report.
- **What makes it an AGENT, not a wrapper:** It performs multi-domain schema bridging and entity resolution across disparate datasets (mapping capital market equity tickers to private operational mine concessions, geospatial site data, and export records) to construct and synthesize an end-to-end supply chain thesis.
- **Effort to ship in 4 weeks solo:** **Medium (M)** — Sectors provides rich, structured mining datasets out of the box; build effort centers on entity mapping between ticker symbols and mining slugs, easily displayed via a map/card UI.
- **Biggest ship risk:** Potential mapping mismatches between IDX holding company tickers and their specific operational mining subsidiary slugs in the API.

---

## Track 02

### 1. IDX Pre-Market Foreign Flow & Commodity Radar ("Radar Asing Pagi")

- **Idea name**: IDX Pre-Market Foreign Flow & Commodity Radar
- **One-sentence problem statement**: Indonesian retail traders waste 30 minutes every morning manually cross-referencing global commodity movements with yesterday's big broker/foreign flow before the 09:00 WIB market open.
- **Trigger schedule**: Cron at 08:15 WIB, Monday–Friday (Daily credit cost: 4 calls/run × 1 run/day × 1 credit = **4 credits/day** ≈ 88 credits/month).
- **Output channel**: Telegram message (Bot / Channel broadcast).
- **Sectors endpoints used (≥2)**:
  - `/v2/brokers/top/?date={yesterday}&metric=n_abs_net_flow&n_brokers=20`
  - `/v2/mining/commodities/{name}/price/?start_year=2026&end_year=2026`
  - `/v2/ranking/top-changes/?classifications=top_gainers&periods=1d`
- **What it tells the user**:
  ```text
  🌅 Radar Asing Pagi (30 Agu 2026)
  🔥 Top Inflow Asing Kemarin: BBRI (+Rp 420B), ASII (+Rp 180B), ANTM (+Rp 95B)
  ⛏️ Komoditas Watch: Nikel (+3.2% ↗), Batubara (-0.8% ↘)
  🎯 Sinyal Rotasi: Akumulasi asing masif pada sektor Metal & Mining sejalan dengan lonjakan nikel global.
  ```
- **Effort to ship in 4 weeks solo**: **L (Low)** — Scheduled Cloudflare Worker or cron script formatting JSON payload into a Telegram Markdown message.
- **Biggest ship risk**: Sectors API latency or upstream delay in updating previous-day broker summary before 08:00 WIB.
- **Why a real Indonesian will use this daily**: Indonesian retail traders are obsessed with "Bandarmology" and foreign net flow (*asing masuk/keluar*), needing an instant 30-second watchlist check right before the opening bell.

---

### 2. IDX Insider Transaction & Big Whale Watcher ("Pantau Orang Dalam")

- **Idea name**: IDX Insider Transaction & Big Whale Watcher
- **One-sentence problem statement**: Retail investors miss high-conviction insider accumulation signals because OJK/IDX ownership filings are buried in complex daily PDF disclosures.
- **Trigger schedule**: Cron at 17:30 WIB, Monday–Friday after post-market filings settle (Daily credit cost: 3 calls/run × 1 run/day × 1 credit = **3 credits/day** ≈ 66 credits/month).
- **Output channel**: Telegram message / Discord webhook.
- **Sectors endpoints used (≥2)**:
  - `/v2/news/filings/?transaction_type=buy`
  - `/v2/transaction/close/{date}/`
  - `/v2/brokers/foreign-flow/{symbol}/?start={start_date}&end={end_date}`
- **What it tells the user**:
  ```text
  🚨 Sinyal Orang Dalam (Closing 30 Agu 2026)
  👔 Direksi Borong: Direktur Utama BREN beli 500.000 lbr @ Rp 8.900 (Total Rp 4.45M).
  📊 Konfirmasi Harga: BREN ditutup flat di Rp 8.950 (+0.0%), Foreign flow 5-hari: Net Buy Rp 34B.
  💡 Catatan: Akumulasi insider pertama di emiten ini dalam 60 hari terakhir.
  ```
- **Effort to ship in 4 weeks solo**: **L (Low)** — Event filtering logic on filings endpoint paired with closing price verification and webhook dispatch.
- **Biggest ship risk**: Filings endpoint schema variations across different transaction types causing parser drops.
- **Why a real Indonesian will use this daily**: "Direksi borong saham" is one of the most trusted conviction catalysts in the Indonesian investing community to spot undervaluation before the broader public notices.

---

### 3. IDX Earnings Season & Financial Release Sentinel ("Siaga Lapkeu IDX")

- **Idea name**: IDX Earnings Season & Financial Release Sentinel
- **One-sentence problem statement**: Investors consistently get caught off-guard by earnings announcements and post-earnings volatility because IDX financial submission schedules are scattered and unstandardized.
- **Trigger schedule**: Cron at 07:30 WIB, Monday–Friday (Daily credit cost: 3 calls/run × 1 run/day × 1 credit = **3 credits/day** ≈ 66 credits/month).
- **Output channel**: Telegram message.
- **Sectors endpoints used (≥2)**:
  - `/v2/companies/quarterly-financial-dates/?since={date}`
  - `/v2/ranking/most-traded/?start={start_date}&end={end_date}&n_stock=10`
  - `/v2/idx-total/?start={start_date}&end={end_date}`
- **What it tells the user**:
  ```text
  📅 Siaga Lapkeu IDX (30 Agu 2026)
  🔔 Rilis Laporan Keuangan Hari Ini: TLKM (Q2), PGAS (Q2), MEDC (Q2)
  📈 Volume Watch: Likuiditas TLKM naik 45% dalam 3 hari menjelang rilis.
  ⚠️ Alert: Batas akhir penyampaian Lapkeu Q2 audited tersisa 2 hari bursa.
  ```
- **Effort to ship in 4 weeks solo**: **L (Low)** — Daily diff calculation against financial calendar dates pushed straight to chat.
- **Biggest ship risk**: Missing or late quarterly date metadata updates for small-cap tickers.
- **Why a real Indonesian will use this daily**: Quarterly earnings season (*musim rilis lapkeu*) creates the largest single-day price swings on the IDX, making this an indispensable morning risk-management checkpoint.

---

## Track 03

### 1. DividenSehat (IDX Dividend Quality & Yield-Trap Screener)

1. **Idea name**: DividenSehat — IDX Dividend Quality & Yield-Trap Screener
2. **One-sentence problem statement**: Indonesian retail investors frequently chase high trailing dividend yields into cyclical value traps without knowing whether current earnings and cash flows can sustain future payouts.
3. **What interpretation layer**: A composite 0–100 Dividend Health Score synthesizing 3-year payout continuity, free cash flow coverage, and quarterly earnings stability. It applies a deterministic anomaly rule ("Yield Trap Flag") to flag companies with trailing yields >8% whose trailing-12-month net income has contracted by >25% or whose payout ratio exceeds 100% of trailing earnings.
4. **Output shape**: Filterable screener table rank-ordered by Dividend Health Score with category badges ("Compounder", "Safe Yield", "Yield Trap Alert") and score component drill-downs.
5. **Sectors endpoints used (≥3)**:
   - `GET /v2/companies/?where=dividend_yield>0`
   - `GET /v2/company/report/{symbol}/?sections=financials,valuation,dividend`
   - `GET /v2/company/quarterly-financials/{symbol}/?n_quarters=4`
   - `GET /v2/company/corporate-actions/{symbol}/`
6. **Why this counts as Market Intel, not data display**: It transforms raw historical dividends and financial ratios into a forward-looking solvency and payout sustainability rating that warns investors away from mathematically unsustainable payouts.
7. **Effort to ship in 4 weeks solo**: L
8. **Biggest ship risk**: Normalizing cash-flow and payout ratio formulas between financial institutions (e.g., banks) and non-financial issuers.
9. **One real signal the product surfaces**: "PTBA shows a 12.4% trailing dividend yield but receives a 'Yield Trap Alert' due to a 38% YoY net income contraction and an estimated payout requirement exceeding 110% of trailing annual earnings."

---

### 2. BandarDivergence (Smart Money & Insider Conviction Radar)

1. **Idea name**: BandarDivergence — Smart Money & Insider Conviction Radar
2. **One-sentence problem statement**: Indonesian equity traders cannot easily distinguish between speculative retail price spikes and genuine institutional accumulation backed by insider buying.
3. **What interpretation layer**: A calculated "Smart Money Conviction Index" (SMCI) that correlates 90-day foreign broker net accumulation percentiles and insider transaction volumes against valuation deviation bands (PBV/PE z-scores vs. 3-year historical averages). It surfaces positive divergences (heavy foreign/insider accumulation at multi-year valuation troughs) and negative divergences (aggressive foreign distribution during multiple expansion).
4. **Output shape**: Rank-ordered anomaly screener and quadrant matrix (Flow Momentum vs. Valuation Stretch) with automated diagnostic tags.
5. **Sectors endpoints used (≥3)**:
   - `GET /v2/brokers/foreign-flow/{symbol}/?start=...&end=...`
   - `GET /v2/news/filings/?symbol=...&transaction_type=buy|sell`
   - `GET /v2/company/report/{symbol}/?sections=valuation,financials`
   - `GET /v2/brokers/broker-summary/top/{symbol}/?start=...&end=...`
6. **Why this counts as Market Intel, not data display**: It combines microstructure broker flows, regulatory insider filings, and fundamental valuation multiples into a unified quantitative divergence signal that cannot be seen on any single chart.
7. **Effort to ship in 4 weeks solo**: M
8. **Biggest ship risk**: Accurately normalizing historical valuation bands for recently listed companies with short trading track records.
9. **One real signal the product surfaces**: "ACES triggers a 'Bullish Smart Money Divergence' with net foreign broker accumulation in the 92nd percentile over 30 days and net insider buying by commissioners, despite trading at a 3-year PBV valuation trough (-1.8 standard deviations)."

---

### 3. TambangIntel (Mining Margin Sensitivity & Resilience Ranker)

1. **Idea name**: TambangIntel — Indonesian Mining Margin Sensitivity & Resilience Ranker
2. **One-sentence problem statement**: Investors in Indonesia's commodity sector lack visibility into how global commodity price shifts and national export destination changes translate into operational margin compression across listed mining producers.
3. **What interpretation layer**: A comparative "Commodity Resilience Score" that maps benchmark commodity price deltas (thermal coal, nickel, copper) and national export destination volumes against company-level quarterly cost structures, gross margin trends, and production capacity. It stratifies mining operators into operational tiers (Low-Cost Resilient vs. High-Break-Even Vulnerable) based on simulated sensitivity to commodity price declines.
4. **Output shape**: Rank-ordered comparative matrix and sector heatmap showing margin sensitivity tiers, break-even resilience, and export destination exposure.
5. **Sectors endpoints used (≥3)**:
   - `GET /v2/mining/commodities/price/{commodity}/?start_year=...&end_year=...`
   - `GET /v2/mining/exports/?commodity_type=coal&year=2024`
   - `GET /v2/mining/companies/{slug}/financials/?year=...`
   - `GET /v2/company/quarterly-financials/{symbol}/?n_quarters=4`
6. **Why this counts as Market Intel, not data display**: It models macro commodity price trajectories and export flows directly against micro financial margins to generate a predictive operational resilience ranking rather than simply plotting commodity prices or financial statements.
7. **Effort to ship in 4 weeks solo**: M
8. **Biggest ship risk**: Reliably mapping Sectors mining company slugs to their corresponding listed IDX parent tickers and financial reporting entities.
9. **One real signal the product surfaces**: "ADRO demonstrates an 'Elite Cost-Resilience Score' in thermal coal, sustaining positive operating margin expansion even as benchmark coal prices dropped 15% YoY, supported by diversified export destinations to India and Southeast Asia."

---

