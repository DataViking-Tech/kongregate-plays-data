# Kongregate Data Quality Report

- Run timestamp: 2026-06-29T22:53:40Z
- As of: 2026-06-29
- Ranked rows: 25736
- Ranked rows with play counts: 8643
- Ranked date range: 2007-01-20 to 2026-06-26
- Mini catalog games: 2878
- Metrics history rows/games: 4834 / 1274
- Metrics date range: 2013-09-18 to 2026-06-29
- Invalid cached HTML files: 0

## Top Issues

- MEDIUM coverage/months_without_ranked_captures: 78 - Fetch additional CDX captures for ranked/listing pages, prioritizing long empty stretches.
- HIGH metrics/catalog_games_without_metrics_history: 1268 - Sweep metrics.json histories by catalog chunks using --catalog-offset/--catalog-limit.
- HIGH metrics/catalog_games_need_page_history: 2200 - Continue per-game metrics history backfill.
- LOW dedupe/duplicate_ranked_rows: 2285 - Review duplicate key handling by date/source/rank/game.
- MEDIUM identity/games_with_multiple_url_variants: 312 - Use canonical URL keys for joins and charting; consider canonicalizing processed rows.

## Top Metrics Backfill Priorities

- Alexia Crow and the pandora's box (score 3351, best rank 1, metrics rows 0)
- as3q32@gmail.com (score 3351, best rank 1, metrics rows 0)
- Brakeless Trials Game 2014 (score 3351, best rank 1, metrics rows 0)
- Clash of the Races 5 (score 3351, best rank 1, metrics rows 0)
- Classical Snake (score 3351, best rank 1, metrics rows 0)
- Football Legends 2016 (score 3351, best rank 1, metrics rows 0)
- Geoshape beta (score 3351, best rank 1, metrics rows 0)
- Jellydad Hero (score 3351, best rank 1, metrics rows 0)
- Key to Success (score 3351, best rank 1, metrics rows 0)
- Last Warrior (score 3351, best rank 1, metrics rows 0)
- LT-Breakout (score 3351, best rank 1, metrics rows 0)
- Make Me 10 (score 3351, best rank 1, metrics rows 0)
