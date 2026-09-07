"""IDX brief scraper — Sectors-backed edition (rewritten Lane E, legacy removed).

Was: Yahoo global index/commodity quotes. Now: Sectors v2 universe feed
(top turnover + sector breadth) for the IDX section. Keyless -> honest
sectors_missing_key brief (loud, no fallback). fetch_data() name kept for CLI compat.
"""
from datetime import date, datetime, timedelta
import os


def fetch_data():
    report = f"IDX Institutional Brief - {datetime.now().strftime('%Y-%m-%d')}\n\n"

    try:
        from server.sectors import universe_close

        day = date.today()
        raw = None
        for _ in range(5):
            try:
                raw = universe_close(day.isoformat())
                break
            except Exception as e:
                if "SectorsNotConfigured" in type(e).__name__:
                    raise
                day -= timedelta(days=1)
        if raw is None:
            raise RuntimeError("universe feed unavailable")

        rows = raw.get("data") or raw.get("results") or []
        recs = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            kode = str(r.get("kode") or r.get("symbol") or r.get("ticker") or "").upper()
            if not kode:
                continue
            try:
                close = float(r.get("close") or r.get("closing_price") or 0)
                prev = float(r.get("prev") or r.get("previous_close") or close)
                vol = float(r.get("vol") or r.get("volume") or 0)
            except (TypeError, ValueError):
                continue
            pct = ((close - prev) / prev * 100) if prev else 0.0
            recs.append((kode, close, pct, vol, r.get("sector")))

        report += "--- TOP TURNOVER (Sectors universe) ---\n"
        recs.sort(key=lambda x: x[1] * x[3], reverse=True)
        for kode, close, pct, vol, _sec in recs[:15]:
            report += f"{kode:<15}: {close:>10.2f} {pct:>+7.2f}%\n"
        report += "\n"

        report += "--- SECTOR BREADTH ---\n"
        by_sec: dict[str, list[float]] = {}
        for _, _, pct, _, sec in recs:
            by_sec.setdefault(str(sec or "Unknown"), []).append(pct)
        for sec, pcts in sorted(by_sec.items(), key=lambda kv: sum(kv[1]) / len(kv[1]), reverse=True):
            avg = sum(pcts) / len(pcts)
            report += f"{sec[:15]:<15}: {avg:>+7.2f}% (n={len(pcts)})\n"
        report += "\nSOURCE: Sectors v2 universe feed\n"
    except Exception as e:
        report += f"--- INDICES ---\nSectors unavailable (source=sectors_missing_key): {e}\n"
    return report

if __name__ == "__main__":
    brief = fetch_data()
    print(brief)
    folder = "/home/fadil/Documents/vault/second brain/IDX Research/"
    file_path = os.path.join(folder, f"Morning_Brief_{datetime.now().strftime('%Y-%m-%d')}.md")
    if not os.path.exists(folder):
        os.makedirs(folder)
    with open(file_path, "w") as f:
        f.write(brief)
