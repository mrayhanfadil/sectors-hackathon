# Slide 3 - Performance Visualisation & Forecasting spec (AMMN)

## 0. Binding rule text (owner, 12 Sep 2026)

The owner's wording outranks any paraphrase elsewhere in this document.

> **SLIDE 3 - Visualisasi Kinerja Keuangan dan Forecasting**
>
> Layout grid 2x2, masing-masing kuadran berisi satu chart plus blok narasi pendamping (baik di bawah chart atau di sampingnya tergantung ruang, tapi harus menempel visual dengan chart-nya masing-masing, bukan narasi terpisah di ujung slide).
>
> **Exhibit 4. Revenue & Revenue Growth.** Chart combo: bar untuk Revenue absolut (Rpbn) periode 2024A-2028F, line untuk growth yoy (%) di secondary axis. Warna bar navy solid untuk data aktual, navy dengan pattern/opacity lebih rendah untuk data forecast (supaya visual langsung membedakan aktual vs proyeksi tanpa perlu baca label). Narasi (2-3 kalimat): identifikasi driver utama pertumbuhan atau penurunan revenue di tiap periode signifikan, bandingkan CAGR historis (2024A-2025A) dengan CAGR forecast (2026F-2028F) dan jelaskan kalau ada perbedaan laju yang material, flag inflection point kalau ada (contoh: growth melambat tajam di satu tahun forecast karena base effect tinggi atau selesainya periode ekspansi kapasitas).
>
> **Exhibit 5. EBITDA & EBITDA Margin.** Chart combo serupa: bar EBITDA (Rpbn), line EBITDA margin (%) secondary axis. Narasi: jelaskan arah trajectory margin (ekspansi atau kontraksi) dan penyebab strukturalnya (cost structure shift, pricing power, operating leverage dari fixed cost absorption), bandingkan level margin forecast dengan rata-rata historis 3-5 tahun sebagai sanity check apakah asumsi margin forecast realistis atau terlalu optimis/pesimis dibanding track record perusahaan.
>
> **Exhibit 6. Net Profit & EPS Growth.** Chart combo: bar Net Profit (Rpbn), line EPS growth (%) secondary axis. Narasi: bandingkan laju growth net profit/EPS dengan laju growth revenue dan EBITDA di dua chart sebelumnya, kalau ada gap material (misal EBITDA growth 15% tapi net profit growth cuma 5%), wajib jelaskan below-the-line item penyebabnya secara eksplisit (kenaikan tax rate efektif, beban bunga naik karena leverage tambahan, minority interest, atau kerugian/keuntungan kurs).
>
> **Exhibit 7. Chart keempat (switchable by sector).** Default non-bank: DER (bar, x) vs ROE (line, %) - untuk menilai apakah pertumbuhan yang diproyeksikan didanai dengan leverage yang sehat atau berisiko meningkatkan financial risk berlebihan. Bank: NIM (%) dan Cost of Credit (%) trend, atau alternatif NPL/LaR ratio trend, karena ini driver utama profitabilitas emiten bank, bukan leverage dalam pengertian umum. E&P/upstream: production volume (bar) dan lifting cost per barrel/boe (line), karena revenue emiten E&P tidak bisa dianalisis lewat leverage sederhana, harus lihat volume dan cost structure produksi. Sektor lain (property, plantation) perlu penyesuaian serupa sesuai driver utama earnings masing-masing, didiskusikan case-by-case saat build.
>
> **Tie-out.** Semua data di Slide 3 harus tie-out langsung dengan Exhibit 3 (Key Financials Slide 1), tidak boleh ada angka yang berbeda antara dua exhibit ini untuk periode yang sama.

### 0.1 How the rules are enforced

