// report_single.typ — Institutional equity research report (single ticker archetype)
#import "../common/theme.typ": *
#import "../common/cover.typ": *


#let ticker = sys.inputs.at("ticker", default: none)
#let data-path = sys.inputs.at("data_path")
#let data = json(data-path)

#let m = data.at("meta")
#show: set-page-defaults.with(date: m.date)
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
      #text(weight: "bold", fill: PALETTE.brand_dark)[Struktur Kepemilikan Saham]
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
      // R2T-R1: canonical Ex 1 (EPS consensus) is skipped per spec — offset the
      // document-global exhibit counter once so Kinerja Harga vs IHSG numbers
      // as Exhibit 2. theme.typ owns the counter; this is a one-time offset.
      #counter(figure.where(kind: "exhibit")).update(1)
      #exhibit-header(pc.at("title", default: "Kinerja Harga vs IHSG (YTD)"), pc_src)
      #v(2pt)
      #let pc_label = pc.at("label", default: if m.ticker == "RATU" {
        "Kinerja Harga " + m.ticker + " (+18,4% YTD) vs IHSG (+12,2% YTD)"
      } else {
        "Kinerja Harga " + m.ticker + (if vj.at("ytd_abs", default: none) != none { " (" + (if vj.ytd_abs > 0 { "+" } else { "" }) + str(vj.ytd_abs) + "% YTD)" } else { "" }) + " vs IHSG"
      })
      #let pc_caption = pc.at("caption", default: if m.ticker == "RATU" {
        "Performa Relatif YTD: Outperform +6,2%"
      } else {
        "Performa Relatif YTD: " + (if vj.at("ytd_rel", default: none) != none { (if vj.ytd_rel > 0 { "Outperform +" } else { "Underperform " }) + str(vj.ytd_rel) + "%" } else { "-" }) 
      })
      #if data.at("charts", default: (:)).at("vs_jci", default: false) {
        image(chart-dir + "/vs_jci.png", width: 100%);
        v(2pt);
        text(size: 6.5pt, fill: PALETTE.muted, style: "italic")[#pc_label];
      } else {
        chart-placeholder(pc_label, caption: pc_caption, height: 75pt, palette: PALETTE);
      }

      #v(8pt)
      #let kf = data.at("key_financials", default: (:))
      #let kf_title = kf.at("title", default: "Key Financials (2024A-2028F)")
      #let kf_src = kf.at("source", default: "Sectors (pending)")
      #let kf_headers = kf.at("headers", default: ("Metrik Finansial", "2024A", "2025A", "2026F", "2027F", "2028F"))
      #let kf_rows = if kf.at("rows", default: ()).len() > 0 {
        kf.rows.map(r => r.map(c => if c == none { "—" } else if type(c) == str { c } else { str(c) }))
      } else {
        (
          ("Revenue", "—", "—", "—", "—", "—"),
          ("EBITDA", "—", "—", "—", "—", "—"),
          ("EBITDA Growth %", "—", "—", "—", "—", "—"),
          ("Net Profit", "—", "—", "—", "—", "—"),
          ("EPS", "—", "—", "—", "—", "—"),
          ("EPS Growth %", "—", "—", "—", "—", "—"),
          ("PER (x)", "—", "—", "—", "—", "—"),
          ("PBV (x)", "—", "—", "—", "—", "—"),
          ("EV/EBITDA (x)", "—", "—", "—", "—", "—"),
        )
      }
      #exhibit-header(kf_title, kf_src)
      #v(2pt)
      #fin-table(
        kf_headers,
        kf_rows,
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
      #text(weight: "bold", fill: PALETTE.brand_dark)[#("Informasi Pasar & Saham " + m.ticker)]
      #card(PALETTE)[
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

#pagebreak(weak: true)

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

  #text(size: T_H3, weight: "bold", fill: PALETTE.brand_dark)[#ex3_title]
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

  #text(size: T_H3, weight: "bold", fill: PALETTE.brand_dark)[#ex4_title]
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

