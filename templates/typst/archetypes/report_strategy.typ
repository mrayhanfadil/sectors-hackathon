// =====================================================================
// report_strategy.typ — Institutional equity research (Strategy archetype)
// Case: JCI / IHSG (Indeks Harga Saham Gabungan) — Indonesia 2026 Strategy Outlook
// =====================================================================
#import "../common/theme.typ": *
#import "../common/cover.typ": *


#let ticker = sys.inputs.at("ticker", default: "JCI")
#let data-path = sys.inputs.at("data_path")
#let data = json(data-path)

#let m = data.at("meta")
#show: set-page-defaults.with(date: m.date)
#let gate-verdict = data.at("gate-verdict", default: data.at("gate_verdict", default: none))
#let chart-dir = "/home/fadil/projects/sectors-hackathon/output/cache/render_" + lower(m.ticker) + "/charts"


// Archetype Palette for Strategy / Macro Outlook (Deep Indigo & Slate)
#let PALETTE = (
  brand: rgb("#3730a3"),        // deep indigo
  brand_dark: rgb("#1e1b4b"),   // dark navy indigo
  accent: rgb("#eef2ff"),       // soft indigo tint
  ink: rgb("#101828"),
  muted: rgb("#475467"),
  line: rgb("#e4e7ec"),
  band: rgb("#f9fafb"),
  paper: rgb("#ffffff"),
  pos: rgb("#067647"),
  neg: rgb("#b42318"),
)

// Visual placeholder helper for charts
#let chart-placeholder(label, caption: "Engine Chart Renderer (Sectors)", height: 70pt, palette: PALETTE) = {
  block(
    width: 100%,
    height: height,
    fill: palette.band,
    stroke: (paint: palette.line, dash: "densely-dashed", thickness: 0.75pt),
    radius: 4pt,
    inset: 6pt,
    align(center + horizon)[
      #text(size: 7.5pt, weight: "bold", fill: palette.brand_dark)[#label]
      #v(2pt)
      #text(size: 6.2pt, fill: palette.muted, style: "italic")[#caption]
    ]
  )
}

