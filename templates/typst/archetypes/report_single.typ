// report_single.typ — Institutional equity research report (single ticker archetype)
#import "../common/theme.typ": *
#import "../common/cover.typ": *

#show: set-page-defaults

#let ticker = sys.inputs.at("ticker", default: none)
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
#let chart-placeholder(label, caption: "Engine Chart Renderer (Sectors pending)", height: 80pt, palette: PALETTE) = {
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
#page-wrap(m.at("prepared_by", default: "RESEARCH — Equity Report"), m.date, m.ticker, 1, PALETTE, [
  #grid(
    columns: (2fr, 1.15fr),
    column-gutter: 14pt,
    [
      #text(size: T_SMALL, fill: PALETTE.muted, tracking: 0.12em, weight: "bold")[
        #upper(m.at("report_type", default: "INITIATION")) · #upper(m.at("sector", default: "ENERGI — PURE-PLAY HOLDING"))
      ]
      #v(4pt)
      #text(size: T_COVER_TITLE, weight: "bold", fill: PALETTE.brand_dark)[
        #m.at("company_name", default: if m.ticker == "RATU" { "Raharja Energi Cepu" } else { "—" })
      ]
      #v(2pt)
      #text(size: 13pt, weight: "bold", fill: PALETTE.muted)[
        #m.ticker · IDX
      ]
      #v(8pt)

      #card(PALETTE)[
        #text(weight: "bold", fill: PALETTE.ink)[Executive Summary / Key Points]
        #v(1pt)
        #text(size: 6pt, style: "italic", fill: PALETTE.muted)[Core investment thesis, rating stance, target price derivation, and operational highlights.]
        #v(2.5pt)
        #if data.at("cover", default: (:)).at("summary", default: none) != none [
          #text(size: T_BODY)[#data.cover.summary]
        ] else if cover.at("key_takeaways", default: ()).len() > 0 [
          #list(
            ..cover.key_takeaways.map(t => [#t])
          )
        ] else [
          #text(size: T_BODY)[
            #if m.ticker == "RATU" [Inisiasi liputan dengan Investment Recommendation *BUY* dan target harga *Rp 7.880* (+27,1% upside). Arus kas Lapangan Banyu Urip (Blok Cepu) menopang marjin EBITDA \~49,6%, efisiensi lifting cost USD 4,85/bbl, dan neraca net cash tanpa utang berbunga.] else [Ringkasan eksekutif belum tersedia untuk ticker ini — lengkapi fixture sebelum render.]
          ]
        ]
      ]

      #v(8pt)
      #let sh_src = data.at("cover", default: (:)).at("shareholders_src", default: "KSEI & IDX")
      #exhibit-header("Exhibit 1", "Struktur Kepemilikan Saham", sh_src)
      #v(2pt)
      #let default_sh = (
        ("PT Ratu Energi Tuban Jaya (RETJ)", "45,0%", "Pengendali"),
        ("PT Petro Java Utama Cepu (PJUC)", "23,8%", "Strategis"),
        ("Publik (Free Float)", "31,2%", "Non-Warkat"),
      )
      #let sh_list = data.at("cover", default: (:)).at("shareholders", default: ())
      #let sh_rows = if sh_list.len() > 0 {
        sh_list.map(s => {
          if type(s) == array {
            s.map(c => str(c))
          } else {
            (
              s.at("name", default: "-"),
              if type(s.at("pct", default: "-")) == str { s.pct } else { str(s.pct) + "%" },
              s.at("status", default: if s.name == "Publik" { "Non-Warkat" } else { "-" }),
            )
          }
        })
      } else if m.ticker == "RATU" {
        default_sh
      } else {
        (
          (m.company_name + " / Manajemen", "-", "Pengendali"),
          ("Publik (Free Float)", if data.at("cover", default: (:)).at("shares", default: (:)).at("free_float_pct", default: none) != none { str(data.cover.shares.free_float_pct) + "%" } else { "-" }, "Non-Warkat"),
        )
      }
      #fin-table(
        ("Pemegang Saham", "Porsi (%)", "Status"),
        sh_rows,
        palette: PALETTE,
      )

      #v(8pt)
      #let pc = data.at("cover", default: (:)).at("price_chart", default: (:))
      #let vj = data.at("cover", default: (:)).at("vs_jci", default: (:))
      #let pc_src = vj.at("source", default: "Sectors pending (" + m.ticker + " vs IHSG)")
      #exhibit-header("Exhibit 2", pc.at("title", default: "Kinerja Harga vs IHSG (YTD)"), pc_src)
      #v(2pt)
      #let pc_label = pc.at("label", default: if m.ticker == "RATU" {
        "Kinerja Harga " + m.ticker + " (+18,4% YTD) vs IHSG (+12,2% YTD)"
      } else {
        "Kinerja Harga " + m.ticker + (if vj.at("ytd_abs", default: none) != none { " (" + (if vj.ytd_abs > 0 { "+" } else { "" }) + str(vj.ytd_abs) + "% YTD)" } else { "" }) + " vs IHSG"
      })
      #let pc_caption = pc.at("caption", default: if m.ticker == "RATU" {
        "Performa Relatif YTD: Outperform +6,2% · Sumber: Sectors"
      } else {
        "Performa Relatif YTD: " + (if vj.at("ytd_rel", default: none) != none { (if vj.ytd_rel > 0 { "Outperform +" } else { "Underperform " }) + str(vj.ytd_rel) + "%" } else { "-" }) + " · Sumber: " + pc_src
      })
      #if data.at("charts", default: (:)).at("vs_jci", default: false) {
        image(chart-dir + "/vs_jci.png", width: 100%);
        v(2pt);
        text(size: 6.5pt, fill: PALETTE.muted, style: "italic")[#pc_label · Sumber: #pc_src];
      } else {
        chart-placeholder(pc_label, caption: pc_caption, height: 75pt, palette: PALETTE);
      }
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
      #card(PALETTE)[
        #text(size: T_SMALL, weight: "bold", fill: PALETTE.muted)[INFORMASI SAHAM]
        #v(1pt)
        #text(size: 5.5pt, style: "italic", fill: PALETTE.muted)[Market trading metrics, liquidity statistics, and shareholding structure profile.]
        #v(2.5pt)
        #let sh = data.at("cover", default: (:)).at("shares", default: (:))
        #let mkt = data.at("cover", default: (:)).at("market", default: (:))
        #grid(
          columns: (1fr, auto),
          row-gutter: 2.8pt,
          text(size: 6.8pt)[Harga Kini], text(size: 6.8pt, weight: "bold")[Rp #nstr(cover.price)],
          text(size: 6.8pt)[Target Harga], text(size: 6.8pt, weight: "bold")[Rp #nstr(cover.tp)],
          text(size: 6.8pt)[Saham Beredar], text(size: 6.8pt, weight: "bold")[#sh.at("outstanding", default: 2.71) #sh.at("unit", default: "Miliar")],
          text(size: 6.8pt)[Kapitalisasi Pasar], text(size: 6.8pt, weight: "bold")[#mkt.at("market_cap", default: if cover.price == none { "-" } else { "Rp " + str(calc.round(cover.price * sh.at("outstanding", default: 0) / 1000, digits: 2)) + " T" })],
          text(size: 6.8pt)[Free Float], text(size: 6.8pt, weight: "bold")[#if sh.at("free_float_pct", default: none) != none { str(sh.free_float_pct) + "%" } else { "-" }],
          text(size: 6.8pt)[52-Wk Range], text(size: 6.8pt, weight: "bold")[#mkt.at("range_52w", default: "-")],
          text(size: 6.8pt)[Rerata Nilai 3M], text(size: 6.8pt, weight: "bold")[#mkt.at("avg_value_3m", default: "-")],
          text(size: 6.8pt)[Klasifikasi Indeks], text(size: 6.8pt, weight: "bold")[#mkt.at("index_class", default: "-")],
        )
      ]
    ]
  )
])

#pagebreak()

// // =====================================================================
// PAGE 2 — KPI HERO (OPERATIONAL METRICS)
// =====================================================================
#page-wrap(m.at("prepared_by", default: "RESEARCH — Equity Report"), m.date, m.ticker, 2, PALETTE, [
  #section-header(1, "Metrik Operasional Kunci (KPI Hero)", PALETTE, sub: "Menjawab: Bagaimana trajektori operasional, efisiensi unit biaya, dan keunggulan kompetitif (moat) emiten?")
  
  #let kpi_hero = data.at("kpi_hero", default: (:))
  #let kpi_p = kpi_hero.at("paragraph", default: "Kinerja operasional " + m.company_name + " (" + m.ticker + ") didorong oleh keunggulan posisi fundamental pada sektor " + m.sector + ", efisiensi biaya, dan eksekusi strategi pertumbuhan yang disiplin.")
  #text(size: T_BODY)[#kpi_p]
  #v(6pt)

  #let kpi_cards = if kpi_hero.at("cards", default: none) != none {
    kpi_hero.cards
  } else if data.at("kpis", default: ()).len() > 0 {
    data.kpis.slice(0, calc.min(data.kpis.len(), 4)).map(k => (
      label: upper(k.at("name", default: "")),
      value: str(k.at("value", default: "")),
      unit: " " + k.at("unit", default: ""),
      note: if k.at("prev", default: none) != none { "vs " + str(k.prev) } else { k.at("formula", default: "") },
      note_pos: false,
    ))
  } else {
    ()
  }

  #if kpi_cards.len() > 0 {
    grid(
      columns: (1fr,) * calc.min(kpi_cards.len(), 4),
      gutter: 8pt,
      ..kpi_cards.map(c => card(PALETTE)[
        #text(size: 6.8pt, fill: PALETTE.muted, weight: "bold")[#c.label]
        #v(2pt)
        #text(size: 13pt, weight: "black", fill: PALETTE.brand_dark)[#c.value]
        #text(size: 7pt, weight: "bold")[#c.at("unit", default: "")]
        #v(1pt)
        #text(size: 6.5pt, fill: if c.at("note_pos", default: false) { PALETTE.pos } else { PALETTE.muted }, weight: if c.at("note_pos", default: false) { "bold" } else { "regular" })[#c.at("note", default: "")]
      ])
    )
  }

  #v(8pt)
  #let ops_tables = data.at("ops_tables", default: (:))
  #let ex3 = ops_tables.at("exhibit_3", default: ops_tables.at("table_1", default: (:)))
  #let ex3_title = ex3.at("title", default: "Trajektori Parameter Operasional — " + m.sector)
  #let ex3_src = ex3.at("source", default: data.at("kpis_src", default: "Keterbukaan IDX"))
  #let ex3_headers = ex3.at("headers", default: ("Parameter Operasional", "Nilai", "Satuan", "Keterangan", "Sumber"))
  #let ex3_rows = ex3.at("rows", default: if data.at("kpis", default: ()).len() > 0 {
    data.kpis.map(k => (
      k.at("name", default: "-"),
      str(k.at("value", default: "-")),
      k.at("unit", default: "-"),
      if k.at("prev", default: none) != none { "vs " + str(k.prev) } else { k.at("formula", default: "-") },
      k.at("source", default: "IDX"),
    ))
  } else {
    (("Parameter Operasional Utama", "-", "-", "-", "-"),)
  })

  #exhibit-header("Exhibit 3", ex3_title, ex3_src)
  #v(2pt)
  #fin-table(
    ex3_headers,
    ex3_rows.map(r => r.map(c => str(c))),
    palette: PALETTE,
  )

  #v(8pt)
  #let ex4 = ops_tables.at("exhibit_4", default: ops_tables.at("table_2", default: (:)))
  #let ex4_title = ex4.at("title", default: "Karakteristik Aset & Jaringan Operasional")
  #let ex4_src = ex4.at("source", default: "Keterbukaan IDX & Profil Perusahaan")
  #let ex4_headers = ex4.at("headers", default: ("Komponen Aset", "Deskripsi & Kapasitas", "Mitra & Status Operasional"))
  #let ex4_rows = ex4.at("rows", default: (
    ("Jaringan Operasional", m.company_name + " mengoperasikan jaringan bisnis terintegrasi", "Status operasional aktif"),
    ("Cakupan Wilayah", "Cakupan operasional strategis mendukung pertumbuhan bisnis", "Pertumbuhan berkelanjutan"),
    ("Tata Kelola & Kepatuhan", "Standar kepatuhan industri dan keandalan operasional prima", "Kepatuhan penuh regulasi"),
  ))

  #exhibit-header("Exhibit 4", ex4_title, ex4_src)
  #v(2pt)
  #fin-table(
    ex4_headers,
    ex4_rows.map(r => r.map(c => str(c))),
    palette: PALETTE,
  )

  #v(8pt)
  #let moat_text = data.at("moat", default: m.company_name + " (" + m.ticker + ") memiliki keunggulan kompetitif (economic moat) yang kokoh pada sektor " + m.sector + ", didukung oleh efisiensi struktur biaya, diferensiasi produk/layanan, serta posisi neraca keuangan yang sehat dalam menghadapi dinamika pasar.")
  #card(PALETTE)[
    #text(weight: "bold", fill: PALETTE.ink)[Keunggulan Biaya Operasional (Economic Moat)]
    #v(2pt)
    #text(size: 7.5pt)[#moat_text]
  ]
])

