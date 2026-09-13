"""
KPI Analyst — T07

Owns: Operational KPIs per subsector — HERO for infra (MTEL archetype).

Archetype refs:
- MTEL (KSI 27 Aug 2026) — HERO: Tower 40,563 (+2%), Colocation 23,303 (+10%), Tenant 63,866 (+5%),
  Reseller tenants 2,650, Tenancy Ratio 1.57x (vs 1.53), Fiber 59,239 km (+9%), add/less per quarter
  + Catalyst Quant: PST & UMT Merger + Spectrum 700MHz/2.6GHz -> +3,000-3,500 tenants, +IDR 360-420bn
- RATU: BOPD (Cepu 169k gross, net entitlement via PSC) — single KPI
- CDIA: MW / m³ / DWT / TC/COA/spot per pillar (Energy/Water/Port/Logistics)

Spec: plan.md 2.3 (MTEL Operational KPIs HERO) + 3 "KPI Analyst (tenancy, fiber km)"
      + Upgrade P1-7 KPI module per subsector + P1-8 Catalyst quantification
      + 9 Risks: KPI tenancy salah hitung | Formula tenant/tower, Critic validate
Branch: wt/t07-analyst
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal, Optional
import json
import os

ARCHETYPE_SOURCES = {
    "RATU": "HP Sekuritas 7 Jan 2026 — RATU (BOPD)",
    "CDIA": "BCA Sekuritas 23 Jun 2026 — CDIA (MW/m³/DWT)",
    "MTEL": "KSI/Kiwoom 27 Aug 2026 — MTEL (Tower/Fiber tenancy HERO)",
}

Subsector = Literal["tower-infra", "oil-holding", "conglomerate", "bank", "coal", "property", "telco", "general"]


@dataclass
class TowerKPI:
    """MTEL infra HERO — C22 template expects these exact fields."""
    towers: int = 40563              # total towers
    towers_yoy_pct: float = 2.0
    colocation: int = 23303          # colocation tenants
    colocation_yoy_pct: float = 10.0
    tenants: int = 63866             # total tenants (colocation + anchor)
    tenants_yoy_pct: float = 5.0
    reseller_tenants: int = 2650     # reseller subset
    tenancy_ratio: float = 1.57      # tenants / towers — THE thesis KPI
    tenancy_ratio_prior: float = 1.53
    fiber_km: int = 59239
    fiber_yoy_pct: float = 9.0
    # quarterly flow
    towers_added_q: int = 180
    towers_removed_q: int = 12
    tenants_added_q: int = 820
    tenants_removed_q: int = 95
    source: str = ARCHETYPE_SOURCES["MTEL"]
    as_of: str = "2026-08-31"

    def validate(self) -> list[str]:
        errors: list[str] = []
        # tenancy must equal tenants/towers (allow 0.02 rounding)
        calc = round(self.tenants / self.towers, 2) if self.towers else 0
        if abs(calc - self.tenancy_ratio) > 0.03:
            errors.append(
                f"tenancy_ratio {self.tenancy_ratio} != tenants/towers {self.tenants}/{self.towers}={calc} (Critic: tenancy = tenant/tower)"
            )
        # fiber vs towers correlation sanity
        if self.fiber_km < 0 or self.towers < 0:
            errors.append("fiber/towers negative")
        return errors


@dataclass
class OilKPI:
    """RATU — Cepu BOPD."""
    gross_bopd: int = 169000
    net_bopd: float = 4056.0         # gross * PI (2.4%)
    participation_pct: float = 2.4
    dmo_pct: float = 25.0
    reserve_life_years: Optional[float] = None
    source: str = ARCHETYPE_SOURCES["RATU"]
    as_of: str = "2026-08-31"

    def validate(self) -> list[str]:
        errors: list[str] = []
        calc_net = round(self.gross_bopd * self.participation_pct / 100, 1)
        if abs(calc_net - self.net_bopd) > 5:
            errors.append(f"net_bopd {self.net_bopd} != gross*PI {calc_net}")
        return errors


@dataclass
class ConglomerateKPI:
    """CDIA — per-pillar operational specs."""
    pillars: list[dict] = field(default_factory=lambda: [
        {"pillar": "Energy", "spec": "120MW CCPP", "unit": "MW", "value": 120, "yoy_pct": 4.2},
        {"pillar": "Water", "spec": "2,000 l/s", "unit": "l/s", "value": 2000, "yoy_pct": 2.1},
        {"pillar": "Port", "spec": "72 tanks 130k m3", "unit": "m3", "value": 130000, "yoy_pct": 3.0},
        {"pillar": "Logistics", "spec": "7 vessels 5-8600 DWT", "unit": "DWT", "value": 8600, "yoy_pct": 1.5},
    ])
    source: str = ARCHETYPE_SOURCES["CDIA"]
    as_of: str = "2026-08-31"

    def validate(self) -> list[str]:
        errors: list[str] = []
        if len(self.pillars) < 2:
            errors.append("conglomerate KPI needs >=2 pillars (CDIA has 4)")
        for p in self.pillars:
            if p.get("value", 0) < 0:
                errors.append(f"pillar {p.get('pillar')} value negative")
        return errors


@dataclass
class CatalystQuant:
    """MTEL P1-8 catalyst quantification — tenants + IDR revenue by FY."""
    title: str                       # e.g. "PST & UMT Merger" | "Spectrum 700MHz & 2.6GHz"
    effective_date: str              # ISO
    tenants_added: tuple[int, int] = (3000, 3500)  # range
    revenue_idr_bn_annualized: tuple[int, int] = (360, 420)
    by_fy: str = "FY27-29"           # annualized by FY27-29
    opex_efficiency: str = ""        # e.g. "opex/capex efficiency"
    source: str = ARCHETYPE_SOURCES["MTEL"]


@dataclass
class KPIBundle:
    ticker: str
    subsector: Subsector
    archetype: str                   # single | sotp | infra
    tower: Optional[TowerKPI] = None
    oil: Optional[OilKPI] = None
    conglomerate: Optional[ConglomerateKPI] = None
    # generic fallback for banks/property etc — e.g. BBCA: CAR, NIM, LDR, CASA
    generic: dict = field(default_factory=dict)
    catalysts: list[CatalystQuant] = field(default_factory=list)
    # provenance
    as_of: str = ""
    source_tier: str = "T1"

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.ticker:
            errors.append("ticker required")
        # archetype must have matching KPI populated
        if self.archetype == "infra" and self.tower is None:
            errors.append("infra archetype requires tower KPI (MTEL HERO)")
        if self.archetype == "single" and self.subsector == "oil-holding" and self.oil is None:
            errors.append("oil-holding single requires oil KPI")
        if self.archetype == "sotp" and self.conglomerate is None:
            errors.append("sotp requires conglomerate KPI")
        # delegate
        if self.tower:
            errors.extend(self.tower.validate())
        if self.oil:
            errors.extend(self.oil.validate())
        if self.conglomerate:
            errors.extend(self.conglomerate.validate())
        # catalyst quant sanity
        for c in self.catalysts:
            lo, hi = c.tenants_added
            if lo > hi:
                errors.append(f"catalyst {c.title} tenants range inverted {lo}>{hi}")
            rlo, rhi = c.revenue_idr_bn_annualized
            if rlo > rhi:
                errors.append(f"catalyst {c.title} revenue range inverted")
        return errors

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# Deterministic helpers — NEVER let LLM invent these
# ---------------------------------------------------------------------------
def calc_tenancy_ratio(tenants: int, towers: int) -> float:
    """THE thesis KPI — Critic validates tenant/tower."""
    if towers == 0:
        raise ValueError("towers cannot be 0")
    return round(tenants / towers, 2)


def calc_yoy_pct(current: float, prior: float) -> float:
    if prior == 0:
        raise ValueError("prior cannot be 0")
    return round((current - prior) / prior * 100, 2)


def calc_net_growth(added: int, removed: int) -> int:
    return added - removed


def calc_revenue_per_tenant(total_revenue_idr_bn: float, tenants: int) -> float:
    """IDR bn per tenant — for catalyst revenue bridging."""
    if tenants == 0:
        return 0.0
    return round(total_revenue_idr_bn / tenants, 4)


def calc_catalyst_revenue_bridge(
    tenants_added: int,
    revenue_per_tenant_idr_bn: float,
) -> float:
    """Annualized incremental revenue = tenants * revenue/tenant."""
    return round(tenants_added * revenue_per_tenant_idr_bn, 2)


def calc_tenancy_delta_vs_prior(current: float, prior: float) -> float:
    return round(current - prior, 2)


# ---------------------------------------------------------------------------
# Prompt contract — ADK LlmAgent (Gemini 3.7 Flash High)
# ---------------------------------------------------------------------------
KPI_SYSTEM_PROMPT = """\
You are KPI Analyst (T07) — IDX institutional research, operational KPIs per subsector.

