-- Headline numbers for one player. NP = non-penalty.
SELECT
    count(*)                                                  AS shots,
    count(*) FILTER (WHERE is_goal)                           AS goals,
    sum(xg)                                                   AS xg,
    count(*) FILTER (WHERE is_goal AND NOT is_penalty)        AS np_goals,
    sum(xg) FILTER (WHERE NOT is_penalty)                     AS npxg,
    avg(xg) FILTER (WHERE NOT is_penalty)                     AS npxg_per_shot,
    avg(distance_m) FILTER (WHERE NOT is_penalty)             AS avg_distance_m,
    100.0 * avg(on_target::INT)                               AS on_target_pct
FROM shot_features
WHERE player = $player;