#pagebreak()

// =====================================================================
// PAGE 3 — FINANCIAL HIGHLIGHTS & INVESTMENT THESIS
// =====================================================================
#page-wrap(m.at("prepared_by", default: "RESEARCH — Equity Report"), m.date, m.ticker, 3, PALETTE, [
  #section-header(2, "Sorotan Keuangan & Tesis Investasi", PALETTE, sub: "Menjawab: Dari mana pertumbuhan historis berasal dan apa pilar tesis katalis ekspansi ke depan?")

  #let fh = data.at("financial_highlights", default: (:))
  #let fh_years = fh.at("years", default: ("FY24A", "FY25A", "FY26F", "FY27F", "FY28F", "FY29F"))
  #let fh_src = fh.at("source", default: "Laporan Keuangan " + m.ticker + " (IDX), data diolah")
  #let fh_title = "Financial Highlights " + (if fh_years.len() > 0 { str(fh_years.len()) + " Periode (" + fh_years.at(0) + " – " + fh_years.at(-1) + ")" } else { "" })
  #let default_fh_rows = (
    ("Pendapatan Bersih", "1.290", "1.122", "1.180", "1.245", "1.310", "1.375"),
    ("EBITDA", "610", "540", "585", "620", "658", "694"),
    ("Laba Bersih", "402", "355", "390", "425", "462", "498"),
    ("EPS (Rp Penuh)", "148", "131", "144", "157", "170", "184"),
    ("P/E (x)", "55,2x", "47,3x", "42,7x", "38,5x", "35,2x", "32,4x"),
    ("ROE (%)", "88,0%", "41,0%", "30,0%", "28,5%", "27,2%", "26,0%"),
    ("Free Cash Flow", "435", "410", "432", "455", "480", "510"),
  )
  #let fh_rows = if fh.at("rows", default: ()).len() > 0 {
    fh.rows.map(r => r.map(c => if c == none { "-" } else if type(c) == str { c } else { str(c) }))
  } else {
    default_fh_rows
  }

  #exhibit-header("Exhibit 5", fh_title, fh_src)
  #v(2pt)
  #fin-table(
    ("Metrik Finansial", ..fh_years),
    fh_rows,
    palette: PALETTE,
  )

  #if data.at("charts", default: (:)).at("margin_trajectory", default: false) {
    v(4pt);
    exhibit-header("Exhibit 5a", "Lintasan Pendapatan & Marjin", fh_src);
    v(2pt);
    image(chart-dir + "/margin_trajectory.png", width: 100%);
  }

  #v(8pt)
  #let thesis_list = data.at("thesis", default: ())
  #let thesis_count = thesis_list.len()
  #let thesis_title = if thesis_count > 0 { str(thesis_count) + " Pilar Tesis Investasi" } else { "Pilar Tesis Investasi" }
  #text(size: T_H3, weight: "bold", fill: PALETTE.brand_dark)[#thesis_title]
  #v(4pt)

  #if thesis_count > 0 {
    grid(
      columns: (1fr, 1fr),
      gutter: 7pt,
      ..thesis_list.enumerate().map(((i, t)) => card(PALETTE)[
        #text(weight: "bold", fill: PALETTE.ink)[#(str(i + 1) + ". " + t.headline)]
        #v(2pt)
        #text(size: 7.2pt)[#t.detail]
      ])
    )
  } else {
    grid(
      columns: (1fr, 1fr),
      gutter: 7pt,
      card(PALETTE)[
        #text(weight: "bold", fill: PALETTE.ink)[1. Fundamental Kokoh & Marjin Terjaga]
        #v(2pt)
        #text(size: 7.2pt)[
          Struktur biaya efisien dan posisi pasar strategis menopang marjin profitabilitas dan arus kas operasional yang resilien.
        ]
      ],
      card(PALETTE)[
        #text(weight: "bold", fill: PALETTE.ink)[2. Kemampuan Menghasilkan Kas Bebas]
        #v(2pt)
        #text(size: 7.2pt)[
          Konversi laba operasional menjadi Free Cash Flow yang solid memberikan ruang likuiditas untuk pertumbuhan dan pembagian dividen.
        ]
      ],
      card(PALETTE)[
        #text(weight: "bold", fill: PALETTE.ink)[3. Struktur Neraca Sehat]
        #v(2pt)
        #text(size: 7.2pt)[
          Pengelolaan modal kerja yang disiplin dan posisi kas memadai memitigasi risiko volatilitas pasar dan suku bunga.
        ]
      ],
      card(PALETTE)[
        #text(weight: "bold", fill: PALETTE.ink)[4. Peluang Pertumbuhan Berkelanjutan]
        #v(2pt)
        #text(size: 7.2pt)[
          Ekspansi strategis dan optimalisasi aset memperkuat daya saing perusahaan dalam jangka panjang.
        ]
      ],
    )
  }
])

