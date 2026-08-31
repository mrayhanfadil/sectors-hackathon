# Plan: Institutional-Grade Equity Report for Retail — Multi-Agent System

> **Branch:** `feat/institutional-report` | **Status:** DRAFT — nunggu ide tambahan Fadiil + temen  
> **Locked idea:** Bikin equity research report kualitas institusi (kayak HP Sekuritas RATU 7 Jan 2026) tapi accessible buat retail investor. Multi-agent, tiap agent punya expertise.  
> **Benchmark PDFs:** `lre-ratu-en-hp-260107.pdf` (RATU, HP Sekuritas, 7 Jan 2026, pure-play Oil & Gas) + `lre-cdia-en-sq-260701.pdf` (CDIA, BCA Sekuritas, 23 Jun 2026, conglomerate 4-pilar). Dua archetype: single-asset vs diversified holding.  
> **Deadline hackathon:** 30 Sep 2026 23:59 WIB (build closes) — 29 hari lagi.

---

## 1. Why This Wins

**Problem:** Retail di IDX dapet info cuma dari headline / influencer, bukan report institutional yang ada DCF, peer comps, risk, dan asumsi eksplisit. Sekuritas ngasih report tapi tebal, bahasa berat, dan nggak personalized.

**Judges fit:** Real-world usability 40% — semua retail butuh. Video storytelling 30% — “before: bingung baca laporan, after: 1 PDF jelas + angka traceable” itu cinematic. Technical depth 30% — multi-agent + deterministic math (bukan LLM ngarang angka) = defensible.

**Pivot dari Sektoral.id:** Dulu 31 demo showcase, sekarang deep 1 product tapi kualitas institusi. Kredibel.

## 2. Benchmark — Apa yang Bikin Report Institutional (RATU vs CDIA)

### 2.1 RATU (HP Sekuritas, 7 Jan 2026) — Pure-Play Holding, 11 halaman, 819KB

| Section PDF | Isi | Replicate |
|---|---|---|
| **Cover** | Ticker RATU, IPO 1,150 → Current 10,650, Shares 2.71B, Free Float 31.2%, Tag MSCI/IDX80/JII | Cover generator (Sectors metadata) |
| **Summary** | 3-yr snapshot: FY24A 129x P/E / 65x P/BV → FY26F 42.7x / 22x + revenue/EBITDA/net profit | Summary table deterministic |
| **Main Thesis** | 4 narasi + angka: Bottom line +28% YoY meski revenue -13%, Madura Gas, Cepu 169k BOPD, Jabung decline | Thesis Writer |
| **Risk** | 4 bucket: Commodity, Operator dependence, Regulatory (PSC/DMO), Natural decline | Risk Officer |
| **Valuation** | DCF WACC 8.4%, beta 0.7, ERP 6.9%, CoE 10%, CoD 3.5%, g 5% → IDR 7,880 + EV/EBITDA 22.6x → IDR 6,960 | Financial Modeler (Python) |
| **Overview** | History 2006→2023, IPO proceeds 88% ke RETJ/PJUC, BOD 6 orang, PSC→Extraction→Lifting→Revenue | Company Analyst |
| **Industry Outlook** | Brent $55-65, IEA +0.7%, Gas +2%, downstream $40B | Industry/Macro |
| **Exhibits 1-15** | Semua klaim + source (HP Analytics, Bloomberg, SKK Migas, BPS, FactSet) | Visualizer + provenance |
| **Financials** | P&L, CF, BS, Key Ratios 5Y (2023A-2027F), ROE 88%→30%, DER, Interest Coverage | Data Collector + Modeler |

### 2.2 CDIA (BCA Sekuritas, 23 Jun 2026) — Conglomerate 4-Pilar, 1656 lines, 1.58MB — Company Update (1Q26)

**Struktur beda, tapi lebih kaya — ini yang bikin institutional grade untuk holding:**

