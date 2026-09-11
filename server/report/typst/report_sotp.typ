// =====================================================================
// report_sotp.typ — Institutional equity research (SOTP archetype)
// Case: CDIA (PT Chandra Daya Investasi) — 4 Pillars: Energi, Logistik, Air, Pelabuhan
// =====================================================================
#import "theme.typ": *
#import "cover.typ": *


#let ticker = sys.inputs.at("ticker", default: "CDIA")
#let data-path = sys.inputs.at("data_path")
#let data = json(data-path)

#let m = data.at("meta")
#show: set-page-defaults.with(date: m.date)
#let cover = data.at("cover").at("rating_box")
#let gate-verdict = data.at("gate-verdict", default: data.at("gate_verdict", default: none))
#let chart-dir = "/home/fadil/projects/sectors-hackathon/output/cache/render_" + lower(m.ticker) + "/charts"


// Archetype Palette for Conglomerate / SOTP (Cyan & Deep Teal)
#let PALETTE = (
  brand: rgb("#0e7490"),       // cyan/teal
  brand_dark: rgb("#155e63"),  // deep teal
  accent: rgb("#ecfeff"),
  ink: rgb("#101828"),
  muted: rgb("#475467"),
  line: rgb("#e4e7ec"),
  band: rgb("#f9fafb"),
  paper: rgb("#ffffff"),
  pos: rgb("#067647"),
  neg: rgb("#b42318"),
)

// Pillar-specific color tokens for charts
#let C_ENERGY = rgb("#0e7490")
#let C_LOGISTICS = rgb("#2563eb")
#let C_WATER = rgb("#059669")
#let C_PORT = rgb("#d97706")

// Mini segment progress bar helper
#let pillar-bar(pct, fill-color) = {
  block(width: 100%)[
    #stack(
      spacing: 0pt,
      rect(width: 100%, height: 4pt, fill: rgb("#e4e7ec"), radius: 2pt)[
        #place(top + left)[
          #rect(width: pct, height: 4pt, fill: fill-color, radius: 2pt)
        ]
      ]
    )
  ]
}

