# Plan: Institutional-Grade Equity Report for Retail — Multi-Agent System

> **Branch:** `feat/institutional-report` | **Status:** DRAFT — nunggu ide tambahan Fadiil + temen  
> **Locked idea:** Bikin equity research report kualitas institusi (kayak HP Sekuritas RATU 7 Jan 2026) tapi accessible buat retail investor. Multi-agent, tiap agent punya expertise.  
> **Benchmark PDF:** `lre-ratu-en-hp-260107.pdf` (PT Raharja Energi Cepu Tbk, RATU) — 9 sections, 15+ exhibits, 2 valuasi (DCF + EV/EBITDA), full financials 5Y.  
> **Deadline hackathon:** 30 Sep 2026 23:59 WIB (build closes) — 29 hari lagi.

---

## 1. Why This Wins

**Problem:** Retail di IDX dapet info cuma dari headline / influencer, bukan report institutional yang ada DCF, peer comps, risk, dan asumsi eksplisit. Sekuritas ngasih report tapi tebal, bahasa berat, dan nggak personalized.

**Judges fit:** Real-world usability 40% — semua retail butuh. Video storytelling 30% — “before: bingung baca laporan, after: 1 PDF jelas + angka traceable” itu cinematic. Technical depth 30% — multi-agent + deterministic math (bukan LLM ngarang angka) = defensible.

**Pivot dari Sektoral.id:** Dulu 31 demo showcase, sekarang deep 1 product tapi kualitas institusi. Kredibel.

## 2. Benchmark — Apa yang Bikin RATU Report Keliatan Institutional

Di-bedah dari PDF HP Sekuritas (819KB, 11 halaman):

| Section PDF | Isi | Yang Harus Kita Replicate |
|---|---|---|
| **Cover** | Ticker RATU, IPO 1,150 → Current 10,650, Shares 2.71B, Free Float 31.2%, Tag MSCI/IDX80/JII, Sharia | Cover generator (auto dari Sectors metadata) |
| **Summary** | 3-yr valuation snapshot: FY24A 129x P/E / 65x P/BV → FY26F 42.7x / 22x + revenue/EBITDA/net profit forecast | Summary table (deterministic dari model) |
| **Main Thesis** | 4 narasi + angka: Bottom line +28% YoY meski revenue -13%, Madura Gas acquisition, Cepu peak 169k BOPD, Jabung decline + new subsidiaries | Thesis Writer agent |
| **Investment Risk** | 4 bucket: Commodity, Operator dependence, Regulatory (PSC/DMO), Natural decline | Risk Officer agent |
| **Valuation** | DCF (WACC 8.4%, beta 0.7, ERP 6.9%, CoE 10%, CoD 3.5%, g 5% → IDR 7,880) + EV/EBITDA 22.6x peers → IDR 6,960 | Financial Modeler (Python, BUKAN LLM) |
| **Overview** | History 2006→2023, IPO proceeds 88% ke RETJ/PJUC, BOD 6 orang lengkap, PSC→Extraction→Lifting→Revenue | Company Analyst |
| **Industry Outlook** | Brent $55-65, IEA +0.7% demand, Gas +2%, downstream $40B | Industry/Macro agent |
| **Exhibits 1-15** | Semua klaim ada tabel/chart + source (HP Analytics, Bloomberg, SKK Migas, BPS, FactSet) | Visualizer + provenance |
| **Financials** | P&L, Cash Flow, Balance Sheet, Key Ratios 5Y (2023A-2027F), ROE 88%→30%, DER, Interest Coverage | Data Collector + Modeler |
| **Disclaimer** | OJK, restricted, no offer | Template footer |

**Kunci institutional = bukan bahasa indah, tapi:** angka traceable, asumsi eksplisit, 2 metode valuasi, peer comps 22 perusahaan, risiko jujur, source di tiap exhibit.

## 3. Architecture — 7+1 Agents

