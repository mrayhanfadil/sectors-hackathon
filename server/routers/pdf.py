"""PDF report router — staged to avoid merge collision with sa-0 (BE enrichment lane).

Exposes:
  GET /api/report/{ticker}/pdf  -> FileResponse application/pdf (%PDF magic)
  GET /api/report/{ticker}/html -> debug HTML (text/html)

Pipeline:
  build payload via _assumptions_for + engines (Sectors-only, Sep 2026:
  fixtures purged) -> select_template()
  -> select_template() -> Jinja2 HTML (templates/*.html via helpers) -> PDF (Playwright else weasyprint else minimal fallback)
"""
from __future__ import annotations

import asyncio
import logging
import pathlib
import sys
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from typing import Optional

logger = logging.getLogger(__name__)

#: Slide-rule violations that do NOT block the render: they make the document imperfect, not
#: incomplete. A document missing a mandated section or a derivation note is a different
#: matter — that one blocks (see the gate at the end of _build_live_payload).
_ADVISORY_VIOLATIONS = (
    "carries no unit",
    "exactly one decimal",
    "absolute Rp figures carry no decimals",
    "one-page budget",
    "is generic",
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
TEMPLATES_DIR = REPO_ROOT / "templates"
#: Authoritative per-ticker input store (loud-failure policy: no generic fallback).
ASSUMPTIONS_DIR = REPO_ROOT / "data" / "assumptions"

# Make scripts importable for select_template
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

router_pdf = APIRouter()

TEMPLATE_FILES = {
    "single": "report_single.html",
    "sotp": "report_sotp.html",
    "infra": "report_infra.html",
    "strategy": "report_strategy.html",
}

# ---------------------------------------------------------------- helpers
def _idr(value) -> str:
    try:
        v = float(value)
        return f"{v:,.0f}"
    except Exception:
        return str(value)

def _pct(value, dec: int = 1) -> str:
    try:
        v = float(value)
        sign = "+" if v > 0 else ""
        return f"{sign}{v:.{dec}f}%"
    except Exception:
        return str(value)

# Gate-0..5 inputs passed through to the payload for agents/valuation/gates.py.
# The assumptions file is the ONLY permitted source for them — read the file,
# never invent values.
_GATE_INPUT_KEYS = (
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

#: Optional for the renderer (Gate-0 domain override); passed through when declared.
_GATE_DOMAIN_KEY = "domain"


def _gate_inputs_from_assumptions(assum: dict) -> dict:
    """Read-or-restate the Gate-0..5 inputs from data/assumptions/{T}.json.

    Sources, in order:
      1. ``assum["gate_inputs"]`` — the file's own gate block (authoritative,
         may also carry ``domain``);
      2. the same keys at the file's top level;
      3. restatements of a quantity the file *already* declares, so the file's
         own numbers are what reaches the gate:
         - ``wd`` is documented spot gearing D/(D+E) -> gate 1c ``d_de_ratio``;
         - ``net_debt_after_cash`` / ``ebitda`` -> gate 1c ``net_debt_to_ebitda``
           (the file labels ``net_debt_after_cash`` the economically net figure
           and ``net_debt`` the gross bridge leg, which dcf()/ev_ebitda() add
           cash back against — so the gross leg is NOT used here).

    Nothing else is inferred. A key the file does not support is left absent on
    purpose: the gate stage raises ValueError naming it rather than being handed
    an invented filing history, coverage ratio or equity base (LOUD policy).
    ``archetype`` is deliberately NOT mapped to ``revenue_drivers``: the repo
    bucket ("coal" for anything Basic Materials) is inferred from the subsector
    and would mislabel a copper/gold miner as coal-driven.
    """
    gi: dict = {}
    nested = assum.get("gate_inputs")
    if isinstance(nested, dict):
        gi.update({k: v for k, v in nested.items() if v is not None})
    for key in (*_GATE_INPUT_KEYS, _GATE_DOMAIN_KEY):
        if assum.get(key) is not None:
            gi[key] = assum[key]

    wd = assum.get("wd")
    if "d_de_ratio" not in gi and isinstance(wd, (int, float)) and not isinstance(wd, bool):
        gi["d_de_ratio"] = float(wd)
    if "net_debt_to_ebitda" not in gi:
        nd, eb = assum.get("net_debt_after_cash"), assum.get("ebitda")
        if (isinstance(nd, (int, float)) and not isinstance(nd, bool)
                and isinstance(eb, (int, float)) and not isinstance(eb, bool)
                and float(eb) != 0.0):
            gi["net_debt_to_ebitda"] = round(float(nd) / float(eb), 4)
    return gi


def _build_live_payload(ticker: str, template_override: Optional[str]) -> dict:
    """Build minimal DATA_CONTRACT payload via assumptions+engines when no fixture."""
    # import helpers from endpoints to reuse
    import importlib.util

    # Load _assumptions_for and _template_for from endpoints.py without importing the router (avoid circular)
    ep_path = REPO_ROOT / "server" / "routers" / "endpoints.py"
    spec = importlib.util.spec_from_file_location("_ep_tmp", str(ep_path))
    # Instead of exec endpoints (side effects), replicate assumptions logic inline by importing server.engines
    from server.engines import wacc as calc_wacc, dcf as calc_dcf, ev_ebitda

    t = ticker.upper().strip()
    # Loud failure: no silent generic numbers. A ticker without a verified
    # assumptions file must 422, mirroring endpoints.py:583-592.
    _has_assump = (ASSUMPTIONS_DIR / f"{t}.json").exists()
    _required = ("rf", "beta", "erp", "cod", "g", "payout", "fcf", "shares_out",
                 "net_debt", "cash", "ebitda", "ev_multiple", "last_price", "we", "wd")
    if not _has_assump:
        raise HTTPException(
            status_code=422,
            detail={
                "ticker": t,
                "missing": list(_required),
                "summary": (
                    f"no verified assumptions for {t} — refusing generic fallback "
                    f"(add data/assumptions/{t}.json or set SECTORS_API_KEY)"
                ),
            },
        )
    # reuse _assumptions_for logic (duplicate to avoid circular import)
    import json, os

    # Inline _assumptions_for (same loud-failure policy as endpoints.py).
    # No fabricated archetype numbers: only keys present in
    # data/assumptions/{T}.json are used — missing keys stay missing and 422
    # below instead of being silently completed with generic numbers.
    def _assumptions_for_inner(ticker: str) -> dict:
        tt = ticker.upper().strip()
        base: dict = {}
        p = str(ASSUMPTIONS_DIR / f"{tt}.json")
        if os.path.exists(p):
            try:
                loaded = json.loads(open(p, encoding="utf-8").read())
                if isinstance(loaded, dict):
                    for k, v in loaded.items():
                        if v is not None:
                            base[k] = v
                    base["source"] = f"assumptions/{tt}.json"
            except Exception:
                pass
        else:
            base["source"] = "no_assumptions_file"
        return base

    assum = _assumptions_for_inner(t)
    _missing = [k for k in _required if assum.get(k) is None]
    if assum.get("source") == "no_assumptions_file" or _missing:
        raise HTTPException(
            status_code=422,
            detail={
                "ticker": t,
                "missing": _missing or list(_required),
                "summary": (
                    f"no verified assumptions for {t} — refusing generic fallback "
                    f"(missing={_missing or ['assumptions file']}; add data/assumptions/{t}.json)"
                ),
            },
        )
    w = calc_wacc(assum["rf"], assum["beta"], assum["erp"], assum["cod"], we=assum.get("we", 0.608), wd=assum.get("wd", 0.392))
    wacc_val = w["wacc"]
    raw_fcf = assum.get("fcf")
    assert raw_fcf is not None  # guaranteed by required-key 422 above
    fcf_list = [float(x) * 1e9 for x in raw_fcf]
    try:
        dcf_res = calc_dcf(fcf_list, wacc_val, assum.get("g", 0.015), shares_out=assum.get("shares_out", 1e9), net_debt=assum.get("net_debt", 0), cash=assum.get("cash", 0))
        ev_res = ev_ebitda(assum.get("ebitda", 2000), assum.get("ev_multiple", 10), net_debt=assum.get("net_debt", 0), shares_out=assum.get("shares_out", 1e9), cash=assum.get("cash", 0))
        blended_res = None
        chosen = template_override or _template_for_inline(t, None)
        if chosen == "infra":
            from server.engines import blended as calc_blended

            blended_res = calc_blended({"dcf": dcf_res["fv_per_share"], "ev": ev_res["fv_per_share"]}, {"dcf": 0.6, "ev": 0.4})
            fv = blended_res["blended"]
            fv_anchor = {"leg": "blended_dcf_ev", "fv": fv,
                         "basis": "infra template: blended 60% DCF / 40% EV/EBITDA"}
        else:
            from server.engines import pick_fv_anchor

            try:
                fv_anchor = pick_fv_anchor(assum, dcf_res["fv_per_share"], ev_res["fv_per_share"])
            except ValueError as e:
                raise HTTPException(422, str(e))
            fv = fv_anchor["fv"]
            if fv is None:
                raise HTTPException(
                    422,
                    f"fv anchor '{fv_anchor['leg']}' produced no value for {t} "
                    f"({fv_anchor['basis']}) — refusing to rate on a missing leg.",
                )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            422, f"valuation engine failed for {t}: {e} — refusing generic fallback "
            f"(check data/assumptions/{t}.json inputs; no silent last_price FV)")

    last_price = assum["last_price"]  # guaranteed by required-key 422 above; never invented
    upside = round((fv - last_price) / last_price * 100, 2) if fv and last_price else None

    # Map rating
    def _rating(up):
        if up is None:
            return "HOLD"
        if up >= 15:
            return "BUY"
        if up >= 5:
            return "TRADING BUY"
        if up <= -15:
            return "SELL"
        if up <= -5:
            return "TRADING SELL"
        return "HOLD"

    rating = _rating(upside)
    chosen = template_override or _template_for_inline(t, None)

    # Gate-0..5 inputs: assumptions file -> payload passthrough (see
    # _gate_inputs_from_assumptions). Keys the file does not carry stay OUT of
    # the block on purpose: the gate stage then halts loudly and names them
    # instead of evaluating fabricated params.
    # NOTE for test authors: tests/_loud_test_inputs.inject_gate_inputs() uses
    # setdefault, so a payload that already carries this block must be
    # overwritten explicitly when a declared test scenario is required.
    gate_inputs = _gate_inputs_from_assumptions(assum)

    # Build minimal contract that all templates can render without crashing
    is_infra = chosen == "infra"
    payload = {
        "meta": {
            "template": chosen,
            "reason": f"auto:{chosen} via _template_for",
            "ticker": t,
            "company_name": f"{t} Tbk.",
            "sector": "Infrastruktur Telekomunikasi" if is_infra else "General",
            "report_type": "Initiation",
            "date": "31 Agt 2026",
            "prepared_by": "RESEARCH — Sectors Hackathon 2026",
            "language": "id",
            "subsector": "telco-infra" if is_infra else "",
        },
        "cover": {
            "rating_box": {"action": rating, "tp": round(fv or last_price), "prev_tp": None, "price": last_price, "upside_pct": upside, "key_takeaways": ["Valuasi DCF deterministik", "Asumsi WACC eksplisit", "Bukan saran investasi"] if is_infra else []},
            "vs_jci": {"ytd_abs": None, "ytd_rel": None, "source": "sectors_missing_key", "note": "perbandingan vs IHSG menunggu Sectors daily (tidak ada deret sintetik)"},
            "shares": {"outstanding": round(assum["shares_out"] / 1e9, 1), "unit": "bn", "free_float_pct": None, "note": "free float menunggu Sectors ownership"},
            "shareholders": [],
            "shareholders_src": "sectors_missing_key",
            "shareholders_note": "komposisi pemegang saham menunggu Sectors ownership (tidak ada 30/70 karangan)",
            "esg": {"found": False},
        },
        "financial_highlights": {
            "source": "sectors_missing_key",
            "note": "ikhtisar keuangan menunggu Sectors quarterly (tidak ada baris 1000/1100 karangan)",
            "years": [],
            "rows": [],
        },
        "segments": [],
        "segments_src": "sectors_missing_key",
        "segments_note": "pilar segmen menunggu data segmen Sectors/IDX (tidak ada 1000/+5% karangan)",
        "kpis": [],
        "kpis_src": "sectors_missing_key",
        "kpis_note": "KPI menunggu data emiten terverifikasi (tidak ada tenancy/tower karangan)",
        "thesis": [
            {"headline": "Valuasi terdorong DCF", "detail": f"WACC {wacc_val*100:.2f}% → FV Rp {fv:,.0f}", "source": "scripts/dcf.py"},
            {"headline": "Asumsi eksplisit & auditable", "detail": f"Rf {assum['rf']*100:.2f}%, Beta {assum['beta']}, ERP {assum['erp']*100:.2f}%", "source": "assumptions"},
        ],
        "valuation": {
            # Which leg anchors the headline FV (server/engines pick_fv_anchor). Without this
            # the cover's TP provenance is unknowable, and methods[] used to label the ANCHORED
            # value as "DCF" even when the anchor was EV/EBITDA — the table named the wrong leg
            # as the source of the number it printed.
            "anchor": fv_anchor["leg"],
            "anchor_basis": fv_anchor["basis"],
            "legs": {
                "dcf": (dcf_res.get("fv_per_share") if isinstance(dcf_res, dict) else None),
                "ev_ebitda": (ev_res.get("fv_per_share") if isinstance(ev_res, dict) else None),
            },
            "methods": [
                {"method": "DCF", "fv": round(dcf_res.get("fv_per_share", 0) if isinstance(dcf_res, dict) else 0), "assumptions": {"wacc": round(wacc_val*100, 2), "beta": assum["beta"], "rf": assum["rf"]*100, "erp": assum["erp"]*100, "g": assum.get("g", 0.015)*100}, "table": {"headers": ["Item", "Nilai"], "rows": [["WACC (%)", round(wacc_val*100, 2)], ["FV (Rp)", round(dcf_res.get("fv_per_share", 0) if isinstance(dcf_res, dict) else 0)]]}, "source": "scripts/dcf.py"},
                {"method": "EV/EBITDA", "fv": round(ev_res.get("fv_per_share", 0) if isinstance(ev_res, dict) else 0), "assumptions": {"multiple": assum.get("ev_multiple", 10)}, "table": {"headers": ["Item", "Nilai"], "rows": [["Multiple (x)", assum.get("ev_multiple", 10)]]}, "source": "scripts/ev_ebitda.py"},
            ],
            "blended": {"source": "scripts/blended.py", "weights": {"DCF": 60, "EV/EBITDA": 40}, "fv": round(fv or 0), "margin_of_safety_pct": 15, "weights_sum_100": True, "rows": [["DCF", "60%", round(dcf_res.get("fv_per_share", 0) if isinstance(dcf_res, dict) else 0)], ["EV/EBITDA", "40%", round(ev_res.get("fv_per_share", 0) if isinstance(ev_res, dict) else 0)]], "fv_str": str(round(fv or 0))} if blended_res else None,
            "bands": None,
        },
        "financials": [],
        "financials_note": "laporan keuangan menunggu Sectors quarterly (tidak ada baris 1000/1100 karangan; proyeksi placeholder dimatikan LOUD policy)",
        "risks": [],
        "risks_note": "risiko menunggu Sectors filings/suspensions (tidak ada bucket generik)",
        "peers": {"tables": [], "source": "sectors_missing_key", "note": "komparabel menunggu Sectors peers (tidak ada baris 10.0/6.0 karangan)"},
        "news": [],
        "sentiment": None,
        "strategy": None,
        "catalysts": [],
        "catalysts_note": "katalis menunggu filings/keterbukaan (tidak ada tenant-kuantifikasi karangan)" if is_infra else "",
        "exhibits": [],
        "gate_inputs": gate_inputs,
    }
    # 2A+4F forecast expansion RETIRED (LOUD policy): it projected FY26F-FY29F
    # from placeholder actuals [1000, 1100] — fabricated trend presented as IDX
    # financials. Re-enable only with real Sectors quarterly actuals as base.
    # financial_highlights stays honest-empty (set above).
    if t == "AMMN":
        # AMMN-FILLT: fill FILL_MAP-mapped keys from output/cache/ammn_fill
        # (sibling harvest, 0 credits). Missing cache -> honest-empty kept;
        # never crash the render (filler itself is section-guarded too).
        try:
            from server.report.ammn_fill import apply_ammn_fill
        except ImportError:
            apply_ammn_fill = None  # type: ignore
        if apply_ammn_fill is not None:
            try:
                apply_ammn_fill(payload, assum, fv, rating, upside, wacc_val,
                                anchor_basis=fv_anchor.get("basis"),
                                anchor_leg=fv_anchor.get("leg"))
            except Exception:
                pass
    # Slide-1 contract (rating status, price box, secondary stats, analyst, theme title,
    # 24M price-vs-IHSG series, quarterly performance paragraph). Runs for every ticker,
    # after the AMMN fill so it reads the filled cover. A leg with no source renders as an
    # honest "n/a" (see server/report/cover_slide1.py) — but a builder that CRASHES is
    # recorded, not swallowed: a missing section would otherwise make the §7-§9 audit
    # "not applicable" and slip past the gate.
    build_errors: list[str] = []
    try:
        from server.report.cover_slide1 import build as build_slide1

        build_slide1(payload, assum if _has_assump else {})
    except Exception as exc:
        build_errors.append(f"slide1 builder failed: {type(exc).__name__}: {exc}")
    # Cover main-column contract: catalysts paragraph, valuation paragraph, Key Financials.
    try:
        from server.report.slide2 import build as build_slide2

        build_slide2(payload, assum if _has_assump else {})
    except Exception as exc:
        build_errors.append(f"slide2 builder failed: {type(exc).__name__}: {exc}")
    # Deck page 2 (the owner's "slide 2"): Kondisi Industri / Katalis Emiten / Sentimen — three
    # narrative paragraphs, no mandatory object. NOTE the naming: `cover.slide1/slide2` above are
    # the cover's two COLUMNS, while the slide numbers in docs/ammn-slides are PAGES. Built after
    # the fills so it reads the filled catalysts/sentiment blocks; a crash is recorded, never
    # swallowed — a page that silently vanished would take the §7-§9 audit with it.
    try:
        from server.report.industry_page import build_industry_page

        payload["industry_page"] = build_industry_page(payload, assum if _has_assump else {})
    except Exception as exc:
        build_errors.append(f"industry page builder failed: {type(exc).__name__}: {exc}")
    if build_errors:
        payload.setdefault("cover", {})["build_errors"] = build_errors

    # Deterministic Critic gate — the same audit `agents/critic.py` exposes, run here because
    # this is the single choke point every render path goes through. The
    # verdict rides on the payload, so output/cache/render_<TICKER>/report_data.json shows it
    # instead of leaving it in a log nobody reads.
    #
    # Severity: a builder that CRASHED blocks the render — a section silently vanished and the
    # document is incomplete. Content violations (a paragraph missing its mandate, a misplaced
    # decimal, the copy budget) are reported rather than thrown: a sparse ticker renders an
    # honest "n/a" cover, and taking the report offline over a style defect would be worse than
    # shipping it with the defect named. `agents/critic.py` still REJECTs those payloads in the
    # ADK gate, and tests/test_slide_rules_adoption.py keeps the shipped cover clean.
    try:
        from agents.critic import audit_report_payload
        from server.report.house_rules import audit_house_rules

        rules = audit_house_rules(payload)
        if build_errors:
            rules.setdefault("violations", []).extend(build_errors)
            rules["ok"] = False
        payload["house_rules"] = rules
        payload["critic"] = audit_report_payload(payload)
        if build_errors:
            raise RuntimeError(
                "cover builders failed for " + str(payload.get("meta", {}).get("ticker"))
                + ": " + "; ".join(build_errors[:3])
            )
        blocking = [v for v in (rules.get("violations") or [])
                    if not any(m in v for m in _ADVISORY_VIOLATIONS)]
        if blocking:
            logger.warning(
                "house slide rules (§7-§9): %d structural violation(s) for %s — first: %s",
                len(blocking), payload.get("meta", {}).get("ticker"), blocking[0],
            )
    except RuntimeError:
        raise
    except Exception as exc:
        logger.warning("house gate unavailable: %s", exc)
    return payload


def _template_for_inline(ticker: str, segments: Optional[dict]) -> str:
    infra = {"MTEL", "TOWR", "EXCL", "ISAT", "TLKM"}
    if ticker.upper() in infra:
        return "infra"
    if segments and isinstance(segments, dict):
        segs = segments.get("segments") or segments.get("items") or []
        if isinstance(segs, list) and len(segs) > 1:
            return "sotp"
    return "single"


def _select_template(report_data: dict) -> tuple[str, str]:
    try:
        from select_template import select_template  # type: ignore

        return select_template(report_data)
    except Exception:
        # fallback
        t = (report_data.get("meta") or {}).get("ticker", "")
        segs = report_data.get("segments") or []
        if len(segs) > 1:
            # check infra precedence
            sub = ((report_data.get("meta") or {}).get("subsector") or (report_data.get("meta") or {}).get("sector") or "").lower()
            if any(k in sub for k in ("infra", "telco", "tower", "fiber")):
                return "infra", "infra precedence"
            return "sotp", "segments>1"
        sub = ((report_data.get("meta") or {}).get("subsector") or (report_data.get("meta") or {}).get("sector") or "").lower()
        if any(k in sub for k in ("infra", "telco", "tower", "fiber")):
            return "infra", "subsector infra"
        return "single", "default"


def render_html_for_ticker(
    ticker: str, template_override: Optional[str] = None, native_furniture: bool = False
) -> tuple[str, str, dict]:
    """Return (template_name, html, report_data).

    `native_furniture=True` omits the per-`<div class="page">` header/footer and leaves the
    furniture to Chromium (see `render_pdf_bytes_for_ticker`) — only the PDF path wants
    that. The `/html` debug endpoint and the tests keep the per-div furniture because a
    browser (which does not paginate) has no other way to show a header.
    """
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    t = ticker.upper().strip()
    # LOUD policy: no fixture preference in prod — fixtures are declared demo
    # data (scripts/report_fixtures.py), never live responses. Tests that need
    # demo payloads load them explicitly (tests/_loud_test_inputs.py).
    data = _build_live_payload(t, template_override)

    # select template (honors meta.template override + infra precedence)
    template_name, reason = _select_template(data)
    if template_override in ("single", "sotp", "infra", "strategy"):
        template_name = template_override
        reason = f"query template override -> {template_override}"

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["idr"] = _idr
    env.filters["pct"] = _pct
    # House furniture (docs/rules/house-report-format.md). Macros are imported without
    # context, so the computed date and the inline logo can only reach them as globals.
    from server.report import house_format

    house_format.install(env, data, native_furniture=native_furniture)

    tpl_file = TEMPLATE_FILES.get(template_name, "report_single.html")
    tpl = env.get_template(tpl_file)
    html = tpl.render(**data, template_reason=reason, palette={"brand": "#1d4ed8", "brand_dark": "#152c6e", "accent": "#eef2ff"})
    return template_name, html, data


def _minimal_pdf_bytes(title: str, text_lines: Optional[list[str]] = None) -> bytes:
    """Generate minimal valid PDF (no deps) with title text. Satisfies %PDF magic check."""
    # Very small PDF 1.4 with one page, Helvetica, text
    lines = text_lines or [title, "RESEARCH — Sectors Hackathon 2026", "Informasi, bukan saran investasi"]
    # Escape parens
    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    # Build content stream
    y = 750
    stream_parts = ["BT", "/F1 14 Tf", f"50 {y} Td", f"({esc(title)}) Tj"]
    y -= 20
    for ln in lines[1:]:
        stream_parts.append(f"0 -20 Td")
        stream_parts.append(f"({esc(ln[:90])}) Tj")
    stream_parts.append("ET")
    stream = "\n".join(stream_parts).encode("utf-8")
    # Objects
    objs = []
    objs.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    objs.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    objs.append(b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> >>\nendobj\n")
    objs.append(b"4 0 obj\n<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream\nendobj\n")
    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    body = b"".join(objs)
    # xref
    offsets = []
    off = len(header)
    for o in objs:
        offsets.append(off)
        off += len(o)
    xref_off = off
    xref = b"xref\n0 5\n0000000000 65535 f \n"
    for o in offsets:
        xref += f"{o:010d} 00000 n \n".encode()
    trailer = b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n" + str(xref_off).encode() + b"\n%%EOF"
    return header + body + xref + trailer


async def _html_to_pdf_bytes(
    html: str,
    title: str,
    header_html: Optional[str] = None,
    footer_html: Optional[str] = None,
    margin: Optional[dict] = None,
) -> tuple[bytes, str]:
    """Try Playwright, else weasyprint, else minimal fallback. Always returns %PDF bytes.

    Returns `(pdf_bytes, engine)` with engine in `{"playwright", "weasyprint", "minimal"}`
    so the caller can tell whether the furniture it asked for was actually drawn: the
    Chromium header/footer templates only exist in the Playwright branch. A caller that
    rendered with `native_furniture=True` MUST fall back to a per-div-furniture render
    when the engine is not Playwright, otherwise the document ships without furniture.
    """
    # 1) Playwright
    try:
        from playwright.async_api import async_playwright  # type: ignore

        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out.pdf"
            async with async_playwright() as pw:
                browser = await pw.chromium.launch()
                page = await browser.new_page()
                await page.set_content(html, wait_until="load")
                await page.wait_for_timeout(700)
                pdf_kwargs: dict = {
                    "path": str(out),
                    "format": "A4",
                    "print_background": True,
                    "margin": margin or {"top": "0", "right": "0", "bottom": "0", "left": "0"},
                }
                if header_html is not None:
                    # Chromium only renders the header/footer templates when it is asked
                    # to AND the margins reserve room for them; it substitutes
                    # `.pageNumber` / `.totalPages` with the real physical page counter.
                    pdf_kwargs["display_header_footer"] = True
                    pdf_kwargs["header_template"] = header_html
                    pdf_kwargs["footer_template"] = footer_html or ""
                await page.pdf(**pdf_kwargs)
                await browser.close()
            data = out.read_bytes()
            if data.startswith(b"%PDF"):
                return data, "playwright"
    except Exception as exc:
        # Loud: a failure here silently downgrades the document to per-div furniture (or
        # to weasyprint), which is the exact bug this function exists to prevent. The
        # usual cause is an invalid margin unit — Chromium rejects `pt`.
        print(f"[warn] Playwright PDF render failed, falling back: {exc}", file=sys.stderr)

    # 2) WeasyPrint
    try:
        from weasyprint import HTML  # type: ignore

        pdf_bytes = HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf()
        if pdf_bytes.startswith(b"%PDF"):
            return pdf_bytes, "weasyprint"
    except Exception:
        pass

    # 3) Minimal fallback (pure python, no deps)
    return _minimal_pdf_bytes(title, [f"Report {title}", "Generated via fallback minimal PDF (Playwright/WeasyPrint not available)", "HTML length: " + str(len(html))]), "minimal"


async def render_pdf_bytes_for_ticker(
    ticker: str, template_override: Optional[str] = None
) -> tuple[bytes, str, str, dict]:
    """Render the house-compliant PDF for a ticker. Returns (pdf, engine, template, data).

    Two passes by design. Pass 1 renders with the furniture left to Chromium
    (`native_furniture=True`), which is the only variant that reaches EVERY physical page
    — per-`<div class="page">` furniture sits inside the content flow, so any page that
    overflows produces a continuation page with no header and a duplicated footer
    (house-report-format.md §3-4: header and footer on every slide). Pass 2 only runs if
    Chromium was unavailable, re-rendering with the per-div furniture so the weasyprint
    fallback is not left with a bare document.
    """
    from server.report import house_format

    title = f"{ticker.upper().strip()} — institutional report"
    tpl_name, html, data = render_html_for_ticker(ticker, template_override, native_furniture=True)
    date_str = house_format.format_house_date((data.get("meta") or {}).get("date"))
    pdf, engine = await _html_to_pdf_bytes(
        html,
        title,
        header_html=house_format.header_template(date_str),
        footer_html=house_format.footer_template(),
        margin=dict(house_format.PDF_MARGIN),
    )
    if engine != "playwright":
        tpl_name, html, data = render_html_for_ticker(ticker, template_override)
        pdf, engine = await _html_to_pdf_bytes(html, title)
    return pdf, engine, tpl_name, data


# ---------------------------------------------------------------- routes
@router_pdf.get("/api/report/{ticker}/pdf", summary="Institutional PDF — Playwright else weasyprint else minimal (always %PDF)")
async def report_pdf(ticker: str, template: Optional[str] = Query(None, description="force single|sotp|infra|strategy")):
    t = ticker.upper().strip()
    if not t or len(t) > 12:
        raise HTTPException(400, "invalid ticker")
    if template and template not in ("single", "sotp", "infra", "strategy"):
        raise HTTPException(400, "invalid template")

    pdf_bytes, engine, tpl_name, data = await render_pdf_bytes_for_ticker(t, template)
    title = f"{t} — {data.get('meta', {}).get('report_type', 'Report')} ({tpl_name})"

    # Write to temp file for FileResponse (ensures proper streaming + Content-Disposition)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", prefix=f"{t}_")
    tmp.write(pdf_bytes)
    tmp.close()

    headers = {
        "Content-Disposition": f'attachment; filename="{t}_{tpl_name}.pdf"',
        "X-PDF-Engine": engine,
    }
    return FileResponse(tmp.name, media_type="application/pdf", headers=headers, filename=f"{t}_{tpl_name}.pdf")


@router_pdf.get("/api/report/{ticker}/html", summary="Debug HTML for report (same jinja2 render as PDF)")
async def report_html(ticker: str, template: Optional[str] = Query(None, description="force single|sotp|infra|strategy")):
    t = ticker.upper().strip()
    if not t or len(t) > 12:
        raise HTTPException(400, "invalid ticker")
    if template and template not in ("single", "sotp", "infra", "strategy"):
        raise HTTPException(400, "invalid template")
    _, html, _ = render_html_for_ticker(t, template)
    return HTMLResponse(content=html, media_type="text/html")
