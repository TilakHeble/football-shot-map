-- Sanity check on the xG model: does mean xG match actual conversion by distance band?
SELECT
    CASE
        WHEN distance_m < 6  THEN '1. 0-6m'
        WHEN distance_m < 11 THEN '2. 6-11m'
        WHEN distance_m < 16 THEN '3. 11-16m'
        WHEN distance_m < 22 THEN '4. 16-22m'
        WHEN distance_m < 30 THEN '5. 22-30m'
        ELSE                      '6. 30m+'
    END                              AS distance_band,
    count(*)                         AS shots,
    count(*) FILTER (WHERE is_goal)  AS goals,
    avg(is_goal::INT)                AS conversion_rate,
    avg(xg)                          AS mean_xg
FROM shot_features
WHERE NOT is_penalty
GROUP BY distance_band
ORDER BY distance_band;
