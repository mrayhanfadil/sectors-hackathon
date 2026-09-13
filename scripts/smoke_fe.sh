#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# FE Before/After Smoke Harness
# ==============================================================================
# 1. Builds Vite FE into a scratch directory: src/fe/dist-smoke
# 2. Serves dist-smoke with SPA fallback on an ephemeral free port
# 3. Headless browser visits each route:
#    - /
#    - /report/AMMN
#    - /report/AMMN/sentiment
#    - /report/AMMN/challenge
#    - /agent
#    - /mock-sectors/AMMN
# 4. Captures screenshots & visible text into docs/audits/fe-smoke/<route>.{png,txt}
# 5. Evaluates anti-fabrication signals (lorem/dummy/example) and counts numeric tokens
# 6. Detects API state (live / offline / not-covered (HTTP 422))
# 7. Outputs PASS/FAIL table and exits non-zero if empty or threw
# ==============================================================================

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FE_DIR="$REPO_ROOT/src/fe"
OUT_DIR="$FE_DIR/dist-smoke"
AUDIT_DIR="$REPO_ROOT/docs/audits/fe-smoke"
PYTHON_BIN="$REPO_ROOT/.venv/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
    PYTHON_BIN="$(which python3)"
fi

echo "=== [1/4] Building FE scratch dist (dist-smoke) ==="
mkdir -p "$AUDIT_DIR"
(
    cd "$FE_DIR"
    npx vite build --outDir dist-smoke
)

# Deep links fallback assurance: copy index.html to 404.html
cp "$OUT_DIR/index.html" "$OUT_DIR/404.html"

echo "=== [2/4] Finding free port and serving dist-smoke with SPA fallback ==="
FREE_PORT=$("$PYTHON_BIN" -c "import socket; s = socket.socket(); s.bind(('', 0)); print(s.getsockname()[1]); s.close()")
echo "Serving dist-smoke on http://localhost:$FREE_PORT (SPA fallback enabled)..."

npx serve -s "$OUT_DIR" -l "$FREE_PORT" >/dev/null 2>&1 &
SERVER_PID=$!

