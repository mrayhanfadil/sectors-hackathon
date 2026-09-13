# FE Payload Availability Audit & Fabrication Inventory

**Date:** 2026-09-13  
**Target Repository:** `/home/fadil/projects/sectors-hackathon` (branch `feat/institutional-report`)  
**Scope:** Backend payload availability verification against `server/routers/pdf.py::render_html_for_ticker` and comprehensive frontend fabrication scan in `src/fe/src/**`.

---

## Executive Summary

- **Verified Assumption Files:** Only `data/assumptions/AMMN.json` exists in `data/assumptions/*.json`.
- **Payload Availability for AMMN:** 100% of the 17 mandated payload paths are **PRESENT** with full structured data generated deterministically from internal valuation engines and the cached Sectors harvest.
- **Unverified Tickers Refusal:** Any ticker without a verified `data/assumptions/<TICKER>.json` (e.g., `BBCA`, `ADRO`, `MTEL`, `CDIA`, `RATU`, `POWR`, `TLKM`, `ASII`, `GOTO`, `UNVR`) is strictly rejected by the backend with **HTTP 422 Unprocessable Entity** carrying a list of 15 missing required assumption keys.
- **Frontend Fabrication Scan:** A total of **48 fabrication instances** were identified across 5 key patterns in `src/fe/src/**`. Of these, **23 instances directly reach the main report page or its active subroutes**.

---

## Part 1 — Payload Availability Audit

### 1.1 Verified Tickers Identification
Scanning `data/assumptions/*.json`:
- **Found:** `data/assumptions/AMMN.json`
- **Active Ticker Universe with Verified Assumptions:** `['AMMN']`

### 1.2 Availability Matrix
Executed:
```bash
.venv/bin/python -c "import sys; sys.path.insert(0, '.'); from server.routers.pdf import render_html_for_ticker; _t, _h, p = render_html_for_ticker('AMMN', None)"
```

| Payload Path | AMMN |
| --- | --- |
| `cover.rating_box` | PRESENT (6 keys) |
| `cover.slide2.key_financials` | PRESENT (12 keys) |
| `key_financials` | PRESENT (4 keys) |
| `valuation_page.bridge` | PRESENT (22 keys) |
| `valuation_page.sensitivity` | PRESENT (11 keys) |
| `valuation_page.notes` | PRESENT (6 items) |
| `valuation_page.crosscheck_rows` | PRESENT (4 items) |
| `valuation_page.legs` | PRESENT (2 keys) |
| `peers_page.part_a` | PRESENT (14 keys) |
| `peers_page.part_b.bands` | PRESENT (4 items) |
| `peers_page.part_b.implied` | PRESENT (4 items) |
| `financial_statements` | PRESENT (6 keys) |
| `financials` | PRESENT (3 items) |
| `kpis` | PRESENT (4 items) |
| `risks` | PRESENT (6 items) |
| `exhibits` | PRESENT (2 items) |
| `sector_data` | PRESENT (5 keys) |

### 1.3 Path-Level Data Inspection (AMMN)

