# ~/work/xyllidium/core/xyllencore/cap_handler.py
import os, json, hashlib, time
from datetime import datetime, timezone
from typing import Dict, Any
from pathlib import Path

# ------------------------------------------------------------------
# FIXED BASE PATH (always absolute within repo)
# ------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
BASE = REPO_ROOT / "data" / "timevault"
BASE.mkdir(parents=True, exist_ok=True)
# ------------------------------------------------------------------

def _now_iso():
    return datetime.now(timezone.utc).isoformat()

def _cap_path(cap_id: str) -> Path:
    return BASE / f"{cap_id}.json"

def _stub_path(cap_id: str) -> Path:
    return BASE / f"{cap_id}.stub.json"

def make_anchor_payload(intent: Dict[str, Any]) -> Dict[str, Any]:
    """Build CAP record with entropy hash."""
    intent_str = json.dumps(intent, sort_keys=True)
    eh = hashlib.sha256(intent_str.encode()).hexdigest()
    cap_id = f"CAP-{eh[:12]}"
    record = {
        "id": cap_id,
        "timestamp": _now_iso(),
        "intent": intent,
        "entropy_hash": eh,
        "status": "pending",
        "version": "cap.v1",
        "permanent": bool(intent.get("permanent", False)),
    }
    return record

def store_anchor(record: Dict[str, Any]) -> str:
    path = _cap_path(record["id"])
    with open(path, "w") as f:
        json.dump(record, f, indent=2)
    return str(path)

def list_caps() -> list[Dict[str, Any]]:
    """List all active CAPs (not stubs)."""
    caps = []
    for fn in os.listdir(BASE):
        if fn.startswith("CAP-") and fn.endswith(".json") and not fn.endswith(".stub.json"):
            with open(BASE / fn) as f:
                caps.append(json.load(f))
    return caps

def load_cap(cap_id: str) -> Dict[str, Any] | None:
    """Load a CAP or stub."""
    path = _cap_path(cap_id)
    if path.exists():
        with open(path) as f: return json.load(f)
    sp = _stub_path(cap_id)
    if sp.exists():
        with open(sp) as f: return json.load(f)
    return None

def write_decayed_stub(cap: Dict[str, Any]):
    """Write a decay stub for later reconstruction."""
    stub = {
        "id": cap["id"],
        "entropy_hash": cap["entropy_hash"],
        "decayed_at": _now_iso(),
        "version": cap.get("version", "cap.v1"),
        "status": "decayed",
        "permanent": False,
        "hint": {
            "type": cap["intent"].get("type"),
            "from": cap["intent"].get("from"),
            "to": cap["intent"].get("to"),
            "unit": cap["intent"].get("unit"),
            "amount": cap["intent"].get("amount"),
        }
    }
    with open(_stub_path(cap["id"]), "w") as f:
        json.dump(stub, f, indent=2)

def decay_non_permanent(ttl_seconds: int = 3600) -> int:
    """Remove non-permanent CAPs older than TTL."""
    now = time.time()
    decayed = 0
    for fn in os.listdir(BASE):
        if not fn.startswith("CAP-") or not fn.endswith(".json") or fn.endswith(".stub.json"):
            continue
        path = BASE / fn
        with open(path) as f:
            cap = json.load(f)
        if cap.get("permanent"):
            continue
        age = now - os.stat(path).st_mtime
        if age >= ttl_seconds:
            write_decayed_stub(cap)
            try: os.remove(path)
            except FileNotFoundError: pass
            decayed += 1
    return decayed

def reconstruct_from_stub(cap_id: str) -> Dict[str, Any] | None:
    """Regenerate a decayed CAP from its stub metadata."""
    sp = _stub_path(cap_id)
    if not sp.exists():
        return None
    with open(sp) as f:
        stub = json.load(f)
    intent = {
        "id": f"REGEN-{cap_id[4:]}",
        "type": stub["hint"].get("type"),
        "from": stub["hint"].get("from"),
        "to": stub["hint"].get("to"),
        "amount": stub["hint"].get("amount"),
        "unit": stub["hint"].get("unit"),
        "timestamp": _now_iso(),
        "permanent": False
    }
    regen = {
        "id": cap_id,
        "timestamp": _now_iso(),
        "reconstructed": True,
        "entropy_hash": stub["entropy_hash"],
        "status": "reconstructed",
        "version": stub.get("version", "cap.v1"),
        "intent": intent,
    }
    return regen
