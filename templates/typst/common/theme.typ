// =====================================================================
// common/theme.typ — Institutional equity research design tokens
// =====================================================================
// Universal theme applicable to all 4 archetypes (single / sotp / infra / strategy).
// Fonts: Newsreader (serif body), IBM Plex Sans (headings/UI), IBM Plex Mono (numerics)
// Palette: institutional charcoal/slate base + archetype-specific brand color
// =====================================================================

#let FONT_DIR = "../assets/fonts"

// ------ Page geometry ------
#let PAGE_W = 210mm
#let PAGE_H = 297mm
#let MARGIN_LR = 12mm
#let MARGIN_TB = 14mm
#let HEADER_SIZE = 7pt
#let FOOTER_SIZE = 6.5pt
#let BODY_SIZE = 8.5pt
#let BODY_LEADING = 11pt

// ------ Archetype palettes (passed in as theme parameter) ------
#let DEFAULT_PALETTE = (
  brand: rgb("#067647"),       // emerald (default for infra)
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

// ------ Font fallback chains ------
#let FONT_SERIF = ("Newsreader", "Liberation Serif", "DejaVu Serif")
#let FONT_SANS = ("IBM Plex Sans", "Liberation Sans", "DejaVu Sans")
#let FONT_MONO = ("IBM Plex Mono", "Liberation Mono", "DejaVu Sans Mono")

// ------ Typography scale ------
#let T_BODY = 8.5pt
#let T_SMALL = 7pt
#let T_H3 = 10.5pt
#let T_H2 = 14pt
#let T_H1 = 26pt
#let T_COVER_TITLE = 26pt
#let T_TP_BIG = 17pt
#let T_RATING = 20pt

// ------ Set page geometry + fonts ------
#let set-page-defaults(doc) = {
  set page(
    paper: "a4",
    margin: (left: MARGIN_LR, right: MARGIN_LR, top: MARGIN_TB, bottom: MARGIN_TB),
  )
  set text(
    font: FONT_SANS,
    size: T_BODY,
    lang: "id",
    fill: rgb("#101828"),
    features: ("tnum",),
  )
  set par(leading: 0.65em, justify: false)
  set list(indent: 8pt, marker: [•])
  doc
}

// ------ Running header ------
#let running-header(brand-label, date, ticker) = {
  v(-2pt)
  text(size: HEADER_SIZE, weight: "bold", fill: rgb("#475467"), tracking: 0.08em, upper(brand-label))
  h(1fr)
  text(size: HEADER_SIZE, weight: "bold", fill: rgb("#475467"), tracking: 0.08em)[#ticker · #date]
  v(-2pt)
  line(length: 100%, stroke: 1.5pt + rgb("#067647"))
  v(8pt)
}

// ------ Page footer ------
#let page-footer(pg-num, palette) = {
  set text(size: FOOTER_SIZE, fill: rgb("#475467"))
  v(-2pt)
  line(length: 100%, stroke: 0.5pt + rgb("#e4e7ec"))
  v(4pt)
  block(width: 100%)[
    #grid(
      columns: (1fr, auto),
      align: (left, right),
      [Informasi, bukan saran investasi — bukan rekomendasi jual/beli (OJK compliance)],
      [#pg-num],
    )
  ]
}

// ------ Section header ------
#let section-header(no, title, palette) = {
  block(width: 100%)[
    #set text(size: T_H2, weight: "bold", fill: palette.brand_dark)
    #grid(
      columns: (auto, 1fr),
      align: (left, left),
      [
        #set text(size: 7pt, weight: "bold", fill: white)
        #box(
          fill: palette.brand,
          inset: (x: 5pt, y: 1pt),
          radius: 2pt,
          baseline: 2pt,
        )[#no]
      ],
      [#h(8pt) #title],
    )
    #v(2pt)
    #line(length: 100%, stroke: 1pt + palette.brand)
    #v(6pt)
  ]
}