| Rule | Enforced by | Mechanism |
|---|---|---|
| 2x2 grid, narrative attached to its own chart | `templates/report_single.html` + `templates/macros.html` | `.s3-grid` two-column CSS grid, one `.s3-cell` per quadrant holding label, chart, narrative and source line; `audit_performance_page` fails a quadrant without an attached narrative |
| Combo charts, 2024A-2028F, actual vs forecast visually distinct | `templates/_slide3_macro.html` (`svg_combo`) | bars solid navy for the actual periods and lighter with a hatch overlay for the forecast periods; the line rides the secondary axis with its own value labels |
| Every number ties out with the Key Financials exhibit | `server/report/house_rules.py::audit_performance_page` | the builder reads the cover's Key Financials rows themselves, and the gate re-compares each bar against that table per period, naming the period in the violation |
| Narrative per quadrant (drivers, CAGR, margin sanity check, below-the-line gap) | `server/report/performance_page.py` | each narrative is computed from the series (growth, CAGR, margin vs realised average, EBITDA-to-net-profit gap with the leverage and coverage that explain it); a forecast assumption the narrative disagrees with is stated on the page |
| Sector switch for the fourth quadrant | `performance_page.QUADRANT_TITLES` + page notes | non-bank default (DER vs ROE) is built; bank (NIM/CoC) and E&P (volume/lifting cost) branches are named as unavailable in the data rather than faked |

Ticker: AMMN (PT Amman Mineral Internasional Tbk, AMMN IJ). Sector: copper-gold mining.
Slide 3 is the model made visible: four charts on a 2x2 grid, each with its own attached
narrative block. Its job is to make the forecast auditable - a reader must be able to see
whether the projected growth is *produced* (volume), *earned* (price vs cost), and *kept*
(below-the-line leakage to net profit), and to reconcile every printed number back to the
Key Financials table on Slide 1.

Scope note: AMMN is NOT a bank and NOT a generic leveraged corporate. Exhibit 7 is the
MANDATORY mining variant (production volume + unit cash cost), never DER/ROE, never NIM.
This mirrors `agents/adk/agents/instructions.py` visualizer block `Exhibit-7 SECTOR SWITCH`
and the copper-gold KPI slot line (`Cu-eq production (t/lbs), ore grade (Cu % / Au g/t),
strip ratio, C1 cash cost and AISC per lb Cu-eq, realized Cu price (USD/lb), realized Au
price (USD/oz), reserve life (years)`).

## 1. Purpose (what this slide must prove)

1. Revenue growth has a named driver per significant period (volume, realised Cu/Au price,
   or both) - not a top-down percentage.
2. EBITDA margin direction has a structural cause (cost structure / pricing power /
   operating leverage), and the forecast margin is sanity-checked against the 3-5Y
   historical average.
3. Net profit / EPS growth is reconciled against the revenue and EBITDA pace; ANY material
   gap names the below-the-line item explicitly.
4. Growth is fundable and producible: volume vs unit-cost relationship is visible, with
   reserve-life context deferred to Slide 4.
5. Every number is IDENTICAL to the Key Financials table on Slide 1 for the same period.

## 2. Layout - 2x2 grid

| Quadrant | Chart (role slot) | Narrative block |
|---|---|---|
| Top-left | Revenue & Revenue Growth (2024A-2028F) | attached BELOW the chart |
| Top-right | EBITDA & EBITDA Margin (2024A-2028F) | attached BELOW the chart |
| Bottom-left | Net Profit & EPS Growth (2024A-2028F) | attached BELOW the chart |
| Bottom-right | Mining: Production Volume vs Unit Cash Cost | attached BELOW the chart |

Binding layout rules:

- Each narrative block is a child of its own quadrant. A narrative parked at the slide end
  (a detached block covering "all four charts") is a REJECT - with 2x2 there is no room and
  the reader loses the pairing.
- If a quadrant overflows, the narrative moves BESIDE its chart inside the same quadrant -
  never to another quadrant, never to the slide footer.
- All four charts share one visual grammar: identical bar-vs-line treatment, identical
  actual-vs-forecast encoding, identical axis-label style. Four charts in four different
  styles reads as four unrelated pages.
- Both charts and narrative are renderer-owned objects: label ABOVE, source line BELOW,
  `Source: Company, Team Estimates` exactly. No header/footer/logo/page number emitted by
  the agent.
- X axis on all four charts is the same fixed band: 2024A, 2025A, 2026F, 2027F, 2028F
  (2 actual + 3 forecast, rolling). No per-chart year windows.

## 3. Exhibit slots vs renderer numbering (house rule §2)

The four exhibits below are written as ROLE SLOTS (4/5/6/7 in the template's intended
sequence) because the house format forbids literal `Exhibit N` strings in payloads and
forbids an `id` field - the number is the renderer's global figure counter
(`kind: "exhibit"`). Consequences the builder must respect:

