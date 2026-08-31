"""
Company Analyst Agent — T07

Owns: Company history, IPO, BOD, PSC/ownership structure for institutional equity reports.

Archetype refs:
- RATU (HP 7 Jan 2026): History 2006→2023, IPO 88% ke RETJ/PJUC, BOD 6, PSC flow, Shares 2.71B Float 31.2%
- CDIA (BCA 23 Jun 2026): Conglomerate 4-pilar (Energy/Water/Port/Logistics), segment specs (MW/m³/DWT)
- MTEL (KSI 27 Aug 2026): Infra recurring (Tower/Fiber), TLKM 71.83% holder, 81.5Bn shares

Spec: plan.md §2.1-2.3 + §3 Architecture "Company Analyst (bisnis+ops specs/MW/DWT)"
Branch: wt/t07-analyst
Provider: AGY Gemini 3.7 Flash High — deterministic Python when math, LLM when narasi + source.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal, Optional
import json
import math

# ---------------------------------------------------------------------------
# Provenance helper — every exhibit must carry source
# ---------------------------------------------------------------------------
ARCHETYPE_SOURCES = {
    "RATU": "HP Sekuritas 7 Jan 2026 — RATU (11p, 819KB)",
    "CDIA": "BCA Sekuritas 23 Jun 2026 — CDIA (4-pilar, 1.58MB)",
    "MTEL": "KSI/Kiwoom 27 Aug 2026 — MTEL (infra recurring, 302p)",
    "JPM": "J.P. Morgan 02 Dec 2025 — Indonesia Equity 2026 Outlook (52p)",
}

# ---------------------------------------------------------------------------
# Data models — input is ticker + resolved context from Collector/Modeler
# ---------------------------------------------------------------------------
Archetype = Literal["single", "sotp", "infra"]

@dataclass
class TimelineEvent:
    year: int
    title: str
    detail: str
    source: str = ""

@dataclass
class IPODetail:
    ipo_date: str              # ISO
    ipo_price: float           # IDR
    listing_price: Optional[float] = None  # e.g. RATU 1,150 → 10,650
    shares_offered_bn: Optional[float] = None
    shares_outstanding_bn: Optional[float] = None  # RATU 2.71
    free_float_pct: Optional[float] = None         # RATU 31.2
    proceeds_use: list[dict] = field(default_factory=list)  # [{"to": "RETJ", "pct": 52}, ...]
    underwriter: str = ""
    source: str = ""

@dataclass
class BODMember:
    name: str
    role: str                  # e.g. "President Director", "Independent Commissioner"
    since: Optional[str] = None
    background: str = ""
    source: str = ""

@dataclass
class PSCStructure:
    """Production Sharing Contract / concession structure (RATU: Cepu 169k BOPD via SKK Migas)."""
    block_name: str            # e.g. "Cepu"
    operator: str              # e.g. "ExxonMobil Cepu Ltd"
    participation_pct: float   # RATU effective via RETJ/PJUC
    gross_production_bopd: Optional[int] = None  # 169k
    contract_type: str = "PSC" # PSC / IUP / concession
    expiry: Optional[str] = None
    regulator: str = "SKK Migas"
    dmo_pct: Optional[float] = None  # Domestic Market Obligation
    source: str = ""

@dataclass
class Holder:
    name: str
    pct: float
    shares_bn: Optional[float] = None
    source: str = ""

@dataclass
class BusinessSegment:
    name: str                  # e.g. "Tower leasing" / "Energy" / "Cepu PSC"
    revenue_share_pct: Optional[float] = None  # CDIA Energy 55%, MTEL Tower 3,833
    revenue_idr_bn: Optional[float] = None
    yoy_pct: Optional[float] = None
    qoq_pct: Optional[float] = None
    specs: dict = field(default_factory=dict)  # MW, DWT, m³, Tower count, etc.
    source: str = ""

@dataclass
class CompanyProfile:
    ticker: str
    name: str
    archetype: Archetype       # single | sotp | infra — drives template switch
    subsector: str             # e.g. "oil-holding" | "conglomerate" | "tower-infra" | "bank" | "coal"
    established: Optional[int] = None  # RATU 2006
    listing_board: str = "IDX Main"
    history: list[TimelineEvent] = field(default_factory=list)
    ipo: Optional[IPODetail] = None
    holders: list[Holder] = field(default_factory=list)  # sorted desc pct
    bod: list[BODMember] = field(default_factory=list)   # BOD 6 for RATU
    commissioners: list[BODMember] = field(default_factory=list)
    psc: list[PSCStructure] = field(default_factory=list)
    segments: list[BusinessSegment] = field(default_factory=list)
    key_specs: dict = field(default_factory=dict)  # operational specs per archetype
    disclaimer_source: str = ""  # OJK footer
    # provenance
    as_of: str = ""            # ISO date of snapshot
    source_tier: str = "T1"    # T1 IDX disclosure/Kontan/Bisnis, T2 Reuters/Bloomberg, T3 blog

    def validate(self) -> list[str]:
        """Critic checks — returns error strings (empty = pass)."""
        errors: list[str] = []
        if not self.ticker:
            errors.append("ticker required")
        if self.archetype not in ("single", "sotp", "infra"):
            errors.append(f"archetype {self.archetype!r} must be single|sotp|infra")
        if self.ipo and self.ipo.free_float_pct is not None:
            if not 0 < self.ipo.free_float_pct <= 100:
                errors.append(f"free_float_pct {self.ipo.free_float_pct} out of range")
        # holder pct should not exceed 100 sum (allow rounding 100.5)
        total_holder = sum(h.pct for h in self.holders)
        if self.holders and total_holder > 100.5:
            errors.append(f"holders sum {total_holder:.1f}% > 100%")
        # segment pct should sum ~100 when provided (allow 99-101)
        seg_pcts = [s.revenue_share_pct for s in self.segments if s.revenue_share_pct is not None]
        if seg_pcts and not 99 <= sum(seg_pcts) <= 101:
            # only flag if >1 segment and all have pct
            if len(seg_pcts) == len(self.segments):
                errors.append(f"segment pct sum {sum(seg_pcts):.1f}% != 100%")
        # PSC participation 0-100
        for p in self.psc:
            if not 0 < p.participation_pct <= 100:
                errors.append(f"PSC {p.block_name} participation {p.participation_pct}% out of range")
            if p.gross_production_bopd is not None and p.gross_production_bopd < 0:
                errors.append(f"PSC {p.block_name} BOPD negative")
        return errors

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# Deterministic helpers — NEVER let LLM invent these numbers
# ---------------------------------------------------------------------------
def calc_free_float_pct(public_shares_bn: float, outstanding_bn: float) -> float:
    """Critic validates: free_float = public / outstanding * 100."""
    if outstanding_bn == 0:
        raise ValueError("outstanding_bn cannot be 0")
    return round(public_shares_bn / outstanding_bn * 100, 2)

def calc_proceeds_allocation(total_idr_bn: float, allocations: list[dict]) -> list[dict]:
    """Validate that proceeds_use pct sums to 100 and compute IDR amounts."""
    total_pct = sum(a["pct"] for a in allocations)
    if not 99.5 <= total_pct <= 100.5:
        raise ValueError(f"proceeds pct sum {total_pct} != 100")
    return [
        {**a, "idr_bn": round(total_idr_bn * a["pct"] / 100, 2)}
        for a in allocations
    ]

def calc_net_entitlement_bopd(gross_bopd: int, participation_pct: float) -> float:
    """RATU: net entitlement = gross * participation% (before cost recovery split)."""
    return round(gross_bopd * participation_pct / 100, 1)


# ---------------------------------------------------------------------------
# Prompt contract — what the LLM sub-agent receives (ADK LlmAgent)
# ---------------------------------------------------------------------------
ANALYST_SYSTEM_PROMPT = """\
You are Company Analyst (T07) — institutional equity research for IDX retail.

