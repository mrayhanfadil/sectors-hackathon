// =====================================================================
// common/theme.typ — Institutional equity research design tokens
// =====================================================================
// Universal theme applicable to all 4 archetypes (single / sotp / infra / strategy).
// Fonts: Liberation Serif (serif body), Liberation Sans (headings/UI), Liberation Mono (numerics)
// Palette: institutional charcoal/slate base + archetype-specific brand color
// =====================================================================

#let FONT_DIR = "../assets/fonts"

// ------ Brand assets ------
// Official Sectors mark. Sourced from hackathon.sectors.app/brand/sectors-icon.svg
// (an official Sectors property; sectors.app itself is behind a bot wall).
// A copy ships next to EVERY theme.typ so this same relative path resolves for
// both template trees (templates/typst/common/ and server/report/typst/).
#let LOGO_PATH = "../assets/brand/sectors-icon.svg"

// ------ House document furniture (fixed strings, do not vary per page) ------
#let HEADER_TITLE = "Equity Research – Company Update"
#let FOOTER_LEFT = "sectors.app"
#let FOOTER_RIGHT = "See important disclosure at the back of this report"
#let SOURCE_LINE = "Company, Team Estimates"
#let HEADER_DIVIDER_COLOR = rgb("#067647")

// ------ English date formatting: "Day, DD Month YYYY" ------
// Accepts the mixed date strings the archetypes receive ("31 Agt 2026",
// "20 Jul 2026", ISO, or free text). Unparseable input passes through
// unchanged rather than inventing a date.
#let _MONTHS = (
  jan: 1, januari: 1, january: 1, feb: 2, februari: 2, february: 2,
  mar: 3, maret: 3, march: 3, apr: 4, april: 4, mei: 5, may: 5,
  jun: 6, juni: 6, june: 6, jul: 7, juli: 7, july: 7,
  agt: 8, agu: 8, ags: 8, agustus: 8, aug: 8, august: 8,
  sep: 9, sept: 9, september: 9, okt: 10, oktober: 10, oct: 10, october: 10,
  nov: 11, november: 11, des: 12, desember: 12, dec: 12, december: 12,
)
#let _DAY_NAMES = (
  "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
)
#let _MONTH_NAMES = (
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
)

#let format-date-en(raw) = {
  let s = if type(raw) == str { raw } else { str(raw) }
  let toks = s.replace(",", " ").replace(".", " ").split(" ").filter(t => t != "")
  if toks.len() >= 3 {
    let day-ok = toks.at(0).matches(regex("^[0-9]{1,2}$")).len() > 0
    let yr-ok = toks.at(2).matches(regex("^[0-9]{4}$")).len() > 0
    let m = _MONTHS.at(lower(toks.at(1)), default: none)
    if day-ok and yr-ok and m != none {
      let dt = datetime(year: int(toks.at(2)), month: m, day: int(toks.at(0)))
      // Typst weekday(): 1 = Monday .. 7 = Sunday
      return _DAY_NAMES.at(dt.weekday() - 1) + ", " + toks.at(0) + " " + _MONTH_NAMES.at(m - 1) + " " + toks.at(2)
    }
  }
  return s
}