- Never write `"Exhibit 4"` (or any number) into a chart title, payload, or `id` field.
  The agent supplies a descriptive title + data; the renderer numbers sequentially.
- The actual printed number depends on how many exhibits earlier slides emit. Slide 1's
  Key Financials table is the tie-out source of truth referred to here as "Exhibit 3" in
  the template sequence (Slide 1 spec §4 skipped the EPS-consensus table, so under the
  current build it renders as the SECOND exhibit, and slide 2's default build emits none -
  meaning the first Slide 3 chart can legitimately render as Exhibit 3). This is expected,
  not a bug: it is exactly why the counter is global.
- Prose cross-references must therefore be live references (`#exhibit-figure(...)` +
  `@ex-...`), never frozen text. A prose sentence saying "see Exhibit 7" is a REJECT.
- The tie-out in §6 is defined by OBJECT IDENTITY (chart series → table row), never by
  exhibit number, so it survives any re-sequencing.

## 4. Exhibit specs (title + data + chart shape only - no literal numbers, no `id`)

Shared axis/encoding contract for the three financial combo charts:

- Chart type: combo - NAVY bars (primary axis, left) + line (secondary axis, right).
- Bar encoding (actual vs forecast is visible WITHOUT reading labels):
  - 2024A, 2025A → NAVY SOLID (theme `NAVY`, e.g. `#004b93`).
  - 2026F, 2027F, 2028F → NAVY at reduced opacity (~40%) OR diagonal hatch, consistently
    one of the two across the whole slide (renderer picks; spec requires the two encodings
    never mixed).
  - A vertical divider / break marker between 2025A and 2026F marks the actual|forecast
    boundary on every combo chart.
- Line: the growth/margin series, single stroke in a clearly distinct hue from NAVY
  (theme accent). Negative values are signalled (theme `neg` `#b42318` for the negative
  segment, or an explicit below-zero marker) - a negative year must not masquerade as a
  positive one.
- Axis labels carry the unit explicitly. Left axis and right axis units are always both
  printed (no unitless axes).
- Data labels: none printed on bars (2x2 on one page = clutter); the reader reads the
  values off the table tie-out, and the narrative quotes the numbers.
- Gridlines: horizontal only, `line` token; no chart chrome, no 3D, no shadow.

### Exhibit - Revenue and Revenue Growth (2024A-2028F)

- Type: combo. Bars = Revenue, line = Revenue growth (yoy %).
- Axes: left `Revenue (Rpbn)`; right `Growth (yoy %)`.
- Series binding:
  - Revenue actual 2024A/2025A: Sectors annual financials (`company_report()` /
    `report_sections()` financials sections; `quarterly()` for the interim detail that
    reconciles the annual figure).
  - Revenue forecast 2026F-2028F: model output - MUST equal the Revenue row of the Key
    Financials table (Slide 1), cell-for-cell (§6).
  - Growth line = yoy change of the SAME revenue series (derived, never an independently
    sourced growth number).
- Currency bridge (AMMN-specific, blocking): AMMN reports in USD; the house table is Rpbn.
  Bars must be in the SAME currency as the tie-out table. The USD→IDR conversion uses one
  stated rate + date (USDIDR, as-of date printed in the audit field) and that same rate is
  reused by Slide 4's USD legs. Two different FX rates across slides = tie-out failure.

### Exhibit - EBITDA and EBITDA Margin (2024A-2028F)

- Type: combo. Bars = EBITDA, line = EBITDA margin (%).
- Axes: left `EBITDA (Rpbn)`; right `EBITDA Margin (%)`.
- Series binding: EBITDA actuals from Sectors financials; forecast = EBITDA row of the Key
  Financials table. Margin is DERIVED as EBITDA / Revenue x 100 from the two series on this
  slide - never an independently sourced margin, so the margin line cannot drift away from
  the bars.
- Mining reality: for AMMN, EBITDA is a price x volume − cash-cost function. The chart must
  be consistent with Exhibit 7's volume/cost path; a margin expansion with falling volume
  and rising unit cost is a contradiction the narrative must either explain or drop.

### Exhibit - Net Profit and EPS Growth (2024A-2028F)

