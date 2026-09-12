# Slide 4 — Intrinsic Valuation spec (AMMN)

Ticker: AMMN (PT Amman Mineral Internasional Tbk, AMMN IJ). Sector: copper-gold mining.
Anchor method: DCF-SHORTENED (reserve-life explicit horizon + fade). Cross-checks:
RNAV (Batu Hijau + Elang + exploration + smelter interest) and EV/EBITDA on
MID-CYCLE EBITDA (3Y average, constituent years cited — never TTM/peak). DDM only
if gate allows (payout > 0 AND DPS history present); otherwise DDM is skipped with
reason recorded in method_gate.

## 1. Method choice + why

- Perpetual-growth Gordon terminal value is NOT defensible for a depleting-reserve
  miner. A growing perpetuity on peak-cycle cash flow overstates a finite asset.
- ANCHOR = DCF-shortened: explicit forecast horizon tied to reserve life (Batu Hijau
  remaining life + Elang development timeline), then a fade (declining growth /
  declining margin towards mid-cycle), then a terminal value on the FADED base with
  g capped at/below long-term GDP growth. No smooth growth through a known smelter
  / expansion capex cycle.
- CROSS-CHECK 1 = RNAV: per-asset project DCFs (Batu Hijau producing, Elang
  development-stage with higher discount rate, exploration option value, smelter
  interest) summed to attributable NAV, then corporate overhead PV deducted, then
  an explicit discount-to-RNAV to reach TP.
- CROSS-CHECK 2 = EV/EBITDA on MID-CYCLE EBITDA: 3Y average EBITDA with all 3
  constituent years cited. Peak-earnings-on-peak-multiple is the classic cyclical
  overvaluation trap — this spec forbids TTM/peak EBITDA as the multiple base.
- FRAMING = SINGLE-TP: exactly ONE headline TP = the anchor (DCF-shortened FV,
  normally converging with RNAV). RNAV-per-share and EV/EBITDA-implied values are
  labelled cross-checks with their OWN upsides stated separately — never silently
  averaged into the anchor.
- DDM leg: gated. Allowed only if payout_ratio > 0 AND dps_history_years >= 2
  (gate inputs). If allowed it uses CoE (NOT WACC) and payout capped <= 100% every
  year tested vs 3Y NORMALIZED EPS (not forward EPS), with D0->D1 timing lock.

## 2. Exhibit specs (titles + data only — NO literal numbers, NO id field)

House rule: renderer owns the global `Exhibit N` counter (Typst figure counter
`kind: "exhibit"`). This spec supplies titles + row/column structure + data
bindings only. No hand-numbered exhibit literals in payloads, no `id` fields, no
header/footer/logo/page-number furniture. Label above each object (descriptive,
never generic "Table"); source line below exactly `Source: Company, Team Estimates`.

### Exhibit — FCFF Forecast and Terminal Value (3-block table)

Block 1 — explicit period (reserve-life horizon, typically 5Y: current year + 4):

| Row | Definition / binding |
|---|---|
| Revenue | Sectors mining/financials forecast; Slide 3 tie-out (same revenue years). Copper/gold realised price x volume, NOT top-down % growth alone. |
| EBIT | Operating earnings; consistent with Slide 3 EBITDA minus D&A. |
| Tax on EBIT | EBIT x effective rate (NOT statutory). Effective rate stated in assumptions with source years. |
| NOPAT | EBIT minus Tax on EBIT. |
| + D&A | Depreciation & amortisation add-back. |
| − Capex | MUST deduct announced expansion capex (smelter / capacity roadmap from news_output). Unknown schedule → explicit disclosed FCF haircut + uncertainty flag, never smooth growth through a known expansion cycle. |
| −/+ NWC change | Increase/Decrease in Net Working Capital, sign-explicit. |
| FCFF (bold) | Subtotal. |
| FCFF growth % | yoy; fade must be visible (growth declining towards terminal g). |
| Discount factor | 1/(1+WACC)^n, n = year index from valuation date. |
| PV of FCFF (bold) | FCFF x discount factor. |

Block 2 — terminal:

