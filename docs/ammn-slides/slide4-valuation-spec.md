# Slide 4 — Valuasi Intrinsik (DCF / DDM / RNAV)

## 0. Binding rule text (owner, 12 Sep 2026)

The owner's wording outranks any paraphrase. One option is active per report; the analyst picks it by
hand, never the system.

### Method selection

> Metode dipilih manual oleh analis berdasarkan karakteristik emiten (bank pakai DDM, property/resources pakai RNAV, general corporate pakai DCF), bukan otomatis dari sistem. Struktur berikut generik, hanya satu opsi yang aktif per report sesuai emiten yang dicover.

### Opsi A — DCF (FCFF-based)

> **Exhibit 8. FCFF Forecast and Terminal Value.** Satu tabel gabungan dengan tiga blok:
>
> Blok 1 - Explicit forecast period (5 tahun: umumnya tahun berjalan +4 forecast tahun ke depan): baris berurutan Revenue, EBIT, Tax on EBIT (dihitung EBIT x (1-effective tax rate), bukan tax rate statutory), NOPAT, (+) Depreciation & Amortization, (-) Capital Expenditure, (-)/(+) Increase/Decrease in Net Working Capital, FCFF (subtotal bold), FCFF growth (%) yoy, Discount Factor (1/(1+WACC)^n), PV of FCFF (bold).
>
> Blok 2 - Terminal value: Terminal FCFF (FCFF tahun terakhir forecast x (1+terminal growth)), Terminal Growth (g) dinyatakan eksplisit sebagai asumsi (biasanya di-cap tidak lebih tinggi dari long-term GDP growth atau risk-free rate, sesuai prinsip yang sudah Anda pegang), Terminal Value undiscounted, Discount Factor terminal, PV of Terminal Value. Kalau dilakukan cross-check dua metode (Gordon Growth vs Exit Multiple), tampilkan berdampingan sebagai dua kolom terpisah dalam blok yang sama.
>
> Blok 3 - Bridge ke equity value: Sum PV of FCFF (explicit period), (+) PV of Terminal Value, Enterprise Value (bold), (-) Net Debt (Total Debt - Cash & Equivalents pada tanggal valuasi), (+/-) Minority Interest dan/atau Non-Operating Assets, Equity Value (bold), dibagi jumlah saham beredar, Fair Value per Share (bold, highlight).
>
> **Exhibit 9. WACC Components.** Tabel dua kolom (parameter, nilai): Cost of Equity dihitung via CAPM (Risk-free rate, Beta, Equity Risk Premium, hasil Cost of Equity), Cost of Debt (pre-tax cost of debt dari rata-rata kupon obligasi/pinjaman existing, tax rate efektif, after-tax cost of debt), Capital Structure (Weight of Debt = D/(D+E), Weight of Equity = E/(D+E), berdasarkan market value bukan book value kalau memungkinkan), hasil akhir WACC di baris paling bawah, bold.
>
> **Exhibit 10. Sensitivity Analysis.** Grid matrix: baris WACC (rentang misal -1%, -0.5%, base, +0.5%, +1% dari WACC yang dipakai), kolom Terminal Growth atau Exit Multiple (rentang serupa), isi cell adalah Fair Value per Share hasil kombinasi tersebut. Base case (WACC dan growth yang dipakai di Exhibit 8) di-highlight beda warna supaya mudah dilihat reader.
>
> Narasi (di bawah ketiga exhibit, satu blok terpadu): sebutkan parameter mana yang paling sensitif terhadap valuasi (biasanya terminal growth di DCF perpetual), justifikasi asumsi growth/margin di forecast FCFF dikaitkan ke driver bisnis riil yang sudah dibahas di Slide 2-3 (bukan angka yang berdiri sendiri tanpa linkage), dan kalau ada gap material antara hasil Gordon Growth dan Exit Multiple, itu wajib di-flag eksplisit sebagai unresolved assumption yang perlu disclosure ke reader, bukan dirata-rata diam-diam.