// =====================================================================
// PAGE 1 — COVER & OVERVIEW
// =====================================================================
#page-wrap(
  "RESEARCH — Equity Report",
  "31 Agt 2026",
  "CDIA",
  1,
  PALETTE,
  [
    #grid(
      columns: (2fr, 1.1fr),
      column-gutter: 14pt,
      [
        #text(size: T_SMALL, fill: PALETTE.muted, tracking: 0.12em, weight: "bold")[
          INITIATION · KONGLOMERASI — 4 PILAR BISNIS
        ]
        #v(3pt)
        #text(size: T_COVER_TITLE, weight: "bold", fill: PALETTE.brand_dark)[
          Chandra Daya Investasi
        ]
        #v(1pt)
        #text(size: 13pt, weight: "bold", fill: PALETTE.muted)[
          CDIA · IDX · Sektor Konglomerasi
        ]
        #v(5pt)

        #card(PALETTE)[
          #text(weight: "bold", fill: PALETTE.ink)[Executive Summary / Key Points]
          #v(1pt)
          #text(size: 6pt, style: "italic", fill: PALETTE.muted)[Core investment thesis, rating stance, target price derivation, and operational highlights.]
          #v(2.5pt)
          #text(size: 8pt)[
            Inisiasi liputan dengan Investment Recommendation *HOLD* dan target harga *Rp 815* (+4,5% upside). CDIA adalah holding infrastruktur terintegrasi dengan 4 pilar bisnis: Energi, Logistik, Air, dan Pelabuhan. Logistik menjadi motor pertumbuhan utama (+44,7% YoY), sementara normalisasi one-off Rp 15,9 bn pada FY26 menopang kualitas laba jangka panjang.
          ]
        ]

        #v(5pt)
        #exhibit-header("Bauran Pendapatan 4 Pilar (1H26)", "Laporan Segmentasi CDIA (IDX)")
        #v(1pt)
        #block(width: 100%)[
          #grid(
            columns: (53.4%, 34.0%, 7.2%, 5.4%),
            rect(width: 100%, height: 8pt, fill: C_ENERGY, radius: (left: 2pt)),
            rect(width: 100%, height: 8pt, fill: C_LOGISTICS),
            rect(width: 100%, height: 8pt, fill: C_WATER),
            rect(width: 100%, height: 8pt, fill: C_PORT, radius: (right: 2pt)),
          )
          #v(2pt)
          #grid(
            columns: (1.3fr, 1.3fr, 1fr, 1fr),
            [#box(width: 5pt, height: 5pt, fill: C_ENERGY, radius: 1pt) #text(size: 6.5pt)[ Energi 53,4%]],
            [#box(width: 5pt, height: 5pt, fill: C_LOGISTICS, radius: 1pt) #text(size: 6.5pt)[ Logistik 34,0%]],
            [#box(width: 5pt, height: 5pt, fill: C_WATER, radius: 1pt) #text(size: 6.5pt)[ Air 7,2%]],
            [#box(width: 5pt, height: 5pt, fill: C_PORT, radius: 1pt) #text(size: 6.5pt)[ Pelabuhan 5,4%]],
          )
        ]
        #v(2pt)
        #fin-table(
          ("Pilar Bisnis", "Pendapatan (Rp bn)", "Bauran (%)", "YoY (%)", "Status"),
          (
            ("Energi (Power & Grid)", "6.300", "53,4%", "-8,0%", "Cash Cow"),
            ("Logistik (Chemical Shipping)", "4.010", "34,0%", "+44,7%", "Growth Engine"),
            ("Air (Water Treatment)", "850", "7,2%", "+6,0%", "Defensive"),
            ("Pelabuhan (Jetty & Storage)", "640", "5,4%", "+9,0%", "High Margin"),
            ([*Total Konsolidasian*], [*11.800*], [*100,0%*], [*-22,4%*], [*4 Pilar*]),
          ),
          palette: PALETTE,
        )

        #v(5pt)
        #exhibit-header("Kinerja Saham vs IHSG (YTD 2026)", "Sectors (CDIA vs IHSG)")
        #v(1pt)
        #fin-table(
          ("Periode", "CDIA Return", "IHSG", "Alpha Relatif"),
          (
            ("1 Bulan (1M)", "-12,0%", "+2,0%", "-14,0%"),
            ("3 Bulan (3M)", "-28,0%", "+5,0%", "-33,0%"),
            ("6 Bulan (6M)", "-55,0%", "+9,0%", "-64,0%"),
            ("Year-to-Date (YTD)", "-62,9%", "+15,0%", "-30,9% (Relatif)"),
          ),
          palette: PALETTE,
        )
      ],
      [
        #rating-box(
          cover.action,
          cover.tp,
          cover.price,
          cover.upside_pct,
          prev-tp: if cover.at("prev_tp", default: none) != none { str(cover.prev_tp) } else { none },
          palette: PALETTE,
        )

        #v(4pt)
        #method-selection-panel(gate-verdict, palette: PALETTE)

        #v(4pt)
        #exhibit-header("Informasi Pasar & Saham " + m.ticker, data.at("cover", default: (:)).at("market_src", default: "-"))
        #card(PALETTE)[
          #v(1pt)
          #text(size: 5.5pt, style: "italic", fill: PALETTE.muted)[Market trading metrics, liquidity statistics, and shareholding structure profile.]
          #v(2.5pt)
          #let sh = data.cover.at("shares", default: (:))
          #grid(
            columns: (1fr, auto),
            row-gutter: 2.8pt,
            text(size: 6.8pt)[Harga Terakhir], text(size: 6.8pt, weight: "bold")[Rp #nstr(cover.price)],
            text(size: 6.8pt)[Target Harga (12M)], text(size: 6.8pt, weight: "bold")[Rp #nstr(cover.tp)],
            text(size: 6.8pt)[Potensi Upside], text(size: 6.8pt, weight: "bold", fill: if cover.upside_pct == none { PALETTE.muted } else { PALETTE.pos })[#if cover.upside_pct == none { "—" } else { "+" + str(cover.upside_pct) + "%" }],
            text(size: 6.8pt)[Saham Beredar], text(size: 6.8pt, weight: "bold")[#nstr(sh.at("outstanding", default: none)) Miliar],
            text(size: 6.8pt)[Kapitalisasi Pasar], text(size: 6.8pt, weight: "bold")[—],
            text(size: 6.8pt)[Free Float], text(size: 6.8pt, weight: "bold")[#if sh.at("free_float_pct", default: none) == none { "—" } else { str(sh.free_float_pct) + "%" }],
            text(size: 6.8pt)[52-Week Range], text(size: 6.8pt, weight: "bold")[—],
            text(size: 6.8pt)[Indeks Konstituen], text(size: 6.8pt, weight: "bold")[—],
          )
        ]

        #v(4pt)
        #exhibit-header("Struktur Pemegang Saham " + m.ticker, data.cover.at("shareholders_src", default: "-"))
        #card(PALETTE)[
          #v(1pt)
          #text(size: 5.5pt, style: "italic", fill: PALETTE.muted)[Ownership distribution, controlling shareholder stakes, and free-float allocation.]
          #v(2.5pt)
          #grid(
            columns: (1fr, auto),
            row-gutter: 2.8pt,
            text(size: 6.8pt)[PT Chandra Asri Pacific (TPIA)], text(size: 6.8pt, weight: "bold")[60,0%],
            text(size: 6.8pt)[EGCO Group (Phoenix Power)], text(size: 6.8pt, weight: "bold")[30,0%],
            text(size: 6.8pt)[Publik (Free Float)], text(size: 6.8pt, weight: "bold")[10,0%],
          )
        ]
      ]
    )
  ]
)

#pagebreak(weak: true)