| Row | Rule |
|---|---|
| Terminal FCFF | Last explicit FCFF x (1 + terminal g), on the FADED base. |
| Terminal g | Explicit assumption, capped at/below long-term GDP growth. State cap basis. |
| Terminal Value (undiscounted) | Gordon: Terminal FCFF x (1+g) / (WACC − g), or Exit Multiple leg. |
| Discount factor (terminal) | 1/(1+WACC)^T. |
| PV of TV | TV x discount factor. |
| Gordon vs Exit Multiple | If both computed: side-by-side columns. Material gaps flagged as unresolved assumptions, NEVER silently averaged. |

Block 3 — bridge to equity:

Sum PV FCFF + PV TV = EV (bold) − Net Debt (Total Debt − Cash at valuation date,
date stated) +/− MI / non-operating assets = Equity Value (bold) / shares
outstanding = Fair Value per share (bold highlight).

Traceability footer (assumption fields, not furniture): Rf source (INDOGB 10Y for
IDR), ERP source (Damodaran), Beta source (Bloomberg), valuation date, share count
source. Same values as the assumption table in section 4.

### Exhibit — WACC Components (2-col parameter|value)

| Parameter | Value / rule |
|---|---|
| Risk-free rate (Rf) | INDOGB 10Y, with as-of date. |
| Beta | Bloomberg, with as-of date / version. |
| Equity Risk Premium (ERP) | Damodaran, with vintage. |
| Cost of Equity (CoE) | CAPM: Rf + Beta x ERP. |
| Pre-tax Cost of Debt (CoD) | Existing coupon average (outstanding borrowings). |
| Effective tax rate | Same rate used in Block 1 Tax on EBIT. |
| After-tax CoD | Pre-tax CoD x (1 − effective tax). |
| Weight of Debt D/(D+E) | Market-value weights where possible. |
| Weight of Equity E/(D+E) | Market-value weights where possible. |
| WACC (bold, bottom row) | CoE x wE + after-tax CoD x wD. |

Rules: DDM/GGM legs (if gated) discount with CoE, NOT WACC — equity cash flows.
WACC SENSITIVITY DISCLOSURE: if weight_equity is modeler-selected (not in the
assumptions file), disclose the DCF range under BOTH selected weights AND
spot-gearing weights from latest D/E — never publish a single DCF point from an
unsourced weight.

### Exhibit — Sensitivity Analysis (matrix)

- Rows: WACC −1%, −0.5%, base, +0.5%, +1% from the WACC used in the FCFF exhibit.
- Columns: terminal g steps (or exit multiple steps if Exit Multiple is the
  terminal leg).
- Cells: Fair Value per share for that combination. Base case cell highlighted
  (renderer-owned highlight; spec marks which cell is base).
- State explicitly which parameter the FV is most sensitive to (usually
  terminal g) in the narrative — computed from the matrix range, not assumed.

### Exhibit — RNAV Bridge (Opsi C applied to AMMN)

Block 1 — per-asset rows (one row per asset; columns: asset | size |
NAV (100%) | AMMN ownership % | attributable NAV):

| Asset | Size field | NAV basis |
|---|---|---|
| Batu Hijau (producing) | Reserves ton + grade + remaining life | Project DCF at producing-asset discount rate, or independent appraisal. |
| Elang (development) | Resources/reserves ton + grade + timeline to production | Project DCF at HIGHER development-stage discount rate, or appraisal. Must exceed Batu Hijau rate — record both. |
| Exploration / other tenements | Area / resource statement | Option/appraisal value; if nil, state nil explicitly, never zero-fill silently. |
| Smelter interest | Capacity + AMMN stake + commissioning progress | Attributable project NAV or equity-accounted value; capex still to spend must already sit in the asset DCF, not re-deducted in the bridge. |

Block 2 — bridge:

Sum attributable NAV + Cash − Total Debt − Corporate overhead PV (unallocated
G&A capitalised at WACC, stated) = Total RNAV (bold) / shares = RNAV per share
− Discount to RNAV % = Target Price (bold).

Discount-to-RNAV % must be EXPLICITLY justified vs historical peer discounts
(copper/gold developers and Indonesian miners); if no comparable basis exists,
label it pure judgment — never present an unjustified discount as a final number.

Sensitivity: Discount-to-RNAV % x discount rate (or x commodity price deck:
copper US$/t / gold US$/oz steps). State which driver moves RNAV most.

### Exhibit — EV/EBITDA Mid-Cycle Cross-Check (part of Slide 4 peer leg)