cleanup() {
    echo "Stopping test server (PID: $SERVER_PID)..."
    kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Wait for server readiness
SERVER_READY=0
for i in $(seq 1 30); do
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$FREE_PORT/" | grep -q "200"; then
        SERVER_READY=1
        break
    fi
    sleep 0.2
done

if [[ "$SERVER_READY" -ne 1 ]]; then
    echo "Error: Server failed to start on port $FREE_PORT within 6 seconds."
    exit 1
fi
echo "Server is ready on http://localhost:$FREE_PORT."

echo "=== [3/4] Running Headless Smoke Tests with Playwright ==="
"$PYTHON_BIN" - <<PYEOF
import asyncio
import os
import re
import sys
import time
from playwright.async_api import async_playwright

AUDIT_DIR = "${AUDIT_DIR}"
PORT = "${FREE_PORT}"
BASE_URL = f"http://localhost:{PORT}"

ROUTES = [
    {"path": "/", "slug": "root", "is_report": False},
    {"path": "/report/AMMN", "slug": "report-AMMN", "is_report": True},
    {"path": "/report/AMMN/sentiment", "slug": "report-AMMN-sentiment", "is_report": False},
    {"path": "/report/AMMN/challenge", "slug": "report-AMMN-challenge", "is_report": False},
    {"path": "/agent", "slug": "agent", "is_report": False},
    {"path": "/mock-sectors/AMMN", "slug": "mock-sectors-AMMN", "is_report": False},
]

FABRICATION_REGEX = re.compile(r"\b(lorem|dummy|example)\b", re.IGNORECASE)
NUMERIC_REGEX = re.compile(r"\d+(?:[.,]\d+)*")

async def run_smoke():
    results = []
    has_failure = False

    async with async_playwright() as p:
        browser_type = p.chromium
        engine_name = "Playwright Bundled Chromium"
        try:
            browser = await browser_type.launch(headless=True)
        except Exception as e:
            print(f"[WARN] Failed to launch default chromium: {e}")
            print("[INFO] Falling back to system /usr/bin/google-chrome...")
            browser = await browser_type.launch(executable_path="/usr/bin/google-chrome", headless=True)
            engine_name = "System Google Chrome (/usr/bin/google-chrome)"

        browser_version = browser.version
        print(f"Browser Engine: {engine_name} (version {browser_version})")

        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            device_scale_factor=1,
        )

        for item in ROUTES:
            path = item["path"]
            slug = item["slug"]
            is_report = item["is_report"]

            page = await context.new_page()
            console_errors = []
            page_errors = []
            api_statuses = []

            page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type in ["error"] else None)
            page.on("pageerror", lambda err: page_errors.append(str(err)))
            page.on("response", lambda resp: api_statuses.append({"url": resp.url, "status": resp.status}) if "/api/" in resp.url else None)

            target_url = f"{BASE_URL}{path}"
            http_status = None
            try:
                resp = await page.goto(target_url, wait_until="domcontentloaded", timeout=12000)
                http_status = resp.status if resp else None
            except Exception as e:
                page_errors.append(f"Navigation error: {e}")

            # Wait for React DOM to render and hydrate
            try:
                await page.wait_for_selector("#root", timeout=5000)
            except Exception as e:
                page_errors.append(f"Selector timeout (#root): {e}")

            # Settle query / async effects
            await page.wait_for_timeout(1000)

            title = await page.title()
            text = await page.evaluate("() => document.body.innerText") or ""
            trimmed_text = text.strip()
            has_non_empty_text = len(trimmed_text) > 0

            # Screenshots & text dumps
            png_path = os.path.join(AUDIT_DIR, f"{slug}.png")
            txt_path = os.path.join(AUDIT_DIR, f"{slug}.txt")

            try:
                await page.screenshot(path=png_path, full_page=True)
            except Exception as e:
                page_errors.append(f"Screenshot error: {e}")

            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(trimmed_text)

            # Numeric tokens count
            numeric_tokens = NUMERIC_REGEX.findall(trimmed_text)
            numeric_count = len(numeric_tokens)

            # Anti-fabrication check
            fab_matches = FABRICATION_REGEX.findall(trimmed_text)
            fab_failed = False
            if is_report and len(fab_matches) > 0:
                fab_failed = True

            # Determine API state
            api_state = "live"
            # Check if 422 was returned on any /api/ endpoint
            has_422 = any(s["status"] == 422 for s in api_statuses)
            if has_422:
                api_state = "not-covered (HTTP 422)"
            elif "[MODE OFFLINE]" in trimmed_text or "BE tidak tersedia saat ini" in trimmed_text or any(s["status"] in [404, 500, 502, 503, 504] for s in api_statuses):
                api_state = "offline"
            elif any("ERR_FAILED" in err or "CORS policy" in err for err in console_errors):
                api_state = "offline"
            elif is_report and "MENUNGGU" in trimmed_text and numeric_count < 10:
                api_state = "offline"

            # PASS/FAIL determination
            # Route fails if:
            # - empty text
            # - page threw uncaught JS error (pageerror)
            # - http status is not 200
            # - fabrication check failed on report route
            route_passed = (
                http_status == 200 and
                has_non_empty_text and
                len(page_errors) == 0 and
                not fab_failed
            )

            if not route_passed:
                has_failure = True

            result_entry = {
                "route": path,
                "slug": slug,
                "status": http_status,
                "title": title,
                "non_empty": has_non_empty_text,
                "text_length": len(trimmed_text),
                "console_errors": console_errors,
                "console_error_count": len(console_errors),
                "page_errors": page_errors,
                "numeric_tokens": numeric_count,
                "fab_matches": fab_matches,
                "api_state": api_state,
                "passed": route_passed,
                "png": png_path,
                "txt": txt_path,
            }
            results.append(result_entry)

            print(f"\n--- [ROUTE] {path} ---")
            print(f"HTTP Status      : {http_status}")
            print(f"Title            : {title!r}")
            print(f"Root Non-Empty   : {has_non_empty_text} ({len(trimmed_text)} chars)")
            print(f"Numeric Tokens   : {numeric_count}")
            print(f"API State        : {api_state}")
            print(f"Anti-Fabrication : {'FAIL: ' + str(fab_matches) if fab_failed else 'PASS (0 matches)'}")
            print(f"Page Errors      : {len(page_errors)}")
            print(f"Console Errors   : {len(console_errors)}")
            if console_errors:
                print("Verbatim Console Errors:")
                for ce in console_errors:
                    print(f"  {ce}")
            if page_errors:
                print("Verbatim Page Errors:")
                for pe in page_errors:
                    print(f"  {pe}")
            print(f"Artifacts        : {slug}.png, {slug}.txt")
            print(f"Result           : {'PASS' if route_passed else 'FAIL'}")

            await page.close()

        await browser.close()

    print("\n" + "="*85)
    print("=== [4/4] SMOKE HARNESS SUMMARY TABLE ===")
    print("="*85)
    header = f"| {'Route':<24} | {'Status':<6} | {'Rendered':<8} | {'Num Tokens':<10} | {'Console Err':<11} | {'API State':<12} | {'Result':<6} |"
    divider = f"|{'-'*26}|{'-'*8}|{'-'*10}|{'-'*12}|{'-'*13}|{'-'*14}|{'-'*8}|"
    print(header)
    print(divider)

    for r in results:
        rend_str = "YES" if r["non_empty"] else "NO"
        res_str = "PASS" if r["passed"] else "FAIL"
        row = f"| {r['route']:<24} | {str(r['status']):<6} | {rend_str:<8} | {r['numeric_tokens']:<10} | {r['console_error_count']:<11} | {r['api_state']:<12} | {res_str:<6} |"
        print(row)

    print("="*85)

    if has_failure:
        print("\n[ERROR] Smoke test harness encountered FAILURES.")
        sys.exit(1)
    else:
        print("\n[SUCCESS] All routes PASSED smoke verification.")
        sys.exit(0)

asyncio.run(run_smoke())
PYEOF
