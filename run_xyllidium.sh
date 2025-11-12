#!/usr/bin/env bash
# v3.5.5 Orchestrator — launch Bridge, Engine, Scope
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

source "$ROOT/.venv/bin/activate"

# logs
mkdir -p "$ROOT/logs"
: > "$ROOT/logs/bridge.log"
: > "$ROOT/logs/engine.log"
: > "$ROOT/logs/scope.log"

echo "[orchestrator] launching Bridge…"
nohup python "$ROOT/core/xyllencore/bridge_server.py" > "$ROOT/logs/bridge.log" 2>&1 & echo $! > "$ROOT/logs/bridge.pid"
sleep 0.8

echo "[orchestrator] launching Xyllenor engine…"
nohup python "$ROOT/core/xyllenor/engine.py" > "$ROOT/logs/engine.log" 2>&1 & echo $! > "$ROOT/logs/engine.pid"
sleep 0.8

echo "[orchestrator] launching Xyllscope…"
nohup python "$ROOT/interface/xyllscope/app.py" > "$ROOT/logs/scope.log" 2>&1 & echo $! > "$ROOT/logs/scope.pid"

echo "[orchestrator] All services up."
echo "Bridge:   ws://127.0.0.1:8765"
echo "Xyllscope http://127.0.0.1:8050"
