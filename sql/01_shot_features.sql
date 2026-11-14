-- Shot-level features, built on top of the raw shots table.
-- StatsBomb pitch: 120 x 80 yards, attacking towards x = 120, goal posts at y = 36 and y = 44.
CREATE OR REPLACE TEMP VIEW shot_features AS
SELECT
    s.*,
    m.match_date,
    m.home_team,
    m.away_team,
    CASE WHEN s.team = m.home_team THEN m.away_team ELSE m.home_team END AS opponent,
    s.outcome = 'Goal'                                     AS is_goal,
    s.shot_type = 'Penalty'                                AS is_penalty,
    s.outcome IN ('Goal', 'Saved', 'Saved to Post')        AS on_target,
    (s.x >= 102 AND s.y BETWEEN 18 AND 62)                 AS in_box,
    sqrt(power(120 - s.x, 2) + power(40 - s.y, 2))         AS distance_yd,
    sqrt(power(120 - s.x, 2) + power(40 - s.y, 2)) * 0.9144 AS distance_m,
    -- angle the goal mouth subtends from the shot location
    degrees(abs(atan2(44 - s.y, 120 - s.x) - atan2(36 - s.y, 120 - s.x))) AS angle_deg
FROM shots AS s
JOIN matches AS m USING (match_id);
