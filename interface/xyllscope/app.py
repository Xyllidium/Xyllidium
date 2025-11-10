#!/usr/bin/env python3
# Xyllscope v3.1 – Energy Pulses + Resonance + Xyllenai Awareness Stream
# Runs standalone (mock events) or connected to ws://127.0.0.1:8765

import json
import math
import random
import threading
import asyncio
from collections import deque
from datetime import datetime

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import dash
from dash import dcc, html, Input, Output, State, no_update
import dash_bootstrap_components as dbc

# -----------------------------
# Config
# -----------------------------
GRID = 10                 # 10x10x10 volume
TICK_MS = 200             # refresh interval
PULSE_TTL = 20            # ticks a pulse remains visible
PULSE_DECAY = 0.88        # intensity decay per tick
DIFFUSION_RATE = 0.10     # energy diffusion between neighbors per tick
RESONANCE_SPEED = 0.06    # breathing speed
WS_URL = "ws://127.0.0.1:8765"

# -----------------------------
# Global State (in-memory)
# -----------------------------
state = {
    "energies": np.random.rand(GRID, GRID, GRID) * 0.02 + 0.04,  # calm baseline ~0.05
    "pulses": [],                         # list of dicts {x,y,z,intensity,ttl}
    "phase": 0.0,                         # resonance breathing phase
    "tick": 0,
    "history_coh": deque(maxlen=500),     # temporal coherence history
    "ai_stream": deque(maxlen=200),       # xyllenai awareness log lines (strings)
    "toggles": {"diffusion": True, "resonance": True, "trail": True},
    "queue": asyncio.Queue(),             # inbound event queue (ws or mock)
    "ws_connected": False,
}

# -----------------------------
# Utility: coherence index ~ inverse variance proxy
# -----------------------------
def coherence_index(field: np.ndarray) -> float:
    # Normalize variance into 0..1 (lower variance => higher coherence)
    v = np.var(field)
    # clamp and invert; tuned for small field variances ~1e-3 to 1e-2
    norm = max(0.0, 1.0 - min(1.0, v * 150.0))
    return float(norm)

# -----------------------------
# Visual Builders
# -----------------------------
def build_volume_figure(field: np.ndarray, pulses):
    # Apply resonance “breathing” overlay (for display only)
    disp = field.copy()
    if state["toggles"]["resonance"]:
        # sinusoidal modulation based on distance from center
        cx = cy = cz = (GRID - 1) / 2.0
        zz, yy, xx = np.indices((GRID, GRID, GRID))
        r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2 + (zz - cz) ** 2)
        disp += 0.015 * np.sin(0.6 * r + state["phase"])

    # Add pulse blobs (for display)
    for p in pulses:
        # gaussian bump around pulse coordinate
        x0, y0, z0 = p["x"], p["y"], p["z"]
        sig = 1.1 + (1.8 * (p["ttl"] / PULSE_TTL))
        zz, yy, xx = np.indices((GRID, GRID, GRID))
        g = np.exp(-((xx - x0) ** 2 + (yy - y0) ** 2 + (zz - z0) ** 2) / (2 * sig ** 2))
        disp += p["intensity"] * g

    vmin = float(np.min(disp))
    vmax = float(np.max(disp))

    fig = go.Figure(
        data=go.Volume(
            x=np.repeat(np.arange(GRID), GRID * GRID),
            y=np.tile(np.repeat(np.arange(GRID), GRID), GRID),
            z=np.tile(np.arange(GRID), GRID * GRID),
            value=disp.flatten(),
            opacity=0.15,      # semi transparent
            surface_count=15,  # number of isosurfaces
            isomin=vmin,
            isomax=vmax,
            colorbar=dict(title="Energy"),
        )
    )
    fig.update_layout(
        paper_bgcolor="#000", plot_bgcolor="#000",
        margin=dict(l=0, r=0, t=0, b=0),
        scene=dict(
            xaxis=dict(color="#00e5ff", gridcolor="#444"),
            yaxis=dict(color="#00e5ff", gridcolor="#444"),
            zaxis=dict(color="#00e5ff", gridcolor="#444"),
        ),
    )
    return fig

def build_heatmap(field_xy: np.ndarray):
    # 2D slice (z mid) to click & inject
    zmid = GRID // 2
    slice2d = field_xy[:, :, zmid]
    fig = go.Figure(data=go.Heatmap(z=slice2d.T, colorbar=dict(title="Energy")))
    fig.update_layout(
        paper_bgcolor="#000", plot_bgcolor="#000",
        margin=dict(l=40, r=10, t=10, b=40),
        xaxis=dict(color="#00e5ff"),
        yaxis=dict(color="#00e5ff"),
    )
    return fig

