"""Harvest the two market series the cover needs but Sectors does not expose.

Sectors caps its daily endpoint at 90 days, so the cover's 1-2 year relative chart and the
USD/IDR leg of the dual-currency rows have to come from yfinance. The server must not import
yfinance (tests/test_prod_fixture_isolation.py::test_no_yfinance_imports_under_server - the
production render path stays offline and deterministic), so this script does the network work
and the renderer reads the artifact it writes.

    .venv/bin/python scripts/build_cover_market.py AMMN [--months 24] [--refresh-fx]

Writes:
    output/cache/cover_market/<TICKER>.json   labels / price / index / rel_pct + provenance
    output/cache/fx_usdidr.json               rate + as-of date + source

Nothing is written when a fetch fails: the renderer then shows an honest "n/a" instead of a
stale or synthetic series (LOUD policy).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "output" / "cache" / "cover_market"
FX_PATH = REPO_ROOT / "output" / "cache" / "fx_usdidr.json"


def fetch_fx() -> dict | None:
    try:
        import yfinance as yf

        h = yf.Ticker("IDR=X").history(period="5d")
        if h.empty:
            return None
        return {
            "rate": round(float(h["Close"].iloc[-1]), 0),
            "date": str(h.index[-1].date()),
            "source": "yfinance IDR=X (close)",
        }
    except Exception as e:  # network down / symbol missing
        print(f"fx: FAILED ({e})")
        return None


def fetch_vs_index(ticker: str, months: int = 24) -> dict | None:
    try:
        import yfinance as yf

        sym = f"{ticker.upper()}.JK"
        df = yf.download([sym, "^JKSE"], period="2y", interval="1mo",
                         progress=False, auto_adjust=False)
        if df is None or df.empty:
            return None
        close = df["Close"].dropna(how="all").dropna()
        if len(close) < 6:
            return None
        if months and len(close) > months:
            close = close.tail(months)
        px = [float(v) for v in close[sym].tolist()]
        ix = [float(v) for v in close["^JKSE"].tolist()]
        rel = [round((px[i] / px[0] - 1.0) * 100.0 - (ix[i] / ix[0] - 1.0) * 100.0, 2)
               for i in range(len(px))]
        labels = [d.strftime("%b-%y") for d in close.index]
        return {
            "ticker": ticker.upper(),
            "labels": labels,
            "price": [round(p, 1) for p in px],
            "index": [round(i, 1) for i in ix],
            "rel_pct": rel,
            "window": f"{labels[0]}–{labels[-1]}",
            "months": len(labels),
            "abs_chg_pct": round((px[-1] / px[0] - 1.0) * 100.0, 2),
            "idx_chg_pct": round((ix[-1] / ix[0] - 1.0) * 100.0, 2),
            "source": f"yfinance {sym} vs ^JKSE, monthly closes, rebased",
        }
    except Exception as e:
        print(f"vs_index: FAILED ({e})")
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker")
    ap.add_argument("--months", type=int, default=24)
    ap.add_argument("--refresh-fx", action="store_true")
    a = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rc = 0

    if a.refresh_fx or not FX_PATH.exists():
        fx = fetch_fx()
        if fx:
            FX_PATH.write_text(json.dumps(fx, indent=1), encoding="utf-8")
            print(f"fx: {fx['rate']} ({fx['date']}) -> {FX_PATH.relative_to(REPO_ROOT)}")
        else:
            rc = 1
    else:
        print(f"fx: cache kept ({json.loads(FX_PATH.read_text())['rate']}) - use --refresh-fx")

    series = fetch_vs_index(a.ticker, a.months)
    if series:
        p = OUT_DIR / f"{a.ticker.upper()}.json"
        p.write_text(json.dumps(series, indent=1), encoding="utf-8")
        print(f"vs_index: {series['months']} bulan {series['window']} "
              f"({series['abs_chg_pct']:+.2f}% vs IHSG {series['idx_chg_pct']:+.2f}%) "
              f"-> {p.relative_to(REPO_ROOT)}")
    else:
        rc = 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
