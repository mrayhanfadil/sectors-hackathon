# 9 niche ideas — Indonesian-specific microstructure + macro + viral

> Generated 2026-08-30 by 3 parallel `agy --model gemini-3.7-flash-high --effort high` runs against the `sectors-hackathon` repo. Each AGY received one niche angle NOT covered by batch 1 (track buckets) or batch 2 (retail=institutional).
>
> **Compare with prior batches:**
> - [Batch 1 (`ideas/agy-9-ideas.md`)](https://github.com/mrayhanfadil/sectors-hackathon/blob/idea/agy-brainstorm-2026-08-30/ideas/agy-9-ideas.md): 3 per track (9 ideas), generic bucket coverage.
> - [Batch 2 (`ideas/agy-9-retail-institutional.md`)](https://github.com/mrayhanfadil/sectors-hackathon/blob/idea/agy-retail-institutional-2026-08-30/ideas/agy-9-retail-institutional.md): 3 empowerment angles × 3 ideas each.
> - **Batch 3 (this file):** 3 niche angles × 3 ideas each. Specific to Indonesian market.

## Quick index

| # | Angle | Idea | Track fit | Effort |
|---|---|---|---|---|
| 1 | Macro | KursImpact (USD/IDR shock + sector sensitivity) | T02 / T03 | M |
| 2 | Macro | KomoditasLokal (commodity price → IDX mining/concrete) | T02 / T03 | M |
| 3 | Macro | BI-Rate-Pulse (BI Rate decision calendar + portfolio prep) | T02 | L |
| 4 | Microstructure | DES-Guard (OJK Sharia classification forced-divestment radar) | T03 | M |
| 5 | Microstructure | ARA-Lock (auto-rejection atas + retail herd detector) | T03 | M |
| 6 | Microstructure | BrokerCodeWhisper (CG/ZP/RX/CS institutional folklore) | T03 / T01 | M |
| 7 | Viral | IDX DividenHunter (dividend safety card) | T03 | L |
| 8 | Viral | IDX MoversRadar (weekly sector rotation recap) | T02 / T03 | L |
| 9 | Viral | Billionaire Watch IDX (insider/concentrated ownership tracker) | T03 | M |

---

## Angle: macro

### 1. KursImpact: USD/IDR FX Shock & Foreign Flow Explainer

1. **Idea name**: KursImpact (USD/IDR Real-Time Shock & Sector Sensitivity Explainer)
2. **One-sentence problem statement**: Indonesian retail investor sees heavy-cap banking and consumer staples (BBRI, ICBP, KLBF) suddenly sell off intraday but doesn't know USD/IDR just spiked past a psychological resistance level triggering systematic foreign outflows and import margin squeeze, so they can avoid panic selling at bottoms or catching falling knives during currency devaluations.
3. **What external data source**: `open.er-api.com/v6/latest/USD` (free real-time FX endpoint) cross-validated with Bank Indonesia JISDOR daily reference rate RSS feed (`bi.go.id`).
4. **Core workflow**:
   - Step 1 (*External*): Fetch hourly USD/IDR spot rate from `open.er-api.com`; trigger alert when 1-day Rupiah depreciation exceeds +0.4% or breaches key round levels (e.g., IDR 16,300).
   - Step 2 (*Sectors*): Query `/subsectors/banking/` and `/subsectors/food-beverages/` to pull constituent tickers and their foreign ownership sensitivity.
   - Step 3 (*Sectors*): Fetch `/companies/{ticker}/daily/` for top 10 large-cap names to calculate real-time correlation between USD/IDR spike and foreign net-sell volume (`foreign_flow`).
   - Step 4 (*Sectors*): Fetch `/companies/{ticker}/financials/` to rank companies by FX debt exposure and imported COGS sensitivity.
   - Step 5: Deliver an automated 16:15 WIB market close breakdown attributing sector drops directly to FX and foreign flow dynamics.
5. **Real signal example**: "ICBP dropped -2.6% and BBRI dropped -1.9% today; here's why: USD/IDR spiked +0.68% to 16,410, triggering Rp 620B in institutional foreign net-selling on Big 4 banks and raising wheat/raw material import cost concerns for Indofood."
6. **Output surface**: Telegram Bot + daily automated 16:15 WIB digest graphic.
7. **Effort to ship in 4 weeks solo**: Low (L)
8. **Biggest ship risk**: Foreign investors occasionally net-buy export-oriented miners (ADRO, MEDC) during USD strength, requiring accurate sector segmentation so users don't think USD strength hurts every IDX stock equally.
9. **Free data source caveat**: `open.er-api.com` is 100% free with no API key requirement (hourly updates); Bank Indonesia JISDOR provides an official unauthenticated daily JSON/HTML summary at 16:00 WIB.

---

### 2. KomoditasRadar: Global Benchmark to IDX Mining Dislocation Scanner

1. **Idea name**: KomoditasRadar (Global Commodity Benchmark to IDX Mining Dislocation Scanner)
2. **One-sentence problem statement**: Indonesian retail investor sees nickel and coal stocks (ANTM, INCO, ADRO, PTBA) gap down or trade flat at market open but doesn't know overnight LME Nickel/Newcastle Coal futures moved sharply in the opposite direction, so they can capture morning open dislocations and avoid chasing false intraday momentum.
3. **What external data source**: Yahoo Finance free API via `yfinance` Python library (`GC=F` for Gold, `CL=F` for Brent Crude, `HG=F` for Copper, `ALI=F` for Aluminum) + TradingEconomics/MarketsInsider cached overnight scrape for Newcastle Coal and LME Nickel cash prices.
4. **Core workflow**:
   - Step 1 (*External*): Ingest overnight commodity settlement prices (Gold, Nickel, Copper, Coal, Crude Oil) at 07:30 WIB using `yfinance`.
   - Step 2 (*Sectors*): Query `/subsectors/metals-minerals/` and `/subsectors/coal/` to retrieve mapped IDX tickers (ANTM $\rightarrow$ Gold/Nickel, INCO/MBMA/NCKL $\rightarrow$ Nickel, ADRO/PTBA $\rightarrow$ Coal, MEDC $\rightarrow$ Oil).
   - Step 3 (*Sectors*): Call `/companies/{ticker}/daily/` and `/companies/{ticker}/valuation/` at 09:15 WIB to calculate the divergence between overnight commodity returns and 09:00 WIB stock opening returns.
   - Step 4: Flag tickers with a "Dislocation Score" $> 2.5\sigma$ where global benchmark moved $> +2\%$ but the IDX stock opened negative or flat.
5. **Real signal example**: "ANTM opened -0.9% at 09:05 WIB despite spot Gold hitting an all-time high (+1.6% overnight) and Nickel jumping +2.3%; Sectors valuation shows forward P/E at 11.4x with net positive domestic accumulation, flagging an opening retail divergence dip."
6. **Output surface**: Web Dashboard (Streamlit/Next.js) with live 08:30 WIB pre-market Telegram alerts.
7. **Effort to ship in 4 weeks solo**: Medium (M)
8. **Biggest ship risk**: LME Nickel prices occasionally decouple from physical Indonesian Class 2 NPI (Nickel Pig Iron) prices, which can create false divergence signals for pure NPI producers like MBMA.
9. **Free data source caveat**: Yahoo Finance (`yfinance`) is free and open for Gold, Copper, and Oil futures; Rotterdam/Newcastle Coal futures can be polled via free public financial widgets with a 15-minute delay (sufficient for Indonesian pre-market 08:30 WIB execution).

---

### 3. MakroKalender: BI Rate & Inflation Sector Playbook

1. **Idea name**: MakroKalender (BI Rate Decision & CPI Volatility Playbook for IDX)
2. **One-sentence problem statement**: Indonesian retail investor trades rate-sensitive property and automotive stocks (BSDE, CTRA, ASII) into high-impact Bank Indonesia RDG (Rapat Dewan Gubernur) meetings without knowing the sector's historical win rate and balance sheet debt vulnerability, so they can manage risk and position before interest rate announcements.
3. **What external data source**: Bank Indonesia Official Published RDG Calendar & BI-Rate History (`bi.go.id` press release portal) + BPS (Badan Pusat Statistik) Consumer Price Index (CPI) monthly release schedule.
4. **Core workflow**:
   - Step 1 (*External*): Ingest static 2026 BI RDG 2-day meeting schedule (12 scheduled dates/year) and BPS CPI print dates (1st working day of each month).
   - Step 2 (*Sectors*): Query `/subsectors/properties-real-estate/` and `/subsectors/automotive/` to pull rate-sensitive mid-and-large cap tickers.
   - Step 3 (*Sectors*): Fetch `/companies/{ticker}/price-history/` over the past 24 months to calculate average 3-day pre-meeting and 3-day post-meeting price alpha across past BI Rate hold/cut cycles.
   - Step 4 (*Sectors*): Query `/companies/{ticker}/financials/` to filter out companies with high Net-Debt-to-Equity ($> 0.8\text{x}$) that face refinancing risks during hawkish rate pauses.
   - Step 5: Send an automated "T-48h BI RDG Radar" preview showing historical sector win rates and lowest-debt defensive picks.
5. **Real signal example**: "BI RDG Rate Decision in 48 hours (Hold expected at 6.00%): Sectors balance sheet metrics show CTRA has low net gearing (0.21x) vs SMRA (0.64x); historical backtest over the last 6 rate-hold cycles shows Property sector yields an average +2.1% pre-announcement rally before stalling."
6. **Output surface**: Interactive Web Calendar + Weekly Sunday Email Dispatch.
7. **Effort to ship in 4 weeks solo**: Low (L)
8. **Biggest ship risk**: BI RDG happens only 12 times a year, so between monthly meetings the product needs supplementary weekly macro events (BPS inflation, trade balance prints) to maintain user engagement.
9. **Free data source caveat**: The Bank Indonesia RDG meeting calendar is published at the beginning of each calendar year as a public schedule on `bi.go.id` and can be stored as a static JSON file, supplemented by free RSS feed alerts for surprise extraordinary press conferences.

---

## Angle: microstructure

### Idea 1: DES-Guard (OJK Daftar Efek Syariah Debt-Limit & Rebalance Front-Runner)

1. **Idea name**: DES-Guard: Predictive OJK Sharia Classification & Forced-Divestment Radar
2. **One-sentence problem statement**: Indonesian retail and Islamic fund allocators see sudden multi-day ARB cascades when a stock is unexpectedly stripped of its Sharia status by OJK, but lack a tool to audit financial ratios against OJK limits before the semi-annual Daftar Efek Syariah (DES) announcement.
3. **Which IDX microstructure feature this exploits**: OJK Regulation No. 35/POJK.04/2017 governing the **Daftar Efek Syariah (DES)** / **Indeks Saham Syariah Indonesia (ISSI)**. Key criteria: (1) interest-bearing debt to total assets $\le 45\%$, and (2) non-halal/interest income to total revenue $\le 10\%$. When a stock breaches $45\%$ due to new bank facilities or working capital debt, Sharia-mandated mutual funds (*Reksa Dana Syariah*) are legally required to liquidate $100\%$ of their holdings within 10 to 30 days, causing severe downward price shock.
4. **What the product surfaces**: 
   - **DES Downgrade Hazard Score**: Flags current ISSI stocks whose interest-bearing debt-to-assets ratio has drifted into the danger zone ($43.0\% - 45.0\%+$) based on latest quarterly filings.
   - **DES Inclusion Alpha Watchlist**: Identifies high-growth non-Sharia mid-caps that just paid down debt below $45\%$, triggering fresh institutional buying eligibility ahead of the May/November review.
   - **Forced Liquidation Volume Estimate**: Calculated overhang based on estimated domestic institutional Sharia fund holdings vs. 30-day average daily turnover (ADTV).
5. **Core workflow**:
   - Step 1: Query `GET /v1/companies/` to fetch all actively listed IDX equities.
   - Step 2: Fetch quarterly balance sheets using `GET /v1/company/{ticker}/report/` to extract short-term loans, long-term bank debt, bonds, and total assets.
   - Step 3: Compute exact debt-to-asset ratios; filter tickers where $\frac{\text{Interest-Bearing Debt}}{\text{Total Assets}} \ge 44\%$ or where non-Sharia tickers dropped below $44\%$.
   - Step 4: Call `GET /v1/company/{ticker}/daily/` to compare estimated institutional float overhang against 20-day liquidity at current fraksi levels.
6. **Output surface**: Clean web dashboard with a traffic-light alert table (Green = Safe, Amber = $42-44\%$ Warning, Red = Immediate Exclusion Risk), plus a Telegram bot broadcasting critical balance sheet triggers within 1 hour of earnings submissions.
7. **Why this can't be replicated by a US/global product**: Global screeners (e.g., Bloomberg, Koyfin, Yahoo Finance) use standard Western ESG or generic Islamic screeners (AAOIFI standards which use market cap denominators rather than OJK's total-asset denominator). Only Indonesia uses the strict OJK 45% total-assets threshold tied directly to IDX ISSI and JII rebalancing mandates.
8. **Effort to ship in 4 weeks solo**: Low-to-Medium (1.5 weeks for ratio calculation & backtesting against historic OJK DES releases; 1.5 weeks for dashboard UI & Telegram webhook; 1 week for test suite and Sectors API caching).
9. **Biggest ship risk**: Inconsistent debt item naming across non-standard banking/financial sector balance sheets compared to standard industrial/mining filers.
10. **Credit cost per run**: ~12 credits per daily sync (Sectors batch quarterly data updates + caching; full universe scan once weekly runs well within the 1,000 credit limit).

---

### Idea 2: IDX Lock-Up Cliff (POJK Pre-IPO Share Release & Distribution Monitor)

1. **Idea name**: IDX Lock-Up Cliff: Pre-IPO Float Dilution & Underwriter Unload Tracker
2. **One-sentence problem statement**: Indonesian retail investors routinely buy hyped recent IPOs without knowing the exact POJK lock-up expiry date, leaving them trapped in consecutive ARBs when pre-IPO venture/founder shares unlock and flood the order book.
3. **Which IDX microstructure feature this exploits**: **POJK No. 25/POJK.04/2017** 6-month to 8-month mandatory share lock-up for shareholders acquiring equity at a discount prior to the IPO, alongside IDX board lot supply math and broker-led distribution (e.g., retail brokers like YP/PD/CC absorbing supply dumped through underwriter brokers like MG/KI/CP/SH).
4. **What the product surfaces**:
   - **Unlock Countdown & Supply Multiplier**: Shows the exact unlock date, the percentage of newly tradeable shares relative to the existing public float (e.g., "Float expands by $+380\%$ on Day 180"), and historical precedent drops on comparable IPOs.
   - **Liquidity Absorption Pressure**: Calculates how many days of median volume at the current price tick (Fraksi) it would take the market to absorb a $5\%$ founder divestment.
   - **Pre-Lockup Run-Up/Distribution Indicator**: Tracks if volume surges with retail net buying (broker codes YP, PD, NI) during D-30 to D-7 while institutional/foreign flow quietly exits.
5. **Core workflow**:
   - Step 1: Query `GET /v1/companies/` to identify all IPOs from the past 3 to 12 months.
   - Step 2: Query `GET /v1/company/{ticker}/overview/` to extract listing date, total listed shares, founder share breakdown, and initial public offering float.
   - Step 3: Compute the 180-day and 240-day POJK lock-up expiry dates.
   - Step 4: Call `GET /v1/company/{ticker}/daily/` to calculate the 30-day average daily turnover and price volatility leading up to the unlock window.
6. **Output surface**: A timeline calendar view of IDX IPO lock-up expirations, paired with downloadable PDF single-page risk memos for upcoming unlocks within 30 days.
7. **Why this can't be replicated by a US/global product**: US lockup trackers follow US SEC Form 4 and S-1 90/180-day rules under US GAAP. They do not map to OJK/IDX prospectus structures, POJK No. 25 lockup clauses, or IDX's asymmetric price tick/lot sizes.
8. **Effort to ship in 4 weeks solo**: Low (2 weeks to structure the IPO prospectus database & Sectors API pipeline; 1 week for timeline frontend; 1 week for alert triggers).
9. **Biggest ship risk**: Manual edge cases where special lock-up agreements (e.g., voluntary 1-year/2-year escrow extensions) are buried in prospectus footnotes rather than standardized metadata.
10. **Credit cost per run**: ~5 credits per day (tracking active ~40-60 IPOs listed in the prior 12 months with cached daily price/volume calls).

---

### Idea 3: FraksiBreak (IDX Tick-Border Transition & Institutional Flow Divergence)

1. **Idea name**: FraksiBreak: IDX Tick-Border Breakout & Foreign-Retail Divergence Radar
2. **One-sentence problem statement**: Indonesian retail traders struggle to determine whether a price breakout across a major IDX tick-size boundary (*Fraksi Harga*) is backed by genuine foreign institutional accumulation or an unsustainable retail pump headed straight for an Auto-Rejection (ARA/ARB) trap.
3. **Which IDX microstructure feature this exploits**: 
   - **IDX Fraksi Harga (Board Lot Tick Sizing)**: Rp 50–200 (Rp 1 tick), Rp 200–500 (Rp 2 tick), Rp 500–2,000 (Rp 5 tick), Rp 2,000–5,000 (Rp 10 tick), and >Rp 5,000 (Rp 25 tick). Crossing a fraksi threshold (e.g., Rp 199 to Rp 200, or Rp 1,995 to Rp 2,000) alters the capital required per lot to move the bid-ask queue by $2\times$ to $2.5\times$.
   - **Auto-Rejection Limits (ARA/ARB)**: $\pm 35\%$ for $< \text{Rp } 200$, $\pm 25\%$ for $\text{Rp } 200 - 5,000$, and $\pm 20\%$ for $> \text{Rp } 5,000$.
   - **Broker Flow Divergence**: Foreign institutional brokers (e.g., RX, BK, ZP, AK) accumulating quietly at the border of a fraksi tier vs. domestic retail churn brokers (YP, PD, CC) triggering false breakouts.
4. **What the product surfaces**:
   - **Fraksi Resistance/Support Wall Matrix**: Identifies stocks hovering within $2\%$ of a fraksi boundary (e.g., Rp 195–205 or Rp 490–510) and calculates the liquidity depth required to sustain the new tick step.
   - **Foreign Accumulation vs. Retail Churn Score**: Cross-references Net Foreign Flow with daily turnover volume to isolate stealth accumulation by tier-1 institutional brokers before the stock hits ARA.
   - **ARA Continuation vs. Exhaustion Alert**: Flags whether a stock that closed at ARA (+25%) has strong unmatched bid queues and institutional participation or is vulnerable to a next-morning opening ARB dump.
5. **Core workflow**:
   - Step 1: Query `GET /v1/companies/` to filter stocks currently trading within $\pm 3\%$ of key fraksi threshold zones (Rp 200, Rp 500, Rp 2,000, Rp 5,000).
   - Step 2: Fetch 30-day historical trading activity using `GET /v1/company/{ticker}/daily/` to extract price velocity, daily volume, and net foreign transaction value.
   - Step 3: Run `GET /v1/sector/{sector_name}/` to benchmark individual ticker momentum against sector-wide capital rotation (e.g., Energy/Mining vs. Banking).
   - Step 4: Calculate the Fraksi Resilience Index (Net Foreign Buying / Total Value Traded $\times$ Distance to Tick Shift) and generate real-time breakout setups.
6. **Output surface**: A live interactive screener with visual "Fraksi Transition Ladders", plus a daily Discord/Telegram channel pinging morning setups before the 09:00 WIB opening bell.
7. **Why this can't be replicated by a US/global product**: US markets trade in 1-cent decimal increments with no board lots or tiered tick-size step-ups. Global tools do not model the step-function liquidity dynamics of IDX's 5 distinct price bands or the Indonesian ARA/ARB daily circuit-breaker mechanics.
8. **Effort to ship in 4 weeks solo**: Medium (1.5 weeks for the fraksi mathematical engine & Sectors data pipeline; 1.5 weeks for screener UI; 1 week for alert delivery).
9. **Biggest ship risk**: Rapid intra-day intraday volatility near tick boundaries without tick-by-tick order book data, requiring reliance on Sectors' daily aggregates and end-of-day foreign flow indicators.
10. **Credit cost per run**: ~8–15 credits per scan run (focused on the ~150 most liquid IDX stocks trading near boundary zones, easily staying within the 1,000 credits hackathon budget).

---

## Angle: viral

### 1. IDX DividenHunter — Dividend Safety & Trap Inspector Card

**One-sentence distribution thesis:**  
Indonesian retail investors share this on Twitter/X and Stockbit Stream because dividend investing is retail's favorite passive-income obsession, and users love flexing safe double-digit yields while debating whether popular high-yielders are actually dividend traps.

**What the output artifact looks like:**  
A dark-mode 1080x1350 visual scorecard (auto-generated PNG image card + copy-pasteable Markdown table) featuring a prominent "Dividend Safety Score" (0–100), payout health gauges, and a binary badge: `🟢 CASH COW` vs `🔴 DIVIDEND TRAP RISK`.

**Sample output:**
```
📊 RAPOR DIVIDEN IDX: PTBA vs ITMG vs BJBR (FY2025/2026 Snapshot)
Generated via DividenHunter IDX

1. PTBA (Bukit Asam) — Skor Keamanan: 68/100 🟡 [WASPADA PAYOUT RATIO]
   • Est. Div Yield: 11.2% (Rp 285/lembar)
   • DPR Historis: 75% - 100% (Sangat Agresif)
   • FCF Coverage: 0.82x (Dividen melebihi Free Cash Flow operasional)
   • Net Cash: Rp 6.4 Triliun (Bantalan kas masih aman)
   👉 Vonis: Yield jumbo menggiurkan, tapi risiko pemangkasan dividen jika ASP batu bara turun lanjut.

2. ITMG (Indo Tambangraya) — Skor Keamanan: 88/100 🟢 [CASH COW JUARA]
   • Est. Div Yield: 13.8% (Rp 3.450/lembar)
   • DPR Historis: 65% - 70% (Konsisten)
   • FCF Coverage: 1.35x (Arus kas bebas melimpah, tidak pakai utang)
   • Net Cash: Rp 11.2 Triliun (Zero interest-bearing debt)
   👉 Vonis: Raja dividen teraman di sektor energi. Cash buffer tebal.

3. BJBR (Bank BJB) — Skor Keamanan: 42/100 🔴 [DIVIDEND TRAP ALERT]
   • Est. Div Yield: 9.1%
   • NPL Trend: Naik ke 1.8% | Loan-to-Deposit: 89%
   • Capital Adequacy Buffer: Menipis (Tier 1 CAR mendekati batas minimum regulator)
   👉 Vonis: Yield tinggi karena harga saham turun drastis. Risiko pemotongan dividen untuk perkuatan modal.

⚠️ "Dividen 10%+ jangan cuma dilihat yield-nya, cek FCF & Kas Perusahaan!" 
Download Card lengkap: dividenhunter.id/c/energy-q1
```

**Distribution loop:**  
A dividend-focused investor or finfluencer generates the card on the web app -> downloads and posts the PNG to Twitter/X or Stockbit Stream -> followers debate the "Dividend Trap" rating in replies -> new users click the watermark/URL to audit their own portfolio tickers.

**Core workflow:**  
1. User enters 1 to 4 IDX tickers (e.g., `PTBA, ITMG, BJBR`).
2. App queries Sectors API for dividend history, ratios, and balance sheet data.
3. System calculates the *Dividend Safety Score* (FCF / Total Dividends Paid, Net Debt / EBITDA, and 3-year DPR stability).
4. Headless image renderer (e.g., Satori / HTML5 Canvas) builds the shareable 1080x1350 card + pre-formatted social text.

**Sectors endpoints used:**  
- `/companies/{ticker}/dividends` (Historical DPS, payout dates, dividend yield)
- `/companies/{ticker}/financials` (Free Cash Flow, Operating Cash Flow, Total Debt, Cash & Equivalents)
- `/companies/{ticker}/ratios` (ROE, Payout Ratio, DER, Current Ratio)

**What makes it shareable:**  
*Contrarian / Fear Reduction mechanic.* Retail loves high yield but gets burned by capital loss post-cum-date. Calling out a popular ticker as a "Dividend Trap" sparks instant debate and retweets.

**Effort to ship in 4 weeks solo:** Low (Single-page Next.js app + Satori OG image generator + Sectors SDK).

**Biggest ship risk:** Retail ignoring the cash flow safety nuance and only focusing on the headline yield number if the visual card isn't starkly contrastive.

**Natural virality coefficient:** High.

---

### 2. WhaleFootprint IDX — Asing Silent Accumulation Radar

**One-sentence distribution thesis:**  
Indonesian retail investors share this on Telegram VIP channels, WhatsApp groups, and Twitter because Indonesian stock culture is deeply obsessed with "Bandarmology" and tracking foreign institutional flow ("Asing akumulasi diam-diam saat IHSG koreksi").

**What the output artifact looks like:**  
A compact, highly scannable daily/weekly image card (4:3 ratio for Telegram/Twitter previews) and copyable Telegram bot broadcast format featuring "Top 5 Silent Foreign Buys at 3-Year Valuation Lows".

**Sample output:**
```
🚨 RADAR ASING IDX: AKUMULASI DIAM-DIAM (Edisi Minggu ke-3, Agustus 2026)
"Asing belanja jumbo di saham diskon saat ritel panik cut loss"

Top 5 Inflow Asing Terbesar + Valuasi Murah:
┌──────┬──────────────┬────────────┬─────────────┬─────────────────┐
│ Kode │ Net Buy (5D) │  PER (TTM) │ PBV vs 3Y L │ Status Valuasi  │
├──────┼──────────────┼────────────┼─────────────┼─────────────────┤
│ BBRI │ +Rp 842.5 M  │ 10.8x      │ Diskon -24% │ 🟢 Bottom 5-Yr  │
│ MEDC │ +Rp 148.2 M  │  5.2x      │ Diskon -18% │ 🟢 FCF Yield 19%│
│ ASII │ +Rp 312.0 M  │  6.7x      │ Diskon -12% │ 🟢 Net Cash Pos │
│ CPIN │ +Rp  95.4 M  │ 18.2x      │ Netral      │ 🟡 Fair Value   │
│ PGAS │ +Rp  78.1 M  │  6.1x      │ Diskon -15% │ 🟢 PBV 0.7x     │
└──────┴──────────────┴────────────┴─────────────┴─────────────────┘

⚠️ RADAR DISTRIBUSI (Asing Guyur Diam-Diam):
• GOTO: Net Sell -Rp 410.5 M (Lanjut Net Foreign Outflow 4 minggu berturut-turut)
• BUMI: Net Sell -Rp 122.0 M (Margin Operasional tergerus)

💡 Sinyal Analis: Big money fokus cicil Big Banks & Oil Producers yang punya FCF tebal.
🔗 Cek ticker kamu gratis: whalefootprint.id
```

**Distribution loop:**  
Telegram channel admins and Twitter market commentary accounts generate the weekly recap card -> post it with `#Saham #IHSG #Bandarmology` -> retail traders forward the image directly into their private trading groups to validate their trade setups -> group members visit the site to screen their own watchlist.

**Core workflow:**  
1. Backend runs a daily scheduled job aggregating transaction flow and foreign activity.
2. Cross-references top net foreign buys with Sectors historical valuation ratios to filter out overhyped stocks.
3. Classifies tickers into *Silent Accumulation* (Net Buy high + PE/PBV at multi-year lows) vs *Silent Distribution*.
4. Generates an instant Telegram-ready message and downloadable card graphic.

**Sectors endpoints used:**  
- `/market/top-volume` or `/market/foreign-flow` (Net foreign transaction volume & turnover)
- `/companies/{ticker}/ratios` (Historical PBV, PER, EV/EBITDA bands)
- `/companies/{ticker}/financials` (Operating Margins, Net Debt to confirm fundamentals behind the flow)

**What makes it shareable:**  
*Smart-money validation & FOMO.* Retail traders don't want to feel left behind by institutional money ("Asing udah cicil, masa kita nggak?").

**Effort to ship in 4 weeks solo:** Low-Medium (FastAPI cron scraper + React dashboard with clipboard-ready Telegram markdown & canvas exporter).

**Biggest ship risk:** Sectors API latency or rate limits during market closing hours (16:00 WIB) when the rush of daily recaps is highest.

**Natural virality coefficient:** High.

---

### 3. IDX Sector Battlecard — 1-Click Peer Teardown Generator

**One-sentence distribution thesis:**  
Indonesian retail investors share this on Stockbit Stream and Twitter threads because head-to-head stock debates (e.g., "Mending ADRO atau ITMG?", "BBNI vs BMRI murah mana?") generate the highest comment volume, tribalism, and ego-driven retweets in the IDX community.

**What the output artifact looks like:**  
A visual head-to-head battlecard (1:1 square infographic card) comparing 2 to 4 peer companies side-by-side across Valuation, Profitability, Debt, and Shareholder Return, with automated "🏆 Category Winner" badges and an overall "Verdict Summary".

**Sample output:**
```
⚔️ HEAD-TO-HEAD BATTLECARD: ADRO vs ITMG vs PTBA
Sektor: Coal & Energy Producers | Data: Q2 2026

┌──────────────────────┬─────────────┬─────────────┬─────────────┬──────────┐
│ Metrik Finansial     │ ADRO        │ ITMG        │ PTBA        │ Winner   │
├──────────────────────┼─────────────┼─────────────┼─────────────┼──────────┤
│ Valuasi (PER TTM)    │ 4.8x        │ 5.3x        │ 6.1x        │ 🏆 ADRO  │
│ Valuasi (PBV)        │ 0.78x       │ 1.05x       │ 1.42x       │ 🏆 ADRO  │
│ Profitabilitas (ROE) │ 21.4%       │ 24.8%       │ 17.5%       │ 🏆 ITMG  │
│ Net Profit Margin    │ 28.2%       │ 22.1%       │ 14.8%       │ 🏆 ADRO  │
│ Div. Yield (Est.)    │ 10.5%       │ 14.2%       │ 11.2%       │ 🏆 ITMG  │
│ Neraca (Net Cash)    │ $1.7B       │ $740M       │ Rp 6.2T     │ 🏆 ADRO  │
│ Revenue Diversifikasi│ 32% Non-Coal│ 8% Non-Coal │ 2% Non-Coal │ 🏆 ADRO  │
├──────────────────────┼─────────────┼─────────────┼─────────────┼──────────┤
│ SKOR AKHIR           │ 5 POIN 🥇   │ 2 POIN 🥈   │ 0 POIN 🥉   │          │
└──────────────────────┴─────────────┴─────────────┴─────────────┴──────────┘

🥊 KESIMPULAN PERTANDINGAN:
• Jangka Pendek (Dividen Hunter): ITMG menang mutlak di yield & ROE.
• Jangka Panjang (Transisi & Kas): ADRO jauh lebih unggul di valuasi murah, bantalan kas jumbo, dan diversifikasi smelter/green energy.
• PTBA: Tertekan valuasi PBV relatif mahal dan beban capex logistik.

🔥 Siapa jagoan portofolio kamu?
Bikin Battlecard saham favoritmu di: battlecard.sahamidx.app
```

**Distribution loop:**  
A user inputs two rival tickers they hold or debate with friends -> web app spits out the high-res comparative battlecard image -> user tweets "Buat yang masih bingung mending pegang ADRO atau ITMG, ini data perbandingannya 📊" -> ticker holders quote-tweet to defend their holdings -> triggers new card generations.

**Core workflow:**  
1. User picks 2 to 4 tickers from the same sector (e.g., Banking: `BBCA, BBRI, BMRI, BBNI`, or Mining: `ADRO, ITMG, PTBA`).
2. App fetches real-time valuation, margins, cash, and dividend stats via Sectors API.
3. Logic engine compares metric-by-metric and awards categorical winner badges (`🏆`).
4. Generates an aesthetic 1:1 image card optimized for mobile display, plus an auto-formatted Stockbit/Twitter markdown post.

**Sectors endpoints used:**  
- `/companies/{ticker}/ratios` (PER, PBV, ROE, NPM, DER)
- `/companies/{ticker}/financials` (Revenue, Net Income, Cash, Total Debt)
- `/companies/{ticker}/dividends` (TTM DPS, Historical Yield)

**What makes it shareable:**  
*Tribalism and debate fuel.* Stock market participants identify strongly with their holdings. Giving them an objective, beautiful data referee card weaponizes social debate and encourages organic quoting.

**Effort to ship in 4 weeks solo:** Low-Medium (Template-driven React UI, HTML-to-Image / Sharp microservice, preset sector peer lists).

**Biggest ship risk:** Users disputing the automated "winner" logic if non-standard metrics (like one-off asset sale gains) distort a company's net income.

**Natural virality coefficient:** High.

---

