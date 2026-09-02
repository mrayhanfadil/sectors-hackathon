// =====================================================================
// report_infra.typ — Institutional equity research (Infra archetype)
// Case: MTEL (PT Dayamitra Telekomunikasi Tbk) — 11 Pages Comprehensive Report
// =====================================================================
#import "../common/theme.typ": *

#show: set-page-defaults

#let PALETTE = (
  brand: rgb("#067647"),       // emerald green (telecom infra)
  brand_dark: rgb("#054f31"),
  accent: rgb("#ecfdf3"),
  ink: rgb("#101828"),
  muted: rgb("#475467"),
  line: rgb("#e4e7ec"),
  band: rgb("#f9fafb"),
  paper: rgb("#ffffff"),
  pos: rgb("#067647"),
  neg: rgb("#b42318"),
)

// Helper: visual placeholder for chart rendering
#let chart-placeholder(label, caption: "Engine Chart Renderer (IDX / yfinance)", height: 70pt, palette: PALETTE) = {
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

// Helper: compact financial table for dense pages
#let compact-fin-table(headers, rows, footers: (), columns: none, palette: PALETTE) = {
  set text(font: FONT_MONO, size: 6.2pt, features: ("tnum",))
  set table(
    stroke: 0.4pt + palette.line,
    fill: (col, row) => if row == 0 { palette.brand_dark } else if calc.odd(row) { palette.band } else { palette.paper },
    inset: (x: 2.5pt, y: 1.5pt),
  )
  let headers-arr = if type(headers) == array { headers } else { headers.pos() }
  let rows-arr = if type(rows) == array { rows } else { rows.pos() }
  let cols = if columns != none { columns } else { (1.6fr, ..(1fr,) * (headers-arr.len() - 1)) }
  let header-cells = headers-arr.enumerate().map(((i, h)) => table.cell(
    text(fill: white, weight: "bold", size: 6.2pt)[#h],
    align: if i == 0 { left } else { right },
  ))
  let body-cells = rows-arr.map(row => {
    let row-arr = if type(row) == array { row } else { row.pos() }
    row-arr.enumerate().map(((i, c)) => table.cell(
      align: if i == 0 { left } else { right },
      [#c],
    ))
  })
  let footer-cells = footers.map(row => row.enumerate().map(((i, c)) => table.cell(
    text(weight: "bold"),
    align: if i == 0 { left } else { right },
    [#c],
  )))
  table(
    columns: cols,
    ..header-cells,
    ..body-cells.flatten(),
    ..(if footers.len() > 0 {
      footer-cells.flatten()
    } else { () }),
  )
}

// Colors for segment pillars
#let C_TOWER = rgb("#067647")
#let C_FIBER = rgb("#0284c7")
#let C_RELATED = rgb("#d97706")
#let C_RESELLER = rgb("#7c3aed")

// =====================================================================
// PAGE 1 — COVER & SNAPSHOT
// =====================================================================
#page-wrap("RESEARCH — Equity Report", "27 Agt 2026", "MTEL", 1, PALETTE, [
  #grid(
    columns: (2fr, 1.15fr),
    column-gutter: 12pt,
    [
      #text(size: T_SMALL, fill: PALETTE.muted, tracking: 0.12em, weight: "bold")[
        EQUITY UPDATE · INFRASTRUKTUR TELEKOMUNIKASI
      ]
      #v(3pt)
      #text(size: T_COVER_TITLE, weight: "bold", fill: PALETTE.brand_dark)[
        Dayamitra Telekomunikasi
      ]
      #v(1pt)
      #text(size: 12.5pt, weight: "bold", fill: PALETTE.muted)[
        MTEL · IDX · Sektor Infrastruktur Telekomunikasi
      ]
      #v(6pt)

      #card(PALETTE)[
        #text(size: 7.8pt, weight: "bold", fill: PALETTE.brand_dark)[KEY TAKEAWAYS & HIGHLIGHTS]
        #v(3pt)
        #list(
          [PST & UMT merger efektif 1 Jul 2026 membuka efisiensi opex/capex dan tenancy >1,6x.],
          [Spectrum 700MHz/2.6GHz berpotensi menambah 3.000–3.500 tenant (+Rp 360–420 bn) by FY27–29.],
          [DCF 60% + EV/EBITDA 40% blended TP Rp 635, margin of safety 15%, upside +38% dari harga Rp 460.],
        )
      ]

      #v(6pt)
      #exhibit-header("Exhibit 1", "Bauran Pendapatan per Segmen (1H26)", "MTEL 1H26 (IDX)")
      #v(2pt)
      #block(width: 100%)[
        #grid(
          columns: (49.2%, 17.8%, 18.2%, 14.8%),
          rect(width: 100%, height: 7pt, fill: C_TOWER, radius: (left: 2pt)),
          rect(width: 100%, height: 7pt, fill: C_FIBER),
          rect(width: 100%, height: 7pt, fill: C_RELATED),
          rect(width: 100%, height: 7pt, fill: C_RESELLER, radius: (right: 2pt)),
        )
        #v(2pt)
        #grid(
          columns: (1.2fr, 1fr, 1.2fr, 1fr),
          [#box(width: 4.5pt, height: 4.5pt, fill: C_TOWER, radius: 1pt) #text(size: 6.2pt)[ Tower 49,2%]],
          [#box(width: 4.5pt, height: 4.5pt, fill: C_FIBER, radius: 1pt) #text(size: 6.2pt)[ Fiber 17,8%]],
          [#box(width: 4.5pt, height: 4.5pt, fill: C_RELATED, radius: 1pt) #text(size: 6.2pt)[ Related 18,2%]],
          [#box(width: 4.5pt, height: 4.5pt, fill: C_RESELLER, radius: 1pt) #text(size: 6.2pt)[ Reseller 14,8%]],
        )
      ]
      #v(2pt)
      #fin-table(
        ("Segmen Bisnis", "1H26 (Rp bn)", "Bauran (%)", "YoY (%)", "Status"),
        (
          ("Tower Leasing", "3.833", "49,2%", "+1,0%", "Core Anchor"),
          ("Fiber Optic", "309", "17,8%", "+8,0%", "Growth Driver"),
          ("Tower-Related Business", "299", "18,2%", "+15,0%", "High Expansion"),
          ("Reseller", "251", "14,8%", "0,0%", "Stable Cashflow"),
          ([*Total Pendapatan 1H26*], [*4.691*], [*100,0%*], [*+2,1%*], [*Konsolidasian*]),
        ),
        palette: PALETTE,
      )

      #v(6pt)
      #exhibit-header("Exhibit 2", "Kinerja Harga MTEL vs IHSG (YTD)", "IDX & yfinance (MTEL.JK vs ^JKSE)")
      #v(2pt)
      #chart-placeholder("Kinerja Harga MTEL (+12,1% YTD) vs IHSG (-2,9% Relatif)", caption: "Alpha Relatif vs IHSG · Sumber: IDX & yfinance", height: 60pt, palette: PALETTE)
    ],
    [
      #rating-box(
        "BUY",
        "635",
        "460",
        38.0,
        prev-tp: "815",
        palette: PALETTE,
      )

      #v(5pt)
      #card(PALETTE)[
        #text(size: T_SMALL, weight: "bold", fill: PALETTE.muted)[INFORMASI PASAR & SAHAM]
        #v(2.5pt)
        #grid(
          columns: (1fr, auto),
          row-gutter: 3pt,
          text(size: 7pt)[Harga Kini], text(size: 7pt, weight: "bold")[Rp 460],
          text(size: 7pt)[Target Harga (12M)], text(size: 7pt, weight: "bold")[Rp 635],
          text(size: 7pt)[TP Sebelumnya], text(size: 7pt, weight: "bold")[Rp 815],
          text(size: 7pt)[Potensi Kenaikan], text(size: 7pt, weight: "bold", fill: PALETTE.pos)[+38,0% (BUY)],
          text(size: 7pt)[Saham Beredar], text(size: 7pt, weight: "bold")[81,50 Miliar],
          text(size: 7pt)[Kapitalisasi Pasar], text(size: 7pt, weight: "bold")[Rp 37,49 T],
          text(size: 7pt)[Free Float], text(size: 7pt, weight: "bold")[28,2%],
          text(size: 7pt)[52-Wk Range], text(size: 7pt, weight: "bold")[420 - 710],
          text(size: 7pt)[Indeks Konstituen], text(size: 7pt, weight: "bold")[LQ45 / IDX80 / KOMPAS100],
        )
      ]

      #v(5pt)
      #card(PALETTE)[
        #text(size: T_SMALL, weight: "bold", fill: PALETTE.muted)[STRUKTUR KEPEMILIKAN]
        #v(2.5pt)
        #grid(
          columns: (1fr, auto),
          row-gutter: 3pt,
          text(size: 7pt)[PT Telkom Indonesia (TLKM)], text(size: 7pt, weight: "bold")[71,83%],
          text(size: 7pt)[Publik (Free Float)], text(size: 7pt, weight: "bold")[28,17%],
        )
        #v(2pt)
        #text(size: 6.2pt, style: "italic", fill: PALETTE.muted)[Sumber: IDX struktur pemegang saham]
      ]

      #v(5pt)
      #card(PALETTE)[
        #text(size: T_SMALL, weight: "bold", fill: PALETTE.muted)[SKOR ESG (SUSTAINALYTICS 2026)]
        #v(2.5pt)
        #grid(
          columns: (1fr, auto),
          row-gutter: 3pt,
          text(size: 7pt)[Lingkungan (E)], text(size: 7pt, weight: "bold")[2,23 / 10],
          text(size: 7pt)[Sosial (S)], text(size: 7pt, weight: "bold")[3,03 / 10],
          text(size: 7pt)[Tata Kelola (G)], text(size: 7pt, weight: "bold")[5,08 / 10],
          text(size: 7pt)[Kategori Risiko ESG], text(size: 7pt, weight: "bold", fill: PALETTE.brand)[Low to Medium Risk],
        )
      ]
    ]
  )
])

