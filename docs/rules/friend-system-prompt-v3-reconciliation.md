# Generator ruleset v3 (handed over Sep 2026): reconciliation

**Source (verbatim, frozen):** `friend-system-prompt-v3.source.md` (sha256
`6d0c878f87405632d9473d2299d138087e08f3ee8e4c692bc8687b6a2096f532`, 265 lines).

**What this document is.** A friend handed over a generator spec: "System Prompt: Generator
Equity Research Company Update (v3)". It proposes one model staging intake, forecast, valuation
and narration top to bottom, with Indonesian body copy. This project keeps the opposite
architecture on purpose: Python computes every figure, the LLM only explains, and **gates are
code that runs on the render payload and on the printed PDF** (house rules, format verifier,
metric gate), never prose instructions hoping the writer behaves. So this document records, arm
by arm, what was **adopted as a deterministic check**, what was **amended**, and what was
**declined** with the reason. Each adopted arm cites its clause id, and each violation message
starts with that id, so a failure traces back to the clause.

**Status: live.** Adopted arms are enforced in `server/report/forecast_gate.py` (`audit_friend_v3`,
called by the aggregate in `server/report/house_rules.py`), and pinned by
`tests/test_friend_v3_gates.py` (54 tests). The shipped AMMN deck satisfies every arm
(live probe: 0 violations).

**What the deck already proved.** The parts quoted like statistics in the handed-over text
(`28.42x` mid-cycle, `17.99x` 2026) suggest its author saw this pipeline. The deck's own voice
today: title *"Capital spending peak passed, free cash flow funds debt paydown"*, BUY at
Rp 5.667 (+16,61%) on 15,0x 2026 operating profit, DCF as comparison only.

---

## Adopted (with amendments)

### G1.1 period freshness (adopted as written)
Rule: when the report date is more than 45 days after a half-year close, the half-year result is
the newest the deck may lead with; presenting the older quarter as "latest" is a violation. A
disclosure that the newer period is unavailable satisfies the arm (the rule's own fallback).
Live: `11 Sep 2026` → `1H26` expected; the cover says *"The newest period available is first
quarter 2026; the first-half report is not yet available."*

### G1.2 unit scale (adopted, classifier tightened)
Rule: one declared unit per table, and the same metric agrees across every surface that prints
it. The classifier compares levels only: margin, growth, multiple, per-share and return rows are
excluded, because reading *"Marjin EBITDA (%)"* as an EBITDA level produced ten false
disagreements on the first live run. Two genuine boundary notes: the tolerance is 1% relative
(below that is repricing rounding), and rows without a unit label never silently convert.

### G2.2 margin sanity (adopted, wording fixed)
Rule: a forecast margin above the issuer's own record needs the driver stated in the margin
narrative. Amended: the word "margin" itself does not count as the explanation (observed: the
sentence *"Margins move to the end of the period"* passed the first draft). The marker list holds
cost, mix and capacity drivers (operating leverage, cash cost, product mix, smelter ramp, grade).
Live: 2026-2028 margin `50,6%→67,8%` vs record `54,8%`, explained by efficiency and mix.

### G2.3 operating leverage (adopted, arm narrowed)
Rule: a ±10% price/demand move must change EBITDA by about ±10%/margin, never a flat
pass-through. The arm judges only a sentence that links a shock to EBITDA; any other percentage
in the sentence (a WACC, a growth rate) is ignored. The expected figure is recomputed from the
model's own margin, so the check cannot drift from the numbers it checks.
Example: at `50,6%` margin the implied move prints `±19,8%`; `10,0%` in that sentence is the hit.

### G2.6 forecast variation (adopted as written)
Rule: no two consecutive forecast years print the same level. A declared flat basis in the
exhibit notes (all drivers flat, with the reason) satisfies the arm; the old test fixture with
`27.236` held across all three forecast columns now fails by design, which is why the fixture
was moved instead of the arm being softened.

### G3.4 scenario ladder (adopted as written)
Rule: the downside prices below the base case and the upside above it. The existing ladder
(`scenarios_bull_bear`) computed levels but never checked the ordering; the arm reads those
levels instead of duplicating them. Silent when no ladder was computed.

### G4.2 currency discipline (adopted, one row relabelled)
Rule: one currency, risk-free rate in the same currency, no country premium counted twice. For
an INDOGB-based build the premium row now reads *"Damodaran mature-market ERP - no country
premium added (the risk-free rate is the 10Y government bond)"*: the previous label *"(country
risk adj.)"* read as if a country adjustment had been added on top. USD builds (UST 10Y) must
carry the premium; IDR builds (INDOGB 10Y) must not.

### G5.2 headline caps (adopted, verb check documented as proxy)
Rule: title ≤10 words with a verb, paragraph headline ≤9 words stating the conclusion, bullets
≤30 words each, ≤3 figures per sentence. Two deliberate judgments. First, the verb list holds
inflected forms only (`rises`, `funds`), plus `-ed`/`-ing` tokens: bare forms collide with the
nouns this deck's titles are made of (`fund`, `record`, `price`), and a proxy that accepts them
passes any statistic. Second, a figure is what a reader budgets (`Rp 33,9 tn` is one;
`Phase-8`, `FY26F`, `1Q26` are names, not figures).
Live title: *"Capital spending peak passed, free cash flow funds debt paydown"* (9 words).
The statistical title the ruleset's §5.2 rejects (*"19,5x ... versus 28,42x"*) fails the arm;
the deck does not print it.

### G5.3 catalyst curation (adopted as hybrid: code where decidable, LLM brief where not)
Rule: score 0-3 on driver impact, materiality, durability, freshness; print only items scoring
≥7; ≤7 in the table, ≤3 named in the thesis paragraph; no daily price moves, no index reviews
without flow figures; an insider item below 0.5% of shares outstanding is a net direction, not a
single trade. Code limitation, stated openly: materiality ("changes EBITDA >3%") and freshness
("not yet in the price") need a forecast run and a market read the gate cannot do, so the arm
scores **the item's own fields** (driver named → 3/2/0 by keyword class; a quantified field
with a unit → 3; a date within 90 days → freshness) instead of pretending to re-underwrite the
analyst. The exclusions and the insider-floor rule are exact. Live: the `0.018%` board block now
prints as *"Board net buying in Jul 2026 - a cumulative sign management backs the company
outlook"* plus the offsetting *"related shareholders also sold Rp 5,4 tn (9 transactions)"*.

