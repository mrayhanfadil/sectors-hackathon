// =====================================================================
// server/report/typst/cover.typ — Method Selection Panel for PDF Cover
// =====================================================================
#import "theme.typ": *

// ------ Method Selection Framework Panel ------
#let method-selection-panel(
  gate-verdict,
  palette: DEFAULT_PALETTE,
) = {
  if gate-verdict == none {
    return []
  }

  let primary = gate-verdict.at("primary", default: "DCF")
  let secondary = gate-verdict.at("secondary", default: none)
  if secondary == none or secondary == "" or secondary == "None" {
    secondary = "—"
  }
  let rating = gate-verdict.at("rating", default: "BUY")
  let thin-data = gate-verdict.at("thin_data", default: gate-verdict.at("thin-data", default: false))
  let gates = gate-verdict.at("gates", default: ())

  // Coerce if string/other
  if type(gates) != array {
    gates = ()
  }

  block(
    width: 100%,
    stroke: 0.75pt + palette.line,
    radius: 4pt,
    inset: (x: 5pt, y: 4.5pt),
    fill: palette.band,
  )[
    #set text(font: FONT_SANS, size: 6pt)
    #block(width: 100%)[
      #set text(size: 6.8pt, weight: "bold", fill: palette.brand_dark, tracking: 0.04em)
      Method Selection Framework
      #v(2pt)
      #line(length: 100%, stroke: 0.75pt + palette.brand)
      #v(2.5pt)
    ]

    #set text(font: FONT_SANS, size: 5.6pt)
    #table(
      columns: (13pt, 68pt, 1fr),
      stroke: 0.3pt + palette.line,
      fill: (col, row) => if row == 0 { palette.brand_dark } else if calc.odd(row) { palette.band } else { palette.paper },
      inset: (x: 2.5pt, y: 1.8pt),
      align: (col, row) => if col == 0 { center } else { left },
      // Header
      table.cell(text(fill: white, weight: "bold", size: 5.6pt)[Gate]),
      table.cell(text(fill: white, weight: "bold", size: 5.6pt)[Verdict]),
      table.cell(text(fill: white, weight: "bold", size: 5.6pt)[Rationale]),
      // Rows
      ..gates.map(g => (
        table.cell(text(size: 5.6pt)[#g.gate]),
        table.cell(
          text(
            weight: "semibold",
            size: 5.6pt,
            fill: if g.at("passed", default: true) { palette.ink } else { palette.neg },
          )[#g.verdict]
        ),
        table.cell(text(fill: palette.muted, size: 5.2pt)[#g.rationale]),
      )).flatten()
    )

    #v(2.5pt)
    #line(length: 100%, stroke: 0.5pt + palette.line)
    #v(2pt)

    #block(width: 100%)[
      #set text(size: 5.8pt)
      #grid(
        columns: (1fr,),
        align: left,
        [
          Primary: *#primary* · Secondary: *#secondary* · Rating: *#rating*
        ]
      )
      #if thin-data [
        #v(1.5pt)
        #text(fill: palette.neg, weight: "bold", size: 5.6pt)[
          ⚠ Thin Data — DCF with shortened horizon, history \<4y
        ]
      ]
    ]
  ]
}
