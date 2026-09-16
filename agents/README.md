# T08 Agent Contracts - Writer / Visualizer / SOTP Aggregator

Status: v1 (31 Aug 2026) - owned by branch `wt/t08-writer` off `feat/institutional-report`.

These three agents are the **narrative + visual + aggregation layer** of the pipeline
(downstream of Data Collector T01 and Financial Modeler T02; upstream of the PDF
Renderer P4). They are **pure functions of a deterministic input JSON** - no LLM math,
no network I/O, no credit spend. Every number they emit must already exist in the input
or be computed by the deterministic engines in `scripts/` (T02).

## File map

| File | Role | I/O |
|---|---|---|
| `agents/common.py` | Shared: load company.json, source labels, exhibit registry, rounding, JSON write | - |
| `agents/writer.py` | Thesis Writer | `company.json` → `out/<ticker>/thesis.json` + `thesis.md` |
| `agents/visualizer.py` | Visualizer | `company.json` + `out/<ticker>/financials.json` (optional) → `out/<ticker>/charts/*.png` + `charts.json` manifest |
| `agents/sotp.py` | SOTP Aggregator (conglomerate only) | `company.json` (segments>1) → `out/<ticker>/sotp.json` |
| `templates/helpers.py` | Exhibit format helpers for the PDF renderer (P4) | import-time, pure |
| `tests/fixtures/company/*.json` | Deterministic fixtures: CDIA (sotp), MTEL (infra), ADRO (sotp+holdco) | - |
| `tests/run_tests.py` | Deterministic acceptance asserts (no pytest dependency) | - |

## Canonical input schema - `company.json`

T01 Collector writes one file per ticker. Required keys for these agents:

```jsonc
{
  "ticker": "CDIA",
  "name": "Citra Nusantara Gemilang",
  "archetype": "sotp" | "infra" | "single",          // collector/modeler decides
  "currency": "IDR",
  "units": "mn",
  "price": 152.0,                                     // last close
  "shares_outstanding_mn": 4704.0,
  "market_cap_mn": 715008.0,                          // price × shares (may be supplied)
  "date": "2026-06-23",
  "source": {"primary": "idx", "label": "IDX / company filings, data as of 23 Jun 2026"},
  "segments": [                                       // REQUIRED if archetype=sotp (≥2)
    {"pillar": "Energy",    "revenue_mn": 25300000.0, "pct": 55.0, "growth_yoy": 0.15,  "peer_avg_pe": 9.0,  "peer_avg_ev_ebitda": 6.5,  "peer_set": "POWR, BREN, Sembcorp"},
    {"pillar": "Logistics", "revenue_mn": 15640000.0, "pct": 34.0, "growth_yoy": 0.447, "peer_avg_pe": 11.5, "peer_avg_ev_ebitda": 8.0,  "peer_set": "HATM, ASSA, Westports"},
    {"pillar": "Water",     "revenue_mn": 3680000.0,  "pct": 8.0,  "growth_yoy": 0.05,  "peer_avg_pe": 12.0, "peer_avg_ev_ebitda": 9.0,  "peer_set": "ACWA, PAM, Sembcorp"},
    {"pillar": "Port",      "revenue_mn": 1380000.0,  "pct": 3.0,  "growth_yoy": 0.06,  "peer_avg_pe": 10.0, "peer_avg_ev_ebitda": 7.5,  "peer_set": "PGAS, Westports, MDRN"}
  ],
  "one_offs": {                                       // one-off / non-recurring items (IDR mn)
    "description": "impairment + legal provision (BCA Sekuritas normalization)",
    "items": [{"label": "impairment", "amount_mn": 10000.0}, {"label": "legal provision", "amount_mn": 5900.0}],
    "reported_net_income_mn": 12000.0,                // as-reported net income
    "tax_rate": 0.22
  },
  "financials": {                                     // T02 modeler output; visualizer uses it
    "years": ["2024A", "2025A", "2026F"],
    "revenue_mn": [54000000.0, 46000000.0, 47000000.0],
    "ebitda_mn":  [17000000.0, 12500000.0, 13000000.0],
    "net_income_mn": [16000000.0, 12000000.0, 3360.0],
    "roe":    [0.34, 0.24, 0.065],
    "roa":    [0.09, 0.06, 0.017],
    "gearing_pct":      [140.0, 170.0, 160.0],
    "debt_ebitda":      [11.0, 18.0, 15.0],
    "current_ratio":    [0.3, 0.35, 0.8],
    "gross_margin":     [0.30, 0.27, 0.28],
    "ebitda_margin":    [0.31, 0.27, 0.28],
    "net_margin":       [0.30, 0.26, 0.07],
    "eps_mn": ...
  },
  "kpi": {                                            // subsector-specific hero KPIs
    "tenants": 63866, "towers": 40563, "tenancy_ratio": 1.57,
    "fiber_km": 59239, "colocation": 23303
  },
  "catalysts": [{
    "id": "MTEL-PST-UMT",
    "title": "PST & UMT merger + 700MHz/2.6GHz spectrum",
    "date": "2026-07-01",
    "type": "merger|spectrum|policy",
    "quantified": {"tenants_added_min": 3000, "tenants_added_max": 3500,
                   "annualized_revenue_min_mn": 360000.0, "annualized_revenue_max_mn": 420000.0,
                   "by_fy": "FY27-29"},
    "status": "pending", "source": "KSI Research 27 Aug 2026; TLKM spectrum allocation"
  }],
  "price_history": {"jci": {"dates": [...], "close": [...]}, "ticker": {"dates": [...], "close": [...]}, "ytd_perf": {...}},
  "peers": [{"ticker": "POWR", "name": "...", "pe": 8.5, "ev_ebitda": 6.2, "sector": "Energy"}],
  "bands": {"pbv": {"dates": [...], "values": [...], "mean": 1.7, "std": 0.3}, "ev_ebitda": {...}},
  "esg": {"source": "MSCI", "date": "2026-08-01", "score": "2.23/3.03/5.08"}   // optional - hide if absent
}
```

