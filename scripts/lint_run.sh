#!/usr/bin/env bash
# scripts/lint_run.sh — Local runner for 5 lint & quality gates.
# Run order: lint -> format -> tests -> harness -> typst. Stop on first fail.
# Output is a single PASS/FAIL.

set -eo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

VENV_PYTHON="$REPO_ROOT/.venv/bin/python"
VENV_RUFF="$REPO_ROOT/.venv/bin/ruff"
VENV_BLACK="$REPO_ROOT/.venv/bin/black"
VENV_PYTEST="$REPO_ROOT/.venv/bin/pytest"

# 0. Sanity check binaries
if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Error: Python venv not found at $VENV_PYTHON" >&2
  echo "LINT-RESULT: FAIL"
  exit 1
fi

if [[ ! -x "$VENV_RUFF" ]]; then
  echo "Error: ruff not found in venv ($VENV_RUFF)" >&2
  echo "LINT-RESULT: FAIL"
  exit 1
fi

export PYTHONPATH="$REPO_ROOT"

# Determine target files for ruff
TARGETS=("$@")
if [[ ${#TARGETS[@]} -eq 0 ]]; then
  # Find changed or untracked python files, excluding files we are forbidden from touching
  CHANGED=$(git status --porcelain 2>/dev/null | awk '{print $2}' | grep -E '\.py$' || true)
  for f in $CHANGED; do
    case "$f" in
      scripts/report_charts.py|agents/valuation/gates.py|agents/valuation/assumptions.py|server/routers/*)
        # Skip forbidden / lane-B files
        ;;
      *)
        if [[ -f "$f" ]]; then
          TARGETS+=("$f")
        fi
        ;;
    esac
  done
fi

# If no changed files, default to scripts/harness_post_agy.py
if [[ ${#TARGETS[@]} -eq 0 ]]; then
  TARGETS=("scripts/harness_post_agy.py")
fi

echo "=== LINT & QUALITY GATES ==="

# Step 1: ruff check --fix
echo "[1/5] Running ruff check --fix..."
if ! "$VENV_RUFF" check --fix "${TARGETS[@]}"; then
  echo "Step 1 failed: ruff check found errors" >&2
  echo "LINT-RESULT: FAIL"
  exit 1
fi
echo "  Step 1: PASS (ruff check --fix)"

# Step 2: ruff format
echo "[2/5] Running ruff format..."
if ! "$VENV_RUFF" format "${TARGETS[@]}"; then
  echo "Step 2 failed: ruff format encountered error" >&2
  echo "LINT-RESULT: FAIL"
  exit 1
fi
echo "  Step 2: PASS (ruff format)"

# Step 3: pytest agents/valuation/ scripts/test_audit_quintet.py
echo "[3/5] Running pytest agents/valuation/ scripts/test_audit_quintet.py..."
if ! "$VENV_PYTEST" agents/valuation/ scripts/test_audit_quintet.py -q; then
  echo "Step 3 failed: pytest subset failed" >&2
  echo "LINT-RESULT: FAIL"
  exit 1
fi
echo "  Step 3: PASS (pytest valuation + quintet)"

# Step 4: python scripts/harness_post_agy.py
echo "[4/5] Running post-agy recovery harness..."
if ! "$VENV_PYTHON" scripts/harness_post_agy.py; then
  echo "Step 4 failed: recovery harness failed" >&2
  echo "LINT-RESULT: FAIL"
  exit 1
fi
echo "  Step 4: PASS (harness_post_agy.py)"

# Step 5: typst compile-check on the 4 archetype .typ files
echo "[5/5] Running typst compile-check on 4 archetypes..."
TYPST_BIN="$(which typst 2>/dev/null || echo "/home/fadil/.local/bin/typst")"
if [[ ! -x "$TYPST_BIN" ]]; then
  echo "Step 5 failed: typst binary not found" >&2
  echo "LINT-RESULT: FAIL"
  exit 1
fi

TMP_PDF="/tmp/typst_lint_check_$$.pdf"
for arch in single sotp infra strategy; do
  tmpl="templates/typst/archetypes/report_${arch}.typ"
  if ! "$TYPST_BIN" compile --font-path assets/fonts --root / "$tmpl" "$TMP_PDF" >/dev/null 2>&1; then
    rm -f "$TMP_PDF"
    echo "Step 5 failed: typst compile failed for $tmpl" >&2
    echo "LINT-RESULT: FAIL"
    exit 1
  fi
done
rm -f "$TMP_PDF"
echo "  Step 5: PASS (typst 4/4 archetypes compiled)"

echo ""
echo "LINT-RESULT: PASS"
exit 0
