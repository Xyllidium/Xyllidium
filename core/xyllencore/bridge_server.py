# ============================================================
# Xyllencore → Xyllscope Bridge Server
# ============================================================
# Streams real-time execution data over WebSockets.
# Run first:  python ~/work/xyllidium/core/xyllencore/bridge_server.py
# ============================================================

import asyncio
import websockets
import json

connected_clients = set()

async def handler(ws):
    """Relay messages between all connected clients."""
    connected_clients.add(ws)
    try:
        async for msg in ws:
            # Broadcast to all connected listeners except sender
            for c in connected_clients:
                if c != ws:
                    await c.send(msg)
    finally:
        connected_clients.remove(ws)

async def main():
    async with websockets.serve(handler, "127.0.0.1", 8765):
        print("[Bridge] 🌐 Xyllscope live feed active on ws://127.0.0.1:8765")
        await asyncio.Future()  # Keeps running forever

if __name__ == "__main__":
    asyncio.run(main())
