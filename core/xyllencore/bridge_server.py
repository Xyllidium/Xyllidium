#!/usr/bin/env python3
# v3.5.5 Bridge — WebSocket hub for Xyllidium
import asyncio, json, websockets
from websockets.server import WebSocketServerProtocol

CLIENTS:set[WebSocketServerProtocol] = set()

async def broadcast(message: str, sender: WebSocketServerProtocol|None=None):
    dead = []
    for ws in CLIENTS:
        if ws is sender:  # echo to everyone (including sender) is fine;
            pass          # flip to `continue` if you don’t want self-echo
        try:
            await ws.send(message)
        except Exception:
            dead.append(ws)
    for d in dead:
        CLIENTS.discard(d)

async def handler(ws: WebSocketServerProtocol):
    CLIENTS.add(ws)
    try:
        # Let late joiners know the hub is alive
        await ws.send(json.dumps({"type":"bridge","status":"ready"}))
        async for msg in ws:
            # We relay any well-formed JSON payload to all peers
            try:
                json.loads(msg)  # sanity check
                await broadcast(msg, sender=ws)
            except Exception:
                # non-JSON: wrap it
                await broadcast(json.dumps({"type":"raw","data":msg}), sender=ws)
    finally:
        CLIENTS.discard(ws)

async def main():
    print("🌉 Bridge server @ ws://127.0.0.1:8765")
    async with websockets.serve(handler, "127.0.0.1", 8765, max_size=2**23):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
