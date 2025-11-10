"""
components/equilibrium_panel.py
Real-time equilibrium visualizer for Xyllenor ↔ Xyllscope link.
"""

from dash import html, dcc
import dash_daq as daq
import plotly.graph_objs as go

def layout():
    return html.Div(
        [
            html.H4("⚖️  Xyllenor Equilibrium Panel", 
                    style={"textAlign": "center", "color": "#00FFFF"}),

            html.Div([
                daq.Gauge(
                    id="entropy-gauge", min=0, max=1, value=0.0,
                    label="Entropy", color="#FF1493", showCurrentValue=True
                ),
                daq.Gauge(
                    id="balance-gauge", min=0, max=1, value=1.0,
                    label="Balance Index", color="#00FF7F", showCurrentValue=True
                ),
                daq.Gauge(
                    id="flux-gauge", min=0, max=0.2, value=0.0,
                    label="Flux Rate", color="#1E90FF", showCurrentValue=True
                )
            ], style={"display": "flex", "justifyContent": "space-around", "marginBottom": "10px"}),

            dcc.Graph(id="flux-wave", style={"height": "280px"}),

            html.Pre(id="metrics-log", style={
                "backgroundColor": "#000", "color": "#0FF",
                "padding": "10px", "height": "160px",
                "overflowY": "scroll", "borderRadius": "8px"
            })
        ]
    )

def make_flux_wave(history):
    if not history:
        return go.Figure()
    times = [m["timestamp"] for m in history]
    fluxes = [m["flux_rate"] for m in history]
    fig = go.Figure(
        data=[go.Scatter(x=times, y=fluxes, mode="lines+markers", line=dict(color="#1E90FF"))],
        layout=go.Layout(
            template="plotly_dark",
            xaxis_title="Time",
            yaxis_title="Flux Rate",
            margin=dict(l=40, r=20, t=30, b=40),
        )
    )
    return fig
