# Indonesia Equity Research — Source Library (Ranked Inventory)

> **Purpose:** Ranked inventory of 15 candidate Indonesia (and adjacent) equity research sources beyond / in addition to the 3 known anchors, to serve as template variations for the institutional report.
> **Branch:** `feat/institutional-report` · **Date:** 2026-08-31 (WIB) · **Agent C sweep**
> **Method:** `web_search` for HSBC / Morgan Stanley / Credit Suisse / CLSA / Nomura / Macquarie / CGS / DBS + `site:scribd.com` leaks + generic `IDX target price PDF`. Each hit checked with `curl -I` + `pdfinfo` (where downloadable) to verify access & page count.

## Legend

- **Access:** `Yes` = direct PDF download verified (HTTP 200 + `Content-Type: application/pdf` + `pdfinfo` pages). `Scribd/Paywall` = Scribd viewer, first ~3 pages blurred then gated. `Gated/Portal` = requires entitlement/login. `CF 403` = Cloudflare-blocked without session cookie (recoverable via browser).
- **Template Value:** Why this source matters as a layout/template variation vs. the 3 known anchors.
- **Priority:** `P0` = use first (downloadable, Indonesia + target-price + rating table). `P1` = strong variation but paywalled or Singapore-adjacent. `P2` = reference / news / gated — useful for structure but not as primary PDF template.

## Known anchors (complete the library)

These 3 were already held by the team — included here so library is self-contained.

| # | Bank | Ticker/Scope | URL | Access | Pages | Template Value | Priority |
|---|---|---|---|---|---|---|---|
| 0a | **J.P. Morgan** | Indonesia Equity **2026 Outlook** (JCI target 9,100; Industrials/Materials/Consumer Staples) | https://www.scribd.com/document/986815192/JPM-Indonesia-Equity-2026-Outlook-260122-142656 | Scribd/Paywall | ~28* (Scribd viewer; blurred after p3) | **Gold standard** — strategy outlook, JCI target, sector overweights, Danantara thesis, valuation bridge. Closest to desired "global-like" house style. | **P0** (anchor) |
| 0b | **J.P. Morgan** | **IMPC IJ** — Impack Pratama: Growth & Recycling Strategy (Not Covered initiation-style via Sirkular Karya Indonesia/SKI) | https://www.scribd.com/document/973391447/JPM-Research-Impack-Pratama-IMPC | Scribd/Paywall | ~20* (Scribd viewer) | Single-name **initiation** template — free-float uplift (>20%), subtitle "Growth & Recycling", ESG/circular-economy angle. Mirror for any Not Covered name. | **P0** (anchor) |
| 0c | **Goldman Sachs + UBS** | Indonesia equities **downgrade to Underweight** (MSCI investability warning; >$13bn outflow risk) | https://www.bloomberg.com/news/articles/2026-01-29/goldman-sachs-downgrades-indonesian-stocks-after-msci-warning · https://jakartaglobe.id/business/ubs-goldman-cut-indonesia-equity-calls-after-msci-warning · https://www.idnfinancials.com/news/60860/goldman-and-ubs-cut-rating-on-indonesian-equities | News/Paywall (Bloomberg paywall; Jakarta Globe/IDNFinancials open) | 1 page (article) | News-event template — how to frame a downgrade call, risk box, flow math, MSCI contingency. Complement to PDF templates. | **P1** (anchor context) |

\* Scribd page counts estimated from viewer HTML; full PDF requires Scribd Pro.

---

## New sweep — ranked inventory (10+ additional sources)

