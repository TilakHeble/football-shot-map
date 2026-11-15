"""Build a DuckDB database from StatsBomb Open Data.

Creates two tables in data/statsbomb.duckdb:
  matches - one row per match (date, teams, score)
  shots   - one row per shot (location, xG, outcome, body part, ...)
"""
from pathlib import Path
import warnings

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "statsbomb.duckdb"


def build_database(competition_id: int = 9, season_id: int = 281,
                   db_path: Path = DB_PATH) -> Path:
    """Download one competition-season and (re)write the matches and shots tables."""
    from statsbombpy import sb   # only needed when downloading
    warnings.filterwarnings("ignore", module="statsbombpy")

    matches = sb.matches(competition_id=competition_id, season_id=season_id)
    matches = matches[["match_id", "match_date", "home_team", "away_team",
                       "home_score", "away_score"]].copy()
    matches["match_date"] = pd.to_datetime(matches["match_date"]).dt.date
    matches["competition_id"], matches["season_id"] = competition_id, season_id

    frames = []
    for match_id in matches["match_id"]:
        ev = sb.events(match_id=match_id)
        frames.append(ev[ev["type"] == "Shot"])
    raw = pd.concat(frames, ignore_index=True)

    shots = pd.DataFrame({
        "shot_id": raw["id"],
        "match_id": raw["match_id"],
        "period": raw["period"],
        "minute": raw["minute"],
        "second": raw["second"],
        "team": raw["team"],
        "player": raw["player"],
        "position": raw["position"],
        "x": raw["location"].str[0],
        "y": raw["location"].str[1],
        "end_x": raw["shot_end_location"].str[0],
        "end_y": raw["shot_end_location"].str[1],
        "xg": raw["shot_statsbomb_xg"],
        "outcome": raw["shot_outcome"],
        "body_part": raw["shot_body_part"],
        "shot_type": raw["shot_type"],
        "technique": raw["shot_technique"],
        "play_pattern": raw["play_pattern"],
        "under_pressure": raw.get("under_pressure").fillna(False).astype(bool),
        "first_time": raw.get("shot_first_time").fillna(False).astype(bool),
    })

    db_path.parent.mkdir(exist_ok=True)
    with duckdb.connect(str(db_path)) as con:
        con.execute("CREATE OR REPLACE TABLE matches AS SELECT * FROM matches")
        con.execute("CREATE OR REPLACE TABLE shots AS SELECT * FROM shots")
    return db_path


def connect(db_path: Path = DB_PATH) -> duckdb.DuckDBPyConnection:
    """Open the database, building it first if it doesn't exist."""
    if not db_path.exists():
        print("Database not found - downloading StatsBomb data (about a minute)...")
        build_database(db_path=db_path)
    return duckdb.connect(str(db_path), read_only=True)


if __name__ == "__main__":
    print(f"Built {build_database()}")
