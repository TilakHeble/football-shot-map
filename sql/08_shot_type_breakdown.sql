-- Non-penalty goals vs xG split by shot type (open play, free kick, ...).
SELECT
    shot_type,
    count(*)                        AS shots,
    count(*) FILTER (WHERE is_goal) AS goals,
    sum(xg)                         AS xg
FROM shot_features
WHERE player = $player AND NOT is_penalty
GROUP BY shot_type
ORDER BY shots DESC;