### Opsi B — DDM (bank/institusi keuangan)

> **Exhibit 8. Dividend Forecast and Terminal Value.** Blok 1 explicit period: Net Profit, Payout Ratio (%) asumsi berdasarkan historical payout perusahaan atau kebijakan dividen yang diumumkan, DPS, DPS growth (%), Discount Factor (menggunakan Cost of Equity bukan WACC karena DDM adalah equity valuation langsung), PV of DPS. Blok 2 terminal value: Terminal DPS, Terminal Growth, Terminal Value, PV of Terminal Value, Fair Value per Share (Gordon Growth formula: Terminal DPS x (1+g) / (CoE-g)).
>
> Jalur alternatif (kalau BRIDS pakai Inverse Cost of Equity method seperti pola BBTN di project): tambahkan baris Forward ROE (biasanya FY26F ROAE), Fair Value P/BV = (ROAE - g) / (CoE - g), BVPS (book value per share forecast), Fair Value = Fair Value P/BV x BVPS.
>
> **Exhibit 9. Cost of Equity Components.** Kalau pakai CAPM: Risk-free rate, Beta, ERP, Cost of Equity hasil. Kalau pakai band method (pola BBTN): Cost of Equity mean 5-tahun, Cost of Equity SD 5-tahun, jumlah SD yang dipakai dari mean (contoh: mean atau -0.5SD tergantung view terhadap risiko), Cost of Equity yang dipakai di valuasi.
>
> **Exhibit 10. Sensitivity Analysis.** Grid Cost of Equity x Long-term Growth, atau Cost of Equity x Forward ROE kalau pakai Inverse CoE method, isi cell Fair Value per Share.
>
> Narasi: fokus ke ROE trajectory sebagai driver utama (bukan cash flow generation seperti DCF), dan sustainability payout ratio ke depan mengingat kebutuhan modal untuk pertumbuhan kredit/aset bank.

### Opsi C — RNAV (property / plantation / resources dengan aset dominan)

> **Exhibit 8. Asset Breakdown and RNAV Bridge.** Blok 1 per-aset: daftar aset/proyek/tambang/landbank, dengan kolom nama aset, ukuran (landbank hectare, cadangan ton/barrel, atau kapasitas produksi tergantung jenis aset), NAV per aset (hasil DCF per proyek atau appraisal value pihak independen), persentase kepemilikan emiten di aset tersebut, NAV attributable ke emiten (NAV per aset x % kepemilikan).
>
> Blok 2 bridge: Sum of NAV seluruh aset, (+) Cash & Equivalents, (-) Total Debt, (-) Corporate overhead (PV dari biaya korporat yang tidak attributable ke aset spesifik), Total RNAV (bold), dibagi jumlah saham, RNAV per share, (-) Discount to RNAV (%) sebagai judgment call analis, Target Price (bold, highlight) = RNAV per share x (1 - discount%).
>
> **Exhibit 9. Discount Rate per Aset.** Kalau tiap proyek/aset di-valuasi dengan DCF masing-masing yang punya risk profile berbeda, tabel ini breakdown WACC/discount rate per aset (bisa beda signifikan antara proyek matang vs proyek development stage).
>
> **Exhibit 10. Sensitivity Analysis.** Grid Discount to RNAV (%) x Discount rate/WACC, atau kalau driver utama adalah harga komoditas/properti, grid Discount to RNAV x asumsi harga jual per unit.
>
> Narasi: besaran discount to RNAV yang dipakai wajib dijustifikasi eksplisit, idealnya dengan basis pembanding (level discount historis emiten sejenis, atau rata-rata discount sektor), kalau tidak ada basis pembanding, state itu sebagai pure judgment assumption, jangan dipresentasikan seolah angka final tanpa dasar.

### Catatan lintas opsi

