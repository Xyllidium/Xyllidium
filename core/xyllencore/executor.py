# ~/work/xyllidium/core/xyllencore/executor.py
import os, sys, time, json, hashlib, datetime, logging, socket
import argparse, requests, asyncio
import websockets

from core.xyllenor.xap_handler import make_xap

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

WS_URI = "ws://127.0.0.1:8765"
HTTP_API = "http://127.0.0.1:8766"

def generate_txn_id(intent):
    data = f"{intent['from']}{intent['to']}{intent['timestamp']}".encode()
    digest = hashlib.sha256(data).hexdigest()[:8].upper()
    return f"XYLL-TXN-{digest}"

def wait_for_ws(host="127.0.0.1", port=8765, timeout=8):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.4)
    return False

async def send_ws(intent):
    async with websockets.connect(WS_URI, max_size=2**23) as ws:
        await ws.send(json.dumps(intent))
        ack = await ws.recv()
        return ack

def try_ws(intent):
    try:
        return asyncio.get_event_loop().run_until_complete(send_ws(intent))
    except Exception as e:
        log.error(f"⚠️ WebSocket send failed: {e}")
        return None

def try_http_fallback(intent):
    try:
        r = requests.post(f"{HTTP_API}/apply_intent", json=intent, timeout=3)
        if r.ok and r.json().get("ok"):
            return {"ok": True, "via": "http"}
        return {"ok": False, "via": "http", "error": r.text}
    except Exception as e:
        return {"ok": False, "via": "http", "error": str(e)}

def build_intent(sender, receiver, amount, unit, permanent):
    ts = datetime.datetime.utcnow().isoformat(timespec="seconds")
    base = {
        "type": "transfer",
        "from": sender,
        "to": receiver,
        "amount": float(amount),
        "unit": unit,
        "timestamp": ts,
        "permanent": permanent,
    }
    base["id"] = generate_txn_id({"from": sender, "to": receiver, "timestamp": ts})
    return base

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="sender", default="alice")
    ap.add_argument("--to", dest="receiver", default="bob")
    ap.add_argument("--amount", type=float, default=500.0)
    ap.add_argument("--unit", default="xyls")
    ap.add_argument("--permanent", action="store_true", default=True)
    args = ap.parse_args()

    intent = build_intent(args.sender, args.receiver, args.amount, args.unit, args.permanent)
    log.info(f"⚙️ Executing intent: {args.sender} → {args.receiver}, {args.amount} {args.unit}")

    delivered = False
    if wait_for_ws():
        ack = try_ws(intent)
        if ack:
            log.info(f"🔗 Acknowledged by equilibrium engine: {ack}")
            delivered = True
            log.info("✅ Intent transmitted successfully.")
    else:
        log.warning("❌ WS not ready; switching to HTTP fallback.")

    if not delivered:
        # Try HTTP fallback to still mutate balances
        http_res = try_http_fallback(intent)
        if http_res.get("ok"):
            delivered = True
            log.info("✅ Intent applied via HTTP fallback.")

    # Always anchor
    log.info("🧩 Anchoring permanent transaction via XAP...")
    xap = make_xap(intent)
    # You likely already print the XAP record inside make_xap or after; repeating here for clarity:
    print(json.dumps(xap, indent=2, ensure_ascii=False))

    # Show balances
    try:
        a = requests.get(f"{HTTP_API}/balance/{args.sender}", timeout=2).json()["balance"]
        b = requests.get(f"{HTTP_API}/balance/{args.receiver}", timeout=2).json()["balance"]
        print("\n💰 Balances:", json.dumps({args.sender: a, args.receiver: b}, indent=2))
    except Exception as e:
        log.warning(f"⚠️ Could not fetch balances: {e}")

if __name__ == "__main__":
    main()