def build_temporal(history):
    y = list(history) if history else [coherence_index(state["energies"])]
    x = list(range(len(y)))
    fig = go.Figure(
        data=go.Scatter(x=x, y=y, mode="lines+markers")
    )
    fig.update_layout(
        paper_bgcolor="#000", plot_bgcolor="#000",
        margin=dict(l=40, r=10, t=10, b=40),
        xaxis=dict(color="#00e5ff"),
        yaxis=dict(color="#00e5ff", range=[0, 1]),
        title=None,
    )
    return fig

# -----------------------------
# Physics-ish updates
# -----------------------------
def step_diffusion(field: np.ndarray, rate=DIFFUSION_RATE):
    """Average with 6-neighborhood (laplacian-like)."""
    f = field
    out = f.copy()
    # neighbors with padding
    def sh(a, axis, dir):
        return np.roll(a, dir, axis=axis)

    avg_neigh = (
        sh(f, 0, 1) + sh(f, 0, -1) +
        sh(f, 1, 1) + sh(f, 1, -1) +
        sh(f, 2, 1) + sh(f, 2, -1)
    ) / 6.0
    out += rate * (avg_neigh - f)
    return out

def apply_pulses(field: np.ndarray):
    # apply & decay pulses
    new_pulses = []
    for p in state["pulses"]:
        # inject a little energy at the pulse center each tick
        x, y, z = p["x"], p["y"], p["z"]
        field[x, y, z] += 0.01 * p["intensity"]  # deposit
        # ripple to neighbors (simple)
        for dx, dy, dz in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
            xi, yi, zi = x+dx, y+dy, z+dz
            if 0 <= xi < GRID and 0 <= yi < GRID and 0 <= zi < GRID:
                field[xi, yi, zi] += 0.006 * p["intensity"]

        # decay & ttl
        p["intensity"] *= PULSE_DECAY
        p["ttl"] -= 1
        if p["ttl"] > 0:
            new_pulses.append(p)
    state["pulses"] = new_pulses
    return field

# -----------------------------
# WebSocket Listener (or mock)
# -----------------------------
async def listen_ws():
    import websockets
    try:
        async with websockets.connect(WS_URL) as ws:
            state["ws_connected"] = True
            while True:
                msg = await ws.recv()
                await state["queue"].put(msg)
    except Exception:
        state["ws_connected"] = False
        # Fallback: generate mock events
        while True:
            await asyncio.sleep(1.2)
            evt = random.choice(["pulse", "ai"])
            if evt == "pulse":
                msg = json.dumps({
                    "type": "pulse",
                    "x": random.randrange(GRID),
                    "y": random.randrange(GRID),
                    "z": random.randrange(GRID),
                    "intensity": round(random.uniform(0.8, 1.5), 3),
                    "source": "mock"
                })
            else:
                msg = json.dumps({
                    "type": "ai_log",
                    "text": random.choice([
                        "xyllenai exploring solver market…",
                        "rebalancing portfolio toward high-coherence projects",
                        "predictive equilibrium shift detected",
                        "delegated execution optimized"
                    ])
                })
            await state["queue"].put(msg)

def start_ws_thread():
    def runner():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(listen_ws())
    t = threading.Thread(target=runner, daemon=True)
    t.start()

# -----------------------------
# Dash App
# -----------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
app.title = "Xyllscope v3.1"

controls = dbc.Row(
    [
        dbc.Col(dbc.Checklist(
            options=[{"label": " Diffusion", "value": "diffusion"}],
            value=["diffusion"], id="toggle-diffusion", switch=True
        ), width="auto"),
        dbc.Col(dbc.Checklist(
            options=[{"label": " Resonance", "value": "resonance"}],
            value=["resonance"], id="toggle-resonance", switch=True
        ), width="auto"),
        dbc.Col(dbc.Checklist(
            options=[{"label": " Pulse Trails", "value": "trail"}],
            value=["trail"], id="toggle-trail", switch=True
        ), width="auto"),
        dbc.Col(dbc.Button("Inject Pulse ⚡", id="inject-btn", color="info", outline=True), width="auto"),
    ],
    className="g-3"
)