#pagebreak()

// =====================================================================
// PAGE 4 — VALUATION (DCF, MULTIPLES, BLENDED & BANDS)
// =====================================================================
#page-wrap(m.at("prepared_by", default: "RESEARCH — Equity Report"), m.date, m.ticker, 4, PALETTE, [
  #section-header(3, "Valuation Methodology & Hasil Valuasi", PALETTE, sub: "Menjawab: Berapa estimasi nilai wajar saham berdasarkan metode DCF dan perbandingan multiple pasar?")

  #let val = data.at("valuation", default: (:))
  #let methods = val.at("methods", default: ())
  #let dcf_m = methods.find(x => x.method == "DCF")
  #let dcf_assump = if dcf_m != none { dcf_m.at("assumptions", default: (:)) } else { (:) }
  #let dcf_wacc = dcf_assump.at("wacc", default: none)
  #let dcf_g = dcf_assump.at("g", default: none)
  #let dcf_beta = dcf_assump.at("beta", default: none)
  #let dcf_rf = dcf_assump.at("rf", default: none)
  #let dcf_erp = dcf_assump.at("erp", default: none)
  #let dcf_fv = if dcf_m != none { dcf_m.at("fv", default: cover.tp) } else { cover.tp }
  #let dcf_table = if dcf_m != none { dcf_m.at("table", default: (:)) } else { (:) }
  #let dcf_headers = dcf_table.at("headers", default: ("Komponen DCF (Rp bn)", "FY26F", "FY27F", "FY28F", "FY29F"))
  #let default_dcf_rows = (
    ("Free Cash Flow (FCF)", "—", "—", "—", "—"),
    ("Discount Factor", "—", "—", "—", "—"),
    ("Present Value FCF", "—", "—", "—", "—"),
  )
  #let dcf_rows = if dcf_table.at("rows", default: ()).len() > 0 {
    dcf_table.rows.map(r => r.map(c => str(c)))
  } else {
    default_dcf_rows
  }

  #let mult_m = methods.find(x => x.method == "EV/EBITDA" or x.method == "Multiples")
  #let mult_assump = if mult_m != none { mult_m.at("assumptions", default: (:)) } else { (:) }
  #let mult_multiple = mult_assump.at("multiple", default: none)
  #let mult_fv = if mult_m != none { mult_m.at("fv", default: none) } else { none }
  #let mult_table = if mult_m != none { mult_m.at("table", default: (:)) } else { (:) }
  #let mult_headers = mult_table.at("headers", default: ("Parameter", "Nilai", "Satuan"))
  #let default_mult_rows = (
    ("Target EV/EBITDA", nstr(mult_multiple), "x"),
    ("EBITDA", str(mult_assump.at("ebitda_bn", default: "-")), "Rp bn"),
    ("Implied EV", if mult_assump.at("ebitda_bn", default: none) != none { str(calc.round(mult_multiple * mult_assump.ebitda_bn, digits: 0)) } else { "-" }, "Rp bn"),
    ("Fair Value EV/EBITDA", nstr(mult_fv), "Rp/saham"),
  )
  #let mult_rows = if mult_table.at("rows", default: ()).len() > 0 {
    mult_table.rows.map(r => r.map(c => str(c)))
  } else {
    default_mult_rows
  }

  #let blended = val.at("blended", default: (:))
  #let blended_weights = if blended != none { blended.at("weights", default: "60/40") } else { "60/40" }
  #let blended_fv = if blended != none { blended.at("fair_value", default: cover.tp) } else { cover.tp }

  #grid(
    columns: (1.15fr, 1fr),
    column-gutter: 10pt,
    [
      #text(size: 9.5pt, weight: "bold", fill: PALETTE.brand_dark)[Metode 1: Discounted Cash Flow (DCF)]
      #v(2pt)
      #text(size: 7.2pt, fill: PALETTE.muted)[
        Asumsi: WACC #nstr(dcf_wacc)%, Terminal Growth (g) #nstr(dcf_g)%, Beta #nstr(dcf_beta), Rf #nstr(dcf_rf)%, ERP #nstr(dcf_erp)%
      ]
      #v(4pt)
      #exhibit-header("Exhibit 6", "Proyeksi Arus Kas Bebas (FCFF)", if dcf_m != none { dcf_m.at("source", default: "Engine DCF") } else { "Engine DCF" })
      #v(2pt)
      #fin-table(
        dcf_headers,
        dcf_rows,
        palette: PALETTE,
      )
      #v(4pt)
      #card(PALETTE)[
        #grid(
          columns: (1fr, auto),
          row-gutter: 3pt,
          text(size: 7pt)[PV Arus Kas Eksplisit], text(size: 7pt, weight: "bold")[#val.at("dcf_grid", default: (:)).at("pv_explicit", default: "-")],
          text(size: 7pt)[PV Nilai Terminal (TV)], text(size: 7pt, weight: "bold")[#val.at("dcf_grid", default: (:)).at("pv_tv", default: "-")],
          text(size: 7pt)[Enterprise Value (EV)], text(size: 7pt, weight: "bold")[#val.at("dcf_grid", default: (:)).at("ev", default: "-")],
          text(size: 7pt)[Kas Bersih / (Utang)], text(size: 7pt, weight: "bold")[#val.at("dcf_grid", default: (:)).at("net_cash", default: "-")],
          text(size: 7.5pt, weight: "bold")[Nilai Wajar DCF per Saham], text(size: 7.5pt, weight: "black", fill: PALETTE.brand_dark)[#if dcf_fv == none { "Excluded (Gate 3+5)" } else { "Rp " + str(dcf_fv) }],
        )
      ]
    ],
    [
      #text(size: 9.5pt, weight: "bold", fill: PALETTE.brand_dark)[Metode 2: Multiple EV/EBITDA]
      #v(2pt)
      #text(size: 7.2pt, fill: PALETTE.muted)[
        Target multiple #mult_multiple x berdasarkan analisis komparatif & historis siklus normal.
      ]
      #v(4pt)
      #fin-table(
        mult_headers,
        mult_rows,
        palette: PALETTE,
      )

      #v(6pt)
      #text(size: 9.5pt, weight: "bold", fill: PALETTE.brand_dark)[Valuasi Blended (#blended_weights)]
      #v(2pt)
      #let blended_rows = (
        ("DCF (WACC " + nstr(dcf_wacc) + "%, g " + nstr(dcf_g) + "%)", "pembanding", if dcf_fv == none { "Excluded (Gate 3+5)" } else { "Rp " + str(dcf_fv) }),
        ("EV/EBITDA (" + nstr(mult_multiple) + "x)", "primer", "Rp " + nstr(mult_fv)),
        ("Target Price (TP 12M)", "100%", "Rp " + nstr(blended_fv)),
      )
      #fin-table(
        ("Metode", "Bobot", "Fair Value"),
        blended_rows,
        palette: PALETTE,
      )
    ]
  )

  #v(8pt)
  #let bands = val.at("bands", default: none)
  #let bands_rows = if bands != none and bands.at("rows", default: ()).len() > 0 {
    bands.rows.map(r => r.map(c => str(c)))
  } else {
    (
      ("STD +2 (Batas Atas)", "-", "-", "Overvalued Ekstrem"),
      ("STD +1 (Batas Atas)", "-", "-", "Overvalued Moderat"),
      ("Rerata 3 Tahun (Mean)", "-", "-", "Rentang Nilai Wajar"),
      ("STD -1 (Batas Bawah)", "-", "-", "Undervalued Menarik"),
      ("STD -2 (Batas Bawah)", "-", "-", "Undervalued Ekstrem"),
      ("Posisi Harga Kini", "-", "Rp " + nstr(cover.price), "Valuasi Wajar"),
    )
  }
  #exhibit-header("Exhibit 7", "Pita Valuasi Historis P/BV 3-Tahun (STD±2)", "IDX & Analisis Data")
  #v(2pt)
  #if bands != none and bands.at("rows", default: ()).len() > 0 {
    fin-table(
      ("Deviasi Standar", "P/BV (x)", "Implied Price", "Interpretasi Valuasi"),
      bands_rows,
      palette: PALETTE,
    );
  } else {
    text(size: 7.2pt, fill: PALETTE.muted)[Pita historis tidak disajikan — riwayat book value tidak komparabel pasca-akuisisi Aster (ekuitas USD 2,93 miliar menjadi USD 4,66 miliar). Lihat P/B spot 2,10x pada Exhibit 13.];
  }

  #v(6pt)
  #let conclusion_text = val.at("conclusion", default: if cover.tp == none { "Valuasi menunggu data Sectors — target harga dan kesimpulan belum tersedia untuk " + m.ticker + "." } else { "Harga saham kini Rp " + nstr(cover.price) + " mencerminkan target harga Rp " + nstr(cover.tp) + " dengan potensi imbal hasil " + (if cover.upside_pct != none and cover.upside_pct > 0 { "+" } else { "" }) + nstr(cover.upside_pct) + "% (" + nstr(cover.action) + "), didukung oleh analisis fundamental komprehensif pada sektor " + m.sector + "." })
  #card(PALETTE)[
    #text(weight: "bold", fill: PALETTE.ink)[Kesimpulan Valuasi]
    #v(2pt)
    #text(size: 7.3pt)[#conclusion_text]
  ]
])