#pagebreak()

// =====================================================================
// PAGE 2 — KPI OPERASIONAL HERO & KATALIS TERKUANTIFIKASI
// =====================================================================
#page-wrap("RESEARCH — Equity Report", "27 Agt 2026", "MTEL", 2, PALETTE, [
  #section-header(1, "KPI Operasional — Hero Section", PALETTE)

  #text(size: 7.8pt)[
    KPI per subsektor infrastruktur telekomunikasi (tenancy ratio = tenant/tower, fiber optic deployment km) adalah tesis utama bisnis *recurring infra* — bukan hanya sekadar metrik P&L kuartalan. Portofolio menara MTEL terbesar di Asia Tenggara memperkuat skala keekonomian dan daya tawar terhadap seluruh MNO.
  ]
  #v(4pt)

  #grid(
    columns: (1fr, 1fr, 1fr, 1fr, 1.15fr),
    gutter: 6pt,
    card(PALETTE)[
      #text(size: 6.5pt, fill: PALETTE.muted, weight: "bold")[TOTAL TOWER]
      #v(1pt)
      #text(size: 11.5pt, weight: "black", fill: PALETTE.brand_dark)[40.563]
      #text(size: 6.5pt, weight: "bold")[ unit]
      #v(1pt)
      #text(size: 6.2pt, fill: PALETTE.pos, weight: "bold")[+796 (+2,0% YoY)]
    ],
    card(PALETTE)[
      #text(size: 6.5pt, fill: PALETTE.muted, weight: "bold")[COLOCATION]
      #v(1pt)
      #text(size: 11.5pt, weight: "black", fill: PALETTE.brand_dark)[23.303]
      #text(size: 6.5pt, weight: "bold")[ unit]
      #v(1pt)
      #text(size: 6.2pt, fill: PALETTE.pos, weight: "bold")[+2.178 (+10,3% YoY)]
    ],
    card(PALETTE)[
      #text(size: 6.5pt, fill: PALETTE.muted, weight: "bold")[TOTAL TENANT]
      #v(1pt)
      #text(size: 11.5pt, weight: "black", fill: PALETTE.brand_dark)[63.866]
      #text(size: 6.5pt, weight: "bold")[ tnt]
      #v(1pt)
      #text(size: 6.2pt, fill: PALETTE.pos, weight: "bold")[+2.959 (+4,9% YoY)]
    ],
    card(PALETTE)[
      #text(size: 6.5pt, fill: PALETTE.muted, weight: "bold")[TENANCY RATIO]
      #v(1pt)
      #text(size: 11.5pt, weight: "black", fill: PALETTE.brand_dark)[1,57x]
      #text(size: 6.5pt, weight: "bold")[ rasio]
      #v(1pt)
      #text(size: 6.2pt, fill: PALETTE.pos, weight: "bold")[+0,04x (vs 1,53x)]
    ],
    card(PALETTE)[
      #text(size: 6.5pt, fill: PALETTE.muted, weight: "bold")[FIBER OPTIC]
      #v(1pt)
      #text(size: 11.5pt, weight: "black", fill: PALETTE.brand_dark)[59.239]
      #text(size: 6.5pt, weight: "bold")[ km]
      #v(1pt)
      #text(size: 6.2pt, fill: PALETTE.pos, weight: "bold")[+4.792 km (+8,8% YoY)]
    ],
  )

  #v(6pt)
  #exhibit-header("Exhibit 3", "Tabel KPI Operasional vs Periode Lalu (1H26 vs 1H25)", "Company data 1H26, data diolah")
  #v(2pt)
  #fin-table(
    ("Metrik KPI", "Kini (1H26)", "Lalu (1H25)", "Perubahan (Δ)", "Satuan", "Formula & Karakteristik", "Sumber Data"),
    (
      ("Jumlah Menara (Tower)", "40.563", "39.782", "+781 (+2,0%)", "unit", "Total owned towers", "Company data 1H26"),
      ("Kolokasi (Colocation)", "23.303", "21.125", "+2.178 (+10,3%)", "unit", "Sewa tambahan di menara existing", "Company data 1H26"),
      ("Jumlah Penyewa (Tenant)", "63.866", "60.907", "+2.959 (+4,9%)", "tenant", "Total tenant aktif MNO", "Company data 1H26"),
      ("Tenancy Ratio", "1,57x", "1,53x", "+0,04x (+2,6%)", "x", "Tenant / Tower (Utilisasi aset)", "Company data, diolah"),
      ("Jaringan Fiber Optic", "59.239", "54.447", "+4.792 (+8,8%)", "km", "Panjang fiber terbangun", "Company data 1H26"),
      ("Penyewa Reseller", "2.650", "2.659", "-9 (-0,3%)", "tenant", "Reseller managed tenancy", "Company data 1H26"),
    ),
    palette: PALETTE,
  )

  #v(6pt)
  #exhibit-header("Exhibit 4", "Perbandingan Visual Menara, Kolokasi & Total Tenant", "Company data 1H26 & Analisis Riset")
  #v(2pt)
  #chart-placeholder("Grafik Komparasi: Tower 40.563 (+2%) · Colocation 23.303 (+10%) · Tenant 63.866 (+5%)", caption: "Pertumbuhan Colocation Lebih Cepat Mengindikasikan Efisiensi Margin Operasional", height: 65pt, palette: PALETTE)

  #v(6pt)
  #section-header(2, "Katalis Pertumbuhan Terkuantifikasi", PALETTE)
  #v(-2pt)

  #grid(
    columns: (1fr, 1fr),
    gutter: 8pt,
    card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.brand_dark)[1. Merger PST & UMT (Efektif 1 Juli 2026)]
      #v(2pt)
      #text(size: 7.2pt)[
        *Dampak Operasional & Finansial:* \
        Konsolidasi operator telekomunikasi membuka optimalisasi belanja modal dan opex jaringan. Rasio tenancy MTEL diproyeksikan terdorong melampaui *>1,60x*, disertai peningkatan permintaan solusi terintegrasi: Fixed Wireless Access (FWA), fiberization, IoT, dan power management.
      ]
      #v(3pt)
      #grid(
        columns: (1fr, auto),
        text(size: 6.8pt, fill: PALETTE.muted)[Target Tenancy: >1,60x],
        text(size: 6.8pt, weight: "bold", fill: PALETTE.pos)[Periode: FY27–FY29],
      )
    ],
    card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.brand_dark)[2. Lelang Spektrum 700MHz & 2,6GHz]
      #v(2pt)
      #text(size: 7.2pt)[
        *Dampak Kuantitatif Terukur:* \
        Alokasi frekuensi baru oleh Komdigi (TLKM 20/80 MHz, ISAT 20/60 MHz, EXCL 30/50 MHz) mendorong kewajiban perluasan cakupan broadband ke luar Jawa. MTEL berpotensi menambah *3.000–3.500 tenant baru* atau setara *+Rp 360–420 miliar pendapatan tahunan*.
      ]
      #v(3pt)
      #grid(
        columns: (1fr, auto),
        text(size: 6.8pt, fill: PALETTE.muted)[+3.000 s.d. 3.500 Tenant],
        text(size: 6.8pt, weight: "bold", fill: PALETTE.pos)[+Rp 360–420 bn (FY27–29)],
      )
    ],
  )
])

