"""
Xyllira → Xyllencore Translator (Phase 2)
-----------------------------------------
Takes parsed Xyllira intents (from interpreter.py) and converts them
into executable graph nodes for Xyllencore.

- Normalizes amounts/units
- Extracts coherence/entropy conditions into structured constraints
- Builds a minimal, causal intent graph
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import json
import re


# ---------- Utility parsing ----------

_COND_RE = re.compile(
    r"(?P<fn>coherence|entropy)\((?P<field>[A-Za-z0-9_\.\-]+)\)\s*(?P<op>>=|<=|>|<|==|!=)\s*(?P<val>[0-9]*\.?[0-9]+)"
)

def parse_condition(expr: str) -> Optional[Dict[str, Any]]:
    """
    Parses strings like:
      coherence(wallet.me) > 0.7
      entropy(core.layer) <= 0.4
    Returns a structured dict or None if it doesn't match.
    """
    if not isinstance(expr, str):
        return None
    m = _COND_RE.search(expr.replace(" ", ""))
    if not m:
        return None
    return {
        "type": m.group("fn"),          # "coherence" | "entropy"
        "field": m.group("field"),      # e.g., "wallet.me"
        "op": m.group("op"),            # >, <, >=, <=, ==, !=
        "value": float(m.group("val")), # numeric threshold
    }


def normalize_amount(value: Any) -> Tuple[float, str]:
    """
    The interpreter emits:
      {"amount": 500.0, "unit": "xyls"}
    or sometimes a raw number / string.

    Returns (amount: float, unit: str)
    """
    if isinstance(value, dict) and "amount" in value:
        amt = float(value["amount"])
        unit = str(value.get("unit", "xyls"))
        return amt, unit
    if isinstance(value, (int, float)):
        return float(value), "xyls"
    if isinstance(value, str):
        # last-resort attempt to parse "<num> xyls"
        s = value.strip().lower()
        if s.endswith("xyls"):
            num = s.replace("xyls", "").strip()
            return float(num), "xyls"
        try:
            return float(s), "xyls"
        except:
            pass
    # default fallback
    return 0.0, "xyls"


# ---------- Graph model ----------

@dataclass
class GraphNode:
    id: str
    type: str
    params: Dict[str, Any] = field(default_factory=dict)
    constraints: List[Dict[str, Any]] = field(default_factory=list)
    # Example constraint:
    # {"type": "coherence", "field": "governance.field", "op": ">=", "value": 0.85}

@dataclass
class IntentGraph:
    nodes: List[GraphNode] = field(default_factory=list)
    edges: List[Tuple[str, str]] = field(default_factory=list)  # (from_id, to_id)

    def add_node(self, node: GraphNode):
        self.nodes.append(node)

    def add_edge(self, from_id: str, to_id: str):
        self.edges.append((from_id, to_id))

    def to_json(self) -> str:
        return json.dumps(
            {
                "nodes": [vars(n) for n in self.nodes],
                "edges": self.edges,
            },
            indent=2
        )


# ---------- Translator ----------

class Translator:
    """
    Converts Xyllira Parser output:
      [{"name": "...", "params": {...}}, ...]
    into an IntentGraph consumable by Xyllencore.
    """

    def __init__(self):
        self.counter = 0

    def _next_id(self, base: str) -> str:
        self.counter += 1
        return f"{base}-{self.counter}"

    def translate(self, intents: List[Dict[str, Any]]) -> IntentGraph:
        graph = IntentGraph()

        for intent in intents:
            name = intent.get("name", "intent")
            params: Dict[str, Any] = intent.get("params", {})

            # Determine node type (semantic)
            node_type = self._classify_node(name, params)

            # Extract constraints (coherence/entropy)
            constraints = []
            for key in ("condition", "when", "confirmation"):
                if key in params:
                    parsed = parse_condition(params[key])
                    if parsed:
                        constraints.append(parsed)

            node_id = self._next_id(node_type)
            node_params = self._normalize_params(node_type, params)

            node = GraphNode(
                id=node_id,
                type=node_type,
                params=node_params,
                constraints=constraints,
            )
            graph.add_node(node)

            # Minimal causal edges (optional):
            # If there are explicit references to preceding intent names, add edges here.
            # (We can extend later with 'after:<intent-name>' syntax.)
            # For now, no implicit edges.

        return graph

    # ---- helpers ----

    def _classify_node(self, name: str, params: Dict[str, Any]) -> str:
        n = name.lower()
        if n in ("transfer", "send_funds", "send", "pay"):
            return "Transfer"
        if n in ("stake", "staking"):
            return "Stake"
        if n in ("convert", "swap", "exchange"):
            return "Convert"
        if n in ("upgrade_protocol", "protocol_upgrade"):
            return "Evolve"
        if n in ("ai_investment", "auto_invest"):
            return "AIInvest"
        if n in ("build_exchange", "build_defi", "build"):
            return "Build"
        # fallback: infer by presence of keys
        if "to" in params and "from" in params and "amount" in params:
            return "Transfer"
        if "duration" in params and "amount" in params:
            return "Stake"
        if "action" in params and str(params["action"]).startswith("evolve("):
            return "Evolve"
        return "Generic"

    def _normalize_params(self, node_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}

        # Common fields
        if "from" in params:
            out["from"] = params["from"]
        if "to" in params:
            out["to"] = params["to"]
        if "delegate" in params:
            out["delegate"] = params["delegate"]
        if "strategy" in params:
            out["strategy"] = params["strategy"]
        if "pairs" in params:
            out["pairs"] = params["pairs"]
        if "deploy_on" in params:
            out["deploy_on"] = params["deploy_on"]
        if "mode" in params:
            out["mode"] = params["mode"]
        if "duration" in params:
            out["duration"] = params["duration"]
        if "method" in params:
            out["method"] = params["method"]
        if "name" in params:
            out["name"] = params["name"]

        # Amount normalization
        if "amount" in params:
            amt, unit = normalize_amount(params["amount"])
            out["amount"] = amt
            out["unit"] = unit

        # Action parse (e.g., evolve(core.module))
        if "action" in params and isinstance(params["action"], str):
            action = params["action"].strip()
            if action.startswith("evolve(") and action.endswith(")"):
                target = action[len("evolve("):-1]
                out["evolve_target"] = target

        # Specialization per node type (optional extensions later)
        # e.g., Convert should have "from_token" / "to_token"
        if node_type == "Convert":
            # Attempt to parse convert pairs: from: xyls, to: eth, amount: X
            from_tok = params.get("from", None)
            to_tok = params.get("to", None)
            if from_tok:
                out["from_token"] = from_tok
            if to_tok:
                out["to_token"] = to_tok

        return out


# ---------- Example runner (optional) ----------

if __name__ == "__main__":
    # Example: expect to receive from interpreter output
    sample_intents = [
        {
            "name": "transfer",
            "params": {
                "from": "wallet.me",
                "to": "wallet.bob",
                "amount": {"amount": 500.0, "unit": "xyls"},
                "condition": "coherence(wallet.me) > 0.7"
            }
        },
        {
            "name": "upgrade_protocol",
            "params": {
                "when": "coherence(governance.field) >= 0.85",
                "action": "evolve(core.module)"
            }
        },
        {
            "name": "ai_investment",
            "params": {
                "delegate": "xyllenai",
                "amount": {"amount": 2000.0, "unit": "xyls"},
                "strategy": "maximize(coherence(projects))"
            }
        },
        {
            "name": "convert",
            "params": {
                "from": "xyls",
                "to": "eth",
                "amount": 100
            }
        },
    ]

    graph = Translator().translate(sample_intents)
    print("🧠 Intent Graph → Xyllencore Executable Nodes")
    print(graph.to_json())