// ------ Page geometry ------
#let PAGE_W = 210mm
#let PAGE_H = 297mm
#let MARGIN_LR = 12mm
#let MARGIN_TB = 14mm
// Page furniture lives in the page margin boxes. The header band is positioned
// ABSOLUTELY from the paper edge with `place` (see running-header), so its offsets
// are independent of MARGIN_TOP; MARGIN_TOP only decides where body text starts and
// must clear the divider rule:
//   HEADER_TOP_INSET      paper edge -> header title (0 clipped the ascenders)
//   HEADER_TITLE_DATE_GAP title -> date
//   HEADER_RULE_GAP       date -> green divider rule
//   MARGIN_TOP            body start; must be > HEADER_TOP_INSET + band height
//   FOOTER_BOTTOM_INSET   footer text -> paper edge
//   MARGIN_BOTTOM         body stop; must clear the footer rule
// Guarded by tests/test_exhibit_convention.py::test_header_and_footer_cleared_by_margins.
#let HEADER_TOP_INSET = 10mm
#let HEADER_TITLE_DATE_GAP = 3mm
#let HEADER_RULE_GAP = 2.2mm
#let FOOTER_BOTTOM_INSET = 3.5mm
#let MARGIN_TOP = 24mm
#let MARGIN_BOTTOM = 15mm
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
#let FONT_SERIF = ("Source Serif 4", "Liberation Serif", "Caladea", "DejaVu Serif")
#let FONT_SANS = ("Inter", "Liberation Sans", "Carlito", "DejaVu Sans")
#let FONT_MONO = ("JetBrains Mono", "Liberation Mono", "DejaVu Sans Mono")

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
// ------ Running header (house convention) ------
// Left: report title, with the publication date on the line below, formatted
// "Day, DD Month YYYY". Right: Sectors.app logo, identical size on every page.
// Below: full-width house-color divider (#067647).
#let running-header(title, date) = {
  set par(leading: 0.42em, spacing: 0pt)
  // `place` pins the band to the PAPER edge. Without it Typst anchors header content
  // to the BOTTOM of the margin box, so every offset inside measured from the wrong
  // origin: the title clipped at y=-0.5mm, and the divider rule tracked MARGIN_TOP
  // at exactly 0.7x (padding and `v()` could not move it). All offsets below are
  // therefore absolute distances from the top of the paper.
  place(top + left, dy: HEADER_TOP_INSET)[
    #grid(
      columns: (1fr, auto),
      align: (left + horizon, right + horizon),
      stack(dir: ttb, spacing: HEADER_TITLE_DATE_GAP,
        text(font: FONT_SANS, size: 8.5pt, weight: "bold", fill: rgb("#101828"))[#title],
        text(font: FONT_SANS, size: 7pt, weight: "regular", fill: rgb("#475467"))[#date],
      ),
      image(LOGO_PATH, height: 13pt),
    )
    #v(HEADER_RULE_GAP)
    #line(length: 100%, stroke: 1.2pt + HEADER_DIVIDER_COLOR)
  ]
}

// ------ Page footer (house convention) ------
// Left: sectors.app. Right: disclosure pointer + the real page number.
#let page-footer() = context {
  set text(font: FONT_SANS, size: FOOTER_SIZE, fill: rgb("#475467"))
  set par(leading: 0.42em, spacing: 0pt)
  // Bottom-anchored too: the inset lifts the rule clear of the paper edge and
  // keeps it below the content area (MARGIN_BOTTOM must clear it).
  pad(bottom: FOOTER_BOTTOM_INSET)[
    #line(length: 100%, stroke: 0.5pt + rgb("#e4e7ec"))
    #v(3pt)
    #grid(
      columns: (1fr, auto),
      align: (left, right),
      [#FOOTER_LEFT],
      [#FOOTER_RIGHT · #counter(page).display()],
    )
  ]
}

// ------ Section header ------
#let section-header(no, title, palette, sub: none) = {
  block(width: 100%)[
    #set text(font: FONT_SANS, size: T_H2, weight: "bold", fill: palette.brand_dark)
    #grid(
      columns: (auto, 1fr),
      align: (left, left),
      [
        #set text(font: FONT_SANS, size: 7pt, weight: "bold", fill: white)
        #box(
          fill: palette.brand,
          inset: (x: 5pt, y: 1pt),
          radius: 2pt,
          baseline: 2pt,
        )[#no]
      ],
      [#h(8pt) #title],
    )
    #if sub != none [
      #v(1pt)
      #text(font: FONT_SERIF, size: 7pt, style: "italic", fill: palette.muted)[#sub]
    ]
    #v(2pt)
    #line(length: 100%, stroke: 1pt + palette.brand)
    #v(5pt)
  ]
}

