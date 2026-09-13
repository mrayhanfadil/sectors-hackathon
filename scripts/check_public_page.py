"""Open the public report page in a real browser and report what a visitor actually gets.

Console errors and the API calls the page makes are the two things a screenshot cannot tell you, and they are exactly
what "blank screen" incidents hide behind.
"""
import asyncio
import json
import sys

from playwright.async_api import async_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://feat-institutional-report.sektoral-report.pages.dev/report/AMMN"


async def main() -> int:
    console, calls = [], []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--no-sandbox"])
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("console", lambda m: console.append(f"{m.type}: {m.text[:120]}") if m.type in ("error", "warning") else None)
        page.on("response", lambda r: calls.append((r.status, r.url.split("/api/")[-1][:70])) if "/api/" in r.url else None)

        await page.goto(URL, wait_until="networkidle", timeout=90_000)
        await page.wait_for_timeout(4000)

        report = await page.evaluate("""() => {
            const t = document.body.innerText || '';
            return {
              text_len: t.length,
              has_ticker: t.includes('AMMN'),
              sections: document.querySelectorAll('section,article').length,
              svgs: document.querySelectorAll('svg').length,
              tables: document.querySelectorAll('table').length,
              honest_pending: (t.match(/Belum Tersedia|Belum Terverifikasi/g) || []).length,
              title: document.title,
              head: t.slice(0, 180).replace(/\\s+/g, ' ')
            };
        }""")
        await browser.close()

    print(json.dumps({**report, "api_calls": calls[:10], "console": console[:6]}, indent=1, ensure_ascii=False))
    empty = report["text_len"] < 500
    print("VERDICT:", "BLANK/SHORT — not a usable page" if empty else "renders with content")
    return 1 if empty else 0


raise SystemExit(asyncio.run(main()))