| # | Bank | Ticker/Scope | URL | Access | Pages | Template Value | Priority |
|---|---|---|---|---|---|---|---|
| 1 | **CLSA** (CITIC CLSA) | **HRTA IJ** — *Fast growing gold proxy* (Hartadinata Abadi) | https://hartadinataabadi.co.id/download?filename=investor-report-file/8226/Indonesia-materials-(Fast-growing-gold-proxy)-20250515.pdf | **Yes** — direct PDF, `cloudflare`, verified 31 Aug 2026 | **9** (`pdfinfo`: Norman Choong, A4, 573.9 KB) | **Best P0 Indonesia single-name.** Clean CLSA disclaimer, PT CLSA Sekuritas Indonesia footer, materials/mining lens, DCF + multiples. Hosted on issuer IR (no paywall) — ideal to copy disclaimer/ratings/definitions block verbatim. | **P0** |
| 2 | **Bahana Sekuritas** (Daiwa-affiliated) | **Construction sector** — Indonesia Construction | https://adhi.co.id/wp-content/uploads/2025/09/RR-Bahana-Construction-Sector.pdf | **Yes** — direct PDF via ADHI IR | **19** (`pdfinfo`: Research Bahana 2025, Quartz PDFContext, 2.1 MB) | **Best sector report** — 19pp sector initiation, stock ratings based on absolute upside vs target price, sector valuation table. Longest downloadable Indonesia sector PDF in sweep. | **P0** |
| 3 | **DBS Group Research** (PT DBS Vickers Sekuritas Indonesia distributor) | **PGAS IJ** + Weekly — *Focus of the Week* (Perusahaan Gas Negara: "Downfall", HOLD / TP USD152.40) | https://www.dbs.com/content/article/pdf/CIO/2025/202506/250604EquitiesWeekly.pdf | **Yes** — direct PDF | **12** (`pdfinfo`: Christine WOO, Adobe Acrobat 25.1, 1.7 MB) | **Weekly format** includes "INDONESIA EQUITY RESEARCH" sub-section. Shows DBS house style: HOLD/BUY, TP cut, Indonesia distribution disclosure. Directly re-usable for any IDX energy name. | **P0** |
| 4 | **CGS International** (CGSI / ex-CGS-CIMB) | **DBS Group Holdings** — *Clarity behind its confidence for FY26F* (SGX, but Indonesia-distributed) | https://api2.sgx.com/sites/default/files/2026-05/300426%20CGSI%20-%20DBS%20Group%20Update%20-%20Clarity%20behind%20its%20confidence%20for%20FY26F.pdf | **Yes** — direct PDF via SGX | **11** (`pdfinfo`: Word for Microsoft 365, 417.3 KB) | Cross-border template: SGX report with **Indonesia distribution clause** ("PT CGS International Sekuritas Indonesia / CGS ID"). Shows how CGS handles dual-market disclaimer — replicate for IDX names. | **P0** |
| 5 | **BRI Danareksa Sekuritas (BRIDS)** | **Banking sector — 2M23 Banking, Maintain Overweight** | https://www.scribd.com/document/751952020/Danareksa-Equity-Research-2M23-Banking-5-Apr-2023-Maintain-Overweight | Scribd/Paywall | ~25* (Scribd) | Local champion banks template — BRIDS covers ~70% of IDX mkt cap. Sector-level Overweight call with peer comp table. Best **domestic** contrast to JPM/GS. | **P1** |
| 6 | **Bahana Sekuritas** | **Staple Retailers** — *Standing the Test of Time* (13 Nov 2025) | https://www.scribd.com/document/985262879/PT-Bahana-Securities-Research-Division-Standing-the-Test-of-Time-13-Nov-2025 | Scribd/Paywall | ~22* (Scribd) | Consumer staples sector initiation — selling space CAGR, box/sqm comps, staple retail valuation. Strong **local-global-like hybrid** structure. | **P1** |
| 7 | **UOB Kay Hian** | **Indonesia 2026 Market Strategy Overview** | https://www.scribd.com/document/969493800/UOB-Strategy | Scribd/Paywall | ~30* (Scribd) | Strategy overview with Indonesia stock table (e.g., ARCI BUY 1,290 → 2,050, +58.9%), OVERWEIGHT consumer, initiative/Village Coop Programme thesis. Good **table-heavy** template. | **P1** |
| 8 | **Maybank IBG** | **SGX SP** — *Volatility champion* (SGX Ltd) | https://mkefactsettd.maybank-ke.com/PDFS/465887.pdf | **Yes** — direct PDF | **11** (`pdfinfo`: Asa P. Fransson, Word 2016, 1.0 MB) | Singapore template with Maybank house header (Maybank IBG 3-yr manager disclosure). SGX name but **Maybank IBG Indonesia uses identical layout** — transferable to IDX banks. | **P1** |
| 9 | **DBS CIO** | **Global CIO Perspectives** (Sep 2025, includes Uber TP USD105.00 + gold TP upgrade to USD4,450/oz) | https://www.dbs.com/content/article/pdf/CIO/2025/202509/250908CIOP.pdf | **Yes** — direct PDF | **5** (`pdfinfo`: michelelee, Acrobat PDFMaker 25, 249.3 KB) | CIO house style — concise TP + rationale boxes (Uber BUY). Minimal but shows DBS **target price + rationale** micro-format. | **P1** |
| 10 | **IDX-hosted — HD LRE / HYGN** (local brokers, e.g., HD Capital / KGI-style) | **HYGN IJ** — Initiation (Target Rp190, +40.4% upside) | https://www.idx.co.id/Media/4hliohky/20240515-hd-lre-hygn-en.pdf | **CF 403** — Cloudflare-gated on curl (browser OK) | ~12–15 (est. from idx.co.id feed) | **IDX Official Research Report** template — the exchange-mandated equity research filing per `idx.co.id/en/listed-companies/equity-research-report/`. Required disclosure box; most "local" template. Fetch via browser, not curl. | **P1** |
| 11 | **KGI Sekuritas / IDX-hosted** | **BATR IJ** — *Resilient Demand Amid Revenue Decline 9M24* (Target Rp80, 10-yr projection table to 2033+TV) | https://www.idx.co.id/Media/wvajtd44/20241223-kgi-report-batr-en.pdf | **CF 403** | ~14–18 (est.) | Long-horizon DCF template — 2023A→2033F+TV projection table visible in search snippet. Rare **10-yr forecast** layout. | **P1** |
| 12 | **IDX-hosted — MKAP** | **MKAP IJ — 1Q24 Research Report** (Target Rp456, 20.2× PE; oil avg USD87) | https://www.idx.co.id/Media/041irh1j/mkap-research-report-1q24-pdf.pdf | **CF 403** | ~10–14 (est.) | Quarterly-results update template — "most concerns are priced in" narrative, 1Q24 snapshot. Matches Not Covered update cadence. | **P2** |
| 13 | **HSBC Global Investment Research** | **Portal + sample** — Global Investment Research (askResearch@hsbc.com) + HSBC ADR 23% undervalued narrow-moat sample | https://www.business.hsbc.com/en-gb/products/global-investment-research · https://www.scribd.com/document/472040185/HSBC-1 | Gated/Portal + Scribd/Paywall | Portal n/a; Scribd ~40* | HSBC house style (quant + moat). **No Indonesia single-name PDF found in open sweep** — portal shows Indonesia covered via PT Bank HSBC Indonesia / HSBC Securities, but reports are entitlement-only. Useful for HSBC disclaimer/ratings language. | **P2** |
| 14 | **Morgan Stanley** | **Indonesia — Asia Research Team** (Selvie Jusman) + General Research Disclosures | https://www.morganstanley.com/asiaresearch/country-and-region/indonesia.html · https://www.morganstanley.com/eqr/disclosures/webapp/generalresearch | Gated/Portal | n/a | **No open Indonesia PDF** surfaced. Page confirms active IB franchise since 2007. Disclosures page gives Morgan Stanley **Stock Ratings definitions** — harvest for disclaimer parity. | **P2** |
| 15 | **Credit Suisse / Nomura / Macquarie** (residual sweep) | Credit Suisse Netflix initiation sample (PT Credit Suisse Sekuritas Indonesia disclosure) · Nomura Spring 2025 Outlook (Scribd) · Macquarie Asia Equity Research portal | https://wsp-blog-images.s3.amazonaws.com/uploads/2020/11/16135219/Sample-Equity-Research-Report-CS-Inititation-on-Netflix.pdf · https://www.scribd.com/document/872125863/Nomura-Asset-Management-s-Spring-2025-Investment-Outlook-1749015769 · https://www.macquarie.com/us/en/about/company/macquarie-capital/macquarie-asia-equity-research.html | Yes (CS sample) / Scribd / Portal | CS sample 30+ pp | Negative result documented — sweep confirms **no open Indonesia single-name PDFs** from these three in public webSearch. CS sample still useful for Credit Suisse initiation layout; Macquarie Asia portal lists PT Macquarie Sekuritas Indonesia but gated. | **P2** |

