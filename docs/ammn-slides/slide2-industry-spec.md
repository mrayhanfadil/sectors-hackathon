# Slide 2 — Kondisi Industri dan Katalis/Sentimen Emiten spec (AMMN)

Ticker: AMMN (PT Amman Mineral Internasional Tbk, AMMN IJ). Subsector: Copper & Gold Mining (`metals-mining`).
Asset Scope: Batu Hijau open-pit mine (Phase 7 completion, Phase 8 high-grade mining), Elang porphyry exploration/development asset, and PT AMIN Sumbawa copper smelter & precious metals refinery (PMR) downstream processing.

---

## 1. Purpose & Layout Architecture

Slide 2 establishes the macro industry reality, issuer-specific operational catalysts, and prevailing market sentiment for institutional portfolio managers (PMs) and buy-side analysts. It bridges the high-level investment thesis on Slide 1 with the granular operational and financial forecasts on Slide 3 and intrinsic valuation on Slide 4.

### 1.1 Structural Role in Report Deck
- **P1 (Kondisi Industri)**: Global macro and sector supply-demand dynamics (copper/gold price decks, mine supply disruptions, TC/RC collapse, inventories, USD interest rates, USD/IDR FX mechanics for a USD-functional IDX reporter, China demand, energy costs) and AMMN's structural cost-curve positioning.
- **P2 (Katalis Spesifik Emiten)**: Actionable, issuer-specific catalysts (ESDM regulations, smelter progress & tolling economics, Elang porphyry timeline & capex, M&A/consolidation). Strict quantification rule: every catalyst is quantified where an empirical basis exists; otherwise explicitly stated as qualitative.
- **P3 (Sentimen Pasar)**: Market perception, foreign institutional flow, relative price action vs JCI, media tone, and sell-side consensus ratings. **STRICT DOMAIN BOUNDARY**: zero valuation multiples, zero Target Price, zero Fair Value per share (strictly reserved for Slides 4–5).

### 1.2 Layout & House Format Rules (docs/rules/house-report-format.md)
- **Narrative by default**: Slide 2 consists of three dense narrative paragraphs with bold subheadings. It contains NO mandatory chart or table by default.
- **Supporting visual discipline**: If an optional supporting visual is included (e.g. Copper/Gold Price Trend or Cumulative Foreign Flow):
  1. Descriptive label **ABOVE** the visual: e.g. `Exhibit [renderer-counter]. Copper LME Cash vs Gold LBMA Spot Trajectory (2024-2026YTD)`. Never generic (`Chart`, `Table`, `Figure`).
  2. Source line **BELOW** the visual: strictly `Source: Company, Team Estimates`, without exception.
  3. Numbering is **renderer-owned**: managed via the global Typst figure counter (`kind: "exhibit"`). Payloads must **never** supply literal `Exhibit N` strings and must **never** emit an `id` field.
  4. Page furniture (header, publication date, Sectors.app logo, `#067647` divider, footer disclosure, page numbers) is entirely **renderer-owned**. Agents never emit layout furniture.

---

## 2. Paragraph 1 — Kondisi Industri (Industry Conditions)

### 2.1 Narrative Specification & Guidelines
P1 establishes the external environment for AMMN. It must cover four core thematic pillars:
1. **Commodity Price Trajectory & Outlook**: Trailing 12-month trend and forward 12–24 month institutional consensus forecast for copper (LME US$/tonne or US$/lb) and gold (LBMA US$/oz). Cite institutional forecasts (e.g., Consensus, World Bank Commodity Outlook, CRU, Wood Mackenzie via Sectors news/subsector).
2. **Global Demand-Supply Balance**: 
   - *Mine Supply*: Structural deficit/surplus, acute disruptions (e.g., global pit closures, Chilean grade depletion, water/community constraints).
   - *Smelting & Refining Overhang*: Chinese/Indonesian smelter capacity buildout vs mine concentrate availability, driving spot Treatment & Refining Charges (TC/RC) to historic multi-year lows (sub-zero / near-zero), widening operating margins for pure concentrate miners while penalizing standalone custom smelters.
   - *Inventories*: Global exchange inventories (LME, SHFE, COMEX) expressed in days of global consumption.
3. **Material Macro Backdrop for Copper-Gold Miners**:
   - *US Monetary Policy & USD Rates*: Real interest rate trajectories, opportunity cost of holding non-yielding gold, and US Dollar Index (DXY) impact.
   - *USD/IDR FX Mechanics*: AMMN's functional and financial reporting currency is **USD**, and 100% of mineral sales are priced against USD benchmarks (LME Cu, LBMA Au). However, domestic Indonesian operating costs (labor, local contractors, land, domestic transport) are incurred in **IDR**. Consequently, IDR depreciation against USD provides an unhedged operational cost buffer, lowering cash costs in USD terms.
   - *China Macro & Energy Transition*: Chinese grid infrastructure investment, renewable power expansion (solar/wind), and EV penetration offsetting traditional property sector headwinds.
   - *Energy & Fuel Input Costs*: High-speed diesel (HSD) and fuel costs for open-pit hauling fleets and captive power generation at Sumbawa.
