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
import pathlib
import sys
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
TEMPLATES_DIR = REPO_ROOT / "templates"

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
    _repo = Path(__file__).resolve().parents[2]
    _has_assump = (_repo / "data" / "assumptions" / f"{t}.json").exists()
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
        p = os.path.join(os.path.dirname(__file__), "..", "..", "data", "assumptions", f"{tt}.json")
        p = os.path.normpath(p)
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
        fv = dcf_res["fv_per_share"]
        ev_res = ev_ebitda(assum.get("ebitda", 2000), assum.get("ev_multiple", 10), net_debt=assum.get("net_debt", 0), shares_out=assum.get("shares_out", 1e9), cash=assum.get("cash", 0))
        blended_res = None
        chosen = template_override or _template_for_inline(t, None)
        if chosen == "infra":
            from server.engines import blended as calc_blended

            blended_res = calc_blended({"dcf": dcf_res["fv_per_share"], "ev": ev_res["fv_per_share"]}, {"dcf": 0.6, "ev": 0.4})
            fv = blended_res["blended"]
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
            "methods": [
                {"method": "DCF", "fv": round(fv or 0), "assumptions": {"wacc": round(wacc_val*100, 2), "beta": assum["beta"], "rf": assum["rf"]*100, "erp": assum["erp"]*100, "g": assum.get("g", 0.015)*100}, "table": {"headers": ["Item", "Nilai"], "rows": [["WACC (%)", round(wacc_val*100, 2)], ["FV (Rp)", round(fv or 0)]]}, "source": "scripts/dcf.py"},
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
    }
    # 2A+4F forecast expansion RETIRED (LOUD policy): it projected FY26F-FY29F
    # from placeholder actuals [1000, 1100] — fabricated trend presented as IDX
    # financials. Re-enable only with real Sectors quarterly actuals as base.
    # financial_highlights stays honest-empty (set above).
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


def render_html_for_ticker(ticker: str, template_override: Optional[str] = None) -> tuple[str, str, dict]:
    """Return (template_name, html, report_data)."""
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

    house_format.install(env, data)

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


async def _html_to_pdf_bytes(html: str, title: str) -> bytes:
    """Try Playwright, else weasyprint, else minimal fallback. Always returns %PDF bytes."""
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
                await page.pdf(path=str(out), format="A4", print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
                await browser.close()
            data = out.read_bytes()
            if data.startswith(b"%PDF"):
                return data
    except Exception:
        pass

    # 2) WeasyPrint
    try:
        from weasyprint import HTML  # type: ignore

        pdf_bytes = HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf()
        if pdf_bytes.startswith(b"%PDF"):
            return pdf_bytes
    except Exception:
        pass

    # 3) Minimal fallback (pure python, no deps)
    return _minimal_pdf_bytes(title, [f"Report {title}", "Generated via fallback minimal PDF (Playwright/WeasyPrint not available)", "HTML length: " + str(len(html))])


# ---------------------------------------------------------------- routes
@router_pdf.get("/api/report/{ticker}/pdf", summary="Institutional PDF — Playwright else weasyprint else minimal (always %PDF)")
async def report_pdf(ticker: str, template: Optional[str] = Query(None, description="force single|sotp|infra|strategy")):
    t = ticker.upper().strip()
    if not t or len(t) > 12:
        raise HTTPException(400, "invalid ticker")
    if template and template not in ("single", "sotp", "infra", "strategy"):
        raise HTTPException(400, "invalid template")

    tpl_name, html, data = render_html_for_ticker(t, template)
    title = f"{t} — {data.get('meta', {}).get('report_type', 'Report')} ({tpl_name})"
    pdf_bytes = await _html_to_pdf_bytes(html, title)

    # Write to temp file for FileResponse (ensures proper streaming + Content-Disposition)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", prefix=f"{t}_")
    tmp.write(pdf_bytes)
    tmp.close()

    headers = {"Content-Disposition": f'attachment; filename="{t}_{tpl_name}.pdf"'}
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