#pagebreak(weak: true)

// =====================================================================
// PAGE 3 — FINANCIAL HIGHLIGHTS & INVESTMENT THESIS
// =====================================================================
#page-wrap(m.at("prepared_by", default: "RESEARCH — Equity Report"), m.date, m.ticker, 3, PALETTE, [
  #section-header(2, "Sorotan Keuangan & Tesis Investasi", PALETTE, sub: "Menjawab: Dari mana pertumbuhan historis berasal dan apa pilar tesis katalis ekspansi ke depan?")

  #let fh = data.at("financial_highlights", default: (:))
  #let fh_years = fh.at("years", default: ("FY24A", "FY25A", "FY26F", "FY27F", "FY28F", "FY29F"))
  #let fh_src = fh.at("source", default: "Laporan Keuangan " + m.ticker + " (IDX), data diolah")
  #let fh_title = "Financial Highlights " + (if fh_years.len() > 0 { str(fh_years.len()) + " Periode (" + fh_years.at(0) + " – " + fh_years.at(-1) + ")" } else { "" })
  // R2T-R2: honest-empty defaults (dashes) to tie out with Slide-1 Key
  // Financials. The hardcoded static numbers (1.290, 610, 402...) contradicted
  // the Slide-1 dashes — CHK-08.
  #let default_fh_rows = (
    ("Pendapatan Bersih", "—", "—", "—", "—", "—", "—"),
    ("EBITDA", "—", "—", "—", "—", "—", "—"),
    ("Laba Bersih", "—", "—", "—", "—", "—", "—"),
    ("EPS (Rp Penuh)", "—", "—", "—", "—", "—", "—"),
    ("P/E (x)", "—", "—", "—", "—", "—", "—"),
    ("ROE (%)", "—", "—", "—", "—", "—", "—"),
    ("Free Cash Flow", "—", "—", "—", "—", "—", "—"),
  )
  #let fh_rows = if fh.at("rows", default: ()).len() > 0 {
    fh.rows.map(r => r.map(c => if c == none { "-" } else if type(c) == str { c } else { str(c) }))
  } else {
    default_fh_rows
  }

  #text(size: T_H3, weight: "bold", fill: PALETTE.brand_dark)[#fh_title]
  #v(2pt)
  #fin-table(
    ("Metrik Finansial", ..fh_years),
    fh_rows,
    palette: PALETTE,
  )

  #if data.at("charts", default: (:)).at("margin_trajectory", default: false) {
    v(4pt);
    text(size: 9.5pt, weight: "bold", fill: PALETTE.brand_dark)[Lintasan Pendapatan & Marjin];
    v(2pt);
    image(chart-dir + "/margin_trajectory.png", width: 100%);
  }

  // Slide-3 2x2 grid (canonical Ex4-7): three financial combos + the mining
  // volume/cost chart. R2T-R3: the exhibit header sits OUTSIDE the chart-flag
  // guard and a muted placeholder renders when the PNG flag is false, so the
  // header always fires and canonical numbering never shifts between keyless
  // and keyed renders. Titles/sources stay payload-driven.
  #v(4pt)
  #grid(
    columns: (1fr, 1fr),
    column-gutter: 8pt,
    row-gutter: 5pt,
    [#let rc = data.at("revenue_combo", default: (:))
     #let rc_title = rc.at("title", default: "Revenue & Revenue Growth (2024A-2028F)")
     #exhibit-header(rc_title, rc.at("source", default: fh_src))
     #v(2pt)
     #if data.at("charts", default: (:)).at("revenue_combo", default: false) {
       image(chart-dir + "/revenue_combo.png", width: 100%);
     } else {
       chart-placeholder(rc_title, height: 44pt, palette: PALETTE);
     }],
    [#let ec = data.at("ebitda_combo", default: (:))
     #let ec_title = ec.at("title", default: "EBITDA & EBITDA Margin (2024A-2028F)")
     #exhibit-header(ec_title, ec.at("source", default: fh_src))
     #v(2pt)
     #if data.at("charts", default: (:)).at("ebitda_combo", default: false) {
       image(chart-dir + "/ebitda_combo.png", width: 100%);
     } else {
       chart-placeholder(ec_title, height: 44pt, palette: PALETTE);
     }],
    [#let nc = data.at("netprofit_combo", default: (:))
     #let nc_title = nc.at("title", default: "Net Profit & EPS Growth (2024A-2028F)")
     #exhibit-header(nc_title, nc.at("source", default: fh_src))
     #v(2pt)
     #if data.at("charts", default: (:)).at("netprofit_combo", default: false) {
       image(chart-dir + "/netprofit_combo.png", width: 100%);
     } else {
       chart-placeholder(nc_title, height: 44pt, palette: PALETTE);
     }],
    [#let pcc = data.at("production_cost", default: (:))
     #let pcc_title = pcc.at("title", default: "Volume Produksi & Biaya Kas (C1/AISC)")
     #exhibit-header(pcc_title, pcc.at("source", default: fh_src))
     #v(2pt)
     #if data.at("charts", default: (:)).at("production_cost", default: false) {
       image(chart-dir + "/production_cost.png", width: 100%);
     } else {
       chart-placeholder(pcc_title, height: 44pt, palette: PALETTE);
     }],
  )

  #v(4pt)
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

