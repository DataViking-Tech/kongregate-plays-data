# Kongregate Data Quality Report

- Run timestamp: 2026-06-30T05:04:42Z
- As of: 2026-06-30
- Ranked rows: 36325
- Ranked rows with play counts: 11087
- Ranked date range: 2007-01-20 to 2026-06-26
- Mini catalog games: 3007
- Metrics history rows/games: 5486 / 1366
- Metrics date range: 2013-09-18 to 2026-06-30
- Invalid cached HTML files: 0

## Top Issues

- MEDIUM coverage/months_without_ranked_captures: 66 - Fetch additional CDX captures for ranked/listing pages, prioritizing long empty stretches.
- HIGH metrics/catalog_games_without_metrics_history: 1220 - Sweep metrics.json histories by catalog chunks using --catalog-offset/--catalog-limit.
- HIGH metrics/catalog_games_need_page_history: 2311 - Continue per-game metrics history backfill.
- LOW dedupe/duplicate_ranked_rows: 3437 - Review duplicate key handling by date/source/rank/game.
- MEDIUM identity/games_with_multiple_url_variants: 349 - Use canonical URL keys for joins and charting; consider canonicalizing processed rows.
- LOW plays/stale_listing_play_count_observations: 148 - Kept as raw observations, but excluded from true decrease counts because the value repeats an older listing count.

## Top Metrics Backfill Priorities

- as3q32@gmail.com (score 3351, best rank 1, metrics rows 0)
- Football Legends 2016 (score 3351, best rank 1, metrics rows 0)
- Key to Success (score 3351, best rank 1, metrics rows 0)
- Last Warrior (score 3351, best rank 1, metrics rows 0)
- LT-Breakout (score 3351, best rank 1, metrics rows 0)
- Make Me 10 (score 3351, best rank 1, metrics rows 0)
- Missiles Again (score 3351, best rank 1, metrics rows 0)
- Run Bird Run Online (score 3351, best rank 1, metrics rows 0)
- SpaceWarrior (score 3351, best rank 1, metrics rows 0)
- SuperBall Idle (score 3351, best rank 1, metrics rows 0)
- Surrounded (score 3351, best rank 1, metrics rows 0)
- The Funniest Game Ever (score 3351, best rank 1, metrics rows 0)
