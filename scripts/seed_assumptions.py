import json, os
from pathlib import Path
from datetime import datetime, timezone, timedelta
JKT = timezone(timedelta(hours=7))
OUT_DIR = Path("data/assumptions")
TICKERS = ["RATU","CDIA","MTEL","BBCA","ADRO"]
# placeholders — will be overwritten by verify script with real IDX vs yfinance provenance
for t in TICKERS:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    p = OUT_DIR / f"{t}.json"
    if not p.exists():
        p.write_text(json.dumps({
            "ticker": t,
            "generated_at": datetime.now(JKT).isoformat(),
            "source": "idx",  # idx|yfinance — BBCA may be yfinance-complete, small caps idx
            "posture": "IDX primary (stockdata:15437) + yfinance .JK fallback — cache 4h, disclosed per exhibit",
            "fallback_policy": "yfinance gap for small caps → IDX + label estimated",
            "wacc": None, "beta": None, "risk_free": None, "erp": None, "growth": None,
            "note": "placeholder — verify_e2e.py will fill with IDX live provenance + yfinance gap table"
        }, indent=2, ensure_ascii=False))
print(f"seeded {len(TICKERS)} assumption stubs in {OUT_DIR}")
