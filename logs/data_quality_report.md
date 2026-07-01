# Kongregate Data Quality Report

- Run timestamp: 2026-07-01T07:26:14Z
- As of: 2026-07-01
- Ranked rows: 47885
- Ranked rows with play counts: 15217
- Ranked date range: 2007-01-20 to 2026-07-01
- Ranked months with rows but zero listing play counts: 134 (2014-09 to 2025-10)
- Mini catalog games: 2997
- Metrics history rows/games: 7932 / 2667
- Metrics date range: 2007-03-24 to 2026-07-01
- Invalid cached HTML files: 0

## Top Issues

- HIGH plays/ranked_months_without_listing_play_counts: 134 - Use per-game metrics/page-history backfill for this era; archived ranked-list rows are present but the observed layout often omits public play-count text.
- HIGH metrics/catalog_games_without_metrics_history: 330 - Sweep metrics.json histories by catalog chunks using --catalog-offset/--catalog-limit.
- HIGH metrics/catalog_games_need_page_history: 2247 - Continue per-game metrics history backfill.
- MEDIUM plays/suspicious_metric_route_decreases: 2 - Review canonical URL aliases or quarantine the lower metrics route; chart uses max observed counts.
- LOW plays/source_conflict_play_count_decreases: 7 - Kept as raw observations, but excluded from true decrease counts because nearby listing/page sources disagree.
- LOW plays/stale_listing_play_count_observations: 353 - Kept as raw observations, but excluded from true decrease counts because the value repeats an older listing count.

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
