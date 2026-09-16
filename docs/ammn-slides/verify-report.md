# AMMN-VERIFY - End-to-End AMMN Render & Compliance Verdict Report

- **Target Ticker**: AMMN (PT Amman Mineral Internasional Tbk, AMMN IJ)
- **Sub-Sector**: Copper & Gold Mining (`metals-mining`, `Basic Materials`)
- **Repository Branch**: `feat/institutional-report`
- **Audit Date**: Saturday, 12 September 2026
- **Auditor**: AGY Lane (Automated Compliance & Verification Auditor)
- **Primary Template Source**: `/home/fadil/.hermes/cache/documents/doc_8073c261b904_Struktur Template Equity.md` (BRIDS Institutional Equity Research Template)
- **Slide Specifications**: `docs/ammn-slides/slide1-cover-spec.md` through `slide6-statements-spec.md`
- **Governing Rules**: `docs/rules/house-report-format.md`
- **Render Engine**: `scripts/render_typst.py` / `server/report/typst_renderer.py` (`report_single.typ`)

---

## Executive Summary & Final Verdict

| Metric / Check Group | Status | Summary |
|---|:---:|---|
| **Overall Verdict** | **FAIL-8 / GAP-1** | Production pipeline honestly refuses keyless AMMN synthesis (422/503); typst template implementation diverges from BRIDS 7-slide structure. |
| **Exhibit Sequence** | **BROKEN** | Emits 1..18/19 exhibits across 8-11 pages instead of sequential 2..17 across 7 slides; 5 canonical exhibits missing; 4+ non-canonical exhibits injected. |
| **Exhibit 1 Skip** | **FAIL** | Spec records rationale to skip Exhibit 1 (consensus), but `report_single.typ:88` labels Shareholder Structure as Exhibit 1. |
| **Source Lines** | **PASS (100%)** | `theme.typ:62-72` uniformly renders `Source: Company, Team Estimates` below 100% of exhibits. |
| **Page Furniture (Header/Footer)** | **PASS (100%)** | Native page margin placement (`theme.typ:86-141`) guarantees header, date, Sectors logo, divider `#067647`, and footer disclosure/page number on all pages. |
| **Slide 3 == Exhibit 3 Tie-Out** | **BROKEN** | Exhibit 3 Key Financials is absent on Slide 1; Slide 3 lacks the 2x2 combo charts to reconcile. |
| **Slide 6–7 Statement Tie-Outs** | **BROKEN** | Cash flow default displays honest dashes (`-`) while IS/BS carry static values; Net Profit and Ending Cash do not tie out; statements crammed on Page 6 (6Y horizon vs 5Y template). |
| **Slide 4 Mining Valuation** | **FAIL** | Modeler instructions & gate framework contain finite-reserve discipline, but `report_single.typ` lacks the RNAV bridge (Opsi C) and mid-cycle EV/EBITDA table. |
| **Slide 5 Peer Bands & Disclaimer** | **FAIL** | P/E 1Y and P/BV 1Y historical band charts missing; median/average summary rows missing from peer table; mandatory own-history disclaimer missing. |

---

## Section 1: Production Pipeline & Sectors API Audit

### 1.1 Live Data Ingestion & Assumptions Check
- **Endpoint / Module Tested**: `server/report/typst_renderer.py:render_report('AMMN')` -> `_load_or_build_report_data('AMMN', 'auto')` -> `server/routers/pdf.py:_build_live_payload('AMMN', None)`.
- **Environment State**: `SECTORS_API_KEY` is **unset** in the environment and absent from `/home/fadil/projects/sectors-hackathon/.env`.
- **Assumptions File State**: `data/assumptions/AMMN.json` does **NOT exist**.
- **Raw Cache State**: `output/cache/ammn_sectors_raw.json` exists but contains `{}` (2 bytes, zero cached data).
- **Execution Result**:
  ```python
  fastapi.exceptions.HTTPException: 422: {
    'ticker': 'AMMN',
    'missing': ['rf', 'beta', 'erp', 'cod', 'g', 'payout', 'fcf', 'shares_out', 'net_debt', 'cash', 'ebitda', 'ev_multiple', 'last_price', 'we', 'wd'],
    'summary': 'no verified assumptions for AMMN - refusing generic fallback (add data/assumptions/AMMN.json or set SECTORS_API_KEY)'
  }
  ```
