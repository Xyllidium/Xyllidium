# ===============================================================
# 🧠 Xyllidium v4.4 — Xyllenor Equilibrium Engine
# Modules:
#   - WebSocket intent processor
#   - HTTP balance + memory interface
#   - XAP anchoring (Xyllidium Anchorage Protocol)
#   - Temporal Memory Decay (neural entropy simulation)
# ===============================================================

import os
import json
import asyncio
import datetime
import logging
import threading
import time
from flask import Flask, jsonify, request
from websockets.server import serve
import websockets
from core.xyllenor.xap_handler import make_xap
from core.xyllenor.temporal_decay import run_decay

# ---------------------------------------------------------------
# Logging
# ---------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("Xyllenor")

# ---------------------------------------------------------------
# Flask HTTP Interface
# ---------------------------------------------------------------
app = Flask(__name__)
balances = {"alice": 0.0, "bob": 0.0}
timevault_dir = "data/timevault"
os.makedirs(timevault_dir, exist_ok=True)


@app.route("/balance/<name>", methods=["GET"])
def get_balance(name):
    bal = balances.get(name, 0.0)
    return jsonify({name: bal})


@app.route("/memory/search", methods=["GET"])
def memory_search():
    """Return all XAPs optionally filtered by sender ('from' param)."""
    frm = request.args.get("from")
    results = []
    for f in os.listdir(timevault_dir):
        if not f.endswith(".json"):
            continue
        path = os.path.join(timevault_dir, f)
        try:
            xap = json.load(open(path))
            if frm and xap["intent"]["from"] != frm:
                continue
            results.append(xap)
        except Exception:
            continue
    return jsonify(results)


@app.route("/memory/get/<xap_id>", methods=["GET"])
def memory_get(xap_id):
    """Return one specific XAP record."""
    path = os.path.join(timevault_dir, f"{xap_id}.json")
    if not os.path.exists(path):
        return jsonify({"ok": False, "error": "not_found"}), 404
    return jsonify(json.load(open(path)))


@app.route("/reconstruct/<xap_id>", methods=["GET"])
def reconstruct_xap(xap_id):
    """Placeholder for future stub reconstruction."""
    stub = os.path.join(timevault_dir, f"{xap_id}.stub.json")
    if not os.path.exists(stub):
        return jsonify({"ok": False, "error": "no_stub"}), 404
    return jsonify(json.load(open(stub)))


@app.route("/peers", methods=["POST"])
def register_peers():
    peers = request.json.get("peers", [])
    return jsonify({"ok": True, "peers": peers})

# ---------------------------------------------------------------
# WebSocket Intent Processor
# ---------------------------------------------------------------
async def handle_intent(websocket):
    """Process incoming intents from executor or remote nodes."""
    try:
        async for message in websocket:
            intent = json.loads(message)
            logger.info(f"⚡ received intent: {intent}")
            # Basic transfer simulation
            if intent.get("type") == "transfer":
                frm, to = intent["from"], intent["to"]
                amt = float(intent["amount"])
                balances[frm] = balances.get(frm, 0.0) - amt
                balances[to] = balances.get(to, 0.0) + amt
                logger.info(f"✅ processed transfer {frm} → {to}, {amt} xyls")
                ack = {
                    "ok": True,
                    "type": "transfer",
                    "from": frm,
                    "to": to,
                    "amount": amt
                }
                await websocket.send(json.dumps(ack))
                logger.info(f"🔗 Acknowledged by equilibrium engine: {json.dumps(ack)}")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")


async def ws_server():
    """Launch the WebSocket listener."""
    async with serve(handle_intent, "127.0.0.1", 8765):
        logger.info("✅ WebSocket server active on ws://127.0.0.1:8765")
        await asyncio.Future()  # keep running

# ---------------------------------------------------------------
# Background Decay Thread
# ---------------------------------------------------------------
def background_decay():
    """Continuously decay old XAPs to maintain neural equilibrium."""
    while True:
        time.sleep(600)  # every 10 minutes
        run_decay("data/timevault")

# ---------------------------------------------------------------
# Main Launcher
# ---------------------------------------------------------------
def main():
    logger.info("WS server → ws://127.0.0.1:8765")
    logger.info("HTTP read API → http://127.0.0.1:8766")

    # Start decay thread
    threading.Thread(target=background_decay, daemon=True).start()

    # Launch WebSocket + HTTP concurrently
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(ws_server())

    # Run Flask server (non-blocking)
    from threading import Thread
    Thread(target=lambda: app.run(port=8766, debug=False, use_reloader=False)).start()

    # Keep loop alive
    loop.run_forever()


if __name__ == "__main__":
    main()
