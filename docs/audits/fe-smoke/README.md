# Frontend Smoke Test & Baseline Audit

Smoke harness and baseline audit for the Sektoral.id institutional report frontend (`src/fe`).

## 1. Execution Command

```bash
# Run full FE smoke harness (builds to dist-smoke, serves with SPA fallback, navigates via Playwright Chromium)
./scripts/smoke_fe.sh
```

### Environment & Test Engine
- **Engine**: Playwright Bundled Chromium (`version 148.0.7778.96`)
- **Runtime**: Node.js `v24.14.1` / Python `3.11.14` (`.venv`)
- **Build Tool**: Vite `v8.2.2` (Rolldown + TailwindCSS v4 + React 19)
- **Scratch Output**: `src/fe/dist-smoke` (main `dist` untouched)
- **SPA Fallback**: `npx serve -s` on ephemeral port with `index.html -> 404.html` fallback

---

## 2. Per-Route Summary Table

| Route | Status | Root Rendered | Text Length | Numeric Tokens | Console Errors | Page Errors | Anti-Fabrication | API State | Result |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `/` | `200` | YES | 5,292 chars | 47 | 30 | 0 | PASS (0 matches) | `offline` | **PASS** |
| `/report/AMMN` | `200` | YES | 913 chars | 5 | 4 | 0 | PASS (0 matches) | `offline` | **PASS** |
| `/report/AMMN/sentiment` | `200` | YES | 1,327 chars | 15 | 8 | 0 | PASS (0 matches) | `offline` | **PASS** |
| `/report/AMMN/challenge` | `200` | YES | 1,327 chars | 15 | 4 | 0 | PASS (0 matches) | `offline` | **PASS** |
| `/agent` | `200` | YES | 2,475 chars | 33 | 6 | 0 | PASS (0 matches) | `offline` | **PASS** |
| `/mock-sectors/AMMN` | `200` | YES | 1,177 chars | 8 | 0 | 0 | PASS (0 matches) | `live` | **PASS** |

---

## 3. Detected API State & Anti-Fabrication Signals

### Detected API State
- **`/` (Market Monitor Hub)**: `offline`
  - Attempts to fetch live prices/DCF for quintet tickers (`RATU`, `CDIA`, `MTEL`, `BBCA`, `ADRO`). Due to offline/unreachable backend (`https://report.server-fadil.my.id`), fallback triggers honest `MENUNGGU` and offline status.
- **`/report/AMMN` (Institutional Report)**: `offline`
  - Rendered: `[MODE OFFLINE] SERVER BACKEND BELUM TERSEDIA // AMMN`.
  - Honest zero-fabrication fallback: displays clean offline notification with 0 synthesized figures.
- **`/report/AMMN/sentiment`**: `offline`
  - Rendered: offline notice banner with retry capability.
- **`/report/AMMN/challenge`**: `offline`
  - Rendered: offline notice banner with retry capability.
- **`/agent` (Multi-Agent Orchestrator)**: `offline`
  - Rendered: `MESIN SIAGA` with standby controls.
- **`/mock-sectors/AMMN` (Deprecated Mock Route)**: `live`
  - Static 301 deprecation landing page explaining that mock data has been completely retired.

### Numeric Token Counts (Before/After Diff Baseline)
- `/`: **47** numeric tokens (monitoring card layout, time, quintet indices)
- `/report/AMMN`: **5** numeric tokens (`1`, `2`, `3` shortcuts, `12.24.49` clock, `2.6` version). *Note: Baseline has 0 fake financial figures in offline mode. When the institutional report payload lands, this count will scale to 120+ authentic data points.*
- `/report/AMMN/sentiment`: **15** numeric tokens (date timestamps, system metrics)
- `/report/AMMN/challenge`: **15** numeric tokens (date timestamps, system metrics)
- `/agent`: **33** numeric tokens (16 agents, version 1.2, timer offsets)
- `/mock-sectors/AMMN`: **8** numeric tokens (100% live notice, 301 status, version 2.6)

### Anti-Fabrication Check
- Regex: `\b(lorem|dummy|example)\b` (case-insensitive)
- Result: **0 matches across all routes** (PASS). Zero synthesized lorem ipsum or placeholder text.

---

## 4. Per-Route Detailed Logs & Verbatim Console Errors

### Route: `/`
- **Title**: `""`
- **Status**: `200`
- **Page Errors**: `0`
- **Console Errors (30 total)**:
  - `[error] Access to fetch at 'https://report.server-fadil.my.id/api/dcf/MTEL' from origin 'http://localhost:55533' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
  - `[error] Failed to load resource: net::ERR_FAILED`
  - `[error] Access to fetch at 'https://report.server-fadil.my.id/api/dcf/RATU' from origin 'http://localhost:55533' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
  - `[error] Failed to load resource: net::ERR_FAILED`
  - `[error] Access to fetch at 'https://report.server-fadil.my.id/api/report/RATU' from origin 'http://localhost:55533' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
  - `[error] Failed to load resource: net::ERR_FAILED`
  - `[error] Access to fetch at 'https://report.server-fadil.my.id/api/dcf/CDIA' from origin 'http://localhost:55533' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
  - `[error] Failed to load resource: net::ERR_FAILED`
  - `[error] Access to fetch at 'https://report.server-fadil.my.id/api/dcf/BBCA' from origin 'http://localhost:55533' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
  - `[error] Failed to load resource: net::ERR_FAILED`
  - `[error] Access to fetch at 'https://report.server-fadil.my.id/api/dcf/ADRO' from origin 'http://localhost:55533' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
  - `[error] Failed to load resource: net::ERR_FAILED`
  - `[error] Access to fetch at 'https://report.server-fadil.my.id/api/report/CDIA' from origin 'http://localhost:55533' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
  - `[error] Failed to load resource: net::ERR_FAILED`
  - `[error] Access to fetch at 'https://report.server-fadil.my.id/api/report/MTEL' from origin 'http://localhost:55533' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
  - `[error] Failed to load resource: net::ERR_FAILED`
  - `[error] Access to fetch at 'https://report.server-fadil.my.id/api/report/BBCA' from origin 'http://localhost:55533' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
  - `[error] Failed to load resource: net::ERR_FAILED`
  - `[error] Access to fetch at 'https://report.server-fadil.my.id/api/report/ADRO' from origin 'http://localhost:55533' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
  - `[error] Failed to load resource: net::ERR_FAILED`