#pagebreak(weak: true)

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
      #exhibit-header("Proyeksi Arus Kas Bebas (FCFF)", if dcf_m != none { dcf_m.at("source", default: "Engine DCF") } else { "Engine DCF" })
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
  #let rnav = val.at("rnav", default: (:))
  #exhibit-header(rnav.at("title", default: "RNAV Bridge — Attributable NAV ke Target Price"), rnav.at("source", default: "Engine RNAV (Sectors pending)"))
  #v(2pt)
  #fin-table(
    rnav.at("headers", default: ("Aset / Komponen", "Kepemilikan %", "NAV Atrib. (Rp bn)", "Keterangan")),
    if rnav.at("rows", default: ()).len() > 0 {
      rnav.rows.map(r => r.map(c => if c == none { "—" } else { str(c) }))
    } else {
      (
        ("Aset produksi (100% basis)", "—", "—", "Project DCF / appraisal"),
        ("Aset pengembangan (100% basis)", "—", "—", "Higher discount rate vs produksi"),
        ("Eksplorasi / tenemen lain", "—", "—", "Option / appraisal value"),
        ("Smelter / hilirisasi interest", "—", "—", "Attributable project NAV"),
        ("(+) Kas & setara kas", "—", "—", "Valuation-date balance"),
        ("(-) Total utang berbunga", "—", "—", "Valuation-date balance"),
        ("(-) PV overhead korporat", "—", "—", "Unallocated G&A at WACC"),
      )
    },
    footers: rnav.at("footers", default: (
      ("Total RNAV", "—", "—", "Bold total"),
      ("RNAV per saham", "—", "—", "Total RNAV / shares"),
      ("Diskon ke RNAV", "—", "—", "Peer comps or pure judgment"),
      ("Target Price (RNAV)", "—", "—", "RNAV/share x (1 - discount)"),
    )),
    palette: PALETTE,
  )

  #v(6pt)
  // R2T-R5: the Mid-Cycle EV/EBITDA cross-check lived here and spilled Page 4
  // onto a second physical page — relocated to the Slide-4 DCF deep-dive page
  // (before Cost of Capital Build) so Page 4 fits its paper.
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
  #text(size: 9.5pt, weight: "bold", fill: PALETTE.brand_dark)[Pita Valuasi Historis P/BV 3-Tahun (STD±2)]
  #v(2pt)
  #if bands != none and bands.at("rows", default: ()).len() > 0 {
    fin-table(
      ("Deviasi Standar", "P/BV (x)", "Implied Price", "Interpretasi Valuasi"),
      bands_rows,
      palette: PALETTE,
    );
  } else {
    text(size: 7.2pt, fill: PALETTE.muted)[Pita historis tidak disajikan — riwayat book value tidak komparabel. Lihat tabel di atas.];
  }

  #v(6pt)
  #let conclusion_text = val.at("conclusion", default: if cover.tp == none { "Valuasi menunggu data Sectors — target harga dan kesimpulan belum tersedia untuk " + m.ticker + "." } else { "Harga saham kini Rp " + nstr(cover.price) + " mencerminkan target harga Rp " + nstr(cover.tp) + " dengan potensi imbal hasil " + (if cover.upside_pct != none and cover.upside_pct > 0 { "+" } else { "" }) + nstr(cover.upside_pct) + "% (" + nstr(cover.action) + "), didukung oleh analisis fundamental komprehensif pada sektor " + m.sector + "." })
  #card(PALETTE)[
    #text(weight: "bold", fill: PALETTE.ink)[Kesimpulan Valuasi]
    #v(2pt)
    #text(size: 7.3pt)[#conclusion_text]
  ]
])