- **Sectors Gateway Check**: `server/sectors.py:86-97` raises `SectorsNotConfigured: SECTORS_API_KEY missing - onboard at sectors.app/api, save key to .env (mode 600). No fallback wired on purpose.` (maps to HTTP 503).
- **Compliance Assessment**: **GAP (LOUD)**. The production pipeline behaves with strict integrity: it halts loudly with HTTP 422 / 503 rather than fabricating synthetic financial estimates or hallucinating commodity price decks.

### 1.2 PDF Render Execution Path
- **API Render Path**: `server/report/typst_renderer.py:436` halted by the 422 exception.
- **CLI Render Path**: `scripts/render_typst.py` executed with an honest-empty payload (`output/render_ammn_test/report_data.json`):
  - **Crash Observed**:
    ```
    error: file not found (searched at /home/fadil/projects/sectors-hackathon/output/cache/render_ammn/charts/relval_bars.png)
    ┌─ templates/typst/archetypes/report_single.typ:781:10
    │
    781 │ image(chart-dir + "/relval_bars.png", width: 100%);
    ```
  - **Root Cause**: In `templates/typst/archetypes/report_single.typ:778-784`, the fallback condition `if not data.charts.peer_evebitda` unconditionally assumes `relval_bars.png` exists. When `peer_evebitda.png` is not generated (because peer data is missing), `scripts/render_typst.py` has no fallback placeholder generator (unlike `typst_renderer.py:381-397`), causing typst compile to fail.
- **Compliance Assessment**: **FAIL**. The template contains an unhandled file dependency in the absence of peer data.

---

## Section 2: Complete Compliance Verification Matrix

| Check ID | Verification Item | Template / Spec Reference | Implementation Reference | Verdict | Evidence / Failure Details |
|---|---|---|---|:---:|---|
| **CHK-01** | Production pipeline path (Sectors-first, no synthetic fill) | Spec §5, `house-report-format.md` | `server/routers/pdf.py:72-86`, `server/sectors.py:86-97` | **GAP** | Returns honest HTTP 422 (`missing 15 valuation inputs`) and HTTP 503 (`SECTORS_API_KEY missing`). Zero synthetic numbers injected. |
| **CHK-02** | PDF Render Execution | Prompt Job §2 | `scripts/render_typst.py:286`, `report_single.typ:781` | **FAIL** | Typst CLI compilation crashes on missing `relval_bars.png` when peer data is empty. Production renderer blocked by 422. |
| **CHK-03** | Exhibits 1–17 present with descriptive titles | Template lines 7–254 | `templates/typst/archetypes/report_single.typ` | **FAIL** | Template emits 18–19 exhibits instead of 17. Exhibits 4, 5, 6, 12, 13 from the template are missing; 4+ spurious tables are labelled as exhibits. |
| **CHK-04** | Exhibit 1 skipped with rationale recorded | `slide1-cover-spec.md:113-119` | `report_single.typ:88` | **FAIL** | Rationale recorded in spec, but `report_single.typ:88` labels "Struktur Kepemilikan Saham" as Exhibit 1 instead of skipping. |
| **CHK-05** | Source line under 100% of objects | `house-report-format.md`, Template line 11 | `templates/typst/common/theme.typ:62-72` | **PASS** | Every `#exhibit-header` and `#exhibit-figure` automatically appends `Source: Company, Team Estimates`. 100% compliant. |
| **CHK-06** | Numbering sequential 2..17 with no gaps | Template line 13-15, Prompt Job §3 | `report_single.typ:88-787` | **FAIL** | Figure counter runs 1..18/19 rather than 2..17. Exhibit 1 is not skipped, and total exhibit count exceeds 17 due to layout divergence. |
| **CHK-07** | House header/footer on every page | Template lines 16–26, `house-report-format.md` | `theme.typ:86-141, 335-344` | **PASS** | Native margin placement ensures header (`Equity Research – Company Update`, formatted date, Sectors logo, `#067647` rule) and footer (`sectors.app`, disclosure, page number) render on 100% of pages. |
| **CHK-08** | Slide 3 numbers == Exhibit 3 numbers (Tie-out) | `slide1-cover-spec.md:139`, `slide3-visual-spec.md:28` | `report_single.typ:160, 285-335` | **FAIL** | Exhibit 3 on Slide 1 in `report_single.typ` is "Informasi Pasar & Saham" (market cap/float), NOT Key Financials. Slide 3 lacks the 2x2 combo charts to reconcile. |
| **CHK-09** | Slide 6–7 tie-outs hold (Net Profit, Cash) | `slide6-statements-spec.md:270-284` | `report_single.typ:630-740` | **FAIL** | Cash Flow default is honest dashes (`-`) while IS/BS carry hardcoded values (`402` NP, `410` Cash); all 4 statements merged on 1 page; 6Y horizon used instead of 5Y. |
| **CHK-10** | Slide 4 method = DCF-shortened + RNAV + mid-cycle EV/EBITDA + gates | `slide4-valuation-spec.md:1-33`, `instructions.py:221` | `report_single.typ:393-623`, `gates.py:73-74` | **FAIL** | Gate engine and agent instructions are compliant, but template `report_single.typ` lacks the RNAV bridge (Opsi C) and mid-cycle EV/EBITDA table, implementing generic perpetual DCF. |
| **CHK-11** | Slide 5 peer table + bands + disclaimer present | `slide5-peer-spec.md:58-135, 200` | `report_single.typ:748-796` | **FAIL** | P/E 1Y and P/BV 1Y band charts missing; peer table lacks Median/Average summary rows; mandatory own-history disclaimer completely missing. |