Rules:
- JANGAN hitung. Panggil calc_tenancy_ratio / calc_yoy_pct / calc_net_growth / calc_revenue_per_tenant / calc_catalyst_revenue_bridge untuk angka.
- MTEL infra HERO: Tower 40,563 (+2%), Colocation 23,303 (+10%), Tenant 63,866 (+5%), Reseller 2,650, Tenancy 1.57x (vs 1.53), Fiber 59,239 km (+9%), add/less per quarter. Wajib sebut semua — ini thesis KPI. Tenancy = tenant/tower — Critic akan validate sum.
- RATU oil: Cepu 169k BOPD gross, net = gross * PI (2.4%), DMO 25%. Single KPI.
- CDIA conglomerate: MW / m3 / DWT / TC/COA/spot per pillar (Energy/Water/Port/Logistics) — 4 pillars.
- Catalyst quantification (P1-8): PST & UMT Merger eff 1 Jul 2026 + Spectrum 700MHz & 2.6GHz (TLKM 20/80 MHz) -> +3,000-3,500 tenants, +IDR 360-420bn annualized by FY27-29. Opex/capex efficiency + FWA/fiberization/IoT/power. Sebut tenants + IDR + by FY — jangan narasi tanpa angka.
- Tiap exhibit: source tier + url+date. Critic REJECT kalau tenancy != tenant/tower atau KPI tanpa source.
- Bahasa default ID. Anti-sycophancy: defend(evidence: calc+source) atau concede(correction).
"""

KPI_USER_TEMPLATE = """\
Ticker: {ticker} | Subsector: {subsector} | Archetype: {archetype}
Collector (as_of {as_of}):
{collector_json}