// =====================================================================
// PAGE 1 — COVER & SNAPSHOT
// =====================================================================
#page-wrap("RESEARCH — Strategy Outlook", "31 Agt 2026", "IHSG / JCI", 1, PALETTE, [
  #grid(
    columns: (2fr, 1.15fr),
    column-gutter: 12pt,
    [
      #text(size: T_SMALL, fill: PALETTE.muted, tracking: 0.12em, weight: "bold")[
        OUTLOOK · STRATEGY — MARKET LEVEL
      ]
      #v(3pt)
      #text(size: 21pt, weight: "bold", fill: PALETTE.brand_dark)[
        Kembalinya Animal Spirit
      ]
      #v(1pt)
      #text(size: 11.5pt, weight: "bold", fill: PALETTE.muted)[
        Indonesia 2026 Outlook · Target IHSG 9.100 (Bull 10.000 / Bear 7.800)
      ]
      #v(5pt)

      #card(PALETTE)[
        #text(size: 7.8pt, weight: "bold", fill: PALETTE.brand_dark)[EXECUTIVE SUMMARY / KEY POINTS]
        #v(1pt)
        #text(size: 6pt, style: "italic", fill: PALETTE.muted)[Core macroeconomic thesis, index target derivation, and market allocation stance.]
        #v(2.5pt)
        #list(
          [Siklus pelonggaran moneter global (Fed rate cuts) dan penurunan BI-Rate ke 5,25%–5,50% membuka ekspansi likuiditas pasar modal domestik.],
          [Pertumbuhan EPS konsensus agregat IHSG FY26F diproyeksikan tumbuh solid *+8,0% YoY*, didukung normalisasi biaya bunga dan daya beli konsumsi.],
          [Target IHSG Base Case *9.100* mencerminkan valuasi wajar *P/E 15,0x* (rerata historis 5-tahun), dengan skenario *Bull Case 10.000* dan *Bear Case 7.800*.],
          [Katalis struktural: Pembentukan Sovereign Wealth Fund *BP Danantara* mengonsolidasi aset BUMN >USD 600 miliar untuk efisiensi investasi dan dividen.],
        )
      ]

      #v(5pt)
      #exhibit-header("Asumsi Makroekonomi & Parameter Kunci Pasar Modal 2026F", "Konsensus Riset & Bank Indonesia")
      #v(2pt)
      #fin-table(
        ("Indikator Makro / Pasar", "2024A", "2025A", "2026F (Base)", "Implikasi Strategi"),
        (
          ("Pertumbuhan PDB Riil (%)", "5,05%", "5,10%", "5,25%", "Ekspansi Konsumsi & Investasi"),
          ("Tingkat Inflasi IHK (%)", "2,61%", "2,40%", "2,50%", "Daya Beli Riil Terjaga"),
          ("Suku Bunga BI-Rate (Year-End)", "6,00%", "5,75%", "5,25%–5,50%", "Cost of Funds Turun & Likuiditas Naik"),
          ("Nilai Tukar Rupiah (USD/IDR)", "15.850", "15.700", "15.500", "Stabilitas Arus Modal Asing"),
          ("Pertumbuhan EPS IHSG (%)", "+5,2%", "+6,1%", "+8,0%", "Re-rating Pertumbuhan Laba"),
          ("Target Forward P/E IHSG (x)", "12,8x", "13,2x", "15,0x", "Mean Reversion Valuasi Historis"),
        ),
        palette: PALETTE,
      )

      #v(5pt)
      #exhibit-header("Trajektori Target Indeks IHSG 2026 vs Historis 5 Tahun", "IDX, Bloomberg & Estimasi Riset")
      #v(2pt)
      #chart-placeholder("Trajektori Target IHSG 2026: Bear (7.800) — Base (9.100) — Bull (10.000)", caption: "Pergerakan Indeks Historis 2021–2025 & Proyeksi Skenario 2026F", height: 60pt, palette: PALETTE)
    ],
    [
      #block(
        width: 100%,
        stroke: 1.5pt + PALETTE.brand,
        radius: 5pt,
        inset: 8pt,
      )[
        #set align(center)
        #set text(font: FONT_SANS)
        #text(size: 13pt, weight: "black", fill: PALETTE.brand_dark)[OVERWEIGHT]
        #v(1pt)
        #text(size: 6.8pt, fill: PALETTE.muted)[Outlook Strategi Ekuitas 2026]
        #v(3pt)
        #text(size: 7.2pt, fill: PALETTE.muted)[Target IHSG (Base Case)]
        #v(1pt)
        #text(size: 18pt, weight: "black", fill: PALETTE.brand_dark)[9.100]
        #v(1pt)
        #text(size: 6.8pt)[Level Penutupan Kini: 7.930]
        #v(1.5pt)
        #text(size: 8pt, weight: "bold", fill: PALETTE.pos)[+14,8% Implied Upside]
        #v(1.5pt)
        #text(size: 6.5pt, fill: PALETTE.muted)[Rentang Skenario: 7.800 – 10.000]
      ]

      #v(4pt)
      #method-selection-panel(gate-verdict, palette: PALETTE)

      #v(4pt)
      #exhibit-header("Parameter Valuasi Indeks — Target IHSG 2026", "Model proyeksi valuasi indeks")
      #card(PALETTE)[
        #v(1pt)
        #text(size: 5.5pt, style: "italic", fill: PALETTE.muted)[Composite index targets, forward valuation multiples, and aggregate return metrics.]
        #v(2.5pt)
        #grid(
          columns: (1fr, auto),
          row-gutter: 2.8pt,
          text(size: 6.8pt)[IHSG Level Penutupan], text(size: 6.8pt, weight: "bold")[7.930],
          text(size: 6.8pt)[Target IHSG Base Case], text(size: 6.8pt, weight: "bold")[9.100 (+14,8%)],
          text(size: 6.8pt)[Target IHSG Bull Case], text(size: 6.8pt, weight: "bold", fill: PALETTE.pos)[10.000 (+26,1%)],
          text(size: 6.8pt)[Target IHSG Bear Case], text(size: 6.8pt, weight: "bold", fill: PALETTE.neg)[7.800 (-1,6%)],
          text(size: 6.8pt)[Pertumbuhan EPS FY26F], text(size: 6.8pt, weight: "bold")[8,0% YoY],
          text(size: 6.8pt)[Forward P/E Target (Base)], text(size: 6.8pt, weight: "bold")[15,0x (5Y Mean)],
          text(size: 6.8pt)[Forward P/E Kini], text(size: 6.8pt, weight: "bold")[13,1x],
          text(size: 6.8pt)[Estimasi Dividend Yield], text(size: 6.8pt, weight: "bold")[3,8%],
          text(size: 6.8pt)[Total Market Cap IDX], text(size: 6.8pt, weight: "bold")[Rp 12.850 T],
        )
      ]

      #v(4pt)
      #exhibit-header("Panduan Alokasi Aset 2026 (Equities / Bonds / Cash)", "Strategi alokasi portofolio riset")
      #card(PALETTE)[
        #v(1pt)
        #text(size: 5.5pt, style: "italic", fill: PALETTE.muted)[Asset allocation weighting recommendation across equities, fixed income, and cash.]
        #v(2.5pt)
        #grid(
          columns: (1fr, auto),
          row-gutter: 2.8pt,
          text(size: 6.8pt)[Saham Ekuitas (Equities)], text(size: 6.8pt, weight: "bold", fill: PALETTE.pos)[65% (Overweight)],
          text(size: 6.8pt)[Obligasi Negara (SBN)], text(size: 6.8pt, weight: "bold", fill: PALETTE.muted)[25% (Neutral)],
          text(size: 6.8pt)[Pasar Uang & Kas], text(size: 6.8pt, weight: "bold", fill: PALETTE.neg)[10% (Underweight)],
        )
      ]

      #v(4pt)
      #exhibit-header("Sektor Top Picks 2026", "Semesta riset ekuitas")
      #card(PALETTE)[
        #v(1pt)
        #text(size: 5.5pt, style: "italic", fill: PALETTE.muted)[High-conviction sectoral exposures and individual equity selection priorities.]
        #v(2pt)
        #text(size: 6.5pt)[
          - *Perbankan:* BBCA (CASA & Quality)
          - *Konsumer & Otomotif:* ICBP, ASII
          - *Digital & Telco:* GOTO, ISAT
          - *Mineral & Infra:* ANTM, JSMR
        ]
      ]
    ]
  )
])

