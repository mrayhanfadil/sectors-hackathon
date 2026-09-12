# Slide 5 — Peer Valuation + Historical Relative spec (AMMN)

Ticker: AMMN (PT Amman Mineral Internasional Tbk, AMMN IJ). Sector: copper-gold mining (IDX Basic Materials / Mining — copper-gold sub-sector).
Valuation lenses on this slide: cross-sectional (peer multiples, Exhibit global 11) vs time-series (own-history bands + implied-price cross-checks, Exhibits global 12/13 + scoring extras). The two halves are STRICTLY SEPARATED visually — divider or section header — and must NEVER read as confirming one conclusion.

Applies to AMMN ONLY. Mining IDX peer set. Global house rules binding: docs/rules/house-report-format.md (label above + constant source line below; global counter, no literal numbers/ids; header/footer renderer-owned). Full template: /home/fadil/.hermes/cache/documents/doc_8073c261b904_Struktur Template Equity.md (Slide 5 Struktur Template + docs/rules/house-report-format.md).

---

## 0. Binding rule text (owner, 12 Sep 2026)

The owner's wording is the contract. Anything below that contradicts it loses.

> SLIDE 5 — Peer Valuation & Historical Relative Valuation
>
> Slide ini terbagi dua metodologi berbeda filosofi (cross-sectional vs time-series), wajib dipisah
> tegas secara visual dengan divider atau section header, supaya reader tidak salah interpretasi bahwa
> keduanya saling mengonfirmasi satu kesimpulan yang sama.
>
> **Bagian Atas (~50%) — Peer Valuation Table**
> Exhibit 11. Peer Valuation Table. Kolom: nama perusahaan + ticker, P/E (x), PBV (x), EV/EBITDA (x),
> opsional ROE (%) dan Market Cap sebagai kolom konteks tambahan kalau ruang memungkinkan. Periode data:
> FY26F dan/atau LTM, harus konsisten dipakai di semua baris. Baris penutup di bawah daftar peers:
> Median dan Average dari seluruh peer set (dua baris terpisah, bold, dengan sedikit spasi/garis
> pemisah dari baris peer individual). Baris emiten yang dicover di-highlight beda warna/shading supaya
> langsung terlihat posisinya relatif terhadap median/average tanpa perlu scanning manual.
> Kriteria pemilihan peer set harus eksplisit dan defensible, dicantumkan minimal di source line
> tambahan atau footnote: kesamaan sektor/sub-sektor, rentang market cap yang sebanding, dan "as of"
> date data harga yang dipakai. Narasi (2-3 kalimat): state posisi emiten relatif ke median dan average
> peer set, lalu justifikasi kenapa premium atau discount tersebut wajar atau tidak wajar, dikaitkan ke
> fundamental differential yang konkret (kualitas earnings, growth rate relatif, ROE gap, atau risk
> profile berbeda), bukan sekadar menyatakan angka gap tanpa penjelasan.
>
> **Bagian Bawah (~50%) — Relative Valuation Historical (Own-History Tool)**
> Blok deskripsi metodologi ditampilkan sebagai teks pendek: tool ini own-history relative valuation,
> menghitung empat trailing multiple (P/E, P/BV, EV/EBITDA, EV/Sales) sepanjang window satu tahun,
> membandingkan level saat ini terhadap distribusi historisnya sendiri (average, median, persentil).
> Item laporan keuangan dikonversi ke mata uang harga, driver fundamental dibangun dengan rolling TTM
> plus fallback berlapis, dan sistem scoring rule-based memilih multiple mana yang paling relevan
> ditampilkan berdasarkan karakteristik sektor, stabilitas historis multiple tersebut, dan validitas
> driver fundamentalnya.
> Exhibit 12. P/E Historical Band (1-Year): chart line P/E trailing 1 tahun, garis horizontal mean
> (dashed) dan median (dotted), marker khusus menandai level P/E saat ini di titik paling kanan.
> Exhibit 13. P/BV Historical Band (1-Year): format serupa.
> Implied Price Judgement: minimal dua metode implied price secara eksplisit dalam bentuk angka —
> (1) reversion ke mean 1-tahun, dan (2) reversion ke median 1-tahun — untuk minimal dua multiple
> (P/E dan P/BV default, ditambah EV/EBITDA atau EV/Sales kalau scoring rule-based memilihnya). Semua
> implied price dihitung dengan asumsi driver fundamental tetap konstan di level TTM/forward saat ini,
> hanya multiple yang direversi. Narasi per chart/metode (bukan satu paragraf gabungan): sebutkan
> persentil posisi multiple saat ini, lalu angka implied price dari reversion ke mean dan ke median
> secara terpisah; kalau kedua angka berbeda material, presentasikan sebagai range bukan angka tunggal.
> Disclaimer eksplisit wajib: implied price dari tool ini adalah cross-check mean-reversion berbasis
> multiple historis, bukan Target Price resmi di Slide 4, dan berbasis asumsi driver fundamental
> konstan, sehingga sifatnya snapshot bukan proyeksi.

