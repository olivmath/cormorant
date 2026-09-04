#!/bin/bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    if command -v sudo >/dev/null 2>&1; then
        sudo apt-get update
        sudo apt-get install -y libgl1
    else
        apt-get update
        apt-get install -y libgl1
    fi
fi

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
