# Report Data Contract — single JSON consumed by all 4 templates (T10)

> Status: LOCKED 31 Aug 2026. Renderer `scripts/render_pdf.py` + templates `templates/*.html` both read this.
> Sibling lanes produce pieces of this contract; the Renderer stitches them into one JSON before Jinja2 render.

## Why a single contract

4 templates (single/sotp/infra/strategy) share ~80% structure. One schema means: (a) template switch is a pure
function of `meta.template`, (b) Critic/QA can validate one contract instead of 4, (c) missing data degrades
gracefully via `{{ if }}` guards instead of crashing the render.

## Top-level shape

```jsonc
{
  "meta": {
    "template": "single|sotp|infra|strategy",     // chosen by scripts/select_template.py
    "reason": "segments=4 > 1 -> sotp",            // audit trail for the switch decision
    "ticker": "MTEL", "company_name": "Mitratel",
    "sector": "Telecommunication Infrastructure",
    "report_type": "Initiation",                    // LOCKED: Initiation only P0
    "date": "31 Agt 2026",                          // ID locale
    "prepared_by": "RESEARCH — Sectors Hackathon 2026",
    "language": "id"                                // LOCKED: ID default
  },
  "cover": {
    "rating_box": {"action": "BUY", "tp": 635, "prev_tp": 705, "price": 460, "upside_pct": 38.0,
                    "key_takeaways": ["...", "...", "..."]},   // takeaways: MTEL upgrade #11
    "vs_jci": {"ytd_abs": -30.9, "ytd_rel": -12.4, "chart": {"type": "line", "series": [...]}},
    "shares": {"outstanding": 81.5, "unit": "bn", "free_float_pct": 40.2},
    "shareholders": [{"name": "TLKM", "pct": 71.83}],           // pie
    "esg": {"found": true, "scores": {"e": 2.23, "s": 3.03, "g": 5.08}, "source": "...", "date": "..."} // found=false -> hide
  },
  "financial_highlights": {                          // 6Y table, A + F years
    "years": ["2023A", "2024A", "2025A", "2026F", "2027F", "2028F"],
    "rows": [{"label": "Pendapatan (Rp tn)", "values": [8.5, 9.1, 9.8, 10.2, 10.5, 10.7]}]
  },
  "segments": [                                      // >1 row => sotp/infra eligibility
    {"name": "Tower Leasing", "revenue": 3833, "yoy_pct": 1, "qoq_pct": 2, "share_pct": 49.2,
     "pie": true, "source": "MTEL 1H26 / IDX Financial Reports"}
  ],
  "kpis": [                                          // infra hero section
    {"name": "Tenancy Ratio", "value": 1.57, "prev": 1.53, "unit": "x",
     "formula": "tenant/tower", "source": "Company data"}
  ],
  "performance": {"quarterly_table": {...}, "narrative": "..."},
  "valuation": {
    "methods": [                                     // 1-3 methods, deterministic scripts only
      {"method": "DCF", "fv": 630, "assumptions": {"wacc": 10.1, "beta": 0.65, "rf": 6.96, "erp": 8.89,
        "coe": 12.74, "cod": 6.0, "we": 60.8, "wd": 39.2, "g": 1.5}, "table": {"rows": [...]},
       "source": "scripts/dcf.py"},
      {"method": "EV/EBITDA", "fv": 745, "multiple": 10, "source": "scripts/ev_ebitda.py"}
    ],
    "blended": {"weights": {"DCF": 60, "EV/EBITDA": 40}, "fv": 635, "margin_of_safety_pct": 15,
                 "weights_sum_100": true},            // Critic checks weights_sum_100 == true
    "bands": {"pbv_3y": {"std+2": 2.9, "std+1": 2.5, "avg": 2.1, "std-1": 1.7, "std-2": 1.3,
               "current": 1.47, "label": "BELOW AVG"}, "source": "scripts/bands.py"}
  },
  "financials": {"income": [...], "balance": [...], "cashflow": [...], "ratios": [...]},
  "risks": [{"bucket": "Ketergantungan Operator", "detail": "..."}],
  "peers": {"tables": [{"pillar": "Tower", "rows": [{"ticker": "TOWR", ...}]}]},
  "news": [{"title": "...", "url": "...", "date": "2026-08-28", "source": "Kontan", "tier": 1}],
  "sentiment": {"gauge": 62, "confidence": "medium", "top_narratives": [...],
                 "timeline": [...], "platforms": {"x": {...}, "reddit": {...}}},
  "strategy": {                                      // strategy template only (JPM overlay)
    "index_target": {"base": 9100, "bull": 10000, "bear": 7800, "eps_growth_pct": 8, "multiple": 15},
    "sectors": [{"name": "Industrials", "view": "OW"}],
    "flows": "...", "thematics": [...], "picks": [...]
  },
  "catalysts": [{"name": "PST & UMT Merger", "effect": "opex/capex efficiency",
                  "quantified": {"tenants": "+3,000-3,500", "revenue_idr_bn": "+360-420", "by": "FY27-29"}}],
  // HOUSE FORMAT (docs/rules/house-report-format.md):
  //   - NO "id": exhibit numbers come from the renderer's global figure counter, so a
  //     payload must never pre-number them. A hand-written "Exhibit 1" here is a
  //     local variable pretending to be a global counter and desyncs on any revision.
  //   - `source` is INTERNAL PROVENANCE (audit trail), NOT the printed line. The
  //     renderer stamps the visible "Source: Company, Team Estimates" under every
  //     object, without exception. Keep `source` populated for audit builds.
  //   - `title` is descriptive, never generic ("Chart"/"Table" is a REJECT).
  "exhibits": [{"title": "Revenue and Revenue Growth (2024A-2028F)",
                 "chart": {"type": "line|bar|pie|doughnut",
                 "series": [...]}, "source": "SKK Migas, data diolah"}],
  "disclaimer": {"text": "<OJK boilerplate from disclaimer-template.md, ID locale>"}
}
```

