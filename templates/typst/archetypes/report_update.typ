// =====================================================================
// ARCHETYPE: company-update — BRIDS-style Company Update (sidebar + main)
// A4, navy palette, Calibri-metric (Liberation Sans), footer + page numbers
// =====================================================================
#import "../common/theme.typ": *
#let m = sys.inputs.at("ticker", default: "BBRI")
#let data = json(sys.inputs.at("data_path", default: "/home/fadil/projects/sectors-hackathon/output/cache/render_bbri/report_data.json"))
#let meta = data.at("meta", default: (:))
#let PALETTE = (
  brand: rgb("#0842c2"),
  brand_dark: rgb("#00529c"),
  accent: rgb("#e8f1fc"),
  ink: rgb("#101828"),
  muted: rgb("#475467"),
  line: rgb("#e4e7ec"),
  band: rgb("#f2f5fa"),
  paper: rgb("#ffffff"),
  pos: rgb("#067647"),
  neg: rgb("#b42318"),
)
#let NAVY = rgb("#0842c2")
#let NAVY_D = rgb("#00529c")
#let NAVY_L = rgb("#3080e3")
#let PALE = rgb("#70c4e8")
#let PAPER2 = rgb("#f2f5fa")

#let upd-foot(prep, date, ticker, pg) = {
  grid(columns: (1fr, auto), gutter: 6pt,
    text(size: 6pt, fill: gray)[#prep · #date · #ticker],
    text(size: 6pt, fill: gray)[#str(pg)],
  )
  line(length: 100%, stroke: 0.5pt + gray)
  text(size: 5.5pt, fill: gray)[Informasi, bukan saran investasi — bukan rekomendasi jual/beli (OJK compliance). Lihat pengungkapan penting di akhir laporan.]
}
#let upd-wrap(prep, date, ticker, pg, body) = {
  set page(paper: "a4", margin: (x: 11mm, y: 9mm), footer: upd-foot(prep, date, ticker, pg), numbering: none)
  body
}
#let h-main(txt) = text(size: 10pt, weight: "bold", fill: NAVY_D)[#txt]
#let h-sec(txt) = text(size: 9pt, weight: "bold", fill: NAVY)[#txt]
#let side-h(txt) = text(size: 7.5pt, weight: "bold", fill: white)[#txt]
#let side-box(title, body) = {
  block(fill: NAVY, inset: 3pt, radius: 2pt, width: 100%)[#side-h(title)]
  block(fill: PAPER2, inset: 3pt, radius: 2pt, width: 100%)[#body]
  v(4pt)
}
#let kv(k, v) = grid(columns: (1fr, auto), gutter: 4pt, text(size: 7pt)[#k], text(size: 7pt, weight: "bold")[#v])

// resolve meta (dict or string-safe)
#let TICK = if type(meta.at("ticker", default: m)) == str { meta.at("ticker", default: m) } else { m }
#let CO = meta.at("company_name", default: TICK)
#let SECTOR = meta.at("sector", default: "")
#let RDATE = meta.at("date", default: "")
#let PREP = meta.at("prepared_by", default: "RESEARCH")
#let cover = data.at("cover", default: (:))
#let rb = cover.at("rating_box", default: (:))
#let RACT = str(rb.at("action", default: "-"))
#let RTP = rb.at("tp", default: "-")
#let RPRICE = rb.at("price", default: "-")
#let RUP = rb.at("upside_pct", default: none)
#let sh = cover.at("shares", default: (:))
#let mkt = cover.at("market", default: (:))
#let shlist = cover.at("shareholders", default: ())
#let chart-dir = "/home/fadil/projects/sectors-hackathon/output/cache/render_" + lower(TICK) + "/charts"

// ============ PAGE 1 — header + sidebar + thesis ============
#upd-wrap(PREP, RDATE, TICK, 1, [
  #grid(columns: (1fr, auto), gutter: 6pt,
    text(size: 7.5pt, fill: NAVY)[#RDATE],
    text(size: 7.5pt, weight: "bold", fill: NAVY)[Equity Research – Company Update],
  )
  #v(1pt)
  #text(size: 16pt, weight: "bold", fill: NAVY_D)[#CO]
  #v(1pt)
  #text(size: 10pt, fill: NAVY)[(#TICK IJ) — #SECTOR]
  #v(1pt)
  #text(size: 10.5pt, weight: "bold")[#cover.at("headline", default: "")]
  #v(3pt)
  #grid(columns: (52mm, 1fr), gutter: 6pt, [
    #block(fill: NAVY, inset: 3pt, radius: 2pt, width: 100%)[#text(size: 10pt, weight: "bold", fill: white)[#RACT]]
    #v(1pt)
    #side-box("Harga & Valuasi")[
      #kv("Last Price (Rp)", str(RPRICE))
      #kv("Target Price (Rp)", str(RTP))
      #kv("Upside/Downside", if RUP != none { (if RUP > 0 { "+" } else { "" }) + str(RUP) + "%" } else { "-" })
      #kv("No. of Shares", str(sh.at("outstanding", default: "-")) + " " + sh.at("unit", default: ""))
      #kv("Mkt Cap", mkt.at("market_cap", default: "-"))
      #kv("Avg Daily T/O", mkt.at("avg_value_3m", default: "-"))
      #kv("Free Float", if sh.at("free_float_pct", default: none) != none { str(sh.free_float_pct) + "%" } else { "-" })
    ]
    #if shlist.len() > 0 {
      side-box("Major Shareholders")[#for s in shlist [#kv(if type(s) == array { str(s.at(0)) } else { s.at("name", default: "-") }, if type(s) == array { str(s.at(1)) } else { str(s.at("pct", default: "-")) + "%" })]]
    }
    #if data.at("charts", default: (:)).at("vs_jci", default: false) {
      side-box("Price Performance")[#image(chart-dir + "/vs_jci.png", width: 100%)]
    }
    #side-box("Analyst")[#text(size: 7pt)[#PREP]]
  ], [
    #for t in data.at("thesis", default: ()) [
      #text(size: 7.5pt)[• #t.at("headline", default: "") — #t.at("detail", default: "")]
      #v(1pt)
    ]
    #v(1pt)
    #let fh = data.at("financial_highlights", default: (:))
    #h-sec("Key Financials")
    #v(1pt)
    #fin-table(
      ("Year to 31 Dec", ..fh.at("years", default: ())),
      fh.at("rows", default: (("—",))).map(r => r.map(c => str(c))),
      palette: PALETTE,
    )
    #v(1pt)
    #text(size: 6.5pt, fill: PALETTE.muted, style: "italic")[Sumber: #fh.at("source", default: "-")]
  ])
])

