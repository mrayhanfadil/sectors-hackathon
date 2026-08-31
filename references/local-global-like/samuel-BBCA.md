# Samuel Sekuritas — BBCA (Buyback + 3Q25 Results) Dissection
> **Global-like proxy for: single-stock bank note inside a Daily pack (closest to RATU single-pilar template)**

| Field | Value |
|---|---|
| **Broker** | Samuel Sekuritas Indonesia (SSI) |
| **URL** | https://samuel.co.id/wp-content/uploads/2025/10/RSH-251021-English.pdf |
| **Filename** | RSH-251021-English.pdf |
| **Date** | 21 Oct 2025 (Equity Research — DAILY) |
| **Pages** | 8 |
| **Size** | 598 KB |
| **Type** | Daily Research (4 company notes + market snapshot) |
| **Hero ticker** | **BBCA** (2 notes: Buyback p3 + 3Q25 Results p3) — also ASSA, LPKR |
| **Rating / TP** | **BBCA BUY, TP IDR 9,600** (+21.9% upside from 7,875). SSI TP vs Cons 10,748. |
| **Valuation method** | **Implied multiples (P/E 18.3/16.9x, P/BV 3.7/3.3x, ROE 20.0/19.7%) — no explicit DCF/Gordon shown in Daily**. TP derived from GGM/PBV-RoE framework disclosed in full BBCA initiation (cross-ref: BRIDS-style GGM at 4.4× P/BV). Daily cites only the output. Replication: treat as **Gordon Growth / residual-income-implied P/BV** — same as Maybank/Samuel bank coverage. |

---

## 1. Cover

- **Header:** `www.samuel.co.id` + `Equity Research │ 21 October 2025` + `DAILY` + `Daily Research — JCI is Expected to Move Up Today`
- **Topline bullets (4):** `BBCA: IDR 5T Buyback` / `BBCA: 3Q25 Results` / `ASSA: 3Q25 Results` / `LPKR: Acquisition of PT Karya Sentra Sejahtera`
- **Market Snapshot box (p1):** JCI 8,089.0 +173.3 (+2.19%), Volume 31,719 Mn shrs, Value 21,267 Bn IDR; Leading movers BBCA 7,875 (+5.0%), BBRI 3,680 (+5.1%), BMRI 4,300 (+6.2%), AMMN lagging; Foreign Net Buy (Regular) BBCA IDR 894bn / ASII 73bn / TLKM 56bn vs Net Sell BMRI 240bn / ANTM 149bn / PSAB 113bn
- **Macro preamble:** US close (Dow +1.12%, S&P +1.07%, 10Y 3.985%, DXY 98.59), commodities (WTI 57.54, Brent 61.29, coal 104, CPO 4,514, gold 4,359), Asia (Nikkei +3.37%, HS +2.42%, JCI +2.19%, net foreign buy 529.8bn)
- **Footer:** Kospi +1.47%, Nikkei +0.97% open → "We expect JCI to move upward today"

**DNA vs RATU/CDIA/MTEL:** No single-ticker cover — this is a **Daily pack** (4-in-1). RATU/CDIA/MTEL each have a dedicated cover with MCap/Shares/Float/ESG/Takeaways. Samuel Daily has a **universe snapshot cover** instead. Closest analog is MTEL's cover with Key Takeaways + shareholder pie — Samuel Daily replaces it with a **market breadth + flows cover**.

## 2. Summary

- **BBCA Buyback (p3):** max IDR 5T, period 22 Oct 2025–19 Jan 2026 (early termination possible), purpose "price stabilization", management: no material impact on performance/operations. Source: Company.
- **BBCA 3Q25 (p3):** net profit IDR 14.4tn (-3.3% QoQ, +1.3% YoY), **74.9% SSI / 75.1% consensus of FY25** → in line. NII IDR 21.4tn (-0.2% QoQ) + non-interest income +9.6% QoQ. Loan +7.6% YoY (corporate +10.4% YoY — investment + working capital). Deposits +7.0% YoY, **CASA +9.1% YoY, CASA ratio 83.8%**. Credit cost 0.6% (vs 0.5% 2Q25) — buffer build on consumer/auto softness. Rating reaffirmed **BUY TP 9,600**.
- **ASSA 3Q25 (p4):** revenue IDR 1.6tn (+8.9% QoQ, +24.0% YoY), 9M25 IDR 4.4tn (+21.2% YoY) — SSI 75.3%, Cons 82.1% (SSI in line, above cons run-rate). Segments: Delivery & Logistics 712bn (+15.6% QoQ, +153.5% YoY), Lease & Autopool 504bn (+3.5% YoY), Used vehicles 284bn (+25.6% YoY), Auction 70bn (-2.9% YoY). COGS -4.7% QoQ → gross margin 33.2% (vs 31.3% 2Q25). Net profit 143bn (+38.5% QoQ, +70.2% YoY), 9M25 349bn (+63.9% YoY) — **SSI 97.4% / Cons 94.0% → well above**. BUY TP 1,200 (+32%).
- **LPKR (p4):** acquires 100% PT Karya Sentra Sejahtera via AJS+TME from Lovage/IAHCC (Singapore), PPJB 17 Oct 2025, value IDR 332.2bn (pre-adjustment), no material impact. Source: IDX Channel.