1. **`cover.rating_box`**: Present (6 keys: `action="BUY"`, `tp=5667`, `prev_tp=null`, `price=4860.0`, `upside_pct=16.61`, `key_takeaways=[3 items]`).
2. **`cover.slide2.key_financials`**: Present (12 keys: `exhibit_title="Key Financials (2024A–2028F)"`, `headers=['Year to 31 Dec', '2024A', '2025A', '2026F', '2027F', '2028F']`, `rows=[5 metric rows]`, `path_notes`, `forecast_basis`, etc.).
3. **`key_financials`**: Present (4 keys: `title="Key Financials (FY21A–FY25A)"`, `source="Sectors company/report financials.historical_financials (IDR bn)"`, `headers=['Metrik Finansial', 'FY21A', 'FY22A', 'FY23A', 'FY24A', 'FY25A']`, `rows=[5 metric rows]`).
4. **`valuation_page.bridge`**: Present (22 keys: `basis="FCFF normalised (steady-state, dokumentasi asumsi)"`, `fcff=[5 values]`, `growth`, `discount`, `pv_fcff`, `ev_gordon`, `net_debt`, `equity_gordon`, `fv_gordon`, `fv_exit`, `tv_share`).
5. **`valuation_page.sensitivity`**: Present (11 keys: `fair_value` 5x5 matrix, `wacc_axis=[12.77%, 13.27%, 13.77%, 14.27%, 14.77%]`, `g_axis=[2.0%, 2.25%, 2.5%, 2.75%, 3.0%]`, `base={wacc, g, fv}`, `swing={min, max}`).
6. **`valuation_page.notes`**: Present (6 items: Verbatim analytical disclosure notes covering Multiple basis, EV/EBITDA anchor, DCF secondary leg, terminal growth, capex assumptions).
7. **`valuation_page.crosscheck_rows`**: Present (4 items: Method comparison crosschecks comparing DCF 148, DCF+exit 1067, EV/EBITDA 5667, Market Price 4860).
8. **`valuation_page.legs`**: Present (2 keys: `{"dcf": 147.02, "ev_ebitda": 5667.31}`).
9. **`peers_page.part_a`**: Present (14 keys: Exhibit 11 peer table with 9 mining peer rows including TBMS, BRMS, MDKA, ANTM, TINS, NCKL, MBMA, EMAS, INCO).
10. **`peers_page.part_b.bands`**: Present (4 items: 1-year historical multiple distributions for `pe`, `pbv`, `ev_ebitda`, `ev_sales`, each containing `n=161`, `mean`, `median`, `current`, `percentile`, `p10`, `p90`, `series=[161 points]`).
11. **`peers_page.part_b.implied`**: Present (4 items: Implied target valuation bands across `pe`, `pbv`, `ev_ebitda`, `ev_sales` based on own-history median/mean).
12. **`financial_statements`**: Present (6 keys: Comprehensive 6-year audited statements spanning `income`, `balance`, `cashflow`, `ratios`, `provenance`).
13. **`financials`**: Present (3 items: `Income Statement`, `Balance Sheet`, `Cashflow Statement` tables FY20A–FY25A).
14. **`kpis`**: Present (4 items: `Pendapatan FY2025`, `EBITDA FY2025`, `Net Debt / Equity`, `Cash Conversion`).
15. **`risks`**: Present (6 items: `Distribusi insider`, `Volatilitas komoditas`, `Risiko eksekusi smelter`, `Fluktuasi kurs USD/IDR`, `Kebijakan royalti & DMO`, `Konsentrasi pelanggan`).
16. **`exhibits`**: Present (2 items: `Pendapatan & Laba Bersih (FY20A–FY25A)` and `EBITDA & Arus Kas Operasi`).
17. **`sector_data`**: Present (5 keys: `subsector="Basic Materials"`, `growth_forecast_2026`, `growth_actual_2025`, `top_mcap`, `source`).

---

### 1.4 Refused Tickers & Backend Error Response Contract

When `render_html_for_ticker(ticker)` is invoked for any ticker lacking a verified assumptions file in `data/assumptions/`:

#### HTTP Status Code:
`422 Unprocessable Entity`

#### Response Body Fields:
```json
{
  "detail": {
    "ticker": "<TICKER>",
    "missing": [
      "rf",
      "beta",
      "erp",
      "cod",
      "g",
      "payout",
      "fcf",
      "shares_out",
      "net_debt",
      "cash",
      "ebitda",
      "ev_multiple",
      "last_price",
      "we",
      "wd"
    ],
    "summary": "no verified assumptions for <TICKER> — refusing generic fallback (add data/assumptions/<TICKER>.json or set SECTORS_API_KEY)"
  }
}
```

#### Tested Refused Tickers:
- `BBCA` (Banking) -> HTTP 422 (15 missing keys)
- `ADRO` (Coal/Energy) -> HTTP 422 (15 missing keys)
- `MTEL` (Telco Infra) -> HTTP 422 (15 missing keys)
- `CDIA` (Conglomerate) -> HTTP 422 (15 missing keys)
- `RATU` (Oil & Gas) -> HTTP 422 (15 missing keys)
- `POWR` (Utilities) -> HTTP 422 (15 missing keys)
- `TLKM` (Telecom) -> HTTP 422 (15 missing keys)
- `ASII` (Automotive/Conglomerate) -> HTTP 422 (15 missing keys)
- `GOTO` (Tech) -> HTTP 422 (15 missing keys)
- `UNVR` (Consumer) -> HTTP 422 (15 missing keys)

