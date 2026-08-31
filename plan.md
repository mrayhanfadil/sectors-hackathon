# Plan: Institutional-Grade Equity Report for Retail — Multi-Agent System

> **Branch:** `feat/institutional-report` | **Status:** DRAFT — nunggu ide tambahan Fadiil + temen  
> **Locked idea:** Bikin equity research report kualitas institusi (kayak HP Sekuritas RATU 7 Jan 2026) tapi accessible buat retail investor. Multi-agent, tiap agent punya expertise.  
> **Benchmark PDFs (3+4 archetypes):** `RATU` (HP 7 Jan 2026, pure Oil) + `CDIA` (BCA 23 Jun 2026, conglomerate SOTP) + `MTEL` (KSI 27 Aug 2026, infra recurring) + `JPM 2026 Outlook` (52p strategy, JCI 9100) + 4 local global-like (Samuel BBCA, Maybank Strategy, BRIDS SOTP+DCF, Samuel Strategy). **Library 15 sources** in `references/source-library.md`.  
> **Deadline hackathon:** 30 Sep 2026 23:59 WIB — 29 hari lagi.

---

## 1. Why This Wins

**Problem:** Retail IDX cuma dapet headline/influencer, bukan report institutional yang ada DCF, peer comps, risk, asumsi eksplisit.

**Judges fit:** Real-world usability 40% + video storytelling 30% ("before: bingung, after: 1 PDF traceable") + technical depth 30% (multi-agent + deterministic math).

**Pivot dari Sektoral.id:** Dulu 31 demo showcase, sekarang deep 1 product kredibel. 7 sources (3 single + 1 strategy + 4 local) bikin template anti-overfit semua sektor.

## 2. Benchmark — 3 Archetype

### 2.1 RATU (HP Sekuritas, 7 Jan 2026) — Pure-Play Holding, 11 hal, 819KB

| Section | Isi | Replicate |
|---|---|---|
| Cover | RATU, IPO 1,150→10,650, Shares 2.71B, Float 31.2%, MSCI/IDX80/JII | Cover generator |
| Summary | 3Y: FY24A 129x P/E → FY26F 42.7x + revenue/EBITDA/net | Summary deterministic |
| Thesis | 4 narasi + angka: Bottom line +28% meski revenue -13%, Cepu 169k BOPD | Thesis Writer |
| Risk | 4 bucket generik: Commodity, Operator, Regulatory PSC/DMO, Natural decline | Risk Officer |
| Valuation | DCF WACC 8.4%, beta 0.7, ERP 6.9%, CoE 10%, CoD 3.5%, g5% → 7,880 + EV/EBITDA 22.6x → 6,960 | Modeler (Python) |
| Overview | History 2006→2023, IPO 88% ke RETJ/PJUC, BOD 6, PSC flow | Company Analyst |
| Exhibits 1-15 | Semua + source (Bloomberg, SKK Migas, BPS, FactSet) | Visualizer + provenance |
| Financials | P&L/CF/BS + Key Ratios 5Y, ROE 88%→30%, DER, Interest Coverage | Collector + Modeler |

### 2.2 CDIA (BCA Sekuritas, 23 Jun 2026) — Conglomerate 4-Pilar, 1.58MB, 1656 lines

| Section CDIA | Delta vs RATU |
|---|---|
| Cover + **vs JCI** | Relative perf YTD -62.9% abs / -30.9% rel + chart — RATU cuma price |
| 1Q segment mix | Energy 55% (23mn) / Logistics 34% (+44.7% fastest, 14mn) + one-off 15.9mn normalization |
| Valuation | **DCF 815 + DDM 810** (payout 40% 27-28 → 104% 28F). DCF table: CFO/CAPEX/Borrowing/FCFE/Discount |
| Peer SOTP | **4 peer tables per pilar** Energy/Water/Port/Logistics (POWR, Sembcorp, Westports, HATM etc) — RATU 1 table |
| Forecast revision | Revenue -37.4%, EBITDA -52.1%, Net -75.8% (M&A delay 2H26, fuel cost) |
| Ops specs | 120MW CCPP, 150kV, 2,000 l/s, 72 tanks 130k m³, 7 vessels 5-8600 DWT, TC/COA/spot |
| Risk | 7 buckets pillar-specific (sedimentation, gas supply, vessel damage, climate) — RATU generik |