---

## Section 3: Canonical Exhibit Audit (Template vs Implementation)

The canonical BRIDS equity template defines exactly 17 exhibits across 7 slides. The table below audits each canonical slot against the current `report_single.typ` render output:

| Canonical Slot | Canonical Description (Template / Specs) | Slide / Location | Current Implementation in `report_single.typ` | Rendered Exhibit # | Status / Verdict |
|:---:|---|:---:|---|:---:|:---:|
| **Ex 1** | **EPS Consensus Table** | Slide 1 (Cover) | **SKIPPED in Spec** (Rationale: no locked consensus feed). However, `report_single.typ:88` inserts `#exhibit-header("Struktur Kepemilikan Saham")` as Exhibit 1. | **Exhibit 1** | **FAIL** (Unwanted table labelled as Exhibit 1) |
| **Ex 2** | **AMMN relative to JCI Index** (Dual-axis) | Slide 1 (Cover) | `report_single.typ:126` `#exhibit-header("Kinerja Harga vs IHSG (YTD)")` | **Exhibit 2** | **PASS** (Dual-axis chart slot present) |
| **Ex 3** | **Key Financials Table** (2024A–2028F, 9 rows) | Slide 1 (Cover) | **MISSING from Slide 1**. `report_single.typ:160` instead inserts `#exhibit-header("Informasi Pasar & Saham AMMN")`. Financial Highlights pushed to Page 3. | **Exhibit 3 (wrong content)** | **FAIL** (Key Financials missing from Cover) |
| - | *Spurious Exhibit: Trajektori Parameter Operasional* | Slide 2 (KPI Hero) | `report_single.typ:244` `#exhibit-header(ex3_title)` | **Exhibit 4** | **FAIL** (Slide 2 is pure narrative in template) |
| - | *Spurious Exhibit: Karakteristik Aset & Jaringan* | Slide 2 (KPI Hero) | `report_single.typ:263` `#exhibit-header(ex4_title)` | **Exhibit 5** | **FAIL** (Slide 2 is pure narrative in template) |
| **Ex 4** | **Revenue & Revenue Growth Combo Chart** | Slide 3 (Visuals 2x2) | `report_single.typ:307` `#exhibit-header("Financial Highlights")` table. Combo chart absent. | **Exhibit 6 (table, not chart)** | **FAIL** (Combo chart missing) |
| **Ex 5** | **EBITDA & EBITDA Margin Combo Chart** | Slide 3 (Visuals 2x2) | `report_single.typ:317` embeds `margin_trajectory.png` only if flagged. Distinct EBITDA combo absent. | **Exhibit 7 (conditional)** | **FAIL** (Combo chart missing) |
| **Ex 6** | **Net Profit & EPS Growth Combo Chart** | Slide 3 (Visuals 2x2) | Absent from `report_single.typ`. | **None** | **FAIL** (Missing entirely) |
| **Ex 7** | **Mining: Volume vs Cash Cost Combo Chart** | Slide 3 (Visuals 2x2) | `report_single.typ:329` embeds `production_cost.png` behind `charts.production_cost`. | **Exhibit 7 or 8 (conditional)** | **PASS** (Chart function & wiring compliant per commit 266a08d) |
| **Ex 8** | **FCFF Forecast & TV** / **RNAV Asset Bridge** | Slide 4 (Valuation) | `report_single.typ:453` `#exhibit-header("Proyeksi Arus Kas Bebas (FCFF)")` (Page 4). RNAV bridge absent. | **Exhibit 7 / 8** | **FAIL** (Lacks mining RNAV bridge) |
| - | *Pita Valuasi Historis P/BV 3-Tahun (STD±2) Table* | Slide 4 (Valuation) | `report_single.typ:517` `#exhibit-figure("Pita Valuasi Historis P/BV 3-Tahun (STD±2)")` | **Exhibit 8 / 9** | **FAIL** (Band chart misplaced on Slide 4 as table) |
| **Ex 9** | **WACC Components / Cost of Capital Build** | Slide 4 (Valuation) | `report_single.typ:552` `#exhibit-header("Cost of Capital Build")` on Page 5. | **Exhibit 9 / 10** | **PASS** (Table present, though pushed to Page 5) |
| **Ex 10** | **Sensitivity Analysis Matrix** | Slide 4 (Valuation) | `report_single.typ:572` `#exhibit-header("Sensitivity Analysis - WACC vs Terminal Growth")` | **Exhibit 10 / 11** | **PASS** (5x5 matrix present on Page 5) |
| - | *Spurious Exhibit: Scenario Analysis* | Slide 4 (Valuation) | `report_single.typ:592` `#exhibit-header("Scenario Analysis")` | **Exhibit 11 / 12** | **FAIL** (Non-template exhibit) |
| - | *Spurious Exhibit: Jembatan Nilai EV ke Ekuitas* | Slide 4 (Valuation) | `report_single.typ:606` `#exhibit-header("Jembatan Nilai EV ke Ekuitas")` | **Exhibit 12 / 13** | **FAIL** (Non-template exhibit) |
| **Ex 11** | **Peer Valuation Table** (P/E, P/BV, EV/EBITDA) | Slide 5 (Peers) | `report_single.typ:767` `#exhibit-header("Peer Comparison - ...")` on Page 7. | **Exhibit 17** | **FAIL** (Missing Median/Average rows; numbered 17) |
| **Ex 12** | **P/E Historical Band (1-Year)** (Chart) | Slide 5 (Peers) | Absent from `report_single.typ`. Line 793 emits note: "Grafik P/E tidak disajikan". | **None** | **FAIL** (1Y P/E band chart missing) |
| **Ex 13** | **P/BV Historical Band (1-Year)** (Chart) | Slide 5 (Peers) | Absent from `report_single.typ` (placed on Page 4 as table). | **None** | **FAIL** (1Y P/BV band chart missing) |
| **Ex 14** | **Income Statement (2024A–2028F)** | Slide 6 (Statements) | `report_single.typ:634` `#exhibit-header("Laporan Laba Rugi Komprehensif")` on Page 6. | **Exhibit 13 / 14** | **FAIL** (6Y horizon vs 5Y; merged on single page) |
| **Ex 15** | **Balance Sheet (2024A–2028F)** | Slide 6 (Statements) | `report_single.typ:656` `#exhibit-header("Neraca Keuangan Ringkas 6 Tahun")` on Page 6. | **Exhibit 14 / 15** | **FAIL** (6Y horizon vs 5Y; no total balance check row) |
| **Ex 16** | **Cash Flow Statement (2024A–2028F)** | Slide 7 (Statements) | `report_single.typ:676` `#exhibit-header("Laporan Arus Kas 6 Tahun")` on Page 6. | **Exhibit 15 / 16** | **PASS** (Added in 266a08d, house row order Operating->Investing->Financing) |
| **Ex 17** | **Key Financial Ratios (2024A–2028F)** | Slide 7 (Statements) | `report_single.typ:726` `#exhibit-header("Rasio Keuangan & Efisiensi 6 Tahun")` on Page 6. | **Exhibit 16 / 17** | **FAIL** (Missing Growth section, Net Gearing, Interest Coverage) |