**Anti-hallucination rule:** any number rendered in `thesis.json` / charts / SOTP must
trace to a key in `company.json` (or a `scripts/` engine result) - writers never invent.

## Output schemas

### `out/<ticker>/thesis.json`
```jsonc
{
  "ticker": "CDIA",
  "bull_case": {
    "title": "...", "headline": "one line with the hard numbers",
    "arguments": [{"id": "T1", "point": "...", "evidence": {"metric": "...", "value": ..., "source": "..."}}],
    "catalysts": [{"id": "...", "title": "...", "date": "...", "quantified": {...}, "source": "..."}]
  },
  "normalizations": [{"label": "impairment", "amount_mn": ..., "impact_pct": ...}],
  "adjusted": {"reported_net_income_mn": ..., "adjusted_net_income_mn": ..., "delta_pct": -72.0, "method": "..."},
  "risks": [{"id": "R1", "title": "...", "detail": "...", "severity": "high"}],
  "kpi_highlights": [{"kpi": "tenancy_ratio", "value": 1.57, "source": "..."}],
  "meta": {"generated_at": "...", "engine": "writer.py v1", "sources": [...]}
}
```

### `out/<ticker>/charts.json` (manifest)
```jsonc
{"ticker": "CDIA", "charts": [{"id": "revenue_mix", "file": "charts/revenue_mix.png", "title": "...", "kind": "pie", "source": "..."}], "total": 8}
```

### `out/<ticker>/sotp.json`
```jsonc
{
  "ticker": "CDIA", "conglomerate": true,
  "pillars": [{"pillar": "Energy", "revenue_mn": ..., "pct": ..., "peer_avg_pe": ..., "implied_equity_mn": ..., "weight_pct": ...}],
  "holdco_discount_pct": 0.15, "pre_discount_total_mn": ..., "post_discount_equity_mn": ...,
  "sum_check": {"pct_sum": 100.0, "ok": true, "equity_total_pct": 100.0},
  "method": "peer-avg per pillar (SOTP), sum of parts = 100% before holdco discount"
}
```

## Acceptance (must pass `tests/run_tests.py`)

1. Thesis writer emits CDIA normalized net delta **-72%** from the 15.9 one-off → `adjusted_net_income_mn = 4,823mn` (reported 17,225 − 15,900×(1−22%)), Δ = −72.0%.
2. Catalyst quantified: MTEL PST+UMT merger 1 Jul 2026 + spectrum → **3,000–3,500 tenants** and **IDR 360,000–420,000 mn (+360–420bn)** annualized by FY27-29, both present in thesis output.
3. SOTP: segments pct **sum to 100%**; pillar weights sum to **100%**; `sum_check.ok == true`; holdco discount applied. **Conglomerate-only** - archetype must be `sotp` (CDIA/ADRO); MTEL (infra) is skipped with a non-conglomerate reason.
4. Visualizer emits exactly the 8 mandated PNGs (revenue mix pie, trend, margin, leverage, ROE/ROA, vs JCI, peer multiples + bands, KPI) with a `charts.json` manifest; infra (MTEL) additionally gets a bands chart.
5. Every chart file exists, non-empty, and is a valid PNG (`\x89PNG` magic).