### 2.3 MTEL (KSI/Kiwoom, 27 Aug 2026) — Infra Recurring (Tower/Fiber), 302 lines, 1.05MB

**Archetype ketiga — recurring infra, KPI operasional adalah hero (bukan cuma P&L).**

| Section MTEL | Isi Kunci | Delta vs RATU & CDIA |
|---|---|---|
| **Cover + Rating Box** | BUY, TP 635 vs 460 **+38%**, Prev TP 705, 3 **Key Takeaways** bullets, Shareholder pie TLKM 71.83%, MCap 37.5T, Shares 81.5Bn, Turnover, **ESG 2.23/3.03/5.08** | **Baru:** Key Takeaways box + ESG box + Shareholder structure — RATU/CDIA cuma table |
| **Price vs IHSG chart** | YTD Turnover + Value overlay | CDIA udah ada vs JCI, MTEL lebih visual |
| **Financial Highlights 6Y** | 2023A-2028F: Revenue 8.5T→10.7T, Net 2.0T→2.5T, EPS 24→32, EBITDA margin 54%→74%, NPM 23%, Div Yield 2.6%→3.7%, ROE 6%→7%, P/E 29→20x, P/BV 1.7→1.47, EV/EBITDA 16.3→8.47x | Lebih panjang horizon (6Y), fokus **yield + recurring margin** |
| **1H26 Performance Overview** | **Revenue split 4 segmen:** Tower leasing 3,833 (+1%), Fiber 309 (+8%), Tower-Related 299 (+15%), Reseller 251 (0%) + **QoQ + YoY** (2% y/y, 5% q/q), Gross -2%, EBIT -4%, EBITDA flat 3,510, Net +2% 1,111. Cost +6%, Finance -12% | **Baru:** QoQ + YoY dalam satu tabel, segment growth eksplisit, margin pressure narrative |
| **Operational KPIs (HERO)** | Tower 40,563 (+2%), Colocation 23,303 (+10%), Tenant 63,866 (+5%), Reseller tenants 2,650, **Tenancy Ratio 1.57x (vs 1.53)**, Fiber 59,239 km (+9%), add/less per quarter | **Beda kelas:** RATU/CDIA cuma produksi BOPD/kWh. MTEL KPI adalah **tenancy ratio + fiber km** — tiap sektor punya KPI sendiri. **Kita butuh KPI module per subsector** |
| **Catalyst Quantified** | **PST & UMT Merger** eff 1 Jul 2026 → opex/capex efficiency, tenancy >1.6x, FWA/fiberization/IoT/power. **Spectrum 700MHz & 2.6GHz** → TLKM 20/80 MHz, ISAT 20/60, EXCL 30/50 → **+3,000-3,500 tenants, +IDR 360-420bn annualized by FY27-29** | **Baru:** catalyst di-kuantifikasi jadi tenant & revenue — RATU/CDIA cuma narasi |
| **Valuation — DCF Detail** | EBIT 4,264→5,239, tax **6%**, EBIT(1-tax), +D&A 3,188→3,658, -Capex 2,981→2,437, +WC 762, **FCF 4,988 + Terminal 72,736**, Discount 1.00→0.62, Firm 71,344, Cash 1,643, Debt 21,430, Equity 51,556, Shares 81.5, **FV 630**. Assumptions: **WACC 10.10%, Beta 0.65, RF 6.96%, RP 8.89%, CoE 12.74%, CoD 6.00%, W.E 60.8%/W.D 39.2%, g 1.5%** | Paling transparan — semua asumsi di tabel (RATU cuma mention, CDIA FCFE only). **Template kita harus tampilkan semua** |
| **Blended Valuation** | **DCF 60% (51,556) + EV/EBITDA 40% (7,451×10x=74,513) = 60,739 → TP 635**. Weighted, bukan side-by-side. Margin of safety 15% | **Baru:** blended weighted — RATU side-by-side, CDIA DCF vs DDM terpisah. **Kita butuh blended engine** |
| **Historical Bands** | PBV 3Y + EV/EBITDA 3Y dengan **STD+2/STD+1/AVG/STD-1/STD-2** — "BELOW AVG" label | **Baru:** mean-reversion visual — belum ada di RATU/CDIA |
| **Financial Exhibits 2023A-2028F** | Income (Revenue, Costs, Gross, Operating, Interest, EBITDA, Pre-tax, Net, EPS), BS (Cash, Receivables, Fixed 51T, Total 58T, Liabilities, Equity, BVPS), CF (Net, Dep, WC, OCF, Capex, Investing, Financing, Dividends), **Ratios:** Growth, Margin (GPM/EBITDA/EBIT), Liquidity (Current 0.3→0.8, Quick, Cash 8%→57%), Leverage (LT D/E 0.34→0.46, DER 0.67→0.69, DAR, ICR 2→4x), Activity (Inventory turnover, AP days), Shareholder Return (Div Yield, Earnings Yield) | Paling lengkap — termasuk **Activity + Cash Ratio trajectory** |
| **Rating Guide** | BUY >+15%, TRADING BUY +5-15%, HOLD -10 to +15%, TRADING SELL -5 to -15%, SELL <-15% (12M ex-div) + Sector OVERWEIGHT/NEUTRAL/UNDERWEIGHT | Lebih granular dari RATU |
| **Risks** | Dependency on operators (Telkomsel), competition, satellite/Open RAN, regulatory, financing (rising rates), location/natural | Spesifik infra |


