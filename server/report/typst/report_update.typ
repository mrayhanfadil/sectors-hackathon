// =====================================================================
// ARCHETYPE: company-update v2 — BRIDS-grade redesign (AGY audit 2026-09-05)
// A4, deep navy #004b93, full sans + tnum, banner header, zebra tables,
// sidebar 64mm / main 1fr, zero dead space.
// =====================================================================
#import "theme.typ": *
#let m = sys.inputs.at("ticker", default: "BBRI")
#let data = json(sys.inputs.at("data_path", default: "/home/fadil/projects/sectors-hackathon/output/cache/render_bbri/report_data.json"))
#let meta = data.at("meta", default: (:))
#let INK = rgb("#101828")
#let MUT = rgb("#475467")
#let NAVY = rgb("#004b93")
#let NAVY_D = rgb("#003a75")
#let TINT = rgb("#eef4fb")
#let ZEBRA = rgb("#f1f4f8")
#let LINEG = rgb("#e5e9f0")
#let SANS = "Liberation Sans"
#let PAL2 = (brand: NAVY, brand_dark: NAVY_D, accent: TINT, ink: INK, muted: MUT, line: LINEG, band: ZEBRA, paper: white, pos: rgb("#067647"), neg: rgb("#b42318"))

#let banner() = {
  set text(font: SANS)
  grid(columns: (1fr, auto), gutter: 6pt,
    [#text(size: 12pt, weight: "bold", fill: NAVY)[Equity Research – Company Update]
     #text(size: 8pt, fill: MUT)[#meta.at("date", default: "")]],
    align(right)[#text(size: 11pt, weight: "black", fill: NAVY)[SECTORS] #text(size: 8pt, fill: MUT)[Research]],
  )
  v(2pt)
  line(length: 100%, stroke: 1.5pt + NAVY)
  v(4pt)
}
#let foot(ticker, pg) = {
  set text(font: SANS)
  grid(columns: (1fr, auto), gutter: 6pt,
    text(size: 6pt, fill: MUT)[SECTORS Research · #meta.at("date", default: "") · #ticker — informasi, bukan saran investasi],
    text(size: 6pt, fill: MUT)[#str(pg)],
  )
  line(length: 100%, stroke: 0.5pt + LINEG)
  text(size: 5.5pt, fill: MUT)[Bukan rekomendasi jual/beli (kepatuhan OJK). Lihat pengungkapan penting di akhir laporan.]
}
#let wrap(ticker, pg, body) = {
  set page(paper: "a4", margin: (top: 8mm, bottom: 8mm, x: 10mm), footer: foot(ticker, pg), numbering: none)
  set text(font: SANS, size: 8pt, fill: INK)
  banner()
  body
}
#let h-main(t) = text(size: 10.5pt, weight: "bold", fill: NAVY_D)[#t]
#let h-sec(t) = text(size: 9pt, weight: "bold", fill: NAVY)[#t]
#let src(t) = text(size: 6pt, style: "italic", fill: rgb("#667085"))[Sumber: #t]
// compact zebra key-value table (sidebar market snapshot)
#let zebra(rows) = {
  set text(font: SANS, size: 6.8pt)
  table(columns: (1.25fr, 1fr), stroke: none, inset: (x: 3pt, y: 2.2pt),
    fill: (col, row) => if calc.odd(row) { ZEBRA },
    ..rows.map(r => (align(left)[#text(fill: rgb("#344054"))[#r.at(0)]], align(right)[#text(weight: "bold")[#r.at(1)]])).flatten())
}
#let TICK = if type(meta.at("ticker", default: m)) == str { meta.at("ticker", default: m) } else { m }
#let cover = data.at("cover", default: (:))
#let rb = cover.at("rating_box", default: (:))
#let sh = cover.at("shares", default: (:))
#let mkt = cover.at("market", default: (:))
#let chart-dir = "/home/fadil/projects/sectors-hackathon/output/cache/render_" + lower(TICK) + "/charts"
#let has-chart(n) = data.at("charts", default: (:)).at(n, default: false)

// ============ P1 — sidebar + thesis + key financials ============
#wrap(TICK, 1, [
  #grid(columns: (64mm, 1fr), gutter: 14pt, [
    #text(size: 22pt, weight: "black", fill: NAVY)[#str(rb.at("action", default: "-"))]
    #v(2pt)
    #zebra((
      ("Last Price (Rp)", str(rb.at("price", default: "-"))),
      ("Target Price (Rp)", str(rb.at("tp", default: "-"))),
      ("Previous TP (Rp)", { let p = rb.at("prev_tp", default: none); if p == none { "n/a" } else { str(p) } }),
      ("Upside/Downside", { let u = rb.at("upside_pct", default: none); if u != none { (if u > 0 { "+" } else { "" }) + str(u).replace(".", ",") + "%" } else { "-" } }),
      ("No. of Shares", str(sh.at("outstanding", default: "-")) + " " + sh.at("unit", default: "")),
      ("Mkt Cap", mkt.at("market_cap", default: "-")),
      ("Avg Daily T/O", mkt.at("avg_value_3m", default: "-")),
      ("Free Float (%)", { let f = sh.at("free_float_pct", default: none); if f != none { str(f) } else { "-" } }),
      ..cover.at("shareholders", default: ()).map(s => (if type(s) == array { "MS: " + str(s.at(0)) } else { "MS: " + s.at("name", default: "-") }, if type(s) == array { str(s.at(1)) } else { str(s.at("pct", default: "-")) + "%" })),
    ))
    #v(4pt)
    #if has-chart("vs_jci") [
      #text(size: 7.5pt, weight: "bold", fill: NAVY)[#cover.at("price_chart", default: (:)).at("title", default: "Price Performance")]
      #v(1pt)
      #image(chart-dir + "/vs_jci.png", width: 100%)
      #src(cover.at("price_chart", default: (:)).at("caption", default: "yfinance monthly closes"))
      #v(3pt)
    ]
    #text(size: 7pt, weight: "bold", fill: NAVY)[Analyst]
    #text(size: 7pt)[#meta.at("prepared_by", default: "Research")]
  ], [
    #text(size: 16pt, weight: "bold", fill: NAVY_D)[#meta.at("company_name", default: TICK) (#TICK IJ)]
    #v(1pt)
    #text(size: 8pt, fill: NAVY)[#meta.at("sector", default: "")]
    #v(1pt)
    #text(size: 11pt, weight: "bold")[#cover.at("headline", default: "")]
    #v(3pt)
    #block(fill: TINT, inset: 6pt, radius: 2pt, width: 100%)[
      #text(size: 8pt, weight: "bold", fill: NAVY_D)[Executive Summary]
      #v(1pt)
      #for t in data.at("thesis", default: ()) [
        #text(size: 7.5pt)[• *#t.at("headline", default: "")* — #t.at("detail", default: "")]
        #v(1pt)
      ]
    ]
    #v(3pt)
    #for p in data.at("analysis", default: ()) [
      #text(size: 7.5pt)[#p]
      #v(2pt)
    ]
    #v(1pt)
    #let fh = data.at("financial_highlights", default: (:))
    #h-sec("Key Financials")
    #v(2pt)
    #fin-table(("Year to 31 Dec", ..fh.at("years", default: ())), fh.at("rows", default: (("—",))).map(r => r.map(c => str(c))), palette: PAL2, font: SANS)
    #v(1pt)
    #src(fh.at("source", default: "-"))
  ])
])

