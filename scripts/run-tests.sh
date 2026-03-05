#!/bin/bash
# Run all CallPilot tests (backend + frontend).
# Usage: ./scripts/run-tests.sh [--backend-only | --frontend-only]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

BACKEND_ONLY=false
FRONTEND_ONLY=false

for arg in "$@"; do
  case $arg in
    --backend-only)  BACKEND_ONLY=true ;;
    --frontend-only) FRONTEND_ONLY=true ;;
  esac
done

BACKEND_EXIT=0
FRONTEND_EXIT=0

# ---------------------------------------------------------------------------
# Backend (pytest)
# ---------------------------------------------------------------------------

if [ "$FRONTEND_ONLY" = false ]; then
  echo "=============================="
  echo " Backend Tests (pytest)"
  echo "=============================="
  echo ""

  cd "$BACKEND_DIR"

  # Use a virtualenv if present, otherwise fall back to the system python
  if [ -d ".venv" ]; then
    source .venv/bin/activate
  elif [ -d "venv" ]; then
    source venv/bin/activate
  fi

  # Install test dependencies if pytest is not already available
  if ! python -m pytest --version &>/dev/null 2>&1; then
    echo "Installing backend test dependencies..."
    pip install -q -r requirements.txt -r requirements-test.txt
  fi

  python -m pytest "$@" || BACKEND_EXIT=$?
  echo ""
fi

# ---------------------------------------------------------------------------
# Frontend (jest)
# ---------------------------------------------------------------------------

if [ "$BACKEND_ONLY" = false ]; then
  echo "=============================="
  echo " Frontend Tests (jest)"
  echo "=============================="
  echo ""

  cd "$FRONTEND_DIR"

  # Install dependencies if jest binary is missing (node_modules may exist without jest)
  if [ ! -f "node_modules/.bin/jest" ]; then
    echo "Installing frontend dependencies..."
    npm install --silent
  fi

  npm test -- --passWithNoTests || FRONTEND_EXIT=$?
  echo ""
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo "=============================="
echo " Results"
echo "=============================="

if [ "$FRONTEND_ONLY" = false ]; then
  if [ "$BACKEND_EXIT" -eq 0 ]; then
    echo " Backend:  PASSED"
  else
    echo " Backend:  FAILED (exit $BACKEND_EXIT)"
  fi
fi

if [ "$BACKEND_ONLY" = false ]; then
  if [ "$FRONTEND_EXIT" -eq 0 ]; then
    echo " Frontend: PASSED"
  else
    echo " Frontend: FAILED (exit $FRONTEND_EXIT)"
  fi
fi

echo ""

OVERALL=$((BACKEND_EXIT + FRONTEND_EXIT))
if [ "$OVERALL" -ne 0 ]; then
  echo "One or more test suites failed."
  exit 1
fi

echo "All tests passed."
