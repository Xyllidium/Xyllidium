# Xyllscope v3.1-Stable Restoration (Cognitive Field Monitor)
# Combines visuals of v2.3 + renderer patch of v3.5.8.1
# Works on Dash>=8, NumPy>=1.26

import os, json, threading, asyncio
from collections import deque
from datetime import datetime
import numpy as np
import plotly.graph_objects as go
import dash
from dash import dcc, html, Output, Input
import dash_bootstrap_components as dbc

# --- configuration ---
GRID = (16,16)
state = dict(Z=np.zeros(GRID), hist=deque(maxlen=300), ai=[], tick=0, connected=False)

# --- utilities ---
def ts(): return datetime.now().strftime("%H:%M:%S")
def log(msg): state["ai"].append(f"[{ts()}] {msg}")

def coherence(Z):
    m,s=np.mean(Z),np.std(Z)
    return float(max(0,min(1,1-s/(m+1e-9))))

# --- visuals ---
def surface(Z):
    fig=go.Figure(go.Surface(z=Z,colorscale="Viridis",opacity=0.85,
                             showscale=True,lighting={"ambient":0.6}))
    fig.update_layout(scene=dict(
        xaxis=dict(visible=False),yaxis=dict(visible=False),
        zaxis=dict(visible=False),aspectmode="cube",
        camera=dict(eye=dict(x=1.4,y=1.4,z=1.1))),
        margin=dict(l=10,r=10,t=10,b=10),
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
    return fig

def heat(Z):
    fig=go.Figure(go.Heatmap(z=Z,colorscale="Turbo",showscale=False))
    fig.update_layout(margin=dict(l=10,r=10,t=20,b=20),
                      paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)",height=220)
    return fig

def line(y):
    fig=go.Figure(go.Scatter(y=y,mode="lines",line=dict(color="#00FFFF",width=2)))
    fig.update_layout(margin=dict(l=10,r=10,t=20,b=20),
                      paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)",height=200)
    return fig

# --- mock update loop ---
def offline_step():
    Z=state["Z"]
    wave=np.sin(0.1*state["tick"]+np.linspace(0,3.14,GRID[0]))[None,:]
    Z=0.9*Z+0.1*wave
    state["Z"]=np.clip(Z,0,1)

# --- dash app ---
app=dash.Dash(__name__,external_stylesheets=[dbc.themes.CYBORG],
              title="Xyllscope – Cognitive Field Monitor")

app.index_string="""
<!DOCTYPE html>
<html>
  <head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}</head>
  <body style="background-color:#000;">
    {%app_entry%}
    <footer>{%config%}{%scripts%}{%renderer%}</footer>
  </body>
</html>"""

app.layout=dbc.Container([
    html.H1("🧠 Xyllscope – Cognitive Field Monitor",
            style={"color":"#6ee7ff","marginTop":"10px"}),
    dbc.Row([
        dbc.Col(dbc.Button("Start/Stop",id="btn",color="danger",outline=True,size="sm")),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id="surf",figure=surface(state["Z"])),md=7),
        dbc.Col([dcc.Graph(id="heat",figure=heat(state["Z"])),
                 dcc.Graph(id="line",figure=line([]))],md=5)
    ],className="mt-3"),
    html.Pre(id="ai",style={"height":"160px","overflowY":"auto"}),
    html.Div(id="status",style={"color":"#6ee7ff"}),
    dcc.Interval(id="tick",interval=900,n_intervals=0)
],fluid=True)

@app.callback(Output("surf","figure"),Output("heat","figure"),
              Output("line","figure"),Output("ai","children"),
              Output("status","children"),
              Input("tick","n_intervals"))
def update(_):
    offline_step()
    state["tick"]+=1
    coh=coherence(state["Z"]); state["hist"].append(coh)
    return (surface(state["Z"]),heat(state["Z"]),line(state["hist"]),
            "\n".join(state["ai"][-200:]),f"Tick {state['tick']} | coherence {coh:.3f}")

if __name__=="__main__":
    app.run(host="127.0.0.1",port=8050,debug=True)