## How to use (template variation guidance)

- **For the institutional report, clone structure from P0s first:** CLSA 9-pg (single-name compact) + Bahana 19-pg (sector) + DBS Weekly 12-pg (Indonesia sub-section) + CGSI 11-pg (cross-border disclaimer). Together they cover all disclaimer variants (PT CLSA Sekuritas Indonesia, PT DBS Vickers Sekuritas Indonesia, PT CGS International Sekuritas Indonesia).
- **Add domestic flavor from P1 Scribds:** Danareksa Banking Overweight + Bahana Retail + UOB Strategy — these show how local houses table comps and sector overweights (different from JPM's strategy deck).
- **IDX-hosted PDFs (10–12):** Download via browser (Cloudflare challenges curl). They are the mandated "Equity Research Report" filings — shortest, most regulator-facing template. Use to sanity-check required fields (Target Price, Recommendation, Market Cap, Shares Issued).
- **P2s:** Do not use as primary layout — harvest **ratings definitions & disclaimer language** only (HSBC askResearch, Morgan Stanley disclosures, CS sample).

## Verification log (31 Aug 2026)

```
curl -I CLSA HRTA            → 200 application/pdf (cloudflare)
curl -I DBS Weekly           → 200 application/pdf (cloudfront+cloudflare)
curl -I CGSI SGX             → 200 application/pdf (nginx, 427307 bytes)
curl -I DBS Sep CIO          → 200 application/pdf (HIT, 249KB)
curl -I Bahana ADHI          → 200 application/pdf (verified via pdfinfo 19p)
curl -I idx.co.id/*.pdf      → 403 text/html (CF_BM cookie required)
pdfinfo CLSA  = 9 pages / Norman Choong / 573.9K
pdfinfo Bahana= 19 pages / Research Bahana 2025 / 2.1M
pdfinfo DBS W = 12 pages / Christine WOO / 1.7M
pdfinfo CGSI  = 11 pages / Word 365 / 417.3K
pdfinfo Maybk = 11 pages / Asa P. Fransson / 1.0M
pdfinfo DBS Sep=5 pages / michelelee / 249.3K
```

## Next steps for Agent A/B

1. Bulk-download P0 PDFs to `references/pdfs/` (browser for idx.co.id if needed).
2. Extract 2–3 "ratings & target price" table crops for the design system.
3. Add CGS ID / DBS Vickers / CLSA Sekuritas disclaimer blocks to `disclaimer-template.md`.

---
*Generated by Agent C — no push performed (file write only).*