// ------ Exhibit header (id + name + source, baseline-aligned) ------
#let exhibit-header(id, title, source) = {
  block(width: 100%)[
    #set text(size: 7.5pt, weight: "bold", fill: rgb("#054f31"))
    #grid(
      columns: (auto, 1fr, auto),
      align: (left, left, right),
      [#id],
      [#h(6pt) #text(size: 8.5pt, weight: "semibold")[#title]],
      [#text(size: 6.8pt, style: "italic", fill: rgb("#475467"))[Sumber: #source]],
    )
  ]
}

// ------ Financial table (with header band, alternating rows, tab nums) ------
#let fin-table(headers, rows, footers: (), columns: none, palette: DEFAULT_PALETTE) = {
  set text(font: FONT_MONO, size: 7.5pt, features: ("tnum",))
  set table(
    stroke: 0.5pt + palette.line,
    fill: (col, row) => if row == 0 { palette.brand_dark } else if calc.odd(row) { palette.band } else { palette.paper },
    inset: (x: 4pt, y: 2.5pt),
  )
  // Coerce tuple-of-tuples (typst markup) into array-of-arrays for .enumerate()
  let headers-arr = if type(headers) == array { headers } else { headers.pos() }
  let rows-arr = if type(rows) == array { rows } else { rows.pos() }
  let cols = if columns != none { columns } else { (1.6fr, ..(1fr,) * (headers-arr.len() - 1)) }
  // Header row
  let header-cells = headers-arr.enumerate().map(((i, h)) => table.cell(
    text(fill: white, weight: "bold", size: 7.5pt)[#h],
    align: if i == 0 { left } else { right },
  ))
  // Body rows
  let body-cells = rows-arr.map(row => {
    let row-arr = if type(row) == array { row } else { row.pos() }
    row-arr.enumerate().map(((i, c)) => table.cell(
      align: if i == 0 { left } else { right },
      [#c],
    ))
  })
  // Footer rows (totals)
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

// ------ Card (border + tinted background) ------
#let card(palette, fill-left-border: true, content) = {
  block(
    width: 100%,
    stroke: if fill-left-border {
      (left: 2.5pt + palette.brand, top: 0.75pt + palette.line, right: 0.75pt + palette.line, bottom: 0.75pt + palette.line)
    } else {
      0.75pt + palette.line
    },
    radius: 4pt,
    inset: 8pt,
    fill: palette.band,
  )[
    #content
  ]
}

// ------ Rating box (BUY badge + TP + upside) ------
#let rating-box(action, tp, price, upside-pct, prev-tp: none, palette: DEFAULT_PALETTE) = {
  block(
    width: 100%,
    stroke: 1.5pt + palette.brand,
    radius: 5pt,
    inset: 10pt,
  )[
    #set align(center)
    #set text(font: FONT_SANS)
    #text(size: T_RATING, weight: "black", fill: palette.brand_dark)[#action]
    #v(2pt)
    #text(size: T_SMALL, fill: rgb("#475467"))[12 bulan · eks-dividen]
    #v(6pt)
    #text(size: T_TP_BIG, weight: "black")[Rp #tp]
    #v(2pt)
    #text(size: T_SMALL)[Harga kini Rp #price]
    #v(2pt)
    #text(
      size: T_BODY,
      weight: "bold",
      fill: if upside-pct > 0 { palette.pos } else { palette.neg },
    )[#calc.abs(upside-pct)% #if upside-pct > 0 [upside] else [downside]]
    #if prev-tp != none {
      v(2pt)
      text(size: T_SMALL, fill: rgb("#475467"))[TP sebelumnya: Rp #prev-tp]
    }
  ]
}

// ------ Page wrapper ------
#let page-wrap(
  brand-label,
  date,
  ticker,
  pg-num,
  palette,
  content,
) = {
  running-header(brand-label, date, ticker)
  content
  page-footer(pg-num, palette)
  v(8pt)
}