### 2.4 JPM Indonesia 2026 Outlook (J.P. Morgan, 2 Dec 2025) — Global Strategy, 52p, Henry Wibowo et al

**Archetype ke-4 — strategy/top-down, bukan single-stock. Ini yang bikin report kita ada market-level narrative kayak UBS/Goldman.**

| Section JPM | Isi Kunci | Delta vs RATU/CDIA/MTEL |
|---|---|---|
| **Cover: The return of animal spirit** | JCI **9,100 base / 10,000 bull / 7,800 bear** ( MXID 7,200/7,500/6,000), 8% EPS growth × 15x flat P/E, priced 28 Nov 2025 | **Index target bull/base/bear + methodology box** — RATU/CDIA/MTEL cuma fair value per share |
| **OW Sectors** | **Industrials, Materials, Consumer Staples/Discretionary, Property** (N: Financials/Comm Services/Healthcare, UW: Energy/Utilities) | **Sector allocation module** dengan OW/N/UW — belum ada |
| **Picks** | Large: BBCA/ASII/ICBP/GOTO/ANTM + SMID: ISAT/EMTK/JSMR/MAPI/PWON dengan criteria & rationale | **Top picks table + rationale** per sektor |
| **Flows** | Retail 58% ADTV IDR14.5tn (COVID-peak), JCI vs MXID/LQ45 divergence on conglomerate speculation, MSCI Adjusted Free Float 1Q26→May 26 risk, Foreign -US$2.2bn YTD / -2.6bn 2Y, FDI -28%, FPI -14bn, 44% foreign ownership UW since 2003; Institutional bid via Danantara US$1.5bn + pension | **Flows narrative + MSCI/foreign ownership box** |
| **Danantara Value-Up** | BPI+DAM+DIM segregation, US$12bn dry powder (0.8% GDP) + >US$14bn SWF, 9 priority sectors, SOE ex-banks +25% YTD re-rating | **Policy catalyst (Danantara) dedicated section** |
| **5 Thematics** | #1 Consumption recovery, #2 TSR improvement, #3 Re-attracting foreign, #4 Fiscal policy, #5 Danantara swing factor + 14pp sector economics (Banks, Consumer, Autos, Metals, Cement, Energy, Property, Coal, Healthcare, Internet, Telcos) | **Thematic framework** — bisa jadi Industry Outlook yang thematic, bukan cuma Brent/IEA |
| **Toc 52p** | p1 Cover+4 bullets, p3 Investment summary, p7 Lessons from 2025, p13-30 5 thematics, p30 Stock picks, p33 Economics+sectors, p47 Disclosures | Panjang = report strategy, bukan company update — template beda (multi-sector) |

**Yang kita serap:** Index target box (bull/base/bear + EPS×Multiple math), Sector OW/N/UW, Flows/MSCI risk box, Danantara catalyst, Thematic Industry Outlook.

### 2.5 Local Global-Like (4 PDFs public, verified downloadable)

