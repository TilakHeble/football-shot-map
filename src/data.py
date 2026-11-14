"""Load and cache shot data from StatsBomb Open Data."""
from pathlib import Path
import warnings

import pandas as pd
from statsbombpy import sb

warnings.filterwarnings("ignore", module="statsbombpy")

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

SHOT_COLS = [
    "match_id", "minute", "second", "period", "team", "player", "position",
    "location", "shot_end_location", "shot_statsbomb_xg", "shot_outcome",
    "shot_body_part", "shot_type", "shot_technique", "play_pattern",
    "under_pressure", "shot_first_time",
]


def load_shots(competition_id: int = 9, season_id: int = 281,
               refresh: bool = False) -> pd.DataFrame:
    """Return every shot in a competition-season (cached to CSV).

    Defaults: Bundesliga 2023/24 (Bayer Leverkusen's matches are in the open data).
    """
    DATA_DIR.mkdir(exist_ok=True)
    cache = DATA_DIR / f"shots_{competition_id}_{season_id}.csv"
    if cache.exists() and not refresh:
        df = pd.read_csv(cache)
        for col in ("location", "shot_end_location"):
            df[col] = df[col].apply(_parse_list)
        return df

    matches = sb.matches(competition_id=competition_id, season_id=season_id)
    frames = []
    for match_id in matches["match_id"]:
        ev = sb.events(match_id=match_id)
        shots = ev[ev["type"] == "Shot"].copy()
        frames.append(shots[[c for c in SHOT_COLS if c in shots.columns]])
    df = pd.concat(frames, ignore_index=True)

    meta = matches[["match_id", "match_date", "home_team", "away_team",
                    "home_score", "away_score"]]
    df = df.merge(meta, on="match_id", how="left")
    df["under_pressure"] = df["under_pressure"].fillna(False).astype(bool)
    df["shot_first_time"] = df["shot_first_time"].fillna(False).astype(bool)
    df = df.sort_values(["match_date", "period", "minute", "second"]).reset_index(drop=True)
    df.to_csv(cache, index=False)
    return df


def _parse_list(v):
    if isinstance(v, str):
        return [float(x) for x in v.strip("[]").split(",")]
    return v


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add goal flag, x/y, distance and angle to goal (StatsBomb 120x80 pitch)."""
    import numpy as np
    out = df.copy()
    out["is_goal"] = out["shot_outcome"].eq("Goal")
    out["x"] = out["location"].str[0]
    out["y"] = out["location"].str[1]
    dx, dy = 120 - out["x"], (40 - out["y"]).abs()
    out["distance"] = np.hypot(dx, dy)
    # angle subtended by the goal mouth (posts at y=36 and y=44)
    out["angle_deg"] = np.degrees(np.abs(
        np.arctan2(44 - out["y"], dx) - np.arctan2(36 - out["y"], dx)))
    out["is_penalty"] = out["shot_type"].eq("Penalty")
    return out
