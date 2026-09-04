// report_single.typ — Institutional equity research report (RATU single ticker archetype)
#import "../common/theme.typ": *
#import "../common/cover.typ": *

#show: set-page-defaults

#let ticker = sys.inputs.at("ticker", default: "RATU")
#let default-data-path = "/home/fadil/projects/sectors-hackathon/scripts/fixtures/ratu_report_data.json"
#let data-path = sys.inputs.at("data_path", default: default-data-path)
#let data = json(data-path)

#let m = data.at("meta")
#let cover = data.at("cover").at("rating_box")
#let gate-verdict = data.at("gate-verdict", default: data.at("gate_verdict", default: none))
#let chart-dir = "/home/fadil/projects/sectors-hackathon/output/cache/render_" + lower(m.ticker) + "/charts"


#let PALETTE = (
  brand: rgb("#1d4ed8"),        // royal blue (energy/holding)
  brand_dark: rgb("#152c6e"),
  accent: rgb("#eff6ff"),
  ink: rgb("#101828"),
  muted: rgb("#475467"),
  line: rgb("#e4e7ec"),
  band: rgb("#f9fafb"),
  paper: rgb("#ffffff"),
  pos: rgb("#067647"),
  neg: rgb("#b42318"),
)

// Helper: visual placeholder for chart rendering
#let chart-placeholder(label, caption: "Engine Chart Renderer (IDX / yfinance)", height: 80pt, palette: PALETTE) = {
  block(
    width: 100%,
    height: height,
    fill: palette.band,
    stroke: (paint: palette.line, dash: "densely-dashed", thickness: 0.75pt),
    radius: 4pt,
    inset: 8pt,
    align(center + horizon)[
      #text(size: 8pt, weight: "bold", fill: palette.brand_dark)[#label]
      #v(3pt)
      #text(size: 6.5pt, fill: palette.muted, style: "italic")[#caption]
    ]
  )
}

// =====================================================================
// PAGE 1 — COVER & SNAPSHOT
// =====================================================================
#page-wrap("RESEARCH — Equity Report", "31 Agt 2026", "RATU", 1, PALETTE, [
  #grid(
    columns: (2fr, 1.15fr),
    column-gutter: 14pt,
    [
      #text(size: T_SMALL, fill: PALETTE.muted, tracking: 0.12em, weight: "bold")[
        INITIATION · ENERGI — PURE-PLAY HOLDING
      ]
      #v(4pt)
      #text(size: T_COVER_TITLE, weight: "bold", fill: PALETTE.brand_dark)[
        Ratu Prabu Energi
      ]
      #v(2pt)
      #text(size: 13pt, weight: "bold", fill: PALETTE.muted)[
        RATU · IDX
      ]
      #v(8pt)

      #card(PALETTE)[
        #text(weight: "bold", fill: PALETTE.ink)[Executive Summary / Key Points]
        #v(1pt)
        #text(size: 6pt, style: "italic", fill: PALETTE.muted)[Core investment thesis, rating stance, target price derivation, and operational highlights.]
        #v(2.5pt)
        #text(size: T_BODY)[
          Inisiasi liputan dengan Investment Recommendation *BUY* dan target harga *Rp 7.880* (+27,1% upside). Arus kas Lapangan Banyu Urip (Blok Cepu) menopang marjin EBITDA \~49,6%, efisiensi lifting cost USD 4,85/bbl, dan neraca net cash tanpa utang berbunga.
        ]
      ]

      #v(8pt)
      #exhibit-header("Exhibit 1", "Struktur Kepemilikan Saham", "KSEI & IDX")
      #v(2pt)
      #fin-table(
        ("Pemegang Saham", "Porsi (%)", "Status"),
        (
          ("PT Ratu Energi Tuban Jaya (RETJ)", "45,0%", "Pengendali"),
          ("PT Petro Java Utama Cepu (PJUC)", "23,8%", "Strategis"),
          ("Publik (Free Float)", "31,2%", "Non-Warkat"),
        ),
        palette: PALETTE,
      )

      #v(8pt)
      #exhibit-header("Exhibit 2", "Kinerja Harga vs IHSG (YTD)", "IDX & yfinance (RATU.JK vs ^JKSE)")
      #v(2pt)
      #chart-placeholder("Kinerja Harga RATU (+18,4% YTD) vs IHSG (+12,2% YTD)", caption: "Performa Relatif YTD: Outperform +6,2% · Sumber: IDX & yfinance", height: 75pt, palette: PALETTE)
    ],
    [
      #rating-box(
        cover.action,
        str(cover.tp),
        str(cover.price),
        cover.upside_pct,
        prev-tp: if cover.at("prev_tp", default: none) != none { str(cover.prev_tp) } else { none },
        palette: PALETTE,
      )

      #v(4pt)
      #method-selection-panel(gate-verdict, palette: PALETTE)

      #v(4pt)
      #card(PALETTE)[
        #text(size: T_SMALL, weight: "bold", fill: PALETTE.muted)[INFORMASI SAHAM]
        #v(1pt)
        #text(size: 5.5pt, style: "italic", fill: PALETTE.muted)[Market trading metrics, liquidity statistics, and shareholding structure profile.]
        #v(2.5pt)
        #let sh = data.cover.at("shares", default: (:))
        #grid(
          columns: (1fr, auto),
          row-gutter: 2.8pt,
          text(size: 6.8pt)[Harga Kini], text(size: 6.8pt, weight: "bold")[Rp #cover.price],
          text(size: 6.8pt)[Target Harga], text(size: 6.8pt, weight: "bold")[Rp #cover.tp],
          text(size: 6.8pt)[Saham Beredar], text(size: 6.8pt, weight: "bold")[#sh.at("outstanding", default: 2.71) Miliar],
          text(size: 6.8pt)[Kapitalisasi Pasar], text(size: 6.8pt, weight: "bold")[Rp 16,80 T],
          text(size: 6.8pt)[Free Float], text(size: 6.8pt, weight: "bold")[#sh.at("free_float_pct", default: 31.2)%],
          text(size: 6.8pt)[52-Wk Range], text(size: 6.8pt, weight: "bold")[4.500 - 8.200],
          text(size: 6.8pt)[Rerata Nilai 3M], text(size: 6.8pt, weight: "bold")[Rp 14,2 M/hari],
          text(size: 6.8pt)[Klasifikasi Indeks], text(size: 6.8pt, weight: "bold")[MSCI / IDX80 / JII],
        )
      ]
    ]
  )
])