- Type: combo. Bars = Net Profit, line = EPS growth (yoy %).
- Axes: left `Net Profit (Rpbn)`; right `EPS Growth (yoy %)`.
- Series binding: net profit actuals from Sectors financials; forecast = Net Profit row of
  the Key Financials table. EPS = net profit attributable to owners / shares outstanding
  (Sectors company snapshot, same share count as Slide 1/Slide 4) - the EPS growth line must
  reconcile to the EPS row of the Key Financials table, not to an independently computed EPS.
- Mandatory gap disclosure: if net profit growth differs materially from EBITDA growth in
  any forecast year, the attached narrative MUST name the below-the-line cause (effective
  tax rate, interest on smelter/expansion debt, minority interest on the smelter JV, FX
  loss/gain). A visible gap with no named cause is a REJECT.

### Exhibit - Mining: Production Volume vs Unit Cash Cost (role slot 7, MANDATORY variant)

- Type: combo. Bars = production volume, line = unit cash cost.
- NOT DER/ROE. NOT NIM / Cost of Credit. Rationale: AMMN's earnings are volume x realised
  price − unit cost; a leverage ratio says nothing about whether the forecast tonnage can be
  mined at a sane cost.
- Axes: left `Production Volume (unit stated)`; right `Cash Cost (unit stated)`.
  - Volume unit MUST be stated in the axis label and in the audit field. Recommended:
    contained copper, either `kt Cu` or `Mlb Cu` - pick ONE and hold it across the slide,
    the report, and Slide 4's reserve-life leg. (AMMN produces copper CONCENTRATE, not
    cathode - never label the series "cathode".)
  - Gold is carried as a memo series or an annotation only (e.g. `Au koz`), never as a second
    competing bar series that muddies the volume read.
  - Cost unit MUST be stated and MUST be one of C1 or AISC - state WHICH. Recommended:
    `AISC (US$/lb Cu, net of Au by-product credit)` because AMMN's gold credit materially
    changes the cost read; the axis label must say `net of Au credit` when that is the basis.
- Series binding: production/cost from the mining extension (`mining_company_financials()`
  → `/mining/financials/{slug}/`, USD millions) plus `data/assumptions/AMMN.json` model
  output for forecast years. Actual vs forecast encoding identical to the other three charts.
  Strip ratio is NOT a plotted series - it belongs in the narrative as the cost driver (§5,
  Exhibit 7 narrative).
- Narrative must include the reserve-life pointer: one clause handing off to Slide 4 for the
  horizon (Batu Hijau remaining life + Elang development timeline). Do not re-derive reserve
  life here.
- If the cost basis used by Sectors differs from the model's AISC definition (e.g. reported
  C1 vs model AISC), emit BOTH labels explicitly rather than silently relabelling one as the
  other.

## 5. Narrative templates (one per quadrant; 2-3 sentences each)

Every narrative is attached to its own chart and must carry explicit numbers. Placeholders
in `<...>` are filled from the same model output that feeds the charts.

### N4 - Revenue
"Revenue <+/-X%> yoy to Rp<A>bn in <year>, driven mainly by <volume change> and
<realised Cu/Au price change> (state which dominates). Historic CAGR 2024A-2025A of
<X>% vs forecast CAGR 2026F-2028F of <Y>% - <reason for the pace change>. Inflection at
<year> reflects <base effect | capacity/phase end | grade step-change>."
Required: main driver per significant period; both CAGRs; every material pace change
explained; inflection points flagged.

### N5 - EBITDA
"EBITDA margin <expands|contracts> <X>pp to <Y>% by 2028F, structurally driven by
<cost structure shift | realised-price capture | operating leverage on fixed cost>.
The 2028F margin of <Y>% compares with the 3-5Y historical average of <Z>% (years
<lo-hi>) - <above/below> track record because <reason>. Forecast margin assumes
<volume growth | unit-cost path> as shown in the mining quadrant."
Required: direction + structural cause; explicit sanity check vs 3-5Y average with the
years cited; no margin assumption floating free of Exhibit 7.

### N6 - Net Profit / EPS
"Net profit <+/-X%> yoy to Rp<A>bn with EPS growth of <Y>% in <year>, vs revenue growth
of <B>% and EBITDA growth of <C>% - <in line | gap of D>pp>. The gap is explained by
<named below-the-line item: effective tax rate of <t>% | interest expense on
<smelter/expansion debt> | minority interest on the smelter JV | FX loss/gain on
USD-denominated debt>."
Required: the three-growth comparison (revenue/EBITDA/net profit); ANY material gap → named
below-the-line cause with a number. Forbidden: "dampened by higher costs" with no line item.

