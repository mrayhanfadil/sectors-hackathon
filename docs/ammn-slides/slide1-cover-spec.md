# Slide 1 - Cover / Main Page spec (AMMN)

Ticker: AMMN (PT Amman Mineral Internasional Tbk, AMMN IJ). Sector: copper-gold mining.
Valuation lens for AMMN: RNAV for finite reserve + shortened DCF (mining extension -
reserve life, copper/gold price deck, smelter capex/progress). Bank-style GGM does NOT apply.

## 1. Purpose

Slide 1 is the only page an institutional PM may read. It must stand alone:
rating + price box + secondary stats (sidebar ~30%), thesis header + 3 highlight
bullets + 3 narrative paragraphs P1/P2/P3 + Key Financials tie-out table (main ~70%).
Every quantitative claim carries an explicit number. No generic titles, no unquantified
"kinerja membaik".

## 2. Sidebar spec (~30%)

### 2.1 Rating block

- Big bold rating word: one of Buy / Hold / Sell.
- Italic status line directly beneath, exactly one of:
  (Maintained) / (Upgrade from Hold) / (Downgrade from Buy) / (Initiation).
- Renderer owns fonts/sizes; this spec owns the allowed strings.

### 2.2 Price box (2-col label|value, values right-aligned)

| Label | Definition |
|---|---|
| Last Price (Rp) | Close before publish date. Source: Sectors `daily()` (fetch-daily-transaction), NOT web magic numbers. |
| Target Price (Rp) | New TP from Slide 4 valuation (RNAV/shortened-DCF output). This box CONSUMES Slide 4; never invents. |
| Potensi naik/turun (%) | `(TP / Last - 1) * 100`, always with explicit `+`/`-` sign, 1 decimal. Amended 19 Sep 2026 from `Upside/Downside (%)`: the label is the most-read text on the cover, and the token is one the plain-language rule bans in prose. |

Consistency rule: Last Price date == publish-date-minus-1-trading-day; TP == Slide 4
final TP to the rupiah. Critic check: recompute upside from the two printed numbers.

### 2.3 Secondary stats

- No. of Shares (mn): shares outstanding, from Sectors `company_report()` /
  `report_sections()` company snapshot.
- Mkt Cap (Rpbn/US$mn): `Last Price x No. of Shares`, slash-separated; USD leg uses
  the FX (USDIDR) stated in Slide 4 assumptions with its date. State both.
- Avg Daily T/O (Rpbn/US$mn): average daily turnover value. DEFINE the window once
  (3 or 6 months) and use it consistently across ALL reports. Recommended: 6 months
  for AMMN (large-cap post-IPO liquidity normalisation). Record chosen window here.
- Free Float %: public holders with <5% each ONLY - NOT total non-controller.
  Source: `shareholders_composition()` (GET /company/shareholders-composition/).
  If two sources conflict (e.g. IDX fact sheet vs Sectors), emit BOTH figures +
  explicit flag, never silently pick one.
- Major Shareholder name + %: top holder; second row if >1 significant holder >5%.
  (AMMN note: expect concentrated ownership - verify, do not assume names.)

### 2.4 Sidebar footer

Analyst name (bold) + "Equity Analyst" beneath. Renderer-owned layout.

## 3. Main content spec (~70%)

### 3.1 Company header

Full name + (AMMN IJ), big bold navy. Thesis subheading beneath (italic/different
colour, MAPA pattern e.g. "Conservative Guidance, Sustained Growth Ahead") - must
reflect the actual thesis (e.g. copper-price leverage, smelter ramp, Batu Hijau
phase), never generic ("AMMN Company Update").

### 3.2 Three highlight bullets

Bold, one dense sentence each, each with a quantitative claim. Fixed roles:

1. Last quarter result vs expectations (actual vs BRIDS est vs consensus, with
   running-rate % where available).
2. Specific driver (copper/gold realised price, sales volume, cash cost / AISC,
   smelter milestone - name the number).
3. Rating action + TP (e.g. "Maintain Buy, raise TP to RpX on ...").

Must stand alone: a reader who reads only these 3 lines knows result, driver, call.

### 3.3 P1 Financials (bold subheading, e.g. earnings-growth-driven-by-X)

- Open with actual net profit / revenue, qoq AND yoy.
- Running-rate check: % of BRIDS FY est + % of consensus achieved.
- Driver breakdown: margin movement, volume growth, specific cost item
  (treatment charges, royalties/DMO, depreciation on smelter capex).