#pagebreak()

// =====================================================================
// PAGE 2 — KPI HERO (OPERATIONAL METRICS FOR ENERGY PURE-PLAY)
// =====================================================================
#page-wrap("RESEARCH — Equity Report", "31 Agt 2026", "RATU", 2, PALETTE, [
  #section-header(1, "Metrik Operasional Kunci (KPI Hero)", PALETTE)
  
  #text(size: T_BODY)[
    Kinerja operasional RATU ditopang oleh keikutsertaan dalam Lapangan Banyu Urip (Blok Cepu), salah satu aset hulu migas paling produktif dan efisien di Asia Tenggara. Fasilitas pemrosesan pusat (CPF) beroperasi dengan keandalan tinggi dan biaya lifting terendah di kelasnya.
  ]
  #v(6pt)

  #grid(
    columns: (1fr, 1fr, 1fr, 1fr),
    gutter: 8pt,
    card(PALETTE)[
      #text(size: 6.8pt, fill: PALETTE.muted, weight: "bold")[PRODUKSI CEPU]
      #v(2pt)
      #text(size: 13pt, weight: "black", fill: PALETTE.brand_dark)[169k]
      #text(size: 7pt, weight: "bold")[ BOPD]
      #v(1pt)
      #text(size: 6.5pt, fill: PALETTE.pos, weight: "bold")[+11,2% YoY (vs 152k)]
    ],
    card(PALETTE)[
      #text(size: 6.8pt, fill: PALETTE.muted, weight: "bold")[LIFTING COST]
      #v(2pt)
      #text(size: 13pt, weight: "black", fill: PALETTE.brand_dark)[\$4,85]
      #text(size: 7pt, weight: "bold")[ /bbl]
      #v(1pt)
      #text(size: 6.5pt, fill: PALETTE.pos, weight: "bold")[Top 10% Terendah RI]
    ],
    card(PALETTE)[
      #text(size: 6.8pt, fill: PALETTE.muted, weight: "bold")[REALISASI ICP]
      #v(2pt)
      #text(size: 13pt, weight: "black", fill: PALETTE.brand_dark)[\$78,5]
      #text(size: 7pt, weight: "bold")[ /bbl]
      #v(1pt)
      #text(size: 6.5pt, fill: PALETTE.muted)[Premium vs Minas]
    ],
    card(PALETTE)[
      #text(size: 6.8pt, fill: PALETTE.muted, weight: "bold")[CADANGAN 1P]
      #v(2pt)
      #text(size: 13pt, weight: "black", fill: PALETTE.brand_dark)[142]
      #text(size: 7pt, weight: "bold")[ MMBOE]
      #v(1pt)
      #text(size: 6.5pt, fill: PALETTE.muted)[RLI \~11,4 Tahun]
    ],
  )

  #v(8pt)
  #exhibit-header("Exhibit 3", "Trajektori Parameter Operasional Hulu Migas", "SKK Migas & Laporan KKKS")
  #v(2pt)
  #fin-table(
    ("Parameter Operasional", "FY22A", "FY23A", "FY24A", "FY25A", "FY26F", "Satuan"),
    (
      ("Produksi Harian Rata-rata Cepu", "162.000", "158.000", "152.000", "169.000", "165.000", "BOPD"),
      ("Biaya Lifting (Opex per Barel)", "5,30", "5,20", "5,10", "4,85", "4,95", "USD/bbl"),
      ("Realisasi Rata-rata ICP", "97,00", "82,40", "80,10", "78,50", "76,00", "USD/bbl"),
      ("Domestic Market Obligation (DMO)", "25,0%", "25,0%", "25,0%", "25,0%", "25,0%", "Kepatuhan"),
      ("Uptime Fasilitas Pemrosesan (CPF)", "98,8%", "99,1%", "99,3%", "99,4%", "99,2%", "% waktu"),
      ("Tingkat Keberhasilan Infill Well", "88%", "90%", "92%", "94%", "92%", "% sukses"),
    ),
    palette: PALETTE,
  )

  #v(8pt)
  #exhibit-header("Exhibit 4", "Karakteristik Aset Hulu & Infrastruktur Distribusi", "Kementerian ESDM & Operator")
  #v(2pt)
  #fin-table(
    ("Komponen Aset", "Deskripsi & Kapasitas", "Mitra & Status Operasional"),
    (
      ("Area Konsesi", "Blok Cepu (Jawa Timur & Jawa Tengah)", "Kontrak PSC berlaku hingga 2031"),
      ("Operator Utama", "ExxonMobil Cepu Ltd (45%), Pertamina (45%), BUMD (10%)", "Operasional kelas dunia, standar HSSE tinggi"),
      ("Fasilitas CPF", "Kapasitas desain 220.000 BOPD di Bojonegoro", "Operasi stabil dengan uptime konsisten >99%"),
      ("Jalur Pipa & FSO", "Pipa darat-laut 72 km menuju FSO Gagak Rimang Tuban", "Kapasitas tampung 1,7 juta barel minyak mentah"),
    ),
    palette: PALETTE,
  )

  #v(8pt)
  #card(PALETTE)[
    #text(weight: "bold", fill: PALETTE.ink)[Keunggulan Biaya Operasional (Economic Moat)]
    #v(2pt)
    #text(size: 7.5pt)[
      Biaya lifting sebesar USD 4,85/bbl menempatkan RATU di kuartil terbawah struktur biaya produsen migas nasional (rerata industri USD 12-16/bbl). Keunggulan ini memberikan fleksibilitas arus kas yang tinggi bahkan dalam skenario penurunan harga minyak global hingga USD 50/bbl.
    ]
  ]
])

