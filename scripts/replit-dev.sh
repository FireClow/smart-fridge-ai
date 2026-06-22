#!/usr/bin/env bash
# Replit development: FastAPI on :8000, Vite on :5000 (webview).
set -euo pipefail
cd "$(dirname "$0")/.."

export API_PORT="${API_PORT:-8000}"

pip install -r backend/requirements.txt -q

uvicorn backend.main:app --host 0.0.0.0 --port "$API_PORT" &
API_PID=$!

cd frontend
if [ ! -d node_modules ]; then
  npm ci
fi
npm run dev -- --host 0.0.0.0 --port 5000

kill "$API_PID" 2>/dev/null || true