| # | PDF | Pages | Valuation | Global-like score | Delta yang kita serap |
|---|---|---|---|---|---|
| L1 | **Samuel BBCA** RSH 21 Oct 2025 (`RSH-251021-English.pdf`, 8p, 598K) — BUY TP **9,600** (21.9% upside) | 8 | GGM-implied P/BV (P/E 16.9x, P/BV 3.3x, ROE 19.7%), **no WACC/g printed** | 5.5/10 — daily pack | **GGM shortcut:** kalau tidak ada DCF, pakai GGM `P/BV = (ROE-g)/(CoE-g)` — fallback engine kalau data WACC tipis |
| L2 | **Maybank Strategy 2025 Outlook** (`427903.pdf`, 74p, 3.6M) — JCI **7,900-8,600** (12.9-14.0x, 8% core profit growth), universe 35 stocks Fig62 | 74 | Top-down P/E band 12.9-14.0x | 8.5/10 — **60+ exhibits**, rate-sensitive weights, EV/EBITDA bands | **Outlook playbook:** 74p strategy dengan 60+ exhibits sebagai template `Market Outlook` chapter |
| L3 | **BRIDS Morning 18 Nov 2024** (`35772`, 12p, 1.8M) — ADRO SOTP **US$6.1bn (AADI) + US$5.3-7.0bn post-spin (holdco discount)** + **GOTO DCF TP Rp90 @ 6% CAGR FY24-34 GTV** | 12 | **SOTP + DCF dual** — best disclosure | 8.0/10 — bank monthly table (mom/yoy vs target) | **SOTP holdco discount + spin-off bridge** (kayak CDIA tapi untuk demerger) |
| L4 | **Samuel Strategy Dec 2023** (`Strategy-Report-Dec-En.pdf`, 26p, 2.6M) — JCI **7,600 base / 7,300 bear / 8,000 bull** (14.0x, 3.6/8.6/13.6% growth, 5Y avg 22.1x) | 26 | P/E 14.0x base | 7.5/10 | **Bear/base/bull growth table** dengan 3 skenario + 5Y avg reference |

**Source library:** `references/source-library.md` — 15 ranked (P0 4 downloadable: CLSA HRTA 9p, Bahana Construction 19p, DBS PGAS Weekly 12p, CGSI DBS 11p; P1 6 Scribd; P2 5 gated). Liat file untuk URL + access status.

### 2.6 Synthesis — DNA Institutional + Upgrade List

**DNA yang sama di 3 PDF:** cover + summary snapshot, thesis narasi + angka, risk buckets, 2 metode valuasi, exhibits dengan source, financials 5-6Y, disclaimer OJK, asumsi WACC/beta eksplisit.

**Yang beda & wajib kita serap (8 → 17 upgrades):**

| # | Upgrade | Sumber | Prioritas |
|---|---|---|---|
| 1 | **Adaptive Valuation:** DCF selalu + 2nd otomatis: `infra/dividend → DDM, conglomerate → SOTP, infra recurring → blended 60/40, else → EV/EBITDA` | RATU + CDIA + **MTEL blended** | **P0** |
| 2 | **Segment Breakdown %** + pie (hide kalau single-pilar) | CDIA 55/34% + **MTEL 4 segmen** | **P0** |
| 3 | **Stock perf vs JCI/IHSG** (YTD/1M/3M/12M abs & rel) | CDIA + MTEL chart | **P0** |
| 4 | **Forecast Revision block** (delta % vs prior) | CDIA -37% | **P0** |
| 5 | **Leverage lengkap:** Gearing, Net Gearing, Debt/EBITDA, ICR, Current/Quick, Cash Ratio trajectory | CDIA 170% + MTEL 0.3→0.8 | **P0** |
| 6 | **Source di tiap exhibit** | Semua | **P0** |
| 7 | **Operational KPIs per subsector** (baru, HERO untuk infra): Tower/colocation/tenancy/fiber km (MTEL), BOPD (RATU), MW/m³/DWT (CDIA) | **MTEL** | **P1 — Baru** |
| 8 | **Catalyst quantification** (tenants + IDR revenue by FY) | **MTEL** 3k + 360-420bn | **P1 — Baru** |
| 9 | **Blended valuation table** (weight 60/40) + MoS 15% | **MTEL** | **P1 — Baru** |
| 10 | **Historical valuation bands** (PBV & EV/EBITDA 3Y, STD±2, AVG) | **MTEL** | **P1 — Baru** |
| 11 | **Key Takeaways box** (3 bullets di cover) + **Shareholder pie** + **ESG box** | **MTEL** | **P1 — Baru** |
| 12 | **QoQ + YoY table** (1H vs 2Q, y/y & q/q) + quarterly momentum narasi | **MTEL** | P2 |
| 13 | One-off normalization + Activity ratios + granular Rating Guide | CDIA + MTEL | P2 |
| 14 | **Index target bull/base/bear + EPS×Multiple math** (JCI 9,100/10,000/7,800, 15x, 8% EPS) | **JPM Strategy** | **P1 — Baru** |
| 15 | **Sector OW/N/UW + Top picks + Flows/MSCI + Danantara Value-Up** | **JPM** | **P1 — Baru** |
| 16 | **GGM fallback `P/BV=(ROE-g)/(CoE-g)` + SOTP holdco discount + spin-off bridge** | **Samuel/BRIDS** | **P1 — Baru** |
| 17 | **Retail Social Sentiment (X P0 + Reddit P0 + Stockbit, gauge 0-100 + timeline + top 3 narratives)** — Threads P1, IG/FB skip | **Fadiil Ide 3** | **P1 — Baru** |