---

## Section 4: Deep Dive into Critical Deficiencies

### 4.1 Slide 1 & Slide 3 Linkage Breakdown
1. **Displaced Tie-Out Anchor**: In the canonical BRIDS template, the Key Financials table sits on Slide 1 (~70% pane) as Exhibit 3 and acts as the tie-out source of truth for the entire report. In `report_single.typ:160`, Exhibit 3 is replaced by "Informasi Pasar & Saham AMMN" (a secondary card for market cap and free float), while the financials are pushed to Page 3 as Exhibit 6.
2. **Missing Slide 3 Grid**: Slide 3 is specified as a 2x2 quadrant containing four combo charts (Revenue, EBITDA, Net Profit, Mining Volume/Cost). In `report_single.typ`, Page 3 contains only a tabular summary and conditional single charts, lacking the combo visual architecture.

### 4.2 Financial Statements Integrity & Disclosures (Slides 6 & 7)
1. **Single-Page Statement Squashing**: Slides 6 and 7 in the template provide dedicated full slides for IS + BS (Slide 6) and CF + Key Ratios (Slide 7). In `report_single.typ:629-741`, all four financial tables are stacked onto a single logical page (Page 6). Because of vertical height, this triggers severe page overflow in Typst, splitting unpredictably across physical pages 7 and 8.
2. **Broken Accounting Tie-Outs**:
   - **TIE-01 & TIE-02**: Income Statement Net Profit (line 649: `402, 355, 390...`) does not reconcile with Cash Flow starting CFO Net Profit (line 690: `-, -, -...`).
   - **TIE-03**: Cash Flow Ending Cash (line 714: `-, -, -...`) does not reconcile with Balance Sheet Cash & Equivalents (line 661: `410, 465, 500...`).
