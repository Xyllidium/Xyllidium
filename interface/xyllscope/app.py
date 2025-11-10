
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import dash_daq as daq
import numpy as np
import plotly.graph_objs as go
import asyncio, threading, websockets, json
from datetime import datetime
from collections import deque
from components.equilibrium_panel import layout as equilibrium_layout, make_flux_wave

# ---- Global Config ----
GRID = 8
MAX_HISTORY = 60
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
app.title = "Xyllscope v3.3 – Cognitive Aura Edition"
app.config.suppress_callback_exceptions = True

# ---- State ----
state = {
    "energies": np.random.rand(GRID, GRID, GRID),
    "pulses": [],
    "ai_stream": deque(maxlen=200),
    "history_coh": deque(maxlen=MAX_HISTORY),
    "tick": 0,
    "ws_connected": False,
}

# ---- Equilibrium Feed ----
latest_metrics = {}
history_metrics = deque(maxlen=10)

# ---- Helper Functions ----
def build_volume_figure(field, pulses):
    """
    Volumetric cognitive aura visualization.
    Replaces scatter points with smooth coherence cloud.
    """
    from plotly.colors import sample_colorscale

    # Flatten grid into coordinates + energy values
    energy = field.flatten()
    coords = np.indices(field.shape).reshape(3, -1).T

    # Normalize energy
    norm = (energy - energy.min()) / (energy.max() - energy.min() + 1e-9)

    # Dynamic threshold — aura breathes with coherence
    coh = coherence_index(field)
    iso_min = np.percentile(energy, 60 - 20 * (coh - 0.5))  # coherence controls transparency
    iso_max = energy.max()

    # Generate volumetric aura
    fig = go.Figure(data=[
        go.Volume(
            x=coords[:, 0], y=coords[:, 1], z=coords[:, 2],
            value=energy,
            isomin=iso_min,
            isomax=iso_max,
            opacity=0.1 + coh * 0.3,  # more coherence = brighter aura
            surface_count=20,
            colorscale="Electric"
        )
    ])

    # Black background, centered layout
    fig.update_layout(
        scene=dict(
            bgcolor="black",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="black",
        plot_bgcolor="black"
    )

    return fig


def build_heatmap(field):
    heat = field.mean(axis=2)
    fig = go.Figure(data=[go.Heatmap(z=heat, colorscale="Viridis")])
    fig.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=20, b=20))
    return fig

def build_temporal(history):
    fig = go.Figure(data=[go.Scatter(y=list(history), mode="lines", line=dict(color="#00FFFF"))])
    fig.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=20, b=20))
    return fig

def coherence_index(field):
    mean_val = np.mean(field)
    var_val = np.var(field)
    return np.exp(-var_val / (mean_val + 1e-9))

def add_pulse(x, y, z, intensity):
    x, y, z = int(x), int(y), int(z)
    state["pulses"].append({"x": x, "y": y, "z": z, "intensity": float(intensity)})

def append_ai(text: str):
    ts = datetime.now().strftime("%H:%M:%S")
    state["ai_stream"].append(f"[{ts}] {text}")

# ---- Async WebSocket ----
async def listen_bridge():
    uri = "ws://127.0.0.1:8765"
    global latest_metrics, history_metrics
    try:
        async with websockets.connect(uri) as ws:
            state["ws_connected"] = True
            append_ai("Connected to bridge.")
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get("type") == "energy_update":
                    state["energies"] = np.array(data["energies"])
                elif data.get("type") == "xyllenor_metrics":
                    latest_metrics = data["data"]
                    history_metrics.append(latest_metrics)
    except Exception as e:
        append_ai(f"Bridge connection failed: {e}")
        state["ws_connected"] = False

def start_ws_thread():
    threading.Thread(target=lambda: asyncio.run(listen_bridge()), daemon=True).start()

# ---- Dash Layout ----
app.layout = dbc.Container(
    [
        html.H2("🌌 Xyllscope v3.2 – Cognitive Field Monitor", 
                style={"textAlign": "center", "marginTop": "20px"}),
        html.Div(id="ws-status", style={"textAlign": "center", "color": "#00FFFF"}),
        dbc.Row([
            dbc.Col(dcc.Graph(id="voxel-view", style={"height": "500px"}), width=6),
            dbc.Col(dcc.Graph(id="heatmap", style={"height": "500px"}), width=6),
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(id="temporal-coherence", style={"height": "300px"}), width=12)
        ]),
        html.Hr(),
        equilibrium_layout(),  # ⚖️ attach equilibrium panel here
        html.Hr(),
        html.Pre(id="ai-console", style={
            "backgroundColor": "#000", "color": "#0FF", "padding": "10px",
            "height": "200px", "overflowY": "scroll", "borderRadius": "8px"
        }),
        dcc.Interval(id="interval-component", interval=2000, n_intervals=0)
    ],
    fluid=True,
)

# ---- Callbacks ----
@app.callback(
    [
        Output("voxel-view", "figure"),
        Output("heatmap", "figure"),
        Output("temporal-coherence", "figure"),
        Output("ai-console", "children"),
        Output("ws-status", "children"),
        Output("entropy-gauge", "value"),
        Output("balance-gauge", "value"),
        Output("flux-gauge", "value"),
        Output("flux-wave", "figure"),
        Output("metrics-log", "children"),
    ],
    Input("interval-component", "n_intervals")
)
def update_visuals(_):
    # compute coherence + pulses
    coh = coherence_index(state["energies"])
    state["history_coh"].append(coh)
    state["tick"] += 1

    # visuals
    vol = build_volume_figure(state["energies"], state["pulses"])
    hm = build_heatmap(state["energies"])
    tt = build_temporal(state["history_coh"])
    console = "\n".join(list(state["ai_stream"])[-20:])
    ws_txt = f"{'🔌 Connected' if state['ws_connected'] else '⚠️ Disconnected'} — tick {state['tick']} — coherence {coh:.3f}"

    # equilibrium metrics (if present)
    if latest_metrics:
        ent = latest_metrics.get("entropy", 0)
        bal = latest_metrics.get("balance_index", 1)
        flux = latest_metrics.get("flux_rate", 0)
        flux_fig = make_flux_wave(history_metrics)
        log = json.dumps(latest_metrics, indent=2)
    else:
        ent, bal, flux = 0, 1, 0
        flux_fig, log = make_flux_wave([]), "Awaiting Xyllenor data..."

    return vol, hm, tt, console, ws_txt, ent, bal, flux, flux_fig, log


# ---- Start Background ----
start_ws_thread()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8050, debug=True)