## 3. Architecture — 7+1 → 11+1 Agents (incl. News Harvester + Adversarial + Social Sentiment)

```
[Ticker: RATU single | CDIA SOTP | MTEL infra]  (+ Strategy JCI 9100 overlay + Sentiment) 
        ↓
  ┌─ Data Collector (parallel, Sectors API v2) ─┐  ┌─ News Harvester (parallel, Google) ─┐  ┌─ Social Sentiment (parallel, X+Reddit) ─┐
  │  via web_search + web_extract, 0 credit     │  via xurl + web_search, 0 credit       │
  │  • overview, financials 5-6Y, prices, segments│
  │  • operational KPIs per subsector (baru)      │
  │  • peers PER PILAR (SOTP) atau universe       │
  │  • JCI benchmark + historical multiples 3Y    │
  │  • dividends, holders, ESG proxy              │
  └───────────────────┬───────────────────────────┘
                      ↓ (blocking)
          ┌─ Financial Modeler (THE BRAIN) ─┐
          │  wacc(), dcf(), ddm(),          │
          │  ev_ebitda(), sotp(), blended() │
          │  ratios() incl. gearing/debt/ebitda/activity │
          │  + historical_bands()           │
          └───────────┬─────────────────────┘
                      ↓ (parallel)
  ┌──────────────────────────────────────────────────────────────┐
  │ Company Analyst │ Industry/Macro │ Risk Officer │ KPI Analyst│
  │ (bisnis+ops     │ (Brent/IEA/    │ (pillar/     │ (baru:     │
  │  specs/MW/DWT)  │  SKK Migas/    │  sector-     │  tenancy,  │
  │                 │  regulator)    │  specific)   │  fiber km) │
  └────────┬────────┴───────┬────────┴──────┬───────┴──────┬─────┘
           └────────────────┼───────────────┼──────────────┘
                            ↓
                   Thesis Writer (segment growth + one-off adj + catalyst quantified)
                            ↓
                   Visualizer (mix pie, leverage trajectory, vs JCI, PBV/EV bands)
                            ↓
                   SOTP Aggregator (conglomerate only)
                            ↓
                   Adversarial Red Team (Challenge & Defense) — 2 rounds max
                   • challenger: 'WACC 8.4% too low vs MTEL 10.1%?' / 'Tenancy 1.57 over-optimistic?'
                   • defender must: defend(evidence: calc+source) OR concede(correction)
                   • arbiter: Critic checks vs assumptions/valuation/news.json → verdict
                   • log: debate.json {round, challenger, claim, defense, verdict}
                            ↓
                   Orchestrator + QA Critic (arbiter, anti-sycophancy)
                   • angka narasi == tabel? blended weight sum 100%?
                   • segment % sum 100%? DDM payout math?
                   • KPI tenancy = tenant/tower? source per exhibit?
                   → REJECT jika mismatch
                            ↓
                   PDF Renderer (template switch: single vs SOTP vs infra)
```

**Anti-halusinasi + Anti-sycophancy:** `JANGAN hitung. Panggil calc_*()`. `JANGAN setuju karena user bilang.` Defender harus `defend(evidence)` kalau benar — kutip `valuation.json` + Exhibit + `news.json url+date` — atau `concede(correction)` kalau salah. Critic REJECT kalau `agree without evidence`.

## 4. Data Layer

