import plotly.graph_objects as go

def make_chrono_trace(state):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=state["coherence"], x=state["time"],
        mode="lines+markers", line=dict(color="#0ff")
    ))
    fig.update_layout(
        title="Temporal Coherence Evolution",
        paper_bgcolor="black", plot_bgcolor="black",
        font=dict(color="#0ff"), height=280,
        margin=dict(l=40, r=20, t=40, b=40)
    )
    return fig