Rules:
- JANGAN hitung. Panggil calc_*() untuk angka (free float, BOPD, proceeds).
- Setiap klaim butuh source tier + url+date. Tier1: IDX disclosure/Kontan/Bisnis/IDX Channel. Tier2: Reuters/Bloomberg/JP. Tier3: blog (flag).
- History: tulis 2006→2023 timeline faktual. RATU: founded 2006, PSC Cepu, IPO 88% ke RETJ/PJUC — jangan ngarang untuk ticker lain.
- BOD: sebut 6 anggota RATU kalau ticker RATU. Untuk ticker lain, search via web_search + web_extract, jangan hallucinate names.
- PSC: sebut block, operator, SKK Migas, DMO%, expiry. Kalau tidak ada PSC (e.g. MTEL infra, BBCA bank), isi psc=[] dan jelaskan why N/A.
- Holders: urut desc %. MTEL TLKM 71.83% — sebut kalau MTEL. CDIA 60% — sebut kalau CDIA.
- Segments: kalau single-pilar hide % (sotp/infra tampilkan). Sum 100% — Critic akan reject jika tidak.
- Output: JSON CompanyProfile (as_dict). Bahasa default ID (EN kalau diminta). Tambah as_of ISO date.
- Anti-sycophancy: defend(evidence: calc+source) atau concede(correction) kalau di-challenge Adversarial — jangan agree tanpa bukti.
"""

ANALYST_USER_TEMPLATE = """\
Ticker: {ticker} | Archetype: {archetype} | Subsector: {subsector}
Collector snapshot (as_of {as_of}):
{collector_json}

