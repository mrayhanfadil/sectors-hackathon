import sqlite3, json, random, hashlib
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Synthetic fallback for P0-P1 when Postgres or yfinance is unavailable.
# Seed=42 deterministic. Covers peers, JCI, segments, KPI synthetic.
# Per plan §4: SQLite sectors.db + peers.json dual + assumptions/{ticker}.json

SEED = 42
JKT = timezone(timedelta(hours=7))
DB_PATH = Path("data/sectors.db")
PEERS_PATH = Path("data/peers.json")

# Quintet + universe peers (49 tickers synthetic)
QUINTET = ["RATU","CDIA","MTEL","BBCA","ADRO"]
UNIVERSE = [
  "BBCA","BBRI","BMRI","BBNI","BRIS","ARTO","BNGA","PNBN",
  "TLKM","ISAT","EXCL","MTEL","TOWR","TBIG",
  "ADRO","PTBA","ITMG","UNTR","HRUM","BYAN","ADMR","ANTM","INCO","MDKA","NCKL",
  "ASII","UNVR","ICBP","INDF","KLBF","SIDO","CPIN","JPFA","MYOR",
  "RATU","CDIA","GOTO","BUKA","EMTK","SCMA","MAPI","ACES","PWON","CTRA","SMGR","INTP","PGAS","AKRA","MEDC"
]

SECTORS = ["Energy","Financials","Infrastructures","Technology","Consumer Non-Cyclicals","Consumer Cyclicals","Healthcare","Industrials","Basic Materials","Properties & Real Estate","Transportation & Logistic"]

def gen():
    rng = random.Random(SEED)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS synthetic_prices")
    cur.execute("DROP TABLE IF EXISTS synthetic_tickers")
    cur.execute("DROP TABLE IF EXISTS synthetic_peers")
    cur.execute("""CREATE TABLE synthetic_prices (
        kode_saham TEXT, time TEXT, open REAL, high REAL, low REAL, close REAL, volume REAL, source TEXT
    )""")
    cur.execute("""CREATE TABLE synthetic_tickers (
        kode_saham TEXT PRIMARY KEY, nama_saham TEXT, sector TEXT, industry TEXT, source TEXT
    )""")
    cur.execute("""CREATE TABLE sector_kpi (
        kode_saham TEXT, metric TEXT, value REAL, period TEXT, source TEXT
    )""")
    # tickers
    sector_map = {
        "RATU":"Energy","CDIA":"Infrastructures","MTEL":"Infrastructures","BBCA":"Financials","ADRO":"Energy",
        "BBRI":"Financials","BMRI":"Financials","TLKM":"Infrastructures","TOWR":"Infrastructures",
        "ADMR":"Energy","ANTM":"Basic Materials","ASII":"Industrials","UNVR":"Consumer Non-Cyclicals"
    }
    tickers = []
    for kode in UNIVERSE:
        sector = sector_map.get(kode, rng.choice(SECTORS))
        tickers.append((kode, f"{kode} Synthetic Tbk.", sector, sector, "synthetic"))
    cur.executemany("INSERT INTO synthetic_tickers VALUES (?,?,?,?,?)", tickers)

    # prices: 5y daily synthetic (business days) with deterministic walk
    start = datetime(2021, 1, 4, tzinfo=JKT).date()
    end = datetime(2026, 8, 26, tzinfo=JKT).date()
    dates = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            dates.append(d)
        d += timedelta(days=1)
    base_price = {"RATU":1150,"CDIA":600,"MTEL":600,"BBCA":8000,"ADRO":2500}
    for kode in UNIVERSE:
        price = base_price.get(kode, rng.uniform(500, 8000))
        rows = []
        for dt in dates:
            drift = rng.gauss(0.0003, 0.018)
            price = max(50, price * (1 + drift))
            high = price * (1 + abs(rng.gauss(0, 0.01)))
            low = price * (1 - abs(rng.gauss(0, 0.01)))
            open_p = price * (1 + rng.gauss(0, 0.005))
            vol = int(rng.uniform(5_000_000, 150_000_000))
            rows.append((kode, dt.isoformat(), round(open_p,0), round(high,0), round(low,0), round(price,0), vol, "synthetic"))
        cur.executemany("INSERT INTO synthetic_prices VALUES (?,?,?,?,?,?,?,?)", rows)

    # KPI synthetic (MTEL tenancy etc)
    kpis = [
        ("MTEL","towers", 40563, "2026H1", "synthetic"),
        ("MTEL","tenancy_ratio", 1.57, "2026H1", "synthetic"),
        ("MTEL","fiber_km", 59239, "2026H1", "synthetic"),
        ("RATU","bopd", 169000, "2026H1", "synthetic"),
        ("CDIA","power_MW", 120, "2026H1", "synthetic"),
    ]
    cur.executemany("INSERT INTO sector_kpi VALUES (?,?,?,?,?)", kpis)
    conn.commit()

    # peers.json dual mode
    peers = {
        "generated_at": datetime.now(JKT).isoformat(),
        "seed": SEED,
        "source": "synthetic",
        "note": "P0-P1 synthetic fallback seed=42; P2 will swap to IDX+yfinance+Sectors",
        "universe": UNIVERSE,
        "by_ticker": {
            "RATU": {"peers": ["MEDC","AKRA","PGAS"], "sector":"Energy"},
            "CDIA": {"peers": ["POWR","Sembcorp","Westports","HATM"], "sector":"Infrastructures", "sotp_pillars":["Energy","Water","Port","Logistics"]},
            "MTEL": {"peers": ["TOWR","TBIG","ISAT"], "sector":"Infrastructures", "kpi":["towers","tenancy_ratio","fiber_km"]},
            "BBCA": {"peers": ["BBRI","BMRI","BBNI","BRIS"], "sector":"Financials"},
            "ADRO": {"peers": ["PTBA","ITMG","UNTR","HRUM"], "sector":"Energy"},
        }
    }
    PEERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PEERS_PATH.write_text(json.dumps(peers, indent=2, ensure_ascii=False))
    conn.close()
    print(f"seeded {DB_PATH} + {PEERS_PATH}")

if __name__ == "__main__":
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    gen()
