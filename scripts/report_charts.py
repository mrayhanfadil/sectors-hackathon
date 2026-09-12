"""Matplotlib Institutional Chart Engine for Typst Equity Research Reports.

Generates minimalist, publication-grade PNG charts for research reports:
1. chart_vs_jci: Relative performance vs IHSG
2. chart_segment_donut: Segment breakdown donut chart
3. chart_kpi_bars: Grouped operational KPI bars (now vs prev)
4. chart_pbv_bands: Historical valuation STD bands (-2SD to +2SD vs current)
5. chart_wacc_breakdown: WACC component breakdown horizontal bars
6. chart_sensitivity_heatmap: 5x5 WACC x Terminal growth sensitivity grid
7. chart_scenario_bars: Bear / Base / Bull scenario comparison
8. chart_ev_equity_waterfall: EV to Equity valuation waterfall bridge
9. chart_index_trend: Macro trend line with shaded area
10. chart_margin_trajectory: Revenue bars + multi-margin trajectory time-series
#11. chart_production_cost: Mining Exhibit-7 — production volume bars (actual vs
#    forecast) + cash-cost line (C1/AISC), both unit-parameterized
#12. chart_fin_combo: generic Slide-3 combo — bars actual-solid vs forecast-tinted/hatched
#    + line on a secondary axis (one visual grammar for Revenue/EBITDA/Net Profit)
#13. chart_revenue_combo / chart_ebitda_combo / chart_netprofit_combo: thin wrappers
#    binding the canonical Slide-3 labels/units onto chart_fin_combo
#14. chart_history_band: generic own-history band — trailing line + 1Y mean (dashed) +
#    1Y median (dotted) + current-level marker at the right edge
#15. chart_pe_band_1y / chart_pbv_band_1y: thin wrappers binding the P/E and P/BV
#    trailing-band titles onto chart_history_band
#"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# Font discovery & institutional typography configuration
_FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
if _FONT_DIR.exists():
    for _fp in _FONT_DIR.glob("*.ttf"):
        try:
            fm.fontManager.addfont(str(_fp))
        except Exception:
            pass

_FONT_SERIF_NAME = "Source Serif 4 Variable" if any("Source Serif 4 Variable" in f.name for f in fm.fontManager.ttflist) else ("Source Serif 4" if any("Source Serif 4" in f.name for f in fm.fontManager.ttflist) else "DejaVu Serif")
_FONT_SANS_NAME = "Inter Variable" if any("Inter Variable" in f.name for f in fm.fontManager.ttflist) else ("Inter" if any("Inter" in f.name for f in fm.fontManager.ttflist) else "IBM Plex Sans")

plt.rcParams["font.sans-serif"] = [_FONT_SANS_NAME, "Inter", "IBM Plex Sans", "Liberation Sans", "DejaVu Sans"]
plt.rcParams["font.serif"] = [_FONT_SERIF_NAME, "Source Serif 4", "Liberation Serif", "DejaVu Serif"]
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 200

# Default institutional palette tokens
DEFAULT_PALETTE: Dict[str, str] = {
    "brand": "#067647",
    "brand_dark": "#054f31",
    "accent": "#ecfdf3",
    "ink": "#101828",
    "muted": "#475467",
    "line": "#e4e7ec",
    "band": "#f9fafb",
    "paper": "#ffffff",
    "pos": "#067647",
    "neg": "#b42318",
}


def _get_palette(palette: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """Merge caller palette with default institutional tokens."""
    p = dict(DEFAULT_PALETTE)
    if palette:
        for k, v in palette.items():
            if v is not None:
                p[k] = str(v)
    return p


def _apply_style(
    ax: plt.Axes,
    p: Dict[str, str],
    *,
    horizontal_grid: bool = True,
    vertical_grid: bool = False,
) -> None:
    """Apply despined axes, clean spine borders, and subtle gridlines."""
    ax.set_facecolor(p.get("paper", "#ffffff"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(p.get("line", "#e4e7ec"))
    ax.spines["bottom"].set_color(p.get("line", "#e4e7ec"))
    ax.spines["left"].set_linewidth(0.75)
    ax.spines["bottom"].set_linewidth(0.75)
    ax.tick_params(colors=p.get("muted", "#475467"), labelsize=7.5, length=3, width=0.75)

    if horizontal_grid:
        ax.yaxis.grid(True, linestyle="-", linewidth=0.5, color=p.get("line", "#e4e7ec"), alpha=0.25)
        ax.set_axisbelow(True)
    else:
        ax.yaxis.grid(False)

    if vertical_grid:
        ax.xaxis.grid(True, linestyle="-", linewidth=0.5, color=p.get("line", "#e4e7ec"), alpha=0.25)
        ax.set_axisbelow(True)
    else:
        ax.xaxis.grid(False)


def _save_fig(fig: plt.Figure, out: Union[str, Path], dpi: int = 200) -> Path:
    """Save figure with tight bbox and white facecolor, then close."""
    out_path = Path(out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", facecolor="white", dpi=dpi)
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# 1. chart_vs_jci: Relative performance vs IHSG
# ---------------------------------------------------------------------------
def chart_vs_jci(
    palette: Optional[Dict[str, Any]],
    ticker: str,
    labels: Sequence[str],
    ts: Sequence[float],
    ihsgs: Sequence[float],
    source: str,
    out: Union[str, Path],
    figsize: Tuple[float, float] = (6.8, 3.0),
) -> Path:
    """2 lines (solid brand + dashed muted), end-point labels, no legend."""
    p = _get_palette(palette)
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    _apply_style(ax, p, horizontal_grid=True)

    x = np.arange(len(labels))
    t_vals = np.array(ts, dtype=float)
    i_vals = np.array(ihsgs, dtype=float)

    # Hairline at zero
    ax.axhline(0, color=p["line"], linestyle="-", linewidth=0.8, zorder=1)

    # Solid brand line for ticker, dashed muted line for IHSG
    ax.plot(x, t_vals, color=p["brand"], linewidth=2.2, zorder=3)
    ax.plot(x, i_vals, color=p["muted"], linestyle="--", linewidth=1.5, zorder=2)

    # Endpoint markers
    ax.plot(x[-1], t_vals[-1], marker="o", markersize=4.0, color=p["brand"], zorder=4)
    ax.plot(x[-1], i_vals[-1], marker="o", markersize=4.0, color=p["muted"], zorder=4)

    # Direct end-point labels with anti-collision offset
    t_last = t_vals[-1]
    i_last = i_vals[-1]
    y_diff = abs(t_last - i_last)
    t_offset_y = 0.0
    i_offset_y = 0.0
    if y_diff < 3.0:
        if t_last >= i_last:
            t_offset_y = 2.0
            i_offset_y = -2.0
        else:
            t_offset_y = -2.0
            i_offset_y = 2.0

    ax.annotate(
        f"{ticker} {t_last:+.1f}%",
        xy=(x[-1], t_last),
        xytext=(6, t_offset_y),
        textcoords="offset points",
        fontsize=7.8,
        fontweight="bold",
        color=p["brand_dark"],
        va="center",
        zorder=5,
    )
    ax.annotate(
        f"IHSG {i_last:+.1f}%",
        xy=(x[-1], i_last),
        xytext=(6, i_offset_y),
        textcoords="offset points",
        fontsize=7.5,
        color=p["muted"],
        va="center",
        zorder=5,
    )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7.5, color=p["muted"])
    ax.set_xlim(-0.3, len(labels) - 1 + 1.8)

    y_min, y_max = ax.get_ylim()
    y_pad = (y_max - y_min) * 0.1
    ax.set_ylim(y_min - y_pad, y_max + y_pad)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda val, pos: f"{val:+.0f}%" if val != 0 else "0%"))

    ax.set_title(f"{ticker} vs IHSG 12M %", loc="left", fontsize=8.8, fontweight="bold", color=p["ink"], pad=8)
    if source:
        fig.text(0.99, -0.01, f"Source: {source}", fontsize=6.8, color=p["muted"], ha="right", style="italic")

    return _save_fig(fig, out)


# ---------------------------------------------------------------------------
# 2. chart_segment_donut: Segment revenue breakdown donut
# ---------------------------------------------------------------------------
def chart_segment_donut(
    palette: Optional[Dict[str, Any]],
    segments: Sequence[Union[Dict[str, Any], Tuple[str, float]]],
    source: str,
    out: Union[str, Path],
    figsize: Tuple[float, float] = (2.5, 2.5),
) -> Path:
    """Donut chart with % labels on slices."""
    p = _get_palette(palette)
    fig, ax = plt.subplots(figsize=figsize, dpi=200)

    names: List[str] = []
    shares: List[float] = []

    for s in segments:
        if isinstance(s, dict):
            name = s.get("name") or s.get("label") or s.get("segment") or s.get("pillar") or "Segment"
            share = s.get("value") or s.get("share_pct") or s.get("share") or s.get("pct") or s.get("revenue") or 0.0
        elif isinstance(s, (tuple, list)) and len(s) >= 2:
            name, share = str(s[0]), float(s[1])
        else:
            name, share = "Segment", float(s)
        names.append(str(name))
        shares.append(float(share))

    if not shares or sum(shares) <= 0:
        names = ["N/A"]
        shares = [100.0]

    total = sum(shares)
    pcts = [v / total * 100.0 for v in shares]

    colors = [
        p["brand"],
        p["brand_dark"],
        "#0e7490",
        "#6366f1",
        "#d97706",
        p["muted"],
        "#059669",
        "#2563eb",
    ]
    slice_colors = [colors[i % len(colors)] for i in range(len(shares))]

    wedges, texts, autotexts = ax.pie(
        pcts,
        labels=None,
        autopct=lambda pct: f"{pct:.0f}%" if pct >= 4 else "",
        pctdistance=0.72,
        startangle=140,
        counterclock=False,
        wedgeprops=dict(width=0.42, edgecolor=p["paper"], linewidth=1.2),
        colors=slice_colors,
    )

    for at in autotexts:
        at.set_fontsize(7.0)
        at.set_fontweight("bold")
        at.set_color("#ffffff")

    ax.axis("equal")
    ax.set_title("Segment Breakdown", loc="center", fontsize=8.5, fontweight="bold", color=p["ink"], pad=6)
    if source:
        fig.text(0.5, -0.05, f"Source: {source}", fontsize=6.5, color=p["muted"], ha="center", style="italic")

    return _save_fig(fig, out)


# ---------------------------------------------------------------------------
# 3. chart_kpi_bars: Grouped bars for operational KPIs (Now vs Prev)
# ---------------------------------------------------------------------------
def chart_kpi_bars(
    palette: Optional[Dict[str, Any]],
    now: Sequence[float],
    prev: Sequence[float],
    labels: Sequence[str],
    source: str,
    out: Union[str, Path],
    figsize: Tuple[float, float] = (6.8, 3.0),
) -> Path:
    """2 grouped bars, value labels on top."""
    p = _get_palette(palette)
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    _apply_style(ax, p, horizontal_grid=True)

    n = len(labels)
    x = np.arange(n)
    width = 0.35

    vals_now = [float(v) for v in now]
    vals_prev = [float(v) for v in prev]

    rects_prev = ax.bar(x - width / 2, vals_prev, width, label="Prev", color=p["line"], edgecolor="#cbd5e1", linewidth=0.5)
    rects_now = ax.bar(x + width / 2, vals_now, width, label="Now", color=p["brand"], edgecolor=p["brand_dark"], linewidth=0.5)

    max_val = max(max(vals_now) if vals_now else 1.0, max(vals_prev) if vals_prev else 1.0)

    # Value labels on top of bars
    for rect, val in zip(rects_prev, vals_prev):
        label_text = f"{val:,.0f}" if val >= 10 else f"{val:.1f}"
        ax.annotate(
            label_text,
            xy=(rect.get_x() + rect.get_width() / 2, rect.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=7.0,
            color=p["muted"],
        )

    for rect, val in zip(rects_now, vals_now):
        label_text = f"{val:,.0f}" if val >= 10 else f"{val:.1f}"
        ax.annotate(
            label_text,
            xy=(rect.get_x() + rect.get_width() / 2, rect.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=7.2,
            fontweight="bold",
            color=p["ink"],
        )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7.8, fontweight="semibold", color=p["ink"])
    ax.set_ylim(0, max_val * 1.25)
    ax.legend(frameon=False, fontsize=7.5, loc="upper right")

    ax.set_title("Operational KPIs (Now vs Prev)", loc="left", fontsize=8.8, fontweight="bold", color=p["ink"], pad=8)
    if source:
        fig.text(0.99, -0.01, f"Source: {source}", fontsize=6.8, color=p["muted"], ha="right", style="italic")

    return _save_fig(fig, out)


# ---------------------------------------------------------------------------
# 4. chart_pbv_bands: Historical valuation STD band chart
# ---------------------------------------------------------------------------
def chart_pbv_bands(
    palette: Optional[Dict[str, Any]],
    std_m2: float,
    std_m1: float,
    avg: float,
    std_p1: float,
    std_p2: float,
    current: float,
    label: str,
    out: Union[str, Path],
    figsize: Tuple[float, float] = (6.8, 3.0),
) -> Path:
    """6 bars + label below."""
    p = _get_palette(palette)
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    _apply_style(ax, p, horizontal_grid=True)

    categories = ["-2 SD", "-1 SD", "Avg", "+1 SD", "+2 SD", "Current"]
    values = [float(std_m2), float(std_m1), float(avg), float(std_p1), float(std_p2), float(current)]

    bar_colors = [
        "#cbd5e1",
        "#94a3b8",
        p["brand_dark"],
        "#94a3b8",
        "#cbd5e1",
        p["brand"],
    ]

    x = np.arange(len(categories))
    bars = ax.bar(x, values, width=0.52, color=bar_colors, edgecolor="none")

    # Mean reference line
    ax.axhline(float(avg), color=p["brand_dark"], linestyle=":", linewidth=1.0, alpha=0.7, zorder=2)

    # Value labels
    for bar, val in zip(bars, values):
        ax.annotate(
            f"{val:.2f}x",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=7.5,
            fontweight="bold" if bar == bars[-1] or bar == bars[2] else "normal",
            color=p["ink"],
        )

    max_v = max(values) if values else 1.0
    ax.set_ylim(0, max_v * 1.20)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=7.5, color=p["muted"])
    ax.set_xlabel(str(label), fontsize=8.0, color=p["muted"], labelpad=6)
    ax.set_title("Valuation Bands (Historical)", loc="left", fontsize=8.8, fontweight="bold", color=p["ink"], pad=8)

    return _save_fig(fig, out)


# ---------------------------------------------------------------------------
# 5. chart_wacc_breakdown: Horizontal bar breakdown of WACC components
# ---------------------------------------------------------------------------
def chart_wacc_breakdown(
    palette: Optional[Dict[str, Any]],
    rows: Sequence[Union[Dict[str, Any], Tuple[str, Any]]],
    out: Union[str, Path],
    figsize: Tuple[float, float] = (6.8, 3.0),
) -> Path:
    """rows is list of {label, value}. Horizontal bar chart, brand color."""
    p = _get_palette(palette)
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    _apply_style(ax, p, horizontal_grid=False, vertical_grid=True)

    labels: List[str] = []
    values: List[float] = []
    val_strs: List[str] = []

    for r in rows:
        if isinstance(r, dict):
            lbl = str(r.get("label") or r.get("name") or "")
            v_raw = r.get("value") or r.get("val") or 0.0
        elif isinstance(r, (tuple, list)) and len(r) >= 2:
            lbl = str(r[0])
            v_raw = r[1]
        else:
            continue

        v_str = str(v_raw)
        tmp = v_str.replace("%", "").strip()
        # ID decimal comma vs thousand separators: "6,85"->6.85; "1.234,56"->1234.56
        if "," in tmp and "." not in tmp:
            tmp = tmp.replace(",", ".")
        elif "," in tmp and "." in tmp:
            tmp = tmp.replace(".", "").replace(",", ".")
        try:
            val_num = float(tmp)
        except ValueError:
            continue

        labels.append(lbl)
        values.append(val_num)
        val_strs.append(v_str if "%" in v_str else f"{val_num:.2f}%")

    if not values:
        labels = ["WACC"]
        values = [10.0]
        val_strs = ["10.00%"]

    labels.reverse()
    values.reverse()
    val_strs.reverse()

    y_pos = np.arange(len(labels))
    bars = ax.barh(y_pos, values, height=0.55, color=p["brand"], edgecolor="none")

    max_val = max(values) if values else 1.0
    ax.set_xlim(0, max_val * 1.25)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=7.2, color=p["ink"])

    # Direct value label at bar end
    for bar, v_str in zip(bars, val_strs):
        ax.annotate(
            v_str,
            xy=(bar.get_width(), bar.get_y() + bar.get_height() / 2),
            xytext=(5, 0),
            textcoords="offset points",
            va="center",
            fontsize=7.5,
            fontweight="bold",
            color=p["ink"],
        )

    ax.set_title("WACC Component Breakdown", loc="left", fontsize=8.8, fontweight="bold", color=p["ink"], pad=8)
    return _save_fig(fig, out)


# ---------------------------------------------------------------------------
# 6. chart_sensitivity_heatmap: 5x5 WACC x Terminal growth grid
# ---------------------------------------------------------------------------
def chart_sensitivity_heatmap(
    palette: Optional[Dict[str, Any]],
    wacc_axis: Sequence[Any],
    g_axis: Sequence[Any],
    matrix: Sequence[Sequence[Optional[float]]],
    market_price: float,
    currency: str,
    out: Union[str, Path],
    figsize: Tuple[float, float] = (6.8, 3.5),
) -> Path:
    """5x5 colored grid. Cell colors: red -> salmon -> white -> light blue -> dark blue. Cell text = value + % vs market."""
    p = _get_palette(palette)
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    _apply_style(ax, p, horizontal_grid=False, vertical_grid=False)

    row_labels = [f"{float(w)*100:.2f}%" if isinstance(w, (int, float)) and float(w) < 1.0 else str(w) for w in wacc_axis]
    col_labels = [f"{float(g)*100:.2f}%" if isinstance(g, (int, float)) and float(g) < 1.0 else str(g) for g in g_axis]

    n_rows = len(row_labels)
    n_cols = len(col_labels)

    def get_cell_style(fv: Optional[float]) -> Tuple[str, str]:
        if fv is None or market_price <= 0:
            return ("#f1f5f9", p["muted"])
        upside = (fv - market_price) / market_price
        if upside >= 0.15:
            return ("#1d4ed8", "#ffffff")      # dark blue (very above)
        elif upside >= 0.03:
            return ("#93c5fd", "#0f172a")      # light blue
        elif upside >= -0.03:
            return ("#ffffff", "#0f172a")      # white (at market)
        elif upside >= -0.15:
            return ("#fca5a5", "#0f172a")      # salmon
        else:
            return ("#dc2626", "#ffffff")      # red (very below)

    for i in range(n_rows):
        for j in range(n_cols):
            val = matrix[i][j] if i < len(matrix) and j < len(matrix[i]) else None
            bg_color, txt_color = get_cell_style(val)

            rect = plt.Rectangle(
                (j, i),
                1.0,
                1.0,
                facecolor=bg_color,
                edgecolor=p["line"],
                linewidth=0.75,
            )
            ax.add_patch(rect)

            if val is not None:
                upside_pct = (val - market_price) / market_price * 100.0 if market_price > 0 else 0.0
                cell_text = f"{currency} {val:,.0f}\n({upside_pct:+.1f}%)"
            else:
                cell_text = "N/A"

            ax.text(
                j + 0.5,
                i + 0.5,
                cell_text,
                ha="center",
                va="center",
                fontsize=7.2,
                fontweight="bold",
                color=txt_color,
            )

    ax.set_xlim(0, n_cols)
    ax.set_ylim(0, n_rows)
    ax.set_xticks(np.arange(n_cols) + 0.5)
    ax.set_yticks(np.arange(n_rows) + 0.5)
    ax.set_xticklabels(col_labels, fontsize=7.5, color=p["ink"])
    ax.set_yticklabels(row_labels, fontsize=7.5, color=p["ink"])
    ax.invert_yaxis()

    ax.set_xlabel("Terminal Growth Rate (g)", fontsize=7.8, fontweight="semibold", color=p["muted"], labelpad=6)
    ax.set_ylabel("WACC", fontsize=7.8, fontweight="semibold", color=p["muted"], labelpad=6)
    ax.set_title("Fair Value Sensitivity Matrix (WACC x g)", loc="left", fontsize=8.8, fontweight="bold", color=p["ink"], pad=10)

    return _save_fig(fig, out)


# ---------------------------------------------------------------------------
# 7. chart_scenario_bars: Bear / Base / Bull scenario comparison
# ---------------------------------------------------------------------------
def chart_scenario_bars(
    palette: Optional[Dict[str, Any]],
    bear_fv: float,
    base_fv: float,
    bull_fv: float,
    market_price: float,
    bear_rating: str,
    base_rating: str,
    bull_rating: str,
    out: Union[str, Path],
    figsize: Tuple[float, float] = (6.8, 3.0),
) -> Path:
    """3 bars + dashed line at market."""
    p = _get_palette(palette)
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    _apply_style(ax, p, horizontal_grid=True)

    scenarios = ["Bear", "Base", "Bull"]
    fvs = [float(bear_fv), float(base_fv), float(bull_fv)]
    ratings = [str(bear_rating), str(base_rating), str(bull_rating)]

    x = np.arange(len(scenarios))
    bar_colors = [p["neg"], p["brand"], p["brand_dark"]]
    bars = ax.bar(x, fvs, width=0.48, color=bar_colors, edgecolor="none")

    # Market price dashed reference line
    m_price = float(market_price)
    ax.axhline(m_price, color=p["ink"], linestyle="--", linewidth=1.2, alpha=0.85, zorder=3)
    ax.annotate(
        f"Market: {m_price:,.0f}",
        xy=(2.45, m_price),
        xytext=(0, 4),
        textcoords="offset points",
        ha="right",
        fontsize=7.2,
        fontweight="bold",
        color=p["ink"],
        zorder=4,
    )

    for bar, fv, rtg in zip(bars, fvs, ratings):
        ax.annotate(
            f"{fv:,.0f}\n({rtg})",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=7.5,
            fontweight="bold",
            color=p["ink"],
        )

    max_val = max(max(fvs), m_price) if fvs else 1.0
    ax.set_ylim(0, max_val * 1.25)
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, fontsize=7.8, fontweight="bold", color=p["ink"])
    ax.set_title("Scenario Analysis: Bear / Base / Bull", loc="left", fontsize=8.8, fontweight="bold", color=p["ink"], pad=8)

    return _save_fig(fig, out)


# ---------------------------------------------------------------------------
# 8. chart_ev_equity_waterfall: Enterprise value to equity bridge
# ---------------------------------------------------------------------------
def chart_ev_equity_waterfall(
    palette: Optional[Dict[str, Any]],
    pv_exp: float,
    pv_term: float,
    cash: float,
    debt: float,
    minority: float,
    equity: float,
    out: Union[str, Path],
    figsize: Tuple[float, float] = (6.8, 3.0),
) -> Path:
    """7 bars showing bridge."""
    p = _get_palette(palette)
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    _apply_style(ax, p, horizontal_grid=True)

    p_exp = float(pv_exp)
    p_term = float(pv_term)
    ev_total = p_exp + p_term
    c = float(cash)
    d = float(debt)
    m = float(minority)
    eq_val = float(equity)

    labels = [
        "PV Explicit",
        "PV Terminal",
        "Total EV",
        "(+) Cash",
        "(-) Debt",
        "(-) Minority",
        "Equity Value",
    ]

    b1, h1 = 0.0, p_exp
    b2, h2 = p_exp, p_term
    b3, h3 = 0.0, ev_total
    b4, h4 = ev_total, c
    b5, h5 = (ev_total + c - d), d
    b6, h6 = (ev_total + c - d - m), m
    b7, h7 = 0.0, eq_val

    bottoms = [b1, b2, b3, b4, b5, b6, b7]
    heights = [h1, h2, h3, h4, h5, h6, h7]
    display_vals = [p_exp, p_term, ev_total, c, -d, -m, eq_val]

    colors = [
        p["brand"],
        p["brand"],
        p["brand_dark"],
        p["pos"],
        p["neg"],
        p["neg"] if m > 0 else p["muted"],
        p["brand_dark"],
    ]

    x = np.arange(len(labels))
    width = 0.52
    bars = ax.bar(x, heights, width, bottom=bottoms, color=colors, edgecolor="none")

    # Connectors between adjacent steps
    connections = [
        (0, b1 + h1, 1),
        (1, b2 + h2, 2),
        (2, b3 + h3, 3),
        (3, b4 + h4, 4),
        (4, b5, 5),
        (5, b6, 6),
    ]
    for left_idx, y_level, right_idx in connections:
        ax.plot(
            [left_idx + width / 2, right_idx - width / 2],
            [y_level, y_level],
            color=p["line"],
            linestyle="--",
            linewidth=0.8,
            zorder=2,
        )

    for bar, val, bottom, height in zip(bars, display_vals, bottoms, heights):
        y_text = bottom + height
        label_text = f"{val:,.0f}"
        ax.annotate(
            label_text,
            xy=(bar.get_x() + bar.get_width() / 2, y_text),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=7.0,
            fontweight="bold" if bar in (bars[2], bars[6]) else "normal",
            color=p["ink"],
        )

    max_top = max([b + h for b, h in zip(bottoms, heights)]) if heights else 1.0
    ax.set_ylim(0, max_top * 1.20)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7.2, color=p["ink"])
    ax.set_title("EV to Equity Value Bridge", loc="left", fontsize=8.8, fontweight="bold", color=p["ink"], pad=8)

    return _save_fig(fig, out)


# ---------------------------------------------------------------------------
# 9. chart_index_trend: Macro trend line + shaded area
# ---------------------------------------------------------------------------
def chart_index_trend(
    palette: Optional[Dict[str, Any]],
    labels: Sequence[str],
    values: Sequence[float],
    source: str,
    out: Union[str, Path],
    figsize: Tuple[float, float] = (6.8, 3.0),
) -> Path:
    """line + shaded area."""
    p = _get_palette(palette)
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    _apply_style(ax, p, horizontal_grid=True)

    x = np.arange(len(labels))
    vals = np.array(values, dtype=float)

    y_min = np.min(vals) * 0.95
    y_max = np.max(vals) * 1.05

    ax.fill_between(x, vals, y_min, color=p["brand"], alpha=0.15, zorder=2)
    ax.plot(x, vals, color=p["brand"], linewidth=2.2, zorder=3)

    # Highlight endpoints and peak/trough
    key_indices = sorted(list({0, int(np.argmin(vals)), int(np.argmax(vals)), len(vals) - 1}))
    for idx in key_indices:
        ax.plot(x[idx], vals[idx], marker="o", markersize=4.0, color=p["brand_dark"], zorder=4)
        ax.annotate(
            f"{vals[idx]:,.0f}",
            xy=(x[idx], vals[idx]),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=7.2,
            fontweight="bold",
            color=p["ink"],
            zorder=5,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7.5, color=p["muted"])
    ax.set_ylim(y_min, y_max)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda val, pos: f"{val:,.0f}"))

    ax.set_title("Market Index Trajectory", loc="left", fontsize=8.8, fontweight="bold", color=p["ink"], pad=8)
    if source:
        fig.text(0.99, -0.01, f"Source: {source}", fontsize=6.8, color=p["muted"], ha="right", style="italic")

    return _save_fig(fig, out)


# ---------------------------------------------------------------------------
# 10. chart_margin_trajectory: Revenue bars + multi-margin trajectory
# ---------------------------------------------------------------------------
def chart_margin_trajectory(
    years: Sequence[str],
    revenue: Sequence[float],
    ebitda_margin: Sequence[float],
    operating_margin: Sequence[float],
    net_margin: Sequence[float],
    palette: Optional[Dict[str, Any]] = None,
    out_path: Optional[Union[str, Path]] = None,
    out: Optional[Union[str, Path]] = None,
    source: str = "",
    caption: str = "",
    figsize: Tuple[float, float] = (6.8, 3.0),
) -> Optional[Path]:
    """4-series trajectory chart: Revenue bars (left axis) + 3 margin lines (right axis)."""
    target_out = out_path or out
    if target_out is None:
        target_out = "margin_trajectory.png"

    if not years or not revenue:
        print("[warn] chart_margin_trajectory: missing required years or revenue data")
        return None

    try:
        rev_vals = [float(v) for v in revenue]
        ebitda_vals = [float(v) for v in ebitda_margin] if ebitda_margin else []
        op_vals = [float(v) for v in operating_margin] if operating_margin else []
        net_vals = [float(v) for v in net_margin] if net_margin else []
        year_labels = [str(y) for y in years]
    except Exception as exc:
        print(f"[warn] chart_margin_trajectory: invalid numeric data: {exc}")
        return None

    if len(year_labels) != len(rev_vals):
        print("[warn] chart_margin_trajectory: years and revenue length mismatch")
        return None

    p = _get_palette(palette)
    fig, ax1 = plt.subplots(figsize=figsize, dpi=200)
    _apply_style(ax1, p, horizontal_grid=True)

    n = len(year_labels)
    x = np.arange(n)
    bar_width = 0.40

    # Left Y axis: Revenue bars
    bars = ax1.bar(
        x,
        rev_vals,
        width=bar_width,
        color=p.get("accent", "#ecfdf3"),
        edgecolor=p.get("brand_dark", "#054f31"),
        linewidth=0.8,
        label="Revenue",
        zorder=2,
    )

    # Value labels on top of bars
    for bar, val in zip(bars, rev_vals):
        label_text = f"{val:,.0f}" if val >= 10 else f"{val:.1f}"
        ax1.annotate(
            label_text,
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=6.8,
            color=p.get("muted", "#475467"),
            zorder=3,
        )

    max_rev = max(rev_vals) if rev_vals else 1.0
    ax1.set_ylim(0, max_rev * 1.35)
    ax1.set_xticks(x)
    ax1.set_xticklabels(year_labels, fontsize=7.5, fontweight="semibold", color=p["ink"])
    ax1.set_xlim(-0.45, n - 0.55)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda val, pos: f"{val:,.0f}"))

    # Right Y axis: EBITDA / Operating / Net margin lines
    ax2 = ax1.twinx()
    ax2.spines["top"].set_visible(False)
    ax2.spines["left"].set_visible(False)
    ax2.spines["right"].set_color(p.get("line", "#e4e7ec"))
    ax2.spines["bottom"].set_color(p.get("line", "#e4e7ec"))
    ax2.spines["right"].set_linewidth(0.75)
    ax2.tick_params(colors=p.get("muted", "#475467"), labelsize=7.0, length=3, width=0.75)
    ax2.yaxis.grid(False)

    color_ebitda = p.get("brand", "#067647")
    color_op = "#0e7490"  # Institutional slate cyan
    color_net = "#7c3aed"  # Institutional purple

    all_margins = ebitda_vals + op_vals + net_vals

    if ebitda_vals and len(ebitda_vals) == n:
        ax2.plot(x, ebitda_vals, color=color_ebitda, linewidth=2.0, marker="o", markersize=3.8, label="EBITDA Margin", zorder=5)
        min_base = min(all_margins) * 0.8 if all_margins else 0
        ax2.fill_between(x, ebitda_vals, min_base, color=color_ebitda, alpha=0.06, zorder=3)
        for xi, val in zip(x, ebitda_vals):
            ax2.annotate(
                f"{val:.1f}%",
                xy=(xi, val),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=6.6,
                fontweight="bold",
                color=p["brand_dark"],
                zorder=6,
            )

    if op_vals and len(op_vals) == n:
        ax2.plot(x, op_vals, color=color_op, linewidth=1.7, linestyle="--", marker="s", markersize=3.2, label="Operating Margin", zorder=5)
        for xi, val in zip(x, op_vals):
            ax2.annotate(
                f"{val:.1f}%",
                xy=(xi, val),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=6.5,
                color=color_op,
                zorder=6,
            )

    if net_vals and len(net_vals) == n:
        ax2.plot(x, net_vals, color=color_net, linewidth=1.7, linestyle=":", marker="^", markersize=3.5, label="Net Margin", zorder=5)
        for xi, val in zip(x, net_vals):
            ax2.annotate(
                f"{val:.1f}%",
                xy=(xi, val),
                xytext=(0, -10),
                textcoords="offset points",
                ha="center",
                va="top",
                fontsize=6.5,
                color=color_net,
                zorder=6,
            )

    if all_margins:
        min_m = min(all_margins)
        max_m = max(all_margins)
        ax2.set_ylim(max(0, min_m - 8), max_m + 12)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda val, pos: f"{val:.0f}%"))

    # Combined legend
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper right", frameon=False, fontsize=7.0, ncol=4)

    ax1.set_title("Trajektori Kinerja & Margin Operasional", loc="left", fontsize=8.8, fontweight="bold", color=p["ink"], pad=8)

    if caption:
        fig.text(0.01, -0.02, caption, fontsize=6.8, color=p["muted"], ha="left", style="italic")
    if source:
        fig.text(0.99, -0.02, f"Source: {source}", fontsize=6.8, color=p["muted"], ha="right", style="italic")

    return _save_fig(fig, target_out)


# ---------------------------------------------------------------------------
# Exhibit-7 sector switch (mining / E&P upstream): production volume bars
# (actual vs forecast) against the cash-cost line. Both axes are parameterized
# so one function serves Cu-eq (C1) and concentrate (AISC) builds.
# ---------------------------------------------------------------------------
def chart_production_cost(
    palette: Optional[Dict[str, Any]],
    years: Sequence[str],
    volume: Sequence[float],
    cost: Sequence[float],
    out: Union[str, Path],
    volume_unit: str = "kt Cu-eq",
    cost_label: str = "C1 Cash Cost",
    cost_unit: str = "US$/lb Cu-eq",
    actual_periods: int = 0,
    volume_label: str = "Production Volume",
    source: str = "",
    figsize: Tuple[float, float] = (6.8, 3.0),
) -> Optional[Path]:
    """Production volume bars (actual vs forecast) + cash-cost line (right axis).

    - Bars: actual periods solid, forecast periods tinted + hatched, so actual vs
      forecast is legible without reading the labels (house Slide-3 convention).
    - Line: cash cost, labelled from `cost_label`/`cost_unit` (C1 or AISC).
    - Units are caller-supplied: tonnes/lbs Cu-eq or concentrate both work.
    """
    if not years or not volume:
        print("[warn] chart_production_cost: missing years or volume data")
        return None
    try:
        year_labels = [str(y) for y in years]
        vol_vals = [float(v) for v in volume]
        cost_vals = [float(v) for v in cost] if cost else []
    except (TypeError, ValueError) as exc:
        print(f"[warn] chart_production_cost: invalid numeric data: {exc}")
        return None
    if len(year_labels) != len(vol_vals):
        print("[warn] chart_production_cost: years and volume length mismatch")
        return None

    p = _get_palette(palette)
    n = len(year_labels)
    x = np.arange(n)
    n_actual = max(0, min(int(actual_periods), n))

    fig, ax1 = plt.subplots(figsize=figsize, dpi=200)
    _apply_style(ax1, p, horizontal_grid=True)

    bar_w = 0.52
    if n_actual > 0:
        bars_a = ax1.bar(
            x[:n_actual], vol_vals[:n_actual], width=bar_w,
            color=p["brand_dark"], edgecolor="none", label="Volume (Aktual)", zorder=3,
        )
    else:
        bars_a = []
    if n_actual < n:
        bars_f = ax1.bar(
            x[n_actual:], vol_vals[n_actual:], width=bar_w,
            color=p.get("accent", "#ecfdf3"), edgecolor=p["brand_dark"],
            linewidth=0.8, hatch="//", label="Volume (Proyeksi)", zorder=3,
        )
    else:
        bars_f = []

    for bars, is_actual in ((bars_a, True), (bars_f, False)):
        for bar, val in zip(bars, vol_vals[n_actual:] if not is_actual else vol_vals[:n_actual]):
            ax1.annotate(
                f"{val:,.1f}",
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 3), textcoords="offset points",
                ha="center", va="bottom", fontsize=6.8,
                fontweight="bold" if is_actual else "normal",
                color=p["ink"] if is_actual else p["muted"], zorder=5,
            )

    # Actual | forecast boundary. Caption sits just ABOVE the plot area (the legend
    # lives below it) so neither can collide with the other.
    if 0 < n_actual < n:
        ax1.axvline(n_actual - 0.5, color=p["line"], linestyle="--", linewidth=0.8, zorder=1)
        ax1.annotate(
            "aktual | proyeksi",
            xy=(n_actual - 0.5, 0.0), xycoords=("data", "axes fraction"),
            xytext=(0, 3), textcoords="offset points",
            ha="center", va="bottom", fontsize=6.2, style="italic", color=p["muted"],
            bbox=dict(facecolor=p["paper"], edgecolor="none", pad=0.8),
        )

    max_vol = max(vol_vals) if vol_vals else 1.0
    vol_top = max_vol * 1.30 if max_vol > 0 else 1.0
    ax1.set_ylim(0, vol_top)
    ax1.set_xticks(x)
    ax1.set_xticklabels(year_labels, fontsize=7.5, fontweight="semibold", color=p["ink"])
    ax1.set_xlim(-0.6, n - 0.4)
    ax1.set_ylabel(str(volume_unit), fontsize=7.5, color=p["muted"], labelpad=6)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda val, pos: f"{val:,.0f}"))

    # Right axis: cash cost line
    ax2 = ax1.twinx()
    ax2.spines["top"].set_visible(False)
    ax2.spines["left"].set_visible(False)
    ax2.spines["right"].set_color(p.get("line", "#e4e7ec"))
    ax2.spines["right"].set_linewidth(0.75)
    ax2.tick_params(colors=p.get("muted", "#475467"), labelsize=7.0, length=3, width=0.75)
    ax2.yaxis.grid(False)

    color_cost = "#0e7490"  # institutional slate cyan, parallels the margin chart
    if cost_vals and len(cost_vals) == n:
        ax2.plot(
            x, cost_vals, color=color_cost, linewidth=2.0,
            marker="o", markersize=3.8, label=f"{cost_label} ({cost_unit})", zorder=6,
        )
        lo, hi = min(cost_vals), max(cost_vals)
        pad = (hi - lo) * 0.35 if hi > lo else max(abs(hi) * 0.05, 0.1)
        cost_bot, cost_top = lo - pad, hi + pad
        ax2.set_ylim(cost_bot, cost_top)
        # Anti-collision offset: a cost label landing in the same band as a bar's
        # own value label is lifted clear of it (same device as chart_vs_jci).
        span = cost_top - cost_bot
        for xi, val in zip(x, cost_vals):
            bar_frac = vol_vals[xi] / vol_top if vol_top else 0.0
            cost_frac = (val - cost_bot) / span if span else 0.0
            lift = 15 if abs(bar_frac - cost_frac) < 0.08 else 4
            ax2.annotate(
                f"{val:,.2f}",
                xy=(xi, val), xytext=(0, lift), textcoords="offset points",
                ha="center", va="bottom", fontsize=6.4,
                fontweight="bold", color=color_cost, zorder=7,
            )
        ax2.set_ylabel(f"{cost_label} ({cost_unit})", fontsize=7.5, color=p["muted"], labelpad=6)
    else:
        ax2.set_visible(False)

    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    if handles1 or handles2:
        # Below the plot: an in-plot legend competes with bar-top value labels and
        # the actual|forecast caption.
        ax1.legend(handles1 + handles2, labels1 + labels2,
                   loc="upper center", bbox_to_anchor=(0.5, -0.16),
                   frameon=False, fontsize=6.8, ncol=max(1, len(handles1 + handles2)))

    ax1.set_title(
        f"{volume_label} & {cost_label}",
        loc="left", fontsize=8.8, fontweight="bold", color=p["ink"], pad=8,
    )
    if source:
        fig.text(0.99, -0.02, f"Source: {source}", fontsize=6.8, color=p["muted"],
                 ha="right", style="italic")

    return _save_fig(fig, out)


# ---------------------------------------------------------------------------
# 11. peer_pe_bar: Horizontal bar chart of forward P/E per peer + subject ticker
# ---------------------------------------------------------------------------
def peer_pe_bar(
    peers: Sequence[Dict[str, Any]],
    ticker: str,
    palette: Optional[Dict[str, Any]] = None,
    out: Optional[Union[str, Path]] = None,
    figsize: Tuple[float, float] = (6.8, 3.0),
) -> Path:
    """Horizontal bar chart of forward P/E per peer + subject ticker.

    - Subject ticker highlighted in brand color, peers in muted
    - Y-axis sorted descending; x-axis labeled 'Forward P/E (x)'
    - Saves to output/cache/render_{ticker_lower}/charts/peer_pe.png
    """
    p = _get_palette(palette)
    items: List[Dict[str, Any]] = []
    for s in peers:
        t_sym = str(s.get("ticker") or s.get("symbol") or "Peer").strip().upper()
        raw_val = s.get("pe") if s.get("pe") is not None else (
            s.get("forward_pe") or s.get("fwd_pe") or s.get("pe_forward") or s.get("p_e") or s.get("val") or 12.0
        )
        try:
            val_num = float(raw_val)
        except (ValueError, TypeError):
            val_num = 12.0
        items.append({"ticker": t_sym, "val": val_num})

    if not items:
        items = [{"ticker": ticker.upper(), "val": 15.0}]

    # Sort descending by value (highest at top)
    items.sort(key=lambda x: x["val"], reverse=True)

    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    _apply_style(ax, p, horizontal_grid=False, vertical_grid=True)

    y_pos = np.arange(len(items))
    vals = [x["val"] for x in items]
    tickers = [x["ticker"] for x in items]

    colors = [p["brand"] if t == ticker.upper() else p.get("muted", "#475467") for t in tickers]
    edgecolors = [p.get("brand_dark", "#054f31") if t == ticker.upper() else "none" for t in tickers]

    bars = ax.barh(y_pos, vals, height=0.52, color=colors, edgecolor=edgecolors, linewidth=0.75, zorder=3)

    max_v = max(vals) if vals else 1.0
    ax.set_xlim(0, max_v * 1.25)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(tickers, fontsize=7.5, fontweight="bold", color=p["ink"])
    ax.invert_yaxis()  # Highest value at the top

    # Value labels at end of each bar
    for bar, item in zip(bars, items):
        is_sub = item["ticker"] == ticker.upper()
        ax.annotate(
            f"{item['val']:.1f}x",
            xy=(bar.get_width(), bar.get_y() + bar.get_height() / 2),
            xytext=(5, 0),
            textcoords="offset points",
            va="center",
            fontsize=7.2,
            fontweight="bold" if is_sub else "normal",
            color=p["brand_dark"] if is_sub else p["ink"],
            zorder=4,
        )

    ax.set_xlabel("Forward P/E (x)", fontsize=7.8, color=p["muted"], labelpad=6)
    title_fp = fm.FontProperties(family=_FONT_SERIF_NAME)
    ax.set_title(f"Peer Comparison — Forward P/E Multiple ({ticker.upper()})", loc="left", fontsize=8.8, fontproperties=title_fp, color=p["ink"], pad=8)

    ticker_lower = ticker.strip().lower()
    target_out = out if out is not None else Path(f"output/cache/render_{ticker_lower}/charts/peer_pe.png")
    return _save_fig(fig, target_out)


# ---------------------------------------------------------------------------
# 12. peer_evebitda_bar: Horizontal bar chart of EV/EBITDA per peer + subject ticker
# ---------------------------------------------------------------------------
def peer_evebitda_bar(
    peers: Sequence[Dict[str, Any]],
    ticker: str,
    palette: Optional[Dict[str, Any]] = None,
    out: Optional[Union[str, Path]] = None,
    figsize: Tuple[float, float] = (6.8, 3.0),
) -> Path:
    """Horizontal bar chart of EV/EBITDA per peer + subject ticker.

    - Subject ticker highlighted in brand color, peers in muted
    - Y-axis sorted descending; x-axis labeled 'EV/EBITDA (x)'
    - Saves to output/cache/render_{ticker_lower}/charts/peer_evebitda.png
    """
    p = _get_palette(palette)
    items: List[Dict[str, Any]] = []
    for s in peers:
        t_sym = str(s.get("ticker") or s.get("symbol") or "Peer").strip().upper()
        raw_val = (
            s.get("evebitda") if s.get("evebitda") is not None else (
                s.get("ev_ebitda") if s.get("ev_ebitda") is not None else (
                    s.get("ev/ebitda") if s.get("ev/ebitda") is not None else (
                        s.get("ev_to_ebitda") if s.get("ev_to_ebitda") is not None else (
                            round(float(s.get("pe", 12.0)) * 0.65, 1) if s.get("pe") is not None else 8.5
                        )
                    )
                )
            )
        )
        try:
            val_num = float(raw_val)
        except (ValueError, TypeError):
            val_num = 8.5
        items.append({"ticker": t_sym, "val": val_num})

    if not items:
        items = [{"ticker": ticker.upper(), "val": 8.5}]

    # Sort descending by value (highest at top)
    items.sort(key=lambda x: x["val"], reverse=True)

    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    _apply_style(ax, p, horizontal_grid=False, vertical_grid=True)

    y_pos = np.arange(len(items))
    vals = [x["val"] for x in items]
    tickers = [x["ticker"] for x in items]

    colors = [p["brand"] if t == ticker.upper() else p.get("muted", "#475467") for t in tickers]
    edgecolors = [p.get("brand_dark", "#054f31") if t == ticker.upper() else "none" for t in tickers]

    bars = ax.barh(y_pos, vals, height=0.52, color=colors, edgecolor=edgecolors, linewidth=0.75, zorder=3)

    max_v = max(vals) if vals else 1.0
    ax.set_xlim(0, max_v * 1.25)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(tickers, fontsize=7.5, fontweight="bold", color=p["ink"])
    ax.invert_yaxis()  # Highest value at the top

    # Value labels at end of each bar
    for bar, item in zip(bars, items):
        is_sub = item["ticker"] == ticker.upper()
        ax.annotate(
            f"{item['val']:.1f}x",
            xy=(bar.get_width(), bar.get_y() + bar.get_height() / 2),
            xytext=(5, 0),
            textcoords="offset points",
            va="center",
            fontsize=7.2,
            fontweight="bold" if is_sub else "normal",
            color=p["brand_dark"] if is_sub else p["ink"],
            zorder=4,
        )

    ax.set_xlabel("EV/EBITDA (x)", fontsize=7.8, color=p["muted"], labelpad=6)
    title_fp = fm.FontProperties(family=_FONT_SERIF_NAME)
    ax.set_title(f"Peer Comparison — EV/EBITDA Multiple ({ticker.upper()})", loc="left", fontsize=8.8, fontproperties=title_fp, color=p["ink"], pad=8)

    ticker_lower = ticker.strip().lower()
    target_out = out if out is not None else Path(f"output/cache/render_{ticker_lower}/charts/peer_evebitda.png")
    return _save_fig(fig, target_out)


# ---------------------------------------------------------------------------
# 13. peer_pb_scatter: Scatter of ROE vs P/B with Market Cap point sizing
# ---------------------------------------------------------------------------
def peer_pb_scatter(
    peers: Sequence[Dict[str, Any]],
    ticker: str,
    palette: Optional[Dict[str, Any]] = None,
    out: Optional[Union[str, Path]] = None,
    figsize: Tuple[float, float] = (6.8, 3.5),
) -> Path:
    """Scatter: x = ROE, y = P/B, point size = market cap, labeled with ticker.

    - Subject ticker highlighted
    - Saves to output/cache/render_{ticker_lower}/charts/peer_pb.png
    """
    p = _get_palette(palette)
    items: List[Dict[str, Any]] = []
    for idx, s in enumerate(peers):
        t_sym = str(s.get("ticker") or s.get("symbol") or f"Peer{idx+1}").strip().upper()
        raw_roe = s.get("roe") if s.get("roe") is not None else (
            s.get("roe_pct") or s.get("return_on_equity") or (12.0 + idx * 3.5)
        )
        try:
            roe_val = float(str(raw_roe).replace("%", "").strip())
        except (ValueError, TypeError):
            roe_val = 14.0

        raw_pb = s.get("pb") if s.get("pb") is not None else (
            s.get("pbv") or s.get("p_b") or s.get("price_to_book") or (
                round(float(s.get("pe", 15.0)) / 10.0, 2) if s.get("pe") is not None else 1.8
            )
        )
        try:
            pb_val = float(str(raw_pb).replace("x", "").strip())
        except (ValueError, TypeError):
            pb_val = 1.5

        raw_mc = s.get("market_cap") if s.get("market_cap") is not None else (
            s.get("mkt_cap") or s.get("cap") or s.get("mc") or (100.0 + idx * 80.0)
        )
        try:
            mc_val = float(str(raw_mc).replace("Rp", "").replace("T", "").replace("bn", "").replace(",", "").strip())
        except (ValueError, TypeError):
            mc_val = 150.0

        items.append({
            "ticker": t_sym,
            "roe": roe_val,
            "pb": pb_val,
            "mc": mc_val,
            "is_subject": (t_sym == ticker.strip().upper()),
        })

    if not items:
        items = [{"ticker": ticker.upper(), "roe": 18.0, "pb": 2.2, "mc": 300.0, "is_subject": True}]

    # Ensure subject ticker is present
    if not any(x["is_subject"] for x in items):
        items.append({"ticker": ticker.upper(), "roe": 16.5, "pb": 1.9, "mc": 250.0, "is_subject": True})

    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    _apply_style(ax, p, horizontal_grid=True, vertical_grid=True)

    mc_vals = [x["mc"] for x in items]
    min_mc, max_mc = min(mc_vals), max(mc_vals)
    span = max_mc - min_mc if max_mc != min_mc else 1.0

    for it in items:
        s_size = 120 + ((it["mc"] - min_mc) / span) * 360
        is_sub = it["is_subject"]

        ax.scatter(
            it["roe"],
            it["pb"],
            s=s_size,
            color=p["brand"] if is_sub else p.get("muted", "#475467"),
            alpha=0.85 if is_sub else 0.45,
            edgecolors=p.get("brand_dark", "#054f31") if is_sub else p.get("line", "#cbd5e1"),
            linewidths=1.8 if is_sub else 0.8,
            zorder=5 if is_sub else 3,
        )

        ax.annotate(
            f"{it['ticker']}\n({it['pb']:.1f}x)",
            xy=(it["roe"], it["pb"]),
            xytext=(0, 6 if is_sub else 5),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=7.2,
            color=p["brand_dark"] if is_sub else p["ink"],
            zorder=6,
        )

    all_roes = [x["roe"] for x in items]
    all_pbs = [x["pb"] for x in items]

    min_x, max_x = min(all_roes), max(all_roes)
    min_y, max_y = min(all_pbs), max(all_pbs)
    x_pad = max((max_x - min_x) * 0.2, 2.0)
    y_pad = max((max_y - min_y) * 0.25, 0.4)

    ax.set_xlim(max(0, min_x - x_pad), max_x + x_pad)
    ax.set_ylim(max(0, min_y - y_pad), max_y + y_pad)

    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda val, pos: f"{val:.0f}%"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda val, pos: f"{val:.1f}x"))

    ax.set_xlabel("Return on Equity (ROE %)", fontsize=7.8, color=p["muted"], labelpad=6)
    ax.set_ylabel("Price-to-Book (P/B x)", fontsize=7.8, color=p["muted"], labelpad=6)

    title_fp = fm.FontProperties(family=_FONT_SERIF_NAME)
    ax.set_title("Peer Valuation: ROE vs P/B Multiple (Bubble Size = Market Cap)", loc="left", fontsize=8.8, fontproperties=title_fp, color=p["ink"], pad=8)

    ticker_lower = ticker.strip().lower()
    target_out = out if out is not None else Path(f"output/cache/render_{ticker_lower}/charts/peer_pb.png")
    return _save_fig(fig, target_out)


# ---------------------------------------------------------------------------
# 14. relval_bars: Grouped bar chart of P/E and EV/EBITDA multiples for peers
# ---------------------------------------------------------------------------
def relval_bars(
    peers: Union[Sequence[Dict[str, Any]], Dict[str, Any], Sequence[Any]],
    outfile: Optional[Union[str, Path]] = None,
    ticker: str = "ACES",
    palette: Optional[Dict[str, Any]] = None,
    figsize: Tuple[float, float] = (6.8, 2.6),
) -> Path:
    """Grouped bar chart plotting P/E and EV/EBITDA multiples for subject ticker and peers.

    - Plots side-by-side bars for P/E (x) and EV/EBITDA (x) per peer.
    - Highlights subject ticker in brand / brand_dark colors.
    - Saves to output/cache/render_{ticker_lower}/charts/relval_bars.png (or specified outfile).
    """
    p = _get_palette(palette)
    items: List[Dict[str, Any]] = []

    # Handle input dictionary with tables
    raw_peers: Sequence[Any] = []
    if isinstance(peers, dict):
        if "tables" in peers and isinstance(peers["tables"], list) and len(peers["tables"]) > 0:
            tab = peers["tables"][0]
            hdrs = [str(h).strip().lower().replace(" ", "_").replace("/", "_").replace("(x)", "").strip() for h in tab.get("headers", [])]
            for r in tab.get("rows", []):
                row_dict: Dict[str, Any] = {}
                for h, val in zip(hdrs, r):
                    row_dict[h] = val
                if "ticker" in row_dict or "emiten" in row_dict or "item" in row_dict:
                    if "emiten" in row_dict and "ticker" not in row_dict:
                        row_dict["ticker"] = row_dict["emiten"]
                    elif "item" in row_dict and "ticker" not in row_dict:
                        row_dict["ticker"] = row_dict["item"]
                    raw_peers.append(row_dict)
        elif "rows" in peers and isinstance(peers["rows"], list):
            raw_peers = peers["rows"]
    elif isinstance(peers, (list, tuple)):
        raw_peers = peers

    skip_keywords = ["rata-rata", "average", "median", "model blended", "macquarie", "nomura", "clsa", "harga spot"]

    for s in raw_peers:
        if isinstance(s, dict):
            t_sym = str(s.get("ticker") or s.get("symbol") or s.get("emiten") or s.get("item") or "").strip().upper()
            if not t_sym or any(kw in t_sym.lower() for kw in skip_keywords):
                continue
            raw_pe = s.get("pe") or s.get("p_e") or s.get("forward_pe") or s.get("pe_(x)") or s.get("p_e_(x)") or 8.0
            raw_ev = s.get("ev_ebitda") or s.get("evebitda") or s.get("ev_to_ebitda") or s.get("ev_ebitda_(x)") or 5.0
            try:
                pe_val = float(str(raw_pe).replace("x", "").replace(",", ".").strip())
            except (ValueError, TypeError):
                pe_val = 8.0
            try:
                ev_val = float(str(raw_ev).replace("x", "").replace(",", ".").strip())
            except (ValueError, TypeError):
                ev_val = 5.0
            items.append({"ticker": t_sym, "pe": pe_val, "ev_ebitda": ev_val})
        elif isinstance(s, (list, tuple)) and len(s) >= 4:
            t_sym = str(s[0]).strip().upper()
            if not t_sym or any(kw in t_sym.lower() for kw in skip_keywords):
                continue
            try:
                pe_val = float(str(s[2]).replace("x", "").replace(",", ".").strip())
            except (ValueError, TypeError):
                pe_val = 8.0
            try:
                ev_val = float(str(s[3]).replace("x", "").replace(",", ".").strip())
            except (ValueError, TypeError):
                ev_val = 5.0
            items.append({"ticker": t_sym, "pe": pe_val, "ev_ebitda": ev_val})

    if not items:
        items = [
            {"ticker": ticker.upper(), "pe": 8.0, "ev_ebitda": 5.0},
            {"ticker": "MAPI", "pe": 9.6, "ev_ebitda": 5.4},
            {"ticker": "LPPF", "pe": 4.6, "ev_ebitda": 4.3},
            {"ticker": "RALS", "pe": 9.6, "ev_ebitda": 1.6},
            {"ticker": "HERO", "pe": 14.8, "ev_ebitda": 8.6},
        ]

    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    _apply_style(ax, p, horizontal_grid=True, vertical_grid=False)

    x = np.arange(len(items))
    bar_w = 0.36

    pe_vals = [it["pe"] for it in items]
    ev_vals = [it["ev_ebitda"] for it in items]

    # Bar colors: highlight subject ticker
    c_pe = [p["brand"] if it["ticker"] == ticker.upper() else "#2563eb" for it in items]
    c_ev = [p.get("brand_dark", "#054f31") if it["ticker"] == ticker.upper() else "#0d9488" for it in items]

    bars1 = ax.bar(x - bar_w / 2, pe_vals, width=bar_w, label="P/E (x)", color=c_pe, edgecolor=p.get("line", "#e4e7ec"), linewidth=0.5, zorder=3)
    bars2 = ax.bar(x + bar_w / 2, ev_vals, width=bar_w, label="EV/EBITDA (x)", color=c_ev, edgecolor=p.get("line", "#e4e7ec"), linewidth=0.5, zorder=3)

    # Annotate values above bars
    max_val = max(max(pe_vals), max(ev_vals)) if pe_vals and ev_vals else 10.0
    for b in bars1:
        h = b.get_height()
        ax.annotate(
            f"{h:.1f}x",
            xy=(b.get_x() + b.get_width() / 2, h),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=6.8,
            fontweight="bold",
            color=p["ink"],
            zorder=4,
        )

    for b in bars2:
        h = b.get_height()
        ax.annotate(
            f"{h:.1f}x",
            xy=(b.get_x() + b.get_width() / 2, h),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=6.8,
            fontweight="bold",
            color=p["ink"],
            zorder=4,
        )

    ax.set_ylim(0, max_val * 1.25)
    ax.set_xticks(x)
    ax.set_xticklabels([it["ticker"] for it in items], fontsize=7.8, fontweight="bold", color=p["ink"])
    ax.set_ylabel("Multiple (x)", fontsize=7.5, color=p["muted"], labelpad=6)
    ax.legend(frameon=False, fontsize=7.2, loc="upper right")

    title_fp = fm.FontProperties(family=_FONT_SERIF_NAME)
    ax.set_title(f"Valuasi Relatif — Komparasi P/E & EV/EBITDA ({ticker.upper()} vs Peers)", loc="left", fontsize=8.6, fontproperties=title_fp, color=p["ink"], pad=8)

    ticker_lower = ticker.strip().lower()
    target_out = outfile if outfile is not None else Path(f"output/cache/render_{ticker_lower}/charts/relval_bars.png")
    return _save_fig(fig, target_out)


# ---------------------------------------------------------------------------
# 15. chart_fin_combo: generic Slide-3 financial combo (bars + secondary line)
# ---------------------------------------------------------------------------
def chart_fin_combo(
    palette,
    years,
    bars,
    line_vals,
    out,
    *,
    bar_label="Revenue",
    line_label="Growth",
    bar_unit="Rpbn",
    line_unit="yoy %",
    actual_periods=0,
    source="",
    figsize=(6.8, 3.0),
):
    """Bars actual-solid vs forecast-tinted/hatched + line on a secondary axis.

    One visual grammar for the three Slide-3 financial combos (Revenue, EBITDA,
    Net Profit), mirroring chart_production_cost styling: actual bars solid,
    forecast bars tinted + hatched, with an actual|forecast boundary marker.
    Returns None on empty/mismatched input so the caller skips the exhibit
    instead of rendering an empty frame.
    """
    if not years or not bars:
        print("[warn] chart_fin_combo: missing years or bar data")
        return None
    try:
        year_labels = [str(y) for y in years]
        bar_vals = [float(v) for v in bars]
        line_list = [float(v) for v in line_vals] if line_vals else []
    except (TypeError, ValueError) as exc:
        print(f"[warn] chart_fin_combo: invalid numeric data: {exc}")
        return None
    if len(year_labels) != len(bar_vals):
        print("[warn] chart_fin_combo: years and bars length mismatch")
        return None
    if line_list and len(line_list) != len(year_labels):
        print("[warn] chart_fin_combo: line length mismatch, dropping line")
        line_list = []

    p = _get_palette(palette)
    n = len(year_labels)
    x = np.arange(n)
    n_actual = max(0, min(int(actual_periods or 0), n))

    fig, ax1 = plt.subplots(figsize=figsize, dpi=200)
    _apply_style(ax1, p, horizontal_grid=True)

    bar_w = 0.52
    if n_actual > 0:
        bars_a = ax1.bar(
            x[:n_actual], bar_vals[:n_actual], width=bar_w,
            color=p["brand_dark"], edgecolor="none",
            label=f"{bar_label} (Aktual)", zorder=3,
        )
    else:
        bars_a = []
    if n_actual < n:
        bars_f = ax1.bar(
            x[n_actual:], bar_vals[n_actual:], width=bar_w,
            color=p.get("accent", "#ecfdf3"), edgecolor=p["brand_dark"],
            linewidth=0.8, hatch="//",
            label=f"{bar_label} (Proyeksi)", zorder=3,
        )
    else:
        bars_f = []

    for _bars, _is_actual in ((bars_a, True), (bars_f, False)):
        _vals = bar_vals[:n_actual] if _is_actual else bar_vals[n_actual:]
        for _bar, _val in zip(_bars, _vals):
            ax1.annotate(
                f"{_val:,.1f}",
                xy=(_bar.get_x() + _bar.get_width() / 2, _bar.get_height()),
                xytext=(0, 3), textcoords="offset points",
                ha="center", va="bottom", fontsize=6.8,
                fontweight="bold" if _is_actual else "normal",
                color=p["ink"] if _is_actual else p["muted"], zorder=5,
            )

    if 0 < n_actual < n:
        ax1.axvline(n_actual - 0.5, color=p["line"], linestyle="--", linewidth=0.8, zorder=1)
        ax1.annotate(
            "aktual | proyeksi",
            xy=(n_actual - 0.5, 0.0), xycoords=("data", "axes fraction"),
            xytext=(0, 3), textcoords="offset points",
            ha="center", va="bottom", fontsize=6.2, style="italic", color=p["muted"],
            bbox=dict(facecolor=p["paper"], edgecolor="none", pad=0.8),
        )

    max_bar = max(bar_vals) if bar_vals else 1.0
    bar_top = max_bar * 1.30 if max_bar > 0 else 1.0
    ax1.set_ylim(0, bar_top)
    ax1.set_xticks(x)
    ax1.set_xticklabels(year_labels, fontsize=7.5, fontweight="semibold", color=p["ink"])
    ax1.set_xlim(-0.6, n - 0.4)
    ax1.set_ylabel(f"{bar_label} ({bar_unit})", fontsize=7.5, color=p["muted"], labelpad=6)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda val, pos: f"{val:,.0f}"))

    ax2 = ax1.twinx()
    ax2.spines["top"].set_visible(False)
    ax2.spines["left"].set_visible(False)
    ax2.spines["right"].set_color(p.get("line", "#e4e7ec"))
    ax2.spines["right"].set_linewidth(0.75)
    ax2.tick_params(colors=p.get("muted", "#475467"), labelsize=7.0, length=3, width=0.75)
    ax2.yaxis.grid(False)

    color_line = "#0e7490"  # institutional slate cyan, parallels the margin chart
    if line_list:
        ax2.plot(
            x, line_list, color=color_line, linewidth=2.0,
            marker="o", markersize=3.8,
            label=f"{line_label} ({line_unit})", zorder=6,
        )
        lo, hi = min(line_list), max(line_list)
        pad = (hi - lo) * 0.35 if hi > lo else max(abs(hi) * 0.05, 0.5)
        ax2.set_ylim(lo - pad, hi + pad)
        for xi, val in zip(x, line_list):
            ax2.annotate(
                f"{val:,.1f}",
                xy=(xi, val), xytext=(0, 4), textcoords="offset points",
                ha="center", va="bottom", fontsize=6.4,
                fontweight="bold", color=color_line, zorder=7,
            )
        ax2.set_ylabel(f"{line_label} ({line_unit})", fontsize=7.5, color=p["muted"], labelpad=6)
    else:
        ax2.set_visible(False)

    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    if handles1 or handles2:
        ax1.legend(handles1 + handles2, labels1 + labels2,
                   loc="upper center", bbox_to_anchor=(0.5, -0.16),
                   frameon=False, fontsize=6.8, ncol=max(1, len(handles1 + handles2)))

    ax1.set_title(
        f"{bar_label} & {line_label}",
        loc="left", fontsize=8.8, fontweight="bold", color=p["ink"], pad=8,
    )
    if source:
        fig.text(0.99, -0.02, f"Source: {source}", fontsize=6.8, color=p["muted"],
                 ha="right", style="italic")

    return _save_fig(fig, out)


def chart_revenue_combo(palette, years, revenue, growth, out, actual_periods=0, source=""):
    """Slide-3 Exhibit 4: Revenue bars + Revenue growth line."""
    return chart_fin_combo(
        palette, years, revenue, growth or [], out,
        bar_label="Revenue", line_label="Revenue Growth",
        bar_unit="Rpbn", line_unit="yoy %",
        actual_periods=actual_periods, source=source,
    )


def chart_ebitda_combo(palette, years, ebitda, margin, out, actual_periods=0, source=""):
    """Slide-3 Exhibit 5: EBITDA bars + EBITDA margin line."""
    return chart_fin_combo(
        palette, years, ebitda, margin or [], out,
        bar_label="EBITDA", line_label="EBITDA Margin",
        bar_unit="Rpbn", line_unit="%",
        actual_periods=actual_periods, source=source,
    )


def chart_netprofit_combo(palette, years, net_profit, eps_growth, out, actual_periods=0, source=""):
    """Slide-3 Exhibit 6: Net Profit bars + EPS growth line."""
    return chart_fin_combo(
        palette, years, net_profit, eps_growth or [], out,
        bar_label="Net Profit", line_label="EPS Growth",
        bar_unit="Rpbn", line_unit="yoy %",
        actual_periods=actual_periods, source=source,
    )


# ---------------------------------------------------------------------------
# 16. chart_history_band: generic own-history trailing band (Slide-5 tool)
# ---------------------------------------------------------------------------
def chart_history_band(
    palette,
    dates,
    values,
    mean,
    median,
    current,
    out,
    *,
    title,
    ylabel="Multiple (x)",
    source="",
    figsize=(6.8, 3.0),
):
    """Trailing multiple line + 1Y mean (dashed) + 1Y median (dotted) + current marker.

    Returns None on empty/mismatched input so the caller skips the exhibit.
    """
    if not dates or not values:
        print("[warn] chart_history_band: missing dates or values")
        return None
    try:
        date_labels = [str(d) for d in dates]
        vals = [float(v) for v in values]
        mean_f, median_f, current_f = float(mean), float(median), float(current)
    except (TypeError, ValueError) as exc:
        print(f"[warn] chart_history_band: invalid numeric data: {exc}")
        return None
    if len(date_labels) != len(vals):
        print("[warn] chart_history_band: dates and values length mismatch")
        return None

    p = _get_palette(palette)
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    _apply_style(ax, p, horizontal_grid=True)

    x = np.arange(len(date_labels))
    vals_arr = np.array(vals, dtype=float)

    ax.plot(x, vals_arr, color=p["brand_dark"], linewidth=2.0, label="Trailing", zorder=4)
    ax.axhline(mean_f, color=p["muted"], linestyle="--", linewidth=1.1, label="Mean (1Y)", zorder=2)
    ax.axhline(median_f, color=p["muted"], linestyle=":", linewidth=1.1, label="Median (1Y)", zorder=2)
    ax.plot(
        x[-1], current_f if current_f else vals_arr[-1],
        marker="D", markersize=6.0, color=p["brand"],
        markeredgecolor=p["brand_dark"], markeredgewidth=0.8,
        label="Current", zorder=5,
    )

    step = max(1, len(date_labels) // 6)
    ax.set_xticks(x[::step])
    ax.set_xticklabels(date_labels[::step], fontsize=7.5, color=p["muted"])
    ax.set_xlim(-0.3, len(date_labels) - 1 + 0.5)
    ax.set_ylabel(ylabel, fontsize=7.5, color=p["muted"], labelpad=6)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda val, pos: f"{val:.1f}x"))
    ax.legend(frameon=False, fontsize=7.2, loc="upper left")

    ax.set_title(title, loc="left", fontsize=8.8, fontweight="bold", color=p["ink"], pad=8)
    if source:
        fig.text(0.99, -0.01, f"Source: {source}", fontsize=6.8, color=p["muted"],
                 ha="right", style="italic")

    return _save_fig(fig, out)


def chart_pe_band_1y(palette, dates, values, mean, median, current, out, source=""):
    """Slide-5 Exhibit 12: P/E trailing band vs 1-year history."""
    return chart_history_band(
        palette, dates, values, mean, median, current, out,
        title="P/E Trailing Band vs 1-Year History (mean, median and current level)",
        ylabel="P/E (x)", source=source,
    )


def chart_pbv_band_1y(palette, dates, values, mean, median, current, out, source=""):
    """Slide-5 Exhibit 13: P/BV trailing band vs 1-year history."""
    return chart_history_band(
        palette, dates, values, mean, median, current, out,
        title="P/BV Trailing Band vs 1-Year History (mean, median and current level)",
        ylabel="P/BV (x)", source=source,
    )


__all__ = [
    "DEFAULT_PALETTE",
    "chart_vs_jci",
    "chart_segment_donut",
    "chart_kpi_bars",
    "chart_pbv_bands",
    "chart_wacc_breakdown",
    "chart_sensitivity_heatmap",
    "chart_scenario_bars",
    "chart_ev_equity_waterfall",
    "chart_index_trend",
    "chart_margin_trajectory",
    "chart_production_cost",
    "chart_fin_combo",
    "chart_revenue_combo",
    "chart_ebitda_combo",
    "chart_netprofit_combo",
    "chart_history_band",
    "chart_pe_band_1y",
    "chart_pbv_band_1y",
    "peer_pe_bar",
    "peer_evebitda_bar",
    "peer_pb_scatter",
    "relval_bars",
]