// ------ Exhibit labeling: ONE global counter for the whole document ------
// Numbering runs sequentially from the first page to the last and never resets
// per page. The number comes from Typst's own figure counter for kind
// "exhibit", so adding or removing an object re-sequences every later exhibit
// automatically — no call site ever writes "Exhibit N".
//
// Because the label is a real `figure`, an exhibit can also be CITED from prose:
// attach a label at the call site and reference it — the number resolves at
// layout time, so a stale hardcoded cross-reference is impossible.
//
//   #exhibit-header("Pita Valuasi Historis P/BV", "IDX") <ex-pbv>
//   #fin-table(...)
//   ... lihat @ex-pbv ...       -> renders "see Exhibit 13"
#let exhibit-src-state = state("exhibit-src", SOURCE_LINE)
#let exhibit-flushed = state("exhibit-flushed", true)

// Source line, rendered UNDER the object it belongs to. House rule: the visible
// line is always "Source: Company, Team Estimates", including for purely
// historical data. The `source` argument still carries the real provenance
// (engine, filing, screener) — it is stashed in exhibit-src-state so an audit
// build can surface it via exhibit-source-detail().
#let exhibit-source(source: none) = {
  exhibit-flushed.update(true)
  context {
    let s = if source != none { source } else { SOURCE_LINE }
    block(width: 100%)[
      #v(1pt)
      #text(font: FONT_SANS, size: 6.8pt, style: "italic", fill: rgb("#475467"))[Source: #s]
    ]
  }
}

// Provenance variant — internal/audit builds only, never the house PDF.
#let exhibit-source-detail() = context {
  exhibit-flushed.update(true)
  block(width: 100%)[
    #v(1pt)
    #text(font: FONT_SANS, size: 6.8pt, style: "italic", fill: rgb("#475467"))[Source: #exhibit-src-state.get()]
  ]
}

// ------ Exhibit label (auto-numbered) — ABOVE the object ------
// Both arguments are positional: exhibit-header("Title", "internal provenance").
// Flushes the previous exhibit's source line first, so a source line always
// lands directly beneath its own object rather than after the next label.
// Bare label figure — a SINGLE element, so a markup label attaches to it and a
// prose citation resolves to the exhibit number at layout time:
//
//   #exhibit-mark("<provenance>")
//   #exhibit-figure("P/BV Band (4-Year History)") <ex-pbv>
//   ... lihat @ex-pbv ...        -> renders "lihat Exhibit 13"
//
// (exhibit-header cannot be labeled at the call site: it emits the source flush
// plus the figure, and a label on a multi-element sequence is unreferenceable.)
#let exhibit-figure(title) = figure(
  [],
  kind: "exhibit",
  supplement: [Exhibit],
  caption: title,
  placement: none,
  numbering: "1.",
)

// Stash this exhibit's provenance and flush the previous exhibit's source line.
#let exhibit-mark(source) = {
  context {
    if not exhibit-flushed.get() { exhibit-source() }
  }
  exhibit-src-state.update(source)
  exhibit-flushed.update(false)
}

// The normal call: label above (auto-numbered), source line below (flushed by
// the next label or by the end of the page).
#let exhibit-header(title, source) = {
  exhibit-mark(source)
  exhibit-figure(title)
}