> Catatan lintas ketiga opsi: semua komponen Risk-free rate, Beta, ERP harus dicatat sumbernya (INDOGB 10Y untuk Rf IDR, US Treasury untuk Rf USD kalau emiten functional currency USD seperti kasus GMFI, Damodaran untuk ERP, Bloomberg untuk Beta), supaya traceable saat direview internal maupun eksternal. Kasus khusus E&P/PSC company perlu modifikasi tambahan dari Opsi A standar karena perpetual growth DCF secara teoritis tidak defensible untuk aset dengan cadangan terbatas (finite reserve life), sesuai prinsip yang sudah established sebelumnya, perlu didiskusikan terpisah kalau ada emiten E&P yang akan pakai template ini.

> ambil engine dari repo
> https://github.com/abidamassi/dcf-valuation-tool
> https://github.com/abidamassi/ddm_tool
> https://github.com/abidamassi/relativepeers

## 1. Which option is active for AMMN, and why

AMMN is Basic Materials / metals & mining, so the owner's mapping points at Opsi C, and the assumptions
file already records that a perpetual Gordon terminal is not defensible for a depleting reserve. With
the data the Sectors API carries, the choice is constrained:

| Option | Verdict for AMMN | Evidence |
|---|---|---|
| B — DDM | not applicable | AMMN pays no dividend: every dividend field in `company_report` is null (`historical_dividends`, `upcoming_dividends`, `yield_ttm`, `payout_ratio`), and `payout` is 0.0 in the assumptions. There is no DPS to discount. |
| C — RNAV | blocked by data | Sectors carries no asset-level data: no reserve tonnage, no per-asset production, no NAV per asset. RNAV needs reserve statements, ownership per asset, a commodity price deck and a discount rate per asset — annual/technical report material, not API material. |
| A — DCF | active | The engine runs on the Sectors inputs and produces all three exhibits. Modified as the rules require for finite resources: Gordon and the exit multiple are shown side by side and the gap is disclosed, never averaged. |

The anchor (target price) stays the relative leg — `data/assumptions/AMMN.json` already records
`anchor: ev_ebitda`, `anchor_basis: gate_primary: EV/EBITDA mid-cycle (REL)` — and this page exists to
show how far the cash-flow model reads below it.

## 2. Engine

`server/report/engines/abida_dcf/` — the calculation modules of
https://github.com/abidamassi/dcf-valuation-tool, copied verbatim (`config`, `utils`, `s06_wacc`,
`s07_forecast`, `s08_terminal`, `s09_valuation`, `s11_sensitivity`). Only the math is taken: that
repo's fetch layer reads yfinance, and yfinance's mapping for AMMN returns D&A of Rp 24 tn on revenue
of Rp 32.5 tn (EBITDA above revenue), which drives its own output to Rp 768/share against a Rp 4,860
price — its own module flags that as "Review Required ... likely modelling or data issue". The deck
therefore feeds the engine Sectors numbers and never fetches at render time.

`ddm_tool` (Opsi B) and `relativepeers` (slide 5 peer work) are cloned at
`~/projects/valuation-engines/` and import cleanly.

## 3. Enforcement

| Rule | Enforced by | Mechanism |
|---|---|---|
| Exhibit 8 three blocks, 11 required rows, five periods | `house_rules.audit_valuation_page` | every required row must exist and match the period count |
| Gordon and exit multiple side by side | `audit_valuation_page` | a missing exit-multiple column is a violation, because the rules ask for the cross-check whenever both are computed |
| Every WACC parameter carries its source | `audit_valuation_page` | the risk-free rate, beta and ERP rows must have a non-empty third column |
| Sensitivity grid complete, base case marked | `audit_valuation_page` | every cell must be filled and the base cell index must be set |
| A material Gordon-vs-multiple gap is disclosed | `audit_valuation_page` | if the two terminal methods differ by 2x or more, the disclosure block must contain an "UNRESOLVED" note |
| The perpetual-growth limitation on a depleting reserve | `audit_valuation_page` | a note mentioning the reserve or perpetual growth is required |
| The method choice is auditable | `audit_valuation_page` | the subtitle must name DDM and RNAV and why they were excluded |
| No re-derivation of the numbers | `server/report/valuation_page.py` | the projection columns come from the same cover table the reader sees, and the gate compares slide 4 against the cover's DCF leg |

