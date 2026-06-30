# Kongregate Data Quality Report

- Run timestamp: 2026-06-30T09:30:28Z
- As of: 2026-06-30
- Ranked rows: 40253
- Ranked rows with play counts: 12461
- Ranked date range: 2007-01-20 to 2026-06-26
- Mini catalog games: 3358
- Metrics history rows/games: 6520 / 2309
- Metrics date range: 2013-09-18 to 2026-06-30
- Invalid cached HTML files: 0

## Top Issues

- MEDIUM coverage/months_without_ranked_captures: 37 - Fetch additional CDX captures for ranked/listing pages, prioritizing long empty stretches.
- HIGH metrics/catalog_games_without_metrics_history: 576 - Sweep metrics.json histories by catalog chunks using --catalog-offset/--catalog-limit.
- HIGH metrics/catalog_games_need_page_history: 2549 - Continue per-game metrics history backfill.
- LOW dedupe/duplicate_ranked_rows: 3517 - Review duplicate key handling by date/source/rank/game.
- MEDIUM identity/games_with_multiple_url_variants: 377 - Use canonical URL keys for joins and charting; consider canonicalizing processed rows.
- MEDIUM plays/play_count_decreases: 3 - Review source-specific decreases; chart uses max observed counts but raw rows need QA labels.
- LOW plays/stale_listing_play_count_observations: 156 - Kept as raw observations, but excluded from true decrease counts because the value repeats an older listing count.

## Top Metrics Backfill Priorities

- The Gates of Heaven (score 3352, best rank 1, metrics rows 0)
- as3q32@gmail.com (score 3351, best rank 1, metrics rows 0)
- Cute Baby Girl Spring Outing (score 3351, best rank 1, metrics rows 0)
- Evolve (score 3351, best rank 1, metrics rows 0)
- Football Legends 2016 (score 3351, best rank 1, metrics rows 0)
- Guess the city2 (score 3351, best rank 1, metrics rows 0)
- Key to Success (score 3351, best rank 1, metrics rows 0)
- Last Warrior (score 3351, best rank 1, metrics rows 0)
- LT-Breakout (score 3351, best rank 1, metrics rows 0)
- Make Me 10 (score 3351, best rank 1, metrics rows 0)
- Minions Bejeweled (score 3351, best rank 1, metrics rows 0)
- Missiles Again (score 3351, best rank 1, metrics rows 0)
