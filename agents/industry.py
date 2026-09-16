"""
Industry / Macro Analyst - T07

Owns: Commodity (Brent), regulatory (SKK Migas), macro thematics (JPM 5 + Danantara $12bn).

Archetype refs:
- RATU: Commodity (Brent), Operator PSC, Regulatory (PSC/DMO), Natural decline
- CDIA: Pillar-specific (sedimentation, gas supply, vessel damage, climate)
- MTEL: Infra recurring - dependency on operators, satellite/Open RAN, regulatory, financing
- JPM 2026 Outlook (02 Dec 2025): 5 thematics + Danantara Value-Up $12bn (0.8% GDP) + $14bn SWF

Spec: plan.md 2.4 (JPM archetype) + 3 "Industry/Macro (Brent/IEA/regulator)"
Branch: wt/t07-analyst
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal, Optional
import json
import os

ARCHETYPE_SOURCES = {
    "RATU": "HP Sekuritas 7 Jan 2026 - RATU",
    "CDIA": "BCA Sekuritas 23 Jun 2026 - CDIA",
    "MTEL": "KSI/Kiwoom 27 Aug 2026 - MTEL",
    "JPM": "J.P. Morgan 02 Dec 2025 - Indonesia Equity 2026 Outlook (52p)",
    "IEA": "IEA Oil Market Report",
}

ThematicId = Literal["T1_consumption", "T2_tsr", "T3_foreign", "T4_fiscal", "T5_danantara"]


@dataclass
class CommodityAssumption:
    commodity: str              # "Brent" | "WTI" | "Newcastle Coal" etc
    unit: str                   # "USD/bbl" | "USD/t" etc
    spot: float
    forecast_2026: Optional[float] = None
    forecast_2027: Optional[float] = None
    yoy_pct: Optional[float] = None
    driver: str = ""            # e.g. "IEA demand +1.1mb/d, OPEC+ spare 5.2mb/d"
    source: str = ""
    as_of: str = ""


@dataclass
class RegulatorContext:
    regulator: str              # "SKK Migas" | "OJK" | "MEMR" | "Kominfo" | "BI"
    regime: str                 # e.g. "PSC Cost Recovery" | "Gross Split"
    key_term: str               # e.g. "DMO 25%, expiry 2035"
    change_risk: str = ""       # e.g. "PP 28/2025 SLA, positive fictitious approval"
    source: str = ""


@dataclass
class Thematic:
    id: ThematicId
    title: str
    jpm_source_page: str        # e.g. "p13" / "p28"
    description: str
    related_sectors: list[str] = field(default_factory=list)
    our_exposure: str = ""      # how ticker maps to this theme
    catalyst_quant: str = ""    # e.g. Danantara $12bn = 0.8% GDP
    source: str = ""


@dataclass
class DanantaraContext:
    structure: str = "BPI Danantara (Holding) + DAM (Asset Mgmt) + DIM (Investment Mgmt)"
    dry_powder_usd_bn: float = 12.0   # JPM Fig54: $5bn 2025 div + $5bn 2026E + $3bn Patriot - $1.8bn Garuda
    gdp_pct: float = 0.8
    swf_commitments_usd_bn: float = 14.0  # >$14bn callable
    priority_sectors: list[str] = field(default_factory=lambda: [
        "Downstream mineral (HPAL/nickel)", "Renewable/Energy", "Healthcare",
        "Food security", "Digital infra", "Industrial estate", "Logistics/Port",
        "Water", "Housing/Property"
    ])
    market_signal: str = "SOE ex-banks +25% YTD vs MXID (JPM Fig 55)"
    source: str = "JPM p28-29; CNBC Indonesia 5 Nov 2025; Danantara.go.id"


@dataclass
class IndustryOutlook:
    ticker: str
    subsector: str
    archetype: str
    commodities: list[CommodityAssumption] = field(default_factory=list)
    regulator: Optional[RegulatorContext] = None
    thematics: list[Thematic] = field(default_factory=list)
    danantara: Optional[DanantaraContext] = None
    sector_stance: str = ""     # OW | N | UW + rationale
    index_target: dict = field(default_factory=dict)  # {base: 9100, bull: 10000, bear: 7800}
    as_of: str = ""
    source_tier: str = "T1"

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.ticker:
            errors.append("ticker required")
        valid_ids = {"T1_consumption", "T2_tsr", "T3_foreign", "T4_fiscal", "T5_danantara"}
        for t in self.thematics:
            if t.id not in valid_ids:
                errors.append(f"thematic {t.id!r} not in JPM 5")
        if self.danantara:
            if not 5 <= self.danantara.dry_powder_usd_bn <= 30:
                errors.append(f"Danantara dry powder {self.danantara.dry_powder_usd_bn}bn outside 5-30")
            if not 0.3 <= self.danantara.gdp_pct <= 2.0:
                errors.append(f"Danantara gdp_pct {self.danantara.gdp_pct}% outside 0.3-2.0")
        for c in self.commodities:
            if c.spot is not None and c.spot <= 0:
                errors.append(f"commodity {c.commodity} spot {c.spot} <=0")
            if c.forecast_2026 is not None and c.forecast_2026 <= 0:
                errors.append(f"commodity {c.commodity} forecast_2026 <=0")
        return errors

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# Deterministic helpers - NEVER let LLM invent these
# ---------------------------------------------------------------------------
def calc_yoy_pct(current: float, prior: float) -> float:
    if prior == 0:
        raise ValueError("prior cannot be 0")
    return round((current - prior) / prior * 100, 2)


def calc_commodity_sensitivity(
    revenue_idr_bn: float,
    commodity_exposure_pct: float,
    commodity_move_pct: float,
) -> dict:
    """Simple sensitivity: delta if commodity moves X%."""
    exposed = revenue_idr_bn * commodity_exposure_pct / 100
    delta = exposed * commodity_move_pct / 100
    return {
        "exposed_idr_bn": round(exposed, 2),
        "delta_idr_bn": round(delta, 2),
        "delta_pct_of_total": round(delta / revenue_idr_bn * 100, 2) if revenue_idr_bn else 0,
    }


def calc_danantara_gdp_pct(dry_powder_usd_bn: float, gdp_usd_bn: float = 1500) -> float:
    """JPM: 12 / ~1500 = 0.8%."""
    return round(dry_powder_usd_bn / gdp_usd_bn * 100, 2)


# ---------------------------------------------------------------------------
# Prompt contract - ADK LlmAgent (Gemini 3.7 Flash High)
# ---------------------------------------------------------------------------
INDUSTRY_SYSTEM_PROMPT = """\
You are Industry/Macro Analyst (T07) - IDX institutional research.

