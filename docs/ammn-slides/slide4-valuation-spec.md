# Slide 4 - Valuasi Intrinsik (DCF / DDM / RNAV)

## 0. Binding rule text (owner, 12 Sep 2026)

The owner's wording outranks any paraphrase. One option is active per report; the analyst picks it by
hand, never the system.

### Method selection

> Metode dipilih manual oleh analis berdasarkan karakteristik emiten (bank pakai DDM, property/resources pakai RNAV, general corporate pakai DCF), bukan otomatis dari sistem. Struktur berikut generik, hanya satu opsi yang aktif per report sesuai emiten yang dicover.

### Opsi A - DCF (FCFF-based)

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

### Opsi B - DDM (bank/institusi keuangan)

> **Exhibit 8. Dividend Forecast and Terminal Value.** Blok 1 explicit period: Net Profit, Payout Ratio (%) asumsi berdasarkan historical payout perusahaan atau kebijakan dividen yang diumumkan, DPS, DPS growth (%), Discount Factor (menggunakan Cost of Equity bukan WACC karena DDM adalah equity valuation langsung), PV of DPS. Blok 2 terminal value: Terminal DPS, Terminal Growth, Terminal Value, PV of Terminal Value, Fair Value per Share (Gordon Growth formula: Terminal DPS x (1+g) / (CoE-g)).
>
> Jalur alternatif (kalau BRIDS pakai Inverse Cost of Equity method seperti pola BBTN di project): tambahkan baris Forward ROE (biasanya FY26F ROAE), Fair Value P/BV = (ROAE - g) / (CoE - g), BVPS (book value per share forecast), Fair Value = Fair Value P/BV x BVPS.
>
> **Exhibit 9. Cost of Equity Components.** Kalau pakai CAPM: Risk-free rate, Beta, ERP, Cost of Equity hasil. Kalau pakai band method (pola BBTN): Cost of Equity mean 5-tahun, Cost of Equity SD 5-tahun, jumlah SD yang dipakai dari mean (contoh: mean atau -0.5SD tergantung view terhadap risiko), Cost of Equity yang dipakai di valuasi.
>
> **Exhibit 10. Sensitivity Analysis.** Grid Cost of Equity x Long-term Growth, atau Cost of Equity x Forward ROE kalau pakai Inverse CoE method, isi cell Fair Value per Share.
>
> Narasi: fokus ke ROE trajectory sebagai driver utama (bukan cash flow generation seperti DCF), dan sustainability payout ratio ke depan mengingat kebutuhan modal untuk pertumbuhan kredit/aset bank.

### Opsi C - RNAV (property / plantation / resources dengan aset dominan)

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

> Nilai intrinsik dihitung oleh engine internal repo ini (server/report/engines/), bukan repo luar.

## 1. Which option is active for AMMN, and why

AMMN is Basic Materials / metals & mining, so the owner's mapping points at Opsi C, and the assumptions
file already records that a perpetual Gordon terminal is not defensible for a depleting reserve. With
the data the Sectors API carries, the choice is constrained:

| Option | Verdict for AMMN | Evidence |
|---|---|---|
| B - DDM | not applicable | AMMN pays no dividend: every dividend field in `company_report` is null (`historical_dividends`, `upcoming_dividends`, `yield_ttm`, `payout_ratio`), and `payout` is 0.0 in the assumptions. There is no DPS to discount. |
| C - RNAV | blocked by data | Sectors carries no asset-level data: no reserve tonnage, no per-asset production, no NAV per asset. RNAV needs reserve statements, ownership per asset, a commodity price deck and a discount rate per asset - annual/technical report material, not API material. |
| A - DCF | active | The engine runs on the Sectors inputs and produces all three exhibits. Modified as the rules require for finite resources: Gordon and the exit multiple are shown side by side and the gap is disclosed, never averaged. |