- Close with positioning vs management guidance (if issued).
- Rule: EVERY quantitative claim carries an explicit number.

### 3.4 P2 News / sentiment / catalyst (bold subheading)

- Concrete catalyst: copper/gold price move, smelter construction/commissioning
  progress, ESDM royalty/DMO/export policy change, macro assumption change.
- Quantified earnings/valuation impact WITH calculation basis where possible
  (e.g. "every +US$100/t copper ≈ +RpY net profit FY26F at Z% margin"); if no basis
  exists, state explicitly qualitative - never force numbers.
- Priced-in assessment vs sector/JCI price action (reference Exhibit 2 relatively).

### 3.5 P3 Valuation (bold subheading, mandatory 4 elements)

1. Methodology: "We maintain/raise/lower our TP to Rp[X] using RNAV for AMMN's
   finite reserve (plus shortened DCF cross-check), with [WACC/CoE/long-term
   copper-gold deck] at [Y]." Mining extension: name reserve life + price deck.
2. Forecast linkage: "Our TP implies [EBITDA/Revenue] CAGR FY26-28F of [Z]%,
   driven by [specific driver: Batu Hijau Phase 8 grade, smelter contribution]."
3. Trading multiple at TP: PER/PBV/EV-EBITDA 26F [N]x vs 5y hist avg [M]x or peer
   avg [P]x (peers: `peers()` section + global copper peers for cross-check).
4. Risk to view (mandatory for AMMN given commodity leverage): 1-2 concrete risks
   with direction (e.g. downside: copper -10% ≈ -RpY earnings; upside: smelter
   early commissioning).

### 3.6 Bahasa awam - aturan bahasa untuk seluruh halaman ini (owner, 19 Sep 2026)

Owner feedback: *"menurut gua ini susah dibaca untuk awam"*. The cover spread is the first thing a
lay reader meets, so every reader-facing string on page 1 is written in plain Indonesian. Figures
never change; only the wrapping does - every number keeps its source and its exact value.

Surfaces (all of them live on the cover spread) and their status:

| Surface | Source | Rule |
|---|---|---|
| Theme title | `data/assumptions/<T>.json` -> `theme_title` | awam; scanned by the audit since 19 Sep 2026 |
| 3 highlight bullets | `cover.rating_box.key_takeaways` | awam; each bullet still carries a number |
| P1 heading + body | `server/report/cover_slide1.py::_financial_para` | awam; max 1 bridging quarter sentence |
| P2 body | `cover.slide2.katalis.body` | awam wrapper; market facts keep their market terms |
| P3 body | `cover.slide2.valuasi.body` | **discan juga** (19 Sep 2026, owner: "bungkus juga, biar enak bacanya"), dengan `VALUASI_MANDATE_TOKENS` di-carve-out by name |
| Thesis rail + risk details | `payload.thesis`, `payload.risks` | awam |

Glossary (what the deck printed -> what it prints now):

| Jangan | Pakai |
|---|---|
| `Basis Q1-2026: pendapatan ...` | `Penjualan kuartal itu ...` |
| `Q1-2026` / `FY26F` / `FY26F-28F` | `Kuartal I 2026` / `2026` / `2026-2028` |
| `Jalur FY26F-28F` | `Proyeksi 2026-2028` |
| `Cluster-buy direksi` | `Direksi membeli saham serentak` |
| `sinyal keyakinan insider` | `tanda orang dalam yakin pada prospek perusahaan` |
| `vs mid-cycle 28,42x` | `rata-rata jangka panjangnya 28,42 kali` |
| `re-rating belum tercermin` | `kenaikan penilaian ini belum tercermin` |
| `multiple 18,38x` | `18,38 kali laba 2026` |
| `estimasi tim atas basis data berlisensi` | `estimasi tim kami, angka proyeksi` |
| `marjin kotor 42,4%` | `laba kotor 42,4% dari penjualan` |
| `EBITDA` tanpa penjelasan | `Laba operasi (EBITDA)` sekali, lalu `laba operasi` |
| `Rebalancing GDX/GDXJ` | `Masuknya dana indeks GDX/GDXJ` |
| `kualitatif` | `belum bisa dihitung angkanya` |
| `exit multiple`, `run-rate`, `capex`, `FCF`, `CAGR`, `qoq/yoy` | dilarang di permukaan awam |