## 1. Layout — two methodologies, one slide, hard visual break

- Top ~50%: Section header "Peer Valuation (Cross-Sectional)" + divider line (renderer-owned colour #067647 or muted grey, full-width). This is the peer table block.
- Bottom ~50%: Section header "Historical Relative Valuation — Own-History Tool (Time-Series)" + divider. This is the band-chart block.
- Between the two: a horizontal rule or shaded band with label, so a reader cannot scan the peer discount and the historical percentile as two legs of the same argument. Critic check: if the slide is exported to PDF, the two headers must be on visually distinct bands; no shared narrative sentence may bridge the two.
- Renderer owns pagination/figure counter: no hand-numbered exhibits in payloads, no header/footer/logo/page-number furniture from the agent.

---

## 2. Peer set — criteria, final set (record with as-of date), and cut-off convention

### 2.1 Peer-selection criteria (explicit, defensible, printed as footnote or source-line extension)

| Criterion | Rule for AMMN | How to evidence |
|---|---|---|
| Same sub-sector / commodity exposure | IDX copper-gold and adjacent base/precious miners whose revenue is dominantly copper and/or gold (and coal majors only where copper/gold peer depth is thin — then label "adjacent coal major, included for market-cap depth"). Exclude banks/property/telco — sector mismatch. | `peers()` subsector field + segment revenue note if available |
| Comparable market-cap band | Within ~0.3x–3x AMMN market cap at the as-of price, OR top-5 IDX miners by market cap if band would leave <4 peers. Record band actually used. | Market cap = Last Price (as-of) x shares outstanding |
| Listing + liquidity | IDX primary listing, 6M avg daily T/O disclosed; exclude suspended names (check `suspensions()`). | Sectors daily volume/value |
| Price cut-off ("as of") | ONE single as-of date for every multiple on the slide (e.g. "as of close 11 Sep 2026"). Multiples move daily — mixing dates is a fabrication. All peer prices, AMMN price, and the median/average are from that same close. | `daily()` / `universe_close()` date field |

If criteria would leave <5 peers, add 1–2 regional copper comps ONLY if Sectors covers them (SGX/KLSE copper miners via `sgx`/`klse` report sections). If Sectors does not cover them, do NOT invent — keep IDX-only set and record "regional comps unavailable in Sectors universe — IDX-only set retained".

### 2.2 AMMN mining peer set to record (finalise with as-of date; do not assume — verify in Sectors)

Primary IDX candidates (verify each via `peers()` / `company_report(..., "overview")` and keep only those that pass criteria above; record final kept set with as-of date):

- ANTM — Aneka Tambang (gold/nickel, IDX mining large-cap)
- INCO — Vale Indonesia (nickel, base-metal peer; include only if copper/gold depth requires it — label "nickel-adjacent")
- TINS — Timah (tin/mining, adjacent)
- ADRO — Alamtri Resources Indonesia (coal major; MDKA-era label: if ticker migrated to MDKA/ADRO split, record the live ticker actually returned by Sectors on the as-of date and note the lineage)
- BRMS — Bumi Resources Minerals (gold/copper exploration-development)
- MDKA — Merdeka Copper Gold (copper-gold direct comparable; if MDKA is the live ticker post-ADRO reorg, list MDKA not a legacy code)
- Regional copper comps (optional, only if Sectors covers): e.g. SGX/KLSE copper producer — include only with Sectors-sourced multiple and same as-of date, otherwise omit with explicit note.

The spec does NOT lock the count: the modeler records the FINAL peer list actually emitted (5–7 names typical) as one row per peer plus two summary rows (see section 3). Any peer that Sectors cannot return on the as-of date is dropped with a one-line note — never fabricated.

### 2.3 As-of convention (binding)

- Every price-driven input on Slide 5 shares one `as_of_close` (YYYY-MM-DD). Format: "Multiples as of close DD Month YYYY (IDX close)".
- Publish the cut-off in the peer-table footnote AND the band-chart footnote (same date). If `daily()` for any peer is missing on that date, roll that peer to the prior trading close and footnote "price as of DD MMM (prior close; DD MMM unavailable)" — never mix dates silently.
- The peer table period (FY26F and/or LTM — see section 3) must be CONSISTENT across all rows for that column. Do not show LTM for one peer and FY26F for another in the same column.

---

## 3. Exhibit specs (titles + data only — NO literal numbers, NO id field)

House rule: renderer owns the global `Exhibit N` counter (Typst figure counter `kind: "exhibit"`). This spec supplies titles + column/row structure + data bindings only. No hand-numbered exhibit literals in payloads, no `id` fields, no header/footer/logo/page-number furniture. Label above each object (descriptive, never generic "Table"/"Chart"); source line below exactly `Source: Company, Team Estimates` (constant). Real provenance (ticker+print+url+date) is retained as an internal audit field per exhibit — see section 8.

### Exhibit — Peer Valuation Table (global position 11; ~50% top)

Title (descriptive, period-explicit; modeler fills period — example patterns, never literal):
- If FY26F: "Peer Valuation — P/E, P/BV and EV/EBITDA (FY26F, as of DD Month YYYY)"
- If LTM: "Peer Valuation — P/E, P/BV and EV/EBITDA (LTM, as of DD Month YYYY)"
- Title must state FY26F/LTM and the as-of date; do not emit a period-free title.

Table structure (columns; order fixed):

| Column | Definition / binding | Format |
|---|---|---|
| Company (Ticker) | Full name + IDX ticker (e.g. "Aneka Tambang (ANTM IJ)") — AMMN row highlighted (shading/bold, renderer-owned) | Text, AMMN row distinct |
| P/E (x) | Price / EPS. Period = FY26F (consensus/BRIDS forward EPS) OR LTM EPS (trailing 12M). Same period for every row. | 1 decimal, "x" suffix |
| P/BV (x) | Price / BVPS (latest reported book, or forward BV if FY26F). Same period for every row. | 1 decimal, "x" |
| EV/EBITDA (x) | (Market cap + Net Debt − Cash) / EBITDA. Period-consistent (LTM EBITDA or FY26F EBITDA). | 1 decimal, "x" |
| ROE % (optional) | Net Income / Equity (LTM or FY26F, period-consistent) — context column if space allows | 1 decimal, "%" |
| Market Cap (Rpbn / US$mn) (optional) | As-of price x shares outstanding; USD leg uses FX stated in Slide 4 assumptions (rate+date) | No decimals for Rpbn; slash-separated dual leg |

Rows (order fixed):
1. One row per peer (5–7 peers as finalised in section 2).
2. A thin divider / extra spacing.
3. **Median** (bold, separate row) — median of each multiple column across peer rows ONLY (exclude AMMN from median/average computation; AMMN is the subject, not its own peer).
4. **Average** (bold, separate row) — arithmetic mean of each multiple column across peer rows.

Rules:
- Period consistency: every cell in a multiple column uses the same period (all FY26F or all LTM). Do not mix LTM for thin-coverage peers and FY26F for covered peers in one column — if FY26F unavailable for any peer, fall back the ENTIRE column to LTM and footnote why.
- Negative/meaningless P/E (loss-making LTM): show "n.m." with footnote "LTM EPS negative — P/E not meaningful", do not print a negative multiple; exclude n.m. from median/average.
- Highlight: AMMN row highlighted (shading/bold). Median and Average rows spaced off from peer rows (divider + extra padding).
- Peer-criteria footnote (or source-line extension): one line stating criteria actually applied + as-of date, e.g. "Peers: IDX copper/gold/adjacent miners within 0.3–3x AMMN mkt cap; multiples as of close 11 Sep 2026. Source: Sectors peers + daily close."

### Exhibit — P/E Historical Band, 1-Year (global position 12; bottom-left ~50%)

Title (descriptive): "AMMN — P/E Trailing Band vs 1-Year History (mean, median and current level)" — period (1Y) must appear; never generic "P/E Chart".

Chart spec:
- X: daily trading days, trailing 1 year from as-of close (approx 252 trading days; use whatever `daily("AMMN", start, end)` returns — do not pad missing days).
- Y: trailing P/E (x) = as-of price / rolling TTM EPS ( diluted, see section 5 fallbacks ). Y in "x".
- Series:
  - Solid line (navy, 1.8pt): trailing P/E daily.
  - Horizontal dashed line (grey, 1.1pt, dashed): 1-year arithmetic **mean** of the trailing P/E series.
  - Horizontal dotted line (grey, 1.1pt, dotted): 1-year **median** (50th percentile) of the trailing P/E series.
  - Marker at the right edge (filled dot or diamond, 6pt): **current P/E level** (as-of close).
- Labels: Y-axis "P/E (x)"; X-axis month-year short ("Sep-24", "Mar-25"); legend distinguishes mean (dashed) vs median (dotted).
- Source line below: `Source: Company, Team Estimates`.
- No header/footer furniture; renderer numbers the exhibit.

Data binding: `daily("AMMN", start, end)` for prices; `quarterly("AMMN", n_quarters=8)` + `quarterly_dates("AMMN")` for TTM EPS drivers; currency conversion if reporter is USD (see section 4).

### Exhibit — P/BV Historical Band, 1-Year (global position 13; bottom-right ~50%)

Same format as the P/E band, for P/BV:
- Y: trailing P/BV (x) = as-of price / BVPS (latest reported book per share, rolling; see section 5).
- Same three overlays: mean (dashed), median (dotted), current-level marker at right edge.
- Title: "AMMN — P/BV Trailing Band vs 1-Year History (mean, median and current level)".
- Source line: `Source: Company, Team Estimates`.

### Scoring-selected extras (conditional exhibits — emit only if the rule-based scorer selects them)

If the own-history scoring (section 4) ranks EV/EBITDA or EV/Sales as more relevant than P/E or P/BV for AMMN (sector/stability/validity rule), emit one or both as additional band charts in the same visual language (trailing line + mean dashed + median dotted + current marker), stacked or tabbed beneath the two mandatory bands. Titles:
- "AMMN — EV/EBITDA Trailing Band vs 1-Year History (mean, median and current level)"
- "AMMN — EV/Sales Trailing Band vs 1-Year History (mean, median and current level)"

These are NOT free-form: they appear only with a scorer justification line (see section 4) and they do NOT change the renderer counter rule.

---

## 4. Methodology note (short printable version — render as caption/footnote under the bottom half)

Display this (or a tighter paraphrase that preserves every clause) as a boxed note beneath the band charts, 2–3 lines, 8–9pt:

"Own-history relative tool — four trailing multiples (P/E, P/BV, EV/EBITDA, EV/Sales) measured daily over a trailing 1-year window and compared to their own historical distribution (average, median, percentiles). Items are converted to the price currency for non-IDR reporters; drivers are rolling-TTM with layered fallbacks where quarterly gaps exist; a rule-based scoring system selects the most relevant multiple by sector, historical stability and driver validity."

Scoring rule to document (for audit, not printed verbatim, but the note must imply it):
- Sector gate: miners → EV/EBITDA and P/BV often more informative than P/E when earnings are cyclical/negative; P/E deprioritised if EPS sign flips within the year.
- Stability gate: coefficient of variation / percentile spread within the 1Y window — multiples with CV > threshold or with >20% n.m. days are down-ranked.
- Validity gate: driver availability — if TTM EPS/BVPS/EBITDA/Revenue has >2 consecutive missing quarters after fallbacks, that multiple is scored invalid for this window.
- Output: rank 1–4; P/E and P/BV are ALWAYS shown (mandatory Exhibits 12/13); the top-ranked of EV/EBITDA vs EV/Sales is shown as an extra if it outranks P/E or P/BV.

---

## 5. Implied-price judgement — method spec (binding)

### 5.1 Principle

Every implied price is a **multiple-reversion cross-check with drivers held constant**: the multiple reverts to its 1Y historical statistic (mean or median), the fundamental driver (EPS/BVPS/EBITDA/Revenue) stays at its CURRENT TTM/forward level. No forward driver growth is assumed. This is a snapshot, not a forecast.

### 5.2 At least TWO methods explicit in numbers, for at least P/E + P/BV

For each multiple selected (P/E and P/BV mandatory; plus EV/EBITDA or EV/Sales if scoring selects — see section 4):

| Method | Formula (driver CONSTANT) | Label in exhibit/table |
|---|---|---|
| (1) Reversion to 1Y **mean** | Implied Price (mean) = 1Y mean multiple x current driver | "Implied price @ 1Y mean" |
| (2) Reversion to 1Y **median** | Implied Price (median) = 1Y median multiple x current driver | "Implied price @ 1Y median" |

Drivers (constant at current level):
- P/E → TTM EPS (diluted, rolling 4 quarters) OR FY26F EPS if the peer table is on FY26F — period must match the band's period; state which.
- P/BV → BVPS (latest reported, per share).
- EV/EBITDA → EBITDA (TTM) → implied EV = mean/median EV/EBITDA x TTM EBITDA → implied equity = implied EV − Net Debt + Cash → implied price = implied equity / shares outstanding.
- EV/Sales → Revenue (TTM) → same EV→equity→price bridge.

For EV legs, Net Debt, Cash and shares outstanding are the SAME valuation-date figures used in Slide 4 bridges — tie-out required.

### 5.3 Currency, rolling-TTM and fallbacks (layered, in order)

- Currency conversion: if AMMN (or any peer for the peer table) reports in USD, convert the driver to IDR using the FX stated in Slide 4 assumptions (rate + date) — same FX for every leg on the as-of date. Drivers and price must be in the same currency.
- Rolling TTM: sum of the last 4 reported quarters from `quarterly()` (report_date order). Use `quarterly_dates()` to avoid billed-empty calls.
- Layered fallbacks (apply in order; record which fired):
  1. Use 4-quarter TTM if all 4 quarters present.
  2. If 1 quarter missing: annualise the last 3 quarters (x 4/3) and flag "3Q annualised".
  3. If 2+ quarters missing: fall back to latest annual figure and flag "annual fallback — TTM unavailable".
  4. If driver is still non-positive/non-meaningful: mark that multiple-day as n.m. and exclude from mean/median/percentile; if >20% of the 1Y window is n.m., down-rank that multiple in scoring.

### 5.4 Presentation

- Show mean-implied and median-implied prices as **two separate numbers** (e.g. "P/E mean-implied Rp X; median-implied Rp Y"), not blended.
- If the two differ materially (spread >10% or >1x daily ATR — disclose threshold), present as a **RANGE** ("Implied range Rp X–Y (mean–median)"), never a false-precision single number.
- Show the driver value used and the multiple value used alongside each implied price (e.g. "TTM EPS Rp 123 x 1Y mean P/E 9.4x = Rp 1,156"), so the Critic can recompute.
- Reference the current percentile (see section 6) in the same table/paragraph — the implied price and the percentile are co-located, not on different pages.

---

## 6. Narrative specs

### 6.1 Peer-table narrative (2–3 sentences, directly under the peer table — NOT merged with band narratives)

Required elements, in order:
1. Position vs median and vs average (with explicit discount/premium %). Example pattern: "AMMN trades at P/E FY26F 9.0x, a X% discount to the peer median of Yx and Z% to the peer average of Wx (EV/EBITDA Ax vs median Bx)." Numbers are recomputable from the table.
2. WHY the premium/discount is fair or unfair — tied to concrete fundamental differentials, never a bare gap. Must name at least two differentials from: earnings quality (cyclicality / one-offs in TTM), relative growth (revenue/EBITDA CAGR vs peers), ROE gap (AMMN ROE vs peer median ROE), risk (reserve life / single-asset concentration / smelter execution / leverage / regulatory risk including DMO/royalty), or cost position (AISC vs peers if disclosed). Example: "The discount reflects AMMN's single-asset concentration (Batu Hijau) and smelter capex overhang vs diversified peers, partly offset by its higher ROE/growth on copper leverage."
3. No generic "kinerja membaik" — every comparative claim carries a number or is explicitly labelled qualitative with reason if the datum is unavailable.

### 6.2 Per-chart band narratives (one paragraph per chart/multiple — NOT a single merged paragraph)

For each band chart shown (P/E mandatory, P/BV mandatory, plus any scoring-selected extra):

- State the **current percentile** of the multiple in its 1Y distribution (e.g. "P/E currently at the 25th percentile of its 1Y range (mean 11.2x, median 10.8x, current 8.1x)").
- State the **mean-implied price** and **median-implied price** separately with drivers shown (see section 5.4). If the two differ materially, restate as a RANGE and explain the direction ("mean above median → distribution right-skewed by peak-cycle prints").
- One sentence of interpretation: cheap vs expensive vs own history, with the caveat that this is a mean-reversion snapshot (drivers constant) — see disclaimer.
- Do NOT merge the P/E and P/BV narratives into one paragraph — the reader must be able to audit each multiple independently.

---

## 7. Mandatory disclaimer (verbatim — include exactly, not paraphrased)

Place as a footnote / boxed note directly beneath the bottom-half narratives, 7–8pt, italic or muted colour but legible:

"Implied prices from this own-history tool are mean-reversion cross-checks that hold fundamental drivers constant at their current TTM/forward level and revert only the multiple to its 1-year historical mean/median. They are a snapshot, not a forecast, and are NOT the official Target Price established in Slide 4 (DCF-shortened / RNAV)."

Additionally, for the peer half, include a one-line scope note beneath the peer narrative (not the disclaimer):

"Peer multiples are cross-sectional as of a single cut-off date and reflect market pricing on that date; they do not imply convergence to the peer median/average."

---

## 8. Data dependencies (Sectors primary; web_search colour only — NO web magic numbers)

| Need | Sectors wrapper → endpoint | Fields used | Fallback |
|---|---|---|---|
| Peer set + subsector | `peers("AMMN")` → `company_report("AMMN","peers")` → GET /company/report/AMMN/?sections=peers | peer tickers, subsector, valuation section if present | NONE for peer list — if empty, emit loud STOP note "peer set await Sectors peers — cross-sectional leg unavailable on this cut-off"; no invented peers |
| Peer multiple prints (provenance) | `peers()` for the list + `daily(peer, as_of, as_of)` for price + `quarterly(peer)` / `company_report(peer,"valuation,financials")` for EPS/BVPS/EBITDA drivers | price, EPS, BVPS, EBITDA, net debt, cash, shares | web_search prints ONLY as provenance colour with ticker+print+url+date preserved — still counts as "live peer print" only if url+date present; bare outlet = fabrication |
| AMMN daily price for bands | `daily("AMMN", start, end)` → GET /transaction/daily/AMMN/?start=&end= (range max 90 days — loop with 90-day windows for 1Y; cache aggressively) | close, date | NONE for prices — loud STOP on sectors_missing_key; no synthetic prices |
| Quarterly drivers for TTM | `quarterly_dates("AMMN")` → /company/get_quarterly_financial_dates/AMMN/ then `quarterly("AMMN", n_quarters=8)` → /financials/quarterly/AMMN/ | revenue, net income, EPS, book value, EBITDA (or derive), shares | layered fallbacks in section 5.3; empty 200 still bills — check dates first |
| JCI where needed (relative context) | `index_daily("JCI" or "COMPOSITE", start, end)` → GET /index-daily/... | index close | same as daily — loud STOP if both legs missing; never synthetic |
| Mining financials (ops context) | `mining_company_financials("ammn")` → /mining/companies/financials/ammn/ | production, cost (if available) | qualitative only — not a substitute for quarterly drivers |
| FX for USD reporters | Slide 4 assumption (USDIDR rate + date stated) | rate | — (state rate+date) |
| Smelter/expansion, DMO/royalty policy (narrative WHY) | `news(symbols="AMMN", start, end)` → /news/?extension=idx + `corporate_actions("AMMN")` | url+date mandatory per provenance gate | web_search T1 IDX/Kontan T2 Reuters/Bloomberg — url+date mandatory |

Rules (from end-to-end discipline):
- `sectors_missing_key` → loud STOP with note in the exhibit payload, never synthetic.
- Empty-result 200 still bills — cache aggressively and call `quarterly_dates()` before `quarterly()`.
- Credit discipline: request minimal `sections=` (peers, valuation, overview), prefer universe feeds (`universe_close(date)`) if peer breadth is needed on the same as-of date.

---

## 9. Provenance — PRIMARY-MULTIPLE PROVENANCE (binding, Critic-enforced)

- Every multiple on the **primary leg** (the period actually headlined in the peer table — FY26F if FY26F is headlined, otherwise LTM) must cite **>=2 live peer prints** with `ticker + print value + url + date`. A bare outlet name-drop without url+date is fabrication and the Critic MUST reject.
- "Live peer print" means: a Sectors-sourced price/driver pair on the as-of date, OR a web_search print that carries a resolvable URL and a publication/cut-off date that matches the as-of convention. PDF/IDX filings count if url+date present.
- Internal audit field: `source` on each exhibit payload retains the real provenance (array of {ticker, multiple, value, url, date, engine path like `server/sectors.py:peers` or `news.py`}) — this is the audit build detail (`exhibit-source-detail()`), NOT the printed line. The visible line stays `Source: Company, Team Estimates`.
- If live peers are unusable (coverage <2 prints after Sectors + web_search with url+date): publish the multiple as an **explicit assumption** (e.g. "FY26F P/E 10x assumed — peer coverage insufficient on this cut-off") AND add a **sensitivity leg** (e.g. ±2x on P/E, ±1x on EV/EBITDA) whose implied prices are shown alongside the base. Do not silently keep the base as if it were peer-grounded.

---

## 10. Tie-outs

1. Peer-table multiples are all on the SAME as-of date and the SAME period (FY26F or LTM) per column — recomputable from `daily()` closes and the stated driver; median/average recomputed from peer rows only (AMMN excluded).
2. Band drivers (TTM EPS/BVPS/EBITDA/Revenue) tie to the same Sectors quarterly source that feeds Slide 3 and Slide 4; any Slide 3 revision re-derives the TTM drivers on Slide 5.
3. EV-implied prices (EV/EBITDA, EV/Sales) use the SAME Net Debt / Cash / shares outstanding as Slide 4 bridges, same valuation date — bridge figures identical.
4. Implied prices are labelled cross-checks and do NOT move the Slide 4 headline TP; the peer narrative's premium/discount % recomputes from the peer table's median/average.
5. Exhibit order: peer table emitted before P/E band before P/BV band before any scoring-selected extra; renderer numbers sequentially — no literal "Exhibit N" anywhere in payloads.

---

## 11. Assumption table skeleton (modeler fills values; spec fixes rows+sources)

| # | Parameter | Source / rule | Used in |
|---|---|---|---|
| B1 | As-of close date | Single YYYY-MM-DD, all multiples | Peer table, bands |
| B2 | Peer set (final kept tickers) | Section 2 criteria, as verified in Sectors | Peer table |
| B3 | Peer period (FY26F vs LTM) | Consistent per column; state headlined period | Peer table columns |
| B4 | FY26F EPS / BVPS / EBITDA source | `company_report(peer,"future,valuation,financials")` or consensus feed; if unavailable, LTM fallback flagged | Peer multiples |
| B5 | TTM EPS / BVPS / EBITDA / Revenue (AMMN) | `quarterly()` rolling 4Q, fallbacks per section 5.3 | Bands + implied prices |
| B6 | FX USDIDR (if non-IDR reporter) | Slide 4 assumption rate+date | Currency conversion |
| B7 | Market cap / shares outstanding | `company_report()` snapshot, date | Peer table market-cap col, EV bridges |
| B8 | Net Debt / Cash (valuation date) | Same as Slide 4 bridge | EV-implied prices |
| B9 | 1Y mean / median / percentile per multiple | Computed from trailing daily series | Bands + implied prices |
| B10 | Scoring rank + justification | Sector/stability/validity gates (section 4) | Extra bands decision |
| B11 | Provenance prints (>=2 per primary multiple) | ticker+print+url+date | Critic gate |

---

## 12. Critic checks (gate before ship — every box must be ticked)

- [ ] Zero literal "Exhibit N" strings; zero `id` fields on exhibits (renderer owns the global counter).
- [ ] Every exhibit has descriptive label above + exactly `Source: Company, Team Estimates` below — no exceptions.
- [ ] No renderer-owned furniture emitted (header/footer/logo/page number/date block) from the agent.
- [ ] Peer table: period consistent across all rows per column; median + average are separate bold rows, spaced off; AMMN row highlighted; peer criteria + as-of date published in footnote.
- [ ] Primary-multiple provenance: >=2 live peer prints with ticker+print+url+date retained as internal audit `source` per exhibit, OR explicit-assumption label + sensitivity leg present; bare name-drops rejected.
- [ ] Bands: trailing line + horizontal mean (dashed) + median (dotted) + current-level marker at right edge; X = 1Y daily, Y = trailing multiple (x); month-year X labels.
- [ ] Implied-price judgement: at least TWO methods explicit in numbers (mean-reversion + median-reversion) for at least P/E + P/BV (+ extras if scoring selects); drivers held constant; mean- and median-implied shown separately; material gap presented as RANGE.
- [ ] Per-chart narrative: percentile in 1Y distribution + mean-implied and median-implied prices separately — NOT one merged paragraph.
- [ ] Mandatory disclaimer present verbatim (section 7) — tool implied prices are mean-reversion cross-checks, NOT the Slide 4 Target Price.
- [ ] Visual separation: divider/section headers between cross-sectional (top) and time-series (bottom) — no sentence bridges the two as confirming one conclusion.
- [ ] No synthetic numbers; `sectors_missing_key` → loud STOP recorded with note; empty 200 billed honestly; no web magic numbers in price/driver fields.
- [ ] Internal provenance (outlet, url, date, engine path) retained as audit field per object — visible line stays constant.
- [ ] Cross-exhibit tie-outs verified (peer medians recomputed, EV bridges use Slide 4 Net Debt/Cash/shares, TTM drivers match Slide 3 source).

## 7. Decision log — data basis (12 Sep 2026)

| Decision | Why | Alternatives rejected |
|---|---|---|
| P/E and P/BV columns print Sectors' published `pe_ttm` / `pb_mrq` | One source, one as-of, identical basis on every row; verified against our own LTM rebuild (TBMS 12.5 vs 12.51, ANTM 8.9 vs 8.64, INCO 19.3 vs 19.29, TINS 9.2 vs 9.19, AMMN 39.3 vs 38.62) | Recomputing both columns from the peers payload's `market_cap`: that cap is a *prior fiscal year's* snapshot, so TBMS came out 2.31x against Sectors' own published 12.51x |
| Peer financials pulled from `quarterly(sym)`, not `company_report(sym,'financials')` | The financials section is **annual** (rows keyed by `year`); the quarterly endpoint gives dated per-quarter rows. Mixing them breaks the rule's "one consistent period" requirement | Annual rows for peers + quarterly for the covered name: cheaper, but the table would compare FY2025 EBITDA against Q1-2026 equity |
| Market cap recovered as `pb_mrq x latest equity` | Keeps the EV bridge on the same basis as the published ratios without a second cap source | Re-deriving shares outstanding: not published in the payloads we hold |
| Net debt = `total_debt - cash_and_short_term_investments` | Quarterly rows carry no `net_debt` field, but carry both components | Leaving EV/EBITDA blank (the previous page's `—` / GAP G8) |
| Slide 5 prints as two consecutive pages, 5A (peer table) and 5B (own history) | The owner's rule requires the two philosophies be separated hard so no reader reads one as confirmation of the other; at the required content density (a 12-row table, two band charts, an implied-price table and the disclaimer) one page either overflows to three pages or forces type below 7.5pt | One page at 7.4pt (measured: the deck grew 9 -> 11 pages and the band charts still split across a page break) |
| Rows with negative or near-zero earnings print `n.m.` and leave the median/average | A negative P/E is not a comparison; a near-zero denominator produces 9,141x noise | Printing them: pushes the average to nonsense (the old page showed EMAS -368.61) |
| Implied prices shown as a range when mean- and median-reversion differ by >10% | The rule forbids presenting a materially different pair as one number (false precision) | Averaging the two reversion targets |

**Data-layer contract:** `server/report/peers_data.py` is cache-first and Sectors-only. Artifacts live at
`output/cache/sectors/<TICKER>/peer_table.json` and `bands_1y.json`, raw responses under `raw/`. A rebuild
that finds them on disk makes **zero billed calls** (verified: `billed calls: 0 | cache hits: 11`); only
`--refresh` can spend. The renderer reads the JSON, so a PDF render performs no network calls at all.

**Known data gap (disclosed on the page, not hidden):** Sectors' latest quarter for AMMN is Q1-2026
(2026-03-31), so the 129 sessions after that date reuse the same TTM driver — the page states the driver
as-of date and the number of frozen sessions rather than implying a fresh TTM at every point.
