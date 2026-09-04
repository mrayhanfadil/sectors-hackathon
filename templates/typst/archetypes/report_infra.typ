// =====================================================================
// report_infra.typ — Institutional equity research (Infra archetype)
// Multi-ticker parameterized template for infrastructure / recurring archetypes
// =====================================================================
#import "../common/theme.typ": *

#show: set-page-defaults

#let ticker = sys.inputs.at("ticker", default: "MTEL")
#let default-data-path = "/home/fadil/projects/sectors-hackathon/output/cache/render_" + lower(ticker) + "/report_data.json"
#let data-path = sys.inputs.at("data_path", default: default-data-path)
#let data = json(data-path)

#let m = data.at("meta")
#let cover = data.at("cover").at("rating_box")
#let unit = m.at("report_unit", default: if data.at("quarterly_pl", default: (:)).at("headers", default: ()).len() > 0 { data.quarterly_pl.headers.at(0) } else { "Rp Miliar" })
#let chart-dir = "/home/fadil/projects/sectors-hackathon/output/cache/render_" + lower(m.ticker) + "/charts"

#let PALETTE = (
  brand: rgb("#067647"),       // emerald green (infra archetype)
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
#let SEG_COLORS = (
  rgb("#067647"),
  rgb("#0284c7"),
  rgb("#d97706"),
  rgb("#7c3aed"),
  rgb("#0891b2"),
  rgb("#4f46e5"),
)