// ------ Financial table (with header band, alternating rows, tab nums) ------
// `bold-rows` names the body row indices that render bold in place — the way a
// statement marks its subtotals (Laba Kotor, EBIT, Arus Kas Bersih dari Operasi)
// without pretending they are bottom-of-table totals. `footers` stays for rows
// that genuinely close the table.
#let fin-table(headers, rows, footers: (), columns: none, palette: DEFAULT_PALETTE, font: auto, bold-rows: ()) = {
  set text(font: if font == auto { FONT_MONO } else { font }, size: 7.5pt, features: ("tnum",))
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
  let body-cells = rows-arr.enumerate().map(((ri, row)) => {
    let row-arr = if type(row) == array { row } else { row.pos() }
    row-arr.enumerate().map(((i, c)) => table.cell(
      align: if i == 0 { left } else { right },
      if bold-rows.contains(ri) { text(weight: "bold")[#c] } else { [#c] },
    ))
  })
  // Footer rows (totals). `table.cell` takes ONE positional body: this branch had
  // `text(weight: "bold")` as the body and `[#c]` as a second positional argument,
  // so it raised "missing argument: body" — it only stayed hidden because no call
  // site used `footers:` until the cash-flow exhibit did.
  let footer-cells = footers.map(row => row.enumerate().map(((i, c)) => table.cell(
    align: if i == 0 { left } else { right },
    text(weight: "bold")[#c],
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

// ------ Honest-empty display (LOUD policy, Sep 2026): none renders as em
// dash instead of crashing str(none) or inventing a number. ------
#let nstr(x) = if x == none { "—" } else { str(x) }

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
    #text(size: T_RATING, weight: "black", fill: palette.brand_dark)[#if action == none { "—" } else { action }]
    #v(2pt)
    #text(size: T_SMALL, fill: rgb("#475467"))[12 bulan · eks-dividen]
    #v(6pt)
    #text(size: T_TP_BIG, weight: "black")[Rp #nstr(tp)]
    #v(2pt)
    #text(size: T_SMALL)[Harga kini Rp #nstr(price)]
    #v(2pt)
    #if upside-pct == none {
      text(size: T_BODY, weight: "bold", fill: palette.muted)[— data Sectors pending]
    } else {
      text(
        size: T_BODY,
        weight: "bold",
        fill: if upside-pct > 0 { palette.pos } else { palette.neg },
      )[#calc.abs(upside-pct)% #if upside-pct > 0 [upside] else [downside]]
    }
    #if prev-tp != none {
      v(2pt)
      text(size: T_SMALL, fill: rgb("#475467"))[TP sebelumnya: Rp #prev-tp]
    }
  ]
}

// ------ Page wrapper ------
// Furniture is native (see set-page-defaults), so this only keeps the source-line
// flush: the last exhibit on a page still gets its Source line before the page
// ends instead of leaking onto the next page. Page breaks stay at the call site.
#let page-wrap(
  brand-label,
  date,
  ticker,
  pg-num,
  palette,
  content,
) = {
  content
  context {
    if not exhibit-flushed.get() { exhibit-source() }
  }
}

#let set-page-defaults(doc, date: none) = {
  set document(keywords: ("Font: Liberation Serif, Liberation Sans, Liberation Mono, Source Serif 4, Inter",))
  // Native page furniture: Typst draws these on EVERY physical page, including
  // pages produced by content overflow, and the page number is the real page
  // counter rather than a hand-written literal.
  set page(
    paper: "a4",
    margin: (left: MARGIN_LR, right: MARGIN_LR, top: MARGIN_TOP, bottom: MARGIN_BOTTOM),
    header: context running-header(HEADER_TITLE, if date == none { "" } else { format-date-en(date) }),
    footer: context page-footer(),
  )
  set text(
    font: FONT_SERIF,
    size: T_BODY,
    lang: "id",
    fill: rgb("#101828"),
    features: ("tnum",),
  )
  set par(leading: 0.65em, justify: false)
  set list(indent: 8pt, marker: [•])
  // Exhibit labels render ABOVE their object and carry the document-global
  // exhibit counter, so numbering re-sequences automatically on revision.
  set figure.caption(position: top, separator: [ ])
  set figure(gap: 1pt)
  show figure.caption: it => block(width: 100%, above: 6pt, below: 2pt)[
    #set text(font: FONT_SANS, size: 8.5pt, weight: "bold", fill: rgb("#054f31"))
    #it
  ]
  doc
}
