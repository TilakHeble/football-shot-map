-- Non-penalty shots inside vs outside the penalty box.
SELECT
    CASE WHEN in_box THEN 'Inside box' ELSE 'Outside box' END AS zone,
    count(*)                        AS shots,
    count(*) FILTER (WHERE is_goal) AS goals,
    sum(xg)                         AS npxg,
    avg(xg)                         AS xg_per_shot,
    100.0 * count(*) / sum(count(*)) OVER () AS share_of_shots_pct
FROM shot_features
WHERE player = $player AND NOT is_penalty
GROUP BY zone
ORDER BY zone;