The anchor (target price) stays the relative leg - `data/assumptions/AMMN.json` already records
`anchor: ev_ebitda`, `anchor_basis: gate_primary: EV/EBITDA mid-cycle (REL)` - and this page exists to
show how far the cash-flow model reads below it.

## 2. Engine

Intrinsic value is computed by the repo's own engine modules under `server/report/engines/`:

* `dcf_engine/` - FCFF arithmetic (CAPM cost of equity, cost of debt, Gordon terminal value with the
  implied exit multiple, discounting and the bridge to equity, the WACC x growth grid).
* `ddm_engine/` - the equity-side arithmetic (dividend discounting, terminal value with the
  stable-phase payout test, fair P/BV for the inverse cost-of-equity cross-check).

Both are pure calculators: they fetch nothing, import no network client, and take every input from
`data/assumptions/<ticker>.json` plus the Sectors payload, so a render stays offline and deterministic.
Which numbers go in is the analyst's job; the engines only do the arithmetic.

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

### 4.1 Opsi C (RNAV) - the data contract

Wired as `server/report/valuation_rnav.py` with its own gate arm (`_audit_rnav_page`). It needs, per
asset: `name`, `size` + `size_unit` (ha / ton / boe / MW), `nav_bn` (per-project DCF or an independent
appraisal), `ownership_pct`, a `nav_source`, and optionally `discount_rate`. The assumptions file also
carries `rnav_discount` and either `rnav_discount_comparables` (a benchmark: peer or sector discount
levels) or nothing - in which case the page declares the discount a PURE JUDGMENT, as the rules demand.

No engine repo covers RNAV (the owner supplied DCF, DDM and relative peers), so the arithmetic is the
open identity: SUM(NAV x ownership) + cash - total debt - PV(corporate overhead), divided by shares,
minus the discount to RNAV. With no asset data at all the branch returns `available: False` and lists
what is missing - it never invents a NAV, and it says so when the bridge leaves a non-positive RNAV.

**Verified 12 Sep 2026: Sectors cannot supply this.** `GET /v2/news/filings/` is an insider-filing feed
(`references/sectors-api-and-mcp.md`: "insider buy/sell + holder_type"; filters are transaction_type,
holder_type, sector and dates). The cached AMMN pull returns 22 filings - 11 buys worth Rp 1,901 bn
against 9 sells worth Rp 5,442 bn between 2025-08-15 and 2026-07-22 - each carrying an IDX PDF link in
`source`, and nothing else: no annual report, no reserve statement, no per-asset production. Asset-level
NAV has to come from the issuer's annual report (amman.co.id/annual-report) or from the analyst.

## 3.1 Decision log - RNAV stays dormant for AMMN

**Decision (owner, 12 Sep 2026):** do not populate AMMN's RNAV page. Keep Opsi A (DCF) as the intrinsic
branch and the relative leg as the anchor; Opsi C remains implemented and generic, but no AMMN asset
table is built.

**Why:** the project uses Sectors data only. Sectors carries no reserve tonnage, no per-asset production
and no NAV per asset - verified against both the live endpoint and the cached pull (see §4.1). The other
candidate sources (the annual report at amman.co.id/annual-report, technical reports, KJPP appraisals)
are outside that boundary, so an AMMN RNAV would be built on inputs the project has ruled out.

**Alternatives rejected:** (a) pulling the annual report and extracting reserves - cheap to do, but it
breaks the Sectors-only rule and would put non-Sectors numbers in a deck whose every other figure traces
to Sectors; (b) filling the asset table with analyst judgment NAVs - the gate would pass but the number
would not be reproducible from data.

**Consequence, enforced in code:** `valuation_rnav.py` now refuses any asset whose `nav_source` does not
cite Sectors, and `_audit_rnav_page` flags an outside-Sectors NAV as a violation. A ticker whose asset
data does live in Sectors can still activate `valuation_method: "rnav"`.

## 4. Activating an option