#pagebreak()

// =====================================================================
// PAGE 3 — FINANCIAL HIGHLIGHTS & INVESTMENT THESIS
// =====================================================================
#page-wrap("RESEARCH — Equity Report", "31 Agt 2026", "RATU", 3, PALETTE, [
  #section-header(2, "Sorotan Keuangan & Tesis Investasi", PALETTE)

  #exhibit-header("Exhibit 5", "Financial Highlights 6 Tahun (FY23A - FY28F)", "Laporan Keuangan RATU (IDX), data diolah")
  #v(2pt)
  #fin-table(
    ("Metrik Finansial (Rp bn)", "FY23A", "FY24A", "FY25A", "FY26F", "FY27F", "FY28F"),
    (
      ("Pendapatan Bersih", "1.150", "1.290", "1.122", "1.180", "1.245", "1.310"),
      ("Pertumbuhan Penjualan (%)", "+8,5%", "+12,2%", "-13,0%", "+5,2%", "+5,5%", "+5,2%"),
      ("EBITDA", "580", "610", "540", "585", "620", "658"),
      ("Marjin EBITDA (%)", "50,4%", "47,3%", "48,1%", "49,6%", "49,8%", "50,2%"),
      ("Laba Bersih", "365", "402", "355", "390", "425", "462"),
      ("EPS (Rp/saham)", "134,7", "148,3", "131,0", "143,9", "156,8", "170,5"),
      ("P/E (x)", "46,0x", "41,8x", "47,3x", "43,1x", "39,5x", "36,4x"),
      ("ROE (%)", "72,5%", "88,0%", "41,0%", "30,0%", "28,5%", "27,2%"),
      ("Net Debt / EBITDA (x)", "Net Cash", "Net Cash", "Net Cash", "Net Cash", "Net Cash", "Net Cash"),
    ),
    palette: PALETTE,
  )

  #v(8pt)
  #text(size: T_H3, weight: "bold", fill: PALETTE.brand_dark)[4 Pilar Tesis Investasi]
  #v(4pt)

  #grid(
    columns: (1fr, 1fr),
    gutter: 7pt,
    card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.ink)[1. Arus Kas Resilien & Marjin EBITDA \~50%]
      #v(2pt)
      #text(size: 7.2pt)[
        Lifting cost rendah (USD 4,85/bbl) dan efisiensi opex menjaga marjin EBITDA di kisaran 49,6%–50,2%. Fluktuasi harga ICP tertopang natural hedge valuta asing dan struktur biaya tetap yang ramping.
      ]
    ],
    card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.ink)[2. Mesin Kas Bebas (FCF Generation)]
      #v(2pt)
      #text(size: 7.2pt)[
        Tanpa kebutuhan capex ekspansi kilang yang berat, konversi EBITDA ke Free Cash Flow mencapai >70%. FCF tahunan diproyeksikan rata-rata Rp 410–455 miliar pada FY26F–FY28F.
      ]
    ],
    card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.ink)[3. Neraca Kas Bersih Tanpa Utang]
      #v(2pt)
      #text(size: 7.2pt)[
        Posisi kas mencapai Rp 500 miliar tanpa beban utang berbunga. Struktur neraca zero debt membebaskan perusahaan dari tekanan kenaikan suku bunga acuan dan risiko refinansial.
      ]
    ],
    card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.ink)[4. Program Infill Well Menahan Decline]
      #v(2pt)
      #text(size: 7.2pt)[
        Pelaksanaan infill drilling dan workover sumur di Blok Cepu berhasil membatasi natural decline rate di level \~8%/tahun, memperpanjang masa plateau produksi hingga dekade berikutnya.
      ]
    ],
  )
])