#pagebreak()
// ============ P2 — quarterly exhibit full-width ============
#wrap(TICK, 2, [
  #let earn = data.at("earnings", default: (:))
  #h-main(earn.at("title", default: "Quarterly Results"))
  #v(2pt)
  #text(size: 7.5pt)[#earn.at("narrative", default: "")]
  #v(3pt)
  #let et = earn.at("table", default: (:))
  #h-sec("Exhibit 1 — " + et.at("title", default: "Results"))
  #v(2pt)
  #fin-table(et.at("headers", default: ("—",)), et.at("rows", default: (("—",))).map(r => r.map(c => str(c))), palette: PAL2, font: SANS)
  #v(1pt)
  #src(et.at("source", default: "-"))
  #v(4pt)
  #let kr = data.at("key_ratios", default: (:))
  #h-sec(kr.at("title", default: "Key Ratios"))
  #v(2pt)
  #fin-table(kr.at("headers", default: ("—",)), kr.at("rows", default: (("—",))).map(r => r.map(c => str(c))), palette: PAL2, font: SANS)
  #v(1pt)
  #src(kr.at("source", default: "-"))
  #v(4pt)
  #if has-chart("pbv_bands") [
    #h-sec("Exhibit 2 — P/BV Band (4Y)")
    #v(2pt)
    #image(chart-dir + "/pbv_bands.png", width: 100%)
    #v(1pt)
    #text(size: 7.5pt)[#data.at("pbv_caption", default: "")]
    #v(1pt)
    #src("yfinance monthly closes / BVPS year-end")
  ]
])

