-- Running non-penalty goals and npxG across every matchday of the team's season,
-- including matchdays where the player didn't shoot (they contribute zero).
WITH team_matches AS (
    SELECT
        match_id,
        match_date,
        CASE WHEN home_team = $team THEN away_team ELSE home_team END AS opponent,
        row_number() OVER (ORDER BY match_date) AS matchday
    FROM matches
    WHERE $team IN (home_team, away_team)
),
player_per_match AS (
    SELECT
        match_id,
        count(*) FILTER (WHERE is_goal) AS np_goals,
        sum(xg)                         AS npxg
    FROM shot_features
    WHERE player = $player AND NOT is_penalty
    GROUP BY match_id
)
SELECT
    t.matchday,
    t.match_id,
    t.match_date,
    t.opponent,
    coalesce(p.np_goals, 0) AS np_goals,
    coalesce(p.npxg, 0)     AS npxg,
    sum(coalesce(p.np_goals, 0)) OVER (ORDER BY t.matchday) AS cum_np_goals,
    sum(coalesce(p.npxg, 0))     OVER (ORDER BY t.matchday) AS cum_npxg
FROM team_matches AS t
LEFT JOIN player_per_match AS p USING (match_id)
ORDER BY t.matchday;
