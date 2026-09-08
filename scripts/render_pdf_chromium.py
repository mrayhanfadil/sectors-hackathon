"""PDF renderer — Jinja2 templates + Chart.js via Playwright chromium (T10 task item 1).

Pipeline: report_data.json -> select_template() -> Jinja2 HTML -> chromium pdf().
Header "RESEARCH + tanggal" and OJK footer are baked per page (Playwright
displayHeaderFooter is off because we need styled headers/footers with rules).

Usage:
    render_pdf.py <report_data.json> [--out out.pdf] [--html-out out.html]
    render_pdf.py --all          # render all fixtures (smoke test)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATES_DIR = HERE.parent / "templates"
sys.path.insert(0, str(HERE))

from select_template import select_template  # noqa: E402

TEMPLATE_FILES = {
    "single": "report_single.html",
    "sotp": "report_sotp.html",
    "infra": "report_infra.html",
    "strategy": "report_strategy.html",
}


# ---------------------------------------------------------------- validation
def validate(report_data: dict) -> list[str]:
    """Pre-flight checks from DATA_CONTRACT.md. Returns list of violations (empty = OK)."""
    errors: list[str] = []

    blended = (report_data.get("valuation") or {}).get("blended")
    if blended:
        total = sum((blended.get("weights") or {}).values())
        if abs(total - 100) > 0.001:
            errors.append(f"blended weights sum to {total}, expected 100")

    for ex in report_data.get("exhibits") or []:
        if not (ex.get("source") or "").strip():
            errors.append(f"exhibit '{ex.get('id')}' missing source")

    segments = report_data.get("segments") or []
    if len(segments) > 1:
        total = sum(float(s.get("share_pct") or 0) for s in segments)
        if abs(total - 100) > 0.5:
            errors.append(f"segment share_pct sums to {total:.1f}, expected 100±0.5")

    rb = (report_data.get("cover") or {}).get("rating_box")
    if rb and rb.get("tp") and rb.get("price"):
        recomputed = round((rb["tp"] - rb["price"]) / rb["price"] * 100, 1)
        if abs(recomputed - rb.get("upside_pct", recomputed)) > 0.15:
            errors.append(f"upside_pct {rb.get('upside_pct')} != recomputed {recomputed}")

    for n in report_data.get("news") or []:
        if not (n.get("url") or "").strip() or not (n.get("date") or "").strip():
            errors.append(f"news item '{str(n.get('title'))[:40]}' missing url/date")

    gauge = (report_data.get("sentiment") or {}).get("gauge")
    if gauge is not None and not 0 <= gauge <= 100:
        errors.append(f"sentiment gauge {gauge} out of 0..100")

    return errors


# ---------------------------------------------------------------- render
def render_html(report_data: dict) -> tuple[str, str]:
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    template_name, reason = select_template(report_data)
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    def _idr(value: float) -> str:
        return f"{value:,.0f}" if isinstance(value, (int, float)) else str(value)

    def _pct(value: float, dec: int = 1) -> str:
        return f"{value:+.{dec}f}%"

    env.filters["idr"] = _idr
    env.filters["pct"] = _pct
    tpl = env.get_template(TEMPLATE_FILES[template_name])
    html = tpl.render(**report_data, template_reason=reason, palette={
        "brand": "#1d4ed8", "brand_dark": "#152c6e", "accent": "#eef2ff",
    })
    return template_name, html


def render_pdf(report_data: dict, out_pdf: Path, html_out: Path | None = None) -> str:
    import asyncio

    template_name, html = render_html(report_data)

    if html_out:
        html_out.parent.mkdir(parents=True, exist_ok=True)
        html_out.write_text(html, encoding="utf-8")

    async def _pdf() -> None:
        from playwright.async_api import async_playwright

        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            page = await browser.new_page()
            await page.set_content(html, wait_until="load")
            # Charts are static (animation off) but give Canvas one frame to paint.
            await page.wait_for_timeout(700)
            out_pdf.parent.mkdir(parents=True, exist_ok=True)
            await page.pdf(
                path=str(out_pdf),
                format="A4",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            await browser.close()

    asyncio.run(_pdf())
    return template_name


def main() -> None:
    ap = argparse.ArgumentParser(description="Render report JSON to institutional PDF")
    ap.add_argument("report_data", help="path to report_data.json (explicit Sectors-built payload; no fixture defaults)")
    ap.add_argument("--out", help="output pdf path")
    ap.add_argument("--html-out", help="also dump intermediate html")
    args = ap.parse_args()

    report_data = json.loads(Path(args.report_data).read_text(encoding="utf-8"))
    errs = validate(report_data)
    if errs:
        print("VALIDATION ERRORS:", *errs, sep="\n  - ")
        raise SystemExit(1)

    out = Path(args.out) if args.out else Path(args.report_data).with_suffix(".pdf")
    tpl = render_pdf(report_data, out, Path(args.html_out) if args.html_out else None)
    print(f"rendered {out} (template={tpl})")


if __name__ == "__main__":
    main()