// =====================================================================
// PAGE 1 — COVER & SNAPSHOT
// =====================================================================
#page-wrap(m.at("prepared_by", default: "RESEARCH — Equity Report"), m.date, m.ticker, 1, PALETTE, [
  #grid(
    columns: (2fr, 1.15fr),
    column-gutter: 12pt,
    [
      #text(size: T_SMALL, fill: PALETTE.muted, tracking: 0.12em, weight: "bold")[
        #upper(m.at("report_type", default: "EQUITY UPDATE")) · #upper(m.sector)
      ]
      #v(3pt)
      #text(size: T_COVER_TITLE, weight: "bold", fill: PALETTE.brand_dark)[
        #m.company_name
      ]
      #v(1pt)
      #text(size: 12.5pt, weight: "bold", fill: PALETTE.muted)[
        #m.ticker · IDX · Sektor #m.sector
      ]
      #v(6pt)

      #card(PALETTE)[
        #text(size: 7.8pt, weight: "bold", fill: PALETTE.brand_dark)[KEY TAKEAWAYS & HIGHLIGHTS]
        #v(3pt)
        #list(
          ..cover.key_takeaways.map(t => [#t])
        )
      ]

      #v(6pt)
      #exhibit-header("Exhibit 1", "Bauran Pendapatan per Segmen (1H26)", data.at("segments_src", default: m.ticker + " 1H26 (IDX)"))
      #v(2pt)
      #block(width: 100%)[
        #let segs = data.at("segments", default: ())
        #if segs.len() > 0 {
          let seg-cols = segs.map(s => s.share_pct * 1%)
          grid(
            columns: seg-cols,
            ..segs.enumerate().map(((i, s)) => rect(
              width: 100%,
              height: 7pt,
              fill: SEG_COLORS.at(calc.rem(i, SEG_COLORS.len())),
              radius: if i == 0 { (left: 2pt) } else if i == segs.len() - 1 { (right: 2pt) } else { 0pt }
            ))
          )
          v(2pt)
          let label-cols = (1fr,) * segs.len()
          grid(
            columns: label-cols,
            ..segs.enumerate().map(((i, s)) => [
              #box(width: 4.5pt, height: 4.5pt, fill: SEG_COLORS.at(calc.rem(i, SEG_COLORS.len())), radius: 1pt) #text(size: 6.2pt)[ #s.name #s.share_pct%]
            ])
          )
        }
      ]
      #v(2pt)
      #let seg-headers = ("Segmen Bisnis", "1H26 (" + unit + ")", "Bauran (%)", "YoY (%)", "Status")
      #let seg-rows = data.at("segments", default: ()).enumerate().map(((i, s)) => (
        s.name,
        str(s.revenue_1h26),
        str(s.share_pct) + "%",
        if s.yoy_pct > 0 { "+" + str(s.yoy_pct) + "%" } else { str(s.yoy_pct) + "%" },
        if i == 0 { "Core Anchor" } else if i == 1 { "Growth Driver" } else if i == 2 { "High Expansion" } else { "Stable Cashflow" }
      ))
      #let total-rev = data.at("segments", default: ()).fold(0, (acc, s) => acc + s.revenue_1h26)
      #let seg-total-row = ([*Total Pendapatan 1H26*], [*#str(total-rev)*], [*100,0%*], [*+2,1%*], [*Konsolidasian*])
      #fin-table(
        seg-headers,
        (..seg-rows, seg-total-row),
        palette: PALETTE,
      )

      #v(6pt)
      #let vs-jci = data.cover.at("vs_jci", default: (:))
      #exhibit-header("Exhibit 2", "Kinerja Harga " + m.ticker + " vs IHSG (YTD)", vs-jci.at("source", default: "IDX & yfinance"))
      #v(2pt)
      #image(chart-dir + "/vs_jci.png", width: 100%)
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

      #v(5pt)
      #card(PALETTE)[
        #text(size: T_SMALL, weight: "bold", fill: PALETTE.muted)[INFORMASI PASAR & SAHAM]
        #v(2.5pt)
        #let sh = data.cover.at("shares", default: (:))
        #grid(
          columns: (1fr, auto),
          row-gutter: 3pt,
          text(size: 7pt)[Harga Kini], text(size: 7pt, weight: "bold")[Rp #cover.price],
          text(size: 7pt)[Target Harga (12M)], text(size: 7pt, weight: "bold")[Rp #cover.tp],
          text(size: 7pt)[TP Sebelumnya], text(size: 7pt, weight: "bold")[#(if cover.at("prev_tp", default: none) != none { "Rp " + str(cover.prev_tp) } else { "—" })],
          text(size: 7pt)[Potensi #(if cover.upside_pct >= 0 { "Kenaikan" } else { "Penurunan" })], text(size: 7pt, weight: "bold", fill: if cover.upside_pct >= 0 { PALETTE.pos } else { PALETTE.neg })[#(if cover.upside_pct > 0 { "+" } else { "" })#cover.upside_pct% (#cover.action)],
          text(size: 7pt)[Saham Beredar], text(size: 7pt, weight: "bold")[#sh.at("outstanding", default: 81.50) Miliar],
          text(size: 7pt)[Kapitalisasi Pasar], text(size: 7pt, weight: "bold")[Rp #str(calc.round(sh.at("outstanding", default: 81.50) * cover.price / 1000, digits: 2)) T],
          text(size: 7pt)[Free Float], text(size: 7pt, weight: "bold")[#sh.at("free_float_pct", default: 28.2)%],
          text(size: 7pt)[52-Wk Range], text(size: 7pt, weight: "bold")[#sh.at("range_52w", default: "420 - 710")],
          text(size: 7pt)[Indeks Konstituen], text(size: 7pt, weight: "bold")[#sh.at("indices", default: "LQ45 / IDX80 / KOMPAS100")],
        )
      ]

      #v(5pt)
      #card(PALETTE)[
        #text(size: T_SMALL, weight: "bold", fill: PALETTE.muted)[STRUKTUR KEPEMILIKAN]
        #v(2.5pt)
        #let sh-list = data.cover.at("shareholders", default: ())
        #grid(
          columns: (1fr, auto),
          row-gutter: 3pt,
          ..sh-list.map(s => (
            text(size: 7pt)[#s.name],
            text(size: 7pt, weight: "bold")[#s.pct%]
          )).flatten()
        )
        #v(2pt)
        #text(size: 6.2pt, style: "italic", fill: PALETTE.muted)[Sumber: #data.cover.at("shareholders_src", default: "IDX struktur pemegang saham")]
      ]

      #v(5pt)
      #card(PALETTE)[
        #let esg = data.cover.at("esg", default: (:))
        #text(size: T_SMALL, weight: "bold", fill: PALETTE.muted)[SKOR ESG (#upper(esg.at("source", default: "SUSTAINALYTICS")) #esg.at("date", default: "2026"))]
        #v(2.5pt)
        #let scores = esg.at("scores", default: (:))
        #grid(
          columns: (1fr, auto),
          row-gutter: 3pt,
          text(size: 7pt)[Lingkungan (E)], text(size: 7pt, weight: "bold")[#scores.at("e", default: "2.23") / 10],
          text(size: 7pt)[Sosial (S)], text(size: 7pt, weight: "bold")[#scores.at("s", default: "3.03") / 10],
          text(size: 7pt)[Tata Kelola (G)], text(size: 7pt, weight: "bold")[#scores.at("g", default: "5.08") / 10],
          text(size: 7pt)[Kategori Risiko ESG], text(size: 7pt, weight: "bold", fill: PALETTE.brand)[#esg.at("risk_category", default: "Low to Medium Risk")],
        )
      ]
    ]
  )
])

#pagebreak()

// =====================================================================
// PAGE 2 — KPI OPERASIONAL HERO & KATALIS TERKUANTIFIKASI
// =====================================================================
#page-wrap(m.at("prepared_by", default: "RESEARCH — Equity Report"), m.date, m.ticker, 2, PALETTE, [
  #section-header(1, "KPI Operasional — Hero Section", PALETTE)

  #let kpis = data.at("kpis", default: ())
  #text(size: 7.8pt)[
    KPI per subsektor #m.sector (#kpis.map(k => k.name).join(", ")) adalah tesis utama bisnis *recurring infra* — bukan hanya sekadar metrik P&L kuartalan. Portofolio operasional #m.ticker memperkuat skala keekonomian dan keunggulan kompetitif di industri.
  ]
  #v(4pt)

  #if kpis.len() > 0 {
    grid(
      columns: (1fr,) * kpis.len(),
      gutter: 6pt,
      ..kpis.map(k => card(PALETTE)[
        #text(size: 6.5pt, fill: PALETTE.muted, weight: "bold")[#upper(k.name)]
        #v(1pt)
        #text(size: 11.5pt, weight: "black", fill: PALETTE.brand_dark)[#k.row.at(1)]
        #text(size: 6.5pt, weight: "bold")[ #k.unit]
        #v(1pt)
        #text(size: 6.2pt, fill: if str(k.row.at(3)).starts-with("-") { PALETTE.neg } else { PALETTE.pos }, weight: "bold")[#k.row.at(3) YoY]
      ])
    )
  }

  #v(6pt)
  #exhibit-header("Exhibit 3", "Tabel KPI Operasional vs Periode Lalu (1H26 vs 1H25)", data.at("kpis_src", default: "Company data 1H26"))
  #v(2pt)
  #fin-table(
    ("Metrik KPI", "Kini (1H26)", "Lalu (1H25)", "Perubahan (Δ)", "Satuan", "Formula & Karakteristik", "Sumber Data"),
    kpis.map(k => k.row),
    palette: PALETTE,
  )

  #v(6pt)
  #exhibit-header("Exhibit 4", "Perbandingan Visual KPI Operasional " + m.ticker, data.at("kpis_src", default: "Company data 1H26"))
  #v(2pt)
  #image(chart-dir + "/kpi_bars.png", width: 100%)

  #v(6pt)
  #section-header(2, "Katalis Pertumbuhan Terkuantifikasi", PALETTE)
  #v(-2pt)

  #let cats = data.at("catalysts", default: ())
  #if cats.len() > 0 {
    grid(
      columns: (1fr,) * cats.len(),
      gutter: 8pt,
      ..cats.enumerate().map(((i, c)) => card(PALETTE)[
        #text(weight: "bold", fill: PALETTE.brand_dark)[#(i + 1). #c.name]
        #v(2pt)
        #text(size: 7.2pt)[
          *Dampak Operasional & Finansial:*           #c.effect
        ]
        #v(3pt)
        #grid(
          columns: (1fr, auto),
          text(size: 6.8pt, fill: PALETTE.muted)[#c.at("source", default: "")],
          text(size: 6.8pt, weight: "bold", fill: PALETTE.pos)[Periode: #c.quantified.at("by", default: "FY27–29")],
        )
      ])
    )
  }
])

