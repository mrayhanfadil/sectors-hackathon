# Slide 6 & 7 — Financial Statements & Key Ratios spec (AMMN)

Ticker: AMMN (PT Amman Mineral Internasional Tbk, AMMN IJ). Sector: copper-gold mining (non-bank general corporate miner).
Archetype: Non-bank capital-intensive resources / mining (Batu Hijau open pit Phase 7/8, copper/gold concentrate, smelter ramp-up). Bank-style financial structure does NOT apply (bank sector switch noted as architectural record only).

---

## 1. Purpose

Slides 6 and 7 provide the comprehensive, full-length 5-year financial statement projections (2024A–2028F) and structural financial ratio analysis for institutional readers (portfolio managers, credit analysts, investment committee members, and model auditors).

- **Slide 6 (Accounting Position & Earnings)**: Houses **Exhibit 14 (Income Statement)** and **Exhibit 15 (Balance Sheet)** in a vertically stacked layout (~50% height each). Establishes operational revenue generation, cost structure, operational leverage (EBITDA/EBIT), debt service burden, asset intensity, capital structure, and solvency.
- **Slide 7 (Cash Generation & Performance Ratios)**: Houses **Exhibit 16 (Cash Flow Statement)** and **Exhibit 17 (Key Financial Ratios)** in a vertically stacked layout (~55% and ~45% height). Details cash flow dynamics (Operating, Investing, Financing), cash reconciliation, capex requirements (smelter completion and mine development), and computes canonical sell-side growth, margin, return, and leverage metrics.
- **Model Rigor Rule**: The four exhibits form a closed, dynamically linked accounting system. Disconnected static figures, hardcoded orphan rows, or synthetic gap-fillers are strictly prohibited. Every cell reconciles across the entire report deck.

---

## 2. Global House Rules & Formatting Standards (Binding)