```
[User input: ticker e.g. BBCA] 
        ↓
  ┌─ Data Collector (parallel, Sectors API v2) ─┐
  │  • company/overview, financials (5Y), prices  │
  │  • peers, dividends, subsector comps          │
  │  • simpan ke JSON (source of truth)           │
  └───────────────────┬───────────────────────────┘
                      ↓ (blocking)
          ┌─ Financial Modeler (THE BRAIN) ─┐
          │  Python deterministic:           │
          │  wacc(), dcf(), ev_ebitda(),    │
          │  ratios(), forecast()            │
          │  Output: assumptions.json +     │
          │  valuation.json + ratios.json    │
          └───────────┬─────────────────────┘
                      ↓ (parallel)
  ┌─────────────────────────────────────────────────┐
  │ Company Analyst │ Industry/Macro │ Risk Officer │
  │ (bisnis model,  │ (Brent, IEA,   │ (4 bucket    │
  │  PSC, BOD)      │  SKK Migas)    │  bear case)  │
  └────────┬────────┴───────┬────────┴──────┬───────┘
           └────────────────┼───────────────┘
                            ↓
                   Thesis Writer (bull case narrative)
                            ↓
                   Visualizer (PNG charts: Revenue, Margin, ROE/ROA, Assets)
                            ↓
                   Orchestrator + QA Critic
                   • cek tiap angka di narasi == tabel?
                   • source ada di tiap exhibit?
                   • DCF math reproducible?
                   → REJECT jika mismatch
                            ↓
                   PDF Renderer (LaTeX/HTML → PDF, mirip HP Sekuritas layout)
```

**Anti-halusinasi rule (wajib di system prompt tiap agent):**
- `JANGAN hitung. Panggil tool calc_dcf() / calc_multiple().`
- LLM cuma jelaskan, bukan ngitung. Math = Python.
- Critic agent nge-grep angka: kalau thesis tulis “P/E 42.7x” tapi valuation.json bilang 52.7x → auto-reject.

## 4. Data Layer

**Sectors API v2 (hemat credit):**
- `GET /v2/equity/{ticker}/overview` — profile, IPO, shares, free float
- `GET /v2/equity/{ticker}/financials?sections=income,balance,cashflow` — 5Y
- `GET /v2/equity/{ticker}/prices?range=5y` — buat chart + valuation anchor
- `GET /v2/universe/peers?subsector=banks` — prefer universe feed (1 credit) daripada loop per-ticker (N credit)
- `GET /v2/commodities/*` + Mining extension kalau energy ticker

**Synthetic fallback (kaya Sektoral.id):**
- SQLite `data/sectors.db` seed=42, 49 tickers, biar demo tanpa burn credit. Pattern udah proven di `sectors-idea-lab`.

**Peers master:** `data/peers.json` — list 22 comps kayak RATU (MEDC, ENRG, AKRA, INPEX, Harbour, CNOOC, PTTEP, dll) + mapping subsector → peers.

**Assumptions store:** `data/assumptions/{ticker}.json` — WACC, beta, ERP, g, CoD — versioned & auditable (ditampilin di PDF kayak RATU Exhibit 7).

## 5. Output — PDF yang Mirip HP Sekuritas

- **Engine:** HTML → PDF (Playwright/puppeteer atau LaTeX) biar pixel-perfect, bukan markdown.
- **Layout:** Header “RESEARCH” + tanggal, footer disclaimer OJK, page number, source di bawah tiap exhibit.
- **9 sections** persis urutan RATU (Cover → Summary → Thesis → Risk → Valuation → Overview → Industry → Exhibits → Financials).
- **Charts:** 6 exhibits wajib (Revenue, Gross/EBITDA/Net Margin, Assets, ROE/ROA/ROIC, Brent/WTI, Peer multiples).
- **Bahasa:** ID + EN toggle (kayak disclaimer-template.md).

## 6. Tech Stack (lean, proven)

- **Frontend:** Next.js (kayak Sektoral.id) — 1 page `/report/[ticker]` + PDF preview + download
- **Backend:** Python FastAPI — agent orchestrator + Sectors proxy (cache 4h kayak KV di BankPromo)
- **DB:** SQLite (sintesis) / KV cache (prod)
- **PDF:** HTML template + Tailwind + Chart.js → PDF
- **Deploy:** Cloudflare Pages (`*.pages.dev` — Fadiil prefer ini over workers.dev)
- **Repo structure:**
  ```
  sectors-hackathon/
  ├── plan.md (this file)
  ├── data/peers.json, assumptions/
  ├── scripts/sectors_api.py, dcf_engine.py
  ├── agents/{collector,modeler,analyst,industry,risk,writer,visualizer,critic}.py
  ├── templates/report.html (HP Sekuritas clone)
  ├── app/ (Next.js)
  └── demos/report/assets/api-data.js (synthetic)
  ```