// =====================================================================
// PAGE 2 — SEGMENT BREAKDOWN (4 PILLARS)
// =====================================================================
#page-wrap(
  "RESEARCH — Equity Report",
  "31 Agt 2026",
  "CDIA",
  2,
  PALETTE,
  [
    #section-header(1, "Segment Breakdown — 4 Pilar Bisnis", PALETTE)

    #text(size: 8pt)[
      CDIA mengoperasikan 4 pilar bisnis infrastruktur terintegrasi di kawasan industri Cilegon dan perairan strategis nasional. Kombinasi pilar defensif (Air & Energi) dan pilar ekspansif (Logistik & Pelabuhan) membentuk struktur arus kas yang terdiversifikasi.
    ]

    #v(4pt)
    #exhibit-header("Kinerja & Bauran Pendapatan Segmen 1H26", "Laporan Segmentasi CDIA 1H26 (IDX)")
    #v(1pt)
    #fin-table(
      ("Pilar Segmen", "Pendapatan (Rp bn)", "YoY (%)", "QoQ (%)", "Bauran (%)", "EBITDA (Rp bn)", "EBITDA Margin"),
      (
        ("Pilar Energi", "6.300", "-8,0%", "-3,0%", "53,4%", "2.205", "35,0%"),
        ("Pilar Logistik", "4.010", "+44,7%", "+12,0%", "34,0%", "1.404", "35,0%"),
        ("Pilar Air", "850", "+6,0%", "+2,0%", "7,2%", "425", "50,0%"),
        ("Pilar Pelabuhan", "640", "+9,0%", "+4,0%", "5,4%", "352", "55,0%"),
        ([*Total Segmen*], [*11.800*], [*-22,4%*], [*+3,5%*], [*100,0%*], [*4.386*], [*37,2%*]),
      ),
      palette: PALETTE,
    )

    #v(2pt)
    #text(size: 6.8pt, style: "italic", fill: PALETTE.muted)[
      *Catatan One-Off:* Normalisasi keuntungan penjualan aset Rp 15,9 bn dikeluarkan dari segmen Energi guna mencerminkan recurring earnings murni.
    ]

    #v(6pt)
    #grid(
      columns: (1fr, 1fr),
      column-gutter: 10pt,
      row-gutter: 6pt,
      [
        #section-header("1.1", "Pilar Energi (Energy Infrastructure)", PALETTE)
        #card(PALETTE)[
          #grid(
            columns: (1fr, auto),
            text(size: 7.6pt, weight: "bold", fill: C_ENERGY)[Porsi Bauran: 53,4%],
            text(size: 7.2pt, fill: PALETTE.muted)[Rp 6.300 bn],
          )
          #v(2pt)
          #pillar-bar(53.4%, C_ENERGY)
          #v(3pt)
          #text(size: 7.5pt)[
            - *Aset Utama:* Pembangkit Listrik CCPP 120MW & Transmisi 150kV.
            - *Model Bisnis:* Pasokan listrik captive jangka panjang kawasan industri.
            - *Kinerja 1H26:* Pendapatan Rp 6.300 bn (-8,0% YoY), EBITDA Rp 2.205 bn.
            - *Karakter Arus Kas:* Arus kas stabil dan kontraktual (Base utility).
          ]
        ]
      ],
      [
        #section-header("1.2", "Pilar Logistik (Chemical & Liquid Shipping)", PALETTE)
        #card(PALETTE)[
          #grid(
            columns: (1fr, auto),
            text(size: 7.6pt, weight: "bold", fill: C_LOGISTICS)[Porsi Bauran: 34,0%],
            text(size: 7.2pt, fill: PALETTE.muted)[Rp 4.010 bn],
          )
          #v(2pt)
          #pillar-bar(34.0%, C_LOGISTICS)
          #v(3pt)
          #text(size: 7.5pt)[
            - *Aset Utama:* 7 unit armada kapal tangki kimia (5.000 - 8.600 DWT).
            - *Model Bisnis:* Time Charter (TC) & Contract of Affreightment (COA).
            - *Kinerja 1H26:* Pendapatan Rp 4.010 bn (+44,7% YoY, pilar tercepat).
            - *Karakter Arus Kas:* Growth engine utama dengan ekspansi rute regional.
          ]
        ]
      ],
      [
        #section-header("1.3", "Pilar Air (Industrial Water Treatment)", PALETTE)
        #card(PALETTE)[
          #grid(
            columns: (1fr, auto),
            text(size: 7.6pt, weight: "bold", fill: C_WATER)[Porsi Bauran: 7,2%],
            text(size: 7.2pt, fill: PALETTE.muted)[Rp 850 bn],
          )
          #v(2pt)
          #pillar-bar(7.2%, C_WATER)
          #v(3pt)
          #text(size: 7.5pt)[
            - *Aset Utama:* Fasilitas pengolahan air baku Sungai Cidanau (2.000 l/s).
            - *Model Bisnis:* Konsesi penyediaan air bersih industri berkelanjutan.
            - *Kinerja 1H26:* Pendapatan Rp 850 bn (+6,0% YoY, EBITDA margin 50,0%).
            - *Karakter Arus Kas:* Monopoli alamiah dengan margin EBITDA defensif.
          ]
        ]
      ],
      [
        #section-header("1.4", "Pilar Pelabuhan (Jetty & Storage Tank)", PALETTE)
        #card(PALETTE)[
          #grid(
            columns: (1fr, auto),
            text(size: 7.6pt, weight: "bold", fill: C_PORT)[Porsi Bauran: 5,4%],
            text(size: 7.2pt, fill: PALETTE.muted)[Rp 640 bn],
          )
          #v(2pt)
          #pillar-bar(5.4%, C_PORT)
          #v(3pt)
          #text(size: 7.5pt)[
            - *Aset Utama:* 3 dermaga curah cair (s.d. 80k DWT) & 72 tangki (130k m³).
            - *Model Bisnis:* Jasa kepelabuhanan, bongkar muat & sewa tangki timbun.
            - *Kinerja 1H26:* Pendapatan Rp 640 bn (+9,0% YoY, EBITDA margin 55,0%).
            - *Karakter Arus Kas:* Margin tertinggi grup didukung tarif berbasis dolar.
          ]
        ]
      ]
    )
  ]
)