Tetap Inggris karena pasar memang memakainya (owner rule): `BUY` / `SELL` / `HOLD`, `DCF`,
`WACC`, `EV/EBITDA` (P3), `EBITDA` (diberi glosa sekali), `Priced-in` (diberi glosa di tempat,
dan gate paragraf 2 mensyaratkan token itu ada).

Enforcement: `server/report/house_rules.py::audit_plain_language` (denylist `PLAIN_JARGON` +
`PLAIN_JARGON_PATTERNS` untuk tag tahun/kuartal) dipanggil `audit_house_rules` di jalur render dan
oleh `agents/critic.py`; mutasi di `tests/test_slide_rules_adoption.py` membuktikan gate-nya
menangkap persis string yang dulu tercetak di halaman ini. Panjang copy tetap dibatasi
`tests/test_slide2_forecast.py::test_cover_copy_stays_within_the_one_pager_budget` (2600 karakter
untuk P1+P2+P3): bahasa awam lebih panjang, jadi penerjemahan berikutnya harus muat di anggaran
itu atau tata letak satu halaman (dan posisi exhibit Key Financials) ikut bergeser.

### 3.7 Paragraf 2 ditulis agent, bukan template (19 Sep 2026)

Owner: *"ini juga cuma copy paste data, ngga ada narasi yang mengalir. minta agent ADK bikin ini
lebih easy to read oleh awam"*. Paragraf 2 sekarang punya dua jalur, satu fact sheet:

| Jalur | Kapan | Sumber |
|---|---|---|
| `writer_frozen` | `data/narrative/<TICKER>_katalis.json` ada DAN hash-nya cocok dengan fact sheet sekarang | prose dari agent `katalis_narrative_writer` (writer role) |
| `template_fallback` | artifact tidak ada / hash beda (fakta berubah) | rangkaian deterministik di `slide2.build_katalis` |

Jalur yang dipakai selalu tertulis di payload (`cover.slide2.katalis.narrative_source`), jadi
Critic dan halaman audit bisa membedakan tulisan agent dari template tanpa menebak.