#pagebreak()

// =====================================================================
// PAGE 3 — SEGMENT BREAKDOWN QUARTERLY + INCOME STATEMENT QUARTERLY
// =====================================================================
#page-wrap(m.at("prepared_by", default: "RESEARCH — Equity Report"), m.date, m.ticker, 3, PALETTE, [
  #section-header(3, "Segment Breakdown & Kinerja Laba Rugi Kuartalan", PALETTE)

  #text(size: 7.8pt)[
    Analisis momentum kinerja keuangan kuartalan menunjukkan pertumbuhan portofolio #m.company_name (#m.ticker) merefleksikan diversifikasi portofolio dan eksekusi operasional yang solid.
  ]
  #v(4pt)

  #exhibit-header("Exhibit 5", "Pendapatan per Segmen: 1H26 vs 1H25 & Momentum Kuartalan (" + unit + ")", data.at("segments_src", default: m.ticker + " 1H26 Laporan Segmentasi (IDX)"))
  #v(2pt)
  #fin-table(
    ("Segmen Bisnis", "1H25", "1H26", "YoY (%)", "Q2-25", "Q1-26", "Q2-26", "YoY (Q2)", "QoQ (%)"),
    data.at("segments", default: ()).map(s => s.row),
    palette: PALETTE,
  )

  #v(6pt)
  #exhibit-header("Exhibit 6", "Laporan Laba Rugi Kuartalan (1H25 vs 1H26 & Q2-25 vs Q2-26)", data.quarterly_pl.source)
  #v(2pt)
  #fin-table(
    data.quarterly_pl.headers,
    data.quarterly_pl.rows.map(r => r.map(c => str(c))),
    palette: PALETTE,
  )

  #v(6pt)
  #card(PALETTE)[
    #text(weight: "bold", fill: PALETTE.ink)[Catatan Kinerja 1H26 & Efisiensi Operasional]
    #v(2pt)
    #text(size: 7.2pt)[
      Kinerja 1H26 #m.company_name (#m.ticker) mencerminkan ketahanan pendapatan dan disiplin efisiensi beban operasional serta struktur modal, menopang profitabilitas berkelanjutan di sektor #m.sector.
    ]
  ]
])