**Sectors API v2 (hemat) + Google News (0 credit):**
- `overview` (holders CDIA 60%, MTEL TLKM 71.83%), `financials?sections=income,balance,cashflow` 5-6Y, `prices?range=5y` + `segments` kalau ada
- `peers` — single (RATU 22) atau SOTP 4 pilar (CDIA 4 credit) atau infra comps (MTEL: TBIG, TOWR)
- `operational_kpis` — tenancy/fiber/tower (MTEL), BOPD (RATU), MW/m³ (CDIA) — kalau API belum ada → synthetic + disclosed proxy
- `index/JCI/prices` + historical multiples 3Y (untuk bands)
- **News Harvester:** `web_search(ticker + 'IDX target price' / 'earnings' / 'Danantara catalyst')` → `web_extract(url)` → dedup + tier (T1 IDX/Kontan/Bisnis, T2 Reuters/Bloomberg, T3 blog) → `news.json` (url/date/title/source/tier/snippet/relevance) — max 8, last 30d, cache 1h
- **Social Sentiment:** `search_social(ticker, days=14, max=8)` → X via `xurl` + Reddit via `web_search site:reddit.com` + Stockbit (IDX) → dedup + relevance → `sentiment.json` (platform/url/date/text/sentiment/score/relevance) + gauge 0-100 + top 3 narratives + timeline — cache 1h — Threads P1 (needs token), IG/FB skip
- Cache 4h + synthetic fallback

**Synthetic:** SQLite `data/sectors.db` seed=42, 49 tickers + JCI + segments + KPI synthetic (tenancy ratio, fiber km). `data/peers.json` dual mode single/SOTP/infra. `data/assumptions/{ticker}.json` — WACC, beta, RF, RP, g, payout, prior forecast, blended weights.

## 5. Output — Adaptive 3 Templates

- **Engine:** HTML → PDF (Playwright), header RESEARCH + tanggal, footer OJK, source per exhibit.
- **Template switch:**
  - `single` (RATU): 9 sections, 1 peer table, DCF+Multiples
  - `sotp` (CDIA): 10 sections + Segment + SOTP, 4 peer tables, DCF+DDM, Revision
  - `infra` (MTEL): 10 sections + **KPI Operational + Catalyst Quant + Blended + Bands + Key Takeaways + ESG**
  - Logic: `if segments>1 → sotp, elif subsector infra/telco → infra, else single`
- **Challenge UI:** `/report/[ticker]/challenge` — user ketik kritik, agent relevan jawab dengan sitasi (Exhibit + url+date), tidak boleh sycophancy. Log `debate_user.json`.
- **Sentiment UI:** `/report/[ticker]/sentiment` — gauge 0-100 (bear-bull) + top 3 retail narratives + timeline (how narrative evolved) + per-platform breakdown (X vs Reddit) + disclaimer `sentiment ≠ advice`.
- **Wajib charts (7):** Revenue mix, Trend, Margin, Leverage trajectory, ROE/ROA, vs JCI, Peer multiples (+ Bands kalau infra), KPI (tenancy/fiber).

## 6. Tech Stack

- Frontend Next.js `/report/[ticker]` + `/outlook` + PDF preview + template switch | Backend FastAPI + Sectors proxy (KV 4h) | DB SQLite | PDF HTML+Tailwind+Chart.js (4 templates: single/SOTP/infra/strategy) | Deploy Pages.dev
- Repo: `data/peers.json`, `scripts/{sectors_api,dcf,ddm,sotp,blended,bands,ggm,news,adversarial,social}.py`, `agents/{collector,news_harvester,social_sentiment,modeler,analyst,industry,risk,kpi,writer,visualizer,critic,sotp,adversarial}.py`, `templates/{report_single,sotp,infra,strategy}.html`, `references/{global,jpm*, local-global-like/*, source-library.md}`, `app/`, `demos/report/assets/api-data.js`

## 7. Phased Build (29 hari ke 30 Sep)