Fact sheet = `server/report/narrative_facts.py`. Isinya **kalimat lengkap**, bukan pasangan
key/value mentah: sheet berisi pasangan telanjang mengundang agent menggabungkan dua field jadi
klaim yang datanya tidak pernah bilang (kejadian nyata: "+37,0%" dan "Rp 4.860" jadi "posisi
direksi naik 37,0% menjadi Rp 4.860"). Template dan gate membaca nilai mentahnya lewat
`facts["raw"]`, jadi tidak ada angka yang ditulis dua kali.

Gate `house_rules.audit_katalis_narrative` (jalan dari `audit_house_rules` → Critic + render):
angka yang tidak ada di fact sheet, jargon metode, kata plumbing internal ("payload", "freeze",
"via Sectors"), cerita tentang deck sendiri, dan panjang > 1100 karakter. Runner
(`agents/adk/narrative_runner.py`) menjalankan gate SEBELUM membekukan, jadi prose yang gagal
tidak pernah masuk deck. Aturan binding untuk agent-nya: `KATALIS_NARRATIVE_RULE` di
`agents/adk/agents/instructions.py`, dilampirkan ke `writer_instruction`.

## 4. Exhibit specs (titles + data only - NO literal numbers, NO id field)

House rule: renderer owns the global `Exhibit N` counter (Typst figure counter
`kind: "exhibit"`). Agent supplies title + data only.

### Exhibit - SKIPPED (template Exhibit 1, EPS Consensus table)

SKIP with rationale: the EPS-consensus transparency device (BRIDS vs Consensus vs
BRIDS/Cons %) assumes meaningful sell-side consensus coverage. AMMN is a single-name
test build with no locked consensus feed; fabricating a consensus column would
violate the no-synthetic rule. Skipping keeps the global counter honest: the
relative-performance chart becomes the FIRST emitted exhibit and the renderer
numbers it accordingly. Revisit if a consensus source is wired.

### Exhibit - `[AMMN] relative to JCI Index` (dual-axis chart)

- LHS: AMMN absolute price line (navy). RHS: relative performance vs JCI (%).
- Trailing window 18–24 months; X labels short month-year (Sep-24).
- Label above (descriptive, never generic "Chart"); source line below exactly
  `Source: Company, Team Estimates`.
- Dependency (blocking): granular price time series - Sectors `daily("AMMN", start,
  end)` (fetch-daily-transaction) + `index_daily("JCI"/"COMPOSITE", start, end)`
  (fetch-index-daily). Never web magic numbers. If either leg missing →
  loud STOP, never synthetic.

### Exhibit - Key Financials table (tie-out source of truth for Slide 3)

- Columns: 2024A 2025A 2026F 2027F 2028F (2 actual + 3 forecast, rolling).
- Rows: Revenue, EBITDA, EBITDA Growth %, Net Profit, EPS, EPS Growth %,
  PER x, PBV x, EV/EBITDA x.
- Format: navy header white text, right-aligned numbers, 1 decimal for
  multiples/% , no decimals for Rpbn absolutes except EPS (1 decimal).
- THIS TABLE is the tie-out source of truth for Slide 3: Slide 3 model output
  must reconcile cell-for-cell (revenue/EBITDA/net profit forecast years).
  Any Slide 3 revision re-exports this table; Critic rejects mismatches.
- Mining extension rows live on Slide 3 (production, realised prices, AISC),
  NOT here - this table keeps the 9 canonical rows.

## 5. Data dependencies (Sectors primary; web_search colour only)

| Need | Sectors (server/sectors.py wrapper → endpoint) | Fields | Fallback |
|---|---|---|---|
| Last price / price history | `daily()` → daily-transaction | close, date, volume/value | NONE for numbers - loud STOP on sectors_missing_key; web_search backup for narrative colour only |
| JCI history (Exhibit 2 RHS) | `index_daily()` → GET /index-daily/ | index close, date | same as above |
| Shares, mkt cap inputs | `company_report()` / `report_sections()` → /company/report/ | shares outstanding, company snapshot | same |
| Quarterly result (P1, bullets) | `quarterly()` → /financials/quarterly/ + `quarterly_dates()` | revenue, net profit, qoq/yoy | same |
| Shareholders / free float | `shareholders_composition()` → /company/shareholders-composition/ | holder name, %, <5% public float | emit BOTH + flag on conflict; never silent-pick |
| Segments (mining ops context) | `segments()` → /company/get-segments/ (known 404 for some names - billed 1 credit, handle honestly) | segment revenue | Slide 3 mining financials |
| AMMN mining financials | `mining_company_financials()` → /mining/companies/financials/ | year, production, cost | same |
| Peers (P3 multiple) | `peers()` → peers section | PER/PBV/EV-EBITDA | global copper peers via web_search, labelled qualitative |
| Catalysts/news (P2) | `news()` → news endpoint; `corporate_actions()` | url+date (Critic requires both) | web_search T1 IDX/Kontan T2 Reuters/Bloomberg, url+date mandatory |
| FX for US$mn legs | Slide 4 assumption (state rate + date) | USDIDR | - |

Rules: if `sectors_missing_key` → loud STOP, never synthetic. Empty-result 200
still bills - cache aggressively. Dividend freshness: N/A on cover (no dividend
field emitted here); payout discussion belongs to Slide 3/4 if raised.

## 6. Tie-outs

1. Price box: Upside == (TP/Last-1)*100 recomputed; TP == Slide 4 final TP.
2. Mkt Cap == Last Price x No. of Shares (both currency legs, stated FX).
3. Key Financials table == Slide 3 model output cell-for-cell (forecast years).
4. P3 methodology (RNAV/DCF, WACC/CoE, price deck) == Slide 4 assumptions.
5. Exhibit order: relative-performance chart emitted before Key Financials table;
   renderer numbers sequentially - no literal "Exhibit N" anywhere in payloads.

## 7. Critic checks (gate before ship)

- [ ] Zero literal "Exhibit N" strings; zero `id` fields on exhibits.
- [ ] Every exhibit has descriptive label above + exactly `Source: Company, Team Estimates` below.
- [ ] No renderer-owned furniture emitted (header/footer/logo/page number/date block).
- [ ] Every quantitative claim in bullets/P1/P2/P3 carries an explicit number or is
      explicitly labelled qualitative with reason.
- [ ] Free-float figure follows <5%-public discipline, or dual-emit + flag.
- [ ] P2 impact quantification shows basis or is explicitly qualitative.
- [ ] P3 contains all 4 mandatory elements including risk-to-view.
- [ ] Upside sign (+/-) present; TP matches Slide 4; Key Financials match Slide 3.
- [ ] Provenance (outlet, url, date) retained as internal audit field per object.
- [ ] No synthetic numbers; sectors_missing_key → loud STOP recorded.
