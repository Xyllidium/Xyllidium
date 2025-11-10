import json, asyncio, websockets, random, time, math
from datetime import datetime

# ============================================================
# 🧠 Xyllencore Executor v2.9 – Coherence Execution Engine
# Processes intent graph nodes, applies Coherence Field logic,
# propagates energy states, and streams updates to Xyllscope.
# ============================================================

GRAPH_PATH = "/home/xyllidium/work/xyllidium/core/xyllira/intent_graph.json"
WS_URI = "ws://127.0.0.1:8765"

# --- Internal Coherence State Memory ---
state = {
    "wallets": {"wallet.me": 10000.0, "wallet.bob": 2000.0},
    "modules": {"core.module": 1.0},
    "ai": {"xyllenai": {"portfolio": 0.0}},
    "field_energy": 1.0,
    "coherence": 0.75,
    "tick": 0,
}


# ============================================================
# 🧩 Core Utility Functions
# ============================================================

def load_graph():
    print("📡 Loading intent graph…")
    with open(GRAPH_PATH) as f:
        data = json.load(f)
    print(f"✅ Loaded {len(data['nodes'])} nodes.")
    return data["nodes"]


def coherence_function():
    """Simulates coherence evolution over time."""
    base = state["coherence"]
    delta = (random.random() - 0.5) * 0.02
    state["coherence"] = max(0.0, min(1.0, base + delta))
    return state["coherence"]


def field_diffusion():
    """Diffuse energy field slowly to simulate ambient resonance."""
    f = state["field_energy"]
    drift = math.sin(state["tick"] / 10) * 0.01
    f = max(0.5, min(1.5, f + drift))
    state["field_energy"] = f


# ============================================================
# ⚙️ Node Execution Logic
# ============================================================

async def execute_node(ws, node):
    ntype = node["type"]
    params = node.get("params", {})

    if ntype == "Transfer":
        src, dst = params["from"], params["to"]
        amt = params["amount"]
        unit = params.get("unit", "xyls")
        state["wallets"][src] -= amt
        state["wallets"][dst] += amt
        msg = f"Transferred {amt} {unit} from {src} → {dst}"

    elif ntype == "Evolve":
        module = params.get("evolve_target", "core.module")
        coherence_function()
        msg = f"Evolution check on {module} | Coherence: {state['coherence']:.3f}"

    elif ntype == "AIInvest":
        delegate = params.get("delegate", "xyllenai")
        amt = params.get("amount", 0)
        growth = round(amt * random.uniform(0.05, 0.15), 2)
        state["ai"][delegate]["portfolio"] += growth
        msg = f"{delegate} investing {amt} xyls → +{growth} growth (coherence {state['coherence']:.3f})"

    elif ntype == "Convert":
        amt = params.get("amount", 0)
        rate = 1.04
        converted = round(amt * rate, 3)
        msg = f"Converted {amt} xyls → {converted} eth (rate {rate})"

    else:
        msg = f"Unknown node type: {ntype}"

    print(f"⚙️ Executing Node: {ntype}\n   ▸ {msg}\n------------------------------------------------------------")
    await send_state(ws, msg)


# ============================================================
# 🌐 WebSocket Bridge Communication
# ============================================================

async def send_state(ws, msg):
    """Send live updates to Xyllscope feed."""
    payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "message": msg,
        "state": state,
    }
    try:
        await ws.send(json.dumps(payload))
    except Exception as e:
        print(f"[Bridge] ⚠️ Send failed: {e}")


# ============================================================
# 🔁 Execution Loop
# ============================================================

async def main():
    try:
        async with websockets.connect(WS_URI) as ws:
            print("[Bridge] Connected to Xyllscope feed.")
            nodes = load_graph()

            for n in nodes:
                state["tick"] += 1
                coherence_function()
                field_diffusion()
                await execute_node(ws, n)
                await asyncio.sleep(1.2)  # simulate time between executions

            print("✅ All executable nodes processed successfully.")
            await send_state(ws, "✅ Execution completed.")
    except ConnectionRefusedError:
        print("[Bridge] Connection failed – ensure bridge_server.py is running.")
    except Exception as e:
        print(f"💥 Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