| Section CDIA | Isi Kunci | Delta vs RATU |
|---|---|---|
| **Cover + Stock Perf** | Price 620, Range 575-2450, Shares 124.8B, MCap 77.3T/5.4B USD, Holders Chandra Asri 60% + EGCO 30% + chart price vs JCI + tabel Absolute/Relative YTD/1M/3M/12M (-62.9% YTD, -30.9% rel) | **Baru:** relative performance vs benchmark (IHSG/JCI) — RATU cuma price |
| **1Q Headline** | "Time to catch up", revenue 41mn +19% YoY, Energy 55% (23mn +7.7%), Logistics +44.7% fastest (14mn, 34%), 9 vessels +6 guidance, GPM 24.4% vs 26.6%, EBIT 11.6% vs 15.3%, Net 8.4mn -72% (normalisasi dari one-off 15.9mn gain) | **Baru:** segment growth mix + one-off normalization narrative |
| **Valuation** | **DCF → 815 + DDM → 810** (40% payout 27-28, 104% avg 28F onwards). DCF table: CFO/CAPEX/Net Borrowing/FCFE/Discount Factor/Discounted FCFE. DDM table: Dividend/Discount Factor/Discounted | **Beda metode:** RATU = DCF + EV/EBITDA multiples. CDIA = DCF + DDM (karena infra/dividend story). → Kita butuh **adaptive 2nd method** |
| **Financial Summary 5Y** | Revenue 102→523, EBITDA margin 10.6%→40%, ROE 4.2%→4.6%, Gearing 44%→147%, Debt/EBITDA 27x→8x, Current ratio, Interest coverage | Lebih fokus leverage (Gearing, Net Gearing, Debt/EBITDA) — RATU fokus ROE/ROIC |
| **Exhibit 1-2** | 1Q vs 4Q vs YoY detail (Revenue, COGS, GPM, EBITM, Pretax, NPM, BS, ROA, Gearing) + Revenue breakdown by segment (Electricity 55%, Fuel 6%, Time charter 34%, Tank 3%) | **Segment breakdown %** — wajib untuk conglomerate |
| **Exhibit 3-4** | DCF & DDM full calculation | Transparency FCF → equity value |
| **Exhibit 5-8** | **4 peer tables terpisah per pilar:** Energy (POWR, Tokyo Electric etc, avg Asia/China/Europe/US/Global), Water (Sembcorp, ION etc), Port & Storage (PORT, IPCC, Westports etc), Logistics (HATM, BULL, TMAS, SMDR etc) — tiap ada P/E, EV/EBITDA, P/B, ROE, DivYield | **SOTP approach** — RATU cuma 1 peer table 22 comps. CDIA = **Sum-of-the-Parts** |
| **Forecast revision** | Revisi FY26 revenue -37.4%, EBITDA -52.1%, Net -75.8% dengan alasan: M&A delay ke 2H26, fuel cost naik, working capital heavier | **Baru:** track record revision vs prior — bikin credible |
| **Company Overview 4-pilar** | Energy: KCE 120MW CCPP, 150kV, solar 2.2MWp; Water: KTI 1996, 2,000 l/s, 3 WTP demin, 3 WWTP, reservoir Krenceng 3.4mn m³; Port: RPU 2 berths 35k DWT + 72 tanks 130k m³; Logistics: CSI+MIM 7 vessels 5k-8600 DWT, TC/COA/spot, 60% internal → target 60% external, 8 vessels pipeline | **Operational depth** — RATU cuma PSC, CDIA spek teknis tiap pilar |
| **Key Risks 7 buckets** | Global uncertainties, FX, Customer dependency, Energy (regulatory/operational/vendor/gas supply), Logistics (weather/maritime/fleet), Port (sedimentation/capacity), Water (climate/infra) | RATU 4 buckets generik, CDIA **pillar-specific** |
| **Milestones + BOD/BOC** | Timeline mergers 2023, EGCO 30%, Cilegon 2,666ha hub, Board Commissioner & Director terpisah | Sama, tapi lebih visual |

### 2.3 Yang Kita Serap ke Produk — Upgrade List

> **Kunci institutional = bukan bahasa indah, tapi:** angka traceable, asumsi eksplisit, 2 metode valuasi, peer comps, risiko jujur, source di tiap exhibit. CDIA nambah: **SOTP + relative perf + forecast revision + segment mix**.