#pagebreak()

// =====================================================================
// PAGE 4 — BALANCE SHEET, RATIOS & OPERATIONAL KPI QUARTERLY
// =====================================================================
#page-wrap(m.at("prepared_by", default: "RESEARCH — Equity Report"), m.date, m.ticker, 4, PALETTE, [
  #section-header(4, "Neraca Keuangan, Rasio & KPI Kuartalan", PALETTE)

  #exhibit-header("Exhibit 7", "Neraca Keuangan Kuartalan Ringkas (" + data.quarterly_balance.headers.at(0) + ")", data.quarterly_balance.source)
  #v(2pt)
  #fin-table(
    data.quarterly_balance.headers,
    data.quarterly_balance.rows.map(r => r.map(c => str(c))),
    palette: PALETTE,
  )

  #v(4pt)
  #exhibit-header("Exhibit 8", "Rasio Keuangan Kuartalan", data.quarterly_ratios.source)
  #v(2pt)
  #fin-table(
    data.quarterly_ratios.headers,
    data.quarterly_ratios.rows.map(r => r.map(c => str(c))),
    palette: PALETTE,
  )

  #v(4pt)
  #exhibit-header("Exhibit 9", "Operational KPI Kuartalan", data.quarterly_kpi.source)
  #v(2pt)
  #fin-table(
    data.quarterly_kpi.headers,
    data.quarterly_kpi.rows.map(r => r.map(c => str(c))),
    palette: PALETTE,
  )
])

#pagebreak()

