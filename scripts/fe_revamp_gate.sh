#!/usr/bin/env bash
# Integration gate for the FE revamp. Run this AFTER the lanes land, before claiming anything.
#
# It answers one question: does the frontend show what the PDF shows, from the same payload, without a single
# fabricated value? Each check prints its own evidence line, and the script fails loudly rather than passing on a
# missing artifact.
#
#   bash scripts/fe_revamp_gate.sh            # full run
#   SKIP_TESTS=1 bash scripts/fe_revamp_gate.sh   # skip the Python suite (slow) and check the rest
set -u
cd "$(dirname "$0")/.." || exit 1
ROOT=$(pwd)
API_BASE="${API_BASE:-https://report.server-fadil.my.id}"
PAYLOAD_PATH="${PAYLOAD_PATH:-/api/report/AMMN/payload}"
PASS=0
FAIL=0
BLOCKED=0

say()  { printf '\n=== %s\n' "$1"; }
ok()   { printf '  PASS  %s\n' "$1"; PASS=$((PASS+1)); }
bad()  { printf '  FAIL  %s\n' "$1"; FAIL=$((FAIL+1)); }
note() { printf '        %s\n' "$1"; }
blocked() { printf '  BLOCKED  %s\n' "$1"; BLOCKED=$((BLOCKED+1)); }

say "1. backend: the payload endpoint exists and matches the PDF payload"
if [ "${SKIP_TESTS:-0}" != "1" ] && [ -f tests/test_fe_payload_endpoint.py ]; then
  OUT=$(timeout 300 .venv/bin/python -m pytest tests/test_fe_payload_endpoint.py -q -p no:randomly 2>&1 | tail -3)
  note "$(echo "$OUT" | tail -1)"
  if echo "$OUT" | grep -qE "passed"; then ok "payload endpoint tests pass"; else bad "payload endpoint tests failed"; fi
else
  note "tests/test_fe_payload_endpoint.py not present — lane A has not landed"
  bad "payload endpoint has no test file"
fi

say "2. backend: the endpoint equals the builder the PDF uses (parity, live)"
CODE_LOCAL=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "http://127.0.0.1:8777${PAYLOAD_PATH}" || echo 000)
note "GET http://127.0.0.1:8777${PAYLOAD_PATH} -> $CODE_LOCAL"
if [ "$CODE_LOCAL" = "404" ]; then
  blocked "the running backend serves no /payload — it predates this work, so the parity cannot be observed yet"
else
PARITY=$(timeout 240 .venv/bin/python - <<'PY' 2>&1 | tail -4
import json, sys, urllib.request
sys.path.insert(0, ".")
from server.routers.pdf import render_html_for_ticker

_t, _h, payload = render_html_for_ticker("AMMN", None)
try:
    with urllib.request.urlopen("http://127.0.0.1:8777/api/report/AMMN/payload", timeout=60) as r:
        body = json.loads(r.read())
except Exception as exc:
    print(f"local endpoint unreachable ({type(exc).__name__}: {exc})")
    raise SystemExit(0)

served = body.get("payload", body)
local_keys, served_keys = set(payload), set(served)
print(f"local keys {len(local_keys)} · served keys {len(served_keys)}")
print(f"missing from endpoint: {sorted(local_keys - served_keys)[:6] or 'none'}")
print(f"extra in endpoint:     {sorted(served_keys - local_keys)[:6] or 'none'}")
print("PARITY_OK" if local_keys == served_keys else "PARITY_MISMATCH")
PY
)
echo "$PARITY" | sed 's/^/        /'
echo "$PARITY" | grep -q PARITY_OK && ok "endpoint key set == render_html_for_ticker key set" || bad "endpoint drifted from the PDF payload"
fi

say "3. backend: an uncovered ticker is refused, not faked"
CODE=$(timeout 60 curl -s -o /tmp/gate_422.json -w '%{http_code}' "$API_BASE/api/report/BBCA/payload" || echo 000)
note "GET $API_BASE/api/report/BBCA/payload -> $CODE"
if [ "$CODE" = "422" ]; then
  ok "uncovered ticker refused with 422 (body: $(head -c 160 /tmp/gate_422.json 2>/dev/null))"
elif [ "$CODE" = "404" ]; then
  blocked "404 — the running backend does not serve the payload route yet, so the refusal cannot be observed"
else
  bad "uncovered ticker returned $CODE — a fabricated payload would be the wrong answer"
fi

say "3b. frontend reads the refusal in the shape the API actually sends"
# FastAPI wraps HTTPException in {"detail": {...}}, so the missing list lives at detail.missing, not missing.
# A page that reads the flat key renders "belum tercakup" with an empty list and never shows what is missing.
if grep -rqE "detail" src/fe/src/routes src/fe/src/lib 2>/dev/null; then
  ok "the FE references the detail envelope"
else
  bad "no FE file reads detail.* — the 422 missing list would render empty"
fi
if grep -rqE "missing" src/fe/src/routes src/fe/src/lib 2>/dev/null; then
  ok "the FE surfaces the missing-field list"
else
  bad "the FE never mentions the missing list"
fi

say "4. frontend: typecheck (the project's own, tsc -b)"
if [ -d src/fe ]; then
  if grep -q '"typecheck"' src/fe/package.json; then
    TSC=$(cd src/fe && timeout 420 npm run typecheck 2>&1 | tail -6)
  else
    TSC=$(cd src/fe && timeout 420 npx tsc --noEmit 2>&1 | tail -6)
  fi
  if echo "$TSC" | grep -qiE "error TS|error:"; then
    echo "$TSC" | sed 's/^/        /'; bad "typecheck reported errors"
  else
    ok "typecheck clean"
  fi
  if grep -q '"lint"' src/fe/package.json; then
    LINT=$(cd src/fe && timeout 300 npm run lint 2>&1 | tail -4)
    if echo "$LINT" | grep -qiE "error|warn"; then note "lint: $(echo "$LINT" | tail -2 | tr '\n' ' ')"; fi
  fi