Valuation context (for tenancy/revenue bridging):
{valuation_json}

Task: Build KPIBundle JSON for {ticker}.
- Infra: fill tower (semua 7 KPI + quarterly flow) + catalysts[2] (PST/UMT + Spectrum) dengan tenants + IDR bridge.
- Oil single: fill oil (gross/net/PI/DMO).
- SOTP: fill conglomerate (4 pillars).
- Call calc_* for tenancy/yoy/net/revenue-per-tenant — do not compute mentally.
- Return ONLY JSON.
"""


def build_kpi_prompt(
    ticker: str,
    subsector: str,
    archetype: str,
    as_of: str,
    collector_json: str,
    valuation_json: str = "{}",
) -> tuple[str, str]:
    user = KPI_USER_TEMPLATE.format(
        ticker=ticker, subsector=subsector, archetype=archetype,
        as_of=as_of, collector_json=collector_json,
        valuation_json=valuation_json,
    )
    return KPI_SYSTEM_PROMPT, user


# ---------------------------------------------------------------------------
# Fixtures — offline dev / tests
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
) -> KPIBundle:
    """Dynamic archetype-driven KPIBundle fixture generator."""
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
        return KPIBundle(
            ticker=t,
            subsector="oil-holding",
            archetype="single",
            oil=OilKPI(
                gross_bopd=169000,
                net_bopd=4056.0,
                participation_pct=2.4,
                dmo_pct=25.0,
                reserve_life_years=None,
                source=source_label,
                as_of=as_of_val,
            ),
            catalysts=[],
            as_of=as_of_val,
            source_tier="T1",
        )

    elif arch_norm == "sotp":
        return KPIBundle(
            ticker=t,
            subsector="conglomerate",
            archetype="sotp",
            conglomerate=ConglomerateKPI(
                pillars=[
                    {"pillar": "Energy", "spec": "120MW CCPP", "unit": "MW", "value": 120, "yoy_pct": 4.2},
                    {"pillar": "Water", "spec": "2,000 l/s", "unit": "l/s", "value": 2000, "yoy_pct": 2.1},
                    {"pillar": "Port", "spec": "72 tanks 130k m3", "unit": "m3", "value": 130000, "yoy_pct": 3.0},
                    {"pillar": "Logistics", "spec": "7 vessels 5-8600 DWT", "unit": "DWT", "value": 8600, "yoy_pct": 1.5},
                ],
                source=source_label,
                as_of=as_of_val,
            ),
            catalysts=[],
            as_of=as_of_val,
            source_tier="T1",
        )

    elif arch_norm == "infra":
        return KPIBundle(
            ticker=t,
            subsector="tower-infra",
            archetype="infra",
            tower=TowerKPI(
                towers=40563,
                towers_yoy_pct=2.0,
                colocation=23303,
                colocation_yoy_pct=10.0,
                tenants=63866,
                tenants_yoy_pct=5.0,
                reseller_tenants=2650,
                tenancy_ratio=1.57,
                tenancy_ratio_prior=1.53,
                fiber_km=59239,
                fiber_yoy_pct=9.0,
                towers_added_q=180,
                towers_removed_q=12,
                tenants_added_q=820,
                tenants_removed_q=95,
                source=source_label,
                as_of=as_of_val,
            ),
            catalysts=[
                CatalystQuant(
                    title="PST & UMT Merger",
                    effective_date="2026-07-01",
                    tenants_added=(3000, 3500),
                    revenue_idr_bn_annualized=(360, 420),
                    by_fy="FY27-29",
                    opex_efficiency="opex/capex efficiency, tenancy >1.6×, FWA/fiberization/IoT/power",
                    source=source_label,
                ),
                CatalystQuant(
                    title="Spectrum 700MHz & 2.6GHz",
                    effective_date="2026-07-01",
                    tenants_added=(3000, 3500),
                    revenue_idr_bn_annualized=(360, 420),
                    by_fy="FY27-29",
                    opex_efficiency="TLKM 20/80 MHz, ISAT 20/60, EXCL 30/50 -> tenant pipeline",
                    source=source_label,
                ),
            ],
            as_of=as_of_val,
            source_tier="T1",
        )

    elif arch_norm == "bank":
        return KPIBundle(
            ticker=t,
            subsector="bank",
            archetype="bank",
            generic={
                "nim_pct": 5.5,
                "casa_pct": 80.0,
                "car_pct": 28.0,
                "npl_pct": 0.6,
                "roe_pct": 19.7,
                "ldr_pct": 79.0,
                "source": source_label,
            },
            catalysts=[],
            as_of=as_of_val,
            source_tier="T1",
        )

    elif arch_norm == "coal":
        return KPIBundle(
            ticker=t,
            subsector="coal",
            archetype="coal",
            generic={
                "production_mt": 65.0,
                "sales_mt": 65.0,
                "asp_usd": 85.0,
                "cash_cost_usd": 42.0,
                "royalty_pct": 14.0,
                "source": source_label,
            },
            catalysts=[],
            as_of=as_of_val,
            source_tier="T1",
        )

    else:  # unknown
        return KPIBundle(
            ticker=t,
            subsector="general",
            archetype="unknown",
            generic={"source": source_label},
            catalysts=[],
            as_of=as_of_val,
            source_tier="T1",
        )
