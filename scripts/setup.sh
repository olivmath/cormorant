#!/bin/bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Backend setup ==="
cd "$REPO_ROOT/backend"
if command -v uv &>/dev/null; then
    uv sync
    uv run python -c "from ultralytics import YOLO; YOLO('yolov8s.pt')"
else
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]"
    python -c "from ultralytics import YOLO; YOLO('yolov8s.pt')"
fi

echo "=== Frontend setup ==="
cd "$REPO_ROOT/frontend"
pnpm install

echo "=== Done ==="