## 7. Phased Build (29 hari ke 30 Sep)

| Phase | Tanggal | Deliverable | Owner |
|---|---|---|---|
| **P0 — Scaffold** | 31 Aug – 2 Sep | Branch + plan.md (ini) + `dcf_engine.py` + `peers.json` + HTML template clone RATU | Hermes |
| **P1 — Data** | 3 – 6 Sep | Sectors API proxy + SQLite synthesis + 3 tickers E2E (RATU, BBCA, ADRO) | Collector agent |
| **P2 — Modeler** | 7 – 10 Sep | DCF + multiples deterministic, RATU numbers reproducible (IDR 7,880 & 6,960) | Modeler |
| **P3 — Agents** | 11 – 18 Sep | 5 LLM agents (analyst/industry/risk/writer/critic) + visualizer | Multi-agent |
| **P4 — PDF + UI** | 19 – 23 Sep | PDF renderer pixel-perfect + `/report/[ticker]` page | Frontend |
| **P5 — Polish & Video** | 24 – 29 Sep | 3 tickers showcase, video storytelling, audit swarm (3 AGY kayak kemarin) | All |
| **Submit** | 30 Sep 23:59 WIB | Commit freeze, public repo 90 hari | — |

## 8. Credit Budget (1,000 credits)

- Universe peers (1 credit) >> loop 22 tickers (22 credits) — hemat 95%
- `sections=` param tiap financials call — potong 50%
- Cache 4h + synthetic fallback — demo nggak burn credit live
- Estimasi: 3 tickers showcase × ~8 credits = 24 credits total (aman).

## 9. Risks & Mitigations

| Risk | Mitigasi |
|---|---|
| LLM halusinasi P/E 129x | Critic grep + Python calc only |
| Exhibit tanpa source | Template wajib `Source:` field, CI cek |
| Valuasi cuma 1 metode | DCF + Multiples wajib, kayak RATU |
| Sectors credit habis | Synthetic DB fallback |
| Track disqualification (T01 “off-the-shelf”) | Custom orchestration + tool pipeline, bukan cuma prompt (trap di rules §06) |

## 10. Decision Log

| Keputusan | Kenapa | Alternatif ditolak |
|---|---|---|
| Deep 1 product (report) bukan 31 demo | Judges 40% usability → retail butuh 1 yang jadi, bukan 31 setengah jadi | Sektoral.id 31 demos (proven tapi shallow) |
| 7+1 agents, bukan 1 monolith | Tiap section RATU butuh expertise beda; paralel = cepat, critic = anti-halusinasi | Single LLM prompt (gampang halusinasi angka) |
| Python deterministic untuk valuasi | RATU DCF ada WACC/beta/ERP eksplisit — LLM ngarang = fatal | LLM math (hallucination risk tinggi) |
| HTML→PDF bukan markdown | Biar mirip HP Sekuritas pixel-perfect | Markdown PDF (keliatan amatir) |
| Pages.dev bukan workers.dev | Fadiil prefer brand-aligned URL (valid 30 Aug) | Tunnel/workers.dev |

## 11. Open — Nunggu Ide Tambahan Fadiil + Temen

> **Slot buat ide lo:** tulis di bawah, gue merge ke plan.

- [ ] Ide 1: (dari Fadiil) — 
- [ ] Ide 2: (dari temen) —
- [ ] Ide 3: —
- Track lock-in: T01 AI Agents vs T03 Market Intel? (RATU report paling pas T03, tapi multi-agent = T01 — perlu decide)
- Ticker awal: RATU (benchmark) + 2 lain (BBCA? ADRO? TLKM?) —
- Bahasa default PDF: ID / EN / toggle? —

---

**Next step:** Fadiil drop ide tambahan → gue update Section 11 + scaffold `dcf_engine.py` + `templates/report.html` di branch ini. Gas?