`valuation_method` in `data/assumptions/<ticker>.json` selects the option (`dcf`, `ddm` or `rnav`). With no key
the page falls back to the DCF and says so on the page itself; a sector heuristic never switches the
model silently, because the rules make the choice the analyst's. The DDM branch ships with its own
builder (`server/report/valuation_ddm.py`), its own gate arm (`_audit_ddm_page`) and guard tests on a
synthetic dividend payer - an issuer that pays nothing gets a loud empty page, not invented dividends.

## 7. Decision log - multiple basis after the earnings path changed (12 Sep 2026)

Adopting a cited 3-year earnings path (Rp 66.9 / 71.7 / 81.4 tn revenue, EBITDA 33.9 / 44.7 / 55.2 tn) made
the deck's own multiple unusable, because the multiple and the level it multiplies were measured on
different bases. This section records the measurement, including the fix that did NOT work.

**Why the old pairing broke.** The deck applied a trailing EV/EBITDA mean (**28.42x**, measured in FY2023-25
when EBITDA was depressed by the smelter build: 15.7 / 23.0 / 16.4 tn) to a mid-cycle level. That
double-counts the recovery. Both halves come from the same dataset, so the first question was whether the
multiple itself was wrong.

**Rebasing the multiple does not fix it** (`server/valuation/normalised_multiple.py`, reconstruction
verified exact against the dataset's own prints, max gap 0.00x):

| Print year | EV (Rp bn) | EBITDA | rolling-3Y level | trailing multiple | normalised multiple |
|---|---|---|---|---|---|
| 2023 | 506,661 | 15,738 | 15,939 | 32.19x | 31.79x |
| 2024 | 672,501 | 23,040 | 20,984 | 29.19x | 32.05x |
| 2025 | 562,973 | 16,410 | 18,396 | 34.31x | 30.60x |

Trailing mean 31.90x vs normalised mean **31.48x** - the rebase moves nothing. A forward-consistent series
(EV_t / realised EBITDA_t+1: 22.0x for 2023, 41.0x for 2024) is no better. The reason is visible in the same
table: **EV has sat between Rp 506-672 tn across the cycle while EBITDA halved and doubled** - the market
prices the asset base, not trailing earnings, so an earnings-multiple anchor is the wrong instrument for
this name. Applying the rebased multiple to the new path gives Rp 13,362-20,564 per share, i.e. 2.7-4.2x the
market price: unusable, and now recorded as such in `tests/test_normalised_multiple.py`.

**What the data does support.**

| Leg | Value | Basis |
|---|---|---|
| DCF on the cited FCF path (Rp 11.0/26.1/35.1 tn) | Rp **2,392**/share (g 2.5%) · Rp 1,790 (g 0%) | our WACC 13.77%, our bridge |
| Market's own multiple today | EV/EBITDA **13.3x** FY26F · 10.0x FY27F · 9.0x mid-cycle | fact, not assumption |
| BRIDS' published TP | Rp 6,000 | implies **15.7x** FY26F + Elang NAV Rp 4,522/share (75% of their value) |
| The deck's TP before this change | Rp 5,873 | implies **15.4x** FY26F - same neighbourhood, weaker derivation |

**Reserve-based leg: not buildable from the licence.** A case-insensitive scan of the licensed payload for
`reserve`, `ore_tonnage`, `grade`, `proven_probable` finds nothing, so an RNAV/EV-per-reserve leg requires an
externally cited input; it is disclosed as excluded rather than estimated.

**Recommendation (pending owner sign-off, because it is the deck's headline number):** lead with a target
multiple on a stated basis - 15.0x FY26F EBITDA gives **Rp 5,667**/share, 15.7x gives Rp 5,994 - justified as
the market's current forward multiple (13.3x) plus the ramp not yet printed, cross-checked against BRIDS'
implied 15.7x. Then print the DCF (Rp 2,392) and the excluded Elang optionality as the counter-view instead
of hiding them. What must NOT ship is the 28.42x pairing, or a rebased multiple presented as the fix.