#pagebreak()

// =====================================================================
// PAGE 3 — SEGMENT BREAKDOWN QUARTERLY + INCOME STATEMENT QUARTERLY
// =====================================================================
#page-wrap("RESEARCH — Equity Report", "27 Agt 2026", "MTEL", 3, PALETTE, [
  #section-header(3, "Segment Breakdown & Kinerja Laba Rugi Kuartalan", PALETTE)

  #text(size: 7.8pt)[
    Analisis momentum kinerja keuangan kuartalan menunjukkan pertumbuhan stabil pada segmen inti sewa menara dan lonjakan pendapatan fiber (+8% y/y) serta bisnis terkait menara (+15% y/y), merefleksikan diversifikasi portofolio infrastruktur digital yang solid.
  ]
  #v(4pt)

  #exhibit-header("Exhibit 5", "Pendapatan per Segmen: 1H26 vs 1H25 & Momentum Kuartalan (Rp Miliar)", "MTEL 1H26 Laporan Segmentasi (IDX)")
  #v(2pt)
  #fin-table(
    ("Segmen Bisnis", "1H25", "1H26", "YoY (%)", "Q2-25", "Q1-26", "Q2-26", "YoY (Q2)", "QoQ (%)"),
    (
      ("Tower Leasing", "3.798", "3.833", "+1,0%", "1.956", "1.847", "1.986", "+1,5%", "+7,5%"),
      ("Fiber Optic", "287", "309", "+8,0%", "147", "152", "157", "+6,8%", "+3,3%"),
      ("Tower-Related Business", "260", "299", "+15,0%", "113", "166", "133", "+17,7%", "-19,9%"),
      ("Reseller", "251", "251", "0,0%", "118", "129", "122", "+3,4%", "-5,4%"),
      ([*Total Pendapatan Segmen*], [*4.596*], [*4.691*], [*+2,1%*], [*2.334*], [*2.294*], [*2.398*], [*+2,7%*], [*+4,5%*]),
    ),
    palette: PALETTE,
  )

  #v(6pt)
  #exhibit-header("Exhibit 6", "Laporan Laba Rugi Kuartalan (1H25 vs 1H26 & Q2-25 vs Q2-26)", "Laporan Keuangan MTEL (IDX)")
  #v(2pt)
  #fin-table(
    ("Akun Laba Rugi (Rp Miliar)", "1H25", "1H26", "YoY (%)", "Q2-25", "Q1-26", "Q2-26", "YoY (Q2)", "QoQ (%)"),
    (
      ("Pendapatan Bersih (Revenue)", "4.596", "4.691", "+2,1%", "2.334", "2.294", "2.398", "+2,7%", "+4,5%"),
      ("Beban Pokok Pendapatan (COGS)", "(2.209)", "(2.348)", "+6,3%", "(1.109)", "(1.159)", "(1.189)", "+7,2%", "+2,6%"),
      ("Laba Kotor (Gross Profit)", "2.388", "2.343", "-1,9%", "1.226", "1.134", "1.209", "-1,4%", "+6,6%"),
      ("Beban Usaha (SG&A)", "(139)", "(149)", "+7,2%", "(79)", "(63)", "(86)", "+8,9%", "+36,5%"),
      ("Laba Usaha (EBIT)", "1.744", "1.667", "-4,4%", "898", "814", "853", "-5,0%", "+4,8%"),
      ("Beban Keuangan & Bunga", "(649)", "(569)", "-12,3%", "(308)", "(282)", "(287)", "-6,8%", "+1,8%"),
      ("Laba Sebelum Pajak (EBT)", "1.177", "1.175", "-0,2%", "630", "584", "591", "-6,2%", "+1,2%"),
      ("Beban Pajak Penghasilan", "(83)", "(64)", "-22,9%", "(62)", "(39)", "(25)", "-59,7%", "-35,9%"),
      ("EBITDA", "3.510", "3.510", "0,0%", "1.800", "1.717", "1.793", "-0,4%", "+4,4%"),
      ("Laba Bersih Tahun Berjalan", "1.094", "1.111", "+1,6%", "568", "545", "566", "-0,4%", "+3,9%"),
      ("EPS (IDR Penuh)", "13,00", "13,30", "+2,3%", "6,80", "6,52", "6,77", "-0,4%", "+3,8%"),
    ),
    palette: PALETTE,
  )

  #v(6pt)
  #card(PALETTE)[
    #text(weight: "bold", fill: PALETTE.ink)[Catatan Kinerja 1H26 & Efisiensi Beban Bunga]
    #v(2pt)
    #text(size: 7.2pt)[
      Laba bersih 1H26 tercatat sebesar Rp 1.111 miliar (+1,6% YoY) ditopang oleh penurunan beban keuangan sebesar 12,3% YoY menjadi Rp 569 miliar (vs Rp 649 miliar di 1H25) hasil dari repricing utang dan pelunasan pinjaman berbiaya tinggi, mengimbangi sedikit kenaikan beban depresiasi fiber optic.
    ]
  ]
])

#pagebreak()