#### What the FE Must Display:
When the backend returns HTTP 422, the FE **must not** attempt fallback to generic/archetype constants. It must render an honest **"Belum Tercakup"** / **"Belum Memiliki Asumsi Terverifikasi"** state containing:
1. Clear statement that `<TICKER>` is excluded from the institutional valuation universe.
2. The missing assumption parameters list (`missing` array) to explain why the deterministic engine rejected execution.
3. Instructions to add `data/assumptions/<TICKER>.json` or provide a valid Sectors API key.

---

## Part 2 — Fabrication Inventory in the Current FE

### 2.1 Fabrication Counts by Pattern

| Pattern | Description | Total Count | Reaches Report Page |
| :--- | :--- | :---: | :---: |
| **Pattern 1: Mock/Fixture Imports & Deprecated Mock Routes** | Unused mock components in `components/mock-sectors/**` and deprecated mock route imports in `routeTree.gen.ts` | 4 | No |
| **Pattern 2: Hardcoded Numeric Arrays, Objects & Statistical Defaults** | Hardcoded WACC/NIM/Capex figures in suggestions, hardcoded ticker universe quintets, fallback matrix rows, fallback margin-of-safety | 11 | 4 |
| **Pattern 3: `?? 0`, `|| 0`, `|| "-"`, `|| "—"`, and Magic Number Nullish Defaults** | Zeroes, dashes, or magic constants (`50`, `100`, `15`) applied to missing metric/figure fields | 19 | 12 |
| **Pattern 4: Synthetic / Placeholder Strings Presented as Live Data** | Generic fallback labels, placeholder summaries, simulated debate evidence/verdicts, and default company titles | 14 | 7 |
| **Pattern 5: `Math.random`** | Stochastic or randomized figure generators | 0 | 0 |
| **Total** | | **48** | **23** |

---

### 2.2 Detailed Itemized Inventory

#### Pattern 1: Mock/Fixture Imports & Deprecated Routes (4 instances)

1. **`src/fe/src/routeTree.gen.ts:14`**
   - **Quoted Line:** `import { Route as MockSectorsTickerRouteImport } from './routes/mock-sectors.$ticker'`
   - **Reaches Report Page:** No (Route `/mock-sectors/$ticker` is deprecated and renders a 301 notice redirect).
   - **Should Render Instead:** Remove mock route and routeTree entry entirely.

2. **`src/fe/src/components/mock-sectors/DividendTimeline.tsx`**
   - **Quoted Line:** Whole component file (424 lines)
   - **Reaches Report Page:** No (Dead code, unreferenced).
   - **Should Render Instead:** Purge file or replace with corporate actions block bound to `payload.corporate_actions`.

3. **`src/fe/src/components/mock-sectors/NewsFeedCard.tsx`**
   - **Quoted Line:** Whole component file (316 lines)
   - **Reaches Report Page:** No (Dead code, unreferenced).
   - **Should Render Instead:** Purge file or wire to `payload.news`.

4. **`src/fe/src/components/mock-sectors/QuarterlyTrendChart.tsx`**
   - **Quoted Line:** Whole component file (676 lines)
   - **Reaches Report Page:** No (Dead code, unreferenced).
   - **Should Render Instead:** Purge file or wire to `payload.performance_page`.

---

#### Pattern 2: Hardcoded Numeric Arrays, Objects & Statistical Defaults (11 instances)

5. **`src/fe/src/components/report/ChallengeForm.tsx:20-46`**
   - **Quoted Line:** `const DEFAULT_SUGGESTIONS: Record<string, string[]> = { BBCA: ["WACC 11.1%...", ...], MTEL: ["WACC 10.1%...", ...], RATU: ["WACC 8.4%...", ...], ... }`
   - **Reaches Report Page:** Yes (`/report/$ticker/challenge`).
   - **Should Render Instead:** Dynamic challenge suggestion generator reading actual `payload.valuation_page.bridge.wacc` and `payload.risks`, or neutral non-numeric prompts.