4. **Structural Positioning Close**: Conclude with AMMN's positioning versus global and regional peers (**Outperform / In-line / Underperform**) grounded in structural fundamentals:
   - High ore grades from Batu Hijau Phase 8 ramp-up.
   - First-quartile (bottom-decile) net C1 cash cost globally after byproduct gold credits.
   - Downstream integration via PT AMIN Sumbawa smelter securing domestic processing compliance and insulating from concentrate export bans.

### 2.2 Paragraph Template with AMMN Mining Slots

```markdown
**Kondisi Industri: Dinamika Defisit Konsentrat Global dan Disiplin Biaya Tambang Tembaga-Emas**

Sektor pertambangan tembaga dan emas global berada dalam fase [P1_COMMODITY_CYCLE_PHASE] yang didorong oleh defisit pasokan konsentrat tambang serta penguatan struktural permintaan transisi energi. Harga tembaga LME mencatatkan rata-rata [P1_CU_SPOT_PRICE] ([P1_CU_YOY_PCT]% yoy), dengan konsensus memproyeksikan lintasan harga bergerak menuju [P1_CU_FORECAST_PRICE] pada [P1_CU_FORECAST_PERIOD] (sumber: [P1_COMMODITY_SOURCE_CU]). Secara bersamaan, harga emas LBMA bertahan kuat di level [P1_AU_SPOT_PRICE] ([P1_AU_YOY_PCT]% yoy), ditopang oleh akumulasi cadangan devisa bank sentral global dan ekspektasi pelonggaran suku bunga riil US Federal Reserve sebesar [P1_FED_RATE_DELTA_BPS] bps. Dari sisi neraca penawaran-permintaan, kapasitas peleburan (*smelting*) global mengalami ekspansi agresif yang tidak diimbangi oleh pertumbuhan produksi konsentrat akibat gangguan operasional tambang global di Amerika Latin, memicu anjloknya tarif *Treatment and Refining Charges* (TC/RC) spot hingga menyentuh [P1_TCRC_SPOT_LEVEL] (vs level acuan tahunan [P1_TCRC_BENCHMARK]). Di tengah persediaan gudang LME/SHFE yang setara [P1_INVENTORY_DAYS] hari konsumsi global, kondisi makro yang paling material bagi penambang domestik adalah kombinasi permintaan jaringan listrik China ([P1_CHINA_GRID_GROWTH]% yoy) dan volatilitas nilai tukar USD/IDR di level [P1_USDIDR_LEVEL]. Mengingat AMMN membukukan pembukuan fungsional dalam USD dengan 100% pendapatan berbasis komoditas global sedangkan [P1_DOMESTIC_COST_PCT]% biaya operasional menggunakan denominasi IDR, pelemahan nilai tukar rupiah memberikan bantalan marjin operasional alami (*natural FX hedge*). Kami memposisikan AMMN untuk [P1_AMMN_POSITIONING] (outperform) relatif terhadap rata-rata industri pertambangan tembaga regional, didukung oleh keunggulan struktural kurva biaya C1 bersih pada desil terbawah ([P1_AMMN_C1_COST]) pasca-kredit emas produk sampingan (*byproduct credits*), transisi kadar bijih tinggi Batu Hijau Fase 8, serta integrasi smelter Sumbawa yang memitigasi friksi ekspor bahan mentah.
```

### 2.3 Populated Illustrative Example (AMMN)
> **Kondisi Industri: Dinamika Defisit Konsentrat Global dan Disiplin Biaya Tambang Tembaga-Emas**  
> Sektor pertambangan tembaga dan emas global berada dalam fase pengetatan pasokan konsentrat tambang primer yang didorong oleh penurunan kadar bijih tambang matang serta akselerasi permintaan tembaga untuk elektrifikasi dan transmisi energi baru. Harga tembaga LME bergerak menguat di kisaran US$9.850/ton (+14,2% yoy), dengan konsensus institusional memproyeksikan harga rata-rata stabil di US$10.200/ton pada 2026F (sumber: World Bank Commodity Markets / Consensus, 2026). Secara bersamaan, harga emas LBMA mencetak rekor di level US$2.450/oz (+21,5% yoy), didorong oleh akumulasi agresif bank sentral global dan ekspektasi penurunan suku bunga riil US Federal Reserve sebesar 50–75 bps. Dari sisi neraca penawaran-permintaan, ekspansi kapasitas smelter di China dan Indonesia yang melebihi ketersediaan konsentrat global telah menekan tarif *Treatment and Refining Charges* (TC/RC) spot ke level mendekati nol (US$0–5/ton vs acuan tahunan US$80/ton), memberikan keuntungan marjin signifikan bagi produsen konsentrat tambang hulu atas pelebur pihak ketiga. Dengan cadangan inventori LME/SHFE berada pada level ketat setara 4,5 hari konsumsi, dinamika makro yang paling material bagi AMMN adalah kombinasi permintaan elektrifikasi China (+8,5% yoy pada investasi *grid*) dan stabilitas kurs USD/IDR di kisaran Rp15.900–16.200. Mengingat pendapatan AMMN 100% berdenominasi USD sedangkan ~40% biaya tunai operasional (tenaga kerja lokal, logistik, dan kontraktor) berdenominasi IDR, penguatan USD memberikan efisiensi marjin operasional riil. Kami memposisikan AMMN untuk *outperform* terhadap industri, ditopang oleh kurva biaya tunai bersih C1 pada kuartil pertama global (-US$0,15/lb setelah kredit produk sampingan emas), lonjakan kadar bijih tembaga-emas pada penambangan Batu Hijau Fase 8, serta kepastian serapan konsentrat melalui penyelesaian smelter tembaga terintegrasi di Sumbawa Barat.

