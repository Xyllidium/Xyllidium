# ~/work/xyllidium/core/xyllenor/xap_handler.py
import os, json, hashlib, base64, datetime
from nacl.signing import SigningKey
from nacl.encoding import HexEncoder

KEY_DIR = "core/keys"
TIMEVAULT_DIR = "data/timevault"
os.makedirs(TIMEVAULT_DIR, exist_ok=True)

def load_keys():
    priv = open(f"{KEY_DIR}/node_private.key").read().strip().split("XYLL-PRIV-")[1]
    pub = open(f"{KEY_DIR}/node_public.key").read().strip().split("XYLL-PUB-")[1]
    nid = open(f"{KEY_DIR}/node_id.txt").read().strip()
    return priv, pub, nid

def make_xap(intent):
    priv_hex, pub_hex, node_id = load_keys()
    priv_key = SigningKey(bytes.fromhex(priv_hex))
    pub_key = f"XYLL-PUB-{pub_hex}"

    # Compute entropy hash
    payload = json.dumps(intent, sort_keys=True).encode()
    entropy = hashlib.sha256(payload).hexdigest().upper()
    entropy_prefixed = f"XYLL-ENTR-{entropy}"

    # XAP ID = first 12 chars of entropy
    xap_id = f"XAP-{entropy[:12]}"

    # Signature
    signature = priv_key.sign(payload, encoder=HexEncoder).signature.decode()
    signature_prefixed = f"XYLL-SIG-{signature.upper()}"

    record = {
        "id": xap_id,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "intent": intent,
        "entropy_hash": entropy_prefixed,
        "status": "anchored",
        "version": "xap.v1",
        "permanent": True,
        "signer": node_id,
        "public_key": pub_key,
        "signature": signature_prefixed,
    }

    path = os.path.join(TIMEVAULT_DIR, f"{xap_id}.json")
    with open(path, "w") as f: json.dump(record, f, indent=2)
    print(f"📦 Stored XAP snapshot → {path}")
    return record