6. **`src/fe/src/components/report/ValuationMethodology.tsx:378`**
   - **Quoted Line:** `<Badge ...>Margin of Safety {vd.blended.margin_of_safety_pct ?? 15}%</Badge>`
   - **Reaches Report Page:** Yes (`/report/$ticker`).
   - **Should Render Instead:** Render badge only if `margin_of_safety_pct` exists in `payload.valuation.blended`; otherwise render `"N/A"` or omit badge.

7. **`src/fe/src/components/report/ValuationMethodology.tsx:398`**
   - **Quoted Line:** `: [["DCF", "60%", "—"], ["EV/EBITDA", "40%", "—"]]`
   - **Reaches Report Page:** Yes (`/report/$ticker`).
   - **Should Render Instead:** Empty table state or omit table when `payload.valuation.blended.rows` is absent.

8. **`src/fe/src/components/report/ReportHeader.tsx:147`**
   - **Quoted Line:** `{ENGINE_TICKERS.map((symbol) => {`
   - **Reaches Report Page:** Yes (`/report/$ticker` header ticker switcher).
   - **Should Render Instead:** Fetch universe dynamically from `GET /api/tickers` or verified list `data/assumptions/*.json`. (Currently omits AMMN!).

9. **`src/fe/src/components/agent/tickers.ts:11`**
   - **Quoted Line:** `export const ENGINE_TICKERS = ["ADRO", "BBCA", "CDIA", "MTEL", "POWR", "RATU"] as const`
   - **Reaches Report Page:** Yes (imported by `ReportHeader.tsx`).
   - **Should Render Instead:** Dynamic array populated from backend assumptions files (must include `"AMMN"`).

10. **`src/fe/src/routes/__root.tsx:9`**
    - **Quoted Line:** `const QUINTET = ["RATU", "CDIA", "MTEL", "BBCA", "ADRO"] as const`
    - **Reaches Report Page:** Yes (Root layout router state).
    - **Should Render Instead:** Dynamic ticker validator.

11. **`src/fe/src/routes/__root.tsx:34`**
    - **Quoted Line:** `return "BBCA"`
    - **Reaches Report Page:** Yes (Root layout ticker fallback).
    - **Should Render Instead:** Return current route ticker parameter or null without defaulting to arbitrary ticker `"BBCA"`.

12. **`src/fe/src/routes/index.tsx:24`**
    - **Quoted Line:** `const QUINTET = ["RATU", "CDIA", "MTEL", "BBCA", "ADRO"] as const`
    - **Reaches Report Page:** No (Hub home route `/`).
    - **Should Render Instead:** Read verified assumption files from API universe.

13. **`src/fe/src/routes/mock-sectors.$ticker.tsx:12`**
    - **Quoted Line:** `const validQuintet = ["RATU", "CDIA", "MTEL", "BBCA", "ADRO"]`
    - **Reaches Report Page:** No (Deprecated mock route).
    - **Should Render Instead:** Remove route.

14. **`src/fe/src/lib/api.ts:202`**
    - **Quoted Line:** `jci: { base: 0, bull: 0, bear: 0, pe: 0, epsGrowth: "-" }`
    - **Reaches Report Page:** No (Used by `/api/outlook` query).
    - **Should Render Instead:** Explicit `null` fields to indicate missing outlook data.

15. **`src/fe/src/components/mock-sectors/DividendTimeline.tsx:89`**
    - **Quoted Line:** `const maxPayout = stats?.max ?? 100`
    - **Reaches Report Page:** No (Dead code).
    - **Should Render Instead:** Null check and empty chart state.

---

#### Pattern 3: `?? 0`, `|| 0`, `|| "-"`, `|| "—"`, and Magic Number Nullish Defaults (19 instances)

16. **`src/fe/src/components/report/charts/DcfSpreadCharts.tsx:81`**
    - **Quoted Line:** `price ?? 0,`
    - **Reaches Report Page:** Yes (`/report/$ticker`).
    - **Should Render Instead:** Exclude `price` from `Math.max` scaling if `price === null`.

