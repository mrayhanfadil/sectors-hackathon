# Forecast inputs — internal calibration trail (NOT rendered in the deck)

The shipped deck presents the forecast columns as **team estimates aligned to the licensed dataset** and does
not name any other research house. This file is the audit trail behind that label; it stays in the repo, is
not read by any page builder, and never reaches the PDF. Auditors and the Critic can check it here.

## What was calibrated

| Driver | Origin of the initial shape | How it was re-based |
|---|---|---|
| Revenue FY26F-28F | BRIDS Equity Research, "From Pit to Cathode: Unlocking a New Earnings Cycle" (initiation 29 Jun 2026), Exhibit 41 | converted US$mn -> Rp bn on the FY2025A-implied cross-rate (Sectors revenue Rp 30,904 bn / US$1,847 mn = 16.73 Rp bn per US$1mn), then anchored to the Sectors FY2025A actuals |
| EBITDA FY26F-28F | same, Exhibit 41 | same re-basing, then checked against the Sectors annual actuals |
| Net profit FY26F-28F | same, Exhibit 41 | same |
| D&A FY26F-28F | same, Exhibit 43 | same |
| Capex FY26F-28F | same, Exhibit 24 (DCF) | same |
| Interest expense, minority interest | same, Exhibit 41 | same |
| Gross debt, inventory | same, Exhibit 42 | same |
| Working capital | same, Exhibit 43 | same |
| The reserve-based leg ELANG | BRIDS (unbuildable from the licensed dataset) | EXCLUDED and disclosed as excluded, not synthesised |

`data/drivers/AMMN.json` carries this in `attribution_internal` and per-series `source_internal`; the fields the
deck prints (`attribution`, `source`) hold the neutral label.

## Rule

A page may cite: the licensed dataset (Sectors), the issuer's own filings / IDX, public news and the team's own
estimates. A page may not name another research house. The gate `audit_source_independence` enforces it.
