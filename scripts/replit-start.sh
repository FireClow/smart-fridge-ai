#!/usr/bin/env bash
# Replit production: single FastAPI process serves /api + built React SPA on port 80.
set -euo pipefail
cd "$(dirname "$0")/.."

export REPLIT_DEPLOYMENT=1

if [ ! -f frontend/dist/index.html ]; then
  echo "Missing frontend/dist — run deployment build first." >&2
  exit 1
fi

exec uvicorn backend.main:app --host 0.0.0.0 --port 80
