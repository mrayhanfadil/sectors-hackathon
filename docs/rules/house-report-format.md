# House Report Format — Sectors.app Equity Research

Binding rules for every generated report document (all archetypes: `single`, `sotp`,
`infra`, `strategy`, `update`). A document that breaks any rule below is not shippable.

Owner: research. Enforced at: `templates/*.html` + `templates/macros.html` (the Jinja/HTML
render the report API and the front end serve, rendered to PDF by Chromium),
`server/report/house_format.py` (the shared furniture), `server/report/house_rules.py` (the
executable form of §7-§9), `server/report/cover_slide1.py` + `server/report/slide2.py` (the
cover builders), `templates/DATA_CONTRACT.md` (data),
`agents/adk/agents/instructions.py` (agent output), `agents/critic.py` (gate).
Guards: `tests/test_house_format_adoption.py`, `tests/test_slide2_forecast.py`.

The fixed strings live once in `server/report/house_format.py` and as template defaults in
`templates/macros.html`, and the tests assert the two agree — retyping them in either place is
how they drifted apart before.

---

## 1. Exhibit labeling

Every visual object (chart) and every tabular object (table, card-grid) — **without
exception** — carries a label directly ABOVE it and a source line directly BELOW it.

**Label format**

```
Exhibit [nomor]. [deskripsi singkat, deskriptif]
```

- Benar: `Exhibit 4. Revenue and Revenue Growth (2024A-2028F)`
- Salah (generik): `Exhibit 4. Chart`, `Exhibit 4. Table`, `Exhibit 4. Data`

The description must say what is being shown and, where relevant, the horizon or unit
— a reader who never sees the chart should still know what it contains.

**Source line**

The visible line below every object is always, **tanpa terkecuali**:

```
Source: Company, Team Estimates
```

This holds even when the data is purely historical from the financial statements
(meskipun datanya murni historis dari lapkeu).

> **Reconciliation with the provenance policy.** The real provenance (outlet, url,
> date, engine path) is NOT dropped — it is retained as an internal audit field
> (`source` in the data payload) and surfaced only by audit builds
> (`exhibit-source-detail()`), never in the house PDF. Agents still must supply
> verifiable provenance with url+date; the Critic still rejects fabricated or
> bare institution name-drops. What changed is only *where* it is rendered.

## 2. Exhibit numbering

Numbering runs **continuously from the first page to the last** and never resets per
page: Exhibit 1 on page 1 continues to Exhibit 10 and onward.

**Technical implication (binding):** the number is a **global counter owned by the
generator**, never a per-slide local variable and never a literal string supplied by
an agent. If the number of charts on one page changes, every later exhibit
re-sequences by itself.

In this codebase that counter belongs to the exhibit macro itself (`m.exhibit_auto(...)` in
`templates/macros.html`), so no call site ever writes `Exhibit N`. Data payloads must NOT carry a pre-numbered
`id` such as `"Exhibit 1"` — that is a local variable masquerading as a global one and
it desynchronises the moment a chart moves.

Prose that refers to an exhibit cites it live (`#exhibit-figure(...) <ex-abcd>` then
`@ex-abcd`), so a cross-reference can never go stale.

## 3. Page header (every page)

| Position | Content |
|---|---|
| Top-left | `Equity Research – Company Update` |
| Under it | Publication date, format `Day, DD Month YYYY` (e.g. `Monday, 20 July 2026`) |
| Top-right | Sectors.app logo — same size and position on every page |
| Below the block | Horizontal divider, `#067647` |

## 4. Page footer (every page)

| Position | Content |
|---|---|
| Bottom-left | `sectors.app` |
| Bottom-right | `See important disclosure at the back of this report` + page number |

The page number is the real page counter, not a per-page literal.

## 5. Who enforces what

