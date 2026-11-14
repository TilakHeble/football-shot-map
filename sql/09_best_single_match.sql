-- The player's biggest non-penalty scoring match (used to annotate the season chart).
SELECT
    match_id,
    match_date,
    opponent,
    count(*) FILTER (WHERE is_goal)              AS np_goals,
    sum(xg) FILTER (WHERE is_goal)               AS xg_of_goals,
    sum(xg)                                      AS npxg
FROM shot_features
WHERE player = $player AND NOT is_penalty
GROUP BY match_id, match_date, opponent
ORDER BY np_goals DESC, match_date
LIMIT 1;
