# Kongregate Data Quality Report

- Run timestamp: 2026-06-30T20:17:22Z
- As of: 2026-06-30
- Ranked rows: 47186
- Ranked rows with play counts: 14518
- Ranked date range: 2007-01-20 to 2026-06-26
- Mini catalog games: 2936
- Metrics history rows/games: 7466 / 2569
- Metrics date range: 2013-09-18 to 2026-06-30
- Invalid cached HTML files: 0

## Top Issues

- HIGH metrics/catalog_games_without_metrics_history: 367 - Sweep metrics.json histories by catalog chunks using --catalog-offset/--catalog-limit.
- HIGH metrics/catalog_games_need_page_history: 2250 - Continue per-game metrics history backfill.
- MEDIUM plays/play_count_decreases: 6 - Review source-specific decreases; chart uses max observed counts but raw rows need QA labels.
- LOW plays/stale_listing_play_count_observations: 227 - Kept as raw observations, but excluded from true decrease counts because the value repeats an older listing count.

## Top Metrics Backfill Priorities

- as3q32@gmail.com (score 3351, best rank 1, metrics rows 0)
- Football Legends 2016 (score 3351, best rank 1, metrics rows 0)
- Key to Success (score 3351, best rank 1, metrics rows 0)
- Last Warrior (score 3351, best rank 1, metrics rows 0)
- LT-Breakout (score 3351, best rank 1, metrics rows 0)
- Make Me 10 (score 3351, best rank 1, metrics rows 0)
- Missiles Again (score 3351, best rank 1, metrics rows 0)
- Run Bird Run Online (score 3351, best rank 1, metrics rows 0)
- Salads by Chef: Merge Сraft (score 3351, best rank 1, metrics rows 0)
- SpaceWarrior (score 3351, best rank 1, metrics rows 0)
- SuperBall Idle (score 3351, best rank 1, metrics rows 0)
- Surrounded (score 3351, best rank 1, metrics rows 0)