Every table and element emitted under this specification must strictly comply with the binding rules in [`docs/rules/house-report-format.md`](file:///home/fadil/projects/sectors-hackathon/docs/rules/house-report-format.md):

### 2.1 Exhibit Labeling & Numbering
- **Label above every object**: Format `Exhibit [nomor]. [deskripsi singkat, deskriptif]`.
  - Canonical titles:
    - Slide 6 Top: `Exhibit 14. Income Statement (2024A-2028F)`
    - Slide 6 Bottom: `Exhibit 15. Balance Sheet (2024A-2028F)`
    - Slide 7 Top: `Exhibit 16. Cash Flow Statement (2024A-2028F)`
    - Slide 7 Bottom: `Exhibit 17. Key Financial Ratios (2024A-2028F)`
  - Never use generic titles (e.g. `Exhibit 14. Table`, `Exhibit 15. Data`).
- **Global counter owned by renderer**: The exhibit number is a document-global counter managed by Typst (`kind: "exhibit"`). Data payloads must **never** supply a pre-numbered `id` (e.g. banned: `"id": "Exhibit 14"`).
- **Constant source line below every object**: The visible line below each exhibit is always, without exception:
  ```
  Source: Company, Team Estimates
  ```
  Even for purely historical lapkeu data, the printed line is invariant. Internal provenance (Sectors API, IDX filings, modeler calculations) is retained in the data payload audit fields, never printed on the house PDF.

### 2.2 Table Layout & Styling
- **Header row**: Dark navy background (`#0A2540`), bold white text, center-aligned for year columns, left-aligned for item descriptions.
- **Columns (5-year rolling horizon)**: `2024A`, `2025A`, `2026F`, `2027F`, `2028F` (2 actual historical years, 3 forecast years).
- **Alignment**:
  - Line item descriptions: Left-aligned with hierarchical indentation for child items.
  - Numerical values: Right-aligned across all 5 period columns.
- **Negative numbers convention**:
  - Sell-side institutional convention: Negatives are strictly displayed in parentheses `(x,xxx)` or `(x.x)`.
  - **Zero minus signs (`-`)**: Minus signs are strictly prohibited in printed tables.
- **Deduction line items**: Operating expenses, COGS, interest expense, taxes, capex, and dividends are explicitly enclosed in parentheses `(...)`.
- **Subtotals and totals**: Rendered in **bold text** with subtle top/bottom borders.
- **Highlighting**:
  - `Net Profit` in Exhibit 14 is bold with shaded background highlight (the most critical bottom-line figure).
  - `Ending Cash Balance` in Exhibit 16 and `Total Liabilities & Equity` in Exhibit 15 are bolded.
- **Number precision & units**:
  - Absolute statements (Exhibits 14, 15, 16): Reported in `US$ mn` (AMMN's functional reporting currency) or `Rp bn` if explicitly translated, with unit stated in table header/subhead. No decimals for Rp bn; 1 decimal or integer for US$ mn (applied consistently). If converted to IDR, the conversion FX rate (USDIDR) must match Slide 1 and Slide 4 valuation assumptions to the rupiah.
  - Key Ratios (Exhibit 17): Strictly **ONE decimal place** everywhere (`0.0%`, `0.0x`).
- **Renderer-owned furniture**: Page headers, Sectors.app logo, `#067647` divider, and footers (`sectors.app` / disclosure pointer + page number) are drawn natively by the renderer.

---

## 3. Slide 6 Specification — Exhibit 14 & Exhibit 15 (Stacked)

Slide 6 presents the income and financial position statements stacked vertically.

### 3.1 Exhibit 14 — Income Statement (2024A-2028F)

#### Layout & Hierarchy
- Label: `Exhibit 14. Income Statement (2024A-2028F)`
- Source: `Source: Company, Team Estimates`
- Columns: `Line Item`, `2024A`, `2025A`, `2026F`, `2027F`, `2028F`

#### Row Order Specification
Rows must appear in the following exact sequence:

| # | Line Item | Display Style | Math / Accounting Definition |
|---|---|---|---|
| 1 | Revenue/Sales | Regular | Gross sales from copper concentrate, copper cathode, gold, and silver |
| 2 | Cost of Goods Sold (COGS) | Regular `(parentheses)` | Direct mining, milling, processing, TC/RC, royalties (ESDM), export duties |
| 3 | **Gross Profit** | **Bold subtotal** | `Revenue - COGS` |
| 4 | SG&A / Operating Expenses | Regular `(parentheses)` | General corporate overhead, selling, marketing, logistics, handling |
| 5 | **EBIT** | **Bold subtotal** | `Gross Profit - SG&A / Operating Expenses` (Operating Profit) |
| 6 | Interest Income | Regular | Finance income from bank deposits, short-term placements |
| 7 | Interest Expense | Regular `(parentheses)` | Borrowing costs on syndicated loans, credit facilities, bonds |
| 8 | Other Non-Operating Income / (Expense) | Regular `(net)` | FX gains/(losses), gain on asset disposal, other non-core items |
| 9 | **Pre-tax Profit** | **Bold subtotal** | `EBIT + Interest Income - Interest Expense + Other Non-Operating` |
| 10 | Income Tax | Regular `(parentheses)` | Corporate income tax expense (effective tax rate applied to EBT) |
| 11 | Minority Interest | Regular `(parentheses/net)` | Non-controlling interests in subsidiaries (e.g. PT Amman Mineral Nusa Tenggara) |
| 12 | **Net Profit** | **Bold highlight** | `Pre-tax Profit - Income Tax - Minority Interest` (Headline Net Income) |

#### Mining Operational Notes for AMMN
- **Revenue Drivers**: Copper cathode & gold volume ramp post-smelter commissioning; realized copper price (US$/lb) and gold price (US$/oz).
- **COGS Structure**: Includes treatment charges and refining charges (TC/RC) paid to third parties, transitioning to internal processing costs once the Sumbawa smelter reaches full commercial operation. Royalties to the Indonesian Government (ESDM) and progressive export duties under MEMR regulations.
- **EBITDA Reconciler**: While EBITDA is not an explicit line in the standard P&L stack, it is derived as `EBIT + Depreciation & Amortization` and must reconcile identically to Exhibit 3 (Slide 1) and Exhibit 17.

---

### 3.2 Exhibit 15 — Balance Sheet (2024A-2028F)

#### Layout & Hierarchy
- Label: `Exhibit 15. Balance Sheet (2024A-2028F)`
- Source: `Source: Company, Team Estimates`
- Columns: `Line Item`, `2024A`, `2025A`, `2026F`, `2027F`, `2028F`
- Structure: Split into Assets followed by Liabilities & Equity, with bold subtotal dividers.

#### Row Order Specification
Rows must appear in the following exact sequence:

| Section | # | Line Item | Display Style | Accounting Definition |
|---|---|---|---|---|
| **Assets** | 1 | Cash & Equivalents | Regular | Cash on hand, bank deposits, short-term highly liquid investments (must match Ex 16 Ending Cash) |
| | 2 | Trade Receivables | Regular | Outstanding balances from smelters/buyers for concentrate/cathode shipments |
| | 3 | Inventory | Regular | Stockpiles of ore, copper concentrates, refined cathodes, spare parts & supplies |
| | 4 | Other Current Assets | Regular | Prepaid taxes, advances, other short-term assets |
| | 5 | **Total Current Assets** | **Bold subtotal** | `Sum(Cash, Receivables, Inventory, Other Current Assets)` |
| | 6 | Net Fixed Assets | Regular | Property, plant and equipment net of accumulated depreciation (includes smelter facility & Batu Hijau infrastructure) |
| | 7 | Other Non-Current Assets | Regular | Mining properties, mine development assets, deferred stripping costs, reclamation escrow |
| | 8 | **Total Assets** | **Bold total** | `Total Current Assets + Net Fixed Assets + Other Non-Current Assets` |
| **Liabilities & Equity** | 9 | Short-term Debt | Regular | Working capital borrowings, current portion of syndicated term loans |
| | 10 | Trade Payables | Regular | Amounts due to contractors, fuel suppliers, explosive/chemical vendors |
| | 11 | Other Current Liabilities | Regular | Accrued royalties, current tax payable, accrued employee benefits |
| | 12 | **Total Current Liabilities** | **Bold subtotal** | `Sum(Short-term Debt, Trade Payables, Other Current Liabilities)` |
| | 13 | Long-term Debt | Regular | Non-current portion of syndicated bank term loans (smelter financing, senior debt) |
| | 14 | Other Non-Current Liabilities | Regular | Provision for mine closure & environmental rehabilitation, deferred tax liabilities |
| | 15 | **Total Liabilities** | **Bold subtotal** | `Total Current Liabilities + Long-term Debt + Other Non-Current Liabilities` |
| | 16 | Shareholders' Equity | Regular | Share capital, additional paid-in capital, retained earnings, NCI |
| | 17 | **Total Liabilities & Equity** | **Bold total** | `Total Liabilities + Shareholders' Equity` (**MUST equal Total Assets**) |

#### Hard Balance Check Constraint
- For every single period $t \in [2024\text{A}, 2025\text{A}, 2026\text{F}, 2027\text{F}, 2028\text{F}]$:
  $$\text{Total Assets}_t - \text{Total Liabilities \& Equity}_t = 0$$
- Any non-zero difference (exceeding 0.01 units due to rounding) constitutes an unbalance condition and causes an immediate Critic rejection.

---

### 3.3 Bank Variant Specification (Record Switch Note — NOT built for AMMN)

For banking and financial institution archetypes (e.g. BBTN, BBCA), the general corporate structure above is replaced by the banking-specific presentation:

```
[SECTOR SWITCH: General Corporate / Mining -> Banking]
AMMN Status: DEACTIVATED (AMMN is a non-bank corporate miner; this switch is NOT built for AMMN).
```

When activated for banking tickers, the engine applies the following canonical structure:
- **Bank Income Statement**:
  - `Interest Income`
  - `Interest Expense` `(parentheses)`
  - **`Net Interest Income (NII)`** `(bold subtotal)`
  - `Non-Interest Income` (Fee-based, FX, treasury)
  - `Operating Expenses` `(parentheses)`
  - **`Pre-Provision Operating Profit (PPOP)`** `(bold subtotal)`
  - `Provisions & Allowances (Cost of Credit)` `(parentheses)`
  - **`Operating Profit`** `(bold subtotal)`
  - `Non-Operating Items` `(net)`
  - **`Pre-tax Profit`** `(bold subtotal)`
  - `Income Tax` `(parentheses)`
  - **`Net Profit`** `(bold highlight)`
- **Bank Balance Sheet**:
  - *Earning Assets*: `Cash & Central Bank Placements`, `Gross Loans`, `Provisions for Impairment (Allowance)` `(parentheses)`, `Net Loans`, `Government Bonds / Surat Berharga`, `Other Securities & Placements`.
  - **`Total Earning Assets`** `(bold subtotal)`.
  - *Non-Earning Assets*: `Fixed Assets & Other Assets`.
  - **`Total Assets`** `(bold total)`.
  - *Liabilities*: `Customer Deposits` (`CASA` + `Time Deposits`), `Borrowings & Debt Issued`, `Other Liabilities`.
  - **`Total Liabilities`** `(bold subtotal)`.
  - *Equity*: `Shareholders' Funds / Total Equity`.
  - **`Total Liabilities & Equity`** `(bold total, balances to Total Assets)`.

---

## 4. Slide 7 Specification — Exhibit 16 & Exhibit 17

Slide 7 presents the cash generation statement and key financial ratios.

### 4.1 Exhibit 16 — Cash Flow Statement (2024A-2028F)

#### Layout & Hierarchy
- Label: `Exhibit 16. Cash Flow Statement (2024A-2028F)`
- Source: `Source: Company, Team Estimates`
- Columns: `Line Item`, `2024A`, `2025A`, `2026F`, `2027F`, `2028F`
- Structure: Divided into 3 operating/investing/financing sections, followed by cash closing reconciliation, and a memo cross-check row below a visual horizontal divider.

#### Row Order Specification
Rows must appear in the following exact sequence:

| Section | # | Line Item | Display Style | Accounting Definition / Link |
|---|---|---|---|---|
| **Cash Flow from Operations** | 1 | Net Profit | Regular | **Starting point** — MUST equal Exhibit 14 Net Profit |
| | 2 | (+) Depreciation & Amortization | Regular | Non-cash D&A addback (mining equipment, plant, smelter) |
| | 3 | (-)/(+) Working Capital change | Regular | Net change in operating assets and liabilities `(ΔReceivables + ΔInventory - ΔPayables)` |
| | 4 | Other Operating Items | Regular | Non-cash provisions, rehabilitation accruals, other items |
| | 5 | **Net Cash from Operations** | **Bold subtotal** | `Net Profit + D&A + Working Capital Change + Other Operating Items` |
| **Cash Flow from Investing** | 6 | (-) Capital Expenditure (Capex) | Regular `(parentheses)` | Mine development (Batu Hijau Phase 7/8), waste stripping, smelter construction capex |
| | 7 | Other Investing Items | Regular | Proceeds from asset sales, exploration advances, interest received |
| | 8 | **Net Cash from Investing** | **Bold subtotal** | `Capex + Other Investing Items` (normally negative, in parentheses) |
| **Cash Flow from Financing** | 9 | Debt Raised / (Repaid) | Regular | Net drawdowns minus amortizations of syndicated credit facilities |
| | 10 | Dividends Paid | Regular `(parentheses)` | Dividend distributions to equity holders |
| | 11 | Equity Raised / (Buyback) | Regular | Proceeds from share issuances / IPO proceeds / (share repurchases) |
| | 12 | **Net Cash from Financing** | **Bold subtotal** | `Debt Raised/(Repaid) + Dividends Paid + Equity Raised/(Buyback)` |
| **Closing Cash Position** | 13 | Net Change in Cash | Regular | `Net Cash from Operations + Net Cash from Investing + Net Cash from Financing` |
| | 14 | Beginning Cash Balance | Regular | Cash & Equivalents at beginning of period (equals prior period Ending Cash) |
| | 15 | **Ending Cash Balance** | **Bold total** | `Beginning Cash + Net Change in Cash` (**MUST equal Exhibit 15 Cash & Equivalents**) |
| **Memo Row (Separator)** | 16 | **Free Cash Flow (FCF)** | **Bold italic memo** | `Net Cash from Operations - Capital Expenditure` |

#### Free Cash Flow Memo Row & Slide 4 FCFF Cross-Check
- **Equation**: $$\text{FCF} = \text{Net Cash from Operations} - \text{Capital Expenditure}$$
- **Role**: Institutional cross-check against Slide 4 Exhibit 8 (FCFF Forecast in DCF).
- **Theoretical Bridge**:
  - Slide 4 **FCFF** (Free Cash Flow to Firm) is an **unlevered** metric starting from NOPAT:
    $$\text{FCFF} = \text{NOPAT} + \text{D\&A} - \text{Capex} - \Delta\text{NWC}$$
    where $\text{NOPAT} = \text{EBIT} \times (1 - \text{tax rate})$.
  - Exhibit 16 **FCF** is a **levered cash flow metric** starting from Net Profit (or CFO):
    $$\text{FCF} = \text{CFO} - \text{Capex}$$
  - The reconciliation between the two:
    $$\text{FCFF} \approx \text{FCF} + \text{Interest Expense} \times (1 - \text{tax rate}) - \text{Interest Income} \times (1 - \text{tax rate}) + \text{Non-operating / Financing items in CFO}$$
- **Sanity Check Discipline**: While FCF and FCFF are not identical, they must track within the same economic ballpark. A wide unexplained divergence (>15–20%) indicates mismatched capex schedules, inconsistent working capital assumptions, or double-counted financing items between the DCF valuation sheet and the financial statement models.

---

### 4.2 Exhibit 17 — Key Financial Ratios (2024A-2028F)

#### Layout & Precision Standards
- Label: `Exhibit 17. Key Financial Ratios (2024A-2028F)`
- Source: `Source: Company, Team Estimates`
- Columns: `Ratio`, `2024A`, `2025A`, `2026F`, `2027F`, `2028F`
- **Formatting Rules (Strictly Enforced)**:
  - **ONE decimal place everywhere** (`0.0%`, `0.0x`).
  - **Negatives in parentheses `(x.x)`** — sell-side convention, NO minus signs (`-`).
  - **Section headers**: Bold font with distinct vertical spacing before each section.

#### Row Order Specification
Divided into 3 distinct sections:

| Section | # | Ratio Name | Unit | Exact Formula |
|---|---|---|---|---|
| **Growth (% yoy)** | 1 | Sales Growth | `%` | `(Revenue_t / Revenue_{t-1} - 1) * 100` |
| | 2 | EBITDA Growth | `%` | `(EBITDA_t / EBITDA_{t-1} - 1) * 100` |
| | 3 | Operating Profit (EBIT) Growth | `%` | `(EBIT_t / EBIT_{t-1} - 1) * 100` |
| | 4 | Net Profit Growth | `%` | `(Net Profit_t / Net Profit_{t-1} - 1) * 100` |
| **Profitability (%)** | 5 | Gross Margin | `%` | `(Gross Profit / Revenue) * 100` |
| | 6 | EBITDA Margin | `%` | `(EBITDA / Revenue) * 100` |
| | 7 | Operating Margin | `%` | `(EBIT / Revenue) * 100` |
| | 8 | Net Margin | `%` | `(Net Profit / Revenue) * 100` |
| | 9 | Return on Average Assets (ROAA) | `%` | `(Net Profit / ((Total Assets_t + Total Assets_{t-1}) / 2)) * 100` |
| | 10 | Return on Average Equity (ROAE) | `%` | `(Net Profit / ((Equity_t + Equity_{t-1}) / 2)) * 100` |
| **Leverage & Coverage (x)** | 11 | Net Gearing | `x` | `(Total Debt - Cash & Equivalents) / Shareholders' Equity`<br>*Note: Total Debt = Short-term Debt + Long-term Debt. Net Cash position displayed in parentheses `(0.1)x`.* |
| | 12 | Interest Coverage | `x` | `EBIT / Interest Expense`<br>*Note: If Interest Expense is 0, display `N/A`.* |

*Note on 2024A Growth: 2024A to 2025A represents historical actual growth. 2024A growth utilizes 2023A actual audited base.*

---

### 4.3 Bank Variant Key Ratios Note (Record Switch Only — NOT built for AMMN)

For banking archetypes (e.g. BBTN/BBCA), Exhibit 17 is completely replaced by banking performance metrics:

```
[SECTOR SWITCH: Non-Bank Key Ratios -> Bank Key Ratios]
AMMN Status: DEACTIVATED (AMMN uses general corporate / mining ratios).
```

When activated for banks, the ratio schedule comprises:
- **Margins & Spread**: `Yield on Earning Assets (%)`, `Cost of Funds (CoF) (%)`, `Interest Spread (%)`, `Net Interest Margin (NIM) (%)`.
- **Efficiency & Asset Quality**: `Cost to Income Ratio (CIR) (%)`, `Gross NPL Ratio (%)`, `Loan Loss Provision (LLP) Coverage (%)`, `Cost of Credit (CoC) (%)`.
- **Liquidity & Funding**: `Loan to Deposit Ratio (LDR) (%)`, `CASA Ratio (%)`.
- **Profitability & Capital**: `ROAE (%)`, `ROAA (%)`, `Capital Adequacy Ratio (CAR) (%)`.
- **Dupont Analysis Breakdown** (included if space permits):
  $$\text{ROAE} = \text{Pre-Tax ROAA} \times \text{Tax Retention Rate} \times \text{Asset Leverage (Assets/Equity)}$$

---

## 5. Hard Tie-Out Matrix (Cross-Checks & Link Integrity)

The following reconciliation conditions are mathematically binding. A mismatch at any check constitutes a broken model link and immediately blocks report publication:

| Check ID | Source Line Item | Target Line Item | Condition / Formula | Tolerance | Failure Handling |
|---|---|---|---|---|---|
| **TIE-01** | Exhibit 14: `Net Profit` | Exhibit 3 (Slide 1): `Net Profit` | `Ex 14 Net Profit == Ex 3 Net Profit` | Strictly 0 (<0.1% rounding) | **CRITICAL STOP**: Re-export Exhibit 3 from statement model |
| **TIE-02** | Exhibit 14: `Net Profit` | Exhibit 16: `Net Profit` (CFO start) | `Ex 14 Net Profit == Ex 16 Starting CFO` | Strictly 0 (0.00) | **CRITICAL STOP**: Fix cash flow model link |
| **TIE-03** | Exhibit 16: `Ending Cash Balance` | Exhibit 15: `Cash & Equivalents` | `Ex 16 Ending Cash == Ex 15 Cash & Equivalents` | Strictly 0 (0.00) | **CRITICAL STOP**: Balance sheet cash linkage error |
| **TIE-04** | Exhibit 15: `Total Assets` | Exhibit 15: `Total Liabilities & Equity` | `Total Assets == Total Liabilities & Equity` | Zero delta (`0.00`) | **CRITICAL STOP**: Unbalanced balance sheet; model rejected |
| **TIE-05** | Exhibit 14: `Revenue/Sales` | Exhibit 3 (Slide 1) & Exhibit 4 (Slide 3) | `Ex 14 Revenue == Ex 3 Revenue == Ex 4 Revenue` | Strictly 0 (<0.1% rounding) | **CRITICAL STOP**: Sync forecast revenue deck |
| **TIE-06** | Exhibit 14 / Ex 17: `EBITDA` | Exhibit 3 (Slide 1) & Exhibit 5 (Slide 3) | `Ex 14 EBITDA == Ex 3 EBITDA == Ex 5 EBITDA` | Strictly 0 (<0.1% rounding) | **CRITICAL STOP**: Sync operational EBITDA deck |
| **TIE-07** | Exhibit 16: `Capex` | Slide 4 Exhibit 8: `Capex` | `Ex 16 Capex == Slide 4 DCF Capex` | Strictly 0 (0.00) | **CRITICAL STOP**: Smelter / expansion capex schedule conflict |
| **TIE-08** | Exhibit 16 Memo: `Free Cash Flow` | Slide 4 Exhibit 8: `FCFF` | Ballpark consistency check: `abs(FCFF - (FCF + Net Int*(1-t))) / FCFF < 0.15` | < 15% delta | **AUDIT WARNING**: Flag reconciliation bridge for analyst review |
| **TIE-09** | Exhibit 17: `Growth (%)` | Exhibit 14: `Revenue`, `EBITDA`, `EBIT`, `Net Profit` | Exact yoy formula match | Exact to 1 decimal | **CRITICAL STOP**: Recompute ratio table |
| **TIE-10** | Exhibit 17: `Net Gearing (x)` | Exhibit 15: `Short-term Debt`, `Long-term Debt`, `Cash`, `Equity` | `(ST Debt + LT Debt - Cash) / Equity` | Exact to 1 decimal | **CRITICAL STOP**: Recompute gearing ratio |

---

## 6. Data Dependencies & Modeling Logic

### 6.1 Primary Sectors Data Endpoints
- **Historical Data (2024A, 2025A)**:
  - `financials("AMMN")` → `/company/financials/` (annual audited balance sheet, income statement, cash flow).
  - `quarterly("AMMN")` → `/financials/quarterly/` for latest quarterly run-rate reconciliation.
  - `mining_company_financials("AMMN")` → `/mining/companies/financials/` for production volume, ore throughput, and cash costs.
- **Forecast Period (2026F–2028F)**:
  - Generated by financial modeling engine based on:
    1. Copper production schedule (Batu Hijau Phase 7 completion, Phase 8 ramp).
    2. Realized copper and gold price decks (stated in Slide 4 assumptions).
    3. Smelter capex and commissioning timeline (commercial operation date, processing capacity 900kt concentrate/year).
    4. Financing schedule: syndicated loan repayment schedule and interest rate assumptions.

### 6.2 Currency & FX Discipline
- **AMMN Functional Currency**: AMMN prepares statutory accounts in **USD**.
- **Display Standard**: Statements can be presented in `US$ mn` (native) or translated to `Rp bn`.
- **Conversion Rule**: If translated to `Rp bn`, the FX rate (USDIDR) applied must be identical to the FX rate stated in Slide 1 sidebar and Slide 4 valuation assumptions (e.g. USDIDR 16,200 as of valuation cut-off). Never use unaligned FX rates between slides.

---

## 7. Critic Checks (Gate Before Ship)

Before emitting the document or approving the model output, the Critic gate validates the following checklist:

- [ ] **No Hardcoded Numbers / IDs**: Zero literal `"Exhibit N"` strings or `"id": "Exhibit N"` fields in data payloads; renderer owns figure counter.
- [ ] **Descriptive Labels & Constant Sourcing**:
  - Exhibit 14 labeled `Income Statement (2024A-2028F)` with `Source: Company, Team Estimates` below.
  - Exhibit 15 labeled `Balance Sheet (2024A-2028F)` with `Source: Company, Team Estimates` below.
  - Exhibit 16 labeled `Cash Flow Statement (2024A-2028F)` with `Source: Company, Team Estimates` below.
  - Exhibit 17 labeled `Key Financial Ratios (2024A-2028F)` with `Source: Company, Team Estimates` below.
- [ ] **Columns Pinned**: Exactly 5 columns labeled `2024A`, `2025A`, `2026F`, `2027F`, `2028F` in dark navy header rows with white text.
- [ ] **Parentheses Discipline**: All negative numbers, deductions (COGS, SG&A, Interest Expense, Tax, Capex, Dividends), and net cash figures are enclosed in parentheses `(...)`. **Zero minus signs (`-`)** appear in the tables.
- [ ] **Exhibit 14 Integrity**:
  - Row order matches spec: Revenue, COGS, Gross Profit, SG&A, EBIT, Interest Income, Interest Expense, Other Non-Operating, Pre-tax Profit, Income Tax, Minority Interest, Net Profit.
  - Subtotals bolded; `Net Profit` bolded and visually highlighted.
- [ ] **Exhibit 15 Balance Check**:
  - `Total Assets == Total Liabilities & Equity` holds cell-for-cell for all 5 years (difference == 0.00).
  - Cash & Equivalents matches Exhibit 16 Ending Cash.
- [ ] **Exhibit 16 Cash Flow Structure**:
  - Starts with Net Profit (matching Exhibit 14).
  - 3 canonical sections: Operations, Investing, Financing.
  - Ending Cash Balance equals Beginning Cash + Net Change in Cash.
  - Memo row `Free Cash Flow` = `CFO - Capex` is present below separator and cross-checked vs Slide 4 FCFF.
- [ ] **Exhibit 17 Ratio Standards**:
  - Strictly ONE decimal place everywhere (`0.0%`, `0.0x`).
  - 3 distinct sections: Growth (% yoy), Profitability (%), Leverage & Coverage (x).
  - Section headers bolded with vertical spacing.
  - Net Gearing and Interest Coverage formulas match definitions.
- [ ] **Tie-Out Matrix 100% Verified**:
  - `Net Profit (Ex 14) == Net Profit (Ex 3) == Net Profit (Ex 16 CFO Start)`.
  - `Ending Cash (Ex 16) == Cash & Equivalents (Ex 15)`.
  - `Revenue (Ex 14) == Revenue (Ex 3) == Revenue (Ex 4)`.
  - `EBITDA (Ex 14/17) == EBITDA (Ex 3) == EBITDA (Ex 5)`.
  - Capex aligns between Exhibit 16 and Slide 4 DCF.
- [ ] **Sector Switch Verification**: Bank variant is documented as a dormant switch; AMMN cleanly uses the non-bank mining general corporate schema.