| Rule | Enforced by | Mechanism |
|---|---|---|
| Label above object | `templates/macros.html` | the exhibit macro emits the label immediately above the object, one call per object |
| Descriptive label | template authoring + Critic | titles are template-side; agents never write labels |
| Constant source line | `templates/macros.html` | the source macro stamps `SOURCE_LINE`; per-exhibit provenance is stashed, not printed |
| Global sequential numbering | `templates/macros.html` | the exhibit macro's own counter — it is NEVER offset, so the first rendered label is `Exhibit 1` |
| No hand-numbered exhibits in data | `templates/DATA_CONTRACT.md` + Critic | `exhibits[*].id` banned |
| Header / logo / divider / footer on every page | `server/report/house_format.py` (`header_template()`, `footer_template()`, `PDF_MARGIN`) driven by Chromium `display_header_footer` | repeats on every PHYSICAL page. The per-`<div class="page">` fallback in `templates/macros.html` is used only when Chromium is unavailable, because it cannot survive a page overflow |
| Footer page number = real page counter | Chromium `<span class="pageNumber">` | resolves to the physical page index; never a per-page literal |
| Date format | `house_format.format_house_date()` / `format-date-en()` | `Day, DD Month YYYY` from the payload's raw date |
| Label/object/source not split by a page break | template authoring | `break-after/before: avoid` is a hint Chromium does NOT honour reliably — measure with `scripts/verify_house_format.py` |

Agents do not lay out pages. They supply data and narrative; the renderer owns
every element in the tables above. An agent that emits its own header, footer, page
number, or `Exhibit N` string is producing a duplicate that will drift.

## 7. Cover slide — the one-pager

The cover is **one physical page**. Sidebar (~30%, left) and main column (~70%, right)
carry, in this order:

| Sidebar | Main column |
|---|---|
| rating (large) + change status in italics — `Buy` / `(Initiation)`, `(Maintained)`, `(Upgrade from X)`, `(Downgrade from X)` | company name + `(TICKER IJ)` |
| price box: Last Price (Rp), Target Price (Rp), **Previous TP (Rp)** (italic `NA` on an initiation), Upside/Downside (%) with an explicit sign | theme title — the thesis with a figure, never a generic product name |
| secondary stats: No. of Shares (mn), Mkt Cap (Rpbn/US$mn), Avg. Daily T/O (Rpbn/US$mn) **with its window stated** (e.g. `T/O 3M`), Free Float (%) | three highlights, each a quantitative claim, in a tinted callout box |
| Major Shareholder (%) — every holder ≥5% | paragraph 1, 2, 3 (§8) |
| relative-performance chart vs the index, source line directly beneath it | Key Financials exhibit (§9) |
| analyst block (name + title) | |

Rationale for the ordering: an institutional reader scans the rating, its change status
and the price box before reading a single sentence, and reads the change status
specifically to see whether the rating moved — so both are above everything else and the
status is never omitted or folded into prose.

The cover is rendered from `templates/report_single.html` off the `cover.slide1` /
`cover.slide2` payload block. The copy budget below is what keeps the Key Financials exhibit on
the same physical page, so it binds every render path.

**Copy budget (binding):** paragraphs 1–3 together are limited to **2.600 characters**.
Measured at the typography in `templates/macros.html`, that is the point at which the Key
Financials exhibit stops fitting on the same page; past it the exhibit is pushed to page 2
and the one-pager contract silently breaks. The budget is asserted by
`tests/test_house_format_adoption.py` and by the Critic gate, not by eyeballing the PDF.

## 8. Narrative paragraphs (cover)

Three paragraphs, each with a bold subheading, each claim attached to an explicit figure:

1. **Financial performance** — current-period revenue and net profit against the prior
   quarter (and the prior year *where the base is meaningful*; a ramp-up quarter is named as
   such instead of being used as a growth base), the running rate against any verified
   full-year estimate, the margin/cost drivers, and positioning against management guidance.
   Where a comparison cannot be computed from verified figures, the paragraph says so
   explicitly — it does not substitute a number.
2. **News, sentiment, catalysts** — the period's concrete catalysts with their figures
   (news flow, corporate action, regulation, macro), the quantified impact on earnings or
   valuation **where a basis exists**, and an explicit statement of *why* it cannot be
   quantified where one does not exist. It closes with a verdict on whether the market has
   already priced the catalysts in, read off relative performance versus the index and the
   sector. Silence about an unquantifiable catalyst reads as an implied zero.
