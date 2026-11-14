-- Every shot by one player (used for the shot map).
SELECT x, y, xg, is_goal, is_penalty, outcome, body_part, match_date, opponent, minute
FROM shot_features
WHERE player = $player
ORDER BY match_date, period, minute, second;