// =====================================================================
// PAGE 4 — BALANCE SHEET, RATIOS & OPERATIONAL KPI QUARTERLY
// =====================================================================
#page-wrap("RESEARCH — Equity Report", "27 Agt 2026", "MTEL", 4, PALETTE, [
  #section-header(4, "Neraca Keuangan, Rasio & KPI Kuartalan", PALETTE)

  #exhibit-header("Exhibit 7", "Neraca Keuangan Kuartalan Ringkas (Rp Miliar)", "MTEL 1H26 (IDX)")
  #v(2pt)
  #fin-table(
    ("Pos Neraca", "1H25", "1H26", "YoY (%)", "Q2-25", "Q1-26", "Q2-26", "YoY (Q2)", "QoQ (%)"),
    (
      ("Kas & Setara Kas", "2.768", "1.952", "-29,5%", "2.768", "2.836", "1.952", "-29,5%", "-31,2%"),
      ("Utang Jangka Pendek (ST Debt)", "4.466", "4.416", "-1,1%", "4.466", "4.477", "4.416", "-1,1%", "-1,4%"),
      ("Utang Jangka Panjang (LT Debt)", "15.728", "16.575", "+5,4%", "15.728", "16.592", "16.575", "+5,4%", "-0,1%"),
      ("Total Liabilitas", "27.661", "28.055", "+1,4%", "27.661", "26.904", "28.055", "+1,4%", "+4,3%"),
      ("Ekuitas Bersih", "32.416", "32.051", "-1,1%", "32.416", "33.659", "32.051", "-1,1%", "-4,8%"),
      ("Total Aset", "60.076", "60.106", "+0,1%", "60.076", "60.563", "60.106", "+0,1%", "-0,8%"),
    ),
    palette: PALETTE,
  )

  #v(4pt)
  #exhibit-header("Exhibit 8", "Rasio Keuangan Kuartalan (12 Rasio Kunci)", "Perhitungan Analis & IDX")
  #v(2pt)
  #fin-table(
    ("Rasio Finansial", "1H25", "1H26", "Perubahan", "Q2-25", "Q1-26", "Q2-26", "YoY (Q2)", "QoQ (%)"),
    (
      ("Gross Profit Margin (GPM %)", "51,95%", "49,94%", "-2,01%", "52,51%", "49,45%", "50,41%", "-2,10%", "+0,96%"),
      ("Operating Profit Margin (OPM %)", "37,94%", "35,53%", "-2,41%", "38,46%", "35,48%", "35,58%", "-2,88%", "+0,10%"),
      ("Net Profit Margin (NPM %)", "23,81%", "23,69%", "-0,12%", "24,34%", "23,76%", "23,61%", "-0,73%", "-0,15%"),
      ("EBITDA Margin (%)", "76,36%", "74,83%", "-1,53%", "77,11%", "74,87%", "74,78%", "-2,33%", "-0,09%"),
      ("Return on Equity (ROE %)", "6,80%", "6,90%", "+0,10%", "7,00%", "6,50%", "7,10%", "+0,10%", "+0,60%"),
      ("Return on Assets (ROA %)", "3,60%", "3,70%", "+0,10%", "3,80%", "3,60%", "3,80%", "0,00%", "+0,20%"),
      ("Debt to Equity Ratio (DER x)", "0,62x", "0,65x", "+0,03x", "0,62x", "0,63x", "0,65x", "+0,03x", "+0,02x"),
      ("Debt to Assets Ratio (DAR x)", "0,46x", "0,47x", "+0,01x", "0,46x", "0,44x", "0,47x", "+0,01x", "+0,03x"),
      ("Liabilities to Equity (x)", "0,85x", "0,88x", "+0,03x", "0,85x", "0,80x", "0,88x", "+0,03x", "+0,08x"),
      ("Interest Coverage Ratio (ICR x)", "5,41x", "6,17x", "+0,76x", "5,85x", "6,08x", "6,25x", "+0,40x", "+0,17x"),
      ("Current Ratio (x)", "0,28x", "0,38x", "+0,10x", "0,25x", "0,47x", "0,38x", "+0,13x", "-0,09x"),
      ("Cash Ratio (%)", "5,00%", "8,00%", "+3,00%", "7,00%", "24,00%", "8,00%", "+1,00%", "-16,00%"),
    ),
    palette: PALETTE,
  )

  #v(4pt)
  #exhibit-header("Exhibit 9", "Operational KPI Kuartalan (Net Additions per Kuartal)", "Company data 1H26")
  #v(2pt)
  #fin-table(
    ("KPI Operasional", "1H25", "1H26", "YoY (%)", "1Q25", "2Q25", "3Q25", "4Q25", "1Q26", "2Q26"),
    (
      ("Menara (Tower Unit)", "39.782", "40.563", "+2,0%", "+189", "+189", "+320", "+128", "+97", "+236"),
      ("Kolokasi (Colocation)", "21.125", "23.303", "+10,3%", "+202", "+459", "+760", "+969", "+152", "+297"),
      ("Total Penyewa (Tenant)", "60.907", "63.866", "+4,9%", "+391", "+648", "+1.080", "+1.097", "+249", "+533"),
      ("Penyewa Reseller", "2.659", "2.650", "-0,3%", "-71", "-30", "+0", "-9", "+0", "+0"),
      ("Tenant inc. Reseller", "63.566", "66.516", "+4,6%", "+320", "+618", "+1.080", "+1.088", "+249", "+533"),
      ("Tenancy Ratio (x)", "1,53x", "1,57x", "+2,6%", "—", "—", "—", "—", "—", "—"),
      ("Fiber Optic (km)", "54.447", "59.239", "+8,8%", "+2.505", "+903", "+1.146", "+1.606", "+1.080", "+960"),
    ),
    palette: PALETTE,
  )
])

#pagebreak()

// =====================================================================
// PAGE 5 — DCF TABLE + BLENDED VALUATION + P/BV BANDS
// =====================================================================
#page-wrap("RESEARCH — Equity Report", "27 Agt 2026", "MTEL", 5, PALETTE, [
  #section-header(5, "Metodologi Valuasi: DCF, Blended & Bands", PALETTE)

  #grid(
    columns: (1.2fr, 1fr),
    column-gutter: 10pt,
    [
      #text(size: 9pt, weight: "bold", fill: PALETTE.brand_dark)[Metode 1: Discounted Cash Flow (DCF)]
      #v(2pt)
      #text(size: 6.8pt, fill: PALETTE.muted)[
        Asumsi: WACC 10,10%, Beta 0,65, Rf 6,96%, ERP 8,89%, CoE 12,74%, CoD 6,00%, We 60,8%, Wd 39,2%, g 1,50%
      ]
      #v(3pt)
      #exhibit-header("Exhibit 10", "Proyeksi Arus Kas Bebas (FCFF 2026F–2028F)", "Model DCF")
      #v(2pt)
      #fin-table(
        ("Komponen DCF (Rp bn)", "2026F", "2027F", "2028F"),
        (
          ("EBIT", "4.264", "4.750", "5.239"),
          ("EBIT (1 - Tax 6%)", "4.008", "4.465", "4.925"),
          ("(+) Depresiasi & Amortisasi", "3.188", "3.423", "3.658"),
          ("(-) Belanja Modal (Capex)", "(2.981)", "(2.709)", "(2.437)"),
          ("(+) Perubahan Modal Kerja", "+762", "+762", "+762"),
          ("Free Cash Flow (FCF)", "4.977", "4.941", "4.908"),
          ("Terminal Value (TV)", "—", "—", "72.736"),
        ),
        palette: PALETTE,
      )
      #v(3pt)
      #card(PALETTE)[
        #grid(
          columns: (1fr, auto),
          row-gutter: 2.5pt,
          text(size: 6.8pt)[Enterprise Value (EV)], text(size: 6.8pt, weight: "bold")[Rp 71.343 bn],
          text(size: 6.8pt)[Kas Bersih / (Utang Bersih)], text(size: 6.8pt, weight: "bold")[-(Rp 19.787 bn)],
          text(size: 6.8pt)[Nilai Ekuitas (Equity Value)], text(size: 6.8pt, weight: "bold")[Rp 51.556 bn],
          text(size: 7.2pt, weight: "bold")[Nilai Wajar DCF per Saham], text(size: 7.2pt, weight: "black", fill: PALETTE.brand_dark)[Rp 630],
        )
      ]
    ],
    [
      #text(size: 9pt, weight: "bold", fill: PALETTE.brand_dark)[Metode 2: Multiple EV/EBITDA]
      #v(2pt)
      #text(size: 6.8pt, fill: PALETTE.muted)[
        Target multiple 10,0x berdasarkan peers industri menara regional.
      ]
      #v(3pt)
      #fin-table(
        ("Parameter", "Nilai", "Satuan"),
        (
          ("Target EV/EBITDA", "10,0", "x"),
          ("EBITDA 2026F", "7.451", "Rp bn"),
          ("Implied EV", "74.510", "Rp bn"),
          ("Fair Value EV/EBITDA", "745", "Rp/saham"),
        ),
        palette: PALETTE,
      )

      #v(5pt)
      #text(size: 9pt, weight: "bold", fill: PALETTE.brand_dark)[Rekonsiliasi Valuasi Blended (60/40)]
      #v(2pt)
      #fin-table(
        ("Metode Valuasi", "Bobot", "Fair Value"),
        (
          ("DCF (WACC 10,1%, g 1,5%)", "60%", "Rp 630"),
          ("EV/EBITDA (10,0x FY26F)", "40%", "Rp 745"),
          ([*Target Price (Blended)*], [*100%*], [*Rp 635*]),
        ),
        palette: PALETTE,
      )
      #v(2pt)
      #text(size: 6.2pt, style: "italic", fill: PALETTE.muted)[Margin of Safety (MoS) yang diterapkan: 15%]
    ]
  )

  #v(6pt)
  #exhibit-header("Exhibit 11", "Pita Valuasi Historis P/BV 3-Tahun (Mean Reversion)", "IDX & Analisis Data")
  #v(2pt)
  #fin-table(
    ("Deviasi Standar", "P/BV (x)", "Implied Price", "Interpretasi & Posisi Pasar"),
    (
      ("STD +2 (Batas Atas Ekstrem)", "2,90x", "Rp 1.250", "Overvalued Ekstrem"),
      ("STD +1 (Batas Atas)", "2,50x", "Rp 1.080", "Overvalued Moderat"),
      ("Rerata 3 Tahun (Mean)", "2,10x", "Rp 900", "Rentang Nilai Wajar Historis"),
      ("STD -1 (Batas Bawah)", "1,70x", "Rp 730", "Undervalued Menarik"),
      ("STD -2 (Batas Bawah Ekstrem)", "1,30x", "Rp 560", "Undervalued Ekstrem"),
      ("Posisi Harga Kini (Rp 460)", "1,47x", "Rp 460", "BELOW AVERAGE (Peluang Akumulasi Diskon)"),
    ),
    palette: PALETTE,
  )

  #v(4pt)
  #chart-placeholder("Grafik Pita Valuasi Historis P/BV 3Y (1,47x Kini vs Rerata 2,10x)", caption: "Valuasi P/BV Berada di Dekat Batas Bawah STD-2 Menunjukkan Ruang Re-rating Signifikan", height: 50pt, palette: PALETTE)
])

