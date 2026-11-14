"""Streamlit dashboard: Bayer Leverkusen 2023/24 shooting and finishing.

Run locally:  streamlit run app.py
Every number comes from the SQL files in sql/, run against data/statsbomb.duckdb.
"""
import pandas as pd
import streamlit as st

from src import interactive as viz
from src.queries import ShotAnalysis

TEAM = "Bayer Leverkusen"
st.set_page_config(page_title="Leverkusen 2023/24 · Shots & xG", page_icon="⚽", layout="wide")


@st.cache_data
def query(name: str, **params) -> pd.DataFrame:
    # a fresh connection per cached query keeps DuckDB thread-safe under Streamlit
    return ShotAnalysis().run(name, **params)


@st.cache_data
def sql_text(name: str) -> str:
    return ShotAnalysis.sql(name)


# ---------- sidebar ----------
st.sidebar.header("Filters")
all_squad = query("06_squad_finishing", team=TEAM, min_shots=1)
players = all_squad.sort_values("shots", ascending=False)["player"].tolist()
player = st.sidebar.selectbox("Player", players, index=players.index("Florian Wirtz"),
                              help="Leverkusen players, ordered by number of non-penalty shots")
min_shots = st.sidebar.slider("Squad chart: minimum shots", 5, 40, 15, step=5)
include_pens = st.sidebar.checkbox("Show penalties on the shot map", value=True)
st.sidebar.markdown("---")
st.sidebar.caption("Data: StatsBomb Open Data, Bundesliga 2023/24 (all 34 Leverkusen matches). "
                   "NP = non-penalty. xG = StatsBomb expected goals.")

# ---------- data ----------
s = query("03_player_summary", player=player).iloc[0]
shots = query("02_player_shots", player=player)
cum = query("05_cumulative_by_matchday", player=player, team=TEAM)
squad = query("06_squad_finishing", team=TEAM, min_shots=min_shots)
me = all_squad.set_index("player").loc[player]

# ---------- header + KPIs ----------
st.title(player)
st.caption(f"{TEAM} · Bundesliga 2023/24 · shooting and finishing")

k = st.columns(5)
k[0].metric("Shots", int(s["shots"]))
k[1].metric("Goals", int(s["goals"]), help=f"{int(s['np_goals'])} non-penalty")
k[2].metric("npxG", f"{(s['npxg'] or 0):.1f}", help="Non-penalty expected goals")
k[3].metric("NP goals − npxG", f"{me['goals_minus_xg']:+.1f}",
            help=f"z = {me['z_score']:+.2f}: how many standard deviations from what xG expects "
                 "(|z| < 2 is normal variation)")
k[4].metric("npxG per shot", f"{(s['npxg_per_shot'] or 0):.2f}", help="Average chance quality")

# ---------- shot map + season timeline ----------
left, right = st.columns(2)
with left:
    st.subheader("Shot map")
    st.plotly_chart(viz.shot_map(shots, include_pens), width="stretch",
                    config={"displayModeBar": False})
    st.caption("Marker size = xG · filled = goal · hover a shot for details")
with right:
    st.subheader("Goals vs xG through the season")
    st.plotly_chart(viz.cumulative(cum), width="stretch",
                    config={"displayModeBar": False})
    best = query("09_best_single_match", player=player)
    if not best.empty and best.iloc[0]["np_goals"] >= 2:
        b = best.iloc[0]
        st.caption(f"Best game: {int(b['np_goals'])} non-penalty goals vs {b['opponent']} "
                   f"({b['match_date']:%d %b %Y}), from shots worth {b['npxg']:.2f} xG in total")

# ---------- breakdowns ----------
a, b = st.columns(2)
with a:
    st.subheader("Inside vs outside the box")
    zones = query("04_player_zones", player=player)
    st.dataframe(zones.rename(columns={"zone": "Zone", "shots": "Shots", "goals": "Goals",
                                       "npxg": "npxG", "xg_per_shot": "xG/shot",
                                       "share_of_shots_pct": "% of shots"}),
                 hide_index=True, width="stretch",
                 column_config={"npxG": st.column_config.NumberColumn(format="%.2f"),
                                "xG/shot": st.column_config.NumberColumn(format="%.2f"),
                                "% of shots": st.column_config.NumberColumn(format="%.0f%%")})
with b:
    st.subheader("By shot type")
    types = query("08_shot_type_breakdown", player=player)
    st.dataframe(types.rename(columns={"shot_type": "Type", "shots": "Shots", "goals": "Goals",
                                       "xg": "xG"}),
                 hide_index=True, width="stretch",
                 column_config={"xG": st.column_config.NumberColumn(format="%.2f")})

# ---------- squad context ----------
st.subheader("Squad finishing: who scored more than their chances suggest?")
st.plotly_chart(viz.squad_scatter(squad, player), width="stretch",
                config={"displayModeBar": False})
st.caption("Above the dashed line = more goals than xG. Hover a player for their z-score.")
st.dataframe(
    squad[["player", "shots", "np_goals", "npxg", "npxg_per_shot", "goals_minus_xg", "z_score"]]
    .rename(columns={"player": "Player", "shots": "Shots", "np_goals": "NP goals",
                     "npxg": "npxG", "npxg_per_shot": "npxG/shot",
                     "goals_minus_xg": "Goals − xG", "z_score": "z-score"}),
    hide_index=True, width="stretch",
    column_config={c: st.column_config.NumberColumn(format="%.2f")
                   for c in ["npxG", "npxG/shot", "Goals − xG", "z-score"]},
)

with st.expander("How the luck check works, and the SQL behind this page"):
    st.markdown(
        "Each shot is treated as a coin flip that lands with probability = its xG. "
        "The spread of goals you'd expect is then √Σ xG(1 − xG), and the **z-score** is "
        "(goals − xG) divided by that spread. Values beyond ±2 are unusual.")
    for name in ["01_shot_features", "05_cumulative_by_matchday", "06_squad_finishing"]:
        st.code(sql_text(name), language="sql")
