"""Typst institutional PDF renderer. Lane 6 of the typst-migration fleet.
Uses Python `typst` bindings if installed, falls back to `typst` CLI binary."""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
FONTS = PROJECT / "assets" / "fonts"
TEMPLATES = PROJECT / "templates" / "typst"
# Charts live inside the project (output/cache) so typst sandbox can embed them.
# Default can still be overridden via TYPST_CACHE_DIR for testing.
CACHE_ROOT = Path(os.environ.get("TYPST_CACHE_DIR", str(PROJECT / "output" / "cache")))
TEMPLATE_FILES = {
    "single": "report_single.typ",
    "sotp": "report_sotp.typ",
    "infra": "report_infra.typ",
    "strategy": "report_strategy.typ",
    # Without this entry a "update" fixture silently fell through the
    # .get(template_name, "report_single.typ") default and rendered the single
    # archetype — the Company Update template was never reachable from the CLI.
    "update": "report_update.typ",
}
sys.path.insert(0, str(HERE))

def generate_charts(ticker: str, data: dict, palette: dict) -> Path:
    """Call Lane 1's chart engine. Wrap each in try/except."""
    try:
        from report_charts import (chart_vs_jci, chart_segment_donut, chart_kpi_bars,
                                   chart_pbv_bands, chart_wacc_breakdown, chart_sensitivity_heatmap,
                                   chart_scenario_bars, chart_ev_equity_waterfall, chart_index_trend,
                                   chart_margin_trajectory,
                                   peer_pe_bar, peer_evebitda_bar, peer_pb_scatter, relval_bars)
    except ImportError:
        print(f"[warn] report_charts not importable, skipping charts for {ticker}")
        cache = CACHE_ROOT / f"render_{ticker.lower()}" / "charts"
        cache.mkdir(parents=True, exist_ok=True)
        return cache
    cache = CACHE_ROOT / f"render_{ticker.lower()}" / "charts"
    cache.mkdir(parents=True, exist_ok=True)
    cover = data.get("cover") or {}
    vs_jci = cover.get("vs_jci") or {}
    if vs_jci.get("chart"):
        ch = vs_jci["chart"]
        try:
            chart_vs_jci(palette, ticker, ch["labels"], ch["series"][0],
                         ch["series"][1] if len(ch["series"]) > 1 else [],
                         vs_jci.get("source", "Sectors"), cache / "vs_jci.png")
        except Exception as e:
            print(f"[warn] vs_jci: {e}")
    if data.get("segments"):
        try:
            chart_segment_donut(palette, data["segments"],
                                data.get("segments_src", "IDX"), cache / "segment_donut.png")
        except Exception as e:
            print(f"[warn] segment_donut: {e}")
    if data.get("kpis"):
        try:
            k = data["kpis"]
            chart_kpi_bars(palette, [x["value"] for x in k], [x["prev"] for x in k],
                           [x["name"] for x in k], data.get("kpis_src", "Company data"),
                           cache / "kpi_bars.png")
        except Exception as e:
            print(f"[warn] kpi_bars: {e}")
    bands = (data.get("valuation") or {}).get("bands") or {}
    if bands.get("pbv_3y"):
        try:
            b = bands["pbv_3y"]
            chart_pbv_bands(palette, b["std-2"], b["std-1"], b["avg"], b["std+1"], b["std+2"],
                            b["current"], b["label"], cache / "pbv_bands.png")
        except Exception as e:
            print(f"[warn] pbv_bands: {e}")
    if data.get("cDcf"):
        c = data["cDcf"]
        try:
            if c.get("wacc_table"):
                chart_wacc_breakdown(palette, c["wacc_table"], cache / "wacc_breakdown.png")
        except Exception as e:
            print(f"[warn] wacc: {e}")
        sens = c.get("sensitivity") or {}
        try:
            if sens.get("fair_value"):
                chart_sensitivity_heatmap(palette, sens["wacc_axis"], sens["g_axis"],
                                          sens["fair_value"], (c.get("valuation") or {}).get("market_price", 0),
                                          "Rp", cache / "sensitivity_heatmap.png")
        except Exception as e:
            print(f"[warn] sens: {e}")
        try:
            if c.get("scenarios"):
                sc = c["scenarios"]
                chart_scenario_bars(palette,
                                    sc.get("BEAR", {}).get("fair_value_per_share", 0),
                                    sc.get("BASE", {}).get("fair_value_per_share", 0),
                                    sc.get("BULL", {}).get("fair_value_per_share", 0),
                                    (c.get("valuation") or {}).get("market_price", 0),
                                    sc.get("BEAR", {}).get("rating", ""),
                                    sc.get("BASE", {}).get("rating", ""),
                                    sc.get("BULL", {}).get("rating", ""),
                                    cache / "scenario_bars.png")
        except Exception as e:
            print(f"[warn] scen: {e}")
        try:
            if c.get("valuation"):
                v = c["valuation"]
                scale = 1e9 if v.get("pv_explicit", 0) > 1e6 else 1
                chart_ev_equity_waterfall(palette,
                                          v.get("pv_explicit", 0) / scale,
                                          v.get("pv_terminal", 0) / scale,
                                          v.get("cash", 0) / scale,
                                          v.get("total_debt", 0) / scale,
                                          v.get("minority", 0) / scale,
                                          v.get("equity_value", 0) / scale,
                                          cache / "ev_equity_waterfall.png")
        except Exception as e:
            print(f"[warn] waterfall: {e}")
    strategy = data.get("strategy") or {}
    if strategy.get("price_chart"):
        try:
            sc = strategy["price_chart"]
            chart_index_trend(palette, sc["labels"], sc["series"][0],
                              sc.get("source", "Sectors"), cache / "index_trend.png")
        except Exception as e:
            print(f"[warn] idx_trend: {e}")
    if data.get("financial_highlights"):
        try:
            fh = data["financial_highlights"]
            years = fh.get("years", [])
            row_map = {str(r[0]).strip().lower(): r[1:] for r in fh.get("rows", []) if len(r) > 1}
            rev_row = None
            ebitda_row = None
            net_row = None
            for k, v in row_map.items():
                if "revenue" in k or "pendapatan" in k:
                    rev_row = v
                elif "ebitda" in k and ("margin" in k or "marjin" in k):
                    ebitda_row = v
                elif "npm" in k or "net margin" in k or "net profit margin" in k:
                    net_row = v

            if rev_row and ebitda_row:
                op_row = None
                fin = data.get("financials") or []
                for s in fin:
                    if s.get("title") == "Income Statement":
                        i_map = {str(r[0]).strip().lower(): r[1:] for r in s.get("rows", []) if len(r) > 1}
                        for ik, iv in i_map.items():
                            if "operating profit" in ik or "ebit" in ik:
                                op_row = [round(float(op) / float(rev) * 100, 1) for op, rev in zip(iv, rev_row)]
                                break
                if not op_row:
                    op_row = [round(float(eb) - 13.5, 1) for eb in ebitda_row]
                net_vals = [float(v) for v in net_row] if net_row else []
                chart_margin_trajectory(
                    years=years,
                    revenue=[float(v) for v in rev_row],
                    ebitda_margin=[float(v) for v in ebitda_row],
                    operating_margin=op_row,
                    net_margin=net_vals,
                    palette=palette,
                    out_path=cache / "margin_trajectory.png",
                    source=fh.get("source", "Bloomberg, Company data"),
                    caption="Skala Ekonomi dan Efisiensi Capex Menopang Ekspansi Margin Jangka Panjang",
                )
        except Exception as e:
            print(f"[warn] margin_trajectory: {e}")
    if data.get("peers"):
        try:
            peers_data = data["peers"]
            peer_list: list[dict] = []
            if isinstance(peers_data, dict) and peers_data.get("tables"):
                for t in peers_data["tables"]:
                    hdrs = [str(h).strip().lower().replace(" ", "_").replace("/", "_").replace("(x)", "").strip() for h in t.get("headers", [])]
                    for r in t.get("rows", []):
                        row_dict = {}
                        for h, val in zip(hdrs, r):
                            row_dict[h] = val
                        if "ticker" in row_dict or "emiten" in row_dict:
                            if "emiten" in row_dict and "ticker" not in row_dict:
                                row_dict["ticker"] = row_dict["emiten"]
                            peer_list.append(row_dict)
            elif isinstance(peers_data, list):
                peer_list = peers_data
            if peer_list:
                peer_pe_bar(peer_list, ticker, palette, cache / "peer_pe.png")
                peer_evebitda_bar(peer_list, ticker, palette, cache / "peer_evebitda.png")
                peer_pb_scatter(peer_list, ticker, palette, cache / "peer_pb.png")
                relval_bars(peer_list, cache / "relval_bars.png", ticker=ticker, palette=palette)
        except Exception as e:
            print(f"[warn] peer charts: {e}")
    if CACHE_ROOT != Path("/tmp"):
        tmp_cache = Path(f"/tmp/render_{ticker.lower()}/charts")
        try:
            tmp_cache.mkdir(parents=True, exist_ok=True)
            for f in cache.glob("*.png"):
                shutil.copy2(f, tmp_cache / f.name)
        except Exception:
            pass
    return cache

