# Slide 7 - Cash Flow Statement (Exhibit 16) & Key Ratio (Exhibit 17)

## 0. Binding rule text (owner, 13 Sep 2026)

> Ex.16 cash flow, 5 columns, three sections: OPERATIONS (Net Profit, (+) D&A, (-)/(+) Increase/Decrease in
> Working Capital, Other Operating Items, Net Cash from Operations bold subtotal); INVESTING ((-) Capital
> Expenditure, Other Investing Items, Net Cash from Investing bold subtotal); FINANCING (Debt Raised/(Repaid),
> Dividends Paid in brackets, Equity Raised/(Buyback), Net Cash from Financing bold subtotal). Closing: Net
> Change in Cash, Beginning Cash Balance, Ending Cash Balance - must match Cash & Cash Equivalents in
> Exhibit 15 for the same period. Memo below the divider: FCF = Net Cash from Operations - Capital
> Expenditure, cross-checked to FCFF in Exhibit 8 on slide 4 (not identical - FCFF uses NOPAT - but it must
> be in a sensible ballpark).
>
> Ex.17 key ratio, three sections: GROWTH (%) Sales/EBITDA/Operating Profit/Net Profit yoy; PROFITABILITY (%)
> Gross Margin/EBITDA Margin/Operating Margin/Net Margin/ROAA/ROAE; LEVERAGE Net Gearing (x) and Interest
> Coverage (x). One decimal everywhere, negatives in brackets, bold section headers with extra space before
> each section. Bank issuers switch to the BBTN exhibit 9-10 pattern plus a DuPont breakdown.
>
> Tie-outs are mandatory: Net Profit in Exhibit 14 = Net Profit in the cover's Key Financials = the starting
> point of Exhibit 16. Ending Cash in Exhibit 16 = Cash & Equivalents in Exhibit 15. Any mismatch is a broken
> sheet link to be fixed before publishing, not a rounding difference, unless genuinely below 0.1%.

## 1. How the deck satisfies it

* `server/report/slide7_page.py` - `build_cashflow_page` and `build_key_ratio_page`.
* Actual columns come from Sectors' published cash-flow sections; forecast columns come from the cited driver
  path (net profit, D&A, working capital, capex, debt schedule, dividends at payout 0%).
* `build_statements_page(..., cashflow=...)` takes the FORECAST cash from this statement, so Exhibit 15 and
  Exhibit 16 tie by construction; the balance sheet's residual current-asset bucket absorbs the difference.
* Gate `audit_cashflow_page` / `audit_key_ratio_page`, template `templates/_slide7_cashflow.html`.
* The legacy "Financials 6Y + Rasio" exhibits are retired (their content is now Exhibits 14-17, and the
  performance quadrants already carry the revenue/net-profit charts).

## 2. Decision log

| Decision | Why | Alternative rejected |
|---|---|---|
| Actual columns print Sectors' sections as published, plus a NAMED reconciliation row | Sectors' own sections do not foot to its published cash balance (FY2024A: net change -7,686 matches the cash movement; FY2025A: sections sum -962 against a published net change of 0 and a cash move of -859). Smoothing it would hide exactly the broken link this page exists to expose | Deriving ΔWC as a residual so the sections foot: that would restate the source silently |
| Forecast cash drives the balance sheet instead of the balance sheet plugging cash | The rules require the two exhibits to be linked; a plug inside the cash-flow statement would make the tie cosmetic | Keeping the balance-sheet plug and forcing the cash-flow statement to balance to it |
| Working capital excludes cash | Cash sits inside current assets; including it counts the cash movement twice and produced a ΔWC twice the true size in the first build | Using (current assets - current liabilities) as printed |
| Dividends are zero, sourced from payout = 0% | AMMN has paid none since listing; a dividend line must be sourced, not assumed | Assuming a payout to make the financing section look complete |
| ROAA/ROAE use (opening + closing)/2 with the FY2023A balance from Sectors | The exhibit's own columns start at 2024A, so the first average needs a published prior-year balance rather than an interpolated one | Skipping the first column's ratio |
