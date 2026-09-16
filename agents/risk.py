"""
Risk Officer - T07

Owns: Risk buckets 4-7 (+ J8 MSCI), severity, mitigants, pillar-specific.

Archetype refs:
- RATU (HP 7 Jan 2026): 4 bucket generik - Commodity, Operator, Regulatory PSC/DMO, Natural decline
- CDIA (BCA 23 Jun 2026): 7 buckets pillar-specific (sedimentation, gas supply, vessel damage, climate, etc)
- MTEL (KSI 27 Aug 2026): 6 infra-specific - Dependency on operators (Telkomsel), competition, satellite/Open RAN, regulatory, financing (rising rates), location/natural
- JPM 2026 Outlook (02 Dec 2025): J3 - MSCI Adjusted Free Float (Bucket 8: Index & Regulatory, May-26 implementation)

Spec: plan.md 2.1-2.4 + 3 "Risk Officer (pillar/sector-specific)" + 9 Risks & Mitigations
Branch: wt/t07-analyst
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal, Optional
import json
import os

ARCHETYPE_SOURCES = {
    "RATU": "HP Sekuritas 7 Jan 2026 - RATU (4 buckets)",
    "CDIA": "BCA Sekuritas 23 Jun 2026 - CDIA (7 buckets, pillar-specific)",
    "MTEL": "KSI/Kiwoom 27 Aug 2026 - MTEL (6 infra buckets)",
    "JPM": "J.P. Morgan 02 Dec 2025 - Indonesia Equity 2026 Outlook (52p, p1/p8-9 MSCI)",
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
    title: str                   # e.g. "Commodity - Brent downside"
    description: str             # 1-2 sentence narasi + quantification
    impact: str = ""             # e.g. "Revenue -13% if Brent -10% (sensitivity)"
    severity: Severity = "Medium"
    likelihood: Likelihood = "Medium"
    mitigant: str = ""           # how company/market mitigates
    pillar: Optional[str] = None # CDIA: Energy/Water/Port/Logistics - null for single/infra
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
    disclosure: str = "Risiko di atas adalah ringkasan - bukan daftar lengkap. Lihat prospektus/laporan tahunan untuk detail."
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
# Prompt contract - ADK LlmAgent (Gemini 3.7 Flash High)
# ---------------------------------------------------------------------------
RISK_SYSTEM_PROMPT = """\
You are Risk Officer (T07) - IDX institutional research.

Rules:
- JANGAN hitung. Panggil calc_risk_score / pick_top_risk / calc_sensitivity_impact untuk angka.
- Buckets 4-7 (max 8 dengan JPM MSCI). RATU=4 generik (Commodity, Operator, Regulatory PSC/DMO, Natural decline). CDIA=7 pillar-specific (sedimentation, gas supply, vessel damage, climate). MTEL=6 infra (Dependency on operators Telkomsel, competition, satellite/Open RAN, regulatory, financing rising rates, location/natural).
- JPM J3: Bucket 8 Index & Regulatory - MSCI Adjusted Free Float (announced 1Q26 → May-26 impl), quantify % mcap in low-float conglomerates. Wajib kalau ticker ada di JPM flows narrative.
- Tiap bucket: category, title, description (1-2 kalimat + quantification), impact (IDR/%, sensitivity), severity, likelihood, mitigant, pillar (CDIA only), source tier+url+date. Critic REJECT kalau bucket tanpa mitigant atau tanpa source.
- Severity*likelihood = risk score 1-9 - top_risk_id = max score.
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