3. **Horizon Mismatch**: The house specification pins a 5-year rolling horizon (`2024A 2025A 2026F 2027F 2028F`), whereas `report_single.typ` renders 6 columns (`FY24A - FY29F`).
4. **Line Item Gaps**:
   - Income Statement merges interest income/expense and omits Minority Interest.
   - Balance Sheet omits inventory, does not split short-term vs long-term debt, and omits the mandatory `Total Liabilities & Equity` balance check row.
   - Key Ratios omits the Growth section (`Sales`, `EBITDA`, `EBIT`, `Net Profit`), Net Gearing, and Interest Coverage.

### 4.3 Slide 4 Mining Valuation Architecture
1. **Finite-Reserve vs Gordon Perpetuity**: Commit `1319bd0` added the `FINITE-RESERVE DISCIPLINE` to `agents/adk/agents/instructions.py:221` and `agents/valuation/gates.py:73-74`, enforcing that perpetual Gordon terminal values are forbidden for depleting miners.
2. **Template Divergence**: `templates/typst/archetypes/report_single.typ:447-500` still implements Opsi A (single-business DCF with terminal growth $, EV/EBITDA, and 60/40 blended). It completely lacks:
   - **Exhibit 8 Opsi C (RNAV Bridge)**: Per-asset rows for Batu Hijau (producing), Elang (development), exploration tenements, and PT AMIN smelter interest, deducting corporate overhead PV and applying an explicit discount-to-RNAV.
   - **Mid-Cycle EV/EBITDA Table**: 3-year normalized EBITDA cross-check with the 3 constituent years cited.

### 4.4 Slide 5 Peer Valuation & Own-History Bands
1. **Absence of Band Charts**: Slide 5 requires a hard visual split:
   - Top 50%: Cross-sectional Peer Valuation Table.
   - Bottom 50%: Time-series Own-History Tool featuring Exhibit 12 (P/E 1Y Band) and Exhibit 13 (P/BV 1Y Band) with mean (dashed), median (dotted), and current level marker.
   - `report_single.typ` omits both band charts, explicitly writing on line 793: `"Grafik P/E tidak disajikan - P/E trailing tak bermakna di trough siklikal"`.
