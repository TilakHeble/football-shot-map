"""Generate the shot map, xG timeline and squad comparison for one player.

Usage:
    python run.py                                   # Florian Wirtz (default)
    python run.py --player "Victor Okoh Boniface"
"""
import argparse
from pathlib import Path

from src.data import add_features, load_shots
from src.plots import cumulative_xg, shot_map, squad_comparison, summary

FIG_DIR = Path(__file__).parent / "figures"


def hat_trick_note(player_shots):
    """If the player scored 3+ non-penalty goals in a match, label the biggest haul."""
    np_goals = player_shots[player_shots["is_goal"] & ~player_shots["is_penalty"]]
    per = np_goals.groupby("match_id").size()
    if per.empty or per.max() < 3:
        return None
    mid = per.idxmax()
    row = player_shots[player_shots["match_id"] == mid].iloc[0]
    team = player_shots["team"].iloc[0]
    opp = row["away_team"] if row["home_team"] == team else row["home_team"]
    return {"match_id": mid, "text": f"{per.max()} goals vs {opp} ({row['match_date']})"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--player", default="Florian Wirtz")
    p.add_argument("--team", default="Bayer Leverkusen")
    p.add_argument("--competition-id", type=int, default=9)   # Bundesliga
    p.add_argument("--season-id", type=int, default=281)      # 2023/24
    args = p.parse_args()

    FIG_DIR.mkdir(exist_ok=True)
    shots = add_features(load_shots(args.competition_id, args.season_id))
    player = shots[shots["player"] == args.player]
    if player.empty:
        names = sorted(shots.loc[shots["team"] == args.team, "player"].unique())
        raise SystemExit(f"No shots for {args.player!r}. Try one of:\n  " + "\n  ".join(names))

    slug = args.player.lower().replace(" ", "_")
    shot_map(player, args.player, f"{args.team} · Bundesliga 2023/24 · all shots",
             FIG_DIR / f"{slug}_shot_map.png")
    cumulative_xg(player, shots, args.team, args.player,
                  FIG_DIR / f"{slug}_cumulative_xg.png",
                  annotate=hat_trick_note(player))
    table = squad_comparison(shots, args.team, args.player,
                             FIG_DIR / "squad_goals_vs_xg.png")

    print(f"\n{args.player}")
    for k, v in summary(player).items():
        print(f"  {k:<18}{v:.2f}" if isinstance(v, float) else f"  {k:<18}{v}")
    print("\nSquad (non-penalty):")
    print(table.round(2).to_string())


if __name__ == "__main__":
    main()