Task: Build RiskAssessment JSON for {ticker} - 4-7 buckets (8 max).
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
# Fixtures - offline dev / tests
# ---------------------------------------------------------------------------
def _load_assumptions(ticker: str, assum: Optional[dict] = None) -> dict:
    """Load data/assumptions/{ticker}.json if available, merged with passed assum dict."""
    data: dict = {}
    t = ticker.upper().strip() if ticker else ""
    if t:
        base_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data", "assumptions"))
        path = os.path.join(base_dir, f"{t}.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        data.update(loaded)
            except Exception:
                pass
    if assum and isinstance(assum, dict):
        data.update(assum)
    return data


def fixture_from_archetype(
    ticker: str,
    archetype: str = "single",
    assum: Optional[dict] = None,
) -> RiskAssessment:
    """Dynamic archetype-driven RiskAssessment fixture generator."""
    merged_assum = _load_assumptions(ticker, assum)
    t = ticker.upper().strip() if ticker else "UNKNOWN"
    arch = (archetype or "").lower().strip()

    if arch in ("oil-holding", "single-pillar", "single"):
        arch_norm = "single"
    elif arch in ("conglomerate", "sotp", "multi"):
        arch_norm = "sotp"
    elif arch in ("tower-infra", "tower", "infra", "telecom"):
        arch_norm = "infra"
    elif arch in ("bank", "banking", "financials"):
        arch_norm = "bank"
    elif arch in ("coal", "mining"):
        arch_norm = "coal"
    elif arch == "unknown":
        arch_norm = "unknown"
    else:
        arch_norm = arch if arch in ("single", "sotp", "infra", "bank", "coal") else "unknown"

    source_label = f"assumption_derived archetype={arch_norm}"
    as_of_val = merged_assum.get("generated_at") or merged_assum.get("as_of") or "2026-08-31"
    if isinstance(as_of_val, str) and "T" in as_of_val:
        as_of_val = as_of_val.split("T")[0]

    if arch_norm == "single":
        buckets = [
            RiskBucket("R1", "Commodity", "Commodity - Brent downside", "Brent -10% -> net entitlement value -9% (PSC cost recovery buffers partial). IEA OMR Jan 2026 demand +1.1mb/d vs OPEC+ spare 5.2mb/d.", "Revenue -9% ~ IDR 120bn (calc_sensitivity_impact)", "High", "Medium", "PSC cost-recovery floors + DMO pricing buffer; hedge via term lifting", None, source_label, as_of_val),
            RiskBucket("R2", "Operator", "Operator - Cepu execution", "Cepu gross 169k BOPD operated by ExxonMobil Cepu Ltd - non-operator (2.4% PI).", "Production deferral 5% -> net -202 BOPD", "Medium", "Low", "SKK Migas oversight + operator track record; PSC technical committee", None, source_label, as_of_val),
            RiskBucket("R3", "Regulatory", "Regulatory - PSC/DMO & fiscal terms", "DMO 25% at regulated price + PSC expiry 2035 + potential gross-split migration. PP 28/2025 SLA risk.", "DMO price -20% vs ICP -> netback -5%", "Medium", "Medium", "Grandfathered PSC terms until 2035; engagement via SKK Migas", None, source_label, as_of_val),
            RiskBucket("R4", "Natural Decline", "Natural decline - reservoir depletion", "Natural decline ~6-8% p.a. without infill drilling; reserve replacement critical.", "Plateau 169k -> decline -10k BOPD p.a.", "Medium", "Medium", "Infill drilling + EOR; SKK Migas POD approval", None, source_label, as_of_val),
        ]
        return RiskAssessment(t, "single", "oil-holding", buckets, pick_top_risk(buckets), "Risiko di atas adalah ringkasan - bukan daftar lengkap.", as_of_val, "T1")

    elif arch_norm == "sotp":
        buckets = [
            RiskBucket("R1", "Pillar-specific", "Pillar 1 (Energy) - Off-take & gas supply", "Power purchase agreement off-take curtailment or fuel gas supply disruption.", "Energy EBITDA -5%", "Medium", "Medium", "Long-term take-or-pay off-take agreements with state utility", "Energy", source_label, as_of_val),
            RiskBucket("R2", "Pillar-specific", "Pillar 2 (Water) - Concession & volume", "Industrial water concession intake turbidity or dry season raw water volume.", "Water volume -8%", "Low", "Medium", "Dual water intake reservoirs and sedimentation management", "Water", source_label, as_of_val),
            RiskBucket("R3", "Pillar-specific", "Pillar 3 (Port) - Throughput & tank occupancy", "Regional commodity shipment volatility impacting liquid storage and jetty throughput.", "Port throughput -10%", "Medium", "Low", "Multi-year commercial tank storage contracts", "Port", source_label, as_of_val),
            RiskBucket("R4", "Pillar-specific", "Pillar 4 (Logistics) - Vessel charter & fuel costs", "Vessel damage, charter rate volatility, or bunker fuel spikes.", "Logistics margin -2pp", "Medium", "Medium", "Time-charter contracts with bunker cost pass-through clauses", "Logistics", source_label, as_of_val),
            RiskBucket("R5", "Financing", "Holding - Leverage & debt service", "HoldCo leverage servicing dependent on operating subsidiary dividend upstreaming.", "DSCR tighter by 0.3×", "Medium", "Medium", "Diversified cash flows across 4 independent pillars", None, source_label, as_of_val),
            RiskBucket("R6", "Regulatory", "Cross-pillar regulatory & licensing compliance", "PP 28/2025 SLA risk across environmental and concession permits.", "Permit delay 3-6 months", "Medium", "Low", "Dedicated regulatory affairs unit and centralized compliance tracking", None, source_label, as_of_val),
            RiskBucket("R7", "Location/Natural", "Climate & sedimentation risk", "Extreme rainfall causing port sedimentation and river intake flooding.", "Dredging capex +IDR 15bn", "Low", "Medium", "Scheduled maintenance dredging and flood mitigation dykes", None, source_label, as_of_val),
        ]
        return RiskAssessment(t, "sotp", "conglomerate", buckets, pick_top_risk(buckets), "Risiko di atas adalah ringkasan - bukan daftar lengkap.", as_of_val, "T1")

    elif arch_norm == "infra":
        buckets = [
            RiskBucket("R1", "Dependency", "Dependency on anchor operators (TLKM 71.83%)", "Anchor tenant concentration and operator capex cycle.", "Loss of 5% tenants -> revenue -4.3%", "High", "Medium", "Long-term MLA + strategic alignment; diversify to other telco tenants", None, source_label, as_of_val),
            RiskBucket("R2", "Competition", "Competition - tower infra pricing", "Towerco competition pressures lease rates and colocation renewals.", "Lease rate -5% -> EBITDA margin -2pp", "Medium", "Medium", "Scale (40k+ towers) + tenancy 1.57× operating leverage", None, source_label, as_of_val),
            RiskBucket("R3", "Technology", "Technology - satellite / Open RAN", "LEO satellite + Open RAN could bypass macro towers in remote areas.", "Remote 10% sites at risk -> fiber offset", "Medium", "Low", "Fiber 59k+ km diversification; monitor satellite rollout", None, source_label, as_of_val),
            RiskBucket("R4", "Regulatory", "Regulatory - spectrum & tower permits", "Kominfo 700MHz/2.6GHz allocation reshapes tenant demand; local permit risk.", "Permit delay 6M -> fiber rollout push 1Q", "Medium", "Medium", "Kominfo spectrum pipeline + PP 28/2025 positive fictitious approval", None, source_label, as_of_val),
            RiskBucket("R5", "Financing", "Financing - rising rates", "Debt servicing sensitive to benchmark interest rate hikes and WACC.", "CoD +100bps -> WACC +39bps -> FV -4%", "Medium", "Medium", "Prudent debt ratio, refinance ladder, interest rate hedges", None, source_label, as_of_val),
            RiskBucket("R6", "Location/Natural", "Location / natural - site & disaster", "Tower sites in seismic/flood zones; location risk + natural disaster.", "Site damage 0.5% p.a. -> capex +1%", "Low", "Medium", "Geographic diversification 40k+ sites; insurance coverage", None, source_label, as_of_val),
        ]
        return RiskAssessment(t, "infra", "tower-infra", buckets, pick_top_risk(buckets), "Risiko di atas adalah ringkasan - bukan daftar lengkap.", as_of_val, "T1")

    elif arch_norm == "bank":
        buckets = [
            RiskBucket("R1", "Regulatory", "Monetary policy & reserve requirements", "BI rate policy shifts, statutory reserve adjustments, or lending caps.", "NIM compression -20-30 bps", "High", "Medium", "Strong CASA franchise keeping funding costs low", None, source_label, as_of_val),
            RiskBucket("R2", "Financing", "Credit risk & asset quality deterioration", "Macro downturn increasing non-performing loans (NPL/LAR).", "Credit cost +30-50 bps", "High", "Low", "Conservative credit underwriting and high coverage (>200%)", None, source_label, as_of_val),
            RiskBucket("R3", "Competition", "Competition from FinTech & digital banking", "Disruption in fee-based income and payment processing.", "Fee growth slowdown -2%", "Medium", "Medium", "Extensive digital ecosystem and transaction banking platform", None, source_label, as_of_val),
            RiskBucket("R4", "ESG", "Cybersecurity & IT operational risk", "System outages or data security incidents impacting operations.", "Operational disruption impact", "Medium", "Low", "Multi-tier cybersecurity framework and disaster recovery sites", None, source_label, as_of_val),
        ]
        return RiskAssessment(t, "bank", "bank", buckets, pick_top_risk(buckets), "Risiko di atas adalah ringkasan - bukan daftar lengkap.", as_of_val, "T1")

    elif arch_norm == "coal":
        buckets = [
            RiskBucket("R1", "Commodity", "Commodity - Thermal coal price cyclicality", "Global energy transition and ASP decline impacting topline cash generation.", "Revenue -15% if ASP drops 15%", "High", "High", "First-quartile low cash cost position ($40-45/t)", None, source_label, as_of_val),
            RiskBucket("R2", "Regulatory", "Regulatory - Royalty tariffs & DMO cap", "Progressive royalty rates (14-28%) and mandatory 25% domestic market obligation.", "Margin compression -3-4pp", "High", "Medium", "Full regulatory compliance and long-term utility contracts", None, source_label, as_of_val),
            RiskBucket("R3", "ESG", "ESG & decarbonization policies", "Global coal divestment policies restricting long-term capital access.", "Valuation multiple de-rating", "High", "Medium", "Strategic diversification into renewables and mineral processing", None, source_label, as_of_val),
            RiskBucket("R4", "Location/Natural", "Weather & logistics disruptions", "Monsoon rainfall disrupting mining pits and river barging logistics.", "Quarterly volume deferral 5-10%", "Medium", "Medium", "Pit dewatering infrastructure and buffer stockpile management", None, source_label, as_of_val),
        ]
        return RiskAssessment(t, "coal", "coal", buckets, pick_top_risk(buckets), "Risiko di atas adalah ringkasan - bukan daftar lengkap.", as_of_val, "T1")

    else:  # unknown
        buckets = [
            RiskBucket("R1", "Regulatory", "Regulatory & compliance risk", "General corporate governance and regulatory compliance obligations.", "Compliance variance", "Medium", "Medium", "Strict adherence to OJK and IDX listing regulations", None, source_label, as_of_val),
            RiskBucket("R2", "Competition", "Market competition risk", "Competitive market dynamics impacting revenue growth and margins.", "Margin variance +-2%", "Medium", "Medium", "Product differentiation and customer retention", None, source_label, as_of_val),
            RiskBucket("R3", "Financing", "Macroeconomic & funding risk", "Interest rate fluctuations and working capital requirements.", "Funding cost +-50bps", "Medium", "Low", "Prudent balance sheet and liquidity management", None, source_label, as_of_val),
            RiskBucket("R4", "ESG", "Operational & continuity risk", "Operational disruptions or business interruption risks.", "Operational variance +-3%", "Low", "Low", "Business continuity planning and internal controls", None, source_label, as_of_val),
        ]
        return RiskAssessment(t, "unknown", "general", buckets, pick_top_risk(buckets), "Risiko di atas adalah ringkasan - bukan daftar lengkap.", as_of_val, "T1")
