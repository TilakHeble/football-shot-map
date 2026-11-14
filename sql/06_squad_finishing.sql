-- Non-penalty finishing for every player in a squad with at least $min_shots shots.
-- Treating each shot as a Bernoulli trial with p = xG:
--   Var(goals) = sum xG (1 - xG)   ->   z = (goals - xG) / sd
WITH per_player AS (
    SELECT
        player,
        count(*)                        AS shots,
        count(*) FILTER (WHERE is_goal) AS np_goals,
        sum(xg)                         AS npxg,
        sqrt(sum(xg * (1 - xg)))        AS sd
    FROM shot_features
    WHERE team = $team AND NOT is_penalty
    GROUP BY player
)
SELECT
    player,
    shots,
    np_goals,
    npxg,
    npxg / shots              AS npxg_per_shot,
    sd,
    np_goals - npxg           AS goals_minus_xg,
    (np_goals - npxg) / sd    AS z_score,
    rank() OVER (ORDER BY np_goals - npxg DESC) AS overperformance_rank
FROM per_player
WHERE shots >= $min_shots
ORDER BY npxg DESC;