// =====================================================================
// PAGE 5 — DCF TABLE + BLENDED VALUATION + P/BV BANDS
// =====================================================================
#page-wrap(m.at("prepared_by", default: "RESEARCH — Equity Report"), m.date, m.ticker, 5, PALETTE, [
  #section-header(5, "Metodologi Valuasi: DCF, Blended & Bands", PALETTE)

  #let dcf_meth = data.valuation.methods.at(0)
  #let ev_meth = data.valuation.methods.at(1)
  #let dcf_ass = dcf_meth.assumptions
  #let blended = data.valuation.blended

  #grid(
    columns: (1.2fr, 1fr),
    column-gutter: 10pt,
    [
      #text(size: 9pt, weight: "bold", fill: PALETTE.brand_dark)[Metode 1: Discounted Cash Flow (DCF)]
      #v(2pt)
      #text(size: 6.8pt, fill: PALETTE.muted)[
        Asumsi: WACC #dcf_ass.wacc%, Beta #dcf_ass.beta, Rf #dcf_ass.rf%, ERP #dcf_ass.erp%, CoE #dcf_ass.coe%, CoD #dcf_ass.cod%, We #dcf_ass.we%, Wd #dcf_ass.wd%, g #dcf_ass.g%
      ]
      #v(3pt)
      #exhibit-header("Exhibit 10", "Proyeksi Arus Kas Bebas (FCFF)", dcf_meth.source)
      #v(2pt)
      #fin-table(
        dcf_meth.table.headers,
        dcf_meth.table.rows.map(r => r.map(c => str(c))),
        palette: PALETTE,
      )
      #v(3pt)
      #card(PALETTE)[
        #grid(
          columns: (1fr, auto),
          row-gutter: 2.5pt,
          text(size: 6.8pt)[Enterprise Value (EV)], text(size: 6.8pt, weight: "bold")[Rp #str(calc.round(data.cDcf.valuation.enterprise_value / 1e9, digits: 0)) bn],
          text(size: 6.8pt)[Kas Bersih / (Utang Bersih)], text(size: 6.8pt, weight: "bold")[-(Rp #str(calc.round((data.cDcf.valuation.total_debt - data.cDcf.valuation.cash) / 1e9, digits: 0)) bn)],
          text(size: 6.8pt)[Nilai Ekuitas (Equity Value)], text(size: 6.8pt, weight: "bold")[Rp #str(calc.round(data.cDcf.valuation.equity_value / 1e9, digits: 0)) bn],
          text(size: 7.2pt, weight: "bold")[Nilai Wajar DCF per Saham], text(size: 7.2pt, weight: "black", fill: PALETTE.brand_dark)[Rp #dcf_meth.fv],
        )
      ]
    ],
    [
      #text(size: 9pt, weight: "bold", fill: PALETTE.brand_dark)[Metode 2: Multiple EV/EBITDA]
      #v(2pt)
      #text(size: 6.8pt, fill: PALETTE.muted)[
        Target multiple #ev_meth.assumptions.multiple x berdasarkan peers industri #m.sector.
      ]
      #v(3pt)
      #fin-table(
        ev_meth.table.headers,
        ev_meth.table.rows.map(r => r.map(c => str(c))),
        palette: PALETTE,
      )

      #v(5pt)
      #text(size: 9pt, weight: "bold", fill: PALETTE.brand_dark)[Rekonsiliasi Valuasi Blended (#blended.weights.DCF/#blended.weights.at("EV/EBITDA"))]
      #v(2pt)
      #fin-table(
        ("Metode Valuasi", "Bobot", "Fair Value"),
        (
          ..blended.rows.map(r => (str(r.at(0)), str(r.at(1)), "Rp " + str(r.at(2)))),
          ([*Target Price (Blended)*], [*100%*], [*Rp #blended.fv_str*]),
        ),
        palette: PALETTE,
      )
      #v(2pt)
      #text(size: 6.2pt, style: "italic", fill: PALETTE.muted)[Margin of Safety (MoS) yang diterapkan: #blended.margin_of_safety_pct%]
    ]
  )

  #v(6pt)
  #let pbv = data.valuation.bands.pbv_3y
  #exhibit-header("Exhibit 11", "Pita Valuasi Historis P/BV 3-Tahun (Mean Reversion)", data.valuation.bands.source)
  #v(2pt)
  #fin-table(
    ("Deviasi Standar", "P/BV (x)", "Interpretasi & Posisi Pasar"),
    (
      ("STD +2 (Batas Atas Ekstrem)", str(pbv.at("std+2")) + "x", "Overvalued Ekstrem"),
      ("STD +1 (Batas Atas)", str(pbv.at("std+1")) + "x", "Overvalued Moderat"),
      ("Rerata 3 Tahun (Mean)", str(pbv.avg) + "x", "Rentang Nilai Wajar Historis"),
      ("STD -1 (Batas Bawah)", str(pbv.at("std-1")) + "x", "Undervalued Menarik"),
      ("STD -2 (Batas Bawah Ekstrem)", str(pbv.at("std-2")) + "x", "Undervalued Ekstrem"),
      ("Posisi Harga Kini (Rp " + str(cover.price) + ")", str(pbv.current) + "x", pbv.label),
    ),
    palette: PALETTE,
  )

  #v(4pt)
  #image(chart-dir + "/pbv_bands.png", width: 100%)
])

#pagebreak()

