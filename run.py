"""Generate the shot map, xG timeline and squad comparison for one player.

All numbers come from the SQL files in sql/, run against data/statsbomb.duckdb.

Usage:
    python run.py                                   # Florian Wirtz (default)
    python run.py --player "Victor Okoh Boniface"
    python run.py --rebuild                         # re-download StatsBomb data first
"""
import argparse
from pathlib import Path

import pandas as pd

from src.database import build_database
from src.plots import cumulative_xg, shot_map, squad_comparison
from src.queries import ShotAnalysis

FIG_DIR = Path(__file__).parent / "figures"
pd.set_option("display.width", 120)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--player", default="Florian Wirtz")
    p.add_argument("--team", default="Bayer Leverkusen")
    p.add_argument("--min-shots", type=int, default=15)
    p.add_argument("--rebuild", action="store_true", help="re-download data into DuckDB")
    args = p.parse_args()

    if args.rebuild:
        build_database()
    db = ShotAnalysis()

    shots = db.run("02_player_shots", player=args.player)
    if shots.empty:
        names = [r[0] for r in db.players(args.team)]
        raise SystemExit(f"No shots for {args.player!r}. Try one of:\n  " + "\n  ".join(names))

    summary = db.run("03_player_summary", player=args.player).iloc[0]
    cum = db.run("05_cumulative_by_matchday", player=args.player, team=args.team)
    squad = db.run("06_squad_finishing", team=args.team, min_shots=args.min_shots)
    best = db.run("09_best_single_match", player=args.player).iloc[0]
    note = None
    if best["np_goals"] >= 3:
        note = {"match_id": best["match_id"],
                "text": f"{best['np_goals']} goals vs {best['opponent']} ({best['match_date']:%Y-%m-%d})"}

    FIG_DIR.mkdir(exist_ok=True)
    slug = args.player.lower().replace(" ", "_")
    shot_map(shots, summary, args.player, f"{args.team} · Bundesliga 2023/24 · all shots",
             FIG_DIR / f"{slug}_shot_map.png")
    cumulative_xg(cum, args.player, FIG_DIR / f"{slug}_cumulative_xg.png", note)
    squad_comparison(squad, args.team, args.player, FIG_DIR / "squad_goals_vs_xg.png",
                     min_shots=args.min_shots)

    print(f"\n{args.player}\n{summary.round(2).to_string()}")
    print("\nInside vs outside the box (non-penalty):")
    print(db.run("04_player_zones", player=args.player).round(2).to_string(index=False))
    print("\nBy shot type (non-penalty):")
    print(db.run("08_shot_type_breakdown", player=args.player).round(2).to_string(index=False))
    print(f"\n{args.team} squad finishing (non-penalty, {args.min_shots}+ shots):")
    print(squad.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
