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
}
sys.path.insert(0, str(HERE))

def generate_charts(ticker: str, data: dict, palette: dict) -> Path:
    """Call Lane 1's chart engine. Wrap each in try/except."""
    try:
        from report_charts import (chart_vs_jci, chart_segment_donut, chart_kpi_bars,
                                   chart_pbv_bands, chart_wacc_breakdown, chart_sensitivity_heatmap,
                                   chart_scenario_bars, chart_ev_equity_waterfall, chart_index_trend)
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
                         vs_jci.get("source", "IDX, yfinance"), cache / "vs_jci.png")
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
                              sc.get("source", "IDX, yfinance"), cache / "index_trend.png")
        except Exception as e:
            print(f"[warn] idx_trend: {e}")
    if CACHE_ROOT != Path("/tmp"):
        tmp_cache = Path(f"/tmp/render_{ticker.lower()}/charts")
        try:
            tmp_cache.mkdir(parents=True, exist_ok=True)
            for f in cache.glob("*.png"):
                shutil.copy2(f, tmp_cache / f.name)
        except Exception:
            pass
    return cache

def compile_typst(input_typ: Path, output_pdf: Path, font_path: Path = FONTS, ticker: str | None = None) -> bool:
    """Compile via Python `typst` lib or fallback to CLI binary."""
    try:
        import typst as _t
        _t.compile(str(input_typ), output=str(output_pdf))
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
    # Per-ticker template override: templates/typst/archetypes/POWR_infra.typ
    ticker_specific = TEMPLATES / "archetypes" / f"{ticker.lower()}_{template_name}.typ"
    if ticker_specific.exists():
        template_file = ticker_specific
    else:
        template_file = TEMPLATES / "archetypes" / TEMPLATE_FILES.get(template_name, "report_single.typ")
    if not template_file.exists():
        raise FileNotFoundError(f"template {template_file} not built yet")
    if not compile_typst(template_file, out_pdf, ticker=ticker):
        raise RuntimeError(f"typst compile failed for {ticker}")
    try:
        return out_pdf.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return str(out_pdf)

def main() -> None:
    ap = argparse.ArgumentParser(description="Typst institutional PDF renderer")
    ap.add_argument("report_data", nargs="?", help="path to report_data.json")
    ap.add_argument("--out", help="output pdf path")
    ap.add_argument("--all", action="store_true", help="render all fixtures")
    ap.add_argument("--renderer", default="typst", choices=["typst", "chromium"])
    args = ap.parse_args()
    if args.renderer == "chromium":
        sys.argv = ["render_pdf_chromium.py"] + ([args.report_data] if args.report_data else []) + (["--out", args.out] if args.out else []) + (["--all"] if args.all else [])
        from render_pdf_chromium import main as legacy_main
        legacy_main()
        return
    if args.all:
        from report_fixtures import ALL
        for name, fn in ALL.items():
            try:
                data = fn()
                data_path = CACHE_ROOT / f"render_{name.lower()}" / "report_data.json"
                data_path.parent.mkdir(parents=True, exist_ok=True)
                data_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                out_pdf = PROJECT / "output" / f"{name.lower()}_report_typst.pdf"
                render(data_path, out_pdf)
                print(f"[OK] {name} -> {out_pdf}")
            except Exception as exc:
                print(f"[FAIL] {name}: {exc}")
        return
    if not args.report_data:
        ap.print_help()
        sys.exit(2)
    out_pdf = Path(args.out) if args.out else Path(args.report_data).with_suffix(".pdf")
    render(Path(args.report_data), out_pdf)
    print(f"rendered {out_pdf}")

if __name__ == "__main__":
    main()