app.layout = dbc.Container(
    [
        html.Br(),
        html.H2("🧠 Xyllscope – Live Coherence Monitor (v3.1)", className="text-info"),
        html.Div(id="ws-status", className="text-secondary", style={"fontSize": "12px"}),
        html.Hr(),
        controls,
        html.Br(),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="volume", style={"height": "520px"}), md=7),
                dbc.Col(dcc.Graph(id="heatmap", style={"height": "520px"}), md=5),
            ],
            className="g-2"
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="temporal", style={"height": "260px"}), md=7),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("🧬 Xyllenai Awareness Stream"),
                            dbc.CardBody(
                                dcc.Markdown(id="ai-console",
                                             style={"height": "240px", "overflowY": "auto",
                                                    "whiteSpace": "pre", "backgroundColor": "#000"})
                            )
                        ], color="dark", outline=True
                    ), md=5
                ),
            ],
            className="g-2"
        ),
        dcc.Interval(id="timer", interval=TICK_MS, n_intervals=0)
    ],
    fluid=True
)

# -----------------------------
# Interactions
# -----------------------------
@app.callback(
    Output("volume", "figure"),
    Output("heatmap", "figure"),
    Output("temporal", "figure"),
    Output("ai-console", "children"),
    Output("ws-status", "children"),
    Input("timer", "n_intervals"),
    Input("inject-btn", "n_clicks"),
    Input("toggle-diffusion", "value"),
    Input("toggle-resonance", "value"),
    Input("toggle-trail", "value"),
    State("heatmap", "clickData"),
    prevent_initial_call=False,
)
def tick(n, clicks, v_diff, v_res, v_trail, clickData):
    # update toggles
    state["toggles"]["diffusion"] = "diffusion" in (v_diff or [])
    state["toggles"]["resonance"] = "resonance" in (v_res or [])
    state["toggles"]["trail"] = "trail" in (v_trail or [])

    # consume inbound events (ws or mock)
    drained = False
    try:
        while True:
            msg = state["queue"].get_nowait()
            drained = True
            try:
                evt = json.loads(msg)
            except Exception:
                continue
            if evt.get("type") == "pulse":
                add_pulse(evt.get("x"), evt.get("y"), evt.get("z"), evt.get("intensity", 1.0))
                append_ai(f"⚡ Energy pulse @ ({evt.get('x')},{evt.get('y')},{evt.get('z')}) — source: {evt.get('source','bridge')}")
            elif evt.get("type") == "ai_log":
                append_ai(f"🤖 {evt.get('text')}")
            elif evt.get("type") == "coherence_update":
                append_ai(f"Σ coherence={evt.get('value'):.3f}")
    except asyncio.QueueEmpty:
        pass

    # click inject (on heatmap)
    if clicks:
        # if user clicked heatmap, inject at that x,y with z=mid
        if clickData and clickData.get("points"):
            px = int(clickData["points"][0]["x"])
            py = int(clickData["points"][0]["y"])
            pz = GRID // 2
            add_pulse(px, py, pz, 1.4)
            append_ai(f"🖱️ user-injected pulse @ ({px},{py},{pz})")
        # reset clicks count (idempotent)
        # dash keeps counting; no need to modify here

    # physics step
    field = state["energies"]
    if state["toggles"]["diffusion"]:
        field = step_diffusion(field)
    field = apply_pulses(field)
    state["energies"] = np.clip(field, 0.0, 1e9)

    # resonance phase
    if state["toggles"]["resonance"]:
        state["phase"] = (state["phase"] + RESONANCE_SPEED) % (2 * math.pi)

    # temporal history update
    coh = coherence_index(state["energies"])
    state["history_coh"].append(coh)
    state["tick"] += 1

    # figures
    vol = build_volume_figure(state["energies"], state["pulses"] if state["toggles"]["trail"] else [])
    hm = build_heatmap(state["energies"])
    tt = build_temporal(state["history_coh"])

    # ai console text
    console = "\n".join(list(state["ai_stream"])[-20:])
    ws_txt = ("🔌 Connected to bridge" if state["ws_connected"] else "🧪 Mock mode (bridge not connected)") \
             + f" — tick {state['tick']} — coherence {coh:.3f}"

    return vol, hm, tt, console, ws_txt

def add_pulse(x, y, z, intensity):
    x = int(np.clip(x, 0, GRID - 1))
    y = int(np.clip(y, 0, GRID - 1))
    z = int(np.clip(z, 0, GRID - 1))
    state["pulses"].append({"x": x, "y": y, "z": z, "intensity": float(intensity), "ttl": PULSE_TTL})

def append_ai(text: str):
    ts = datetime.now().strftime("%H:%M:%S")
    state["ai_stream"].append(f"[{ts}] {text}")

# start background listener
start_ws_thread()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8050, debug=True)
