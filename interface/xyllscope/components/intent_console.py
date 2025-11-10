# xyllscope/components/intent_console.py
import re

def parse_intent(text: str):
    """Parse simple Xyllira-like intent lines:
       manifest(intent { energy:+0.3, awareness:0.7, target:"core" })
    """
    if not text:
        return {}

    t = text.lower()
    vals = {}

    def grab_float(key):
        m = re.search(rf"{key}\s*[:=]\s*([+\-]?\d*\.?\d+)", t)
        return float(m.group(1)) if m else None

    def grab_str(key):
        m = re.search(rf'{key}\s*[:=]\s*"?([a-z0-9_\-]+)"?', t)
        return m.group(1) if m else None

    e = grab_float("energy")
    a = grab_float("awareness")
    g = grab_str("target")

    if e is not None: vals["energy"] = e
    if a is not None: vals["awareness"] = a
    if g is not None: vals["target"] = g
    return vals