---

## 3. Paragraph 2 — Katalis Spesifik Emiten (Issuer-Specific Catalysts)

### 3.1 Narrative Specification & Guidelines
P2 focuses **exclusively on catalysts applicable to AMMN**. Generic sector themes (e.g. "copper demand is rising") are forbidden here. Every catalyst must fall into one of four mandatory categories and follow the **Strict Quantification Discipline**:
1. **ESDM & Regulatory Framework**:
   - IUPK operational tenure, compliance, and extension milestones under Law No. 3/2020 (UU Minerba).
   - Export permit (*Surat Persetujuan Ekspor* / SPE) extensions and progressive export duty (*bea keluar*) rates under Ministry of Finance / ESDM regulations tied to physical smelter progress verification (>90%).
   - Royalty obligations under PP No. 26/2022 (copper and gold progressive tariffs).
2. **Smelter Progress & Tolling Economics**:
   - PT Amman Mineral Industri (AMIN) copper smelter (900.000 dmt/year concentrate input, producing up to 222.000 tpa copper cathodes) and Precious Metals Refinery (PMR, up to 18 tpa gold and 55 tpa silver).
   - Financial transition from concentrate export seller to refined cathode and bullion supplier:
     * *Duty Savings*: Elimination of progressive export duty (saving 7.5%–15% of concentrate FOB export value).
     * *Freight & TC/RC Savings*: Elimination of international ocean freight and offshore treatment/refining deductions.
     * *Byproduct Commercialization*: Revenue from ~830.000 tpa sulfuric acid off-take.
     * *Cost Offsets*: Incremental fixed operating costs (~US$65/t concentrate) and asset depreciation once commercial operations commence.
3. **Elang Porphyry Development Timeline & Capex**:
   - Long-term reserve replacement: Elang deposit (~1,4 billion tonnes ore resources at ~0,35% Cu and ~0,35 g/t Au) ensuring multi-decade operational continuity post-Batu Hijau.
   - Exploration, feasibility study (FS), AMDAL environmental permit, and infrastructure staging.
   - Capex sequencing: pacing of capital expenditure post-smelter completion to maintain balance sheet strength and avoid liquidity stress.
4. **M&A / Regional Downstream Consolidation**:
   - Strategic positioning alongside Freeport Indonesia's Manyar smelter in forming domestic refined copper self-sufficiency in Indonesia.
   - Long-term domestic off-take agreements with cable, wire-rod, and industrial manufacturing supply chains.

### 3.2 Strict Quantification Discipline
- **Quantified Basis**: Wherever an operational or financial parameter can be computed, state the explicit formula and basis:
  $$\Delta \text{Revenue (Duty Saving)} = \text{Annual Export Volume (ton)} \times \text{Concentrate FOB Price (US\$/ton)} \times \Delta \text{Export Duty Rate (\%)} \times \text{USD/IDR}$$
  $$\Delta \text{EBITDA (Copper Sensitivity)} = \pm \text{US\$0,10/lb Cu} \times \text{Annual Payable Copper Production (lbs)} \times (1 - \text{Royalty \%})$$
- **No Basis = Explicitly Qualitative**: If an event has no verifiable numerical guidance (e.g. government regulatory discretion on domestic processing quotas or long-term consolidation talk), state it explicitly as **kualitatif** with rationale. **Never force synthetic numbers.**

### 3.3 Paragraph Template with AMMN Mining Slots