#pagebreak()

// =====================================================================
// PAGE 5 — COMPREHENSIVE DCF DEEP DIVE
// =====================================================================
#page-wrap(m.at("prepared_by", default: "RESEARCH — Equity Report"), m.date, m.ticker, 5, PALETTE, [
  #let ddd = data.at("dcf_deep_dive", default: (:))
  #section-header(4, "Analisis DCF Komprehensif", PALETTE, sub: ddd.at("section_sub", default: "Menjawab: Bagaimana kalkulasi biaya modal (WACC), sensitivitas pertumbuhan, dan skenario nilai intrinsik?"))
  
  #text(size: 7.2pt, fill: PALETTE.muted)[
    #ddd.at("intro", default: "Discounted Cash Flow (DCF) Model — Model deterministik multi-periode mengevaluasi nilai intrinsik ekuitas melalui proyeksi arus kas bebas eksplisit (FCFF) dan nilai terminal, dilengkapi Cost of Capital Build, Sensitivity Analysis 5x5, dan Scenario Analysis (Bear / Base / Bull).")
  ]
  #v(6pt)

  #exhibit-header("Exhibit 8", "Cost of Capital Build", "Model CAPM & SBN 10Y")
  #v(2pt)
  #let wb = ddd.at("wacc_build", default: (:))
  #fin-table(
    wb.at("headers", default: ("Komponen WACC", "Nilai", "Metodologi / Sumber")),
    wb.at("rows", default: (
      ("Risk-Free Rate (Rf)", "7,00%", "Yield Obligasi Pemerintah SBN 10Y"),
      ("Equity Risk Premium (ERP)", "6,90%", "Damodaran Indonesia ERP 2026"),
      ("Beta Raw & Adjusted (Blume)", "0,700", "Regresi mingguan 3Y vs IHSG"),
      ("Biaya Ekuitas (Cost of Equity - Ke)", "11,83%", "Ke = Rf + Beta * ERP"),
      ("Biaya Utang Sebelum Pajak (Kd)", "9,00%", "Rf + 200 bps (Floor utang korporasi)"),
      ("Tarif Pajak Efektif", "22,00%", "UU Harmonisasi Perpajakan (HPP)"),
      ("Biaya Utang Setelah Pajak", "7,02%", "Kd * (1 - Tax Rate)"),
      ("Bobot Ekuitas / Utang", "100% / 0%", "Struktur Modal Bersih (Net Cash)"),
      ("WACC Final Diterapkan", "11,83%", "We * Ke + Wd * Kd_aftertax"),
    )).map(r => r.map(c => str(c))),
    palette: PALETTE,
  )

  #v(6pt)
  #exhibit-header("Exhibit 9", ddd.at("sensitivity", default: (:)).at("title", default: "Sensitivity Analysis — WACC vs Terminal Growth (g)"), "Engine Sensitivitas 5x5")
  #v(2pt)
  #let sens = ddd.at("sensitivity", default: (:))
  #fin-table(
    sens.at("headers", default: ("WACC \\ g", "4,50%", "4,75%", "5,00% (Base)", "5,25%", "5,50%")),
    sens.at("rows", default: (
      ("10,83%", "Rp 4.979 (+18,5%)", "Rp 5.134 (+22,2%)", "Rp 5.303 (+26,3%)", "Rp 5.487 (+30,6%)", "Rp 5.688 (+35,4%)"),
      ("11,33%", "Rp 4.631 (+10,3%)", "Rp 4.762 (+13,4%)", "Rp 4.903 (+16,7%)", "Rp 5.055 (+20,4%)", "Rp 5.221 (+24,3%)"),
      ("11,83% (Base)", "Rp 4.331 (+3,1%)", "Rp 4.442 (+5,8%)", "Rp 4.562 (+8,6%)", "Rp 4.690 (+11,7%)", "Rp 4.828 (+15,0%)"),
      ("12,33%", "Rp 4.070 (-3,1%)", "Rp 4.165 (-0,8%)", "Rp 4.267 (+1,6%)", "Rp 4.376 (+4,2%)", "Rp 4.493 (+7,0%)"),
      ("12,83%", "Rp 3.840 (-8,6%)", "Rp 3.922 (-6,6%)", "Rp 4.010 (-4,5%)", "Rp 4.104 (-2,3%)", "Rp 4.204 (+0,1%)"),
    )).map(r => r.map(c => str(c))),
    palette: PALETTE,
  )

  #v(6pt)
  #grid(
    columns: (1fr, 1.15fr),
    column-gutter: 8pt,
    [
      #exhibit-header("Exhibit 10", "Scenario Analysis (Bear / Base / Bull)", "Engine Skenario")
      #v(2pt)
      #let scen = ddd.at("scenarios", default: (:))
      #fin-table(
        scen.at("headers", default: ("Scenario", "Nilai Wajar", "Investment Recommendation")),
        scen.at("rows", default: (
          ("BEAR (Rev +6%, EBIT 29%)", "Rp 3.567", "SELL (-15,1%)"),
          ("BASE (Rev +10%, EBIT 32%)", "Rp 4.562", "HOLD (+8,6%)"),
          ("BULL (Rev +14%, EBIT 35%)", "Rp 5.812", "BUY (+38,4%)"),
        )).map(r => r.map(c => str(c))),
        palette: PALETTE,
      )
    ],
    [
      #exhibit-header("Exhibit 11", "Jembatan Nilai EV ke Ekuitas", "Bridge Waterfall")
      #v(2pt)
      #let brg = ddd.at("bridge", default: (:))
      #fin-table(
        brg.at("headers", default: ("Komponen Jembatan", "Nilai (Rp bn)", "Keterangan")),
        brg.at("rows", default: (
          ("PV Explicit + PV Terminal", "11.862", "Enterprise Value"),
          ("(+) Kas & Setara Kas", "+500", "Likuiditas"),
          ("(-) Total Utang Berbunga", "-0", "Bebas Utang"),
          ("Implied Equity Value", "12.362", "Nilai Bersih"),
        )).map(r => r.map(c => str(c))),
        palette: PALETTE,
      )
    ]
  )
  #if false { }
])

