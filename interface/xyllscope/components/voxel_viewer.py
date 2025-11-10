import plotly.graph_objects as go
import numpy as np

def generate_voxel_fig(
    energies,
    selected_voxel=None,
    pulse_frame=None,
    diffusion_map=None,
    flow_vectors=None,
    harmonic_mode=False,
    mesh_edges=None,
    show_diffusion=True,
    show_flow=True,
    show_mesh=True,
):
    energies = np.array(energies)
    nx, ny, nz = energies.shape
    x, y, z = np.meshgrid(np.arange(nx), np.arange(ny), np.arange(nz))
    values = energies.flatten()

    # --- Color logic ---
    if harmonic_mode:
        # Proper numeric mean handling
        c_energy = energies / np.max(energies)
        c_coh = np.ones_like(energies) * (1 - np.std(energies) / (np.mean(energies) + 1e-6))
        grad = np.gradient(energies)
        grad_mag = np.sqrt(sum(g**2 for g in grad))
        c_awareness = grad_mag / (np.max(grad_mag) + 1e-6)
        rgb = np.stack([c_energy, c_coh, c_awareness], axis=-1)
        colorscale = "RdYlBu"
    else:
        colorscale = "Viridis"

    fig = go.Figure(
        data=go.Volume(
            x=x.flatten(),
            y=y.flatten(),
            z=z.flatten(),
            value=values,
            opacity=0.25,
            surface_count=12,
            colorscale=colorscale,
            showscale=True,
            colorbar=dict(
                title=dict(text="Energy", font=dict(color="#0ff")),
                tickfont=dict(color="#0ff"),
            ),
        )
    )

    # --- Diffusion Glow ---
    if show_diffusion and diffusion_map is not None:
        glow = np.clip(diffusion_map * 1.5, 0, 1)
        fig.add_trace(go.Volume(
            x=x.flatten(), y=y.flatten(), z=z.flatten(),
            value=glow.flatten(), opacity=0.06,
            surface_count=8, colorscale="Electric",
            showscale=False
        ))

    # --- Pulse Wave ---
    if pulse_frame is not None:
        px, py, pz, radius = pulse_frame
        phi = np.linspace(0, np.pi, 40)
        theta = np.linspace(0, 2 * np.pi, 40)
        phi, theta = np.meshgrid(phi, theta)
        xs = px + radius * np.sin(phi) * np.cos(theta)
        ys = py + radius * np.sin(phi) * np.sin(theta)
        zs = pz + radius * np.cos(phi)
        fig.add_trace(go.Surface(
            x=xs, y=ys, z=zs,
            surfacecolor=np.ones_like(xs),
            colorscale="Electric", opacity=0.25, showscale=False, name="Pulse"
        ))

    # --- Flow Vectors ---
    if show_flow and flow_vectors is not None:
        ix, iy, iz, gx, gy, gz = flow_vectors
        fig.add_trace(go.Cone(
            x=ix, y=iy, z=iz, u=gx, v=gy, w=gz,
            sizemode="absolute", sizeref=1.3,
            colorscale="Blues", opacity=0.4, showscale=False
        ))

    # --- Mesh Links ---
    if show_mesh and mesh_edges is not None:
        for e in mesh_edges:
            fig.add_trace(go.Scatter3d(
                x=[e[0][0], e[1][0]],
                y=[e[0][1], e[1][1]],
                z=[e[0][2], e[1][2]],
                mode="lines",
                line=dict(color="cyan", width=2),
                opacity=0.25,
            ))

    # --- Highlight Selected ---
    if selected_voxel is not None:
        vx, vy = selected_voxel
        vz = np.argmax(energies[vx, vy])
        fig.add_trace(go.Scatter3d(
            x=[vx], y=[vy], z=[vz],
            mode="markers", marker=dict(size=8, color="cyan")
        ))

    fig.update_layout(
        title="Cognitive Coherence Volume",
        paper_bgcolor="black", plot_bgcolor="black",
        scene=dict(
            xaxis=dict(color="#0ff", gridcolor="#222", zeroline=False),
            yaxis=dict(color="#0ff", gridcolor="#222", zeroline=False),
            zaxis=dict(color="#0ff", gridcolor="#222", zeroline=False),
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        height=600,
    )
    return fig
