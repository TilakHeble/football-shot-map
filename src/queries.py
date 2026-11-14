"""Run the SQL files in sql/ against the DuckDB database and return DataFrames."""
from pathlib import Path
import re

import pandas as pd

from src.database import DB_PATH, connect

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"


class ShotAnalysis:
    """Thin wrapper: every analysis step is a named .sql file in sql/."""

    def __init__(self, db_path: Path = DB_PATH):
        self.con = connect(db_path)
        self.con.execute(self.sql("01_shot_features"))   # creates the shot_features view

    @staticmethod
    def sql(name: str) -> str:
        return (SQL_DIR / f"{name}.sql").read_text()

    def run(self, name: str, **params) -> pd.DataFrame:
        """Execute sql/<name>.sql with $named parameters, e.g. run('03_player_summary', player='...')."""
        query = self.sql(name)
        used = set(re.findall(r"\$(\w+)", query))
        missing = used - params.keys()
        if missing:
            raise ValueError(f"{name}.sql needs parameters: {sorted(missing)}")
        return self.con.execute(query, {k: v for k, v in params.items() if k in used}).df()

    def players(self, team: str) -> list[str]:
        return self.con.execute(
            "SELECT DISTINCT player FROM shots WHERE team = $team ORDER BY player",
            {"team": team}).fetchall()
