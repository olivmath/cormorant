#!/bin/bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cleanup() {
    echo "Stopping..."
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
    wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
}
trap cleanup EXIT

echo "Starting backend on :8000..."
cd "$REPO_ROOT/backend"
if command -v uv &>/dev/null; then
    uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 &
else
    source .venv/bin/activate
    uvicorn src.main:app --host 0.0.0.0 --port 8000 &
fi
BACKEND_PID=$!

echo "Starting frontend on :3000..."
cd "$REPO_ROOT/frontend"
pnpm dev &
FRONTEND_PID=$!

echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
wait
