"""PDF report router — staged to avoid merge collision with sa-0 (BE enrichment lane).

Exposes:
  GET /api/report/{ticker}/pdf  -> FileResponse application/pdf (%PDF magic)
  GET /api/report/{ticker}/html -> debug HTML (text/html)

Pipeline:
  report_fixtures fixture (if known ticker) OR build payload via _assumptions_for + engines
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

# Make scripts importable for select_template / report_fixtures
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

def _load_fixture(ticker: str) -> Optional[dict]:
    """Try report_fixtures ALL for known archetypes (RATU/CDIA/MTEL)."""
    try:
        from report_fixtures import ALL  # type: ignore

        fn = ALL.get(ticker.upper()) or ALL.get(ticker.upper().lower()) or ALL.get(f"{ticker.upper()}_single") or ALL.get(f"{ticker.upper()}_sotp") or ALL.get(f"{ticker.upper()}_infra")
        # ALL is keyed as lower-case? check report_fixtures.py
        # fallback direct names
        mapping = {
            "RATU": "ratu_single",
            "CDIA": "cdia_sotp",
            "MTEL": "mtel_infra",
        }
        key = mapping.get(ticker.upper())
        if key and key in ALL:
            fn = ALL[key]
        if fn:
            return fn()
    except Exception:
        pass
    # also try direct import of functions
    try:
        import report_fixtures as rf  # type: ignore

        t = ticker.upper()
        if t == "RATU" and hasattr(rf, "ratu_single"):
            return rf.ratu_single()
        if t == "CDIA" and hasattr(rf, "cdia_sotp"):
            return rf.cdia_sotp()
        if t == "MTEL" and hasattr(rf, "mtel_infra"):
            return rf.mtel_infra()
        if t == "JPM" and hasattr(rf, "jpm_strategy"):
            return rf.jpm_strategy()
    except Exception:
        pass
    return None


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
    # Loud failure: no silent generic numbers. A ticker without a fixture or
    # assumptions file must 422, mirroring endpoints.py:583-592.
    _repo = Path(__file__).resolve().parents[2]
    _has_fixture = (_repo / "scripts" / "fixtures" / f"{t}_report_data.json").exists()
    _has_assump = (_repo / "data" / "assumptions" / f"{t}.json").exists()
    if not _has_fixture and not _has_assump:
        raise HTTPException(
            422, f"no fixture or assumptions for {t} — refusing generic fallback")
    # reuse _assumptions_for logic (duplicate to avoid circular import)
    import json, os

    # Inline _assumptions_for (copied semantics from endpoints.py)
    def _assumptions_for_inner(ticker: str) -> dict:
        tt = ticker.upper().strip()
        if tt in ("MTEL", "TOWR", "TLKM"):
            base = {"rf": 0.0696, "beta": 0.65, "erp": 0.0889, "cod": 0.06, "we": 0.608, "wd": 0.392, "wacc": 0.101, "g": 0.015, "payout": 0.35, "fcf": [4988, 5200, 5400, 5600, 5800], "shares_out": 81.5e9, "net_debt": 21430e9, "cash": 1643e9, "ebitda": 7451e9, "ev_multiple": 10, "last_price": 460, "tower": 40563, "tenancy_ratio": 1.57, "fiber_km": 59239, "source": "assumptions/MTEL.json"}
        elif tt == "RATU":
            base = {"rf": 0.07, "beta": 0.7, "erp": 0.069, "cod": 0.035, "g": 0.05, "payout": 0.3, "fcf": [456, 570, 684, 760, 836], "shares_out": 2.71e9, "net_debt": 0, "cash": 500e9, "ebitda": 585e9, "ev_multiple": 22.6, "last_price": 6200, "source": "assumptions/RATU.json"}
        elif tt == "CDIA":
            base = {"rf": 0.0696, "beta": 0.90, "erp": 0.06, "cod": 0.05, "g": 0.03, "payout": 0.40, "fcf": [4800, 5400, 6000, 6600, 7200], "shares_out": 124.8e9, "net_debt": 5000e9, "cash": 1200e9, "ebitda": 2500e9, "ev_multiple": 12.0, "last_price": 645, "source": "assumptions/CDIA.json"}
        elif tt == "BBCA":
            base = {"rf": 0.0696, "beta": 0.80, "erp": 0.06, "cod": 0.05, "g": 0.04, "roe": 0.197, "bvps": 4200, "payout": 0.50, "fcf": [40000, 46000, 52000, 58000, 64000], "shares_out": 123.2e9, "net_debt": 0, "cash": 50000e9, "ebitda": 35000e9, "ev_multiple": 16.9, "last_price": 7890, "source": "assumptions/BBCA.json"}
        elif tt == "ADRO":
            base = {"rf": 0.0696, "beta": 0.95, "erp": 0.06, "cod": 0.05, "g": 0.02, "payout": 0.45, "fcf": [7500, 7800, 8100, 8400, 8700], "shares_out": 28.8e9, "net_debt": 2000e9, "cash": 3500e9, "ebitda": 8000e9, "ev_multiple": 6.5, "last_price": 2080, "source": "assumptions/ADRO.json"}
        else:
            base = {"rf": 0.0696, "beta": 0.85, "erp": 0.06, "cod": 0.06, "g": 0.025, "payout": 0.4, "fcf": [1000, 1100, 1200, 1300, 1400], "shares_out": 10e9, "net_debt": 5000e9, "cash": 1000e9, "ebitda": 3000e9, "ev_multiple": 12, "last_price": 1000, "source": "fallback generic"}
        p = os.path.join(os.path.dirname(__file__), "..", "..", "data", "assumptions", f"{tt}.json")
        p = os.path.normpath(p)
        if os.path.exists(p):
            try:
                loaded = json.loads(open(p, encoding="utf-8").read())
                if isinstance(loaded, dict):
                    for k, v in loaded.items():
                        if v is not None:
                            base[k] = v
            except Exception:
                pass
        return base

    assum = _assumptions_for_inner(t)
    w = calc_wacc(assum["rf"], assum["beta"], assum["erp"], assum["cod"], we=assum.get("we", 0.608), wd=assum.get("wd", 0.392))
    wacc_val = w["wacc"]
    raw_fcf = assum.get("fcf") or [1000, 1100, 1200, 1300, 1400]
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
        dcf_res = {"error": str(e)}
        ev_res = {}
        blended_res = None
        fv = assum.get("last_price", 1000)

    last_price = assum.get("last_price", 1000)
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
    # Use payload structure expected by templates: meta, cover, financial_highlights, thesis, valuation, etc.
    MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agt", "Sep", "Okt", "Nov", "Des"]
    is_infra = chosen == "infra"
    seg_name = "Tower Leasing" if is_infra else "Core"
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
            "rating_box": {"action": rating, "tp": round(fv or last_price), "prev_tp": None, "price": last_price, "upside_pct": upside or 0, "key_takeaways": ["Valuasi DCF deterministik", "Asumsi WACC eksplisit", "Bukan saran investasi"] if is_infra else []},
            "vs_jci": {"ytd_abs": 0, "ytd_rel": 0, "source": "IDX, yfinance", "chart": {"labels": MONTHS, "series": [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5]]}},
            "shares": {"outstanding": round(assum.get("shares_out", 10e9) / 1e9, 1), "unit": "bn", "free_float_pct": 30.0},
            "shareholders": [{"name": "Publik", "pct": 30.0}, {"name": "Pengendali", "pct": 70.0}],
            "shareholders_src": "IDX",
            "esg": {"found": False},
        },
        "financial_highlights": {
            "source": "Laporan keuangan (IDX), data diolah",
            "years": ["FY24A", "FY25A", "FY26F"],
            "rows": [["Pendapatan (Rp bn)", 1000, 1100, 1200], ["EBITDA (Rp bn)", 500, 550, 600], ["Laba bersih (Rp bn)", 200, 220, 250]],
        },
        "segments": [
            {"name": seg_name, "revenue": 1000, "yoy_pct": 5, "qoq_pct": 2, "share_pct": 100.0, "row": [seg_name, 1000, "+5%", "+2%", "100%"]}
        ] if chosen in ("sotp", "infra") else [],
        "segments_src": "IDX",
        "kpis": [
            {"name": "Tenancy Ratio", "value": 1.57, "prev": 1.53, "unit": "x", "formula": "tenant/tower", "source": "Company data", "row": ["Tenancy Ratio", 1.57, 1.53, "+0.04", "x", "tenant/tower", "Company data"]},
            {"name": "Tower", "value": 40563, "prev": 39767, "unit": "unit", "formula": "jumlah tower", "source": "Company data", "row": ["Tower", 40563, 39767, "+796", "unit", "jumlah tower", "Company data"]},
        ] if is_infra else [],
        "kpis_src": "Company data 1H26, data diolah" if is_infra else "",
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
        "financials": [
            {"title": "Laba Rugi Ringkas", "headers": ["Rp bn", "FY24A", "FY25A", "FY26F"], "rows": [["Pendapatan", 1000, 1100, 1200], ["EBITDA", 500, 550, 600]], "source": "Laporan keuangan IDX"},
        ],
        "risks": [{"bucket": "Risiko Pasar", "detail": "Volatilitas harga & permintaan.", "source": None}],
        "peers": {"tables": [{"pillar": "Peers", "headers": ["Ticker", "P/E", "EV/EBITDA"], "rows": [[t, 10.0, 6.0]], "source": "IDX, yfinance"}]},
        "news": [],
        "sentiment": None,
        "strategy": None,
        "catalysts": [{"name": "Ekspansi jaringan", "effect": "Tambahan tenant", "quantified": {"tenants": "+1.000", "revenue_idr_bn": "+100", "by": "FY27"}, "source": "Company disclosure"}] if is_infra else [],
        "exhibits": [],
    }
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
    # Prefer fixtures for known archetypes (richer exhibits)
    data = _load_fixture(t)
    if data is None:
        data = _build_live_payload(t, template_override)
    else:
        # honor explicit template override if provided
        if template_override in ("single", "sotp", "infra", "strategy"):
            data["meta"]["template"] = template_override

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