### N7 - Mining volume vs cash cost
"Copper production of <V> <kt/Mlb> in <year> (<+/-X%> yoy) at AISC of US$<c>/lb
<net of Au credit>, <+/-Y%> vs <prior year / historical average of US$<z>/lb>. The
volume-cost relationship is <favourable: volume growth absorbing fixed cost | adverse:
declining grade/strip ratio pushing unit cost up>. Cost trajectory vs history: <...>;
reserve-life context and the mine-plan horizon are covered on Slide 4."
Required: volume-cost relationship; cost trajectory vs historical; explicit reserve-life
pointer to Slide 4; strip ratio named as the mining-cost driver where it moves the result.
Forbidden: generic "cost efficiency improved" with no unit number.

## 6. Tie-out matrix vs the Key Financials table (Slide 1)

"Key Financials" = the table referred to as Exhibit 3 in the template sequence (Slide 1
spec §4; currently renders with the counter one lower because the EPS-consensus table is
skipped). Match by object identity, not by exhibit number.

| Slide 3 series | Key Financials row | Periods that must match | Tolerance |
|---|---|---|---|
| Revenue bars | Revenue | 2024A-2028F | IDENTICAL |
| Revenue growth line | Revenue row, derived yoy | 2025A-2028F | derived from the same row |
| EBITDA bars | EBITDA | 2024A-2028F | IDENTICAL |
| EBITDA margin line | EBITDA row / Revenue row, derived | 2024A-2028F | derived from the same two rows |
| Net Profit bars | Net Profit | 2024A-2028F | IDENTICAL |
| EPS growth line | EPS row, yoy | 2025A-2028F | derived from the same row |
| Mining volume bars | production (mining extension rows) | forecast years | IDENTICAL to Slide 4 A11 horizon inputs |
| Mining AISC line | cash cost / AISC (mining extension rows) | forecast years | IDENTICAL to Slide 4 cost assumption |
| Growth/margin/ratio values quoted in N4-N7 | same rows | as quoted | IDENTICAL |

Rules:

1. A mismatch between Slide 3 and the Key Financials table is a MODEL LINK ERROR, never a
   "rounding difference". The only exception is a genuine sub-0.1% rounding artefact - and
   even then the difference is disclosed, not absorbed.
2. Any Slide 3 revision re-exports the Key Financials table on Slide 1 (and Slide 4's
   revenue/EBITDA/cost assumption rows) in the same change. There is no version of this
   build where Slide 3 is refreshed alone.
3. Derived series (growth %, margin %, EPS growth) are computed from the tied-out rows
   in-render, not typed in as separate numbers. This is the structural defence against
   tie-out drift.
4. One FX rate (USDIDR, rate + as-of date) bridges every USD↔IDR leg on this slide and
   Slide 4's USD legs. Two rates = tie-out failure.
5. Share count is identical across EPS (this slide), market cap (Slide 1) and per-share
   legs (Slide 4).

## 7. KPI / hero cross-ref (`kpi_output`)

AMMN hero KPIs live in `kpi_output`; every chart states which KPI feeds it.

| KPI (kpi_output) | Feeds | How |
|---|---|---|
| Cu-eq production / sales volume (unit stated) | Exhibit 4 bars (revenue), Exhibit 7 bars | volume leg of revenue = price x volume; Exhibit 7 is the volume KPI made visual |
| Cu realised price (USD/lb, stated unit) | Exhibit 4, Exhibit 5, N4/N7 | price leg of revenue and of the margin read |
| Au realised price (USD/oz) | Exhibit 4, Exhibit 5, Exhibit 7 cost basis | by-product credit that makes AISC net-of-credit meaningful |
| Cash cost / AISC (USD/lb Cu-eq) | Exhibit 5 line (via margin cause), Exhibit 7 line | cost leg of margin; Exhibit 7 is its own series |
| Strip ratio (x) | Exhibit 5 / Exhibit 7 narratives (cost driver, not a plotted series) | explains mining cost movement |
| Ore grade (Cu % / Au g/t) | N4/N7 narrative (volume-cost relationship) | explains why volume or unit cost steps |
| Reserve life (years) | pointer to Slide 4 only | never re-derived on this slide |