#pagebreak(weak: true)

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

  // R2T-R5 (relocated from Page 4): EV/EBITDA Mid-Cycle cross-check stays in
  // the Slide-4 family and fires before Cost of Capital Build, so canonical
  // header order is preserved. Payload-driven, honest-empty defaults.
  #let mcev = data.at("valuation", default: (:)).at("midcycle", default: (:))
  #exhibit-header(mcev.at("title", default: "EV/EBITDA Mid-Cycle Cross-Check (3Y Average)"), mcev.at("source", default: "Engine Multiple (Sectors pending)"))
  #v(2pt)
  #fin-table(
    mcev.at("headers", default: ("Komponen Mid-Cycle", "Nilai", "Keterangan")),
    if mcev.at("rows", default: ()).len() > 0 {
      mcev.rows.map(r => r.map(c => if c == none { "—" } else { str(c) }))
    } else {
      (
        ("EBITDA tahun-1 (constituent)", "—", "3Y constituent year 1"),
        ("EBITDA tahun-2 (constituent)", "—", "3Y constituent year 2"),
        ("EBITDA tahun-3 (constituent)", "—", "3Y constituent year 3"),
        ("Rata-rata EBITDA 3Y (mid-cycle)", "—", "Average of 3 constituents"),
        ("Target EV/EBITDA", "—", "Min 2 peer prints or assumption + sensitivity leg"),
        ("Implied EV", "—", "Mid-cycle EBITDA x multiple"),
        ("(-) Net Debt (same valuation date)", "—", "Same figure as DCF bridge"),
        ("Implied equity", "—", "Implied EV - Net Debt"),
        ("Implied per saham (cross-check)", "—", "Own upside, NOT headline TP"),
      )
    },
    palette: PALETTE,
  )

  #v(6pt)
  #exhibit-header("Cost of Capital Build", "Model CAPM & SBN 10Y")
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
  #exhibit-header(ddd.at("sensitivity", default: (:)).at("title", default: "Sensitivity Analysis — WACC vs Terminal Growth (g)"), "Engine Sensitivitas 5x5")
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
      #text(size: 9.5pt, weight: "bold", fill: PALETTE.brand_dark)[Scenario Analysis (Bear / Base / Bull)]
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
      #text(size: 9.5pt, weight: "bold", fill: PALETTE.brand_dark)[Jembatan Nilai EV ke Ekuitas]
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

#pagebreak(weak: true)