Rules:
- JANGAN hitung. Panggil calc_yoy_pct / calc_commodity_sensitivity / calc_danantara_gdp_pct untuk angka.
- Brent: sebut spot + IEA demand/supply + OPEC+ spare. Kutip IEA OMR bulan/tahun + url. Jangan ngarang harga - pakai collector spot.
- IEA: cite IEA Oil Market Report dengan bulan/tahun + url. Kalau tidak ada, label source T2 dan flag estimated.
- Regulator: RATU=SKK Migas PSC/DMO 25% expiry 2035. MTEL=Kominfo 700MHz/2.6GHz. Bank=OJK/BI. Sebut regime + key term + change risk (PP 28/2025).
- JPM 5 thematics - WAJIB mapping tiap sektor OW/N/UW ke >=1 thematic. Table: Theme | Description | Related sectors | Our exposure. Critic REJECT kalau OW tanpa theme.
- Danantara: $12bn = 0.8% GDP (JPM Fig 54), >$14bn SWF commitments, 9 priority sectors. Sebut struktur BPI+DAM+DIM + market signal SOE +25% YTD. Source: JPM p28-29 + CNBC Indonesia + danantara.go.id.
- Index target: JCI 9,100 base / 10,000 bull / 7,800 bear (JPM 02 Dec 2025, priced 28 Nov 2025) - sebut EPS 8% x 15x flat bridge. Jangan ubah angka.
- Bahasa default ID. Setiap klaim: source tier + url+date. Anti-sycophancy: defend(evidence) atau concede(correction).
"""

INDUSTRY_USER_TEMPLATE = """\
Ticker: {ticker} | Subsector: {subsector} | Archetype: {archetype}
Collector (as_of {as_of}):
{collector_json}

Commodities snapshot:
{commodity_json}

JPM context (5 thematics + Danantara):
{jpm_json}