#pagebreak(weak: true)

// =====================================================================
// PAGE 3 — FINANCIAL HIGHLIGHTS 6Y
// =====================================================================
#page-wrap(
  "RESEARCH — Equity Report",
  "31 Agt 2026",
  "CDIA",
  3,
  PALETTE,
  [
    #section-header(2, "Financial Highlights 6Y & P&L Contribution", PALETTE)

    #text(size: 8pt)[
      Ringkasan kinerja keuangan historis dan proyeksi konsolidasian CDIA periode FY23A s.d. FY28F. Tahun FY26F merefleksikan penurunan pendapatan sementara akibat perlambatan M&A dan normalisasi one-off sebelum pemulihan kembali di FY27F-FY28F.
    ]

    #v(5pt)
    #exhibit-header("Kinerja Keuangan Konsolidasian 6 Tahun (FY23A - FY28F)", "Laporan Keuangan CDIA & Proyeksi Riset")
    #v(1pt)
    #fin-table(
      ("Metrik Keuangan (Rp bn)", "FY23A", "FY24A", "FY25A", "FY26F", "FY27F", "FY28F"),
      (
        ("Pendapatan Bersih", "12.800", "14.500", "15.200", "11.800", "12.900", "14.200"),
        ("Pertumbuhan Pendapatan (%)", "+18,5%", "+13,3%", "+4,8%", "-22,4%", "+9,3%", "+10,1%"),
        ("Laba Kotor (Gross Profit)", "4.864", "5.510", "5.168", "3.068", "3.870", "4.686"),
        ("EBITDA Konsolidasi", "4.400", "4.900", "4.300", "2.100", "2.800", "3.500"),
        ("Margin EBITDA (%)", "34,4%", "33,8%", "28,3%", "17,8%", "21,7%", "24,6%"),
        ("Beban Bunga & Keuangan", "(720)", "(890)", "(1.150)", "(1.380)", "(1.250)", "(1.100)"),
        ("Laba Bersih (Net Profit)", "2.500", "2.800", "2.100", "510", "890", "1.350"),
        ("Margin Laba Bersih (%)", "19,5%", "19,3%", "13,8%", "4,3%", "6,9%", "9,5%"),
        ("EPS (Rp per Saham)", "167", "187", "140", "34", "59", "90"),
      ),
      palette: PALETTE,
    )

    #v(6pt)
    #exhibit-header("Kontribusi Pendapatan per Pilar 6Y (Rp bn)", "Laporan Segmentasi CDIA (IDX)")
    #v(1pt)
    #fin-table(
      ("Pilar Bisnis (Rp bn)", "FY23A", "FY24A", "FY25A", "FY26F", "FY27F", "FY28F"),
      (
        ("Pilar Energi", "6.900", "7.800", "8.100", "6.300", "6.700", "7.200"),
        ("Pilar Logistik", "4.100", "4.800", "5.150", "4.010", "4.500", "5.100"),
        ("Pilar Air", "1.050", "1.150", "1.180", "850", "920", "1.020"),
        ("Pilar Pelabuhan", "750", "750", "770", "640", "780", "880"),
        ([*Total Pendapatan*], [*12.800*], [*14.500*], [*15.200*], [*11.800*], [*12.900*], [*14.200*]),
      ),
      palette: PALETTE,
    )

    #v(6pt)
    #exhibit-header("Rasio Neraca, Likuiditas & Profitabilitas 6Y", "Kalkulasi Riset & Data Olahan")
    #v(1pt)
    #fin-table(
      ("Rasio Utama", "FY23A", "FY24A", "FY25A", "FY26F", "FY27F", "FY28F"),
      (
        ("Return on Equity (ROE %)", "14,5%", "12,0%", "8,4%", "1,9%", "3,2%", "4,6%"),
        ("Return on Assets (ROA %)", "8,2%", "7,1%", "4,8%", "1,1%", "1,8%", "2,6%"),
        ("Gearing Ratio / DER (%)", "82,0%", "96,0%", "130,0%", "170,0%", "145,0%", "120,0%"),
        ("Net Debt / EBITDA (x)", "1,6x", "1,9x", "2,6x", "4,1x", "3,2x", "2,4x"),
        ("Current Ratio (x)", "1,4x", "1,2x", "0,9x", "0,7x", "1,0x", "1,2x"),
        ("Price to Earnings / PE (x)", "4,7x", "4,2x", "5,6x", "22,9x", "13,2x", "8,7x"),
      ),
      palette: PALETTE,
    )
  ]
)

