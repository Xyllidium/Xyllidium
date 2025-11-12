# ~/work/xyllidium/core/xyllenor/timevault_bridge.py
import os
import json
import logging
from datetime import datetime

log = logging.getLogger("timevault")

# Base vault directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "../../data/timevault")
os.makedirs(DATA_DIR, exist_ok=True)


def list_timevault_files():
    """Return list of all XAP and CAP files in the TimeVault directory."""
    try:
        return [f for f in os.listdir(DATA_DIR) if f.endswith(".json") or f.endswith(".stub.json")]
    except FileNotFoundError:
        os.makedirs(DATA_DIR, exist_ok=True)
        return []


def load_xap(filename):
    """Load a single XAP or CAP file from TimeVault."""
    path = os.path.join(DATA_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.warning(f"⚠️ Failed to load {filename}: {e}")
        return None


def store_xap(xap):
    """Store a new XAP record in the TimeVault."""
    if not isinstance(xap, dict):
        raise ValueError("XAP must be a dict")

    xap_id = xap.get("id") or f"XAP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    path = os.path.join(DATA_DIR, f"{xap_id}.json")

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(xap, f, indent=2)
        log.info(f"📦 Stored XAP snapshot → {path}")
    except Exception as e:
        log.error(f"❌ Failed to store XAP: {e}")
        raise
