"""Visualizer agent — institutional charts as PNG files.

Deterministic matplotlib renderer (Agg backend, no display). Emits exactly the
plan.md §5 chart set and writes a machine-readable manifest:

  1. revenue_mix   — pie (segments)            [sotp/infra only]
  2. trend         — revenue & EBITDA lines
  3. margin        — gross / EBITDA / net margin lines
  4. leverage      — gearing %, Debt/EBITDA, Current ratio (dual axis)
  5. roe_roa       — ROE / ROA bars
  6. vs_jci        — indexed price vs JCI + YTD abs/rel callout
  7. peer_multiples— P/E & EV/EBITDA dot/bar vs peers
  8. kpi           — subsector hero KPIs (tenancy ratio, fiber km, ...)

  + bands          — PBV & EV/EBITDA historical bands (MTEL infra; when data exists)

Every chart footer prints the source label from company.json (provenance rule).

Usage:
    python agents/visualizer.py [TICKER...]     # default: all fixtures
Outputs:
    out/<TICKER>/charts/<id>.png
    out/<TICKER>/charts.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (  # noqa: E402
    ENGINE_VERSION,
    ensure_out,
    load_company,
    now_iso,
    source_label,
    write_json,
)

FIGW, FIGH = 9.0, 5.4
DPI = 150
PALETTE = ["#1f6feb", "#2da44e", "#bf8700", "#cf222e", "#8250df", "#57606a"]
JCI_COLOR = "#bf8700"
TICKER_COLOR = "#1f6feb"
GRID: dict[str, object] = dict(alpha=0.25, linestyle="--", linewidth=0.6)  # noqa: F841 (kept for reference)


def _new_ax(style: str = "clean") -> tuple[Figure, Axes]:
    fig, ax = plt.subplots(figsize=(FIGW, FIGH), dpi=DPI)
    fig.patch.set_facecolor("white")
    if style == "clean":
        ax.spines[["top", "right"]].set_visible(False)
    ax.grid(True, alpha=0.25, linestyle="--", linewidth=0.6)
    return fig, ax


def _foot(fig: plt.Figure, company: dict, note: str = "") -> None:
    src = source_label(company)
    text = f"Source: {src}" + (f"  ·  {note}" if note else "")
    fig.text(0.01, 0.005, text, fontsize=7.5, color="#57606a", ha="left")


def _save(fig: plt.Figure, path: str) -> str:
    fig.tight_layout(rect=(0, 0.03, 1, 0.98))
    fig.savefig(path, format="png", dpi=DPI)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Chart builders (each returns {id, title, kind, source, note})
# ---------------------------------------------------------------------------


def chart_revenue_mix(company: dict, outdir: str) -> dict:
    segs = company.get("segments", [])
    labels = [s["pillar"] for s in segs]
    sizes = [s.get("pct", 0) for s in segs]
    growth = [s.get("growth_yoy", 0) for s in segs]
    fig, ax = plt.subplots(figsize=(9, 5.4), dpi=DPI)
    wedges, _texts, _autotexts = ax.pie(
        sizes, labels=None, autopct=lambda p: f"{p:.0f}%",
        startangle=90, counterclock=False,
        colors=PALETTE[: len(sizes)], pctdistance=0.72,
        wedgeprops=dict(width=0.42, edgecolor="white"),
    )
    for w, g in zip(wedges, growth):
        w.set_label("")
    legend = [f"{l}  {s:.0f}%  (y/y {g*100:+.1f}%)" for l, s, g in zip(labels, sizes, growth)]
    ax.legend(wedges, legend, loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=9, frameon=False)
    ax.set_title(f"{company['ticker']} — Revenue Mix by Segment", fontsize=13, fontweight="bold", pad=14)
    ax.axis("equal")
    _foot(fig, company)
    path = _save(fig, os.path.join(outdir, "revenue_mix.png"))
    return {"id": "revenue_mix", "file": "charts/revenue_mix.png", "path": path, "title": "Revenue Mix by Segment (donut)", "kind": "pie", "source": source_label(company)}


def chart_trend(company: dict, outdir: str) -> dict:
    fin = company.get("financials", {})
    years, rev, ebitda = fin.get("years", []), fin.get("revenue_mn", []), fin.get("ebitda_mn", [])
    fig, ax = _new_ax()
    x = np.arange(len(years))
    ax.bar(x, rev, color=PALETTE[0], alpha=0.85, label="Revenue", width=0.5)
    ax.plot(x, ebitda, color=PALETTE[3], marker="o", linewidth=2, label="EBITDA")
    for xi, r in zip(x, rev):
        rtn = r / 1e6 if abs(r) >= 1e6 else r / 1e3
        ax.text(float(xi), r, f"{rtn:,.0f}" + ("tn" if abs(r) >= 1e6 else "bn"), ha="center", va="bottom", fontsize=8.5)
    ax.set_xticks(x, years)
    ax.set_ylabel("IDR mn")
    ax.set_title(f"{company['ticker']} — Revenue & EBITDA Trend", fontsize=13, fontweight="bold")
    ax.legend(frameon=False, loc="upper left")
    _foot(fig, company, "units: IDR mn; T = trillion")
    path = _save(fig, os.path.join(outdir, "trend.png"))
    return {"id": "trend", "file": "charts/trend.png", "path": path, "title": "Revenue & EBITDA Trend", "kind": "bar+line", "source": source_label(company)}


def chart_margin(company: dict, outdir: str) -> dict:
    fin = company.get("financials", {})
    years = fin.get("years", [])
    g, e, n = fin.get("gross_margin", []), fin.get("ebitda_margin", []), fin.get("net_margin", [])
    fig, ax = _new_ax()
    ax.plot(years, [v * 100 for v in g], marker="o", label="Gross margin", color=PALETTE[0], linewidth=2)
    ax.plot(years, [v * 100 for v in e], marker="s", label="EBITDA margin", color=PALETTE[1], linewidth=2)
    ax.plot(years, [v * 100 for v in n], marker="^", label="Net margin", color=PALETTE[3], linewidth=2)
    ax.set_ylabel("%")
    ax.set_ylim(0, max([*[v * 100 for v in g], *[v * 100 for v in n], 10]) * 1.15)
    ax.set_title(f"{company['ticker']} — Margin Structure", fontsize=13, fontweight="bold")
    ax.legend(frameon=False, loc="best")
    _foot(fig, company)
    path = _save(fig, os.path.join(outdir, "margin.png"))
    return {"id": "margin", "file": "charts/margin.png", "path": path, "title": "Margin Structure (Gross/EBITDA/Net)", "kind": "line", "source": source_label(company)}


def chart_leverage(company: dict, outdir: str) -> dict:
    fin = company.get("financials", {})
    years = fin.get("years", [])
    gear = fin.get("gearing_pct", [])
    debt_eb = fin.get("debt_ebitda", [])
    cur = fin.get("current_ratio", [])
    fig, ax1 = _new_ax()
    ax1.bar(years, gear, color=PALETTE[4], alpha=0.75, label="Gearing % (LHS)")
    ax1.set_ylabel("Gearing %")
    ax1.set_ylim(0, max(gear + [10]) * 1.15)
    ax2 = ax1.twinx()
    ax2.plot(years, debt_eb, marker="o", color=PALETTE[3], linewidth=2, label="Debt/EBITDA (RHS)")
    ax2.plot(years, cur, marker="s", color=PALETTE[1], linewidth=2, linestyle="--", label="Current ratio (RHS)")
    ax2.set_ylim(0, max(debt_eb + [1]) * 1.15)
    ax2.set_ylabel("x")
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, frameon=False, loc="upper right")
    ax1.set_title(
        f"{company['ticker']} — Leverage & Liquidity "
        f"(Gearing {gear[0]:.0f}→{gear[-1]:.0f}% · D/EBITDA {debt_eb[0]:.0f}→{debt_eb[-1]:.0f}x · Current {cur[0]:.1f}→{cur[-1]:.1f})",
        fontsize=11, fontweight="bold",
    )
    _foot(fig, company, f"trajectory {years[0]}→{years[-1]} (de-lever + liquidity recovery)")
    path = _save(fig, os.path.join(outdir, "leverage.png"))
    return {"id": "leverage", "file": "charts/leverage.png", "path": path, "title": "Leverage & Liquidity Trajectory", "kind": "combo", "source": source_label(company)}


def chart_roe_roa(company: dict, outdir: str) -> dict:
    fin = company.get("financials", {})
    years = fin.get("years", [])
    roe, roa = fin.get("roe", []), fin.get("roa", [])
    fig, ax = _new_ax()
    x = np.arange(len(years))
    w = 0.38
    ax.bar(x - w / 2, [v * 100 for v in roe], w, color=PALETTE[0], label="ROE")
    ax.bar(x + w / 2, [v * 100 for v in roa], w, color=PALETTE[5], label="ROA")
    for xi, v in zip(x - w / 2, roe):
        ax.text(xi, v * 100 + 0.4, f"{v*100:.1f}", ha="center", fontsize=8.5)
    for xi, v in zip(x + w / 2, roa):
        ax.text(xi, v * 100 + 0.4, f"{v*100:.1f}", ha="center", fontsize=8.5)
    ax.set_xticks(x, years)
    ax.set_ylabel("%")
    ax.set_title(f"{company['ticker']} — ROE / ROA", fontsize=13, fontweight="bold")
    ax.legend(frameon=False)
    _foot(fig, company)
    path = _save(fig, os.path.join(outdir, "roe_roa.png"))
    return {"id": "roe_roa", "file": "charts/roe_roa.png", "path": path, "title": "ROE / ROA", "kind": "bar", "source": source_label(company)}


def chart_vs_jci(company: dict, outdir: str) -> dict:
    ph = company.get("price_history", {})
    tk, jci = ph.get("ticker", {}), ph.get("jci", {})
    dates = tk.get("dates", [])
    if not dates:
        return {"id": "vs_jci", "file": "charts/vs_jci.png", "path": None, "title": "Price vs JCI (no data)", "kind": "line", "source": source_label(company)}
    t_close = tk.get("close", [])
    j_close = jci.get("close", [])
    t0 = t_close[0] if t_close[0] else 1
    j0 = j_close[0] if j_close[0] else 1
    fig, ax = _new_ax()
    ax.plot(dates, [c / t0 * 100 for c in t_close], marker="o", color=TICKER_COLOR, linewidth=2, label=f"{company['ticker']} (indexed)")
    if j_close:
        ax.plot(dates, [c / j0 * 100 for c in j_close], marker="s", color=JCI_COLOR, linewidth=2, label="JCI (indexed)")
    ytd = ph.get("ytd_perf", {})
    if ytd:
        ax.text(0.02, 0.95, f"YTD: {company['ticker']} {ytd.get('ticker_pct', 0):+.1f}% vs JCI {ytd.get('jci_pct', 0):+.1f}% (rel {ytd.get('relative_pct', 0):+.1f}pp)",
                transform=ax.transAxes, fontsize=9, color="#24292f",
                bbox=dict(boxstyle="round,pad=0.4", fc="#f6f8fa", ec="#d0d7de"))
    ax.set_ylabel("Indexed (100 = first point)")
    ax.set_title(f"{company['ticker']} vs JCI — Relative Performance", fontsize=13, fontweight="bold")
    ax.legend(frameon=False, loc="best")
    _foot(fig, company, "indexed to 100 at first date; YTD absolute & relative")
    path = _save(fig, os.path.join(outdir, "vs_jci.png"))
    return {"id": "vs_jci", "file": "charts/vs_jci.png", "path": path, "title": "Price vs JCI (indexed)", "kind": "line", "source": source_label(company)}


def chart_peer_multiples(company: dict, outdir: str) -> dict:
    peers = company.get("peers", [])
    fig, ax = _new_ax()
    if not peers:
        ax.text(0.5, 0.5, "No peer data in input", ha="center", va="center", transform=ax.transAxes, fontsize=12, color="#57606a")
    else:
        labels = [p["ticker"] for p in peers]
        x = np.arange(len(labels))
        w = 0.38
        ax.bar(x - w / 2, [p.get("pe", 0) for p in peers], w, color=PALETTE[0], label="P/E")
        ax.bar(x + w / 2, [p.get("ev_ebitda", 0) for p in peers], w, color=PALETTE[1], label="EV/EBITDA")
        for xi, p in zip(x - w / 2, peers):
            ax.text(xi, p.get("pe", 0) + 0.2, f"{p.get('pe', 0):.1f}", ha="center", fontsize=8)
        for xi, p in zip(x + w / 2, peers):
            ax.text(xi, p.get("ev_ebitda", 0) + 0.2, f"{p.get('ev_ebitda', 0):.1f}", ha="center", fontsize=8)
        ax.set_xticks(x, labels)
        ax.set_ylabel("x")
        ax.legend(frameon=False)
    ax.set_title(f"{company['ticker']} — Peer Multiples (P/E & EV/EBITDA)", fontsize=13, fontweight="bold")
    _foot(fig, company, "peer set: " + ", ".join(p["ticker"] for p in peers[:5]) if peers else "")
    path = _save(fig, os.path.join(outdir, "peer_multiples.png"))
    return {"id": "peer_multiples", "file": "charts/peer_multiples.png", "path": path, "title": "Peer Multiples", "kind": "bar", "source": source_label(company)}


def chart_kpi(company: dict, outdir: str) -> dict:
    kpi = company.get("kpi", {})
    fig, ax = _new_ax()
    tenancy = kpi.get("tenancy_ratio")
    if tenancy is not None:
        ax.text(0.5, 0.55, f"Tenancy ratio {tenancy:.2f}x", ha="center", fontsize=20, color=PALETTE[0], fontweight="bold", transform=ax.transAxes)
        ax.text(0.5, 0.40, f"tenants {kpi.get('tenants', 0):,.0f} / towers {kpi.get('towers', 0):,.0f}", ha="center", fontsize=11, color="#24292f", transform=ax.transAxes)
        ax.text(0.5, 0.28, f"colocation {kpi.get('colocation', 0):,.0f} · fiber {kpi.get('fiber_km', 0):,.0f} km", ha="center", fontsize=11, color="#24292f", transform=ax.transAxes)
        ax.set_title(f"{company['ticker']} — Operational KPI (infra hero)", fontsize=13, fontweight="bold")
        ax.axis("off")
    else:
        keys = [k for k in ("ccpp_mw", "water_lps", "vessels", "tanks") if k in kpi]
        vals = [kpi[k] for k in keys]
        ax.bar(keys, [float(v) for v in vals], color=PALETTE[2])
        ax.set_title(f"{company['ticker']} — Operational KPI", fontsize=13, fontweight="bold")
        ax.set_ylabel("units")
    _foot(fig, company, kpi.get("kpi_period", ""))
    path = _save(fig, os.path.join(outdir, "kpi.png"))
    return {"id": "kpi", "file": "charts/kpi.png", "path": path, "title": "Operational KPI", "kind": "kpi-card/bar", "source": source_label(company)}


def chart_bands(company: dict, outdir: str) -> dict:
    """Historical valuation bands (MTEL pattern): PBV & EV/EBITDA ± STD around mean."""
    bands = company.get("bands", {})
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.8), dpi=DPI)
    fig.patch.set_facecolor("white")
    made = False
    for ax, key, name in ((axes[0], "pbv", "P/BV"), (axes[1], "ev_ebitda", "EV/EBITDA")):
        b = bands.get(key)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(True, alpha=0.25, linestyle="--", linewidth=0.6)
        if not b or not b.get("values"):
            ax.text(0.5, 0.5, "no band data", ha="center", va="center", transform=ax.transAxes, fontsize=10, color="#57606a")
            continue
        made = True
        dates, vals = b["dates"], b["values"]
        mean, std = b.get("mean"), b.get("std")
        ax.plot(dates, vals, marker="o", color=TICKER_COLOR, linewidth=2, label=name)
        if mean and std:
            ax.axhline(mean, color="#57606a", linestyle="--", linewidth=1, label=f"mean {mean:.2f}")
            for sgn, lab in ((-2, "-2σ"), (-1, "-1σ"), (1, "+1σ"), (2, "+2σ")):
                ax.axhline(mean + sgn * std, color="#bf8700", linestyle=":", linewidth=0.9)
            cur = vals[-1]
            pos = "ABOVE" if cur > mean + std else ("BELOW" if cur < mean - std else "within")
            ax.set_title(f"{name} — {pos} AVG ({cur:.2f}x)", fontsize=11, fontweight="bold")
        else:
            ax.set_title(f"{name} — historical", fontsize=11, fontweight="bold")
        ax.legend(frameon=False, fontsize=8)
    fig.suptitle(f"{company['ticker']} — Historical Valuation Bands (±σ)", fontsize=13, fontweight="bold")
    _foot(fig, company, "mean-reversion: STD+2/+1/AVG/-1/-2 labels (MTEL pattern)")
    path = _save(fig, os.path.join(outdir, "bands.png"))
    return {"id": "bands", "file": "charts/bands.png", "path": path, "title": "Historical Valuation Bands (P/BV & EV/EBITDA)", "kind": "bands", "source": source_label(company), "present": made}


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

MANDATED = [
    chart_revenue_mix, chart_trend, chart_margin, chart_leverage,
    chart_roe_roa, chart_vs_jci, chart_peer_multiples, chart_kpi,
]


def run(ticker: str) -> dict:
    company = load_company(ticker)
    outdir = ensure_out(ticker, "charts")
    charts = []
    for builder in MANDATED:
        try:
            meta = builder(company, outdir)
            charts.append(meta)
        except Exception as exc:  # keep pipeline alive; QA critic flags missing chart
            charts.append({"id": builder.__name__.replace("chart_", ""), "file": None, "path": None, "title": builder.__name__, "kind": "error", "source": source_label(company), "error": str(exc)})
    if company.get("bands") or company.get("archetype") == "infra":
        charts.append(chart_bands(company, outdir))
    manifest = {
        "ticker": ticker,
        "generated_at": now_iso(),
        "engine": ENGINE_VERSION,
        "source": source_label(company),
        "total": len(charts),
        "charts": [{k: v for k, v in c.items() if k != "path"} for c in charts],
    }
    write_json(os.path.join(ensure_out(ticker), "charts.json"), manifest)
    ok = sum(1 for c in charts if c.get("path"))
    print(f"[visualizer] {ticker}: {ok}/{len(charts)} charts written -> {os.path.join(outdir)}")
    for c in charts:
        if not c.get("path"):
            print(f"  !! missing: {c['id']} {c.get('error', '')}")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description="Visualizer agent (deterministic charts)")
    ap.add_argument("tickers", nargs="*")
    args = ap.parse_args()
    tickers = [t.upper() for t in args.tickers] or ["CDIA", "MTEL", "ADRO"]
    for t in tickers:
        run(t)


if __name__ == "__main__":
    main()