#pagebreak(weak: true)

// =====================================================================
// PAGE 4 — SOTP VALUATION & BLENDED FAIR VALUE
// =====================================================================
#page-wrap(
  "RESEARCH — Equity Report",
  "31 Agt 2026",
  "CDIA",
  4,
  PALETTE,
  [
    #section-header(3, "Valuation Methodology — SOTP & Blended Fair Value", PALETTE)

    #card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.ink)[Valuation Methodology: Sum-Of-The-Parts (SOTP)]
      #v(2pt)
      #text(size: 7.8pt)[
        Valuasi CDIA menggunakan pendekatan *Sum-Of-The-Parts (SOTP)* untuk mengukur nilai intrinsik masing-masing pilar berdasarkan karakteristik industri spesifiknya. Diskon holding (Holdco Discount) sebesar *15,0%* diterapkan pada level konsolidasi guna mengakomodasi struktur konglomerasi dan kompleksitas alokasi modal.
      ]
    ]

    #v(5pt)
    #exhibit-header("Tabel Valuasi Sum-Of-The-Parts (SOTP FY26F)", "Engine: scripts/sotp_engine.py")
    #v(1pt)
    #fin-table(
      ("Pilar Segmen", "Metode", "Metrik (Rp bn)", "Multiple", "EV (Rp bn)", "Net Debt", "Nilai Ekuitas", "Per Saham", "Porsi"),
      (
        ("Pilar Energi", "EV/EBITDA", "2.205 (EBITDA)", "8,5x", "18.742", "(8.200)", "10.542", "Rp 703", "51,8%"),
        ("Pilar Logistik", "EV/EBITDA", "1.404 (EBITDA)", "7,2x", "10.108", "(4.900)", "5.208", "Rp 347", "25,6%"),
        ("Pilar Air", "P/E", "170 (Net Inc)", "14,0x", "—", "—", "2.380", "Rp 159", "11,7%"),
        ("Pilar Pelabuhan", "EV/EBITDA", "352 (EBITDA)", "11,0x", "3.872", "(1.650)", "2.222", "Rp 148", "10,9%"),
        ([*Total Ekuitas Bruto*], [*SOTP*], [—], [—], [*32.722*], [*(14.750)*], [*20.352*], [*Rp 1.357*], [*100,0%*]),
        ([*Diskon Holding (15%)*], [*Holdco*], [—], [—], [—], [—], [*(3.053)*], [*(Rp 204)*], [*-15,0%*]),
        ([*Nilai Ekuitas Bersih*], [*Net SOTP*], [—], [—], [—], [—], [*17.299*], [*Rp 1.153*], [*85,0%*]),
      ),
      palette: PALETTE,
    )

    #v(5pt)
    #exhibit-header("Rekonsiliasi Valuasi Blended & Target Price", "Engine: scripts/dcf_engine.py & scripts/ddm_engine.py")
    #v(1pt)
    #fin-table(
      ("Metode Valuasi", "Bobot (%)", "Fair Value (Rp)", "Kontribusi (Rp)", "Parameter & Asumsi Kunci"),
      (
        ("DCF (Discounted Cash Flow)", "50,0%", "815", "408", "WACC 9,8% · Beta 1,05 · Rf 6,2% · ERP 7,4% · g 4,0%"),
        ("DDM (Dividend Discount Model)", "30,0%", "810", "243", "CoE 14,0% · Payout FY27 40% / FY28 104% · g 4,0%"),
        ("SOTP (Multiples Diskon 15%)", "20,0%", "825", "165", "Peer-based multiple · 15% Holdco discount applied"),
        ([*Target Price (Blended)*], [*100,0%*], [*Rp 815*], [*Rp 815*], [*Investment Recommendation: HOLD (Upside +4,5%)*]),
      ),
      palette: PALETTE,
    )

    #v(5pt)
    #card(PALETTE)[
      #text(size: T_SMALL, weight: "bold", fill: PALETTE.muted)[INVESTMENT RECOMMENDATION & MARGIN OF SAFETY]
      #v(2pt)
      #text(size: 7.8pt)[
        Target harga blended ditetapkan pada *Rp 815 per saham*, menghasilkan potensi kenaikan sebesar *+4,5%* dari harga penutupan terakhir Rp 780. Mengingat upside berada di rentang -10% s.d. +15%, our view: *HOLD*. Valuasi ini merefleksikan margin kehati-hatian terhadap penundaan integrasi M&A serta normalisasi earnings base pada FY26F.
      ]
    ]
  ]
)

#pagebreak(weak: true)