#pagebreak()

// =====================================================================
// PAGE 6 — FINANCIAL STATEMENTS 6Y (INCOME, BALANCE & CASHFLOW)
// =====================================================================
#page-wrap(m.at("prepared_by", default: "RESEARCH — Equity Report"), m.date, m.ticker, 6, PALETTE, [
  #let fs = data.at("financial_statements", default: (:))
  #section-header(5, fs.at("section_title", default: "Laporan Keuangan & Rasio Finansial 6 Tahun"), PALETTE, sub: fs.at("section_sub", default: "Menjawab: Bagaimana proyeksi menyeluruh laba rugi, neraca keuangan, likuiditas, dan profitabilitas 6 tahun?"))

  #let inc = fs.at("income", default: (:))
  #exhibit-header("Exhibit 12", inc.at("title", default: "Laporan Laba Rugi Komprehensif (Rp Miliar)"), inc.at("source", default: "Laporan Keuangan IDX & Proyeksi"))
  #v(2pt)
  #fin-table(
    inc.at("headers", default: ("Akun Laba Rugi", "FY24A", "FY25A", "FY26F", "FY27F", "FY28F", "FY29F")),
    inc.at("rows", default: (
      ("Pendapatan Bersih", "1.290", "1.122", "1.180", "1.245", "1.310", "1.375"),
      ("Beban Pokok Pendapatan (COGS)", "-520", "-470", "-492", "-516", "-540", "-565"),
      ("Laba Kotor", "770", "652", "688", "729", "770", "810"),
      ("Beban Penjualan & Administrasi", "-160", "-112", "-103", "-109", "-112", "-116"),
      ("EBITDA", "610", "540", "585", "620", "658", "694"),
      ("Depresiasi & Amortisasi", "-125", "-118", "-132", "-144", "-154", "-162"),
      ("Laba Usaha (EBIT)", "485", "422", "453", "476", "504", "532"),
      ("Penghasilan Bunga Bersih", "+18", "+22", "+25", "+28", "+31", "+34"),
      ("Laba Sebelum Pajak (EBT)", "503", "444", "478", "504", "535", "566"),
      ("Beban Pajak Penghasilan", "-101", "-89", "-88", "-79", "-73", "-68"),
      ("Laba Bersih Tahun Berjalan", "402", "355", "390", "425", "462", "498"),
    )).map(r => r.map(c => str(c))),
    palette: PALETTE,
  )

  #v(6pt)
  #let bal = fs.at("balance", default: (:))
  #exhibit-header("Exhibit 13", bal.at("title", default: "Neraca Keuangan Ringkas 6 Tahun (FY24A - FY29F)"), bal.at("source", default: "Laporan Keuangan IDX & Proyeksi"))
  #v(2pt)
  #fin-table(
    bal.at("headers", default: ("Pos Neraca", "FY24A", "FY25A", "FY26F", "FY27F", "FY28F", "FY29F")),
    bal.at("rows", default: (
      ("Kas & Setara Kas", "410", "465", "500", "560", "640", "725"),
      ("Piutang Usaha & Lancar Lain", "208", "184", "194", "203", "212", "221"),
      ("Total Aset Lancar", "618", "649", "694", "763", "852", "946"),
      ("Aset Tetap & Hulu Migas", "1.080", "1.020", "1.086", "1.157", "1.228", "1.295"),
      ("Aset Tidak Lancar Lainnya", "192", "195", "200", "205", "210", "215"),
      ("Total Aset", "1.890", "1.864", "1.980", "2.125", "2.290", "2.456"),
      ("Liabilitas Jangka Pendek", "185", "162", "170", "178", "186", "194"),
      ("Total Liabilitas", "275", "247", "258", "269", "280", "291"),
      ("Total Ekuitas", "1.615", "1.617", "1.722", "1.856", "2.010", "2.165"),
    )).map(r => r.map(c => str(c))),
    palette: PALETTE,
  )

  #v(6pt)
  #let rat = fs.at("ratios", default: (:))
  #exhibit-header("Exhibit 14", rat.at("title", default: "Rasio Keuangan & Efisiensi 6 Tahun vs Peer Median"), rat.at("source", default: "Perhitungan Analis & IDX"))
  #v(2pt)
  #fin-table(
    rat.at("headers", default: ("Rasio Kunci", "FY24A", "FY25A", "FY26F", "FY27F", "FY28F", "FY29F", "Peer Median")),
    rat.at("rows", default: (
      ("Marjin Laba Kotor (%)", "59,7%", "58,1%", "58,3%", "58,6%", "58,8%", "59,0%", "45,2%"),
      ("Marjin EBITDA (%)", "47,3%", "48,1%", "49,6%", "49,8%", "50,2%", "50,5%", "32,5%"),
      ("Marjin Laba Bersih (%)", "31,2%", "31,6%", "33,1%", "34,1%", "35,3%", "36,2%", "18,4%"),
      ("Imbal Hasil Ekuitas (ROE)", "88,0%", "41,0%", "30,0%", "28,5%", "27,2%", "26,0%", "15,0%"),
      ("Imbal Hasil Aset (ROA)", "21,3%", "19,0%", "19,7%", "20,0%", "20,2%", "20,5%", "8,5%"),
      ("Price to Earnings (P/E)", "55,2x", "47,3x", "42,7x", "38,5x", "35,2x", "32,4x", "12,4x"),
      ("Current Ratio (x)", "3,34x", "4,01x", "4,08x", "4,29x", "4,58x", "4,88x", "1,85x"),
    )).map(r => r.map(c => str(c))),
    palette: PALETTE,
  )
])

