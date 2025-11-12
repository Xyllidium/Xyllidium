# v3.5.1 Equilibrium gauges
import plotly.graph_objects as go

def gauge(value: float, title: str, range_max: float, color: str) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=float(value),
        gauge={'axis': {'range': [0, range_max]},
               'bar': {'color': color}},
        title={'text': title}
    ))
    fig.update_layout(margin=dict(l=10,r=10,t=30,b=10),
                      height=240, paper_bgcolor="black", font_color=color)
    return fig