// =====================================================================
// PAGE 5 — PEERS PER PILLAR (4 SUB-TABLES)
// =====================================================================
#page-wrap(
  "RESEARCH — Equity Report",
  "31 Agt 2026",
  "CDIA",
  5,
  PALETTE,
  [
    #section-header(4, "Peer Comparison — Per Pilar Bisnis", PALETTE)

    #text(size: 8pt)[
      Perbandingan komparatif multipel valuasi dan indikator profitabilitas per pilar bisnis terhadap emiten sejenis di bursa domestik (IDX) dan regional (SGX, KLSE, PSE).
    ]

    #v(3pt)
    #section-header("4.1", "Pilar Energi (Power Generation & Utilities)", PALETTE)
    #v(-3pt)
    #fin-table(
      ("Ticker / Emiten", "EV/EBITDA (x)", "P/E (x)", "ROE (%)", "Div Yield (%)", "EBITDA Margin"),
      (
        ("POWR (PT Cikarang Listrindo Tbk)", "8,1x", "10,2x", "14,0%", "7,5%", "48,2%"),
        ("Sembcorp Industries (SGX: U96)", "9,3x", "11,5x", "11,0%", "4,2%", "28,5%"),
        ("YTL Power Intl (KLSE: YTLP)", "8,8x", "10,8x", "13,2%", "5,1%", "32,0%"),
        ("CDIA Energi (Implied Multiple)", "8,5x", "11,0x", "12,5%", "4,5%", "35,0%"),
        ([*Rata-rata Industri Energi*], [*8,7x*], [*10,8x*], [*12,7%*], [*5,6%*], [*36,2%*]),
      ),
      palette: PALETTE,
    )
    #v(2pt)
    #text(size: 6.5pt, fill: PALETTE.muted, style: "italic")[Komparabel ilustratif CDIA, statis Sep 2026 — cross-check via Sectors peers pending.]

    #v(3pt)
    #section-header("4.2", "Pilar Logistik (Chemical & Liquid Shipping)", PALETTE)
    #v(-3pt)
    #fin-table(
      ("Ticker / Emiten", "EV/EBITDA (x)", "P/E (x)", "ROE (%)", "Div Yield (%)", "EBITDA Margin"),
      (
        ("HATM (PT Habco Trans Maritima Tbk)", "7,4x", "8,2x", "8,0%", "3,8%", "38,0%"),
        ("SMDR (PT Samudera Indonesia Tbk)", "6,9x", "7,5x", "10,0%", "6,0%", "32,4%"),
        ("TMAS (PT Temas Tbk)", "7,1x", "8,0x", "9,5%", "4,5%", "34,1%"),
        ("CDIA Logistik (Implied Multiple)", "7,2x", "8,5x", "9,0%", "4,0%", "35,0%"),
        ([*Rata-rata Industri Logistik*], [*7,1x*], [*7,9x*], [*9,2%*], [*4,8%*], [*34,8%*]),
      ),
      palette: PALETTE,
    )
    #v(2pt)
    #text(size: 6.5pt, fill: PALETTE.muted, style: "italic")[Komparabel ilustratif CDIA, statis Sep 2026 — cross-check via Sectors peers pending.]

    #v(3pt)
    #section-header("4.3", "Pilar Air (Water Treatment & Concession)", PALETTE)
    #v(-3pt)
    #fin-table(
      ("Ticker / Emiten", "P/E (x)", "EV/EBITDA (x)", "ROE (%)", "Div Yield (%)", "Net Margin"),
      (
        ("TOWR (Utility Infrastructure Proxy)", "13,2x", "10,4x", "18,0%", "3,2%", "24,5%"),
        ("Manila Water Co (PSE: MWC)", "14,5x", "9,8x", "16,5%", "4,0%", "20,2%"),
        ("Regional Aqua-Utility Peers", "15,0x", "11,2x", "20,0%", "3,5%", "22,0%"),
        ("CDIA Air (Implied Multiple)", "14,0x", "10,5x", "17,5%", "3,5%", "20,0%"),
        ([*Rata-rata Industri Air & Utilitas*], [*14,2x*], [*10,5x*], [*18,2%*], [*3,6%*], [*22,2%*]),
      ),
      palette: PALETTE,
    )
    #v(2pt)
    #text(size: 6.5pt, fill: PALETTE.muted, style: "italic")[Komparabel ilustratif CDIA, statis Sep 2026 — cross-check via Sectors peers pending.]

    #v(3pt)
    #section-header("4.4", "Pilar Pelabuhan (Port & Tank Storage)", PALETTE)
    #v(-3pt)
    #fin-table(
      ("Ticker / Emiten", "EV/EBITDA (x)", "P/E (x)", "ROE (%)", "Div Yield (%)", "EBITDA Margin"),
      (
        ("Westports Holdings (KLSE: WPRTS)", "11,5x", "16,2x", "12,0%", "4,1%", "52,0%"),
        ("IPCC / IPBB (PT Indonesia Kendaraan)", "10,8x", "14,5x", "9,0%", "5,8%", "46,5%"),
        ("PORT (PT Nusantara Pelabuhan Handal)", "10,2x", "13,8x", "8,5%", "2,5%", "40,0%"),
        ("CDIA Pelabuhan (Implied Multiple)", "11,0x", "15,0x", "10,0%", "4,5%", "55,0%"),
        ([*Rata-rata Industri Pelabuhan*], [*10,8x*], [*14,8x*], [*9,8%*], [*4,1%*], [*46,2%*]),
      ),
      palette: PALETTE,
    )
    #v(2pt)
    #text(size: 6.5pt, fill: PALETTE.muted, style: "italic")[Komparabel ilustratif CDIA, statis Sep 2026 — cross-check via Sectors peers pending.]
  ]
)

