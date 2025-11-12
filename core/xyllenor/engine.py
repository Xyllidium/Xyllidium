# ~/work/xyllidium/core/xyllenor/engine.py
import os
import json
import time
import asyncio
import logging
import hashlib
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from websockets.server import serve
import threading

# === Imports from sibling modules (absolute) ===
from core.xyllenor.xap_handler import make_xap
from core.xyllenor.timevault_bridge import (
    list_timevault_files,
    load_xap,
    store_xap,
)

# --- Logging setup ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("xyllenor")

# --- Globals ---
balances = {"alice": 0.0, "bob": 0.0}
DATA_DIR = os.path.join(os.path.dirname(__file__), "../../data/timevault")
os.makedirs(DATA_DIR, exist_ok=True)

# === Flask App ===
app = Flask("engine")

@app.route("/balance/<acct>")
def balance(acct):
    """Return current balance for a given account."""
    return jsonify({"balance": balances.get(acct, 0.0)})

@app.route("/apply_intent", methods=["POST"])
def apply_intent_http():
    """HTTP fallback endpoint to apply transfer intents."""
    try:
        intent = request.get_json(force=True)
        if not intent or intent.get("type") != "transfer":
            return jsonify({"ok": False, "error": "invalid_intent"}), 400

        apply_transfer(intent)
        xap = make_xap(intent)
        store_xap(xap)
        return jsonify({"ok": True, "applied": intent["id"], "xap_id": xap["id"]})
    except Exception as e:
        log.exception("Error applying intent")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/memory/search")
def memory_search():
    """Search all XAPs anchored from a specific account."""
    acct = request.args.get("from")
    results = []
    for fn in list_timevault_files():
        if fn.endswith(".json"):
            rec = load_xap(fn)
            if rec and rec["intent"]["from"] == acct:
                results.append(rec)
    return jsonify(results)

# === WebSocket handler ===
async def ws_handler(websocket):
    """Handles live transfer intents from clients."""
    async for message in websocket:
        intent = json.loads(message)
        log.info(f"⚡ received intent: {intent}")
        if intent["type"] == "transfer":
            apply_transfer(intent)
            xap = make_xap(intent)
            store_xap(xap)
            ack = {"ok": True, "type": "transfer", "from": intent["from"], "to": intent["to"], "amount": intent["amount"]}
            await websocket.send(json.dumps(ack))
            log.info(f"✅ processed transfer {intent['from']} → {intent['to']}, {intent['amount']} xyls")

def apply_transfer(intent):
    """Apply a transfer intent to balances."""
    sender, receiver, amt = intent["from"], intent["to"], float(intent["amount"])
    balances.setdefault(sender, 0.0)
    balances.setdefault(receiver, 0.0)
    balances[sender] -= amt
    balances[receiver] += amt

# === Temporal Memory Decay ===
def decay_old_xaps():
    """Removes old non-permanent XAPs from the vault (memory decay)."""
    now = datetime.utcnow()
    decay_window = timedelta(minutes=2)  # delete anything older than 2 min if non-permanent
    decayed = 0

    for fn in list_timevault_files():
        path = os.path.join(DATA_DIR, fn)
        try:
            rec = load_xap(fn)
            if not rec:
                continue
            if not rec.get("permanent", False):
                t = datetime.fromisoformat(rec["timestamp"])
                if now - t > decay_window:
                    os.remove(path)
                    decayed += 1
        except Exception:
            continue
    if decayed > 0:
        log.info(f"🫧 decayed {decayed} non-permanent XAP(s)")
    else:
        log.info(f"🫧 decayed 0 non-permanent XAP(s)")

def decay_loop():
    """Run decay periodically in background."""
    while True:
        decay_old_xaps()
        time.sleep(60)

# === Startup ===
async def main():
    http_port, ws_port = 8766, 8765
    log.info(f"HTTP read API → http://127.0.0.1:{http_port}")
    log.info(f"WS server → ws://127.0.0.1:{ws_port}")

    # Background thread for decay
    threading.Thread(target=decay_loop, daemon=True).start()

    # Start WebSocket server
    async with serve(ws_handler, "127.0.0.1", ws_port):
        log.info(f"✅ WebSocket server active on ws://127.0.0.1:{ws_port}")
        # Start Flask in a thread
        threading.Thread(target=lambda: app.run(host="127.0.0.1", port=http_port, use_reloader=False), daemon=True).start()
        # Keep running forever
        while True:
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