**Wajib masuk (P0/P1):**
1. **Adaptive Valuation Engine:** DCF selalu + 2nd method otomatis: `if dividend_yield>0 & infra → DDM`, `if conglomerate → SOTP + multiples`, `else → EV/EBITDA`. RATU & CDIA jadi test case.
2. **Segment Breakdown:** Collector ambil revenue per segmen kalau ada (Sectors API `segments` field). Kalau single-pilar kayak RATU → hide, kalau CDIA → tampilkan mix % + Exhibit 2 style.
3. **Stock Performance vs Benchmark:** Modul `vs JCI` — tabel Absolute/Relative YTD/1M/3M/12M + chart. Data dari `prices` + JCI benchmark (Sectors atau synthetic).
4. **Forecast Revision Block:** Kalau ada prior forecast (kita simpan `assumptions_v1.json`), tampilkan delta % kayak CDIA Exhibit 9 ("Revenue -37.4%"). Kalau initiation report (no prior) → skip.
5. **Leverage Metrics:** Tambah Gearing, Net Gearing, Debt/EBITDA, Interest Coverage di Key Ratios — penting buat infra kayak CDIA (gearing 170%).
6. **Source di tiap exhibit:** Wajib, kayak kedua PDF.

**Nice-to-have (P3/P4):**
7. One-off normalization narrative (CDIA: net -72% karena 1Q25 gain 15.9mn) — Thesis Writer perlu flag "adjusted vs reported".
8. Operational specs box per pilar (MW, m³, DWT, l/s) — Company Analyst pakai template per sektor.

## 3. Architecture — 7+1 Agents (upgraded)

```
[User input: ticker e.g. RATU / CDIA] 
        ↓
  ┌─ Data Collector (parallel, Sectors API v2) ─┐
  │  • company/overview, financials (5Y), prices  │
  │  • segments (kalau conglomerate)              │
  │  • peers PER PILAR (SOTP) atau universe       │
  │  • benchmark JCI untuk relative perf          │
  │  • simpan ke JSON (source of truth)           │
  └───────────────────┬───────────────────────────┘
                      ↓ (blocking)
          ┌─ Financial Modeler (THE BRAIN) ─┐
          │  Python deterministic:           │
          │  wacc(), dcf(), ddm(),          │
          │  ev_ebitda(), sotp(),           │
          │  ratios() incl. gearing/debt/ebitda │
          │  Output: assumptions.json +     │
          │  valuation.json (dcf+adaptive)  │
          │  + segment_mix.json             │
          └───────────┬─────────────────────┘
                      ↓ (parallel)
  ┌─────────────────────────────────────────────────┐
  │ Company Analyst │ Industry/Macro │ Risk Officer │
  │ (bisnis model,  │ (Brent/IEA/    │ (pillar-     │
  │  operasional    │  SKK Migas +   │  specific    │
  │  specs per pilar│  sektor)       │  4-7 buckets)│
  └────────┬────────┴───────┬────────┴──────┬───────┘
           └────────────────┼───────────────┘
                            ↓
                   Thesis Writer (bull case + segment growth + one-off adj)
                            ↓
                   Visualizer (PNG: Revenue mix, Margin, Leverage, ROE, vs JCI)
                            ↓
                   SOTP Aggregator (khusus conglomerate — sum peer avg per pilar)
                            ↓
                   Orchestrator + QA Critic
                   • cek tiap angka di narasi == tabel?
                   • DDM dividend math cek?
                   • SOTP sum == total?
                   • source ada di tiap exhibit?
                   → REJECT jika mismatch
                            ↓
                   PDF Renderer (HTML → PDF, template switch: single-pilar vs SOTP)
```

**Anti-halusinasi rule (wajib di system prompt tiap agent):**
- `JANGAN hitung. Panggil tool calc_dcf() / calc_ddm() / calc_sotp().`
- LLM cuma jelaskan, bukan ngitung. Math = Python.
- Critic nge-grep: kalau thesis tulis “P/E 42.7x” tapi valuation.json bilang 52.7x → auto-reject.
- Segment mix % harus sum 100% — Critic validasi.

## 4. Data Layer

**Sectors API v2 (hemat credit):**
- `GET /v2/equity/{ticker}/overview` — profile, IPO, shares, free float, holders (CDIA: Chandra Asri 60%)
- `GET /v2/equity/{ticker}/financials?sections=income,balance,cashflow` — 5Y + segments kalau ada
- `GET /v2/equity/{ticker}/prices?range=5y` — buat chart + relative vs JCI
- `GET /v2/universe/peers?subsector=banks` — single-pilar. Untuk SOTP: loop 4 subsector (1 credit each, total 4) — tetap hemat vs 22 loop
- `GET /v2/index/JCI/prices` — benchmark buat relative perf (atau synthetic JCI)
- `GET /v2/commodities/*` + Mining extension kalau energy ticker

