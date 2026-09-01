import yfinance as yf
from datetime import datetime
import os

# Symbols mapping
symbols = {
    "Dow": "^DJI",
    "Nasdaq": "^IXIC",
    "S&P 500": "^GSPC",
    "FTSE": "^FTSE",
    "DAX": "^GDAXI",
    "CAC": "^FCHI",
    "Nikkei": "^N225",
    "HSI": "^HSI",
    "Shanghai": "000001.SS",
    "IDX": "^JKSE",
    "Oil (WTI)": "CL=F",
    "Oil (Brent)": "BZ=F",
    "Gold": "GC=F",
    "US 10Yr": "^TNX",
    "USD/IDR": "IDR=X",
    "DXY": "DX-Y.NYB"
}

def fetch_data():
    report = f"IDX Institutional Brief - {datetime.now().strftime('%Y-%m-%d')}\n\n"
    
    # Process market data grouped by section
    groups = {
        "INDICES": ["Dow", "Nasdaq", "S&P 500", "FTSE", "DAX", "CAC", "Nikkei", "HSI", "Shanghai", "IDX"],
        "COMMODITIES": ["Oil (WTI)", "Oil (Brent)", "Gold"],
        "MACRO & RATES": ["US 10Yr", "USD/IDR", "DXY"]
    }
    
    for group, group_symbols in groups.items():
        report += f"--- {group} ---\n"
        for name in group_symbols:
            ticker = symbols.get(name)
            if not ticker: continue
            try:
                # Need sufficient history to ensure we get latest
                data = yf.Ticker(ticker).history(period="5d")
                if len(data) >= 2:
                    curr = data.iloc[-1]['Close']
                    prev = data.iloc[-2]['Close']
                    change = curr - prev
                    pct = (change / prev) * 100
                    report += f"{name:<15}: {curr:>10.2f} {change:>+10.2f} {pct:>+7.2f}%\n"
            except Exception:
                report += f"{name:<15}: Error fetching\n"
        report += "\n"
            
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