#pagebreak()
// ============ P3 — valuation + outlook + risks + rating guide ============
#wrap(TICK, 3, [
  #let val = data.at("valuation", default: (:))
  #h-main("Valuation — " + val.at("heading", default: "Relative Valuation"))
  #v(2pt)
  #text(size: 7.5pt)[#val.at("narrative", default: "")]
  #v(3pt)
  #for mt in val.at("methods", default: ()) [
    #h-sec(mt.at("title", default: mt.at("method", default: "Metode")))
    #v(2pt)
    #let tb = mt.at("table", default: (:))
    #fin-table(tb.at("headers", default: ("Parameter", "Nilai", "Keterangan")), tb.at("rows", default: (("—", "—", "—"),)).map(r => r.map(c => str(c))), palette: PAL2, font: SANS)
    #v(1pt)
    #src(mt.at("source", default: "-"))
    #v(3pt)
  ]
  #block(fill: TINT, inset: 6pt, radius: 2pt, width: 100%)[
    #text(size: 8pt, weight: "bold", fill: NAVY_D)[Kesimpulan Valuasi]
    #v(1pt)
    #text(size: 7.5pt)[#val.at("conclusion", default: "")]
  ]
  #v(4pt)
  #h-main("Outlook & Risks")
  #v(2pt)
  #for p in data.at("outlook", default: ()) [#text(size: 7.5pt)[• #p] #v(1pt)]
  #v(2pt)
  #grid(columns: (1fr, 1fr), gutter: 5pt,
    ..data.at("risks", default: ()).map(r => block(fill: ZEBRA, inset: 5pt, radius: 2pt, width: 100%)[
      #text(size: 7.5pt, weight: "bold", fill: PAL2.neg)[#r.at("bucket", default: "-")]
      #v(1pt)
      #text(size: 7pt)[#r.at("detail", default: "")]
      #if r.at("source", default: none) != none [#v(1pt) #text(size: 6pt, style: "italic", fill: rgb("#667085"))[#r.at("source")]]
    ]))
  #v(4pt)
  #h-sec("Investment Rating Definition")
  #v(1pt)
  #fin-table(("Rating", "Kriteria", "Horizon"), (("BUY", "Upside > +15%", "12 bulan"), ("HOLD", "-15% s/d +15%", "12 bulan"), ("SELL", "Downside < -15%", "12 bulan")), palette: PAL2, font: SANS)
  #v(2pt)
  #block(fill: ZEBRA, inset: 5pt, radius: 2pt, width: 100%)[
    #text(size: 7pt, weight: "bold")[Pengungkapan Penting (Compliance)]
    #v(1pt)
    #text(size: 6.5pt)[Laporan ini disusun untuk tujuan edukasi dalam rangka hackathon dan bukan rekomendasi transaksi efek. Penulis dapat memegang posisi pada efek yang dibahas. Metodologi, asumsi, dan sumber data diungkap di dalam laporan; angka forward-looking bersifat estimasi dan dapat bias. Investor wajib melakukan analisis mandiri.]
  ]
])

#pagebreak()
// ============ P4 — financial statements + market history ============
#wrap(TICK, 4, [
  #let st = data.at("statements", default: none)
  #if st != none [
    #h-main("Financial Statements")
    #v(1pt)
    #text(size: 7.5pt, fill: MUT)[Unit: #st.at("unit", default: "-")]
    #v(2pt)
    #h-sec("Income Statement (ringkas)")
    #v(2pt)
    #fin-table(("Pos", ..st.at("years", default: ())), st.at("income", default: (("—",))).map(r => r.map(c => str(c))), palette: PAL2, font: SANS)
    #v(1pt)
    #src(st.at("source", default: "-"))
    #v(4pt)
  ]
  #let mh = data.at("market_hist", default: none)
  #if mh != none [
    #h-sec("Riwayat Pasar & Dividen")
    #v(2pt)
    #fin-table(("Statistik 52M", "Nilai"), (("Tertinggi", mh.at("high52", default: "-")), ("Terendah", mh.at("low52", default: "-"))), palette: PAL2, font: SANS)
    #v(3pt)
    #h-sec("Dividen Terakhir")
    #v(2pt)
    #fin-table(("Ex-date", "DPS (Rp)"), mh.at("divs", default: (("—", "—"),)).map(r => r.map(c => str(c))), palette: PAL2, font: SANS)
    #v(1pt)
    #src(mh.at("source", default: "-"))
  ]
])