#pagebreak()

// =====================================================================
// PAGE 6 — ABIDA FRIEND-STYLE DCF DEEP DIVE (AUDITABLE ENGINE)
// =====================================================================
#page-wrap("RESEARCH — Equity Report", "27 Agt 2026", "MTEL", 6, PALETTE, [
  #section-header(6, "Analisis DCF Komprehensif (Abida Massi Engine)", PALETTE)

  #text(size: 7.2pt, fill: PALETTE.muted)[
    Porting algoritma deterministik dari _abidamassi/dcf-valuation-tool_ untuk transparansi matematis audit, analisis sensitivitas 5x5, dan pengujian ketahanan skenario operasional.
  ]
  #v(3pt)

  // TODO Lane 6: real chart paths
  #grid(
    columns: (1fr, 1fr),
    column-gutter: 8pt,
    row-gutter: 4pt,
    [
      #exhibit-header("Exhibit 12", "WACC Breakdown", "CAPM & SBN 10Y")
      #v(1pt)
      #image("/tmp/render_mtel/charts/wacc_breakdown.png", width: 100%)
    ],
    [
      #exhibit-header("Exhibit 13", "Sensitivity Heatmap (WACC x g)", "Engine Sensitivitas 5x5")
      #v(1pt)
      #image("/tmp/render_mtel/charts/sensitivity_heatmap.png", width: 100%)
    ],
    [
      #exhibit-header("Exhibit 14", "Skenario Operasional", "Engine Skenario")
      #v(1pt)
      #image("/tmp/render_mtel/charts/scenario_bars.png", width: 100%)
    ],
    [
      #exhibit-header("Exhibit 15", "EV to Equity Bridge Waterfall", "Bridge Engine")
      #v(1pt)
      #image("/tmp/render_mtel/charts/ev_equity_waterfall.png", width: 100%)
    ]
  )

  #v(2pt)
  #grid(
    columns: (1.1fr, 1fr),
    column-gutter: 8pt,
    [
      #exhibit-header("Exhibit 16", "Matriks Sensitivitas Nilai Wajar: WACC vs g", "Engine Sensitivitas 5x5")
      #v(1pt)
      #fin-table(
        ("WACC \\ g", "1,00%", "1,25%", "1,50% (Base)", "1,75%", "2,00%"),
        (
          ("9,10%", "Rp 438 (-4,8%)", "Rp 453 (-1,6%)", "Rp 468 (+1,8%)", "Rp 485 (+5,5%)", "Rp 503 (+9,4%)"),
          ("9,60%", "Rp 399 (-13,2%)", "Rp 412 (-10,5%)", "Rp 425 (-7,5%)", "Rp 440 (-4,4%)", "Rp 455 (-1,1%)"),
          ("10,10% (Base)", "Rp 364 (-20,8%)", "Rp 376 (-18,4%)", "Rp 387 (-15,8%)", "Rp 400 (-13,1%)", "Rp 413 (-10,2%)"),
          ("10,60%", "Rp 334 (-27,5%)", "Rp 343 (-25,4%)", "Rp 353 (-23,2%)", "Rp 364 (-20,8%)", "Rp 376 (-18,3%)"),
          ("11,10%", "Rp 306 (-33,6%)", "Rp 314 (-31,7%)", "Rp 323 (-29,7%)", "Rp 333 (-27,7%)", "Rp 343 (-25,5%)"),
        ),
        palette: PALETTE,
      )
    ],
    [
      #exhibit-header("Exhibit 17", "Skenario Operasional & Jembatan Nilai", "Model Deterministik")
      #v(1pt)
      #fin-table(
        ("Skenario", "Nilai Wajar", "Upside / Downside", "Rekomendasi"),
        (
          ("BEAR (Rev +1%, EBIT 41,9%, g 1,0%)", "Rp 300", "-34,8%", "SELL"),
          ("BASE (Rev +4%, EBIT 42,9%, g 1,5%)", "Rp 387", "-15,8%", "SELL (Overvalued)"),
          ("BULL (Rev +7%, EBIT 43,9%, g 2,0%)", "Rp 490", "+6,5%", "HOLD"),
        ),
        palette: PALETTE,
      )
      #v(2pt)
      #card(PALETTE)[
        #text(size: 6.8pt, weight: "bold", fill: PALETTE.ink)[Jembatan Nilai EV ke Ekuitas (Abida Massi Model):] \
        #text(size: 6.2pt)[
          PV Arus Kas Eksplisit: *Rp 20,17 T* \
          (+) PV Nilai Terminal: *Rp 31,18 T* \
          (=) Enterprise Value (EV): *Rp 51,35 T* \
          (+) Kas & Setara Kas: *+Rp 1,64 T* \
          (-) Total Utang Berbunga: *-(Rp 21,43 T)* \
          (=) Implied Equity Value: *Rp 31,56 T* \
          *Fair Value per Saham Model Standalone: Rp 387 (Downside -15,8% vs Rp 460)*
        ]
      ]
    ]
  )
])

#pagebreak()