```markdown
**Katalis Spesifik Emiten: Progres Smelter Sumbawa, Normalisasi Bea Keluar, dan Jalur Pengembangan Elang**

Kinerja operasional dan profil profitabilitas AMMN didorong oleh empat katalis spesifik yang terkuantifikasi secara bertahap. Pertama, dari aspek regulasi ESDM dan Kementerian Keuangan, penyelesaian progres fisik fasilitas peleburan dan pemurnian PT AMIN yang telah melampaui [P2_SMELTER_PHYSICAL_PROGRESS]% memberikan kepastian perpanjangan izin ekspor konsentrat serta penurunan tarif bea keluar dari [P2_DUTY_RATE_OLD]% menjadi [P2_DUTY_RATE_NEW]%. Kami mengestimasi normalisasi tarif bea keluar ini menghasilkan penghematan biaya langsung (*cash cost savings*) sebesar [P2_DUTY_SAVINGS_USD] juta (setara [P2_DUTY_SAVINGS_IDR] triliun) pada periode pelaporan berjalan, dengan basis perhitungan volume ekspor konsentrat tahunan sebesar [P2_CONCENTRATE_EXP_VOL] ribu dmt pada harga realisasi rata-rata [P2_CONCENTRATE_AVG_PRICE]/dmt. Kedua, komisioning smelter Sumbawa berkapasitas [P2_SMELTER_CAPACITY_DMT] ribu dmt konsentrat/tahun mentransformasi profil penjualan AMMN menjadi produk bernilai tambah tinggi berupa [P2_CATHODE_CAPACITY_TPA] ton katoda tembaga dan [P2_GOLD_PMR_TPA] ton emas murni batangan. Transisi ini mengeliminasi potongan TC/RC luar negeri dan biaya pengapalan internasional, yang kami kalkulasikan menyumbang ekspansi marjin EBITDA konsolidasi sebesar [P2_EBITDA_MARGIN_EXP_BPS] bps setelah memperhitungkan biaya operasional smelter sebesar [P2_SMELTER_OPEX_PER_TON]/ton konsentrat. Ketiga, terkait kontinuitas cadangan jangka panjang, kelanjutan eksploitasi pit Batu Hijau Fase 8 diproyeksikan mengerek produksi tembaga sebesar [P2_CU_VOL_GROWTH_PCT]% yoy dan emas sebesar [P2_AU_VOL_GROWTH_PCT]% yoy, sebelum transisi bertahap menuju mega-proyek porfiri Elang yang memiliki estimasi cadangan bijih [P2_ELANG_ORE_TONNES] miliar ton. Alokasi belanja modal (*capex*) Elang dijadwalkan melandai pasca-selesainya smelter, menjaga rasio *net debt to EBITDA* di bawah level [P2_NET_DEBT_EBITDA_MAX]x. Keempat, dampak kebijakan integrasi rantai pasok industri tembaga domestik dinilai bersifat kualitatif positif, memperkuat posisi AMMN sebagai pemasok katoda tembaga primer untuk industri manufaktur kabel nasional.
```

### 3.4 Populated Illustrative Example (AMMN)
> **Katalis Spesifik Emiten: Progres Smelter Sumbawa, Normalisasi Bea Keluar, dan Jalur Pengembangan Elang**  
> Kinerja operasional dan profitabilitas AMMN didorong oleh empat katalis spesifik yang terkuantifikasi. Pertama, dari aspek regulasi ESDM dan Kemenkeu, progres fisik smelter tembaga PT AMIN yang mencapai 92,4% memastikan izin ekspor konsentrat tetap aktif sekaligus memangkas tarif bea keluar dari 10,0% menjadi 7,5%, sebelum tereliminasi penuh (0%) saat operasi komersial penuh. Kami mengestimasi relaksasi dan transisi tarif bea keluar ini menghasilkan penghematan kas operasional sebesar US$145,0 juta (~Rp2,32 triliun) pada FY26F, dengan basis perhitungan volume ekspor konsentrat 850.000 dmt pada asumsi harga konsentrat FOB US$2.275/dmt. Kedua, ramp-up komersial smelter Sumbawa berkapasitas 900.000 dmt konsentrat/tahun mentransformasi pendapatan AMMN ke 222.000 ton katoda tembaga LME Grade A dan 18 ton emas per tahun dari fasilitas PMR. Langkah hilirisasi ini mengeliminasi potongan TC/RC pihak ketiga dan biaya logistik maritim internasional, memberikan ekspansi marjin EBITDA bersih konsolidasian sebesar +280 bps setelah memperhitungkan biaya operasional smelter terintegrasi sebesar US$68/ton konsentrat olahan. Ketiga, terkait umur tambang (*mine life*), penambangan bijih berkadar tinggi di Batu Hijau Fase 8 mendongkrak produksi tembaga sebesar +18,5% yoy menjadi 415 juta lbs dan emas +32,0% yoy menjadi 580 ribu oz pada FY26F, mendanai transisi pengembangan deposit porfiri Elang (1,4 miliar ton bijih; 0,35% Cu, 0,35 g/t Au). Manajemen mengonfirmasi alokasi capex ekspansi Elang disinkronisasi pasca-penurunan belanja modal smelter, mempertahankan rasio Net Debt to EBITDA yang sehat pada 1,2x. Keempat, dampak sinergi penjualan produk sampingan asam sulfat (830.000 ton/tahun) kepada industri pupuk domestik dinilai secara kualitatif memperkuat ketahanan arus kas dari volatilitas harga komoditas global.

---

## 4. Paragraph 3 — Sentimen Pasar (Market Sentiment)

