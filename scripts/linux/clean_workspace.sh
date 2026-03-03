#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-$(pwd)}"
cd "$PROJECT_ROOT"

find . -type d -name "__pycache__" -prune -exec rm -rf {} + || true
find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete || true

rm -rf .pytest_cache .mypy_cache .ruff_cache || true
rm -rf backup_patch_* || true

echo "OK: limpieza aplicada."

