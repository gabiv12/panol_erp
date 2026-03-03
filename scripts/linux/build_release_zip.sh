#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-$(pwd)}"
REF="${2:-HEAD}"
OUT_ZIP="${3:-$HOME/LaTermal_release.zip}"

cd "$PROJECT_ROOT"
if [ ! -d ".git" ]; then
  echo "ERROR: no se encontró .git. Ejecutar en repo git."
  exit 1
fi

git archive --format=zip --output "$OUT_ZIP" "$REF"
echo "OK: ZIP generado en: $OUT_ZIP"

