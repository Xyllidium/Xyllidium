# v3.5.1 XNTF visual layer (surface + heatmap)
import numpy as np
import plotly.graph_objects as go

def build_surface(field: np.ndarray) -> go.Figure:
    fig = go.Figure(
        data=[go.Surface(z=field, showscale=True, opacity=0.96,
                         colorscale="Viridis")]
    )
    fig.update_scenes(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False)
    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=420,
                      paper_bgcolor="black", plot_bgcolor="black")
    return fig

def build_heatmap(field: np.ndarray) -> go.Figure:
    fig = go.Figure(
        data=[go.Heatmap(z=field, colorscale="Viridis", showscale=True)]
    )
    fig.update_layout(margin=dict(l=10,r=20,t=5,b=5), height=220,
                      paper_bgcolor="black", plot_bgcolor="black",
                      xaxis=dict(showgrid=False, color="#00E5FF"),
                      yaxis=dict(showgrid=False, color="#00E5FF"),
                      title="Temporal Coherence Index", titlefont_color="#00E5FF")
    return fig
