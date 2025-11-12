# ===============================================================
# 🧠 Xyllidium v4.4 — Temporal Memory Decay Engine
# Purpose: Non-permanent XAPs slowly decay (deleted) over time to
# simulate entropy and neural forgetting in the Xyllidium organism.
# ===============================================================

import os
import json
import datetime
import logging

# How long before a non-permanent XAP is decayed (hours)
DECAY_HOURS = 24  

logger = logging.getLogger("TemporalDecay")

def load_xap(file_path: str):
    """Safely load a JSON XAP anchor."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"⚠️ Failed to read {file_path}: {e}")
        return None

def should_decay(xap: dict):
    """Determine whether this XAP should decay."""
    if xap.get("permanent", False):
        return False
    try:
        ts = datetime.datetime.fromisoformat(xap["timestamp"])
        age_hours = (datetime.datetime.utcnow() - ts).total_seconds() / 3600
        return age_hours > DECAY_HOURS
    except Exception:
        return False

def run_decay(timevault_dir="data/timevault"):
    """Scan the TimeVault and decay old non-permanent anchors."""
    decayed = 0
    if not os.path.exists(timevault_dir):
        logger.info(f"🫧 No TimeVault found at {timevault_dir}")
        return 0

    for file in os.listdir(timevault_dir):
        if not file.endswith(".json"):
            continue
        path = os.path.join(timevault_dir, file)
        xap = load_xap(path)
        if xap and should_decay(xap):
            try:
                os.remove(path)
                decayed += 1
            except Exception as e:
                logger.warning(f"❌ Could not remove {file}: {e}")
    logger.info(f"🫧 decayed {decayed} non-permanent XAP(s)")
    return decayed
