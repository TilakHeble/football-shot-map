"""Figures: shot map, cumulative goals vs xG, squad goals-vs-xG comparison.

Every function takes the DataFrame returned by one of the queries in sql/;
no football calculations happen here, only drawing."""
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


def shot_map(shots: pd.DataFrame, s: pd.Series, player: str, subtitle: str, path):
    """Half-pitch shot map: marker size = xG, filled = goal, hollow = no goal.

    shots: output of 02_player_shots.sql; s: the single row of 03_player_summary.sql.
    """
    pitch = VerticalPitch(pitch_type="statsbomb", half=True, pad_bottom=-25,
                          pitch_color=SURFACE, line_color=MUTED, linewidth=1)
    fig, ax = pitch.draw(figsize=(9, 7.2))
    fig.subplots_adjust(bottom=0.2, top=0.84)

    misses = shots[~shots["is_goal"]]
    goals = shots[shots["is_goal"]]
    size = lambda d: 60 + 1400 * d["xg"]
    pitch.scatter(misses["x"], misses["y"], s=size(misses), ax=ax,
                  facecolors="none", edgecolors=INK_2, linewidths=1, alpha=0.7,
                  label="No goal", zorder=2)
    pitch.scatter(goals["x"], goals["y"], s=size(goals), ax=ax,
                  color=GOAL, edgecolors=SURFACE, linewidths=1.5,
                  label="Goal", zorder=3)

    fig.text(0.08, 0.935, player, fontsize=20, weight="bold")
    fig.text(0.08, 0.885, subtitle, fontsize=12, color=INK_2)

    stats = [("Shots", f"{int(s['shots'])}"), ("Goals", f"{int(s['goals'])}"),
             ("xG", f"{s['xg']:.1f}"), ("npxG / shot", f"{s['npxg_per_shot']:.2f}"),
             ("Avg dist.", f"{s['avg_distance_m']:.1f} m")]
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


def cumulative_xg(cum: pd.DataFrame, player: str, path, note: dict | None = None):
    """Running non-penalty goals vs npxG. cum: output of 05_cumulative_by_matchday.sql."""
    # start at matchday 0 and pad one step past the end so the last jump is drawn in full
    end = int(cum["matchday"].max())
    days = np.concatenate([[0], cum["matchday"], [end + 1]])
    g = np.concatenate([[0], cum["cum_np_goals"], [cum["cum_np_goals"].iloc[-1]]])
    x = np.concatenate([[0], cum["cum_npxg"], [cum["cum_npxg"].iloc[-1]]])

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.step(days, g, where="post", color=GOAL, lw=2, label="Non-penalty goals")
    ax.step(days, x, where="post", color=XG, lw=2, label="npxG")
    ax.text(end + 1.5, g[-1], f"{int(g[-1])} NP goals", va="center", fontsize=10)
    ax.text(end + 1.5, x[-1], f"{x[-1]:.1f} npxG", va="center", fontsize=10)
    if note:
        md = int(cum.loc[cum["match_id"] == note["match_id"], "matchday"].iloc[0])
        ax.annotate(note["text"], xy=(md, g[md]), xytext=(md - 13, g[md] + 0.6),
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


def squad_comparison(g: pd.DataFrame, team: str, highlight: str, path,
                     min_shots: int = 15):
    """Scatter of npxG vs NP goals. g: output of 06_squad_finishing.sql."""
    g = g.set_index("player").rename(columns={"npxg": "xg", "np_goals": "goals"})

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
