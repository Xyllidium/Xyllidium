import numpy as np
import plotly.graph_objects as go

def build_xntf_field(nodes=80):
    """Simulate XNTF neurofractal field flow (preview build)."""
    x, y, z = np.random.randn(nodes), np.random.randn(nodes), np.random.randn(nodes)
    coherence = np.random.rand(nodes)
    colors = ["rgb(0,255,255)" if c > 0.5 else "rgb(80,80,255)" for c in coherence]

    fig = go.Figure(
        data=[go.Scatter3d(
            x=x, y=y, z=z, mode="markers",
            marker=dict(size=4, color=colors, opacity=0.8),
            hovertext=[f"Node {i} | Coherence {coherence[i]:.2f}" for i in range(nodes)]
        )]
    )
    fig.update_layout(
        title="XNTF Neurofractal Transmission Field",
        scene=dict(xaxis_title="X", yaxis_title="Y", zaxis_title="Z"),
        template="plotly_dark"
    )
    return fig
