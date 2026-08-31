"""
Risk Officer — T07

Owns: Risk buckets 4-7 (+ J8 MSCI), severity, mitigants, pillar-specific.

Archetype refs:
- RATU (HP 7 Jan 2026): 4 bucket generik — Commodity, Operator, Regulatory PSC/DMO, Natural decline
- CDIA (BCA 23 Jun 2026): 7 buckets pillar-specific (sedimentation, gas supply, vessel damage, climate, etc)
- MTEL (KSI 27 Aug 2026): 6 infra-specific — Dependency on operators (Telkomsel), competition, satellite/Open RAN, regulatory, financing (rising rates), location/natural
- JPM 2026 Outlook (02 Dec 2025): J3 — MSCI Adjusted Free Float (Bucket 8: Index & Regulatory, May-26 implementation)

Spec: plan.md 2.1-2.4 + 3 "Risk Officer (pillar/sector-specific)" + 9 Risks & Mitigations
Branch: wt/t07-analyst
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal, Optional
import json

ARCHETYPE_SOURCES = {
    "RATU": "HP Sekuritas 7 Jan 2026 — RATU (4 buckets)",
    "CDIA": "BCA Sekuritas 23 Jun 2026 — CDIA (7 buckets, pillar-specific)",
    "MTEL": "KSI/Kiwoom 27 Aug 2026 — MTEL (6 infra buckets)",
    "JPM": "J.P. Morgan 02 Dec 2025 — Indonesia Equity 2026 Outlook (52p, p1/p8-9 MSCI)",
}

Severity = Literal["Low", "Medium", "High"]
Likelihood = Literal["Low", "Medium", "High"]
Category = Literal[
    "Commodity", "Operator", "Regulatory", "Natural Decline",
    "Pillar-specific", "Dependency", "Competition", "Technology",
    "Financing", "Location/Natural", "Index & Regulatory", "ESG",
]


@dataclass
class RiskBucket:
    id: str                      # e.g. "R1", "R8"
    category: Category
    title: str                   # e.g. "Commodity — Brent downside"
    description: str             # 1-2 sentence narasi + quantification
    impact: str = ""             # e.g. "Revenue -13% if Brent -10% (sensitivity)"
    severity: Severity = "Medium"
    likelihood: Likelihood = "Medium"
    mitigant: str = ""           # how company/market mitigates
    pillar: Optional[str] = None # CDIA: Energy/Water/Port/Logistics — null for single/infra
    source: str = ""
    as_of: str = ""


@dataclass
class RiskAssessment:
    ticker: str
    archetype: str               # single | sotp | infra
    subsector: str
    buckets: list[RiskBucket] = field(default_factory=list)
    # summary
    top_risk_id: str = ""        # highest severity*likelihood
    disclosure: str = "Risiko di atas adalah ringkasan — bukan daftar lengkap. Lihat prospektus/laporan tahunan untuk detail."
    as_of: str = ""
    source_tier: str = "T1"

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.ticker:
            errors.append("ticker required")
        if not 4 <= len(self.buckets) <= 8:
            errors.append(f"buckets {len(self.buckets)} outside 4-8 (RATU 4, CDIA 7, JPM 8)")
        # IDs must be unique
        ids = [b.id for b in self.buckets]
        if len(ids) != len(set(ids)):
            errors.append(f"duplicate bucket ids: {ids}")
        # each bucket needs source
        for b in self.buckets:
            if not b.source:
                errors.append(f"bucket {b.id} missing source")
            if not b.mitigant:
                errors.append(f"bucket {b.id} missing mitigant (institutional requires mitigant per bucket)")
        # RATU archetype must have Commodity + Regulatory buckets
        if self.archetype == "single":
            cats = {b.category for b in self.buckets}
            if "Commodity" not in cats:
                errors.append("single archetype must have Commodity bucket")
            if "Regulatory" not in cats:
                errors.append("single archetype must have Regulatory bucket")
        return errors

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# Deterministic helpers
# ---------------------------------------------------------------------------
SEVERITY_SCORE = {"Low": 1, "Medium": 2, "High": 3}

def calc_risk_score(severity: Severity, likelihood: Likelihood) -> int:
    """Risk score = severity * likelihood (1-9). Top risk = max score."""
    return SEVERITY_SCORE[severity] * SEVERITY_SCORE[likelihood]

def pick_top_risk(buckets: list[RiskBucket]) -> str:
    """Return id of highest score; tie-break by first occurrence."""
    if not buckets:
        return ""
    scored = [(calc_risk_score(b.severity, b.likelihood), b.id) for b in buckets]
    scored.sort(reverse=True)
    return scored[0][1]

def calc_sensitivity_impact(
    revenue_idr_bn: float,
    exposure_pct: float,
    shock_pct: float,
) -> float:
    """Revenue impact IDR bn if risk materializes by shock_pct."""
    return round(revenue_idr_bn * exposure_pct / 100 * shock_pct / 100, 2)


# ---------------------------------------------------------------------------
# Prompt contract — ADK LlmAgent (Gemini 3.7 Flash High)
# ---------------------------------------------------------------------------
RISK_SYSTEM_PROMPT = """\
You are Risk Officer (T07) — IDX institutional research.

