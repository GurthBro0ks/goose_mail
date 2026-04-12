#!/usr/bin/env bash
# goose_mail — Agent Environment Init
# Run at the start of every agent session: source init.sh
set -euo pipefail

echo "=== goose_mail Init ==="

# 1. Confirm correct directory
if [ ! -f "AGENTS.md" ] || ! grep -q "goose_mail" AGENTS.md 2>/dev/null; then
  echo "ERROR: Run this from the goose_mail repo root."
  exit 1
fi

# 2. Check Python
echo "[1/4] Checking Python..."
python3 --version || { echo "ERROR: python3 not found"; exit 1; }

# 3. Set up virtual environment
echo "[2/4] Setting up environment..."
if command -v uv &>/dev/null; then
  echo "  Using uv"
  uv venv .venv 2>/dev/null || true
  source .venv/bin/activate 2>/dev/null || true
  [ -f "pyproject.toml" ] && uv pip install -e ".[dev]" --quiet 2>/dev/null || true
elif [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
  echo "  Activated existing .venv"
else
  python3 -m venv .venv 2>/dev/null || true
  source .venv/bin/activate 2>/dev/null || true
  [ -f "pyproject.toml" ] && pip install -e ".[dev]" -q 2>/dev/null || \
  [ -f "requirements.txt" ] && pip install -r requirements.txt -q 2>/dev/null || true
fi

# 4. Truth gate (quick lint check)
echo "[3/4] Running quick lint check..."
if command -v ruff &>/dev/null; then
  ruff check . 2>/dev/null && echo "  Lint: PASS" || echo "  WARN: Lint issues — fix before new work"
elif command -v flake8 &>/dev/null; then
  flake8 . 2>/dev/null && echo "  Lint: PASS" || echo "  WARN: Lint issues"
else
  echo "  WARN: No linter found (install ruff: pip install ruff)"
fi

# 5. Run tests
echo "[4/4] Running tests..."
if command -v pytest &>/dev/null; then
  pytest --tb=no -q 2>/dev/null && echo "  Tests: PASS" || echo "  WARN: Test failures detected"
else
  echo "  WARN: pytest not found"
fi

echo ""
echo "Available commands:"
echo "  pytest              → run test suite"
echo "  ruff check .        → lint"
echo "  ruff format .       → format"
echo "  git log --oneline -10 → recent history"
echo ""
echo "=== Init complete. Read agent-progress.md and feature_list.json next. ==="