| Phase | Tanggal | Deliverable | Owner |
|---|---|---|---|
| **P0 — Scaffold** | 31 Aug – 1 Sep | Branch + plan.md (RATU+CDIA+MTEL+JPM+L1-4) + `dcf/ddm/sotp/blended/bands/ggm.py` + `peers.json` (3 modes) + 4 HTML templates | DONE |
| **P1 — Data** | 2 – 6 Sep | Sectors proxy + SQLite (segments+KPI+JCI+3Y+flows) + 5 tickers E2E (RATU, CDIA SOTP, MTEL infra, BBCA GGM, ADRO SOTP) + `source-library.md` (15 sources) | Collector |
| **P2 — Modeler** | 7 – 10 Sep | DCF+DDM+SOTP+Blended+bands+GGM; RATU 7,880/6,960 + CDIA 815/810 + MTEL 630/635 + BBCA GGM + JPM JCI 9,100 (8%×15x) reproducible | Modeler |
| **P3 — Agents** | 11 – 18 Sep | 11 agents + SOTP Aggregator + Strategy Thematic (JPM 5 thematics) + Adversarial Red Team (2-round duel + user challenge) + Social Sentiment (X+Reddit P0) + Critic arbiter | Multi-agent |
| **P4 — PDF + UI** | 19 – 23 Sep | 4 templates PDF (single/SOTP/infra/strategy) + `/report/[ticker]` + `/outlook` + Key Takeaways/ESG/Revision/Flows/MSCI boxes | Frontend |
| **P5 — Polish & Video** | 24 – 29 Sep | 5 tickers showcase (RATU/CDIA/MTEL/BBCA/ADRO) + strategy page, video, audit swarm 3 AGY | All |
| **Submit** | 30 Sep 23:59 WIB | Commit freeze, public 90 hari | — |

## 8. Credit Budget (1,000)

- Universe 1 credit >> loop 22 (hemat 95%). SOTP 4 pilar = 4 credit vs 88 loop. Infra peers 1 credit.
- `sections=` potong 50%, cache 4h, synthetic fallback.
- Estimasi: 5 tickers × ~10-12 credits (KPI+JCI+bands+flows) = 50-60 credits (aman, masih <6% dari 1,000).

## 9. Risks & Mitigations

| Risk | Mitigasi |
|---|---|
| LLM halusinasi P/E | Critic grep + Python only |
| Exhibit tanpa source | Template wajib Source, CI cek |
| SOTP sum mismatch | Aggregator + Critic 100% check |
| Blended weight !=100% | Critic sum check (60+40) |
| KPI tenancy salah hitung | Formula tenant/tower, Critic validate |
| Bands tanpa 3Y data | Fallback synthetic 3Y + disclosed |
| Credit habis | Synthetic DB |
| News stale / hoax | Tier filter + date check + Critic url+date per klaim |
| Agent sycophancy (asal terima) | Adversarial must defend/concede with evidence; Critic REJECT agree-without-evidence |
| Sentiment noise / brigading / spam | Dedup + relevance + platform tier (X/Reddit P0, Threads P1), gauge with confidence, Critic url+date check, disclaimer |
| IG/FB scrape blocked | SKIP for MVP — use X+Reddit+Stockbit; document as P2 |

## 10. Decision Log

| Keputusan | Kenapa | Alternatif ditolak |
|---|---|---|
| Deep 1 product bukan 31 demo | Judges 40% usability | 31 demos shallow |
| 8+1 agents + KPI + SOTP + Strategy | MTEL KPI, CDIA SOTP, JPM thematics | Single peer table |
| Adaptive 2nd + blended + GGM | RATU multiples, CDIA DDM, MTEL blended 60/40, BBCA GGM | Fixed DCF+multiples |
| KPI module per subsector | MTEL tenancy 1.57 & fiber km adalah thesis | Financials only |
| Catalyst quantification | MTEL 3k tenants + 360bn itu alpha | Narasi tanpa angka |
| Historical bands | Mean-reversion institutional | Single point multiple |
| Key Takeaways + ESG + Holder pie | Cover institutional MTEL | Cover plain |
| 4 templates (single/SOTP/infra/strategy) | Tiap archetype layout beda (JPM 52p strategy beda) | 1 template |
| Python deterministic | Semua WACC/beta/ERP/payout eksplisit | LLM math |
| News Harvester (Google) | Narasi + asumsi butuh freshness — Sectors EOD only, news kasih catalyst timeline | Tanpa news (cuma Sectors) |
| Adversarial Challenge & Defense | Biar report kredibel — agent harus defend pakai bukti, bukan yes-man; user bisa challenge post-PDF | Tanpa adversarial (agent asal terima) |
| Social Sentiment (X+Reddit P0, Threads P1, IG/FB skip) | Retail narrative tracker — gimana narasi berkembang di retail, bandingin thesis vs crowd | Tanpa sentiment (cuma news+Sectors) |
| Pages.dev | Fadiil prefer | workers.dev |