## 3. Thesis

**BBCA — resilience thesis in tight liquidity:**
1. **NII stability despite rate pressure** — flat QoQ NII with NIM held via CASA dominance (83.8%, +9.1% YoY vs loan +7.6% — funding advantage).
2. **Corporate-led loan growth** (+10.4% YoY) offsets consumer softness — quality mix, not just volume.
3. **Asset quality buffer** — CoC 0.6% uptick is proactive provisioning, not NPL spike; consumer/auto flagged as watch, but overall book still strong.
4. **Capital return signal** — 5T buyback = confidence + price floor, declared immaterial to operations → shareholder-friendly without balance-sheet stress.
5. **Valuation anchor** — 21.9% upside at 16.9× FY25E P/E, 3.3× P/BV, 19.7% ROE → premium justified by 83.8% CASA and lowest CoC among big banks.

**ASSA — logistics as growth engine:** Delivery & Logistics +153.5% YoY is the alpha; margin expansion from COGS discipline; 9M already at ~97% FY — implies FY25 beat if 4Q holds.

**Implication for our template:** Bank thesis = **CASA ratio + CoC + loan mix + NIM trajectory** — directly maps to RATU's BOPD and MTEL's tenancy ratio as sector KPIs. We need a **bank KPI module** (CASA, LDR, NIM, CoC, coverage).

## 4. Valuation Method (forensic)

- **Daily does NOT print DCF/WACC/g table** — only the **output table (p5–6)** with `TP SSI / TP Cons / Upside / P/E 24A-25E / P/BV 24A-25E / ROE 24A-25E` for ~40 stocks across sectors (Banks, Consumer, Healthcare, Poultry, Retail, Media, Telco, Telco Infra, Auto, Mining Contracting, Property, Industrial Estate, Oil & Gas, Metal).
- **BBCA line:** Last 7,875 | TP SSI 9,600 | Cons 10,748 | Upside 21.9% | P/E 18.3→16.9 | P/BV 3.7→3.3 | ROE 20.0→19.7 | JCI weight 9.1%.
- **Method inferred:** SSI bank coverage historically uses **Gordon Growth Model (GGM) / Residual Income implied P/BV = (ROE – g)/(CoE – g)**, with CoE from CAPM (Rf ~6.9%, beta ~0.7–0.9, ERP ~5–6%). The Daily's P/BV + ROE disclosure is the GGM fingerprint. No explicit WACC/CoE/g printed here — must pull from SSI's full BBCA initiation (same pattern as BRIDS GGM 4.4× FY23 P/BV for BBCA).
- **Blended vs single:** No blended weight — single TP only (like RATU side-by-side, not MTEL 60/40).
- **Replicability:** For our engine → `calc_ggm(roe, coe, g) → implied P/BV → TP = BVPS × P/BV`. If g/CoE not in Daily, fallback to `calc_ev_ebitda` or `calc_per_multiple` using the peer table.

## 5. Exhibits (inventory)

| # | Exhibit | Page | Content | Source cited |
|---|---|---|---|---|
| 1 | Market Activity table | p1 | Index move, volume, value, leading/lagging movers, foreign net buy/sell | SSI / IDX |
| 2 | Commodities — 6 sparklines | p2 | Gold (3,400→4,359), Brent (60→61), Newcastle Coal (104), CPO (4,200→4,514), Pulp (CNY), Nickel (15k) — 12M trend | Bloomberg (implied) |
| 3 | World Indices / Rates / FX table | p7 | 16 indices 1D/1W/1M/3M/YTD/1Y + High/Low; Foreign reserves, inflation, gov bond 10Y, Fed rate; 6 FX pairs | Bloomberg / BI / Fed |
| 4 | **Recommendation & Valuation table (THE exhibit)** | p5–6 | ~40 tickers × Rec / JCI Wgt / Last / TP SSI / TP Cons / Upside / P/E 24A-25E / P/BV 24A-25E / ROE 24A-25E — sector-grouped | **SSI Research, Bloomberg, Company** |
| 5 | Global markets preamble | p1 | US/Asia close + futures (Kospi/Nikkei open) | Bloomberg |
| 6 | Company notes (narrative) | p3–4 | BBCA buyback, BBCA 3Q25 KPIs, ASSA segment split, LPKR deal terms | **Company, IDX Channel** |

**Count:** 6 exhibit groups (1 is the hero valuation table spanning 2 pages). No DCF bridge, no historical P/E bands, no SOTP breakdown — lighter than archetypes, because Daily is a **snapshot**, not an initiation.

## 6. Financials