**Synthetic fallback (kaya Sektoral.id):**
- SQLite `data/sectors.db` seed=42, 49 tickers + JCI synthetic, biar demo tanpa burn credit.
- Tambah `segments` synthetic untuk CDIA archetype (Energy 55%, Logistics 34%, dll).

**Peers master:** `data/peers.json` — dua mode: `single` (RATU: 22 comps) + `sotp` (CDIA: 4 pilar × masing-masing peers). Mapping subsector → peers per pilar.

**Assumptions store:** `data/assumptions/{ticker}.json` — WACC, beta, ERP, g, CoD, payout ratio (buat DDM), prior forecast (buat revision). Versioned & auditable (ditampilin di PDF kayak RATU Exhibit 7 + CDIA Exhibit 3-4).

## 5. Output — PDF yang Mirip HP/BCA Sekuritas (Adaptive Template)

- **Engine:** HTML → PDF (Playwright/puppeteer atau LaTeX) biar pixel-perfect, bukan markdown.
- **Layout:** Header “RESEARCH” + tanggal, footer disclaimer OJK, page number, source di bawah tiap exhibit.
- **Template switch:**
  - `single-pilar` (RATU): 9 sections, 1 peer table, Valuation = DCF + Multiples
  - `conglomerate/SOTP` (CDIA): 10 sections (+ Segment Breakdown + SOTP), 4 peer tables, Valuation = DCF + DDM, + Forecast Revision block
  - Logic: `if segments.length >1 → SOTP template, else → single`
- **Adaptive sections:**
  - Cover + Stock Perf vs JCI (baru dari CDIA)
  - Summary (3-yr snapshot)
  - Main Thesis (segment growth highlights)
  - Risk (4-7 buckets, pillar-specific kalau SOTP)
  - Valuation (DCF + adaptive 2nd)
  - Overview (ops specs per pilar — MW/DWT/m³)
  - Industry Outlook (per pilar kalau SOTP)
  - Exhibits + Financials
  - Forecast Revision (kalau ada prior)
- **Charts:** 7 exhibits wajib: Revenue mix (pie/bar per segmen), Revenue/EBITDA trend, Margin (GPM/EBITM/NPM), Leverage (Gearing/Debt-EBITDA), ROE/ROA, vs JCI, Peer multiples (per pilar).
- **Bahasa:** ID + EN toggle (kayak disclaimer-template.md).

## 6. Tech Stack (lean, proven)

- **Frontend:** Next.js (kayak Sektoral.id) — 1 page `/report/[ticker]` + PDF preview + download + template switch preview
- **Backend:** Python FastAPI — agent orchestrator + Sectors proxy (cache 4h kayak KV di BankPromo)
- **DB:** SQLite (sintesis) / KV cache (prod)
- **PDF:** HTML template + Tailwind + Chart.js → PDF (2 templates)
- **Deploy:** Cloudflare Pages (`*.pages.dev` — Fadiil prefer ini over workers.dev)
- **Repo structure:**
  ```
  sectors-hackathon/
  ├── plan.md (this file)
  ├── data/peers.json (single + sotp), assumptions/
  ├── scripts/sectors_api.py, dcf_engine.py, ddm_engine.py, sotp_engine.py
  ├── agents/{collector,modeler,analyst,industry,risk,writer,visualizer,critic, sotp_aggregator}.py
  ├── templates/report_single.html (RATU clone)
  ├── templates/report_sotp.html (CDIA clone)
  ├── app/ (Next.js)
  └── demos/report/assets/api-data.js (synthetic + segments)
  ```

## 7. Phased Build (29 hari ke 30 Sep)

| Phase | Tanggal | Deliverable | Owner |
|---|---|---|---|
| **P0 — Scaffold** | 31 Aug – 2 Sep | Branch + plan.md (ini, RATU+CDIA) + `dcf_engine.py` + `ddm_engine.py` + `sotp_engine.py` + `peers.json` (single+SOTP) + 2 HTML templates | Hermes |
| **P1 — Data** | 3 – 6 Sep | Sectors API proxy + SQLite synthesis (segments + JCI) + 3 tickers E2E (RATU single, CDIA SOTP, BBCA single) | Collector |
| **P2 — Modeler** | 7 – 10 Sep | DCF+DDM+SOTP deterministic, RATU (7,880 & 6,960) + CDIA (815 & 810) reproducible | Modeler |
| **P3 — Agents** | 11 – 18 Sep | 5 LLM agents + SOTP Aggregator + Visualizer (mix pie, leverage, vs JCI) | Multi-agent |
| **P4 — PDF + UI** | 19 – 23 Sep | PDF renderer 2 templates + `/report/[ticker]` + forecast revision block | Frontend |
| **P5 — Polish & Video** | 24 – 29 Sep | 3 tickers showcase (1 pure + 1 SOTP + 1 bank), video storytelling, audit swarm (3 AGY) | All |
| **Submit** | 30 Sep 23:59 WIB | Commit freeze, public repo 90 hari | — |