Task: Build IndustryOutlook JSON for {ticker}.
- Fill commodities[] (Brent spot + forecast + driver with IEA cite), regulator (SKK Migas / Kominfo / OJK), thematics[5] with Our exposure per ticker, danantara block, sector_stance OW/N/UW + index_target.
- Call calc_* for yoy/sensitivity/gdp%. Do not compute mentally.
- Return ONLY JSON.
"""


def build_industry_prompt(
    ticker: str,
    subsector: str,
    archetype: str,
    as_of: str,
    collector_json: str,
    commodity_json: str = "[]",
    jpm_json: str = "{}",
) -> tuple[str, str]:
    user = INDUSTRY_USER_TEMPLATE.format(
        ticker=ticker, subsector=subsector, archetype=archetype,
        as_of=as_of, collector_json=collector_json,
        commodity_json=commodity_json, jpm_json=jpm_json,
    )
    return INDUSTRY_SYSTEM_PROMPT, user


# ---------------------------------------------------------------------------
# Fixtures - offline dev / tests (seed=42 style)
# ---------------------------------------------------------------------------
JPM_FIVE_THEMATICS: list[Thematic] = [
    Thematic("T1_consumption", "Domestic consumption recovery", "p13",
             "1-2Y weak purchasing power -> 2026 recovery on gov spending + online gambling -48% + raw material normalization",
             ["Consumer Staples", "Consumer Discretionary", "Healthcare", "Cement", "Property"], "", "", ARCHETYPE_SOURCES["JPM"]),
    Thematic("T2_tsr", "Emerging TSR improvement narratives", "p18",
             "10-15Y PBV de-rating + 42% net cash + ROE<COE -> buybacks/dividends/spin-offs; LQ45 PBV at GFC/COVID lows",
             ["Overall Market Re-Rating"], "", "", ARCHETYPE_SOURCES["JPM"]),
    Thematic("T3_foreign", "(Re)-attracting foreign investment", "p21",
             "FDI -28% + FPI -$14bn -> tight liquidity + IDR weakness; PP 28/2025 + Easing cycle = re-attraction",
             ["Macro", "Banks"], "", "", ARCHETYPE_SOURCES["JPM"]),
    Thematic("T4_fiscal", "Fiscal policy in focus", "p24",
             "Soft revenue -6% YoY 10M25; 5 quick wins M0 IDR200tn + IDR60tn arrears + CoreTax; 2026 Budget +10% optimistic vs JPM 5-6%",
             ["Macro", "Metals & Mining", "Coal", "Energy", "Consumer"], "", "", ARCHETYPE_SOURCES["JPM"]),
    Thematic("T5_danantara", "Danantara: The swing factor", "p28",
             "2025 $5bn div parked -> 2026 $12bn deployment (0.8% GDP) + >$14bn SWF; 9 priority sectors; SOE ex-banks +25% YTD",
             ["SOE Companies", "Macro", "Overall Market"], "", "", ARCHETYPE_SOURCES["JPM"]),
]


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
) -> IndustryOutlook:
    """Dynamic archetype-driven IndustryOutlook fixture generator."""
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

    danantara_block = DanantaraContext()
    index_target_dict = {"base": 9100, "bull": 10000, "bear": 7800, "eps_growth": 8, "pe": 15, "bridge": "8500x1.08x1.00"}

    if arch_norm == "single":
        return IndustryOutlook(
            ticker=t,
            subsector="oil-holding",
            archetype="single",
            commodities=[
                CommodityAssumption(
                    commodity="Brent",
                    unit="USD/bbl",
                    spot=82.0,
                    forecast_2026=80.0,
                    forecast_2027=78.0,
                    yoy_pct=-2.4,
                    driver="IEA OMR Jan 2026: demand +1.1mb/d, OPEC+ spare 5.2mb/d",
                    source=source_label,
                    as_of=as_of_val,
                ),
            ],
            regulator=RegulatorContext(
                regulator="SKK Migas",
                regime="PSC Cost Recovery",
                key_term="DMO 25%, Cepu expiry 2035",
                change_risk="PP 28/2025: SLA + positive fictitious approval",
                source=source_label,
            ),
            thematics=JPM_FIVE_THEMATICS,
            danantara=danantara_block,
            sector_stance="UW Energy (JPM) - single-pillar commodity exposure hedged via PSC floor",
            index_target=index_target_dict,
            as_of=as_of_val,
            source_tier="T1",
        )

    elif arch_norm == "sotp":
        return IndustryOutlook(
            ticker=t,
            subsector="conglomerate",
            archetype="sotp",
            commodities=[
                CommodityAssumption(
                    commodity="Coal",
                    unit="USD/t",
                    spot=135.0,
                    forecast_2026=130.0,
                    forecast_2027=125.0,
                    yoy_pct=-3.7,
                    driver="Global multi-pillar energy balance",
                    source=source_label,
                    as_of=as_of_val,
                ),
            ],
            regulator=RegulatorContext(
                regulator="Multi-Ministry (MEMR/MoT)",
                regime="Multi-sector concession/licensing",
                key_term="Concession terms across energy/ports/water",
                change_risk="PP 28/2025 regulatory harmonization",
                source=source_label,
            ),
            thematics=JPM_FIVE_THEMATICS,
            danantara=danantara_block,
            sector_stance="OW Conglomerates (JPM T2_tsr / T5_danantara) - multi-pillar diversification & TSR re-rating",
            index_target=index_target_dict,
            as_of=as_of_val,
            source_tier="T1",
        )

    elif arch_norm == "infra":
        return IndustryOutlook(
            ticker=t,
            subsector="tower-infra",
            archetype="infra",
            commodities=[],
            regulator=RegulatorContext(
                regulator="Kominfo",
                regime="Spectrum licensing",
                key_term="700MHz & 2.6GHz allocation (TLKM 20/80 MHz)",
                change_risk="Spectrum 700MHz & 2.6GHz -> tenant rollout pipeline",
                source=source_label,
            ),
            thematics=JPM_FIVE_THEMATICS,
            danantara=danantara_block,
            sector_stance="N Communication Services (JPM) - infra recurring, tower demand tied to FWA/fiberization",
            index_target=index_target_dict,
            as_of=as_of_val,
            source_tier="T1",
        )

    elif arch_norm == "bank":
        return IndustryOutlook(
            ticker=t,
            subsector="bank",
            archetype="bank",
            commodities=[],
            regulator=RegulatorContext(
                regulator="OJK / Bank Indonesia",
                regime="Banking Prudential Regulation",
                key_term="CAR min 15%, BI-Rate policy, LDR target",
                change_risk="BI monetary easing & liquidity requirements",
                source=source_label,
            ),
            thematics=JPM_FIVE_THEMATICS,
            danantara=danantara_block,
            sector_stance="OW Financials (JPM T3_foreign) - loan growth 10-12%, NIM resilience, ROE expansion",
            index_target=index_target_dict,
            as_of=as_of_val,
            source_tier="T1",
        )

    elif arch_norm == "coal":
        return IndustryOutlook(
            ticker=t,
            subsector="coal",
            archetype="coal",
            commodities=[
                CommodityAssumption(
                    commodity="Newcastle Coal",
                    unit="USD/t",
                    spot=140.0,
                    forecast_2026=135.0,
                    forecast_2027=130.0,
                    yoy_pct=-3.5,
                    driver="Thermal coal power demand in Asia",
                    source=source_label,
                    as_of=as_of_val,
                ),
            ],
            regulator=RegulatorContext(
                regulator="MEMR (ESDM)",
                regime="IUPK / Mining Concession",
                key_term="DMO 25% price cap $70/t for power, progressive royalty 14-28%",
                change_risk="PP 28/2025 SLA & RKAB approval",
                source=source_label,
            ),
            thematics=JPM_FIVE_THEMATICS,
            danantara=danantara_block,
            sector_stance="UW Coal (JPM T4_fiscal) - high cash dividend yield offset by ASP moderation",
            index_target=index_target_dict,
            as_of=as_of_val,
            source_tier="T1",
        )

    else:  # unknown
        return IndustryOutlook(
            ticker=t,
            subsector="general",
            archetype="unknown",
            commodities=[],
            regulator=RegulatorContext(
                regulator="IDX / OJK",
                regime="Capital Market Regulation",
                key_term="Public listing disclosure & governance",
                change_risk="OJK free-float & governance rules",
                source=source_label,
            ),
            thematics=JPM_FIVE_THEMATICS,
            danantara=danantara_block,
            sector_stance="N General Market - neutral stance pending sector categorization",
            index_target=index_target_dict,
            as_of=as_of_val,
            source_tier="T1",
        )