- **No 5Y P&L/BS/CF in this Daily** — only **3Q25 KPI snapshot + FY multiples** from the rec table. Must pull full financials from SSI's BBCA model (not printed here).
- **What IS disclosed (BBCA 3Q25):** Net profit 14.4tn (74.9% FY25), NII 21.4tn, Loan +7.6% YoY (corp +10.4%), Deposits +7.0% YoY, CASA +9.1% YoY → 83.8%, CoC 0.6%. **Quarterly, not TTM/annualized.**
- **Peers:** Valuation table IS the peer comp — big banks side-by-side: BBCA (P/E 16.9, P/BV 3.3, ROE 19.7) vs BBRI (7.1×, 1.6×, 22.9%) vs BMRI (6.3×, 1.3×, 20.3%) vs BBNI (5.7×, 0.9×, 14.9%). Implies SSI's bank universe is the comp set.
- **For our template:** Daily is **insufficient as a financial source** — need to join with `financials?sections=income,balance,cashflow` 5Y. Keep Daily only for thesis/KPI/TP.

## 7. Source per Exhibit (provenance — mandatory for template)

| Exhibit | Source printed | Verbatim |
|---|---|---|
| BBCA buyback terms | Company | "(Company)" |
| BBCA 3Q25 KPIs | Company | "(Company)" |
| ASSA 3Q25 segment split | Company | "(Company)" (SSI 75.3%/97.4% vs Cons 82.1%/94.0% shown) |
| LPKR acquisition | IDX Channel | "(IDX Channel)" |
| Market activity / indices / FX / reserves | Bloomberg / BI / Fed | Implied from p7 header "Source: Bloomberg" style (not footnoted per table but standard SSI footer) |
| Recommendation table | SSI Research + Bloomberg + Company | Footer p5–6: "Source: SSI Research" + Bloomberg prices |
| Commodities sparklines | Bloomberg | Y-axis labels "Gold 100 Oz Futures", "Brent Generic 1st", "Newcastle Coal" — Bloomberg naming |
| Disclaimer | SSI | 8-line disclaimer p8 + analyst certification (Harry Su, Prasetya Gunadi, Fithra Hastiadi…) |

## 8. Global-likeness Score

| DNA element | Present? | Note |
|---|---|---|
| Cover + snapshot | ✅ | Market + flows, not single-ticker — Daily format |
| Summary 3Y snapshot | ⚠️ | Only 3Q snapshot + FY multiples, not 3Y FY24A→26F |
| Thesis narasi + angka | ✅ | BBCA: 4 angka (CASA 83.8%, CoC 0.6%, loan 7.6%, buyback 5T) |
| Valuation method explicit | ❌ | TP only, no WACC/beta/g — **biggest gap** vs MTEL/RATU |
| Exhibits + source | ✅ | 6 groups, source per note (Company/IDX/Bloomberg) |
| Financials 5Y + ratios | ❌ | Not in Daily — need separate initiation |
| Risks | ❌ | No risk bucket in Daily (vs 4–7 buckets in archetypes) |
| Peer comps | ✅ | Universe table = 1-table peer comp (like RATU) |
| Segment breakdown | ✅ (ASSA) | Only for ASSA, not BBCA |
| KPI module | ✅ | CASA/CoC/NIM/LDR — bank KPIs |
| Disclaimer OJK | ✅ | Full disclaimer + analyst cert p8 |

**Verdict:** **5.5/10 global-like** — excellent as a **flow + KPI + TP snapshot**, but **not a standalone initiation**. Use as **BBCA control ticker** for P1 data layer (prices/segments/KPI/JCI), and as a **negative example** of what a Daily lacks vs a true 11-page RATU/1656-line CDIA/302-line MTEL. The valuation table (p5–6) is the **most replicable artifact**: a single `recommendation.csv`-style table with TP/PE/PBV/ROE that our `peers.json` must mimic.

## 9. Replicable Patterns for Our Template

1. **Recommendation table (p5–6) = `peers.json` single-mode** — columns: `ticker, rec, jci_wgt, last, tp_ssi, tp_cons, upside, pe_24a, pe_25e, pbv_24a, pbv_25e, roe_24a, roe_25e`. Directly feed our Visualizer peer multiples chart.
2. **Foreign flow box (p1)** → add `foreign_flow` widget (Net Buy/Sell IDR bn by ticker) to cover — none of RATU/CDIA/MTEL have this; Samuel's is unique and retail-friendly.
3. **Commodity sparklines (p2)** → reuse as `Industry/Macro` section backdrop — 6 small multiples with 12M trend (gold, oil, coal, CPO, pulp, nickel).
4. **Bank KPI trio (CASA, CoC, LDR/NIM)** → add to `operational_kpis` per subsector `banking` — tenancy ratio for towers, BOPD for oil, CASA for banks.
5. **Gap to fix:** If we clone Samuel Daily as BBCA control, **inject a GGM box** (ROE, CoE, g, implied P/BV, TP bridge) — Daily omits it but our template must not.
