# AMMN-FILLV - Content Audit & Data Provenance Verification Matrix

**Execution Date**: 2026-09-12 WIB  
**Workspace**: `/home/fadil/projects/sectors-hackathon` (branch: `feat/institutional-report`, commit `a57e3ca`)  
**Lane**: AGY Audit Lane (AMMN-FILLV)  
**Target File**: [`output/ammn_report_typst.pdf`](file:///home/fadil/projects/sectors-hackathon/output/ammn_report_typst.pdf) (Post-FILLT live render, 13 physical pages, Typst engine)  
**Source Evidence**:
- [`output/cache/ammn_fill/FILL_MAP.md`](file:///home/fadil/projects/sectors-hackathon/output/cache/ammn_fill/FILL_MAP.md) (Sibling lane harvest map, kanban `t_2c5f420e`)
- [`output/cache/ammn_fill/CALL_LOG.md`](file:///home/fadil/projects/sectors-hackathon/output/cache/ammn_fill/CALL_LOG.md) (Sectors API v2 call audit)
- [`data/assumptions/AMMN.json`](file:///home/fadil/projects/sectors-hackathon/data/assumptions/AMMN.json) (15 gate keys + mid-cycle constituents + WACC build)
- [`agents/adk/agents/instructions.py`](file:///home/fadil/projects/sectors-hackathon/agents/adk/agents/instructions.py) (Writer & Critic institutional rules)
- [`docs/ammn-slides/slide1-cover-spec.md`](file:///home/fadil/projects/sectors-hackathon/docs/ammn-slides/slide1-cover-spec.md) (Tie-out contract source of truth)

---

## Executive Summary & Final Verdict

| Audit Item | Scope & Rule | Evaluation | Evidence Reference |
|---|---|---|---|
| **(a) Zero Placeholders** | Zero `"lengkapi fixture"`, `"Ringkasan eksekutif belum tersedia"`, or `"-"` where a mapped key promised data. | **FAIL (Residual Template Placeholders)** | `"lengkapi fixture"` count = 0; `"Ringkasan eksekutif belum tersedia"` count = 0; all 22 promised mapped keys are populated. However, 7 unmapped visual placeholders remain from template fallbacks (4 dashes in Exhibit 8 DCF card at `P6L12-15`, 3 literal `Engine Chart Renderer (Sectors pending)` strings at `P5L3`, `P9L22`, `P9L26`). |
| **(b) Number Traceability** | Every thesis, valuation, and peer number traces to `FILL_MAP.md` or `AMMN.json`. | **FAIL (38 Untraced Valuation Numbers)** | Pages 1–6 and 9–13 trace 100% to live harvested Sectors data and assumptions. However, Page 7–8 contains 38 untraced mock numbers in Exhibit 12 (Sensitivity matrix), Scenario Analysis, and EV Bridge due to unpopulated `dcf_deep_dive` sub-keys in `ammn_fill.py`. |
| **(c) Gated TP & Anchor** | TP == ONE gated FV with anchor named; rating follows gates. | **PASS** | Target Price is exactly Rp 147 (live DCF FV). Anchor is named in cover summary (`P1L20-23`: *"berjangkar pada SATU FV engine (DCF/EV-blend)"*). Rating is `Review Required`, strictly adhering to Gate 5 output sanity flag (`P1L57-60`: upside -97.0% out of band). |
| **(d) Tie-Outs & Identities** | Slide-3 numbers == Exhibit-3; IS/BS/CF tie-outs hold. | **PASS (Clean)** | Exhibit 3 (Page 2) matches Slide 3 Financial Highlights (Page 4) cell-for-cell for all 5 overlapping years (FY21A–FY25A) across Revenue, EBITDA, Net Profit, EPS, and PER. Net Profit ties out across IS, FH, and Ex 3. CF closing cash ties out to BS Cash for all 6 years (FY20A–FY25A). BS accounting identity Assets = Liabilities + Equity holds. Minorities derived tie-out holds. |
| **(e) News Claims Grounding** | News claims carry url+date. | **PASS** | `report_data.json:news` carries 8 items, 100% with citable `url` and `date`. Narrative claims in thesis, risks, and catalysts cite exact transaction dates and media dates (`P5L24`, `P13L7-10`, `P13L13`, `P13L23`). Printed exhibits display `Source: Company, Team Estimates` per `HOUSE_FORMAT_RULE`. |
| **(f) No Synthetic Markers** | Zero synthetic or invented data markers. | **FAIL (Template Fallback Markers)** | Page 7 EV Bridge asserts `(-) Total Utang Berbunga: -0 Bebas Utang` and `(+) Kas: +500` for a company with Rp 110.79 tn gross debt and Rp 13.85 tn cash. Sensitivity table centers on mock WACC 11.83% and g 5.00% (Base Rp 4.562) instead of AMMN's 13.77% / 2.5%. |
| **Credit Audit** | Total billable spend vs 1,000-credit budget. | **PASS (22 / 1000 credits)** | 13 credits from FILLD (`CALL_LOG.md`) + 9 credits prior AMMN assumptions spend (`sectors_cache` / `/tmp/ammn_work`). 0 credits in FILLT, 0 in FILLV. Total spend: **22 credits** (978 credits remaining, 2.2% consumed). |

### Overall Verdict
```
Verdict: FAIL-2 (placeholders 7, uncited numbers 38, tie-outs ok)
```
*(Alternative strict DATA_CONTRACT classification: `FAIL-2 (placeholders 0, uncited numbers 38, tie-outs ok)` if placeholders are measured strictly against promised keys in `FILL_MAP.md`).*

---

## 1. Check (a) - Placeholders & Honest-Empty Ledger

### 1.1 Forbidden Placeholder String Scan
Extracted full-text search against [`output/ammn_report_typst.pdf`](file:///home/fadil/projects/sectors-hackathon/output/ammn_report_typst.pdf):

| Forbidden String | Target Section | Occurrences in Rendered PDF | Status |
|---|---|:---:|:---:|
| `"lengkapi fixture"` | Cover Summary / Thesis / Global | **0** | PASS |
| `"Ringkasan eksekutif belum tersedia"` | Cover Slide 1 | **0** | PASS |
| `"fixture"` | Global text | **0** | PASS |
| `"placeholder"` | Global text | **0** | PASS |
| `"Lorem ipsum"` | Global narrative | **0** | PASS |

### 1.2 Mapped Keys Promise Verification (FILL_MAP.md Delivery)
Audit of the 22 keys marked `FILLED` in [`output/cache/ammn_fill/FILL_MAP.md`](file:///home/fadil/projects/sectors-hackathon/output/cache/ammn_fill/FILL_MAP.md):

| # | Mapped Key | Promised in `FILL_MAP.md` | Rendered Value in PDF | PDF Page & Line | Verdict |
|:---:|---|---|---|---|:---:|
| 1 | `meta.company_name` | PT Amman Mineral Internasional Tbk. | PT Amman Mineral Internasional Tbk. | `P1L4-5` | PASS |
| 2 | `meta.sector` | Basic Materials - Metals & Minerals | Basic Materials - Metals & Minerals | `P1L3` | PASS |
| 3 | `cover.summary` | 4-bullet thesis prose | 4-bullet prose (tembaga-emas Batu Hijau, FY24 Rp 43,04 tn...) | `P1L9-24` | PASS |
| 4 | `cover.rating_box.price` | Rp 4,860 | Rp 4860 | `P1L45`, `P1L66` | PASS |
| 5 | `cover.rating_box.tp` | Rp 147 | Rp 147 | `P1L44`, `P1L69` | PASS |
| 6 | `cover.shares.outstanding` | 72.5 bn shares | 72.5 bn | `P1L72` | PASS |
| 7 | `cover.market.market_cap` | Rp 352.44 T | Rp 352.44 T | `P1L75` | PASS |
| 8 | `cover.market.range_52w` | Rp 2,710–8,500 | Rp 2,710–8,500 | `P1L81` | PASS |
| 9 | `cover.shareholders` | 12 major shareholders | 12 rows rendered (Sumber Gemilang 32.17%, Public 25.26%...) | `P1L25-40` | PASS |
| 10 | `cover.vs_jci` series | 90D 62-session chart series | Exhibit 2: Kinerja Harga vs IHSG (90D, 15 Jun–11 Sep 2026) | `P1L41`, `P2L3` | PASS |
| 11 | `key_financials` | 5Y Key Financials (FY21A–FY25A) | Exhibit 3: 9 rows x 5 actual years | `P2L5-19` | PASS |
| 12 | `kpis` | 4 operational KPIs (same-basis) | Pendapatan, EBITDA, D/E, Interest Coverage FY2025 | `P3L7-25` | PASS |
| 13 | `financial_highlights` | 6Y Financial Highlights (FY20A–FY25A) | 9 rows x 6 actual years | `P4L5-19` | PASS |
| 14 | `thesis` | 4 investment pillars | 4 numbered pillars with detailed quantitative citations | `P5L4-24` | PASS |
| 15 | `valuation.methods` | DCF + Multiple EV/EBITDA | DCF (13.77%, 2.5%) Rp 147; EV/EBITDA (28.42x) Rp 5,873 | `P6L5-28` | PASS |
| 16 | `valuation.midcycle` | 3Y Mid-cycle EBITDA cross-check | Exhibit 10: 8 rows (EBITDA 3Y avg Rp 18.40 tn -> Rp 5,873) | `P7L7-20` | PASS |
| 17 | `dcf_deep_dive.wacc_build` | 9-row WACC parameters | Exhibit 11: Rf 7.10%, ERP 6.69%, Beta 1.407 -> WACC 13.77% | `P7L22-37` | PASS |
| 18 | `peers` | 9 comparable peers + Median/Avg | Exhibit 13: 9 peers, Median PE 12.51, Average PE 1003.88 | `P9L5-17` | PASS |
| 19 | `financial_statements` | 6Y Comprehensive Financials | Exhibit 16 (IS), Exhibit 17 (BS), Exhibit 18 (CF), Exhibit 19 (Ratios) | `P11L5-P12L32` | PASS |
| 20 | `risks` | 6 risk buckets | 6 numbered risk cards (Insider, Komoditas, Leverage, FCF, Indeks, Valuasi) | `P13L5-29` | PASS |
| 21 | `catalysts` | 4 quantified catalysts | Cluster-buy direksi, Reli tembaga, Rebalancing GDX, Smelter PAC | Embedded in Thesis/Risks | PASS |
| 22 | `sentiment` | Flow posture 90d/30d | Net foreign 90d -0.37 tn, 30d +0.24 tn, broker flows | `P5L23-24` | PASS |

### 1.3 Honest-Empty Gap Ledger (GAP G1–G10 Verification)
Audit confirming that unavailable data points stay loud, honest, and uninvented:

| Gap # | Description | Representation in Rendered PDF | Evidence / Justification | Status |
|:---:|---|---|---|:---:|
| **G1** | `cover.vs_jci` YTD % | Substituted with 90D window (+28.6% vs +4.6%, rel +24.0 pp) | Sectors API caps `/daily/` and `/index-daily/` at 90 days; window 253d unreachable | PASS (Honest) |
| **G2** | Free Float % | Displayed as `-` (`P1L77`) | Screener projects only `symbol` + `name`; Public bucket 25.26% is not IDX free float definition | PASS (Honest) |
| **G3** | FY2025 Segments | FY2024 and FY2023 presented | GET `/company/get-segments/AMMN/?financial_year=2025` returns HTTP 404 (CALL_LOG #11) | PASS (Honest) |
| **G4** | Mining Extension | Qualitative disclosure (`P3L4`) | AMMN absent from Sectors `/mining/companies/` universe (coal-focused) | PASS (Honest) |
| **G5** | Forward Estimates | Projections null, consensus directional only (`P1L20`) | `valuation.forward_pe` and `future.company_growth_forecasts` null in API | PASS (Honest) |
| **G6** | Dividend History | Excluded from catalyst; DPS = 0 | AMMN paid zero dividends since July 2023 IPO; `corporate_actions.dividend` null | PASS (Honest) |
| **G7** | KPI Volumes (Mt/tonase) | Financial KPIs used (Rev, EBITDA, D/E, ICR) | Zero volumetric rows in Sectors quarterly/annual payloads | PASS (Honest) |
| **G8** | Peer EV/EBITDA Multiple | Rendered as `-` for all 9 peers (`P9L7-15`) | Sectors peer payload provides Mcap, P/E, P/BV, but omits peer EBITDA/debt/cash | PASS (Honest) |
| **G9** | Historical Bands Chart | Muted text note (`P6L49`, `P9L20-26`) | Historical valuation table has only 4 annual points; no continuous time-series bands | PASS (Honest) |
| **G10** | Reserve Life / Grade / C1 | Honest exclusion in KPI/Thesis | No volumetric or grade metrics available in Sectors AMMN feeds | PASS (Honest) |

### 1.4 Residual Template Placeholders (Defects)
The following visual placeholders appear in the PDF due to Typst template unhandled fallbacks:

1. **Exhibit 8 DCF Bridge Card (`P6L12-15`)**:
   - `PV Arus Kas Eksplisit`: `-`
   - `PV Nilai Terminal (TV)`: `-`
   - `Enterprise Value (EV)`: `-`
   - `Kas Bersih / (Utang)`: `-`
   *Cause*: `server/report/typst/report_single.typ:532-535` queries `val.at("dcf_grid", default: (:))`, which was omitted from the live payload.
2. **Literal "Sectors pending" Strings**:
   - `P5L3`: `Engine Chart Renderer (Sectors pending)` (Page 5 header)
   - `P9L22`: `Exhibit 14: Engine Chart Renderer (Sectors pending)` (Page 9)
   - `P9L26`: `Exhibit 15: Engine Chart Renderer (Sectors pending)` (Page 9)
   *Cause*: Chart PNG generation skipped or missing from cache; template emits placeholder string.
3. **Exhibit 9 RNAV Bridge (`P6L30-47`)**:
   - 11 rows of `- -` under title `Engine RNAV (Sectors pending)`.
   *Cause*: Fallback default in `report_single.typ:578-593`.

---

## 2. Check (b) & (f) - Number Provenance & Synthetic Markers

### 2.1 Traceable Number Matrix (Clean Sections)
All numbers in the following sections trace 100% to verified data sources:

| Section | Number / Metric | Rendered Value | Sourced From | Traceability Evidence |
|---|---|---|---|---|
| **Cover** | Close Price | Rp 4,860 | `valuation.last_close_price` | `company_report_AMMN_multisection.json` |
| **Cover** | Market Cap | Rp 352.44 T | `overview.market_cap` | $4860 \times 72,518,217,656 = \text{Rp } 352.44 \text{ T}$ |
| **Cover** | 52-Week Range | Rp 2,710–8,500 | `overview.all_time_price` | Min/Max across 52W dictionary in report JSON |
| **Cover** | Relative 90D Perf | +23.99 pp | `daily_AMMN_90d` + `ihsg` | AMMN $+28.57\%$, IHSG $+4.58\%$, Diff $= +23.99 \text{ pp}$ |
| **Cover** | Top Shareholder | 32.17% | `ownership.major_shareholders` | PT Sumber Gemilang Persada (23,327,657,590 shares) |
| **Thesis P1** | FY24 Revenue | Rp 43.04 tn | `segments_AMMN_2024.json` | Copper 19.36 tn (45.0%) + Gold 23.67 tn (55.0%) |
| **Thesis P1** | FY23 Revenue | Rp 31.39 tn | `segments_AMMN_2023.json` | Copper 17.72 tn (56.5%) + Gold 13.67 tn (43.5%) |
| **Thesis P2** | TTM Revenue | Rp 44.48 tn | `quarterly_AMMN_8.json` | Sum of Q2-24 to Q1-26 (4 trailing quarters) |
| **Thesis P2** | TTM EBITDA | Rp 24.98 tn | `quarterly_AMMN_8.json` | Q1-26: 7.92 tn, Q4-25: 4.88 tn, Q3-25: 7.04 tn, Q2-25: 5.14 tn |
| **Thesis P2** | Q1-26 EBITDA Mgn | 57.3% | `quarterly_AMMN_8.json` | EBITDA 7,921.8 bn / Revenue 13,831.6 bn $= 57.27\%$ |
| **Thesis P3** | Q1-26 Gross Debt | Rp 110.79 tn | `quarterly_AMMN_8.json` | Total debt row as of 2026-03-31 |
| **Thesis P3** | Q1-26 Cash | Rp 13.85 tn | `quarterly_AMMN_8.json` | Cash and equivalents row as of 2026-03-31 |
| **Thesis P3** | TTM Net Debt/EBITDA | 3.9x (3.88x) | Derived | $(\text{Rp } 110.79 \text{ tn} - \text{Rp } 13.85 \text{ tn}) / \text{Rp } 24.98 \text{ tn} = 3.88\times$ |
| **Thesis P3** | TTM EBITDA/Interest | 3.5x (3.48x) | Derived | $\text{Rp } 24.98 \text{ tn} / \text{Rp } 7.19 \text{ tn} = 3.48\times$ |
| **Thesis P4** | EV/EBITDA 2026 | 17.99x | `valuation.historical_valuation` | 2026 enterprise to EBITDA print |
| **Thesis P4** | 90D Foreign Flow | -Rp 0.37 tn | `foreign_flow_AMMN_90d.json` | Sum of 62 trading sessions $= -\text{Rp } 370,651,368,000$ |
| **Thesis P4** | 30D Foreign Flow | +Rp 0.24 tn | `foreign_flow_AMMN_90d.json` | Flow from 2026-08-13 to 2026-09-11 $= +\text{Rp } 244,621,450,000$ |
| **Valuation** | DCF Parameters | Rf 7.1%, Beta 1.407, ERP 6.69%, WACC 13.77% | `data/assumptions/AMMN.json` | SBN 10Y, Damodaran global metals relevered, Indonesia ERP |
| **Valuation** | Mid-Cycle EBITDA | Rp 18.40 tn | `data/assumptions/AMMN.json` | Mean of FY23 (15.74 tn), FY24 (23.04 tn), FY25 (16.41 tn) |
| **Valuation** | Mid-Cycle Implied FV | Rp 5,873 | `data/assumptions/AMMN.json` | $(\text{Rp } 18.40 \text{ tn} \times 28.42 - \text{Rp } 110.79 \text{ tn} + \text{Rp } 13.85 \text{ tn}) / 72.52 \text{ bn}$ |
| **Peers** | 9 Peer P/E & P/BV | TBMS 12.5x, EMAS -368.6x, BRMS 150.0x, ANTM 8.6x, MDKA 9141.7x... | `company_report_AMMN_multisection.json` | Verbatim peer multiples from Sectors peer comparison section |

---

### 2.2 Untraced / Synthetic Mock Numbers (Defects)
Audit identified **38 distinct mock numbers** (and 45 total numeric tokens) appearing on **Page 7 and Page 8** in [`output/ammn_report_typst.pdf`](file:///home/fadil/projects/sectors-hackathon/output/ammn_report_typst.pdf). These do not trace to any AMMN harvest file or assumption file:

| Exhibit / Section | Untraced / Synthetic Numbers in PDF | Origin in Code | Contradiction / Defect |
|---|---|---|---|
| **Exhibit 12: Sensitivity Analysis (`P7L40-90`)** | **25 cell values**: Rp 4.979, Rp 5.134, Rp 5.303, Rp 5.487, Rp 5.688, Rp 4.631, Rp 4.762, Rp 4.903, Rp 5.055, Rp 5.221, Rp 4.331, Rp 4.442, **Rp 4.562 (Base)**, Rp 4.690, Rp 4.828, Rp 4.070, Rp 4.165, Rp 4.267, Rp 4.376, Rp 4.493, Rp 3.840, Rp 3.922, Rp 4.010, Rp 4.104, Rp 4.204.<br>**10 header values**: WACC 10.83%–12.83%, g 4.50%–5.50%. | Hardcoded fallback in `report_single.typ:701-707` | Matrix centers on mock WACC 11.83% and g 5.00% (Base FV Rp 4.562), directly contradicting AMMN's real WACC 13.77%, g 2.5%, and DCF FV Rp 147. |
| **Scenario Analysis (`P7L91-99`, `P8L3-5`)** | **3 Fair Values**: BEAR Rp 3.567 (-15.1%), BASE Rp 4.562 (+8.6%), BULL Rp 5.812 (+38.4%).<br>**6 Operational Assumptions**: Rev +6%, EBIT 29%, Rev +10%, EBIT 32%, Rev +14%, EBIT 35%. | Hardcoded fallback in `report_single.typ:721-725` | Synthetic scenario table from a generic template; completely detached from AMMN's DCF (Rp 147) and EV/EBITDA cross-check (Rp 5,873). |
| **Jembatan Nilai EV ke Ekuitas (`P7L100-106`)** | **4 Bridge Values**: PV Explicit 11.862, Kas +500, Utang -0, Implied Equity 12.362. | Hardcoded fallback in `report_single.typ:735-739` | Claims `(-) Total Utang Berbunga: -0 Bebas Utang` and `(+) Kas: +500` for AMMN, which actually carries Rp 110.79 tn debt and Rp 13.85 tn cash. |

*Root Cause*: `server/report/ammn_fill.py:787-805` only populated `payload["dcf_deep_dive"]["wacc_build"]`. It did not populate `sensitivity`, `scenarios`, or `bridge`, triggering the Typst template's hardcoded fallback blocks.

---

## 3. Check (c) - Target Price, Anchor & Gate Stance

### 3.1 Single Gated FV & Anchor Rule
- **Published Target Price**: **Rp 147** (`P1L44`, `P1L69`, `P6L28`).
- **Engine Output Alignment**: Matches the deterministic live DCF Fair Value (Rp 147) produced by `calc_dcf` with WACC 13.77%, terminal growth 2.5%, normalized flat FCF Rp 13,088.9 bn, gross debt Rp 110.79 tn, and cash Rp 13.85 tn.
- **Anchor Named**: Explicitly stated in Cover Summary (`P1L20-23`):
  > *"Target harga Rp 147 (SELL, -96.97%) berjangkar pada SATU FV engine (DCF/EV-blend, bukan intrinsic_value API Rp -11.850 yang tak terpakai)."*
- **Blended / Cross-Check Disclosure**:
  In Exhibit 8 Blended Table (`P6L23-28`):
  - DCF (WACC 13.77%, g 2.5%): pembanding Rp 147
  - EV/EBITDA (28.42x): primer Rp 5,873
  - Target Price (TP 12M): 100% Rp 147
  *Architectural observation*: As documented in commit `a57e3ca`, EV/EBITDA is marked "primer Rp 5,873" and DCF is marked "pembanding Rp 147" in the template, while the headline TP consumes Rp 147. Both values are disclosed honestly and neither is silently dropped.

### 3.2 Gate Framework & Rating Override
- **Evaluated Gates**:
  - Gate 0 (Business model): mining / finite reserves -> NAV primary (`P1L50`)
  - Gate 1 (Data eligibility): 6y filing history, EBIT+ 3/3y (`P1L52`)
  - Gate 2 (NCI structure): 1% NCI, DCF proceeds (`P1L53`)
  - Gate 3 (Cyclicality): commodity-driven cycle, NAV primary (`P1L54`)
  - Gate 4 (Life cycle): mature, stable FCF (`P1L56`)
  - Gate 5 (Output sanity): upside -97.0% out of band -> **Review Required** (`P1L57`)
- **Rating Stance**: Published rating is **`Review Required`** (`P1L41`, `P1L60`, `P6L51`), strictly obeying the Gate 5 sanity trip. It avoids a bare unflagged `BUY` or `SELL`.

---

## 4. Check (d) - Slide 3 vs Exhibit 3 & Financial Statements Tie-Outs

### 4.1 Slide 3 Financial Highlights vs Exhibit 3 Key Financials
Cross-table reconciliation for the overlapping periods (FY21A–FY25A):

| Line Item | Exhibit 3 (Page 2, `P2L8-19`) | Slide 3 FH (Page 4, `P4L6-19`) | Cell Variance | Tie-Out Status |
|---|---|---|:---:|:---:|
| **Revenue (Rp bn)** | `[18466.7, 44127.3, 31393.1, 43036.3, 30904.2]` | `[18466.7, 44127.3, 31393.1, 43036.3, 30904.2]` | 0.0 | **TIE-OUT OK** |
| **EBITDA (Rp bn)** | `[7904.3, 24174.6, 15738.4, 23039.9, 16410.5]` | `[7904.3, 24174.6, 15738.4, 23039.9, 16410.5]` | 0.0 | **TIE-OUT OK** |
| **EBITDA Growth %** | `[98.2, 205.8, −34.9, 46.4, −28.8]` | *(calculated from EBITDA)* | 0.0 | **TIE-OUT OK** |
| **Net Profit (Rp bn)**| `[4506.9, 17049.7, 3892.9, 10290.3, 4167.0]` | `[4506.9, 17049.7, 3892.9, 10290.3, 4167.0]` | 0.0 | **TIE-OUT OK** |
| **EPS (Rp)** | `[-, -, 53.68, 141.9, 57.46]` | `[-, -, 53.68, 141.9, 57.46]` | 0.0 | **TIE-OUT OK** |
| **EPS Growth %** | `[-, -, -, 164.3, −59.5]` | *(calculated from EPS)* | 0.0 | **TIE-OUT OK** |
| **PER (x)** | `[-, -, 122.02, 59.73, 111.81]` | `[-, -, 122.02, 59.73, 111.81]` | 0.0 | **TIE-OUT OK** |
| **PBV (x)** | `[-, -, 6.64, 7.25, 5.13]` | *(reported in ratios)* | 0.0 | **TIE-OUT OK** |
| **EV/EBITDA (x)** | `[-, -, 32.19, 29.19, 34.31]` | *(reported in ratios)* | 0.0 | **TIE-OUT OK** |

### 4.2 Comprehensive Statements & Accounting Identities (Pages 11–12)
Verification across all 6 historical periods (FY20A–FY25A):

1. **Net Profit Tie-Out Across All Exhibits**:
   - `Income Statement (Exhibit 16, P11L16)`: `[1212.8, 4506.9, 17049.7, 3892.9, 10290.3, 4167.0]`
   - `Financial Highlights (Page 4, P4L11)`: `[1212.8, 4506.9, 17049.7, 3892.9, 10290.3, 4167.0]`
   - `Key Financials (Exhibit 3, P2L14)`: `[-, 4506.9, 17049.7, 3892.9, 10290.3, 4167.0]`
   *Status*: **100% Exact Match**.
2. **Cash Reconciliation (Balance Sheet vs Cash Flow)**:
   - `Balance Sheet Cash & Equivalents (Exhibit 17, P11L20)`:
     `[6399.9, 7929.6, 12665.7, 18968.3, 12186.9, 11327.7]`
   - `Cash Flow Statement Saldo Kas Akhir (Exhibit 18, P12L15)`:
     `[6399.9, 7929.6, 12665.7, 18968.3, 12186.9, 11327.7]`
   *Status*: **100% Exact Match**.
3. **Balance Sheet Accounting Identity ($Assets = Liabilities + Equity$)**:
   - FY20A: $36,580.0 + 30,277.7 = 66,857.7$ (Assets: 66,857.7) -> **Diff 0.0**
   - FY21A: $38,499.4 + 35,463.4 = 73,962.8$ (Assets: 73,962.8) -> **Diff 0.0**
   - FY22A: $45,055.6 + 56,276.2 = 101,331.8$ (Assets: 101,331.8) -> **Diff 0.0**
   - FY23A: $68,881.2 + 71,568.2 = 140,449.4$ (Assets: 140,449.4) -> **Diff 0.0**
   - FY24A: $94,891.5 + 84,798.4 = 179,689.9$ (Assets: 179,689.9) -> **Diff 0.0**
   - FY25A: $141,248.0 + 90,897.6 = 232,145.6$ (Assets: 232,145.5) -> **Diff 0.1 (rounding)**
   *Status*: **Holds Cleanly**.
4. **Minorities Reconciliation ($EBT - Tax - Minorities = Net Profit$)**:
   - FY20A: $2,264.5 - 633.5 - 418.2 = 1,212.8$ (NP: 1,212.8) -> **Diff 0.0**
   - FY21A: $6,206.2 - 1,648.5 - 50.7 = 4,507.0 \approx 4,506.9$ -> **Diff 0.1**
   - FY22A: $21,954.3 - 4,822.2 - 82.4 = 17,049.7$ (NP: 17,049.7) -> **Diff 0.0**
   - FY23A: $6,060.3 - 2,063.3 - 104.1 = 3,892.9$ (NP: 3,892.9) -> **Diff 0.0**
   - FY24A: $13,778.7 - 3,411.1 - 77.3 = 10,290.3$ (NP: 10,290.3) -> **Diff 0.0**
   - FY25A: $5,812.9 - 1,494.3 - 151.6 = 4,167.0$ (NP: 4,167.0) -> **Diff 0.0**
   *Status*: **Derived Minorities Formula Holds Exactly**.

---

## 5. Check (e) - News Claims & Provenance Grounding

### 5.1 News Feed Payload Audit
The live data payload carries 8 citable news articles, 100% equipped with valid URL and publish date:

| # | Article Headline | Date | Verified Source URL | Outlet |
|:---:|---|:---:|---|---|
| 1 | Saham-saham emas tertekan jelang rebalancing indeks acuan VanEck | 2026-09-10 | `https://www.idnfinancials.com/id/news/68652/saham-saham-emas-tertekan-jelang-rebalancing-indeks-acuan-vaneck` | idnfinancials |
| 2 | Terdorong Reli Harga Tembaga, Saham AMMN Diborong Banyak Broker | 2026-09-09 | `https://www.bloombergtechnoz.com/detail-news/120995/terdorong-reli-harga-tembaga-saham-ammn-diborong-banyak-broker` | bloombergtechnoz |
| 3 | Saham AMMN MDKA Menguat, Harga Tembaga Cetak Rekor | 2026-09-09 | `https://www.bloombergtechnoz.com/detail-news/120980/saham-ammn-mdka-menguat-harga-tembaga-cetak-rekor` | bloombergtechnoz |
| 4 | Mandiri Sekuritas Buka Peluang IHSG Tembus 7.470 Akhir 2026 | 2026-09-03 | `https://market.bisnis.com/read/20260903/7/2001179/mandiri-sekuritas-buka-peluang-ihsg-tembus-7470-akhir-2026-ini-katalisnya` | bisnis |
| 5 | Daftar Saham PER Terendah-Tertinggi LQ45 2 September 2026 | 2026-09-03 | `https://investasi.kontan.co.id/news/daftar-saham-per-terendah-tertinggi-lq45-2-september-2026-dewa-dan-aadi-disorot` | kontan |
| 6 | Emas Berpeluang Masuk GDX, PSAB Terancam Keluar GDXJ | 2026-08-31 | `https://investor.id/market/452290/emas-berpeluang-masuk-gdx-psab-terancam-keluar-gdxj` | investor.id |
| 7 | Asing Lepas Sejumlah Saham Ini | 2026-08-27 | `https://investor.id/market/451775/asing-lepas-sejumlah-saham-ini` | investor.id |
| 8 | Rekomendasi Saham Hari Ini: AMMN, BUMI Hingga UNVR | 2026-08-21 | `https://www.cnbcindonesia.com/market/20260821081805-17-761142/rekomendasi-saham-hari-ini-ammn-bumi-hingga-unvr` | cnbcindonesia |

### 5.2 Narrative Claim Citations in PDF Text
- **Insider Distribution (`P13L7-10`)**: Cites dates `12 Mei 2026`, `26 Mei 2026`, `31 Des 2025`, `3 Okt 2025` from IDX filings feed.
- **Commodity Rally (`P13L13`)**: Cites copper price record US$ 14,708/ton on `8 Sep 2026` from bloombergtechnoz.
- **Index Rebalancing (`P13L23`)**: Cites VanEck GDX rebalancing on `12 Sep 2026` and market reaction on `10 Sep 2026`.
- **Director Cluster-Buy (`P5L24`)**: Cites `Jul-2026` 12,961,700 shares @ Rp 3,548 from IDX keterbukaan.
- **House Format Rule Compliance**: Printed source lines under exhibits display `Source: Company, Team Estimates` per design specification, while URL/date provenance is preserved in internal payload audit fields.

---

## 6. Credit Spend Audit vs 1,000-Credit Budget

### 6.1 FILLD Live Harvest Spend (`CALL_LOG.md`)
- Total call attempts: 23
- SQLite cache hits (0 credits): 8
- Free rejections (400 bad request / uppercase): 2
- **Billable calls (1 credit each)**: **13 credits**
  1. `daily/AMMN` (90d): 1
  2. `company/get-segments/AMMN` (FY25, 404): 1
  3. `company/shareholders-composition/AMMN`: 1
  4. `filings/?symbol=AMMN`: 1
  5. `news/?symbols=AMMN`: 1
  6. `foreign-flow/AMMN`: 1
  7. `broker-summary/AMMN/top`: 1
  8. `index-daily/ihsg` (lowercase): 1
  9. `company/get-segments/AMMN` (FY24): 1
  10. `companies/list_companies_with_segments`: 1
  11. `company/get-segments/AMMN` (FY23): 1
  12. `companies/?where=free_float>=0`: 1
  13. `suspensions/?symbol=AMMN`: 1

### 6.2 Prior AMMN Live Spend Evidence (`data/agent_runs.db:sectors_cache`)
- Timestamp: 2026-09-12 02:20:27 – 02:23:57 UTC (09:20 – 09:23 WIB)
- Corroborating artifact: `/tmp/ammn_work/commit_msg.txt` (commit `c604aa6`)
- **Billable calls (1 credit each)**: **9 credits**
  1. `daily/AMMN`: 1
  2. `company/report/AMMN` (8 sections): 1
  3. `financials/quarterly/AMMN` (8Q): 1
  4. `company/get_quarterly_financial_dates/AMMN`: 1
  5. `company/corporate-actions/AMMN`: 1
  6. `mining/companies/?keyword=AMMN`: 1
  7. `mining/companies/` (all): 1
  8. `subsectors/`: 1
  9. `subsector/report/basic-materials`: 1

### 6.3 Downstream Lanes Spend
- **FILLT Lane (`a57e3ca`)**: **0 credits** (Keyless execution using cached artifacts).
- **FILLV Lane (Content Audit)**: **0 credits** (Read-only execution).

### 6.4 Total Budget Reconciliation
$$\text{Total AMMN Spend} = 13 \text{ (FILLD)} + 9 \text{ (Prior)} + 0 \text{ (FILLT)} + 0 \text{ (FILLV)} = \mathbf{22 \text{ credits}}$$
$$\text{Budget Headroom} = 1,000 - 22 = \mathbf{978 \text{ credits remaining (2.20\% budget consumed)}}$$

---

## 7. Actionable Recommendations for Downstream Lanes

To achieve a full `PASS-clean` in the next template/modeler pass, the following 3 remediation steps are required (DO NOT FIX in this lane - reported only):

1. **Populate `dcf_deep_dive` sub-keys in `server/report/ammn_fill.py`**:
   Supply explicit `sensitivity` (5x5 matrix evaluated around WACC 13.77% and g 2.5%), `scenarios` (Bear/Base/Bull using AMMN's real parameters), and `bridge` (using AMMN's real Rp 110.79 tn debt and Rp 13.85 tn cash). This will eliminate all 38 synthetic numbers on Pages 7 and 8.
2. **Populate `dcf_grid` in `payload["valuation"]`**:
   Supply `pv_explicit`, `pv_tv`, `ev`, and `net_cash` so Exhibit 8 renders real valuation bridge numbers instead of four `-` dashes.
3. **Handle RNAV and Pending Charts cleanly in Typst Template**:
   If RNAV is unmapped for AMMN (finite reserve / lack of mine-level asset split in Sectors), demote Exhibit 9 or hide it when `val.at("rnav")` is empty rather than rendering 11 rows of `- -`.
   Suppress the literal string `Engine Chart Renderer (Sectors pending)` when chart PNGs are absent, replacing it with an honest static note matching Exhibit 10/11.

---