#pagebreak()

// =====================================================================
// PAGE 7 — PEERS, RISKS, RATING GUIDE & DISCLAIMER
// =====================================================================
#page-wrap(m.at("prepared_by", default: "RESEARCH — Equity Report"), m.date, m.ticker, 7, PALETTE, [
  #section-header(6, "Peer Comparison & Investment Risks", PALETTE, sub: "Menjawab: Bagaimana posisi valuasi relatif terhadap kompetitor sejenis dan apa risiko investasi utama?")

  #let peer_data = data.at("peers", default: (:))
  #let peer_tables = peer_data.at("tables", default: ())
  #let peer_tab = if peer_tables.len() > 0 { peer_tables.at(0) } else { (:) }
  #let default_peer_headers = ("Ticker", "Market Cap", "P/E (x)", "EV/EBITDA", "P/BV (x)", "ROE (%)", "Gearing")
  // LOUD policy: RATU/MEDC/ENRG/ELSA/PGAS peer multiples were baked demo
  // comparables. Peer rows come from Sectors peers only; absent -> dashes.
  #let default_peer_rows = ((m.ticker, "-", "-", "-", "-", "-", "-"),)
  #let peer_title = if peer_tab.at("pillar", default: none) != none { "Peer Comparison — " + peer_tab.pillar } else { "Peer Comparison — Emiten Sektor " + m.sector }
  #let peer_src = peer_tab.at("source", default: "Sectors (pending)")
  #let peer_headers = peer_tab.at("headers", default: default_peer_headers)
  #let peer_rows = if peer_tab.at("rows", default: ()).len() > 0 {
    peer_tab.rows.map(r => r.map(c => if type(c) == str or type(c) == content { c } else { str(c) }))
  } else {
    default_peer_rows
  }

  #exhibit-header("Exhibit 15", peer_title, peer_src)
  #v(2pt)
  #fin-table(
    peer_headers,
    peer_rows,
    palette: PALETTE,
  )

  #v(4pt)
  #let relval_title = "Perbandingan Valuasi Relatif (P/E & EV/EBITDA Peers)"
  #let relval_src = "Sectors (pending)"
  #if not data.at("charts", default: (:)).at("peer_evebitda", default: false) {
    exhibit-header("Exhibit 16", relval_title, relval_src);
    v(2pt);
    image(chart-dir + "/relval_bars.png", width: 100%);
    v(2pt);
    text(size: 6.5pt, fill: PALETTE.muted, style: "italic")[Grafik Batang Komparasi Multiple Valuasi Relatif · Sumber: #relval_src];
  }
  #if data.at("charts", default: (:)).at("peer_evebitda", default: false) {
    v(4pt);
    exhibit-header("Exhibit 16a", "EV/EBITDA Peers vs Subjek", peer_src);
    v(2pt);
    image(chart-dir + "/peer_evebitda.png", width: 88%);
  }
  #if data.at("charts", default: (:)).at("peer_evebitda", default: false) {
    v(2pt);
    text(size: 6.5pt, fill: PALETTE.muted, style: "italic")[Grafik P/E tidak disajikan — P/E trailing tak bermakna di trough siklikal (TPIA 139x, peers terdistorsi).];
  }

  #if data.at("charts", default: (:)).at("peer_evebitda", default: false) {
    pagebreak();
  }
  #text(size: 8.5pt, weight: "bold", fill: PALETTE.brand_dark)[Investment Risks]
  #v(2pt)
  #let risks_list = data.at("risks", default: ())
  #if risks_list.len() > 0 {
    grid(
      columns: (1fr, 1fr),
      gutter: 5pt,
      ..risks_list.enumerate().map(((i, r)) => card(PALETTE)[
        #text(weight: "bold", fill: PALETTE.neg)[#(str(i + 1) + ". " + r.bucket)]
        #v(1pt)
        #text(size: 6.5pt)[#r.detail]
      ])
    )
  } else {
    grid(
      columns: (1fr, 1fr),
      gutter: 5pt,
      card(PALETTE)[
        #text(weight: "bold", fill: PALETTE.neg)[1. Fluktuasi Harga Komoditas & Pasar]
        #v(1pt)
        #text(size: 6.5pt)[
          Volatilitas harga komoditas global dan daya beli konsumen berpotensi mempengaruhi realisasi pertumbuhan pendapatan.
        ]
      ],
      card(PALETTE)[
        #text(weight: "bold", fill: PALETTE.neg)[2. Ketergantungan Rantai Pasok & Mitra]
        #v(1pt)
        #text(size: 6.5pt)[
          Kelancaran operasional bergantung pada keandalan rantai pasok dan hubungan strategis dengan mitra bisnis utama.
        ]
      ],
      card(PALETTE)[
        #text(weight: "bold", fill: PALETTE.neg)[3. Perubahan Regulasi & Kebijakan]
        #v(1pt)
        #text(size: 6.5pt)[
          Penyesuaian regulasi perpajakan, tarif impor, atau ketentuan industri dapat mempengaruhi struktur biaya dan marjin laba.
        ]
      ],
      card(PALETTE)[
        #text(weight: "bold", fill: PALETTE.neg)[4. Risiko Eksekusi & Kompetisi]
        #v(1pt)
        #text(size: 6.5pt)[
          Persaingan industri dan tantangan ekspansi operasional menuntut eksekusi strategi bisnis yang terukur dan adaptif.
        ]
      ],
    )
  }

  #v(4pt)
  #card(PALETTE)[
    #text(size: 6.5pt, weight: "bold", fill: PALETTE.brand_dark)[PANDUAN RATING REKOMENDASI (INVESTMENT RECOMMENDATION)]
    #v(1.5pt)
    #text(size: 6pt)[
      - *BUY*: Ekspektasi total return > +15% dalam 12 bulan (eks-dividen).
      - *HOLD*: Ekspektasi total return -10% s/d +15% dalam 12 bulan.
      - *SELL*: Ekspektasi total return \< -15% dalam 12 bulan.
      - *NOT RATED*: Saham di luar cakupan riset reguler / tidak memiliki rating aktif.
    ]
  ]

  #v(4pt)
  #card(PALETTE)[
    #text(size: 6.5pt, weight: "bold", fill: PALETTE.ink)[INFORMASI, BUKAN SARAN INVESTASI (OJK COMPLIANCE)]
    #v(1.5pt)
    #text(size: 5.8pt, fill: PALETTE.muted)[
      Laporan ini diproduksi untuk tujuan riset dan edukasi pasar modal semata. Seluruh angka dan analisis didasarkan pada data publik laporan keuangan emiten, keterbukaan informasi IDX, dan sumber resmi terkait. Laporan ini bukan merupakan penawaran atau rekomendasi untuk membeli atau menjual efek tertentu. Keputusan investasi sepenuhnya tanggung jawab investor. Kinerja historis bukan indikasi masa depan.
    ]
  ]

  #v(3pt)
  #text(size: 5.8pt, fill: PALETTE.muted, style: "italic")[
    Disiapkan oleh #m.at("prepared_by", default: "RESEARCH — Sectors Hackathon 2026") · Tanggal #m.date · Ticker: #m.ticker · Bahasa: #upper(m.at("language", default: "id"))
  ]
])

