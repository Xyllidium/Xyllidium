import plotly.graph_objects as go
import numpy as np

def make_energy_heatmap(energies):
    # 2D projection for visualization
    avg_plane = np.mean(energies, axis=2)

    fig = go.Figure(
        data=go.Heatmap(
            z=avg_plane,
            colorscale="Turbo",
            colorbar=dict(
                title=dict(text="Energy", font=dict(color="#0ff")),
                tickfont=dict(color="#0ff")
            ),
        )
    )

    fig.update_layout(
        title="Per-Voxel Energy Heatmap (Interactive)",
        paper_bgcolor="black",
        plot_bgcolor="black",
        font=dict(color="#0ff"),
        margin=dict(l=30, r=30, t=60, b=30),
        height=600,
    )
    return fig