// =====================================================================
// PAGE 7 — FINANCIAL HIGHLIGHTS 6Y & INVESTMENT THESIS
// =====================================================================
#page-wrap("RESEARCH — Equity Report", "27 Agt 2026", "MTEL", 7, PALETTE, [
  #section-header(7, "Ringkasan Finansial 6Y & Tesis Investasi", PALETTE)

  #exhibit-header("Exhibit 18", "Financial Highlights 6 Tahun (2023A – 2028F)", "Bloomberg, Company & Estimasi Riset")
  #v(2pt)
  #fin-table(
    ("Metrik Finansial", "2023A", "2024A", "2025A", "2026F", "2027F", "2028F"),
    (
      ("Pendapatan Bersih (Rp bn)", "8.595", "9.308", "9.534", "9.937", "10.360", "10.795"),
      ("Laba Bersih (Rp bn)", "2.010", "2.104", "2.119", "2.169", "2.362", "2.571"),
      ("EPS (IDR Penuh)", "24", "26", "26", "27", "29", "32"),
      ("Marjin EBITDA (%)", "54,0%", "74,0%", "63,0%", "75,0%", "75,0%", "74,0%"),
      ("Marjin Laba Bersih (NPM %)", "23,4%", "22,6%", "22,2%", "21,8%", "22,8%", "23,8%"),
      ("Dividend Yield (%)", "2,60%", "3,93%", "2,79%", "3,14%", "3,42%", "3,72%"),
      ("Return on Equity (ROE %)", "6,0%", "6,0%", "6,0%", "6,0%", "7,0%", "7,0%"),
      ("Price to Earnings (P/E x)", "29,0x", "25,2x", "26,9x", "23,9x", "21,9x", "20,1x"),
      ("Price to Book Value (P/BV x)", "1,70x", "1,59x", "1,71x", "1,53x", "1,50x", "1,47x"),
      ("EV/EBITDA (x)", "16,3x", "10,5x", "12,9x", "9,6x", "9,0x", "8,5x"),
    ),
    palette: PALETTE,
  )

  #v(6pt)
  #exhibit-header("Exhibit 19", "Trajektori Marjin EBITDA & Tenancy Ratio", "Laporan Keuangan MTEL & Proyeksi")
  #v(2pt)
  #chart-placeholder("Trajektori Marjin EBITDA (54% -> 75%) & Tenancy Ratio (1,53x -> 1,60x)", caption: "Skala Ekonomi dan Efisiensi Capex Menopang Ekspansi Margin Jangka Panjang", height: 55pt, palette: PALETTE)

  #v(6pt)
  #text(size: 9.5pt, weight: "bold", fill: PALETTE.brand_dark)[3 Pilar Utama Tesis Investasi]
  #v(3pt)

  #grid(
    columns: (1fr, 1fr, 1fr),
    gutter: 6pt,
    card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.ink)[1. KPI adalah Tesis Inti]
      #v(2pt)
      #text(size: 6.8pt)[
        Tenancy ratio 1,57x dan jaringan fiber 59,2k km mencerminkan kualitas arus kas recurring yang kontraktual (tenor 10 tahun) dengan perlindungan inflasi.
      ]
    ],
    card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.ink)[2. Sinergi Merger Operator]
      #v(2pt)
      #text(size: 6.8pt)[
        Merger PST & UMT efektif 1 Juli 2026 menaikkan utilisasi menara ke arah >1,60x serta memicu permintaan fiberisasi dan power backup terintegrasi.
      ]
    ],
    card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.ink)[3. Katalis Lelang Spektrum]
      #v(2pt)
      #text(size: 6.8pt)[
        Alokasi pita 700MHz/2,6GHz mendorong MNO menambah 3.000–3.500 tenant baru (+Rp 360–420 bn) untuk ekspansi cakupan 4G/5G luar Jawa.
      ]
    ],
  )
])

#pagebreak()

// =====================================================================
// PAGE 8 — INCOME STATEMENT 6Y & BALANCE SHEET 6Y
// =====================================================================
#page-wrap("RESEARCH — Equity Report", "27 Agt 2026", "MTEL", 8, PALETTE, [
  #section-header(8, "Laporan Keuangan 6 Tahun: Laba Rugi & Neraca", PALETTE)

  #exhibit-header("Exhibit 20", "Laporan Laba Rugi Komprehensif (Rp Miliar — FY23A s.d. FY28F)", "Bloomberg, Company & Estimasi Riset")
  #v(2pt)
  #fin-table(
    ("Akun Laba Rugi", "2023A", "2024A", "2025A", "2026F", "2027F", "2028F"),
    (
      ("Pendapatan Bersih (Revenue)", "8.595", "9.308", "9.534", "9.937", "10.360", "10.795"),
      ("Beban Pokok Pendapatan (COGS)", "(4.379)", "(4.507)", "(4.665)", "(4.862)", "(5.069)", "(5.282)"),
      ("Laba Kotor (Gross Profit)", "4.216", "4.801", "4.869", "5.075", "5.291", "5.513"),
      ("Laba Usaha (Operating Profit)", "2.057", "4.173", "3.514", "4.264", "4.455", "4.643"),
      ("Beban Bunga Pinjaman", "(1.333)", "(1.357)", "(1.306)", "(1.287)", "(1.271)", "(1.243)"),
      ("Penghasilan Bunga Bersih", "(441)", "(97)", "(1.145)", "+15", "+41", "+77"),
      ("EBITDA", "4.658", "6.910", "6.036", "7.451", "7.730", "8.007"),
      ("Laba Sebelum Pajak (EBT)", "2.138", "2.261", "2.248", "2.301", "2.505", "2.727"),
      ("Beban Pajak Penghasilan", "(128)", "(157)", "(129)", "(132)", "(143)", "(156)"),
      ("Kepentingan Non-Pengendali", "0", "0", "0", "0", "0", "0"),
      ("Laba Bersih Tahun Berjalan", "2.010", "2.104", "2.119", "2.169", "2.362", "2.571"),
      ("EPS (IDR Penuh)", "24,3", "25,6", "26,0", "26,6", "29,0", "31,5"),
    ),
    palette: PALETTE,
  )

  #v(6pt)
  #exhibit-header("Exhibit 21", "Neraca Keuangan Konsolidasian (Rp Miliar — FY23A s.d. FY28F)", "Bloomberg, Company & Estimasi Riset")
  #v(2pt)
  #fin-table(
    ("Pos Neraca", "2023A", "2024A", "2025A", "2026F", "2027F", "2028F"),
    (
      ("Kas & Setara Kas", "879", "597", "609", "1.643", "3.075", "4.425"),
      ("Piutang Usaha (AR)", "1.607", "2.004", "2.212", "1.932", "1.870", "1.949"),
      ("Aset Tetap (Fixed Assets)", "51.246", "52.918", "53.782", "53.576", "52.374", "51.168"),
      ("Aset Lain-Lain", "3.278", "2.622", "1.747", "1.745", "1.785", "1.825"),
      ("Total Aset (Total Assets)", "57.010", "58.140", "58.350", "58.896", "59.104", "59.367"),
      ("Liabilitas Jangka Pendek (ST)", "6.732", "8.082", "4.254", "4.500", "4.399", "4.298"),
      ("Liabilitas Jangka Pendek Lain", "4.339", "4.204", "3.246", "3.286", "3.371", "3.462"),
      ("Liabilitas Jangka Panjang (LT)", "11.660", "12.214", "17.224", "16.930", "16.550", "16.169"),
      ("Liabilitas Jangka Panjang Lain", "241", "253", "275", "286", "298", "311"),
      ("Total Liabilitas (Liabilities)", "22.973", "24.753", "24.999", "25.002", "24.619", "24.240"),
      ("Total Ekuitas (Equity)", "34.038", "33.387", "33.351", "33.894", "34.484", "35.127"),
      ("Nilai Buku per Saham (BVPS IDR)", "412", "407", "409", "416", "423", "431"),
    ),
    palette: PALETTE,
  )
])

#pagebreak()