// =====================================================================
// PAGE 6 — PEERS & HISTORICAL VALUATION (SLIDE 5)
// =====================================================================
#page-wrap(m.at("prepared_by", default: "RESEARCH — Equity Report"), m.date, m.ticker, 6, PALETTE, [
  #section-header(5, "Peer Comparison & Historical Valuation", PALETTE, sub: "Menjawab: Bagaimana posisi valuasi relatif terhadap kompetitor sejenis dan terhadap sejarah multiple emiten sendiri?")

  #let peer_data = data.at("peers", default: (:))
  #let peer_tables = peer_data.at("tables", default: ())
  #let peer_tab = if peer_tables.len() > 0 { peer_tables.at(0) } else { (:) }
  #let default_peer_headers = ("Ticker", "Market Cap", "P/E (x)", "EV/EBITDA", "P/BV (x)", "ROE (%)", "Gearing")
  // LOUD policy: legacy peer multiples were baked demo comparables. Peer rows
  // come from Sectors peers only; absent -> dashes. Median/Average are bold
  // summary rows over peer rows only (subject row excluded by the modeler);
  // absent -> dashes, never fabricated.
  #let default_peer_rows = ((m.ticker, "-", "-", "-", "-", "-", "-"),)
  #let peer_title = if peer_tab.at("pillar", default: none) != none { "Peer Comparison — " + peer_tab.pillar } else { "Peer Comparison — Emiten Sektor " + m.sector }
  #let peer_src = peer_tab.at("source", default: "Sectors (pending)")
  #let peer_headers = peer_tab.at("headers", default: default_peer_headers)
  #let peer_rows = if peer_tab.at("rows", default: ()).len() > 0 {
    peer_tab.rows.map(r => r.map(c => if type(c) == str or type(c) == content { c } else { str(c) }))
  } else {
    default_peer_rows
  }
  #let peer_median = peer_tab.at("median", default: ("Median", "-", "-", "-", "-", "-", "-")).map(c => if type(c) == str or type(c) == content { c } else { str(c) })
  #let peer_average = peer_tab.at("average", default: ("Average", "-", "-", "-", "-", "-", "-")).map(c => if type(c) == str or type(c) == content { c } else { str(c) })
  #let peer_all = (..peer_rows, peer_median, peer_average)

  #exhibit-header(peer_title, peer_src)
  #v(2pt)
  #fin-table(
    peer_headers,
    peer_all,
    bold-rows: (peer_rows.len(), peer_rows.len() + 1),
    palette: PALETTE,
  )

  #v(6pt)
  #text(size: 9.5pt, weight: "bold", fill: PALETTE.brand_dark)[Historical Relative Valuation — Own-History Tool (Time-Series)]
  #v(2pt)
  // R2T-R3: band exhibit headers sit OUTSIDE the chart-flag guards with a
  // muted placeholder fallback, so Ex12-13 always fire and numbering never
  // shifts between keyless and keyed renders.
  #let peb = data.at("pe_hist_band", default: (:))
  #let peb_title = peb.at("title", default: m.ticker + " — P/E Trailing Band vs 1-Year History (mean, median and current level)")
  #exhibit-header(peb_title, peb.at("source", default: peer_src))
  #v(2pt)
  #if data.at("charts", default: (:)).at("pe_hist_band", default: false) {
    image(chart-dir + "/pe_hist_band.png", width: 100%);
  } else {
    chart-placeholder(peb_title, height: 75pt, palette: PALETTE);
  }
  #let pbb = data.at("pbv_hist_band", default: (:))
  #let pbb_title = pbb.at("title", default: m.ticker + " — P/BV Trailing Band vs 1-Year History (mean, median and current level)")
  #exhibit-header(pbb_title, pbb.at("source", default: peer_src))
  #v(2pt)
  #if data.at("charts", default: (:)).at("pbv_hist_band", default: false) {
    image(chart-dir + "/pbv_hist_band.png", width: 100%);
  } else {
    chart-placeholder(pbb_title, height: 75pt, palette: PALETTE);
  }
  #v(4pt)
  #text(size: 6.5pt, fill: PALETTE.muted, style: "italic")[Implied prices from this own-history tool are mean-reversion cross-checks that hold fundamental drivers constant at their current TTM/forward level and revert only the multiple to its 1-year historical mean/median. They are a snapshot, not a forecast, and are NOT the official Target Price established in Slide 4 (DCF-shortened / RNAV).]

  // R2T-R4: non-canonical extras — demoted to un-numbered plain titles (same
  // pattern as the demoted Slide-4 tables). They consume no exhibit numbers,
  // so the canonical sequence caps at 17.
  #v(4pt)
  #let relval_title = "Perbandingan Valuasi Relatif (P/E & EV/EBITDA Peers)"
  #let relval_src = "Sectors (pending)"
  #if data.at("charts", default: (:)).at("relval_bars", default: false) {
    text(size: 9.5pt, weight: "bold", fill: PALETTE.brand_dark)[#relval_title];
    v(2pt);
    image(chart-dir + "/relval_bars.png", width: 100%);
    v(2pt);
    text(size: 6.5pt, fill: PALETTE.muted, style: "italic")[Grafik Batang Komparasi Multiple Valuasi Relatif];
  }
  #if data.at("charts", default: (:)).at("peer_evebitda", default: false) {
    v(4pt);
    text(size: 9.5pt, weight: "bold", fill: PALETTE.brand_dark)[EV/EBITDA Peers vs Subjek];
    v(2pt);
    image(chart-dir + "/peer_evebitda.png", width: 88%);
  }
  #if data.at("charts", default: (:)).at("peer_evebitda", default: false) {
    v(2pt);
    text(size: 6.5pt, fill: PALETTE.muted, style: "italic")[Grafik P/E tidak disajikan — P/E trailing tak bermakna di trough siklikal (TPIA 139x, peers terdistorsi).];
  }
])