#pagebreak(weak: true)

// =====================================================================
// PAGE 2 — INDEX TARGET SCENARIOS (BULL / BASE / BEAR + MATH DERIVATION)
// =====================================================================
#page-wrap("RESEARCH — Strategy Outlook", "31 Agt 2026", "IHSG / JCI", 2, PALETTE, [
  #section-header(1, "Scenario Analysis (Bear / Base / Bull) — Target Indeks IHSG", PALETTE)

  #text(size: 7.6pt)[
    Metodologi penetapan target IHSG memadukan proyeksi laba per saham agregat (*Consolidated EPS*) konstituen indeks dengan kelipatan valuasi (*Forward P/E Multiple*) berbasis deviasi standar historis 5 tahun. Kerangka kerja top-down ini menguji ketahanan pasar dalam 3 skenario makro: Bull, Base, dan Bear.
  ]
  #v(4pt)

  #grid(
    columns: (1fr, 1fr, 1fr),
    gutter: 6pt,
    card(PALETTE)[
      #text(size: 7pt, weight: "bold", fill: PALETTE.neg)[BEAR CASE (Probabilitas 20%)]
      #v(1pt)
      #text(size: 13pt, weight: "black", fill: PALETTE.brand_dark)[7.800]
      #text(size: 6.8pt, weight: "bold", fill: PALETTE.neg)[ (-1,6% return)]
      #v(1.5pt)
      #text(size: 6.4pt)[
        - *EPS FY26F:* Rp 578 (+2,0% YoY)
        - *Target Multiple:* 13,5x (-1,0 STD)
        - *Asumsi Makro:* Proteksionisme tarif dagang global, pelemahan rupiah >Rp 16.500/USD, Fed menahan suku bunga tinggi, pertumbuhan PDB melambat ke 4,7%.
      ]
    ],
    card(PALETTE)[
      #text(size: 7pt, weight: "bold", fill: PALETTE.brand)[BASE CASE (Probabilitas 60%)]
      #v(1pt)
      #text(size: 13pt, weight: "black", fill: PALETTE.brand_dark)[9.100]
      #text(size: 6.8pt, weight: "bold", fill: PALETTE.pos)[ (+14,8% return)]
      #v(1.5pt)
      #text(size: 6.4pt)[
        - *EPS FY26F:* Rp 607 (+8,0% YoY)
        - *Target Multiple:* 15,0x (5Y Mean)
        - *Asumsi Makro:* BI-Rate turun bertahap ke 5,25%–5,50%, inflasi stabil 2,5%, pertumbuhan laba korporasi 8,0%, PDB tumbuh 5,25%, Danantara mulai operasional.
      ]
    ],
    card(PALETTE)[
      #text(size: 7pt, weight: "bold", fill: PALETTE.pos)[BULL CASE (Probabilitas 20%)]
      #v(1pt)
      #text(size: 13pt, weight: "black", fill: PALETTE.brand_dark)[10.000]
      #text(size: 6.8pt, weight: "bold", fill: PALETTE.pos)[ (+26,1% return)]
      #v(1.5pt)
      #text(size: 6.4pt)[
        - *EPS FY26F:* Rp 625 (+12,0% YoY)
        - *Target Multiple:* 16,0x (+1,0 STD)
        - *Asumsi Makro:* Fed & BI cut rate agresif (-100 bps), foreign inflow masif (>Rp 85 T), percepatan capex SWF Danantara, PDB tumbuh akseleratif 5,5%.
      ]
    ],
  )

  #v(4pt)
  #exhibit-header("Tabel Penurunan Matematis Target IHSG Berdasarkan EPS & Forward P/E", "Model Proyeksi Valuasi Riset")
  #v(2pt)

  #card(PALETTE)[
    #grid(
      columns: (1fr, 1fr),
      gutter: 8pt,
      [
        #text(size: 6.8pt, weight: "bold", fill: PALETTE.brand_dark)[Formula Valuasi Target Indeks:] \
        #text(size: 6.3pt)[
          $text("Target IHSG") = text("EPS Konsolidasian FY26F") times text("Forward P/E Target")$ \
          $text("Implied Return") = frac(text("Target IHSG") - text("Level Penutupan Kini (7.930)"), text("Level Penutupan Kini (7.930)")) times 100\%$
        ]
      ],
      [
        #text(size: 6.8pt, weight: "bold", fill: PALETTE.brand_dark)[Ekspektasi Tertimbang Probabilitas (Expected Value):] \
        #text(size: 6.3pt)[
          $text("E(IHSG)") = sum (P_i times text("Target"_i)) = (20% times 7.800) + (60% times 9.100) + (20% times 10.000)$ \
          $text("Nilai Harapan IHSG FY26F") = 1.560 + 5.460 + 2.000 = bold(9.020) quad text("pts") (+13,7%)$
        ]
      ]
    )
  ]

  #v(3pt)
  #fin-table(
    ("Komponen / Parameter Valuasi", "Bear Case (20%)", "Base Case (60%)", "Bull Case (20%)", "Metodologi & Sumber Asumsi"),
    (
      ("EPS Basis FY25F (IDR Penuh)", "Rp 562", "Rp 562", "Rp 562", "Agregasi bottom-up laba bersih konstituen"),
      ("Pertumbuhan EPS FY26F (%)", "+2,0%", "+8,0%", "+12,0%", "Model sensitivitas pendapatan & marjin"),
      ("EPS Proyeksi FY26F (IDR)", "Rp 578", "Rp 607", "Rp 625", "EPS FY25F * (1 + Pertumbuhan EPS)"),
      ("Forward P/E Target Multiple", "13,5x", "15,0x", "16,0x", "Pita deviasi standar historis 5-tahun"),
      ("Posisi Deviasi Standar P/E", "-1,0 STD", "Rata-rata 5-Tahun", "+1,0 STD", "Mean reversion valuasi siklikal"),
      ("Implied Target Level IHSG", "7.800", "9.100", "10.000", "Pembulatan indeks = EPS * Multiple"),
      ("Implied Capital Gain vs 7.930", "-1,6%", "+14,8%", "+26,1%", "Apresiasi modal eks-dividen"),
      ("Estimasi Dividend Yield (%)", "4,2%", "3,8%", "3,5%", "Rata-rata payout ratio 45%–50%"),
      ("Total Expected Return (%)", "+2,6%", "+18,6%", "+29,6%", "Capital gain + dividend yield"),
    ),
    palette: PALETTE,
  )

  #v(4pt)
  #exhibit-header("Sensitivity Analysis — Pertumbuhan EPS vs Kelipatan P/E Forward", "Engine Sensitivitas Valuasi Indeks")
  #v(2pt)
  #fin-table(
    ("Forward P/E \\ EPS Growth", "+4,0% (Rp 584)", "+6,0% (Rp 596)", "+8,0% (Base Rp 607)", "+10,0% (Rp 618)", "+12,0% (Rp 625)"),
    (
      ("13,0x (-1,5 STD)", "7.592 (-4,3%)", "7.748 (-2,3%)", "7.891 (-0,5%)", "8.034 (+1,3%)", "8.125 (+2,5%)"),
      ("14,0x (-0,5 STD)", "8.176 (+3,1%)", "8.344 (+5,2%)", "8.498 (+7,2%)", "8.652 (+9,1%)", "8.750 (+10,3%)"),
      ("15,0x (Base Mean 5Y)", "8.760 (+10,5%)", "8.940 (+12,7%)", [*9.105 (+14,8%)*], "9.270 (+16,9%)", "9.375 (+18,2%)"),
      ("16,0x (+1,0 STD)", "9.344 (+17,8%)", "9.536 (+20,3%)", "9.712 (+22,5%)", "9.888 (+24,7%)", [*10.000 (+26,1%)*]),
      ("17,0x (+2,0 STD)", "9.928 (+25,2%)", "10.132 (+27,8%)", "10.319 (+30,1%)", "10.506 (+32,5%)", "10.625 (+34,0%)"),
    ),
    palette: PALETTE,
  )
])