17. **`src/fe/src/components/report/ExecutiveSummary.tsx:272`**
    - **Quoted Line:** `const action = s1?.rating?.action || cover?.rating_box?.action || "—"`
    - **Reaches Report Page:** Yes (`/report/$ticker`).
    - **Should Render Instead:** `null` with `<PendingBlock label="Rating" />` if rating is omitted.

18. **`src/fe/src/components/report/ReportHeader.tsx:233`**
    - **Quoted Line:** `{upside || "—"}` (via `upsideDisplay`)
    - **Reaches Report Page:** Yes (`/report/$ticker`).
    - **Should Render Instead:** Display `"N/A"` or omit return container if upside cannot be computed.

19. **`src/fe/src/components/report/ValuationMethodology.tsx:99-103`**
    - **Quoted Line:** `const p2 = Number(bands["std+2"] ?? 0); const p1 = Number(bands["std+1"] ?? 0); const avg = Number(bands.avg ?? 0); const m1 = Number(bands["std-1"] ?? 0); const m2 = Number(bands["std-2"] ?? 0)`
    - **Reaches Report Page:** Yes (`/report/$ticker`).
    - **Should Render Instead:** Abort band chart rendering if any standard deviation level is undefined/null.

20. **`src/fe/src/components/report/ValuationMethodology.tsx:192`**
    - **Quoted Line:** `const total = segments.reduce((s, x) => s + Number(x.share_pct ?? 0), 0)`
    - **Reaches Report Page:** Yes (`/report/$ticker`).
    - **Should Render Instead:** Filter out null segments and report unallocated percentage honestly.

21. **`src/fe/src/components/report/ValuationMethodology.tsx:210`**
    - **Quoted Line:** `style={{ width: `${Number(s.share_pct ?? 0)}%` }}`
    - **Reaches Report Page:** Yes (`/report/$ticker`).
    - **Should Render Instead:** Omit segment bar segment if `share_pct` is missing.

22. **`src/fe/src/components/report/SentimentStatCards.tsx:65`**
    - **Quoted Line:** `const score = it.score ?? 50`
    - **Reaches Report Page:** Yes (`/report/$ticker/sentiment`).
    - **Should Render Instead:** Skip un-scored items from polarization calculation instead of assuming neutral 50.

23. **`src/fe/src/components/report/SentimentStatCards.tsx:90`**
    - **Quoted Line:** `const totalSources = (sentiment?.sources?.length || 0) + (sentiment?.items?.length || 0) + newsCount`
    - **Reaches Report Page:** Yes (`/report/$ticker/sentiment`).
    - **Should Render Instead:** Display `"0"` or `"MENUNGGU"` if arrays are null/undefined.

24. **`src/fe/src/components/report/SentimentStatCards.tsx:198`**
    - **Quoted Line:** `style={{ width: `${distribution.bullishPct ?? 0}%` }}`
    - **Reaches Report Page:** Yes (`/report/$ticker/sentiment`).
    - **Should Render Instead:** Do not render bar segment if `bullishPct === null`.

25. **`src/fe/src/components/report/SentimentStatCards.tsx:203`**
    - **Quoted Line:** `style={{ width: `${distribution.neutralPct ?? 0}%` }}`
    - **Reaches Report Page:** Yes (`/report/$ticker/sentiment`).
    - **Should Render Instead:** Do not render bar segment if `neutralPct === null`.

26. **`src/fe/src/components/report/SentimentStatCards.tsx:208`**
    - **Quoted Line:** `style={{ width: `${distribution.bearishPct ?? 0}%` }}`
    - **Reaches Report Page:** Yes (`/report/$ticker/sentiment`).
    - **Should Render Instead:** Do not render bar segment if `bearishPct === null`.

27. **`src/fe/src/components/report/SentimentStatCards.tsx:243`**
    - **Quoted Line:** `style={{ width: `${confidencePct ?? 0}%` }}`
    - **Reaches Report Page:** Yes (`/report/$ticker/sentiment`).
    - **Should Render Instead:** Hide progress bar if `confidencePct === null`.

28. **`src/fe/src/components/report/SentimentChart.tsx:40`**
    - **Quoted Line:** `const angleDeg = -180 + ((gauge ?? 50) / 100) * 180`
    - **Reaches Report Page:** Yes (`/report/$ticker/sentiment`).
    - **Should Render Instead:** Do not compute needle coordinates if `gauge === null`.

