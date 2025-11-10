#!/bin/bash
# ============================================================
# Xyllidium Unified Launcher
# Starts Bridge → Executor → Xyllscope automatically
# ============================================================

PROJECT_DIR=~/work/xyllidium
VENV=$PROJECT_DIR/.venv/bin/activate

echo "🔋 Activating environment..."
source $VENV

# --- Start Bridge Server ---
echo "🌐 Starting Bridge Server..."
python $PROJECT_DIR/core/xyllencore/bridge_server.py &
sleep 2

# --- Start Executor ---
echo "⚙️ Starting Xyllencore Executor..."
python $PROJECT_DIR/core/xyllencore/executor.py &
sleep 3

# --- Start Xyllscope Interface ---
echo "🧠 Launching Xyllscope Dashboard..."
python $PROJECT_DIR/interface/xyllscope/app.py