---

## Declined (with reasons)

### Indonesian body copy (§5.1, §7 output)  -  declined
Owner decision 2026-09-22 (§14/§15): the shipped deck is full-English. No Bahasa rule was
ported, and none of the English copy was touched to satisfy one.

### One model staging all four phases (§0)  -  declined
Owner architecture: Python computes, LLM explains; the Critic judges payloads, not drafts.
Porting the four phases as prompt text would replace enforced gates with hoped-for behaviour.

### 6-page map (§5.4)  -  declined
The deck ships 11 pages with fixed numbering. The ruleset's 6-page map would renumber pages
behind "Asumsi & Sensitivitas" and break every downstream reference; forecast assumptions and
sensitivity already live where the map wants them.

### "One sentence per forecast year" (§5.4 p3)  -  declined as prose, kept as data
The cover forward paragraph already states why each year differs (EBITDA `Rp 33,9 tn → Rp 55,2
tn`, FCF `Rp 11,0 tn → Rp 35,1 tn`, debt → `Rp 49,1 tn`), and the numbers are payload-bound.
A sentence-count rule adds no check a reader can verify.

### Rating bands (§4.4: Buy >+15%, Sell <-10%)  -  already enforced
Identical to the dissent audit (`BUY_UPSIDE 0.15`, `SELL_UPSIDE -0.10`). No second copy was
added. Live: `+16,61%` → BUY.

### Terminal share >75% note (G3.1)  -  already enforced, stricter
The house DCF flags above 80% (`tv_dependency_check(threshold=0.80)`). The 75% figure was not
ported; lowering the threshold would add noise, not safety.

### Equity-vs-market-cap stop (G3.2), implied multiples at TP (G3.3), Key-Financials multiples
(G3.5), peer set (G3.6), in-band averages (G3.7)  -  already enforced
Covered by the method gate (upside >100% / downside <-50% → review), the valuation page
(multiples recomputed from the model, never typed), the single forecast resolver, the peer
audit (`n.m.` outliers), and the source-line verifier. No duplicates added.

### Gate/self-check/output JSON (§6, §7)  -  declined as format
`log_gate` exists only as QA-internal by the ruleset's own definition and is never rendered;
the house equivalent is the violations list the Critic already reads.

---

## Bugs the port caught (fix-first log)

1. `_surface_series` kept only the first observation per (metric, year), so the second surface
   could never disagree: the cross-surface arm was dead on arrival. Now keeps every observation.
2. G2.6 compared header indices against cell indices without the label-column offset: every real
   flat pair was missed. Now maps header index → cell index.
3. G2.3 skipped any sentence containing `10%`, including the one printing the claim. Now consumes
   the first `10%` as the shock and judges the remaining figure.
4. G1.2 classified ratio rows (`Marjin EBITDA (%)`, `EBITDA Growth (%)`) as EBITDA levels: ten
   false hits on the live deck. Ratio tokens now disqualify a row before classification.
5. G5.2 verb proxy accepted bare forms (`fund`, `record`, `price` are nouns in deck titles), so
   any statistic passed. Now inflected forms + `-ed`/`-ing` only.
6. G5.2 figure counter read digits inside names (`Phase-8`) as figures. Standalone tokens only.

## Open items (not blockers)

- G3.5-style per-year net-debt EV multiples remain computed but unpinned by a dedicated arm;
  the metric gate covers consistency, not the basis choice.
- Catalyst durability/freshness scoring reads the item's own date/source fields; a stale item
  re-dated by its author would pass. Provenance of catalyst rows is a future arm, not this one.
