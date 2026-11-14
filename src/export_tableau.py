"""Export Tableau-ready files to tableau/: the shots CSV and a half-pitch background image.

Usage:  python -m src.export_tableau
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, Rectangle

from src.queries import ShotAnalysis

OUT = Path(__file__).resolve().parents[1] / "tableau"
LINE = "#a3a29c"
SURFACE = "#fcfcfb"


def export_shots(team: str = "Bayer Leverkusen") -> Path:
    df = ShotAnalysis().run("10_tableau_shots", team=team)
    path = OUT / "leverkusen_2023_24_shots.csv"
    df.to_csv(path, index=False)
    return path


def pitch_image(path: Path = None) -> Path:
    """Attacking half of a StatsBomb pitch, goal at the top.

    The image covers EXACTLY  horizontal 0-80 (StatsBomb y)  x  vertical 60-120 (StatsBomb x),
    so in Tableau the background image is mapped X: [y] 0 -> 80, Y: [x] 60 -> 120.
    """
    path = path or OUT / "pitch_half_vertical.png"
    fig = plt.figure(figsize=(8, 6), dpi=200)          # 80 x 60 units -> 4:3
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 80)
    ax.set_ylim(60, 120)
    ax.set_facecolor(SURFACE)
    fig.patch.set_facecolor(SURFACE)
    ax.axis("off")
    kw = dict(fill=False, edgecolor=LINE, linewidth=1.6)
    ax.add_patch(Rectangle((0.1, 60), 79.8, 59.9, **kw))       # touchlines, goal line, halfway
    ax.add_patch(Rectangle((18, 102), 44, 18, **kw))           # penalty box
    ax.add_patch(Rectangle((30, 114), 20, 6, **kw))            # six-yard box
    ax.plot([36, 44], [119.85, 119.85], color=LINE, linewidth=5, solid_capstyle="butt")  # goal
    ax.add_patch(Circle((40, 108), 0.35, color=LINE))          # penalty spot
    ax.add_patch(Arc((40, 108), 20, 20, theta1=216.87, theta2=323.13, edgecolor=LINE, linewidth=1.6))  # the D
    ax.add_patch(Arc((40, 60), 20, 20, theta1=0, theta2=180, edgecolor=LINE, linewidth=1.6))  # centre circle
    fig.savefig(path, dpi=200, facecolor=SURFACE)
    plt.close(fig)
    return path


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    print(export_shots())
    print(pitch_image())
