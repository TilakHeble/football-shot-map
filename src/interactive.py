"""Interactive Plotly versions of the charts, used by the Streamlit dashboard (app.py).

Like src/plots.py, these functions only draw: every input is a DataFrame returned
by one of the queries in sql/.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#a3a29c"
GRID = "#e6e5e0"
GOAL = "#2a78d6"   # categorical slot 1
XG = "#eb6834"     # categorical slot 2
FONT = dict(family="Inter, -apple-system, Segoe UI, sans-serif", color=INK, size=13)


def _base_layout(fig, height, title=None):
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=40 if title else 10, b=10),
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, font=FONT,
        title=dict(text=title, x=0, font=dict(size=15, color=INK)) if title else None,
        hoverlabel=dict(bgcolor="white", bordercolor=MUTED, font=dict(color=INK, size=12)),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1,
                    font=dict(color=INK_2)),
    )
    return fig


def _pitch_shapes(bottom: float) -> list[dict]:
    """Attacking half of a StatsBomb pitch, drawn vertically (goal at the top).

    Horizontal axis = StatsBomb y (0-80), vertical axis = StatsBomb x (goal line at 120).
    """
    line = dict(color=MUTED, width=1.2)
    rect = lambda x0, x1, y0, y1: dict(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                                       line=line, layer="below")
    shapes = [
        rect(0, 80, bottom, 120),       # touchlines + goal line
        rect(18, 62, 102, 120),         # penalty box
        rect(30, 50, 114, 120),         # six-yard box
        dict(type="line", x0=36, x1=44, y0=120.6, y1=120.6,
             line=dict(color=MUTED, width=4), layer="below"),   # goal
    ]
    # penalty spot and the "D" (arc of radius 10 around the spot, outside the box)
    shapes.append(dict(type="circle", x0=39.6, x1=40.4, y0=107.6, y1=108.4,
                       fillcolor=MUTED, line=dict(width=0), layer="below"))
    t = np.linspace(0, 2 * np.pi, 200)
    ax, ay = 40 + 10 * np.cos(t), 108 + 10 * np.sin(t)
    keep = ay < 102
    path = "M " + " L ".join(f"{a:.2f},{b:.2f}" for a, b in zip(ax[keep], ay[keep]))
    shapes.append(dict(type="path", path=path, line=line, layer="below"))
    if bottom <= 60:   # centre circle, if the halfway line is in view
        shapes.append(dict(type="circle", x0=30, x1=50, y0=50, y1=70, line=line, layer="below"))
    return shapes


def shot_map(shots: pd.DataFrame, include_penalties: bool = True) -> go.Figure:
    """Shots on a vertical half pitch. Size = xG, filled = goal. shots: 02_player_shots.sql."""
    d = shots if include_penalties else shots[~shots["is_penalty"]]
    bottom = float(min(85, np.floor(d["x"].min() - 3))) if len(d) else 85.0
    # crop the width to where the shots are (always keeping the whole penalty box)
    left = float(min(10, np.floor(d["y"].min() - 3))) if len(d) else 10.0
    right = float(max(70, np.ceil(d["y"].max() + 3))) if len(d) else 70.0
    fig = go.Figure()
    hover = ("<b>%{customdata[0]}</b> vs %{customdata[1]}<br>"
             "Minute %{customdata[2]}<br>xG %{customdata[3]:.2f}<br>"
             "%{customdata[4]} · %{customdata[5]}<extra></extra>")

    for is_goal, name in [(False, "No goal"), (True, "Goal")]:
        part = d[d["is_goal"] == is_goal]
        custom = np.stack([part["match_date"].astype(str), part["opponent"], part["minute"],
                           part["xg"], part["outcome"], part["body_part"]], axis=-1) \
            if len(part) else None
        fig.add_trace(go.Scatter(
            x=part["y"], y=part["x"], mode="markers", name=name, customdata=custom,
            hovertemplate=hover,
            marker=dict(
                size=6 + 32 * np.sqrt(part["xg"]),          # area roughly proportional to xG
                color=GOAL if is_goal else "rgba(0,0,0,0)",
                line=dict(color=SURFACE if is_goal else INK_2, width=1.5 if is_goal else 1),
                opacity=1 if is_goal else 0.75,
            ),
        ))
    fig.update_xaxes(range=[left, right], visible=False, fixedrange=True)
    fig.update_yaxes(range=[bottom - 1, 122], visible=False, fixedrange=True,
                     scaleanchor="x", scaleratio=1)
    fig.update_layout(shapes=_pitch_shapes(bottom))
    return _base_layout(fig, height=400)


def cumulative(cum: pd.DataFrame) -> go.Figure:
    """Running NP goals vs npxG by matchday. cum: 05_cumulative_by_matchday.sql."""
    hover = ("<b>Matchday %{x}</b> vs %{customdata[0]}<br>"
             "This match: %{customdata[1]}<br>Season total: %{y:.2f}<extra>%{fullData.name}</extra>")
    fig = go.Figure()
    for col, per, name, color, fmt in [
        ("cum_np_goals", "np_goals", "Non-penalty goals", GOAL, "{:.0f} goals"),
        ("cum_npxg", "npxg", "npxG", XG, "{:.2f} xG"),
    ]:
        custom = np.stack([cum["opponent"], cum[per].map(fmt.format)], axis=-1)
        fig.add_trace(go.Scatter(x=cum["matchday"], y=cum[col], name=name, mode="lines",
                                 line=dict(color=color, width=2, shape="hv"),
                                 customdata=custom, hovertemplate=hover))
    fig.update_xaxes(title="Matchday", showgrid=False, linecolor=MUTED,
                     tickfont=dict(color=INK_2), range=[0.5, cum["matchday"].max() + 1.5])
    fig.update_yaxes(title="Cumulative total", gridcolor=GRID, zeroline=False,
                     tickfont=dict(color=INK_2), rangemode="tozero")
    fig.update_layout(hovermode="x unified")
    return _base_layout(fig, height=430)


LABEL_POS = {"Jonathan Tah": "top left"}   # avoid colliding with Andrich
SHORT_NAMES = {"Alejandro Grimaldo García": "Grimaldo", "Victor Okoh Boniface": "Boniface",
               "Exequiel Alejandro Palacios": "Palacios", "Piero Martín Hincapié Reyna": "Hincapié"}


def squad_scatter(squad: pd.DataFrame, highlight: str) -> go.Figure:
    """npxG vs NP goals for the squad. squad: 06_squad_finishing.sql."""
    lim = float(max(squad["npxg"].max(), squad["np_goals"].max()) + 2)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, lim], y=[0, lim], mode="lines", hoverinfo="skip",
                             line=dict(color=MUTED, dash="dash", width=1), showlegend=False))
    hover = ("<b>%{customdata[0]}</b><br>%{customdata[1]} shots<br>"
             "NP goals %{y} · npxG %{x:.2f}<br>Goals − xG %{customdata[2]:+.2f} "
             "(z = %{customdata[3]:+.2f})<extra></extra>")
    for is_hl in (False, True):
        part = squad[(squad["player"] == highlight) == is_hl]
        if part.empty:
            continue
        labels = part["player"].map(lambda n: SHORT_NAMES.get(n, n.split()[-1]))
        fig.add_trace(go.Scatter(
            x=part["npxg"], y=part["np_goals"], mode="markers+text", text=labels,
            textposition=[LABEL_POS.get(n, "top right") for n in part["player"]],
            showlegend=False,
            textfont=dict(color=INK if is_hl else INK_2, size=12 if is_hl else 11),
            customdata=np.stack([part["player"], part["shots"], part["goals_minus_xg"],
                                 part["z_score"]], axis=-1),
            hovertemplate=hover,
            marker=dict(size=14 if is_hl else 10, color=GOAL if is_hl else INK_2,
                        opacity=1 if is_hl else 0.55, line=dict(color=SURFACE, width=2)),
        ))
    fig.add_annotation(x=lim * 0.97, y=lim * 0.97 - 0.8, text="goals = xG", showarrow=False,
                       font=dict(color=INK_2, size=11), xanchor="right")
    fig.update_xaxes(title="Non-penalty xG", range=[0, lim], gridcolor=GRID, zeroline=False,
                     tickfont=dict(color=INK_2))
    fig.update_yaxes(title="Non-penalty goals", range=[0, lim], gridcolor=GRID, zeroline=False,
                     tickfont=dict(color=INK_2))
    return _base_layout(fig, height=480)