// =====================================================================
// PAGE 6 — ABIDA FRIEND-STYLE DCF DEEP DIVE (AUDITABLE ENGINE)
// =====================================================================
#page-wrap(m.at("prepared_by", default: "RESEARCH — Equity Report"), m.date, m.ticker, 6, PALETTE, [
  #section-header(6, "Analisis DCF Komprehensif (Abida Massi Engine)", PALETTE)

  #text(size: 7.2pt, fill: PALETTE.muted)[
    Porting algoritma deterministik dari _abidamassi/dcf-valuation-tool_ untuk transparansi matematis audit, analisis sensitivitas 5x5, dan pengujian ketahanan skenario operasional.
  ]
  #v(3pt)

  #grid(
    columns: (1fr, 1fr),
    column-gutter: 8pt,
    row-gutter: 4pt,
    [
      #exhibit-header("Exhibit 12", "WACC Breakdown", "CAPM & SBN 10Y")
      #v(1pt)
      #image(chart-dir + "/wacc_breakdown.png", width: 100%)
    ],
    [
      #exhibit-header("Exhibit 13", "Sensitivity Heatmap (WACC x g)", "Engine Sensitivitas 5x5")
      #v(1pt)
      #image(chart-dir + "/sensitivity_heatmap.png", width: 100%)
    ],
    [
      #exhibit-header("Exhibit 14", "Skenario Operasional", "Engine Skenario")
      #v(1pt)
      #image(chart-dir + "/scenario_bars.png", width: 100%)
    ],
    [
      #exhibit-header("Exhibit 15", "EV to Equity Bridge Waterfall", "Bridge Engine")
      #v(1pt)
      #image(chart-dir + "/ev_equity_waterfall.png", width: 100%)
    ]
  )

  #v(2pt)
  #let sens = data.cDcf.sensitivity
  #grid(
    columns: (1.1fr, 1fr),
    column-gutter: 8pt,
    [
      #exhibit-header("Exhibit 16", "Matriks Sensitivitas Nilai Wajar: WACC vs g", "Engine Sensitivitas 5x5")
      #v(1pt)
      #let sens_headers = ("WACC \ g", ..sens.g_axis.map(g => str(calc.round(g * 100, digits: 2)) + "%"))
      #let sens_rows = sens.wacc_axis.enumerate().map(((i, w)) => {
        let r = (str(calc.round(w * 100, digits: 2)) + "%",)
        let fvs = sens.fair_value.at(i)
        let ups = sens.upside.at(i)
        for j in range(fvs.len()) {
          let fv = fvs.at(j)
          let up = ups.at(j)
          let up_str = (if up > 0 { "+" } else { "" }) + str(calc.round(up * 100, digits: 1)) + "%"
          r.push("Rp " + str(calc.round(fv, digits: 0)) + " (" + up_str + ")")
        }
        r
      })
      #fin-table(
        sens_headers,
        sens_rows,
        palette: PALETTE,
      )
    ],
    [
      #exhibit-header("Exhibit 17", "Skenario Operasional & Jembatan Nilai", "Model Deterministik")
      #v(1pt)
      #let sc = data.cDcf.scenarios
      #fin-table(
        ("Skenario", "Nilai Wajar", "Upside / Downside", "Rekomendasi"),
        (
          ("BEAR", "Rp " + str(calc.round(sc.BEAR.fair_value_per_share, digits: 0)), (if sc.BEAR.upside > 0 { "+" } else { "" }) + str(calc.round(sc.BEAR.upside * 100, digits: 1)) + "%", sc.BEAR.rating),
          ("BASE", "Rp " + str(calc.round(sc.BASE.fair_value_per_share, digits: 0)), (if sc.BASE.upside > 0 { "+" } else { "" }) + str(calc.round(sc.BASE.upside * 100, digits: 1)) + "%", sc.BASE.rating),
          ("BULL", "Rp " + str(calc.round(sc.BULL.fair_value_per_share, digits: 0)), (if sc.BULL.upside > 0 { "+" } else { "" }) + str(calc.round(sc.BULL.upside * 100, digits: 1)) + "%", sc.BULL.rating),
        ),
        palette: PALETTE,
      )
      #v(2pt)
      #card(PALETTE)[
        #let dcf_v = data.cDcf.valuation
        #let sc_scale = if dcf_v.pv_explicit > 1e6 { 1e12 } else { 1e6 }
        #let sc_unit = if dcf_v.pv_explicit > 1e6 { "T" } else { "M" }
        #text(size: 6.8pt, weight: "bold", fill: PALETTE.ink)[Jembatan Nilai EV ke Ekuitas (#m.ticker Model):]         #text(size: 6.2pt)[
          PV Arus Kas Eksplisit: *Rp #str(calc.round(dcf_v.pv_explicit / sc_scale, digits: 2)) #sc_unit*           (+) PV Nilai Terminal: *Rp #str(calc.round(dcf_v.pv_terminal / sc_scale, digits: 2)) #sc_unit*           (=) Enterprise Value (EV): *Rp #str(calc.round(dcf_v.enterprise_value / sc_scale, digits: 2)) #sc_unit*           (+) Kas & Setara Kas: *+Rp #str(calc.round(dcf_v.cash / sc_scale, digits: 2)) #sc_unit*           (-) Total Utang Berbunga: *-(Rp #str(calc.round(dcf_v.total_debt / sc_scale, digits: 2)) #sc_unit)*           (=) Implied Equity Value: *Rp #str(calc.round(dcf_v.equity_value / sc_scale, digits: 2)) #sc_unit*           *Fair Value per Saham Model Standalone: Rp #str(calc.round(dcf_v.fair_value_per_share, digits: 0)) (Upside: #(if dcf_v.upside > 0 { "+" } else { "" })#str(calc.round(dcf_v.upside * 100, digits: 1))% vs Rp #cover.price)*
        ]
      ]
    ]
  )
])