## Template switch (task item 2)

```
select_template(report_data):
    if meta.report_kind == "strategy":            return "strategy"   # explicit overlay (JPM)
    segments = report_data.get("segments") or []
    if len(segments) > 1:                          return "sotp"
    subsector = (report_data.get("meta.subsector") or "").lower()
    if any(k in subsector for k in ("infra", "telco", "tower", "fiber", "toll")): return "infra"
    return "single"
```

Priority note: `segments>1` wins over infra (CDIA-style conglomerates with segments + 4 pillar peer tables need
SOTP layout even if they sit in an infra subsector). `strategy` is never auto-selected — it is passed explicitly
by the orchestrator for market-level reports (JPM overlay).

## Section inventories (task item 1 — "9-10 sections adaptive")

| # | Section (single) | sotp delta | infra delta | strategy (all different) |
|---|---|---|---|---|
| 1 | Cover + Rating Box | + shareholder pie | + Key Takeaways + ESG box | Cover: index target bull/base/bear + methodology box |
| 2 | Price vs JCI + Summary | same | same | Investment Summary |
| 3 | Thesis (4 narasi) | + segment growth | + catalyst quantified | Lessons / 5 Thematics |
| 4 | Valuation DCF + 2nd method | DCF+DDM + 4 pillar peer tables | + blended 60/40 + bands | Sector OW/N/UW + picks |
| 5 | Operational KPI (per subsector) | same | HERO: tenancy/fiber table | — |
| 6 | Segments | full segment table | + QoQ + YoY | — |
| 7 | Financials 6Y + ratios | same | same | Economics per sector |
| 8 | Risks buckets | pillar-specific | infra-specific | Flows/MSCI + Danantara |
| 9 | Exhibits (charts, auto-numbered, house source line) | same | same | 60+ exhibits paginated |
| 10 | Disclaimer OJK | same | same | Disclosures |

Every exhibit row carries `source` as **internal provenance** (audit trail) — render aborts
(fail-loud) if any exhibit lacks one. That field is never printed: the visible line under
every object is always `Source: Company, Team Estimates` (house format §1).

## Validation rules enforced by renderer pre-flight

1. `valuation.blended.weights` sums to 100 (Critic rule from plan §3).
2. Every `exhibits[*]` has non-empty `source` (internal provenance) and must NOT carry a
   pre-numbered `id` — exhibit numbers are owned by the renderer's global counter.
3. `segments[*].share_pct` sums to 100 ± 0.5 when >1 segment (else template must hide the pie).
4. `rating_box.upside_pct == round((tp - price) / price * 100, 1)` (deterministic recompute, abort on mismatch).
5. `news[*]` has url + date; `sentiment.gauge` in 0..100.
6. ESG: `found=false` → hide box entirely (LOCKED decision — no fabricated scores).