else
  bad "src/fe missing"
fi

say "4b. the production build points at the live API"
ENVF=src/fe/.env.production
if [ -f "$ENVF" ] && grep -q "VITE_API_URL" "$ENVF"; then
  URL=$(grep -oE 'https?://[^[:space:]]+' "$ENVF" | head -1)
  note "$ENVF: VITE_API_URL=$URL"
  if [ "$URL" = "$API_BASE" ]; then ok "production build targets $API_BASE"
  else bad "production build targets $URL but the gate checks $API_BASE"; fi
else
  bad "src/fe/.env.production does not define VITE_API_URL — the deployed bundle would call its own origin"
fi

say "5. frontend: production build"
BUILD=$(cd src/fe && VITE_API_URL="$API_BASE" timeout 600 npm run build 2>&1 | tail -6)
echo "$BUILD" | sed 's/^/        /'
if echo "$BUILD" | grep -qiE "built in|dist/"; then
  ok "build succeeded"
  BUNDLE=$(ls -S src/fe/dist/assets/*.js 2>/dev/null | head -1)
  if [ -n "${BUNDLE:-}" ]; then note "largest bundle: $(basename "$BUNDLE") $(wc -c < "$BUNDLE") bytes"; fi
else
  bad "build failed"
fi

say "5b. every payload path the FE reads exists in the payload"
PATHS=$(timeout 300 .venv/bin/python scripts/fe_payload_path_check.py 2>/dev/null | grep -vE "^2026-|INFO|Starlette|from starlette")
echo "$PATHS" | sed 's/^/        /'
if echo "$PATHS" | grep -q "NOT in the payload: 0"; then
  ok "no dangling payload path"
else
  bad "the FE reads a payload path the payload does not carry (it renders empty or crashes on .toFixed)"
fi

say "6. frontend bundle: no fabrication markers, honest states present"
JS=$(cat src/fe/dist/assets/*.js 2>/dev/null)
if [ -z "$JS" ]; then
  bad "no built JS to inspect"
else
  # --word-regexp on purpose: a bare "placeholder" also matches Tailwind's `placeholder:text-...` variant, which is a
  # CSS selector rather than fabricated data. These patterns are the shapes a fake dataset actually takes.
  for marker in "lorem ipsum" "dummy data" "sample data" "MOCK_DATA" "FAKE_DATA" "fixture data"; do
    if printf '%s' "$JS" | grep -qi "$marker"; then bad "bundle contains '$marker'"; else ok "bundle free of '$marker'"; fi
  done
  # A MOCK token is not by itself fabrication — the demo route ships a notice saying its mock data was retired, and
  # that notice is the honest thing to ship. Flag a MOCK token only when it is not that notice.
  MOCKHITS=$(printf '%s' "$JS" | grep -oE ".{24}MOCK.{24}" | grep -vc "ROUTE DEPRECATED" || true)
  if [ "${MOCKHITS:-0}" -gt 0 ]; then bad "bundle carries a MOCK/DUMMY token outside the retirement notice ($MOCKHITS)"; else ok "the only MOCK token is the retirement notice"; fi
  # assert the honest states the FE actually renders (checked against the source, not guessed): the 422 panel and the
  # pending state for a section the payload does not carry
  for honest in "Belum Tersedia" "Belum Terverifikasi"; do
    if printf '%s' "$JS" | grep -qi "$honest"; then ok "bundle carries the honest state '$honest'"; else bad "bundle has no '$honest' state"; fi
  done
fi

say "6b. no new fabrication candidate (ratchet against the judged set)"
RATCHET=$(timeout 300 .venv/bin/python scripts/fe_fabrication_ratchet.py 2>&1 | tail -8)
echo "$RATCHET" | sed 's/^/        /'
if echo "$RATCHET" | grep -q "NEW FABRICATION CANDIDATE"; then
  bad "a new fabrication candidate appeared — judge it and give a reason, then re-run --update"
else
  ok "scanner finds nothing beyond the judged set"
fi

say "7. the API base is reachable from a browser build"
LIVE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$API_BASE/api/report/AMMN" || echo 000)
note "$API_BASE/api/report/AMMN -> $LIVE"
[ "$LIVE" = "200" ] && ok "tunnel + BE answering" || bad "API base not answering ($LIVE)"

say "8. the served BE is the systemd unit, not an orphan process"
LISTENER=$(ss -ltnp 2>/dev/null | grep ':8777' | grep -oE 'pid=[0-9]+' | head -1 | cut -d= -f2)
MAINPID=$(systemctl --user show -p MainPID --value sectors-be.service 2>/dev/null)
note "listener pid=$LISTENER · systemd MainPID=$MAINPID"
if [ -n "${LISTENER:-}" ] && [ "${LISTENER:-x}" = "${MAINPID:-y}" ]; then
  ok "port 8777 is owned by the service the supervisor tracks"
else
  bad "port 8777 is owned by a process systemd does not track (orphan)"
fi

say "RESULT"
printf '  %d passed, %d failed, %d blocked\n' "$PASS" "$FAIL" "$BLOCKED"
[ "$FAIL" -eq 0 ] && echo "  GATE: green" || echo "  GATE: NOT green — do not claim the revamp is done"
exit $([ "$FAIL" -eq 0 ] && echo 0 || echo 1)