#pagebreak()

// =====================================================================
// PAGE 7 — FINANCIAL HIGHLIGHTS 6Y & INVESTMENT THESIS
// =====================================================================
#page-wrap(m.at("prepared_by", default: "RESEARCH — Equity Report"), m.date, m.ticker, 7, PALETTE, [
  #section-header(7, "Ringkasan Finansial 6Y & Tesis Investasi", PALETTE)

  #exhibit-header("Exhibit 18", "Financial Highlights 6 Tahun (" + data.financial_highlights.years.at(0) + " – " + data.financial_highlights.years.at(-1) + ")", data.financial_highlights.source)
  #v(2pt)
  #fin-table(
    ("Metrik Finansial", ..data.financial_highlights.years),
    data.financial_highlights.rows.map(r => r.map(c => str(c))),
    palette: PALETTE,
  )

  #v(6pt)
  #exhibit-header("Exhibit 19", "Trajektori Kinerja & Margin Operasional", data.financial_highlights.source)
  #v(2pt)
  #chart-placeholder("Trajektori Kinerja & Margin " + m.ticker, caption: "Skala Ekonomi dan Efisiensi Capex Menopang Ekspansi Margin Jangka Panjang", height: 55pt, palette: PALETTE)

  #v(6pt)
  #text(size: 9.5pt, weight: "bold", fill: PALETTE.brand_dark)[3 Pilar Utama Tesis Investasi]
  #v(3pt)

  #let theses = data.at("thesis", default: ())
  #if theses.len() > 0 {
    grid(
      columns: (1fr,) * theses.len(),
      gutter: 6pt,
      ..theses.enumerate().map(((i, t)) => card(PALETTE)[
        #text(weight: "bold", fill: PALETTE.ink)[#(i + 1). #t.headline]
        #v(2pt)
        #text(size: 6.8pt)[
          #t.detail
        ]
      ])
    )
  }
])

#pagebreak()

// =====================================================================
// PAGE 8 — INCOME STATEMENT 6Y & BALANCE SHEET 6Y
// =====================================================================
#page-wrap(m.at("prepared_by", default: "RESEARCH — Equity Report"), m.date, m.ticker, 8, PALETTE, [
  #section-header(8, "Laporan Keuangan 6 Tahun: Laba Rugi & Neraca", PALETTE)

  #let fin_is = data.financials.at(0)
  #let fin_bs = data.financials.at(1)

  #exhibit-header("Exhibit 20", fin_is.at("title", default: "Laporan Laba Rugi Komprehensif"), fin_is.source)
  #v(2pt)
  #fin-table(
    fin_is.headers,
    fin_is.rows.map(r => r.map(c => str(c))),
    palette: PALETTE,
  )

  #v(6pt)
  #exhibit-header("Exhibit 21", fin_bs.at("title", default: "Neraca Keuangan Konsolidasian"), fin_bs.source)
  #v(2pt)
  #fin-table(
    fin_bs.headers,
    fin_bs.rows.map(r => r.map(c => str(c))),
    palette: PALETTE,
  )
])

