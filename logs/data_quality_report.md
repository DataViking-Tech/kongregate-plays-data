# Kongregate Data Quality Report

- Run timestamp: 2026-06-29T04:21:17Z
- As of: 2026-06-29
- Ranked rows: 5442
- Ranked rows with play counts: 2074
- Ranked date range: 2007-01-20 to 2026-04-19
- Mini catalog games: 646
- Metrics history rows/games: 355 / 21
- Metrics date range: 2014-08-07 to 2025-10-01

## Top Issues

- HIGH coverage/ranked_capture_lag: 71 - Run modern ranked-page discovery/fetch for the newest Wayback captures.
- MEDIUM coverage/months_without_ranked_captures: 142 - Fetch additional CDX captures for ranked/listing pages, prioritizing long empty stretches.
- HIGH metrics/catalog_games_without_metrics_history: 615 - Sweep metrics.json histories by catalog chunks using --catalog-offset/--catalog-limit.
- HIGH metrics/catalog_games_need_page_history: 321 - Continue per-game metrics history backfill.
- HIGH chart/final_top_chart_entries_stale_over_one_year: 9 - Prioritize metrics histories for stale high-play games still dominating final chart ranks.
- LOW dedupe/duplicate_ranked_rows: 116 - Review duplicate key handling by date/source/rank/game.
- MEDIUM identity/games_with_multiple_url_variants: 110 - Use canonical URL keys for joins and charting; consider canonicalizing processed rows.

## Top Metrics Backfill Priorities

- Crusaders of the Lost Idols (score 3391, best rank 1, metrics rows 0)
- Realm Grinder (score 3385, best rank 1, metrics rows 0)
- NGU IDLE (score 3379, best rank 1, metrics rows 0)
- Bit Heroes (score 3377, best rank 1, metrics rows 0)
- AdVenture Capitalist (score 3374, best rank 1, metrics rows 0)
- Incremancer (score 3368, best rank 1, metrics rows 0)
- Swarm Simulator (score 3368, best rank 1, metrics rows 0)
- Retro Bowl (score 3366, best rank 1, metrics rows 0)
- The King's League: Odyssey (score 3365, best rank 1, metrics rows 0)
- Crush The Castle 2 (score 3353, best rank 1, metrics rows 0)
- Frantic Frigates (score 3353, best rank 1, metrics rows 0)
- Plinko Idle (score 3353, best rank 1, metrics rows 0)