Assumptions (WACC/beta — for cross-check only, do not recompute):
{assumptions_json}

News context (last 30d, max 8):
{news_json}

Task: Build CompanyProfile JSON for {ticker}. Fill history+IPO+BOD+PSC+holders+segments+specs.
- Search web_search("{ticker} IDX IPO history BOD") if holder/BOD missing — cite url+date.
- Use calc_free_float_pct / calc_proceeds_allocation / calc_net_entitlement_bopd for math — do not compute mentally.
- Return ONLY JSON (no prose wrapper). Critic will validate sum checks.
"""


def build_analyst_prompt(
    ticker: str,
    archetype: Archetype,
    subsector: str,
    as_of: str,
    collector_json: str,
    assumptions_json: str = "{}",
    news_json: str = "[]",
) -> tuple[str, str]:
    """Return (system, user) prompts for ADK LlmAgent."""
    user = ANALYST_USER_TEMPLATE.format(
        ticker=ticker,
        archetype=archetype,
        subsector=subsector,
        as_of=as_of,
        collector_json=collector_json,
        assumptions_json=assumptions_json,
        news_json=news_json,
    )
    return ANALYST_SYSTEM_PROMPT, user


# ---------------------------------------------------------------------------
# Synthetic fixtures for offline dev / tests (seed=42 style — matches plan.md data layer)
# ---------------------------------------------------------------------------
def fixture_ratu() -> CompanyProfile:
    return CompanyProfile(
        ticker="RATU",
        name="Raharja Energi Cepu Tbk",
        archetype="single",
        subsector="oil-holding",
        established=2006,
        history=[
            TimelineEvent(2006, "Founded", "PT Raharja Energi Cepu established as PSC holding vehicle", ARCHETYPE_SOURCES["RATU"]),
            TimelineEvent(2011, "Participating Interest", "Acquired participating interest in Cepu Block via RETJ/PJUC", ARCHETYPE_SOURCES["RATU"]),
            TimelineEvent(2023, "IPO", "IPO at IDR 1,150 — 88% proceeds to RETJ/PJUC acquisition", ARCHETYPE_SOURCES["RATU"]),
            TimelineEvent(2024, "Production", "Cepu gross 169k BOPD (SKK Migas), RATU net entitlement via PSC", ARCHETYPE_SOURCES["RATU"]),
        ],
        ipo=IPODetail(
            ipo_date="2023-05-08",
            ipo_price=1150,
            listing_price=10650,
            shares_offered_bn=0.844,
            shares_outstanding_bn=2.71,
            free_float_pct=31.2,
            proceeds_use=[{"to": "RETJ", "pct": 52}, {"to": "PJUC", "pct": 36}, {"to": "Working capital", "pct": 12}],
            underwriter="HP Sekuritas",
            source=ARCHETYPE_SOURCES["RATU"],
        ),
        holders=[
            Holder("PT Raharja Energi Investama", 45.3, 1.23, ARCHETYPE_SOURCES["RATU"]),
            Holder("Public (free float)", 31.2, 0.85, ARCHETYPE_SOURCES["RATU"]),
            Holder("PT Jenggala Energi", 23.5, 0.64, ARCHETYPE_SOURCES["RATU"]),
        ],
        bod=[
            BODMember("Direktur Utama", "President Director", "2023", "Ex-RETJ, PSC Cepu operator experience", ARCHETYPE_SOURCES["RATU"]),
            BODMember("Direktur Keuangan", "Finance Director", "2023", "", ARCHETYPE_SOURCES["RATU"]),
            BODMember("Direktur Operasional", "Operations Director", "2023", "", ARCHETYPE_SOURCES["RATU"]),
            BODMember("Direktur Teknik", "Technical Director", "2023", "", ARCHETYPE_SOURCES["RATU"]),
            BODMember("Direktur SDM", "HR Director", "2023", "", ARCHETYPE_SOURCES["RATU"]),
            BODMember("Direktur Kepatuhan", "Compliance Director", "2023", "", ARCHETYPE_SOURCES["RATU"]),
        ],
        psc=[
            PSCStructure("Cepu", "ExxonMobil Cepu Ltd", 2.4, 169000, "PSC", "2035", "SKK Migas", 25.0, ARCHETYPE_SOURCES["RATU"]),
        ],
        segments=[
            BusinessSegment("Cepu PSC entitlement", 100.0, None, None, None, {"gross_bopd": 169000, "net_bopd": 4056}, ARCHETYPE_SOURCES["RATU"]),
        ],
        key_specs={"gross_bopd": 169000, "net_bopd": 4056, "bopd_source": "SKK Migas"},
        as_of="2026-08-31",
        source_tier="T1",
    )


def fixture_mtel() -> CompanyProfile:
    return CompanyProfile(
        ticker="MTEL",
        name="Dayamitra Telekomunikasi Tbk",
        archetype="infra",
        subsector="tower-infra",
        established=2006,
        history=[
            TimelineEvent(2006, "Founded", "Telkom infra arm — tower portfolio build-out", ARCHETYPE_SOURCES["MTEL"]),
            TimelineEvent(2021, "IPO", "IPO tower infra, TLKM retains 71.83%", ARCHETYPE_SOURCES["MTEL"]),
            TimelineEvent(2024, "Fiber expansion", "Fiber 59,239 km (+9% y/y), tenancy 1.57x", ARCHETYPE_SOURCES["MTEL"]),
        ],
        ipo=IPODetail(
            ipo_date="2021-11-22",
            ipo_price=800,
            shares_outstanding_bn=81.5,
            free_float_pct=28.17,
            proceeds_use=[{"to": "Tower acquisition", "pct": 60}, {"to": "Fiber build", "pct": 25}, {"to": "Working capital", "pct": 15}],
            underwriter="Mandiri Sekuritas",
            source=ARCHETYPE_SOURCES["MTEL"],
        ),
        holders=[
            Holder("PT Telkom Indonesia (Persero) Tbk", 71.83, 58.54, ARCHETYPE_SOURCES["MTEL"]),
            Holder("Public", 28.17, 22.96, ARCHETYPE_SOURCES["MTEL"]),
        ],
        bod=[
            BODMember("President Director", "President Director", "2021", "Telkom Group", ARCHETYPE_SOURCES["MTEL"]),
            BODMember("Finance Director", "Finance Director", "2021", "", ARCHETYPE_SOURCES["MTEL"]),
            BODMember("Operations Director", "Operations Director", "2021", "", ARCHETYPE_SOURCES["MTEL"]),
        ],
        psc=[],
        segments=[
            BusinessSegment("Tower leasing", 81.7, 3833, 1.0, 0.8, {"towers": 40563}, ARCHETYPE_SOURCES["MTEL"]),
            BusinessSegment("Fiber", 6.6, 309, 8.0, 2.1, {"km": 59239}, ARCHETYPE_SOURCES["MTEL"]),
            BusinessSegment("Tower-Related", 6.4, 299, 15.0, 3.2, {}, ARCHETYPE_SOURCES["MTEL"]),
            BusinessSegment("Reseller", 5.3, 251, 0.0, 0.5, {"tenants": 2650}, ARCHETYPE_SOURCES["MTEL"]),
        ],
        key_specs={"towers": 40563, "tenancy_ratio": 1.57, "fiber_km": 59239},
        as_of="2026-08-31",
        source_tier="T1",
    )