- Base: MID-CYCLE EBITDA = 3Y average with all 3 constituent years cited
  (e.g. 2023A/2024A/2025E — actual years to be filled by the modeler from
  Sectors financials; this spec fixes the rule, not the years).
- Multiple: primary EV/EBITDA MUST cite >= 2 live peer prints
  (ticker + print + url + date) or be published as an explicit assumption WITH a
  ±2x sensitivity leg. Peer set: Indonesian miners + global copper peers.
- Output: implied EV → minus Net Debt (same valuation-date figure as Block 3) →
  implied equity → implied per-share with its OWN upside vs Last Price.
- Labelled cross-check: does NOT move the headline TP unless the anchor is
  invalidated through the gate (then re-gate, never silent-blend).

## 3. Narrative (one integrated block under exhibits)

Mandatory elements, in order:

1. Most-sensitive parameter named (from the sensitivity matrix: WACC vs terminal
   g vs discount-to-RNAV vs copper price — whichever has the widest FV range).
2. Forecast growth/margin linkage: every material FCFF assumption (revenue CAGR,
   EBIT margin, capex intensity) tied to a Slide 2–3 real driver (Batu Hijau
   grade/phase, Elang timeline, realised copper/gold deck, smelter capex/ramp,
   royalties/DMO). No standalone numbers.
3. Gordon-vs-Exit-Multiple gap: if both terminal legs computed and the gap is
   material, flag explicitly as an unresolved assumption with direction
   (which leg is higher and why) — never average.
4. RNAV-vs-DCF reconciliation: one sentence on why the anchor and RNAV agree or
   diverge (timing of Elang cash flows, discount-rate differential, overhead PV,
   discount-to-RNAV). Divergence without explanation = Critic reject.
5. Mid-cycle multiple read: one sentence placing the anchor TP's implied
   EV/EBITDA against the mid-cycle cross-check (premium/discount + fundamental
   justification: grade, cost position, growth).

## 4. Assumption table skeleton (modeler fills values; spec fixes rows+sources)

| # | Parameter | Source / rule | Used in |
|---|---|---|---|
| A1 | Risk-free rate (Rf) | INDOGB 10Y, as-of date | CoE / WACC |
| A2 | Beta | Bloomberg, as-of date | CoE |
| A3 | Equity Risk Premium (ERP) | Damodaran, vintage | CoE |
| A4 | Cost of Equity (CoE) | CAPM computed | WACC, DDM leg (if gated) |
| A5 | Pre-tax CoD (coupon avg) | Outstanding borrowings | WACC |
| A6 | Effective tax rate | Historical effective, years stated | Tax on EBIT, after-tax CoD |
| A7 | D/(D+E), E/(D+E) | Market-value; state selected vs spot-gearing | WACC |
| A8 | WACC | Computed, bold | FCFF discount, sensitivity rows |
| A9 | Terminal g | Capped ≤ long-term GDP growth; state cap | Terminal value, sensitivity cols |
| A10 | Copper/gold price deck | State deck + source (e.g. consensus / futures curve) | Revenue, RNAV sensitivity |
| A11 | Reserve life / horizon T | Batu Hijau remaining life + Elang timeline | Explicit period length, fade |
| A12 | Smelter/expansion capex schedule | news_output roadmap; unknown → haircut + flag | FCFF capex row |
| A13 | Shares outstanding | Sectors company snapshot, date | Per-share legs |
| A14 | Net Debt (Debt, Cash) | Valuation-date balances | EV→equity bridges |
| A15 | Payout ratio + DPS history | Gate inputs; DDM only if payout>0 + history | DDM leg or skip reason |
| A16 | Mid-cycle EBITDA + 3 years | 3 constituent years cited | EV/EBITDA cross-check |
| A17 | Primary multiple + ≥2 peer prints | ticker+print+url+date, or explicit assumption + ±2x leg | EV/EBITDA cross-check |
| A18 | Per-asset discount rates | Batu Hijau vs Elang rates recorded separately | RNAV |
| A19 | Discount to RNAV % + basis | Peer comps or pure-judgment label | RNAV → TP |
| A20 | Blended weights (if blended) | blended_from_gated only; weights sum 1.0 | Final TP (single headline) |

## 5. Data dependencies (Sectors primary; web_search colour only)

