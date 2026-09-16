# Frontend No-Fabrication Scan Report

**Date**: 2026-09-13
**Target Directory**: `src/fe/src/`
**Total Findings**: 14

## Exact Commands Run

```bash
# 1. Static Scan on current tree (findings check)
.venv/bin/python scripts/verify_fe_no_fabrication.py

# 2. Baseline generation (writes this audit report and exits 0)
.venv/bin/python scripts/verify_fe_no_fabrication.py --baseline

# 3. Standalone Selftest
.venv/bin/python scripts/verify_fe_no_fabrication.py --selftest

# 4. Payload Cross-Check (AMMN Contract / Live Payload)
.venv/bin/python scripts/verify_fe_no_fabrication.py --ticker AMMN
```

## Real Tool Output on Current Tree

```text
================================================================================
FRONTEND NO-FABRICATION VERIFIER (STATIC SCAN)
Target Directory: /home/fadil/projects/sectors-hackathon/src/fe/src
================================================================================

[!] FINDINGS DETECTED: 14 fabrication issues found:

 1. src/fe/src/routeTree.gen.ts:14
    Rule:        RULE_A_MOCK_IMPORT (Mock/Fixture/Sample Import)
    Line:        import { Route as MockSectorsTickerRouteImport } from './routes/mock-sectors.$ticker'
    Why:         Imports mock, fixture, or sample module instead of binding to backend payload
    Remediation: Remove mock import and consume live fields from ReportPayload contract
------------------------------------------------------------
 2. src/fe/src/components/report/charts/DcfSpreadCharts.tsx:81
    Rule:        RULE_C_FIGURE_FALLBACK (Fabricated Figure Fallback (price ?? 0))
    Line:        price ?? 0,
    Why:         Substitutes default figure '0' when 'price' is missing, masking absent backend data
    Remediation: Render honest pending block (PendingBlock) or format null as '-'
------------------------------------------------------------
 3. src/fe/src/components/report/charts/PeersCharts.tsx:251
    Rule:        RULE_B_NUMERIC_ARRAY (Hardcoded Numeric Literal Array (3+ elements))
    Line:        {[1.0, 0.5, 0.0].map((frac, idx) => {
    Why:         Hardcoded numeric array in source fabricates data series instead of reading payload
    Remediation: Derive series dynamically from payload arrays or pass file to --allow if static axis
------------------------------------------------------------
 4. src/fe/src/components/report/charts/PerformanceQuadrants.tsx:103
    Rule:        RULE_B_NUMERIC_ARRAY (Hardcoded Numeric Literal Array (3+ elements))
    Line:        {[0, 0.5, 1].map((frac, idx) => {
    Why:         Hardcoded numeric array in source fabricates data series instead of reading payload
    Remediation: Derive series dynamically from payload arrays or pass file to --allow if static axis
------------------------------------------------------------
 5. src/fe/src/components/report/charts/PerformanceQuadrants.tsx:138
    Rule:        RULE_B_NUMERIC_ARRAY (Hardcoded Numeric Literal Array (3+ elements))
    Line:        {[0, 0.5, 1].map((frac, idx) => {
    Why:         Hardcoded numeric array in source fabricates data series instead of reading payload
    Remediation: Derive series dynamically from payload arrays or pass file to --allow if static axis
------------------------------------------------------------
 6. src/fe/src/components/mock-sectors/DividendTimeline.tsx:22
    Rule:        RULE_D_PLACEHOLDER_STRING (Placeholder String Presented (N/A))
    Line:        if (val == null || Number.isNaN(Number(val))) return "N/A"
    Why:         Presents fabricated/placeholder text 'N/A' to the user
    Remediation: Render honest pending state or omit empty section
------------------------------------------------------------
 7. src/fe/src/components/mock-sectors/NewsFeedCard.tsx:28
    Rule:        RULE_D_PLACEHOLDER_STRING (Placeholder String Presented (N/A))
    Line:        if (!ts) return "N/A"
    Why:         Presents fabricated/placeholder text 'N/A' to the user
    Remediation: Render honest pending state or omit empty section
------------------------------------------------------------
 8. src/fe/src/components/mock-sectors/QuarterlyTrendChart.tsx:65
    Rule:        RULE_D_PLACEHOLDER_STRING (Placeholder String Presented (N/A))
    Line:        if (val == null || Number.isNaN(Number(val))) return "N/A"
    Why:         Presents fabricated/placeholder text 'N/A' to the user
    Remediation: Render honest pending state or omit empty section
------------------------------------------------------------
 9. src/fe/src/components/mock-sectors/QuarterlyTrendChart.tsx:326
    Rule:        RULE_D_PLACEHOLDER_STRING (Placeholder String Presented (N/A))
    Line:        <span className="text-slate-500 dark:text-slate-400">N/A</span>
    Why:         Presents fabricated/placeholder text 'N/A' to the user
    Remediation: Render honest pending state or omit empty section
------------------------------------------------------------
10. src/fe/src/components/mock-sectors/QuarterlyTrendChart.tsx:622
    Rule:        RULE_D_PLACEHOLDER_STRING (Placeholder String Presented (N/A))
    Line:        : "N/A"}
    Why:         Presents fabricated/placeholder text 'N/A' to the user
    Remediation: Render honest pending state or omit empty section
------------------------------------------------------------
11. src/fe/src/routes/agent.tsx:71
    Rule:        RULE_E_SIMULATED_DATE (Date.now() Fallback in FE State/Data)
    Line:        ts: ev.ts ?? (ev.payload?.ts || Date.now() / 1000),
    Why:         Fabricates current timestamp when backend event timestamp is missing
    Remediation: Preserve null/undefined timestamp or render pending status without inventing time
------------------------------------------------------------
12. src/fe/src/routes/agent.tsx:312
    Rule:        RULE_E_SIMULATED_DATE (Date.now() Fallback in FE State/Data)
    Line:        started_at: statusData.started_at || prev?.started_at || Date.now() / 1000,
    Why:         Fabricates current timestamp when backend event timestamp is missing
    Remediation: Preserve null/undefined timestamp or render pending status without inventing time
------------------------------------------------------------
13. src/fe/src/routes/agent.tsx:528
    Rule:        RULE_E_SIMULATED_DATE (Date.now() Fallback in FE State/Data)
    Line:        ms: j.elapsed_ms || Date.now() - startRef.current,
    Why:         Fabricates current timestamp when backend event timestamp is missing
    Remediation: Preserve null/undefined timestamp or render pending status without inventing time
------------------------------------------------------------
14. src/fe/src/routes/agent.tsx:570
    Rule:        RULE_E_SIMULATED_DATE (Date.now() Fallback in FE State/Data)
    Line:        started_at: Date.now() / 1000,
    Why:         Fabricates current timestamp when backend event timestamp is missing
    Remediation: Preserve null/undefined timestamp or render pending status without inventing time
------------------------------------------------------------
```

