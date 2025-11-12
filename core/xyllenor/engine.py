# ~/work/xyllidium/core/xyllenor/engine.py
import asyncio, json, os, logging, threading
from flask import Flask, jsonify, request
import websockets
from datetime import datetime
from core.xyllenor.xap_handler import make_xap

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("xyllenor")

app = Flask(__name__)

BALANCES = {"alice": 0.0, "bob": 0.0}
TIMEVAULT_DIR = "data/timevault"
os.makedirs(TIMEVAULT_DIR, exist_ok=True)

# ---------- WebSocket handler ----------
async def handle_ws(websocket):
    async for message in websocket:
        try:
            intent = json.loads(message)
            logger.info(f"⚡ received intent: {intent}")
            if intent["type"] == "transfer":
                amt = float(intent["amount"])
                BALANCES[intent["from"]] -= amt
                BALANCES[intent["to"]] += amt
                await websocket.send(json.dumps({
                    "ok": True,
                    "type": "transfer",
                    "from": intent["from"],
                    "to": intent["to"],
                    "amount": amt
                }))
                logger.info(f"✅ processed transfer {intent['from']} → {intent['to']}, {amt} xyls")
                make_xap(intent)
        except Exception as e:
            logger.error(f"❌ WS processing error: {e}")

async def start_ws():
    async with websockets.serve(handle_ws, "127.0.0.1", 8765):
        logger.info("✅ WebSocket server active on ws://127.0.0.1:8765")
        await asyncio.Future()  # run forever

# ---------- Flask routes ----------
@app.route("/balance/<user>")
def balance(user):
    return jsonify({user: BALANCES.get(user, 0.0)})

@app.route("/memory/search")
def memory_search():
    frm = request.args.get("from")
    results = []
    for fn in os.listdir(TIMEVAULT_DIR):
        if fn.endswith(".json"):
            data = json.load(open(os.path.join(TIMEVAULT_DIR, fn)))
            if data["intent"]["from"] == frm:
                results.append(data)
    return jsonify(results)

# ---------- Start servers in parallel ----------
def run_flask():
    logger.info("HTTP read API → http://127.0.0.1:8766")
    app.run(host="127.0.0.1", port=8766, use_reloader=False)

def run_ws():
    logger.info("WS server → ws://127.0.0.1:8765")
    asyncio.run(start_ws())

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    run_ws()  # main thread handles WebSocket loop

if __name__ == "__main__":
    main()