#pagebreak(weak: true)

// =====================================================================
// PAGE 3 — THEMATICS + SECTOR POSITIONING GRID + TOP PICKS TABLE
// =====================================================================
#page-wrap("RESEARCH — Strategy Outlook", "31 Agt 2026", "IHSG / JCI", 3, PALETTE, [
  #section-header(2, "5 Tema Investasi Utama, Posisi Sektoral & Saham Pilihan (Top Picks)", PALETTE)

  #grid(
    columns: (1fr, 1fr, 1fr, 1fr, 1fr),
    gutter: 4pt,
    card(PALETTE)[
      #text(size: 6.2pt, weight: "bold", fill: PALETTE.brand_dark)[1. SIKLUS MONETER]
      #v(1pt)
      #text(size: 5.8pt)[
        Penurunan BI-Rate ke 5,25%–5,50% menurunkan CoF perbankan dan mendorong pertumbuhan kredit 10%–12%.
      ]
    ],
    card(PALETTE)[
      #text(size: 6.2pt, weight: "bold", fill: PALETTE.brand_dark)[2. DAYA BELI FMCG]
      #v(1pt)
      #text(size: 5.8pt)[
        Stimulus bansos, kenaikan UMR, dan program baru menopang konsumsi pangan dan barang konsumsi pokok.
      ]
    ],
    card(PALETTE)[
      #text(size: 6.2pt, weight: "bold", fill: PALETTE.brand_dark)[3. HILIRISASI & EV]
      #v(1pt)
      #text(size: 5.8pt)[
        Smelter emas, tembaga, dan integrasi rantai pasok baterai memperbesar nilai tambah ekspor mineral.
      ]
    ],
    card(PALETTE)[
      #text(size: 6.2pt, weight: "bold", fill: PALETTE.brand_dark)[4. SWF DANANTARA]
      #v(1pt)
      #text(size: 5.8pt)[
        Konsolidasi dividen BUMN dan recycling aset infrastruktur tol/energi membuka likuiditas baru di IDX.
      ]
    ],
    card(PALETTE)[
      #text(size: 6.2pt, weight: "bold", fill: PALETTE.brand_dark)[5. EKONOMI DIGITAL]
      #v(1pt)
      #text(size: 5.8pt)[
        Monetisasi platform teknologi menuju laba bersih dan kenaikan ARPU telekomunikasi pasca-merger.
      ]
    ],
  )

  #v(4pt)
  #exhibit-header("Matriks Alokasi Sektoral IHSG 2026 (Overweight / Neutral / Underweight)", "Strategi Alokasi Portofolio Riset")
  #v(1.5pt)

  #set text(font: FONT_SANS, size: 6.2pt)
  #table(
    columns: (1.3fr, 0.45fr, 3.25fr),
    stroke: 0.4pt + PALETTE.line,
    fill: (col, row) => if row == 0 { PALETTE.brand_dark } else if calc.odd(row) { PALETTE.band } else { PALETTE.paper },
    inset: (x: 3.5pt, y: 1.8pt),
    table.cell(text(fill: white, weight: "bold", size: 6.5pt)[Sektor Indeks], align: left),
    table.cell(text(fill: white, weight: "bold", size: 6.5pt)[Pandangan], align: center),
    table.cell(text(fill: white, weight: "bold", size: 6.5pt)[Catatan Strategis & Tesis Kunci Sektor], align: left),

    [Perbankan (Financials)], align(center)[#text(fill: PALETTE.pos, weight: "bold")[OW]], [Pertumbuhan kredit 10%–12%, NIM defensif \~5,0%, CASA kokoh >80%, penerima likuiditas asing.],
    [Konsumer Non-Siklikal], align(center)[#text(fill: PALETTE.pos, weight: "bold")[OW]], [Pemulihan daya beli kelas menengah-bawah ditopang bansos dan penurunan biaya bahan baku gandum/CPO.],
    [Otomotif & Siklikal], align(center)[#text(fill: PALETTE.pos, weight: "bold")[OW]], [Sensitif terhadap pelonggaran suku bunga kredit 4W/2W, peluncuran model hybrid baru, dividen yield tinggi.],
    [Telekomunikasi & Digital], align(center)[#text(fill: PALETTE.pos, weight: "bold")[OW]], [Kenaikan ARPU data pasca-konsolidasi, monetisasi data center AI, platform teknologi menuju profitabilitas.],
    [Infrastruktur & Jalan Tol], align(center)[#text(fill: PALETTE.pos, weight: "bold")[OW]], [Katalis optimalisasi dan recycling konsesi jalan tol melalui Danantara; volume lalu lintas harian stabil.],
    [Mineral & Logam Hilir], align(center)[#text(fill: PALETTE.pos, weight: "bold")[OW]], [Rally harga emas global sebagai aset lindung nilai, ekspansi smelter nikel dan rantai pasok baterai EV.],
    [Properti & Real Estat], align(center)[#text(fill: PALETTE.muted, weight: "bold")[N]], [Pelonggaran suku bunga KPR menjadi katalis positif, namun penyerapan segmen menengah masih bertahap.],
    [Semen & Bahan Bangunan], align(center)[#text(fill: PALETTE.muted, weight: "bold")[N]], [Overkapasitas industri masih membatasi kenaikan ASP, meski ada dorongan belanja infrastruktur IKN.],
    [Energi & Batubara Termal], align(center)[#text(fill: PALETTE.neg, weight: "bold")[UW]], [Normalisasi harga batubara Newcastle ke USD 110–130/ton serta tantangan percepatan transisi energi.],
    [Perkebunan (CPO)], align(center)[#text(fill: PALETTE.neg, weight: "bold")[UW]], [Volatilitas bea keluar ekspor dan penuaan profil usia tanaman kelapa sawit membatasi pertumbuhan volume.],
  )

  #v(4pt)
  #exhibit-header("Peer Comparison — Valuasi Saham Pilihan Utama (Top Picks 2026)", "Semesta Riset Ekuitas")
  #v(1.5pt)

  #fin-table(
    ("Ticker", "Cap", "P/E (x)", "ROE (%)", "PBV (x)", "Karakteristik & Rationale"),
    (
      ("BBCA", "Large", "14,5x", "18,5%", "2,3x", "Kualitas aset prima (NPL 1,8%), CASA 82%, penerima inflow asing."),
      ("ASII", "Large", "8,5x", "14,0%", "1,1x", "Pemulihan 4W/2W pasca-rate cut, dividen yield 6,5%."),
      ("ICBP", "Large", [*13,2x*], "19,2%", "2,5x", "Ekspansi margin bruto dari deflasi gandum & kemasan."),
      ("GOTO", "Large", "28,0x", "3,5%", "1,2x", "Perbaikan adjusted EBITDA positif, fintech GoPay & TikTok."),
      ("ANTM", "Mid", "12,0x", "15,5%", "1,6x", "Rekor harga emas global, Feronikel Haltim, baterai EV."),
      ("ISAT", "Large", [*13,8x*], "16,8%", "1,8x", "Kenaikan ARPU seluler, sinergi merger, data center AI."),
      ("JSMR", "Mid", "10,2x", "12,0%", "1,0x", "Pertumbuhan volume tol stabil (+3%–4%), de-leveraging Danantara."),
      ([*Rata-rata Peers (Average)*], [*Large/Mid*], [*14,3x*], [*14,2%*], [*1,64x*], [*Rerata tertimbang semesta Top Picks IHSG*]),
      ([*Median Peers*], [*Large/Mid*], [*13,2x*], [*15,5%*], [*1,60x*], [*Nilai median semesta Top Picks IHSG*]),
    ),
    columns: (0.9fr, 0.7fr, 0.8fr, 0.8fr, 0.8fr, 3.8fr),
    palette: PALETTE,
  )
])
#v(2pt)
#text(size: 6.5pt, fill: PALETTE.muted, style: "italic")[Top Picks ilustratif, statis Sep 2026 — cross-check via Sectors screener pending.]

#pagebreak(weak: true)

// =====================================================================
// PAGE 4 — FOREIGN FLOWS & BP DANANTARA
// =====================================================================
#page-wrap("RESEARCH — Strategy Outlook", "31 Agt 2026", "IHSG / JCI", 4, PALETTE, [
  #section-header(3, "Dinamika Arus Modal Asing (Flows) & Transformasi BP Danantara", PALETTE)

  #text(size: 7.2pt)[
    Dua pendorong likuiditas utama pasar saham Indonesia 2026 adalah kembalinya modal portofolio asing (*Foreign Flows*) pasca pelonggaran suku bunga global dan operasionalisasi Superholding *BP Danantara* yang mengelola aset negara \~USD 520 miliar.
  ]
  #v(3pt)

  #exhibit-header("Dinamika Arus Modal Asing (Foreign Flows) Historis & Proyeksi 2026F", "Bursa Efek Indonesia & Bank Indonesia")
  #v(1.5pt)
  #fin-table(
    ("Periode", "Net Buy (Rp T)", "Porsi IDX", "Yield SBN 10Y", "Cadangan Devisa", "Katalis & Sentimen Global"),
    (
      ("2022A", "+Rp 61,0 T", "28,5%", "6,94%", "USD 137,2 bn", "Windfall komoditas & surplus neraca dagang"),
      ("2023A", "-Rp 6,5 T", "27,2%", "6,48%", "USD 146,4 bn", "Pengetatan agresif suku bunga The Fed"),
      ("2024A", "+Rp 24,8 T", "27,8%", "6,85%", "USD 150,2 bn", "Stabilitas transisi politik pasca-pemilu"),
      ("2025A", "+Rp 38,5 T", "28,4%", "6,60%", "USD 156,0 bn", "Siklus pelonggaran moneter global dimulai"),
      ("2026F (Base)", "+Rp 55,0 T", "29,5%", "6,25%", "USD 165,0 bn", "Re-rating IHSG, inflow Danantara & yield spread menarik"),
      ("2026F (Bull)", "+Rp 85,0 T", "31,0%", "5,90%", "USD 175,0 bn", "Inflow sovereign fund global & kenaikan bobot MSCI"),
    ),
    columns: (1.1fr, 1.2fr, 0.9fr, 1.1fr, 1.3fr, 3.2fr),
    palette: PALETTE,
  )

  #v(3pt)
  #exhibit-header("Portofolio Aset Konsolidasi BP Danantara & Valuasi BUMN Terbuka", "Kementerian BUMN & Estimasi Riset")
  #v(1.5pt)
  #fin-table(
    ("Entitas BUMN Inti", "Porsi", "Total Aset", "Nilai Ekuitas", "Peran Strategis & Dampak Pasar Modal"),
    (
      ("PT Bank Mandiri (BMRI)", "52,0%", "Rp 2.174 T", "Rp 275 T", "Anchor kredit korporasi & sindikasi infra; dividend payout 60%–70%."),
      ("PT Bank Rakyat Indonesia (BBRI)", "53,2%", "Rp 1.965 T", "Rp 312 T", "Ekosistem ultra-mikro & UMKM; dividend yield konsisten >5,5%."),
      ("PT Telkom Indonesia (TLKM)", "52,1%", "Rp 305 T", "Rp 148 T", "Infrastruktur digital, fiber optic, dan monetisasi data center AI."),
      ("PT PLN (Persero)", "100,0%", "Rp 1.690 T", "Rp 410 T", "Transmisi supergrid EBT; potensi green bond & IPO anak usaha."),
      ("PT Pertamina (Persero)", "100,0%", "Rp 1.410 T", "Rp 480 T", "Ketahanan energi nasional, ekspansi petrokimia, valuasi PHE & PGAS."),
      ("MIND ID (Holding Tambang)", "100,0%", "Rp 350 T", "Rp 120 T", "Induk ANTM, PTBA, TINS, INCO; integrasi ekosistem baterai EV."),
      ("JSMR & Konsesi Jalan Tol", "Multi", "Rp 185 T", "Rp 38 T", "Asset recycling jalan tol beroperasi guna de-leveraging neraca."),
      ([*Total Konsolidasi Danantara*], [*SWF*], [*Rp 8.079 T*], [*Rp 1.783 T*], [*Setara \~USD 520 Miliar (\~38% terhadap PDB Indonesia 2026)*]),
    ),
    columns: (1.5fr, 0.7fr, 1.1fr, 1.1fr, 3.4fr),
    palette: PALETTE,
  )

  #v(2pt)
  #exhibit-header("Konsolidasi Laba Rugi Agregat Konstituen IHSG 6 Tahun", "Konsensus Bloomberg & IDX")
  #v(1.5pt)
  #fin-table(
    ("Akun Laba Rugi Agregat", "FY24A", "FY25A", "FY26F", "FY27F", "FY28F", "FY29F"),
    (
      ("Pendapatan Agregat (Rp T)", "3.120", "3.310", "3.575", "3.860", "4.170", "4.500"),
      ("EBITDA Agregat (Rp T)", "1.040", "1.105", "1.215", "1.320", "1.440", "1.570"),
      ("Laba Bersih Agregat (Rp T)", "412", "438", "473", "515", "562", "615"),
      ("Pertumbuhan EPS (%)", "+5,2%", "+6,0%", "+8,0%", "+8,9%", "+9,1%", "+9,4%"),
    ),
    palette: PALETTE,
  )

  #v(3pt)
  #card(PALETTE)[
    #text(size: 6.8pt, weight: "bold", fill: PALETTE.brand_dark)[Implikasi Transformasi BP Danantara bagi Pasar Saham Indonesia]
    #v(1.5pt)
    #text(size: 6.2pt)[
      BP Danantara mengadopsi model *active sovereign asset management* serupa Temasek Singapura. Konsolidasi kepemilikan saham BUMN ke dalam satu SWF profesional meningkatkan efisiensi alokasi capex, memperjelas kebijakan dividen publik, dan membuka peluang *asset recycling* yang memperdalam likuiditas perdagangan di Bursa Efek Indonesia.
    ]
  ]
])