Rules:
- JANGAN hitung. Panggil calc_risk_score / pick_top_risk / calc_sensitivity_impact untuk angka.
- Buckets 4-7 (max 8 dengan JPM MSCI). RATU=4 generik (Commodity, Operator, Regulatory PSC/DMO, Natural decline). CDIA=7 pillar-specific (sedimentation, gas supply, vessel damage, climate). MTEL=6 infra (Dependency on operators Telkomsel, competition, satellite/Open RAN, regulatory, financing rising rates, location/natural).
- JPM J3: Bucket 8 Index & Regulatory — MSCI Adjusted Free Float (announced 1Q26 → May-26 impl), quantify % mcap in low-float conglomerates. Wajib kalau ticker ada di JPM flows narrative.
- Tiap bucket: category, title, description (1-2 kalimat + quantification), impact (IDR/%, sensitivity), severity, likelihood, mitigant, pillar (CDIA only), source tier+url+date. Critic REJECT kalau bucket tanpa mitigant atau tanpa source.
- Severity*likelihood = risk score 1-9 — top_risk_id = max score.
- Bahasa default ID. Anti-sycophancy: defend(evidence: calc+source) atau concede(correction).
"""

RISK_USER_TEMPLATE = """\
Ticker: {ticker} | Archetype: {archetype} | Subsector: {subsector}
Collector (as_of {as_of}):
{collector_json}

Valuation context (for impact quantification):
{valuation_json}

News context (last 30d, for regulatory/MSCI risk):
{news_json}

