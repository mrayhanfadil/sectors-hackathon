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
"""

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

plt.rcParams["font.sans-serif"] = ["IBM Plex Sans", "Liberation Sans", "DejaVu Sans"]
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

    ax.set_title(f"{ticker} vs IHSG (YTD %)", loc="left", fontsize=8.8, fontweight="bold", color=p["ink"], pad=8)
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
        clean_num_str = v_str.replace("%", "").replace(",", "").strip()
        try:
            val_num = float(clean_num_str)
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
]