### 4.1 Narrative Specification & Guidelines
P3 captures institutional positioning, trading flow dynamics, and media perception.
- **STRICT DOMAIN BOUNDARY**: P3 must NEVER discuss valuation, price multiples (PER, PBV, EV/EBITDA), discount rates, or Target Price. Those metrics belong strictly to Slides 4–5.
- **Required Elements**:
  1. **Foreign & Domestic Fund Flow**: Cumulative net foreign buy/sell in AMMN over 1-month, 3-month, or YTD windows (data from Sectors `fetch-foreign-flow` and `fetch-broker-summary-top`).
  2. **Broker Accumulation/Distribution**: Concentration of institutional brokerage desks (e.g. top foreign vs domestic desks) as a proxy for institutional accumulation.
  3. **Relative Performance vs JCI & Sector**: Share price performance relative to the Composite Index (JCI) and basic materials index (IDXBASIC / IDXMINING) in the trailing period (cross-referencing Slide 1 Exhibit relative chart).
  4. **Media Tone & Sentiment Narrative**: Media newsflow tone (Positive / Neutral / Negative) from Sectors `fetch-news` (extension="idx"), citing concrete headline drivers (e.g. smelter commissioning verification, export permit certainty, copper supply deficits).
  5. **Sell-Side Consensus Breadth**: Aggregated consensus ratings in the mining subsector (counts of Buy / Hold / Sell) as a direct gauge of institutional risk appetite.

### 4.2 FLOAT / MSCI DISCIPLINE RULE (AGY Audit Binding Guard)
- **Source of Truth**: Free float % and index-inclusion/exclusion claims (MSCI Emerging Markets, FTSE) **MUST** originate strictly from `collector_output` in the pipeline state (sourced from Sectors `shareholders_composition` / filings feed).
- **Unverified Guard**: If collector data is absent, conflicting, or marked unverified, the agent **MUST** emit:
  $$\text{"UNVERIFIED — requires IDX fact sheet/KSEI"}$$
- **Anti-Speculation**: Agents must **NEVER** invent a free-float percentage (e.g. arbitrarily writing 11.8% or 17.5%) and must **NEVER** assert index exclusion or disqualification (e.g. "MSCI <15% exclusion risk") based on unverified figures. Violating this rule triggers an immediate Critic **REJECT**.

### 4.3 Paragraph Template with AMMN Mining Slots

```markdown
**Sentimen Pasar: Arus Dana Institusi, Posisi Broker, dan Persepsi Risiko Sektor**

Persepsi pasar terhadap AMMN pada periode pelaporan mencerminkan [P3_MARKET_POSTURE] di kalangan investor institusional. Berdasarkan data transaksi pasar modal, investor asing mencatatkan akumulasi *net foreign buy* (jual bersih/beli bersih) kumulatif sebesar [P3_FOREIGN_FLOW_VAL] triliun dalam [P3_FOREIGN_FLOW_PERIOD], dengan konsentrasi beli terkonsentrasi pada broker institusi [P3_TOP_BUY_BROKERS]. Kinerja saham AMMN bergerak [P3_STOCK_VS_JCI_REL]% relatif terhadap Indeks Harga Saham Gabungan (IHSG) dan mencatatkan kenaikan/penurunan [P3_STOCK_ABS_PERF]% secara *year-to-date* (sejalan dengan dinamika pergerakan relatif pada Exhibit di Slide 1), mengungguli/tertinggal dari indeks sektor barang baku (IDXBASIC). Tone pemberitaan media finansial terpantau [P3_MEDIA_TONE] (skor sentimen Sectors: [P3_SECTORS_SENTIMENT_GAUGE]/100), didominasi oleh publikasi positif terkait [P3_PRIMARY_MEDIA_THEME], yang mengimbangi kekhawatiran temporer pasar mengenai [P3_SECONDARY_MEDIA_CONCERN]. Dari sisi konsensus analis institusional di sektor pertambangan logam, selera risiko (*risk appetite*) tercermin solid melalui sebaran peringkat konsensus yang mencakup [P3_CONSENSUS_BUY] Buy, [P3_CONSENSUS_HOLD] Hold, dan [P3_CONSENSUS_SELL] Sell. Terkait struktur kepemilikan saham publik dan potensi likuiditas indeks global, porsi *free float* saham beredar AMMN saat ini tercatat sebesar [P3_FREE_FLOAT_STATUS] (sumber: collector_output filings / KSEI); pasar memantau verifikasi batas likuiditas minimum tanpa melakukan spekulasi prematur terhadap penyesuaian bobot indeks MSCI.
```

