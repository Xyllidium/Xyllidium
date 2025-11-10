"""
Xyllenor Core – Equilibrium Engine v1.0
Part of Xyllidium Coherence Organism
Maintains systemic balance between energy, coherence, and entropy.
"""

import json
import time
import random
import asyncio
import websockets
from statistics import mean, pstdev

class Xyllenor:
    def __init__(self):
        self.metrics = {
            "entropy": 0.0,
            "balance_index": 1.0,
            "flux_rate": 0.0,
            "coherence_mean": 0.0,
            "timestamp": time.time()
        }
        self.history = []
        self.websocket_uri = "ws://127.0.0.1:8765"  # Same bridge as Xyllscope
        print("🧠 Xyllenor equilibrium engine initialized...")

    # --- Simulated input from Xyllencore ---
    def ingest_state(self, state):
        # Expecting wallet balances, coherence data, etc.
        energy_levels = [v for v in state["wallets"].values()]
        entropy = pstdev(energy_levels) / (mean(energy_levels) + 1e-9)
        self.metrics["entropy"] = round(entropy, 3)
        self.metrics["coherence_mean"] = round(mean(energy_levels), 3)
        self.metrics["balance_index"] = round(1.0 - min(entropy, 1.0), 3)
        self.metrics["flux_rate"] = round(random.uniform(0.01, 0.15), 3)
        self.metrics["timestamp"] = time.time()
        self.history.append(self.metrics.copy())

    async def broadcast(self):
        async with websockets.connect(self.websocket_uri) as ws:
            await ws.send(json.dumps({"type": "xyllenor_metrics", "data": self.metrics}))
            print("📡 Sent equilibrium update:", self.metrics)

    def evaluate_equilibrium(self, state):
        self.ingest_state(state)
        return self.metrics

    async def run(self):
        while True:
            # Simulate periodic update
            mock_state = {
                "wallets": {
                    "wallet.me": random.uniform(5000, 10000),
                    "wallet.bob": random.uniform(2000, 5000)
                }
            }
            metrics = self.evaluate_equilibrium(mock_state)
            await self.broadcast()
            await asyncio.sleep(3)


if __name__ == "__main__":
    engine = Xyllenor()
    asyncio.run(engine.run())