#pagebreak()

// =====================================================================
// PAGE 4 — VALUATION (DCF, MULTIPLES, BLENDED & BANDS)
// =====================================================================
#page-wrap("RESEARCH — Equity Report", "31 Agt 2026", "RATU", 4, PALETTE, [
  #section-header(3, "Valuation Methodology & Hasil Valuasi", PALETTE)

  #grid(
    columns: (1.15fr, 1fr),
    column-gutter: 10pt,
    [
      #text(size: 9.5pt, weight: "bold", fill: PALETTE.brand_dark)[Metode 1: Discounted Cash Flow (DCF)]
      #v(2pt)
      #text(size: 7.2pt, fill: PALETTE.muted)[
        Asumsi: WACC 8,40%, Terminal Growth (g) 5,00%, Beta 0,70, Rf 6,20%, ERP 6,90%
      ]
      #v(4pt)
      #exhibit-header("Exhibit 6", "Proyeksi Arus Kas Bebas (FCFF)", "Engine DCF")
      #v(2pt)
      #fin-table(
        ("Komponen DCF (Rp bn)", "FY26F", "FY27F", "FY28F", "FY29F"),
        (
          ("Free Cash Flow (FCF)", "410", "432", "455", "478"),
          ("Discount Factor", "0,922", "0,851", "0,785", "0,724"),
          ("Present Value FCF", "378", "368", "357", "346"),
        ),
        palette: PALETTE,
      )
      #v(4pt)
      #card(PALETTE)[
        #grid(
          columns: (1fr, auto),
          row-gutter: 3pt,
          text(size: 7pt)[PV Arus Kas Eksplisit], text(size: 7pt, weight: "bold")[Rp 1.449 bn],
          text(size: 7pt)[PV Nilai Terminal (TV)], text(size: 7pt, weight: "bold")[Rp 10.413 bn],
          text(size: 7pt)[Enterprise Value (EV)], text(size: 7pt, weight: "bold")[Rp 11.862 bn],
          text(size: 7pt)[Kas Bersih / (Utang)], text(size: 7pt, weight: "bold")[+Rp 500 bn],
          text(size: 7.5pt, weight: "bold")[Nilai Wajar DCF per Saham], text(size: 7.5pt, weight: "black", fill: PALETTE.brand_dark)[Rp 7.880],
        )
      ]
    ],
    [
      #text(size: 9.5pt, weight: "bold", fill: PALETTE.brand_dark)[Metode 2: Multiple EV/EBITDA]
      #v(2pt)
      #text(size: 7.2pt, fill: PALETTE.muted)[
        Target multiple 22,6x berdasarkan rata-rata historis 3 tahun siklus normal.
      ]
      #v(4pt)
      #fin-table(
        ("Parameter", "Nilai", "Satuan"),
        (
          ("Target EV/EBITDA", "22,6", "x"),
          ("EBITDA FY26F", "585", "Rp bn"),
          ("Implied EV", "13.221", "Rp bn"),
          ("Fair Value EV/EBITDA", "6.960", "Rp/saham"),
        ),
        palette: PALETTE,
      )

      #v(6pt)
      #text(size: 9.5pt, weight: "bold", fill: PALETTE.brand_dark)[Valuasi Blended (60/40)]
      #v(2pt)
      #fin-table(
        ("Metode", "Bobot", "Fair Value"),
        (
          ("DCF (WACC 8,4%, g 5,0%)", "60%", "Rp 7.880"),
          ("EV/EBITDA (22,6x)", "40%", "Rp 6.960"),
          ("Target Price (TP 12M)", "100%", "Rp 7.880"),
        ),
        palette: PALETTE,
      )
    ]
  )

  #v(8pt)
  #exhibit-header("Exhibit 7", "Pita Valuasi Historis P/BV 3-Tahun (STD±2)", "IDX & Analisis Data")
  #v(2pt)
  #fin-table(
    ("Deviasi Standar", "P/BV (x)", "Implied Price", "Interpretasi Valuasi"),
    (
      ("STD +2 (Batas Atas Ekstrem)", "2,90x", "Rp 9.850", "Overvalued Ekstrem"),
      ("STD +1 (Batas Atas)", "2,50x", "Rp 8.490", "Overvalued Moderat"),
      ("Rerata 3 Tahun (Mean)", "2,10x", "Rp 7.130", "Rentang Nilai Wajar"),
      ("STD -1 (Batas Bawah)", "1,70x", "Rp 5.770", "Undervalued Menarik"),
      ("STD -2 (Batas Bawah Ekstrem)", "1,30x", "Rp 4.410", "Undervalued Ekstrem"),
      ("Posisi Harga Kini", "1,47x", "Rp 6.200", "BELOW AVERAGE (Peluang Akumulasi)"),
    ),
    palette: PALETTE,
  )

  #v(6pt)
  #card(PALETTE)[
    #text(weight: "bold", fill: PALETTE.ink)[Kesimpulan Valuasi]
    #v(2pt)
    #text(size: 7.3pt)[
      Harga saham kini Rp 6.200 memperdagangkan RATU pada kelipatan P/BV 1,47x (di bawah rata-rata historis 2,10x). Target harga Rp 7.880 memberikan ruang apresiasi +27,1% (BUY), didukung profil hasil kas bebas yang superior.
    ]
  ]
])

