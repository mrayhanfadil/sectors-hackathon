"""Institutional Typst PDF report renderer.

Exposes `render_report(ticker, archetype='auto', out_path=None)` with 6-gate method selection
verdict injection and rating-override handling.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
FONTS_DIR = PROJECT_ROOT / "assets" / "fonts"
TEMPLATES_DIR = PROJECT_ROOT / "server" / "report" / "typst"
TEMPLATES_FALLBACK_DIR = PROJECT_ROOT / "templates" / "typst"
CACHE_ROOT = Path(os.environ.get("TYPST_CACHE_DIR", str(PROJECT_ROOT / "output" / "cache")))

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from agents.valuation.gates import (
    evaluate,
    GateVerdict,
    DOMAIN_BANK,
    DOMAIN_INSURANCE,
    DOMAIN_MULTIFINANCE,
    DOMAIN_SECURITIES,
    DOMAIN_REIT,
    DOMAIN_MINING,
    DOMAIN_OIL_GAS,
    DOMAIN_PLANTATION,
    DOMAIN_HOLDING_DISSIMILAR,
    DOMAIN_SINGLE_BUSINESS,
)

ARCHETYPE_TEMPLATE_FILES = {
    "update": "report_update.typ",
    "single": "report_single.typ",
    "sotp": "report_sotp.typ",
    "infra": "report_infra.typ",
    "strategy": "report_strategy.typ",
}


_GATE_REQUIRED_KEYS = (
    "filing_history_years",
    "ebit_positive_count",
    "d_de_ratio",
    "net_debt_to_ebitda",
    "interest_coverage",
    "shareholders_equity",
    "nci_pct",
    "revenue_drivers",
    "has_steady_state_3y",
    "life_cycle_stage",
)


def _domain_from_sector(sector: str) -> str:
    """Map a fixture meta.sector string onto a Gate-0 domain.

    Only the sector string (real fixture input) is used; anything
    unrecognised defaults to single-business going concern.
    """
    s = (sector or "").lower()
    if any(k in s for k in ("bank", "perbankan", "financial", "keuangan")):
        return DOMAIN_BANK
    if any(k in s for k in ("asuransi", "insurance")):
        return DOMAIN_INSURANCE
    if any(k in s for k in ("multifinance", "pembiayaan")):
        return DOMAIN_MULTIFINANCE
    if any(k in s for k in ("sekuritas", "securities")):
        return DOMAIN_SECURITIES
    if "reit" in s:
        return DOMAIN_REIT
    if any(k in s for k in ("mining", "tambang", "batubara", "coal", "nikel", "mineral", "emas")):
        return DOMAIN_MINING
    if any(k in s for k in ("migas", "oil", "gas")):
        return DOMAIN_OIL_GAS
    if any(k in s for k in ("plantation", "perkebunan", "sawit", "cpo")):
        return DOMAIN_PLANTATION
    if any(k in s for k in ("conglomerate", "diversified", "konglomerat", "dissimilar")):
        return DOMAIN_HOLDING_DISSIMILAR
    return DOMAIN_SINGLE_BUSINESS


def _get_ticker_gate_params(ticker: str, data: dict) -> dict[str, Any]:
    """Derive evaluation inputs for 6-gate framework from report data — honestly.

    - upside_pct comes from cover.rating_box only (None when absent, never a
      fabricated 20.0/27.1/38.0/-60.0).
    - domain comes from data["gate_inputs"]["domain"] or the meta.sector
      keyword map (default single business).
    - Every other gate input must be present in data["gate_inputs"]; absent
      inputs raise ValueError naming them instead of using fabricated
      per-ticker numbers.
    """
    t = ticker.upper().strip()
    cover = data.get("cover", {}).get("rating_box", {})
    tp = cover.get("tp")
    price = cover.get("price")
    upside = cover.get("upside_pct")
    if upside is not None:
        upside_pct: float | None = float(upside)
    elif tp and price:
        upside_pct = (float(tp) - float(price)) / float(price) * 100.0
    else:
        upside_pct = None

    gi = data.get("gate_inputs") or {}
    if not isinstance(gi, dict):
        gi = {}
    domain = gi.get("domain") or _domain_from_sector((data.get("meta") or {}).get("sector", ""))
    missing = [k for k in _GATE_REQUIRED_KEYS if k not in gi]
    if missing:
        raise ValueError(
            f"gate inputs absent for {t}: missing {missing} — refusing fabricated "
            f"gate params (add data['gate_inputs'])")
    params: dict[str, Any] = {"domain": domain, "upside_pct": upside_pct}
    params.update({k: gi[k] for k in _GATE_REQUIRED_KEYS})
    return params


def _build_gate_verdict_dict(ticker: str, verdict: GateVerdict, params: dict, rating_action: str) -> dict[str, Any]:
    """Convert GateVerdict into dictionary matching panel design."""
    t = ticker.upper().strip()
    primary = verdict.primary
    secondary = verdict.secondary or "—"
    thin_data = ("1a_filing_history" in verdict.gates_failed) or ("1a" in verdict.gates_failed) or verdict.thin_data
    rating_override = verdict.rating_override

    # Primary display formatting
    if primary == "FCFF/WACC DCF":
        primary_display = "DCF"
    elif primary == "DCF (shortened horizon)":
        primary_display = "DCF"
    elif primary == "DDM / Excess Return":
        primary_display = "DDM"
    elif primary == "NAV / Reserve-based":
        primary_display = "NAV"
    elif primary == "SOTP":
        primary_display = "SOTP"
    else:
        primary_display = primary

    # Secondary display formatting
    if t == "MTEL":
        secondary_display = "SOTP"
    elif primary == "DDM / Excess Return":
        secondary_display = "Excess Return"
    elif primary == "NAV / Reserve-based":
        secondary_display = "DCF"
    elif secondary == "Relative Valuation":
        secondary_display = "Relative"
    else:
        secondary_display = secondary

    # Rationale generators for gates 0-5
    # Gate 0
    if primary == "DDM / Excess Return" or params.get("domain") == DOMAIN_BANK:
        g0_rat = "financial institution (bank) -> DDM primary"
    elif primary == "NAV / Reserve-based" or params.get("domain") == DOMAIN_MINING:
        g0_rat = "mining / commodity finite reserves -> NAV primary"
    elif primary == "SOTP" or params.get("domain") == DOMAIN_HOLDING_DISSIMILAR:
        g0_rat = "holding company with dissimilar business lines"
    elif t == "RATU":
        g0_rat = "energy pure-play, DCF candidate"
    elif t == "MTEL":
        g0_rat = "telco infrastructure, DCF candidate"
    elif t in ("JCI", "IHSG", "JPM"):
        g0_rat = "macro market-level strategy outlook"
    else:
        g0_rat = "single business line going concern, DCF candidate"

    # Gate 1
    hist_y = params.get("filing_history_years", 8)
    ebit_c = params.get("ebit_positive_count", 3)
    if thin_data:
        g1_rat = f"{hist_y}y filing history <4y (shortened horizon)"
    else:
        g1_rat = f"{hist_y}y filing history, EBIT+ in {ebit_c}/3y"

    # Gate 2
    nci = params.get("nci_pct", 0.0)
    if nci <= 15:
        g2_rat = f"{int(nci)}% NCI, DCF proceeds normally"
    elif nci <= 40:
        g2_rat = f"{int(nci)}% NCI (15-40%), SOTP cross-check"
    else:
        g2_rat = f"{int(nci)}% NCI >40%, SOTP primary"

    # Gate 3
    if params.get("domain") == DOMAIN_MINING or "commodity_coal" in params.get("revenue_drivers", []):
        g3_rat = "commodity-driven cycle, NAV primary"
    elif params.get("domain") == DOMAIN_BANK:
        g3_rat = "banking operations, DDM as usual"
    else:
        g3_rat = "volume-driven, DCF as usual"

    # Gate 4
    stage = params.get("life_cycle_stage", "mature")
    if params.get("domain") == DOMAIN_BANK:
        g4_rat = "mature, stable dividend flow"
    else:
        g4_rat = f"{stage}, stable FCF"

    # Gate 5
    upside = params.get("upside_pct")
    if rating_override == "Review Required":
        g5_rat = f"upside {upside:+.1f}% out of band -> Review Required" if upside is not None else "out of band -> Review Required"
    elif upside is not None:
        g5_rat = f"upside {upside:+.1f}% in band"
    else:
        g5_rat = "valuation in normal bounds"

    gates = [
        {
            "gate": "0",
            "name": "Business model",
            "passed": "0_business_model" in verdict.gates_passed or "0" in verdict.gates_passed,
            "verdict": ("✓" if ("0_business_model" in verdict.gates_passed or "0" in verdict.gates_passed) else "✗") + " Business model",
            "rationale": g0_rat,
        },
        {
            "gate": "1",
            "name": "Data eligibility",
            "passed": not thin_data and not any(f.startswith("1") for f in verdict.gates_failed),
            "verdict": ("⚠" if thin_data else ("✓" if not any(f.startswith("1") for f in verdict.gates_failed) else "✗")) + " Data eligibility",
            "rationale": g1_rat,
        },
        {
            "gate": "2",
            "name": "NCI structure",
            "passed": not any(f.startswith("2") for f in verdict.gates_failed),
            "verdict": ("✓" if not any(f.startswith("2") for f in verdict.gates_failed) else "✗") + " NCI structure",
            "rationale": g2_rat,
        },
        {
            "gate": "3",
            "name": "Cyclicality",
            "passed": not any(f.startswith("3") for f in verdict.gates_failed),
            "verdict": ("✓" if not any(f.startswith("3") for f in verdict.gates_failed) else "✗") + " Cyclicality",
            "rationale": g3_rat,
        },
        {
            "gate": "4",
            "name": "Life cycle",
            "passed": not any(f.startswith("4") for f in verdict.gates_failed),
            "verdict": ("✓" if not any(f.startswith("4") for f in verdict.gates_failed) else "✗") + " Life cycle",
            "rationale": g4_rat,
        },
        {
            "gate": "5",
            "name": "Output sanity",
            "passed": rating_override is None and not any(f.startswith("5") for f in verdict.gates_failed),
            "verdict": ("✓" if (rating_override is None and not any(f.startswith("5") for f in verdict.gates_failed)) else "⚠") + " Output sanity",
            "rationale": g5_rat,
        },
    ]

    return {
        "primary": primary_display,
        "secondary": secondary_display,
        "rating": rating_action,
        "rating_override": rating_override,
        "rating-override": rating_override,
        "thin_data": thin_data,
        "thin-data": thin_data,
        "gates_passed": verdict.gates_passed,
        "gates_failed": verdict.gates_failed,
        "reasons": verdict.reasons,
        "gates": gates,
    }


def _load_or_build_report_data(ticker: str, archetype: str) -> dict[str, Any]:
    """Build structured report data dict from Sectors-backed inputs only."""
    t = ticker.upper().strip()
    # Sectors-only rule (Sep 2026): static demo fixtures purged. No fixture
    # interception exists in the prod loader — unknown tickers fall through
    # to honest-empty skeletons (BBCA/ADRO) or _build_live_payload, which
    # 422s without data/assumptions/{T}.json. Tests use explicit inline
    # scaffolding (see synthetic payloads in test_template_leak.py).

    months = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agt", "Sep", "Okt", "Nov", "Des"]
    # No fixture or builder for this ticker: honest-empty exhibits + source
    # note (never fabricated tp/charts/financials).
    if t in ("BBCA", "ADRO"):
        _name, _sector = {
            "BBCA": ("Bank Central Asia", "Financials — Perbankan"),
            "ADRO": ("Alamtri Resources Indonesia", "Energi — Pertambangan Batubara"),
        }[t]
        _note = "no fixture/builder (Sectors pending) — refusing fabricated exhibits"
        return {
            "meta": {
                "template": archetype if archetype != "auto" else "single",
                "ticker": t,
                "company_name": _name,
                "sector": _sector,
                "report_type": "Initiation",
                "date": "31 Agt 2026",
                "prepared_by": "RESEARCH — Sectors Hackathon 2026",
                "language": "id",
                "data_warning": _note,
            },
            "cover": {
                "rating_box": {
                    "action": None,
                    "tp": None,
                    "prev_tp": None,
                    "price": None,
                    "upside_pct": None,
                    "key_takeaways": [],
                    "note": _note,
                },
                "vs_jci": {
                    "ytd_abs": None,
                    "ytd_rel": None,
                    "source": _note,
                    "chart": {"labels": months, "series": [[], []]},
                },
                "shares": {"outstanding": None, "unit": "bn", "free_float_pct": None},
                "shareholders": [],
                "shareholders_src": _note,
                "esg": {"found": False},
            },
            "financial_highlights": {"source": _note, "years": [], "rows": []},
            "segments": [],
            "kpis": [],
            "thesis": [],
            "valuation": {"methods": [], "note": _note},
            "financials": [],
            "risks": [],
            "peers": {"tables": []},
            "exhibits": [],
        }

    # Generic fallback
    from server.routers.pdf import _build_live_payload
    return _build_live_payload(t, archetype if archetype != "auto" else None)


def _resolve_archetype(ticker: str, data: dict, requested_archetype: str) -> str:
    """Resolve archetype name from ticker / data / request."""
    if requested_archetype and requested_archetype != "auto":
        return requested_archetype
    t = ticker.upper().strip()
    if t in ("JCI", "IHSG", "JPM"):
        return "strategy"
    if t in ("MTEL", "POWR", "TOWR", "TLKM", "ISAT", "EXCL"):
        return "infra"
    if t == "CDIA":
        return "sotp"
    # meta.template explicit override wins (mirrors scripts/select_template.py
    # precedence 1): commodity splits of one mine (AMMN Cu/Au, Batu Hijau) are
    # pillar analysis, not dissimilar SOTP businesses (gate: NCI 1.7%, domain
    # mining -> no SOTP cross-check), so they must not flip single -> sotp via
    # the segments>1 rule. No-op for other tickers (their meta.template already
    # matches the archetype resolved below).
    meta_tpl = data.get("meta", {}).get("template")
    if meta_tpl in ARCHETYPE_TEMPLATE_FILES:
        return meta_tpl
    segs = data.get("segments") or []
    if len(segs) > 1:
        return "sotp"
    return "single"


def _generate_charts(ticker: str, data: dict, palette: dict) -> Path:
    """Call chart engine to create necessary chart PNGs with placeholder fallback."""
    cache = CACHE_ROOT / f"render_{ticker.lower()}" / "charts"
    cache.mkdir(parents=True, exist_ok=True)
    try:
        from render_typst import generate_charts
        generate_charts(ticker, data, palette)
    except Exception as e:
        print(f"[warn] generate_charts: {e}")

    # Ensure all referenced chart images exist so typst sandbox never throws missing file
    chart_names = [
        "vs_jci.png", "vs_jci_narrow.png", "segment_donut.png", "kpi_bars.png", "pbv_bands.png",
        "wacc_breakdown.png", "sensitivity_heatmap.png", "scenario_bars.png",
        "ev_equity_waterfall.png", "margin_trajectory.png", "production_cost.png",
        "revenue_combo.png", "ebitda_combo.png", "netprofit_combo.png",
        "pe_hist_band.png", "pbv_hist_band.png",
        "index_trend.png",
        "relval_bars.png", "peer_pe.png", "peer_evebitda.png", "peer_pb.png",
    ]
    try:
        from PIL import Image
        for name in chart_names:
            p = cache / name
            if not p.exists():
                img = Image.new("RGB", (600, 300), color=(249, 250, 251))
                img.save(p)
    except Exception:
        pass

    if CACHE_ROOT != Path("/tmp"):
        tmp_cache = Path(f"/tmp/render_{ticker.lower()}/charts")
        try:
            tmp_cache.mkdir(parents=True, exist_ok=True)
            for f in cache.glob("*.png"):
                shutil.copy2(f, tmp_cache / f.name)
        except Exception:
            pass

    return cache


def compile_typst(input_typ: Path, output_pdf: Path, data_path: Path | None = None, ticker: str | None = None) -> bool:
    """Compile typst template using CLI."""
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["typst", "compile", "--root", "/"]
    if FONTS_DIR.exists():
        cmd.extend(["--font-path", str(FONTS_DIR)])
    if ticker:
        cmd.extend(["--input", f"ticker={ticker}"])
    if data_path:
        cmd.extend(["--input", f"data_path={data_path}"])
    cmd.extend([str(input_typ), str(output_pdf)])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode == 0:
        return True
    print(f"[fail] typst compile error: {result.stderr}", file=sys.stderr)
    return False


def render_report(ticker: str, archetype: str = "auto", out_path: str | Path | None = None) -> str:
    """Main institutional report rendering entrypoint.
    
    Returns path to rendered PDF file (str).
    """
    t = ticker.upper().strip()
    data = _load_or_build_report_data(t, archetype)
    resolved_archetype = _resolve_archetype(t, data, archetype)
    data.setdefault("meta", {})["template"] = resolved_archetype
    data["meta"]["ticker"] = t

    # Run 6-gate evaluation
    params = _get_ticker_gate_params(t, data)
    verdict = evaluate(t, **params)

    # Determine initial rating
    orig_rating = data.get("cover", {}).get("rating_box", {}).get("action", "BUY")
    if verdict.rating_override == "Review Required":
        final_rating = "Review Required"
        data.setdefault("cover", {}).setdefault("rating_box", {})["action"] = "Review Required"
    else:
        final_rating = orig_rating

    # Inject gate verdict into context dict
    gate_verdict_dict = _build_gate_verdict_dict(t, verdict, params, final_rating)
    data["gate-verdict"] = gate_verdict_dict
    data["gate_verdict"] = gate_verdict_dict

    # Set up cache and data_path
    cache_dir = CACHE_ROOT / f"render_{t.lower()}"
    cache_dir.mkdir(parents=True, exist_ok=True)
    data_path = cache_dir / "report_data.json"
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Generate charts
    palette = {
        "brand": "#067647", "brand_dark": "#054f31", "accent": "#ecfdf3",
        "ink": "#101828", "muted": "#475467", "line": "#e4e7ec",
        "band": "#f9fafb", "paper": "#ffffff", "pos": "#067647", "neg": "#b42318",
    }
    charts_dir = _generate_charts(t, data, palette)

    # Chart availability flags (real render vs 1.2K placeholder): template
    # embeds only real charts, skips failed ones instead of showing junk.
    data["charts"] = {}
    for _name in ["vs_jci", "vs_jci_narrow", "segment_donut", "kpi_bars", "pbv_bands",
                  "wacc_breakdown", "sensitivity_heatmap", "scenario_bars",
                  "ev_equity_waterfall", "margin_trajectory", "production_cost",
                  "revenue_combo", "ebitda_combo", "netprofit_combo",
                  "pe_hist_band", "pbv_hist_band",
                  "index_trend",
                  "relval_bars", "peer_pe", "peer_evebitda", "peer_pb"]:
        _p = charts_dir / f"{_name}.png"
        data["charts"][_name] = bool(_p.exists() and _p.stat().st_size > 2048)
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Select template file
    tpl_filename = ARCHETYPE_TEMPLATE_FILES.get(resolved_archetype, "report_single.typ")
    primary_tpl = TEMPLATES_DIR / tpl_filename
    fallback_tpl = TEMPLATES_FALLBACK_DIR / "archetypes" / tpl_filename

    if primary_tpl.exists():
        template_file = primary_tpl
    elif fallback_tpl.exists():
        template_file = fallback_tpl
    else:
        raise FileNotFoundError(f"Typst template for {resolved_archetype} not found at {primary_tpl} or {fallback_tpl}")

    # Output path
    if out_path:
        pdf_out = Path(out_path)
    else:
        pdf_out = PROJECT_ROOT / "output" / f"{t.lower()}_report_typst.pdf"

    if not compile_typst(template_file, pdf_out, data_path=data_path, ticker=t):
        raise RuntimeError(f"typst compilation failed for {t} using {template_file}")

    return str(pdf_out)


def main() -> None:
    ap = argparse.ArgumentParser(description="Render institutional Typst PDF report")
    ap.add_argument("ticker", help="Stock ticker symbol (e.g. RATU, BBCA, ADRO, CDIA, MTEL)")
    ap.add_argument("--archetype", default="auto", choices=["auto", "single", "sotp", "infra", "strategy"])
    ap.add_argument("--out", help="Output PDF path")
    args = ap.parse_args()

    pdf = render_report(args.ticker, archetype=args.archetype, out_path=args.out)
    print(f"Rendered: {pdf}")


if __name__ == "__main__":
    main()