#pagebreak()

// =====================================================================
// PAGE 9 — CASH FLOW 6Y & COMPREHENSIVE RATIOS (30+)
// =====================================================================
#page-wrap(m.at("prepared_by", default: "RESEARCH — Equity Report"), m.date, m.ticker, 9, PALETTE, [
  #section-header(9, "Arus Kas 6 Tahun & Rasio Finansial Lengkap", PALETTE)

  #let fin_cf = data.financials.at(2)
  #let fin_ratio = data.financials.at(3)

  #grid(
    columns: (1fr, 1.15fr),
    column-gutter: 8pt,
    [
      #exhibit-header("Exhibit 22", fin_cf.at("title", default: "Laporan Arus Kas 6Y"), fin_cf.source)
      #v(1pt)
      #compact-fin-table(
        fin_cf.headers,
        fin_cf.rows.map(r => r.map(c => str(c))),
        palette: PALETTE,
      )
    ],
    [
      #exhibit-header("Exhibit 23", fin_ratio.at("title", default: "Rasio Keuangan Lengkap"), fin_ratio.source)
      #v(1pt)
      #compact-fin-table(
        fin_ratio.headers,
        fin_ratio.rows.map(r => r.map(c => str(c))),
        palette: PALETTE,
      )
    ]
  )
])

#pagebreak()

// =====================================================================
// PAGE 10 — PEERS COMPARISON & RISK ANALYSIS
// =====================================================================
#page-wrap(m.at("prepared_by", default: "RESEARCH — Equity Report"), m.date, m.ticker, 10, PALETTE, [
  #section-header(10, "Perbandingan Peers & Analisis Risiko", PALETTE)

  #let peer_tab = data.peers.tables.at(0)
  #exhibit-header("Exhibit 24", "Perbandingan Emiten " + peer_tab.pillar, peer_tab.source)
  #v(2pt)
  #fin-table(
    peer_tab.headers,
    peer_tab.rows.map(r => r.map(c => str(c))),
    palette: PALETTE,
  )

  #v(6pt)
  #text(size: 9.5pt, weight: "bold", fill: PALETTE.brand_dark)[Faktor Risiko Utama Spesifik Sektor #m.sector]
  #v(3pt)

  #let risks = data.at("risks", default: ())
  #if risks.len() > 0 {
    grid(
      columns: (1fr, 1fr),
      gutter: 6pt,
      ..risks.map(r => card(PALETTE)[
        #text(weight: "bold", fill: PALETTE.neg)[#r.bucket]
        #v(1pt)
        #text(size: 6.8pt)[
          #r.detail
        ]
      ])
    )
  }
])

#pagebreak()

// =====================================================================
// PAGE 11 — RATING GUIDE (9 ROWS), REGULATORY DISCLAIMER & CONTACT
// =====================================================================
#page-wrap(m.at("prepared_by", default: "RESEARCH — Equity Report"), m.date, m.ticker, 11, PALETTE, [
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
      Analis riset yang tercantum dalam laporan ini menyatakan secara independen bahwa: (1) Semua pandangan yang diungkapkan secara akurat merefleksikan penilaian fundamental terhadap #m.company_name (#m.ticker); (2) Kompensasi analis tidak berhubungan, baik langsung maupun tidak langsung, dengan rekomendasi atau target harga spesifik; (3) Analis tidak memiliki kepemilikan saham finansial material pada emiten yang dianalisis.
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
          - *Institusi:* #m.at("prepared_by", default: "RESEARCH — Sectors Hackathon 2026")
          - *Tanggal Publikasi:* #m.date · Bahasa: Indonesia (ID)
          - *Analis Utama:* #m.analyst.name (#m.analyst.role)
          - *Kontak Surel:* #m.analyst.email
        ]
      ],
      [
        #text(size: 7pt, weight: "bold", fill: PALETTE.muted)[KANTOR PUSAT & PROVENANCE]
        #v(2pt)
        #text(size: 6.8pt)[
          - *Kantor Pusat:* #m.head_office
          - *Engine Valuasi:* scripts/dcf_engine.py & scripts/blended_engine.py
          - *Audit Port:* abidamassi/dcf-valuation-tool (WACC #data.cDcf.wacc.wacc_raw%)
          - *Portal Riset:* www.skt.id/research
        ]
      ]
    )
  ]
])