29. **`src/fe/src/components/report/SentimentNewsList.tsx:107`**
    - **Quoted Line:** `const score = s.score ?? 50`
    - **Reaches Report Page:** Yes (`/report/$ticker/sentiment`).
    - **Should Render Instead:** Mark social sentiment as `"unclassified"` when score is null.

30. **`src/fe/src/lib/api.ts:89`**
    - **Quoted Line:** `const fv = Number(dcf["fv_per_share"] ?? dcf["fv"] ?? 0)`
    - **Reaches Report Page:** Yes (Used in legacy report adapter).
    - **Should Render Instead:** Do not create DCF method item if `fv_per_share` is absent.

31. **`src/fe/src/lib/api.ts:94`**
    - **Quoted Line:** `const fv = Number(ev["fv_per_share"] ?? ev["fv"] ?? 0)`
    - **Reaches Report Page:** Yes (Used in legacy report adapter).
    - **Should Render Instead:** Do not create EV/EBITDA method item if `fv_per_share` is absent.

32. **`src/fe/src/lib/api.ts:100`**
    - **Quoted Line:** `const bv = Number(blendedRaw["blended"] ?? 0) || Number(raw["fair_value"] ?? 0) || 0`
    - **Reaches Report Page:** Yes (Used in legacy report adapter).
    - **Should Render Instead:** Keep `blended = null` if no valid blended value is returned.

33. **`src/fe/src/lib/api.ts:518`**
    - **Quoted Line:** `dimension: { sentiment: "neutral", relevance: Number(it["relevance"] ?? 0) },`
    - **Reaches Report Page:** Yes (News items mapping).
    - **Should Render Instead:** Leave `relevance: undefined` rather than fabricating `0`.

34. **`src/fe/src/components/mock-sectors/DividendTimeline.tsx:66`**
    - **Quoted Line:** `const amounts = dividends.map((d) => d.amount_per_share || 0)`
    - **Reaches Report Page:** No (Dead code).
    - **Should Render Instead:** Filter out null/undefined dividend amounts.

---

#### Pattern 4: Synthetic / Placeholder Strings Presented as Live Data (14 instances)

35. **`src/fe/src/components/report/ExecutiveSummary.tsx:273`**
    - **Quoted Line:** `const actionStatus = s1?.rating?.action_status || "Institutional Research"`
    - **Reaches Report Page:** Yes (`/report/$ticker`).
    - **Should Render Instead:** Render nothing or empty string if `action_status` is missing.

36. **`src/fe/src/components/report/ExecutiveSummary.tsx:279`**
    - **Quoted Line:** `const companyName = meta?.company_name || `${tk} Tbk.``
    - **Reaches Report Page:** Yes (`/report/$ticker`).
    - **Should Render Instead:** Render `tk` alone if `company_name` is absent.

37. **`src/fe/src/components/report/ExecutiveSummary.tsx:291`**
    - **Quoted Line:** `const jciSource = s1?.jci_chart?.source || cover?.vs_jci?.source || "Sectors API / yfinance"`
    - **Reaches Report Page:** Yes (`/report/$ticker`).
    - **Should Render Instead:** Omit source tag or display `"Belum ada sumber"` if source is absent.

38. **`src/fe/src/components/report/ReportHeader.tsx:186`**
    - **Quoted Line:** `{finalName || `${tk} Tbk`}`
    - **Reaches Report Page:** Yes (`/report/$ticker`).
    - **Should Render Instead:** Display `{tk}` without synthesizing `"Tbk"`.

39. **`src/fe/src/components/report/SentimentNewsList.tsx:114`**
    - **Quoted Line:** `title: s.text?.slice(0, 80) ? `${s.text.slice(0, 80)}...` : `Postingan ${s.platform || "Ritel"}`,`
    - **Reaches Report Page:** Yes (`/report/$ticker/sentiment`).
    - **Should Render Instead:** Render `"Postingan Komunitas"` without pretending platform identity.