| Need | Sectors wrapper → endpoint | Fallback |
|---|---|---|
| Financials (revenue/EBIT/EBITDA/D&A/capex/NWC) | financials annual/quarterly | NONE for numbers — loud STOP on sectors_missing_key |
| Mining financials / production / cost | `mining_company_financials()` → /mining/companies/financials/ | same |
| Shares, cash, debt, MI | `company_report()` / `report_sections()` | same |
| Segments (ops context) | `segments()` (known 404 for some names — billed 1 credit, handle honestly) | qualitative only |
| Peers + prints (multiple provenance) | `peers()` + live price legs (`daily()` / `index_daily()`) | web_search prints with ticker+print+url+date, else explicit-assumption + ±2x leg |
| Smelter/expansion roadmap, royalty/DMO policy | `news()` + `corporate_actions()` (url+date mandatory) | web_search T1 IDX/Kontan T2 Reuters/Bloomberg, url+date mandatory |
| FX (USD legs) | Slide 4 assumption (rate + date stated) | — |

Rules: sectors_missing_key → loud STOP, never synthetic. Empty-result 200 still
bills — cache aggressively.

## 6. Tie-outs

1. FCFF revenue/EBITDA years == Slide 3 model output == Slide 1 Key Financials
   forecast years, cell-for-cell. Any Slide 3 revision re-exports this exhibit.
2. WACC inputs (Rf/Beta/ERP/CoD/tax/weights) identical between WACC exhibit,
   FCFF discount factors, and assumption table.
3. Net Debt figure identical across DCF bridge, RNAV bridge, EV/EBITDA bridge
   (same valuation date).
4. Slide 1 price box TP == Slide 4 final headline TP to the rupiah; upside
   recomputed (TP/Last − 1) x 100 with sign.
5. Exhibit order: FCFF table emitted before WACC table before sensitivity matrix
   before RNAV bridge before mid-cycle cross-check; renderer numbers
   sequentially — no literal numbers anywhere in payloads.
6. SOTP sign guard: no negative-value asset silently netted; any negative leg
   disclosed with reason.

## 7. Gate checklist (gates.evaluate() FIRST — restated as checks)

- [ ] `gates.evaluate()` run FIRST; `method_gate` ordered list authoritative.
- [ ] `run_method_gate()` called upfront with full inputs (ticker, payout_ratio,
      dps_history_years, ebitda, revenue, net_income, earnings_stable,
      has_peers, segments_count, fcf_available); ordered/skipped emitted inside
      valuation.json.
- [ ] Writer/blended uses ONLY gated FVs (`blended_from_gated`); weights keys ==
      FV keys, weights sum 1.0.
- [ ] DDM leg present ONLY if gated (payout > 0 + DPS history); else skip reason
      recorded, no DDM FV emitted.
- [ ] Primary EV/EBITDA multiple: ≥2 live peer prints (ticker+print+url+date) OR
      explicit assumption + ±2x sensitivity leg.
- [ ] Mid-cycle EBITDA: 3 constituent years cited; never TTM/peak alone.
- [ ] DDM payout ≤ 100% every year tested vs 3Y NORMALIZED EPS (not forward EPS);
      D0→D1 timing lock observed.
- [ ] WACC sensitivity disclosure: modeler-selected weight_equity → DCF range
      under BOTH selected and spot-gearing weights.
- [ ] Single-TP framing: exactly ONE headline TP = anchor; RNAV and multiple
      legs labelled cross-checks with own upsides.

## 8. Critic checks (gate before ship)

- [ ] Zero literal "Exhibit N" strings; zero `id` fields on exhibits.
- [ ] Every exhibit: descriptive label above + exactly
      `Source: Company, Team Estimates` below.
- [ ] No renderer-owned furniture (header/footer/logo/page number/date block).
- [ ] No perpetual Gordon growth on unfaded peak cash flow for AMMN.
- [ ] Expansion capex deducted or haircut+flag present; no smooth growth through
      a known expansion cycle.
- [ ] Tax on EBIT uses effective rate; DDM/GGM legs use CoE not WACC.
- [ ] Gordon-vs-Exit-Multiple gap flagged if material, never silently averaged.
- [ ] Discount-to-RNAV justified vs peers or labelled pure judgment.
- [ ] No synthetic numbers; sectors_missing_key → loud STOP recorded.
- [ ] Provenance (outlet, url, date) retained as internal audit field per object.
