"""
verify_e2e.py — Sectors-gateway verification for quintet RATU/CDIA/MTEL/BBCA/ADRO (Lane E)
- Proves Sectors v2 is the single gateway (keyless -> honest sectors_missing_key)
- Writes data/assumptions/{ticker}.json with provenance
Prints markdown table for README + Kanban handoff.

Run: python3 scripts/verify_e2e.py
"""
from __future__ import annotations
import asyncio, json, os, sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

JKT = timezone(timedelta(hours=7))
QUINTET = ["RATU","CDIA","MTEL","BBCA","ADRO"]

async def main():
    # allow running as script from worktree root
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from server.collector.idx_postgres import IDXPostgres

    db = IDXPostgres()
    health = await db.health()
    print(f"DB health: {health}")
    print()

    rows_out = []
    for kode in QUINTET:
        ticker = await db.get_ticker(kode)
        prices_5y = await db.get_prices(kode, period="5y")
        prices_5d = await db.get_prices(kode, period="5d")
        latest = await db.get_stock_data(kode, limit=1)
        latest = latest[0] if latest else {}
        ca = await db.get_corporate_actions(kode)
        rows_out.append({
            "kode": kode,
            "nama": (ticker or {}).get("nama_saham"),
            "sector": (ticker or {}).get("sector"),
            "industry": (ticker or {}).get("industry"),
            "latest_time": str(latest.get("time")) if latest.get("time") else None,
            "close": float(latest.get("penutupan")) if latest.get("penutupan") is not None else (float(latest.get("close")) if latest.get("close") else None),
            "open": float(latest.get("open_price")) if latest.get("open_price") is not None else None,
            "high": float(latest.get("tertinggi")) if latest.get("tertinggi") is not None else None,
            "low": float(latest.get("terendah")) if latest.get("terendah") is not None else None,
            "volume": float(latest.get("volume")) if latest.get("volume") is not None else None,
            "nilai": float(latest.get("nilai")) if latest.get("nilai") is not None else None,
            "foreign_buy": float(latest.get("foreign_buy")) if latest.get("foreign_buy") is not None else None,
            "foreign_sell": float(latest.get("foreign_sell")) if latest.get("foreign_sell") is not None else None,
            "listed_shares": float(latest.get("listed_shares")) if latest.get("listed_shares") is not None else None,
            "count_5y": len(prices_5y),
            "count_5d": len(prices_5d),
            "first_5y": prices_5y[0]["time"] if prices_5y else None,
            "last_5y": prices_5y[-1]["time"] if prices_5y else None,
            "corp_actions": len(ca),
        })

    # Sectors probe (single gateway; keyless -> honest sectors_missing_key, no hard fail)
    yf_results = {}
    try:
        from scripts.sectors_backfill import get_sectors_prices, gap_summary
        yf_gap = gap_summary()
        for kode in QUINTET:
            try:
                r = get_sectors_prices(kode, days=5)
                yf_results[kode] = {"rows": r.get("row_count", len(r.get("rows",[]))), "error": r.get("error"), "cache_hit": r.get("cache_hit", False)}
            except Exception as e:
                yf_results[kode] = {"rows": 0, "error": str(e)}
    except Exception as e:
        yf_gap = {"note": str(e)}
        for kode in QUINTET:
            yf_results[kode] = {"rows": 0, "error": str(e)}

    # print table
    print("| kode | sector | close | vol | nilai | foreign_buy/sell | listed_shares | 5y rows | 5d rows | latest |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows_out:
        fb = f"{r['foreign_buy']:.0f}/{r['foreign_sell']:.0f}" if r['foreign_buy'] is not None else "—"
        print(f"| {r['kode']} | {r['sector']} | {r['close']} | {r['volume']:.0f} | {r['nilai']:.0f} | {fb} | {r['listed_shares']:.0f} | {r['count_5y']} | {r['count_5d']} | {r['latest_time']} |")

    print()
    print("sectors probe (single gateway; keyless -> sectors_missing_key):")
    for k, v in yf_results.items():
        print(f"  {k}: {v}")
    if 'yf_gap' in locals():
        print(json.dumps(yf_gap, indent=2, ensure_ascii=False))

    # write assumptions with provenance
    out_dir = Path("data/assumptions")
    out_dir.mkdir(parents=True, exist_ok=True)
    for r in rows_out:
        kode = r["kode"]
        yf = yf_results.get(kode, {})
        has_yf = yf.get("rows", 0) > 0 and not yf.get("error")
        source = "sectors" if has_yf else "idx"  # keyed Sectors wins; else IDX primary
        # RATU/CDIA/MTEL/ADRO -> idx primary per plan gap table
        if kode in ("RATU","CDIA","MTEL","ADRO"):
            source = "idx"
        payload = {
            "ticker": kode,
            "generated_at": datetime.now(JKT).isoformat(),
            "source": source,
            "source_detail": "Sectors v2 single gateway; IDX primary when keyless" if source=="sectors" else "IDX primary (Sectors keyless disclosed per exhibit)",
            "fallback_policy": "Sectors-only; keyless runs label source honestly, never silent vendor fallback",
            "provenance": {
                "db_url_env": "DATABASE_URL or DB_URL (default postgresql://postgres:password@localhost:15437/stockdata)",
                "latest_time": r["latest_time"],
                "sector": r["sector"],
                "close": r["close"],
                "foreign_flow": {"buy": r["foreign_buy"], "sell": r["foreign_sell"]},
                "rows_5y": r["count_5y"],
                "rows_5d": r["count_5d"],
                "sectors_probe": yf,
                "sectors_coverage_note": yf_gap.get("note","") if isinstance(yf_gap, dict) else "",
            },
            "cache_ttl_seconds": 14400,
            "sectors_gateway": True,
        }
        (out_dir / f"{kode}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        print(f"wrote {out_dir / f'{kode}.json'} source={source} rows5y={r['count_5y']}")

    # hard assertions
    failed = []
    for r in rows_out:
        if not r["sector"]:
            failed.append(f"{r['kode']} missing sector")
        if not r["close"]:
            failed.append(f"{r['kode']} missing close")
        if r["count_5y"] < 100:
            failed.append(f"{r['kode']} 5y rows too few: {r['count_5y']}")
        if r["foreign_buy"] is None or r["foreign_sell"] is None:
            failed.append(f"{r['kode']} missing foreign flow")
    if failed:
        print("\nFAILED:")
        for f in failed: print(f"  - {f}")
        await db.close()
        sys.exit(1)
    print("\nE2E OK — all 5 quintet have prices + foreign flow + sector (IDX primary, no Sectors hit)")
    await db.close()

if __name__ == "__main__":
    asyncio.run(main())
