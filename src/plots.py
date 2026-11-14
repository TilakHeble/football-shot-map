"""Figures: shot map, cumulative goals vs xG, squad goals-vs-xG comparison."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mplsoccer import VerticalPitch

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#a3a29c"
GOAL = "#2a78d6"     # categorical slot 1
XG = "#eb6834"       # categorical slot 2

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "text.color": INK, "axes.labelcolor": INK_2,
    "xtick.color": INK_2, "ytick.color": INK_2,
    "axes.edgecolor": MUTED, "font.size": 11,
})


def summary(shots: pd.DataFrame) -> dict:
    np_shots = shots[~shots["is_penalty"]]
    return {
        "Shots": len(shots),
        "Goals": int(shots["is_goal"].sum()),
        "xG": shots["shot_statsbomb_xg"].sum(),
        "NP goals": int(np_shots["is_goal"].sum()),
        "npxG": np_shots["shot_statsbomb_xg"].sum(),
        "npxG / shot": np_shots["shot_statsbomb_xg"].mean(),
        "Avg distance (m)": np_shots["distance"].mean() * 0.9144,  # yards -> m
        "On target %": 100 * shots["shot_outcome"].isin(
            ["Goal", "Saved", "Saved to Post"]).mean(),
    }


def shot_map(shots: pd.DataFrame, player: str, subtitle: str, path):
    """Half-pitch shot map: marker size = xG, filled = goal, hollow = no goal."""
    pitch = VerticalPitch(pitch_type="statsbomb", half=True, pad_bottom=-25,
                          pitch_color=SURFACE, line_color=MUTED, linewidth=1)
    fig, ax = pitch.draw(figsize=(9, 7.2))
    fig.subplots_adjust(bottom=0.2, top=0.84)

    misses = shots[~shots["is_goal"]]
    goals = shots[shots["is_goal"]]
    size = lambda s: 60 + 1400 * s["shot_statsbomb_xg"]
    pitch.scatter(misses["x"], misses["y"], s=size(misses), ax=ax,
                  facecolors="none", edgecolors=INK_2, linewidths=1, alpha=0.7,
                  label="No goal", zorder=2)
    pitch.scatter(goals["x"], goals["y"], s=size(goals), ax=ax,
                  color=GOAL, edgecolors=SURFACE, linewidths=1.5,
                  label="Goal", zorder=3)

    fig.text(0.08, 0.935, player, fontsize=20, weight="bold")
    fig.text(0.08, 0.885, subtitle, fontsize=12, color=INK_2)

    s = summary(shots)
    stats = [("Shots", f"{s['Shots']}"), ("Goals", f"{s['Goals']}"),
             ("xG", f"{s['xG']:.1f}"), ("npxG / shot", f"{s['npxG / shot']:.2f}"),
             ("Avg dist.", f"{s['Avg distance (m)']:.1f} m")]
    for i, (label, val) in enumerate(stats):
        x = 0.12 + i * 0.19
        fig.text(x, 0.105, val, fontsize=18, weight="bold", ha="center")
        fig.text(x, 0.065, label, fontsize=10, color=INK_2, ha="center")

    leg = fig.legend(loc="upper right", frameon=False, fontsize=10,
                     bbox_to_anchor=(0.93, 0.95), markerscale=0.6)
    for t in leg.get_texts():
        t.set_color(INK_2)
    fig.text(0.92, 0.015, "Marker size = xG  ·  Data: StatsBomb Open Data",
             ha="right", fontsize=9, color=INK_2)
    fig.savefig(path, dpi=200)
    plt.close(fig)


def cumulative_xg(shots: pd.DataFrame, all_shots: pd.DataFrame, team: str,
                  player: str, path, annotate: dict | None = None):
    """Running non-penalty goals vs npxG across every team matchday (1..N)."""
    matches = (all_shots.loc[all_shots["team"] == team, ["match_id", "match_date"]]
               .drop_duplicates().sort_values("match_date").reset_index(drop=True))
    matches["matchday"] = matches.index + 1
    np_shots = shots[~shots["is_penalty"]]
    per = (np_shots.groupby("match_id")
           .agg(goals=("is_goal", "sum"), xg=("shot_statsbomb_xg", "sum")))
    m = matches.merge(per, on="match_id", how="left").fillna({"goals": 0, "xg": 0})
    # pad one step past the last matchday so its jump is drawn as a full step
    days = np.concatenate([[0], m["matchday"], [m["matchday"].iloc[-1] + 1]])
    g = np.concatenate([[0], m["goals"].cumsum(), [m["goals"].sum()]])
    x = np.concatenate([[0], m["xg"].cumsum(), [m["xg"].sum()]])

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.step(days, g, where="post", color=GOAL, lw=2, label="Non-penalty goals")
    ax.step(days, x, where="post", color=XG, lw=2, label="npxG")
    end = days[-2]
    ax.text(end + 1.5, g[-1], f"{int(g[-1])} NP goals", va="center", fontsize=10)
    ax.text(end + 1.5, x[-1], f"{x[-1]:.1f} npxG", va="center", fontsize=10)
    if annotate:
        md = int(m.loc[m["match_id"] == annotate["match_id"], "matchday"].iloc[0])
        ax.annotate(annotate["text"], xy=(md, g[md]), xytext=(md - 13, g[md] + 0.6),
                    fontsize=9, color=INK_2,
                    arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.set_xlabel("Bundesliga matchday")
    ax.set_ylabel("Cumulative total")
    ax.grid(axis="y", color="#e6e5e0", lw=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xlim(0, end + 7)
    ax.set_ylim(0, max(g[-1], x[-1]) + 2)
    ax.set_xticks([1, 5, 10, 15, 20, 25, 30, end])
    ax.legend(frameon=False, loc="upper left")
    ax.set_title(f"{player}: goals vs expected goals, matchday by matchday",
                 loc="left", fontsize=14, weight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def squad_comparison(shots: pd.DataFrame, team: str, highlight: str, path,
                     min_shots: int = 15):
    """Scatter of npxG vs NP goals for every player with >= min_shots shots."""
    np_shots = shots[(shots["team"] == team) & (~shots["is_penalty"])]
    g = (np_shots.groupby("player")
         .agg(shots=("is_goal", "size"), goals=("is_goal", "sum"),
              xg=("shot_statsbomb_xg", "sum"),
              # each shot ~ Bernoulli(xG): Var(goals) = sum xG(1 - xG)
              sd=("shot_statsbomb_xg", lambda q: np.sqrt((q * (1 - q)).sum()))))
    g = g[g["shots"] >= min_shots]

    fig, ax = plt.subplots(figsize=(9, 7))
    lim = max(g["xg"].max(), g["goals"].max()) + 2
    ax.plot([0, lim], [0, lim], color=MUTED, lw=1, ls="--", zorder=1)
    ax.text(lim - 0.3, lim - 1.3, "goals = xG", ha="right", color=INK_2, fontsize=9)
    others = g.drop(index=highlight, errors="ignore")
    ax.scatter(others["xg"], others["goals"], s=70, color=INK_2, alpha=0.55,
               edgecolors=SURFACE, linewidths=2, zorder=2)
    if highlight in g.index:
        h = g.loc[highlight]
        ax.scatter(h["xg"], h["goals"], s=110, color=GOAL,
                   edgecolors=SURFACE, linewidths=2, zorder=3)
    short = {"Alejandro Grimaldo García": "Grimaldo",
             "Victor Okoh Boniface": "Boniface",
             "Exequiel Alejandro Palacios": "Palacios",
             "Piero Martín Hincapié Reyna": "Hincapié"}
    nudge = {"Jonathan Tah": (-8, 4, "right")}   # avoid collision with Andrich
    for name, row in g.iterrows():
        dx, dy, ha = nudge.get(name, (7, 4, "left"))
        ax.annotate(short.get(name, name.split()[-1]), (row["xg"], row["goals"]),
                    xytext=(dx, dy), textcoords="offset points", fontsize=9, ha=ha,
                    color=INK if name == highlight else INK_2,
                    weight="bold" if name == highlight else "normal")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("Non-penalty xG")
    ax.set_ylabel("Non-penalty goals")
    ax.grid(color="#e6e5e0", lw=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title(f"{team}: finishing vs chance quality (players with {min_shots}+ shots)",
                 loc="left", fontsize=13, weight="bold")
    ax.text(0, -0.13, "Above the line = scored more than expected. "
            "Data: StatsBomb Open Data, Bundesliga 2023/24.",
            transform=ax.transAxes, fontsize=9, color=INK_2)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    g["diff"] = g["goals"] - g["xg"]
    g["z"] = g["diff"] / g["sd"]   # over/under-performance in standard deviations
    return g.sort_values("xg", ascending=False)