#pagebreak()

// =====================================================================
// PAGE 5 — COMPREHENSIVE DCF DEEP DIVE
// =====================================================================
#page-wrap("RESEARCH — Equity Report", "31 Agt 2026", "RATU", 5, PALETTE, [
  #section-header(4, "Analisis DCF Komprehensif", PALETTE)
  
  #text(size: 7.2pt, fill: PALETTE.muted)[
    Discounted Cash Flow (DCF) Model — Model deterministik multi-periode mengevaluasi nilai intrinsik ekuitas melalui proyeksi arus kas bebas eksplisit (FCFF) dan nilai terminal, dilengkapi Cost of Capital Build, Sensitivity Analysis 5x5, dan Scenario Analysis (Bear / Base / Bull).
  ]
  #v(6pt)

  #exhibit-header("Exhibit 8", "Cost of Capital Build", "Model CAPM & SBN 10Y")
  #v(2pt)
  #fin-table(
    ("Komponen WACC", "Nilai", "Metodologi / Sumber"),
    (
      ("Risk-Free Rate (Rf)", "7,00%", "Yield Obligasi Pemerintah SBN 10Y"),
      ("Equity Risk Premium (ERP)", "6,90%", "Damodaran Indonesia ERP 2026"),
      ("Beta Raw & Adjusted (Blume)", "0,700", "Regresi mingguan 3Y vs IHSG"),
      ("Biaya Ekuitas (Cost of Equity - Ke)", "11,83%", "Ke = Rf + Beta * ERP"),
      ("Biaya Utang Sebelum Pajak (Kd)", "9,00%", "Rf + 200 bps (Floor utang korporasi)"),
      ("Tarif Pajak Efektif", "22,00%", "UU Harmonisasi Perpajakan (HPP)"),
      ("Biaya Utang Setelah Pajak", "7,02%", "Kd * (1 - Tax Rate)"),
      ("Bobot Ekuitas / Utang", "100% / 0%", "Struktur Modal Bersih (Net Cash)"),
      ("WACC Final Diterapkan", "11,83%", "We * Ke + Wd * Kd_aftertax"),
    ),
    palette: PALETTE,
  )

  #v(6pt)
  #exhibit-header("Exhibit 9", "Sensitivity Analysis — WACC vs Terminal Growth (g)", "Engine Sensitivitas 5x5")
  #v(2pt)
  #fin-table(
    ("WACC \\ g", "4,50%", "4,75%", "5,00% (Base)", "5,25%", "5,50%"),
    (
      ("10,83%", "Rp 4.979 (+18,5%)", "Rp 5.134 (+22,2%)", "Rp 5.303 (+26,3%)", "Rp 5.487 (+30,6%)", "Rp 5.688 (+35,4%)"),
      ("11,33%", "Rp 4.631 (+10,3%)", "Rp 4.762 (+13,4%)", "Rp 4.903 (+16,7%)", "Rp 5.055 (+20,4%)", "Rp 5.221 (+24,3%)"),
      ("11,83% (Base)", "Rp 4.331 (+3,1%)", "Rp 4.442 (+5,8%)", "Rp 4.562 (+8,6%)", "Rp 4.690 (+11,7%)", "Rp 4.828 (+15,0%)"),
      ("12,33%", "Rp 4.070 (-3,1%)", "Rp 4.165 (-0,8%)", "Rp 4.267 (+1,6%)", "Rp 4.376 (+4,2%)", "Rp 4.493 (+7,0%)"),
      ("12,83%", "Rp 3.840 (-8,6%)", "Rp 3.922 (-6,6%)", "Rp 4.010 (-4,5%)", "Rp 4.104 (-2,3%)", "Rp 4.204 (+0,1%)"),
    ),
    palette: PALETTE,
  )

  #v(6pt)
  #grid(
    columns: (1fr, 1.15fr),
    column-gutter: 8pt,
    [
      #exhibit-header("Exhibit 10", "Scenario Analysis (Bear / Base / Bull)", "Engine Skenario")
      #v(2pt)
      #fin-table(
        ("Scenario", "Nilai Wajar", "Investment Recommendation"),
        (
          ("BEAR (Rev +6%, EBIT 29%)", "Rp 3.567", "SELL (-15,1%)"),
          ("BASE (Rev +10%, EBIT 32%)", "Rp 4.562", "HOLD (+8,6%)"),
          ("BULL (Rev +14%, EBIT 35%)", "Rp 5.812", "BUY (+38,4%)"),
        ),
        palette: PALETTE,
      )
    ],
    [
      #exhibit-header("Exhibit 11", "Jembatan Nilai EV ke Ekuitas", "Bridge Waterfall")
      #v(2pt)
      #fin-table(
        ("Komponen Jembatan", "Nilai (Rp bn)", "Keterangan"),
        (
          ("PV Explicit + PV Terminal", "11.862", "Enterprise Value"),
          ("(+) Kas & Setara Kas", "+500", "Likuiditas"),
          ("(-) Total Utang Berbunga", "-0", "Bebas Utang"),
          ("Implied Equity Value", "12.362", "Nilai Bersih"),
        ),
        palette: PALETTE,
      )
    ]
  )
])