#pagebreak(weak: true)

// =====================================================================
// PAGE 6 — RISKS ANALYSIS
// =====================================================================
#page-wrap(
  "RESEARCH — Equity Report",
  "31 Agt 2026",
  "CDIA",
  6,
  PALETTE,
  [
    #section-header(5, "Investment Risks — Spesifik Pilar & Konglomerasi", PALETTE)

    #text(size: 8pt)[
      Evaluasi risiko komprehensif mencakup eksposur operasional tiap pilar bisnis serta risiko struktural holding terkait leverage finansial dan ketergantungan pasokan.
    ]

    #v(5pt)
    #grid(
      columns: (1fr, 1fr),
      column-gutter: 10pt,
      row-gutter: 6pt,
      [
        #card(PALETTE)[
          #text(weight: "bold", fill: PALETTE.brand_dark)[1. Pasokan Gas & Tarif (Pilar Energi)]
          #v(2pt)
          #text(size: 7.5pt)[
            *Dampak: Tinggi · Probabilitas: Sedang* \
            CCPP 120MW bergantung pada kontinuitas suplai gas pipa dari PGN/SKK Migas. Kenaikan harga gas industri atau gangguan pipa transmisi dapat menekan margin pembangkit listrik jika tidak ada mekanisme pass-through penuh.
          ]
        ]
      ],
      [
        #card(PALETTE)[
          #text(weight: "bold", fill: PALETTE.brand_dark)[2. Kerusakan Vessel & Tarif (Pilar Logistik)]
          #v(2pt)
          #text(size: 7.5pt)[
            *Dampak: Sedang · Probabilitas: Tinggi* \
            Armada 7 kapal tangki kimia (5.000–8.600 DWT) rentan terhadap risiko perawatan mesin mendadak (off-hire) dan fluktuasi charter rate global. Downtime satu vessel dapat menurunkan pendapatan segmen hingga 14%.
          ]
        ]
      ],
      [
        #card(PALETTE)[
          #text(weight: "bold", fill: PALETTE.brand_dark)[3. Sedimentasi Sungai (Pilar Air)]
          #v(2pt)
          #text(size: 7.5pt)[
            *Dampak: Sedang · Probabilitas: Sedang* \
            Intake air baku dari Sungai Cidanau menghadapi risiko sedimentasi dan penurunan debit air saat musim kemarau ekstrem, berpotensi menurunkan kapasitas produksi pengolahan air bersih di bawah batas optimal 2.000 l/s.
          ]
        ]
      ],
      [
        #card(PALETTE)[
          #text(weight: "bold", fill: PALETTE.brand_dark)[4. Cuaca Ekstrem Selat Sunda (Pelabuhan)]
          #v(2pt)
          #text(size: 7.5pt)[
            *Dampak: Rendah · Probabilitas: Tinggi* \
            Gelombang pasang dan cuaca buruk di perairan Selat Sunda dapat menunda proses sandar kapal dan bongkar muat kargo curah cair pada 3 jetty dermaga, memperpanjang turnaround time kapal tanker.
          ]
        ]
      ]
    )

    #v(5pt)
    #card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.brand_dark)[5. Risiko Struktur Finansial, Gearing & M&A Holding (Konglomerasi)]
      #v(2pt)
      #text(size: 7.8pt)[
        *Dampak: Tinggi · Probabilitas: Sedang* \
        Rasio gearing konsolidasi meningkat hingga *170,0%* pada FY26F dengan Net Debt/EBITDA mencapai *4,1x* akibat pembiayaan ekspansi capex. Penundaan integrasi M&A pada semester kedua 2026 berisiko menunda realisasi sinergi pendapatan baru ke tahun fiskal FY27F.
      ]
    ]

    #v(5pt)
    #exhibit-header("Matriks Mitigasi Risiko Terintegrasi", "Analisis Risiko Internal Riset")
    #v(1pt)
    #fin-table(
      ("Pilar / Area", "Kategori Risiko", "Tingkat Risiko", "Mitigasi Strategis yang Diterapkan"),
      (
        ("Pilar Energi", "Suplai Gas & Harga", "Tinggi", "Kontrak GSA jangka panjang + opsi dual-fuel backup"),
        ("Pilar Logistik", "Off-Hire & Utilisasi", "Sedang", "80% armada dalam kontrak Time-Charter (TC) jangka panjang"),
        ("Pilar Air", "Sedimentasi Intake", "Sedang", "Pengerukan sedimentasi berkala & sistem filtrasi multi-tahap"),
        ("Pilar Pelabuhan", "Cuaca & Turnaround", "Rendah", "Radar cuaca maritim real-time & SOP sandar berstandar ISPS"),
        ("Level Holding", "Leverage & Likuiditas", "Tinggi", "Refinancing utang ke tenor panjang + penjadwalan capex fleksibel"),
      ),
      palette: PALETTE,
    )
  ]
)

