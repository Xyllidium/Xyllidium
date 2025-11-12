# ~/work/xyllidium/core/xyllenor/temporal_decay.py
import os, json, time
from datetime import datetime, timezone, timedelta
from typing import Tuple, Dict, Any

VAULT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "timevault")

# Decay config (v4.5)
DECAY_INTERVAL_SEC = 600                 # background sweep every 10 minutes
HALF_LIFE_HOURS   = 24                   # base life for non-permanent anchors
BONUS_PER_SCORE_H = 12                   # each reinforcement adds 12 hours
MAX_BONUS_HOURS   = 24 * 7               # cap total bonus to 7 days

def _parse_ts(iso: str) -> datetime:
    # Accept both with and without timezone (we used naive UTC earlier)
    try:
        return datetime.fromisoformat(iso.replace("Z","")).replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.utcnow().replace(tzinfo=timezone.utc)

def _now() -> datetime:
    return datetime.utcnow().replace(tzinfo=timezone.utc)

def _load(p: str) -> Dict[str, Any]:
    with open(p, "r") as f:
        return json.load(f)

def _save(p: str, data: Dict[str, Any]) -> None:
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, p)

def _list_xaps() -> Tuple[str, ...]:
    if not os.path.isdir(VAULT_DIR):
        return tuple()
    return tuple(
        os.path.join(VAULT_DIR, fn)
        for fn in os.listdir(VAULT_DIR)
        if fn.startswith("XAP-") and fn.endswith(".json")
    )

def _effective_window_hours(resonance: Dict[str, Any]) -> int:
    """
    Base 24h + bonus per resonance score, capped to MAX_BONUS_HOURS.
    """
    score = int(resonance.get("score", 0))
    bonus = min(score * BONUS_PER_SCORE_H, MAX_BONUS_HOURS)
    return HALF_LIFE_HOURS + bonus

def reinforce_record(xap_id: str) -> bool:
    """
    Increase resonance score and refresh last_reinforced; returns True on success.
    """
    path = os.path.join(VAULT_DIR, f"{xap_id}.json")
    if not os.path.exists(path):
        return False
    rec = _load(path)

    # Initialize resonance struct if absent
    res = rec.get("resonance", {})
    res["score"] = int(res.get("score", 0)) + 1
    res["last_reinforced"] = _now().isoformat()

    rec["resonance"] = res
    # Optional: also renew "timestamp" to move the decay window forward
    rec["timestamp"] = _now().isoformat()

    _save(path, rec)
    return True

def run_decay_once(vault_dir: str = VAULT_DIR) -> int:
    """
    Decay pass: deletes non-permanent anchors that exceeded effective life.
    Returns count of deleted records.
    """
    deleted = 0
    now = _now()
    for path in _list_xaps():
        try:
            rec = _load(path)
            if rec.get("permanent", False) is True:
                continue
            ts = _parse_ts(rec.get("timestamp", now.isoformat()))
            res = rec.get("resonance", {})
            window_h = _effective_window_hours(res)
            if (now - ts) > timedelta(hours=window_h):
                os.remove(path)
                deleted += 1
        except Exception:
            # If a file is corrupt, attempt to remove it to avoid poisoning the vault.
            try:
                os.remove(path)
                deleted += 1
            except Exception:
                pass
    return deleted