#pagebreak()

// =====================================================================
// PAGE 6 — FINANCIAL STATEMENTS 6Y (INCOME, BALANCE & CASHFLOW)
// =====================================================================
#page-wrap("RESEARCH — Equity Report", "31 Agt 2026", "RATU", 6, PALETTE, [
  #section-header(5, "Laporan Keuangan & Rasio Finansial 6 Tahun", PALETTE)

  #exhibit-header("Exhibit 12", "Laporan Laba Rugi Komprehensif (Rp Miliar)", "Laporan Keuangan IDX & Proyeksi")
  #v(2pt)
  #fin-table(
    ("Akun Laba Rugi", "FY23A", "FY24A", "FY25A", "FY26F", "FY27F", "FY28F"),
    (
      ("Pendapatan Bersih", "1.150", "1.290", "1.122", "1.180", "1.245", "1.310"),
      ("Beban Pokok Pendapatan (COGS)", "-480", "-520", "-470", "-492", "-516", "-540"),
      ("Laba Kotor", "670", "770", "652", "688", "729", "770"),
      ("Beban Penjualan & Administrasi", "-90", "-160", "-112", "-103", "-109", "-112"),
      ("EBITDA", "580", "610", "540", "585", "620", "658"),
      ("Depresiasi & Amortisasi", "-110", "-125", "-118", "-132", "-144", "-154"),
      ("Laba Usaha (EBIT)", "470", "485", "422", "453", "476", "504"),
      ("Penghasilan Bunga Bersih", "+12", "+18", "+22", "+25", "+28", "+31"),
      ("Laba Sebelum Pajak (EBT)", "482", "503", "444", "478", "504", "535"),
      ("Beban Pajak Penghasilan", "-117", "-101", "-89", "-88", "-79", "-73"),
      ("Laba Bersih Tahun Berjalan", "365", "402", "355", "390", "425", "462"),
    ),
    palette: PALETTE,
  )

  #v(6pt)
  #exhibit-header("Exhibit 13", "Neraca Keuangan Ringkas (Rp Miliar)", "Laporan Keuangan IDX & Proyeksi")
  #v(2pt)
  #fin-table(
    ("Pos Neraca", "FY23A", "FY24A", "FY25A", "FY26F", "FY27F", "FY28F"),
    (
      ("Kas & Setara Kas", "320", "410", "465", "500", "560", "640"),
      ("Piutang Usaha & Lancar Lain", "187", "208", "184", "194", "203", "212"),
      ("Total Aset Lancar", "507", "618", "649", "694", "763", "852"),
      ("Aset Tetap & Hulu Migas", "1.120", "1.080", "1.020", "1.086", "1.157", "1.228"),
      ("Aset Tidak Lancar Lainnya", "185", "192", "195", "200", "205", "210"),
      ("Total Aset", "1.812", "1.890", "1.864", "1.980", "2.125", "2.290"),
      ("Liabilitas Jangka Pendek", "165", "185", "162", "170", "178", "186"),
      ("Total Liabilitas", "247", "275", "247", "258", "269", "280"),
      ("Total Ekuitas", "1.565", "1.615", "1.617", "1.722", "1.856", "2.010"),
    ),
    palette: PALETTE,
  )

  #v(6pt)
  #exhibit-header("Exhibit 14", "Rasio Keuangan & Efisiensi", "Perhitungan Analis")
  #v(2pt)
  #fin-table(
    ("Rasio Kunci", "FY23A", "FY24A", "FY25A", "FY26F", "FY27F", "FY28F"),
    (
      ("Marjin Laba Kotor (%)", "58,3%", "59,7%", "58,1%", "58,3%", "58,6%", "58,8%"),
      ("Marjin EBITDA (%)", "50,4%", "47,3%", "48,1%", "49,6%", "49,8%", "50,2%"),
      ("Marjin Laba Bersih (%)", "31,7%", "31,2%", "31,6%", "33,1%", "34,1%", "35,3%"),
      ("Imbal Hasil Ekuitas (ROE)", "72,5%", "88,0%", "41,0%", "30,0%", "28,5%", "27,2%"),
      ("Imbal Hasil Aset (ROA)", "20,1%", "21,3%", "19,0%", "19,7%", "20,0%", "20,2%"),
      ("Current Ratio (x)", "3,07x", "3,34x", "4,01x", "4,08x", "4,29x", "4,58x"),
    ),
    palette: PALETTE,
  )
])