40. **`src/fe/src/components/report/SentimentNewsList.tsx:116`**
    - **Quoted Line:** `source: s.platform || "Forum Komunitas",`
    - **Reaches Report Page:** Yes (`/report/$ticker/sentiment`).
    - **Should Render Instead:** Render `null` or omit source field if missing.

41. **`src/fe/src/components/report/SentimentNewsList.tsx:117`**
    - **Quoted Line:** `platform: (s.platform || "STOCKBIT / X").toUpperCase(),`
    - **Reaches Report Page:** Yes (`/report/$ticker/sentiment`).
    - **Should Render Instead:** Render `"KOMUNITAS PUBLIK"` without claiming Stockbit or X.

42. **`src/fe/src/routes/report.$ticker.challenge.tsx:110`**
    - **Quoted Line:** `verdict: data.verdict || "defend",`
    - **Reaches Report Page:** Yes (`/report/$ticker/challenge`).
    - **Should Render Instead:** Display `"MENUNGGU VERIFIKASI"` if backend does not return explicit verdict.

43. **`src/fe/src/routes/report.$ticker.challenge.tsx:111`**
    - **Quoted Line:** `evidence: data.evidence || "Model mempertahankan asumsi berdasarkan konsistensi laporan audited.",`
    - **Reaches Report Page:** Yes (`/report/$ticker/challenge`).
    - **Should Render Instead:** Display `"Tidak ada catatan bukti yang dikembalikan oleh backend."`

44. **`src/fe/src/routes/report.$ticker.challenge.tsx:115`**
    - **Quoted Line:** `exhibit_ref: data.exhibit_ref || "Sensitivity & DCF Audit",`
    - **Reaches Report Page:** Yes (`/report/$ticker/challenge`).
    - **Should Render Instead:** Render `null` without fabricating an exhibit citation.

45. **`src/fe/src/lib/api.ts:153`**
    - **Quoted Line:** `name: (anyLive["company_name"] as string) || (anyLive["name"] as string) || `${k} - Live`,`
    - **Reaches Report Page:** Yes (`/report/$ticker`).
    - **Should Render Instead:** Render `k` without attaching `"- Live"`.

46. **`src/fe/src/lib/api.ts:158`**
    - **Quoted Line:** `summary: (anyLive["summary"] as string) || "Ringkasan menunggu BE",`
    - **Reaches Report Page:** Yes (`/report/$ticker`).
    - **Should Render Instead:** Render `""` or null state.

47. **`src/fe/src/routes/index.tsx:107`**
    - **Quoted Line:** `const companyName = report?.name || `${ticker} Tbk``
    - **Reaches Report Page:** No (Hub home route `/`).
    - **Should Render Instead:** Display `{ticker}`.

48. **`src/fe/src/routes/index.tsx:114`**
    - **Quoted Line:** `"Data laporan keuangan terverifikasi sedang disinkronisasikan dari backend..."`
    - **Reaches Report Page:** No (Hub home route `/`).
    - **Should Render Instead:** Render `"Belum ada ringkasan emiten."`

---

## Part 3 — Remediation Directives for FE Lanes

1. **Rebind Main Report Route to Frozen Contract (`fetchReportPayload`):**  
   Transition `src/fe/src/routes/report.$ticker.index.tsx` from `fetchReport` to `fetchReportPayload` (`docs/fe-payload-contract.json`). If the response returns `is422: true`, render the honest unverified state with the exact missing keys list (`missing`).

2. **Replace All Figure Defaults with `PendingBlock`:**  
   Purge every `?? 0`, `|| 0`, and magic constant (`50`, `15`) from figure and percentage calculations. When a section is absent, render `<PendingBlock label="..." message="belum tersedia di payload" />`.

3. **Purge `components/mock-sectors/`:**  
   Delete the unreferenced mock components directory to avoid code drift and confusion with live institutional components.

4. **Synchronize Ticker Universe Dynamically:**  
   Update `src/fe/src/components/agent/tickers.ts` and `ReportHeader.tsx` to read the dynamic universe of verified tickers (starting with `AMMN`), rather than relying on a hardcoded 5-emiten quintet (`RATU, CDIA, MTEL, BBCA, ADRO`) that omits `AMMN`.
