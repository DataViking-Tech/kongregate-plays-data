# Kongregate Data Quality Report

- Run timestamp: 2026-07-01T02:32:29Z
- As of: 2026-07-01
- Ranked rows: 47186
- Ranked rows with play counts: 14518
- Ranked date range: 2007-01-20 to 2026-06-26
- Ranked months with rows but zero listing play counts: 134 (2014-09 to 2025-10)
- Mini catalog games: 2928
- Metrics history rows/games: 7833 / 2572
- Metrics date range: 2007-03-24 to 2026-06-30
- Invalid cached HTML files: 0

## Top Issues

- MEDIUM coverage/months_without_ranked_captures: 1 - Fetch additional CDX captures for ranked/listing pages, prioritizing long empty stretches.
- HIGH plays/ranked_months_without_listing_play_counts: 134 - Use per-game metrics/page-history backfill for this era; archived ranked-list rows are present but the observed layout often omits public play-count text.
- HIGH metrics/catalog_games_without_metrics_history: 356 - Sweep metrics.json histories by catalog chunks using --catalog-offset/--catalog-limit.
- HIGH metrics/catalog_games_need_page_history: 2247 - Continue per-game metrics history backfill.
- MEDIUM plays/play_count_decreases: 9 - Review source-specific decreases; chart uses max observed counts but raw rows need QA labels.
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