// =====================================================================
// PAGE 9 — CASH FLOW 6Y & COMPREHENSIVE RATIOS (30+)
// =====================================================================
#page-wrap("RESEARCH — Equity Report", "27 Agt 2026", "MTEL", 9, PALETTE, [
  #section-header(9, "Arus Kas 6 Tahun & Rasio Finansial Lengkap", PALETTE)

  #grid(
    columns: (1fr, 1.15fr),
    column-gutter: 8pt,
    [
      #exhibit-header("Exhibit 22", "Laporan Arus Kas 6Y (Rp bn)", "Estimasi Riset")
      #v(1pt)
      #compact-fin-table(
        ("Arus Kas (Rp bn)", "2023A", "2024A", "2025A", "2026F", "2027F", "2028F"),
        (
          ("Laba Bersih", "2.010", "2.104", "2.119", "2.169", "2.362", "2.571"),
          ("Depresiasi", "2.601", "2.736", "2.522", "3.188", "3.274", "3.365"),
          ("Δ Modal Kerja", "(4.733)", "(3.935)", "(9.020)", "(4.760)", "(5.598)", "(6.033)"),
          ("Arus Kas Operasi (CFO)", "(122)", "905", "(4.378)", "598", "38", "(98)"),
          ("Capex", "(4.989)", "(1.672)", "(865)", "+207", "+1.202", "+1.206"),
          ("Lainnya (Investasi)", "(416)", "+569", "+259", "(30)", "(31)", "(32)"),
          ("Arus Kas Investasi (CFI)", "(5.405)", "(1.103)", "(606)", "+176", "+1.171", "+1.174"),
          ("Dividen Dibayar", "(18)", "(25)", "(19)", "(20)", "(22)", "(24)"),
          ("Perubahan Bersih Utang", "+68", "0", "+5.010", "(294)", "(380)", "(381)"),
          ("Lainnya (Pendanaan)", "+17", "(59)", "+5", "+574", "+625", "+679"),
          ("Arus Kas Pendanaan (CFF)", "+68", "(85)", "+4.996", "+260", "+223", "+274"),
          ("Efek Kurs Valas", "0", "0", "0", "0", "0", "0"),
          ("Perubahan Kas Bersih", "(5.460)", "(282)", "+12", "+1.034", "+1.432", "+1.350"),
          ("Kas Awal Periode", "6.339", "879", "597", "609", "1.643", "3.075"),
          ("Kas Akhir Periode", "879", "597", "609", "1.643", "3.075", "4.425"),
        ),
        palette: PALETTE,
      )
    ],
    [
      #exhibit-header("Exhibit 23", "Rasio Keuangan Lengkap (30 Metrik)", "Kalkulasi Riset")
      #v(1pt)
      #compact-fin-table(
        ("Rasio Keuangan & Efisiensi", "2023A", "2024A", "2025A", "2026F", "2027F", "2028F"),
        (
          ("Pertumbuhan Pendapatan (%)", "+11,0%", "+11,0%", "+2,0%", "+4,0%", "+4,0%", "+4,0%"),
          ("Pertumbuhan Laba Kotor (%)", "+15,0%", "+14,0%", "+1,0%", "+4,0%", "+4,0%", "+4,0%"),
          ("Pertumbuhan Laba Usaha (%)", "+119,0%", "+103,0%", "-16,0%", "+21,0%", "+4,0%", "+4,0%"),
          ("Pertumbuhan EBITDA (%)", "+38,0%", "+48,0%", "-13,0%", "+23,0%", "+4,0%", "+4,0%"),
          ("Pertumbuhan Laba Bersih (%)", "+13,0%", "+5,0%", "+1,0%", "+2,0%", "+9,0%", "+9,0%"),
          ("Pertumbuhan EPS (%)", "+13,0%", "+5,0%", "+1,0%", "+2,0%", "+9,0%", "+9,0%"),
          ("Gross Margin (%)", "49,0%", "52,0%", "51,0%", "51,0%", "51,0%", "51,0%"),
          ("EBITDA Margin (%)", "54,0%", "74,0%", "63,0%", "75,0%", "75,0%", "74,0%"),
          ("EBIT Margin (%)", "24,0%", "45,0%", "37,0%", "43,0%", "43,0%", "43,0%"),
          ("Pretax Margin (%)", "25,0%", "24,0%", "24,0%", "23,0%", "24,0%", "25,0%"),
          ("Net Margin (%)", "23,0%", "23,0%", "22,0%", "22,0%", "23,0%", "24,0%"),
          ("Return on Equity (ROE %)", "6,0%", "6,0%", "6,0%", "6,0%", "7,0%", "7,0%"),
          ("Return on Assets (ROA %)", "4,0%", "4,0%", "4,0%", "4,0%", "4,0%", "4,0%"),
          ("Current Ratio (x)", "0,3x", "0,3x", "0,4x", "0,5x", "0,7x", "0,8x"),
          ("Quick Ratio (x)", "0,3x", "0,3x", "0,4x", "0,5x", "0,7x", "0,8x"),
          ("LT Debt / Equity (x)", "0,34x", "0,37x", "0,52x", "0,50x", "0,48x", "0,46x"),
          ("Debt to Equity (DER x)", "0,67x", "0,74x", "0,75x", "0,74x", "0,71x", "0,69x"),
          ("Debt to Assets (DAR x)", "0,40x", "0,43x", "0,43x", "0,42x", "0,42x", "0,41x"),
          ("Interest Coverage (x)", "2,0x", "3,0x", "3,0x", "3,0x", "4,0x", "4,0x"),
          ("Inventory Turnover (x)", "6,5x", "5,2x", "4,5x", "4,8x", "5,4x", "5,7x"),
          ("AP Turnover (days)", "56", "71", "81", "76", "67", "65"),
          ("Cash Ratio (%)", "8,0%", "5,0%", "8,0%", "21,0%", "40,0%", "57,0%"),
          ("Sustainable Growth (%)", "1,0%", "0,0%", "2,0%", "2,0%", "2,0%", "2,0%"),
          ("Earnings Yield (%)", "3,0%", "4,0%", "4,0%", "4,0%", "5,0%", "5,0%"),
          ("Dividend Yield (%)", "2,59%", "3,93%", "2,79%", "3,14%", "3,42%", "3,72%"),
          ("Price to Earnings (PE x)", "29,0x", "25,2x", "26,9x", "23,9x", "21,9x", "20,1x"),
          ("Price to Book (PBV x)", "1,7x", "1,6x", "1,7x", "1,5x", "1,5x", "1,5x"),
          ("Price to Sales (P/S x)", "6,8x", "5,7x", "6,0x", "5,2x", "5,0x", "4,8x"),
          ("EV/EBITDA (x)", "16,3x", "10,5x", "12,9x", "9,6x", "9,0x", "8,5x"),
          ("Net Debt / EBITDA (x)", "4,4x", "4,1x", "3,8x", "2,7x", "1,7x", "1,0x"),
        ),
        palette: PALETTE,
      )
    ]
  )
])

#pagebreak()

