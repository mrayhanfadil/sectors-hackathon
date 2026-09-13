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
import os
from server.report import numfmt as _nf

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
Archetype = Literal["single", "sotp", "infra", "bank", "coal", "unknown"]

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
        if self.archetype not in ("single", "sotp", "infra", "bank", "coal", "unknown"):
            errors.append(f"archetype {self.archetype!r} must be single|sotp|infra|bank|coal|unknown")
        if self.ipo and self.ipo.free_float_pct is not None:
            if not 0 < self.ipo.free_float_pct <= 100:
                errors.append(f"free_float_pct {self.ipo.free_float_pct} out of range")
        # holder pct should not exceed 100 sum (allow rounding 100.5)
        total_holder = sum(h.pct for h in self.holders)
        if self.holders and total_holder > 100.5:
            errors.append(f"holders sum {_nf.dec(total_holder, digits=1)}% > 100%")
        # segment pct should sum ~100 when provided (allow 99-101)
        seg_pcts = [s.revenue_share_pct for s in self.segments if s.revenue_share_pct is not None]
        if seg_pcts and not 99 <= sum(seg_pcts) <= 101:
            # only flag if >1 segment and all have pct
            if len(seg_pcts) == len(self.segments):
                errors.append(f"segment pct sum {_nf.dec(sum(seg_pcts), digits=1)}% != 100%")
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
- BOD: sebut 6 anggota RATU kalau ticker RATU. Untuk ticker lain, ambil dari Sectors company_report/filings, jangan hallucinate names.
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
- Search Sectors company_report/filings ("{ticker} IDX IPO history BOD") if holder/BOD missing — cite source+date.
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
# Dynamic archetype fixtures (offline dev / tests)
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
) -> CompanyProfile:
    """Dynamic archetype-driven CompanyProfile fixture generator."""
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
        return CompanyProfile(
            ticker=t,
            name=f"{t} Energy Tbk" if t != "UNKNOWN" else "Unknown Tbk",
            archetype="single",
            subsector="oil-holding",
            established=None,
            listing_board="IDX Main",
            history=[],
            ipo=None,
            holders=[],
            bod=[],
            commissioners=[],
            psc=[],
            segments=[
                BusinessSegment(
                    name="Core Oil & Gas / Upstream",
                    revenue_share_pct=100.0,
                    revenue_idr_bn=None,
                    yoy_pct=None,
                    qoq_pct=None,
                    specs={"gross_bopd": 169000, "net_bopd": 4056},
                    source=source_label,
                ),
            ],
            key_specs={"gross_bopd": 169000, "net_bopd": 4056},
            as_of=as_of_val,
            source_tier="T1",
        )

    elif arch_norm == "sotp":
        return CompanyProfile(
            ticker=t,
            name=f"{t} Nusantara Tbk" if t != "UNKNOWN" else "Unknown Tbk",
            archetype="sotp",
            subsector="conglomerate",
            established=None,
            listing_board="IDX Main",
            history=[],
            ipo=None,
            holders=[],
            bod=[],
            commissioners=[],
            psc=[],
            segments=[
                BusinessSegment(
                    name="Pillar A - Energy & Resources",
                    revenue_share_pct=50.0,
                    revenue_idr_bn=None,
                    yoy_pct=None,
                    qoq_pct=None,
                    specs={"capacity_mw": 120},
                    source=source_label,
                ),
                BusinessSegment(
                    name="Pillar B - Infrastructure & Logistics",
                    revenue_share_pct=30.0,
                    revenue_idr_bn=None,
                    yoy_pct=None,
                    qoq_pct=None,
                    specs={"dwt": 8600},
                    source=source_label,
                ),
                BusinessSegment(
                    name="Pillar C - Utilities & Services",
                    revenue_share_pct=20.0,
                    revenue_idr_bn=None,
                    yoy_pct=None,
                    qoq_pct=None,
                    specs={"water_lps": 2000},
                    source=source_label,
                ),
            ],
            key_specs={"pillars_count": 3, "diversification": "multi-sector"},
            as_of=as_of_val,
            source_tier="T1",
        )

    elif arch_norm == "infra":
        return CompanyProfile(
            ticker=t,
            name=f"{t} Infrastructure Tbk" if t != "UNKNOWN" else "Unknown Tbk",
            archetype="infra",
            subsector="tower-infra",
            established=None,
            listing_board="IDX Main",
            history=[],
            ipo=None,
            holders=[],
            bod=[],
            commissioners=[],
            psc=[],
            segments=[
                BusinessSegment(
                    name="Tower Leasing",
                    revenue_share_pct=85.0,
                    revenue_idr_bn=None,
                    yoy_pct=None,
                    qoq_pct=None,
                    specs={"towers": 40563},
                    source=source_label,
                ),
                BusinessSegment(
                    name="Fiber & Connectivity",
                    revenue_share_pct=15.0,
                    revenue_idr_bn=None,
                    yoy_pct=None,
                    qoq_pct=None,
                    specs={"fiber_km": 59239},
                    source=source_label,
                ),
            ],
            key_specs={"towers": 40563, "fiber_km": 59239, "tenancy_ratio": 1.57},
            as_of=as_of_val,
            source_tier="T1",
        )

    elif arch_norm == "bank":
        return CompanyProfile(
            ticker=t,
            name=f"Bank {t} Tbk" if t != "UNKNOWN" else "Unknown Tbk",
            archetype="bank",
            subsector="bank",
            established=None,
            listing_board="IDX Main",
            history=[],
            ipo=None,
            holders=[],
            bod=[],
            commissioners=[],
            psc=[],
            segments=[
                BusinessSegment(
                    name="Interest Income (Lending)",
                    revenue_share_pct=75.0,
                    revenue_idr_bn=None,
                    yoy_pct=None,
                    qoq_pct=None,
                    specs={"nim_pct": 5.5},
                    source=source_label,
                ),
                BusinessSegment(
                    name="Non-Interest / Fee-Based",
                    revenue_share_pct=25.0,
                    revenue_idr_bn=None,
                    yoy_pct=None,
                    qoq_pct=None,
                    specs={"casa_pct": 80.0},
                    source=source_label,
                ),
            ],
            key_specs={"roe": 0.197, "casa_pct": 80.0, "nim_pct": 5.5},
            as_of=as_of_val,
            source_tier="T1",
        )

    elif arch_norm == "coal":
        return CompanyProfile(
            ticker=t,
            name=f"{t} Energy Coal Tbk" if t != "UNKNOWN" else "Unknown Tbk",
            archetype="coal",
            subsector="coal",
            established=None,
            listing_board="IDX Main",
            history=[],
            ipo=None,
            holders=[],
            bod=[],
            commissioners=[],
            psc=[],
            segments=[
                BusinessSegment(
                    name="Coal Mining & Sales",
                    revenue_share_pct=85.0,
                    revenue_idr_bn=None,
                    yoy_pct=None,
                    qoq_pct=None,
                    specs={"production_mt": 65.0},
                    source=source_label,
                ),
                BusinessSegment(
                    name="Mining Services & Logistics",
                    revenue_share_pct=15.0,
                    revenue_idr_bn=None,
                    yoy_pct=None,
                    qoq_pct=None,
                    specs={"asp_usd": 85.0},
                    source=source_label,
                ),
            ],
            key_specs={"production_mt": 65.0, "asp_usd": 85.0, "royalty_pct": 14.0},
            as_of=as_of_val,
            source_tier="T1",
        )

    else:  # unknown
        return CompanyProfile(
            ticker=t,
            name=f"{t} Tbk" if t != "UNKNOWN" else "Unknown Tbk",
            archetype="unknown",
            subsector="general",
            established=None,
            listing_board="IDX Main",
            history=[],
            ipo=None,
            holders=[],
            bod=[],
            commissioners=[],
            psc=[],
            segments=[],
            key_specs={},
            as_of=as_of_val,
            source_tier="T1",
        )

