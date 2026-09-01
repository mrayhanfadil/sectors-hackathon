from playwright.sync_api import sync_playwright
import json, sys
from pathlib import Path

OUT = Path("/tmp/visual-qa")
OUT.mkdir(exist_ok=True)

routes = [
    ("/", "root", ["Institutional-Grade", "RATU", "MTEL", "BBCA", "ADRO", "BUKAN SARAN"]),
    ("/outlook", "outlook", ["9,100", "10,000", "7,800", "OW"]),
    ("/report/BBCA/", "bbca", ["7,890", "9,645", "+22", "BUY", "DCF"]),
    ("/report/MTEL/", "mtel", ["460", "613", "BUY", "DCF"]),
    ("/report/ADRO/", "adro", ["2,080", "3,875", "BUY", "ADRO"]),
    ("/report/BBCA/sentiment", "sentiment", ["BBCA", "Bullish", "Bearish", "sentiment is not advice"]),
    ("/report/BBCA/challenge", "challenge", ["Challenge", "WACC"]),
    ("/agent", "agent", ["Agent"]),
]

results = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    for path, name, must_contain in routes:
        page = context.new_page()
        url = f"https://sektoral-report.pages.dev{path}"
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: console_errors.append(f"PAGEERROR: {err.message}"))
        try:
            page.goto(url, wait_until="networkidle", timeout=20000)
            page.wait_for_timeout(1500)  # let TanStack Query populate
            text = page.locator("body").inner_text()
            found = [s for s in must_contain if s in text]
            missing = [s for s in must_contain if s not in text]
            screenshot_path = str(OUT / f"{name}.png")
            page.screenshot(path=screenshot_path, full_page=True)
            results.append({
                "name": name,
                "url": url,
                "title": page.title(),
                "text_len": len(text),
                "found": found,
                "missing": missing,
                "screenshot": screenshot_path,
                "console_errors": console_errors[:5],
                "pass": len(missing) == 0 and len(console_errors) == 0,
            })
        except Exception as e:
            results.append({
                "name": name,
                "url": url,
                "error": str(e)[:300],
                "pass": False,
            })
        finally:
            page.close()
    browser.close()

print(json.dumps(results, indent=2, default=str))

# Summary
total = len(results)
passed = sum(1 for r in results if r.get("pass"))
print(f"\n{'='*60}\n{passed}/{total} routes PASS visual QA")
sys.exit(0 if passed == total else 1)
