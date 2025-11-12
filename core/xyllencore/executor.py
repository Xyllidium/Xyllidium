# ~/work/xyllidium/core/xyllencore/executor.py
import asyncio, json, hashlib, datetime, websockets, requests, logging, os
from core.xyllenor.xap_handler import make_xap

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("xyllencore")

WS_URI = "ws://127.0.0.1:8765"
HTTP_API = "http://127.0.0.1:8766"
TIMEVAULT_DIR = "data/timevault"

def generate_txn_id(intent):
    data = f"{intent['from']}{intent['to']}{intent['timestamp']}".encode()
    digest = hashlib.sha256(data).hexdigest()[:8].upper()
    return f"XYLL-TXN-{digest}"

def make_intent(sender, receiver, amount, unit="xyls", permanent=True):
    ts = datetime.datetime.utcnow().isoformat()
    return {
        "id": generate_txn_id({"from": sender, "to": receiver, "timestamp": ts}),
        "type": "transfer",
        "from": sender,
        "to": receiver,
        "amount": amount,
        "unit": unit,
        "timestamp": ts,
        "permanent": permanent,
    }

async def send_intent(intent):
    try:
        async with websockets.connect(WS_URI) as ws:
            await ws.send(json.dumps(intent))
            response = await ws.recv()
            logger.info(f"🔗 Acknowledged by equilibrium engine: {response}")
            return True
    except Exception as e:
        logger.error(f"⚠️ WebSocket send failed: {e}")
        return False

def anchor_transaction(intent):
    logger.info("🧩 Anchoring permanent transaction via XAP...")
    xap = make_xap(intent)
    logger.info(f"✅ Anchored id={xap['id']}")
    return xap

def verify_anchor(xap):
    print("\n🔍 Verifying XAP anchor record:")
    print(json.dumps(xap, indent=2))

def get_balances():
    try:
        a = requests.get(f"{HTTP_API}/balance/alice").json()
        b = requests.get(f"{HTTP_API}/balance/bob").json()
        print("\n💰 Balances:", json.dumps({**a, **b}, indent=2))
    except Exception as e:
        logger.warning(f"⚠️ Could not fetch balances: {e}")

async def main():
    sender, receiver, amount = "alice", "bob", 500.0
    intent = make_intent(sender, receiver, amount, "xyls", True)
    logger.info(f"⚙️ Executing intent: {sender} → {receiver}, {amount} xyls")

    success = await send_intent(intent)
    if not success:
        logger.warning("❌ Could not deliver intent live. Anchoring only.")

    xap = anchor_transaction(intent)
    verify_anchor(xap)
    get_balances()

if __name__ == "__main__":
    asyncio.run(main())
