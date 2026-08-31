"""Exhibit format helpers for the PDF Renderer (P4).

Pure functions: convert the deterministic agent outputs (thesis.json, sotp.json,
charts.json) and company.json into HTML fragments / formatted values the
4 HTML templates (single / sotp / infra / strategy) consume.

Nothing here does math the agents already did — it only formats.
"""

from __future__ import annotations

import html
import json
import os
from typing import Any

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Value formatting
# ---------------------------------------------------------------------------


def fmt_idr(value: float, unit: str = "mn", digits: int = 0) -> str:
    """IDR 420,000 mn / IDR 1.2tn / IDR 420bn style."""
    if unit == "bn":
        return f"IDR {value / 1000.0:,.1f}bn"
    if unit == "tn" or abs(value) >= 1_000_000:
        return f"IDR {value / 1_000_000.0:,.1f}tn"
    return f"IDR {value:,.{digits}f} mn"


def fmt_pct(value: float, digits: int = 1) -> str:
    return f"{value * 100.0:.{digits}f}%"


def fmt_delta_pct(value: float, digits: int = 1) -> str:
    return f"{value:+.{digits}f}%"


def fmt_x(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}x"


def esc(text: Any) -> str:
    return html.escape(str(text))


# ---------------------------------------------------------------------------
# Exhibit fragments (HTML strings, tailwind-friendly, source-per-exhibit)
# ---------------------------------------------------------------------------


def exhibit_source(company: dict[str, Any], note: str = "") -> str:
    """Provenance line required under every exhibit (plan.md upgrade #6)."""
    src = company.get("source", {}).get("label", "—")
    return f'<div class="text-xs text-slate-400 mt-1">Source: {esc(src)}{" · " + esc(note) if note else ""}</div>'


def thesis_exhibit(thesis: dict[str, Any]) -> str:
    bc = thesis.get("bull_case", {})
    rows = []
    for a in bc.get("arguments", []):
        rows.append(
            f'<tr><td class="py-2 align-top font-semibold w-10">{esc(a["id"])}</td>'
            f'<td class="py-2 align-top">{esc(a["point"])}<div class="text-xs text-slate-400">'
            f'Evidence: {esc(a["evidence"]["metric"])} = {esc(a["evidence"]["value"])} · {esc(a["evidence"]["source"])}</div></td></tr>'
        )
    cats = bc.get("catalysts", [])
    cat_rows = "".join(
        f'<tr><td class="py-1.5">{esc(c.get("date", ""))}</td><td class="py-1.5">{esc(c["title"])}</td>'
        f'<td class="py-1.5 font-semibold">{esc(c.get("quantified", ""))}</td>'
        f'<td class="py-1.5 text-xs text-slate-400">{esc(c.get("source", ""))}</td></tr>'
        for c in cats
    )
    cat_block = (
        '<h4 class="font-semibold mt-4 mb-1">Catalysts (quantified)</h4>'
        f'<table class="w-full text-sm"><thead><tr class="text-left text-slate-500 border-b"><th>Date</th><th>Catalyst</th><th>Quantified impact</th><th>Source</th></tr></thead><tbody>{cat_rows}</tbody></table>'
        if cat_rows else ""
    )
    return (
        f'<div class="border rounded-lg p-4"><h3 class="font-bold text-lg mb-2">Bull Case</h3>'
        f'<p class="mb-3">{esc(bc.get("headline", ""))}</p>'
        f'<table class="w-full text-sm">{"" .join(rows)}</table>{cat_block}</div>'
    )


def normalization_exhibit(thesis: dict[str, Any]) -> str:
    n = thesis.get("normalizations")
    if not n:
        return '<div class="text-sm text-slate-500">No one-off items in input.</div>'
    items = "".join(
        f'<tr><td>{esc(i["label"])}</td><td class="text-right">{fmt_idr(i["amount_mn"])}</td></tr>'
        for i in n["items"]
    )
    return (
        '<div class="border rounded-lg p-4"><h3 class="font-bold text-lg mb-2">One-off Normalization</h3>'
        f'<p class="text-sm mb-2">{esc(n.get("description", ""))} <span class="text-xs text-slate-400">({esc(n.get("period", ""))})</span></p>'
        '<table class="w-full text-sm"><tbody>'
        f'{items}'
        f'<tr class="border-t"><td>Gross one-offs</td><td class="text-right">{fmt_idr(n["gross_one_off_mn"])}</td></tr>'
        f'<tr><td>Tax @ {n["tax_rate"]:.0%}</td><td class="text-right">{fmt_idr(n["net_one_off_after_tax_mn"])} net</td></tr>'
        f'<tr><td>Reported net income</td><td class="text-right">{fmt_idr(n["reported_net_income_mn"])}</td></tr>'
        f'<tr class="font-bold"><td>Adjusted net income</td><td class="text-right">{fmt_idr(n["adjusted_net_income_mn"])} ({fmt_delta_pct(n["delta_pct"])})</td></tr>'
        '</tbody></table>'
        f'<p class="text-xs text-slate-400 mt-1">{esc(n.get("method", ""))}</p></div>'
    )