### 4.1 Opsi C (RNAV) — the data contract

Wired as `server/report/valuation_rnav.py` with its own gate arm (`_audit_rnav_page`). It needs, per
asset: `name`, `size` + `size_unit` (ha / ton / boe / MW), `nav_bn` (per-project DCF or an independent
appraisal), `ownership_pct`, a `nav_source`, and optionally `discount_rate`. The assumptions file also
carries `rnav_discount` and either `rnav_discount_comparables` (a benchmark: peer or sector discount
levels) or nothing — in which case the page declares the discount a PURE JUDGMENT, as the rules demand.

No engine repo covers RNAV (the owner supplied DCF, DDM and relative peers), so the arithmetic is the
open identity: SUM(NAV x ownership) + cash - total debt - PV(corporate overhead), divided by shares,
minus the discount to RNAV. With no asset data at all the branch returns `available: False` and lists
what is missing — it never invents a NAV, and it says so when the bridge leaves a non-positive RNAV.

**Verified 12 Sep 2026: Sectors cannot supply this.** `GET /v2/news/filings/` is an insider-filing feed
(`references/sectors-api-and-mcp.md`: "insider buy/sell + holder_type"; filters are transaction_type,
holder_type, sector and dates). The cached AMMN pull returns 22 filings — 11 buys worth Rp 1,901 bn
against 9 sells worth Rp 5,442 bn between 2025-08-15 and 2026-07-22 — each carrying an IDX PDF link in
`source`, and nothing else: no annual report, no reserve statement, no per-asset production. Asset-level
NAV has to come from the issuer's annual report (amman.co.id/annual-report) or from the analyst.

## 3.1 Decision log — RNAV stays dormant for AMMN

**Decision (owner, 12 Sep 2026):** do not populate AMMN's RNAV page. Keep Opsi A (DCF) as the intrinsic
branch and the relative leg as the anchor; Opsi C remains implemented and generic, but no AMMN asset
table is built.

**Why:** the project uses Sectors data only. Sectors carries no reserve tonnage, no per-asset production
and no NAV per asset — verified against both the live endpoint and the cached pull (see §4.1). The other
candidate sources (the annual report at amman.co.id/annual-report, technical reports, KJPP appraisals)
are outside that boundary, so an AMMN RNAV would be built on inputs the project has ruled out.

**Alternatives rejected:** (a) pulling the annual report and extracting reserves — cheap to do, but it
breaks the Sectors-only rule and would put non-Sectors numbers in a deck whose every other figure traces
to Sectors; (b) filling the asset table with analyst judgment NAVs — the gate would pass but the number
would not be reproducible from data.

**Consequence, enforced in code:** `valuation_rnav.py` now refuses any asset whose `nav_source` does not
cite Sectors, and `_audit_rnav_page` flags an outside-Sectors NAV as a violation. A ticker whose asset
data does live in Sectors can still activate `valuation_method: "rnav"`.

## 4. Activating an option

`valuation_method` in `data/assumptions/<ticker>.json` selects the option (`dcf`, `ddm` or `rnav`). With no key
the page falls back to the DCF and says so on the page itself; a sector heuristic never switches the
model silently, because the rules make the choice the analyst's. The DDM branch ships with its own
builder (`server/report/valuation_ddm.py`), its own gate arm (`_audit_ddm_page`) and guard tests on a
synthetic dividend payer — an issuer that pays nothing gets a loud empty page, not invented dividends.