### 4.4 Populated Illustrative Example (AMMN)
> **Sentimen Pasar: Arus Dana Institusi, Posisi Broker, dan Persepsi Risiko Sektor**  
> Persepsi pasar terhadap AMMN pada kuartal berjalan mencerminkan sentimen akumulasi yang terukur di kalangan pengelola dana institusional. Berdasarkan data pergerakan arus modal Sectors, pemodal asing mencatatkan beli bersih (*net foreign buy*) kumulatif sebesar Rp1,85 triliun dalam 3 bulan terakhir, dengan konsentrasi akumulasi dipimpin oleh broker institusi ZP, AK, dan CS. Saham AMMN mencatatkan kinerja relatif +14,8% terhadap IHSG secara *year-to-date* (sejalan dengan pergerakan harga pada grafik historis Slide 1), secara konsisten mengungguli indeks sektor barang baku (IDXBASIC). Tone pemberitaan media finansial domestik terpantau positif (indikator sentimen Sectors berada pada level 68/100), didorong oleh tercapainya target verifikasi teknis komisioning smelter Sumbawa dan kepastian kuota ekspor konsentrat, yang meredakan kekhawatiran pasar terkait batas waktu pengetatan ekspor mineral mentah nasional. Dari sisi konsensus riset institusional, selera risiko terhadap sektor tambang tembaga tetap konstruktif dengan agregat peringkat mencakup 14 Buy, 3 Hold, dan 1 Sell. Terkait kepemilikan saham publik dan potensi likuiditas indeks global, porsi *free float* saham beredar AMMN tercatat sebesar 17,2% berdasarkan data laporan registrasi pemegang efek (sumber: collector_output / KSEI per Juli 2026; status terverifikasi kepemilikan non-pengendali di bawah 5%), meredam narasi spekulatif terkait risiko likuiditas indeks acuan global.

---

## 5. Data Dependencies (Sectors Primary, Web Backup for Color Only)

### 5.1 Endpoint & Tool Mapping
Sectors API tools are **PRIMARY**. Agents must operate under the **Max 2 fetch calls per turn mindset** to preserve API credits and maximize analytical signal. Web search is strictly a secondary backup for qualitative narrative color, with mandatory `url` + `date` citation for every single claim.

| Data Metric / Need | Primary Sectors Endpoint / ADK Tool | Key Return Fields | Turn Mindset & Credit Discipline | Fallback Protocol on Error / Gap |
|---|---|---|---|---|
| **Macro Sector Overview & Breadth** | `fetch-subsector-report(sub_sector="metals-mining", sections="valuation,growth,companies")` | `subsector`, `growth_metrics`, `valuation_overview`, `companies` | Call 1 per turn max. Extract sector growth rate and copper-gold mining peer breadth. | If endpoint missing/down, call `web_search` (T1: BPS, Kemenperin, ESDM). Url+date mandatory. |
| **Commodity Benchmark Decks** | `fetch-news(symbols="AMMN", extension="idx")` + Sectors subsector narrative | `results[].title`, `results[].snippet`, `results[].url`, `results[].date` | Call 1 in news harvesting lane. Extract World Bank / CRU copper & gold price forecast references. | Web search backup: World Bank Commodity Markets Outlook / Consensus Economics. |
| **Foreign Capital Flows** | `fetch-foreign-flow(symbol="AMMN", start=DATE_START, end=DATE_END)` | `foreign_flow.net_foreign_buy_sell`, `foreign_flow.date`, `foreign_flow.cumulative` | Single call with 30-day or 90-day window. | KSEI monthly flow snapshot via web_search or report as provenance gap. |
| **Broker Concentration** | `fetch-broker-summary-top(symbol="AMMN", start=DATE_START, end=DATE_END, n_brokers=20)` | `top_buyers`, `top_sellers`, `broker_code`, `volume`, `value` | Paired with foreign flow call. Max 2 calls per turn. | If empty, omit specific broker codes and rely solely on foreign net aggregate. |
| **Stock & Index Trajectory** | `fetch-daily-transaction(symbol="AMMN", ...)` and `fetch-index-daily(index_code="COMPOSITE", ...)` | `close`, `date`, `volume`, `index_close` | Cache from Slide 1 collector data. Do not re-fetch if already in pipeline state. | Calculate relative % move vs JCI directly from cached time series. |
| **News Sentiment & Media Tone** | `fetch-news(symbols="AMMN", extension="idx")` | `sentiment_score`, `results[].url`, `results[].date`, `results[].content` | Max 8 items, 30-day trailing window. Extract sentiment dimension. | Web search (T1: Bisnis, Kontan, Investor Daily; T2: Reuters). Require exact url+date. |
| **Corporate Filings & Free Float** | `fetch-filings(symbol="AMMN")` + `shareholders_composition("AMMN")` | `shareholders_data`, `public_ownership_pct`, `filing_date`, `filing_type` | Retrieved once during collector phase. | If float missing or conflicted, emit `"UNVERIFIED — requires IDX fact sheet/KSEI"`. NEVER guess. |
| **Smelter Milestone & Capex** | `fetch-news` + `mining_company_financials("AMMN")` | `smelter_progress_pct`, `capex_spent`, `commissioning_target` | Cross-reference ESDM physical verification report in news feed. | Company disclosure / quarterly report via IDX filing feed. |