#pagebreak()

// =====================================================================
// PAGE 7 — PEERS, RISKS, RATING GUIDE & DISCLAIMER
// =====================================================================
#page-wrap("RESEARCH — Equity Report", "31 Agt 2026", "RATU", 7, PALETTE, [
  #section-header(6, "Peer Comparison & Investment Risks", PALETTE)

  #exhibit-header("Exhibit 15", "Peer Comparison — Emiten Sektor Energi Terbuka (IDX Peers)", "IDX & Bloomberg")
  #v(2pt)
  #fin-table(
    ("Ticker", "Market Cap", "P/E (x)", "EV/EBITDA", "P/BV (x)", "ROE (%)", "Gearing"),
    (
      ("RATU", "Rp 16,8 T", "42,7x", "22,6x", "1,47x", "30,0%", "Net Cash"),
      ("MEDC", "Rp 34,2 T", "8,9x", "4,2x", "1,15x", "22,0%", "1,42x"),
      ("ENRG", "Rp 8,9 T", "12,4x", "5,1x", "0,92x", "15,0%", "0,85x"),
      ("ELSA", "Rp 4,8 T", "7,6x", "3,4x", "0,81x", "14,2%", "Net Cash"),
      ("PGAS", "Rp 38,6 T", "8,1x", "3,9x", "0,88x", "12,8%", "0,45x"),
      ("Rerata Peers", "Rp 20,7 T", "15,9x", "7,8x", "1,05x", "18,8%", "0,54x"),
    ),
    palette: PALETTE,
  )

  #v(6pt)
  #text(size: 9pt, weight: "bold", fill: PALETTE.brand_dark)[Investment Risks]
  #v(3pt)
  #grid(
    columns: (1fr, 1fr),
    gutter: 6pt,
    card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.neg)[1. Fluktuasi Harga Minyak (ICP)]
      #v(1pt)
      #text(size: 6.8pt)[
        Penurunan ICP di bawah USD 60/bbl berpotensi menekan pendapatan, meski lifting cost rendah USD 4,85/bbl memberi bantalan impas yang kuat.
      ]
    ],
    card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.neg)[2. Ketergantungan Operator Lapangan]
      #v(1pt)
      #text(size: 6.8pt)[
        Kinerja lifting bergantung pada operasional ExxonMobil Cepu Ltd dan keandalan pipa distribusi ke FSO Gagak Rimang.
      ]
    ],
    card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.neg)[3. Regulasi Domestik & DMO]
      #v(1pt)
      #text(size: 6.8pt)[
        Perubahan formula Domestic Market Obligation atau kebijakan perpajakan hulu dapat mempengaruhi marjin bersih realisasi.
      ]
    ],
    card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.neg)[4. Penurunan Cadangan Alami]
      #v(1pt)
      #text(size: 6.8pt)[
        Natural decline rate lapangan dewasa (\~8%/thn) menuntut kelanjutan infill drilling dan workover sumur secara teratur.
      ]
    ],
  )

  #v(6pt)
  #card(PALETTE)[
    #text(size: 7pt, weight: "bold", fill: PALETTE.brand_dark)[PANDUAN RATING REKOMENDASI (INVESTMENT RECOMMENDATION)]
    #v(2pt)
    #text(size: 6.5pt)[
      - *BUY*: Ekspektasi total return > +15% dalam 12 bulan (eks-dividen).
      - *HOLD*: Ekspektasi total return -10% s/d +15% dalam 12 bulan.
      - *SELL*: Ekspektasi total return \< -15% dalam 12 bulan.
      - *NOT RATED*: Saham di luar cakupan riset reguler / tidak memiliki rating aktif.
    ]
  ]

  #v(6pt)
  #card(PALETTE)[
    #text(size: 7pt, weight: "bold", fill: PALETTE.ink)[INFORMASI, BUKAN SARAN INVESTASI (OJK COMPLIANCE)]
    #v(2pt)
    #text(size: 6.2pt, fill: PALETTE.muted)[
      Laporan ini diproduksi untuk tujuan riset dan edukasi pasar modal semata. Seluruh angka dan analisis didasarkan pada data publik laporan keuangan emiten, keterbukaan informasi IDX, dan SKK Migas. Laporan ini bukan merupakan penawaran atau rekomendasi untuk membeli atau menjual efek tertentu. Keputusan investasi sepenuhnya tanggung jawab investor. Kinerja historis bukan indikasi masa depan.
    ]
  ]

  #v(4pt)
  #text(size: 6pt, fill: PALETTE.muted, style: "italic")[
    Disiapkan oleh RESEARCH — Sectors Hackathon 2026 · Tanggal 31 Agt 2026 · Ticker: RATU.JK · Bahasa: ID
  ]
])

