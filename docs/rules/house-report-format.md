# House Report Format — Sectors.app Equity Research

Binding rules for every generated report document (all archetypes: `single`, `sotp`,
`infra`, `strategy`, `update`). A document that breaks any rule below is not shippable.

Owner: research. Enforced at: `templates/typst/` (Typst render),
`templates/*.html` + `templates/macros.html` (the Jinja/HTML render the report API and
the front end actually serve), `server/report/house_format.py` (the furniture both
renderers share), `templates/DATA_CONTRACT.md` (data),
`agents/adk/agents/instructions.py` (agent output), `agents/critic.py` (gate).
Guards: `tests/test_exhibit_convention.py`, `tests/test_house_format_adoption.py`.

Both render paths are independent template trees, so a rule has to hold in both. The
fixed strings live once in `server/report/house_format.py` and in
`templates/typst/common/theme.typ`, and the tests assert the two agree — retyping them
is how the trees drifted apart before.

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

In this codebase that counter is Typst's own figure counter (`kind: "exhibit"`), so
no call site ever writes `Exhibit N`. Data payloads must NOT carry a pre-numbered
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
| Label above object | `templates/typst` | `figure.caption(position: top)`, one call per object |
| Descriptive label | template authoring + Critic | titles are template-side; agents never write labels |
| Constant source line | `templates/typst` | `exhibit-source()` stamps `SOURCE_LINE`; per-exhibit provenance is stashed, not printed |
| Global sequential numbering | `templates/typst` | Typst `figure` counter for kind `exhibit` |
| No hand-numbered exhibits in data | `templates/DATA_CONTRACT.md` + Critic | `exhibits[*].id` banned |
| Header / logo / divider / footer on every page | `templates/typst` | native page furniture via `set page(header:/footer:)` — survives content overflow |
| Date format | `templates/typst` | `format-date-en()` |

Agents do not lay out pages. They supply data and narrative; the renderer owns
every element in the tables above. An agent that emits its own header, footer, page
number, or `Exhibit N` string is producing a duplicate that will drift.

## 6. Verification

```bash
# convention guards (static + render-level geometry)
.venv/bin/python -m pytest tests/test_exhibit_convention.py -q

# adoption guards (data contract, agent instructions, critic gate, render path)
.venv/bin/python -m pytest tests/test_house_format_adoption.py -q

# artifact check — the only layer that sees PHYSICAL pages. Source-level guards pass
# even when per-page furniture got lost to a page overflow, when an exhibit label is
# orphaned from its object by a page break, or when footer page numbers repeat.
.venv/bin/python scripts/verify_house_format.py output/<ticker>_report_typst.pdf
```

Render-level evidence for a generated document:

```bash
.venv/bin/python scripts/render_typst.py output/cache/render_<TICKER>/report_data.json --out /tmp/r.pdf
```

Check on the produced PDF: label sequence is `1..N` with no gaps, source lines equal
the exhibit count, header/divider/logo/footer present on 100% of pages, footer page
numbers complete.

> `scripts/render_typst.py` compiles with the template directory as the working
> directory, so a RELATIVE `report_data.json` path fails with
> `error: file not found (searched at templates/typst/archetypes/...)`. Pass an
> absolute path (or `$PWD/...`).