2. **Missing Summary Rows**: The peer table lacks bold `Median` and `Average` summary rows.
3. **Missing Mandatory Disclaimer**: The verbatim disclaimer mandated by `slide5-peer-spec.md:200-205` is completely absent from the template:
   > *"Implied prices from this own-history tool are mean-reversion cross-checks that hold fundamental drivers constant at their current TTM/forward level and revert only the multiple to its 1-year historical mean/median. They are a snapshot, not a forecast, and are NOT the official Target Price established in Slide 4 (DCF-shortened / RNAV)."*

---

## Section 5: Concrete Evidence Log (Files & Lines)

1. **`server/routers/pdf.py:72-86`**: Loud failure on missing assumptions (`raise HTTPException(status_code=422)`).
2. **`server/sectors.py:86-97`**: Loud failure on missing API key (`raise SectorsNotConfigured`).
3. **`templates/typst/archetypes/report_single.typ:88`**: `#exhibit-header("Struktur Kepemilikan Saham")` turns an un-numbered sidebar card into Exhibit 1.
4. **`templates/typst/archetypes/report_single.typ:160`**: `#exhibit-header("Informasi Pasar & Saham")` displaces Key Financials from Exhibit 3.
5. **`templates/typst/archetypes/report_single.typ:244, 263`**: Introduces Exhibits 4 and 5 on Page 2 where the template mandates pure narrative.
6. **`templates/typst/archetypes/report_single.typ:307`**: Financial Highlights rendered on Page 3 instead of Slide 1.
7. **`templates/typst/archetypes/report_single.typ:630-740`**: All 4 financial statements stacked on Page 6 with 6 columns (`FY24A-FY29F`).
8. **`templates/typst/archetypes/report_single.typ:685-715`**: Default Cash Flow rows are dashes (`-`), breaking tie-outs with lines 649 (Net Profit) and 661 (Cash).
9. **`templates/typst/archetypes/report_single.typ:781`**: Hardcoded `image(chart-dir + "/relval_bars.png")` without placeholder generation crashes `scripts/render_typst.py`.
10. **`templates/typst/common/theme.typ:62-72`**: Uniform `Source: Company, Team Estimates` generation verified compliant.
11. **`templates/typst/common/theme.typ:86-141`**: Native running header and footer placement verified compliant.

---

## Section 6: Non-Invasive Architectural Recommendations

In accordance with the **READ-ONLY** constraint, no production code has been modified. The following remediation roadmap is provided for the owning lanes:

1. **Template Alignment (Lane 10 / Templates)**:
   - Restructure `report_single.typ` (or create `ammn_single.typ`) into the 7-slide layout.
   - Remove `#exhibit-header` from Page 1 sidebar cards (`Struktur Kepemilikan Saham`, `Informasi Pasar`).
   - Place Exhibit 3 (Key Financials Table, 5 years) on Slide 1 main pane.
   - Convert Slide 2 to pure 3-paragraph narrative without exhibit headers.
   - Implement Slide 3 as a 2x2 grid hosting Exhibits 4 (Revenue combo), 5 (EBITDA combo), 6 (Net Profit combo), and 7 (`chart_production_cost`).
   - Split Page 6 statements across Slide 6 (IS + BS) and Slide 7 (CF + Key Ratios), pinned to 5-year rolling columns (`2024A`–`2028F`).
   - Add Exhibit 8 Opsi C (RNAV Bridge) and 3Y mid-cycle EV/EBITDA to Slide 4.
   - Add Exhibit 12 (P/E 1Y Band) and Exhibit 13 (P/BV 1Y Band) and the mandatory disclaimer to Slide 5.
2. **Renderer Resilience (Lane 6 / Engine)**:
   - In `scripts/render_typst.py`, ensure placeholder generation (`typst_renderer.py:381-397`) is mirrored so that keyless/empty runs never crash on missing chart PNGs.
3. **Data Onboarding (Lane 4 / Backend)**:
   - Provide `SECTORS_API_KEY` in `.env` and configure `data/assumptions/AMMN.json` with verified mining inputs.