### 5.2 Provenance & Missing Key Discipline
1. **Zero Synthetic Tolerance**: If `SECTORS_API_KEY` is absent or the API responds with `source: "sectors_missing_key"`, the agent must emit `source: "sectors_missing_key"` and report a **Loud Data Gap**. Under NO circumstances may the agent fabricate statistics, invent broker codes, or simulate flow amounts.
2. **Provenance Preservation**: The internal audit payload MUST store `{claim, source_name, url, date}` for every factual assertion. In narrative prose, the agent explains the economic logic without rendering raw citation URLs into printable text.

---

## 6. Quantified-Catalyst Worksheet Format

To guarantee analytical rigour and auditability, all catalysts evaluated for P2 must be logged in a structured ledger before narrative synthesis.

### 6.1 Ledger Schema Definition
Each quantified catalyst in the pipeline state must conform to the following schema:

```json
{
  "catalyst_id": "CAT-AMMN-001",
  "category": "ESDM_REGULATION | SMELTER_TOLLING | ELANG_DEVELOPMENT | CONSOLIDATION",
  "headline": "Short descriptive catalyst title",
  "operational_driver": "Target parameter (e.g. Export Duty %, Grade %, Cathode Volume)",
  "baseline_parameter": "Baseline value prior to event",
  "shifted_parameter": "Expected or realized value post-event",
  "annual_financial_impact": {
    "metric": "EBITDA | NET_PROFIT | CASH_COST",
    "amount_usd_mn": 145.0,
    "amount_idr_bn": 2320.0
  },
  "calculation_basis": "Mathematical formula and explicit input assumptions",
  "confidence": "QUANTIFIED | EXPLICITLY_QUALITATIVE",
  "provenance": {
    "outlet": "Kementerian ESDM / Kontan",
    "url": "https://industri.kontan.co.id/...",
    "date": "2026-08-15"
  }
}
```

### 6.2 Pre-Populated Worksheet Entries (AMMN)

| ID | Category | Catalyst Description | Impact Metric & Amount | Calculation Basis & Assumptions | Confidence | Audit Provenance |
|---|---|---|---|---|---|---|
| **CAT-01** | ESDM Regulation | **Smelter Verification >90% & Export Duty Normalization**: Physical progress verified at 92.4%, lowering duty rate from 10.0% to 7.5%, transitioning to 0% at full commercial run. | **Cash Savings**: +US$145,0M (~Rp2.320B) on FY26F cash flows. | $\text{Concentrate Export (850k dmt)} \times \text{Price (\$2.275/dmt)} \times \Delta\text{Duty (7.5\% pts)}$. | **QUANTIFIED** | *Kontan / ESDM Decree*, 2026-07-28 |
| **CAT-02** | Smelter Tolling | **PT AMIN Smelter Commercial Start (900k dmt/yr)**: Internal refining into 222k tpa cathode and 18 tpa gold; elimination of international TC/RC & sea freight. | **EBITDA Expansion**: +US$85,0M net (~Rp1.360B), expanding EBITDA margin +280 bps. | $(\text{Saved Freight \$55/t} + \text{Saved TCRC \$80/t} - \text{Plant Opex \$68/t}) \times 900\text{k dmt} + \text{Acid Rev (\$18M)}$. | **QUANTIFIED** | *AMMN Corporate Disclosure*, 2026-08-10 |
| **CAT-03** | Mining Ops (Batu Hijau) | **Batu Hijau Phase 8 High-Grade Ore Release**: Mining pit transitions into peak copper/gold grade zone. | **EBITDA Boost**: +US$210,0M (~Rp3.360B) on higher payable metal. | $\Delta\text{Cu (+65M lbs)} \times \text{\$4,20/lb} \times 0,85 + \Delta\text{Au (+140k oz)} \times \text{\$2.350/oz} \times 0,90 - \text{Royalties}$. | **QUANTIFIED** | *AMMN Mine Plan & Report*, 2026-06-30 |
| **CAT-04** | Exploration / Capex | **Elang Porphyry Feasibility & AMDAL Approval**: Environmental permit secured for 1,4B ton resource development; capex paced post-smelter. | **Balance Sheet**: Net Debt / EBITDA capped at $\le 1,5\text{x}$; reserve life extended +25 years. | Multi-year capex paced at US$350M–450M/year funded by Phase 8 cash flow; avoids balance sheet stress. | **EXPLICITLY QUALITATIVE** (milestone pace confirmed; exact cash curves span multiple years). | *IDX Filing*, 2026-05-14 |
| **CAT-05** | Downstream Integration | **Domestic Sulfuric Acid Off-Take**: 830.000 tpa byproduct supplied to domestic fertilizer plants (Pupuk Indonesia). | **Revenue**: +US$40,0M–50,0M per annum. | $830\text{k tons acid} \times \text{Netback Price (\$55/ton)}$. Eliminates neutralization waste cost. | **QUANTIFIED** | *Bisnis Indonesia*, 2026-07-05 |

---

## 7. Market Sentiment Checklist

Before publishing P3 (Sentimen Pasar), the agent must audit the draft against this checklist:

- [ ] **Absolute Valuation Isolation**: Zero mention of Target Price, P/E ratio, PBV multiple, EV/EBITDA multiple, WACC, or Fair Value per share.
- [ ] **Flow Timeframe Rigour**: Foreign flow has a defined window (e.g. 1-month, 3-month, or YTD) and an explicit monetary value in IDR (Rp tn/bn) or USD.
- [ ] **Broker Concentration Grounding**: Identified broker desks (e.g., ZP, AK, CS) match live transactions from `fetch-broker-summary-top`. No fictitious names.
- [ ] **Relative Index Comparison**: Stock performance percentage relative to JCI and IDXBASIC/IDXMINING matches Slide 1 Exhibit calculation.
- [ ] **Media Tone Contextualized**: Tone (Positive/Neutral/Negative) is supported by a concrete narrative explanation (e.g., why smelter news offsets export ban concerns).
- [ ] **Consensus Count Verification**: Sell-side consensus breakdown (Buy / Hold / Sell) reflects institutional breadth without extrapolating individual firm target prices.
- [ ] **Float & Index Discipline Check**:
  - [ ] Free float % matches verified `collector_output`.
  - [ ] If float is absent or disputed, exactly `"UNVERIFIED — requires IDX fact sheet/KSEI"` is emitted.
  - [ ] Zero claims asserting MSCI/FTSE exclusion or inclusion unless corroborated by verified regulatory filings.

---

## 8. Peer Communication Protocol & Critic Hooks

### 8.1 Peer Communication Protocol (`peer_requests`)
The Industry & Macro agent cooperates with peer agents in parallel lanes (Collector, News Harvester, Modeler, Company Analyst, KPI Analyst). To prevent communication loops and credit exhaustion:
1. **State Inspection First**: Always inspect the existing execution state (`collector_output`, `news_output`, `kpi_output`) before initiating a request.
2. **Max 3 Requests Pattern**: An agent may submit at most **3** peer data requests across its execution cycle. Each request must specify:
   - `target_agent`: the designated peer agent (`collector`, `news_harvester`, or `kpi_analyst`).
   - `needed_fields`: explicit array of missing data keys (e.g. `["free_float_pct", "public_shareholders"]`).
   - `rationale`: institutional reason for the dependency (e.g. "Verifying float percentage for P3 sentiment compliance").
3. **Graceful Fallback**: If 3 requests have been dispatched or the target agent returns `null`/`sectors_missing_key`, the agent **must proceed with existing data** and disclose an explicit **provenance gap note** in the audit metadata.

#### Standard Peer Request Templates for AMMN Slide 2
- **Request 1 (to Collector)**:
  `request_peer_data(target="collector", needed_fields=["free_float_pct", "shareholders_composition", "subsector"], rationale="Verifying public shareholding for float and index inclusion discipline in P3")`
- **Request 2 (to News Harvester)**:
  `request_peer_data(target="news_harvester", needed_fields=["last_30d_news", "sentiment_score", "esdm_regulatory_updates"], rationale="Extracting citable url+date headlines for P2 catalysts and P3 media tone")`
- **Request 3 (to KPI Analyst)**:
  `request_peer_data(target="kpi_analyst", needed_fields=["batu_hijau_phase8_grades", "smelter_physical_progress", "c1_cash_cost"], rationale="Extracting operational baselines for P1 positioning and P2 catalyst quantification")`

### 8.2 Critic Hooks (Strict Acceptance Gate)
The QA Critic audits Slide 2 output against the following strict failure criteria. Any single violation results in an automatic **REJECT**:

1. **Exhibit Convention Check**:
   - Zero literal `Exhibit N` strings emitted in data payloads or narrative text.
   - Zero `id` fields (e.g. `"id": "Exhibit 1"`) present on supporting visual objects.
   - If an optional exhibit is attached, label is descriptive and positioned above; source line below is strictly `Source: Company, Team Estimates`.
2. **Renderer Furniture Check**:
   - Zero agent-emitted headers, dates, logos, dividers, footers, or page numbers.
3. **Valuation Boundary Enforcement**:
   - Any mention of Target Price, valuation multiples (P/E, P/BV, EV/EBITDA), discount rates, or fair value calculations in Slide 2 triggers an immediate **REJECT**.
4. **Catalyst Quantification Audit**:
   - Every catalyst listed in P2 must have an explicit formula, operational delta, and financial impact, or be explicitly stamped as **kualitatif** with justification. Unsubstantiated numbers are classified as synthetic and rejected.
5. **Float & Index Discipline Audit**:
   - Any assertion of free-float percentage not matching `collector_output` or asserting MSCI index exclusion without verified regulatory backing triggers an immediate **REJECT**.
6. **Provenance & Citation Audit**:
   - Every factual claim in P1, P2, and P3 must trace to a verified `url` + `date` in the audit payload.
   - Generic attribution (e.g. "menurut data analis", "dari sumber terpercaya") without provenance metadata is rejected.
7. **No Synthetic Data**:
   - Any synthetic filling following a `sectors_missing_key` response triggers an immediate **REJECT**.
