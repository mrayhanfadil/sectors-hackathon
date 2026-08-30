# 9 minimal ideas — "retail = institutional" thesis

> Generated 2026-08-30 by 3 parallel `agy --model gemini-3.7-flash-high --effort high` runs against the `sectors-hackathon` repo. Each AGY received one angle of the thesis.
>
> **Thesis:** "Indonesian retail investor bisa act like institusi dengan Sectors data" — by giving retail access to the **same workflow primitives** institutional desks have (pre-market intelligence, custom screening, portfolio discipline).
>
> **Compare with prior brainstorm:** [existing `ideas.md`](../../ideas.md) has 11 generic track-bucket ideas. [F3 scoring doc](https://github.com/mrayhanfadil/sectors-hackathon/blob/audit/f3-ideas-2026-08-29/tracks/idea-scoring.md) scored 5 NEW ideas. [AGY-9 track-bucket ideas](https://github.com/mrayhanfadil/sectors-hackathon/blob/idea/agy-brainstorm-2026-08-30/ideas/agy-9-ideas.md) gave 3 per track. **These 9 are the first batch framed specifically under "retail = institutional" empowerment lens.**

## Quick index

| # | Angle | Idea | Track fit | Effort | Daily credits |
|---|---|---|---|---|---|
| 1 | Pre-market | Smart Money Divergence Radar | T02 Automation | L | ~10/day |
| 2 | Pre-market | Overnight Commodity + IDX Macro Brief | T02 Automation | L | 4-6/day |
| 3 | Pre-market | Earnings Surprise + Foreign-Flow Convergence | T02 Automation | L | ~8/day |
| 4 | Thesis-as-code | InsiderCompounder (skin-in-the-game quality screener) | T03 Market Intel | L | varies |
| 5 | Thesis-as-code | YieldDurability (dividend sustainability + flow) | T03 Market Intel | L | varies |
| 6 | Thesis-as-code | ThematicExposureMap (theme → ticker mapping) | T03 Market Intel | M | varies |
| 7 | Portfolio | ThesisBreak (fundamental drift stop-loss) | T01 Agent | M | varies |
| 8 | Portfolio | Conviction-Rebalancer (insider-aligned sizing) | T01 Agent | M | varies |
| 9 | Portfolio | ForeignFlow Divergence / Portfolio Concentration | T01 Agent | M | varies |

---

## Angle: premarket

### 1. Smart Money Divergence Radar (Pre-Market Flow-Decoupling Brief)

1. **Idea name**: Smart Money Divergence Radar
2. **One-sentence problem statement**: Indonesian retail swing and momentum traders need pre-market foreign flow vs. price divergence alerts so they can exploit institutional accumulation on red days before market open at 09:00 WIB.
3. **What institutional workflow this mirrors**: Institutional sales traders at 08:15 WIB inspect T-1 block flow and foreign broker positioning against closing price action to find "stealth accumulation" (e.g., BBRI fell -2.1% on T-1, but foreign desks CS and ZP net-bought Rp 140B), preparing pre-opening limit buy orders at 08:45 WIB.
4. **Core workflow**:
   1. At 08:15 WIB, a scheduled cron fetches T-1 price performance across liquid tickers via `/v2/ranking/top-changes/?classifications=top_gainers,top_losers&periods=1d` and `/v2/transaction/close/{date}/`.
   2. Queries `/v2/brokers/foreign-flow-by-symbol/` to calculate the Divergence Spread: `Normalized Foreign Net Flow - Normalized % Price Change`.
   3. For the top 5 divergent tickers, queries `/v2/brokers/broker-summary/top/{symbol}/` to verify whether net buying was heavily concentrated in institutional brokers (e.g., ZP, AK, BK).
   4. Formats and dispatches a compact "Smart Money Divergence Brief" categorizing tickers into *Stealth Accumulation (Price Down / Foreign Flow Heavy Buy)* and *Distribution Trap (Price Up / Foreign Flow Heavy Sell)* with estimated institutional accumulation VWAPs.
5. **Output surface**: Telegram Bot (auto-broadcast at 08:20 WIB + on-demand `/divergence` trigger).
6. **What makes retail = institutional here**: Retail traders usually buy green candles and panic on red candles; this gives retail traders the exact institutional desk view of where foreign smart money bought the dip before the 08:45 WIB pre-opening phase.
7. **Effort to ship in 4 weeks solo**: Low (Stateless Python worker, SQLite for 30-day baseline cache, Telegram Bot API).
8. **Biggest ship risk**: T-1 data reconciliation latency if pre-market queries fire before Sectors completes end-of-day broker flow ingestion.
9. **Daily credit cost estimate**: 1 (`ranking`) + 1 (`transaction/close`) + 1 (`foreign-flow-by-symbol`) + 5 (`broker-summary/top`) = **8 calls/day (8 credits/day)**.

---

### 2. Commodity-to-IDX Transmission Engine (Pre-Market Resource Radar)

1. **Idea name**: Commodity-to-IDX Transmission Engine
2. **One-sentence problem statement**: Indonesian retail commodity stock traders need pre-market global commodity price moves mapped to IDX ticker-level broker positioning so they can position in sector leaders (e.g., ANTM, MDKA, ADRO) before the opening gap.
3. **What institutional workflow this mirrors**: Natural resources equity desks at 08:00 WIB cross-examine global overnight benchmark moves (LME Nickel, Gold, Newcastle Coal, Brent Crude) against IDX commodity tickers' T-1 institutional broker accumulation to determine opening gap continuation versus gap-fade setups.
4. **Core workflow**:
   1. At 08:00 WIB, a cron job fetches overnight closing prices and 24h percentage deltas for key commodities (Nickel, Coal, Gold, Copper, Oil) via `/v2/mining/commodities/{name}/price/`.
   2. Filters for commodities with delta $> |1.5\%|$ and maps them to high-beta IDX proxies (e.g., LME Nickel $+3.4\% \rightarrow$ ANTM, INCO, NCKL; Gold $+1.8\% \rightarrow$ MDKA, BRMS).
   3. Calls `/v2/brokers/foreign-flow/{symbol}/` and `/v2/brokers/broker-summary/top/{symbol}/` for mapped tickers to confirm whether institutional brokers (e.g., RX, CC, ZP) accumulated shares on T-1.
   4. Calls `/v2/news/news/?symbols=ANTM,MDKA,INCO,ADRO` to check for overnight regulatory or mining export policy disclosures.
   5. Generates a "Pre-Market Commodity Alpha Matrix" ranking candidate tickers by `Overnight Commodity Delta × Net Institutional Flow Score`.
5. **Output surface**: Discord Webhook / Channel (rich embed with color-coded heat badges and direct action bias).
6. **What makes retail = institutional here**: Replaces disconnected retail news-reading (manually checking external commodity charts) with an automated quantitative institutional desk matrix that directly pairs commodity momentum with smart money positioning.
7. **Effort to ship in 4 weeks solo**: Low (Scheduled Lambda/Cloud Run script, JSON mapping dictionary, Discord webhook payload builder).
8. **Biggest ship risk**: Sectors commodity price update timing lagging behind London/New York overnight settlement hours.
9. **Daily credit cost estimate**: 4 (`commodities/price`) + 4 (`foreign-flow`) + 4 (`broker-summary/top`) + 1 (`news`) = **13 calls/day (13 credits/day)**.

---

### 3. Insider & Whale Concentration Sentinel (08:30 WIB Pre-Open Brief)

1. **Idea name**: Insider & Whale Concentration Sentinel
2. **One-sentence problem statement**: Indonesian retail fundamental-swing investors need pre-market detection of after-hours insider filings cross-referenced with top broker concentration ratios so they can front-run emerging institutional accumulation narratives before the crowd.
3. **What institutional workflow this mirrors**: Buy-side research analysts at 08:20 WIB audit statutory corporate disclosures (OJK/IDX insider buy/sell transactions) filed post-market close and cross-match them with T-1 Broker Concentration (CR3/CR5 net volume absorption) to distinguish authentic insider conviction from retail noise.
4. **Core workflow**:
   1. At 08:25 WIB, a cron worker queries `/v2/news/filings/?transaction_type=buy` to extract all director and major shareholder acquisition filings submitted after 16:00 WIB on T-1.
   2. For tickers with flagged insider accumulation (e.g., directors buying AUTO, BRIS, or ERAA), queries `/v2/brokers/top/?date={t_minus_1}&metric=n_abs_net_flow&n_brokers=20` and `/v2/brokers/broker-summary/top/{symbol}/`.
   3. Computes the **Top-3 Broker Concentration Ratio (CR3)**: `(Top 3 Net Buyer Volume / Total Net Buy Volume) × 100%` to verify if domestic/foreign institutional desks (e.g., CC, BK, AK) acted as the execution vehicle.
   4. Queries `/v2/idx-total/` to benchmark market-wide liquidity regime context.
   5. Dispatches an actionable card: e.g., *"Whale Alert: AUTO — Director bought 500k shares (+0.12% stake), backed by 82% CR3 broker concentration (CC, PD net accumulating)"*.
5. **Output surface**: Telegram Bot / Mobile Webhook with one-tap on-demand lookup (`/whale <ticker>`).
6. **What makes retail = institutional here**: Gives retail investors instant synthesis of dry, buried IDX PDF filings combined with order flow concentration—a workflow that usually requires a paid institutional research assistant.
7. **Effort to ship in 4 weeks solo**: Medium (Parsing unstructured filing metadata, computing concentration metrics, interactive query handling).
8. **Biggest ship risk**: Format variability or inconsistent issuer disclosure structures in the filings endpoint response schema.
9. **Daily credit cost estimate**: 1 (`filings`) + 1 (`brokers/top`) + 5 (`broker-summary/top` for flagged tickers) + 1 (`idx-total`) = **8 calls/day (8 credits/day)**.

---

## Angle: thesis

### 1. InsiderCompounder (Skin-in-the-Game Quality Screener)
1. **Idea name**: InsiderCompounder — Executive-Aligned Capital Quality Screener
2. **One-sentence problem statement**: Indonesian retail investor with a long-term compounding mindset needs to screen IDX by corporate insider buying activity combined with high ROE and free-float liquidity so they can discover high-conviction management alignment without reading daily regulatory PDFs manually.
3. **Sample thesis the product supports**:
   ```yaml
   thesis:
     min_roe_2024: 0.12
     min_dividend_yield_2024: 0.04
     min_free_float_ratio: 0.15
     insider_net_buying_window_days: 90
     insider_min_cumulative_shares: 500000
   ```
4. **What institutional workflow this mirrors**: Replicates a fundamental family office / equity research analyst's custom Bloomberg screen that joins capital allocation hurdle rates (ROE, Dividend Yield) with Form 4 / OAM regulatory insider accumulation filings.
5. **Core workflow**:
   - **Step 1**: Execute coarse filter on entire IDX universe via `/v2/companies/?where=roe[2024] >= {min_roe_2024} AND dividend_yield[2024] >= {min_dividend_yield_2024}` (narrows ~950 tickers down to ~40 candidates).
   - **Step 2**: Check liquidity hurdles against `/v2/screener/free-float/` to filter out tickers below `{min_free_float_ratio}`.
   - **Step 3**: Query `/v2/news/filings/?symbol={symbol}&transaction_type=buy` for each surviving ticker to calculate net insider buying volume over `{insider_net_buying_window_days}`.
   - **Step 4**: Rank and notify matching tickers that pass all encoded constraints.
6. **Output surface**: Telegram bot with weekly scheduled re-run alerts and instant `/test-thesis` command.
7. **What makes retail = institutional here**: Automatically cross-references official capital structure filings with valuation and profitability metrics on a programmatic schedule rather than relying on delayed financial media rumors.
8. **Effort to ship in 4 weeks solo**: L (Low) — Streamlined 2-stage execution pipeline with Telegram webhook alert delivery.
9. **Biggest ship risk**: Periods of low insider transaction volume in IDX small-to-mid caps resulting in zero-match screens without clear explanatory diagnostics.
10. **Credit cost per screen run**: ~25–45 credits (1 credit for base `/v2/companies` screener + 1 credit `/v2/screener/free-float/` + 20–40 symbol filing lookups).

---

### 2. SmartFlow-Inflection (Institutional Flow & Earnings Acceleration Screener)
1. **Idea name**: SmartFlow-Inflection — Sectoral Earnings Acceleration & Foreign Flow Engine
2. **One-sentence problem statement**: Indonesian retail investor with a Growth-At-Reasonable-Price (GARP) strategy needs to screen IDX by multi-quarter earnings acceleration matched with foreign institutional accumulation so they can enter positions right as institutional accumulation starts.
3. **Sample thesis the product supports**:
   ```python
   # User-defined Thesis Configuration
   thesis = {
       "target_subsectors": ["Coal", "Industrial Metals", "Oil & Gas"],
       "max_pbv_2024": 2.5,
       "min_consecutive_qoq_profit_growth": 2, # quarters
       "min_net_foreign_flow_30d_idr": 10_000_000_000 # 10B IDR
   }
   ```
4. **What institutional workflow this mirrors**: Replicates a hedge fund quantitative equity workflow screening for fundamental earnings turnaround/acceleration (consecutive positive QoQ net profit growth) verified by institutional broker accumulation (Foreign Flow Net Buy).
5. **Core workflow**:
   - **Step 1**: Retrieve sector mapping via `/v2/helper-list/subsectors/` and apply valuation ceiling using `/v2/companies/?where=pbv[2024] <= {max_pbv_2024}`.
   - **Step 2**: For matching sector constituents, query `/v2/company/quarterly-financials/{symbol}/?n_quarters=4` to detect consecutive QoQ/YoY net income acceleration.
   - **Step 3**: Query `/v2/brokers/foreign-flow/{symbol}/` for fundamentally accelerating tickers to verify 30-day foreign net accumulation threshold.
   - **Step 4**: Compute flow-to-market-cap ratio and format into a priority watchlist.
6. **Output surface**: Weekly email digest (clean Markdown tables) + minimal single-page web UI for parameter customization.
7. **What makes retail = institutional here**: Synthesizes granular quarterly earnings trajectory with proprietary institutional broker flow data, removing manual broker-summary charting.
8. **Effort to ship in 4 weeks solo**: M (Medium) — Requires clean quarterly time-series acceleration parsing and broker net sum aggregation.
9. **Biggest ship risk**: IDX financial reporting delays causing quarterly earnings data to lag several weeks behind fast-moving broker accumulation signals.
10. **Credit cost per screen run**: ~30–50 credits (1 credit base `/v2/companies` + 1 credit `/v2/helper-list/subsectors/` + 25–45 quarterly and broker-flow endpoint lookups).

---

### 3. DivTrap-Shield (Forensic Dividend Sustainability Screener)
1. **Idea name**: DivTrap-Shield — High-Yield Quality & Payout Sustainability Engine
2. **One-sentence problem statement**: Indonesian retail investor with a dividend-income focus needs to screen IDX high-yield stocks against balance-sheet leverage, payout sustainability, and peer valuation so they can capture yields while avoiding value-destructive dividend cuts.
3. **Sample thesis the product supports**:
   ```json
   {
     "min_dividend_yield_2024": 0.07,
     "max_payout_ratio": 0.65,
     "max_debt_to_equity": 1.20,
     "min_free_float": 0.20,
     "insider_sell_filings_count_180d": 0,
     "peer_relative_pe": "lower_than_peer_median"
   }
   ```
4. **What institutional workflow this mirrors**: Replicates an institutional asset manager's dividend governance committee checklist, stress-testing high nominal yield against cash-flow solvency, relative sector valuation, and absence of executive divestment.
5. **Core workflow**:
   - **Step 1**: Screen high-yield universe using `/v2/companies/?where=dividend_yield[2024] >= {min_dividend_yield_2024}` (filters 950 tickers down to ~25 high-yield candidates).
   - **Step 2**: Discard illiquid dividend traps using `/v2/screener/free-float/` where `free_float_ratio >= {min_free_float}`.
   - **Step 3**: Deep-dive into candidates using `/v2/company/report/{symbol}/?sections=financials,valuation,dividend,peers` to evaluate payout ratio, DER, and relative peer P/E multiples.
   - **Step 4**: Query `/v2/news/filings/?symbol={symbol}&transaction_type=sell` to eliminate companies with recent insider dumping.
6. **Output surface**: Responsive Web UI (Next.js + Tailwind) with an interactive slider thesis builder and downloadable PDF thesis breakdown.
7. **What makes retail = institutional here**: Enforces multi-variable forensic quality checks (peer comp, balance-sheet safety, float liquidity, insider sales) rather than naive yield-chasing.
8. **Effort to ship in 4 weeks solo**: M (Medium) — Involves parsing multi-section company report payloads and comparing metrics against peer medians.
9. **Biggest ship risk**: Non-standard payout ratio disclosures or missing historical dividend data causing false exclusions on seasonal dividend payers.
10. **Credit cost per screen run**: ~20–35 credits (1 credit `/v2/companies` + 1 credit `/v2/screener/free-float/` + 15–25 company report and insider filing lookups).

---

## Angle: portfolio

### 1. ThesisBreak: Fundamental Stop-Loss & Conviction Rebalancer

1. **Idea name**: ThesisBreak — Automated Fundamental Drift & Stop-Allocation Engine
2. **One-sentence problem statement**: Retail investors hold losing positions down -50% because they set stop-losses on arbitrary price levels rather than fundamental thesis breakdown.
3. **What institutional workflow this mirrors**: A Portfolio Manager's quarterly investment committee review where positions are strictly trimmed or liquidated if earnings momentum decelerates or key valuation/insider metrics violate the fund's investment mandate.
4. **Core workflow**:
   - Step 1: User inputs portfolio holdings and target allocation weights via text or CSV.
   - Step 2: Fetch 4-quarter earnings trajectory using `/v2/company/quarterly-financials/{symbol}/?n_quarters=4` to detect net margin decay or revenue contraction.
   - Step 3: Check insider divestment activity via `/v2/news/filings/?symbol={symbol}&transaction_type=sell` and fundamental valuation ratios via `/v2/company/report/{symbol}/?sections=valuation`.
   - Step 4: Compute market portfolio drift using `/v2/transaction/close/{date}/` and generate mathematically sized trim/exit orders.
5. **What rebalance / risk signal fires**: "MDKA weight has expanded to 14.2% of book (Target: 10.0%), but Q2 revenue growth decelerated by -6.8% YoY with 2 executive insider sell filings in 30 days. Mandate: Trim 4.2% (sell 1,100 lots at Rp2,420) and reallocate proceeds to cash buffer."
6. **Output surface**: Telegram bot alert + Weekly PDF Mandate Compliance Card.
7. **What makes retail = institutional here**: Replaces emotional price-based panic selling with unemotional, rule-based fundamental stop-allocations tied directly to quarterly earnings degradation and insider transactions.
8. **Effort to ship in 4 weeks solo**: Low (L)
9. **Biggest ship risk**: Handling irregular filing schedules of IDX issuers when quarterly results are delayed.
10. **Credit cost per portfolio check**: 30 credits per 10-ticker check (10 tickers × 3 endpoints: quarterly financials, insider filings, close price).

---

### 2. BookGuard: Factor Exposure & Institutional Liquidity Drift Guard

1. **Idea name**: BookGuard — Institutional Flow & Sector Concentration Risk Monitor
2. **One-sentence problem statement**: Retail investors believe holding 8 different tickers makes them diversified, unaware that 60%+ of their capital is clustered in a single macro factor facing aggressive foreign capital flight.
3. **What institutional workflow this mirrors**: A Multi-Asset Risk Officer's factor-decomposition screen that detects sectoral clustering, liquidity dry-ups, and foreign institutional capital flight to enforce strict portfolio concentration caps.
4. **Core workflow**:
   - Step 1: Ingest user portfolio and map tickers to macro sectors using `/v2/companies/?where=...&order_by=...`.
   - Step 2: Query 14-day institutional positioning via `/v2/brokers/foreign-flow/{symbol}/` across all held tickers.
   - Step 3: Identify sector-wide momentum breakdown using `/v2/ranking/top-changes/?classifications=top_losers&periods=30d`.
   - Step 4: Price positions via `/v2/transaction/close/{date}/`, evaluate portfolio sector weights against a 25% max-risk ceiling, and emit rebalancing re-weighting trades.
5. **What rebalance / risk signal fires**: "Total Energy & Mining exposure is 44.0% (Risk Limit: 25.0%) with cumulative foreign institutional outflow of -Rp145B across ADRO & PTBA over 14 days. Mandate: Trim ADRO by 9.0% (sell 850 lots) and PTBA by 10.0% (sell 1,200 lots) to neutralize sector concentration below the 25% risk cap."
6. **Output surface**: Responsive Web Dashboard (Next.js/Tailwind) + Instant Telegram Risk Alarm.
7. **What makes retail = institutional here**: Uncovers hidden correlation risk and institutional flight across retail holdings, transforming nominal diversification (counting tickers) into true risk-weighted factor balance.
8. **Effort to ship in 4 weeks solo**: Medium (M)
9. **Biggest ship risk**: Designing a simplified factor-risk metric that retail users can understand without a financial engineering background.
10. **Credit cost per portfolio check**: 21 credits per 10-ticker check (1 sector mapping call + 10 foreign flow calls + 10 close price calls).

---

### 3. ExDate-Alpha: Corporate Action Risk & Shareholder Concentration Rebalancer

1. **Idea name**: ExDate-Alpha — Dividend Trap & Capital Preservation Rotation Engine
2. **One-sentence problem statement**: Retail investors buy high-yield dividend stocks right before the cum-date, only to lose 15-20% in post-ex-date price collapses because they do not evaluate cash flow coverage or shareholder concentration.
3. **What institutional workflow this mirrors**: An Equity Income Desk's corporate-actions risk book that models dividend sustainability (FCF vs payout ratio), public float lock-up, and pre-ex-date rotation timing to avoid dividend traps.
4. **Core workflow**:
   - Step 1: Scan user portfolio for upcoming corporate action dates and yield sizes via `/v2/company/corporate-actions/{symbol}/`.
   - Step 2: Audit dividend sustainability and operating cash buffer using `/v2/company/quarterly-financials/{symbol}/?n_quarters=4`.
   - Step 3: Analyze controlling owner vs retail float concentration via `/v2/company/shareholders-composition/{symbol}/{year}/`.
   - Step 4: Value position sizing using `/v2/transaction/close/{date}/` and compute optimal pre-ex-date capital reduction or hedge sizing.
5. **What rebalance / risk signal fires**: "ITMG position sits at 18.5% of portfolio with an ex-date in 4 trading days. Payout ratio is 96% with 2 consecutive quarters of declining operating cash flow and retail float expanded by 6.2%. Mandate: Reduce ITMG exposure from 18.5% to 6.0% (sell 400 lots at Rp26,100) before cum-date to evade an estimated 12.8% post-ex-date capital drag."
6. **Output surface**: Weekly Actionable Rebalance Email + Calendar Sync (.ics) with one-click rebalance execution checklists.
7. **What makes retail = institutional here**: Elevates retail from naive yield-chasing to institutional cash-flow auditing and systematic pre-corporate-action risk hedging.
8. **Effort to ship in 4 weeks solo**: Low (L)
9. **Biggest ship risk**: Accurately calculating expected dividend drag percentages across different IDX market regimes and liquidity conditions.
10. **Credit cost per portfolio check**: 30 credits per 10-ticker check (10 corporate actions + 10 shareholder compositions + 10 quarterly financials).

---

