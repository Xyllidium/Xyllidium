# ~/work/xyllidium/core/keys/keygen.py
import os, base64, hashlib
from nacl.signing import SigningKey

os.makedirs("core/keys", exist_ok=True)

priv = SigningKey.generate()
pub = priv.verify_key

priv_bytes = priv.encode()
pub_bytes = pub.encode()

priv_b64 = base64.b16encode(priv_bytes).decode()
pub_b64 = base64.b16encode(pub_bytes).decode()

priv_key = f"XYLL-PRIV-{priv_b64}"
pub_key = f"XYLL-PUB-{pub_b64}"

# Node ID = first 6 hex chars of SHA256(pub_key)
node_id = hashlib.sha256(pub_bytes).hexdigest()[:6].upper()
node_id_str = f"NODE-{node_id}"

with open("core/keys/node_private.key", "w") as f: f.write(priv_key)
with open("core/keys/node_public.key", "w") as f: f.write(pub_key)
with open("core/keys/node_id.txt", "w") as f: f.write(node_id_str)

print("✅ Xyllidium keypair generated")
print(f"🔐 Private Key: {priv_key[:60]}...")
print(f"🔓 Public Key: {pub_key[:60]}...")
print(f"🧠 Node ID: {node_id_str}")