// =====================================================================
// PAGE 10 — PEERS COMPARISON & RISK ANALYSIS
// =====================================================================
#page-wrap("RESEARCH — Equity Report", "27 Agt 2026", "MTEL", 10, PALETTE, [
  #section-header(10, "Perbandingan Peers & Analisis Risiko", PALETTE)

  #exhibit-header("Exhibit 24", "Perbandingan Emiten Menara Telekomunikasi Regional (Peers)", "IDX, FactSet & Laporan Keuangan")
  #v(2pt)
  #fin-table(
    ("Ticker / Emiten", "EV/EBITDA", "Tenancy", "Jumlah Menara", "Fiber (km)", "ROE (%)", "P/E (x)", "Karakteristik Aset"),
    (
      ("MTEL (Dayamitra)", "10,1x", "1,57x", "40.563", "59.239 km", "6,0%", "23,9x", "Menara terbesar RI, Telkom group backing"),
      ("TOWR (Sarana Menara)", "8,9x", "1,70x", "31.000", "120.000 km", "18,0%", "22,0x", "Pemimpin penetrasi fiber optik non-captive"),
      ("TBIG (Tower Bersama)", "8,0x", "1,90x", "22.000", "35.000 km", "24,0%", "18,0x", "Tenancy ratio tertinggi di industri"),
      ("EDOT (EdgePoint)", "9,8x", "1,40x", "20.000", "15.000 km", "8,0%", "25,0x", "Ekspansi regional ASEAN agresif"),
      ([*Rata-rata Peers Menara*], [*9,2x*], [*1,64x*], [*28.390*], [*57.310 km*], [*14,0%*], [*22,2x*], [*Sektor Infrastruktur Digital*]),
    ),
    palette: PALETTE,
  )

  #v(6pt)
  #text(size: 9.5pt, weight: "bold", fill: PALETTE.brand_dark)[Faktor Risiko Utama Spesifik Sektor Infrastruktur]
  #v(3pt)

  #grid(
    columns: (1fr, 1fr),
    gutter: 6pt,
    card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.neg)[1. Ketergantungan Operator Utama (Telkomsel)]
      #v(1pt)
      #text(size: 6.8pt)[
        Telkomsel menyumbang porsi mayoritas pendapatan sewa. Penyesuaian belanja modal atau renegosiasi tarif sewa menara induk dapat mempengaruhi pertumbuhan marjin.
      ]
    ],
    card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.neg)[2. Tekanan Kompetisi Harga (TOWR & TBIG)]
      #v(1pt)
      #text(size: 6.8pt)[
        Persaingan ketat dalam tender kolokasi dan bundling fiber dapat memicu perang harga sewa menara pada rute-rute padat di Pulau Jawa.
      ]
    ],
    card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.neg)[3. Disrupsi Teknologi (Open RAN & Satelit LEO)]
      #v(1pt)
      #text(size: 6.8pt)[
        Pengembangan konstelasi satelit orbit rendah (LEO) dan teknologi transmisi nirkabel alternatif dapat mengurangi urgensi pembangunan menara makro di area terpencil.
      ]
    ],
    card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.neg)[4. Regulasi Spektrum & Tata Ruang Pemda]
      #v(1pt)
      #text(size: 6.8pt)[
        Keterlambatan perizinan retribusi pengendalian menara telekomunikasi di tingkat Pemda serta perubahan regulasi lelang spektrum Komdigi berisiko menunda rollout.
      ]
    ],
    card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.neg)[5. Sensitivitas Suku Bunga & Utang Rp 21 Triliun]
      #v(1pt)
      #text(size: 6.8pt)[
        Total utang berbunga mencapai Rp 21,43 T; kenaikan suku bunga acuan BI Rate sebesar 100 bps berpotensi meningkatkan beban bunga tahunan dan menekan nilai wajar DCF.
      ]
    ],
    card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.neg)[6. Risiko Bencana Alam & Keandalan SLA]
      #v(1pt)
      #text(size: 6.8pt)[
        Sebaran 40k menara di ring of fire terpapar risiko gempa, banjir, dan pemadaman listrik yang dapat memicu penalti uptime SLA operasional kepada MNO.
      ]
    ],
  )
])

#pagebreak()

// =====================================================================
// PAGE 11 — RATING GUIDE (9 ROWS), REGULATORY DISCLAIMER & CONTACT
// =====================================================================
#page-wrap("RESEARCH — Equity Report", "27 Agt 2026", "MTEL", 11, PALETTE, [
  #section-header(11, "Panduan Rating, Disklaimer Regulasi & Kontak", PALETTE)

  #exhibit-header("Exhibit 25", "Panduan Pemeringkatan Rekomendasi Investasi (9 Kategori)", "Standar Metodologi Riset Ekuitas")
  #v(2pt)
  #fin-table(
    ("Kategori Peringkat", "Definisi Kriteria (12 Bulan Eks-Dividen)", "Implikasi bagi Keputusan Investor"),
    (
      ("SECTOR — OVERWEIGHT", "Sektor & industri berpotensi kuat dan kondisi makro mendukung", "Alokasi bobot di atas rata-rata portofolio acuan"),
      ("SECTOR — NEUTRAL", "Sektor & industri stabil atau performa cenderung flat", "Alokasi bobot setara dengan portofolio acuan"),
      ("SECTOR — UNDERWEIGHT", "Sektor & industri menghadapi tantangan fundamental berat", "Alokasi bobot di bawah rata-rata portofolio acuan"),
      ("STOCK — BUY", "Ekspektasi total return > +15% dalam 12 bulan ke depan", "Potensi apresiasi substansial di atas biaya modal"),
      ("STOCK — TRADING BUY", "Ekspektasi total return +5% s/d +15% (jangka pendek/menengah)", "Peluang beli berbasis momentum atau katalis spesifik"),
      ("STOCK — HOLD", "Ekspektasi total return -10% s/d +15% dalam 12 bulan", "Valuasi wajar; profil risk-reward berimbang"),
      ("STOCK — SELL", "Ekspektasi total return < -15% dalam 12 bulan ke depan", "Risiko penurunan harga material; disarankan realisasi"),
      ("STOCK — TRADING SELL", "Ekspektasi total return -5% s/d -15% (jangka pendek/menengah)", "Peluang profit-taking taktis saat volatilitas"),
      ("STOCK — NOT RATED", "Saham berada di luar cakupan riset reguler / suspensi", "Tidak ada target harga atau rating aktif yang berlaku"),
    ),
    palette: PALETTE,
  )

  #v(6pt)
  #card(PALETTE)[
    #text(weight: "bold", fill: PALETTE.ink)[Sertifikasi Analis & Independensi Penilaian]
    #v(2pt)
    #text(size: 7pt)[
      Analis riset yang tercantum dalam laporan ini menyatakan secara independen bahwa: (1) Semua pandangan yang diungkapkan secara akurat merefleksikan penilaian fundamental terhadap PT Dayamitra Telekomunikasi Tbk (MTEL); (2) Kompensasi analis tidak berhubungan, baik langsung maupun tidak langsung, dengan rekomendasi atau target harga spesifik; (3) Analis tidak memiliki kepemilikan saham finansial material pada emiten yang dianalisis.
    ]
  ]

  #v(5pt)
  #card(PALETTE)[
    #text(weight: "bold", fill: PALETTE.ink)[Disklaimer Kepatuhan Otoritas Jasa Keuangan (OJK)]
    #v(2pt)
    #text(size: 6.8pt, fill: PALETTE.muted)[
      Laporan ini diterbitkan semata-mata untuk tujuan penyediaan informasi edukatif dan riset pasar modal bagi investor. Dokumen ini bukan merupakan penawaran, ajakan, atau rekomendasi resmi untuk membeli atau menjual instrumen keuangan apa pun. Estimasi dan proyeksi didasarkan pada data publik yang diyakini dapat diandalkan (IDX, KSEI, Laporan Keuangan Emiten, Bloomberg), namun tidak ada garansi atas kelengkapan dan keakuratannya. Kinerja masa lalu bukan merupakan indikasi atau jaminan kinerja masa depan. Setiap keputusan investasi merupakan tanggung jawab mandiri investor sepenuhnya.
    ]
  ]

  #v(5pt)
  #card(PALETTE)[
    #grid(
      columns: (1fr, 1fr),
      column-gutter: 12pt,
      [
        #text(size: 7pt, weight: "bold", fill: PALETTE.muted)[DISIAPKAN OLEH & TIM RISET]
        #v(2pt)
        #text(size: 6.8pt)[
          - *Institusi:* RESEARCH — Sectors Hackathon 2026
          - *Tanggal Publikasi:* 27 Agustus 2026 · Bahasa: Indonesia (ID)
          - *Analis Utama:* Sukarno Alatas (Senior Equity Analyst)
          - *Kontak Surel:* research\@skt.id
        ]
      ],
      [
        #text(size: 7pt, weight: "bold", fill: PALETTE.muted)[KANTOR PUSAT & PROVENANCE]
        #v(2pt)
        #text(size: 6.8pt)[
          - *Kantor Pusat:* Treasury Tower 27th Floor Unit A, District 8 — Jakarta
          - *Engine Valuasi:* scripts/dcf_engine.py & scripts/blended_engine.py
          - *Audit Port:* abidamassi/dcf-valuation-tool (WACC 10,10%)
          - *Portal Riset:* www.skt.id/research
        ]
      ]
    )
  ]
])