def sotp_exhibit(sotp: dict[str, Any]) -> str:
    if not sotp.get("conglomerate"):
        return f'<div class="text-sm text-slate-500">{esc(sotp.get("reason", "SOTP not applicable"))}</div>'
    rows = "".join(
        f'<tr><td>{esc(p["pillar"])}</td><td class="text-right">{fmt_idr(p["revenue_mn"])}</td>'
        f'<td class="text-right">{p["pct"]:.1f}%</td><td class="text-right">{fmt_x(p["peer_avg_pe"])}</td>'
        f'<td class="text-right">{fmt_idr(p["implied_equity_mn"])}</td>'
        f'<td class="text-right">{p["weight_pct"]:.1f}%</td>'
        f'<td class="text-xs text-slate-400">{esc(p["peer_set"])}</td></tr>'
        for p in sotp["pillars"]
    )
    sc = sotp.get("sum_check", {})
    badge = '<span class="text-green-700 font-bold">✓ sum = 100%</span>' if sc.get("ok") else '<span class="text-red-700 font-bold">✗ MISMATCH</span>'
    return (
        '<div class="border rounded-lg p-4"><h3 class="font-bold text-lg mb-2">SOTP — Sum of Parts</h3>'
        f'<p class="text-sm mb-2">{esc(sotp.get("method", ""))} {badge}</p>'
        '<table class="w-full text-sm"><thead><tr class="text-left text-slate-500 border-b">'
        '<th>Pillar</th><th>Revenue</th><th>Mix %</th><th>Peer P/E</th><th>Implied equity</th><th>Weight %</th><th>Peer set</th>'
        '</tr></thead><tbody>'
        f'{rows}'
        f'<tr class="border-t font-bold"><td>Sum of parts</td><td></td><td class="text-right">{sc.get("pct_sum", 0):.1f}%</td><td></td>'
        f'<td class="text-right">{fmt_idr(sotp["pre_discount_total_mn"])}</td><td class="text-right">{sc.get("equity_weight_sum", 0):.1f}%</td><td></td></tr>'
        f'<tr><td>Holdco discount</td><td colspan="4" class="text-xs text-slate-400">{esc(sotp.get("discount_note", ""))}</td>'
        f'<td class="text-right">{sotp["holdco_discount_pct"]:.0%}</td><td></td></tr>'
        f'<tr class="font-bold"><td>Post-discount equity</td><td></td><td></td><td></td>'
        f'<td class="text-right">{fmt_idr(sotp["post_discount_equity_mn"])}</td><td></td><td></td></tr>'
        '</tbody></table></div>'
    )


def charts_block(ticker: str, charts: list[dict[str, Any]]) -> str:
    """Grid of chart <img> tags — paths are relative to out/<TICKER>/charts/."""
    if not charts:
        return ""
    imgs = "".join(
        f'<figure class="mb-4"><img src="charts/{esc(c["file"].split("/")[-1])}" alt="{esc(c.get("title", c["id"]))}" '
        f'class="w-full border rounded"/><figcaption class="text-xs text-slate-400 mt-1">{esc(c.get("title", ""))} · Source: {esc(c.get("source", ""))}</figcaption></figure>'
        for c in charts
        if c.get("file")
    )
    return f'<div class="grid grid-cols-2 gap-4">{imgs}</div>'


def load_agent_outputs(ticker: str) -> dict[str, Any]:
    """Convenience for the renderer: read out/<TICKER>/{thesis,sotp,charts}.json."""
    base = os.path.join(REPO_ROOT, "out", ticker)
    out: dict[str, Any] = {"ticker": ticker}
    for name in ("thesis", "sotp", "charts"):
        p = os.path.join(base, f"{name}.json")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as fh:
                out[name] = json.load(fh)
    return out
