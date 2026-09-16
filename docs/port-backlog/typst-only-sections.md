# Port backlog - sections that existed only in the removed Typst renderer

The Typst render path was removed on 12 Sep 2026 (`0530d8c`): it was reachable only from
`scripts/render_typst.py` and `server/report/typst_renderer.py`, never from the API, so nothing a
reader received changed when it went. Its document was richer than the served one, though, and
that extra content is what this file tracks so it can be rebuilt on the served Jinja/HTML path.

Status: **keep for later** - not scheduled. Nothing here is broken; the served report simply never
had these objects.

## Where the old source is

The last state of the Typst tree is in git, so the layout, table shapes and chart wiring can be
read directly instead of re-derived:

```bash
git show 4dc1f98:templates/typst/archetypes/report_single.typ   # 1119 lines, the document
git show 4dc1f98:server/report/typst/report_single.typ         # the mirror the renderer loaded
git show 4dc1f98:server/report/typst_renderer.py               # section wiring + payload keys
git show 4dc1f98:scripts/render_typst.py                       # which chart function each PNG came from
```

A 12-page render of AMMN from that tree was kept for reference at
`/tmp/house_audit/typst_ammn3.pdf` (also `/home/fadil/house-format-qa/AMMN_typst_cover.pdf`).
`/tmp` is ephemeral - regenerate from the git revision if it is gone.

## What is missing from the served document

Measured by diffing the exhibit titles of the 12-page Typst render against the served 7-page
Chromium render (AMMN, 12 Sep 2026): Typst carried 17 exhibits, the served path carries 11. The
six missing classes, with the surviving chart function that draws each one:

| Object (Typst exhibit title) | Section | Chart function that still exists |
|---|---|---|
| Revenue & Revenue Growth (FY20A–FY25A) | Financial highlights | `chart_revenue_combo` |
| EBITDA & EBITDA Margin (FY20A–FY25A) | Financial highlights | `chart_ebitda_combo` |
| Net Profit & Net Margin (FY20A–FY25A) | Financial highlights | `chart_netprofit_combo` |
| Volume Produksi & Biaya Kas (C1/AISC) | Mining KPI | `chart_production_cost` |
| Proyeksi Arus Kas Bebas (FCFF) | DCF deep dive | `chart_ev_equity_waterfall` / `chart_fin_combo` |
| EV/EBITDA Mid-Cycle Cross-Check (3Y average) | Valuation | `chart_history_band` |
| Cost of Capital Build | DCF deep dive | `chart_wacc_breakdown` |
| Sensitivity - FV DCF 5×5 (WACC ±1% × g ±0.5pp) | DCF deep dive | `chart_sensitivity_heatmap` |
| P/E Trailing Band vs 1-Year History | Peer / historical | `chart_pe_band_1y` |
| P/BV Trailing Band vs 1-Year History | Peer / historical | `chart_pbv_band_1y` |
| Rasio Keuangan & Efisiensi (FY20A–FY25A) | Statements | `chart_fin_combo` + a table |

The Typst document also had three sections the served report folds into other pages: a KPI-hero
page (operational metrics), a separate investment-thesis page, and a standalone risks section. The
page structure is in the git revision above; decide per section whether it earns its own page.

## The chart engine is already the porting kit

`scripts/report_charts.py` survived intact - 18 matplotlib chart functions, including every one in
the table above. It is currently **orphaned**: no HTML template calls it (the served path draws its
own inline SVG through `templates/macros.html`, `svg_*` macros), and its only remaining callers are
`tests/test_engine_exhibit7.py` and `scripts/_gen_powr_margin.py`. So porting an object is template
plus payload work, not a redraw.

## Two findings to fix while porting

1. **The DCF deep-dive charts ship without exhibit labels.** `templates/report_single.html:212-225`
   renders the WACC Breakdown, the Sensitivity heatmap and the Bear/Base/Bull scenario chart as bare
   `<div class="chart-svg">` objects under an `<h4>`. House rule §1 requires every visual object to
   carry `Exhibit N. <descriptive>` above it and the constant source line below it, without
   exception - and this is on the SERVED path, so it is a live breach, not a port item. Wrap those
   three in the exhibit macro.
2. **Mining volume / C1 / AISC series are not in the payload.** `chart_production_cost` needs a
   volume series and a cost series (two unit parameterizations: Cu-eq + C1, concentrate + AISC); the
   assumptions file would have to carry them, otherwise the exhibit must render as an honest
   "not disclosed" state rather than a chart.
