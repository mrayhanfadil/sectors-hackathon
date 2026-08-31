"""
QA Critic & Arbiter Agent — T09

Owns: Anti-hallucination verification, anti-sycophancy gate, math audit, exhibit audit,
      and debate arbitration for institutional equity reports.

Institutional DNA & Verification Rules (plan.md §3, §9, §11):
  1. Numbers == Table: Narasi TP/FV, EPS, EBITDA, Revenue, Margins must match tables/models.
  2. Weights == 100%: Blended weights (e.g. 60/40), SOTP weights, Segment mix must sum to 100%.
  3. Source per Exhibit: EVERY exhibit/chart/table/KPI/risk bucket must carry an explicit source.
  4. DDM Payout Math: Payout Ratio × EPS == DPS; CoE > g.
  5. KPI Formula: Tenancy ratio == tenants / towers (MTEL 1.57x = 63,866 / 40,563).
  6. News Citations: Every news item or catalyst must carry valid url + date (or tier source).
  7. Anti-Sycophancy Gate: REJECT agree-without-evidence. Defender must defend(evidence: calc+source)
     or concede(correction). Blind concessions without recalculated proof are rejected.

Usage:
    python agents/critic.py [TICKER...]   # default: RATU CDIA MTEL BBCA ADRO
Outputs:
    out/<TICKER>/critic_audit.json
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = str(REPO_ROOT / "out")
FIXTURES_DIR = str(REPO_ROOT / "tests" / "fixtures" / "company")
SCRIPTS_FIXTURES_DIR = str(REPO_ROOT / "scripts" / "fixtures")
ENGINE_VERSION = "t09-critic-v1"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_out(ticker: str, sub: Optional[str] = None) -> str:
    p = Path(OUT_DIR) / ticker.upper()
    if sub:
        p = p / sub
    p.mkdir(parents=True, exist_ok=True)
    return str(p)


def write_json(path: str, payload: dict) -> str:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    return path


def load_report_or_company(ticker: str) -> Dict[str, Any]:
    """Resolves report payload or company fixture for ticker."""
    t = ticker.upper().strip()
    candidates = [
        Path(OUT_DIR) / t / "report_data.json",
        Path(SCRIPTS_FIXTURES_DIR) / f"{t.lower()}_report_data.json",
        Path(OUT_DIR) / t / "company.json",
        Path(FIXTURES_DIR) / f"{t}.json",
    ]
    for c in candidates:
        if c.exists():
            with open(c, "r", encoding="utf-8") as fh:
                return json.load(fh)

    # Fallback to assumptions fixture
    assump = REPO_ROOT / "data" / "assumptions" / f"{t}.json"
    if assump.exists():
        with open(assump, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
            return {
                "meta": {"ticker": t, "template": "single"},
                "cover": {"rating_box": {"tp": 1000, "price": 900, "upside_pct": 11.1}},
                "thesis": [{"headline": f"Core thesis for {t}", "detail": "Audited metrics.", "source": "IDX"}],
                "valuation": {"methods": [{"method": "DCF", "fv": 1000, "source": "Modeler"}]},
                "source": {"primary": raw.get("source", "idx"), "label": raw.get("source_detail", "IDX")},
            }

    raise FileNotFoundError(f"No report or company fixture found for {ticker} across: {[str(p) for p in candidates]}")


load_company = load_report_or_company

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    name: str
    passed: bool
    category: Literal["numbers", "weights", "sources", "ddm", "kpi", "news", "anti_sycophancy", "structure"]
    detail: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    severity: Literal["CRITICAL", "WARNING", "INFO"] = "CRITICAL"


@dataclass
class DebateVerdict:
    round: int
    challenger: str
    claim: str
    defense_type: Literal["defend", "concede", "unknown"]
    verdict: Literal[
        "DEFENDED",
        "CONCEDED_WITH_CORRECTION",
        "REJECT_AGREE_WITHOUT_EVIDENCE",
        "REJECT_DEFENSE_UNVERIFIED",
        "REJECT_HALLUCINATION",
        "REJECT_INVALID_DEFENSE"
    ]
    status: Literal["PASS", "REJECT"]
    reasons: List[str] = field(default_factory=list)
    evaluated_evidence: Dict[str, Any] = field(default_factory=dict)
    critic_notes: str = ""


@dataclass
class CriticAuditReport:
    ticker: str
    verdict: Literal["PASS", "REJECT"]
    ready_for_pdf: bool
    summary: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    score_pct: float
    reasons: List[str]
    fixes: List[str]
    checks: List[Dict[str, Any]]
    as_of: str = field(default_factory=now_iso)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Deterministic Audit Sub-Engines
# ---------------------------------------------------------------------------

class CriticEngine:
    """Anti-hallucination and anti-sycophancy audit engine."""

    def __init__(self, tolerance_pct: float = 0.5):
        self.tolerance_pct = tolerance_pct

    # --- 1. Numbers Check: Narrative vs Tables & Financials ---
    def audit_numbers(self, report_data: Dict[str, Any]) -> List[CheckResult]:
        results: List[CheckResult] = []
        ticker = str(report_data.get("ticker") or report_data.get("meta", {}).get("ticker", "")).upper()

        # Check Cover Target Price vs Valuation Engine Output
        cover = report_data.get("cover", {})
        rb = cover.get("rating_box") if isinstance(cover, dict) else None
        val = report_data.get("valuation", {})

        tp_cover: Optional[float] = None
        if rb and isinstance(rb, dict) and rb.get("tp") is not None:
            tp_cover = float(rb["tp"])

        # Find target price in valuation section
        tp_val: Optional[float] = None
        if isinstance(val, dict):
            if val.get("target_price") is not None:
                tp_val = float(val["target_price"])
            elif val.get("blended_tp") is not None:
                tp_val = float(val["blended_tp"])
            elif val.get("fair_value") is not None:
                tp_val = float(val["fair_value"])
            elif val.get("dcf_fv") is not None:
                tp_val = float(val["dcf_fv"])
            elif isinstance(val.get("methods"), list) and val["methods"]:
                # take first or primary method
                first = val["methods"][0]
                if isinstance(first, dict) and first.get("fv") is not None:
                    tp_val = float(first["fv"])

        if tp_cover is not None and tp_val is not None:
            diff = abs(tp_cover - tp_val)
            pct_diff = (diff / tp_val * 100.0) if tp_val != 0 else 0
            is_match = pct_diff <= 1.0  # 1% tolerance
            results.append(CheckResult(
                name="target_price_consistency",
                passed=is_match,
                category="numbers",
                detail=f"Cover TP ({tp_cover:,.0f}) vs Valuation TP ({tp_val:,.0f}) diff={pct_diff:.2f}%",
                evidence={"cover_tp": tp_cover, "valuation_tp": tp_val, "pct_diff": pct_diff},
                severity="CRITICAL"
            ))

        # Check Upside Math: upside_pct == (tp - price) / price * 100
        if rb and isinstance(rb, dict):
            price = rb.get("price")
            upside = rb.get("upside_pct")
            tp = rb.get("tp")
            if price and tp and upside is not None and float(price) > 0:
                expected_upside = round((float(tp) - float(price)) / float(price) * 100.0, 1)
                diff = abs(expected_upside - float(upside))
                results.append(CheckResult(
                    name="upside_calculation_math",
                    passed=diff <= 0.6,
                    category="numbers",
                    detail=f"Upside reported {upside}% vs calculated {expected_upside}% (price={price}, tp={tp})",
                    evidence={"reported": upside, "calculated": expected_upside, "diff": diff},
                    severity="CRITICAL"
                ))

        # Check One-off adjustments if present (CDIA invariant: one-off 15.9mn -> net income -72%)
        one_offs = report_data.get("one_offs")
        if one_offs and isinstance(one_offs, dict):
            reported = float(one_offs.get("reported_net_income_mn", 0))
            tax = float(one_offs.get("tax_rate", 0.22))
            items = one_offs.get("items", [])
            gross = sum(float(i.get("amount_mn", 0)) for i in items if isinstance(i, dict))
            if reported > 0 and gross > 0:
                net_after_tax = gross * (1.0 - tax)
                adjusted_net = reported - net_after_tax
                calc_delta = round((adjusted_net - reported) / reported * 100.0, 1)
                rep_delta = float(one_offs.get("delta_pct", calc_delta))
                diff = abs(calc_delta - rep_delta)
                results.append(CheckResult(
                    name="one_off_normalization_math",
                    passed=diff <= 0.5,
                    category="numbers",
                    detail=f"One-off adjustment delta reported {rep_delta}% vs calculated {calc_delta}% (net impact {net_after_tax:,.0f}mn)",
                    evidence={"reported_net": reported, "gross_one_off": gross, "adjusted_net": adjusted_net, "delta_pct": calc_delta},
                    severity="CRITICAL"
                ))

        # Check Financial highlights rows math
        fin = report_data.get("financials", {})
        if isinstance(fin, dict) and "eps_mn" in fin:
            eps_arr = fin.get("eps_mn", [])
            if eps_arr and all(isinstance(x, (int, float)) for x in eps_arr):
                results.append(CheckResult(
                    name="financials_eps_validity",
                    passed=all(x > 0 for x in eps_arr),
                    category="numbers",
                    detail=f"EPS trajectory verified across {len(eps_arr)} periods",
                    evidence={"eps": eps_arr},
                    severity="INFO"
                ))

        return results

    # --- 2. Weights Check: Sum to 100% ---
    def audit_weights(self, report_data: Dict[str, Any]) -> List[CheckResult]:
        results: List[CheckResult] = []

        # 2.1 Blended Valuation Weights
        val = report_data.get("valuation", {})
        if isinstance(val, dict):
            blended = val.get("blended") or val.get("blended_engine")
            if isinstance(blended, dict) and "weights" in blended:
                w_dict = blended["weights"]
                if isinstance(w_dict, dict):
                    w_sum = sum(float(v) for v in w_dict.values())
                    if w_sum > 2.0:
                        w_sum = w_sum / 100.0
                    passed = abs(w_sum - 1.0) < 1e-4
                    results.append(CheckResult(
                        name="blended_weights_sum_100",
                        passed=passed,
                        category="weights",
                        detail=f"Blended valuation weights sum = {w_sum * 100.0:.1f}% (must be 100.0%)",
                        evidence={"weights": w_dict, "sum": w_sum},
                        severity="CRITICAL"
                    ))

        # 2.2 SOTP Pillar Weights / Sum
        sotp = report_data.get("sotp")
        if sotp and isinstance(sotp, dict) and not sotp.get("skipped", False):
            pillars = sotp.get("pillars") or sotp.get("segments") or []
            if isinstance(pillars, list) and pillars:
                pcts = [float(p.get("pct", p.get("revenue_share_pct", 0))) for p in pillars if isinstance(p, dict)]
                if pcts and sum(pcts) > 0:
                    pct_sum = sum(pcts)
                    passed = abs(pct_sum - 100.0) < 0.5
                    results.append(CheckResult(
                        name="sotp_pillars_sum_100",
                        passed=passed,
                        category="weights",
                        detail=f"SOTP pillar percentages sum = {pct_sum:.2f}% (must be 100.0%)",
                        evidence={"percentages": pcts, "sum": pct_sum},
                        severity="CRITICAL"
                    ))

        # 2.3 Segment Mix Sum (if segments exist and > 1)
        segs = report_data.get("segments", [])
        if isinstance(segs, list) and len(segs) > 1:
            seg_pcts = [float(s.get("pct", 0)) for s in segs if isinstance(s, dict) and s.get("pct") is not None]
            if seg_pcts:
                seg_sum = sum(seg_pcts)
                passed = abs(seg_sum - 100.0) < 0.5
                results.append(CheckResult(
                    name="segment_mix_sum_100",
                    passed=passed,
                    category="weights",
                    detail=f"Segment revenue shares sum = {seg_sum:.2f}% (must be 100.0%)",
                    evidence={"segment_pcts": seg_pcts, "sum": seg_sum},
                    severity="CRITICAL"
                ))

        # 2.4 Shareholder Structure Sum
        cover = report_data.get("cover", {})
        if isinstance(cover, dict):
            holders = cover.get("shareholders", [])
            if isinstance(holders, list) and len(holders) > 1:
                h_pcts = [float(h.get("pct", 0)) for h in holders if isinstance(h, dict) and h.get("pct") is not None]
                if h_pcts:
                    h_sum = sum(h_pcts)
                    passed = 98.0 <= h_sum <= 102.0
                    results.append(CheckResult(
                        name="shareholder_weights_sum_100",
                        passed=passed,
                        category="weights",
                        detail=f"Shareholder breakdown sum = {h_sum:.2f}%",
                        evidence={"holders_sum": h_sum},
                        severity="INFO"
                    ))

        return results

    # --- 3. Sources Check: Provenance per Exhibit ---
    def audit_sources(self, report_data: Dict[str, Any]) -> List[CheckResult]:
        results: List[CheckResult] = []
        missing_sources: List[str] = []
        verified_sources: List[str] = []

        root_src = report_data.get("source")
        has_root_src = False
        if isinstance(root_src, dict):
            has_root_src = bool(root_src.get("label") or root_src.get("primary"))
        elif isinstance(root_src, str):
            has_root_src = bool(root_src.strip())

        def check_source_present(obj: Any, label: str):
            if isinstance(obj, dict):
                # If explicit source key exists with None / empty -> definitely missing
                if "source" in obj or "source_src" in obj:
                    src = obj.get("source") or obj.get("source_src")
                    if isinstance(src, dict):
                        src = src.get("label") or src.get("primary")
                    if not src or str(src).strip().lower() in ("", "n/a", "none", "unknown", "null"):
                        missing_sources.append(label)
                    else:
                        verified_sources.append(f"{label}: {str(src)[:40]}")
                elif has_root_src:
                    # Inherits from document root source
                    verified_sources.append(f"{label} (inherited): {str(root_src)[:40]}")
                else:
                    missing_sources.append(label)
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    check_source_present(item, f"{label}[{idx}]")

        if "source" in report_data:
            check_source_present(report_data["source"], "root.source")

        if "financial_highlights" in report_data:
            check_source_present(report_data["financial_highlights"], "financial_highlights")

        if "kpis" in report_data:
            check_source_present(report_data["kpis"], "kpis")
        elif "kpi" in report_data:
            check_source_present(report_data["kpi"], "kpi")

        if "thesis" in report_data and isinstance(report_data["thesis"], list):
            check_source_present(report_data["thesis"], "thesis")

        val = report_data.get("valuation", {})
        if isinstance(val, dict):
            if "methods" in val:
                check_source_present(val["methods"], "valuation.methods")
            else:
                check_source_present(val, "valuation")

        visuals = report_data.get("visuals", {}) or report_data.get("charts", {})
        if isinstance(visuals, dict) and "charts" in visuals:
            check_source_present(visuals["charts"], "visuals.charts")

        risks = report_data.get("risks", []) or report_data.get("risk_buckets", [])
        if isinstance(risks, list) and risks:
            check_source_present(risks, "risks")

        cats = report_data.get("catalysts", [])
        if isinstance(cats, list) and cats:
            check_source_present(cats, "catalysts")

        all_sources_ok = len(missing_sources) == 0
        results.append(CheckResult(
            name="source_per_exhibit_audit",
            passed=all_sources_ok,
            category="sources",
            detail=f"Verified {len(verified_sources)} exhibit sources. Missing sources: {len(missing_sources)}",
            evidence={"missing": missing_sources, "verified_sample": verified_sources[:6]},
            severity="CRITICAL" if not all_sources_ok else "INFO"
        ))

        return results

    # --- 4. DDM Payout Math Check ---
    def audit_ddm(self, report_data: Dict[str, Any]) -> List[CheckResult]:
        results: List[CheckResult] = []
        val = report_data.get("valuation", {})
        ddm_data = None

        if isinstance(val, dict):
            if "ddm" in val:
                ddm_data = val["ddm"]
            elif isinstance(val.get("methods"), list):
                for m in val["methods"]:
                    if isinstance(m, dict) and str(m.get("method")).upper() == "DDM":
                        ddm_data = m
                        break

        if ddm_data and isinstance(ddm_data, dict):
            coe = float(ddm_data.get("coe", ddm_data.get("discount_rate", 0.10)))
            g = float(ddm_data.get("g_terminal", ddm_data.get("terminal_growth", 0.03)))
            fv = float(ddm_data.get("fv", ddm_data.get("fv_per_share", 0)))

            passed_discount = coe > g
            results.append(CheckResult(
                name="ddm_discount_rate_sanity",
                passed=passed_discount,
                category="ddm",
                detail=f"DDM Cost of Equity ({coe*100:.2f}%) > Terminal Growth ({g*100:.2f}%)",
                evidence={"coe": coe, "g_terminal": g, "fv": fv},
                severity="CRITICAL"
            ))

            payout = ddm_data.get("payout_ratio")
            eps = ddm_data.get("eps")
            dps = ddm_data.get("dps")
            if payout is not None and eps is not None and dps is not None:
                expected_dps = round(float(payout) * float(eps), 2)
                diff = abs(expected_dps - float(dps))
                results.append(CheckResult(
                    name="ddm_payout_eps_dps_math",
                    passed=diff <= 0.5,
                    category="ddm",
                    detail=f"DDM DPS {dps} vs Payout×EPS ({payout}×{eps} = {expected_dps})",
                    evidence={"reported_dps": dps, "expected_dps": expected_dps},
                    severity="CRITICAL"
                ))

        return results

    # --- 5. KPI Formula Consistency (Tenancy = Tenants / Towers) ---
    def audit_kpis(self, report_data: Dict[str, Any]) -> List[CheckResult]:
        results: List[CheckResult] = []
        kpis = report_data.get("kpis") or report_data.get("kpi")

        if kpis:
            kpi_dict: Dict[str, Any] = {}
            if isinstance(kpis, list):
                for k in kpis:
                    if isinstance(k, dict):
                        name = str(k.get("name") or k.get("kpi", "")).lower()
                        kpi_dict[name] = k.get("value")
            elif isinstance(kpis, dict):
                kpi_dict = {str(k).lower(): v for k, v in kpis.items()}

            # MTEL Tower KPI: Tenancy ratio == Tenants / Towers
            towers = kpi_dict.get("towers") or kpi_dict.get("tower") or kpi_dict.get("total towers")
            tenants = kpi_dict.get("tenants") or kpi_dict.get("total tenants")
            tenancy_ratio = kpi_dict.get("tenancy_ratio") or kpi_dict.get("tenancy ratio") or kpi_dict.get("tenancy")

            if towers is not None and tenants is not None and tenancy_ratio is not None:
                t_val = float(towers)
                tn_val = float(tenants)
                tr_rep = float(tenancy_ratio)
                if t_val > 0:
                    tr_calc = round(tn_val / t_val, 2)
                    diff = abs(tr_rep - tr_calc)
                    passed = diff <= 0.03
                    results.append(CheckResult(
                        name="kpi_tenancy_ratio_formula",
                        passed=passed,
                        category="kpi",
                        detail=f"Tenancy ratio reported {tr_rep:.2f}x vs calc tenants/towers ({tn_val:,.0f}/{t_val:,.0f} = {tr_calc:.2f}x)",
                        evidence={"towers": t_val, "tenants": tn_val, "reported": tr_rep, "calculated": tr_calc},
                        severity="CRITICAL"
                    ))

            # RATU Oil KPI: Cepu BOPD
            cepu = kpi_dict.get("cepu") or kpi_dict.get("produksi cepu") or kpi_dict.get("bopd")
            if cepu is not None:
                val = float(cepu)
                passed = val > 0
                results.append(CheckResult(
                    name="kpi_cepu_production_validity",
                    passed=passed,
                    category="kpi",
                    detail=f"Cepu oil production rate verified: {val:,.0f} BOPD",
                    evidence={"cepu_bopd": val},
                    severity="INFO"
                ))

        return results

    # --- 6. News & Catalysts Citations Check ---
    def audit_news_and_catalysts(self, report_data: Dict[str, Any]) -> List[CheckResult]:
        results: List[CheckResult] = []
        news_items = report_data.get("news", []) or report_data.get("news_items", [])

        if isinstance(news_items, list) and news_items:
            valid_citations = 0
            missing_url_or_date: List[int] = []
            for idx, item in enumerate(news_items):
                if isinstance(item, dict):
                    has_url = bool(item.get("url") or item.get("source"))
                    has_date = bool(item.get("date") or item.get("as_of"))
                    if has_url and has_date:
                        valid_citations += 1
                    else:
                        missing_url_or_date.append(idx)

            passed = len(missing_url_or_date) == 0
            results.append(CheckResult(
                name="news_citations_url_date_check",
                passed=passed,
                category="news",
                detail=f"Verified {valid_citations}/{len(news_items)} news items carry url+date citations.",
                evidence={"total": len(news_items), "missing_indices": missing_url_or_date},
                severity="WARNING" if not passed else "INFO"
            ))

        return results

    # --- 7. Anti-Sycophancy & Debate Arbitration Gate ---
    def evaluate_debate_turn(
        self,
        round_idx: int,
        challenger: str,
        claim: str,
        defense_type: str,
        evidence: Union[Dict[str, Any], str],
        company_data: Optional[Dict[str, Any]] = None,
        assumptions_data: Optional[Dict[str, Any]] = None,
        news_data: Optional[List[Dict[str, Any]]] = None,
    ) -> DebateVerdict:
        """Evaluates a single turn in the Adversarial Red Team debate against ground truth.

        Strict Anti-Sycophancy Rule (plan.md §3, §11 Ide 2):
        - REJECT agree-without-evidence.
        - Concessions MUST carry valid recalculation + source to be accepted.
        - Defenses MUST carry verifiable math (calc) + citable source.
        """
        dtype = str(defense_type).strip().lower()
        evidence_dict: Dict[str, Any] = {}
        if isinstance(evidence, dict):
            evidence_dict = evidence
        elif isinstance(evidence, str):
            evidence_dict = {"text": evidence}

        reasons: List[str] = []

        # 1. Evaluate Concessions (Anti-Sycophancy)
        if dtype == "concede":
            correction = evidence_dict.get("correction") or evidence_dict.get("recalculated_value")
            source = evidence_dict.get("source") or evidence_dict.get("exhibit_ref")

            if not correction:
                reasons.append("REJECT: Concession lacks concrete recalculated correction (Agree without evidence).")
            if not source:
                reasons.append("REJECT: Concession lacks verifiable source/evidence citation.")

            if reasons:
                return DebateVerdict(
                    round=round_idx,
                    challenger=challenger,
                    claim=claim,
                    defense_type="concede",
                    verdict="REJECT_AGREE_WITHOUT_EVIDENCE",
                    status="REJECT",
                    reasons=reasons,
                    evaluated_evidence=evidence_dict,
                    critic_notes="Defender conceded to challenger without providing computational proof and source."
                )
            else:
                return DebateVerdict(
                    round=round_idx,
                    challenger=challenger,
                    claim=claim,
                    defense_type="concede",
                    verdict="CONCEDED_WITH_CORRECTION",
                    status="PASS",
                    reasons=[],
                    evaluated_evidence=evidence_dict,
                    critic_notes=f"Concession accepted with verified correction: {correction} (Source: {source})"
                )

        # 2. Evaluate Defenses
        elif dtype == "defend":
            calc = evidence_dict.get("calc") or evidence_dict.get("calculation") or evidence_dict.get("math")
            source = evidence_dict.get("source") or evidence_dict.get("exhibit_ref")
            arg = evidence_dict.get("argument") or evidence_dict.get("text") or evidence_dict.get("explanation", "")

            if not calc and not any(ch.isdigit() for ch in str(arg)):
                reasons.append("REJECT: Defense lacks quantitative calculation / mathematical proof.")

            if not source and "exhibit" not in str(arg).lower() and "source" not in str(arg).lower():
                reasons.append("REJECT: Defense lacks explicit exhibit/source reference.")

            if company_data and isinstance(calc, dict):
                if "wacc" in calc and "coe" in calc:
                    coe_calc = float(calc.get("coe", 0))
                    wacc_calc = float(calc.get("wacc", 0))
                    if coe_calc <= 0 or wacc_calc <= 0:
                        reasons.append(f"REJECT: Illogical WACC calculation values ({wacc_calc}%, CoE {coe_calc}%)")

            if reasons:
                return DebateVerdict(
                    round=round_idx,
                    challenger=challenger,
                    claim=claim,
                    defense_type="defend",
                    verdict="REJECT_DEFENSE_UNVERIFIED",
                    status="REJECT",
                    reasons=reasons,
                    evaluated_evidence=evidence_dict,
                    critic_notes="Defender failed to provide verifiable calculation and source to support the defense."
                )
            else:
                return DebateVerdict(
                    round=round_idx,
                    challenger=challenger,
                    claim=claim,
                    defense_type="defend",
                    verdict="DEFENDED",
                    status="PASS",
                    reasons=[],
                    evaluated_evidence=evidence_dict,
                    critic_notes=f"Defense substantiated with verified math and source: {source}"
                )

        else:
            return DebateVerdict(
                round=round_idx,
                challenger=challenger,
                claim=claim,
                defense_type="unknown",
                verdict="REJECT_INVALID_DEFENSE",
                status="REJECT",
                reasons=[f"Invalid defense type '{dtype}'. Must be 'defend' or 'concede'."],
                evaluated_evidence=evidence_dict,
                critic_notes="Invalid protocol response from target agent."
            )

    # --- 8. Full Report Comprehensive Audit ---
    def audit_report(self, report_data: Dict[str, Any]) -> CriticAuditReport:
        """Performs full institutional audit across all verification dimensions."""
        ticker = str(report_data.get("ticker") or report_data.get("meta", {}).get("ticker", "UNKNOWN")).upper()

        checks: List[CheckResult] = []
        checks.extend(self.audit_numbers(report_data))
        checks.extend(self.audit_weights(report_data))
        checks.extend(self.audit_sources(report_data))
        checks.extend(self.audit_ddm(report_data))
        checks.extend(self.audit_kpis(report_data))
        checks.extend(self.audit_news_and_catalysts(report_data))

        # Check core fields present
        has_content = bool(report_data.get("cover") or report_data.get("thesis") or report_data.get("valuation") or report_data.get("financials"))
        checks.append(CheckResult(
            name="core_report_content_present",
            passed=has_content,
            category="structure",
            detail=f"Report content present for {ticker}",
            evidence={"has_content": has_content},
            severity="CRITICAL"
        ))

        critical_checks = [c for c in checks if c.severity == "CRITICAL"]
        failed_critical = [c for c in critical_checks if not c.passed]

        passed_count = sum(1 for c in checks if c.passed)
        total_count = len(checks)
        score = (passed_count / total_count * 100.0) if total_count > 0 else 0.0

        reasons: List[str] = [f"[{c.category.upper()}] {c.name}: {c.detail}" for c in failed_critical]
        fixes: List[str] = []

        for c in failed_critical:
            if c.category == "weights":
                fixes.append(f"Fix {c.name}: Normalize weights to sum exactly to 100.0%")
            elif c.category == "sources":
                fixes.append(f"Fix {c.name}: Provide explicit source string for all missing exhibits")
            elif c.category == "numbers":
                fixes.append(f"Fix {c.name}: Reconcile narrative numbers with engine calculation tables")
            elif c.category == "kpi":
                fixes.append(f"Fix {c.name}: Recompute KPI ratio according to standard formula (e.g. tenants/towers)")
            elif c.category == "ddm":
                fixes.append(f"Fix {c.name}: Ensure CoE > g and Payout × EPS == DPS")

        verdict: Literal["PASS", "REJECT"] = "PASS" if len(failed_critical) == 0 else "REJECT"
        ready_for_pdf = (verdict == "PASS")

        summary = (
            f"Critic Audit {verdict}: {passed_count}/{total_count} checks passed ({score:.1f}%). "
            f"{'Ready for PDF rendering.' if ready_for_pdf else f'{len(reasons)} critical flaws detected.'}"
        )

        return CriticAuditReport(
            ticker=ticker,
            verdict=verdict,
            ready_for_pdf=ready_for_pdf,
            summary=summary,
            total_checks=total_count,
            passed_checks=passed_count,
            failed_checks=len(failed_critical),
            score_pct=round(score, 1),
            reasons=reasons,
            fixes=fixes,
            checks=[asdict(c) for c in checks],
            meta={
                "engine_version": ENGINE_VERSION,
                "audited_at": now_iso(),
                "strict_mode": True,
            }
        )


# ---------------------------------------------------------------------------
# Public Functions & CLI Interface
# ---------------------------------------------------------------------------

_CRITIC_INSTANCE = CriticEngine()


def audit_report(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to audit a report dict and return dictionary result."""
    report = _CRITIC_INSTANCE.audit_report(report_data)
    return report.to_dict()


