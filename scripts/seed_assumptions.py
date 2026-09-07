import json, os
from pathlib import Path
from datetime import datetime, timezone, timedelta
JKT = timezone(timedelta(hours=7))
OUT_DIR = Path("data/assumptions")
TICKERS = ["RATU","CDIA","MTEL","BBCA","ADRO"]
# placeholders — Sectors v2 is the single gateway (keyless -> sectors_missing_key, no fallback)
for t in TICKERS:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    p = OUT_DIR / f"{t}.json"
    if not p.exists():
        p.write_text(json.dumps({
            "ticker": t,
            "generated_at": datetime.now(JKT).isoformat(),
            "source": "sectors",  # sectors|assumptions — Sectors v2 single gateway
            "posture": "Sectors v2 single gateway — cache 4h, disclosed per exhibit",
            "fallback_policy": "no fallback — keyless returns honest sectors_missing_key",
            "wacc": None, "beta": None, "risk_free": None, "erp": None, "growth": None,
            "note": "placeholder — exhibits disclose Sectors source per exhibit"
        }, indent=2, ensure_ascii=False))
print(f"seeded {len(TICKERS)} assumption stubs in {OUT_DIR}")