3. **Valuation** — four blocks in order: methodology (target price, method, key parameter);
   forecast linkage (the implied CAGR and its driver); the trading multiple at the target
   price versus the historical average and versus peers, naming any leg that is unavailable
   instead of substituting one that exists; and the risk to view with the direction of impact,
   quantified where the arithmetic allows.

## 9. Key Financials exhibit (cover)

Two actual columns, then three forecast columns: `2024A`, `2025A`, `2026F`, `2027F`,
`2028F`, under a first header cell reading `Year to 31 Dec`. Nine rows, in this order:
Revenue, EBITDA, EBITDA Growth (%), Net Profit, EPS, EPS Growth (%), PER (x), PBV (x),
EV/EBITDA (x). Units sit inside the row labels (`Revenue (Rpbn)`, `EPS (Rp)`); the absolute
Rp rows carry no decimals, percentages, multiples and EPS carry exactly one; negative values
use the accounting parenthesis form `(28,8)`, never `-28,8`. Header row navy with white text,
figures right-aligned.

Every forecast cell must be derivable from a stated input, and the derivation is printed as
a note under the table — the same standard as any other number in the document. A forecast
column that cannot be derived is not filled with a plausible curve; the derivation note says
which input is missing.

## 10. Who enforces what (slide rules)

| Rule | Enforced by | Mechanism |
|---|---|---|
| Cover block order, price-box rows, shareholder block | `server/report/cover_slide1.py` + `templates/report_single.html` | the builder derives the fields, the template only lays them out |
| Paragraph mandates (§8) | `server/report/house_rules.py` (`audit_katalis`, `audit_valuasi`) | `agents/critic.py` REJECTs the document |
| Copy budget (§7) | `server/report/house_rules.py` (`audit_copy_budget`) | Critic REJECT + `tests/test_house_format_adoption.py` |
| Highlights are quantitative | `server/report/house_rules.py` (`audit_cover`) | Critic REJECT |
| Key Financials rows/units/decimals (§9) | `server/report/house_rules.py` (`audit_key_financials`) | Critic REJECT |
| Agent-facing statement of §7–§9 | `agents/adk/agents/instructions.py` (`HOUSE_FORMAT_RULE`) | travels with every prompt that can put an object into the report |

The audit result is attached to the render payload as `house_rules` (`{ok, applicable,
violations, copy_chars, copy_budget}`) and the Critic verdict as `critic`, both persisted in
`output/cache/render_<TICKER>/report_data.json`, so the gate, the guards and a human
inspecting the document payload read the same verdict. (`/api/report/{ticker}` is a
different payload — Sectors data, not the cover spread.) `applicable` is false for documents that
carry no cover spread, so the gate never rejects a document for a section it never had.

## 11. Verification

```bash
# convention guards (static + render-level geometry)

# adoption guards (data contract, agent instructions, critic gate, render path)
.venv/bin/python -m pytest tests/test_house_format_adoption.py -q

# artifact check — the only layer that sees PHYSICAL pages. Source-level guards pass
# even when per-page furniture got lost to a page overflow, when an exhibit label is
# orphaned from its object by a page break, or when footer page numbers repeat.
.venv/bin/python scripts/verify_house_format.py output/<ticker>_report.pdf

# slide rules §7-§9 on the payload — the SAME audit the Critic gate runs, so a green
# gate and a green payload mean the same thing
.venv/bin/python -c "import json,sys; from server.report.house_rules import audit_house_rules; \
print(json.dumps(audit_house_rules(json.load(open(sys.argv[1]))), indent=2, ensure_ascii=False))" \
output/cache/render_<TICKER>/report_data.json
```

Render-level evidence for a generated document:

```bash
# the served path: Jinja/HTML templates -> Chromium -> PDF
.venv/bin/python scripts/render_pdf.py output/cache/render_<TICKER>/report_data.json --out /tmp/r.pdf
```

Check on the produced PDF: label sequence is `1..N` with no gaps, source lines equal
the exhibit count, header/divider/logo/footer present on 100% of pages, footer page
numbers complete. `scripts/verify_house_format.py` runs those checks mechanically.

