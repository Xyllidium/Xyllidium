# ~/work/xyllidium/core/xyllenor/timevault_bridge.py
from __future__ import annotations
import os, json, hashlib
from typing import Dict, Any

BASE_DIR = os.path.expanduser("~/work/xyllidium")
VAULT_DIR = os.path.join(BASE_DIR, "data", "timevault")
INDEX_PATH = os.path.join(VAULT_DIR, "index.json")

os.makedirs(VAULT_DIR, exist_ok=True)

def _read_json(p: str) -> Dict[str, Any]:
    if not os.path.exists(p):
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def _write_json(p: str, obj: Dict[str, Any]) -> None:
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    os.replace(tmp, p)

def store_lattice_snapshot(envelope: Dict[str, Any]) -> str:
    """Alias: persists CAP envelope file (already done by cap_handler in executor)."""
    cap_id = envelope["id"]
    path = os.path.join(VAULT_DIR, f"{cap_id}.json")
    _write_json(path, envelope)
    return path

def load_record(cap_id: str) -> Dict[str, Any] | None:
    path = os.path.join(VAULT_DIR, f"{cap_id}.json")
    if not os.path.exists(path):
        return None
    return _read_json(path)

def read_index() -> Dict[str, Any]:
    if not os.path.exists(INDEX_PATH):
        return {"version": "tv.index.v1", "records": []}
    return _read_json(INDEX_PATH)

def search_by_entropy(entropy_hash: str) -> Dict[str, Any] | None:
    idx = read_index()
    for r in reversed(idx["records"]):
        if r["entropy_hash"] == entropy_hash:
            return r
    return None

def reconstruct_from_entropy(entropy_hash: str) -> Dict[str, Any] | None:
    """
    Deterministic regeneration approach for volatile entries.
    Strategy (v1):
      - Find index record by entropy hash
      - If CAP file exists, return exact anchor (preferred)
      - If missing (decayed), regenerate intent envelope (lossless for v1):
          We hash the canonical intent dict to produce a deterministic TXN id,
          then rebuild a CAP-like envelope with the same entropy_hash.
    """
    rec = search_by_entropy(entropy_hash)
    if not rec:
        return None

    # If anchor exists, prefer it (exact)
    cap_path = os.path.join(VAULT_DIR, f"{rec['cap_id']}.json")
    if os.path.exists(cap_path):
        return _read_json(cap_path)

    # Regenerate deterministically (volatile case)
    intent_core = {
        "type": rec.get("type"),
        "from": rec.get("from"),
        "to": rec.get("to"),
        "amount": rec.get("amount"),
        "unit": rec.get("unit"),
        "memory_mode": rec.get("memory_mode", "volatile"),
    }
    # Make a consistent TXN id from the entropy hash subset
    txn_id = "TXN-" + hashlib.sha1(entropy_hash.encode()).hexdigest()[:8]
    intent_core["id"] = txn_id
    # timestamp is not stored for volatile regen; include an approx field
    envelope = {
        "id": rec["cap_id"],
        "timestamp": rec["ts"],         # recorded anchor time from index
        "intent": intent_core,
        "entropy_hash": entropy_hash,   # exact match
        "status": "reconstructed",
        "version": "cap.v1.replay",
    }
    return envelope
