import asyncio
import websockets
import json
import random
import time

async def handler(websocket):
    print("[Bridge] Client connected.")
    try:
        while True:
            payload = {
                "pulse": {
                    "x": random.randint(0, 19),
                    "y": random.randint(0, 19),
                    "z": random.randint(0, 19),
                    "intensity": random.random()
                },
                "ai": f"Pulse event at {time.strftime('%H:%M:%S')}"
            }
            await websocket.send(json.dumps(payload))
            await asyncio.sleep(2)
    except websockets.ConnectionClosed:
        print("[Bridge] Client disconnected.")

async def main():
    async with websockets.serve(handler, "127.0.0.1", 8765):
        print("🛰 Bridge active on ws://127.0.0.1:8765")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
