# Valuation Method Selection Framework

A structured decision logic for choosing between DCF, DDM, NAV, SOTP, and Relative Valuation before financial modeling. 6 sequential gates (0-5), evaluated in order from business-model fundamentals to output sanity. Source: Abida Massi Armand's working document (personal, not institutional publication).

This doc covers **why the gates exist, what each one decides, and how our code maps to them**. The actual implementation lives in `agents/valuation/gates.py`; the orchestrator wiring is in `agents/adk/agents/instructions.py`.

## Why method selection matters

The five methods (DCF, DDM, NAV, SOTP, Relative) are not competing alternatives to be averaged together. Each has a domain where it is structurally correct and domains where it produces a confident-looking number with no economic meaning. The most common valuation error is forcing one method (usually DCF because it looks rigorous) onto a company where its core assumptions don't hold.

The logic below is ordered from the most fundamental gate (what kind of business is this) down to finer checks (data quality, ownership structure, life-cycle stage, output sanity). A company should pass through every gate in sequence; failing a gate doesn't always mean rejection — sometimes the primary method changes, sometimes a second method is required alongside the first.

Gates 0-4 determine which method should be used as the primary. Gate 5 is applied after a DCF has already been computed, to catch cases where the output itself signals an assumption problem the earlier gates missed.

## The 6 gates

| Gate | Question | Method if fails | Code function |
|------|----------|-----------------|---------------|
| **0 — Business model** | How does this company make money? Does "operating FCF" even apply? | Bank/insurance/multifinance/securities → DDM; REIT/property → NAV; mining/oil&gas/plantation → NAV/reserve-based; holding co with dissimilar lines → SOTP; single business → DCF (proceed) | `gate0_business_model(domain)` |
| **1 — Data eligibility** | Do we have enough history, profitability, capital structure, and equity base to compute a defensible DCF? | Filing < 4y → shortened DCF + thin-data disclosure; chronic losses → EV/Sales; capital breach → DCF + mandatory Relative cross-check; negative equity → EV-based multiples only | `gate1_data_eligibility(...)` |
| **2 — Ownership structure** | Is NCI large enough that a consolidated DCF bridge stops being representative? | NCI ≤ 15% → DCF; 15-40% → DCF + mandatory SOTP cross-check; > 40% → SOTP primary, consolidated DCF is rough reference | `gate2_ownership_structure(nci_pct)` |
| **3 — Cyclicality** | Is revenue volume-driven or priced off a mean-reverting global commodity cycle? | Coal/nickel/CPO/oil → NAV/reserve-based + DCF with explicit long-run price deck; newly commissioned (<3y steady state) → forward Relative Valuation; volume-driven → DCF as usual | `gate3_cyclicality(revenue_drivers, has_steady_state_3y)` |
| **4 — Life-cycle stage** | Pre-revenue, high-growth pre-profit, mature, or decline? | Pre-revenue → EV/Sales; high-growth pre-profit → EV/Sales + DCF with margin fade; mature → DCF; decline → P/BV or NAV | `gate4_life_cycle(stage)` |
| **5 — Output sanity** | Did the computed DCF produce a number that signals an assumption problem? | Upside > 100% or downside < -50% vs market → auto-override rating to "Review Required"; TV > 80% of EV → flag for cross-check (no rating override) | `gate5_output_sanity(upside_pct, terminal_value_pct_of_ev)` |

## User-decision deltas (vs. the source PDF)

Two decisions adapted the framework to our pipeline. Both live in `docs/DECISIONS.md`.

### Gate 1 thin-data fallback → shortened DCF + disclosure (NOT pure Relative)

When a ticker has <4y filing history (e.g. CDIA), the gate runner defaults to DCF with a shorter explicit horizon + mandatory "⚠ Thin Data" disclosure banner on the PDF cover. Rationale: pure Relative Valuation produces no defensible fair value (just a peer average); shortened DCF + honest disclosure preserves the math and surfaces the caveat to the reader. Rejected: (a) pure Relative Valuation — no actionable number; (b) skip DCF entirely — throws away the projection work.

### Gate 5 extreme upside/downside → auto-override rating to "Review Required"

When upside > 100% or downside < -50% vs market, the rating auto-overrides to "Review Required" regardless of the BUY/HOLD/SELL math. Rationale: an extreme DCF output signals an assumption problem the earlier gates didn't catch, and presenting it as a BUY/HOLD/SELL would mislead. The override forces a human review before publication. Note: high terminal value share (TV > 80% of EV) is flagged but does NOT auto-override the rating — the DCF is still shown, just with a cross-check recommendation.

## Quintet verdicts

End-to-end audit confirmed at 2026-09-04 with realistic parameters per ticker:

| Ticker | Sector | Primary | Secondary | Override | Notable |
|--------|--------|---------|-----------|----------|---------|
| RATU | Consumer retail | FCFF/WACC DCF | Relative Valuation | — | Mature, stable |
| CDIA | Consumer IPO | DCF (shortened horizon) | Relative Valuation | — | ⚠ Thin Data, 2y history |
| MTEL | Infra tower | FCFF/WACC DCF | Relative Valuation | — | NCI 25% triggers SOTP cross-check |
| BBCA | Bank | DDM / Excess Return | — | — | Gate 0 short-circuits to DDM (financial institution) |
| ADRO | Coal mining | NAV / Reserve-based | FCFF/WACC DCF | — | Gate 3 fires on `commodity_coal` |

Re-running the audit: `cd /home/fadil/projects/sectors-hackathon && .venv/bin/python scripts/audit_quintet_gates.py`.

## How the orchestrator uses this

The pre-flight section in `agents/adk/agents/instructions.py` calls `evaluate()` before any math. The verdict's `primary` field is authoritative for *which* method; the existing adaptive-secondary logic in the orchestrator is the *cross-check* logic. If `gate_verdict.thin_data == True`, the orchestrator emits the "⚠ Thin Data" disclosure banner. If `gate_verdict.rating_override == "Review Required"`, the orchestrator sets the final rating text to "Review Required" regardless of the BUY/HOLD/SELL calculation.

## Source attribution

Framework authored by Abida Massi Armand (personal working document, not an institutional publication). Stored at `/home/fadil/.hermes/cache/documents/doc_7804925ce4fd_framework-valuation.pdf` in this session; archived into the project's `references/` directory as a permanent fixture on next commit.

## Coverage caveats

- The framework does not address **holding period assumptions** (long-only vs. private equity style). Apply domain judgment.
- The framework assumes **Indonesian listed equities** (or comparable emerging-market disclosure regimes). Thin disclosure regimes may shift Gate 1 thresholds.
- The framework does not address **multi-currency distortions** for companies with significant foreign-currency exposure.