## 11. Open — Ide Tambahan Fadiil + Temen

- [x] **Ide 1 (Fadiil, 31 Aug 2026) — News Harvester Agent (Google Search) — APPROVED, POSSIBLE** → Agent khusus search berita di Google sebagai **narasi + asumsi**. Design: `agents/news_harvester.py` → `search_news(ticker, days=30, max=8)` via `web_search` + `web_extract` → dedup + tier filter (Tier1: IDX disclosure/Kontan/Bisnis/IDX Channel, Tier2: Reuters/Bloomberg/JP, Tier3: blog) → output `news.json` {url, date, title, source, snippet, tier, relevance} → feed ke **Thesis Writer** (catalyst timeline), **Risk Officer** (regulatory/MSCI risk), **Industry/Macro** (themantic), **Modeler** (assumption delta, e.g., Danantara $12bn → flows). Critic wajib cek `url+date` per klaim. Cost: 0 Sectors credit.
- [x] **Ide 2 (Fadiil, 31 Aug 2026) — Adversarial Challenge & Defense — APPROVED** → Agents **tidak boleh asal terima** critique. Harus **defend pakai bukti** kalau benar, **concede + revise** kalau salah. Design: `agents/adversarial.py` (Red Team) → 2 loops: **(a) Internal duel** pre-PDF: challenge Thesis/Valuation/Risk masing2 1 claim (e.g., 'WACC 8.4% too low vs MTEL 10.1%?'), target agent must `defend(evidence: calc + source)` or `concede(correction)`; Critic arbiter cek evidence vs `assumptions.json/valuation.json/news.json`; max 2 rounds; log `debate.json` {round, challenger, claim, defense, verdict}. **(b) User challenge** post-PDF: UI `/report/[ticker]/challenge` — user ketik kritik, agent yang relevan jawab dengan sitasi (Exhibit + url+date), tidak boleh sycophancy. Anti-pattern: `agree because user said` = REJECT. 
- [x] **Ide 3 (Fadiil, 31 Aug 2026) — Social Media Sentiment (Retail Narrative Tracker) — APPROVED, PARTIAL** → Feasible **X (P0)** via `web_search site:x.com` + `xurl` skill + **Reddit (P0)** via `web_search site:reddit.com` + `web_extract` + **Stockbit** (IDX-specific, higher signal than IG). **Threads P1** via `threads-meta-api` (needs token, fallback Google index). **IG/FB P2 — SKIP for MVP** (login wall, anti-scrape, ToS risk). Design: `agents/social_sentiment.py` → `search_social(ticker, days=14, max=8)` → queries `"$BBCA"`, `"saham BBCA"`, `"BBCA bullish"` per platform → dedup + relevance → output `sentiment.json` {platform, url, date, text, sentiment: bull/bear/neutral, score 0-100, relevance} + aggregated `gauge 0-100` + `top 3 narratives` + `timeline`. Feeds: Thesis Writer (retail narrative vs thesis), Risk Officer (hype/crowded risk), Adversarial (defense vs crowd). Critic checks `url+date` per claim, REJECT if hallucinated. Cost: 0 Sectors credit. UI: `/report/[ticker]/sentiment` gauge + timeline. Disclaimer: sentiment ≠ advice.
- [ ] Track lock-in: T03 Market Intel paling pas (RATU/CDIA/MTEL semua research), T01 AI Agents kalau tonjolin multi-agent orchestration — decide?
- Ticker awal: RATU (single) + CDIA (SOTP) + MTEL (infra) + BBCA (GGM/bank) + ADRO (SOTP spin-off) — **quintet** cover semua engine; JPM JCI 9,100 untuk market overlay
- Bahasa PDF: ID/EN toggle? —
- Prior forecast: simpen v1 buat revision demo atau initiation only? —
- ESG: include box atau skip dulu (P2)? —

---

**Next step:** 3 ide Fadiil locked (News Harvester + Adversarial + Social Sentiment). Gas scaffold 8 engines (dcf/ddm/sotp/blended/bands/ggm/adversarial/social) + 4 templates + debate + sentiment UI di branch ini. Library 15 sources ready.
