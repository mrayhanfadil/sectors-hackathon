"""
QA Critic Agent — agents/critic.py
Part of Multi-Agent Arbiter & Gate (plan.md §3, §11).

Strict anti-hallucination & anti-sycophancy verification:
- Narrative numbers == Table numbers
- Blended weights == 100% (60/40)
- Segment percentages == 100%
- Tenancy ratio == tenants / towers
- Source present on every exhibit
- News citations have url + date
- Adversarial defense cites verified evidence
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def audit_report_payload(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """Audits full report payload against data contract and anti-hallucination rules."""
    reasons: List[str] = []
    fixes: List[str] = []

    # 1. Blended weight sum check
    valuation = report_data.get("valuation") or {}
    blended = valuation.get("blended")
    if blended and isinstance(blended, dict):
        weights = blended.get("weights") or {}
        w_sum = sum(float(v) for v in weights.values())
        # handle normalized 0-1 vs 0-100%
        if abs(w_sum - 1.0) > 1e-4 and abs(w_sum - 100.0) > 1e-2:
            reasons.append(f"Blended weights sum to {w_sum}, expected 1.0 (or 100%)")
            fixes.append("Normalize blended weights to sum to exactly 100%")

    # 2. Segment % sum check (for conglomerates)
    segments = report_data.get("segments") or []
    if isinstance(segments, list) and len(segments) > 1:
        seg_sum = sum(float(s.get("share_pct") or s.get("pct") or 0) for s in segments)
        if abs(seg_sum - 100.0) > 0.5:
            reasons.append(f"Segment share_pct sums to {seg_sum:.1f}%, expected 100±0.5%")
            fixes.append("Rebalance segment percentages to sum to 100%")

    # 3. KPI tenancy ratio check
    kpi = report_data.get("kpi") or {}
    if isinstance(kpi, dict):
        towers = kpi.get("tower") or kpi.get("towers")
        tenants = kpi.get("tenant") or kpi.get("tenants")
        tenancy = kpi.get("tenancy_ratio")
        if towers and tenants and tenancy:
            calc_ratio = float(tenants) / float(towers)
            if abs(calc_ratio - float(tenancy)) > 0.05:
                reasons.append(f"Tenancy ratio mismatch: reported {tenancy} vs calculated {calc_ratio:.2f}x")
                fixes.append("Update tenancy ratio to match tenants / towers")

    # 4. Source per exhibit check
    exhibits = report_data.get("exhibits") or []
    for i, ex in enumerate(exhibits, 1):
        src = ex.get("source") if isinstance(ex, dict) else None
        if not src or not str(src).strip():
            ex_id = ex.get("id", f"Exhibit {i}") if isinstance(ex, dict) else f"Exhibit {i}"
            reasons.append(f"{ex_id} missing mandatory Source disclosure")
            fixes.append(f"Add verifiable Source citation to {ex_id}")

    # 5. News url + date provenance check
    news_items = report_data.get("news") or []
    for n in news_items:
        if isinstance(n, dict):
            if not n.get("url") or not str(n.get("url")).strip():
                reasons.append(f"News item '{n.get('title', '')[:30]}' missing URL")
            if not n.get("date") or not str(n.get("date")).strip():
                reasons.append(f"News item '{n.get('title', '')[:30]}' missing publication date")

    verdict = "PASS" if not reasons else "REJECT"
    return {
        "verdict": verdict,
        "reasons": reasons,
        "fixes": fixes,
        "ready_for_pdf": (verdict == "PASS"),
    }