#pagebreak(weak: true)

// =====================================================================
// PAGE 7 — FINANCIAL STATEMENTS 5Y (SLIDE 6: IS+BS / SLIDE 7: CF+RATIOS)
// =====================================================================
#page-wrap(m.at("prepared_by", default: "RESEARCH — Equity Report"), m.date, m.ticker, 7, PALETTE, [
  #let fs = data.at("financial_statements", default: (:))
  #section-header(6, fs.at("section_title", default: "Laporan Keuangan & Rasio Finansial 5 Tahun (2024A-2028F)"), PALETTE, sub: fs.at("section_sub", default: "Menjawab: Bagaimana proyeksi menyeluruh laba rugi, neraca keuangan, likuiditas, dan profitabilitas 5 tahun?"))

  #let inc = fs.at("income", default: (:))
  #exhibit-header(inc.at("title", default: "Laporan Laba Rugi Komprehensif (2024A-2028F)"), inc.at("source", default: "Laporan Keuangan IDX & Proyeksi"))
  #v(2pt)
  #let inc_headers = inc.at("headers", default: ("Akun Laba Rugi", "2024A", "2025A", "2026F", "2027F", "2028F"))
  #let inc_rows = if inc.at("rows", default: ()).len() > 0 {
    inc.rows.map(r => r.map(c => if c == none { "—" } else { str(c) }))
  } else {
    (
      ("Revenue/Sales", "—", "—", "—", "—", "—"),
      ("Cost of Goods Sold (COGS)", "—", "—", "—", "—", "—"),
      ("Gross Profit", "—", "—", "—", "—", "—"),
      ("SG&A / Operating Expenses", "—", "—", "—", "—", "—"),
      ("EBIT", "—", "—", "—", "—", "—"),
      ("Interest Income", "—", "—", "—", "—", "—"),
      ("Interest Expense", "—", "—", "—", "—", "—"),
      ("Other Non-Operating Income / (Expense)", "—", "—", "—", "—", "—"),
      ("Pre-tax Profit", "—", "—", "—", "—", "—"),
      ("Income Tax", "—", "—", "—", "—", "—"),
      ("Minority Interest", "—", "—", "—", "—", "—"),
      ("Net Profit", "—", "—", "—", "—", "—"),
    )
  }
  #fin-table(
    inc_headers,
    inc_rows,
    bold-rows: (2, 4, 8, 11),
    palette: PALETTE,
  )

  #v(6pt)
  #let bal = fs.at("balance", default: (:))
  #exhibit-header(bal.at("title", default: "Neraca Keuangan Ringkas (2024A-2028F)"), bal.at("source", default: "Laporan Keuangan IDX & Proyeksi"))
  #v(2pt)
  #let bal_headers = bal.at("headers", default: ("Pos Neraca", "2024A", "2025A", "2026F", "2027F", "2028F"))
  #let bal_rows = if bal.at("rows", default: ()).len() > 0 {
    bal.rows.map(r => r.map(c => if c == none { "—" } else { str(c) }))
  } else {
    (
      ("Cash & Equivalents", "—", "—", "—", "—", "—"),
      ("Trade Receivables", "—", "—", "—", "—", "—"),
      ("Inventory", "—", "—", "—", "—", "—"),
      ("Other Current Assets", "—", "—", "—", "—", "—"),
      ("Total Current Assets", "—", "—", "—", "—", "—"),
      ("Net Fixed Assets", "—", "—", "—", "—", "—"),
      ("Other Non-Current Assets", "—", "—", "—", "—", "—"),
      ("Total Assets", "—", "—", "—", "—", "—"),
      ("Short-term Debt", "—", "—", "—", "—", "—"),
      ("Trade Payables", "—", "—", "—", "—", "—"),
      ("Other Current Liabilities", "—", "—", "—", "—", "—"),
      ("Total Current Liabilities", "—", "—", "—", "—", "—"),
      ("Long-term Debt", "—", "—", "—", "—", "—"),
      ("Other Non-Current Liabilities", "—", "—", "—", "—", "—"),
      ("Total Liabilities", "—", "—", "—", "—", "—"),
      ("Shareholders' Equity", "—", "—", "—", "—", "—"),
      ("Total Liabilities & Equity", "—", "—", "—", "—", "—"),
    )
  }
  #fin-table(
    bal_headers,
    bal_rows,
    bold-rows: (4, 7, 11, 14, 16),
    palette: PALETTE,
  )

  #pagebreak(weak: true)

  #v(6pt)
  #let cf = fs.at("cashflow", default: (:))
  #exhibit-header(cf.at("title", default: "Laporan Arus Kas (2024A-2028F)"), cf.at("source", default: "Laporan Keuangan IDX & Proyeksi"))
  #v(2pt)
  // House Slide-7 row order: Operating -> Investing -> Financing -> closing
  // balances. Section labels and subtotals are bolded IN PLACE via
  // fin-table(bold-rows:), so the sub-total hierarchy is legible without colour,
  // and the three closing balances close the table through `footers`. Rows are
  // payload-driven; the default below is honest-empty (dashes), never fabricated.
  #let cf_headers = cf.at("headers", default: ("Arus Kas", "2024A", "2025A", "2026F", "2027F", "2028F"))
  #let cf_has_data = cf.at("rows", default: ()).len() > 0
  #let cf_rows = if cf_has_data {
    cf.rows.map(r => r.map(c => if c == none { "—" } else { str(c) }))
  } else {
    (
      ("ARUS KAS DARI OPERASI", "", "", "", "", ""),
      ("Laba Bersih Tahun Berjalan", "—", "—", "—", "—", "—"),
      ("(+) Depresiasi & Amortisasi", "—", "—", "—", "—", "—"),
      ("(-)/(+) Perubahan Modal Kerja", "—", "—", "—", "—", "—"),
      ("Pos Operasional Lainnya", "—", "—", "—", "—", "—"),
      ("Arus Kas Bersih dari Operasi", "—", "—", "—", "—", "—"),
      ("ARUS KAS DARI INVESTASI", "", "", "", "", ""),
      ("(-) Belanja Modal (Capex)", "—", "—", "—", "—", "—"),
      ("Pos Investasi Lainnya", "—", "—", "—", "—", "—"),
      ("Arus Kas Bersih dari Investasi", "—", "—", "—", "—", "—"),
      ("ARUS KAS DARI PENDANAAN", "", "", "", "", ""),
      ("Utang Ditarik / (Dibayar)", "—", "—", "—", "—", "—"),
      ("Dividen Dibayarkan", "—", "—", "—", "—", "—"),
      ("Ekuitas Diterbitkan / (Buyback)", "—", "—", "—", "—", "—"),
      ("Arus Kas Bersih dari Pendanaan", "—", "—", "—", "—", "—"),
    )
  }
  #let cf_bold = if cf_has_data {
    cf.at("bold_rows", default: ())
  } else {
    (0, 5, 6, 9, 10, 14)
  }
  #let cf_footers = cf.at("footers", default: (
    ("Perubahan Kas Bersih", "—", "—", "—", "—", "—"),
    ("Saldo Kas Awal", "—", "—", "—", "—", "—"),
    ("Saldo Kas Akhir (tie-out ke Neraca)", "—", "—", "—", "—", "—"),
  ))
  #fin-table(
    cf_headers,
    cf_rows,
    footers: cf_footers,
    bold-rows: cf_bold,
    palette: PALETTE,
  )

  #v(6pt)
  #let rat = fs.at("ratios", default: (:))
  #exhibit-header(rat.at("title", default: "Rasio Keuangan & Efisiensi (2024A-2028F)"), rat.at("source", default: "Perhitungan Analis & IDX"))
  #v(2pt)
  #let rat_headers = rat.at("headers", default: ("Rasio Kunci", "2024A", "2025A", "2026F", "2027F", "2028F"))
  #let rat_rows = if rat.at("rows", default: ()).len() > 0 {
    rat.rows.map(r => r.map(c => if c == none { "—" } else { str(c) }))
  } else {
    (
      ("GROWTH (% yoy)", "", "", "", "", ""),
      ("Sales Growth", "—", "—", "—", "—", "—"),
      ("EBITDA Growth", "—", "—", "—", "—", "—"),
      ("Operating Profit (EBIT) Growth", "—", "—", "—", "—", "—"),
      ("Net Profit Growth", "—", "—", "—", "—", "—"),
      ("PROFITABILITY (%)", "", "", "", "", ""),
      ("Gross Margin", "—", "—", "—", "—", "—"),
      ("EBITDA Margin", "—", "—", "—", "—", "—"),
      ("Operating Margin", "—", "—", "—", "—", "—"),
      ("Net Margin", "—", "—", "—", "—", "—"),
      ("Return on Average Assets (ROAA)", "—", "—", "—", "—", "—"),
      ("Return on Average Equity (ROAE)", "—", "—", "—", "—", "—"),
      ("LEVERAGE & COVERAGE (x)", "", "", "", "", ""),
      ("Net Gearing", "—", "—", "—", "—", "—"),
      ("Interest Coverage", "—", "—", "—", "—", "—"),
    )
  }
  #fin-table(
    rat_headers,
    rat_rows,
    bold-rows: (0, 5, 12),
    palette: PALETTE,
  )
])

#pagebreak(weak: true)
// PAGE 8 — investment risks, rating guide and the regulatory disclosure the
// footer points at. Split from page 7 so neither page overflows its paper.
#page-wrap(m.at("prepared_by", default: "RESEARCH — Equity Report"), m.date, m.ticker, 8, PALETTE, [
  #section-header(7, "Investment Risks & Disclosure", PALETTE, sub: "Menjawab: Apa risiko investasi utama, dan bagaimana pemeringkatan rekomendasi kami?")
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