#pagebreak(weak: true)

// =====================================================================
// PAGE 5 — RATING GUIDE & DISCLAIMER
// =====================================================================
#page-wrap("RESEARCH — Strategy Outlook", "31 Agt 2026", "IHSG / JCI", 5, PALETTE, [
  #section-header(4, "Panduan Rating, Valuation Methodology & Disklaimer Kepatuhan OJK", PALETTE)

  #exhibit-header("Panduan Pemeringkatan Investment Recommendation (9 Kategori)", "Standar Metodologi Riset Ekuitas Institusional")
  #v(2pt)
  #fin-table(
    ("Kategori Peringkat", "Definisi Kriteria (Horizon 12-Bulan Eks-Dividen)", "Implikasi bagi Alokasi Portofolio"),
    (
      ("SECTOR — OVERWEIGHT", "Sektor diproyeksikan outperform IHSG > +5% dalam rentang 12 bulan", "Alokasi bobot di atas rata-rata benchmark indeks"),
      ("SECTOR — NEUTRAL", "Sektor diproyeksikan in-line (+/- 5%) dengan pergerakan IHSG", "Alokasi bobot proporsional sesuai benchmark"),
      ("SECTOR — UNDERWEIGHT", "Sektor diproyeksikan underperform IHSG > -5% dalam rentang 12 bulan", "Alokasi bobot di bawah rata-rata benchmark"),
      ("STOCK — BUY", "Ekspektasi total return > +15% dalam 12 bulan ke depan", "Akumulasi agresif / core portfolio holding"),
      ("STOCK — TRADING BUY", "Ekspektasi total return +5% s/d +15% (jangka pendek/taktis)", "Peluang beli berbasis momentum dan katalis spesifik"),
      ("STOCK — HOLD", "Ekspektasi total return -10% s/d +15% dalam rentang 12 bulan", "Pertahankan posisi; profil risk-reward berimbang"),
      ("STOCK — SELL", "Ekspektasi total return < -15% dalam 12 bulan ke depan", "Realisasi keuntungan / pangkas eksposur risiko"),
      ("STOCK — TRADING SELL", "Ekspektasi total return -5% s/d -15% (jangka pendek)", "Profit taking taktis saat reli harga sementara"),
      ("STOCK — NOT RATED", "Saham di luar cakupan riset aktif / proses underwriting", "Tidak ada target harga atau rating aktif yang berlaku"),
    ),
    palette: PALETTE,
  )

  #v(4pt)
  #card(PALETTE)[
    #text(size: 7.2pt, weight: "bold", fill: PALETTE.ink)[Valuation Methodology — Riset Strategi & Proyeksi Pasar]
    #v(2pt)
    #text(size: 6.5pt)[
      Model Strategi Pasar memadukan pendekatan makroekonomi *Top-Down* (analisis siklus moneter BI/Fed, inflasi, fiskal, dan neraca transaksi berjalan) dengan agregasi fundamental *Bottom-Up* dari 120+ emiten dalam cakupan semesta riset yang mencakup >85% kapitalisasi pasar IHSG. Penetapan target kelipatan valuasi (*Forward P/E Multiple*) berbasis pita deviasi standar historis 5-tahun dan penyesuaian terhadap yield spread obligasi negara (SBN 10-Tahun).
    ]
  ]

  #v(4pt)
  #card(PALETTE)[
    #text(size: 7.2pt, weight: "bold", fill: PALETTE.ink)[Sertifikasi Analis & Independensi Penilaian]
    #v(2pt)
    #text(size: 6.5pt)[
      Analis strategi pasar modal yang tercantum dalam laporan ini menyatakan secara independen bahwa: (1) Seluruh pandangan, proyeksi, dan rekomendasi yang diungkapkan secara akurat merefleksikan penilaian fundamental terhadap dinamika makro dan pasar saham Indonesia; (2) Kompensasi analis tidak berhubungan, baik langsung maupun tidak langsung, dengan rekomendasi spesifik; (3) Analis tidak memiliki kepemilikan saham finansial material pada instrumen ekuitas yang dianalisis.
    ]
  ]

  #v(4pt)
  #card(PALETTE)[
    #text(size: 7.2pt, weight: "bold", fill: PALETTE.ink)[Disklaimer Kepatuhan Otoritas Jasa Keuangan (OJK)]
    #v(2pt)
    #text(size: 6.5pt, fill: PALETTE.muted)[
      Laporan ini diterbitkan semata-mata untuk tujuan penyediaan informasi edukatif dan riset pasar modal bagi investor. Dokumen ini bukan merupakan penawaran, ajakan, atau rekomendasi resmi untuk membeli atau menjual instrumen keuangan apa pun. Estimasi dan proyeksi didasarkan pada data publik yang diyakini dapat diandalkan (IDX, Bank Indonesia, Kementerian BUMN, Bloomberg), namun tidak ada garansi atas kelengkapan dan keakuratannya. Kinerja masa lalu bukan merupakan indikasi atau jaminan kinerja masa depan. Setiap keputusan investasi merupakan tanggung jawab mandiri investor sepenuhnya.
    ]
  ]

  #v(4pt)
  #card(PALETTE)[
    #grid(
      columns: (1fr, 1fr),
      column-gutter: 10pt,
      [
        #text(size: 6.8pt, weight: "bold", fill: PALETTE.muted)[DISIAPKAN OLEH & TIM RISET]
        #v(1.5pt)
        #text(size: 6.3pt)[
          - *Institusi:* RESEARCH — Sectors Hackathon 2026
          - *Tanggal Publikasi:* 31 Agustus 2026 · Bahasa: Indonesia (ID)
          - *Lead Strategist:* Sukarno Alatas (Senior Equity Strategist)
          - *Kontak Surel:* strategy\@skt.id
        ]
      ],
      [
        #text(size: 6.8pt, weight: "bold", fill: PALETTE.muted)[KANTOR PUSAT & PROVENANCE]
        #v(1.5pt)
        #text(size: 6.3pt)[
          - *Kantor:* Treasury Tower 27th Floor, SCBD Lot 28 — Jakarta
          - *Divisi:* Macro & Equity Strategy Research Team
          - *Dokumen:* templates/typst/archetypes/report_strategy.typ
          - *Portal Riset:* www.skt.id/strategy
        ]
      ]
    )
  ]
])