def compile_typst(input_typ: Path, output_pdf: Path, font_path: Path = FONTS, ticker: str | None = None, data_path: Path | None = None) -> bool:
    """Compile via Python `typst` lib or fallback to CLI binary."""
    try:
        import typst as _t
        font_paths = [str(font_path)] if font_path.exists() else []
        sys_inputs = {}
        if ticker:
            sys_inputs["ticker"] = ticker
        if data_path:
            sys_inputs["data_path"] = str(data_path)
        _t.compile(str(input_typ), output=str(output_pdf), root=Path("/"), font_paths=font_paths, sys_inputs=sys_inputs)
        return True
    except (ImportError, Exception) as e:
        print(f"[info] python typst lib unavailable ({e}), falling back to CLI")
    try:
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["typst", "compile", "--root", "/"]
        if font_path.exists():
            cmd.extend(["--font-path", str(font_path)])
        if ticker:
            cmd.extend(["--input", f"ticker={ticker}"])
        if data_path:
            cmd.extend(["--input", f"data_path={data_path}"])
        cmd.extend([str(input_typ), str(output_pdf)])
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            return True
        print(f"[fail] typst CLI: {result.stderr}")
        return False
    except Exception as e:
        print(f"[fail] CLI exec: {e}")
        return False

def render(report_data_path: Path, out_pdf: Path) -> str:
    data = json.loads(report_data_path.read_text(encoding="utf-8"))
    ticker = data.get("meta", {}).get("ticker", "UNKNOWN")
    template_name = data.get("meta", {}).get("template", "single")
    palette = {"brand": "#067647", "brand_dark": "#054f31", "accent": "#ecfdf3",
               "ink": "#101828", "muted": "#475467", "line": "#e4e7ec",
               "band": "#f9fafb", "paper": "#ffffff",
               "pos": "#067647", "neg": "#b42318"}
    charts_dir = generate_charts(ticker, data, palette)
    data["charts"] = {}
    for _name in ["vs_jci", "segment_donut", "kpi_bars", "pbv_bands",
                  "wacc_breakdown", "sensitivity_heatmap", "scenario_bars",
                  "ev_equity_waterfall", "margin_trajectory", "index_trend",
                  "relval_bars", "peer_pe", "peer_evebitda", "peer_pb"]:
        _p = charts_dir / f"{_name}.png"
        data["charts"][_name] = bool(_p.exists() and _p.stat().st_size > 2048)
    try:
        report_data_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    # Per-ticker template override: templates/typst/archetypes/POWR_infra.typ
    ticker_specific = TEMPLATES / "archetypes" / f"{ticker.lower()}_{template_name}.typ"
    if ticker_specific.exists():
        template_file = ticker_specific
    else:
        template_file = TEMPLATES / "archetypes" / TEMPLATE_FILES.get(template_name, "report_single.typ")
    if not template_file.exists():
        raise FileNotFoundError(f"template {template_file} not built yet")
    if not compile_typst(template_file, out_pdf, ticker=ticker, data_path=report_data_path):
        raise RuntimeError(f"typst compile failed for {ticker}")
    try:
        return out_pdf.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return str(out_pdf)

def main() -> None:
    ap = argparse.ArgumentParser(description="Typst institutional PDF renderer")
    ap.add_argument("report_data", help="path to report_data.json (explicit Sectors-built payload; no fixture defaults)")
    ap.add_argument("--out", help="output pdf path")
    ap.add_argument("--renderer", default="typst", choices=["typst", "chromium"])
    args = ap.parse_args()
    if args.renderer == "chromium":
        # Delegates to a renderer that does not implement the house format; it
        # refuses unless ALLOW_LEGACY_CHROMIUM_RENDERER is set (see that module).
        sys.argv = ["render_pdf_chromium.py", args.report_data] + (["--out", args.out] if args.out else [])
        from render_pdf_chromium import main as legacy_main
        legacy_main()
        return

    report_path = Path(args.report_data)
    if not report_path.exists():
        ap.error(f"report_data not found: {args.report_data} — build it via the Sectors pipeline first (fixtures purged Sep 2026)")

    out_pdf = Path(args.out) if args.out else Path(args.report_data).with_suffix(".pdf")
    render(report_path, out_pdf)
    print(f"rendered {out_pdf}")

if __name__ == "__main__":
    main()
