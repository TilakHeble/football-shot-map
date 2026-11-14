-- One row per shot, flattened for Tableau (every shot in Leverkusen's 34 league matches, both teams).
-- Booleans become 0/1 so Tableau can SUM them; matchday is Leverkusen's matchday number.
WITH lev_matchdays AS (
    SELECT match_id, row_number() OVER (ORDER BY match_date) AS matchday
    FROM matches
    WHERE $team IN (home_team, away_team)
)
SELECT
    f.shot_id,
    f.match_id,
    md.matchday,
    f.match_date,
    f.team,
    f.opponent,
    f.player,
    f.position,
    f.period,
    f.minute,
    round(f.x, 1)            AS x,
    round(f.y, 1)            AS y,
    round(f.xg, 4)           AS xg,
    f.outcome,
    f.body_part,
    f.shot_type,
    f.play_pattern,
    f.is_goal::INT           AS is_goal,
    f.is_penalty::INT        AS is_penalty,
    f.on_target::INT         AS on_target,
    f.in_box::INT            AS in_box,
    round(f.distance_m, 1)   AS distance_m,
    round(f.angle_deg, 1)    AS angle_deg
FROM shot_features AS f
JOIN lev_matchdays AS md USING (match_id)
ORDER BY f.match_date, f.period, f.minute, f.second;