## Tool Output Summary

| Rule Category | Count | Description |
| :--- | :--- | :--- |
| **Rule A: Mock/Fixture Imports** | 1 | Imports of mock modules or fixture samples |
| **Rule B: Numeric Arrays** | 3 | Hardcoded numeric literal arrays (3+ elements) |
| **Rule C: Figure Fallbacks** | 1 | `?? <num>` or `\|\| <num>` fallbacks on figure names |
| **Rule D: Placeholder Strings** | 5 | Placeholder text ('lorem', 'dummy', 'TBD', 'N/A') |
| **Rule E: Simulated Values** | 4 | `Math.random` or `Date.now` feeding displayed state |

## Table of Findings

| File:Line | Pattern | Why it is fabrication | What it should render instead |
| :--- | :--- | :--- | :--- |
| `src/fe/src/routeTree.gen.ts:14` | `import { Route as MockSectorsTickerRouteImport } from './routes/mock-sectors.$ticker'` | Imports mock, fixture, or sample module instead of binding to backend payload | Remove mock import and consume live fields from ReportPayload contract |
| `src/fe/src/components/report/charts/DcfSpreadCharts.tsx:81` | `price ?? 0` | Substitutes default figure '0' when 'price' is missing, masking absent backend data | Render honest pending block (PendingBlock) or format null as '-' |
| `src/fe/src/components/report/charts/PeersCharts.tsx:251` | `[1.0, 0.5, 0.0]` | Hardcoded numeric array in source fabricates data series instead of reading payload | Derive series dynamically from payload arrays or pass file to --allow if static axis |
| `src/fe/src/components/report/charts/PerformanceQuadrants.tsx:103` | `[0, 0.5, 1]` | Hardcoded numeric array in source fabricates data series instead of reading payload | Derive series dynamically from payload arrays or pass file to --allow if static axis |
| `src/fe/src/components/report/charts/PerformanceQuadrants.tsx:138` | `[0, 0.5, 1]` | Hardcoded numeric array in source fabricates data series instead of reading payload | Derive series dynamically from payload arrays or pass file to --allow if static axis |
| `src/fe/src/components/mock-sectors/DividendTimeline.tsx:22` | `N/A` | Presents fabricated/placeholder text 'N/A' to the user | Render honest pending state or omit empty section |
| `src/fe/src/components/mock-sectors/NewsFeedCard.tsx:28` | `N/A` | Presents fabricated/placeholder text 'N/A' to the user | Render honest pending state or omit empty section |
| `src/fe/src/components/mock-sectors/QuarterlyTrendChart.tsx:65` | `N/A` | Presents fabricated/placeholder text 'N/A' to the user | Render honest pending state or omit empty section |
| `src/fe/src/components/mock-sectors/QuarterlyTrendChart.tsx:326` | `N/A` | Presents fabricated/placeholder text 'N/A' to the user | Render honest pending state or omit empty section |
| `src/fe/src/components/mock-sectors/QuarterlyTrendChart.tsx:622` | `N/A` | Presents fabricated/placeholder text 'N/A' to the user | Render honest pending state or omit empty section |
| `src/fe/src/routes/agent.tsx:71` | `Date.now()` | Fabricates current timestamp when backend event timestamp is missing | Preserve null/undefined timestamp or render pending status without inventing time |
| `src/fe/src/routes/agent.tsx:312` | `Date.now()` | Fabricates current timestamp when backend event timestamp is missing | Preserve null/undefined timestamp or render pending status without inventing time |
| `src/fe/src/routes/agent.tsx:528` | `Date.now()` | Fabricates current timestamp when backend event timestamp is missing | Preserve null/undefined timestamp or render pending status without inventing time |
| `src/fe/src/routes/agent.tsx:570` | `Date.now()` | Fabricates current timestamp when backend event timestamp is missing | Preserve null/undefined timestamp or render pending status without inventing time |

## Limits of this Check

1. **Static Heuristic Boundaries**: The scanner uses robust lexical and pattern analysis. While it detects mock imports, hardcoded numeric arrays, figure fallbacks, placeholders, and synthetic time generators, it cannot guarantee complete runtime semantic correctness across complex dynamic function invocations.
2. **Payload Leaf Cross-Check**: Cross-checking numbers extracted from backend payloads against frontend literals is an investigative tool. A frontend figure may be mathematically scaled (e.g. multiplied by 100 for percentages), formatted into localized strings (Indonesian dot/comma separators), rounded, or represent SVG coordinate geometry. A discrepancy flags a candidate for manual review, not definitive proof of fabrication.
3. **Absence State Verification**: This tool verifies that code does not substitute zero or hardcoded fallbacks when data is missing. It works in tandem with payload contract schemas (`docs/fe-payload-contract.json`) and house format visual verifiers (`scripts/verify_house_format.py`).