Rules: a KPI with `source: sectors_missing_key` and an empty value is a LOUD GAP on the
affected chart - never a synthetic placeholder, never a silent omission of the chart's
narrative obligation (the narrative says the KPI is unavailable, not that it is fine).

## 8. Data dependencies (Sectors primary; web_search colour only)

| Exhibit | Sectors wrapper → endpoint | Fields | Fallback |
|---|---|---|---|
| Revenue / EBITDA / Net Profit actuals | `company_report()` / `report_sections()` → /company/report/ (sections: financials) + `quarterly()` → /financials/quarterly/ + `quarterly_dates()` | revenue, EBITDA/operating profit, net profit, by year/quarter | NONE for numbers - loud STOP on `sectors_missing_key` |
| Shares outstanding (EPS leg) | `company_report()` company snapshot | shares outstanding | same |
| Mining volume + unit cost | `mining_company_financials(slug)` → /v2/mining/companies/financials/?year= | production, cost (USD millions) - slug resolved first via `mining_companies(keyword="AMMN")` | same |
| Mining operational detail (grade, strip ratio, commodity mix) | `/v2/mining/companies/{slug}/` and `/v2/mining/companies/{slug}/performance/` - NOTE: no wrapper exists in `server/sectors.py` yet (only `mining_companies` + `mining_company_financials`); needs MCP tool or a new wrapper - flagged as a build dependency, do NOT fake it | operational fields | loud gap |
| Commodity price deck (Cu/Au realised) | `mining/commodities/price/{commodity}/` (monthly, max 3yr) or the model's realised-price assumption | monthly price | loud gap; web_search for narrative colour only, url+date mandatory |
| Segments (production/sales split) | `segments()` → /company/get-segments/ (known 404 for some names - bills 1 credit, handle honestly) | segment revenue | qualitative only |
| Forecast years 2026F-2028F | data/assumptions/AMMN.json model output | forecast revenue/EBITDA/NP/EPS/volume/cost | NONE - this is the model, not an external feed |

Rules: `sectors_missing_key` → loud STOP recorded on the slide, never synthetic. Empty-result
200 still bills - cache aggressively. Every object keeps `source` (internal provenance:
outlet, url, date) as an AUDIT field; the printed line is always the house constant.

## 9. Critic checks (gate before ship)

- [ ] Zero literal "Exhibit N" strings; zero `id` fields; no frozen prose number references
      (live `@ex-...` refs only).
- [ ] Four quadrants on a 2x2 grid; each narrative attached to its OWN chart (none detached
      at slide end).
- [ ] Every object: descriptive label ABOVE (never "Chart"/"Table") + exactly
      `Source: Company, Team Estimates` BELOW.
- [ ] No renderer-owned furniture emitted (header/footer/logo/page number/date block).
- [ ] Actual vs forecast distinguishable without reading labels (solid vs reduced-opacity/
      hatch), encoded consistently across all four charts, with a visible actual|forecast
      boundary.
- [ ] Every axis label carries its unit; volume unit and C1-vs-AISC choice stated; AISC
      labelled "net of Au credit" if that is the basis.
- [ ] Exhibit 7 is the MINING variant (production volume bar + unit cash cost line) -
      NOT DER/ROE, NOT NIM/Cost of Credit.
- [ ] Revenue/EBITDA/Net Profit/EPS series IDENTICAL to the Key Financials table rows
      (any mismatch = model link error, not rounding; sub-0.1% artefacts disclosed).
- [ ] Derived series (growth %, margin %, EPS growth) computed from tied-out rows, not
      independently typed.
- [ ] One FX rate (USDIDR, rate + date) across this slide and Slide 4's USD legs; one share
      count across EPS / market cap / per-share legs.
- [ ] Net profit growth vs EBITDA growth gap in any year names the below-the-line cause with
      a number.
- [ ] Forecast margin sanity-checked vs 3-5Y historical average with years cited.
- [ ] Mining narrative carries the reserve-life pointer to Slide 4.
- [ ] KPI cross-ref present; each chart names its feeding KPI; `kpi_output` gap → loud gap,
      never synthetic.
- [ ] `sectors_missing_key` → loud STOP recorded; no synthetic numbers anywhere.
- [ ] Provenance (outlet, url, date) retained as internal audit field per object.
