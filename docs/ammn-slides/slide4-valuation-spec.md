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

## 4. Activating an option

`valuation_method` in `data/assumptions/<ticker>.json` selects the option (`dcf` or `ddm`). With no key
the page falls back to the DCF and says so on the page itself; a sector heuristic never switches the
model silently, because the rules make the choice the analyst's. The DDM branch ships with its own
builder (`server/report/valuation_ddm.py`), its own gate arm (`_audit_ddm_page`) and guard tests on a
synthetic dividend payer — an issuer that pays nothing gets a loud empty page, not invented dividends.