## 8. Credit Budget (1,000 credits)

- Universe peers (1 credit) >> loop 22 tickers (22 credits) — hemat 95%. SOTP: 4 pilar × 1 = 4 credits (vs 22×4=88 loop)
- `sections=` param tiap financials call — potong 50%
- Cache 4h + synthetic fallback — demo nggak burn credit live
- Estimasi: 3 tickers showcase (RATU, CDIA, BBCA) × ~10 credits (segments+JCI extra) = 30 credits total (aman).

## 9. Risks & Mitigations

| Risk | Mitigasi |
|---|---|
| LLM halusinasi P/E 129x | Critic grep + Python calc only |
| Exhibit tanpa source | Template wajib `Source:` field, CI cek |
| Valuasi cuma 1 metode | DCF + adaptive 2nd (multiples/DDM/SOTP) — cover RATU & CDIA |
| SOTP sum mismatch | Aggregator + Critic sum check 100% |
| Segment % nggak 100% | Critic validasi mix sum |
| Sectors credit habis | Synthetic DB fallback (segments+JCI synthetic) |
| Track disqualification (T01 “off-the-shelf”) | Custom orchestration + tool pipeline, bukan cuma prompt (trap di rules §06) |

## 10. Decision Log

| Keputusan | Kenapa | Alternatif ditolak |
|---|---|---|
| Deep 1 product (report) bukan 31 demo | Judges 40% usability → retail butuh 1 yang jadi, bukan 31 setengah jadi | Sektoral.id 31 demos (proven tapi shallow) |
| 7+1 agents + SOTP Aggregator (CDIA) | CDIA butuh 4 peer tables + SOTP sum, RATU cuma 1 — architecture harus adaptive | Single peer table (nggak cover conglomerate) |
| Adaptive 2nd valuation (multiples/DDM/SOTP) | RATU pakai EV/EBITDA, CDIA pakai DDM — satu template nggak cukup | Fixed DCF+multiples only |
| Segment breakdown | CDIA 55% Energy / 34% Logistics mix itu insight utama | Aggregate revenue only |
| Stock perf vs JCI | CDIA relative -30.9% YTD itu konteks institutional | Price absolute only |
| Forecast revision block | CDIA -37% revenue revision bikin credible | Hide revision |
| Leverage metrics (Gearing, Debt/EBITDA) | CDIA gearing 170%, Debt/EBITDA 18x — infra story | ROE/ROA only |
| Python deterministic untuk valuasi | Kedua PDF ada WACC/beta/ERP/payout eksplisit — LLM ngarang = fatal | LLM math |
| HTML→PDF 2 templates | Single vs SOTP layout beda | Markdown PDF |
| Pages.dev bukan workers.dev | Fadiil prefer brand-aligned URL (valid 30 Aug) | Tunnel/workers.dev |

## 11. Open — Nunggu Ide Tambahan Fadiil + Temen

> **Slot buat ide lo:** tulis di bawah, gue merge ke plan.

- [ ] Ide 1: (dari Fadiil) — 
- [ ] Ide 2: (dari temen) —
- [ ] Ide 3: —
- Track lock-in: T01 AI Agents vs T03 Market Intelligence? (RATU+CDIA report paling pas T03, tapi multi-agent = T01 — perlu decide. CDIA SOTP complexity condong ke T03 Market Intel juga)
- Ticker awal: RATU (single, benchmark) + CDIA (SOTP, benchmark) + 1 bank (BBCA) — trio ini cover semua template
- Bahasa default PDF: ID / EN / toggle? —
- Prior forecast: simpen v1 buat revision demo atau initiation only? —

---

**Next step:** Fadiil drop ide tambahan → gue update Section 11 + scaffold `dcf_engine.py` + `ddm_engine.py` + `sotp_engine.py` + 2 templates di branch ini. Gas?