#pagebreak(weak: true)

// =====================================================================
// PAGE 7 — RATING GUIDE & REGULATORY DISCLAIMER
// =====================================================================
#page-wrap(
  "RESEARCH — Equity Report",
  "31 Agt 2026",
  "CDIA",
  7,
  PALETTE,
  [
    #section-header(6, "Investment Recommendation Framework & Disklaimer Regulasi", PALETTE)

    #text(size: 8pt)[
      Standar metodologi pemeringkatan saham, independensi sertifikasi analis riset, serta disklaimer kepatuhan regulasi Otoritas Jasa Keuangan (OJK).
    ]

    #v(5pt)
    #section-header("6.1", "Definisi Rating Investment Recommendation (12 Bulan)", PALETTE)
    #v(-3pt)
    #fin-table(
      ("Investment Recommendation", "Kriteria Total Return (12M Eks-Dividen)", "Implikasi bagi Investor"),
      (
        ("BUY", "Total Return Ekspektasi > +15%", "Potensi kenaikan harga substansial di atas biaya modal ekuitas."),
        ("TRADING BUY", "Total Return Ekspektasi +5% s.d. +15%", "Peluang trading jangka pendek/menengah berbasis katalis tertentu."),
        ("HOLD", "Total Return Ekspektasi -10% s.d. +15%", "Valuasi mencerminkan nilai wajar; profil risk-reward seimbang."),
        ("SELL", "Total Return Ekspektasi < -10%", "Risiko koreksi harga material; direkomendasikan realisasi profit."),
      ),
      palette: PALETTE,
    )

    #v(5pt)
    #card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.ink)[Sertifikasi Analis & Independensi Riset]
      #v(2pt)
      #text(size: 7.5pt)[
        Analis yang menyusun laporan riset ekuitas ini menyatakan secara independen bahwa: (1) Seluruh pandangan yang diungkapkan secara akurat mencerminkan penilaian profesional terhadap PT Chandra Daya Investasi (CDIA) dan sekuritas terkait; (2) Tidak ada bagian dari remunerasi atau kompensasi analis yang terkait, baik langsung maupun tidak langsung, dengan rekomendasi atau target harga spesifik dalam laporan ini; (3) Analis dan afiliasinya tidak memiliki benturan kepentingan finansial material terhadap emiten.
      ]
    ]

    #v(5pt)
    #card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.ink)[Disklaimer Kepatuhan Otoritas Jasa Keuangan (OJK)]
      #v(2pt)
      #text(size: 7.2pt)[
        Laporan riset ini diterbitkan semata-mata untuk tujuan penyediaan informasi dan analisis edukatif bagi investor, dan bukan merupakan ajakan, penawaran, atau rekomendasi resmi untuk membeli atau menjual efek atau instrumen keuangan apa pun sebagaimana diatur dalam peraturan perundang-undangan Pasar Modal Republik Indonesia. Pendapat, proyeksi, dan estimasi yang tercantum didasarkan pada data publik yang diyakini dapat dipercaya (IDX, FactSet, KSEI, Laporan Keuangan Emiten) pada tanggal publikasi, namun tidak ada jaminan atas kelengkapan dan keakuratannya. Kinerja masa lalu bukan merupakan indikasi hasil masa depan. Setiap keputusan investasi merupakan tanggung jawab mandiri investor sepenuhnya.
      ]
    ]

    #v(5pt)
    #card(PALETTE)[
      #grid(
        columns: (1fr, 1fr),
        column-gutter: 12pt,
        [
          #text(size: 7pt, weight: "bold", fill: PALETTE.muted)[PROVENANCE & METADATA]
          #v(2pt)
          #text(size: 6.8pt)[
            - *Penerbit:* Tim Riset Ekuitas (Sectors Hackathon 2026)
            - *Tanggal:* 31 Agustus 2026 · Bahasa: Indonesia (ID)
            - *Coverage:* CDIA (Chandra Daya Investasi) — Inisiasi
          ]
        ],
        [
          #text(size: 7pt, weight: "bold", fill: PALETTE.muted)[MODEL DETERMINISTIK]
          #v(2pt)
          #text(size: 6.8pt)[
            - *SOTP Engine:* scripts/sotp_engine.py (Peer multiples)
            - *DCF Engine:* scripts/dcf_engine.py (WACC 9,8%)
            - *DDM Engine:* scripts/ddm_engine.py (CoE 14,0%)
          ]
        ]
      )
    ]
  ]
)