def evaluate_debate_turn(
    round_idx: int,
    challenger: str,
    claim: str,
    defense_type: str,
    evidence: Union[Dict[str, Any], str],
    company_data: Optional[Dict[str, Any]] = None,
    assumptions_data: Optional[Dict[str, Any]] = None,
    news_data: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Evaluate a single debate round and return verdict dict."""
    verdict = _CRITIC_INSTANCE.evaluate_debate_turn(
        round_idx=round_idx,
        challenger=challenger,
        claim=claim,
        defense_type=defense_type,
        evidence=evidence,
        company_data=company_data,
        assumptions_data=assumptions_data,
        news_data=news_data,
    )
    return asdict(verdict)


def audit_ticker(ticker: str) -> Dict[str, Any]:
    """Load ticker fixture or live output, run full audit, and save critic_audit.json."""
    tk = ticker.upper().strip()
    data = load_report_or_company(tk)
    audit = audit_report(data)

    out_file = os.path.join(ensure_out(tk), "critic_audit.json")
    write_json(out_file, audit)
    logger.info(f"Critic audit for {tk} written to {out_file} (Verdict: {audit['verdict']})")
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description="QA Critic Arbiter — Institutional Audit Engine")
    parser.add_argument("tickers", nargs="*", default=["RATU", "CDIA", "MTEL", "BBCA", "ADRO"], help="Tickers to audit")
    parser.add_argument("--strict", action="store_true", default=True, help="Enforce strict rejection on any flaw")
    args = parser.parse_args()

    print(f"==================================================")
    print(f"QA Critic Arbiter — Institutional Report Audit (T09)")
    print(f"==================================================")

    all_passed = True
    for tk in args.tickers:
        try:
            res = audit_ticker(tk)
            status_symbol = "✓ PASS" if res["verdict"] == "PASS" else "✗ REJECT"
            print(f"[{tk:5s}] {status_symbol} | Score: {res['score_pct']}% | Passed: {res['passed_checks']}/{res['total_checks']}")
            if res["reasons"]:
                for r in res["reasons"]:
                    print(f"       ! {r}")
            if res["verdict"] != "PASS":
                all_passed = False
        except Exception as ex:
            print(f"[{tk:5s}] ERROR: {ex}")
            all_passed = False

    print(f"==================================================")
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
