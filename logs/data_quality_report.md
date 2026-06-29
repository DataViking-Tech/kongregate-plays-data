# Kongregate Data Quality Report

- Run timestamp: 2026-06-29T16:32:13Z
- As of: 2026-06-29
- Ranked rows: 15493
- Ranked rows with play counts: 7154
- Ranked date range: 2007-01-20 to 2026-06-26
- Mini catalog games: 1592
- Metrics history rows/games: 4419 / 886
- Metrics date range: 2013-09-18 to 2026-06-29
- Invalid cached HTML files: 0

## Top Issues

- MEDIUM coverage/months_without_ranked_captures: 100 - Fetch additional CDX captures for ranked/listing pages, prioritizing long empty stretches.
- HIGH metrics/catalog_games_without_metrics_history: 397 - Sweep metrics.json histories by catalog chunks using --catalog-offset/--catalog-limit.
- HIGH metrics/catalog_games_need_page_history: 1154 - Continue per-game metrics history backfill.
- LOW dedupe/duplicate_ranked_rows: 1506 - Review duplicate key handling by date/source/rank/game.
- MEDIUM identity/games_with_multiple_url_variants: 280 - Use canonical URL keys for joins and charting; consider canonicalizing processed rows.

## Top Metrics Backfill Priorities

- LT-Breakout (score 3351, best rank 1, metrics rows 0)
- Melon Madness (score 3351, best rank 1, metrics rows 0)
- Nature Hidden Objects (score 3351, best rank 1, metrics rows 0)
- Run Bird Run Online (score 3351, best rank 1, metrics rows 0)
- Spell Sorter (score 3351, best rank 1, metrics rows 0)
- SuperBall Idle (score 3351, best rank 1, metrics rows 0)
- Surrounded (score 3351, best rank 1, metrics rows 0)
- The Space Commando (score 3351, best rank 1, metrics rows 0)
- Britney Spears vs Child Servisous (score 3251, best rank 2, metrics rows 0)
- Caralhinhos Voadores - Age Of Delicia (score 3251, best rank 2, metrics rows 0)
- Cherrie New Spring Trends (score 3251, best rank 2, metrics rows 0)
- Chevrolet Cruze Puzzle (score 3251, best rank 2, metrics rows 0)
