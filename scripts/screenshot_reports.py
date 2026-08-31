"""Screenshot each rendered report HTML for visual inspection (T10 QA).

Playwright headless chromium at A4-ish viewport; saves PNG next to the html dumps.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "output"


async def main() -> None:
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page(viewport={"width": 794, "height": 1123}, device_scale_factor=1.5)
        for html in sorted(OUT.glob("*.html")):
            await page.goto(html.resolve().as_uri())
            await page.wait_for_timeout(700)
            png = html.with_suffix(".png")
            await page.screenshot(path=str(png), full_page=True)
            print(f"shot {png.name}")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