Task: Build RiskAssessment JSON for {ticker} — 4-7 buckets (8 max).
- Archetype single: must include Commodity + Regulatory. sotp: pillar-specific per segment. infra: dependency+competition+tech+financing.
- Quantify impact per bucket (e.g. "Brent -10% -> Revenue -13% = IDR X bn" via calc_sensitivity_impact).
- Compute top_risk_id via pick_top_risk (do not choose manually).
- Return ONLY JSON.
"""


def build_risk_prompt(
    ticker: str,
    archetype: str,
    subsector: str,
    as_of: str,
    collector_json: str,
    valuation_json: str = "{}",
    news_json: str = "[]",
) -> tuple[str, str]:
    user = RISK_USER_TEMPLATE.format(
        ticker=ticker, archetype=archetype, subsector=subsector,
        as_of=as_of, collector_json=collector_json,
        valuation_json=valuation_json, news_json=news_json,
    )
    return RISK_SYSTEM_PROMPT, user


# ---------------------------------------------------------------------------
# Fixtures — offline dev / tests
# ---------------------------------------------------------------------------
def fixture_ratu_risk() -> RiskAssessment:
    buckets = [
        RiskBucket("R1", "Commodity", "Commodity — Brent downside", "Brent -10% -> net entitlement value -9% (PSC cost recovery buffers partial). IEA OMR Jan 2026 demand +1.1mb/d vs OPEC+ spare 5.2mb/d.", "Revenue -9% ~ IDR 120bn (calc_sensitivity_impact)", "High", "Medium", "PSC cost-recovery floors + DMO pricing buffer; hedge via term lifting", None, ARCHETYPE_SOURCES["RATU"], "2026-08-31"),
        RiskBucket("R2", "Operator", "Operator — Cepu execution", "Cepu gross 169k BOPD operated by ExxonMobil Cepu Ltd — RATU non-operator (2.4% PI via RETJ/PJUC).", "Production deferral 5% -> net -202 BOPD", "Medium", "Low", "SKK Migas oversight + operator track record; PSC technical committee", None, ARCHETYPE_SOURCES["RATU"], "2026-08-31"),
        RiskBucket("R3", "Regulatory", "Regulatory — PSC/DMO & fiscal terms", "DMO 25% at regulated price + PSC expiry 2035 + potential gross-split migration. PP 28/2025 SLA risk.", "DMO price -20% vs ICP -> netback -5%", "Medium", "Medium", "Grandfathered PSC terms until 2035; engagement via SKK Migas", None, ARCHETYPE_SOURCES["RATU"], "2026-08-31"),
        RiskBucket("R4", "Natural Decline", "Natural decline — reservoir depletion", "Cepu natural decline ~6-8% p.a. without infill drilling; reserve replacement critical.", "Plateau 169k -> decline -10k BOPD p.a.", "Medium", "Medium", "Infill drilling + EOR; SKK Migas POD approval", None, ARCHETYPE_SOURCES["RATU"], "2026-08-31"),
    ]
    return RiskAssessment("RATU", "single", "oil-holding", buckets, pick_top_risk(buckets), "Risiko di atas adalah ringkasan — bukan daftar lengkap.", "2026-08-31", "T1")


def fixture_mtel_risk() -> RiskAssessment:
    buckets = [
        RiskBucket("R1", "Dependency", "Dependency on operators (Telkomsel 71.83%)", "TLKM 71.83% holder + anchor tenant — tenancy concentration. Telkomsel capex cycle drives tower demand.", "Loss of 5% tenants -> revenue -4.3%", "High", "Medium", "Long-term MLA + TLKM strategic alignment; diversify to ISAT/EXCL tenants", None, ARCHETYPE_SOURCES["MTEL"], "2026-08-31"),
        RiskBucket("R2", "Competition", "Competition — tower infra pricing", "Towerco competition (TOWR, TBIG) pressures lease rates; colocation pricing.", "Lease rate -5% -> EBITDA margin -2pp", "Medium", "Medium", "Scale (40,563 towers) + tenancy 1.57x operating leverage", None, ARCHETYPE_SOURCES["MTEL"], "2026-08-31"),
        RiskBucket("R3", "Technology", "Technology — satellite / Open RAN", "LEO satellite + Open RAN could bypass tower in remote; long-term structural.", "Remote 10% sites at risk -> fiber offset", "Medium", "Low", "Fiber 59,239 km diversification; monitor Starlink/OneWeb rollout", None, ARCHETYPE_SOURCES["MTEL"], "2026-08-31"),
        RiskBucket("R4", "Regulatory", "Regulatory — spectrum & tower permits", "Kominfo 700MHz/2.6GHz allocation reshapes tenant demand; local IMB/permit risk (PP 28/2025).", "Permit delay 6M -> fiber rollout push 1Q", "Medium", "Medium", "Kominfo spectrum pipeline + PP 28/2025 positive fictitious approval", None, ARCHETYPE_SOURCES["MTEL"], "2026-08-31"),
        RiskBucket("R5", "Financing", "Financing — rising rates", "Debt 21.4T (MTEL 2024) — rising BI rate + IDR volatility raises CoD; WACC 10.10% sensitive.", "CoD +100bps -> WACC +39bps -> FV -4%", "Medium", "Medium", "60.8% equity / 39.2% debt; refinance ladder; rate hedge", None, ARCHETYPE_SOURCES["MTEL"], "2026-08-31"),
        RiskBucket("R6", "Location/Natural", "Location / natural — site & disaster", "Tower sites in seismic/flood zones; location risk + natural disaster.", "Site damage 0.5% p.a. -> capex +1%", "Low", "Medium", "Geographic diversification 40k+ sites; insurance", None, ARCHETYPE_SOURCES["MTEL"], "2026-08-31"),
    ]
    return RiskAssessment("MTEL", "infra", "tower-infra", buckets, pick_top_risk(buckets), "Risiko di atas adalah ringkasan — bukan daftar lengkap.", "2026-08-31", "T1")


def fixture_mtel_risk_with_msci() -> RiskAssessment:
    """MTEL + JPM J3 MSCI bucket (7 -> 8) — for tickers in JPM flows narrative."""
    base = fixture_mtel_risk()
    msci = RiskBucket("R7", "Index & Regulatory", "Index & Regulatory — MSCI Adjusted Free Float", "MSCI Adjusted Free Float announced 1Q26 -> May-26 impl (JPM p8-9). Low-float conglomerate rally at risk; retail 58% ADTV.", "Free-float cut 10% -> index weight -15% -> passive outflow", "High", "Medium", "Monitor MSCI consultation; free-float >28% (MTEL 28.17%) above threshold", None, ARCHETYPE_SOURCES["JPM"], "2026-08-31")
    base.buckets.append(msci)
    base.top_risk_id = pick_top_risk(base.buckets)
    return base
