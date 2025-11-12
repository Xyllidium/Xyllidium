#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

source .venv/bin/activate

# kill any stale bridge
fuser -k 8765/tcp 2>/dev/null || true
pkill -f bridge_server.py 2>/dev/null || true

# start bridge
echo "[launcher] starting bridge..."
python core/xyllencore/bridge_server.py >/tmp/xyll_bridge.log 2>&1 &

sleep 0.7
echo "[launcher] starting xyllscope..."
python interface/xyllscope/app.py