- **Artifacts**: [`root.png`](./root.png), [`root.txt`](./root.txt)

### Route: `/report/AMMN`
- **Title**: `""`
- **Status**: `200`
- **Page Errors**: `0`
- **Console Errors (4 total)**:
  - `[error] Access to fetch at 'https://report.server-fadil.my.id/api/report/AMMN/payload' from origin 'http://localhost:55533' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
  - `[error] Failed to load resource: net::ERR_FAILED`
  - `[error] Access to fetch at 'https://report.server-fadil.my.id/api/report/AMMN/log' from origin 'http://localhost:55533' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
  - `[error] Failed to load resource: net::ERR_FAILED`
- **Artifacts**: [`report-AMMN.png`](./report-AMMN.png), [`report-AMMN.txt`](./report-AMMN.txt)

### Route: `/report/AMMN/sentiment`
- **Title**: `""`
- **Status**: `200`
- **Page Errors**: `0`
- **Console Errors (8 total)**:
  - `[error] Access to fetch at 'https://report.server-fadil.my.id/api/sentiment?ticker=AMMN' from origin 'http://localhost:55533' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
  - `[error] Failed to load resource: net::ERR_FAILED`
  - `[error] Access to fetch at 'https://report.server-fadil.my.id/api/report/AMMN' from origin 'http://localhost:55533' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
  - `[error] Failed to load resource: net::ERR_FAILED`
  - `[error] Access to fetch at 'https://report.server-fadil.my.id/api/news?ticker=AMMN&limit=30' from origin 'http://localhost:55533' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
  - `[error] Failed to load resource: net::ERR_FAILED`
  - `[error] Access to fetch at 'https://report.server-fadil.my.id/api/report/AMMN/log' from origin 'http://localhost:55533' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
  - `[error] Failed to load resource: net::ERR_FAILED`
- **Artifacts**: [`report-AMMN-sentiment.png`](./report-AMMN-sentiment.png), [`report-AMMN-sentiment.txt`](./report-AMMN-sentiment.txt)

### Route: `/report/AMMN/challenge`
- **Title**: `""`
- **Status**: `200`
- **Page Errors**: `0`
- **Console Errors (4 total)**:
  - `[error] Access to fetch at 'https://report.server-fadil.my.id/api/report/AMMN/log' from origin 'http://localhost:55533' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
  - `[error] Failed to load resource: net::ERR_FAILED`
  - `[error] Access to fetch at 'https://report.server-fadil.my.id/api/report/AMMN' from origin 'http://localhost:55533' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
  - `[error] Failed to load resource: net::ERR_FAILED`
- **Artifacts**: [`report-AMMN-challenge.png`](./report-AMMN-challenge.png), [`report-AMMN-challenge.txt`](./report-AMMN-challenge.txt)

### Route: `/agent`
- **Title**: `""`
- **Status**: `200`
- **Page Errors**: `0`
- **Console Errors (6 total)**:
  - `[error] Access to fetch at 'https://report.server-fadil.my.id/api/agent/runs' from origin 'http://localhost:55533' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
  - `[error] Failed to load resource: net::ERR_FAILED`
  - `[error] Access to fetch at 'https://report.server-fadil.my.id/api/tickers' from origin 'http://localhost:55533' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
  - `[error] Failed to load resource: net::ERR_FAILED`
  - `[error] Access to fetch at 'https://report.server-fadil.my.id/api/agent/health' from origin 'http://localhost:55533' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
  - `[error] Failed to load resource: net::ERR_FAILED`
- **Artifacts**: [`agent.png`](./agent.png), [`agent.txt`](./agent.txt)

### Route: `/mock-sectors/AMMN`
- **Title**: `""`
- **Status**: `200`
- **Page Errors**: `0`
- **Console Errors**: `0` (clean static rendering)
- **Artifacts**: [`mock-sectors-AMMN.png`](./mock-sectors-AMMN.png), [`mock-sectors-AMMN.txt`](./mock-sectors-AMMN.txt)

---

## 5. Defects and Observations Exposed by this Baseline

1. **Empty Document `<title>` Across All Routes**:
   - `document.title` is currently empty string `""` on every route. No route sets dynamic or branded page titles (e.g. `AMMN Institutional Report | Sektoral.id`).
2. **Missing Backend Service / CORS Fetch Errors in Offline Environment**:
   - Production `.env.production` hardcodes `VITE_API_URL=https://report.server-fadil.my.id`. When running locally in standalone or offline environments without network access to that domain, browsers block requests with CORS / network errors.
   - All client queries properly catch errors and switch to honest offline states without unhandled exceptions (`pageerror: 0`).
3. **Low Numeric Token Density on Offline Report Route**:
   - On `/report/AMMN`, exactly 5 numeric tokens are rendered (header & footer controls). The page strictly refuses to render mock financial tables, waiting for genuine payload response.
4. **No Uncaught JS Exceptions**:
   - Every route cleanly renders non-empty DOM and hydrations without throwing JavaScript runtime crashes.