#pagebreak()
// ============ PAGE 2 — earnings section ============
#upd-wrap(PREP, RDATE, TICK, 2, [
  #grid(columns: (1fr, auto), gutter: 6pt,
    text(size: 7.5pt, fill: NAVY)[#RDATE],
    text(size: 7.5pt, weight: "bold", fill: NAVY)[Equity Research – Company Update],
  )
  #v(1pt)
  #let earn = data.at("earnings", default: (:))
  #h-main(earn.at("title", default: "Quarterly Results"))
  #v(1pt)
  #text(size: 7.5pt)[#earn.at("narrative", default: "")]
  #v(1pt)
  #let et = earn.at("table", default: (:))
  #h-sec(et.at("title", default: "Results"))
  #v(1pt)
  #fin-table(
    et.at("headers", default: ("—",)),
    et.at("rows", default: (("—",))).map(r => r.map(c => str(c))),
    palette: PALETTE,
  )
  #v(1pt)
  #text(size: 6.5pt, fill: PALETTE.muted, style: "italic")[Sumber: #et.at("source", default: "-")]
  #v(3pt)
  #let kr = data.at("key_ratios", default: (:))
  #h-sec(kr.at("title", default: "Key Ratios"))
  #v(1pt)
  #fin-table(
    kr.at("headers", default: ("—",)),
    kr.at("rows", default: (("—",))).map(r => r.map(c => str(c))),
    palette: PALETTE,
  )
  #v(1pt)
  #text(size: 6.5pt, fill: PALETTE.muted, style: "italic")[Sumber: #kr.at("source", default: "-")]
])

#pagebreak()
// ============ PAGE 3 — valuation (DDM) ============
#upd-wrap(PREP, RDATE, TICK, 3, [
  #h-main("Valuation — Dividend Discount Model")
  #v(1pt)
  #let val = data.at("valuation", default: (:))
  #text(size: 7.5pt)[#val.at("narrative", default: "")]
  #v(1pt)
  #for mt in val.at("methods", default: ()) [
    #h-sec(mt.at("title", default: mt.at("method", default: "Metode")))
    #v(1pt)
    #let tb = mt.at("table", default: (:))
    #fin-table(
      tb.at("headers", default: ("Parameter", "Nilai", "Keterangan")),
      tb.at("rows", default: (("—", "—", "—"),)).map(r => r.map(c => str(c))),
      palette: PALETTE,
    )
    #v(1pt)
    #text(size: 6.5pt, fill: PALETTE.muted, style: "italic")[Sumber: #mt.at("source", default: "-")]
    #v(1pt)
  ]
  #card(PALETTE)[
    #text(weight: "bold")[Kesimpulan Valuasi]
    #v(1pt)
    #text(size: 7.5pt)[#val.at("conclusion", default: "")]
  ]
  #v(6pt)
  #h-main("Outlook & Risks")
  #v(1pt)
  #let ol = data.at("outlook", default: "")
  #if type(ol) == str [#text(size: 7.5pt)[#ol]] else [#for p in ol [#text(size: 7.5pt)[• #p]]]
  #v(3pt)
  #h-sec("Investment Risks")
  #v(1pt)
  #let risks_list = data.at("risks", default: ())
  #grid(
    columns: (1fr, 1fr),
    gutter: 5pt,
    ..risks_list.map(r => card(PALETTE)[
      #text(weight: "bold", fill: PALETTE.neg)[#r.at("bucket", default: "-")]
      #v(1pt)
      #text(size: 7pt)[#r.at("detail", default: "")]
    ]),
  )
  #v(3pt)
  #text(size: 7.5pt, weight: "bold", fill: NAVY)[Rating Guide]
  #v(1pt)
  #text(size: 7pt)[BUY: upside > +15% · HOLD: -15% s/d +15% · SELL: downside < -15% · Ulasan tahunan atau saat Noble Events.]
]
)
