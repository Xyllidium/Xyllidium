"""
Xyllira Interpreter v0.3
------------------------
Parses human-readable intents into structured JSON objects.
Supports flexible numeric + unit parsing like:
  amount: 500 xyls
  amount: xyls 500
  amount: 100
"""

import re
import json

class XylliraParser:
    def __init__(self):
        self.pattern = re.compile(
            r"intent\s+([a-zA-Z0-9_]+)\s*\{([^}]*)\}", re.MULTILINE | re.DOTALL
        )

    def parse(self, text):
        intents = []
        matches = self.pattern.findall(text)
        for name, body in matches:
            intent = {"name": name.strip(), "params": {}}
            for line in body.strip().splitlines():
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                intent["params"][key] = self._parse_value(value)
            intents.append(intent)
        return intents

    def _parse_value(self, val: str):
        """Handles numbers, units, nested dicts, and expressions."""
        val = val.strip()

        # --- Boolean & None ---
        if val.lower() in ("true", "false"):
            return val.lower() == "true"
        if val.lower() == "none":
            return None

        # --- Numeric or amount+unit ---
        # Examples:
        #   "500 xyls"
        #   "xyls 500"
        #   "100"
        #   "amount: 2000.5 xyls"
        if " " in val:
            parts = val.split()
            try:
                # case 1: number first, then unit
                amount = float(parts[0])
                unit = parts[1] if len(parts) > 1 else "xyls"
                return {"amount": amount, "unit": unit}
            except ValueError:
                # case 2: unit first, then number
                if len(parts) > 1:
                    try:
                        amount = float(parts[1])
                        unit = parts[0]
                        return {"amount": amount, "unit": unit}
                    except ValueError:
                        pass
                # fallback: raw string if unparseable
                return val

        # --- Simple float ---
        try:
            return {"amount": float(val), "unit": "xyls"}
        except ValueError:
            pass

        # --- Expression or reference ---
        if "(" in val or ")" in val or "." in val:
            return val

        return val

    def tokenize(self, text):
        tokens = re.findall(r"[A-Za-z0-9_\.\-\{\}\:\(\)\>\=<]+", text)
        return tokens


# ---------- Example Runner ----------
if __name__ == "__main__":
    code = """
    intent transfer {
        from: wallet.me
        to: wallet.bob
        amount: 500 xyls
        condition: coherence(wallet.me) > 0.7
    }

    intent upgrade_protocol {
        when: coherence(governance.field) >= 0.85
        action: evolve(core.module)
    }

    intent ai_investment {
        delegate: xyllenai
        amount: 2000 xyls
        strategy: maximize(coherence(projects))
    }

    intent convert {
        from: xyls
        to: eth
        amount: 100
    }
    """

    parser = XylliraParser()
    intents = parser.parse(code)
    print("🧩 Parsed Intent Graph:")
    print(json.dumps(intents, indent=2))

    print("\n⚙️ Executing intents sequentially...\n")
    for intent in intents:
        print(f"⚙️ Executing intent: {intent['name']}")
        for k, v in intent["params"].items():
            print(f"   ▸ {k}: {v}")
    print("\n✅ All intents processed into coherence-ready structures.")
